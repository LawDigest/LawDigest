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


@dataclass(frozen=True)
class PollTarget:
    """수집 대상 선거를 정의하는 불변 데이터클래스.

    search_keyword로 NESDC searchWrd 검색을 수행한 뒤,
    region / election_names 조건으로 클라이언트 사이드 필터링한다.
    election_type은 상세 페이지 수준에서 사용하는 추가 정보이며
    목록 필터링에는 사용하지 않는다.
    """
    search_keyword: str                            # NESDC searchWrd에 사용할 검색어 (지역명 등)
    region: Optional[str] = None                   # title_region의 지역 부분과 매칭
    election_names: Optional[Tuple[str, ...]] = None  # 선거명 OR 매칭 (None = 전체)
    election_type: Optional[str] = None            # 선거구분 (참고용, 로그/출력에 사용)
    slug: str = ""                                 # 출력 디렉터리명 (빈 경우 search_keyword 사용)


# 수집 대상 선거 목록 (필요에 따라 항목 추가)
POLL_TARGETS: List[PollTarget] = [
    # 예시 – 실제 수집 전 필요한 선거로 교체하세요
    PollTarget(
        search_keyword="전라남도",
        region="전라남도 전체",
        election_names=("광역단체장선거", "정당지지도"),
        election_type="제9회 전국동시지방선거",
        slug="9th_local_jeonnam_governor",
    ),
]


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


@dataclass
class QuestionResult:
    """여론조사 결과표 PDF에서 파싱한 개별 설문 항목의 결과."""
    question_number: int
    question_title: str           # 예: "시흥시장 후보 여야 지지도"
    question_text: str            # 예: "Q1. 올해 6월 시흥시장 선거에 출마가..."
    response_options: List[str]   # 응답 선택지 이름 목록 (best-effort)
    overall_n_completed: Optional[int]   # 전체 조사완료 사례수
    overall_n_weighted: Optional[int]    # 전체 가중값 적용 사례수
    overall_percentages: List[float]     # 전체 행의 응답 비율 (response_options 순)


