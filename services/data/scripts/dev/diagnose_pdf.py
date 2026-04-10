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

    # 파서 클래스 뼈대 자동 생성 (--human 출력 뒤 scaffold 코드 출력)
    python scripts/dev/diagnose_pdf.py --pdf "파일명.pdf" --pollster "기관명" --human --scaffold

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
    pdf_dir: Optional[Path] = None,
) -> "ScreeningResult":
    """단일 PDF 스크리닝을 수행하고 ScreeningResult를 반환한다."""
    from screening.models import (
        ScreeningResult, TextSamples,
    )
    from screening.pdf_analyzer import PdfAnalyzer
    from screening.pattern_detector import PatternDetector
    from screening.parser_tester import ParserTester
    from screening.format_profiler import FormatProfiler

    pdf_path = (pdf_dir or _PDF_DIR) / filename
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
    # table_previews: 테이블이 실제로 존재하는 첫 3페이지에서 추출
    # (전체 페이지 앞에서 3개가 아니라 테이블 있는 페이지 앞에서 3개)
    table_previews = []
    pages_with_tables = [
        (page_num, tables)
        for page_num, (_, tables, _) in enumerate(analyzed.pages_data, start=1)
        if tables
    ]
    for page_num, tables in pages_with_tables[:3]:
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


