"""여론조사 결과표 PDF 파서."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

from .models import QuestionResult

# config/ 디렉터리 기본 경로
_DEFAULT_CONFIG_DIR = Path(__file__).resolve().parents[4] / "config"


@dataclass
class _RegistryEntry:
    parser_class: type
    pollster_keywords: Tuple[str, ...] = field(default_factory=tuple)
    content_probe: Optional[str] = None
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
        }
        parsers_def = data.get("parsers", {})
        assignments = data.get("pollster_assignments", {})
        fallback_name = data.get("fallback_parser", "text_format")

        entries: List[_RegistryEntry] = []

        # 기관별 할당 (priority=10)
        for pollster_kw, parser_key in assignments.items():
            parser_def = parsers_def.get(parser_key, {})
            cls = parser_map.get(parser_def.get("class", ""), _TextFormatParser)
            probes: List[str] = parser_def.get("content_probes", [])
            if probes:
                for probe in probes:
                    entries.append(_RegistryEntry(
                        parser_class=cls,
                        pollster_keywords=(pollster_kw,),
                        content_probe=probe,
                        priority=10,
                    ))
            else:
                entries.append(_RegistryEntry(
                    parser_class=cls,
                    pollster_keywords=(pollster_kw,),
                    content_probe=None,
                    priority=10,
                ))

        # content_probe 기반 fallback (priority=5)
        for parser_key, parser_def in parsers_def.items():
            cls = parser_map.get(parser_def.get("class", ""), _TextFormatParser)
            for probe in parser_def.get("content_probes", []):
                entries.append(_RegistryEntry(
                    parser_class=cls,
                    pollster_keywords=(),
                    content_probe=probe,
                    priority=5,
                ))

        # 최종 fallback (priority=0)
        fallback_def = parsers_def.get(fallback_name, {})
        fallback_cls = parser_map.get(fallback_def.get("class", ""), _TextFormatParser)
        entries.append(_RegistryEntry(
            parser_class=fallback_cls,
            pollster_keywords=(),
            content_probe=None,
            priority=0,
        ))

        entries.sort(key=lambda e: e.priority, reverse=True)
        self._registry = entries

    def _load_defaults(self) -> None:
        """JSON 파일 없을 때 내장 기본 레지스트리 로드."""
        self._registry = [
            _RegistryEntry(_TableFormatParser, ("조원씨앤아이",), "▣ 전체 ▣", 10),
            _RegistryEntry(_TextFormatParser, ("데일리리서치",), None, 10),
            _RegistryEntry(_TableFormatParser, ("메타서치",), None, 10),
            _RegistryEntry(_TableFormatParser, (), "가중값적용사례수", 5),
            _RegistryEntry(_TableFormatParser, (), "▣ 전체 ▣", 0),
            _RegistryEntry(_TextFormatParser, (), None, 0),
        ]

    def parse_pdf(
        self,
        pdf_path: Path,
        pollster_hint: Optional[str] = None,
    ) -> List[QuestionResult]:
        """PDF 파일을 파싱하여 QuestionResult 목록을 반환한다."""
        try:
            import pdfplumber
        except ImportError as exc:
            raise RuntimeError("PDF 파싱을 위해 pdfplumber가 필요합니다.") from exc

        pages_data: List[Tuple[str, List]] = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                tables = page.extract_tables() or []
                pages_data.append((text, tables))

        full_text = "\n".join(t for t, _ in pages_data)
        parser_class = self._select_parser(full_text, pollster_hint)

        if issubclass(parser_class, _TableFormatParser):
            return parser_class().parse(pages_data)
        else:
            return parser_class().parse(full_text)

    def _select_parser(self, full_text: str, pollster_hint: Optional[str]) -> type:
        """레지스트리에서 적합한 파서 클래스를 선택한다."""
        if pollster_hint:
            for entry in self._registry:
                if entry.pollster_keywords and any(
                    kw in pollster_hint for kw in entry.pollster_keywords
                ):
                    if entry.content_probe is None or entry.content_probe in full_text:
                        return entry.parser_class

        for entry in self._registry:
            if entry.content_probe and entry.content_probe in full_text:
                return entry.parser_class

        for entry in self._registry:
            if entry.content_probe is None:
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
                    if (
                        1 < len(opt) <= 60
                        and not re.fullmatch(r"[\d().%\-\s]+", opt)
                        and not has_sample_counts
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

    def parse(self, pages_data: List[Tuple[str, List]]) -> List[QuestionResult]:
        results: List[QuestionResult] = []
        for page_text, page_tables in pages_data:
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