@dataclass
class PollResultSet:
    """한 여론조사의 결과표 PDF에서 추출한 전체 결과."""
    registration_number: str
    source_url: str
    pdf_path: str
    questions: List[QuestionResult] = field(default_factory=list)


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

    def download_result_pdf(self, detail: PollDetail, destination: Path) -> bool:
        """결과분석 자료 PDF를 다운로드한다.

        공표 전이거나 URL이 없으면 False를 반환한다.
        세션이 이미 해당 상세 페이지를 방문한 뒤여야 쿠키가 유효하다.
        """
        if not detail.analysis_download_url:
            return False
        # 쿠키 확보를 위해 상세 페이지 선방문
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
    ) -> List["PollResultSet"]:
        """결과분석 자료 PDF를 다운로드하고 파싱하여 PollResultSet 목록을 반환한다."""
        parser = PollResultParser()
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
                self.logger.info(
                    "결과 파싱 완료: %s, 질문 %d개",
                    detail.registration_number, len(questions),
                )
            except Exception as exc:
                if skip_errors:
                    self.logger.exception("결과 파싱 실패: %s", exc)
                else:
                    raise
        return result_sets

    def save_results_json(self, result_sets: List["PollResultSet"], path: str | Path) -> None:
        output = [asdict(rs) for rs in result_sets]
        Path(path).write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    def crawl_for_targets(
        self,
        targets: List[PollTarget],
        max_pages_per_target: int = 50,
        skip_errors: bool = False,
    ) -> Dict[str, List[ListRecord]]:
        """타겟 목록별로 NESDC를 검색하고 매칭된 레코드를 반환한다.

        동일 search_keyword를 가진 타겟은 한 번만 검색하여 네트워크 요청을 절약한다.
        빈 페이지를 만나면 해당 키워드 수집을 중단한다.

        Returns:
            {target.slug or search_keyword: [매칭된 ListRecord, ...]}
        """
        def _slug(t: PollTarget) -> str:
            return t.slug if t.slug else t.search_keyword

        results: Dict[str, List[ListRecord]] = {_slug(t): [] for t in targets}

        # 동일 keyword 타겟 묶기
        keyword_to_targets: Dict[str, List[PollTarget]] = {}
        for t in targets:
            keyword_to_targets.setdefault(t.search_keyword, []).append(t)

        for keyword, kw_targets in keyword_to_targets.items():
            self.logger.info(
                "검색어 '%s' 수집 시작 (타겟 %d개)", keyword, len(kw_targets)
            )
            search_params = build_search_params(search_wrd=keyword)

            for page_index in range(1, max_pages_per_target + 1):
                try:
                    soup = self.fetch_list_page(
                        page_index=page_index, extra_params=search_params
                    )
                    records = self.parse_list_page(soup)
                except NesdcConnectionError:
                    if skip_errors:
                        self.logger.exception(
                            "페이지 수집 실패: keyword=%s page=%d", keyword, page_index
                        )
                        break
                    raise

                if not records:
                    self.logger.info(
                        "빈 페이지, 수집 종료: keyword=%s page=%d", keyword, page_index
                    )
                    break

                for record in records:
                    for target in kw_targets:
                        if matches_target(record, target):
                            results[_slug(target)].append(record)

            for t in kw_targets:
                self.logger.info(
                    "타겟 '%s' 매칭 완료: %d건", _slug(t), len(results[_slug(t)])
                )

        return results

    def save_target_results(
        self,
        target_records: Dict[str, List[ListRecord]],
        output_dir: str | Path,
    ) -> None:
        """타겟별 수집 결과를 output_dir/<slug>/list.csv로 저장한다.

        list.csv에는 ListRecord 필드 외에 parsed_region, parsed_election_name 컬럼이 추가된다.
        """
        output_dir = Path(output_dir)
        for slug, records in target_records.items():
            target_dir = output_dir / slug
            target_dir.mkdir(parents=True, exist_ok=True)
            rows = []
            for r in records:
                row = asdict(r)
                row["parsed_region"], row["parsed_election_name"] = parse_title_region(
                    r.title_region
                )
                rows.append(row)
            write_csv(target_dir / "list.csv", rows)
            self.logger.info(
                "저장 완료: %s (%d건)", target_dir / "list.csv", len(records)
            )


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
    """전체질문지 자료(설문지) 파일명과 다운로드 URL 추출.

    NESDC 첨부파일은 realfile_N div 안에 순서대로 나열된다.
    질문지는 파일명에 '설문지' 또는 '질문지'가 포함된 첫 번째 파일이다.
    없으면 첫 번째 파일을 질문지로 간주한다.
    """
    file_anchors = _collect_file_anchors(soup)
    for text, onclick in file_anchors:
        if any(k in text for k in ("설문지", "질문지")):
            return text, _build_file_download_url(onclick)
    # 키워드 없으면 첫 번째 파일
    if file_anchors:
        text, onclick = file_anchors[0]
        return text, _build_file_download_url(onclick)
    td_text = _td_for_th(meta_table, "전체질문지 자료")
    return td_text, ""


def _extract_analysis(soup: BeautifulSoup, meta_table: Tag) -> Tuple[str, str]:
    """결과분석 자료(결과표) 파일명과 다운로드 URL 추출.

    결과분석 자료는 공표 지정일 이후에만 다운로드 링크가 활성화된다.
    파일명에 '결과표', '결과분석', '분석' 등이 포함된 파일을 우선 반환한다.
    없으면 두 번째 파일(설문지 다음)을 결과표로 간주한다.
    활성화 전(공표 전)에는 빈 URL을 반환한다.
    """
    file_anchors = _collect_file_anchors(soup)
    for text, onclick in file_anchors:
        if any(k in text for k in ("결과표", "결과분석", "분석")):
            return text, _build_file_download_url(onclick)
    # 키워드 없으면 두 번째 파일 (첫 번째가 설문지라고 가정)
    if len(file_anchors) >= 2:
        text, onclick = file_anchors[1]
        return text, _build_file_download_url(onclick)
    td_text = _td_for_th(meta_table, "결과분석 자료")
    return td_text, ""


def _collect_file_anchors(soup: BeautifulSoup) -> List[Tuple[str, str]]:
    """페이지의 모든 첨부파일 링크를 (파일명, onclick) 형태로 순서대로 반환."""
    results = []
    for anchor in soup.select("a[onclick*='view(']"):
        text = _cell_text(anchor)
        onclick = anchor.get("onclick", "")
        if text and onclick:
            results.append((text, onclick))
    return results


