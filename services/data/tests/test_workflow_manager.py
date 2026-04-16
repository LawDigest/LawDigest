import json
import os
import sys
from unittest.mock import Mock, patch

import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lawdigest_data.bills.DataFetcher import DataFetcher  # noqa: E402
from lawdigest_data.bills.DataProcessor import DataProcessor  # noqa: E402
from lawdigest_data.core.WorkFlowManager import WorkFlowManager  # noqa: E402


def _build_candidate_df():
    return pd.DataFrame(
        {
            "bill_id": ["BILL-1"],
            "bill_name": ["테스트 법안"],
            "proposeDate": ["2026-01-01"],
            "summary": [None],
            "stage": ["접수"],
            "proposer_kind": ["의원"],
            "billNumber": [1],
            "bill_link": ["https://example.com/bill"],
            "assemblyNumber": ["22"],
        }
    )


def _build_hydrated_df():
    return pd.DataFrame(
        {
            "bill_id": ["BILL-1"],
            "bill_name": ["테스트 법안"],
            "proposeDate": ["2026-01-01"],
            "summary": ["요약"],
            "stage": ["접수"],
            "proposer_kind": ["의원"],
            "billNumber": [1],
            "billPdfUrl": ["https://example.com/bill.pdf"],
            "billResult": [None],
            "bill_link": ["https://example.com/bill"],
            "publicProposerIdList": [["P1"]],
            "rstProposerIdList": [["R1"]],
        }
    )


def test_normalize_execution_mode_aliases():
    assert WorkFlowManager.normalize_execution_mode("dry_run") == "dry_run"
    assert WorkFlowManager.normalize_execution_mode("dry-run") == "dry_run"
    assert WorkFlowManager.normalize_execution_mode("test_db") == "test_db"
    assert WorkFlowManager.normalize_execution_mode("test") == "test_db"
    assert WorkFlowManager.normalize_execution_mode("prod") == "prod"
    assert WorkFlowManager.normalize_execution_mode("remote") == "prod"


def test_update_bills_data_dry_run_does_not_build_db():
    df_candidates = _build_candidate_df()
    df_bills = _build_hydrated_df()
    manager = WorkFlowManager("dry_run")

    with patch.object(DataFetcher, "discover_bill_candidates", return_value=df_candidates), patch.object(
        DataFetcher, "hydrate_bill_candidates", return_value=df_bills
    ), patch.object(DataProcessor, "process_congressman_bills", return_value=df_bills.copy()), patch.object(
        WorkFlowManager, "_build_db_manager"
    ) as mock_db_builder:
        result = manager.update_bills_data(
            start_date="2026-01-01",
            end_date="2026-01-01",
            age="22",
        )

    assert result["mode"] == "dry_run"
    assert result["fetched"] == 1
    assert result["upserted"] == 0
    mock_db_builder.assert_not_called()


def test_update_lawmakers_data_dry_run():
    df_lawmakers = pd.DataFrame(
        {
            "MONA_CD": ["M1"],
            "HG_NM": ["홍길동"],
            "CMIT_NM": ["교육위원회"],
            "POLY_NM": ["더불어민주당"],
            "REELE_GBN_NM": ["재선"],
            "HOMEPAGE": ["https://example.com"],
            "ORIG_NM": ["서울"],
            "UNITS": ["22대"],
            "BTH_DATE": ["1970-01-01"],
            "SEX_GBN_NM": ["남"],
            "E_MAIL": ["m1@example.com"],
            "ASSEM_ADDR": ["서울시"],
            "TEL_NO": ["02-123-4567"],
            "MEM_TITLE": ["경력"],
            "ENG_NM": [""],
            "HJ_NM": [""],
            "BTH_GBN_NM": [""],
            "ELECT_GBN_NM": [""],
            "STAFF": [""],
            "CMITS": [""],
            "SECRETARY": [""],
            "SECRETARY2": [""],
            "JOB_RES_NM": [""],
        }
    )

    manager = WorkFlowManager("dry_run")

    with patch.object(DataFetcher, "fetch_lawmakers_data", return_value=df_lawmakers), patch.object(
        WorkFlowManager, "_build_db_manager"
    ) as mock_db_builder:
        result = manager.update_lawmakers_data()

    assert result["mode"] == "dry_run"
    assert result["count"] == 1
    mock_db_builder.assert_not_called()


