"""여론조사 결과표 PDF 파서."""
from __future__ import annotations

import importlib
import inspect
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .models import QuestionResult
from .table_utils import (
    DEFAULT_SUMMARY_PATTERNS,
    extract_options_from_row,
    extract_percentages_from_bunched_cell,
    extract_percentages_from_cells,
    extract_sample_count,
    filter_summary_columns,
    find_total_row,
)

# config/ 디렉터리 기본 경로
# parser.py: .../services/data/src/lawdigest_data/polls/parser.py
# parents[3] = .../services/data  →  config/
_DEFAULT_CONFIG_DIR = Path(__file__).resolve().parents[3] / "config"

# PageData: (테이블_외부_텍스트, 테이블_목록, 전체_텍스트) 타입 alias
PageData = Tuple[str, List, str]


class UnknownPollsterError(ValueError):
    """등록된 파서가 없는 조사기관에 대해 발생하는 예외."""


# ── PollParser Protocol ────────────────────────────────────────────────────────
# 모든 파서 클래스는 이 인터페이스를 준수해야 한다.
# - PARSER_KEY: parser_registry.json의 "class" 값과 동일한 클래스 변수
# - parse(pages_data): 단일 시그니처로 통일 (text-only 파서도 포함)
try:
    from typing import Protocol, runtime_checkable
except ImportError:  # Python < 3.8
    from typing_extensions import Protocol, runtime_checkable  # type: ignore[assignment]


@runtime_checkable
class PollParser(Protocol):
    """여론조사 결과표 파서의 공통 인터페이스."""

    PARSER_KEY: str  # parser_registry.json "class" 값과 동일

    def parse(self, pages_data: List[PageData]) -> List[QuestionResult]:
        """pages_data를 파싱하여 QuestionResult 목록을 반환한다."""
        ...


def _build_gid_to_unicode(font_path: Path) -> Dict[int, int]:
    """NotoSansCJKkr 폰트 파일에서 GID→Unicode 역매핑을 생성한다.

    여론조사꽃 PDF는 Identity-H 인코딩으로 임베드된 NotoSansKR 서브셋 폰트를 사용하며,
    ToUnicode CMap에 한글 매핑이 누락되어 있다. 원본 폰트의 cmap(unicode→GID)을
    역전시켜 디코딩 테이블을 만든다.
    """
    try:
        from fontTools.ttLib import TTFont
    except ImportError as exc:
        raise RuntimeError("GID 디코딩을 위해 fonttools가 필요합니다: pip install fonttools") from exc

    font = TTFont(str(font_path))
    cmap = font.getBestCmap()
    gid_map: Dict[int, int] = {}
    for unicode_val, glyph_name in cmap.items():
        gid = font.getGlyphID(glyph_name)
        if gid not in gid_map:
            gid_map[gid] = unicode_val
    font.close()
    return gid_map


def _decode_text_with_gid(raw: str, gid_map: Dict[int, int]) -> str:
    """GID→Unicode 매핑을 이용해 잘못 변환된 문자열을 올바른 유니코드로 디코딩한다.

    PyMuPDF가 ToUnicode CMap 없이 글리프 인덱스를 그대로 유니코드로 해석한
    깨진 문자열을 원래 한글로 복원한다. 매핑이 없는 글리프(공백 등)는 공백으로 대체한다.
    """
    result = []
    for ch in raw:
        cp = ord(ch)
        if cp > 127:
            real = gid_map.get(cp)
            result.append(chr(real) if real else " ")
        else:
            result.append(ch)
    return "".join(result)


def _extract_text_outside_tables(page: "fitz.Page", finder: "fitz.TableFinder") -> str:  # type: ignore[name-defined]  # noqa: F821
    """테이블 영역을 제외한 페이지 텍스트를 줄 단위로 재구성한다.

    PyMuPDF의 get_text()는 테이블 셀 내용까지 포함해 뒤섞이므로,
    words 단위로 테이블 bbox 외부 단어만 추출해 라인을 재조합한다.
    """
    table_bboxes = [t.bbox for t in finder.tables]

    def _in_table(wx0: float, wy0: float, wx1: float, wy1: float) -> bool:
        return any(
            wx0 >= tx0 - 3 and wy0 >= ty0 - 3 and wx1 <= tx1 + 3 and wy1 <= ty1 + 3
            for tx0, ty0, tx1, ty1 in table_bboxes
        )

    words = [
        w for w in page.get_text("words")
        if not _in_table(w[0], w[1], w[2], w[3])
    ]
    words.sort(key=lambda w: (round(w[1]), w[0]))

    lines: List[str] = []
    current_y: Optional[float] = None
    line_words: List[str] = []
    for w in words:
        y = round(w[1])
        if current_y is None or abs(y - current_y) > 3:
            if line_words:
                lines.append(" ".join(line_words))
            current_y, line_words = y, [w[4]]
        else:
            line_words.append(w[4])
    if line_words:
        lines.append(" ".join(line_words))

    return "\n".join(lines)


def _infer_col_x_ranges(fitz_table: "fitz.Table") -> Dict[int, Tuple[float, float]]:  # type: ignore[name-defined]  # noqa: F821
    """테이블 각 컬럼의 x 범위를 추론한다.

    개별 셀이 가장 많은 행(병합 없는 행)을 기준으로 컬럼 x 범위를 결정한다.
    colspan 병합 셀은 x1이 실제 컬럼보다 훨씬 크므로, 비-None 셀이 많은 행을
    선택하면 개별 경계를 정확히 반영할 수 있다.
    """
    col_count = fitz_table.col_count

    # 각 행의 non-None 셀 수 계산, 가장 많은 행(들)을 선택
    best_rows = []
    best_count = 0
    for row in fitz_table.rows:
        non_none = sum(1 for c in row.cells if c is not None)
        if non_none > best_count:
            best_count = non_none
            best_rows = [row]
        elif non_none == best_count:
            best_rows.append(row)

    # 선택된 행들에서 컬럼 x 범위 수집
    col_x: Dict[int, List[Tuple[float, float]]] = {}
    for row in best_rows:
        for ci, cell in enumerate(row.cells):
            if cell is not None:
                x0, _, x1, _ = cell
                col_x.setdefault(ci, []).append((x0, x1))

    # 각 컬럼의 중앙값 사용
    result: Dict[int, Tuple[float, float]] = {}
    for ci in range(col_count):
        ranges = col_x.get(ci)
        if ranges:
            x0s = sorted(r[0] for r in ranges)
            x1s = sorted(r[1] for r in ranges)
            mid = len(ranges) // 2
            result[ci] = (x0s[mid], x1s[mid])

    return result


