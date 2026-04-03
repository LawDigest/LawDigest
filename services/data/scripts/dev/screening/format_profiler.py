"""포맷 프로파일러 — 탐지된 패턴을 정리하여 파서 개발 가이드를 생성한다.

각 기관마다 항상 새 파서를 개발해야 하며, 기존 파서의 재사용은 권장하지 않는다.
이 모듈은 "어떤 파서를 쓸지"가 아니라 "이 PDF의 포맷이 무엇인지"를 서술한다.
"""
from __future__ import annotations

from typing import List

from .models import (
    FormatProfile,
    PageContinuity,
    ParserTestResult,
    QuestionBlockPatterns,
    TableStructure,
    TotalRowMarkers,
)

# 코드 구조 참고용 베이스 클래스 선택 기준 (재사용이 아닌 구조 참고)
# ratio_location 기준으로 가장 유사한 코드 구조를 가진 클래스를 안내
_BASE_CLASS_BY_RATIO: dict = {
    "table_cell":   "_TableFormatParser",
    "text_bundled": "_TextFormatParser",
    "mixed":        "_TableFormatParser",   # 테이블 기반이지만 추가 처리 필요
    "unknown":      "_TableFormatParser",
}


class FormatProfiler:
    """패턴 탐지 결과를 바탕으로 FormatProfile을 생성한다."""

    def build_format_profile(
        self,
        q_patterns:       QuestionBlockPatterns,
        total_markers:    TotalRowMarkers,
        table_structure:  TableStructure,
        page_continuity:  PageContinuity,
        parser_results:   List[ParserTestResult],
        needs_gid_decode: bool = False,
    ) -> FormatProfile:
        """PDF 포맷 특성을 서술하는 FormatProfile을 생성한다."""

        # 질문 마커 (1위)
        question_marker = (
            q_patterns.detected_markers[0].pattern
            if q_patterns.detected_markers else "탐지 안 됨"
        )

        # 전체 행 마커 (1위)
        total_row_marker = (
            total_markers.detected_markers[0].pattern
            if total_markers.detected_markers else "탐지 안 됨"
        )

        # 비율 위치 서술
        ratio_loc = table_structure.ratio_data_location
        if table_structure.ratio_cell_bundled:
            ratio_location_desc = f"{ratio_loc} (비율 뭉침 감지)"
        else:
            ratio_location_desc = ratio_loc

        # 코드 구조 참고용 베이스 클래스
        if needs_gid_decode:
            base_class = "_FlowerResearchParser"
        else:
            base_class = _BASE_CLASS_BY_RATIO.get(ratio_loc, "_TableFormatParser")

        # 주요 도전 과제 수집
        challenges: List[str] = []

        if needs_gid_decode:
            challenges.append("cid 인코딩 — GID→Unicode 역맵핑 필요 (NotoSansCJKkr-Medium.otf)")

        if table_structure.ratio_cell_bundled:
            challenges.append(
                f"비율이 한 셀에 공백 구분으로 뭉쳐 있음 — 셀 분리 파싱 필요"
            )
            if table_structure.bundled_example:
                challenges.append(f"  뭉침 예시: {table_structure.bundled_example[:80]}")

        if ratio_loc == "mixed":
            challenges.append("비율 데이터가 테이블 셀과 텍스트 영역에 혼재")

        if table_structure.header_row_analysis.has_summary_cols:
            patterns = table_structure.header_row_analysis.summary_col_patterns
            challenges.append(f"소계 컬럼 존재 ({', '.join(patterns)}) — 파싱 시 건너뛰기 처리 필요")

        if page_continuity.multi_page_questions_detected:
            signals = ", ".join(page_continuity.continuity_signals)
            challenges.append(f"페이지 연속성 신호 감지 ({signals}) — 멀티페이지 merge 로직 필요")

        meta = table_structure.header_row_analysis.meta_cols_count
        if meta == 0:
            challenges.append("테이블 헤더 meta 컬럼을 탐지하지 못함 — 수동 확인 필요")

        # 파서 시도 결과에서 추가 힌트
        best_test = max(
            (r for r in parser_results if r.exception is None and r.count > 0),
            key=lambda r: r.count,
            default=None,
        )
        if best_test:
            challenges.append(
                f"기존 파서 중 {best_test.class_name}이 {best_test.count}건 파싱했으나 "
                f"검증 오류 {best_test.error_count}건 — 해당 파서의 파싱 로직 구조만 참고"
            )
        else:
            challenges.append("기존 파서 전부 0건 또는 예외 — 완전히 새로운 파싱 로직 필요")

        # 전체 행 마커가 여러 개 탐지된 경우
        if len(total_markers.detected_markers) > 1:
            all_markers = [m.pattern for m in total_markers.detected_markers]
            challenges.append(f"전체 행 마커 후보 복수 탐지: {all_markers} — 실제 비율 행 마커를 PDF에서 직접 확인 필요")

        return FormatProfile(
            question_marker=question_marker,
            total_row_marker=total_row_marker,
            meta_cols=meta,
            ratio_location=ratio_location_desc,
            ratio_decimal_places=table_structure.ratio_format.decimal_places,
            page_continuity=page_continuity.multi_page_questions_detected,
            suggested_base_class=base_class,
            key_challenges=challenges,
        )