def _build_file_download_url(onclick: str) -> str:
    """onclick 문자열에서 NESDC 파일 다운로드 URL 구성.

    NESDC view() 함수 정의:
      location.href = '/portal/cmm/fms/FileDown.do
        ?atchFileId='+atchFileId+'&fileSn='+fileSn+'&bbsId='+bbsId+'&bbsKey='+bbsKey

    onclick 형식: view('atchFileId', 'fileSn', 'bbsId', 'bbsKey')
    파라미터는 이미 URL 인코딩된 상태이므로 그대로 쿼리스트링에 삽입한다.
    """
    m = re.search(r"view\('([^']+)',\s*'([^']+)',\s*'([^']+)',\s*'([^']+)'\)", onclick)
    if not m:
        return ""
    atch_file_id, file_sn, bbs_id, bbs_key = m.group(1), m.group(2), m.group(3), m.group(4)
    params = f"atchFileId={atch_file_id}&fileSn={file_sn}&bbsId={bbs_id}&bbsKey={bbs_key}"
    return f"{BASE_URL}/portal/cmm/fms/FileDown.do?{params}"


# ── PDF 결과 파서 ──────────────────────────────────────────────────────────────

@dataclass
class ParserRegistryEntry:
    """파서 레지스트리 항목.

    pollster_keywords: 조사기관명에 포함될 키워드 (OR 매칭)
    content_probe: PDF 전문에서 탐지할 문자열 (None = 탐지 없이 적용)
    priority: 높을수록 먼저 적용
    """
    parser_class: type
    pollster_keywords: Tuple[str, ...] = field(default_factory=tuple)
    content_probe: Optional[str] = None
    priority: int = 0


def register_parser(entry: ParserRegistryEntry) -> None:
    """외부에서 새로운 파서를 레지스트리에 등록한다."""
    _PARSER_REGISTRY.append(entry)
    _PARSER_REGISTRY.sort(key=lambda e: e.priority, reverse=True)


# _PARSER_REGISTRY 는 _TextFormatParser / _TableFormatParser 정의 이후에 초기화됨
# (모듈 하단 참조)
_PARSER_REGISTRY: List[ParserRegistryEntry] = []


class PollResultParser:
    """결과표 PDF에서 설문 항목별 응답 결과를 추출하는 파서.

    NESDC에 등록된 결과표 PDF는 조사기관마다 레이아웃이 다르므로,
    PDF 내용을 분석하여 아래 두 가지 하위 파서 중 하나를 선택한다.

    [텍스트 형식] 데일리리서치 등
      'N) 섹션명'으로 섹션이 시작되고, 각 옵션이 '선택지명 X.X' 형태로 나열된다.

    [테이블 형식] 조원씨앤아이 등
      각 페이지의 테이블 첫 번째 '전체' 행에 '▣ 전체 ▣'가 있으며,
      해당 행의 각 셀이 선택지별 전체 비율이다.
    """

    def parse_pdf(
        self,
        pdf_path: Path,
        pollster_hint: Optional[str] = None,
    ) -> List[QuestionResult]:
        """PDF 파일을 파싱하여 QuestionResult 목록을 반환한다.

        Args:
            pdf_path: 결과표 PDF 경로.
            pollster_hint: 조사기관명 힌트. 레지스트리에서 기관별 파서를 우선 선택한다.
        """
        try:
            import pdfplumber
        except ImportError as exc:
            raise RuntimeError(
                "PDF 파싱을 위해 pdfplumber가 필요합니다: uv add pdfplumber"
            ) from exc

        pages_data: List[Tuple[str, List]] = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                tables = page.extract_tables() or []
                pages_data.append((text, tables))

        full_text = "\n".join(t for t, _ in pages_data)
        parser_class = self._select_parser(full_text, pollster_hint)

        if issubclass(parser_class, _TableFormatParser):
            return parser_class().parse(pages_data)
        else:
            return parser_class().parse(full_text)

    def _select_parser(
        self,
        full_text: str,
        pollster_hint: Optional[str],
    ) -> type:
        """레지스트리에서 적합한 파서 클래스를 선택한다.

        우선순위:
        1. pollster_hint가 registry 항목의 pollster_keywords에 매칭
           + (content_probe 없거나 전문에 존재)
        2. content_probe가 전문에 존재 (기관 무관 항목)
        3. fallback: content_probe=None인 첫 항목
        """
        # 1단계: pollster_hint 기반 매칭
        if pollster_hint:
            for entry in _PARSER_REGISTRY:
                if entry.pollster_keywords and any(
                    kw in pollster_hint for kw in entry.pollster_keywords
                ):
                    if entry.content_probe is None or entry.content_probe in full_text:
                        return entry.parser_class

        # 2단계: content_probe 기반 매칭
        for entry in _PARSER_REGISTRY:
            if entry.content_probe and entry.content_probe in full_text:
                return entry.parser_class

        # 3단계: fallback (content_probe=None인 첫 항목)
        for entry in _PARSER_REGISTRY:
            if entry.content_probe is None:
                return entry.parser_class

        return _TextFormatParser  # 최후 fallback


