"""지역명/선거명 정규화 유틸.

선거관리위원회 API 응답의 sdName/sggName/sgTypecode를
기존 여론조사(polls) 테이블의 region/election_name과 조인 가능한 형태로 변환한다.

polls 테이블 region 예시: "서울특별시 전체", "경기도 전체"
polls 테이블 election_name 예시: "광역단체장선거"
"""

import logging

logger = logging.getLogger(__name__)

# sgTypecode → election_name 매핑
_TYPECODE_TO_ELECTION_NAME: dict[int, str] = {
    1: "대통령선거",
    2: "국회의원선거",
    3: "광역단체장선거",
    4: "기초단체장선거",
    5: "광역의원선거",
    6: "기초의원선거",
    7: "국회의원비례대표선거",
    8: "광역의원비례대표선거",
    9: "기초의원비례대표선거",
    10: "교육의원선거",
    11: "교육감선거",
}

# sdName → polls region 매핑 (시도 단위)
# polls 테이블에서 "서울특별시 전체" 형태로 저장됨
_SD_NAME_TO_REGION: dict[str, str] = {
    "서울특별시": "서울특별시 전체",
    "부산광역시": "부산광역시 전체",
    "대구광역시": "대구광역시 전체",
    "인천광역시": "인천광역시 전체",
    "광주광역시": "광주광역시 전체",
    "대전광역시": "대전광역시 전체",
    "울산광역시": "울산광역시 전체",
    "세종특별자치시": "세종특별자치시 전체",
    "경기도": "경기도 전체",
    "강원도": "강원도 전체",
    "강원특별자치도": "강원도 전체",
    "충청북도": "충청북도 전체",
    "충청남도": "충청남도 전체",
    "전라북도": "전라북도 전체",
    "전북특별자치도": "전라북도 전체",
    "전라남도": "전라남도 전체",
    "경상북도": "경상북도 전체",
    "경상남도": "경상남도 전체",
    "제주특별자치도": "제주특별자치도 전체",
    "전국": "전국",
}


def normalize_region(sd_name: str, wiw_name: str | None = None) -> str:
    """시도명(+ 구시군명)을 polls region 형태로 정규화한다.

    Args:
        sd_name: API 응답의 sdName (예: "서울특별시")
        wiw_name: API 응답의 wiwName (예: "종로구"), 시도 단위면 None

    Returns:
        정규화된 region (예: "서울특별시 전체")
    """
    region = _SD_NAME_TO_REGION.get(sd_name)
    if region is None:
        logger.warning("정규화 실패 (sd_name=%s), 원본 사용", sd_name)
        region = f"{sd_name} 전체" if sd_name else ""
    return region


def normalize_election_name(sg_typecode: int) -> str:
    """선거종류코드를 polls election_name 형태로 정규화한다.

    Args:
        sg_typecode: 선거종류코드 (예: 3)

    Returns:
        정규화된 election_name (예: "광역단체장선거")
    """
    name = _TYPECODE_TO_ELECTION_NAME.get(sg_typecode)
    if name is None:
        logger.warning("정규화 실패 (sg_typecode=%d), 빈 문자열 반환", sg_typecode)
        return ""
    return name
