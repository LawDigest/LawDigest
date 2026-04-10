"""코드정보 수집기.

CommonCodeService API의 6개 오퍼레이션을 호출하여
선거코드, 선거구, 구시군, 정당, 직업, 학력 코드를 수집·저장한다.
"""

import logging
from typing import Any

from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.orm import Session

from lawdigest_data.elections.api_client import NecApiClient
from lawdigest_data.elections.models.codes import (
    DistrictCode,
    EduCode,
    ElectionCode,
    GusigunCode,
    JobCode,
    PartyCode,
    SgTypecode,
)

logger = logging.getLogger(__name__)

# 오퍼레이션 → (ORM 모델, API→모델 필드 매핑, UNIQUE 키 컬럼)
_OPERATIONS: dict[str, dict[str, Any]] = {
    "getCommonSgCodeList": {
        "model": ElectionCode,
        "field_map": {
            "sgId": "sg_id",
            "sgTypecode": "sg_typecode",
            "sgName": "sg_name",
            "sgVotedate": "sg_vote_date",
        },
        "unique_keys": ["sg_id", "sg_typecode"],
        "extra_params": {},
        "description": "선거코드",
    },
    "getCommonSggCodeList": {
        "model": DistrictCode,
        "field_map": {
            "sgId": "sg_id",
            "sgTypecode": "sg_typecode",
            "sggName": "sgg_name",
            "sdName": "sd_name",
            "wiwName": "wiw_name",
            "sggJungsu": "sgg_jungsu",
            "sOrder": "s_order",
        },
        "unique_keys": ["sg_id", "sg_typecode", "sgg_name", "sd_name"],
        "extra_params": {"sgTypecode": None},  # sgTypecode별 반복 호출 필요
        "description": "선거구코드",
    },
    "getCommonGusigunCodeList": {
        "model": GusigunCode,
        "field_map": {
            "sgId": "sg_id",
            "sdName": "sd_name",
            "wiwName": "wiw_name",
            "wOrder": "w_order",
        },
        "unique_keys": ["sg_id", "sd_name", "wiw_name"],
        "extra_params": {},
        "description": "구시군코드",
    },
    "getCommonPartyCodeList": {
        "model": PartyCode,
        "field_map": {
            "sgId": "sg_id",
            "jdName": "jd_name",
            "pOrder": "p_order",
        },
        "unique_keys": ["sg_id", "jd_name"],
        "extra_params": {},
        "description": "정당코드",
    },
    "getCommonJobCodeList": {
        "model": JobCode,
        "field_map": {
            "sgId": "sg_id",
            "jobId": "job_id",
            "jobName": "job_name",
            "jOrder": "j_order",
        },
        "unique_keys": ["sg_id", "job_id"],
        "extra_params": {},
        "description": "직업코드",
    },
    "getCommonEduBckgrdCodeList": {
        "model": EduCode,
        "field_map": {
            "sgId": "sg_id",
            "eduId": "edu_id",
            "eduName": "edu_name",
            "eOrder": "e_order",
        },
        "unique_keys": ["sg_id", "edu_id"],
        "extra_params": {},
        "description": "학력코드",
    },
}

# 지방선거에 해당하는 선거종류코드 (선거구코드 조회 시 반복 대상)
LOCAL_ELECTION_TYPECODES = [
    SgTypecode.시도지사,        # 3
    SgTypecode.구시군장,        # 4
    SgTypecode.시도의원,        # 5
    SgTypecode.구시군의회의원,  # 6
    SgTypecode.광역의원비례대표, # 8
    SgTypecode.기초의원비례대표, # 9
    SgTypecode.교육감,          # 11
]


def _map_row(row: dict[str, str], field_map: dict[str, str]) -> dict[str, Any]:
    """API 응답 row를 ORM 필드명으로 매핑한다."""
    mapped = {}
    for api_key, model_key in field_map.items():
        value = row.get(api_key, "")
        # 정수 필드 변환
        if model_key in ("sg_typecode", "sgg_jungsu", "s_order", "w_order", "p_order", "j_order", "e_order"):
            mapped[model_key] = int(value) if value else None
        else:
            # UNIQUE 제약의 일부인 필드는 NULL 대신 빈 문자열 유지
            if not value and model_key in ("sd_name", "wiw_name", "sgg_name", "sg_id", "jd_name"):
                mapped[model_key] = ""
            else:
                mapped[model_key] = value if value else None
    return mapped