def _unmerge_table(
    fitz_table: "fitz.Table",  # type: ignore[name-defined]  # noqa: F821
    page: "fitz.Page",  # type: ignore[name-defined]  # noqa: F821
) -> List[List]:
    """colspan 병합 셀을 해제하여 모든 컬럼에 값이 채워진 2D 테이블을 반환한다.

    PyMuPDF ``Table.extract()`` 는 colspan 병합 셀의 텍스트를 첫 번째 셀에 이어
    붙이고 나머지를 None으로 채운다. 이 함수는 병합 셀의 bbox와
    ``page.get_text("words")`` 의 x 좌표를 대조하여 값을 원래 컬럼으로 분리한다.

    rowspan(동일 컬럼의 여러 행에 걸친 병합)은 그대로 None으로 유지된다.
    """
    extracted = fitz_table.extract()

    # 모든 행에 None이 없으면 병합 셀 없음 → 그대로 반환
    has_merge = any(
        None in row
        for row in extracted
    )
    if not has_merge:
        return extracted

    col_x_ranges = _infer_col_x_ranges(fitz_table)
    if not col_x_ranges:
        return extracted

    # 페이지 전체 words 한 번만 추출
    all_words = page.get_text("words")  # (x0, y0, x1, y1, text, block, line, word)

    result: List[List] = []
    for row_idx, ext_row in enumerate(extracted):
        if None not in ext_row:
            result.append(ext_row)
            continue

        row_obj = fitz_table.rows[row_idx]
        new_row: List = list(ext_row)

        for col_idx, cell_bbox in enumerate(row_obj.cells):
            if cell_bbox is None:
                continue  # rowspan — 이 셀은 상위 행이 소유

            x0, y0, x1, y1 = cell_bbox
            typical_x1 = col_x_ranges.get(col_idx, (x0, x1))[1]

            # colspan 감지: 셀 우측 경계가 해당 컬럼의 일반 우측보다 유의미하게 큼
            if x1 <= typical_x1 + 5:
                continue  # 단일 셀

            # colspan에 포함되는 컬럼 목록
            spanned = [
                ci
                for ci, (cx0, cx1) in col_x_ranges.items()
                if cx0 >= x0 - 2 and cx1 <= x1 + 2
            ]
            if len(spanned) <= 1:
                continue

            # 병합 셀 영역 내 words 추출 (y 범위는 셀보다 약간 여유)
            cell_words = [
                w for w in all_words
                if w[0] >= x0 - 2 and w[2] <= x1 + 2
                and w[1] >= y0 - 3 and w[3] <= y1 + 3
            ]

            # 각 word → 컬럼 배정 (x 중심 기준)
            col_texts: Dict[int, List[str]] = {ci: [] for ci in spanned}
            assigned_cols: set = set()
            for w in cell_words:
                x_center = (w[0] + w[2]) / 2
                for ci in spanned:
                    cx0, cx1 = col_x_ranges[ci]
                    if cx0 - 2 <= x_center <= cx1 + 2:
                        col_texts[ci].append(w[4])
                        assigned_cols.add(ci)
                        break

            # 재배분 조건: 여러 컬럼에 단어가 분산되고, 모든 단어가 숫자일 때만 수행.
            #  - 하나의 컬럼에만 있으면 → 정상 colspan 레이블 (extract()가 이미 처리)
            #  - 숫자가 아닌 단어 포함 → '▣ 전 체 ▣' 같은 레이블 (재배분 불필요)
            _float_re = re.compile(r"^\d+\.?\d*$")
            all_numeric = all(_float_re.match(w[4]) for w in cell_words if w[4].strip())
            if len(assigned_cols) <= 1 or not all_numeric:
                continue

            # new_row 갱신
            for ci in spanned:
                texts = col_texts[ci]
                new_row[ci] = " ".join(texts) if texts else None

        result.append(new_row)

    return result


def _extract_pages_with_gid_decode(
    pdf_path: Path,
    gid_map: Dict[int, int],
) -> List[Tuple[str, List, str]]:
    """GID 디코딩을 적용하여 페이지 데이터를 추출한다.

    rawdict 모드로 문자별 코드포인트를 읽고 _decode_text_with_gid를 적용한 뒤,
    기존 pages_data 형식 (outside_text, tables, full_text) 으로 반환한다.
    """
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("PDF 파싱을 위해 pymupdf가 필요합니다.") from exc

    def _decode_page_text(page: "fitz.Page", gid_map: Dict[int, int]) -> str:  # type: ignore[name-defined]
        """페이지 전체 텍스트를 GID 디코딩하여 반환한다."""
        result = []
        for b in page.get_text("rawdict")["blocks"]:
            if b.get("type") != 0:
                continue
            for line in b.get("lines", []):
                line_chars = []
                for span in line.get("spans", []):
                    for ch in span.get("chars", []):
                        c = ch["c"]
                        cp = ord(c) if len(c) == 1 else None
                        if cp and cp > 127:
                            real = gid_map.get(cp)
                            line_chars.append(chr(real) if real else " ")
                        else:
                            line_chars.append(c)
                result.append("".join(line_chars))
        return "\n".join(result)

    def _decode_table(table: List[List], gid_map: Dict[int, int]) -> List[List]:
        """테이블 셀 텍스트를 GID 디코딩하여 반환한다."""
        decoded = []
        for row in table:
            decoded_row = []
            for cell in row:
                if cell is None:
                    decoded_row.append(None)
                else:
                    decoded_row.append(_decode_text_with_gid(str(cell), gid_map))
            decoded.append(decoded_row)
        return decoded

    pages_data: List[Tuple[str, List, str]] = []
    doc = fitz.open(str(pdf_path))
    try:
        for page in doc:
            finder = page.find_tables()
            tables = [_decode_table(_unmerge_table(t, page), gid_map) for t in finder.tables]
            full_text = _decode_page_text(page, gid_map)
            outside_text = _decode_text_with_gid(
                _extract_text_outside_tables(page, finder) if finder.tables else page.get_text(),
                gid_map,
            )
            pages_data.append((outside_text, tables, full_text))
    finally:
        doc.close()
    return pages_data


