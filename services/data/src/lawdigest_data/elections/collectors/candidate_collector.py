"""후보자 및 당선인 수집기.

PofelcddInfoInqireService (예비후보자/후보자) 및
WinnerInfoInqireService2 (당선인) API를 호출하여 데이터를 수집·저장한다.
"""

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.orm import Session

from lawdigest_data.elections.api_client import NecApiClient
from lawdigest_data.elections.models.candidates import Candidate, CandidateType, Winner
from lawdigest_data.elections.models.codes import ElectionCode, SgTypecode
from lawdigest_data.elections.utils.normalizer import normalize_election_name, normalize_region

logger = logging.getLogger(__name__)

# 공통 필드 매핑 (API 응답 키 → ORM 필드명)
_CANDIDATE_FIELD_MAP: dict[str, str] = {
    "huboid": "huboid",
    "sgId": "sg_id",
    "sgTypecode": "sg_typecode",
    "sggName": "sgg_name",
    "sdName": "sd_name",
    "wiwName": "wiw_name",
    "giho": "giho",
    "gihoSangse": "giho_sangse",
    "jdName": "jd_name",
    "name": "name",
    "hanjaName": "hanja_name",
    "gender": "gender",
    "birthday": "birthday",
    "age": "age",
    "addr": "addr",
    "jobId": "job_id",
    "job": "job",
    "eduId": "edu_id",
    "edu": "edu",
    "career1": "career1",
    "career2": "career2",
    "regdate": "regdate",
    "status": "status",
}

_WINNER_FIELD_MAP: dict[str, str] = {
    "huboid": "huboid",
    "sgId": "sg_id",
    "sgTypecode": "sg_typecode",
    "sggName": "sgg_name",
    "sdName": "sd_name",
    "wiwName": "wiw_name",
    "giho": "giho",
    "gihoSangse": "giho_sangse",
    "jdName": "jd_name",
    "name": "name",
    "hanjaName": "hanja_name",
    "gender": "gender",
    "birthday": "birthday",
    "age": "age",
    "addr": "addr",
    "jobId": "job_id",
    "job": "job",
    "eduId": "edu_id",
    "edu": "edu",
    "career1": "career1",
    "career2": "career2",
    "dugsu": "dugsu",
    "dugyul": "dugyul",
}

# 정수 변환 대상 필드
_INT_FIELDS = {"sg_typecode", "age", "dugsu"}


def _map_row(row: dict[str, str], field_map: dict[str, str]) -> dict[str, Any]:
    """API 응답 row를 ORM 필드명으로 매핑한다."""
    mapped: dict[str, Any] = {}
    for api_key, model_key in field_map.items():
        value = row.get(api_key, "")
        if model_key in _INT_FIELDS:
            mapped[model_key] = int(value) if value else None
        else:
            mapped[model_key] = value.strip() if value and value.strip() else None
    return mapped


def _enrich_with_normalized(row: dict[str, Any]) -> dict[str, Any]:
    """정규화 필드를 추가한다."""
    sd_name = row.get("sd_name") or ""
    sg_typecode = row.get("sg_typecode")
    row["normalized_region"] = normalize_region(sd_name) if sd_name else None
    row["normalized_election_name"] = normalize_election_name(sg_typecode) if sg_typecode else None
    return row


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
    update_cols = {
        col: stmt.inserted[col]
        for col in rows[0].keys()
        if col not in unique_keys
    }
    if update_cols:
        stmt = stmt.on_duplicate_key_update(**update_cols)

    session.execute(stmt)
    return len(rows)


def _get_distinct_typecodes(session: Session, sg_id: str) -> list[int]:
    """DB에서 해당 선거의 선거종류코드 목록을 가져온다."""
    result = session.execute(
        select(ElectionCode.sg_typecode)
        .where(ElectionCode.sg_id == sg_id)
        .distinct()
    )
    # 대표선거명(0)은 제외
    return [row[0] for row in result.all() if row[0] != 0]



