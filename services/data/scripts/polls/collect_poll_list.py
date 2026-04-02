"""여론조사 목록 전체 수집 스크립트 (NESDC 포털).

사용법:
    cd services/data
    python scripts/polls/collect_poll_list.py

출력:
    output/polls/lists/9th_local.json   — 전체 레코드 (JSON)
    output/polls/lists/9th_local.csv    — 전체 레코드 (CSV, 분석용)
    output/polls/lists/9th_local.ckpt   — 페이지별 체크포인트 (재시작 지원)
"""
from __future__ import annotations

import csv
import json
import logging
import random
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin, parse_qs, urlparse

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ── 설정 ────────────────────────────────────────────────────────────────────────

POLL_GUBUNCD = "VT026"          # 제9회 전국동시지방선거
BASE_URL = "https://www.nesdc.go.kr"
LIST_PATH = "/portal/bbs/B0000005/list.do"
MENU_NO = "200467"

# 공공기관 서버 부하 방지: 요청 사이 대기 시간 (초)
MIN_DELAY = 2.0
MAX_DELAY = 4.0

MAX_PAGES = 200          # 안전 상한 (실제 페이지 수 초과 시 자동 종료)
CHECKPOINT_EVERY = 10    # N 페이지마다 중간 저장

_BASE = Path(__file__).resolve().parents[2]
OUTPUT_DIR = _BASE / "output" / "polls" / "lists"
OUTPUT_JSON = OUTPUT_DIR / "9th_local.json"
OUTPUT_CSV = OUTPUT_DIR / "9th_local.csv"
CHECKPOINT_FILE = OUTPUT_DIR / "9th_local.ckpt"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Referer": urljoin(BASE_URL, LIST_PATH),
}

# ── 로깅 설정 ────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
log = logging.getLogger(__name__)


# ── HTTP 세션 ────────────────────────────────────────────────────────────────────