@dataclass
class _RegistryEntry:
    parser_class: type
    pollster_keywords: Tuple[str, ...] = field(default_factory=tuple)
    priority: int = 0


def _build_parser_key_map() -> Dict[str, type]:
    """이 모듈 내에서 PARSER_KEY를 가진 모든 파서 클래스를 자동으로 수집한다.

    parser_registry.json의 "class" 값(= PARSER_KEY)으로 클래스를 찾기 위해 사용된다.
    새 파서를 추가할 때 이 함수를 수정할 필요가 없다 — PARSER_KEY만 정의하면 된다.
    """
    module = importlib.import_module(__name__)
    result: Dict[str, type] = {}
    for _name, obj in inspect.getmembers(module, inspect.isclass):
        key = getattr(obj, "PARSER_KEY", None)
        if key:
            result[key] = obj
    return result


class PollResultParser:
    """결과표 PDF에서 설문 항목별 응답 결과를 추출하는 파서.

    기관별 파서는 parser_registry.json에서 로드한다.
    registry_path=None 시 config/parser_registry.json을 자동으로 찾는다.
    JSON이 없으면 RuntimeError를 발생시킨다.

    pollster_hint가 레지스트리에 등록된 기관과 매칭되지 않으면
    UnknownPollsterError를 발생시킨다 (폴백 없음).
    """

    def __init__(self, registry_path: Optional[Path] = None) -> None:
        self._registry: List[_RegistryEntry] = []
        path = registry_path or (_DEFAULT_CONFIG_DIR / "parser_registry.json")
        if not path.exists():
            raise RuntimeError(
                f"parser_registry.json을 찾을 수 없습니다: {path}\n"
                "config/parser_registry.json이 올바른 위치에 있는지 확인하세요."
            )
        self.load_registry(path)

    def load_registry(self, registry_path: Path) -> None:
        """JSON 파일에서 파서 레지스트리를 로드한다.

        PARSER_KEY 클래스 변수를 가진 파서들을 자동으로 탐색하므로
        새 파서 추가 시 이 메서드를 수정할 필요가 없다.
        """
        data = json.loads(registry_path.read_text(encoding="utf-8"))
        # PARSER_KEY 기반으로 이 모듈의 파서 클래스를 자동 탐색
        parser_key_map = _build_parser_key_map()

        parsers_def = data.get("parsers", {})
        entries: List[_RegistryEntry] = []

        for _parser_key, parser_def in parsers_def.items():
            keywords = parser_def.get("pollster_names", [])
            if not keywords:
                continue
            class_name = parser_def.get("class", "")
            cls = parser_key_map.get(class_name)
            if cls is None:
                raise RuntimeError(
                    f"parser_registry.json에 등록된 파서 클래스 '{class_name}'를 "
                    f"모듈에서 찾을 수 없습니다. PARSER_KEY = '{class_name}'인 "
                    "클래스가 parser.py에 정의되어 있는지 확인하세요."
                )
            entries.append(_RegistryEntry(
                parser_class=cls,
                pollster_keywords=tuple(keywords),
                priority=10,
            ))

        self._registry = entries

    def parse_pdf(
        self,
        pdf_path: Path,
        pollster_hint: Optional[str] = None,
    ) -> List[QuestionResult]:
        """PDF 파일을 파싱하여 QuestionResult 목록을 반환한다.

        Args:
            pdf_path: 파싱할 PDF 파일 경로
            pollster_hint: 조사기관명 (레지스트리 매칭에 사용)

        Raises:
            UnknownPollsterError: pollster_hint가 레지스트리에 없는 경우
            RuntimeError: pymupdf 미설치 또는 기타 오류
        """
        try:
            import fitz  # PyMuPDF
        except ImportError as exc:
            raise RuntimeError("PDF 파싱을 위해 pymupdf가 필요합니다.") from exc

        pages_data: List[PageData] = []
        doc = fitz.open(pdf_path)
        try:
            for page in doc:
                finder = page.find_tables()
                tables = [_unmerge_table(t, page) for t in finder.tables]
                full_text = page.get_text() or ""
                outside_text = _extract_text_outside_tables(page, finder) if tables else full_text
                pages_data.append((outside_text, tables, full_text))
        finally:
            doc.close()

        parser_class = self._select_parser(pollster_hint)

        # GID 디코딩이 필요한 파서(여론조사꽃 등)는 rawdict 모드로 재추출
        if getattr(parser_class, "NEEDS_GID_DECODE", False):
            font_path = getattr(parser_class, "FONT_PATH", None)
            if font_path and Path(font_path).exists():
                gid_map = _build_gid_to_unicode(Path(font_path))
                pages_data = _extract_pages_with_gid_decode(pdf_path, gid_map)

        return parser_class().parse(pages_data)

    def _select_parser(self, pollster_hint: Optional[str]) -> type:
        """레지스트리에서 적합한 파서 클래스를 선택한다.

        Raises:
            UnknownPollsterError: pollster_hint가 None이거나 매칭되는 파서가 없는 경우
        """
        if pollster_hint:
            for entry in self._registry:
                if any(kw in pollster_hint for kw in entry.pollster_keywords):
                    return entry.parser_class

        registered = sorted({
            kw for e in self._registry for kw in e.pollster_keywords
        })
        hint_repr = repr(pollster_hint) if pollster_hint else "None (pollster_hint 미지정)"
        raise UnknownPollsterError(
            f"조사기관 {hint_repr}에 대한 파서를 찾을 수 없습니다.\n"
            f"등록된 기관 키워드: {registered}\n"
            "parser_registry.json에 해당 기관을 등록하거나 pollster_hint를 확인하세요."
        )


