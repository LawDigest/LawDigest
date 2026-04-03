"""로컬 PDF를 파싱하여 output/parsed/{선거명}/{지역명}/{기관명}/ 에 저장한다.

사용법:
    cd services/data

    # 전체 파싱 (poll_targets.json 기준 첫 번째 타겟)
    python scripts/polls/parse_all.py

    # 특정 타겟 지정
    python scripts/polls/parse_all.py --target gyeonggi_governor_9th

    # 특정 기관만
    python scripts/polls/parse_all.py --pollster "조원씨앤아이"

    # 강제 재파싱 (이미 존재하는 결과 덮어쓰기)
    python scripts/polls/parse_all.py --force

입력:
    output/polls/checks/{slug}.json  — check_pdfs.py 수집 메타데이터 (필수 — pollster 정보 포함)
    output/pdfs/{선거명}/{지역명}/  — download_pdfs.py가 저장한 PDF 파일

출력:
    output/parsed/{선거명}/{지역명}/{기관명}/{보고서명}.json  — 파싱 결과
    터미널: 기관별 파싱 성공/실패 요약
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import asdict
from pathlib import Path

_BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_BASE / "src"))

from lawdigest_data.polls.parser import PollResultParser  # noqa: E402
from lawdigest_data.polls.targets import load_targets     # noqa: E402

_UNSAFE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def _safe(name: str) -> str:
    name = _UNSAFE.sub("_", name)
    return name.strip(". ") or "_"


def main() -> None:
    ap = argparse.ArgumentParser(description="PDF 파싱 및 결과 저장")
    ap.add_argument("--target",   default=None, help="poll_targets.json의 slug (미지정 시 첫 번째 사용)")
    ap.add_argument("--pollster", default=None, help="특정 기관만 파싱 (부분 문자열 매칭)")
    ap.add_argument("--force",    action="store_true", help="이미 존재하는 결과도 덮어쓰기")
    ap.add_argument("--pdf-dir",  default=None, help="PDF 디렉토리 경로 (기본: output/pdfs/{선거명}/{지역명})")
    args = ap.parse_args()

    # ── 타겟 로드 ──────────────────────────────────────────────────────────────
    targets = load_targets(_BASE / "config" / "poll_targets.json")
    if not targets:
        print("오류: poll_targets.json에 타겟이 없습니다.")
        sys.exit(1)

    if args.target:
        matched = [t for t in targets if t.slug == args.target]
        if not matched:
            print(f"오류: 타겟 없음: {args.target}  (사용 가능: {[t.slug for t in targets]})")
            sys.exit(1)
        target = matched[0]
    else:
        target = targets[0]
        print(f"타겟 미지정 — 첫 번째 타겟 사용: {target.slug}")

    # ── 경로 설정 ──────────────────────────────────────────────────────────────
    pdf_dir = (
        Path(args.pdf_dir) if args.pdf_dir
        else _BASE / "output" / "pdfs"
             / _safe(target.election_type or target.slug)
             / _safe(target.region or "전체")
    )
    check_json = _BASE / "output" / "polls" / "checks" / f"{target.slug}.json"
    parsed_root = _BASE / "output" / "parsed"

    if not pdf_dir.exists():
        print(f"오류: PDF 디렉토리 없음: {pdf_dir}")
        sys.exit(1)

    # ── 메타데이터 로드 (check_pdfs.py 수집 결과 필수) ────────────────────────
    if not check_json.exists():
        print(f"오류: check JSON 없음: {check_json}")
        print(f"먼저 scripts/polls/check_pdfs.py --target {target.slug} 를 실행하세요.")
        sys.exit(1)

    meta_by_filename: dict[str, dict] = {}
    for r in json.loads(check_json.read_text()):
        meta_by_filename[r["analysis_filename"]] = r
    print(f"메타데이터 로드: {len(meta_by_filename)}건 ({check_json.name})")

    # ── 파서 초기화 ────────────────────────────────────────────────────────────
    registry = _BASE / "config" / "parser_registry.json"
    parser = PollResultParser(registry_path=registry)

    # ── PDF 순회 ───────────────────────────────────────────────────────────────
    pdfs = sorted(pdf_dir.glob("*.pdf"))
    if args.pollster:
        pdfs = [p for p in pdfs if args.pollster.lower() in
                meta_by_filename.get(p.name, {}).get("pollster", p.name).lower()]
        print(f"기관 필터 '{args.pollster}': {len(pdfs)}건")

    if not pdfs:
        print("파싱할 PDF가 없습니다.")
        sys.exit(0)

    election_name = target.election_type or "미분류"
    region = target.region or "미분류"

    print(f"\n{'번호':<8} {'Q':>3}  {'초':>4}  {'기관':<25}  파일명")
    print("-" * 90)

    total_ok = total_skip = total_fail = 0
    rows = []

    for pdf_path in pdfs:
        meta = meta_by_filename.get(pdf_path.name, {})
        pollster = meta.get("pollster") or "미분류"
        reg_num = meta.get("registration_number", pdf_path.stem)

        out_dir = parsed_root / _safe(election_name) / _safe(region) / _safe(pollster)
        out_path = out_dir / f"{_safe(pdf_path.stem)}.json"

        if out_path.exists() and not args.force:
            print(f"{reg_num:<8} {'--':>3}   SKIP  {pollster:<25}  {pdf_path.name[:38]}")
            total_skip += 1
            continue

        t0 = time.monotonic()
        try:
            results = parser.parse_pdf(pdf_path, pollster_hint=pollster if pollster != "미분류" else None)
            q = len(results)
            flag = "✔" if q > 0 else "✘"
            error = None

            out_dir.mkdir(parents=True, exist_ok=True)
            data = {
                "pdf_filename": pdf_path.name,
                "pollster": pollster,
                "election_name": election_name,
                "region": region,
                "registration_number": reg_num,
                "question_count": q,
                "questions": [asdict(r) for r in results],
            }
            out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            total_ok += 1

        except Exception as e:
            q = -1
            flag = "E"
            error = str(e)
            total_fail += 1

        elapsed = time.monotonic() - t0
        print(f"{reg_num:<8} {q:>3}{flag}  {elapsed:>4.1f}s  {pollster:<25}  {pdf_path.name[:38]}")
        sys.stdout.flush()

        rows.append({
            "pdf_filename": pdf_path.name,
            "pollster": pollster,
            "question_count": q,
            "flag": flag,
            "elapsed_seconds": round(elapsed, 2),
            "error": error,
            "out_path": str(out_path) if flag != "E" else None,
        })

    print()
    print(f"[ 결과 ] 성공={total_ok}  건너뜀={total_skip}  실패={total_fail}  합계={total_ok + total_skip + total_fail}")
    print(f"저장 위치: {parsed_root / _safe(election_name) / _safe(region)}")


if __name__ == "__main__":
    main()
