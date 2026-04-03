"""NESDC 여론조사 목록/상세 크롤러."""
from __future__ import annotations

import json
import logging
import random
import re
import time
from dataclasses import asdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag
from requests import Response
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .models import (
    ListRecord,
    MethodStats,
    PollDetail,
    PollResultSet,
)
from .parser import PollResultParser
from .targets import PollTarget, matches_target

BASE_URL = "https://www.nesdc.go.kr"
LIST_PATH = "/portal/bbs/B0000005/list.do"
DEFAULT_MENU_NO = "200467"
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Referer": urljoin(BASE_URL, LIST_PATH),
}

_METHOD_TABLE_START = 2
_METHOD_TABLE_GROUP_SIZE = 5
_METHOD_COUNT = 5


class NesdcConnectionError(RuntimeError):
    """NESDC 사이트 연결 또는 응답 검증 실패."""


def _slug(t: PollTarget) -> str:
    return t.slug if t.slug else t.search_keyword


def extract_query_param(url: str, key: str) -> Optional[str]:
    query = parse_qs(urlparse(url).query)
    values = query.get(key)
    return values[0] if values else None


def normalize_spaces(text: str) -> str:
    return re.sub(r"[\u00A0\s]+", " ", text).strip()


def deduplicate_list_records(records: List[ListRecord]) -> List[ListRecord]:
    unique: Dict[str, ListRecord] = {}
    for record in records:
        key = record.ntt_id or record.detail_url
        unique[key] = record
    return list(unique.values())


def safe_filename(value: str, default_name: str) -> str:
    cleaned = re.sub(r"[^\w\-.가-힣]+", "_", value).strip("_")
    return cleaned or default_name


def build_search_params(
    *,
    search_cnd: Optional[str] = None,
    search_wrd: Optional[str] = None,
    sdate: Optional[str] = None,
    edate: Optional[str] = None,
    search_time: Optional[str] = None,
    poll_gubuncd: Optional[str] = None,
) -> Dict[str, str]:
    params: Dict[str, str] = {}
    if search_cnd:
        params["searchCnd"] = search_cnd
    if search_wrd:
        params["searchWrd"] = search_wrd
    if sdate:
        params["sdate"] = sdate
    if edate:
        params["edate"] = edate
    if search_time:
        params["searchTime"] = search_time
    if poll_gubuncd:
        params["pollGubuncd"] = poll_gubuncd
    return params


# ── HTML 파싱 헬퍼 ──────────────────────────────────────────────────────────────

def _cell_text(tag: Tag) -> str:
    return normalize_spaces(tag.get_text(strip=True))


def _td_for_th(table: Tag, th_key: str) -> str:
    for row in table.find_all("tr"):
        ths = row.find_all("th")
        tds = row.find_all("td")
        if not ths or not tds:
            continue
        th_texts = [_cell_text(th) for th in ths]
        if th_key not in th_texts:
            continue
        th_idx = th_texts.index(th_key)
        td_idx = th_idx if th_idx < len(tds) else 0
        return _cell_text(tds[td_idx])
    return ""


def _table_pairs(table: Tag) -> List[Tuple[str, str]]:
    pairs: List[Tuple[str, str]] = []
    for row in table.find_all("tr"):
        ths = row.find_all("th")
        tds = row.find_all("td")
        if not ths or not tds:
            continue
        if len(tds) == 1:
            td_text = _cell_text(tds[0])
            for th in ths:
                th_text = _cell_text(th)
                if th_text:
                    pairs.append((th_text, td_text))
        else:
            for th, td in zip(ths, tds):
                th_text = _cell_text(th)
                td_text = _cell_text(td)
                if th_text:
                    pairs.append((th_text, td_text))
    return pairs


def _pair_nth(pairs: List[Tuple[str, str]], key: str, n: int) -> str:
    found = [v for k, v in pairs if k == key]
    return found[n] if n < len(found) else ""


def _int_td(table: Tag, th_key: str) -> Optional[int]:
    text = _td_for_th(table, th_key)
    if not text:
        return None
    m = re.search(r"(\d+)", text.replace(",", ""))
    return int(m.group(1)) if m else None