class _TextFormatParser:
    """텍스트 형식 파서 – 데일리리서치 등.

    섹션 헤더: 'N) 섹션명'
    질문 텍스트: 헤더 직후 '?' 까지 (없으면 섹션명으로 대체)
    결과 행: '선택지명 X.X' (☞ 소계는 제외)
    """

    _SECTION_NUM_TITLE_RE = re.compile(r"^(\d+)\)\s+(.+)$", re.MULTILINE)
    _OPTION_PCT_RE = re.compile(r"^(.+?)\s+([\d.]+)$")
    # 교차분석 시작 마커 (이 이후는 교차표이므로 파싱 중단)
    _CROSSTAB_MARKERS = ["자료 처리 방법", "교차분석", "교차 분석", "Ⅱ. 조사"]
    # 결과 섹션 시작 마커
    _RESULTS_MARKERS = ["설문 항목별 결과", "조사결과", "제2장 조사결과"]

    def parse(self, full_text: str) -> List[QuestionResult]:
        text = self._extract_results_section(full_text)
        sections = list(self._SECTION_NUM_TITLE_RE.finditer(text))
        results: List[QuestionResult] = []
        for i, m in enumerate(sections):
            q_num = int(m.group(1))
            q_title = m.group(2).strip()

            block_start = m.end()
            block_end = sections[i + 1].start() if i + 1 < len(sections) else len(text)
            block = text[block_start:block_end].strip()

            # 질문 텍스트: ? 까지
            q_text_m = re.search(r"[?？]", block)
            if q_text_m:
                q_text = block[: q_text_m.end()].strip()
                options_block = block[q_text_m.end():]
            else:
                q_text = q_title
                options_block = block

            options: List[str] = []
            percentages: List[float] = []
            for line in options_block.splitlines():
                line = line.strip()
                if not line or line.startswith("☞") or line.startswith("-"):
                    continue
                om = self._OPTION_PCT_RE.match(line)
                if om:
                    opt = om.group(1).strip()
                    pct = float(om.group(2))
                    # 교차표 행 감지: 텍스트에 3자리 이상 정수가 2개 이상이면 사례수 행
                    has_sample_counts = len(re.findall(r"(?<!\w)\d{3,}(?!\w)", opt)) >= 2
                    # 숫자·기호만이거나 너무 길거나 교차표 행이면 제외
                    if (
                        1 < len(opt) <= 60
                        and not re.fullmatch(r"[\d().%\-\s]+", opt)
                        and not has_sample_counts
                    ):
                        options.append(opt)
                        percentages.append(pct)

            if not percentages:
                continue

            results.append(QuestionResult(
                question_number=q_num,
                question_title=q_title,
                question_text=q_text,
                response_options=options,
                overall_n_completed=None,
                overall_n_weighted=None,
                overall_percentages=percentages,
            ))
        return results

    def _extract_results_section(self, text: str) -> str:
        """설문 결과 섹션만 추출한다 (교차분석 섹션 이전까지)."""
        # 시작점: 결과 섹션 마커 중 가장 먼저 나타나는 위치
        start = 0
        for marker in self._RESULTS_MARKERS:
            pos = text.find(marker)
            if pos != -1:
                start = pos
                break

        # 종료점: 교차분석 마커 중 가장 먼저 나타나는 위치
        end = len(text)
        for marker in self._CROSSTAB_MARKERS:
            pos = text.find(marker, start)
            if pos != -1 and pos < end:
                end = pos

        return text[start:end]