def _upsert_batch(
    session: Session,
    model: type,
    rows: list[dict[str, Any]],
    unique_keys: list[str],
) -> int:
    """MySQL INSERT ... ON DUPLICATE KEY UPDATE로 일괄 upsert."""
    if not rows:
        return 0

    stmt = mysql_insert(model).values(rows)

    # unique key 외의 필드를 업데이트 대상으로 설정
    update_cols = {
        col: stmt.inserted[col]
        for col in rows[0].keys()
        if col not in unique_keys
    }
    if update_cols:
        stmt = stmt.on_duplicate_key_update(**update_cols)

    session.execute(stmt)
    return len(rows)


class CodeCollector:
    """코드정보 수집기.

    사용법::

        client = NecApiClient()
        collector = CodeCollector(client)
        with get_session() as session:
            collector.collect_all(session, sg_id="20220601")
    """

    def __init__(self, client: NecApiClient) -> None:
        self.client = client

    def collect_election_codes(self, session: Session) -> list[dict[str, Any]]:
        """선거코드를 수집하고 DB에 저장한다. 수집된 전체 코드 목록을 반환."""
        op_config = _OPERATIONS["getCommonSgCodeList"]
        items = self.client.fetch("code", "getCommonSgCodeList")
        rows = [_map_row(item, op_config["field_map"]) for item in items]
        count = _upsert_batch(session, op_config["model"], rows, op_config["unique_keys"])
        logger.info("선거코드 %d건 upsert 완료", count)
        return rows

    def collect_single(
        self,
        session: Session,
        operation: str,
        sg_id: str,
        extra_params: dict[str, Any] | None = None,
    ) -> int:
        """단일 오퍼레이션의 데이터를 수집·저장한다."""
        op_config = _OPERATIONS[operation]
        params: dict[str, Any] = {"sgId": sg_id}
        if extra_params:
            params.update(extra_params)

        items = self.client.fetch("code", operation, params)
        rows = [_map_row(item, op_config["field_map"]) for item in items]
        return _upsert_batch(session, op_config["model"], rows, op_config["unique_keys"])

    def collect_district_codes(self, session: Session, sg_id: str) -> int:
        """선거구코드를 선거종류코드별로 반복 수집한다."""
        total = 0
        for typecode in LOCAL_ELECTION_TYPECODES:
            count = self.collect_single(
                session,
                "getCommonSggCodeList",
                sg_id,
                extra_params={"sgTypecode": str(typecode.value)},
            )
            logger.info("선거구코드 (sgTypecode=%d %s) %d건", typecode.value, typecode.name, count)
            total += count
        return total

    def collect_all(self, session: Session, sg_id: str) -> dict[str, int]:
        """지정 선거의 모든 코드정보를 수집한다.

        Args:
            session: SQLAlchemy 세션
            sg_id: 대상 선거ID (예: "20220601")

        Returns:
            오퍼레이션별 수집 건수 딕셔너리
        """
        results: dict[str, int] = {}

        # 1) 선거코드 (전체 선거 목록)
        all_codes = self.collect_election_codes(session)
        results["선거코드"] = len(all_codes)

        # 대상 선거가 존재하는지 확인
        target_exists = any(r["sg_id"] == sg_id for r in all_codes)
        if not target_exists:
            logger.warning("sgId=%s에 해당하는 선거를 찾을 수 없습니다. 유사 ID를 확인하세요.", sg_id)
            # 전체 목록에서 비슷한 ID 출력
            for r in all_codes:
                if sg_id[:4] in (r.get("sg_id") or ""):
                    logger.info("  → sgId=%s, sgName=%s", r["sg_id"], r["sg_name"])

        session.flush()

        # 2) 선거구코드 (sgTypecode별 반복)
        results["선거구코드"] = self.collect_district_codes(session, sg_id)
        session.flush()

        # 3) 나머지 코드 (병렬 가능하나 순차 실행)
        for op_name in ("getCommonGusigunCodeList", "getCommonPartyCodeList",
                        "getCommonJobCodeList", "getCommonEduBckgrdCodeList"):
            op_config = _OPERATIONS[op_name]
            count = self.collect_single(session, op_name, sg_id)
            results[op_config["description"]] = count
            logger.info("%s %d건 수집 완료", op_config["description"], count)
            session.flush()

        return results
