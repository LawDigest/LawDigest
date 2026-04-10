"""선거공약 및 정당정책 수집기.

ElecPrmsInfoInqireService (선거공약) 및
PartyPlcInfoInqireService (정당정책) API를 호출하여 데이터를 수집·저장한다.
"""

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.orm import Session

from lawdigest_data.elections.api_client import NecApiClient
from lawdigest_data.elections.models.candidates import Candidate, CandidateType
from lawdigest_data.elections.models.codes import PartyCode
from lawdigest_data.elections.models.pledges import ElectionPledge, PartyPolicy
from lawdigest_data.elections.utils.normalizer import normalize_election_name, normalize_region

logger = logging.getLogger(__name__)

# 공약 제공 대상 선거종류코드
PLEDGE_TYPECODES = {1, 3, 4, 11}  # 대통령, 시도지사, 구시군장, 교육감


def _upsert_batch(
    session: Session,
    model: type,
    rows: list[dict[str, Any]],
    unique_keys: list[str],
) -> int:
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


class PledgeCollector:
    """선거공약 수집기."""

    def __init__(self, client: NecApiClient) -> None:
        self.client = client

    def collect_pledges(self, session: Session, sg_id: str) -> int:
        """후보자별 선거공약을 수집한다."""
        # 공약 대상 후보자 조회 (confirmed만, 공약 지원 typecode만)
        candidates = session.execute(
            select(Candidate.id, Candidate.huboid, Candidate.sg_typecode,
                   Candidate.sd_name, Candidate.sgg_name)
            .where(
                Candidate.sg_id == sg_id,
                Candidate.candidate_type == CandidateType.CONFIRMED.value,
                Candidate.sg_typecode.in_(PLEDGE_TYPECODES),
            )
        ).all()

        logger.info("공약 수집 대상 후보자: %d명 (sgId=%s)", len(candidates), sg_id)

        total = 0
        batch: list[dict[str, Any]] = []

        for i, (cand_id, huboid, sg_typecode, sd_name, sgg_name) in enumerate(candidates):
            try:
                items = self.client.fetch(
                    "pledge", "getCnddtElecPrmsInfoInqire",
                    {"sgId": sg_id, "sgTypecode": str(sg_typecode), "cnddtId": huboid},
                )
            except Exception as e:
                logger.warning("공약 수집 실패 (huboid=%s): %s", huboid, e)
                continue

            for item in items:
                # 공약 필드는 prmsRealmName1~10, prmsTitle1~10, prmsContent1~10
                prms_cnt = int(item.get("prmsCnt", "0") or "0")
                for ord_num in range(1, min(prms_cnt, 10) + 1):
                    title = (item.get(f"prmsTitle{ord_num}") or "").strip()
                    content = (item.get(f"prmsContent{ord_num}") or "").strip()
                    if not title and not content:
                        continue
                    batch.append({
                        "candidate_id": cand_id,
                        "sg_id": sg_id,
                        "sg_typecode": sg_typecode,
                        "cnddt_id": huboid,
                        "prms_ord": ord_num,
                        "prms_title": title or None,
                        "prms_content": content or None,
                        "normalized_region": normalize_region(sd_name or ""),
                        "normalized_election_name": normalize_election_name(sg_typecode),
                    })

            # 배치 단위로 upsert (500건마다)
            if len(batch) >= 500:
                count = _upsert_batch(session, ElectionPledge, batch, ["sg_id", "cnddt_id", "prms_ord"])
                session.flush()
                total += count
                batch.clear()

            if (i + 1) % 100 == 0:
                logger.info("  공약 수집 진행: %d/%d명", i + 1, len(candidates))

        # 잔여 배치
        if batch:
            count = _upsert_batch(session, ElectionPledge, batch, ["sg_id", "cnddt_id", "prms_ord"])
            session.flush()
            total += count

        logger.info("선거공약 총 %d건 수집 완료", total)
        return total


class PartyPolicyCollector:
    """정당정책 수집기."""

    def __init__(self, client: NecApiClient) -> None:
        self.client = client

    def collect_policies(self, session: Session, sg_id: str) -> int:
        """정당별 정책을 수집한다."""
        # DB에서 정당 목록 조회
        parties = session.execute(
            select(PartyCode.jd_name)
            .where(PartyCode.sg_id == sg_id)
        ).all()

        logger.info("정당정책 수집 대상: %d개 정당 (sgId=%s)", len(parties), sg_id)

        total = 0
        batch: list[dict[str, Any]] = []

        for (party_name,) in parties:
            try:
                items = self.client.fetch(
                    "party_policy", "getPartyPlcInfoInqire",
                    {"sgId": sg_id, "partyName": party_name},
                )
            except Exception as e:
                logger.warning("정당정책 수집 실패 (%s): %s", party_name, e)
                continue

            for item in items:
                prms_cnt = int(item.get("prmsCnt", "0") or "0")
                for ord_num in range(1, min(prms_cnt, 10) + 1):
                    title = (item.get(f"prmsTitle{ord_num}") or "").strip()
                    content = (item.get(f"prmsContent{ord_num}") or "").strip()
                    if not title and not content:
                        continue
                    batch.append({
                        "sg_id": sg_id,
                        "party_name": party_name,
                        "prms_cnt": prms_cnt,
                        "prms_ord": ord_num,
                        "prms_title": title or None,
                        "prms_content": content or None,
                    })

        if batch:
            total = _upsert_batch(session, PartyPolicy, batch, ["sg_id", "party_name", "prms_ord"])
            session.flush()

        logger.info("정당정책 총 %d건 수집 완료", total)
        return total