def _generate_scaffold(pollster: str, format_profile: "FormatProfile") -> str:  # type: ignore[name-defined]
    """FormatProfile 을 읽어 파서 클래스 뼈대(scaffold) 텍스트를 반환한다.

    반환값은 두 섹션으로 구성된다:
      1. parser.py 에 추가할 Python 클래스 뼈대
      2. parser_registry.json 에 추가할 JSON 엔트리
    """
    import re as _re
    import json as _json

    # ── 클래스명 생성 ──────────────────────────────────────────────────────────
    # 한글/특수문자 제거 후 간단한 slug 처리 — 실제 transliteration 미지원이므로
    # placeholder 클래스명을 사용하고 TODO 를 남긴다.
    slug_raw = _re.sub(r"[^\w]", "", pollster)
    # 단순히 알파벳/숫자만 추출, 없으면 "Xxx"
    ascii_part = _re.sub(r"[^A-Za-z0-9]", "", slug_raw)
    if ascii_part:
        class_stem = ascii_part[0].upper() + ascii_part[1:]
    else:
        class_stem = "Xxx"
    class_name = f"_{class_stem}Parser"

    # registry key: snake_case
    reg_key = _re.sub(r"(?<!^)(?=[A-Z])", "_", class_stem).lower() + "_format"

    # ── FormatProfile 값 추출 ─────────────────────────────────────────────────
    ratio_loc_raw = format_profile.ratio_location  # 원본 문자열 (뭉침 감지 포함 가능)
    # ratio_location 내 "mixed" / "text_bundled" 여부 판별
    is_mixed = "mixed" in ratio_loc_raw
    is_text_bundled = "text_bundled" in ratio_loc_raw and not is_mixed
    is_table_cell = "table_cell" in ratio_loc_raw and not is_mixed and not is_text_bundled

    meta_cols: int = format_profile.meta_cols or 4
    total_marker: str = format_profile.total_row_marker or "전체"
    q_marker: str = format_profile.question_marker or "탐지 안 됨"
    has_continuity: bool = format_profile.page_continuity

    # ── 비율 추출 방식 선택 ───────────────────────────────────────────────────
    _I = "                "  # 16칸 들여쓰기 (클래스 내 코드 기준)
    if is_table_cell:
        pct_block = (
            f"{_I}# 개별 셀에서 비율 추출\n"
            f"{_I}percentages = extract_percentages_from_cells(total_row, start_col=self.META_COLS)"
        )
        ratio_mode_label = f"table_cell (col{meta_cols}+)"
    elif is_mixed:
        pct_block = (
            f"{_I}# TODO: 뭉침 셀과 개별 셀이 공존 — 셀별 분기 처리 필요\n"
            f"{_I}# pcts_cell = extract_percentages_from_cells(total_row, start_col=self.META_COLS)\n"
            f"{_I}# pcts_bunched = extract_percentages_from_bunched_cell(str(total_row[self.META_COLS] or \"\"))\n"
            f"{_I}# percentages = pcts_bunched if pcts_bunched else pcts_cell\n"
            f"{_I}percentages = extract_percentages_from_cells(total_row, start_col=self.META_COLS)"
        )
        ratio_mode_label = "mixed (뭉침/개별 혼재)"
    else:  # text_bundled or unknown
        pct_block = (
            f"{_I}# TODO: 텍스트 영역에서 비율 추출 — extract_percentages_from_bunched_cell 활용 권장\n"
            f"{_I}# pct_cell = str(total_row[self.META_COLS] or \"\")\n"
            f"{_I}# percentages = extract_percentages_from_bunched_cell(pct_cell)\n"
            f"{_I}percentages = extract_percentages_from_cells(total_row, start_col=self.META_COLS)"
        )
        ratio_mode_label = "text_bundled (공백 구분)"

    continuity_block = ""
    if has_continuity:
        continuity_block = (
            "\n            if q_num in seen_q_nums:\n"
            "                continue\n"
        )
    else:
        continuity_block = (
            "\n            if q_num in seen_q_nums:\n"
            "                continue  # 페이지 연속성 없음 — 중복 방지만 유지\n"
        )

    # ── Python 클래스 뼈대 ────────────────────────────────────────────────────
    class_code = f"""\
# ── {pollster} ──────────────────────────────────────────────────────────────────
# TODO: 클래스명을 실제 기관명에 맞게 수정하세요.
class {class_name}(BaseTableParser):
    \"\"\"{pollster} 크로스탭 파서.

    포맷 특성:
      - 질문 마커: '{q_marker}' 형식
      - 전체 행: '{total_marker}' (테이블 셀)
      - 비율 위치: {ratio_mode_label}
      - meta 컬럼: {meta_cols}개
      - 페이지 연속성: {'있음' if has_continuity else '없음'}
    \"\"\"

    PARSER_KEY = "{class_name}"
    TOTAL_MARKERS = ("{total_marker}",)
    META_COLS = {meta_cols}
    SUMMARY_PATS = DEFAULT_SUMMARY_PATTERNS

    # TODO: 실제 PDF에서 질문 마커 정규식 확인 후 수정 (현재 탐지값: '{q_marker}')
    _Q_RE = re.compile(r"\\d+[.\\).]\\s+([^\\n]+)", re.MULTILINE)

    def parse(self, pages_data):
        results = []
        seen_q_nums = set()

        for _page_text, page_tables, full_text in pages_data:
            if not page_tables:
                continue

            # 질문 번호/제목 추출 — TODO: 실제 포맷에 맞게 수정
            m = self._Q_RE.search(full_text)
            if not m:
                continue
            q_num_raw = m.group(0).strip()
            q_title = m.group(1).strip() if m.lastindex and m.lastindex >= 1 else q_num_raw
            # TODO: q_num 을 실제 정수로 파싱 (현재 임시)
            q_num = len(seen_q_nums) + 1
{continuity_block}
            for table in page_tables:
                if not table or len(table) < 2:
                    continue

                # 전체 행 탐색
                total_row_idx = None
                for ri, row in enumerate(table[:5]):
                    cell0 = str(row[0] or "").strip()
                    if any(marker in cell0 for marker in self.TOTAL_MARKERS):
                        total_row_idx = ri
                        break
                if total_row_idx is None:
                    continue

                total_row = table[total_row_idx]
                header_row = table[1] if len(table) > 1 else table[0]
                options = extract_options_from_row(header_row, start_col=self.META_COLS)
                if not options:
                    continue

                # 사례수: col2, col3 (TODO: 실제 컬럼 위치 확인 필요)
                n_completed = extract_sample_count(str(total_row[2] if len(total_row) > 2 else ""))
                n_weighted = extract_sample_count(str(total_row[3] if len(total_row) > 3 else ""))

{pct_block}
                if not percentages:
                    continue

                options, percentages = filter_summary_columns(
                    options, percentages, summary_patterns=self.SUMMARY_PATS
                )
                min_len = min(len(options), len(percentages))
                if min_len == 0:
                    continue

                seen_q_nums.add(q_num)
                results.append(QuestionResult(
                    question_number=q_num,
                    question_title=q_title,
                    question_text=q_title,
                    response_options=options[:min_len],
                    overall_n_completed=n_completed,
                    overall_n_weighted=n_weighted,
                    overall_percentages=percentages[:min_len],
                ))
                break

        for i, r in enumerate(results):
            r.question_number = i + 1
        return results
"""

    # ── registry JSON 엔트리 ──────────────────────────────────────────────────
    registry_entry = _json.dumps(
        {
            reg_key: {
                "class": class_name,
                "description": (
                    f"{pollster} 크로스탭 파서 — "
                    f"'{q_marker}' 질문 마커, '{total_marker}' 전체 행, {ratio_mode_label}"
                ),
                "pollster_names": [pollster],
            }
        },
        ensure_ascii=False,
        indent=2,
    )

    divider = "─" * 70
    return (
        f"\n{divider}\n"
        f"[scaffold] parser.py 에 추가할 파서 클래스 뼈대\n"
        f"{divider}\n\n"
        f"{class_code}\n"
        f"{divider}\n"
        f"[scaffold] parser_registry.json 에 추가할 엔트리\n"
        f"{divider}\n\n"
        f"{registry_entry}\n"
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="PDF 파서 스크리닝 도구")
    ap.add_argument("--pdf",       help="특정 PDF 파일명 (경로 제외)")
    ap.add_argument("--pollster",  help="기관명 (--pdf 와 함께 사용)")
    ap.add_argument("--pages",     type=int, default=5, help="상세 분석 페이지 수 (기본: 5)")
    ap.add_argument("--dump-text", action="store_true", help="텍스트/테이블 상세 포함")
    ap.add_argument("--human",     action="store_true", help="터미널 출력 모드")
    ap.add_argument("--stdout",    action="store_true", help="JSON을 stdout으로 출력")
    ap.add_argument("--profile",   action="store_true", help="기관별 프로파일 생성")
    ap.add_argument("--scaffold",    action="store_true", help="FormatProfile 기반 파서 클래스 뼈대 생성 (--human 출력 뒤 stdout 출력)")
    ap.add_argument("--output-dir", default=str(_OUTPUT_DIR), help="출력 디렉토리")
    ap.add_argument("--pdf-dir",    default=None, help="PDF 디렉토리 경로 (기본: poll_targets.json 기준 자동 설정)")
    args = ap.parse_args()

    from screening.output import ScreeningOutput
    from screening.profiler import Profiler

    pdf_dir = Path(args.pdf_dir) if args.pdf_dir else _PDF_DIR
    out = ScreeningOutput(Path(args.output_dir))

    targets: List[Tuple[str, str]] = (
        [(args.pollster or "미지정", args.pdf)]
        if args.pdf
        else TARGETS
    )

    print(f"스크리닝 시작 — {len(targets)}건", file=sys.stderr)
    print(f"PDF 경로: {pdf_dir}", file=sys.stderr)
    print(f"출력 경로: {args.output_dir}", file=sys.stderr)

    # 기관별 결과 수집 (프로파일링용)
    pollster_results: Dict[str, List] = defaultdict(list)
    pollster_files:   Dict[str, List[str]] = defaultdict(list)

    for pollster, filename in targets:
        print(f"\n  ▶ {pollster} / {filename[:50]}", file=sys.stderr)
        result = screen_one(pollster, filename, sample_pages=args.pages, dump_text=args.dump_text, pdf_dir=pdf_dir)

        if args.stdout:
            out.print_to_stdout(result)
        elif args.human:
            out.print_human(result, dump_text=args.dump_text)
            if args.scaffold and not result.error:
                scaffold_text = _generate_scaffold(pollster, result.format_profile)
                print(scaffold_text)
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