def _pct_td(table: Tag, th_key: str) -> Optional[float]:
    text = _td_for_th(table, th_key)
    if not text:
        return None
    m = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*%", text)
    return float(m.group(1)) if m else None


def _pct_from_text(text: str) -> Optional[float]:
    m = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*%", text)
    return float(m.group(1)) if m else None


def _extract_survey_datetimes(info_table: Tag) -> List[str]:
    for row in info_table.find_all("tr"):
        ths = row.find_all("th")
        tds = row.find_all("td")
        if ths and tds and "조사일시" in _cell_text(ths[0]):
            raw = normalize_spaces(tds[0].get_text(" ", strip=True))
            pattern = r"\d{4}-\d{2}-\d{2}\s*\d+\s*시\s*\d+\s*분\s*~\s*\d+\s*시\s*\d+\s*분"
            return [normalize_spaces(m) for m in re.findall(pattern, raw)]
    return []


def _extract_sample_size(size_table: Tag) -> Tuple[Optional[int], Optional[int]]:
    for row in size_table.find_all("tr"):
        ths = row.find_all("th")
        tds = row.find_all("td")
        if ths and tds and _cell_text(ths[-1]) == "전체":
            completed = _to_int(tds[0]) if len(tds) > 0 else None
            weighted = _to_int(tds[1]) if len(tds) > 1 else None
            return completed, weighted
    return None, None


def _to_int(td: Tag) -> Optional[int]:
    text = _cell_text(td).replace(",", "")
    m = re.search(r"(\d+)", text)
    return int(m.group(1)) if m else None


def _extract_phone_mix(overall_table: Tag) -> Tuple[Optional[float], Optional[float]]:
    for row in overall_table.find_all("tr"):
        ths = row.find_all("th")
        tds = row.find_all("td")
        if ths and "전체 유·무선 비율" in _cell_text(ths[0]) and len(tds) >= 4:
            landline = _pct_from_text(_cell_text(tds[1]))
            mobile = _pct_from_text(_cell_text(tds[3]))
            return landline, mobile
    return None, None


def _int_from_prefix(table: Tag, th_prefix: str) -> Optional[int]:
    for row in table.find_all("tr"):
        for th in row.find_all("th"):
            th_text = _cell_text(th)
            if th_text.startswith(th_prefix) or th_prefix in th_text:
                tds = row.find_all("td")
                if tds:
                    return _to_int(tds[-1])
    return None


def _parse_method_group(
    idx: int,
    header_table: Tag,
    selection_table: Tag,
    sampling_table: Tag,
    contact_table: Tag,
) -> Optional[MethodStats]:
    rows = header_table.find_all("tr")
    method_name = ""
    method_share: Optional[float] = None
    if rows:
        first_tds = rows[0].find_all("td")
        method_name = _cell_text(first_tds[0]) if first_tds else ""
    if len(rows) > 1:
        second_tds = rows[1].find_all("td")
        if second_tds:
            method_share = _pct_from_text(_cell_text(second_tds[0]))

    if not method_name and method_share is None:
        return None

    target_population = _td_for_th(selection_table, "조사대상")
    sample_frame = _td_for_th(selection_table, "추출틀") or _td_for_th(selection_table, "표본 추출틀")
    frame_size = _int_td(selection_table, "규모")
    frame_build_method = _td_for_th(selection_table, "구축방법")
    sampling_method = _td_for_th(sampling_table, "표본추출방법")
    notes = _td_for_th(sampling_table, "기타")

    used_count = _int_from_prefix(contact_table, "사용규모")
    os_count = _int_from_prefix(contact_table, "결번 (OS)")
    ne_count = _int_from_prefix(contact_table, "그 외의 비적격 사례수(NE)")
    u_count = _int_from_prefix(contact_table, "접촉실패 사례수 (U)")
    r_count = _int_td(contact_table, "접촉 후 거절 및 중도 이탈 사례수 (R)")
    i_count = _int_td(contact_table, "접촉 후 응답완료 사례수 (I)")
    total_count = _int_td(contact_table, "합계")
    contact_rate = _pct_td(contact_table, "접촉률 (I+R)/(I+R+eU)")
    cooperation_rate = _pct_td(contact_table, "응답률 (I/(I+R))")

    return MethodStats(
        method_index=idx,
        method_name=method_name,
        method_share_percent=method_share,
        respondent_selection_method="",
        target_population=target_population,
        sample_frame=sample_frame,
        frame_size=frame_size,
        frame_build_method=frame_build_method,
        sampling_method=sampling_method,
        notes=notes,
        used_count=used_count,
        os_count=os_count,
        ne_count=ne_count,
        u_count=u_count,
        r_count=r_count,
        i_count=i_count,
        total_count=total_count,
        contact_rate_percent=contact_rate,
        cooperation_rate_percent=cooperation_rate,
    )


