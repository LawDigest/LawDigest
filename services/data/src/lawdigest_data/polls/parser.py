"""여론조사 결과표 PDF 파서."""

from __future__ import annotations

import importlib
import inspect
import json
import logging
import re
import time
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

_logger = logging.getLogger(__name__)

# config/ 디렉터리 기본 경로
# parser.py: .../services/data/src/lawdigest_data/polls/parser.py
# parents[3] = .../services/data  →  config/
_DEFAULT_CONFIG_DIR = Path(__file__).resolve().parents[3] / "config"

# PageData: (테이블_외부_텍스트, 테이블_목록, 전체_텍스트) 타입 alias
PageData = Tuple[str, List, str]


class UnknownPollsterError(ValueError):
    """등록된 파서가 없는 조사기관에 대해 발생하는 예외."""


def _should_scan_tables_for_page(parser_class: type, full_text: str) -> bool:
    """파서별 힌트에 따라 현재 페이지에서 테이블 탐색이 필요한지 판단한다."""
    page_filter_re = getattr(parser_class, "QUESTION_PAGE_RE", None)
    if page_filter_re is None:
        return True
    return bool(page_filter_re.search(full_text or ""))


def _extract_page_data(
    page: "fitz.Page",  # type: ignore[name-defined]  # noqa: F821
    parser_class: type,
) -> PageData:
    """단일 페이지에서 (outside_text, tables, full_text)를 안전하게 추출한다."""
    page_num = getattr(page, "number", "?")

    t0 = time.monotonic()
    full_text = page.get_text() or ""
    _logger.debug("get_text: %.3fs (page %s)", time.monotonic() - t0, page_num)

    if not _should_scan_tables_for_page(parser_class, full_text):
        return full_text, [], full_text

    t1 = time.monotonic()
    finder = page.find_tables()
    _logger.debug("find_tables: %.3fs (page %s)", time.monotonic() - t1, page_num)

    finder_tables = getattr(finder, "tables", None) if finder is not None else None

    t2 = time.monotonic()
    tables = [_unmerge_table(t, page) for t in finder_tables] if finder_tables else []
    _logger.debug("unmerge_tables (%d): %.3fs (page %s)", len(tables), time.monotonic() - t2, page_num)

    t3 = time.monotonic()
    outside_text = _extract_text_outside_tables(page, finder) if tables else full_text
    _logger.debug("extract_outside_text: %.3fs (page %s)", time.monotonic() - t3, page_num)

    return outside_text, tables, full_text


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
        raise RuntimeError(
            "GID 디코딩을 위해 fonttools가 필요합니다: pip install fonttools"
        ) from exc

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

    words = [w for w in page.get_text("words") if not _in_table(w[0], w[1], w[2], w[3])]
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
    has_merge = any(None in row for row in extracted)
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
                w
                for w in all_words
                if w[0] >= x0 - 2
                and w[2] <= x1 + 2
                and w[1] >= y0 - 3
                and w[3] <= y1 + 3
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
            tables = [
                _decode_table(_unmerge_table(t, page), gid_map) for t in finder.tables
            ]
            full_text = _decode_page_text(page, gid_map)
            outside_text = _decode_text_with_gid(
                (
                    _extract_text_outside_tables(page, finder)
                    if finder.tables
                    else page.get_text()
                ),
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
        self._gid_cache: Dict[str, Dict[int, int]] = {}  # font_path → gid_map 캐시
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
            entries.append(
                _RegistryEntry(
                    parser_class=cls,
                    pollster_keywords=tuple(keywords),
                    priority=10,
                )
            )

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

        parser_class = self._select_parser(pollster_hint)

        # GID 디코딩이 필요한 파서(여론조사꽃 등)는 일반 파싱 없이 rawdict 모드로 직접 추출
        if getattr(parser_class, "NEEDS_GID_DECODE", False):
            font_path = getattr(parser_class, "FONT_PATH", None)
            if font_path and Path(font_path).exists():
                font_path_str = str(font_path)
                if font_path_str not in self._gid_cache:
                    self._gid_cache[font_path_str] = _build_gid_to_unicode(Path(font_path))
                gid_map = self._gid_cache[font_path_str]
                pages_data = _extract_pages_with_gid_decode(pdf_path, gid_map)
                return parser_class().parse(pages_data)

        pages_data: List[PageData] = []
        doc = fitz.open(pdf_path)
        try:
            for page in doc:
                outside_text, tables, full_text = _extract_page_data(page, parser_class)

                # NEEDS_FITZ_WORDS: 테이블이 없는 페이지에 fitz words를 page_tables[0]으로 전달
                if getattr(parser_class, "NEEDS_FITZ_WORDS", False) and not tables:
                    fitz_words = page.get_text("words")
                    if fitz_words:
                        tables = [fitz_words]

                pages_data.append((outside_text, tables, full_text))
        finally:
            doc.close()

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

        registered = sorted({kw for e in self._registry for kw in e.pollster_keywords})
        hint_repr = (
            repr(pollster_hint) if pollster_hint else "None (pollster_hint 미지정)"
        )
        raise UnknownPollsterError(
            f"조사기관 {hint_repr}에 대한 파서를 찾을 수 없습니다.\n"
            f"등록된 기관 키워드: {registered}\n"
            "parser_registry.json에 해당 기관을 등록하거나 pollster_hint를 확인하세요."
        )

    def get_registered_pollster_names(self) -> List[str]:
        """등록된 모든 기관 키워드 목록을 반환한다."""
        names: List[str] = []
        for entry in self._registry:
            names.extend(entry.pollster_keywords)
        return names


# ── BaseTableParser (Template Method) ─────────────────────────────────────────


class BaseTableParser:
    """table_utils 기반 크로스탭 테이블 파서 기본 클래스.

    Template Method: ``parse()`` 가 공통 알고리즘을 정의하고,
    서브클래스는 설정값과 훅 메서드를 오버라이드한다.
    """

    PARSER_KEY: str = ""

    # ── 서브클래스 설정값 ─────────────────────────────────────────────────────
    TOTAL_MARKERS: tuple = ("전체",)
    META_COLS: int = 4  # 선택지/비율 시작 컬럼
    END_COL: Optional[int] = None  # 비율/선택지 종료 컬럼 (None=끝, -1=마지막 제외)
    TITLE_RE: Optional[re.Pattern] = None
    SUMMARY_PATS: tuple = ()
    HEADER_ROW_INDEX: Optional[int] = None  # None=자동 탐색
    NEEDS_GID_DECODE: bool = False
    FONT_PATH: str = ""
    # 비율 추출 전략: "cell" | "bunched" | "auto"
    # "cell"    : extract_percentages_from_cells() 사용 (기본값)
    # "bunched" : extract_percentages_from_bunched_cell() 사용 (셀 하나에 비율 뭉침)
    # "auto"    : 셀에 단일 비율이면 cell, 아니면 bunched 자동 판단
    RATIO_MODE: str = "cell"

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
        self,
        total_row: List,
    ) -> tuple:
        n = (
            extract_sample_count(str(total_row[2] or ""))
            if len(total_row) > 2
            else None
        )
        nw = (
            extract_sample_count(str(total_row[3] or ""))
            if len(total_row) > 3
            else None
        )
        return n, nw

    def _extract_percentages(
        self,
        total_row: List,
        table: List[List],
        page_text: str,
        full_text: str,
    ) -> List[float]:
        mode = self.RATIO_MODE
        if mode == "bunched":
            # 비율이 META_COLS 위치 셀 하나에 뭉쳐 있는 경우
            bunched_cell = str(total_row[self.META_COLS] if len(total_row) > self.META_COLS else "")
            pcts = extract_percentages_from_bunched_cell(bunched_cell)
            if pcts:
                return pcts
            # fallback: cell 모드로 재시도
            return extract_percentages_from_cells(
                total_row,
                start_col=self.META_COLS,
                end_col=self.END_COL,
            )
        if mode == "auto":
            # 먼저 cell 모드로 시도; 결과가 1개 이하면 bunched 모드로 재시도
            pcts = extract_percentages_from_cells(
                total_row,
                start_col=self.META_COLS,
                end_col=self.END_COL,
            )
            if len(pcts) > 1:
                return pcts
            bunched_cell = str(total_row[self.META_COLS] if len(total_row) > self.META_COLS else "")
            return extract_percentages_from_bunched_cell(bunched_cell) or pcts
        # 기본값: "cell"
        return extract_percentages_from_cells(
            total_row,
            start_col=self.META_COLS,
            end_col=self.END_COL,
        )

    def _extract_options(
        self,
        table: List[List],
        total_idx: int,
        pct_count: int,
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
                row,
                start_col=self.META_COLS,
                end_col=self.END_COL,
            )
            if len(opts) >= pct_count:
                return opts[:pct_count]

        if table:
            return extract_options_from_row(
                table[0],
                start_col=self.META_COLS,
                end_col=self.END_COL,
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
        self,
        options: List[str],
        percentages: List[float],
    ) -> tuple:
        if self.SUMMARY_PATS:
            return filter_summary_columns(
                options,
                percentages,
                summary_patterns=self.SUMMARY_PATS,
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
    QUESTION_PAGE_RE = TITLE_RE
    SUMMARY_PATS = (re.compile(r"\(합\)|합계|소계"),)

    def _extract_sample_counts(self, total_row: List) -> tuple:
        n = (
            extract_sample_count(str(total_row[2] or ""))
            if len(total_row) > 2
            else None
        )
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
                pcts = extract_percentages_from_cells(
                    total_row, start_col=self._META_COLS
                )
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
                    existing.overall_percentages = (
                        existing.overall_percentages + page_pcts
                    )
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
        self,
        table: List,
        page_text: str,
        seen_q_nums: set,
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
        self,
        table: List,
        page_text: str,
        m: re.Match,
        seen_q_nums: set,
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
                options = opts[: len(raw_pcts)]
                break
        if not options:
            options = extract_options_from_row(
                table[1] if len(table) > 1 else table[0],
                start_col=self._META_COLS,
            )[: len(raw_pcts)]

        options, raw_pcts = filter_summary_columns(
            options,
            raw_pcts,
            summary_patterns=(self._SUMMARY_COL_RE,),
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
        self,
        table: List,
        m: re.Match,
        seen_q_nums: set,
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
                options = opts[: len(raw_pcts)]
                break
        if not options:
            return None

        n_completed = extract_sample_count(str(total_row[2] or ""))
        n_weighted = extract_sample_count(str(total_row[3] or ""))

        options, raw_pcts = filter_summary_columns(
            options,
            raw_pcts,
            summary_patterns=(self._SUMMARY_COL_RE,),
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

    _Q_SECTION_RE = re.compile(r"(?m)^[^\S\n\u2013-]*[\u2013-]?\s*(\d+)\.\s+(.+)$")
    _Q_TEXT_RE = re.compile(r"Q\d+\.\s+(.+?)(?:\?|？)", re.DOTALL)
    _N_PAIR_RE = re.compile(r"\((\d[\d,]*)\)")
    _HEADER_META_COLS = 4
    _SUMMARY_OPT_RE = re.compile(r"[①②③④⑤⑥⑦⑧⑨⑩]\s*\+\s*[①②③④⑤⑥⑦⑧⑨⑩]")
    QUESTION_PAGE_RE = re.compile(r"(?ms)^\d+\.\s+.+?Q\d+\.")

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

            options = extract_options_from_row(
                table[0], start_col=self._HEADER_META_COLS
            )
            if not options:
                continue

            percentages = extract_percentages_from_cells(
                total_row,
                start_col=self._HEADER_META_COLS,
            )
            if not percentages:
                continue

            options, percentages = filter_summary_columns(
                options,
                percentages,
                summary_patterns=(self._SUMMARY_OPT_RE,),
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
        / "data"
        / "resources"
        / "fonts"
        / "NotoSansCJKkr-Medium.otf"
    )
    TOTAL_MARKERS = ("전체",)
    META_COLS = 3
    END_COL = -1  # 마지막 컬럼('가중값적용사례수') 제외
    SUMMARY_PATS = (re.compile(r"[①②③④⑤⑥⑦⑧⑨⑩]\s*\+\s*[①②③④⑤⑥⑦⑧⑨⑩]"),)

    _Q_SECTION_RE = re.compile(r"(?m)^(\d+)\.\s+(.+)$")
    _Q_TEXT_RE = re.compile(r"Q[\s\n]+(.+?)(?:\?|？)", re.DOTALL)

    @staticmethod
    def _find_total_row_fallback(table: List[List]) -> Optional[Tuple[int, List]]:
        """'전체' 라벨이 깨진 경우 첫 데이터 행을 전체행으로 간주한다."""
        for i, row in enumerate(table[1:], start=1):
            if not row or len(row) < 5:
                continue
            if str(row[1] or "").strip():
                continue
            if extract_sample_count(str(row[2] or "")) is None:
                continue
            if extract_sample_count(str(row[-1] or "")) is None:
                continue
            if len(extract_percentages_from_cells(row, start_col=3, end_col=-1)) >= 2:
                return i, row
        return None

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
                found = self._find_total_row_fallback(tbl)
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
            if len(percentages) < 2:
                percentages = extract_percentages_from_cells(
                    total_row, start_col=3, end_col=-1
                )
            if not percentages:
                continue

            options, percentages = filter_summary_columns(
                options,
                percentages,
                summary_patterns=self.SUMMARY_PATS,
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
                q_title = f"Q{q_num}"

            if q_num in seen_q_nums:
                continue
            seen_q_nums.add(q_num)

            q_text_m = self._Q_TEXT_RE.search(page_text)
            q_text = (
                re.sub(r"\s+", " ", q_text_m.group(1)).strip() + "?"
                if q_text_m
                else q_title
            )

            results.append(
                QuestionResult(
                    question_number=q_num,
                    question_title=q_title,
                    question_text=q_text,
                    response_options=options,
                    overall_n_completed=n_completed,
                    overall_n_weighted=n_weighted,
                    overall_percentages=percentages,
                )
            )

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
    QUESTION_PAGE_RE = re.compile(r"표\s*\d+")

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
                        c
                        for c in row[4:]
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
                    question_number=0,
                    question_title="",
                    question_text="",
                    response_options=options,
                    overall_n_completed=n_c,
                    overall_n_weighted=n_w,
                    overall_percentages=pcts_a,
                )

        # 포맷 B: col3 뭉침
        pct_cell = str(total_row[3] if len(total_row) > 3 else "")
        pcts_b = extract_percentages_from_bunched_cell(pct_cell)
        if len(pcts_b) < 2:
            return None

        n_c_b = extract_sample_count(str(total_row[2] or ""))
        n_w_b = (
            extract_sample_count(str(total_row[-1] or ""))
            if len(total_row) > 4
            else None
        )

        options_b: List[str] = []
        if table[0] and len(table[0]) > 3:
            raw = re.sub(r"[\n\x00]+", "\n", str(table[0][3] or "")).split("\n")
            options_b = [o.strip() for o in raw if o.strip() and o.lower() != "none"]
            options_b = options_b[: len(pcts_b)]
        while len(options_b) < len(pcts_b):
            options_b.append(f"선택지{len(options_b) + 1}")

        return QuestionResult(
            question_number=0,
            question_title="",
            question_text="",
            response_options=options_b,
            overall_n_completed=n_c_b,
            overall_n_weighted=n_w_b,
            overall_percentages=pcts_b,
        )


class _ResearchAndResearchParser(BaseTableParser):
    """리서치앤리서치 크로스탭 파서."""

    PARSER_KEY = "_ResearchAndResearchParser"
    TOTAL_MARKERS = ("전체",)
    META_COLS = 4
    END_COL = -1  # 마지막 '계' 열 제외
    SUMMARY_PATS = DEFAULT_SUMMARY_PATTERNS + (
        re.compile(r"^\*.+\*$"),
        re.compile(r"^긍정$|^부정$|^모름$"),
        re.compile(r"^없음\s*/\s*모름$|^없음모름$"),
    )
    QUESTION_PAGE_RE = re.compile(r"표\s+.+?\n(?:\d+[A-Z]?)\s*\n【", re.DOTALL)
    _TITLE_RE = re.compile(r"표\s+(.+?)\s+(\d+[A-Z]?)\s+【", re.DOTALL)

    def _extract_title(self, page_text: str, full_text: str) -> str:
        for text in (full_text, page_text):
            normalized = (text or "").replace("\xa0", " ")
            m = self._TITLE_RE.search(normalized)
            if m:
                return re.sub(r"\s+", " ", m.group(1)).strip()
        return ""


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
        self,
        table: List,
        page_text: str,
        fallback_q_num: int,
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

        percentages = extract_percentages_from_cells(
            total_row, start_col=self._META_COLS
        )
        if not percentages:
            return None

        options, percentages = filter_summary_columns(
            options,
            percentages,
            summary_patterns=DEFAULT_SUMMARY_PATTERNS,
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


class _NextResearchParser(BaseTableParser):
    """넥스트리서치 크로스탭 파서.

    포맷 특성:
      - 페이지당 테이블 1개, 각 테이블이 하나의 질문을 담음
      - 전체 행 마커: row[0] == '[전체]'
      - 사례수: col2=조사완료, col3=가중값적용
      - 비율: col4+ 개별 셀
      - 질문 마커: 페이지 텍스트의 '■ 표N. 제목' 패턴
    """

    PARSER_KEY = "_NextResearchParser"

    _TABLE_TITLE_RE = re.compile(
        r"■\s*(표\s*\d+)\s*[.\s]\s*(.+?)(?:\n|$)",
    )
    _META_COLS = 4  # col0=구분, col1=None, col2=n완료, col3=n가중

    def parse(self, pages_data: List[PageData]) -> List[QuestionResult]:
        results: List[QuestionResult] = []
        seen_q_nums: set = set()

        for page_text, page_tables, _full_text in pages_data:
            title_m = self._TABLE_TITLE_RE.search(page_text)
            # '■ 표N.' 마커가 없는 페이지는 응답자 특성 등 비결과 페이지 — 건너뜀
            if title_m is None:
                continue

            for table in page_tables:
                result = self._parse_table(
                    table,
                    title_m,
                    len(results) + 1,
                    seen_q_nums,
                )
                if result is not None:
                    results.append(result)

        return results

    def _parse_table(
        self,
        table: List,
        title_m: Optional[re.Match],
        fallback_q_num: int,
        seen_q_nums: set,
    ) -> Optional[QuestionResult]:
        if not table or len(table) < 2:
            return None

        # 전체 행 탐색: col0 == '[전체]'
        found = find_total_row(table, markers=("[전체]",))
        if found is None:
            return None
        _, total_row = found

        if len(total_row) < self._META_COLS + 1:
            return None

        n_completed = extract_sample_count(str(total_row[2] or ""))
        n_weighted = extract_sample_count(str(total_row[3] or ""))

        percentages = extract_percentages_from_cells(
            total_row, start_col=self._META_COLS
        )
        if not percentages:
            return None

        options = extract_options_from_row(table[0], start_col=self._META_COLS)
        options = options[: len(percentages)]

        options, percentages = filter_summary_columns(
            options,
            percentages,
            summary_patterns=DEFAULT_SUMMARY_PATTERNS,
        )
        min_len = min(len(options), len(percentages))
        if min_len == 0:
            return None

        if title_m:
            q_num_str = re.sub(r"[^\d]", "", title_m.group(1))
            q_num = int(q_num_str) if q_num_str else fallback_q_num
            q_title = re.sub(r"\s+", " ", title_m.group(2)).strip()
        else:
            q_num = fallback_q_num
            q_title = ""

        if q_num in seen_q_nums:
            return None
        seen_q_nums.add(q_num)

        return QuestionResult(
            question_number=q_num,
            question_title=q_title,
            question_text=q_title,
            response_options=options[:min_len],
            overall_n_completed=n_completed,
            overall_n_weighted=n_weighted,
            overall_percentages=percentages[:min_len],
        )


class _STIParser(BaseTableParser):
    """에스티아이(STI) 크로스탭 파서.

    포맷 특성:
      - 질문 마커: 'QN. 질문제목' (페이지 텍스트)
      - 전체 행 마커: '전 체' (공백 포함)
      - 사례수: col2=조사완료, col3=가중값적용
      - 비율: col4+ 개별 셀
      - 멀티페이지: 한 질문이 2페이지에 걸치며, Q마커가 있는 첫 페이지에서만 추출
      - 헤더 행 구조: row[0]에 선택지, row[1]에 '조사완료/가중값적용' 레이블
        (일부 질문은 row[2]에 ①②③... 번호 행이 추가됨)
    """

    PARSER_KEY = "_STIParser"

    _Q_RE = re.compile(r"\bQ\s*(\d+)\s*[.。]\s+(.+?)(?:\n|$)")
    _TOTAL_MARKER = re.compile(r"^전\s+체$")
    _META_COLS = 4  # col0=구분, col1=None, col2=n완료, col3=n가중

    def parse(self, pages_data: List[PageData]) -> List[QuestionResult]:
        results: List[QuestionResult] = []
        seen_q_nums: set = set()

        for page_text, page_tables, _full_text in pages_data:
            q_m = self._Q_RE.search(page_text)
            if q_m is None:
                # Q마커 없는 페이지는 멀티페이지 연속 — 건너뜀
                continue

            for table in page_tables:
                result = self._parse_table(
                    table,
                    q_m,
                    len(results) + 1,
                    seen_q_nums,
                )
                if result is not None:
                    results.append(result)

        return results

    def _parse_table(
        self,
        table: List,
        q_m: re.Match,
        fallback_q_num: int,
        seen_q_nums: set,
    ) -> Optional[QuestionResult]:
        if not table or len(table) < 2:
            return None

        # 전체 행 탐색: '전 체' (공백 포함)
        found = find_total_row(table, markers=("전 체", "전체"))
        if found is None:
            return None
        total_idx, total_row = found

        if len(total_row) < self._META_COLS + 1:
            return None

        n_completed = extract_sample_count(str(total_row[2] or ""))
        n_weighted = extract_sample_count(str(total_row[3] or ""))

        percentages = extract_percentages_from_cells(
            total_row, start_col=self._META_COLS
        )
        if not percentages:
            return None

        # 선택지: 전체 행 위에서 col4+ 비어있지 않은 첫 행 찾기
        options: List[str] = []
        summary_row: Optional[List] = None
        _CIRC_PLUS_SCAN = re.compile(r"[①②③④⑤⑥⑦⑧⑨⑩]\s*\+")
        for row in table[:total_idx]:
            # ①+② 소계 표시 행 항상 검사 (break 이전에)
            cells = [str(c or "") for c in row[self._META_COLS :]]
            if any(_CIRC_PLUS_SCAN.search(c) for c in cells):
                summary_row = row
            if not options:
                opts = extract_options_from_row(row, start_col=self._META_COLS)
                if len(opts) >= len(percentages):
                    options = opts[: len(percentages)]
        if not options:
            options = extract_options_from_row(table[0], start_col=self._META_COLS)[
                : len(percentages)
            ]

        # summary_row가 있으면 ①+② 위치의 컬럼을 소계로 처리해 제거
        if summary_row is not None:
            summary_idxs = {
                i - self._META_COLS
                for i, c in enumerate(summary_row)
                if i >= self._META_COLS and _CIRC_PLUS_SCAN.search(str(c or ""))
            }
            options = [o for i, o in enumerate(options) if i not in summary_idxs]
            percentages = [
                p for i, p in enumerate(percentages) if i not in summary_idxs
            ]

        options, percentages = filter_summary_columns(
            options,
            percentages,
            summary_patterns=DEFAULT_SUMMARY_PATTERNS,
        )
        min_len = min(len(options), len(percentages))
        if min_len == 0:
            return None

        q_num = int(q_m.group(1))
        if q_num in seen_q_nums:
            return None
        seen_q_nums.add(q_num)

        q_title = re.sub(r"\s+", " ", q_m.group(2)).strip()

        return QuestionResult(
            question_number=q_num,
            question_title=q_title,
            question_text=q_title,
            response_options=options[:min_len],
            overall_n_completed=n_completed,
            overall_n_weighted=n_weighted,
            overall_percentages=percentages[:min_len],
        )


class _IpsosParser(BaseTableParser):
    """입소스 주식회사 텍스트 기반 파서.

    포맷 특성:
      - 테이블이 없고 순수 텍스트 레이아웃
      - 질문 마커: '문N. 질문제목' (페이지 텍스트)
      - 전체 행 마커: '전 체' — 그 뒤에 사례수 2개 + 비율 숫자들이 이어짐
      - 비율: 한 줄 이내 공백 구분 정수/소수 (text_bundled)
      - 멀티페이지: 동일 문 번호가 연속 페이지에 반복될 때 첫 페이지만 사용
    """

    PARSER_KEY = "_IpsosParser"
    NEEDS_FITZ_WORDS = True  # fitz words를 통한 x좌표 기반 선택지 추출

    _Q_RE = re.compile(r"문\s*(\d+)\s*[.。]\s+(.+?)(?=문\s*\d+\s*[.。]|$)", re.DOTALL)
    _TOTAL_RE = re.compile(
        r"전\s+체\s+(\(\d[\d,]*\))\s+(\(\d[\d,]*\))\s+((?:[\d.]+[\s\n]+)+)"
    )

    @staticmethod
    def _parse_pct_lines(pct_str: str) -> List[float]:
        """줄/공백 구분 비율 문자열에서 float 목록 추출 (0~100 범위만)."""
        result = []
        for token in re.findall(r"[\d.]+", pct_str):
            try:
                v = float(token)
                if 0.0 <= v <= 100.0:
                    result.append(v)
            except ValueError:
                pass
        return result

    def parse(self, pages_data: List[PageData]) -> List[QuestionResult]:
        results: List[QuestionResult] = []
        seen_q_nums: set = set()

        for _outside_text, page_tables, full_text in pages_data:
            q_m = self._Q_RE.search(full_text)
            if q_m is None:
                continue

            q_num = int(q_m.group(1))
            is_seen = q_num in seen_q_nums

            total_m = self._TOTAL_RE.search(full_text)
            if total_m is None:
                continue

            n_completed = extract_sample_count(total_m.group(1))
            n_weighted = extract_sample_count(total_m.group(2))
            pct_str = total_m.group(3)
            percentages = self._parse_pct_lines(pct_str)
            if not percentages:
                continue

            # 선택지 추출: fitz words 방식(x좌표 기반) 우선, 없으면 헤더 텍스트 폴백
            options: List[str] = []
            has_summary = False

            fitz_words = None
            if (
                page_tables
                and isinstance(page_tables[0], list)
                and page_tables[0]
                and isinstance(page_tables[0][0], tuple)
            ):
                fitz_words = page_tables[0]

            if fitz_words:
                options, has_summary = self._extract_options_from_fitz_words(fitz_words)
            else:
                total_pos = full_text.find("전 체")
                header_text = full_text[:total_pos] if total_pos > 0 else ""
                options, has_summary = self._extract_options_from_header(header_text)

            # 합산 컬럼 감지 시 비율도 선택지 수에 맞게 자름
            if has_summary and len(percentages) > len(options):
                percentages = percentages[: len(options)]

            options, percentages = filter_summary_columns(
                options,
                percentages,
                summary_patterns=DEFAULT_SUMMARY_PATTERNS,
            )
            min_len = min(len(options), len(percentages))
            if min_len == 0:
                continue

            # 복수응답 문항(합계 > 115%) skip
            if sum(percentages[:min_len]) > 115.0:
                continue

            q_title = re.sub(r"\s+", " ", q_m.group(2)).strip()

            # 멀티페이지 병합: 이미 처리된 q_num이고 이전 result의 합계가 75% 미만이면 병합
            if is_seen:
                if (
                    results
                    and results[-1].question_number == q_num
                    and sum(results[-1].overall_percentages) < 75.0
                    and results[-1].overall_n_completed == n_completed
                ):
                    prev = results[-1]
                    merged_opts = list(prev.response_options) + options[:min_len]
                    merged_pcts = list(prev.overall_percentages) + percentages[:min_len]
                    if 75.0 <= sum(merged_pcts) <= 115.0:
                        results[-1] = QuestionResult(
                            question_number=prev.question_number,
                            question_title=prev.question_title,
                            question_text=prev.question_text,
                            response_options=merged_opts,
                            overall_n_completed=n_completed,
                            overall_n_weighted=n_weighted,
                            overall_percentages=merged_pcts,
                        )
                continue

            seen_q_nums.add(q_num)

            results.append(
                QuestionResult(
                    question_number=q_num,
                    question_title=q_title,
                    question_text=q_title,
                    response_options=options[:min_len],
                    overall_n_completed=n_completed,
                    overall_n_weighted=n_weighted,
                    overall_percentages=percentages[:min_len],
                )
            )

        return results

    @staticmethod
    def _extract_options_from_fitz_words(
        fitz_words: List[Tuple],
    ) -> Tuple[List[str], bool]:
        """fitz get_text("words") 결과에서 x좌표 기반 컬럼 그룹화로 선택지 추출.

        fitz words 형식: (x0, y0, x1, y1, word, block_no, line_no, word_no)

        메타 단어(조사완료, 사례수, 가중값 등)의 최대 x0를 기준으로 그보다 오른쪽에
        있는 단어들이 선택지 컬럼이다. '전 체' 행 이전의 헤더 영역만 대상으로 한다.

        Returns:
            (options, has_summary): 선택지 목록, 합산 컬럼('계') 존재 여부
        """
        _META_TEXTS = {"조사완료", "사례수", "가중값", "적용", "기준", "완료", "사례"}
        _SUMMARY_TEXTS = {"계", "합계"}
        TOL = 20  # x좌표 그룹화 tolerance (px)

        # '전 체' y좌표 찾기: '전' 다음에 '체'가 같은 y에 있는 경우
        total_y = None
        for i, w in enumerate(fitz_words):
            if w[4] == "전":
                for j in range(i + 1, min(i + 3, len(fitz_words))):
                    if fitz_words[j][4] == "체" and abs(fitz_words[j][1] - w[1]) < 3:
                        total_y = w[1]
                        break
            if total_y is not None:
                break

        if total_y is None:
            return [], False

        # 헤더 영역: total_y 이전 단어들
        header_words = [w for w in fitz_words if w[1] < total_y - 5]

        # 메타 단어들의 x 범위와 y 범위 파악
        meta_xs = [w[0] for w in header_words if w[4] in _META_TEXTS]
        meta_ys = [w[1] for w in header_words if w[4] in _META_TEXTS]
        if not meta_xs or not meta_ys:
            return [], False

        meta_max_x = max(meta_xs)
        meta_y_min = min(meta_ys)
        meta_y_max = max(meta_ys)
        y_margin = 10

        # 선택지 후보 단어: 메타 x보다 오른쪽, 메타 y 범위 내
        opt_words = [
            w
            for w in header_words
            if w[0] > meta_max_x
            and meta_y_min - y_margin <= w[1] <= meta_y_max + y_margin
        ]

        if not opt_words:
            return [], False

        # x좌표 기반 컬럼 그룹화
        col_groups: dict = {}
        for w in opt_words:
            x, y, text = w[0], w[1], w[4]
            matched_cx = None
            for cx in col_groups:
                if abs(x - cx) <= TOL:
                    matched_cx = cx
                    break
            if matched_cx is None:
                col_groups[x] = []
                matched_cx = x
            col_groups[matched_cx].append((y, text))

        # 각 컬럼의 단어들을 위→아래 결합하여 선택지 이름 생성
        options: List[str] = []
        has_summary = False
        for cx in sorted(col_groups.keys()):
            ws = sorted(col_groups[cx])  # y 기준 정렬
            text = " ".join(t for _, t in ws).strip()
            # '/'로 시작하는 단어는 이전 선택지에 붙임 (예: /무응답)
            if text.startswith("/") and options:
                options[-1] += text
                continue
            if text in _SUMMARY_TEXTS or text.startswith("*없음/"):
                has_summary = True
                continue
            if text:
                options.append(text)

        return options, has_summary

    @staticmethod
    def _extract_options_from_header(header_text: str) -> Tuple[List[str], bool]:
        """헤더 영역에서 선택지 후보 추출.

        입소스 PDF 헤더는 선택지 이름이 단어 단위로 줄바꿈되어 있다.
        직책 단어(국회의원, 지사 등)로 선택지 경계를 감지하고,
        *없음/모름/무응답* 합산 컬럼은 제거한다.

        Returns:
            (options, has_summary_col):
            has_summary_col — *없음/모름/무응답* 합산 컬럼이 있었으면 True
        """
        _META = {"조사완료", "사례수", "가중값", "적용", "조사", "완료", "가중", "사례"}
        # 직책 단어: 이 단어로 현재 그룹을 확정 (선택지 경계)
        _TITLES = {"국회의원", "도지사", "지사", "대표", "장관", "수석대변인", "대변인"}
        # 독립 종료 단어: 단독으로 하나의 선택지가 됨
        _TERMINALS = {"없다", "기타", "없음"}

        candidates: List[str] = []
        current_parts: List[str] = []
        has_summary = False

        for line in header_text.splitlines():
            line = line.strip()
            if not line:
                continue

            # *없음/모름/무응답* 합산 컬럼 시작 → 이후 무시
            if line.startswith("*없음/"):
                if current_parts:
                    merged = " ".join(current_parts)
                    if not any(w in merged for w in _META):
                        candidates.append(merged)
                    current_parts = []
                has_summary = True
                break

            # 메타 단어 — 현재 그룹 확정 후 버림
            if line in _META:
                if current_parts:
                    merged = " ".join(current_parts)
                    if not any(w in merged for w in _META):
                        candidates.append(merged)
                    current_parts = []
                continue

            # /로 시작 — 이전 candidates 마지막 항목에 붙임 (예: 모르겠다 + /무응답)
            if line.startswith("/"):
                suffix = line  # /무응답 그대로
                if candidates:
                    candidates[-1] += suffix
                elif current_parts:
                    current_parts[-1] += suffix
                continue

            # 누적 문자열이 직책으로 끝나는지 확인 (분리된 글자 포함)
            combined = "".join(current_parts + [line]).replace(" ", "")
            if any(combined.endswith(t) for t in _TITLES):
                current_parts.append(line)
                # 단일 글자 파트는 이전 파트에 붙여 직책명 복원 (예: 경기도지 + 사 → 경기도지사)
                merged_parts: List[str] = []
                for part in current_parts:
                    if (
                        merged_parts
                        and len(part) <= 2
                        and len(merged_parts[-1].split()[-1]) <= 3
                    ):
                        merged_parts[-1] += part
                    else:
                        merged_parts.append(part)
                opt = " ".join(merged_parts)
                if not any(w in opt for w in _META):
                    candidates.append(opt)
                current_parts = []
                continue

            # 독립 종료 단어 — 이전 그룹 확정 후 자신도 독립 선택지로
            if line in _TERMINALS:
                if current_parts:
                    merged = " ".join(current_parts)
                    if not any(w in merged for w in _META):
                        candidates.append(merged)
                    current_parts = []
                candidates.append(line)
                continue

            current_parts.append(line)

        if current_parts and not has_summary:
            merged = " ".join(current_parts)
            if not any(w in merged for w in _META):
                candidates.append(merged)

        filtered = [c for c in candidates if c and not any(w in c for w in _META)]
        return filtered, has_summary


class _KStatResearchParser(BaseTableParser):
    """케이스탯리서치 텍스트 기반 파서.

    두 PDF 파일을 지원:
      1. KBS 파일: 질문 마커 없음 (페이지당 1질문), '전 체' 전체 행
      2. 12.31 파일: '<표N>' 질문 마커, '▩전체▩' 전체 행
    두 파일 모두 테이블 내 텍스트 기반 (테이블 구조 있음).

    포맷 특성 (KBS):
      - '전 체' (N완료) (N가중) 비율들 순서로 텍스트 출력
    포맷 특성 (12.31):
      - <표N> 제목 질문 마커
      - '▩전체▩' (N완료) (N가중) 비율들 순서로 텍스트 출력
      - 마지막 비율 '100'은 합계 컬럼 — 제거 필요
    """

    PARSER_KEY = "_KStatResearchParser"

    # KBS: '전 체' 마커 + (N) (N) 숫자들 (줄바꿈 포함)
    _TOTAL_KBS_RE = re.compile(
        r"전\s+체\s+(\(\d[\d,]*\))\s+(\(\d[\d,]*\))\s+((?:[\d]+\s*[\n ]?)+)"
    )
    # 12.31: '▩전체▩' 마커
    _TOTAL_12_RE = re.compile(
        r"▩전체▩\s+(\(\d[\d,]*\))\s+(\(\d[\d,]*\))\s+((?:[\d]+\s*[\n ]?)+)"
    )
    # 12.31 질문 마커: '<표N> 제목'
    _Q12_RE = re.compile(r"<표\s*(\d+)>\s*(.+?)(?:\n|BASE:)")
    # 공백/줄바꿈 구분 숫자 파싱 (미사용, 참조용)
    _NUM_RE = re.compile(r"[\d.]+")

    @staticmethod
    def _parse_pct_multiline(pct_str: str) -> List[float]:
        """줄바꿈/공백으로 구분된 비율 문자열에서 float 목록 추출."""
        result = []
        for token in re.findall(r"[\d.]+", pct_str):
            try:
                v = float(token)
                if 0.0 <= v <= 100.0:
                    result.append(v)
            except ValueError:
                pass
        return result

    def parse(self, pages_data: List[PageData]) -> List[QuestionResult]:
        results: List[QuestionResult] = []
        seen_pct_sigs: set = set()

        for _outside_text, page_tables, full_text in pages_data:
            # KBS 포맷: '전 체' 마커, 테이블에서 선택지 추출
            if self._TOTAL_KBS_RE.search(full_text):
                self._parse_kbs_page(
                    page_tables,
                    full_text,
                    len(results) + 1,
                    seen_pct_sigs,
                    results,
                )
                continue

            # 12.31 포맷: '▩전체▩' 마커
            total_m = self._TOTAL_12_RE.search(full_text)
            if total_m:
                result = self._build_12_result(
                    full_text,
                    page_tables,
                    total_m,
                    len(results) + 1,
                    seen_pct_sigs,
                )
                if result is not None:
                    results.append(result)

        return results

    def _parse_kbs_page(
        self,
        page_tables: List,
        full_text: str,
        fallback_q_num: int,
        seen_pct_sigs: set,
        results: List[QuestionResult],
    ) -> None:
        """KBS 포맷: pdfplumber 테이블 헤더에서 선택지, full_text에서 비율 추출."""
        # 선택지: pdfplumber 테이블 헤더(col[4]+)에서 추출
        options: List[str] = []
        if page_tables:
            header = page_tables[0][0] if page_tables[0] else []
            META_COLS = 4  # 구 분, None, 조사완료, 가중값
            for cell in header[META_COLS:]:
                if cell:
                    opt = re.sub(r"\s+", " ", str(cell).strip())
                    if opt:
                        options.append(opt)

        # 비율: full_text에서 추출 (pdfplumber 마지막 컬럼 None 문제 우회)
        total_m = self._TOTAL_KBS_RE.search(full_text)
        if total_m is None:
            return

        n_completed = extract_sample_count(total_m.group(1))
        n_weighted = extract_sample_count(total_m.group(2))
        percentages = self._parse_pct_multiline(total_m.group(3))
        if not percentages:
            return

        # 중복 페이지 방지
        sig = tuple(percentages)
        if sig in seen_pct_sigs:
            return
        seen_pct_sigs.add(sig)

        # 선택지가 없으면 fallback (선택지 수 = 비율 수)
        if not options:
            options = [f"선택지{i+1}" for i in range(len(percentages))]

        min_len = min(len(options), len(percentages))
        if min_len == 0:
            return

        pct_sum = sum(percentages[:min_len])

        # 복수응답 문항(합계 > 115%) skip
        if pct_sum > 115.0:
            return

        # 멀티페이지 문항: 합계 < 50%이고 이전 결과의 사례수가 동일하면 병합
        if (
            pct_sum < 50.0
            and results
            and results[-1].overall_n_completed == n_completed
        ):
            prev = results[-1]
            merged_opts = list(prev.response_options) + options[:min_len]
            merged_pcts = list(prev.overall_percentages) + percentages[:min_len]
            merged_sum = sum(merged_pcts)
            if 75.0 <= merged_sum <= 115.0:
                results[-1] = QuestionResult(
                    question_number=prev.question_number,
                    question_title=prev.question_title,
                    question_text=prev.question_text,
                    response_options=merged_opts,
                    overall_n_completed=n_completed,
                    overall_n_weighted=n_weighted,
                    overall_percentages=merged_pcts,
                )
            return  # 병합 성공/실패 관계없이 새 질문으로 추가하지 않음

        q_title = f"Q{fallback_q_num}"
        results.append(
            QuestionResult(
                question_number=fallback_q_num,
                question_title=q_title,
                question_text=q_title,
                response_options=options[:min_len],
                overall_n_completed=n_completed,
                overall_n_weighted=n_weighted,
                overall_percentages=percentages[:min_len],
            )
        )

    def _build_12_result(
        self,
        page_text: str,
        page_tables: List,
        total_m: re.Match,
        fallback_q_num: int,
        seen_pct_sigs: set,
    ) -> Optional[QuestionResult]:
        """12.31 포맷: ▩전체▩ 마커, fitz 테이블에서 선택지/비율 추출."""
        n_completed = extract_sample_count(total_m.group(1))
        n_weighted = extract_sample_count(total_m.group(2))

        # fitz 테이블 헤더에서 선택지/비율 추출 시도
        options: List[str] = []
        percentages: List[float] = []

        if page_tables:
            table = page_tables[0]
            # 헤더 row: col 0='BASE:전체', col 1=None, col 2=조사완료, col 3=가중값
            # col 4+: 실제 선택지, '종합' 셀 이후는 합산 컬럼
            META_COLS = 4
            header = table[0] if table else []

            # '종합' 컬럼 인덱스 찾기
            summary_col = len(header)
            for ci, cell in enumerate(header):
                if ci >= META_COLS and cell and "종합" in str(cell):
                    summary_col = ci
                    break

            # 선택지: header[META_COLS:summary_col]
            for cell in header[META_COLS:summary_col]:
                if cell:
                    opt = re.sub(r"\s+", " ", str(cell).strip())
                    if opt:
                        options.append(opt)

            # '▩전체▩' 행에서 비율 추출: col META_COLS~summary_col
            for row in table[1:]:
                if row and row[0] and "▩전체▩" in str(row[0]):
                    for cell in row[META_COLS:summary_col]:
                        try:
                            v = float(str(cell).strip())
                            if 0.0 <= v <= 100.0:
                                percentages.append(v)
                        except (ValueError, TypeError):
                            pass
                    break

        # 테이블 방식 실패 시 full_text 기반 폴백
        if not percentages:
            pct_str = total_m.group(3).strip()
            percentages = self._parse_pct_multiline(pct_str)
            if not percentages:
                return None
            # 마지막 값이 100이면 합계 컬럼 제거
            if percentages[-1] == 100.0:
                percentages = percentages[:-1]

        # 중복 페이지 방지
        sig = tuple(percentages)
        if sig in seen_pct_sigs:
            return None
        seen_pct_sigs.add(sig)

        # 선택지가 없으면 헤더 텍스트 폴백
        if not options:
            total_pos = page_text.find("▩전체▩")
            header_text = page_text[:total_pos] if total_pos > 0 else ""
            options, n_real = self._extract_options_12(header_text)
            if n_real > 0 and len(percentages) > n_real:
                percentages = percentages[:n_real]

        # 질문 번호/제목 추출
        q_title = ""
        q_num = fallback_q_num
        q_m = self._Q12_RE.search(page_text)
        if q_m:
            q_num = int(q_m.group(1))
            q_title = re.sub(r"\s+", " ", q_m.group(2)).strip()

        options, percentages = filter_summary_columns(
            options,
            percentages,
            summary_patterns=DEFAULT_SUMMARY_PATTERNS,
        )
        min_len = min(len(options), len(percentages))
        if min_len == 0:
            return None

        return QuestionResult(
            question_number=q_num,
            question_title=q_title,
            question_text=q_title,
            response_options=options[:min_len],
            overall_n_completed=n_completed,
            overall_n_weighted=n_weighted,
            overall_percentages=percentages[:min_len],
        )

    @staticmethod
    def _extract_options_12(header_text: str) -> Tuple[List[str], int]:
        """12.31 포맷 헤더에서 선택지 추출.

        '종합' 단어가 나타나면 합산 컬럼 시작으로 판단하고 중단한다.

        Returns:
            (options, n_real): 실제 선택지 목록과 그 수.
            n_real > 0 이면 비율도 n_real개만 사용.
        """
        _SKIP = {
            "구 분",
            "조사",
            "완료",
            "사례수",
            "가중값",
            "적용",
            "기준",
            "명",
            "( )",
            "BASE:전체",
            "조사완료",
            "가중값 배율",
        }
        candidates: List[str] = []
        pending: List[str] = []
        hit_summary = False

        for line in header_text.splitlines():
            line = line.strip()
            if not line:
                continue

            # '종합' 단어 → 합산 컬럼 시작, 중단
            if line == "종합":
                if pending:
                    merged = " ".join(pending)
                    if not any(s in merged for s in ("사례수", "가중값", "조사완료")):
                        candidates.append(merged)
                    pending = []
                hit_summary = True
                break

            if line in _SKIP or re.match(r"^\d+$", line):
                if pending:
                    merged = " ".join(pending)
                    if not any(s in merged for s in ("사례수", "가중값", "조사완료")):
                        candidates.append(merged)
                    pending = []
                continue

            pending.append(line)

        if pending and not hit_summary:
            merged = " ".join(pending)
            if not any(s in merged for s in ("사례수", "가중값", "조사완료")):
                candidates.append(merged)

        filtered = [c for c in candidates if len(c) < 40 and c]
        n_real = len(filtered) if hit_summary else 0
        return filtered, n_real

    @staticmethod
    def _extract_options(header_text: str, count: int) -> List[str]:
        """KBS 포맷 헤더 텍스트에서 선택지 추출 (fallback용)."""
        _SKIP = {
            "구 분",
            "조사",
            "완료",
            "사례수",
            "가중값",
            "적용",
            "기준",
            "명",
            "( )",
        }
        candidates: List[str] = []
        pending: List[str] = []
        for line in header_text.splitlines():
            line = line.strip()
            if not line or line in _SKIP or re.match(r"^\d+$", line):
                if pending:
                    merged = " ".join(pending)
                    if not any(s in merged for s in ("사례수", "가중값", "조사완료")):
                        candidates.append(merged)
                    pending = []
                continue
            pending.append(line)
        if pending:
            merged = " ".join(pending)
            if not any(s in merged for s in ("사례수", "가중값", "조사완료")):
                candidates.append(merged)
        filtered = [c for c in candidates if len(c) < 30 and c]
        while len(filtered) < count:
            filtered.append(f"선택지{len(filtered) + 1}")
        return filtered[:count]


class _AceResearchParser(BaseTableParser):
    """에이스리서치 크로스탭 파서.

    포맷 특성:
      - 질문 마커: '<표N> 제목' + 'QN.' 본문
      - 전체 행: '■ 전  체 ■' (테이블 row[2], col0)
      - 비율 위치: table_cell (col4+)
      - meta 컬럼: 4개 (공백, 구분, n완료, n가중)
      - 페이지 연속성: 있음 (<표N>-1, <표N>-2 형태)
    """

    PARSER_KEY = "_AceResearchParser"
    TOTAL_MARKERS = ("■ 전  체 ■", "■ 전 체 ■", "전  체", "전 체")
    META_COLS = 4
    END_COL = None
    SUMMARY_PATS = DEFAULT_SUMMARY_PATTERNS + (
        re.compile(r"긍정층"),   # 국정수행 평가 소계 열
        re.compile(r"부정층"),   # 국정수행 평가 소계 열
    )

    _Q_RE = re.compile(r"<표\s*(\d+)(?:-\d+)?>\s*([^\n]+)\nQ\d+\.\s+([^\n]+)", re.MULTILINE)
    _Q_FALLBACK_RE = re.compile(r"<표\s*(\d+)(?:-\d+)?>\s*([^\n]+)")

    def parse(self, pages_data: List[PageData]) -> List[QuestionResult]:
        results: List[QuestionResult] = []
        seen_q_nums: set = set()

        for _page_text, page_tables, full_text in pages_data:
            if not page_tables:
                continue

            # 질문 번호/제목 추출
            m = self._Q_RE.search(full_text)
            if not m:
                m = self._Q_FALLBACK_RE.search(full_text)
                if not m:
                    continue
                q_num = int(m.group(1))
                q_title = m.group(2).strip()
                q_text = q_title
            else:
                q_num = int(m.group(1))
                q_title = m.group(2).strip()
                q_text = re.sub(r"\s+", " ", m.group(3)).strip()

            if q_num in seen_q_nums:
                continue

            for table in page_tables:
                if not table or len(table) < 3:
                    continue

                # 전체 행 탐색: row[0]~row[3] 중 마커 포함
                total_row_idx = None
                for ri, row in enumerate(table[:5]):
                    cell0 = str(row[0] or "").strip()
                    if any(m2 in cell0 for m2 in self.TOTAL_MARKERS):
                        total_row_idx = ri
                        break
                if total_row_idx is None:
                    continue

                total_row = table[total_row_idx]

                # 선택지: 헤더(row[1])의 col4~
                header_row = table[1] if len(table) > 1 else table[0]
                options = extract_options_from_row(header_row, start_col=self.META_COLS)
                if not options:
                    continue

                # 사례수
                n_completed = extract_sample_count(str(total_row[2] or ""))
                n_weighted = extract_sample_count(str(total_row[3] or ""))

                # 비율: col4~ (개별 셀)
                percentages = extract_percentages_from_cells(
                    total_row, start_col=self.META_COLS
                )
                if not percentages:
                    continue

                options, percentages = filter_summary_columns(
                    options, percentages, summary_patterns=self.SUMMARY_PATS
                )
                min_len = min(len(options), len(percentages))
                if min_len == 0:
                    continue

                seen_q_nums.add(q_num)
                results.append(
                    QuestionResult(
                        question_number=q_num,
                        question_title=q_title,
                        question_text=q_text,
                        response_options=options[:min_len],
                        overall_n_completed=n_completed,
                        overall_n_weighted=n_weighted,
                        overall_percentages=percentages[:min_len],
                    )
                )
                break  # 페이지당 첫 유효 테이블만

        for i, r in enumerate(results):
            r.question_number = i + 1
        return results


class _MediaTomatoParser(BaseTableParser):
    """미디어토마토(뉴스토마토) 크로스탭 파서.

    포맷 특성:
      - 질문 마커: '교차표N_제목' (페이지 상단 텍스트)
      - 전체 행: '전체 (N완료) (N가중) 비율들...' (페이지 텍스트, 테이블 구조 없음)
      - 비율 위치: 텍스트 내 공백 구분 숫자 시퀀스
      - 헤더(선택지): 전체 행 이전 줄의 컬럼명
      - 페이지 연속성: 없음 (페이지당 1 교차표)
    """

    PARSER_KEY = "_MediaTomatoParser"

    # '교차표N_제목' 또는 '교차표N 제목'
    _Q_RE = re.compile(r"교차표\s*(\d+)[_\s]+([^\n]+)")
    # '전체\n(N) (N)\n비율들' 또는 '전체 (N) (N) 비율들'
    _TOTAL_RE = re.compile(
        r"전체\s+\((\d[\d,]*)\)\s+\((\d[\d,]*)\)\s+((?:[\d]+\.[\d]+\s*)+)"
    )
    # 선택지: 전체 행 바로 위의 컬럼 헤더 행
    _HEADER_RE = re.compile(
        r"((?:[^\n]+\n){1,3}?)전체\s+\((\d[\d,]*)\)\s+\((\d[\d,]*)\)",
        re.DOTALL,
    )
    # 헤더 블록: '사례수' 이후 '가중값적용' 직전까지의 줄들이 선택지 후보
    # 미디어토마토 PDF에서 헤더 블록은 항상 사례수로 시작, 가중값적용으로 끝남
    _HEADER_BLOCK_RE = re.compile(
        r"사례수\n(.*?)(?:조사완료\n)?가중값적용",
        re.DOTALL,
    )

    @staticmethod
    def _parse_options_from_header(header_text: str) -> List[str]:
        """헤더 텍스트에서 선택지 이름 추출."""
        # '조사완료\n가중값적용\n선택지1\n선택지2...' 형태
        lines = [ln.strip() for ln in header_text.strip().splitlines() if ln.strip()]
        # 사례수/가중값 키워드 이후 항목이 선택지
        skip = {"사례수", "조사완료", "가중값적용", "가중값", "가중", "단위: %", "%"}
        opts = []
        for ln in lines:
            if ln in skip or re.match(r"^[\d.]+$", ln):
                continue
            if "사례수" in ln or "가중값" in ln:
                continue
            opts.append(ln)
        return opts

    def parse(self, pages_data: List[PageData]) -> List[QuestionResult]:
        results: List[QuestionResult] = []

        for _page_text, _page_tables, full_text in pages_data:
            # 질문 마커 탐색
            q_m = self._Q_RE.search(full_text)
            if not q_m:
                continue

            q_num = int(q_m.group(1))
            q_title = q_m.group(2).strip()

            # 전체 행 탐색
            total_m = self._TOTAL_RE.search(full_text)
            if not total_m:
                continue

            n_completed = extract_sample_count(f"({total_m.group(1)})")
            n_weighted = extract_sample_count(f"({total_m.group(2)})")

            # 비율 파싱
            pct_str = total_m.group(3)
            percentages: List[float] = []
            for token in re.findall(r"[\d]+\.[\d]+", pct_str):
                try:
                    v = float(token)
                    if 0.0 <= v <= 100.0:
                        percentages.append(v)
                except ValueError:
                    pass

            if not percentages:
                continue

            # 선택지 추출: 헤더 블록(사례수~가중값적용) 우선, 폴백은 전체 행 앞 텍스트
            n_opts = len(percentages)
            _skip = {"사례수", "조사완료", "가중값적용", "가중값", "조사완료사례수"}

            def _filter_candidates(raw_lines: List[str]) -> List[str]:
                return [
                    ln for ln in raw_lines
                    if ln not in _skip
                    and "사례수" not in ln
                    and "가중값" not in ln
                    and "단위" not in ln
                    and not re.match(r"^[\d.]+$", ln)
                    and not re.match(r"^\([\d,]+\)$", ln)
                ]

            # 1순위: 헤더 블록(사례수 ~ 가중값적용) 탐지
            hb_m = self._HEADER_BLOCK_RE.search(full_text)
            if hb_m:
                block_lines = [
                    ln.strip() for ln in hb_m.group(1).splitlines() if ln.strip()
                ]
                candidates = _filter_candidates(block_lines)
            else:
                # 2순위: 전체 행 앞의 텍스트에서 추출 (기존 방식)
                before_total = full_text[: total_m.start()]
                lines = [ln.strip() for ln in before_total.splitlines() if ln.strip()]
                candidates = _filter_candidates(lines)

            # 비율 수보다 많으면 마지막 N개 사용 (합계/모름 등 끝 항목 우선)
            options = candidates[-n_opts:] if len(candidates) >= n_opts else candidates
            # 부족하면 placeholder로 앞을 채움
            while len(options) < n_opts:
                options.insert(0, f"선택지{len(options) + 1}")
            options = options[:n_opts]

            results.append(
                QuestionResult(
                    question_number=q_num,
                    question_title=q_title,
                    question_text=q_title,
                    response_options=options,
                    overall_n_completed=n_completed,
                    overall_n_weighted=n_weighted,
                    overall_percentages=percentages,
                )
            )

        for i, r in enumerate(results):
            r.question_number = i + 1
        return results


class _KopraParser(BaseTableParser):
    """KOPRA (한국여론평판연구소) 크로스탭 파서.

    포맷 특성:
      - 질문 마커: 'N. 제목' + 'Q 본문' (별도 페이지)
      - 전체 행: '▣ 전체 ▣' (테이블 row[1], col1)
      - 비율 위치: table_cell (col5+, 정수형)
      - meta 컬럼: 5개 (헤더셀뭉침, 전체마커, None, n완료, n가중)
      - 통계표는 보고서 후반부에 별도 섹션으로 위치
    """

    PARSER_KEY = "_KopraParser"
    TOTAL_MARKERS = ("▣ 전체 ▣",)
    META_COLS = 5
    SUMMARY_PATS = DEFAULT_SUMMARY_PATTERNS

    # 'N. 제목' 패턴 (1~9로 시작, 마침표 뒤 한글 제목)
    _SECTION_RE = re.compile(r"^(\d+)\.\s+([^\n]+)", re.MULTILINE)
    # 'Q 본문' 패턴
    _Q_TEXT_RE = re.compile(r"\bQ(?:\d+)?\.\s+(.+?)(?:\(보기|○|$)", re.DOTALL)

    def parse(self, pages_data: List[PageData]) -> List[QuestionResult]:
        results: List[QuestionResult] = []
        seen_q_nums: set = set()

        for _page_text, page_tables, full_text in pages_data:
            if not page_tables:
                continue

            # 전체 행이 있는 테이블만 처리
            for table in page_tables:
                if not table or len(table) < 2:
                    continue

                # row[1]에서 '▣ 전체 ▣' 탐색
                total_row = None
                for row in table[1:4]:
                    cell1 = str(row[1] if len(row) > 1 else row[0] or "").strip()
                    if "▣ 전체 ▣" in cell1:
                        total_row = row
                        break
                if total_row is None:
                    continue

                # 선택지: 헤더 row[0] col5~
                header_row = table[0]
                options = extract_options_from_row(header_row, start_col=self.META_COLS)
                if not options:
                    continue

                # 사례수: col3, col4
                n_completed = extract_sample_count(str(total_row[3] if len(total_row) > 3 else ""))
                n_weighted = extract_sample_count(str(total_row[4] if len(total_row) > 4 else ""))

                # 비율: col5~ (정수형 퍼센트)
                percentages = extract_percentages_from_cells(
                    total_row, start_col=self.META_COLS
                )
                if not percentages:
                    continue

                # 질문 번호/제목: 페이지 텍스트에서 추출
                section_m = self._SECTION_RE.search(full_text)
                q_num = int(section_m.group(1)) if section_m else len(results) + 1
                q_title = section_m.group(2).strip() if section_m else f"Q{q_num}"
                q_text_m = self._Q_TEXT_RE.search(full_text)
                q_text = re.sub(r"\s+", " ", q_text_m.group(1)).strip() if q_text_m else q_title

                if q_num in seen_q_nums:
                    continue

                options, percentages = filter_summary_columns(
                    options, percentages, summary_patterns=self.SUMMARY_PATS
                )
                min_len = min(len(options), len(percentages))
                if min_len == 0:
                    continue

                seen_q_nums.add(q_num)
                results.append(
                    QuestionResult(
                        question_number=q_num,
                        question_title=q_title,
                        question_text=q_text,
                        response_options=options[:min_len],
                        overall_n_completed=n_completed,
                        overall_n_weighted=n_weighted,
                        overall_percentages=percentages[:min_len],
                    )
                )
                break

        for i, r in enumerate(results):
            r.question_number = i + 1
        return results


class _KSOIParser(BaseTableParser):
    """CBS-KSOI(한국사회여론연구소) 크로스탭 파서.

    포맷 특성:
      - 질문 제목: 테이블 바로 위 outside_text에 '【 표 N 】 제목' 형태로 존재
      - 크로스탭 페이지: 질문당 2페이지 — outside_text에 제목 있는 첫 페이지만 파싱
      - 전체 행: cell0='전체', col4+ 개별 셀 비율
      - 소계 컬럼: SUMMARY_PATS로 필터 + 중복 선택지 이름 첫 재등장 시 컷
      - meta 컬럼: 4개 (빈칸, 빈칸, n완료, n가중)
      - 선택지 텍스트에 개행('\n') 포함 → 공백으로 정규화
    """

    PARSER_KEY = "_KSOIParser"
    TOTAL_MARKERS = ("전체",)
    META_COLS = 4
    SUMMARY_PATS = DEFAULT_SUMMARY_PATTERNS + (
        re.compile(r"^계$"),
        re.compile(r"^긍정\s*평가"),
        re.compile(r"^부정\s*평가"),
    )

    # outside_text 내 '【 표 N 】 제목' 패턴 — 표 번호(그룹1)와 제목(그룹2) 분리
    _TABLE_TITLE_RE = re.compile(r"【\s*표\s*(\d+)\s*】\s*(.+)")

    # 선택지에 이 키워드가 있으면 응답자 특성표 — 스킵
    _META_OPT_KEYWORDS = frozenset({"가중값", "사례수"})

    def parse(self, pages_data: List[PageData]) -> List[QuestionResult]:
        results: List[QuestionResult] = []
        seen_table_nums: set = set()  # 이미 파싱한 표 번호 — 2번째 페이지 중복 방지

        for outside_text, page_tables, _full_text in pages_data:
            if not page_tables:
                continue

            # outside_text에서 '【 표 N 】 제목' 추출 — 없으면 비크로스탭 페이지
            title_match = self._TABLE_TITLE_RE.search(outside_text)
            if title_match is None:
                continue
            table_num = title_match.group(1)
            q_title = title_match.group(2).strip()

            # 같은 표 번호가 이미 파싱됐으면 2번째 크로스탭 페이지 — 스킵
            if table_num in seen_table_nums:
                continue
            seen_table_nums.add(table_num)

            for table in page_tables:
                if not table or len(table) < 3:
                    continue

                total_row = None
                for row in table[:5]:
                    if str(row[0] or "").strip() == "전체":
                        total_row = row
                        break
                if total_row is None:
                    continue

                # 선택지: row[0], col4~ (개행 → 공백)
                options = [
                    re.sub(r"\s+", " ", str(c or "").strip())
                    for c in table[0][self.META_COLS:]
                    if str(c or "").strip()
                ]
                if not options:
                    continue

                # 응답자 특성표 등 메타 테이블 — 스킵
                if any(
                    any(kw in opt for kw in self._META_OPT_KEYWORDS)
                    for opt in options
                ):
                    continue

                n_completed = extract_sample_count(str(total_row[2] or ""))
                n_weighted = extract_sample_count(str(total_row[3] or ""))

                if n_completed is None:
                    continue

                percentages = extract_percentages_from_cells(total_row, start_col=self.META_COLS)
                if not percentages:
                    continue

                options, percentages = filter_summary_columns(
                    options, percentages, summary_patterns=self.SUMMARY_PATS
                )
                min_len = min(len(options), len(percentages))
                if min_len == 0:
                    continue

                # 중복 선택지 이름이 재등장하면 이후는 소계 영역 — 컷
                seen_opts: set = set()
                deduped_opts: list = []
                deduped_pcts: list = []
                for opt, pct in zip(options[:min_len], percentages[:min_len]):
                    if opt in seen_opts:
                        break
                    seen_opts.add(opt)
                    deduped_opts.append(opt)
                    deduped_pcts.append(pct)
                options, percentages = deduped_opts, deduped_pcts
                if not options:
                    continue

                results.append(
                    QuestionResult(
                        question_number=len(results) + 1,
                        question_title=q_title,
                        question_text=q_title,
                        response_options=options,
                        overall_n_completed=n_completed,
                        overall_n_weighted=n_weighted,
                        overall_percentages=percentages,
                    )
                )
                break

        for i, r in enumerate(results):
            r.question_number = i + 1
        return results


class _FairPollParser(BaseTableParser):
    """여론조사공정(주) 크로스탭 파서.

    포맷 특성:
      - 질문 제목: 테이블 바로 위 outside_text에 '【 표 N 】 제목' 형태로 존재
      - 크로스탭 페이지: 질문당 2페이지 — 첫 페이지만 파싱 (seen_table_nums로 중복 방지)
      - 페이지당 테이블 2개: tables[0]=헤더, tables[1]=실제 데이터
      - 전체 행: tables[1]의 row[0]='', row[1]='전체'
      - 메타 컬럼: 4개 (빈칸, 구분값, n완료, n가중) → 비율은 col4부터
      - 소계 컬럼(①+②, ③+④ 등): SUMMARY_PATS로 필터
    """

    PARSER_KEY = "_FairPollParser"
    TOTAL_MARKERS = ("전체",)
    META_COLS = 4          # 데이터 테이블: col0=구분범주, col1=구분값, col2=n완료, col3=n가중
    HEADER_OPT_COL = 3    # 헤더 테이블: col0=구분, col1=사례수(merged), col2=None, col3~=선택지
    SUMMARY_PATS = DEFAULT_SUMMARY_PATTERNS + (
        re.compile(r"^계$"),
        re.compile(r"^긍정\s*평가"),
        re.compile(r"^부정\s*평가"),
        re.compile(r"[①②③④⑤⑥⑦⑧⑨⑩]\s*\+\s*[①②③④⑤⑥⑦⑧⑨⑩]"),  # ①+② 소계
    )

    _TABLE_TITLE_RE = re.compile(r"【\s*표\s*(\d+)\s*】\s*(.+)")
    _META_OPT_KEYWORDS = frozenset({"가중값", "사례수"})

    def parse(self, pages_data: List[PageData]) -> List[QuestionResult]:
        results: List[QuestionResult] = []
        seen_table_nums: set = set()

        for outside_text, page_tables, _full_text in pages_data:
            if not page_tables:
                continue

            title_match = self._TABLE_TITLE_RE.search(outside_text)
            if title_match is None:
                continue
            table_num = title_match.group(1)
            q_title = title_match.group(2).strip()

            if table_num in seen_table_nums:
                continue
            seen_table_nums.add(table_num)

            # 데이터 테이블은 두 번째 (tables[1]) — 헤더(tables[0])에서 선택지 추출
            if len(page_tables) < 2:
                continue
            header_table = page_tables[0]
            data_table = page_tables[1]

            if not header_table or not data_table:
                continue

            # 전체 행: row[1]=='전체'인 첫 번째 행
            total_row = None
            for row in data_table[:5]:
                if str(row[1] or "").strip() == "전체":
                    total_row = row
                    break
            if total_row is None:
                continue

            # 선택지: 헤더 테이블 첫 행의 col3~ (헤더는 col3부터 시작, 개행 → 공백 정규화)
            options = [
                re.sub(r"\s+", " ", str(c or "").strip())
                for c in header_table[0][self.HEADER_OPT_COL:]
                if str(c or "").strip()
            ]
            if not options:
                continue

            if any(
                any(kw in opt for kw in self._META_OPT_KEYWORDS)
                for opt in options
            ):
                continue

            n_completed = extract_sample_count(str(total_row[2] or ""))
            n_weighted = extract_sample_count(str(total_row[3] or ""))
            if n_completed is None:
                continue

            percentages = extract_percentages_from_cells(total_row, start_col=self.META_COLS)
            if not percentages:
                continue

            options, percentages = filter_summary_columns(
                options, percentages, summary_patterns=self.SUMMARY_PATS
            )
            min_len = min(len(options), len(percentages))
            if min_len == 0:
                continue

            # 중복 선택지 이름 재등장 시 소계 영역 — 컷
            seen_opts: set = set()
            deduped_opts: list = []
            deduped_pcts: list = []
            for opt, pct in zip(options[:min_len], percentages[:min_len]):
                if opt in seen_opts:
                    break
                seen_opts.add(opt)
                deduped_opts.append(opt)
                deduped_pcts.append(pct)
            options, percentages = deduped_opts, deduped_pcts
            if not options:
                continue

            results.append(
                QuestionResult(
                    question_number=len(results) + 1,
                    question_title=q_title,
                    question_text=q_title,
                    response_options=options,
                    overall_n_completed=n_completed,
                    overall_n_weighted=n_weighted,
                    overall_percentages=percentages,
                )
            )

        for i, r in enumerate(results):
            r.question_number = i + 1
        return results


class _KIRParser:
    """(주)코리아정보리서치 크로스탭 파서.

    포맷 특성:
      - 질문 제목: outside_text에 'N. 제목' 또는 'N번) ...' 형태
      - 질문당 1페이지, 테이블 1개
      - 헤더: row[0] — col0='구분', col1=None, col2='조사완료사례수', col3='가중값적용사례수',
                        col4+= 선택지 (개행 → 공백 정규화)
      - 전체 행: row[1] — col0='합계' 또는 '전체', col2=n완료, col3=n가중, col4+=비율
      - 메타 컬럼: 4개 (구분, None, n완료, n가중)
    """

    PARSER_KEY = "_KIRParser"
    TOTAL_MARKERS = frozenset({"합계", "전체"})
    SUMMARY_PATS = DEFAULT_SUMMARY_PATTERNS + (
        re.compile(r"^계$"),
    )
    _META_PAGE_MARKERS = frozenset({"조사개요", "조사방법", "조사완료 응답자", "표본의 특성"})
    _Q_TITLE_RE = re.compile(r"^\d+[.\)]\s*(.+?)(?:\n|$)", re.MULTILINE)
    _WEIGHTED_KW = "가중값"
    _N_KW = "사례수"

    @staticmethod
    def _extract_pct_cells(row: List, start_col: int, end_col: Optional[int] = None) -> List[float]:
        """%를 포함한 셀에서 비율 값을 추출한다 (예: '47.0%' → 47.0)."""
        result: List[float] = []
        for cell in row[start_col:end_col]:
            text = str(cell or "").strip().rstrip("%")
            try:
                v = float(text)
            except ValueError:
                continue
            if 0.0 <= v <= 100.0:
                result.append(v)
        return result

    def _detect_layout(self, header_row: List) -> Tuple[int, int, Optional[int]]:
        """헤더 행을 분석하여 (완료사례수_col, 선택지_start_col, 가중값_col_or_None) 반환.

        포맷 A: col0=구분, col1=None, col2=완료사례수, col3=가중값사례수, col4+=선택지
        포맷 B: col0=구분, col1=None, col2=완료사례수, col3+=선택지, col[-1]=가중값사례수
        """
        # 헤더 셀을 정규화
        cells = [re.sub(r"\s+", " ", str(c or "").strip()) for c in header_row]

        # 마지막 컬럼에 '가중값' 키워드가 있으면 포맷 B
        if cells and self._WEIGHTED_KW in cells[-1]:
            # col2=완료사례수, col3~col[-2]=선택지, col[-1]=가중값
            weighted_col = len(cells) - 1
            return 2, 3, weighted_col

        # 그 외 기본 포맷 A (col3=가중값, col4+=선택지)
        return 2, 4, None

    def parse(self, pages_data: List[PageData]) -> List[QuestionResult]:
        results: List[QuestionResult] = []

        for pg_idx, (outside_text, page_tables, _full_text) in enumerate(pages_data):
            pg = pg_idx + 1  # 1-based 페이지 번호

            if any(marker in outside_text for marker in self._META_PAGE_MARKERS):
                _logger.debug("[KIR] p%d SKIP: 메타 페이지", pg)
                continue
            if len(page_tables) != 1:
                _logger.debug("[KIR] p%d SKIP: 테이블 수=%d (1개여야 함)", pg, len(page_tables))
                continue
            table = page_tables[0]
            if len(table) < 2:
                _logger.debug("[KIR] p%d SKIP: 테이블 행 부족(%d행)", pg, len(table))
                continue

            title_match = self._Q_TITLE_RE.search(outside_text)
            if title_match is None:
                _logger.debug("[KIR] p%d SKIP: 질문 제목 미발견 (outside_text=%r)", pg, outside_text[:80])
                continue
            q_title = re.sub(r"\s+", " ", title_match.group(1)).strip()
            if not q_title:
                _logger.debug("[KIR] p%d SKIP: 질문 제목 빈 문자열", pg)
                continue

            header_row = table[0]
            n_col, opt_start, weighted_col = self._detect_layout(header_row)
            opt_end = weighted_col  # None이면 끝까지

            options = [
                re.sub(r"\s+", " ", str(c or "").strip())
                for c in header_row[opt_start:opt_end]
                if str(c or "").strip()
            ]
            if not options:
                _logger.debug(
                    "[KIR] p%d SKIP: 선택지 없음 (header=%r, opt_start=%d, opt_end=%s)",
                    pg, header_row, opt_start, opt_end,
                )
                continue

            total_row = None
            for row in table[1:4]:
                if str(row[0] or "").strip() in self.TOTAL_MARKERS:
                    total_row = row
                    break
            if total_row is None:
                _logger.debug(
                    "[KIR] p%d SKIP: 전체 행 미발견 (row[0]들=%r)",
                    pg, [str(r[0] or "").strip() for r in table[1:4]],
                )
                continue

            n_completed = extract_sample_count(str(total_row[n_col] or ""))
            if n_completed is None:
                _logger.debug(
                    "[KIR] p%d SKIP: n_completed 추출 실패 (total_row[%d]=%r)",
                    pg, n_col, total_row[n_col],
                )
                continue
            # 가중값 사례수: 포맷 A는 col3, 포맷 B는 마지막 컬럼
            n_weighted: Optional[int] = None
            if weighted_col is not None:
                n_weighted = extract_sample_count(str(total_row[weighted_col] or ""))
            else:
                n_weighted = extract_sample_count(str(total_row[n_col + 1] or ""))

            percentages = self._extract_pct_cells(total_row, start_col=opt_start, end_col=opt_end)
            if not percentages:
                _logger.debug(
                    "[KIR] p%d SKIP: 비율 추출 실패 (total_row[%d:%s]=%r)",
                    pg, opt_start, opt_end, total_row[opt_start:opt_end],
                )
                continue

            options, percentages = filter_summary_columns(
                options, percentages, summary_patterns=self.SUMMARY_PATS
            )
            min_len = min(len(options), len(percentages))
            if min_len == 0:
                _logger.debug(
                    "[KIR] p%d SKIP: filter 후 options/pcts 길이 0 (options=%r, pcts=%r)",
                    pg, options, percentages,
                )
                continue

            _logger.debug(
                "[KIR] p%d OK: q='%s' n=%s opts=%d pcts=%s",
                pg, q_title, n_completed, len(options), percentages[:3],
            )
            results.append(
                QuestionResult(
                    question_number=len(results) + 1,
                    question_title=q_title,
                    question_text=q_title,
                    response_options=options[:min_len],
                    overall_n_completed=n_completed,
                    overall_n_weighted=n_weighted,
                    overall_percentages=percentages[:min_len],
                )
            )

        for i, r in enumerate(results):
            r.question_number = i + 1
        return results


class _GallupParser:
    """한국갤럽조사연구소 파서.

    두 가지 포맷을 처리:
    - 통계표 / 결과집계표: 1페이지 1테이블, full_text에 '표 N. 제목' 마커
    - 결과분석(데일리 오피니언): text_bundled 포맷 (추후 구현)

    공통 구조:
    - 전체 행 마커: Col0 셀에 '■' 또는 공백 포함된 '전      체' 포함
    - col2 = 조사완료 사례수, col3 = 가중값 적용 사례수
    - col4 이후 = 선택지 비율 (정수, '-' → 0)
    - 마지막 컬럼 '계' = 100% skip
    """

    PARSER_KEY = "_GallupParser"

    # 통계표/결과집계표 포맷의 전체 행 마커
    _TOTAL_RE = re.compile(r"■\s*전\s+체\s*■|■\s*전체\s*■")

    # 질문 마커 — 두 가지 패턴 모두 처리
    # 패턴1 (통계표): '표 \n제목\n1. \n'
    # 패턴2 (결과집계표): '표 N. 제목\n'
    _Q_RE1 = re.compile(r"표\s*\n(.+?)\n(\d+)\.\s*\n", re.DOTALL)
    _Q_RE2 = re.compile(r"표\s+(\d+)\.\s+(.+?)(?:\n|$)")

    # 메타 페이지 마커 (skip 대상)
    _META_MARKERS = frozenset({
        "조사 개요", "조사개요", "응답자 특성표", "조사완료 응답자 특성표",
        "목   차", "목차",
    })

    # 결과분석 포맷 감지 마커 (page_tables에 text_bundled 셀 감지)
    _DAILY_MARKER = re.compile(r"데일리 오피니언|교차집계표")

    @staticmethod
    def _cell(val) -> str:
        return re.sub(r"\s+", " ", str(val or "").strip())

    @staticmethod
    def _parse_pct(s: str) -> Optional[float]:
        """'-' → None, '42' → 42.0, '0.1%' → 0.1"""
        s = s.strip().rstrip("%")
        if s in ("-", "", "None"):
            return None
        try:
            v = float(s)
            return v if 0.0 <= v <= 100.0 else None
        except ValueError:
            return None

    def _extract_question(self, full_text: str) -> Optional[tuple]:
        """(q_num_str, q_title) 반환, 없으면 None"""
        m = self._Q_RE1.search(full_text)
        if m:
            return m.group(2).strip(), m.group(1).strip()
        m = self._Q_RE2.search(full_text)
        if m:
            return m.group(1).strip(), m.group(2).strip()
        return None

    def _is_meta_page(self, full_text: str) -> bool:
        return any(marker in full_text[:300] for marker in self._META_MARKERS)

    def _find_total_row(self, df) -> Optional[int]:
        """전체 행 인덱스 반환"""
        for i, row in df.iterrows():
            c0 = self._cell(row.iloc[0])
            if self._TOTAL_RE.search(c0):
                return i
            # '전      체' 단독 셀
            if re.match(r"전\s{2,}체$", c0):
                return i
        return None

    def _extract_options_from_header(self, df, n_completed_col: int) -> list[str]:
        """헤더 행에서 선택지 텍스트 추출 (opt_start ~ 마지막 '계' 컬럼 전)"""
        opt_start = n_completed_col + 2  # col2=완료, col3=가중 → col4부터
        n_cols = df.shape[1]

        # 마지막 컬럼이 '계'인지 확인
        opt_end = n_cols
        for row_idx in range(min(10, len(df))):
            last_cell = self._cell(df.iloc[row_idx, -1])
            if last_cell == "계":
                opt_end = n_cols - 1
                break

        # 헤더 행에서 선택지 수집 (row3이 주로 선택지 텍스트 포함)
        candidates: list[str] = [""] * (opt_end - opt_start)
        for row_idx in range(min(10, len(df))):
            row = df.iloc[row_idx]
            for col_i, col_abs in enumerate(range(opt_start, opt_end)):
                if col_abs >= len(row):
                    break
                cell_text = self._cell(row.iloc[col_abs])
                if cell_text and cell_text not in ("%", "None"):
                    if not candidates[col_i]:
                        candidates[col_i] = cell_text
                    else:
                        # 멀티라인 헤더 병합
                        candidates[col_i] = candidates[col_i] + " " + cell_text

        return [c.strip() for c in candidates]

    def _parse_stats_page(self, full_text: str, df) -> Optional["QuestionResult"]:
        """통계표/결과집계표 한 페이지를 파싱해 QuestionResult 반환"""
        # 질문 추출
        q_info = self._extract_question(full_text)
        if q_info is None:
            _logger.debug("[Gallup] 질문 마커 없음, SKIP")
            return None

        q_num_str, q_title = q_info

        # 전체 행 찾기
        total_row_idx = self._find_total_row(df)
        if total_row_idx is None:
            _logger.debug("[Gallup] Q%s SKIP: 전체 행 미발견", q_num_str)
            return None

        total_row = df.iloc[total_row_idx]

        # n_completed: col2
        n_completed = extract_sample_count(self._cell(total_row.iloc[2]))
        if n_completed is None:
            _logger.debug("[Gallup] Q%s SKIP: n_completed 추출 실패 (col2=%r)", q_num_str, total_row.iloc[2])
            return None

        # n_weighted: col3
        n_weighted = extract_sample_count(self._cell(total_row.iloc[3]))

        # 선택지 추출
        options = self._extract_options_from_header(df, n_completed_col=2)

        # 비율 추출 (전체 행 col4+)
        opt_start = 4
        opt_end = 4 + len(options)
        raw_pcts = []
        for col_abs in range(opt_start, min(opt_end, df.shape[1])):
            raw_pcts.append(self._parse_pct(self._cell(total_row.iloc[col_abs])))

        # None → 0.0 변환, 유효 비율만 필터
        percentages = [p if p is not None else 0.0 for p in raw_pcts]

        if not any(p > 0 for p in percentages):
            _logger.debug("[Gallup] Q%s SKIP: 비율 전부 0 또는 None", q_num_str)
            return None

        # 요약 컬럼 필터 (합산 등)
        options, percentages = filter_summary_columns(
            options, percentages, summary_patterns=DEFAULT_SUMMARY_PATTERNS
        )
        min_len = min(len(options), len(percentages))
        if min_len == 0:
            _logger.debug("[Gallup] Q%s SKIP: filter 후 0건", q_num_str)
            return None

        _logger.debug(
            "[Gallup] Q%s OK: '%s' n=%d opts=%d pcts=%s",
            q_num_str, q_title[:30], n_completed, min_len, percentages[:3],
        )

        return QuestionResult(
            question_number=int(q_num_str) if q_num_str.isdigit() else 0,
            question_title=q_title,
            question_text=q_title,
            response_options=options[:min_len],
            overall_n_completed=n_completed,
            overall_n_weighted=n_weighted,
            overall_percentages=percentages[:min_len],
        )

    def _is_daily_format(self, pages_data) -> bool:
        """결과분석(데일리 오피니언) 포맷인지 감지"""
        for outside_text, _, full_text in pages_data[:3]:
            if self._DAILY_MARKER.search(full_text or outside_text or ""):
                return True
        return False

    def _parse_daily(self, pages_data) -> list["QuestionResult"]:
        """결과분석(데일리 오피니언) 포맷 파싱.

        각 페이지의 첫 번째 테이블에서 전체(row 인덱스 1) 행을 파싱.
        헤더(row 0)에서 컬럼명, row 1의 전체 행에서 비율 추출.
        셀 값은 단일 값이거나 개행으로 여러 값이 묶인 text_bundled 형태.
        전국 정기조사이므로 n_completed/n_weighted는 1,001 등 전체.
        """
        results = []
        seen_titles: set[str] = set()

        for pg_idx, (outside_text, page_tables, full_text) in enumerate(pages_data):
            pg = pg_idx + 1
            if not page_tables:
                continue

            ft = full_text or outside_text or ""

            # 질문 제목 추출: outside_text에서 '질문)' 이전 첫 줄을 제목으로 사용
            # '대통령 직무 수행 평가 질문) ...' → '대통령 직무 수행 평가'
            # '질문) ...' 만 있는 경우 → 첫 줄 전체 (문항 내용)
            ot = (outside_text or "").strip()
            if "질문)" in ot:
                before_q = ot.split("질문)")[0].strip()
                q_title_raw = before_q if before_q else ot.split("\n")[0].strip()
            else:
                q_title_raw = ot.split("\n")[0].strip()
            if not q_title_raw:
                q_title_raw = ft.strip().split("\n")[0].strip()
            if not q_title_raw or q_title_raw in seen_titles:
                continue
            # 메타 페이지 제외
            if self._is_meta_page(ft):
                continue

            # 첫 번째 테이블
            table = page_tables[0]
            if len(table) < 2:
                continue

            # 헤더 행(0): 선택지 컬럼명
            header = [self._cell(c) for c in table[0]]

            # 전체 행 찾기: '전체' 또는 '1,001' 포함하는 첫 번째 데이터 행
            total_row = None
            for row in table[1:]:
                c0 = self._cell(row[0])
                if c0 in ("전체", "전      체") or self._TOTAL_RE.search(c0):
                    total_row = row
                    break
                # 전체 셀이 빈 경우 row[1]이 사례수인 경우
                c1 = self._cell(row[1])
                if re.match(r"[\d,]+$", c1) and not c0:
                    total_row = row
                    break

            if total_row is None:
                _logger.debug("[Gallup-Daily] p%d SKIP: 전체 행 없음", pg)
                continue

            # 사례수: col1(조사완료) 또는 col2(가중적용)
            n_completed = extract_sample_count(self._cell(total_row[1]))
            n_weighted = extract_sample_count(self._cell(total_row[2])) if len(total_row) > 2 else None

            if n_completed is None:
                _logger.debug("[Gallup-Daily] p%d SKIP: n_completed 없음", pg)
                continue

            # 선택지와 비율 추출 (col3부터, 마지막 '계' 전까지)
            opt_start = 3
            opt_end = len(header)
            # 마지막 '없음 모름' or 응답거절 컬럼 detect (포함)
            # '계' 컬럼 제외
            if header and header[-1] in ("계", ""):
                opt_end = len(header) - 1

            options = []
            percentages = []
            for col_i in range(opt_start, opt_end):
                if col_i >= len(header) or col_i >= len(total_row):
                    break
                opt_text = header[col_i]
                pct_text = self._cell(total_row[col_i])
                if not opt_text:
                    continue
                pct = self._parse_pct(pct_text.split("\n")[0])  # text_bundled → 첫 값(전체)
                if pct is None:
                    continue
                options.append(opt_text)
                percentages.append(pct)

            if not options or not any(p > 0 for p in percentages):
                _logger.debug("[Gallup-Daily] p%d SKIP: 비율 없음", pg)
                continue

            options, percentages = filter_summary_columns(
                options, percentages, summary_patterns=DEFAULT_SUMMARY_PATTERNS
            )
            min_len = min(len(options), len(percentages))
            if min_len == 0:
                continue

            seen_titles.add(q_title_raw)
            _logger.debug(
                "[Gallup-Daily] p%d OK: '%s' n=%d opts=%d",
                pg, q_title_raw[:30], n_completed, min_len,
            )
            results.append(
                QuestionResult(
                    question_number=len(results) + 1,
                    question_title=q_title_raw,
                    question_text=q_title_raw,
                    response_options=options[:min_len],
                    overall_n_completed=n_completed,
                    overall_n_weighted=n_weighted,
                    overall_percentages=percentages[:min_len],
                )
            )

        for i, r in enumerate(results):
            r.question_number = i + 1
        return results

    def parse(self, pages_data) -> list["QuestionResult"]:
        # 결과분석(데일리) 포맷 감지
        if self._is_daily_format(pages_data):
            _logger.debug("[Gallup] 데일리 오피니언 포맷 감지")
            return self._parse_daily(pages_data)

        # 통계표 / 결과집계표 포맷
        results = []
        for pg_idx, (outside_text, page_tables, full_text) in enumerate(pages_data):
            pg = pg_idx + 1
            ft = full_text or outside_text or ""

            if not page_tables:
                continue

            if self._is_meta_page(ft):
                _logger.debug("[Gallup] p%d SKIP: 메타 페이지", pg)
                continue

            # 테이블을 DataFrame으로 변환
            table = page_tables[0]
            if len(table) < 5:
                _logger.debug("[Gallup] p%d SKIP: 테이블 행 %d개 (너무 적음)", pg, len(table))
                continue

            import pandas as pd
            df = pd.DataFrame(table)

            result = self._parse_stats_page(ft, df)
            if result is not None:
                results.append(result)

        for i, r in enumerate(results):
            r.question_number = i + 1
        return results


class _InnertecParser:
    """(주)이너텍시스템즈 크로스탭 PDF 파서.

    포맷 특성:
      - 챕터 4 (교차분석통계표)에서만 파싱 (챕터 3은 도표+크로스탭 혼재로 스킵)
      - 각 페이지 = 1 질문 (1 문항 × 1 페이지)
      - 질문 제목: 3행짜리 소형 heading 테이블의 row[1][1] 'N. 제목' 패턴
      - 교차분석 테이블 구조:
          row 0    : 빈 행
          row 1    : 질문 텍스트 (col2, 병합)
          row 2    : 빈 행
          row[조사완료] : col2='조사완료', 마지막 열='가중값적용'
          row[조사완료+1]: col3~N-2 = 선택지 이름 (row[조사완료+2]: 이름 suffix)
          row[조사완료+2]: col2='사례수', 마지막 열='사례수'
          '합 계' 행  : col0='합 계', col2=N완료, col3~N-2=%비율, col[-1]=N가중
      - META_COLS = 3 (col0: 구분, col1: 세부, col2: N_completed)
    """

    PARSER_KEY = "_InnertecParser"
    # '제 N 장. 교차분석통계표' 형태만 매칭 (TOC의 '4. 교차분석통계표'는 제외)
    _CHAP4_RE = re.compile(r"제\s*\d+\s*장[\.\s]*교차분석통계표")
    _Q_TITLE_RE = re.compile(r"^(\d+)\.\s+(.{2,50})$")
    _TOTAL_RE = re.compile(r"^합\s*계$")
    _META_PAGE_RE = re.compile(r"조사의\s*개요|표본의\s*특성|피조사자\s*접촉현황|설문\s*지|질문지")

    @staticmethod
    def _cell(val: object) -> str:
        return (val or "").strip() if val is not None else ""

    def _find_crosstab_table(self, page_tables: List) -> Optional[List]:
        """페이지 테이블 목록에서 교차분석 테이블(대형, ≥10행 ≥8열)을 찾는다."""
        for t in page_tables:
            if len(t) >= 10 and t[0] is not None and len(t[0]) >= 8:
                return t
        return None

    def _extract_question_title(self, page_tables: List) -> Optional[tuple]:
        """3행짜리 소형 heading 테이블에서 (question_number, title) 추출."""
        for t in page_tables:
            if len(t) != 3:
                continue
            row1 = t[1]
            for cell in row1:
                if not cell:
                    continue
                m = self._Q_TITLE_RE.match(cell.strip())
                if m and "장" not in m.group(2) and "교차분석" not in m.group(2):
                    return int(m.group(1)), m.group(2).strip()
        return None

    def _find_조사완료_row_idx(self, table: List) -> Optional[int]:
        """'조사완료'가 있는 헤더 행 인덱스를 반환한다."""
        for i, row in enumerate(table):
            if any(cell and "조사완료" in cell for cell in (row or [])):
                return i
        return None

    def _build_options(self, table: List, header_start: int) -> tuple:
        """헤더 행(3행) 기반으로 (options, data_col_end) 반환.

        Returns:
            options: 선택지 이름 목록 (col3 ~ data_col_end)
            data_col_end: 마지막 데이터 컬럼 인덱스 (inclusive)
        """
        header_rows = table[header_start:header_start + 3]
        n_cols = max(len(r) for r in header_rows if r) if header_rows else 0

        # 마지막 '사례수' 컬럼(=N_weighted)을 제외하기 위해 우측부터 탐색
        data_col_end = n_cols - 1
        for row in header_rows:
            for c_i in range(n_cols - 1, 2, -1):
                if row and c_i < len(row) and row[c_i] and "사례수" in row[c_i]:
                    data_col_end = c_i - 1
                    break

        META_COLS = 3  # col0: 구분1, col1: 구분2, col2: N_completed
        options: List[str] = []
        for col_i in range(META_COLS, data_col_end + 1):
            parts = []
            for row in header_rows:
                if not row or col_i >= len(row):
                    continue
                val = self._cell(row[col_i])
                if val and val not in ("%",):
                    parts.append(val)
            options.append(" ".join(parts) if parts else f"선택지{col_i - META_COLS + 1}")

        return options, data_col_end

    def parse(self, pages_data: List[PageData]) -> List[QuestionResult]:
        results: List[QuestionResult] = []
        in_chap4 = False

        for pg_idx, (outside_text, page_tables, full_text) in enumerate(pages_data):
            pg = pg_idx + 1
            ft = full_text or outside_text or ""

            # 챕터 4 시작 감지
            if self._CHAP4_RE.search(ft):
                in_chap4 = True

            if not in_chap4:
                continue

            if not page_tables:
                _logger.debug("[Innertec] p%d SKIP: 테이블 없음", pg)
                continue

            # 메타 페이지 스킵
            if self._META_PAGE_RE.search(ft):
                _logger.debug("[Innertec] p%d SKIP: 메타 페이지", pg)
                continue

            # 교차분석 테이블 찾기
            crosstab = self._find_crosstab_table(page_tables)
            if crosstab is None:
                _logger.debug("[Innertec] p%d SKIP: 교차분석 테이블 없음 (%d개 테이블)", pg, len(page_tables))
                continue

            # 질문 제목 추출 (소형 heading 테이블)
            q_info = self._extract_question_title(page_tables)
            if q_info is None:
                _logger.debug("[Innertec] p%d SKIP: 질문 제목 없음", pg)
                continue
            q_num, q_title = q_info

            # 헤더 행 ('조사완료' 포함 행) 위치
            header_idx = self._find_조사완료_row_idx(crosstab)
            if header_idx is None:
                _logger.debug("[Innertec] p%d SKIP: 조사완료 헤더 없음", pg)
                continue

            # 선택지 및 데이터 컬럼 범위
            options, data_col_end = self._build_options(crosstab, header_idx)
            if not options:
                _logger.debug("[Innertec] p%d SKIP: 선택지 추출 실패", pg)
                continue

            # '합 계' 데이터 행 탐색
            total_row: Optional[List] = None
            for row in crosstab[header_idx + 3:]:
                if row and self._TOTAL_RE.match(self._cell(row[0])):
                    total_row = row
                    break

            if total_row is None:
                _logger.debug("[Innertec] p%d SKIP: 합 계 행 없음", pg)
                continue

            # N_completed (col2)
            n_completed = extract_sample_count(self._cell(total_row[2]) if len(total_row) > 2 else "")
            if n_completed is None:
                _logger.debug("[Innertec] p%d SKIP: N_completed 추출 실패", pg)
                continue

            # N_weighted (data_col_end+1)
            n_weighted: Optional[int] = None
            n_w_idx = data_col_end + 1
            if n_w_idx < len(total_row):
                n_weighted = extract_sample_count(self._cell(total_row[n_w_idx]))

            # 비율 추출 (col3 ~ data_col_end)
            META_COLS = 3
            percentages: List[float] = []
            for col_i in range(META_COLS, data_col_end + 1):
                if col_i >= len(total_row):
                    break
                raw = self._cell(total_row[col_i])
                # "XX.X%" 또는 "XX.X" 형태 허용
                pct_m = re.match(r"(\d{1,3}(?:\.\d+)?)\s*%?$", raw)
                if pct_m:
                    percentages.append(float(pct_m.group(1)))

            if not percentages:
                _logger.debug("[Innertec] p%d SKIP: 비율 없음", pg)
                continue

            options, percentages = filter_summary_columns(
                options, percentages, summary_patterns=DEFAULT_SUMMARY_PATTERNS
            )
            min_len = min(len(options), len(percentages))
            if min_len == 0:
                _logger.debug("[Innertec] p%d SKIP: filter 후 0건", pg)
                continue

            _logger.debug(
                "[Innertec] p%d OK: Q%d '%s' n=%d opts=%d pcts=%s",
                pg, q_num, q_title[:20], n_completed, min_len, percentages[:3],
            )
            results.append(QuestionResult(
                question_number=q_num,
                question_title=q_title,
                question_text=q_title,
                response_options=options[:min_len],
                overall_n_completed=n_completed,
                overall_n_weighted=n_weighted,
                overall_percentages=percentages[:min_len],
            ))

        for i, r in enumerate(results):
            r.question_number = i + 1
        return results


class _ResearchViewParser:
    """리서치뷰 크로스탭 PDF 파서.

    포맷 특성:
      - 1 질문 = 1 페이지 = 1 테이블
      - 질문 페이지 식별: row[0][0]이 'N. 제목\n(%)' 패턴과 일치
      - 표준 포맷: row[N][0]=='전 체'인 행 사용 (지역 여론조사)
      - 추이 포맷: row[2][0]가 날짜 패턴 (전국정기조사) →
        인구통계 행 이전의 마지막 날짜 행 = 최신 조사 결과
      - col[2]: 조사완료 사례수, col[3]: 가중값적용 사례수, col[4+]: 비율
      - META_COLS = 4
      - '없음', '모름', '없음/모름' 컬럼 필터링
    """

    PARSER_KEY = "_ResearchViewParser"
    _Q_TITLE_RE = re.compile(r"^(\d+)\.\s+(.+?)(?:\n|\s*\(%\)|\s*$)", re.DOTALL)
    _TOTAL_MARKER = "전 체"
    _DATE_ROW_RE = re.compile(r"^\d{4}년")  # "2026년 3월..." 패턴
    _DEMO_KEYS = {"성별", "연령", "남성", "여성", "지역", "직업", "학력"}
    META_COLS = 4
    _SUMMARY_PATS = DEFAULT_SUMMARY_PATTERNS + (
        re.compile(r"^없음$"),
        re.compile(r"^모름$"),
        re.compile(r"^없음\s*/\s*모름$|^없음모름$"),
        re.compile(r"^모름\s*/\s*기타$|^모름기타$"),
    )

    @staticmethod
    def _cell(val: object) -> str:
        return (val or "").strip() if val is not None else ""

    def _parse_q_title(self, table: List) -> Optional[tuple]:
        """테이블 row[0][0]에서 질문 번호·제목 추출."""
        if not table or not table[0]:
            return None
        raw = self._cell(table[0][0])
        m = self._Q_TITLE_RE.match(raw)
        if not m:
            return None
        title = m.group(2).strip()
        title = re.sub(r"\s*\(%\)\s*$", "", title).strip()
        return int(m.group(1)), title

    def _build_options(self, table: List) -> List[str]:
        """row[1][META_COLS:]에서 선택지 이름 추출."""
        if len(table) < 2:
            return []
        header = table[1]
        options = []
        for col_i in range(self.META_COLS, len(header)):
            val = self._cell(header[col_i])
            val = val.replace("\n", " ").strip()
            options.append(val if val else f"선택지{col_i - self.META_COLS + 1}")
        return options

    def _find_total_row(self, table: List) -> Optional[List]:
        """전체/최신 데이터 행 탐색.

        - 표준 포맷: '전 체' 행 반환
        - 추이 포맷: 인구통계 행 이전의 마지막 날짜 행 반환
        """
        # 표준 포맷 우선
        for row in table[2:]:
            if row and self._cell(row[0]) == self._TOTAL_MARKER:
                return row
        # 추이 포맷: row[2][0]가 날짜 패턴인 경우
        if len(table) > 2 and table[2] and self._DATE_ROW_RE.match(self._cell(table[2][0])):
            last_date_row = None
            for row in table[2:]:
                if not row:
                    continue
                v = self._cell(row[0])
                if self._DATE_ROW_RE.match(v):
                    last_date_row = row
                elif v in self._DEMO_KEYS or (row[1] and self._cell(row[1]) in self._DEMO_KEYS):
                    break
            return last_date_row
        return None

    def parse(self, pages_data: List[PageData]) -> List[QuestionResult]:
        results: List[QuestionResult] = []
        for _pg_idx, (_outside_text, page_tables, _full_text) in enumerate(pages_data):
            if not page_tables:
                continue
            for table in page_tables:
                q_info = self._parse_q_title(table)
                if q_info is None:
                    continue
                q_num, q_title = q_info

                total_row = self._find_total_row(table)
                if total_row is None:
                    continue

                if len(total_row) <= self.META_COLS:
                    continue

                n_completed = extract_sample_count(
                    self._cell(total_row[2]) if len(total_row) > 2 else ""
                )
                if n_completed is None:
                    continue
                n_weighted = extract_sample_count(
                    self._cell(total_row[3]) if len(total_row) > 3 else ""
                )

                options = self._build_options(table)
                percentages: List[float] = []
                for col_i in range(self.META_COLS, len(total_row)):
                    raw = self._cell(total_row[col_i])
                    m = re.match(r"(\d{1,3}(?:\.\d+)?)\s*%?$", raw)
                    if m:
                        percentages.append(float(m.group(1)))

                if not percentages:
                    continue

                min_len = min(len(options), len(percentages))
                if min_len == 0:
                    continue

                options, percentages = filter_summary_columns(
                    options[:min_len],
                    percentages[:min_len],
                    summary_patterns=self._SUMMARY_PATS,
                )
                if not percentages:
                    continue

                results.append(QuestionResult(
                    question_number=q_num,
                    question_title=q_title,
                    question_text=q_title,
                    response_options=options,
                    overall_n_completed=n_completed,
                    overall_n_weighted=n_weighted,
                    overall_percentages=percentages,
                ))

        # 중복 제거: 같은 질문번호가 여러 번 나오면 첫 번째만 유지
        seen: set = set()
        unique: List[QuestionResult] = []
        for r in results:
            if r.question_number not in seen:
                seen.add(r.question_number)
                unique.append(r)
        return unique


class _MonoCommunicationsParser:
    """모노커뮤니케이션즈(모노리서치) 크로스탭 결과보고서 PDF 파서.

    포맷 특성:
      - 결과보고서 형식: 1질문 = 요약페이지 + 크로스탭 페이지 2장 이상
      - 질문 마커: 페이지 텍스트의 '[QN – 제목상세결과]' 패턴
      - 크로스탭 테이블 식별: row[1][0]=None, row[1][2]=N완료 (숫자)
      - row[0][2]: '조사완료사례수' (N 헤더), row[0][3:-1]: 선택지 이름
      - row[1][2]: N_completed, row[1][3:-1]: 비율, row[1][-1]: N_weighted
      - 각 질문이 2+ 페이지에 반복 → 첫 번째 크로스탭만 사용 (중복 제거)
      - '잘모름/무응답', '지지후보없거나잘모름', '가중적용사례' 컬럼 필터링
    """

    PARSER_KEY = "_MonoCommunicationsParser"
    _Q_MARKER_RE = re.compile(r"\[Q(\d+)\s*[–\-]\s*(.+?)(?:상세결과)?\]")
    _META_COLS = 3  # col0: 그룹, col1: 서브, col2: N_completed
    _SUMMARY_PATS = DEFAULT_SUMMARY_PATTERNS + (
        re.compile(r"잘\s*모름"),
        re.compile(r"무응답"),
        re.compile(r"지지\s*후보\s*없"),
        re.compile(r"가중\s*적용\s*사례"),
        re.compile(r"^없음$"),
        re.compile(r"^모름$"),
    )

    @staticmethod
    def _cell(val: object) -> str:
        return (val or "").strip() if val is not None else ""

    def _is_crosstab_table(self, table: List) -> bool:
        """크로스탭 테이블 판별: row[1][0]=None, row[1][2]가 숫자."""
        if len(table) < 2 or not table[1]:
            return False
        row1 = table[1]
        if len(row1) < 4:
            return False
        if row1[0] is not None:
            return False
        n_val = self._cell(row1[2])
        return bool(re.match(r"^\d+", n_val))

    def parse(self, pages_data: List[PageData]) -> List[QuestionResult]:
        results: List[QuestionResult] = []
        seen_q: set = set()

        for _pg_idx, (_outside_text, page_tables, full_text) in enumerate(pages_data):
            if not page_tables or not full_text:
                continue

            # 크로스탭 테이블 페이지인지 확인 ([QN - 상세결과] + 크로스탭 구조)
            for m in self._Q_MARKER_RE.finditer(full_text):
                q_num = int(m.group(1))
                q_title = m.group(2).strip()
                if q_num in seen_q:
                    continue

                # 크로스탭 테이블 탐색
                for table in page_tables:
                    if not self._is_crosstab_table(table):
                        continue
                    row0 = table[0]
                    row1 = table[1]
                    n_cols = len(row0)

                    # N_completed (row1[2])
                    n_completed = extract_sample_count(self._cell(row1[2]))
                    if n_completed is None:
                        continue

                    # N_weighted (row1[-1])
                    n_weighted = extract_sample_count(self._cell(row1[-1]))

                    # 선택지: row0[3:-1]
                    options = []
                    for c in range(self._META_COLS, n_cols - 1):
                        val = self._cell(row0[c] if c < len(row0) else None)
                        val = val.replace("\n", " ").strip()
                        options.append(val if val else f"선택지{c - self._META_COLS + 1}")

                    # 비율: row1[3:-1]
                    percentages: List[float] = []
                    for c in range(self._META_COLS, n_cols - 1):
                        raw = self._cell(row1[c] if c < len(row1) else None)
                        pm = re.match(r"(\d{1,3}(?:\.\d+)?)\s*%?$", raw)
                        if pm:
                            percentages.append(float(pm.group(1)))

                    if not percentages:
                        continue

                    min_len = min(len(options), len(percentages))
                    if min_len == 0:
                        continue

                    options, percentages = filter_summary_columns(
                        options[:min_len],
                        percentages[:min_len],
                        summary_patterns=self._SUMMARY_PATS,
                    )
                    if not percentages:
                        continue

                    results.append(QuestionResult(
                        question_number=q_num,
                        question_title=q_title,
                        question_text=q_title,
                        response_options=options,
                        overall_n_completed=n_completed,
                        overall_n_weighted=n_weighted,
                        overall_percentages=percentages,
                    ))
                    seen_q.add(q_num)
                    break  # 이 페이지에서 이 질문 완료

        return sorted(results, key=lambda r: r.question_number)
