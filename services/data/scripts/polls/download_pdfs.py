"""여론조사 결과분석 PDF 전체 다운로드 스크립트.

output/polls/checks/{slug}.json 에서 analysis_url을 읽어
output/pdfs/{선거명}/{지역명}/ 에 저장한다.

사용법:
    cd services/data
    # 기본 (poll_targets.json의 첫 번째 타겟)
    python scripts/polls/download_pdfs.py

    # 특정 타겟 지정
    python scripts/polls/download_pdfs.py --target gyeonggi_governor_9th
"""
from __future__ import annotations

import argparse
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

_BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_BASE / "src"))

import re as _re

from lawdigest_data.polls.targets import load_targets  # noqa: E402

_UNSAFE = _re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def _safe_dirname(name: str) -> str:
    name = _UNSAFE.sub("_", name)
    return name.strip(". ") or "_"

BASE_URL = "https://www.nesdc.go.kr"

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
    ap = argparse.ArgumentParser(description="NESDC 여론조사 PDF 다운로드")
    ap.add_argument(
        "--target",
        default=None,
        help="poll_targets.json의 slug (미지정 시 첫 번째 타겟 사용)",
    )
    args = ap.parse_args()

    # ── 타겟 로드 ──────────────────────────────────────────────────────────────
    targets = load_targets(_BASE / "config" / "poll_targets.json")
    if not targets:
        log.error("poll_targets.json에 타겟이 없습니다.")
        sys.exit(1)

    if args.target:
        matched = [t for t in targets if t.slug == args.target]
        if not matched:
            log.error("타겟을 찾을 수 없습니다: %s", args.target)
            log.error("사용 가능한 slug: %s", [t.slug for t in targets])
            sys.exit(1)
        target = matched[0]
    else:
        target = targets[0]
        log.info("타겟 미지정 — 첫 번째 타겟 사용: %s", target.slug)

    # ── 경로 설정 ──────────────────────────────────────────────────────────────
    check_json = _BASE / "output" / "polls" / "checks" / f"{target.slug}.json"
    pdf_dir    = (
        _BASE / "output" / "pdfs"
        / _safe_dirname(target.election_type or target.slug)
        / _safe_dirname(target.region or "전체")
    )

    if not check_json.exists():
        log.error("check JSON 없음: %s", check_json)
        log.error("먼저 scripts/polls/check_pdfs.py --target %s 를 실행하세요.", target.slug)
        sys.exit(1)

    records = json.loads(check_json.read_text(encoding="utf-8"))
    download_targets = [r for r in records if r.get("has_pdf") and r.get("analysis_url")]
    log.info("다운로드 대상: %d건", len(download_targets))
    log.info("저장 경로: %s", pdf_dir)
    log.info("딜레이: %.1f~%.1fs / 요청", MIN_DELAY, MAX_DELAY)
    log.info("─" * 65)

    pdf_dir.mkdir(parents=True, exist_ok=True)
    session = _build_session()

    ok = 0
    skip = 0
    fail = 0

    for i, r in enumerate(download_targets, start=1):
        reg_no  = r["registration_number"]
        filename = _safe_filename(r.get("analysis_filename", ""), f"{reg_no}.pdf")
        if not filename.endswith(".pdf"):
            filename += ".pdf"
        dest = pdf_dir / filename

        if dest.exists() and dest.stat().st_size > 1024:
            log.info("[%2d/%2d] SKIP  %s (이미 존재)", i, len(download_targets), filename)
            skip += 1
            continue

        log.info("[%2d/%2d] %s", i, len(download_targets), reg_no)
        log.info("         %s", filename)

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
    log.info("저장 경로: %s", pdf_dir)


if __name__ == "__main__":
    main()
