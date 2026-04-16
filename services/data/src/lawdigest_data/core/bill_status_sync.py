from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List
from uuid import uuid4

from ..status import BillLifecycleProjector, BillVoteProjector, LifecycleStatusFetcher, VoteStatusFetcher


class BillStatusSyncService:
    def __init__(
        self,
        *,
        mode: str,
        build_db_manager: Callable[[str], Any],
        artifact_dir: Path,
    ):
        self.mode = mode
        self.build_db_manager = build_db_manager
        self.artifact_dir = artifact_dir
        self.lifecycle_fetcher = LifecycleStatusFetcher()
        self.vote_fetcher = VoteStatusFetcher()
        self.lifecycle_projector = BillLifecycleProjector()
        self.vote_projector = BillVoteProjector()

    @staticmethod
    def default_sync_start_date() -> str:
        return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    @staticmethod
    def default_end_date() -> str:
        return datetime.now().strftime("%Y-%m-%d")

    @staticmethod
    def _safe_int(value: Any, default: int = 22) -> int:
        try:
            return int(str(value).strip())
        except (TypeError, ValueError):
            return default

    def _write_artifact(self, prefix: str, payload: Any) -> str:
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        path = self.artifact_dir / f"{prefix}_{uuid4().hex}.json"
        with path.open("w", encoding="utf-8") as fp:
            json.dump(payload, fp, ensure_ascii=False)
        return str(path)

    def _read_artifact(self, artifact_path: str) -> Any:
        with open(artifact_path, "r", encoding="utf-8") as fp:
            return json.load(fp)

    def _resolve_start_date(self, source_name: str, start_date: str | None, end_date: str, age: str) -> str:
        if start_date:
            return start_date
        if self.mode == "dry_run":
            return self.default_sync_start_date()
        db = self.build_db_manager(self.mode)
        checkpoint = db.get_ingest_checkpoint(source_name, self._safe_int(age, default=22))
        if checkpoint and checkpoint.get("last_reference_date"):
            return checkpoint["last_reference_date"].strftime("%Y-%m-%d")
        return self.default_sync_start_date()

    def fetch_lifecycle_step(self, start_date: str | None = None, end_date: str | None = None, age: str | None = None) -> Dict[str, Any]:
        end_date = end_date or self.default_end_date()
        age = str(age or "22")
        start_date = self._resolve_start_date("bill_status_lifecycle", start_date, end_date, age)
        payload = self.lifecycle_fetcher.fetch(start_date=start_date, end_date=end_date, age=age)
        rows = payload.get("rows") or []
        if not rows:
            return {"mode": self.mode, "fetched": 0, "artifact_path": None, "step": "fetch_lifecycle"}
        artifact_path = self._write_artifact("bill_status_lifecycle_fetch", payload)
        return {
            "mode": self.mode,
            "step": "fetch_lifecycle",
            "fetched": len(rows),
            "artifact_path": artifact_path,
        }

    def _update_bill_projection(self, db: Any, updates: List[Dict[str, Any]]) -> int:
        if not updates:
            return 0
        params = [
            (
                item.get("committee"),
                item.get("stage"),
                item.get("bill_result"),
                item.get("bill_id"),
            )
            for item in updates
            if item.get("bill_id")
        ]
        if not params:
            return 0
        with db.transaction() as cursor:
            cursor.executemany(
                """
                UPDATE Bill
                SET committee = COALESCE(%s, committee),
                    stage = COALESCE(%s, stage),
                    bill_result = COALESCE(%s, bill_result),
                    modified_date = NOW()
                WHERE bill_id = %s
                """,
                params,
            )
        return len(params)

    def upsert_lifecycle_step(self, artifact_path: str) -> Dict[str, Any]:
        payload = self._read_artifact(artifact_path)
        projection = self.lifecycle_projector.project(payload)
        events = projection.get("events") or []
        updates = projection.get("updates") or []
        if not events:
            return {"mode": self.mode, "step": "upsert_lifecycle", "upserted": 0, "updated": 0, "duplicate": 0, "not_found": 0}
        if self.mode == "dry_run":
            return {
                "mode": self.mode,
                "step": "upsert_lifecycle",
                "upserted": 0,
                "updated": len(updates),
                "duplicate": 0,
                "not_found": 0,
            }

        db = self.build_db_manager(self.mode)
        stage_result = db.update_bill_stage(events)
        result_rows = [{"bill_id": item["bill_id"], "bill_result": item.get("bill_result")} for item in updates if item.get("bill_result")]
        if result_rows:
            db.update_bill_result(result_rows)
        updated = self._update_bill_projection(db, updates)
        last_reference_date = max((item.get("source_reference_date") for item in updates if item.get("source_reference_date")), default=None)
        db.upsert_ingest_checkpoint(
            source_name="bill_status_lifecycle",
            assembly_number=self._safe_int(payload.get("age"), default=22),
            last_reference_date=last_reference_date,
            metadata={
                "events": len(events),
                "updated": updated,
                "duplicate": len(stage_result.get("duplicate_bill", [])),
                "not_found": len(stage_result.get("not_found_bill", [])),
            },
        )
        return {
            "mode": self.mode,
            "step": "upsert_lifecycle",
            "upserted": len(events),
            "updated": updated,
            "duplicate": len(stage_result.get("duplicate_bill", [])),
            "not_found": len(stage_result.get("not_found_bill", [])),
        }

    def fetch_vote_step(self, start_date: str | None = None, end_date: str | None = None, age: str | None = None) -> Dict[str, Any]:
        end_date = end_date or self.default_end_date()
        age = str(age or "22")
        start_date = self._resolve_start_date("bill_status_vote", start_date, end_date, age)
        payload = self.vote_fetcher.fetch(start_date=start_date, end_date=end_date, age=age)
        vote_rows = payload.get("vote_rows") or []
        if not vote_rows:
            return {"mode": self.mode, "fetched": 0, "artifact_path": None, "step": "fetch_vote"}
        artifact_path = self._write_artifact("bill_status_vote_fetch", payload)
        return {
            "mode": self.mode,
            "step": "fetch_vote",
            "fetched": len(vote_rows),
            "artifact_path": artifact_path,
        }

    def upsert_vote_step(self, artifact_path: str) -> Dict[str, Any]:
        payload = self._read_artifact(artifact_path)
        projection = self.vote_projector.project(payload)
        vote_rows = projection.get("vote_rows") or []
        party_rows = projection.get("vote_party_rows") or []
        if self.mode == "dry_run":
            return {"mode": self.mode, "step": "upsert_vote", "vote_count": 0, "party_count": 0}
        if not vote_rows and not party_rows:
            return {"mode": self.mode, "step": "upsert_vote", "vote_count": 0, "party_count": 0}

        db = self.build_db_manager(self.mode)
        if vote_rows:
            db.insert_vote_record(vote_rows)
        if party_rows:
            db.insert_vote_party(party_rows)
        db.upsert_ingest_checkpoint(
            source_name="bill_status_vote",
            assembly_number=self._safe_int(payload.get("age"), default=22),
            last_reference_date=payload.get("end_date"),
            metadata={"vote_count": len(vote_rows), "party_count": len(party_rows)},
        )
        return {
            "mode": self.mode,
            "step": "upsert_vote",
            "vote_count": len(vote_rows),
            "party_count": len(party_rows),
        }
