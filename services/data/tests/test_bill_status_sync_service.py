import json
import os
import sys
from unittest.mock import Mock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lawdigest_data.core.bill_status_sync import BillStatusSyncService  # noqa: E402


class _CheckpointDb:
    def __init__(self, checkpoint=None):
        self.checkpoint = checkpoint
        self.updated = []
        self.inserted_votes = []
        self.inserted_parties = []
        self.stage_payload = None
        self.result_payload = None
        self.checkpoint_payload = None

    def get_ingest_checkpoint(self, source_name, assembly_number):
        return self.checkpoint

    def update_bill_stage(self, rows):
        self.stage_payload = rows
        return {"duplicate_bill": [], "not_found_bill": []}

    def update_bill_result(self, rows):
        self.result_payload = rows

    def insert_vote_record(self, rows):
        self.inserted_votes = rows

    def insert_vote_party(self, rows):
        self.inserted_parties = rows

    def upsert_ingest_checkpoint(self, **kwargs):
        self.checkpoint_payload = kwargs

    def transaction(self):
        db = self

        class _Ctx:
            def __enter__(self_inner):
                class _Cursor:
                    def executemany(self_cursor, _query, params):
                        db.updated.extend(params)

                return _Cursor()

            def __exit__(self_inner, exc_type, exc, tb):
                return False

        return _Ctx()


class _LifecycleFetcher:
    def fetch(self, start_date, end_date, age):
        return {
            "start_date": start_date,
            "end_date": end_date,
            "age": age,
            "rows": [
                {
                    "BILL_ID": "BILL-1",
                    "BILL_NAME": "테스트 법안",
                    "AGE": "22",
                    "PPSL_DT": "2026-04-15",
                    "JRCMIT_NM": "정무위원회",
                    "JRCMIT_PRSNT_DT": "2026-04-16",
                    "RGS_RSLN_DT": "2026-04-17",
                    "RGS_CONF_RSLT": "원안가결",
                }
            ],
            "review_rows": {},
        }


class _VoteFetcher:
    def fetch(self, start_date, end_date, age):
        return {
            "start_date": start_date,
            "end_date": end_date,
            "age": age,
            "vote_rows": [
                {"BILL_ID": "BILL-1", "YES_TCNT": "10", "NO_TCNT": "2", "BLANK_TCNT": "1", "VOTE_TCNT": "13"}
            ],
            "vote_party_rows": [
                {"BILL_ID": "BILL-1", "POLY_NM": "테스트당", "YES_TCNT": "10"}
            ],
        }


def test_fetch_lifecycle_step_uses_checkpoint_and_writes_artifact(tmp_path):
    checkpoint_db = _CheckpointDb(checkpoint={"last_reference_date": Mock(strftime=lambda fmt: "2026-04-14")})
    service = BillStatusSyncService(mode="test_db", build_db_manager=lambda mode: checkpoint_db, artifact_dir=tmp_path)
    service.lifecycle_fetcher = _LifecycleFetcher()

    result = service.fetch_lifecycle_step(end_date="2026-04-16", age="22")

    assert result["fetched"] == 1
    assert os.path.exists(result["artifact_path"])
    with open(result["artifact_path"], "r", encoding="utf-8") as fp:
        payload = json.load(fp)
    assert payload["start_date"] == "2026-04-14"


def test_upsert_lifecycle_step_updates_projection_and_checkpoint(tmp_path):
    db = _CheckpointDb()
    service = BillStatusSyncService(mode="test_db", build_db_manager=lambda mode: db, artifact_dir=tmp_path)
    service.lifecycle_fetcher = _LifecycleFetcher()
    fetched = service.fetch_lifecycle_step(start_date="2026-04-15", end_date="2026-04-16", age="22")

    result = service.upsert_lifecycle_step(fetched["artifact_path"])

    assert result["upserted"] >= 1
    assert result["updated"] == 1
    assert db.stage_payload is not None
    assert db.result_payload == [{"bill_id": "BILL-1", "bill_result": "원안가결"}]
    assert db.checkpoint_payload["source_name"] == "bill_status_lifecycle"


def test_vote_steps_share_artifact_and_checkpoint(tmp_path):
    db = _CheckpointDb()
    service = BillStatusSyncService(mode="test_db", build_db_manager=lambda mode: db, artifact_dir=tmp_path)
    service.vote_fetcher = _VoteFetcher()

    fetched = service.fetch_vote_step(start_date="2026-04-15", end_date="2026-04-16", age="22")
    result = service.upsert_vote_step(fetched["artifact_path"])

    assert fetched["fetched"] == 1
    assert result["vote_count"] == 1
    assert result["party_count"] == 1
    assert db.checkpoint_payload["source_name"] == "bill_status_vote"
