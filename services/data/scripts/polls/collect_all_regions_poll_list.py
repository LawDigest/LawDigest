"""제9회 전국동시지방선거 전체 지역 여론조사 목록 수집 스크립트.

VT026 (광역단체장선거) 코드로 NESDC 전체를 스캔하여 지역별 목록을 수집한다.
페이지 필터 없이 전체를 수집한 뒤 지역(province) 필드로 분류한다.

사용법:
    cd services/data
    python scripts/polls/collect_all_regions_poll_list.py

출력:
    output/polls/lists/all_regions_9th.json       — 전체 레코드 (JSON)
    output/polls/lists/all_regions_9th.csv        — 전체 레코드 (CSV)
    output/polls/lists/all_regions_9th.ckpt       — 체크포인트 (재시작 지원)
"""
from __future__ import annotations

import csv
import json
import logging
import random
import re
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

_BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_BASE / "src"))

# ── 설정 ─────────────────────────────────────────────────────────────────────────

BASE_URL = "https://www.nesdc.go.kr"
LIST_PATH = "/portal/bbs/B0000005/list.do"
MENU_NO = "200467"

# 제9회 전국동시지방선거 광역단체장선거 코드
POLL_GUBUNCD = "VT026"

OUTPUT_SLUG = "all_regions_9th"

# 공공기관 서버 부하 방지: 요청 사이 대기 시간 (초)
MIN_DELAY = 2.0
MAX_DELAY = 4.0

MAX_PAGES = 500          # 안전 상한
CHECKPOINT_EVERY = 10    # N 페이지마다 중간 저장

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

# ── 로깅 ─────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
log = logging.getLogger(__name__)


# ── HTTP 세션 ─────────────────────────────────────────────────────────────────────

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
        backoff_factor=2.0,
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


# ── HTML 파싱 ─────────────────────────────────────────────────────────────────────

def _normalize(text: str) -> str:
    return re.sub(r"[\u00A0\s]+", " ", text).strip()


def _extract_query_param(url: str, key: str) -> Optional[str]:
    values = parse_qs(urlparse(url).query).get(key)
    return values[0] if values else None


def _parse_total_count(soup: BeautifulSoup) -> Optional[int]:
    for tag in soup.find_all(string=re.compile(r"총\s*[\d,]+")):
        m = re.search(r"총\s*([\d,]+)", tag)
        if m:
            return int(m.group(1).replace(",", ""))
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


# ── 체크포인트 ─────────────────────────────────────────────────────────────────────

def _load_checkpoint(ckpt_path: Path) -> tuple[int, List[Dict]]:
    if not ckpt_path.exists():
        return 0, []
    try:
        data = json.loads(ckpt_path.read_text(encoding="utf-8"))
        last_page = data.get("last_page", 0)
        records = data.get("records", [])
        log.info("체크포인트 로드: %d페이지까지 완료, %d건 누적", last_page, len(records))
        return last_page, records
    except Exception:
        log.warning("체크포인트 파일 손상 — 처음부터 재시작")
        return 0, []


def _save_checkpoint(ckpt_path: Path, last_page: int, records: List[Dict]) -> None:
    ckpt_path.write_text(
        json.dumps({"last_page": last_page, "records": records}, ensure_ascii=False),
        encoding="utf-8",
    )


# ── 저장 ─────────────────────────────────────────────────────────────────────────

def _save_json(path: Path, records: List[Dict]) -> None:
    path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


def _save_csv(path: Path, records: List[Dict]) -> None:
    if not records:
        return
    fieldnames = list(records[0].keys())
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


# ── 진행률 ────────────────────────────────────────────────────────────────────────

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
    rate = current / elapsed
    remaining = (total - current) / rate
    m, s = divmod(int(remaining), 60)
    return f"{m:02d}:{s:02d}"


# ── 통계 출력 ─────────────────────────────────────────────────────────────────────