class _TableFormatParser:
    """테이블 형식 파서 – 조원씨앤아이 등.

    각 페이지에 교차표 형태의 테이블이 있으며 구조는 다음과 같다:
      row[0]: 열 헤더 (col[0]='(단위:%)', col[2]=조사완료사례수,
                       col[3..N-2]=선택지명, col[-1]=가중값적용사례수)
      row[1]: 전체 행 ('▣ 전체 ▣' / None / (N완료) / X.X / ... / (N가중))
      row[2+]: 교차 세부 집단 행

    섹션 제목은 페이지 텍스트에서 'N. 제목' 또는 'N. 제목' 패턴으로 추출한다.
    """

    _SECTION_RE = re.compile(r"^문?(\d+)[.)]\s+([^\n]+)$", re.MULTILINE)
    _N_RE = re.compile(r"\((\d+)\)")

    def parse(self, pages_data: List[Tuple[str, List]]) -> List[QuestionResult]:
        results: List[QuestionResult] = []
        for page_text, page_tables in pages_data:
            for table in page_tables:
                result = self._parse_table(table, page_text)
                if result is not None:
                    results.append(result)
        # 번호가 중복될 수 있으므로 순서대로 재할당
        for i, r in enumerate(results):
            r.question_number = i + 1
        return results

    def _parse_table(
        self, table: List[List], page_text: str
    ) -> Optional[QuestionResult]:
        if not table or len(table) < 2:
            return None

        # '전체' 키워드가 포함된 행을 전체 결과 행으로 사용
        total_row: Optional[List] = None
        for row in table[1:]:
            if row and row[0] and "전체" in str(row[0]):
                total_row = row
                break
        if total_row is None:
            return None

        header_row = table[0]

        # 사례수
        n_completed = self._extract_n(str(total_row[2] if len(total_row) > 2 else ""))
        n_weighted = self._extract_n(str(total_row[-1]))

        # 선택지 이름과 퍼센트를 함께 파싱 (col[3..N-2])
        # 중간합계 열 제거: 헤더에 "(합)" / "합계" / "소계" 포함된 열은 스킵
        _SUBTOTAL_RE = re.compile(r"\(합\)|합계|소계")
        options: List[str] = []
        percentages: List[float] = []
        for header_cell, value_cell in zip(header_row[3:-1], total_row[3:-1]):
            # 줄바꿈/null 바이트 제거 후 연결 (공백 없이) → "더불\n어민\n주당" → "더불어민주당"
            opt = re.sub(r"[\n\x00]", "", str(header_cell or "")).strip()
            if not opt or opt.lower() == "none" or _SUBTOTAL_RE.search(opt):
                continue
            try:
                pct = float(str(value_cell or "").strip())
            except ValueError:
                continue
            options.append(opt)
            percentages.append(pct)

        if not percentages:
            return None

        # 동일한 옵션명+퍼센트 중복 제거 (예: 모름이 중간합계 제거 후 중복되는 경우)
        seen: set = set()
        deduped_options: List[str] = []
        deduped_pcts: List[float] = []
        for opt, pct in zip(options, percentages):
            key = (opt, pct)
            if key not in seen:
                seen.add(key)
                deduped_options.append(opt)
                deduped_pcts.append(pct)
        options, percentages = deduped_options, deduped_pcts

        # 페이지 텍스트에서 섹션 제목 추출 (null 바이트 제거 후 첫 번째 매치 사용)
        section_matches = list(self._SECTION_RE.finditer(page_text.replace("\x00", "")))
        if section_matches:
            q_num = int(section_matches[0].group(1))
            q_title = section_matches[0].group(2).strip()
        else:
            q_num = 0
            q_title = ""

        return QuestionResult(
            question_number=q_num,
            question_title=q_title,
            question_text="",
            response_options=options,
            overall_n_completed=n_completed,
            overall_n_weighted=n_weighted,
            overall_percentages=percentages,
        )

    def _extract_n(self, text: str) -> Optional[int]:
        # "(N)" 형식 우선, 없으면 순수 정수 문자열 시도
        text = text.strip()
        m = self._N_RE.search(text)
        if m:
            return int(m.group(1))
        try:
            return int(text)
        except ValueError:
            return None


