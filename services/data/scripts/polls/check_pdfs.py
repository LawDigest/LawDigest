"""여론조사 상세 페이지 PDF 존재 여부 확인 스크립트.

사용법:
    cd services/data
    # 기본 (poll_targets.json의 첫 번째 타겟)
    python scripts/polls/check_pdfs.py

    # 특정 타겟 지정
    python scripts/polls/check_pdfs.py --target gyeonggi_governor_9th

입력 (slug 기반):
    output/polls/lists/{slug}.json  — collect_poll_list.py 수집 결과

출력 (slug 기반):
    output/polls/checks/{slug}.json  — 전체 결과
    output/polls/checks/{slug}.csv   — 결과 요약 (Excel 열람용)
    터미널: 건별 PDF 존재 여부 + 최종 요약
"""
from __future__ import annotations

import argparse
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

_BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_BASE / "src"))

from lawdigest_data.polls.targets import (  # noqa: E402
    is_ignored_analysis_filename,
    load_targets,
    matches_target,
)
from lawdigest_data.polls.models import ListRecord  # noqa: E402

# ── 설정 ─────────────────────────────────────────────────────────────────────────

BASE_URL = "https://www.nesdc.go.kr"

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

    if tables:
        for table in reversed(tables):
            val = _td_for_th(table, "최초 공표·보도 지정일시")
            if val:
                result["first_publication_datetime"] = val
                break

    return result


# ── 메인 ─────────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description="NESDC 여론조사 PDF 존재 여부 확인")
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
    list_json   = _BASE / "output" / "polls" / "lists" / f"{target.slug}.json"
    output_dir  = _BASE / "output" / "polls" / "checks"
    output_json = output_dir / f"{target.slug}.json"
    output_csv  = output_dir / f"{target.slug}.csv"

    if not list_json.exists():
        log.error("목록 파일이 없습니다: %s", list_json)
        log.error("먼저 scripts/polls/collect_poll_list.py --target %s 를 실행하세요.", target.slug)
        sys.exit(1)

    all_records = json.loads(list_json.read_text(encoding="utf-8"))

    # targets.py의 matches_target()으로 필터링 (config 기반)
    filtered = []
    for raw in all_records:
        record = ListRecord(
            registration_number=raw.get("registration_number", ""),
            pollster=raw.get("pollster", ""),
            sponsor=raw.get("sponsor", ""),
            method=raw.get("method", ""),
            sample_frame=raw.get("sample_frame", ""),
            title_region=raw.get("title_region", ""),
            registered_date=raw.get("registered_date", ""),
            province=raw.get("province", ""),
            ntt_id=raw.get("ntt_id"),
            detail_url=raw.get("detail_url", ""),
        )
        if matches_target(record, target):
            filtered.append(raw)

    log.info("타겟 '%s' 대상: %d건 (전체 %d건 중)", target.slug, len(filtered), len(all_records))
    log.info("딜레이: %.1f~%.1fs / 요청", MIN_DELAY, MAX_DELAY)
    log.info("─" * 65)

    session = build_session()
    results = []
    pdf_count = 0
    ignored_count = 0

    for i, record in enumerate(filtered, start=1):
        url = record["detail_url"]
        log.info(
            "[%2d/%2d] %s  %s",
            i, len(filtered),
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
        if detail["analysis_filename"] and is_ignored_analysis_filename(
            detail["analysis_filename"], target,
        ):
            ignored_count += 1
            log.info("         ↷ 예외 등록 PDF — 제외: %s", detail["analysis_filename"])
            time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
            continue

        results.append({**record, **detail})

        if detail["has_pdf"]:
            pdf_count += 1
            log.info("         ✔ PDF 있음  — %s", detail["analysis_filename"])
        else:
            log.info("         ✘ PDF 없음  (공표 전 또는 미첨부)")

        time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

    # ── 저장 ──────────────────────────────────────────────────────────────────────
    log.info("─" * 65)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_json.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    csv_fields = [
        "registration_number", "registered_date", "pollster", "sponsor",
        "title_region", "election_name", "region",
        "first_publication_datetime",
        "has_pdf", "analysis_filename", "analysis_url",
        "questionnaire_filename", "questionnaire_url",
        "detail_url",
    ]
    with output_csv.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=csv_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)

    log.info("JSON 저장: %s", output_json)
    log.info("CSV  저장: %s", output_csv)

    # ── 요약 ──────────────────────────────────────────────────────────────────────
    log.info("─" * 65)
    log.info("[ 결과 요약 ]")
    log.info("  전체 대상:     %2d건", len(filtered))
    log.info("  예외 제외:     %2d건", ignored_count)
    log.info("  PDF 있음:    %2d건  ← 최종 수집 대상", pdf_count)
    log.info(
        "  PDF 없음:    %2d건  (공표 전 또는 미첨부)",
        len(filtered) - ignored_count - pdf_count,
    )

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
