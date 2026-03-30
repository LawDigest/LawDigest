from __future__ import annotations

import argparse
import csv
import json
import logging
import random
import re
import sys
import time
import unittest
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag
from requests import Response
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

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

# 조사방법 테이블 그룹 구조: 상세 페이지에서 조사방법 관련 테이블은
# table[2]부터 시작하여 방법 하나당 5개 테이블(header, 선정, 추출틀규모, 추출방법, 접촉현황)로 구성
_METHOD_TABLE_START = 2
_METHOD_TABLE_GROUP_SIZE = 5
_METHOD_COUNT = 5


class NesdcConnectionError(RuntimeError):
    """NESDC 사이트 연결 또는 응답 검증 실패."""


@dataclass
class ListRecord:
    registration_number: str
    pollster: str
    sponsor: str
    method: str
    sample_frame: str
    title_region: str
    registered_date: str
    province: str
    detail_url: str
    ntt_id: Optional[str] = None


@dataclass
class MethodStats:
    method_index: int
    method_name: str = ""
    method_share_percent: Optional[float] = None
    respondent_selection_method: str = ""
    target_population: str = ""
    sample_frame: str = ""
    frame_size: Optional[int] = None
    frame_build_method: str = ""
    sampling_method: str = ""
    notes: str = ""
    used_count: Optional[int] = None
    os_count: Optional[int] = None
    ne_count: Optional[int] = None
    u_count: Optional[int] = None
    r_count: Optional[int] = None
    i_count: Optional[int] = None
    total_count: Optional[int] = None
    contact_rate_percent: Optional[float] = None
    cooperation_rate_percent: Optional[float] = None


@dataclass
class PollDetail:
    source_url: str
    registration_number: str = ""
    election_type: str = ""
    region: str = ""
    election_name: str = ""
    sponsor: str = ""
    pollster: str = ""
    joint_pollster: str = ""
    surveyed_region: str = ""
    survey_datetimes: List[str] = field(default_factory=list)
    survey_duration: str = ""
    survey_target: str = ""
    sample_size_completed: Optional[int] = None
    sample_size_weighted: Optional[int] = None
    weighting_base_method: str = ""
    weighting_apply_method: str = ""
    extra_weighting_base_method: str = ""
    extra_weighting_apply_method: str = ""
    margin_of_error: str = ""
    publication_media_type: str = ""
    publication_media_name: str = ""
    first_publication_datetime: str = ""
    questionnaire_filename: str = ""
    questionnaire_download_url: str = ""
    analysis_filename: str = ""
    analysis_download_url: str = ""
    overall_landline_percent: Optional[float] = None
    overall_mobile_percent: Optional[float] = None
    overall_r_count: Optional[int] = None
    overall_i_count: Optional[int] = None
    overall_total_count: Optional[int] = None
    overall_contact_rate_percent: Optional[float] = None
    overall_response_rate_percent: Optional[float] = None
    methods: List[MethodStats] = field(default_factory=list)
    raw_text: str = ""


