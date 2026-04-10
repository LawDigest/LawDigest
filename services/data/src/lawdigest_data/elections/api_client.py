"""중앙선거관리위원회 OpenAPI 범용 클라이언트.

기존 bills DataFetcher의 매퍼 패턴을 참고하되,
선거 API 전용으로 단순화한 독립 클라이언트를 제공한다.
"""

import logging
import os
import time
from typing import Any
from xml.etree import ElementTree

import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

load_dotenv()

logger = logging.getLogger(__name__)

# 공공데이터포털 응답 코드
_SUCCESS_CODES = {"INFO-00", "00"}

BASE_URL = "http://apis.data.go.kr/9760000"

# 서비스별 엔드포인트 매핑
SERVICES = {
    "code": "CommonCodeService",
    "candidate": "PofelcddInfoInqireService",
    "winner": "WinnerInfoInqireService2",
    "pledge": "ElecPrmsInfoInqireService",
    "party_policy": "PartyPlcInfoInqireService",
}


class NecApiError(Exception):
    """선거관리위원회 API 호출 실패."""

    def __init__(self, result_code: str, result_msg: str, url: str = ""):
        self.result_code = result_code
        self.result_msg = result_msg
        self.url = url
        super().__init__(f"[{result_code}] {result_msg} ({url})")


class NecApiClient:
    """중앙선거관리위원회 OpenAPI 범용 클라이언트.

    특징:
    - serviceKey 자동 주입
    - XML/JSON 응답 파싱
    - 페이지네이션 자동 처리
    - HTTPAdapter + Retry (3회, 지수 백오프)
    - rate limiting (요청 간 간격 조절)
    """

    def __init__(
        self,
        api_key: str | None = None,
        result_type: str = "xml",
        page_size: int = 100,
        request_interval: float = 0.05,
    ) -> None:
        self.api_key = api_key or os.environ.get("APIKEY_NEC") or os.environ.get("APIKEY_DATAGOKR", "")
        self.result_type = result_type
        self.page_size = page_size
        self.request_interval = request_interval

        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _build_url(self, service: str, operation: str) -> str:
        """서비스명과 오퍼레이션명으로 전체 URL을 구성한다."""
        service_path = SERVICES.get(service, service)
        return f"{BASE_URL}/{service_path}/{operation}"

    def _parse_xml(self, content: bytes) -> tuple[list[dict[str, str]], int]:
        """XML 응답을 파싱하여 (items, totalCount)를 반환한다."""
        root = ElementTree.fromstring(content)

        # 결과코드 확인
        result_code_elem = root.find(".//resultCode")
        result_code = result_code_elem.text if result_code_elem is not None else ""

        if result_code and result_code not in _SUCCESS_CODES:
            result_msg_elem = root.find(".//resultMsg")
            result_msg = result_msg_elem.text if result_msg_elem is not None else "Unknown error"
            raise NecApiError(result_code, result_msg)

        # 데이터 추출
        items = []
        for item in root.findall(".//item"):
            row = {child.tag: (child.text or "").strip() for child in item}
            items.append(row)

        # totalCount
        total_elem = root.find(".//totalCount")
        total_count = int(total_elem.text) if total_elem is not None else len(items)

        return items, total_count

    def _parse_json(self, content: bytes) -> tuple[list[dict[str, Any]], int]:
        """JSON 응답을 파싱하여 (items, totalCount)를 반환한다."""
        import json

        data = json.loads(content)

        # 결과코드 확인
        header = data.get("response", data).get("header", {})
        result_code = header.get("resultCode", "")

        if result_code and result_code not in _SUCCESS_CODES:
            raise NecApiError(result_code, header.get("resultMsg", "Unknown"))

        body = data.get("response", data).get("body", {})
        items_wrapper = body.get("items", {})
        items = items_wrapper.get("item", []) if isinstance(items_wrapper, dict) else []
        if isinstance(items, dict):
            items = [items]

        total_count = int(body.get("totalCount", len(items)))
        return items, total_count

    def fetch(
        self,
        service: str,
        operation: str,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """단일 API 오퍼레이션을 호출하고 전체 페이지 데이터를 반환한다.

        Args:
            service: 서비스 키 (예: "code", "candidate") 또는 직접 서비스명
            operation: 오퍼레이션명 (예: "getCommonSgCodeList")
            params: 추가 요청 파라미터

        Returns:
            전체 페이지의 item 딕셔너리 리스트
        """
        url = self._build_url(service, operation)
        request_params: dict[str, Any] = {
            "serviceKey": self.api_key,
            "pageNo": 1,
            "numOfRows": self.page_size,
        }
        if self.result_type == "json":
            request_params["resultType"] = "json"

        if params:
            request_params.update(params)

        all_items: list[dict[str, Any]] = []
        total_count = 0
        page = 1

        while True:
            request_params["pageNo"] = page

            try:
                response = self.session.get(url, params=request_params, timeout=30)
                response.raise_for_status()
            except requests.RequestException as e:
                logger.error("API 요청 실패 (page=%d): %s", page, e)
                raise

            if self.result_type == "json":
                items, total_count = self._parse_json(response.content)
            else:
                items, total_count = self._parse_xml(response.content)

            if not items:
                break

            all_items.extend(items)
            logger.debug(
                "%s/%s page=%d, fetched=%d, total=%d",
                service, operation, page, len(all_items), total_count,
            )

            if len(all_items) >= total_count:
                break

            page += 1
            if self.request_interval > 0:
                time.sleep(self.request_interval)

        logger.info(
            "%s/%s 수집 완료: %d건", service, operation, len(all_items),
        )
        return all_items
