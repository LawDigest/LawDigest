"""여론조사 상세 페이지 PDF 존재 여부 확인 스크립트.

사용법:
    cd services/data
    python scripts/polls/check_pdfs.py

입력:
    output/polls/lists/9th_local.json  — collect_poll_list.py 수집 결과

출력:
    output/polls/checks/gyeonggi_governor.json  — 전체 결과
    output/polls/checks/gyeonggi_governor.csv   — 결과 요약 (Excel 열람용)
    터미널: 건별 PDF 존재 여부 + 최종 요약
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

import requests
from bs4 import BeautifulSoup, Tag
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ── 설정 ─────────────────────────────────────────────────────────────────────────

BASE_URL = "https://www.nesdc.go.kr"
_BASE = Path(__file__).resolve().parents[2]
LIST_JSON = _BASE / "output" / "polls" / "lists" / "9th_local.json"
OUTPUT_DIR = _BASE / "output" / "polls" / "checks"
OUTPUT_JSON = OUTPUT_DIR / "gyeonggi_governor.json"
OUTPUT_CSV  = OUTPUT_DIR / "gyeonggi_governor.csv"

MIN_DELAY = 2.0
MAX_DELAY = 4.0

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

# ── 로깅 ─────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
log = logging.getLogger(__name__)


# ── 유틸 ─────────────────────────────────────────────────────────────────────────

REGION_SUFFIX_RE = re.compile(r"[시군구읍면동리]$")


def parse_title_region(title_region: str) -> tuple[str, str]:
    text = title_region.strip()
    parts = text.split()
    if parts and parts[0] == "전국":
        return ("전국", " ".join(parts[1:]))
    idx = text.find(" 전체")
    if idx != -1:
        return (text[: idx + len(" 전체")].strip(), text[idx + len(" 전체"):].strip())
    if len(parts) >= 2 and REGION_SUFFIX_RE.search(parts[1]):
        return (f"{parts[0]} {parts[1]}", " ".join(parts[2:]))
    if len(parts) >= 2:
        return (parts[0], " ".join(parts[1:]))
    return ("", text)


def is_target(record: dict) -> bool:
    region, election_name = parse_title_region(record["title_region"])
    return region == "경기도 전체" and "광역단체장선거" in election_name


def normalize(text: str) -> str:
    return re.sub(r"[\u00A0\s]+", " ", text).strip()


# ── HTTP ─────────────────────────────────────────────────────────────────────────

def build_session() -> requests.Session:
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


# ── 상세 파싱 ─────────────────────────────────────────────────────────────────────

def _build_file_download_url(onclick: str) -> str:
    m = re.search(r"view\('([^']+)',\s*'([^']+)',\s*'([^']+)',\s*'([^']+)'\)", onclick)
    if not m:
        return ""
    atch_file_id, file_sn, bbs_id, bbs_key = m.groups()
    return (
        f"{BASE_URL}/portal/cmm/fms/FileDown.do"
        f"?atchFileId={atch_file_id}&fileSn={file_sn}&bbsId={bbs_id}&bbsKey={bbs_key}"
    )


def _td_for_th(table: Tag, th_key: str) -> str:
    for row in table.find_all("tr"):
        ths = row.find_all("th")
        tds = row.find_all("td")
        if not ths or not tds:
            continue
        th_texts = [normalize(th.get_text(strip=True)) for th in ths]
        if th_key not in th_texts:
            continue
        idx = th_texts.index(th_key)
        td_idx = idx if idx < len(tds) else 0
        return normalize(tds[td_idx].get_text(strip=True))
    return ""


def parse_detail(soup: BeautifulSoup, source_url: str) -> dict:
    result: dict = {
        "source_url": source_url,
        "election_type": "",
        "election_name": "",
        "region": "",
        "pollster": "",
        "sponsor": "",
        "first_publication_datetime": "",
        "questionnaire_filename": "",
        "questionnaire_url": "",
        "analysis_filename": "",
        "analysis_url": "",
        "has_pdf": False,
    }

    tables = soup.find_all("table")
    if tables:
        info = tables[0]
        result["election_type"]  = _td_for_th(info, "선거구분")
        result["election_name"]  = _td_for_th(info, "선거명")
        result["region"]         = _td_for_th(info, "지역")
        result["pollster"]       = _td_for_th(info, "조사기관명")
        result["sponsor"]        = _td_for_th(info, "조사의뢰자")

    # 첨부파일 링크 탐색 (onclick 기반)
    file_anchors = [
        (normalize(a.get_text(strip=True)), a.get("onclick", ""))
        for a in soup.select("a[onclick*='view(']")
        if normalize(a.get_text(strip=True))
    ]

    questionnaire_url = ""
    questionnaire_name = ""
    analysis_url = ""
    analysis_name = ""

    for text, onclick in file_anchors:
        url = _build_file_download_url(onclick)
        if any(k in text for k in ("설문지", "질문지")) and not questionnaire_url:
            questionnaire_name, questionnaire_url = text, url
        elif any(k in text for k in ("결과표", "결과분석", "분석")) and not analysis_url:
            analysis_name, analysis_url = text, url

    # 설문지/분석 파일이 명칭으로 구분 안 된 경우 순서로 fallback
    if not questionnaire_url and len(file_anchors) >= 1:
        questionnaire_name, onclick = file_anchors[0]
        questionnaire_url = _build_file_download_url(onclick)
    if not analysis_url and len(file_anchors) >= 2:
        analysis_name, onclick = file_anchors[1]
        analysis_url = _build_file_download_url(onclick)

    result["questionnaire_filename"] = questionnaire_name
    result["questionnaire_url"]      = questionnaire_url
    result["analysis_filename"]      = analysis_name
    result["analysis_url"]           = analysis_url
    result["has_pdf"]                = bool(analysis_url)

    # 최초 공표일시
    if tables:
        for table in reversed(tables):
            val = _td_for_th(table, "최초 공표·보도 지정일시")
            if val:
                result["first_publication_datetime"] = val
                break

    return result


# ── 메인 ─────────────────────────────────────────────────────────────────────────

def main() -> None:
    if not LIST_JSON.exists():
        log.error("목록 파일이 없습니다: %s", LIST_JSON)
        log.error("먼저 scripts/polls/collect_poll_list.py 를 실행하세요.")
        sys.exit(1)

    all_records = json.loads(LIST_JSON.read_text(encoding="utf-8"))
    targets = [r for r in all_records if is_target(r)]

    log.info("경기도 전체 광역단체장선거 대상: %d건", len(targets))
    log.info("딜레이: %.1f~%.1fs / 요청", MIN_DELAY, MAX_DELAY)
    log.info("─" * 65)

    session = build_session()
    results = []
    pdf_count = 0

    for i, record in enumerate(targets, start=1):
        url = record["detail_url"]
        log.info(
            "[%2d/%2d] %s  %s",
            i, len(targets),
            record["registration_number"],
            record["pollster"],
        )
        log.info("         %s", record["title_region"])

        try:
            resp = session.get(url, timeout=20)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding or "utf-8"
            soup = BeautifulSoup(resp.text, "html.parser")
        except requests.RequestException as exc:
            log.error("         요청 실패: %s", exc)
            results.append({**record, "has_pdf": False, "analysis_url": "", "error": str(exc)})
            time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
            continue

        detail = parse_detail(soup, url)
        merged = {**record, **detail}
        results.append(merged)

        if detail["has_pdf"]:
            pdf_count += 1
            log.info("         ✔ PDF 있음  — %s", detail["analysis_filename"])
        else:
            log.info("         ✘ PDF 없음  (공표 전 또는 미첨부)")

        time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

    # ── 저장 ──────────────────────────────────────────────────────────────────────
    log.info("─" * 65)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    OUTPUT_JSON.write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    csv_fields = [
        "registration_number", "registered_date", "pollster", "sponsor",
        "title_region", "election_name", "region",
        "first_publication_datetime",
        "has_pdf", "analysis_filename", "analysis_url",
        "questionnaire_filename", "questionnaire_url",
        "detail_url",
    ]
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=csv_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)

    log.info("JSON 저장: %s", OUTPUT_JSON)
    log.info("CSV  저장: %s", OUTPUT_CSV)

    # ── 요약 ──────────────────────────────────────────────────────────────────────
    log.info("─" * 65)
    log.info("[ 결과 요약 ]")
    log.info("  전체 대상:     %2d건", len(targets))
    log.info("  PDF 있음:    %2d건  ← 최종 수집 대상", pdf_count)
    log.info("  PDF 없음:    %2d건  (공표 전 또는 미첨부)", len(targets) - pdf_count)

    if pdf_count:
        log.info("")
        log.info("[ PDF 있는 항목 ]")
        for r in results:
            if r.get("has_pdf"):
                log.info(
                    "  %s  %-30s  %s",
                    r["registration_number"],
                    r["pollster"],
                    r["registered_date"],
                )


if __name__ == "__main__":
    main()