class CandidateCollector:
    """후보자 정보 수집기."""

    def __init__(self, client: NecApiClient) -> None:
        self.client = client

    def collect_candidates(
        self,
        session: Session,
        sg_id: str,
        candidate_type: CandidateType = CandidateType.CONFIRMED,
    ) -> int:
        """후보자 정보를 수집한다.

        Args:
            session: SQLAlchemy 세션
            sg_id: 선거ID
            candidate_type: 예비/확정 구분

        Returns:
            수집 건수
        """
        if candidate_type == CandidateType.PRELIMINARY:
            operation = "getPoelpcddRegistSttusInfoInqire"
        else:
            operation = "getPofelcddRegistSttusInfoInqire"

        typecodes = _get_distinct_typecodes(session, sg_id)
        logger.info(
            "%s 후보자 수집 시작 (sgId=%s, %d개 선거종류)",
            candidate_type.value, sg_id, len(typecodes),
        )

        total = 0
        for tc in typecodes:
            tc_name = SgTypecode(tc).name if tc in SgTypecode._value2member_map_ else str(tc)
            logger.info("  sgTypecode=%d (%s) 전체 조회 중...", tc, tc_name)

            try:
                # sdName/sggName 생략 → 해당 선거종류의 전체 후보자를 한번에 조회
                items = self.client.fetch(
                    "candidate", operation,
                    {"sgId": sg_id, "sgTypecode": str(tc)},
                )
            except Exception as e:
                logger.warning("  수집 실패 (sgTypecode=%d): %s", tc, e)
                continue

            batch: list[dict[str, Any]] = []
            for item in items:
                row = _map_row(item, _CANDIDATE_FIELD_MAP)
                row["candidate_type"] = candidate_type.value
                _enrich_with_normalized(row)
                batch.append(row)

            if batch:
                count = _upsert_batch(session, Candidate, batch, ["huboid", "sg_id", "candidate_type"])
                session.flush()
                logger.info("  sgTypecode=%d (%s): %d건 upsert", tc, tc_name, count)
                total += count

        logger.info("%s 후보자 총 %d건 수집 완료", candidate_type.value, total)
        return total


class WinnerCollector:
    """당선인 정보 수집기."""

    def __init__(self, client: NecApiClient) -> None:
        self.client = client

    def collect_winners(self, session: Session, sg_id: str) -> int:
        """당선인 정보를 수집한다."""
        typecodes = _get_distinct_typecodes(session, sg_id)
        logger.info("당선인 수집 시작 (sgId=%s, %d개 선거종류)", sg_id, len(typecodes))

        total = 0
        for tc in typecodes:
            tc_name = SgTypecode(tc).name if tc in SgTypecode._value2member_map_ else str(tc)
            logger.info("  sgTypecode=%d (%s) 전체 조회 중...", tc, tc_name)

            try:
                # sdName/sggName 생략 → 해당 선거종류의 전체 당선인을 한번에 조회
                items = self.client.fetch(
                    "winner", "getWinnerInfoInqire",
                    {"sgId": sg_id, "sgTypecode": str(tc)},
                )
            except Exception as e:
                logger.warning("  수집 실패 (sgTypecode=%d): %s", tc, e)
                continue

            batch: list[dict[str, Any]] = []
            for item in items:
                row = _map_row(item, _WINNER_FIELD_MAP)
                _enrich_with_normalized(row)
                batch.append(row)

            if batch:
                count = _upsert_batch(session, Winner, batch, ["huboid", "sg_id"])
                session.flush()
                logger.info("  sgTypecode=%d (%s): %d건 upsert", tc, tc_name, count)
                total += count

        # 후보자 테이블과 FK 연결
        self._link_candidates(session, sg_id)

        logger.info("당선인 총 %d건 수집 완료", total)
        return total

    def _link_candidates(self, session: Session, sg_id: str) -> int:
        """당선인의 candidate_id를 후보자 테이블과 매칭하여 설정한다."""
        from sqlalchemy import update

        # Winner.huboid + sg_id로 Candidate 테이블에서 confirmed 후보 찾기
        subq = (
            select(Candidate.id)
            .where(
                Candidate.huboid == Winner.huboid,
                Candidate.sg_id == Winner.sg_id,
                Candidate.candidate_type == CandidateType.CONFIRMED.value,
            )
            .correlate(Winner)
            .scalar_subquery()
        )

        stmt = (
            update(Winner)
            .where(Winner.sg_id == sg_id, Winner.candidate_id.is_(None))
            .values(candidate_id=subq)
        )
        result = session.execute(stmt)
        linked = result.rowcount
        session.flush()
        logger.info("당선인-후보자 FK 연결: %d건", linked)
        return linked