def test_fetch_process_upsert_bills_flow_uses_artifacts(tmp_path):
    df_candidates = _build_candidate_df()
    df_bills = _build_hydrated_df()
    manager = WorkFlowManager("dry_run")

    with patch.object(WorkFlowManager, "_artifact_dir", return_value=tmp_path), patch.object(
        DataFetcher, "discover_bill_candidates", return_value=df_candidates
    ), patch.object(DataFetcher, "hydrate_bill_candidates", return_value=df_bills), patch.object(
        DataProcessor, "process_congressman_bills", return_value=df_bills.copy()
    ):
        fetched = manager.fetch_bills_data_step(start_date="2026-01-01", end_date="2026-01-01", age="22")
        processed = manager.process_bills_data_step(fetched["artifact_path"])
        result = manager.upsert_bills_data_step(processed["artifact_path"])

    assert fetched["fetched"] == 1
    assert os.path.exists(fetched["artifact_path"])
    assert processed["processed"] == 1
    assert os.path.exists(processed["artifact_path"])
    assert result["upserted"] == 0

    with open(processed["artifact_path"], "r", encoding="utf-8") as fp:
        rows = json.load(fp)
    assert rows[0]["bill_id"] == "BILL-1"
    assert rows[0]["ingest_status"] == "READY"


def test_fetch_bills_data_step_persists_discovered_candidates_in_test_mode(tmp_path):
    df_candidates = _build_candidate_df()
    db = Mock()
    manager = WorkFlowManager("test")

    with patch.object(WorkFlowManager, "_artifact_dir", return_value=tmp_path), patch.object(
        DataFetcher, "discover_bill_candidates", return_value=df_candidates
    ), patch.object(WorkFlowManager, "_build_db_manager", return_value=db):
        fetched = manager.fetch_bills_data_step(start_date="2026-01-01", end_date="2026-01-01", age="22")

    assert fetched["fetched"] == 1
    assert fetched["discovered"] == 1
    db.insert_bill_info.assert_called_once()
    inserted_rows = db.insert_bill_info.call_args.args[0]
    assert inserted_rows[0]["bill_id"] == "BILL-1"
    assert inserted_rows[0]["ingest_status"] == "PARTIAL"
    db.upsert_ingest_checkpoint.assert_called_once()


def test_build_bill_rows_sets_ready_status_for_public_bill():
    manager = WorkFlowManager("dry_run")
    df_bills = pd.DataFrame(
        {
            "bill_id": ["BILL-1"],
            "bill_name": ["테스트 법안"],
            "proposeDate": ["2026-01-01"],
            "summary": ["요약"],
            "stage": ["접수"],
            "proposer_kind": ["의원"],
            "assemblyNumber": ["22"],
        }
    )

    rows = manager._build_bill_rows(df_bills)

    assert rows[0]["ingest_status"] == "READY"


def test_build_bill_rows_sets_partial_status_when_summary_is_missing():
    manager = WorkFlowManager("dry_run")
    df_bills = pd.DataFrame(
        {
            "bill_id": ["BILL-1"],
            "bill_name": ["테스트 법안"],
            "proposeDate": ["2026-01-01"],
            "summary": [None],
            "stage": ["접수"],
            "proposer_kind": ["의원"],
            "assemblyNumber": ["22"],
        }
    )

    rows = manager._build_bill_rows(df_bills)

    assert rows[0]["ingest_status"] == "PARTIAL"

def test_build_bill_rows_generates_brief_summary_and_does_not_reuse_bill_link_as_pdf_url():
    manager = WorkFlowManager("dry_run")
    df_bills = pd.DataFrame(
        {
            "bill_id": ["BILL-1"],
            "bill_name": ["테스트 법안"],
            "proposeDate": ["2026-01-01"],
            "summary": ["제안이유 및 주요내용\n\n첫 번째 핵심 문장입니다.\n\n상세 설명입니다."],
            "stage": ["접수"],
            "proposer_kind": ["의원"],
            "bill_link": ["https://example.com/bill"],
            "assemblyNumber": ["22"],
        }
    )

    rows = manager._build_bill_rows(df_bills)

    assert rows[0]["brief_summary"] == "첫 번째 핵심 문장입니다."
    assert rows[0]["bill_pdf_url"] is None