# ── BaseTableParser (Template Method) ─────────────────────────────────────────


class BaseTableParser:
    """table_utils 기반 크로스탭 테이블 파서 기본 클래스.

    Template Method: ``parse()`` 가 공통 알고리즘을 정의하고,
    서브클래스는 설정값과 훅 메서드를 오버라이드한다.
    """

    PARSER_KEY: str = ""

    # ── 서브클래스 설정값 ─────────────────────────────────────────────────────
    TOTAL_MARKERS: tuple = ("전체",)
    META_COLS: int = 4          # 선택지/비율 시작 컬럼
    END_COL: Optional[int] = None  # 비율/선택지 종료 컬럼 (None=끝, -1=마지막 제외)
    TITLE_RE: Optional[re.Pattern] = None
    SUMMARY_PATS: tuple = ()
    HEADER_ROW_INDEX: Optional[int] = None  # None=자동 탐색
    NEEDS_GID_DECODE: bool = False
    FONT_PATH: str = ""

    # ── 공통 알고리즘 ─────────────────────────────────────────────────────────

    def parse(self, pages_data: List[PageData]) -> List[QuestionResult]:
        results: List[QuestionResult] = []
        q_counter = 0

        for page_text, page_tables, full_text in pages_data:
            for table in page_tables:
                result = self._process_table(table, page_text, full_text)
                if result is None:
                    continue
                q_counter += 1
                result.question_number = q_counter
                if not result.question_title:
                    result.question_title = self._extract_title(page_text, full_text)
                results.append(result)

        return results

    def _process_table(
        self,
        table: List[List],
        page_text: str,
        full_text: str,
    ) -> Optional[QuestionResult]:
        if not table or len(table) < 2:
            return None

        found = find_total_row(table, markers=self.TOTAL_MARKERS)
        if found is None:
            return None
        total_idx, total_row = found

        n_completed, n_weighted = self._extract_sample_counts(total_row)
        percentages = self._extract_percentages(total_row, table, page_text, full_text)
        if not percentages or len(percentages) < 2:
            return None

        options = self._extract_options(table, total_idx, len(percentages))
        options, percentages = self._filter_summaries(options, percentages)
        if not percentages:
            return None

        # 길이 맞춤
        while len(options) < len(percentages):
            options.append(f"선택지{len(options) + 1}")
        options = options[: len(percentages)]

        return QuestionResult(
            question_number=0,
            question_title=self._extract_title(page_text, full_text),
            question_text="",
            response_options=options,
            overall_n_completed=n_completed,
            overall_n_weighted=n_weighted,
            overall_percentages=percentages,
        )

    # ── 훅 메서드 (서브클래스에서 오버라이드) ─────────────────────────────────

    def _extract_sample_counts(
        self, total_row: List,
    ) -> tuple:
        n = extract_sample_count(str(total_row[2] or "")) if len(total_row) > 2 else None
        nw = extract_sample_count(str(total_row[3] or "")) if len(total_row) > 3 else None
        return n, nw

    def _extract_percentages(
        self,
        total_row: List,
        table: List[List],
        page_text: str,
        full_text: str,
    ) -> List[float]:
        return extract_percentages_from_cells(
            total_row, start_col=self.META_COLS, end_col=self.END_COL,
        )

    def _extract_options(
        self, table: List[List], total_idx: int, pct_count: int,
    ) -> List[str]:
        if self.HEADER_ROW_INDEX is not None and self.HEADER_ROW_INDEX < len(table):
            return extract_options_from_row(
                table[self.HEADER_ROW_INDEX],
                start_col=self.META_COLS,
                end_col=self.END_COL,
            )[:pct_count]

        # 전체 행 위에서 선택지가 충분한 첫 번째 행
        for row in table[:total_idx]:
            opts = extract_options_from_row(
                row, start_col=self.META_COLS, end_col=self.END_COL,
            )
            if len(opts) >= pct_count:
                return opts[:pct_count]

        if table:
            return extract_options_from_row(
                table[0], start_col=self.META_COLS, end_col=self.END_COL,
            )[:pct_count]
        return []

    def _extract_title(self, page_text: str, full_text: str) -> str:
        if self.TITLE_RE is None:
            return ""
        m = self.TITLE_RE.search(page_text)
        if m and m.lastindex and m.lastindex >= 1:
            title_group = m.group(m.lastindex)
            return re.sub(r"\s+", " ", title_group).strip()
        return ""

    def _filter_summaries(
        self, options: List[str], percentages: List[float],
    ) -> tuple:
        if self.SUMMARY_PATS:
            return filter_summary_columns(
                options, percentages, summary_patterns=self.SUMMARY_PATS,
            )
        return options, percentages


# ── 파서 구현체 ───────────────────────────────────────────────────────────────


class _TableFormatParser(BaseTableParser):
    """조원씨앤아이·메타서치 크로스탭 파서."""

    PARSER_KEY = "_TableFormatParser"
    TOTAL_MARKERS = ("전체",)
    META_COLS = 3
    END_COL = -1  # 마지막 컬럼('계') 제외
    TITLE_RE = re.compile(r"^문?(\d+)[.)]\s+([^\n]+)$", re.MULTILINE)
    SUMMARY_PATS = (re.compile(r"\(합\)|합계|소계"),)

    def _extract_sample_counts(self, total_row: List) -> tuple:
        n = extract_sample_count(str(total_row[2] or "")) if len(total_row) > 2 else None
        nw = extract_sample_count(str(total_row[-1] or "")) if total_row else None
        return n, nw


