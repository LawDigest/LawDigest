"""기관별 파서 개발 프로파일 생성기."""
from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Optional

from .models import PollsterProfile, ScreeningResult


class Profiler:
    """동일 기관의 복수 PDF 스크리닝 결과를 집약하여 공통 패턴 프로파일을 생성한다."""

    def build_profile(
        self,
        pollster: str,
        results: List[ScreeningResult],
        screening_files: Optional[List[str]] = None,
    ) -> PollsterProfile:
        """스크리닝 결과 목록에서 공통 패턴을 추출한다.

        Args:
            pollster: 기관명
            results: 해당 기관 PDF들의 ScreeningResult 목록
            screening_files: 각 스크리닝 결과 파일 경로 (참조용)
        """
        if not results:
            return PollsterProfile(pollster=pollster)

        n = len(results)
        common: Dict[str, Any] = {}

        # 1. 질문 마커 공통 패턴
        q_marker_counts: Counter = Counter()
        for r in results:
            for m in r.question_block_patterns.detected_markers:
                q_marker_counts[m.pattern] += 1
        if q_marker_counts:
            top_q, top_q_count = q_marker_counts.most_common(1)[0]
            common["question_block_marker"] = {
                "pattern": top_q,
                "confidence": round(top_q_count / n, 2),
            }

        # 2. 전체 행 마커 공통 패턴
        total_marker_counts: Counter = Counter()
        for r in results:
            for m in r.total_row_markers.detected_markers:
                total_marker_counts[m.pattern] += 1
        if total_marker_counts:
            top_t, top_t_count = total_marker_counts.most_common(1)[0]
            common["total_row_marker"] = {
                "pattern": top_t,
                "confidence": round(top_t_count / n, 2),
            }

        # 3. N 포맷
        n_format_counts: Counter = Counter(
            r.total_row_markers.n_format for r in results if r.total_row_markers.n_format != "unknown"
        )
        if n_format_counts:
            top_nf, top_nf_count = n_format_counts.most_common(1)[0]
            common["n_format"] = {
                "format": top_nf,
                "confidence": round(top_nf_count / n, 2),
            }

        # 4. meta 컬럼 수
        meta_col_counts: Counter = Counter(
            r.table_structure.header_row_analysis.meta_cols_count for r in results
        )
        if meta_col_counts:
            top_mc, top_mc_count = meta_col_counts.most_common(1)[0]
            common["table_meta_cols"] = {
                "count": top_mc,
                "confidence": round(top_mc_count / n, 2),
            }

        # 5. 비율 위치
        ratio_loc_counts: Counter = Counter(
            r.table_structure.ratio_data_location for r in results
            if r.table_structure.ratio_data_location != "unknown"
        )
        if ratio_loc_counts:
            top_rl, top_rl_count = ratio_loc_counts.most_common(1)[0]
            common["ratio_location"] = {
                "location": top_rl,
                "confidence": round(top_rl_count / n, 2),
            }

        # 6. 페이지 연속성
        has_continuity = sum(1 for r in results if r.page_continuity.multi_page_questions_detected)
        common["has_page_continuity"] = {
            "value": has_continuity > n // 2,
            "confidence": round(has_continuity / n, 2),
        }

        # 7. cid 인코딩
        has_cid = sum(1 for r in results if r.basic_info.cid_encoded)
        common["cid_encoded"] = {
            "value": has_cid > 0,
            "confidence": round(has_cid / n, 2),
        }

        # 베이스 클래스 집계 (코드 구조 참고용)
        base_counts: Counter = Counter(
            r.format_profile.suggested_base_class
            for r in results
            if r.format_profile.suggested_base_class
        )
        suggested_base = base_counts.most_common(1)[0][0] if base_counts else None

        # key_challenges 집계 (절반 이상 PDF에서 공통으로 등장한 것만)
        challenge_counts: Counter = Counter(
            ch
            for r in results
            for ch in r.format_profile.key_challenges
        )
        key_challenges = [ch for ch, cnt in challenge_counts.items() if cnt >= max(1, n // 2)]

        return PollsterProfile(
            pollster=pollster,
            pdf_count=n,
            common_patterns=common,
            suggested_base_class=suggested_base,
            key_challenges=key_challenges,
            per_pdf_screening_files=screening_files or [],
        )