def _build_file_download_url(onclick: str) -> str:
    m = re.search(r"view\('([^']+)',\s*'([^']+)',\s*'([^']+)',\s*'([^']+)'\)", onclick)
    if not m:
        return ""
    atch_file_id, file_sn, bbs_id, bbs_key = m.group(1), m.group(2), m.group(3), m.group(4)
    params = f"atchFileId={atch_file_id}&fileSn={file_sn}&bbsId={bbs_id}&bbsKey={bbs_key}"
    return f"{BASE_URL}/portal/cmm/fms/FileDown.do?{params}"


def _collect_file_anchors(soup: BeautifulSoup) -> List[Tuple[str, str]]:
    results = []
    for anchor in soup.select("a[onclick*='view(']"):
        text = _cell_text(anchor)
        onclick = anchor.get("onclick", "")
        if text and onclick:
            results.append((text, onclick))
    return results


def _extract_questionnaire(soup: BeautifulSoup, meta_table: Tag) -> Tuple[str, str]:
    file_anchors = _collect_file_anchors(soup)
    for text, onclick in file_anchors:
        if any(k in text for k in ("설문지", "질문지")):
            return text, _build_file_download_url(onclick)
    if file_anchors:
        text, onclick = file_anchors[0]
        return text, _build_file_download_url(onclick)
    td_text = _td_for_th(meta_table, "전체질문지 자료")
    return td_text, ""


def _extract_analysis(soup: BeautifulSoup, meta_table: Tag) -> Tuple[str, str]:
    file_anchors = _collect_file_anchors(soup)
    for text, onclick in file_anchors:
        if any(k in text for k in ("결과표", "결과분석", "분석")):
            return text, _build_file_download_url(onclick)
    if len(file_anchors) >= 2:
        text, onclick = file_anchors[1]
        return text, _build_file_download_url(onclick)
    td_text = _td_for_th(meta_table, "결과분석 자료")
    return td_text, ""


# ── 크롤러 ──────────────────────────────────────────────────────────────────────