def _print_stats(records: List[Dict]) -> None:
    log.info("─" * 60)
    log.info("[ 지역별(province) 분포 ]")
    province_cnt = Counter(r["province"] for r in records)
    for province, cnt in sorted(province_cnt.items(), key=lambda x: -x[1]):
        log.info("  %-20s %4d건", province, cnt)

    log.info("─" * 60)
    log.info("[ 조사기관별 분포 (상위 30개) ]")
    pollster_cnt = Counter(r["pollster"] for r in records)
    for pollster, cnt in pollster_cnt.most_common(30):
        log.info("  %-35s %4d건", pollster, cnt)

    log.info("─" * 60)
    log.info("[ 조사방법별 분포 ]")
    method_cnt = Counter(r["method"] for r in records)
    for method, cnt in sorted(method_cnt.items(), key=lambda x: -x[1]):
        log.info("  %-30s %4d건", method, cnt)


# ── 메인 ─────────────────────────────────────────────────────────────────────────

def main() -> None:
    output_dir = _BASE / "output" / "polls" / "lists"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_json = output_dir / f"{OUTPUT_SLUG}.json"
    output_csv  = output_dir / f"{OUTPUT_SLUG}.csv"
    ckpt_file   = output_dir / f"{OUTPUT_SLUG}.ckpt"

    session = _build_session()
    last_completed_page, all_records = _load_checkpoint(ckpt_file)
    start_page = last_completed_page + 1

    if last_completed_page > 0:
        log.info("이어서 수집합니다 (페이지 %d부터)", start_page)
    else:
        log.info("제9회 전국동시지방선거 전체 지역 여론조사 목록 수집 시작")
        log.info("pollGubuncd=%s (광역단체장선거)", POLL_GUBUNCD)

    seen_ids = {r["ntt_id"] for r in all_records if r.get("ntt_id")}

    total_pages_known: Optional[int] = None
    total_records_known: Optional[int] = None
    start_ts = time.monotonic()
    pages_done_this_run = 0
    consecutive_empty = 0

    log.info("딜레이 설정: %.1f~%.1fs / 요청 (공공기관 서버 부하 방지)", MIN_DELAY, MAX_DELAY)
    log.info("─" * 60)

    for page_index in range(start_page, MAX_PAGES + 1):
        params = {
            "menuNo":      MENU_NO,
            "pollGubuncd": POLL_GUBUNCD,
            "pageIndex":   str(page_index),
        }
        try:
            resp = session.get(urljoin(BASE_URL, LIST_PATH), params=params, timeout=20)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding or "utf-8"
        except requests.RequestException as exc:
            log.error("페이지 %d 요청 실패: %s", page_index, exc)
            log.info("30초 후 재시도합니다...")
            time.sleep(30)
            continue

        soup = BeautifulSoup(resp.text, "html.parser")

        if total_records_known is None:
            total_records_known = _parse_total_count(soup)
            if total_records_known:
                total_pages_known = (total_records_known + 9) // 10
                log.info("총 %d건 확인 → 예상 페이지 수: %d", total_records_known, total_pages_known)

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

        new_records = [r for r in page_records if r.get("ntt_id") not in seen_ids]
        for r in new_records:
            seen_ids.add(r["ntt_id"])
        all_records.extend(new_records)

        pages_done_this_run += 1
        elapsed = time.monotonic() - start_ts
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

        if page_index % CHECKPOINT_EVERY == 0:
            _save_checkpoint(ckpt_file, page_index, all_records)
            log.info("  → 체크포인트 저장 (%d페이지, %d건)", page_index, len(all_records))

        time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

    # ── 최종 저장 ──────────────────────────────────────────────────────────────────
    log.info("─" * 60)
    log.info("수집 완료: 총 %d건", len(all_records))

    _save_json(output_json, all_records)
    log.info("JSON 저장: %s", output_json)

    _save_csv(output_csv, all_records)
    log.info("CSV  저장: %s", output_csv)

    if ckpt_file.exists():
        ckpt_file.unlink()
        log.info("체크포인트 파일 삭제 완료")

    _print_stats(all_records)

    total_elapsed = time.monotonic() - start_ts
    m, s = divmod(int(total_elapsed), 60)
    log.info("─" * 60)
    log.info("총 소요 시간: %d분 %d초", m, s)


if __name__ == "__main__":
    main()
