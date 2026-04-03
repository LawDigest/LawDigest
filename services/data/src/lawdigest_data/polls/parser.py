"""여론조사 결과표 PDF 파서."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .models import QuestionResult

# config/ 디렉터리 기본 경로
_DEFAULT_CONFIG_DIR = Path(__file__).resolve().parents[4] / "config"


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


def _extract_text_outside_tables(page: "fitz.Page", finder: "fitz.TableFinder") -> str:  # type: ignore[name-defined]
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


class PollResultParser:
    """결과표 PDF에서 설문 항목별 응답 결과를 추출하는 파서.

    기관별 파서는 parser_registry.json에서 로드하거나,
    registry_path=None 시 config/parser_registry.json을 자동으로 찾는다.
    JSON이 없으면 내장 기본 레지스트리를 사용한다.
    """

    def __init__(self, registry_path: Optional[Path] = None) -> None:
        self._registry: List[_RegistryEntry] = []
        path = registry_path or (_DEFAULT_CONFIG_DIR / "parser_registry.json")
        if path.exists():
            self.load_registry(path)
        else:
            self._load_defaults()

    def load_registry(self, registry_path: Path) -> None:
        """JSON 파일에서 파서 레지스트리를 로드한다."""
        data = json.loads(registry_path.read_text(encoding="utf-8"))
        parser_map = {
            "_TableFormatParser": _TableFormatParser,
            "_TextFormatParser": _TextFormatParser,
            "_RealMeterParser": _RealMeterParser,
            "_KoreanResearchParser": _KoreanResearchParser,
            "_SignalPulseParser": _SignalPulseParser,
            "_EmbrainPublicParser": _EmbrainPublicParser,
            "_FlowerResearchParser": _FlowerResearchParser,
        }
        parsers_def = data.get("parsers", {})
        fallback_name = data.get("fallback_parser", "text_format")

        entries: List[_RegistryEntry] = []

        # parsers 정의의 pollster_names로 엔트리 구성 (priority=10)
        for parser_key, parser_def in parsers_def.items():
            keywords = parser_def.get("pollster_names", [])
            if not keywords:
                continue
            cls = parser_map.get(parser_def.get("class", ""), _TextFormatParser)
            entries.append(_RegistryEntry(
                parser_class=cls,
                pollster_keywords=tuple(keywords),
                priority=10,
            ))

        # 최종 fallback (priority=0)
        fallback_def = parsers_def.get(fallback_name, {})
        fallback_cls = parser_map.get(fallback_def.get("class", ""), _TextFormatParser)
        entries.append(_RegistryEntry(
            parser_class=fallback_cls,
            pollster_keywords=(),
            priority=0,
        ))

        entries.sort(key=lambda e: e.priority, reverse=True)
        self._registry = entries

    def _load_defaults(self) -> None:
        """JSON 파일 없을 때 내장 기본 레지스트리 로드."""
        self._registry = [
            _RegistryEntry(_TableFormatParser, ("조원씨앤아이", "메타서치"), 10),
            _RegistryEntry(_TextFormatParser, ("데일리리서치",), 10),
            _RegistryEntry(_TextFormatParser, (), 0),
        ]

    def parse_pdf(
        self,
        pdf_path: Path,
        pollster_hint: Optional[str] = None,
    ) -> List[QuestionResult]:
        """PDF 파일을 파싱하여 QuestionResult 목록을 반환한다."""
        try:
            import fitz  # PyMuPDF
        except ImportError as exc:
            raise RuntimeError("PDF 파싱을 위해 pymupdf가 필요합니다.") from exc

        pages_data: List[Tuple[str, List, str]] = []
        doc = fitz.open(pdf_path)
        try:
            for page in doc:
                finder = page.find_tables()
                tables = [t.extract() for t in finder.tables]
                full_text = page.get_text() or ""
                # 테이블 외부 텍스트: 섹션 제목 파싱 정확도 향상 (word 단위 재조합)
                outside_text = _extract_text_outside_tables(page, finder) if tables else full_text
                pages_data.append((outside_text, tables, full_text))
        finally:
            doc.close()

        parser_class = self._select_parser("", pollster_hint)

        # GID 디코딩이 필요한 파서(여론조사꽃 등)는 rawdict 모드로 재추출
        if getattr(parser_class, "NEEDS_GID_DECODE", False):
            font_path = getattr(parser_class, "FONT_PATH", None)
            if font_path and Path(font_path).exists():
                gid_map = _build_gid_to_unicode(Path(font_path))
                pages_data = _extract_pages_with_gid_decode(pdf_path, gid_map)

        if issubclass(parser_class, _TableFormatParser):
            return parser_class().parse(pages_data)
        else:
            full_text = "\n".join(ft for _, _, ft in pages_data)
            return parser_class().parse(full_text)

    def _select_parser(self, full_text: str, pollster_hint: Optional[str]) -> type:
        """레지스트리에서 적합한 파서 클래스를 선택한다.

        pollster_hint로 기관명 키워드를 매칭한다.
        매칭되지 않으면 fallback 파서(priority=0)를 반환한다.
        """
        if pollster_hint:
            for entry in self._registry:
                if entry.pollster_keywords and any(
                    kw in pollster_hint for kw in entry.pollster_keywords
                ):
                    return entry.parser_class

        # fallback (priority=0 엔트리)
        for entry in self._registry:
            if entry.priority == 0:
                return entry.parser_class

        return _TextFormatParser


class _TextFormatParser:
    """텍스트 형식 파서 – 데일리리서치 등."""

    _SECTION_NUM_TITLE_RE = re.compile(r"^(\d+)\)\s+(.+)$", re.MULTILINE)
    _OPTION_PCT_RE = re.compile(r"^(.+?)\s+([\d.]+)$")
    _CROSSTAB_MARKERS = ["자료 처리 방법", "교차분석", "교차 분석", "Ⅱ. 조사"]
    _RESULTS_MARKERS = ["설문 항목별 결과", "조사결과", "제2장 조사결과"]

    def parse(self, full_text: str) -> List[QuestionResult]:
        text = self._extract_results_section(full_text)
        sections = list(self._SECTION_NUM_TITLE_RE.finditer(text))
        results: List[QuestionResult] = []
        for i, m in enumerate(sections):
            q_num = int(m.group(1))
            q_title = m.group(2).strip()
            block_start = m.end()
            block_end = sections[i + 1].start() if i + 1 < len(sections) else len(text)
            block = text[block_start:block_end].strip()

            q_text_m = re.search(r"[?？]", block)
            if q_text_m:
                q_text = block[: q_text_m.end()].strip()
                options_block = block[q_text_m.end():]
            else:
                q_text = q_title
                options_block = block

            options: List[str] = []
            percentages: List[float] = []
            for line in options_block.splitlines():
                line = line.strip()
                if not line or line.startswith("☞") or line.startswith("-"):
                    continue
                om = self._OPTION_PCT_RE.match(line)
                if om:
                    opt = om.group(1).strip()
                    pct = float(om.group(2))
                    has_sample_counts = len(re.findall(r"(?<!\w)\d{3,}(?!\w)", opt)) >= 2
                    is_subtotal = opt.endswith(":") or opt.endswith(":")
                    if (
                        1 < len(opt) <= 60
                        and not re.fullmatch(r"[\d().%\-\s]+", opt)
                        and not has_sample_counts
                        and not is_subtotal
                    ):
                        options.append(opt)
                        percentages.append(pct)

            if not percentages:
                continue

            results.append(QuestionResult(
                question_number=q_num,
                question_title=q_title,
                question_text=q_text,
                response_options=options,
                overall_n_completed=None,
                overall_n_weighted=None,
                overall_percentages=percentages,
            ))
        return results

    def _extract_results_section(self, text: str) -> str:
        start = 0
        for marker in self._RESULTS_MARKERS:
            pos = text.find(marker)
            if pos != -1:
                start = pos
                break
        end = len(text)
        for marker in self._CROSSTAB_MARKERS:
            pos = text.find(marker, start)
            if pos != -1 and pos < end:
                end = pos
        return text[start:end]


class _TableFormatParser:
    """테이블 형식 파서 – 조원씨앤아이, 메타서치 등."""

    _SECTION_RE = re.compile(r"^문?(\d+)[.)]\s+([^\n]+)$", re.MULTILINE)
    _N_RE = re.compile(r"\((\d+)\)")
    _SUBTOTAL_RE = re.compile(r"\(합\)|합계|소계")

    def parse(self, pages_data: List[Tuple[str, List, str]]) -> List[QuestionResult]:
        results: List[QuestionResult] = []
        for page_text, page_tables, _full_text in pages_data:
            for table in page_tables:
                result = self._parse_table(table, page_text)
                if result is not None:
                    results.append(result)
        for i, r in enumerate(results):
            r.question_number = i + 1
        return results

    def _parse_table(self, table: List[List], page_text: str) -> Optional[QuestionResult]:
        if not table or len(table) < 2:
            return None

        total_row: Optional[List] = None
        for row in table[1:]:
            if row and row[0] and "전체" in str(row[0]):
                total_row = row
                break
        if total_row is None:
            return None

        header_row = table[0]
        n_completed = self._extract_n(str(total_row[2] if len(total_row) > 2 else ""))
        n_weighted = self._extract_n(str(total_row[-1]))

        options: List[str] = []
        percentages: List[float] = []
        for header_cell, value_cell in zip(header_row[3:-1], total_row[3:-1]):
            opt = re.sub(r"[\n\x00]", "", str(header_cell or "")).strip()
            if not opt or opt.lower() == "none" or self._SUBTOTAL_RE.search(opt):
                continue
            try:
                pct = float(str(value_cell or "").strip())
            except ValueError:
                continue
            options.append(opt)
            percentages.append(pct)

        if not percentages:
            return None

        seen: set = set()
        deduped_options: List[str] = []
        deduped_pcts: List[float] = []
        for opt, pct in zip(options, percentages):
            key = (opt, pct)
            if key not in seen:
                seen.add(key)
                deduped_options.append(opt)
                deduped_pcts.append(pct)
        options, percentages = deduped_options, deduped_pcts

        section_matches = list(self._SECTION_RE.finditer(page_text.replace("\x00", "")))
        if section_matches:
            q_num = int(section_matches[0].group(1))
            q_title = section_matches[0].group(2).strip()
        else:
            q_num = 0
            q_title = ""

        return QuestionResult(
            question_number=q_num,
            question_title=q_title,
            question_text="",
            response_options=options,
            overall_n_completed=n_completed,
            overall_n_weighted=n_weighted,
            overall_percentages=percentages,
        )

    def _extract_n(self, text: str) -> Optional[int]:
        text = text.strip()
        m = self._N_RE.search(text)
        if m:
            return int(m.group(1))
        try:
            return int(text)
        except ValueError:
            return None


class _KoreanResearchParser(_TableFormatParser):
    """한국리서치 크로스탭 PDF 파서.

    PDF 구조:
      - 질문 제목: '[표 N] 제목', 질문문: '[문N] 질문문?' 패턴
      - 테이블 헤더 row 0: ['전체', '사례수 (명)', None, opt1, ..., '계']
      - 전체 행 텍스트: '▣ 전체 ▣ (1,000) (1,000) p1 p2 ... 100'
      - PyMuPDF 테이블 추출 시 % 컬럼이 병합(None)될 수 있어 full_text에서 비율 추출
      - T2/B2/(1+2)/(3+4) 소계 컬럼 및 '계' 컬럼 제거
    """

    _TABLE_TITLE_RE = re.compile(r"\[표\s*(\d+)\]\s+(.+)")
    _Q_TEXT_RE = re.compile(r"\[문\s*\d+\]\s+(.+?)(?:\?|？)", re.DOTALL)
    _TOTAL_ROW_RE = re.compile(
        r"▣ 전체 ▣\s+\(([\d,]+)\)\s+\(([\d,]+)\)\s+((?:[\d.]+\s*)+)"
    )
    _SUMMARY_COL_RE = re.compile(r"^T[12]|^B[12]|\(1\+2\)|\(3\+4\)|^계$")
    _META_COLS = 3  # '전체', '사례수 (명)', None

    def parse(self, pages_data: List[Tuple[str, List, str]]) -> List[QuestionResult]:
        # q_num → QuestionResult (페이지 분할 표 merge 지원)
        result_map: dict = {}

        for page_text, page_tables, full_text in pages_data:
            title_match = self._TABLE_TITLE_RE.search(page_text)
            if not title_match:
                continue
            q_num = int(title_match.group(1))

            options = self._extract_options_kr(page_tables)
            if not options:
                continue

            # 전체 행 비율은 테이블 셀 내부에 있으므로 full_text에서 검색
            total_match = self._TOTAL_ROW_RE.search(full_text)
            if not total_match:
                continue

            n_completed = int(total_match.group(1).replace(",", ""))
            n_weighted = int(total_match.group(2).replace(",", ""))
            raw_pcts = [float(v) for v in total_match.group(3).split()]

            # 소계 컬럼 쌍 제거 후 길이 맞춤
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
                # 페이지 분할된 표의 속편 — 기존 결과에 옵션/비율 추가
                existing = result_map[q_num]
                # 마지막 컬럼이 합계(≈100)이면 제거
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
        """헤더 row 0 col 3+ 에서 선택지 추출 (col 0 == '전체' 기준 식별)."""
        for table in page_tables:
            if not table or len(table) < 2:
                continue
            header = table[0]
            if not header or str(header[0] or "").strip() != "전체":
                continue
            options: List[str] = []
            for cell in header[self._META_COLS :]:
                opt = re.sub(r"[\n\x00]", "", str(cell or "")).strip()
                if not opt or opt.lower() == "none":
                    continue
                options.append(opt)
            if options:
                return options
        return []


class _SignalPulseParser(_TableFormatParser):
    """시그널앤펄스 크로스탭 PDF 파서.

    두 가지 PDF 버전을 처리한다:
      - 신버전 ([표N] 형식): 테이블 row 0 에 '[표N] 제목', 전체 비율은 텍스트에서 추출
        '▣ 전 체 ▣ 1,000 1,000 p1 p2 ...'
      - 구버전 ([QN] 형식): 테이블 row 0 에 '[QN] [제목]', 전체 행('합계')이 테이블에 있음
    한 질문이 여러 페이지에 걸쳐 반복됨 → seen_q_nums 중복 방지
    """

    _PYO_TITLE_RE = re.compile(r"\[표\s*(\d+)\]\s+(.+)")   # 신버전: [표N] 제목
    _Q_TITLE_RE = re.compile(r"\[Q(\d+)\]\s+\[(.+)\]")     # 구버전: [Q1] [제목]
    _TOTAL_TEXT_RE = re.compile(                             # 신버전 전체 행 (텍스트)
        r"▣ 전 체 ▣\s+([\d,]+)\s+([\d,]+)\s+((?:[\d.]+\s*)+)"
    )
    _SUMMARY_COL_RE = re.compile(r"\(합\)")                 # 소계 컬럼 필터
    _META_COLS = 4  # col 0~3: 제목/None/조사완료/가중값적용

    def parse(self, pages_data: List[Tuple[str, List, str]]) -> List[QuestionResult]:
        results: List[QuestionResult] = []
        seen_q_nums: set = set()

        for page_text, page_tables, _full_text in pages_data:
            for table in page_tables:
                result = self._try_parse_table(table, page_text, seen_q_nums)
                if result is not None:
                    results.append(result)

        return results

    def _try_parse_table(
        self, table: List, page_text: str, seen_q_nums: set
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
        self, table: List, page_text: str, m: re.Match, seen_q_nums: set
    ) -> Optional[QuestionResult]:
        """신버전: [표N] – 텍스트에서 전체 비율 추출."""
        q_num = int(m.group(1))
        if q_num in seen_q_nums:
            return None

        options = self._extract_options(table)
        if not options:
            return None

        total_match = self._TOTAL_TEXT_RE.search(page_text)
        if not total_match:
            return None

        n_completed = int(total_match.group(1).replace(",", ""))
        n_weighted = int(total_match.group(2).replace(",", ""))
        raw_pcts = [float(v) for v in total_match.group(3).split()]

        options_f, pcts_f = self._filter_summary(options, raw_pcts)
        min_len = min(len(options_f), len(pcts_f))
        if min_len == 0:
            return None

        seen_q_nums.add(q_num)
        return QuestionResult(
            question_number=q_num,
            question_title=m.group(2).strip(),
            question_text="",
            response_options=options_f[:min_len],
            overall_n_completed=n_completed,
            overall_n_weighted=n_weighted,
            overall_percentages=pcts_f[:min_len],
        )

    def _parse_q(
        self, table: List, m: re.Match, seen_q_nums: set
    ) -> Optional[QuestionResult]:
        """구버전: [QN] – 테이블 '합계' 행에서 직접 비율 추출."""
        q_num = int(m.group(1))
        if q_num in seen_q_nums:
            return None

        options = self._extract_options(table)
        if not options:
            return None

        # '합계' 행 탐색
        total_row: Optional[List] = None
        for row in table[2:]:
            if row and str(row[0] or "").strip() == "합계":
                total_row = row
                break
        if total_row is None:
            return None

        options_f, pcts_f = self._filter_summary(
            options,
            [float(str(c or "").strip()) for c in total_row[self._META_COLS:] if self._is_float(str(c or "").strip())],
        )
        min_len = min(len(options_f), len(pcts_f))
        if min_len == 0:
            return None

        seen_q_nums.add(q_num)
        return QuestionResult(
            question_number=q_num,
            question_title=m.group(2).strip(),
            question_text="",
            response_options=options_f[:min_len],
            overall_n_completed=None,
            overall_n_weighted=None,
            overall_percentages=pcts_f[:min_len],
        )

    @staticmethod
    def _is_float(s: str) -> bool:
        try:
            float(s)
            return True
        except ValueError:
            return False


class _EmbrainPublicParser(_TableFormatParser):
    """엠브레인퍼블릭 크로스탭 PDF 파서.

    PDF 구조:
      - 질문 제목: '[표N] 제목' 패턴
      - 테이블 구조: col 0-3 메타(None/None/사례수/None), col 4+가 선택지
      - 전체 행: '■ 전체 ■' 마커, col 2=N완료(조사), col 3=N가중(가중값적용)
      - 【...】 패턴(소계 컬럼) 및 None 헤더 컬럼 제거
    """

    _TABLE_TITLE_RE = re.compile(r"\[표(\d+)\]\s+(.+)")
    _SUMMARY_COL_RE = re.compile(r"【.+】")
    _META_COLS = 4  # None, None, 사례수, None

    def _parse_table(
        self, table: List[List], page_text: str
    ) -> Optional[QuestionResult]:
        if not table or len(table) < 2:
            return None

        # 전체 행: '■ 전체 ■' 으로 시작하는 행
        total_row: Optional[List] = None
        for row in table[1:]:
            if row and row[0] and str(row[0]).startswith("■") and "전체" in str(row[0]):
                total_row = row
                break
        if total_row is None:
            return None

        try:
            n_completed = int(str(total_row[2] or "").replace(",", ""))
            n_weighted = int(str(total_row[3] or "").replace(",", ""))
        except (ValueError, IndexError):
            return None

        options = self._extract_options(table)

        raw_pcts: List[float] = []
        for cell in total_row[self._META_COLS:]:
            try:
                raw_pcts.append(float(str(cell or "").strip()))
            except ValueError:
                pass

        options_f, pcts_f = self._filter_summary(options, raw_pcts)
        min_len = min(len(options_f), len(pcts_f))
        if min_len == 0:
            return None

        title_match = self._TABLE_TITLE_RE.search(page_text)
        if title_match:
            q_num = int(title_match.group(1))
            q_title = title_match.group(2).strip()
        else:
            q_num = 0
            q_title = ""

        return QuestionResult(
            question_number=q_num,
            question_title=q_title,
            question_text="",
            response_options=options_f[:min_len],
            overall_n_completed=n_completed,
            overall_n_weighted=n_weighted,
            overall_percentages=pcts_f[:min_len],
        )

    def _extract_options(self, table: List) -> List[str]:
        """row 1 col META_COLS+ 에서 선택지 추출."""
        if len(table) < 2:
            return []
        option_row = table[1]
        options: List[str] = []
        for cell in option_row[self._META_COLS :]:
            opt = re.sub(r"[\n\x00]", "", str(cell or "")).strip()
            if not opt or opt.lower() == "none" or opt == "빈도":
                continue
            options.append(opt)
        return options

    def _filter_summary(
        self, options: List[str], raw_pcts: List[float]
    ) -> tuple:
        """소계 컬럼 쌍 제거."""
        pairs = [
            (o, p)
            for o, p in zip(options, raw_pcts)
            if not self._SUMMARY_COL_RE.search(o)
        ]
        if not pairs:
            return [], []
        opts, pcts = zip(*pairs)
        return list(opts), list(pcts)


class _RealMeterParser(_TableFormatParser):
    """리얼미터 크로스탭 PDF 파서.

    PDF 구조:
      - 각 질문은 새 페이지에서 시작: "N. [제목]" + "QN. [질문문]?"
      - 테이블 헤더(row 0) col 4+에 선택지 이름
      - 텍스트에서 "전체 (N완료) (N가중) pct1 pct2 ..." 패턴으로 전체 비율 추출
      - 한 질문이 2페이지에 걸칠 수 있으므로 질문번호 중복 방지
    """

    # "N. 제목" 패턴 – 질문 섹션 시작 (숫자 + 점 + 공백 + 텍스트)
    _Q_SECTION_RE = re.compile(r"(?m)^(\d+)\.\s+(.+)$")
    # "QN. 질문문?" 패턴
    _Q_TEXT_RE = re.compile(r"Q\d+\.\s+(.+?)(?:\?|？)", re.DOTALL)
    # "전체 (N완료) (N가중) p1 p2 ..." 패턴
    _TOTAL_ROW_RE = re.compile(
        r"전체\s+\((\d+)\)\s+\((\d+)\)\s+((?:[\d.]+\s*)+)"
    )
    # 테이블 헤더에서 메타 컬럼 개수 (구분, None, 조사완료사례수, 가중값적용사례수)
    _HEADER_META_COLS = 4
    # 복합 요약행 패턴 – "잘함 ①+②", "잘못함 ③+④" 등 소계 행 제거
    # 원형 숫자 두 개가 + 로 연결된 경우
    _SUMMARY_OPT_RE = re.compile(r"[①②③④⑤⑥⑦⑧⑨⑩]\s*\+\s*[①②③④⑤⑥⑦⑧⑨⑩]")

    def parse(self, pages_data: List[Tuple[str, List, str]]) -> List[QuestionResult]:
        results: List[QuestionResult] = []
        seen_q_nums: set = set()

        for page_text, page_tables, full_text in pages_data:
            # ── 질문 섹션 시작 확인 ─────────────────────────────────────────
            q_section_match = self._Q_SECTION_RE.search(page_text)
            if not q_section_match:
                continue
            q_num = int(q_section_match.group(1))
            if q_num in seen_q_nums:
                continue  # 연속 페이지의 크로스탭 반복 — 건너뜀

            # ── 선택지 이름: 테이블 헤더에서 추출 ──────────────────────────
            options = self._extract_options(page_tables)
            if not options:
                continue

            # ── 전체 비율: 전체 텍스트(테이블 셀 포함)에서 추출 ────────────
            # 전체 행('전체 (N완료) (N가중) p1 p2 ...')은 테이블 내부에 있으므로
            # page_text(테이블 외부 텍스트)가 아닌 full_text에서 검색한다.
            total_match = self._TOTAL_ROW_RE.search(full_text)
            if not total_match:
                continue
            n_completed = int(total_match.group(1))
            n_weighted = int(total_match.group(2))
            pct_str = total_match.group(3).strip()
            percentages = [float(v) for v in pct_str.split()]

            # 복합 요약행 제거 – 선택지와 비율을 함께 필터링
            # (예: "잘함 ①+②", "잘못함 ③+④" 같은 소계 행)
            raw_pairs = list(zip(options, percentages))
            filtered = [(o, p) for o, p in raw_pairs
                        if not self._SUMMARY_OPT_RE.search(o)]
            if not filtered:
                # 요약행만 있는 경우(비정상) → 원본 유지
                filtered = raw_pairs
            options, percentages = zip(*filtered) if filtered else ([], [])
            options, percentages = list(options), list(percentages)

            # 선택지 수와 비율 수를 맞춤 (짧은 쪽 기준 truncate)
            min_len = min(len(options), len(percentages))
            if min_len == 0:
                continue
            options = options[:min_len]
            percentages = percentages[:min_len]

            # ── 질문 제목 / 질문문 ─────────────────────────────────────────
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
                response_options=options,
                overall_n_completed=n_completed,
                overall_n_weighted=n_weighted,
                overall_percentages=percentages,
            ))

        return results

    def _extract_options(self, page_tables: List) -> List[str]:
        """테이블 헤더 row 0의 col 4+ 에서 선택지 이름을 추출한다."""
        for table in page_tables:
            if not table or len(table) < 2:
                continue
            header = table[0]
            if len(header) <= self._HEADER_META_COLS:
                continue
            # col 0에 "구" (구 분) 포함 여부로 크로스탭 테이블 식별
            col0 = str(header[0] or "")
            if "구" not in col0:
                continue
            options = []
            for cell in header[self._HEADER_META_COLS:]:
                if cell is None:
                    continue
                opt = re.sub(r"\n", " ", str(cell)).strip()
                if opt and opt.lower() != "none":
                    options.append(opt)
            if options:
                return options
        return []


class _FlowerResearchParser(_TableFormatParser):
    """여론조사꽃 크로스탭 PDF 파서.

    PDF 구조:
      - NotoSansKR Identity-H 인코딩 + ToUnicode CMap 누락 → GID 디코딩 필요
      - 각 질문: 페이지당 1개 테이블, 앞에 "N. (부제) Q 질문문?" 텍스트
      - 테이블 구조:
          row 0: ['Base=전체\\n(단위: %)', None, '조사\\n완료', opt1, opt2, ..., '가중값\\n적용\\n사례수']
          row 1: ['전체', None, '(N완료)', '54.3 25.2 ... 0.3', None, ..., '(N가중)']
      - 전체 행(row 1) col 2에서 N완료, col 3에서 비율 공백구분, col -1에서 N가중 추출
      - 비율이 col 3 하나의 셀에 공백으로 뭉쳐 있음
    """

    NEEDS_GID_DECODE: bool = True
    FONT_PATH: str = str(
        Path(__file__).resolve().parents[4] / "data" / "resources" / "fonts" / "NotoSansCJKkr-Medium.otf"
    )

    # "N. (부제) Q" 패턴에서 N과 질문번호 추출
    _Q_SECTION_RE = re.compile(r"(?m)^(\d+)\.\s+(.+)$")
    # 질문문 추출: "Q\n질문텍스트?" 또는 "Q 질문텍스트?"
    _Q_TEXT_RE = re.compile(r"Q[\s\n]+(.+?)(?:\?|？)", re.DOTALL)
    # 사례수 "(숫자)" 패턴
    _N_RE = re.compile(r"\((\d[\d,]*)\)")
    # 소계 컬럼 제거: "잘하고 있다 ①+②" 형태
    _SUMMARY_COL_RE = re.compile(r"[①②③④⑤⑥⑦⑧⑨⑩]\s*\+\s*[①②③④⑤⑥⑦⑧⑨⑩]")

    def parse(self, pages_data: List[Tuple[str, List, str]]) -> List[QuestionResult]:
        results: List[QuestionResult] = []
        seen_q_nums: set = set()

        for page_text, page_tables, _full_text in pages_data:
            if not page_tables:
                continue

            tbl = page_tables[0]
            if not tbl or len(tbl) < 2:
                continue

            # 전체 행 탐색 (첫 번째 컬럼이 '전체'인 행)
            total_row: Optional[List] = None
            for row in tbl[1:]:
                if row and row[0] and str(row[0]).strip() == "전체":
                    total_row = row
                    break
            if total_row is None:
                continue

            # 선택지: 헤더 row col 3 ~ col -2 (마지막은 '가중값 적용 사례수')
            header = tbl[0]
            options: List[str] = []
            for cell in header[3:-1]:
                if cell is None:
                    continue
                opt = re.sub(r"\s+", " ", str(cell)).strip()
                if opt and opt.lower() not in ("none", ""):
                    options.append(opt)
            if not options:
                continue

            # 사례수: col 2=(완료), col -1=(가중)
            n_completed = self._extract_n_from_cell(str(total_row[2] or ""))
            n_weighted = self._extract_n_from_cell(str(total_row[-1] or ""))

            # 비율: col 3에 공백 구분 문자열로 뭉쳐 있음
            pct_raw = str(total_row[3] or "").strip()
            try:
                percentages = [float(v) for v in pct_raw.split() if re.fullmatch(r"[\d.]+", v)]
            except ValueError:
                continue
            if not percentages:
                continue

            # 소계 컬럼 제거
            pairs = [
                (o, p) for o, p in zip(options, percentages)
                if not self._SUMMARY_COL_RE.search(o)
            ]
            if not pairs:
                pairs = list(zip(options, percentages))
            options, percentages = [p[0] for p in pairs], [p[1] for p in pairs]

            # 길이 맞춤
            min_len = min(len(options), len(percentages))
            if min_len == 0:
                continue
            options = options[:min_len]
            percentages = percentages[:min_len]

            # 질문 번호/제목 추출
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

            # 질문문 추출
            q_text_m = self._Q_TEXT_RE.search(page_text)
            if q_text_m:
                q_text = re.sub(r"\s+", " ", q_text_m.group(1)).strip() + "?"
            else:
                q_text = q_title

            results.append(QuestionResult(
                question_number=q_num,
                question_title=q_title,
                question_text=q_text,
                response_options=options,
                overall_n_completed=n_completed,
                overall_n_weighted=n_weighted,
                overall_percentages=percentages,
            ))

        # 질문 번호 재매김
        for i, r in enumerate(results):
            r.question_number = i + 1
        return results

    def _extract_n_from_cell(self, text: str) -> Optional[int]:
        """'(1,234)' 또는 '1234' 형태에서 정수 추출."""
        m = self._N_RE.search(text)
        if m:
            return int(m.group(1).replace(",", ""))
        text = text.strip()
        try:
            return int(text.replace(",", ""))
        except ValueError:
            return None
