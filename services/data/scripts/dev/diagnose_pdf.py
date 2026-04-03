"""PDF 파서 스크리닝 도구 — 에이전트용 파서 개발 정보 추출기.

미개발 여론조사 PDF를 분석하여 파서 개발에 필요한 정보를
JSON으로 구조화하여 저장한다.

사용법:
    cd services/data

    # 미개발 기관 전체 스크리닝 (JSON 저장)
    python scripts/dev/diagnose_pdf.py

    # 특정 PDF만
    python scripts/dev/diagnose_pdf.py --pdf "결과분석_한길리서치1019.pdf" --pollster "(주)한길리서치"

    # 터미널 출력 (human-readable)
    python scripts/dev/diagnose_pdf.py --human

    # 텍스트/테이블 상세 포함
    python scripts/dev/diagnose_pdf.py --human --dump-text

    # JSON을 stdout으로 출력
    python scripts/dev/diagnose_pdf.py --pdf "파일명.pdf" --stdout

    # 기관별 프로파일 생성 포함
    python scripts/dev/diagnose_pdf.py --profile

출력:
    output/polls/screening/{기관명}/{PDF명}.json   — 스크리닝 결과
    output/polls/screening/{기관명}/_profile.json  — 기관 프로파일 (--profile)
"""
from __future__ import annotations

import argparse
import dataclasses
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

_BASE = Path(__file__).resolve().parents[2]
_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_BASE / "src"))
sys.path.insert(0, str(_SCRIPT_DIR))

_MAIN_DATA = Path("/home/ubuntu/project/Lawdigest/services/data")
_PDF_DIR = (
    (_MAIN_DATA if (_MAIN_DATA / "output" / "pdfs").exists() else _BASE)
    / "output" / "pdfs" / "gyeonggi_governor"
)
_OUTPUT_DIR = (
    (_MAIN_DATA if (_MAIN_DATA / "output").exists() else _BASE)
    / "output" / "polls" / "screening"
)

# ── 진단 대상 ──────────────────────────────────────────────────────────────────

TARGETS: List[Tuple[str, str]] = [
    ("(주)케이스탯리서치",   "(결과표) KBS 지방선거 여론조사 [03. 경기].pdf"),
    ("(주)케이스탯리서치",   "지방선거 관련 여론조사(경기)_한글통계표(12.31).pdf"),
    ("(주)윈지코리아컨설팅", "250915_보고서_드림투데이(경기)_v2.pdf"),
    ("(주)윈지코리아컨설팅", "260305_공표용보고서_경기도_정치지형조사_v2.pdf"),
    ("넥스트리서치",         "(넥스트리서치_조사결과_등록_0319) 제9회 전국동시지방선거관련 경기지역 여론조사.pdf"),
    ("㈜에스티아이",         "통계표_에스티아이_경기도지사 선거 여론조사 0219.pdf"),
    ("입소스 주식회사",      "(통계표) SBS 2026 설 특집 여론조사_경기.pdf"),
    ("(주)한길리서치",       "결과분석_한길리서치1019.pdf"),
]


def screen_one(
    pollster: str,
    filename: str,
    sample_pages: int = 5,
    dump_text: bool = False,
) -> "ScreeningResult":
    """단일 PDF 스크리닝을 수행하고 ScreeningResult를 반환한다."""
    from screening.models import (
        ScreeningResult, TextSamples,
    )
    from screening.pdf_analyzer import PdfAnalyzer
    from screening.pattern_detector import PatternDetector
    from screening.parser_tester import ParserTester
    from screening.format_profiler import FormatProfiler

    pdf_path = _PDF_DIR / filename
    now = datetime.now(timezone.utc).isoformat()

    result = ScreeningResult(
        generated_at=now,
        pdf_filename=filename,
        pollster=pollster,
        pdf_path=str(pdf_path),
    )

    if not pdf_path.exists():
        result.error = f"파일 없음: {pdf_path}"
        return result

    # 1. PDF 분석 (pages_data 공유)
    analyzed = PdfAnalyzer().analyze(pdf_path, sample_pages=sample_pages)
    if analyzed.error:
        result.error = analyzed.error
        return result

    result.basic_info = analyzed.basic_info

    # 2. 패턴 탐지
    detector = PatternDetector()
    result.question_block_patterns = detector.detect_question_blocks(analyzed)
    result.total_row_markers = detector.detect_total_row_markers(analyzed)
    result.table_structure = detector.analyze_table_structure(analyzed)
    result.page_continuity = detector.detect_page_continuity(analyzed)

    # 3. 파서 시도 (pages_data 재사용)
    result.parser_test_results = ParserTester().test_all(analyzed)

    # 4. 포맷 프로파일 생성
    result.format_profile = FormatProfiler().build_format_profile(
        q_patterns=result.question_block_patterns,
        total_markers=result.total_row_markers,
        table_structure=result.table_structure,
        page_continuity=result.page_continuity,
        parser_results=result.parser_test_results,
        needs_gid_decode=analyzed.basic_info.needs_gid_decode,
    )

    # 5. 텍스트 샘플 (에이전트 참고용)
    first_pages = analyzed.per_page_texts[:3]
    table_previews = []
    for page_num, (_, tables, _) in enumerate(analyzed.pages_data[:3], start=1):
        for ti, tbl in enumerate(tables[:2]):
            if tbl:
                table_previews.append({
                    "page": page_num,
                    "table_index": ti,
                    "rows": tbl[:5],
                })
    result.text_samples = TextSamples(
        first_pages_text=first_pages,
        table_previews=table_previews,
    )

    return result


