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
            tables = [_decode_table(t.extract(), gid_map) for t in finder.tables]
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
                tables = [t.extract() for t in finder.tables]
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
      - PyMuPDF 셀 병합 문제로 비율을 full_text에서 추출
      - 페이지 분할 표 merge 지원 (같은 q_num이 여러 페이지에 걸침)
      - 헤더 row[0][0]='전체' (다른 파서의 '구분'과 다름)
    """

    PARSER_KEY = "_KoreanResearchParser"

    _TABLE_TITLE_RE = re.compile(r"\[표\s*(\d+)\]\s+(.+)")
    _Q_TEXT_RE = re.compile(r"\[문\s*\d+\]\s+(.+?)(?:\?|？)", re.DOTALL)
    _TOTAL_ROW_RE = re.compile(
        r"▣ 전체 ▣\s+\(([\d,]+)\)\s+\(([\d,]+)\)\s+((?:[\d.]+\s*)+)"
    )
    _SUMMARY_COL_RE = re.compile(r"^T[12]|^B[12]|\(1\+2\)|\(3\+4\)|^계$")
    _META_COLS = 3

    def parse(self, pages_data: List[PageData]) -> List[QuestionResult]:
        result_map: dict = {}

        for page_text, page_tables, full_text in pages_data:
            title_match = self._TABLE_TITLE_RE.search(page_text)
            if not title_match:
                continue
            q_num = int(title_match.group(1))

            options = self._extract_options_kr(page_tables)
            if not options:
                continue

            total_match = self._TOTAL_ROW_RE.search(full_text)
            if not total_match:
                continue

            n_completed = int(total_match.group(1).replace(",", ""))
            n_weighted = int(total_match.group(2).replace(",", ""))
            raw_pcts = [float(v) for v in total_match.group(3).split()]

            pairs = [
                (o, p)
                for o, p in zip(options, raw_pcts)
                if not self._SUMMARY_COL_RE.search(re.sub(r"\s+", "", o))
            ]
            if not pairs:
                continue
            options_f, pcts_f = zip(*pairs)
            min_len = min(len(options_f), len(pcts_f))
            if min_len == 0:
                continue

            page_options = list(options_f[:min_len])
            page_pcts = list(pcts_f[:min_len])

            if q_num in result_map:
                existing = result_map[q_num]
                if page_pcts and abs(page_pcts[-1] - 100.0) < 1.0:
                    page_options = page_options[:-1]
                    page_pcts = page_pcts[:-1]
                if page_options:
                    existing.response_options = existing.response_options + page_options
                    existing.overall_percentages = existing.overall_percentages + page_pcts
                continue

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

        return list(result_map.values())

    def _extract_options_kr(self, page_tables: List) -> List[str]:
        for table in page_tables:
            if not table or len(table) < 2:
                continue
            header = table[0]
            if not header or str(header[0] or "").strip() != "전체":
                continue
            return extract_options_from_row(header, start_col=self._META_COLS)
        return []


class _SignalPulseParser(BaseTableParser):
    """시그널앤펄스 크로스탭 파서.

    두 가지 PDF 버전:
      - 신버전 ([표N]): 텍스트에서 '▣ 전 체 ▣' 비율 추출
      - 구버전 ([QN]): 테이블 '합계' 행에서 비율 추출
    """

    PARSER_KEY = "_SignalPulseParser"

    _PYO_TITLE_RE = re.compile(r"\[표\s*(\d+)\]\s+(.+)")
    _Q_TITLE_RE = re.compile(r"\[Q(\d+)\]\s+\[(.+)\]")
    _TOTAL_TEXT_RE = re.compile(
        r"▣ 전 체 ▣\s+([\d,]+)\s+([\d,]+)\s+((?:[\d.]+\s*)+)"
    )
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
      - 텍스트에서 '전체 (N완료) (N가중) p1 p2 ...' 패턴으로 비율 추출
      - 테이블 헤더에서 선택지 추출 (col 0에 '구' 포함 여부로 식별)
      - seen_q_nums로 중복 페이지 방지
    """

    PARSER_KEY = "_RealMeterParser"

    _Q_SECTION_RE = re.compile(r"(?m)^(\d+)\.\s+(.+)$")
    _Q_TEXT_RE = re.compile(r"Q\d+\.\s+(.+?)(?:\?|？)", re.DOTALL)
    _TOTAL_ROW_RE = re.compile(
        r"전체\s+\((\d+)\)\s+\((\d+)\)\s+((?:[\d.]+\s*)+)"
    )
    _HEADER_META_COLS = 4
    _SUMMARY_OPT_RE = re.compile(r"[①②③④⑤⑥⑦⑧⑨⑩]\s*\+\s*[①②③④⑤⑥⑦⑧⑨⑩]")

    def parse(self, pages_data: List[PageData]) -> List[QuestionResult]:
        results: List[QuestionResult] = []
        seen_q_nums: set = set()

        for page_text, page_tables, full_text in pages_data:
            q_section_match = self._Q_SECTION_RE.search(page_text)
            if not q_section_match:
                continue
            q_num = int(q_section_match.group(1))
            if q_num in seen_q_nums:
                continue

            options = self._extract_header_options(page_tables)
            if not options:
                continue

            total_match = self._TOTAL_ROW_RE.search(full_text)
            if not total_match:
                continue
            n_completed = int(total_match.group(1))
            n_weighted = int(total_match.group(2))
            percentages = [float(v) for v in total_match.group(3).split()]

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

            seen_q_nums.add(q_num)
            results.append(QuestionResult(
                question_number=q_num,
                question_title=q_title,
                question_text=q_text,
                response_options=options[:min_len],
                overall_n_completed=n_completed,
                overall_n_weighted=n_weighted,
                overall_percentages=percentages[:min_len],
            ))

        return results

    def _extract_header_options(self, page_tables: List) -> List[str]:
        for table in page_tables:
            if not table or len(table) < 2:
                continue
            header = table[0]
            if len(header) <= self._HEADER_META_COLS:
                continue
            if "구" not in str(header[0] or ""):
                continue
            return extract_options_from_row(header, start_col=self._HEADER_META_COLS)
        return []


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