class _DailyResearchParser(BaseTableParser):
    """데일리리서치 크로스탭 파서 (구 _TextFormatParser 대체).

    PDF 구조:
      - 헤더: row[0][0]='구 분', col4+에 선택지명 (줄바꿈 포함)
      - 전체 행: row[1][0]='전 체', col2=n완료, col3=n가중, col4+=비율
      - 질문 제목: 테이블이 없는 이전 페이지 텍스트의 'N  제목' 패턴
    """

    PARSER_KEY = "_DailyResearchParser"
    TOTAL_MARKERS = ("전체",)
    META_COLS = 4
    TITLE_RE = re.compile(r"(?m)^(\d+)\s{2,}(.+)$")
    SUMMARY_PATS = DEFAULT_SUMMARY_PATTERNS
    def _process_table(self, table, page_text, full_text):
        # 가중값 통계표: 헤더에 '배율' 포함 시 스킵
        if table and table[0]:
            header_text = " ".join(str(c or "") for c in table[0])
            if "배율" in header_text:
                return None
        return super()._process_table(table, page_text, full_text)

    def parse(self, pages_data: List[PageData]) -> List[QuestionResult]:
        results: List[QuestionResult] = []
        q_counter = 0
        pending_title = ""
        seen_titles: set = set()

        for page_text, page_tables, full_text in pages_data:
            if not page_tables:
                t = self._extract_title(page_text, full_text)
                if t:
                    pending_title = t
                continue

            for table in page_tables:
                result = self._process_table(table, page_text, full_text)
                if result is None:
                    continue
                title = result.question_title or pending_title
                # 동일 제목 중복 방지 (멀티페이지 크로스탭)
                if title and title in seen_titles:
                    continue
                if title:
                    seen_titles.add(title)
                q_counter += 1
                result.question_number = q_counter
                if not result.question_title:
                    result.question_title = pending_title
                results.append(result)

        return results


class _KoreanResearchParser(BaseTableParser):
    """한국리서치 크로스탭 파서.

    특이사항:
      - 헤더 row[0][0]='전체', 전체 행 row[N][0]='▣ 전체 ▣'
      - 테이블 추출 시 _unmerge_table로 colspan 해제 → 개별 셀에서 비율 추출
      - 페이지 분할 표 merge 지원 (같은 q_num이 여러 페이지에 걸침)
    """

    PARSER_KEY = "_KoreanResearchParser"
    TOTAL_MARKERS: tuple = ("▣ 전체 ▣",)
    _META_COLS: int = 3

    _TABLE_TITLE_RE = re.compile(r"\[표\s*(\d+)\]\s+(.+)")
    _Q_TEXT_RE = re.compile(r"\[문\s*\d+\]\s+(.+?)(?:\?|？)", re.DOTALL)

    def parse(self, pages_data: List[PageData]) -> List[QuestionResult]:
        result_map: dict = {}

        for page_text, page_tables, _full_text in pages_data:
            title_match = self._TABLE_TITLE_RE.search(page_text)
            if not title_match:
                continue
            q_num = int(title_match.group(1))

            for table in page_tables:
                if not table or len(table) < 3:
                    continue
                # 헤더 식별: row[0][0] = '전체'
                if str(table[0][0] or "").strip() != "전체":
                    continue

                # 전체 행 탐색 (헤더 행 이후부터)
                found = find_total_row(table, markers=self.TOTAL_MARKERS, start_row=1)
                if found is None:
                    continue
                _, total_row = found

                n_completed = extract_sample_count(str(total_row[1] or ""))
                n_weighted = extract_sample_count(str(total_row[2] or ""))

                # colspan 해제 후 개별 셀에서 비율 추출
                pcts = extract_percentages_from_cells(total_row, start_col=self._META_COLS)
                if not pcts:
                    continue

                # 헤더에서 선택지 추출
                options = extract_options_from_row(table[0], start_col=self._META_COLS)
                if not options:
                    continue

                # 요약 컬럼 제거 (계, T1/T2, (1+2) 등)
                options, pcts = filter_summary_columns(options, pcts)
                if not pcts:
                    continue

                min_len = min(len(options), len(pcts))
                page_options = options[:min_len]
                page_pcts = pcts[:min_len]

                # 멀티페이지 크로스탭: 동일 q_num 결과에 선택지·비율 추가
                if q_num in result_map:
                    existing = result_map[q_num]
                    existing.response_options = existing.response_options + page_options
                    existing.overall_percentages = existing.overall_percentages + page_pcts
                    break

                q_title = title_match.group(2).strip()
                q_text_match = self._Q_TEXT_RE.search(page_text)
                q_text = (
                    re.sub(r"\s+", " ", q_text_match.group(1)).strip() + "?"
                    if q_text_match
                    else q_title
                )

                result_map[q_num] = QuestionResult(
                    question_number=q_num,
                    question_title=q_title,
                    question_text=q_text,
                    response_options=page_options,
                    overall_n_completed=n_completed,
                    overall_n_weighted=n_weighted,
                    overall_percentages=page_pcts,
                )
                break  # 페이지당 크로스탭 테이블 하나만

        return list(result_map.values())