class NesdcCrawler:
    def __init__(
        self,
        output_dir: str | Path = "./output",
        timeout: int = 20,
        min_delay: float = 0.8,
        max_delay: float = 1.8,
        max_retries: int = 3,
        backoff_factor: float = 1.0,
        verify_connectivity: bool = True,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.session = self._build_session(max_retries=max_retries, backoff_factor=backoff_factor)
        self.logger = logging.getLogger(self.__class__.__name__)
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
            response = self.session.get(
                url,
                params=params,
                timeout=self.timeout,
                stream=stream,
            )
            response.raise_for_status()
            response.encoding = response.apparent_encoding or "utf-8"
            self._sleep()
            return response
        except requests.RequestException as exc:
            prepared_url = requests.Request("GET", url, params=params).prepare().url
            message = (
                "NESDC 사이트에 연결하지 못했습니다. "
                f"URL={prepared_url}. "
                "일시적인 네트워크 문제, 차단, 또는 사이트 장애일 수 있습니다. "
                "잠시 후 다시 시도하거나 max_retries/timeout 값을 늘려 보세요."
            )
            raise NesdcConnectionError(message) from exc

    def check_connectivity(self) -> None:
        try:
            response = self._get(urljoin(BASE_URL, LIST_PATH), params={"menuNo": DEFAULT_MENU_NO, "pageIndex": "1"})
        except NesdcConnectionError:
            raise

        text = response.text
        if not text or "<html" not in text.lower():
            raise NesdcConnectionError("NESDC 응답이 비정상적입니다. HTML 본문을 받지 못했습니다.")

    def fetch_list_page(self, page_index: int = 1, extra_params: Optional[Dict[str, str]] = None) -> BeautifulSoup:
        params = {
            "menuNo": DEFAULT_MENU_NO,
            "pageIndex": str(page_index),
        }
        if extra_params:
            params.update({k: v for k, v in extra_params.items() if v is not None})
        response = self._get(urljoin(BASE_URL, LIST_PATH), params=params)
        return BeautifulSoup(response.text, "html.parser")

    def parse_list_page(self, soup: BeautifulSoup) -> List[ListRecord]:
        """목록 페이지에서 여론조사 목록 레코드 파싱.

        NESDC 목록 페이지는 div.grid > a.row.tr 구조를 사용하며,
        각 a 태그 내에 span.col 8개(등록번호, 조사기관명, 조사의뢰자,
        조사방법, 표본추출틀, 명칭/지역, 등록일, 시도)가 있다.
        """
        records: List[ListRecord] = []
        for anchor in soup.select("a.row.tr[href*='view.do'][href*='nttId=']"):
            cols = [normalize_spaces(span.get_text(strip=True)) for span in anchor.find_all("span", class_="col")]
            if len(cols) < 8:
                self.logger.debug("목록 행 칼럼 수 부족(%d): %s", len(cols), anchor.get("href"))
                continue

            detail_url = urljoin(BASE_URL, anchor["href"])
            ntt_id = extract_query_param(detail_url, "nttId")
            records.append(
                ListRecord(
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
                )
            )
        return deduplicate_list_records(records)

    def fetch_detail_page(self, detail_url: str) -> BeautifulSoup:
        response = self._get(detail_url)
        return BeautifulSoup(response.text, "html.parser")

    def parse_detail_page(self, soup: BeautifulSoup, source_url: str) -> PollDetail:
        """상세 페이지에서 여론조사 상세 정보 파싱.

        NESDC 상세 페이지는 HTML 테이블(th/td) 구조를 사용한다.
        테이블 배치:
          [0]  기본 정보 (등록번호, 선거구분, 지역, ...)
          [1]  표본의 크기
          [2+5*n] 조사방법N 헤더 (방법명, 비율%)
          [3+5*n] 피조사자 선정방법 (조사대상, 추출틀, 규모, 구축방법)
          [4+5*n] 조사대상 추출틀 규모 (구성비율 - 수집 불필요)
          [5+5*n] 표본추출방법
          [6+5*n] 피조사자 접촉현황
          [27]  전체 유무선 비율 및 합계 통계
          [28]  가중값/표본오차/공표매체/첨부파일
        """
        detail = PollDetail(source_url=source_url, raw_text=soup.get_text("\n", strip=True))
        tables = soup.find_all("table")

        # ── 기본 정보 테이블 (table[0]) ──────────────────────────────
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

        # ── 표본의 크기 테이블 (table[1]) ────────────────────────────
        if len(tables) > 1:
            completed, weighted = _extract_sample_size(tables[1])
            detail.sample_size_completed = completed
            detail.sample_size_weighted = weighted

        # ── 조사방법 블록 (table[2]~[26], 5개씩) ────────────────────
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

        # ── 전체 통계 테이블 (table[27]) ─────────────────────────────
        overall_idx = _METHOD_TABLE_START + _METHOD_COUNT * _METHOD_TABLE_GROUP_SIZE
        if len(tables) > overall_idx:
            overall = tables[overall_idx]
            detail.overall_landline_percent, detail.overall_mobile_percent = _extract_phone_mix(overall)
            detail.overall_r_count = _int_td(overall, "접촉 후 거절 및 중도 이탈 사례수 (R) 합계")
            detail.overall_i_count = _int_td(overall, "접촉 후 응답완료 사례수 (I) 합계")
            detail.overall_total_count = _int_td(overall, "전체 합계")
            detail.overall_contact_rate_percent = _pct_td(overall, "전체 접촉률")
            detail.overall_response_rate_percent = _pct_td(overall, "전체 응답률")

        # ── 가중값/표본오차/공표/첨부 테이블 (table[28]) ──────────────
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
                self.logger.info("목록 페이지 %s건 파싱 완료: %s", page_index, len(records))
                all_records.extend(records)
            except NesdcConnectionError:
                if skip_errors:
                    self.logger.exception("목록 페이지 수집 실패, 다음 페이지로 건너뜁니다: %s", page_index)
                    continue
                raise
        return all_records

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

    def download_attachment(self, url: str, destination: Path) -> bool:
        if not url:
            return False
        response = self._get(url, stream=True)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(response.content)
        return True

    def save_list_csv(self, records: List[ListRecord], path: str | Path) -> None:
        write_csv(path, [asdict(record) for record in records])

    def save_details_csv(self, details: List[PollDetail], path: str | Path) -> None:
        rows = []
        for detail in details:
            base = asdict(detail)
            methods = base.pop("methods", [])
            base["methods_json"] = json.dumps(methods, ensure_ascii=False)
            rows.append(base)
        write_csv(path, rows)

    def save_details_json(self, details: List[PollDetail], path: str | Path) -> None:
        output = [asdict(detail) for detail in details]
        Path(path).write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")


# ── HTML 파싱 헬퍼 ─────────────────────────────────────────────────────────────

def normalize_spaces(text: str) -> str:
    """유니코드 공백 및 연속 공백을 단일 스페이스로 정규화."""
    return re.sub(r"[\u00A0\s]+", " ", text).strip()


def _cell_text(tag: Tag) -> str:
    return normalize_spaces(tag.get_text(strip=True))


def _td_for_th(table: Tag, th_key: str) -> str:
    """테이블에서 th_key 텍스트를 가진 th 다음의 td 값을 반환.

    한 행에 th가 여러 개인 경우(예: 기본가중|산출방법|[td]),
    th_key 위치에 해당하는 td를 찾는다. 중복 키가 있을 때는 첫 번째 값을 반환.
    """
    for row in table.find_all("tr"):
        ths = row.find_all("th")
        tds = row.find_all("td")
        if not ths or not tds:
            continue
        th_texts = [_cell_text(th) for th in ths]
        if th_key not in th_texts:
            continue
        th_idx = th_texts.index(th_key)
        # th가 여럿이고 td도 여럿인 경우: 1:1 매핑
        # th가 여럿이고 td가 하나인 경우: 모든 th가 같은 td를 가리킴
        td_idx = th_idx if th_idx < len(tds) else 0
        return _cell_text(tds[td_idx])
    return ""


def _table_pairs(table: Tag) -> List[Tuple[str, str]]:
    """테이블의 모든 (th텍스트, td텍스트) 쌍을 순서대로 반환.

    동일한 키가 여러 번 나타날 수 있음(예: 적용방법이 기본/추가가중 각각 존재).
    """
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
    """pairs에서 key에 해당하는 n번째(0-indexed) 값을 반환."""
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


def _extract_survey_datetimes(info_table: Tag) -> List[str]:
    """기본 정보 테이블에서 조사일시 td의 날짜+시간 문자열 목록 추출.

    td 내부 HTML에 날짜(YYYY-MM-DD)와 시·분이 여러 셀에 분산되어 있으므로
    get_text로 합친 뒤 정규식으로 추출한다.
    """
    for row in info_table.find_all("tr"):
        ths = row.find_all("th")
        tds = row.find_all("td")
        if ths and tds and "조사일시" in _cell_text(ths[0]):
            raw = normalize_spaces(tds[0].get_text(" ", strip=True))
            pattern = r"\d{4}-\d{2}-\d{2}\s*\d+\s*시\s*\d+\s*분\s*~\s*\d+\s*시\s*\d+\s*분"
            return [normalize_spaces(m) for m in re.findall(pattern, raw)]
    return []


def _extract_sample_size(size_table: Tag) -> Tuple[Optional[int], Optional[int]]:
    """표본의 크기 테이블에서 '전체' 행의 조사완료/가중값기준 사례수 반환."""
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


def _to_float(td: Tag) -> Optional[float]:
    text = _cell_text(td)
    m = re.search(r"([0-9]+(?:\.[0-9]+)?)", text)
    return float(m.group(1)) if m else None


def _extract_phone_mix(overall_table: Tag) -> Tuple[Optional[float], Optional[float]]:
    """전체 통계 테이블에서 유선/무선 비율 추출.

    해당 행: th=전체 유·무선 비율 | td=유선 | td=0% | td=무선 | td=100%
    """
    for row in overall_table.find_all("tr"):
        ths = row.find_all("th")
        tds = row.find_all("td")
        if ths and "전체 유·무선 비율" in _cell_text(ths[0]) and len(tds) >= 4:
            # tds[0]="유선", tds[1]="0%", tds[2]="무선", tds[3]="100%"
            landline = _pct_from_text(_cell_text(tds[1]))
            mobile = _pct_from_text(_cell_text(tds[3]))
            return landline, mobile
    return None, None


def _pct_from_text(text: str) -> Optional[float]:
    m = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*%", text)
    return float(m.group(1)) if m else None


def _parse_method_group(
    idx: int,
    header_table: Tag,
    selection_table: Tag,
    sampling_table: Tag,
    contact_table: Tag,
) -> Optional[MethodStats]:
    """조사방법 그룹(5개 테이블)에서 MethodStats 추출.

    헤더 테이블에 방법명과 비율%이 없으면 빈 방법으로 간주하여 None 반환.
    """
    # 헤더 테이블: 첫 번째 행 td=방법명, 두 번째 행 td=비율%
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

    # 방법명도 비율도 없으면 빈 슬롯 (NESDC 폼에 미기재)
    if not method_name and method_share is None:
        return None

    # 피조사자 선정방법 테이블
    target_population = _td_for_th(selection_table, "조사대상")
    # "추출틀" th가 마지막 th인 경우가 많음 (전체|추출틀|[td])
    sample_frame = _td_for_th(selection_table, "추출틀") or _td_for_th(selection_table, "표본 추출틀")
    frame_size = _int_td(selection_table, "규모")
    frame_build_method = _td_for_th(selection_table, "구축방법")

    # 표본추출방법 테이블
    sampling_method = _td_for_th(sampling_table, "표본추출방법")
    notes = _td_for_th(sampling_table, "기타")

    # 피조사자 접촉현황 테이블 (th 텍스트가 길어 prefix 매칭)
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
        respondent_selection_method="",  # NESDC 폼에 별도 입력 항목 없음
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


def _int_from_prefix(table: Tag, th_prefix: str) -> Optional[int]:
    """th 텍스트가 th_prefix로 시작하는 행의 td 정수값 반환."""
    for row in table.find_all("tr"):
        for th in row.find_all("th"):
            th_text = _cell_text(th)
            if th_text.startswith(th_prefix) or th_prefix in th_text:
                tds = row.find_all("td")
                if tds:
                    return _to_int(tds[-1])
    return None


def _extract_questionnaire(soup: BeautifulSoup, meta_table: Tag) -> Tuple[str, str]:
    """전체질문지 자료 파일명과 다운로드 URL 추출.

    NESDC는 파일 다운로드에 JavaScript onclick(view 함수)을 사용한다.
    onclick 파라미터를 추출하여 /portal/nsr/result/FileDown.do 형태로 변환하거나,
    파일명만 반환하여 수동 다운로드를 지원한다.
    """
    # 첨부파일 링크: <a class="ico_pdf" onclick="javascript:view(...)">파일명</a>
    for anchor in soup.select("a.ico_pdf, a[onclick*='view(']"):
        text = _cell_text(anchor)
        if not text:
            continue
        onclick = anchor.get("onclick", "")
        download_url = _build_file_download_url(onclick)
        return text, download_url
    # onclick 없이 직접 href로 연결된 경우
    td_text = _td_for_th(meta_table, "전체질문지 자료")
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        if href.lower().endswith(".pdf") or "download" in href.lower():
            return _cell_text(anchor) or td_text, urljoin(BASE_URL, href)
    return td_text, ""


def _extract_analysis(soup: BeautifulSoup, meta_table: Tag) -> Tuple[str, str]:
    """결과분석 자료 파일명과 다운로드 URL 추출.

    결과분석 자료는 공표 지정일 이후에만 다운로드 링크가 활성화된다.
    파일 다운로드 onclick이 있는 경우에만 URL을 반환하고,
    메뉴 탐색 링크(view.do, content 등)는 무시한다.
    """
    for anchor in soup.select("a.ico_hwp, a.ico_xls, a.ico_xlsx, a[onclick*='view(']"):
        onclick = anchor.get("onclick", "")
        # 질문지용 onclick은 이미 questionnaire에서 처리되었으므로 제외
        text = _cell_text(anchor)
        href = anchor.get("href", "")
        if "pdf" in text.lower() or "질문" in text:
            continue
        download_url = _build_file_download_url(onclick) if onclick else urljoin(BASE_URL, href)
        if download_url:
            return text, download_url
    # 다운로드 링크가 없으면 td 텍스트만 반환 (공표 전 또는 미첨부)
    td_text = _td_for_th(meta_table, "결과분석 자료")
    return td_text, ""


def _build_file_download_url(onclick: str) -> str:
    """onclick 문자열에서 NESDC 파일 다운로드 URL 구성.

    onclick 형식: javascript:view('encodedFileId', 'encodedNttId', 'bbsId', 'encodedMenuNo')
    파라미터는 이미 URL 인코딩된 상태이므로 그대로 쿼리스트링에 삽입한다.
    """
    m = re.search(r"view\('([^']+)',\s*'([^']+)',\s*'([^']+)',\s*'([^']+)'\)", onclick)
    if not m:
        return ""
    file_id, ntt_id, bbs_id, menu_no = m.group(1), m.group(2), m.group(3), m.group(4)
    params = f"atchFileId={file_id}&fileSn={ntt_id}&bbsId={bbs_id}&menuNo={menu_no}"
    return f"{BASE_URL}/portal/bbs/{bbs_id}/fileDown.do?{params}"


# ── 공통 유틸리티 ──────────────────────────────────────────────────────────────

def deduplicate_list_records(records: List[ListRecord]) -> List[ListRecord]:
    unique: Dict[str, ListRecord] = {}
    for record in records:
        key = record.ntt_id or record.detail_url
        unique[key] = record
    return list(unique.values())


def extract_query_param(url: str, key: str) -> Optional[str]:
    query = parse_qs(urlparse(url).query)
    values = query.get(key)
    return values[0] if values else None


def write_csv(path: str | Path, rows: List[Dict]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


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


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def safe_filename(value: str, default_name: str) -> str:
    cleaned = re.sub(r"[^\w\-.가-힣]+", "_", value).strip("_")
    return cleaned or default_name


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="NESDC 여론조사 결과 크롤러")
    parser.add_argument("--start-page", type=int, default=1, help="수집 시작 페이지")
    parser.add_argument("--end-page", type=int, default=2, help="수집 종료 페이지")
    parser.add_argument("--detail-limit", type=int, default=5, help="상세 수집 건수 제한")
    parser.add_argument("--output-dir", default="./output", help="출력 디렉터리")
    parser.add_argument("--timeout", type=int, default=20, help="요청 타임아웃(초)")
    parser.add_argument("--max-retries", type=int, default=3, help="재시도 횟수")
    parser.add_argument("--backoff-factor", type=float, default=1.0, help="재시도 백오프 계수")
    parser.add_argument("--skip-errors", action="store_true", help="일부 요청 실패 시 계속 진행")
    parser.add_argument("--download-attachments", action="store_true", help="질문지 PDF 다운로드")
    parser.add_argument("--no-connectivity-check", action="store_true", help="초기 연결 검사를 건너뜀")
    parser.add_argument("--run-tests", action="store_true", help="내장 단위 테스트 실행")
    return parser.parse_args(argv)


def run(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    if args.run_tests:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(ParserTests)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        return 0 if result.wasSuccessful() else 1

    configure_logging()

    try:
        crawler = NesdcCrawler(
            output_dir=args.output_dir,
            timeout=args.timeout,
            max_retries=args.max_retries,
            backoff_factor=args.backoff_factor,
            verify_connectivity=not args.no_connectivity_check,
        )

        search_params = build_search_params()
        list_records = crawler.crawl_list_pages(
            start_page=args.start_page,
            end_page=args.end_page,
            extra_params=search_params,
            skip_errors=args.skip_errors,
        )
        crawler.save_list_csv(list_records, Path(args.output_dir) / "nesdc_list.csv")

        detail_target = list_records[: args.detail_limit] if args.detail_limit >= 0 else list_records
        detail_records = crawler.crawl_details(detail_target, skip_errors=args.skip_errors)
        crawler.save_details_csv(detail_records, Path(args.output_dir) / "nesdc_details.csv")
        crawler.save_details_json(detail_records, Path(args.output_dir) / "nesdc_details.json")

        if args.download_attachments:
            attachment_dir = Path(args.output_dir) / "attachments"
            for detail in detail_records:
                if detail.questionnaire_download_url:
                    filename = safe_filename(
                        detail.questionnaire_filename,
                        f"{detail.registration_number or 'questionnaire'}.pdf",
                    )
                    crawler.download_attachment(detail.questionnaire_download_url, attachment_dir / filename)

        print(f"목록 {len(list_records)}건, 상세 {len(detail_records)}건 저장 완료")
        return 0
    except NesdcConnectionError as exc:
        logging.getLogger("main").error(str(exc))
        return 2
    except Exception as exc:
        logging.getLogger("main").exception("예상하지 못한 오류가 발생했습니다: %s", exc)
        return 1


# ── 단위 테스트 ────────────────────────────────────────────────────────────────

class ParserTests(unittest.TestCase):
    def test_extract_query_param(self) -> None:
        url = "https://www.nesdc.go.kr/portal/bbs/B0000005/view.do?menuNo=200467&nttId=17823&pageIndex=1"
        self.assertEqual(extract_query_param(url, "nttId"), "17823")

    def test_parse_list_page_span_col(self) -> None:
        """목록 페이지: a.row.tr > span.col 구조 파싱."""
        html = """
        <html><body>
        <div class="grid">
          <a class="row tr" href="/portal/bbs/B0000005/view.do?menuNo=200467&nttId=17823&pageIndex=1">
            <span class="col">17823</span>
            <span class="col">한국갤럽신문주식회사</span>
            <span class="col">중앙일보</span>
            <span class="col">전화면접</span>
            <span class="col">휴대전화가상번호</span>
            <span class="col">전국 대통령선거</span>
            <span class="col">2026-03-21</span>
            <span class="col">전국</span>
          </a>
        </div>
        </body></html>
        """
        crawler = NesdcCrawler(verify_connectivity=False, min_delay=0, max_delay=0)
        records = crawler.parse_list_page(BeautifulSoup(html, "html.parser"))
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].registration_number, "17823")
        self.assertEqual(records[0].pollster, "한국갤럽신문주식회사")
        self.assertEqual(records[0].sponsor, "중앙일보")
        self.assertEqual(records[0].method, "전화면접")
        self.assertEqual(records[0].sample_frame, "휴대전화가상번호")
        self.assertEqual(records[0].registered_date, "2026-03-21")
        self.assertEqual(records[0].province, "전국")
        self.assertEqual(records[0].ntt_id, "17823")

    def test_parse_list_page_sponsor_with_spaces(self) -> None:
        """목록 페이지: 의뢰자명에 공백이 포함된 경우도 올바르게 파싱."""
        html = """
        <html><body>
        <div class="grid">
          <a class="row tr" href="/portal/bbs/B0000005/view.do?menuNo=200467&nttId=99999">
            <span class="col">12345</span>
            <span class="col">한길리서치</span>
            <span class="col">좋은 교육감 만들기 경남 시민연대</span>
            <span class="col">무선 ARS</span>
            <span class="col">무선전화번호 가상번호</span>
            <span class="col">경상남도 전체 교육감선거</span>
            <span class="col">2026-03-30</span>
            <span class="col">경상남도</span>
          </a>
        </div>
        </body></html>
        """
        crawler = NesdcCrawler(verify_connectivity=False, min_delay=0, max_delay=0)
        records = crawler.parse_list_page(BeautifulSoup(html, "html.parser"))
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].sponsor, "좋은 교육감 만들기 경남 시민연대")
        self.assertEqual(records[0].method, "무선 ARS")

    def test_td_for_th_basic(self) -> None:
        """th→td 매핑 기본 동작."""
        html = """
        <table>
          <tr><th>등록 글번호</th><td>15850</td></tr>
          <tr><th>여론조사 명칭</th><th>선거구분</th><td>제9회 전국동시지방선거</td></tr>
          <tr><th>지역</th><td>대전광역시 전체</td></tr>
        </table>
        """
        table = BeautifulSoup(html, "html.parser").find("table")
        self.assertEqual(_td_for_th(table, "등록 글번호"), "15850")
        self.assertEqual(_td_for_th(table, "선거구분"), "제9회 전국동시지방선거")
        self.assertEqual(_td_for_th(table, "지역"), "대전광역시 전체")
        self.assertEqual(_td_for_th(table, "없는키"), "")

    def test_extract_sample_size(self) -> None:
        html = """
        <table>
          <tr><th>구분</th><th>조사완료 사례수(명)</th><th>가중값 적용 기준 사례수(명)</th></tr>
          <tr><th>전체</th><td>850</td><td>850</td></tr>
        </table>
        """
        table = BeautifulSoup(html, "html.parser").find("table")
        completed, weighted = _extract_sample_size(table)
        self.assertEqual(completed, 850)
        self.assertEqual(weighted, 850)

    def test_extract_phone_mix(self) -> None:
        html = """
        <table>
          <tr><th>전체 유·무선 비율</th><td>유선</td><td>10%</td><td>무선</td><td>90%</td></tr>
        </table>
        """
        table = BeautifulSoup(html, "html.parser").find("table")
        landline, mobile = _extract_phone_mix(table)
        self.assertEqual(landline, 10.0)
        self.assertEqual(mobile, 90.0)

    def test_pair_nth(self) -> None:
        """중복 키에서 n번째 값 추출."""
        pairs = [("산출방법", "성별·연령별"), ("적용방법", "셀가중"), ("산출방법", ""), ("적용방법", "")]
        self.assertEqual(_pair_nth(pairs, "산출방법", 0), "성별·연령별")
        self.assertEqual(_pair_nth(pairs, "산출방법", 1), "")
        self.assertEqual(_pair_nth(pairs, "적용방법", 0), "셀가중")
        self.assertEqual(_pair_nth(pairs, "없는키", 0), "")

    def test_write_csv_with_empty_rows(self) -> None:
        temp_path = Path("./_tmp_empty.csv")
        try:
            write_csv(temp_path, [])
            self.assertTrue(temp_path.exists())
            self.assertEqual(temp_path.read_text(encoding="utf-8"), "")
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_build_file_download_url(self) -> None:
        onclick = "javascript:view('abc%3D', 'def%3D', 'B0000005', 'ghi%3D')"
        url = _build_file_download_url(onclick)
        self.assertIn("fileDown.do", url)
        self.assertIn("B0000005", url)

    def test_get_wraps_connection_error(self) -> None:
        crawler = NesdcCrawler(verify_connectivity=False, min_delay=0, max_delay=0)

        class BrokenSession:
            headers = {}

            @staticmethod
            def get(*args, **kwargs):
                raise requests.ConnectionError("boom")

        crawler.session = BrokenSession()  # type: ignore[assignment]
        with self.assertRaises(NesdcConnectionError):
            crawler._get(urljoin(BASE_URL, LIST_PATH), params={"menuNo": DEFAULT_MENU_NO})


if __name__ == "__main__":
    raise SystemExit(run())
