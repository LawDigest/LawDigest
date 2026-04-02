"""여론조사 결과분석 PDF 전체 다운로드 스크립트.

checks/gyeonggi_governor.json 에서 analysis_url을 읽어
output/polls/pdfs/gyeonggi_governor/ 에 저장한다.

사용법:
    cd services/data
    python scripts/polls/download_pdfs.py
"""
from __future__ import annotations

import json
import logging
import random
import re
import sys
import time
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://www.nesdc.go.kr"
_BASE     = Path(__file__).resolve().parents[2]
CHECK_JSON = _BASE / "output" / "polls" / "checks" / "gyeonggi_governor.json"
PDF_DIR    = _BASE / "output" / "polls" / "pdfs" / "gyeonggi_governor"

MIN_DELAY = 2.0
MAX_DELAY = 4.0

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept": "application/pdf,*/*",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s",
                    datefmt="%H:%M:%S", stream=sys.stdout)
log = logging.getLogger(__name__)


def _build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(HEADERS)
    retry = Retry(total=5, backoff_factor=2.0,
                  status_forcelist=[429, 500, 502, 503, 504],
                  allowed_methods=frozenset(["GET"]),
                  respect_retry_after_header=True)
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def _safe_filename(text: str, fallback: str) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|]', "_", text).strip()
    return (cleaned or fallback)[:180]


def main() -> None:
    if not CHECK_JSON.exists():
        log.error("check JSON 없음: %s", CHECK_JSON)
        log.error("먼저 scripts/polls/check_pdfs.py 를 실행하세요.")
        sys.exit(1)

    records = json.loads(CHECK_JSON.read_text(encoding="utf-8"))
    targets = [r for r in records if r.get("has_pdf") and r.get("analysis_url")]
    log.info("다운로드 대상: %d건", len(targets))
    log.info("저장 경로: %s", PDF_DIR)
    log.info("딜레이: %.1f~%.1fs / 요청", MIN_DELAY, MAX_DELAY)
    log.info("─" * 65)

    PDF_DIR.mkdir(parents=True, exist_ok=True)
    session = _build_session()

    ok = 0
    skip = 0
    fail = 0

    for i, r in enumerate(targets, start=1):
        reg_no  = r["registration_number"]
        filename = _safe_filename(r.get("analysis_filename", ""), f"{reg_no}.pdf")
        if not filename.endswith(".pdf"):
            filename += ".pdf"
        dest = PDF_DIR / filename

        if dest.exists() and dest.stat().st_size > 1024:
            log.info("[%2d/%2d] SKIP  %s (이미 존재)", i, len(targets), filename)
            skip += 1
            continue

        log.info("[%2d/%2d] %s", i, len(targets), reg_no)
        log.info("         %s", filename)

        # 상세 페이지에 먼저 GET (Referer 쿠키 획득)
        try:
            session.get(r["detail_url"], timeout=15)
        except requests.RequestException:
            pass

        try:
            resp = session.get(r["analysis_url"], timeout=60, stream=True,
                               headers={"Referer": r["detail_url"]})
            resp.raise_for_status()

            content = resp.content
            if b"%PDF" not in content[:10]:
                log.warning("         PDF 시그니처 없음 — 건너뜀")
                fail += 1
                time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
                continue

            dest.write_bytes(content)
            size_kb = len(content) / 1024
            log.info("         ✔ 저장 완료 (%.1f KB)", size_kb)
            ok += 1

        except requests.RequestException as exc:
            log.error("         ✘ 다운로드 실패: %s", exc)
            fail += 1

        time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

    log.info("─" * 65)
    log.info("완료: 성공 %d건 / 스킵 %d건 / 실패 %d건", ok, skip, fail)
    log.info("저장 경로: %s", PDF_DIR)


if __name__ == "__main__":
    main()
