"""선거 데이터 수집 워크플로우 매니저.

Airflow DAG에서 호출하는 단계별 수집 로직을 캡슐화한다.
각 step은 XCom으로 전달 가능한 딕셔너리를 반환한다.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from time import monotonic
from typing import Any

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# 아티팩트 저장 디렉토리
_ARTIFACT_DIR = os.environ.get(
    "ELECTION_ARTIFACT_DIR",
    "/opt/airflow/project/services/data/output/elections/artifacts",
)


def _write_artifact(name: str, data: dict[str, Any]) -> str:
    """아티팩트를 JSON 파일로 저장하고 경로를 반환한다."""
    Path(_ARTIFACT_DIR).mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"{_ARTIFACT_DIR}/{name}_{ts}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    return path


class ElectionWorkflowManager:
    """선거 데이터 수집 워크플로우 매니저.

    execution_mode:
        - dry_run: DB 미반영, 수집 결과 artifact JSON만 생성
        - test: 테스트 DB에 반영
        - prod: 운영 DB에 반영
    """

    VALID_MODES = ("dry_run", "test", "prod")

    def __init__(self, execution_mode: str = "dry_run") -> None:
        if execution_mode not in self.VALID_MODES:
            raise ValueError(f"Invalid execution_mode: {execution_mode}. Must be one of {self.VALID_MODES}")
        self.execution_mode = execution_mode
        load_dotenv()

    def _should_write_db(self) -> bool:
        return self.execution_mode in ("test", "prod")

    def collect_codes_step(self, sg_id: str) -> dict[str, Any]:
        """코드정보 6종을 수집한다."""
        t0 = monotonic()
        from lawdigest_data.elections.api_client import NecApiClient
        from lawdigest_data.elections.collectors.code_collector import CodeCollector

        client = NecApiClient()
        collector = CodeCollector(client)

        if self._should_write_db():
            from lawdigest_data.elections.database import get_session, init_db
            init_db()
            with get_session() as session:
                results = collector.collect_all(session, sg_id=sg_id)
        else:
            # dry_run: API만 호출하고 DB 미반영
            items = client.fetch("code", "getCommonSgCodeList")
            results = {"선거코드": len(items), "dry_run": True}
            logger.info("[dry_run] 선거코드 %d건 조회 (DB 미반영)", len(items))

        elapsed = round(monotonic() - t0, 3)
        result = {
            "mode": self.execution_mode,
            "sg_id": sg_id,
            "results": results,
            "elapsed_seconds": elapsed,
        }
        result["artifact_path"] = _write_artifact("election_codes", result)
        logger.info("[collect_codes] %s", result)
        return result

    def collect_candidates_step(self, sg_id: str) -> dict[str, Any]:
        """예비후보자 + 확정후보자를 수집한다."""
        t0 = monotonic()
        from lawdigest_data.elections.api_client import NecApiClient
        from lawdigest_data.elections.collectors.candidate_collector import CandidateCollector
        from lawdigest_data.elections.models.candidates import CandidateType

        client = NecApiClient()
        collector = CandidateCollector(client)
        results: dict[str, Any] = {}

        if self._should_write_db():
            from lawdigest_data.elections.database import get_session, init_db
            init_db()
            with get_session() as session:
                results["예비후보자"] = collector.collect_candidates(
                    session, sg_id, CandidateType.PRELIMINARY,
                )
                results["확정후보자"] = collector.collect_candidates(
                    session, sg_id, CandidateType.CONFIRMED,
                )
        else:
            # dry_run: 시도지사 예비후보만 샘플 조회
            from lawdigest_data.elections.api_client import NecApiError
            try:
                items = client.fetch(
                    "candidate", "getPoelpcddRegistSttusInfoInqire",
                    {"sgId": sg_id, "sgTypecode": "3"},
                )
                results = {"시도지사_예비후보_샘플": len(items), "dry_run": True}
                logger.info("[dry_run] 시도지사 예비후보 %d건 조회 (DB 미반영)", len(items))
            except NecApiError:
                results = {"예비후보자": 0, "dry_run": True, "note": "데이터 없음"}
                logger.info("[dry_run] 예비후보자 데이터 없음")

        elapsed = round(monotonic() - t0, 3)
        result = {
            "mode": self.execution_mode,
            "sg_id": sg_id,
            "results": results,
            "elapsed_seconds": elapsed,
        }
        result["artifact_path"] = _write_artifact("election_candidates", result)
        logger.info("[collect_candidates] %s", result)
        return result

    def collect_winners_step(self, sg_id: str) -> dict[str, Any]:
        """당선인을 수집한다."""
        t0 = monotonic()
        from lawdigest_data.elections.api_client import NecApiClient
        from lawdigest_data.elections.collectors.candidate_collector import WinnerCollector

        client = NecApiClient()
        winner_collector = WinnerCollector(client)
        results: dict[str, Any] = {}

        if self._should_write_db():
            from lawdigest_data.elections.database import get_session, init_db
            init_db()
            with get_session() as session:
                results["당선인"] = winner_collector.collect_winners(session, sg_id)
        else:
            from lawdigest_data.elections.api_client import NecApiError
            try:
                items = client.fetch(
                    "winner", "getWinnerInfoInqire",
                    {"sgId": sg_id, "sgTypecode": "3"},
                )
                results = {"시도지사_당선인_샘플": len(items), "dry_run": True}
                logger.info("[dry_run] 시도지사 당선인 %d건 조회 (DB 미반영)", len(items))
            except NecApiError:
                results = {"당선인": 0, "dry_run": True, "note": "데이터 없음 (선거 전)"}
                logger.info("[dry_run] 당선인 데이터 없음 (선거 전)")

        elapsed = round(monotonic() - t0, 3)
        result = {
            "mode": self.execution_mode,
            "sg_id": sg_id,
            "results": results,
            "elapsed_seconds": elapsed,
        }
        result["artifact_path"] = _write_artifact("election_winners", result)
        logger.info("[collect_winners] %s", result)
        return result

    def collect_pledges_step(self, sg_id: str) -> dict[str, Any]:
        """선거공약 + 정당정책을 수집한다."""
        t0 = monotonic()
        from lawdigest_data.elections.api_client import NecApiClient
        from lawdigest_data.elections.collectors.pledge_collector import (
            PartyPolicyCollector,
            PledgeCollector,
        )

        client = NecApiClient()
        results: dict[str, Any] = {}

        if self._should_write_db():
            from lawdigest_data.elections.database import get_session, init_db
            init_db()
            with get_session() as session:
                results["선거공약"] = PledgeCollector(client).collect_pledges(session, sg_id)
                results["정당정책"] = PartyPolicyCollector(client).collect_policies(session, sg_id)
        else:
            results = {"dry_run": True, "선거공약": 0, "정당정책": 0}
            logger.info("[dry_run] 공약/정책 수집 스킵 (DB 미반영)")

        elapsed = round(monotonic() - t0, 3)
        result = {
            "mode": self.execution_mode,
            "sg_id": sg_id,
            "results": results,
            "elapsed_seconds": elapsed,
        }
        result["artifact_path"] = _write_artifact("election_pledges", result)
        logger.info("[collect_pledges] %s", result)
        return result
