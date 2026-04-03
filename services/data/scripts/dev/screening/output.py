"""스크리닝 결과 출력 포매터 — JSON 저장 및 human 터미널 출력."""
from __future__ import annotations

import dataclasses
import json
import re
import sys
from pathlib import Path
from typing import List, Optional

from .models import PollsterProfile, ScreeningResult

_UNSAFE_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def _safe_slug(name: str) -> str:
    return _UNSAFE_RE.sub("_", name).strip(". ") or "_"


class ScreeningOutput:
    """JSON 저장 및 human-readable 터미널 출력을 담당한다."""

    def __init__(self, output_root: Path) -> None:
        self.output_root = output_root

    # ── JSON 출력 ──────────────────────────────────────────────────────────────

    def save_screening(self, result: ScreeningResult) -> Path:
        """스크리닝 결과를 JSON 파일로 저장하고 경로를 반환한다."""
        pollster_slug = _safe_slug(result.pollster)
        pdf_stem = _safe_slug(Path(result.pdf_filename).stem)
        out_dir = self.output_root / pollster_slug
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{pdf_stem}.json"
        out_path.write_text(
            json.dumps(dataclasses.asdict(result), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return out_path

    def save_profile(self, profile: PollsterProfile) -> Path:
        """기관별 프로파일을 JSON 파일로 저장하고 경로를 반환한다."""
        pollster_slug = _safe_slug(profile.pollster)
        out_dir = self.output_root / pollster_slug
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "_profile.json"
        out_path.write_text(
            json.dumps(dataclasses.asdict(profile), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return out_path

    def print_to_stdout(self, result: ScreeningResult) -> None:
        """JSON을 stdout으로 출력한다."""
        print(json.dumps(dataclasses.asdict(result), ensure_ascii=False, indent=2))

    # ── Human-readable 출력 ───────────────────────────────────────────────────

    def print_human(self, result: ScreeningResult, dump_text: bool = False) -> None:
        """터미널 친화적 형식으로 스크리닝 결과를 출력한다."""
        _hr = lambda c="─", w=70: c * w
        bi = result.basic_info
        qp = result.question_block_patterns
        tm = result.total_row_markers
        ts = result.table_structure
        pc = result.page_continuity
        fp = result.format_profile

        print(_hr("═"))
        print(f"📄 {result.pdf_filename}")
        print(f"   기관: {result.pollster}")
        if result.error:
            print(f"  ❌ 오류: {result.error}")
            return
        print(_hr())

        # [1] 기본 정보
        print(f"\n[1] 기본 정보")
        print(f"  페이지: {bi.page_count}  |  텍스트 추출: {'✅' if bi.text_extractable else '❌'}  |  파일: {bi.file_size_bytes // 1024}KB")
        if bi.cid_encoded:
            print("  ⚠️  cid: 인코딩 감지 (GID 디코딩 필요)")

        # [2] 질문 마커
        print(f"\n[2] 질문 블록 마커 (추정 질문 수: {qp.estimated_question_count})")
        if qp.detected_markers:
            for m in qp.detected_markers[:4]:
                print(f"  ✓ '{m.pattern}' — {m.occurrences}회  예: {m.examples[0][:60] if m.examples else ''}")
        else:
            print("  탐지된 마커 없음")

        # [3] 전체 행 마커
        print(f"\n[3] 전체/합계 행 마커  (N 포맷: {tm.n_format})")
        if tm.detected_markers:
            for m in tm.detected_markers[:3]:
                print(f"  ✓ '{m.pattern}' — {m.occurrences}회  예: {m.examples[0][:60] if m.examples else ''}")
        else:
            print("  탐지된 마커 없음")

        # [4] 테이블 구조
        print(f"\n[4] 테이블 구조")
        print(f"  테이블 있는 페이지: {ts.pages_with_tables}  |  없는 페이지: {ts.pages_without_tables}")
        print(f"  전형적 크기: {ts.typical_shape.get('rows', 0)}행×{ts.typical_shape.get('cols', 0)}열")
        ha = ts.header_row_analysis
        print(f"  meta 컬럼 수: {ha.meta_cols_count}  |  선택지 시작: col{ha.option_cols_start_index}")
        if ha.option_examples:
            print(f"  선택지 예시: {', '.join(ha.option_examples[:4])}")
        print(f"  비율 위치: {ts.ratio_data_location}  |  소수점: {ts.ratio_format.decimal_places}자리")
        if ts.ratio_cell_bundled:
            print(f"  ⚠️  비율 뭉침 감지: {ts.bundled_example or ''}")

        # [5] 페이지 연속성
        if pc.multi_page_questions_detected:
            print(f"\n[5] 페이지 연속성: ⚠️ 감지됨 ({', '.join(pc.continuity_signals)})")
        else:
            print(f"\n[5] 페이지 연속성: 없음")

        # [6] 파서 시도 결과
        print(f"\n[6] 기존 파서 시도")
        for r in result.parser_test_results:
            if r.exception:
                print(f"  {r.class_name:30s} → 예외: {r.exception[:60]}")
            elif r.count == 0:
                print(f"  {r.class_name:30s} → 0건")
            else:
                status = "✅" if r.valid_count == r.count else "🔶"
                print(f"  {r.class_name:30s} → {status} {r.count}건 (유효:{r.valid_count}, 오류:{r.error_count})")

        # [7] 포맷 프로파일 (파서 개발 가이드)
        print(f"\n[7] 포맷 프로파일 — 신규 파서 개발 가이드")
        print(f"  질문 마커:      {fp.question_marker}")
        print(f"  전체 행 마커:   {fp.total_row_marker}")
        print(f"  meta 컬럼:     {fp.meta_cols}개")
        print(f"  비율 위치:      {fp.ratio_location}")
        print(f"  소수점:         {fp.ratio_decimal_places}자리")
        print(f"  페이지 연속성:  {'있음' if fp.page_continuity else '없음'}")
        print(f"  코드 구조 참고: {fp.suggested_base_class}  (재사용 아님, 구조만 참고)")
        if fp.key_challenges:
            print(f"  주요 도전 과제:")
            for ch in fp.key_challenges:
                print(f"   • {ch}")

        # [8] 텍스트 샘플
        if dump_text and result.text_samples.first_pages_text:
            print(f"\n[8] 텍스트 샘플 (첫 페이지)")
            for line in result.text_samples.first_pages_text[0].splitlines()[:30]:
                print(f"  {line}")
            if result.text_samples.table_previews:
                print(f"\n  --- 테이블 샘플 (첫 테이블 첫 5행) ---")
                for row in result.text_samples.table_previews[0].get("rows", [])[:5]:
                    cells = [str(c or "").strip()[:18] for c in row]
                    print(f"    {' | '.join(cells)}")
        elif not dump_text and result.text_samples.first_pages_text:
            first_text = result.text_samples.first_pages_text[0]
            lines = first_text.splitlines()[:20]
            print(f"\n[8] 텍스트 샘플 (첫 20줄)")
            for line in lines:
                print(f"  {line}")

        print()

    def print_profile_human(self, profile: PollsterProfile) -> None:
        """기관 프로파일을 human-readable 형식으로 출력한다."""
        _hr = lambda c="─", w=70: c * w
        print(_hr("═"))
        print(f"📊 기관 프로파일: {profile.pollster}  ({profile.pdf_count}건)")
        print(_hr())

        cp = profile.common_patterns
        for key, val in cp.items():
            if isinstance(val, dict):
                conf = val.get("confidence", "?")
                v = val.get("pattern") or val.get("location") or val.get("format") or val.get("count") or val.get("value")
                print(f"  {key}: {v}  (confidence={conf})")
            else:
                print(f"  {key}: {val}")

        print(f"\n  코드 구조 참고 클래스: {profile.suggested_base_class or '미정'}  (재사용 아님)")
        if profile.key_challenges:
            print(f"  공통 도전 과제:")
            for ch in profile.key_challenges:
                print(f"    • {ch}")
        print()