# 파서 클래스 정의 완료 후 레지스트리 초기화 (forward reference 방지)
_PARSER_REGISTRY.extend([
    ParserRegistryEntry(
        parser_class=_TableFormatParser,
        pollster_keywords=("조원씨앤아이",),
        content_probe="▣ 전체 ▣",
        priority=10,
    ),
    ParserRegistryEntry(
        parser_class=_TextFormatParser,
        pollster_keywords=("데일리리서치",),
        content_probe=None,
        priority=10,
    ),
    # 메타서치: 크로스탭 테이블 기반 (조원씨앤아이와 동일한 _TableFormatParser)
    ParserRegistryEntry(
        parser_class=_TableFormatParser,
        pollster_keywords=("메타서치",),
        content_probe=None,
        priority=10,
    ),
    # content_probe 기반 fallback — "가중값적용사례수"는 한국 여론조사 크로스탭 PDF 범용 마커
    ParserRegistryEntry(
        parser_class=_TableFormatParser,
        pollster_keywords=(),
        content_probe="가중값적용사례수",
        priority=5,
    ),
    # content_probe 기반 fallback (기관 무관)
    ParserRegistryEntry(
        parser_class=_TableFormatParser,
        pollster_keywords=(),
        content_probe="▣ 전체 ▣",
        priority=0,
    ),
    ParserRegistryEntry(
        parser_class=_TextFormatParser,
        pollster_keywords=(),
        content_probe=None,
        priority=0,
    ),
])
_PARSER_REGISTRY.sort(key=lambda e: e.priority, reverse=True)


# ── 공통 유틸리티 ──────────────────────────────────────────────────────────────

# ── 타겟 매칭 유틸리티 ─────────────────────────────────────────────────────────


_REGION_SUFFIX_RE = re.compile(r"[시군구읍면동리]$")


def parse_title_region(title_region: str) -> Tuple[str, str]:
    """ListRecord.title_region(col[5])에서 지역과 선거명을 분리한다.

    NESDC title_region 형식: "<지역> <선거명>"

    지역 끝 판별 규칙 (우선순위순):
      1. "전국" 으로 시작하면 → region = "전국"
      2. " 전체" 가 포함되면 → region = "... 전체" 까지
      3. 두 번째 토큰이 시/군/구/읍/면/동/리 로 끝나면 → region = 첫 두 토큰
      4. 그 외 → region = 첫 토큰

    예:
      "경기도 안산시 기초단체장선거 정당지지도"
        → ("경기도 안산시", "기초단체장선거 정당지지도")
      "전라남도 전체 광역단체장선거,정당지지도"
        → ("전라남도 전체", "광역단체장선거,정당지지도")
      "전국 대통령선거"
        → ("전국", "대통령선거")
    """
    text = title_region.strip()
    parts = text.split()

    # 1. 전국
    if parts and parts[0] == "전국":
        return ("전국", " ".join(parts[1:]))

    # 2. "... 전체" 패턴 (광역단위 전체)
    idx = text.find(" 전체")
    if idx != -1:
        region = text[: idx + len(" 전체")].strip()
        election_name = text[idx + len(" 전체"):].strip()
        return (region, election_name)

    # 3. 도 + 시/군/구 패턴 (두 번째 토큰이 지역 단위 접미사로 끝남)
    if len(parts) >= 2 and _REGION_SUFFIX_RE.search(parts[1]):
        region = f"{parts[0]} {parts[1]}"
        election_name = " ".join(parts[2:])
        return (region, election_name)

    # 4. fallback: 첫 토큰만 지역으로
    if len(parts) >= 2:
        return (parts[0], " ".join(parts[1:]))
    return ("", text)


def matches_target(record: ListRecord, target: PollTarget) -> bool:
    """ListRecord가 PollTarget의 기준을 충족하면 True를 반환한다.

    region: title_region이 target.region으로 시작하는지 확인
    election_names: 파싱된 선거명에 target.election_names 중 하나라도 포함되면 OK (OR 매칭)
    None 기준은 와일드카드 (무조건 통과).
    """
    if target.region is None and target.election_names is None:
        return True

    region, election_name = parse_title_region(record.title_region)

    if target.region is not None:
        if region != target.region:
            return False

    if target.election_names is not None:
        # title_region의 선거명은 콤마 또는 공백으로 구분될 수 있음
        clean = election_name.replace("(", "").replace(")", "")
        actual = {t for t in re.split(r"[,\s]+", clean) if t}
        if not actual.intersection(set(target.election_names)):
            return False

    return True


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