class _SignalPulseParser(BaseTableParser):
    """시그널앤펄스 크로스탭 파서.

    두 가지 PDF 버전:
      - 신버전 ([표N]): 텍스트에서 '▣ 전 체 ▣' 비율 추출
      - 구버전 ([QN]): 테이블 '합계' 행에서 비율 추출
    """

    PARSER_KEY = "_SignalPulseParser"

    _PYO_TITLE_RE = re.compile(r"\[표\s*(\d+)\]\s+(.+)")
    _Q_TITLE_RE = re.compile(r"\[Q(\d+)\]\s+\[(.+)\]")
    _SUMMARY_COL_RE = re.compile(r"\(합\)")
    _META_COLS = 4

    def parse(self, pages_data: List[PageData]) -> List[QuestionResult]:
        results: List[QuestionResult] = []
        seen_q_nums: set = set()

        for page_text, page_tables, _full_text in pages_data:
            for table in page_tables:
                result = self._try_parse(table, page_text, seen_q_nums)
                if result is not None:
                    results.append(result)

        return results

    def _try_parse(
        self, table: List, page_text: str, seen_q_nums: set,
    ) -> Optional[QuestionResult]:
        if not table or len(table) < 2 or not table[0]:
            return None
        cell0 = str(table[0][0] or "").strip()

        m_pyo = self._PYO_TITLE_RE.match(cell0)
        if m_pyo:
            return self._parse_pyo(table, page_text, m_pyo, seen_q_nums)

        m_q = self._Q_TITLE_RE.match(cell0)
        if m_q:
            return self._parse_q(table, m_q, seen_q_nums)

        return None

    def _parse_pyo(
        self, table: List, page_text: str, m: re.Match, seen_q_nums: set,
    ) -> Optional[QuestionResult]:
        """신버전: [표N] — 테이블 셀에서 전체 행·비율·선택지 직접 추출."""
        q_num = int(m.group(1))
        if q_num in seen_q_nums:
            return None

        # 전체 행 탐색: '▣ 전 체 ▣' 또는 '▣ 전체 ▣'
        found = find_total_row(table, markers=("전체",))
        if found is None:
            return None
        total_idx, total_row = found

        # 사례수: col2=완료, col3=가중
        n_completed = extract_sample_count(str(total_row[2] or ""))
        n_weighted = extract_sample_count(str(total_row[3] or ""))

        # 비율: col4+ 개별 셀
        raw_pcts = extract_percentages_from_cells(total_row, start_col=self._META_COLS)
        if not raw_pcts:
            return None

        # 선택지: 전체 행 위에서 col4+ 비어있지 않은 첫 행 (보통 row[1])
        options: List[str] = []
        for row in table[1:total_idx]:
            opts = extract_options_from_row(row, start_col=self._META_COLS)
            if len(opts) >= len(raw_pcts):
                options = opts[:len(raw_pcts)]
                break
        if not options:
            options = extract_options_from_row(
                table[1] if len(table) > 1 else table[0],
                start_col=self._META_COLS,
            )[:len(raw_pcts)]

        options, raw_pcts = filter_summary_columns(
            options, raw_pcts, summary_patterns=(self._SUMMARY_COL_RE,),
        )
        min_len = min(len(options), len(raw_pcts))
        if min_len == 0:
            return None

        seen_q_nums.add(q_num)
        return QuestionResult(
            question_number=q_num,
            question_title=m.group(2).strip(),
            question_text="",
            response_options=options[:min_len],
            overall_n_completed=n_completed,
            overall_n_weighted=n_weighted,
            overall_percentages=raw_pcts[:min_len],
        )

    def _parse_q(
        self, table: List, m: re.Match, seen_q_nums: set,
    ) -> Optional[QuestionResult]:
        """구버전: [QN] — 테이블 '합계' 행에서 비율, row[1]에서 선택지."""
        q_num = int(m.group(1))
        if q_num in seen_q_nums:
            return None

        found = find_total_row(table, markers=("합계",), start_row=2)
        if found is None:
            return None
        total_idx, total_row = found

        raw_pcts = extract_percentages_from_cells(total_row, start_col=self._META_COLS)
        if not raw_pcts:
            return None

        # 선택지: 합계 행 위에서 col4+ 비어있지 않은 첫 행 (보통 row[1])
        options: List[str] = []
        for row in table[1:total_idx]:
            opts = extract_options_from_row(row, start_col=self._META_COLS)
            if len(opts) >= len(raw_pcts):
                options = opts[:len(raw_pcts)]
                break
        if not options:
            return None

        n_completed = extract_sample_count(str(total_row[2] or ""))
        n_weighted = extract_sample_count(str(total_row[3] or ""))

        options, raw_pcts = filter_summary_columns(
            options, raw_pcts, summary_patterns=(self._SUMMARY_COL_RE,),
        )
        min_len = min(len(options), len(raw_pcts))
        if min_len == 0:
            return None

        seen_q_nums.add(q_num)
        return QuestionResult(
            question_number=q_num,
            question_title=m.group(2).strip(),
            question_text="",
            response_options=options[:min_len],
            overall_n_completed=n_completed,
            overall_n_weighted=n_weighted,
            overall_percentages=raw_pcts[:min_len],
        )


class _EmbrainPublicParser(BaseTableParser):
    """엠브레인퍼블릭 크로스탭 파서."""

    PARSER_KEY = "_EmbrainPublicParser"
    TOTAL_MARKERS = ("전체",)  # '■ 전체 ■' → normalize로 매칭
    META_COLS = 4
    TITLE_RE = re.compile(r"\[표(\d+)\]\s+(.+)")
    SUMMARY_PATS = (re.compile(r"【.+】"),)
    HEADER_ROW_INDEX = 1  # 선택지가 row 1에 있음

    def _extract_sample_counts(self, total_row: List) -> tuple:
        try:
            n = int(str(total_row[2] or "").replace(",", ""))
            nw = int(str(total_row[3] or "").replace(",", ""))
            return n, nw
        except (ValueError, IndexError):
            return None, None