class NesdcCrawler:
    """NESDC 여론조사 목록/상세 HTTP 크롤러."""

    def __init__(
        self,
        output_dir: str | Path = "./output",
        timeout: int = 20,
        min_delay: float = 0.8,
        max_delay: float = 1.8,
        max_retries: int = 3,
        backoff_factor: float = 1.0,
        verify_connectivity: bool = True,
        registry_path: Optional[Path] = None,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.session = self._build_session(max_retries=max_retries, backoff_factor=backoff_factor)
        self.logger = logging.getLogger(self.__class__.__name__)
        self._registry_path = registry_path
        if verify_connectivity:
            self.check_connectivity()

    @staticmethod
    def _build_session(max_retries: int, backoff_factor: float) -> requests.Session:
        session = requests.Session()
        session.headers.update(DEFAULT_HEADERS)
        retry = Retry(
            total=max_retries,
            connect=max_retries,
            read=max_retries,
            status=max_retries,
            allowed_methods=frozenset(["GET", "HEAD"]),
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=backoff_factor,
            raise_on_status=False,
            respect_retry_after_header=True,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def _sleep(self) -> None:
        if self.max_delay <= 0:
            return
        time.sleep(random.uniform(self.min_delay, self.max_delay))

    def _get(self, url: str, *, params: Optional[Dict[str, str]] = None, stream: bool = False) -> Response:
        try:
            response = self.session.get(url, params=params, timeout=self.timeout, stream=stream)
            response.raise_for_status()
            response.encoding = response.apparent_encoding or "utf-8"
            self._sleep()
            return response
        except requests.RequestException as exc:
            prepared_url = requests.Request("GET", url, params=params).prepare().url
            raise NesdcConnectionError(
                f"NESDC 사이트에 연결하지 못했습니다. URL={prepared_url}"
            ) from exc

    def check_connectivity(self) -> None:
        response = self._get(
            urljoin(BASE_URL, LIST_PATH),
            params={"menuNo": DEFAULT_MENU_NO, "pageIndex": "1"},
        )
        if not response.text or "<html" not in response.text.lower():
            raise NesdcConnectionError("NESDC 응답이 비정상적입니다.")

    def fetch_list_page(self, page_index: int = 1, extra_params: Optional[Dict[str, str]] = None) -> BeautifulSoup:
        params: Dict[str, str] = {"menuNo": DEFAULT_MENU_NO, "pageIndex": str(page_index)}
        if extra_params:
            params.update({k: v for k, v in extra_params.items() if v is not None})
        response = self._get(urljoin(BASE_URL, LIST_PATH), params=params)
        return BeautifulSoup(response.text, "html.parser")

    def parse_list_page(self, soup: BeautifulSoup) -> List[ListRecord]:
        records: List[ListRecord] = []
        for anchor in soup.select("a.row.tr[href*='view.do'][href*='nttId=']"):
            cols = [normalize_spaces(span.get_text(strip=True)) for span in anchor.find_all("span", class_="col")]
            if len(cols) < 8:
                continue
            detail_url = urljoin(BASE_URL, anchor["href"])
            ntt_id = extract_query_param(detail_url, "nttId")
            records.append(ListRecord(
                registration_number=cols[0],
                pollster=cols[1],
                sponsor=cols[2],
                method=cols[3],
                sample_frame=cols[4],
                title_region=cols[5],
                registered_date=cols[6],
                province=cols[7],
                detail_url=detail_url,
                ntt_id=ntt_id,
            ))
        return deduplicate_list_records(records)

    def fetch_detail_page(self, detail_url: str) -> BeautifulSoup:
        response = self._get(detail_url)
        return BeautifulSoup(response.text, "html.parser")

    def parse_detail_page(self, soup: BeautifulSoup, source_url: str) -> PollDetail:
        detail = PollDetail(source_url=source_url, raw_text=soup.get_text("\n", strip=True))
        tables = soup.find_all("table")

        if tables:
            info = tables[0]
            detail.registration_number = _td_for_th(info, "등록 글번호")
            detail.election_type = _td_for_th(info, "선거구분")
            detail.region = _td_for_th(info, "지역")
            detail.election_name = _td_for_th(info, "선거명")
            detail.sponsor = _td_for_th(info, "조사의뢰자")
            detail.pollster = _td_for_th(info, "조사기관명")
            detail.joint_pollster = _td_for_th(info, "공동조사기관명")
            detail.surveyed_region = _td_for_th(info, "조사지역")
            detail.survey_datetimes = _extract_survey_datetimes(info)
            detail.survey_duration = _td_for_th(info, "조사시간")
            detail.survey_target = _td_for_th(info, "조사대상")

        if len(tables) > 1:
            completed, weighted = _extract_sample_size(tables[1])
            detail.sample_size_completed = completed
            detail.sample_size_weighted = weighted

        methods: List[MethodStats] = []
        for i in range(_METHOD_COUNT):
            base = _METHOD_TABLE_START + i * _METHOD_TABLE_GROUP_SIZE
            if base + 4 >= len(tables):
                break
            method = _parse_method_group(
                idx=i + 1,
                header_table=tables[base],
                selection_table=tables[base + 1],
                sampling_table=tables[base + 3],
                contact_table=tables[base + 4],
            )
            if method is not None:
                methods.append(method)
        detail.methods = methods

        overall_idx = _METHOD_TABLE_START + _METHOD_COUNT * _METHOD_TABLE_GROUP_SIZE
        if len(tables) > overall_idx:
            overall = tables[overall_idx]
            detail.overall_landline_percent, detail.overall_mobile_percent = _extract_phone_mix(overall)
            detail.overall_r_count = _int_td(overall, "접촉 후 거절 및 중도 이탈 사례수 (R) 합계")
            detail.overall_i_count = _int_td(overall, "접촉 후 응답완료 사례수 (I) 합계")
            detail.overall_total_count = _int_td(overall, "전체 합계")
            detail.overall_contact_rate_percent = _pct_td(overall, "전체 접촉률")
            detail.overall_response_rate_percent = _pct_td(overall, "전체 응답률")

        meta_idx = overall_idx + 1
        if len(tables) > meta_idx:
            meta = tables[meta_idx]
            pairs = _table_pairs(meta)
            detail.weighting_base_method = _pair_nth(pairs, "산출방법", 0)
            detail.weighting_apply_method = _pair_nth(pairs, "적용방법", 0)
            detail.extra_weighting_base_method = _pair_nth(pairs, "산출방법", 1)
            detail.extra_weighting_apply_method = _pair_nth(pairs, "적용방법", 1)
            detail.margin_of_error = _td_for_th(meta, "표본오차")
            detail.publication_media_type = _td_for_th(meta, "공표·보도 매체")
            detail.publication_media_name = _td_for_th(meta, "공표·보도 매체명")
            detail.first_publication_datetime = _td_for_th(meta, "최초 공표·보도 지정일시")
            detail.questionnaire_filename, detail.questionnaire_download_url = _extract_questionnaire(soup, meta)
            detail.analysis_filename, detail.analysis_download_url = _extract_analysis(soup, meta)

        return detail

    def crawl_list_pages(
        self,
        start_page: int = 1,
        end_page: int = 1,
        extra_params: Optional[Dict[str, str]] = None,
        skip_errors: bool = False,
    ) -> List[ListRecord]:
        all_records: List[ListRecord] = []
        for page_index in range(start_page, end_page + 1):
            self.logger.info("목록 페이지 수집 중: %s", page_index)
            try:
                soup = self.fetch_list_page(page_index=page_index, extra_params=extra_params)
                records = self.parse_list_page(soup)
                if not records:
                    self.logger.info("빈 페이지, 수집 종료: %s", page_index)
                    break
                all_records.extend(records)
            except NesdcConnectionError:
                if skip_errors:
                    self.logger.exception("목록 페이지 수집 실패: %s", page_index)
                    continue
                raise
        return all_records

    def crawl_all_pages(self, max_pages: int = 500, skip_errors: bool = True) -> List[ListRecord]:
        """전체 카탈로그 스캔 — 필터 없이 빈 페이지를 만날 때까지 수집."""
        all_records: List[ListRecord] = []
        for page_index in range(1, max_pages + 1):
            self.logger.info("카탈로그 스캔: 페이지 %d", page_index)
            try:
                soup = self.fetch_list_page(page_index=page_index)
                records = self.parse_list_page(soup)
                if not records:
                    self.logger.info("빈 페이지 도달, 카탈로그 스캔 완료: %d페이지", page_index - 1)
                    break
                all_records.extend(records)
            except NesdcConnectionError:
                if skip_errors:
                    self.logger.exception("카탈로그 스캔 실패: 페이지 %d", page_index)
                    continue
                raise
        return all_records

    def crawl_for_targets(
        self,
        targets: List[PollTarget],
        max_pages_per_target: int = 50,
        skip_errors: bool = False,
    ) -> Dict[str, List[ListRecord]]:
        """타겟별 NESDC 서버 사이드 검색 + 클라이언트 사이드 필터링.

        동일 (poll_gubuncd, search_cnd, search_wrd) 조합의 타겟은 한 번만 검색해
        네트워크를 절약한다.
        """
        results: Dict[str, List[ListRecord]] = {_slug(t): [] for t in targets}

        # 동일 검색 조합끼리 묶기
        search_key_to_targets: Dict[tuple, List[PollTarget]] = {}
        for t in targets:
            key = (t.poll_gubuncd, t.search_cnd, t.search_wrd)
            search_key_to_targets.setdefault(key, []).append(t)

        for (poll_gubuncd, search_cnd, search_wrd), group_targets in search_key_to_targets.items():
            self.logger.info(
                "검색 시작: pollGubuncd=%s searchCnd=%s searchWrd=%s (타겟 %d개)",
                poll_gubuncd, search_cnd, search_wrd, len(group_targets),
            )
            search_params = build_search_params(
                poll_gubuncd=poll_gubuncd or None,
                search_cnd=search_cnd or None,
                search_wrd=search_wrd or None,
            )

            for page_index in range(1, max_pages_per_target + 1):
                try:
                    soup = self.fetch_list_page(page_index=page_index, extra_params=search_params)
                    records = self.parse_list_page(soup)
                except NesdcConnectionError:
                    if skip_errors:
                        self.logger.exception(
                            "페이지 수집 실패: pollGubuncd=%s searchWrd=%s page=%d",
                            poll_gubuncd, search_wrd, page_index,
                        )
                        break
                    raise

                if not records:
                    self.logger.info(
                        "빈 페이지, 수집 종료: pollGubuncd=%s searchWrd=%s page=%d",
                        poll_gubuncd, search_wrd, page_index,
                    )
                    break

                for record in records:
                    for target in group_targets:
                        if matches_target(record, target):
                            results[_slug(target)].append(record)

            for t in group_targets:
                self.logger.info("타겟 '%s' 매칭 완료: %d건", _slug(t), len(results[_slug(t)]))

        return results

    def crawl_details(self, records: Iterable[ListRecord], skip_errors: bool = True) -> List[PollDetail]:
        details: List[PollDetail] = []
        for idx, record in enumerate(records, start=1):
            self.logger.info("상세 수집 중 (%s): %s", idx, record.detail_url)
            try:
                soup = self.fetch_detail_page(record.detail_url)
                detail = self.parse_detail_page(soup, source_url=record.detail_url)
                if not detail.registration_number:
                    detail.registration_number = record.registration_number
                if not detail.pollster:
                    detail.pollster = record.pollster
                if not detail.sponsor:
                    detail.sponsor = record.sponsor
                if not detail.region:
                    detail.region = record.province
                details.append(detail)
            except (requests.HTTPError, NesdcConnectionError) as exc:
                if skip_errors:
                    self.logger.exception("상세 요청 실패: %s", exc)
                    continue
                raise
            except Exception as exc:
                if skip_errors:
                    self.logger.exception("상세 파싱 실패: %s", exc)
                    continue
                raise
        return details

    def download_result_pdf(self, detail: PollDetail, destination: Path) -> bool:
        if not detail.analysis_download_url:
            return False
        self._get(detail.source_url)
        response = self._get(detail.analysis_download_url, stream=True)
        if b"%PDF" not in response.content[:10]:
            self.logger.warning("결과 PDF 다운로드 실패 (PDF 시그니처 없음): %s", detail.source_url)
            return False
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(response.content)
        return True

    def crawl_results(
        self,
        details: List[PollDetail],
        pdf_dir: str | Path = "./pdfs",
        skip_errors: bool = True,
        registry_path: Optional[Path] = None,
    ) -> List[PollResultSet]:
        """결과분석 자료 PDF를 다운로드하고 파서 레지스트리를 적용해 파싱한다."""
        parser = PollResultParser(registry_path=registry_path or self._registry_path)
        pdf_dir = Path(pdf_dir)
        result_sets: List[PollResultSet] = []
        for detail in details:
            if not detail.analysis_download_url:
                self.logger.info("결과 URL 없음(공표 전?): %s", detail.registration_number)
                continue
            filename = safe_filename(
                detail.analysis_filename,
                f"{detail.registration_number or 'result'}.pdf",
            )
            if not filename.endswith(".pdf"):
                filename += ".pdf"
            pdf_path = pdf_dir / filename
            try:
                if not pdf_path.exists():
                    ok = self.download_result_pdf(detail, pdf_path)
                    if not ok:
                        continue
                questions = parser.parse_pdf(pdf_path, pollster_hint=detail.pollster)
                result_sets.append(PollResultSet(
                    registration_number=detail.registration_number,
                    source_url=detail.source_url,
                    pdf_path=str(pdf_path),
                    questions=questions,
                ))
                self.logger.info("결과 파싱 완료: %s, 질문 %d개", detail.registration_number, len(questions))
            except Exception as exc:
                if skip_errors:
                    self.logger.exception("결과 파싱 실패: %s", exc)
                else:
                    raise
        return result_sets

    def save_details_json(self, details: List[PollDetail], path: str | Path) -> None:
        output = [asdict(detail) for detail in details]
        Path(path).write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    def save_results_json(self, result_sets: List[PollResultSet], path: str | Path) -> None:
        output = [asdict(rs) for rs in result_sets]
        Path(path).write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
