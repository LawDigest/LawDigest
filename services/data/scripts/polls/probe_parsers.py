"""현재 파서로 전체 PDF를 돌려 기관별 파싱 성공 여부를 리포트한다.

사용법:
    cd services/data
    # 기본 (poll_targets.json의 첫 번째 타겟)
    python scripts/polls/probe_parsers.py

    # 특정 타겟 지정
    python scripts/polls/probe_parsers.py --target gyeonggi_governor_9th

출력:
    터미널: 기관별 파싱 성공/실패 표
    output/polls/probe_reports/probe_{slug}_{YYYYMMDD_HHMMSS}.json  — 결과 JSON
"""
from __future__ import annotations

import argparse
import json
import signal
import sys
import time
import warnings
from datetime import datetime
from pathlib import Path

warnings.filterwarnings("ignore")

_BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_BASE / "src"))

import re as _re

from lawdigest_data.polls.parser import PollResultParser  # noqa: E402
from lawdigest_data.polls.targets import is_ignored_analysis_filename, load_targets  # noqa: E402

_UNSAFE = _re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def _safe_dirname(name: str) -> str:
    name = _UNSAFE.sub("_", name)
    return name.strip(". ") or "_"

# PDF 파서 타임아웃 (초)
PDF_TIMEOUT = 20


class _Timeout(Exception):
    pass


def _handler(signum, frame):
    raise _Timeout()


def main() -> None:
    ap = argparse.ArgumentParser(description="파서 전체 검증 리포트")
    ap.add_argument(
        "--target",
        default=None,
        help="poll_targets.json의 slug (미지정 시 첫 번째 타겟 사용)",
    )
    args = ap.parse_args()

    # ── 타겟 로드 ──────────────────────────────────────────────────────────────
    targets = load_targets(_BASE / "config" / "poll_targets.json")
    if not targets:
        print("오류: poll_targets.json에 타겟이 없습니다.")
        sys.exit(1)

    if args.target:
        matched = [t for t in targets if t.slug == args.target]
        if not matched:
            print(f"오류: 타겟을 찾을 수 없습니다: {args.target}")
            print(f"사용 가능한 slug: {[t.slug for t in targets]}")
            sys.exit(1)
        target = matched[0]
    else:
        target = targets[0]
        print(f"타겟 미지정 — 첫 번째 타겟 사용: {target.slug}")

    # ── 경로 설정 ──────────────────────────────────────────────────────────────
    check_json  = _BASE / "output" / "polls" / "checks" / f"{target.slug}.json"
    pdf_dir     = (
        _BASE / "output" / "pdfs"
        / _safe_dirname(target.election_type or target.slug)
        / _safe_dirname(target.region or "전체")
    )
    report_dir  = _BASE / "output" / "polls" / "probe_reports"

    if not check_json.exists():
        print(f"오류: check JSON 없음: {check_json}")
        print(f"먼저 scripts/polls/check_pdfs.py --target {target.slug} 를 실행하세요.")
        sys.exit(1)

    registry = _BASE / "config" / "parser_registry.json"
    parser   = PollResultParser(registry_path=registry)
    check    = [
        row for row in json.loads(check_json.read_text())
        if not is_ignored_analysis_filename(row.get("analysis_filename", ""), target)
    ]

    print(f"{'번호':<8} {'Q':>3}  {'초':>4}  {'조사기관':<30}  파일명")
    print("-" * 95)

    rows = []
    for r in sorted(check, key=lambda x: x["registered_date"]):
        pdf_path = pdf_dir / r["analysis_filename"]
        if not pdf_path.exists():
            continue

        signal.signal(signal.SIGALRM, _handler)
        signal.alarm(PDF_TIMEOUT)
        t0 = time.monotonic()
        try:
            results = parser.parse_pdf(pdf_path, pollster_hint=r["pollster"])
            q = len(results)
            flag = "✔" if q > 0 else "✘"
            error = None
        except _Timeout:
            q = -99
            flag = "T"
            error = "timeout"
        except Exception as e:
            q = -1
            flag = "E"
            error = str(e)
        finally:
            signal.alarm(0)
        elapsed = time.monotonic() - t0

        print(f"{r['registration_number']:<8} {q:>3}{flag}  {elapsed:>4.1f}s  {r['pollster']:<30}  {r['analysis_filename'][:38]}")
        sys.stdout.flush()

        rows.append({
            "registration_number": r["registration_number"],
            "pollster": r["pollster"],
            "filename": r["analysis_filename"],
            "question_count": q,
            "flag": flag,
            "elapsed_seconds": round(elapsed, 2),
            "error": error,
        })

    # ── 결과 파일 저장 ────────────────────────────────────────────────────────────
    report_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = report_dir / f"probe_{target.slug}_{timestamp}.json"

    total   = len(rows)
    success = sum(1 for r in rows if r["flag"] == "✔")
    empty   = sum(1 for r in rows if r["flag"] == "✘")
    timeout = sum(1 for r in rows if r["flag"] == "T")
    error   = sum(1 for r in rows if r["flag"] == "E")

    report = {
        "timestamp": timestamp,
        "target_slug": target.slug,
        "summary": {
            "total": total,
            "success": success,
            "empty": empty,
            "timeout": timeout,
            "error": error,
        },
        "rows": rows,
    }

    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print()
    print(f"[ 요약 ] 전체={total}  성공={success}  빈결과={empty}  타임아웃={timeout}  오류={error}")
    print(f"리포트 저장: {report_path}")


if __name__ == "__main__":
    main()