class _RealMeterParser(BaseTableParser):
    """리얼미터 크로스탭 파서.

    특이사항:
      - 질문 테이블 식별: header[0][0]에 '구' 포함
      - 전체 행의 col2에 '(N완료) (N가중)' 두 값이 함께 기재됨
      - col4+에 선택지별 비율이 개별 셀로 저장
      - seen_q_nums로 중복 페이지 방지
    """

    PARSER_KEY = "_RealMeterParser"

    _Q_SECTION_RE = re.compile(r"(?m)^(\d+)\.\s+(.+)$")
    _Q_TEXT_RE = re.compile(r"Q\d+\.\s+(.+?)(?:\?|？)", re.DOTALL)
    _N_PAIR_RE = re.compile(r"\((\d[\d,]*)\)")
    _HEADER_META_COLS = 4
    _SUMMARY_OPT_RE = re.compile(r"[①②③④⑤⑥⑦⑧⑨⑩]\s*\+\s*[①②③④⑤⑥⑦⑧⑨⑩]")

    def parse(self, pages_data: List[PageData]) -> List[QuestionResult]:
        results: List[QuestionResult] = []
        seen_q_nums: set = set()

        for page_text, page_tables, _full_text in pages_data:
            q_section_match = self._Q_SECTION_RE.search(page_text)
            if not q_section_match:
                continue
            q_num = int(q_section_match.group(1))
            if q_num in seen_q_nums:
                continue

            result = self._extract_from_tables(page_tables, q_section_match, page_text)
            if result is None:
                continue

            seen_q_nums.add(q_num)
            result.question_number = q_num
            results.append(result)

        return results

    def _extract_from_tables(
        self,
        page_tables: List,
        q_section_match: re.Match,
        page_text: str,
    ) -> Optional[QuestionResult]:
        for table in page_tables:
            if not table or len(table) < 2:
                continue
            if "구" not in str(table[0][0] or ""):
                continue

            found = find_total_row(table, markers=("전체",))
            if found is None:
                continue
            _, total_row = found

            if len(total_row) < self._HEADER_META_COLS + 1:
                continue

            # col2: '(N완료) (N가중)' 두 값이 한 셀에 있음
            n_vals = self._N_PAIR_RE.findall(str(total_row[2] or ""))
            if len(n_vals) < 2:
                continue
            n_completed = int(n_vals[0].replace(",", ""))
            n_weighted = int(n_vals[1].replace(",", ""))

            options = extract_options_from_row(table[0], start_col=self._HEADER_META_COLS)
            if not options:
                continue

            percentages = extract_percentages_from_cells(
                total_row, start_col=self._HEADER_META_COLS,
            )
            if not percentages:
                continue

            options, percentages = filter_summary_columns(
                options, percentages, summary_patterns=(self._SUMMARY_OPT_RE,),
            )
            min_len = min(len(options), len(percentages))
            if min_len == 0:
                continue

            q_title = q_section_match.group(2).strip()
            q_text_match = self._Q_TEXT_RE.search(page_text)
            q_text = (
                re.sub(r"\s+", " ", q_text_match.group(1)).strip() + "?"
                if q_text_match
                else q_title
            )

            return QuestionResult(
                question_number=0,
                question_title=q_title,
                question_text=q_text,
                response_options=options[:min_len],
                overall_n_completed=n_completed,
                overall_n_weighted=n_weighted,
                overall_percentages=percentages[:min_len],
            )
        return None


class _FlowerResearchParser(BaseTableParser):
    """여론조사꽃 크로스탭 파서.

    특이사항:
      - NotoSansKR Identity-H 인코딩 → GID 디코딩 필요
      - 비율이 col3 하나의 셀에 공백으로 뭉쳐 있음
      - seen_q_nums로 중복 방지
    """

    PARSER_KEY = "_FlowerResearchParser"
    NEEDS_GID_DECODE: bool = True
    FONT_PATH: str = str(
        Path(__file__).resolve().parents[4]
        / "data" / "resources" / "fonts" / "NotoSansCJKkr-Medium.otf"
    )
    TOTAL_MARKERS = ("전체",)
    META_COLS = 3
    END_COL = -1  # 마지막 컬럼('가중값적용사례수') 제외
    SUMMARY_PATS = (
        re.compile(r"[①②③④⑤⑥⑦⑧⑨⑩]\s*\+\s*[①②③④⑤⑥⑦⑧⑨⑩]"),
    )

    _Q_SECTION_RE = re.compile(r"(?m)^(\d+)\.\s+(.+)$")
    _Q_TEXT_RE = re.compile(r"Q[\s\n]+(.+?)(?:\?|？)", re.DOTALL)

    def parse(self, pages_data: List[PageData]) -> List[QuestionResult]:
        results: List[QuestionResult] = []
        seen_q_nums: set = set()

        for page_text, page_tables, _full_text in pages_data:
            if not page_tables:
                continue
            tbl = page_tables[0]
            if not tbl or len(tbl) < 2:
                continue

            found = find_total_row(tbl, markers=self.TOTAL_MARKERS)
            if found is None:
                continue
            _, total_row = found

            # 선택지: 헤더 row col 3 ~ -1
            options = extract_options_from_row(tbl[0], start_col=3, end_col=-1)
            if not options:
                continue

            n_completed = extract_sample_count(str(total_row[2] or ""))
            n_weighted = extract_sample_count(str(total_row[-1] or ""))

            # 비율: col3에 뭉침
            percentages = extract_percentages_from_bunched_cell(str(total_row[3] or ""))
            if not percentages:
                continue

            options, percentages = filter_summary_columns(
                options, percentages, summary_patterns=self.SUMMARY_PATS,
            )
            min_len = min(len(options), len(percentages))
            if min_len == 0:
                continue
            options = options[:min_len]
            percentages = percentages[:min_len]

            q_section = self._Q_SECTION_RE.search(page_text)
            if q_section:
                q_num = int(q_section.group(1))
                q_title = q_section.group(2).strip()
            else:
                q_num = len(results) + 1
                q_title = ""

            if q_num in seen_q_nums:
                continue
            seen_q_nums.add(q_num)

            q_text_m = self._Q_TEXT_RE.search(page_text)
            q_text = (
                re.sub(r"\s+", " ", q_text_m.group(1)).strip() + "?"
                if q_text_m
                else q_title
            )

            results.append(QuestionResult(
                question_number=q_num,
                question_title=q_title,
                question_text=q_text,
                response_options=options,
                overall_n_completed=n_completed,
                overall_n_weighted=n_weighted,
                overall_percentages=percentages,
            ))

        for i, r in enumerate(results):
            r.question_number = i + 1
        return results


