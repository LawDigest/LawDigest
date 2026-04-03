"""기존 파서 전체 시도 및 결과 수집."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import List

from .models import ParserTestResult
from .pdf_analyzer import AnalyzedPdf

# 파서 모듈 경로 설정
_SRC = Path(__file__).resolve().parents[4] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


class ParserTester:
    """등록된 모든 파서 클래스로 파싱을 시도하고 결과를 반환한다."""

    def test_all(self, analyzed: AnalyzedPdf) -> List[ParserTestResult]:
        """AnalyzedPdf의 pages_data를 재사용하여 중복 PDF 열기 없이 시도한다."""
        try:
            from lawdigest_data.polls.parser import _build_parser_key_map
            from lawdigest_data.polls.validation import validate_parse_results
        except ImportError as e:
            return [ParserTestResult(class_name="ImportError", exception=str(e))]

        # PARSER_KEY를 가진 모든 파서를 자동 탐색 (Protocol 통일로 단일 호출 방식)
        parser_classes = _build_parser_key_map()

        pages_data = analyzed.pages_data
        results: List[ParserTestResult] = []

        for cls_name, cls in parser_classes.items():
            try:
                parsed = cls().parse(pages_data)
                errors = validate_parse_results(parsed)
                valid_count = sum(1 for errs in errors.values() if not errs)
                error_count = sum(1 for errs in errors.values() if errs)
                results.append(ParserTestResult(
                    class_name=cls_name,
                    count=len(parsed),
                    valid_count=valid_count,
                    error_count=error_count,
                    errors={k: v for k, v in errors.items() if v},
                    exception=None,
                ))
            except Exception as e:
                results.append(ParserTestResult(
                    class_name=cls_name,
                    count=0,
                    valid_count=0,
                    error_count=0,
                    exception=str(e)[:200],
                ))

        return results