def _build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(HEADERS)
    retry = Retry(
        total=5,
        connect=5,
        read=5,
        status=5,
        allowed_methods=frozenset(["GET", "HEAD"]),
        status_forcelist=[429, 500, 502, 503, 504],
        backoff_factor=2.0,          # 2s → 4s → 8s … 지수 백오프
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


# ── HTML 파싱 ────────────────────────────────────────────────────────────────────

def _normalize(text: str) -> str:
    return re.sub(r"[\u00A0\s]+", " ", text).strip()


def _extract_query_param(url: str, key: str) -> Optional[str]:
    values = parse_qs(urlparse(url).query).get(key)
    return values[0] if values else None


def _parse_total_count(soup: BeautifulSoup) -> Optional[int]:
    """페이지 상단 '총 N건' 또는 '검색결과 N건' 텍스트에서 총 건수 추출."""
    for tag in soup.find_all(string=re.compile(r"총\s*[\d,]+")):
        m = re.search(r"총\s*([\d,]+)", tag)
        if m:
            return int(m.group(1).replace(",", ""))
    # 대안: 숫자가 포함된 span/p 탐색
    for tag in soup.select(".total, .totalCnt, .search_result_count"):
        m = re.search(r"([\d,]+)", tag.get_text())
        if m:
            return int(m.group(1).replace(",", ""))
    return None


def _parse_list_page(soup: BeautifulSoup) -> List[Dict]:
    records = []
    for anchor in soup.select("a.row.tr[href*='view.do'][href*='nttId=']"):
        cols = [_normalize(span.get_text(strip=True)) for span in anchor.find_all("span", class_="col")]
        if len(cols) < 8:
            continue
        detail_url = urljoin(BASE_URL, anchor["href"])
        ntt_id = _extract_query_param(detail_url, "nttId")
        records.append({
            "registration_number": cols[0],
            "pollster":            cols[1],
            "sponsor":             cols[2],
            "method":              cols[3],
            "sample_frame":        cols[4],
            "title_region":        cols[5],
            "registered_date":     cols[6],
            "province":            cols[7],
            "ntt_id":              ntt_id,
            "detail_url":          detail_url,
        })
    return records


# ── 체크포인트 ────────────────────────────────────────────────────────────────────

def _load_checkpoint() -> tuple[int, List[Dict]]:
    """저장된 체크포인트에서 (마지막_페이지, 누적_레코드) 반환."""
    if not CHECKPOINT_FILE.exists():
        return 0, []
    try:
        data = json.loads(CHECKPOINT_FILE.read_text(encoding="utf-8"))
        last_page = data.get("last_page", 0)
        records = data.get("records", [])
        log.info("체크포인트 로드: %d페이지까지 완료, %d건 누적", last_page, len(records))
        return last_page, records
    except Exception:
        log.warning("체크포인트 파일 손상 — 처음부터 재시작")
        return 0, []


def _save_checkpoint(last_page: int, records: List[Dict]) -> None:
    CHECKPOINT_FILE.write_text(
        json.dumps({"last_page": last_page, "records": records}, ensure_ascii=False),
        encoding="utf-8",
    )


# ── 저장 ─────────────────────────────────────────────────────────────────────────

def _save_json(records: List[Dict]) -> None:
    OUTPUT_JSON.write_text(
        json.dumps(records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _save_csv(records: List[Dict]) -> None:
    if not records:
        return
    fieldnames = list(records[0].keys())
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


# ── 진행률 출력 ──────────────────────────────────────────────────────────────────

def _progress_bar(current: int, total: int, width: int = 30) -> str:
    if total <= 0:
        return "[??????????]"
    filled = int(width * current / total)
    bar = "█" * filled + "░" * (width - filled)
    pct = current / total * 100
    return f"[{bar}] {pct:5.1f}%"


def _eta_str(elapsed: float, current: int, total: int) -> str:
    if current <= 0 or total <= 0:
        return "--:--"
    rate = current / elapsed           # 페이지/초
    remaining = (total - current) / rate
    m, s = divmod(int(remaining), 60)
    return f"{m:02d}:{s:02d}"


# ── 메인 ─────────────────────────────────────────────────────────────────────────

def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    session = _build_session()

    # 체크포인트 확인
    last_completed_page, all_records = _load_checkpoint()
    start_page = last_completed_page + 1

    if last_completed_page > 0:
        log.info("이어서 수집합니다 (페이지 %d부터)", start_page)
    else:
        log.info("제9회 전국동시지방선거 여론조사 목록 수집 시작")

    seen_ids = {r["ntt_id"] for r in all_records if r.get("ntt_id")}

    total_pages_known: Optional[int] = None
    total_records_known: Optional[int] = None
    start_ts = time.monotonic()
    pages_done_this_run = 0
    consecutive_empty = 0

    log.info("딜레이 설정: %.1f~%.1fs / 요청 (공공기관 서버 부하 방지)", MIN_DELAY, MAX_DELAY)
    log.info("─" * 60)

    for page_index in range(start_page, MAX_PAGES + 1):
        # ── 요청 ──────────────────────────────────────────────────────────────
        params = {
            "menuNo":      MENU_NO,
            "pollGubuncd": POLL_GUBUNCD,
            "pageIndex":   str(page_index),
        }
        try:
            resp = session.get(
                urljoin(BASE_URL, LIST_PATH),
                params=params,
                timeout=20,
            )
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding or "utf-8"
        except requests.RequestException as exc:
            log.error("페이지 %d 요청 실패: %s", page_index, exc)
            log.info("30초 후 재시도합니다...")
            time.sleep(30)
            continue

        soup = BeautifulSoup(resp.text, "html.parser")

        # ── 총 건수 파악 (첫 페이지에서만) ────────────────────────────────────
        if total_records_known is None:
            total_records_known = _parse_total_count(soup)
            if total_records_known:
                total_pages_known = (total_records_known + 9) // 10
                log.info(
                    "총 %d건 확인 → 예상 페이지 수: %d",
                    total_records_known, total_pages_known,
                )

        # ── 파싱 ──────────────────────────────────────────────────────────────
        page_records = _parse_list_page(soup)

        if not page_records:
            consecutive_empty += 1
            log.info("페이지 %d: 데이터 없음 (연속 빈 페이지: %d회)", page_index, consecutive_empty)
            if consecutive_empty >= 2:
                log.info("연속 빈 페이지 2회 — 수집 완료로 판단합니다.")
                break
            time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
            continue
        else:
            consecutive_empty = 0

        # 중복 제거
        new_records = [r for r in page_records if r.get("ntt_id") not in seen_ids]
        for r in new_records:
            seen_ids.add(r["ntt_id"])
        all_records.extend(new_records)

        pages_done_this_run += 1
        elapsed = time.monotonic() - start_ts

        # ── 진행률 출력 ────────────────────────────────────────────────────────
        known_total_p = total_pages_known or MAX_PAGES
        bar = _progress_bar(page_index, known_total_p)
        eta = _eta_str(elapsed, pages_done_this_run, known_total_p - last_completed_page)

        log.info(
            "페이지 %3d/%s  %s  누적 %d건  +%d건  ETA %s",
            page_index,
            str(known_total_p) if total_pages_known else "?",
            bar,
            len(all_records),
            len(new_records),
            eta,
        )

        # ── 체크포인트 저장 ────────────────────────────────────────────────────
        if page_index % CHECKPOINT_EVERY == 0:
            _save_checkpoint(page_index, all_records)
            log.info("  → 체크포인트 저장 (%d페이지, %d건)", page_index, len(all_records))

        # ── 딜레이 (서버 부하 방지) ────────────────────────────────────────────
        delay = random.uniform(MIN_DELAY, MAX_DELAY)
        time.sleep(delay)

    # ── 최종 저장 ────────────────────────────────────────────────────────────────
    log.info("─" * 60)
    log.info("수집 완료: 총 %d건", len(all_records))

    _save_json(all_records)
    log.info("JSON 저장: %s", OUTPUT_JSON)

    _save_csv(all_records)
    log.info("CSV  저장: %s", OUTPUT_CSV)

    # 체크포인트 삭제 (정상 완료)
    if CHECKPOINT_FILE.exists():
        CHECKPOINT_FILE.unlink()
        log.info("체크포인트 파일 삭제 완료")

    # ── 간단 통계 출력 ────────────────────────────────────────────────────────────
    log.info("─" * 60)
    log.info("[ 지역별 분포 (상위 15개) ]")
    from collections import Counter
    province_cnt = Counter(r["province"] for r in all_records)
    for province, cnt in province_cnt.most_common(15):
        log.info("  %-15s %4d건", province, cnt)

    log.info("─" * 60)
    log.info("[ 조사기관별 분포 (상위 15개) ]")
    pollster_cnt = Counter(r["pollster"] for r in all_records)
    for pollster, cnt in pollster_cnt.most_common(15):
        log.info("  %-30s %4d건", pollster, cnt)

    log.info("─" * 60)
    total_elapsed = time.monotonic() - start_ts
    m, s = divmod(int(total_elapsed), 60)
    log.info("총 소요 시간: %d분 %d초", m, s)


if __name__ == "__main__":
    main()