class _WinjiKoreaParser(BaseTableParser):
    """윈지코리아컨설팅 크로스탭 파서.

    두 가지 포맷 자동 감지:
      - 포맷 A (개별 셀 비율): col4+에 float, 8+열
      - 포맷 B (뭉침 비율): col3에 공백 구분 문자열, 5열
    """

    PARSER_KEY = "_WinjiKoreaParser"

    _TABLE_HEADER_RE = re.compile(r"표\s*\d+(?:-\d+)?\s*\n([^\n]+)", re.MULTILINE)

    def parse(self, pages_data: List[PageData]) -> List[QuestionResult]:
        results: List[QuestionResult] = []
        q_counter = 0

        for _page_text, page_tables, page_full in pages_data:
            page_title = ""
            for m in self._TABLE_HEADER_RE.finditer(page_full):
                page_title = re.sub(r"\s+", " ", m.group(1)).strip()

            for table in page_tables:
                result = self._parse_table_dual(table)
                if result is None:
                    continue
                q_counter += 1
                result.question_number = q_counter
                result.question_title = page_title
                results.append(result)

        return results

    @staticmethod
    def _parse_table_dual(table: List[List]) -> Optional[QuestionResult]:
        if not table or len(table) < 2:
            return None

        found = find_total_row(table, markers=("전체",))
        if found is None:
            return None
        total_row_idx, total_row = found

        if len(total_row) < 3:
            return None

        # 포맷 A: col4+ 개별 float
        col2_is_sample = extract_sample_count(str(total_row[2] or "")) is not None
        if len(total_row) >= 5 and col2_is_sample:
            pcts_a = extract_percentages_from_cells(total_row, start_col=4)
            if len(pcts_a) >= 2:
                n_c = extract_sample_count(str(total_row[2] or ""))
                n_w = extract_sample_count(str(total_row[3] or ""))

                header_row: Optional[List] = None
                for row in table[:total_row_idx]:
                    non_empty = [
                        c for c in row[4:]
                        if str(c or "").strip() and str(c or "").lower() != "none"
                    ]
                    if len(non_empty) >= len(pcts_a):
                        header_row = row
                        break
                if header_row is None and total_row_idx > 0:
                    header_row = table[0]

                options: List[str] = []
                if header_row is not None:
                    options = extract_options_from_row(header_row, start_col=4)
                    options = options[: len(pcts_a)]
                while len(options) < len(pcts_a):
                    options.append(f"선택지{len(options) + 1}")

                return QuestionResult(
                    question_number=0, question_title="", question_text="",
                    response_options=options,
                    overall_n_completed=n_c, overall_n_weighted=n_w,
                    overall_percentages=pcts_a,
                )

        # 포맷 B: col3 뭉침
        pct_cell = str(total_row[3] if len(total_row) > 3 else "")
        pcts_b = extract_percentages_from_bunched_cell(pct_cell)
        if len(pcts_b) < 2:
            return None

        n_c_b = extract_sample_count(str(total_row[2] or ""))
        n_w_b = extract_sample_count(str(total_row[-1] or "")) if len(total_row) > 4 else None

        options_b: List[str] = []
        if table[0] and len(table[0]) > 3:
            raw = re.sub(r"[\n\x00]+", "\n", str(table[0][3] or "")).split("\n")
            options_b = [o.strip() for o in raw if o.strip() and o.lower() != "none"]
            options_b = options_b[: len(pcts_b)]
        while len(options_b) < len(pcts_b):
            options_b.append(f"선택지{len(options_b) + 1}")

        return QuestionResult(
            question_number=0, question_title="", question_text="",
            response_options=options_b,
            overall_n_completed=n_c_b, overall_n_weighted=n_w_b,
            overall_percentages=pcts_b,
        )


class _HangilResearchParser(BaseTableParser):
    """한길리서치 크로스탭 파서.

    특이사항:
      - 질문 결과 테이블 식별: header[0][0]=='' AND header[0][2]=='합계'
      - 전체 행: col0=='전체', n_completed=col2, n_weighted=col3
      - col4+에 선택지별 비율이 개별 셀로 저장
      - ①+②, ③+④ 등 소계 열은 DEFAULT_SUMMARY_PATTERNS로 필터
      - 질문 번호/텍스트: page_text의 '문N)' 패턴에서 추출
    """

    PARSER_KEY = "_HangilResearchParser"

    _Q_RE = re.compile(r"문\s*(\d+)\s*\)\s*(.+?)(?:\?|？)", re.DOTALL)
    _META_COLS = 4

    def parse(self, pages_data: List[PageData]) -> List[QuestionResult]:
        results: List[QuestionResult] = []

        for page_text, page_tables, _full_text in pages_data:
            for table in page_tables:
                result = self._parse_table(table, page_text, len(results) + 1)
                if result is not None:
                    results.append(result)

        return results

    def _parse_table(
        self, table: List, page_text: str, fallback_q_num: int,
    ) -> Optional[QuestionResult]:
        if not table or not table[0] or len(table[0]) < self._META_COLS + 1:
            return None

        # 질문 결과 테이블 식별: col0 빈 셀, col2 == '합계'
        if str(table[0][0] or "").strip() != "":
            return None
        if str(table[0][2] or "").strip() != "합계":
            return None

        found = find_total_row(table, markers=("전체",))
        if found is None:
            return None
        _, total_row = found

        if len(total_row) < self._META_COLS + 1:
            return None

        n_completed = extract_sample_count(str(total_row[2] or ""))
        n_weighted = extract_sample_count(str(total_row[3] or ""))

        options = extract_options_from_row(table[0], start_col=self._META_COLS)
        if not options:
            return None

        percentages = extract_percentages_from_cells(total_row, start_col=self._META_COLS)
        if not percentages:
            return None

        options, percentages = filter_summary_columns(
            options, percentages, summary_patterns=DEFAULT_SUMMARY_PATTERNS,
        )
        min_len = min(len(options), len(percentages))
        if min_len == 0:
            return None

        q_match = self._Q_RE.search(page_text)
        if q_match:
            q_num = int(q_match.group(1))
            q_text = re.sub(r"\s+", " ", q_match.group(2)).strip() + "?"
        else:
            q_num = fallback_q_num
            q_text = ""

        return QuestionResult(
            question_number=q_num,
            question_title=q_text,
            question_text=q_text,
            response_options=options[:min_len],
            overall_n_completed=n_completed,
            overall_n_weighted=n_weighted,
            overall_percentages=percentages[:min_len],
        )
