"""한국갤럽조사연구소 PDF 다운로드 스크립트.

all_regions_9th.json 에서 갤럽 항목을 읽어 상세 페이지를 방문,
PDF URL을 추출해 output/pdfs/gallup/ 에 저장한다.

사용법:
    cd services/data
    python scripts/polls/download_gallup_pdfs.py
    python scripts/polls/download_gallup_pdfs.py --limit 5   # 처음 5건만
    python scripts/polls/download_gallup_pdfs.py --dry-run   # URL만 출력
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
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

_BASE = Path(__file__).resolve().parents[2]

BASE_URL = "https://www.nesdc.go.kr"
OUT_DIR = _BASE / "output" / "pdfs" / "gallup"
LIST_JSON = _BASE / "output" / "polls" / "lists" / "all_regions_9th.json"

POLLSTER_NAMES = {"한국갤럽조사연구소", "(주)한국갤럽조사연구소"}

MIN_DELAY = 2.5
MAX_DELAY = 5.0

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept": "application/pdf,*/*",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
log = logging.getLogger(__name__)


def _build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(HEADERS)
    retry = Retry(
        total=5,
        backoff_factor=2.0,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=frozenset(["GET"]),
        respect_retry_after_header=True,
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


_UNSAFE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def _safe_filename(text: str, fallback: str) -> str:
    cleaned = _UNSAFE.sub("_", text).strip()
    return (cleaned or fallback)[:180]


def _build_file_download_url(onclick: str) -> str:
    m = re.search(
        r"view\('([^']+)',\s*'([^']+)',\s*'([^']+)',\s*'([^']+)'\)", onclick
    )
    if not m:
        return ""
    atch_file_id, file_sn, bbs_id, bbs_key = m.groups()
    return (
        f"{BASE_URL}/portal/cmm/fms/FileDown.do"
        f"?atchFileId={atch_file_id}&fileSn={file_sn}&bbsId={bbs_id}&bbsKey={bbs_key}"
    )


def _extract_pdf_url(soup: BeautifulSoup) -> tuple[str, str]:
    """(filename, url) 반환. 분석 결과표 우선, 없으면 두 번째 파일."""
    file_anchors = [
        (a.get_text(strip=True), a.get("onclick", ""))
        for a in soup.select("a[onclick*='view(']")
        if a.get_text(strip=True)
    ]

    analysis_filename = ""
    analysis_url = ""
    questionnaire_filename = ""
    questionnaire_url = ""

    for text, onclick in file_anchors:
        url = _build_file_download_url(onclick)
        if any(k in text for k in ("결과표", "결과분석", "분석")) and not analysis_url:
            analysis_filename, analysis_url = text, url
        elif any(k in text for k in ("설문지", "질문지")) and not questionnaire_url:
            questionnaire_filename, questionnaire_url = text, url

    # 분석 파일이 없으면 두 번째 파일
    if not analysis_url and len(file_anchors) >= 2:
        analysis_filename, onclick = file_anchors[1]
        analysis_url = _build_file_download_url(onclick)

    # 분석 파일도 없으면 첫 번째 파일
    if not analysis_url and file_anchors:
        analysis_filename, onclick = file_anchors[0]
        analysis_url = _build_file_download_url(onclick)

    return analysis_filename, analysis_url


def main() -> None:
    ap = argparse.ArgumentParser(description="한국갤럽 PDF 다운로드")
    ap.add_argument("--limit", type=int, default=None, help="처리할 최대 건수")
    ap.add_argument("--dry-run", action="store_true", help="URL만 출력하고 다운로드하지 않음")
    ap.add_argument("--force", action="store_true", help="이미 존재하는 파일도 재다운로드")
    args = ap.parse_args()

    with open(LIST_JSON, encoding="utf-8") as f:
        all_data = json.load(f)

    gallup_items = [d for d in all_data if d.get("pollster") in POLLSTER_NAMES]
    log.info("갤럽 항목: %d건", len(gallup_items))

    if args.limit:
        gallup_items = gallup_items[: args.limit]
        log.info("처리 대상: %d건 (limit=%d)", len(gallup_items), args.limit)

    if not args.dry_run:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        log.info("저장 경로: %s", OUT_DIR)

    session = _build_session()
    downloaded = 0
    skipped = 0
    failed = 0

    for i, item in enumerate(gallup_items, start=1):
        ntt_id = item.get("ntt_id", "")
        title = item.get("title_region", ntt_id)
        detail_url = item.get("detail_url", "")

        log.info("[%2d/%2d] ntt_id=%s  %s", i, len(gallup_items), ntt_id, title)

        if not detail_url:
            log.warning("  → detail_url 없음, SKIP")
            failed += 1
            continue

        try:
            resp = session.get(detail_url, timeout=20)
            resp.raise_for_status()
        except Exception as exc:
            log.error("  → 상세 페이지 오류: %s", exc)
            failed += 1
            time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        filename, pdf_url = _extract_pdf_url(soup)

        if not pdf_url:
            log.warning("  → PDF URL 없음, SKIP")
            failed += 1
            time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
            continue

        if args.dry_run:
            log.info("  → [DRY-RUN] %s", pdf_url)
            log.info("  → 파일명: %s", filename)
            time.sleep(0.2)
            continue

        safe_name = _safe_filename(filename or title, f"{ntt_id}.pdf")
        if not safe_name.lower().endswith(".pdf"):
            safe_name += ".pdf"
        dest = OUT_DIR / safe_name

        if dest.exists() and not args.force:
            log.info("  → SKIP (이미 존재: %s)", safe_name)
            skipped += 1
            time.sleep(0.3)
            continue

        try:
            pdf_resp = session.get(pdf_url, timeout=30, stream=True)
            pdf_resp.raise_for_status()
            content_type = pdf_resp.headers.get("Content-Type", "")
            if "pdf" not in content_type and len(pdf_resp.content) < 1024:
                log.warning("  → PDF 아님 (Content-Type: %s), SKIP", content_type)
                failed += 1
            else:
                dest.write_bytes(pdf_resp.content)
                size_kb = dest.stat().st_size // 1024
                log.info("  → 저장: %s (%d KB)", safe_name, size_kb)
                downloaded += 1
        except Exception as exc:
            log.error("  → 다운로드 오류: %s", exc)
            failed += 1

        time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

    log.info(
        "완료: 다운로드=%d, 스킵=%d, 실패=%d", downloaded, skipped, failed
    )
    if not args.dry_run:
        log.info("저장 경로: %s", OUT_DIR)


if __name__ == "__main__":
    main()