def main() -> None:
    ap = argparse.ArgumentParser(description="PDF 파서 스크리닝 도구")
    ap.add_argument("--pdf",       help="특정 PDF 파일명 (경로 제외)")
    ap.add_argument("--pollster",  help="기관명 (--pdf 와 함께 사용)")
    ap.add_argument("--pages",     type=int, default=5, help="상세 분석 페이지 수 (기본: 5)")
    ap.add_argument("--dump-text", action="store_true", help="텍스트/테이블 상세 포함")
    ap.add_argument("--human",     action="store_true", help="터미널 출력 모드")
    ap.add_argument("--stdout",    action="store_true", help="JSON을 stdout으로 출력")
    ap.add_argument("--profile",   action="store_true", help="기관별 프로파일 생성")
    ap.add_argument("--output-dir", default=str(_OUTPUT_DIR), help="출력 디렉토리")
    args = ap.parse_args()

    from screening.output import ScreeningOutput
    from screening.profiler import Profiler

    out = ScreeningOutput(Path(args.output_dir))

    targets: List[Tuple[str, str]] = (
        [(args.pollster or "미지정", args.pdf)]
        if args.pdf
        else TARGETS
    )

    print(f"스크리닝 시작 — {len(targets)}건", file=sys.stderr)
    print(f"PDF 경로: {_PDF_DIR}", file=sys.stderr)
    print(f"출력 경로: {args.output_dir}", file=sys.stderr)

    # 기관별 결과 수집 (프로파일링용)
    pollster_results: Dict[str, List] = defaultdict(list)
    pollster_files:   Dict[str, List[str]] = defaultdict(list)

    for pollster, filename in targets:
        print(f"\n  ▶ {pollster} / {filename[:50]}", file=sys.stderr)
        result = screen_one(pollster, filename, sample_pages=args.pages, dump_text=args.dump_text)

        if args.stdout:
            out.print_to_stdout(result)
        elif args.human:
            out.print_human(result, dump_text=args.dump_text)
        else:
            saved_path = out.save_screening(result)
            print(f"    저장: {saved_path}", file=sys.stderr)
            fp = result.format_profile
            print(f"    질문마커: {fp.question_marker}  |  전체행: {fp.total_row_marker}  |  비율: {fp.ratio_location}", file=sys.stderr)

        pollster_results[pollster].append(result)
        if not args.stdout:
            slug = out._safe_slug(pollster) if hasattr(out, '_safe_slug') else pollster
            from screening.output import _safe_slug
            pollster_files[pollster].append(
                str(Path(args.output_dir) / _safe_slug(pollster) / f"{_safe_slug(Path(filename).stem)}.json")
            )

    # 기관별 프로파일 생성
    if args.profile and not args.stdout:
        print(f"\n프로파일 생성 중...", file=sys.stderr)
        profiler = Profiler()
        for pollster, results in pollster_results.items():
            profile = profiler.build_profile(
                pollster=pollster,
                results=results,
                screening_files=pollster_files[pollster],
            )
            if args.human:
                out.print_profile_human(profile)
            else:
                profile_path = out.save_profile(profile)
                print(f"  프로파일 저장: {profile_path}", file=sys.stderr)

    print(f"\n완료", file=sys.stderr)


if __name__ == "__main__":
    main()