def _build_targets_from_args(args: "argparse.Namespace") -> List[PollTarget]:
    """CLI 인수에서 PollTarget 목록을 구성한다."""
    if args.use_preset_targets:
        return list(POLL_TARGETS)

    election_names: Optional[Tuple[str, ...]] = None
    if getattr(args, "target_election_names", None):
        election_names = tuple(n.strip() for n in args.target_election_names.split(",") if n.strip())

    keyword = getattr(args, "target_keyword", None) or ""
    region = getattr(args, "target_region", None) or ""
    if not keyword and region:
        keyword = region.split()[0]

    return [PollTarget(
        search_keyword=keyword,
        region=region or None,
        election_names=election_names,
        election_type=getattr(args, "target_election_type", None),
        slug=safe_filename(region or keyword, "target"),
    )]


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
    parser.add_argument("--crawl-results", action="store_true", help="결과분석 PDF 다운로드 및 파싱")
    parser.add_argument("--pdf-dir", default="./pdfs", help="결과 PDF 저장 디렉터리")
    parser.add_argument("--no-connectivity-check", action="store_true", help="초기 연결 검사를 건너뜀")
    parser.add_argument("--run-tests", action="store_true", help="내장 단위 테스트 실행")
    # 타겟 기반 수집 옵션
    parser.add_argument("--use-preset-targets", action="store_true", help="POLL_TARGETS 전체 수집")
    parser.add_argument("--target-region", metavar="REGION", help="수집할 지역 (예: '전라남도 전체')")
    parser.add_argument(
        "--target-election-names",
        metavar="NAMES",
        help="수집할 선거명, 콤마 구분 (예: '광역단체장선거,정당지지도')",
    )
    parser.add_argument("--target-election-type", metavar="TYPE", help="선거구분 (참고용)")
    parser.add_argument("--target-keyword", metavar="KEYWORD", help="NESDC searchWrd 검색어 (미지정 시 region 첫 단어)")
    parser.add_argument("--max-pages-per-target", type=int, default=50, help="타겟당 최대 수집 페이지 수")
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

        # ── 타겟 기반 수집 모드 ──────────────────────────────────────────────────
        use_targets = args.use_preset_targets or args.target_region or args.target_keyword
        if use_targets:
            targets = _build_targets_from_args(args)
            target_records = crawler.crawl_for_targets(
                targets,
                max_pages_per_target=args.max_pages_per_target,
                skip_errors=args.skip_errors,
            )
            crawler.save_target_results(target_records, args.output_dir)

            for slug, records in target_records.items():
                target_dir = Path(args.output_dir) / slug
                detail_target = records[: args.detail_limit] if args.detail_limit >= 0 else records
                detail_records = crawler.crawl_details(detail_target, skip_errors=args.skip_errors)
                crawler.save_details_json(detail_records, target_dir / "details.json")

                if args.crawl_results:
                    result_sets = crawler.crawl_results(
                        detail_records,
                        pdf_dir=target_dir / "pdfs",
                        skip_errors=args.skip_errors,
                    )
                    crawler.save_results_json(result_sets, target_dir / "results.json")
                    total_q = sum(len(rs.questions) for rs in result_sets)
                    print(f"[{slug}] 결과 파싱: {len(result_sets)}건, 질문 {total_q}개")

                total = sum(len(v) for v in target_records.values())
            print(f"타겟 수집 완료: 타겟 {len(target_records)}개, 총 목록 {total}건")
            return 0

        # ── 기존 전체 수집 모드 (하위 호환) ─────────────────────────────────────
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

        if args.crawl_results:
            result_sets = crawler.crawl_results(
                detail_records,
                pdf_dir=args.pdf_dir,
                skip_errors=args.skip_errors,
            )
            crawler.save_results_json(result_sets, Path(args.output_dir) / "nesdc_results.json")
            total_questions = sum(len(rs.questions) for rs in result_sets)
            print(f"결과 파싱: {len(result_sets)}건, 총 질문 {total_questions}개")

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
        # 엔드포인트: /portal/cmm/fms/FileDown.do, 파라미터: bbsKey
        self.assertIn("FileDown.do", url)
        self.assertIn("bbsKey=ghi%3D", url)
        self.assertIn("atchFileId=abc%3D", url)

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

    def test_parse_title_region_standard(self) -> None:
        """도+시/군 단위 포맷 파싱 (전체 없음)."""
        region, election = parse_title_region("경기도 안산시 기초단체장선거 정당지지도")
        self.assertEqual(region, "경기도 안산시")
        self.assertEqual(election, "기초단체장선거 정당지지도")

    def test_parse_title_region_with_jeonche(self) -> None:
        """광역 전체 단위 포맷 파싱 (전체 포함)."""
        region, election = parse_title_region("전라남도 전체 광역단체장선거,정당지지도")
        self.assertEqual(region, "전라남도 전체")
        self.assertEqual(election, "광역단체장선거,정당지지도")

    def test_parse_title_region_nationwide(self) -> None:
        """전국 단위 포맷 파싱."""
        region, election = parse_title_region("전국 대통령선거")
        self.assertEqual(region, "전국")
        self.assertEqual(election, "대통령선거")

    def test_parse_title_region_city(self) -> None:
        """도+군 단위 포맷 파싱."""
        region, election = parse_title_region("전라남도 해남군 기초단체장선거 정당지지도")
        self.assertEqual(region, "전라남도 해남군")
        self.assertEqual(election, "기초단체장선거 정당지지도")

    def test_matches_target_hit(self) -> None:
        """타겟 매칭 성공 케이스 (도+시 형식)."""
        record = ListRecord(
            registration_number="99",
            pollster="테스트기관",
            sponsor="테스트의뢰",
            method="전화",
            sample_frame="가상번호",
            title_region="경기도 안산시 기초단체장선거 정당지지도",
            registered_date="2026-01-01",
            province="경기도",
            detail_url="https://example.com",
        )
        target = PollTarget(
            search_keyword="경기도",
            region="경기도 안산시",
            election_names=("기초단체장선거",),
        )
        self.assertTrue(matches_target(record, target))

    def test_matches_target_miss_region(self) -> None:
        """지역이 다른 경우 매칭 실패."""
        record = ListRecord(
            registration_number="99",
            pollster="테스트기관",
            sponsor="테스트의뢰",
            method="전화",
            sample_frame="가상번호",
            title_region="경기도 수원시 기초단체장선거",
            registered_date="2026-01-01",
            province="경기도",
            detail_url="https://example.com",
        )
        target = PollTarget(
            search_keyword="경기도",
            region="경기도 안산시",
            election_names=("기초단체장선거",),
        )
        self.assertFalse(matches_target(record, target))

    def test_matches_target_wildcard(self) -> None:
        """region=None이면 지역 무관하게 매칭."""
        record = ListRecord(
            registration_number="1",
            pollster="기관",
            sponsor="의뢰",
            method="전화",
            sample_frame="가상번호",
            title_region="경기도 안산시 기초단체장선거",
            registered_date="2026-01-01",
            province="경기도",
            detail_url="https://example.com",
        )
        target = PollTarget(search_keyword="경기도", region=None, election_names=None)
        self.assertTrue(matches_target(record, target))

    def test_select_parser_metasearch(self) -> None:
        """메타서치 기관명 힌트 → _TableFormatParser 선택."""
        parser = PollResultParser()
        selected = parser._select_parser("임의 텍스트", "주)메타서치")
        self.assertIs(selected, _TableFormatParser)

    def test_table_parser_section_re_mun_prefix(self) -> None:
        """_TableFormatParser._SECTION_RE가 '문N)' 형식을 인식한다."""
        m = _TableFormatParser._SECTION_RE.search("문1) 지지정당 교차분석")
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), "1")
        self.assertEqual(m.group(2), "지지정당 교차분석")

    def test_table_parser_metasearch_style(self) -> None:
        """메타서치 스타일 크로스탭 테이블 → 옵션·퍼센트 정상 추출."""
        header = ["구분", None, "조사완료사례수", "더불어민주당", "국민의힘", "잘모름", "가중값적용사례수"]
        total  = ["전체", None, "(505)", "52.8", "28.5", "5.2", "(505)"]
        table  = [header, total]
        page_text = "문1) 지지정당 교차분석"
        pages_data = [(page_text, [table])]
        results = _TableFormatParser().parse(pages_data)
        self.assertEqual(len(results), 1)
        q = results[0]
        self.assertEqual(q.question_title, "지지정당 교차분석")
        self.assertIn("더불어민주당", q.response_options)
        self.assertAlmostEqual(q.overall_percentages[0], 52.8)

    def test_select_parser_gaajungsaesus_probe(self) -> None:
        """'가중값적용사례수' content_probe → _TableFormatParser 선택 (미등록 기관)."""
        parser = PollResultParser()
        selected = parser._select_parser("가중값적용사례수가 포함된 PDF 텍스트", None)
        self.assertIs(selected, _TableFormatParser)


if __name__ == "__main__":
    raise SystemExit(run())
