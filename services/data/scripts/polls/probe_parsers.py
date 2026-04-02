"""현재 파서로 전체 PDF를 돌려 기관별 파싱 성공 여부를 리포트한다.

사용법:
    cd services/data
    python scripts/polls/probe_parsers.py

출력:
    터미널: 기관별 파싱 성공/실패 표
    output/polls/probe_reports/probe_YYYYMMDD_HHMMSS.json  — 결과 JSON
"""
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

from lawdigest_data_pipeline.polls.parser import PollResultParser  # noqa: E402

registry  = _BASE / "config" / "parser_registry.json"
parser    = PollResultParser(registry_path=registry)

check     = json.loads((_BASE / "output" / "polls" / "checks" / "gyeonggi_governor.json").read_text())
pdf_dir   = _BASE / "output" / "polls" / "pdfs" / "gyeonggi_governor"
report_dir = _BASE / "output" / "polls" / "probe_reports"

# PDF 파서 타임아웃 (초) – 느린 PDF 스킵
PDF_TIMEOUT = 20


class _Timeout(Exception):
    pass


def _handler(signum, frame):
    raise _Timeout()


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

# ── 결과 파일 저장 ────────────────────────────────────────────────────────────────
report_dir.mkdir(parents=True, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
report_path = report_dir / f"probe_{timestamp}.json"

total = len(rows)
success = sum(1 for r in rows if r["flag"] == "✔")
empty = sum(1 for r in rows if r["flag"] == "✘")
timeout = sum(1 for r in rows if r["flag"] == "T")
error = sum(1 for r in rows if r["flag"] == "E")

report = {
    "timestamp": timestamp,
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
