import os
import sys
from unittest.mock import patch

import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.lawdigest_data_pipeline.DataFetcher import DataFetcher  # noqa: E402
from src.lawdigest_data_pipeline.DataProcessor import DataProcessor  # noqa: E402
from src.lawdigest_data_pipeline.WorkFlowManager import WorkFlowManager  # noqa: E402


def test_normalize_execution_mode_aliases():
    assert WorkFlowManager.normalize_execution_mode("dry_run") == "dry_run"
    assert WorkFlowManager.normalize_execution_mode("dry-run") == "dry_run"
    assert WorkFlowManager.normalize_execution_mode("test_db") == "test_db"
    assert WorkFlowManager.normalize_execution_mode("test") == "test_db"
    assert WorkFlowManager.normalize_execution_mode("prod") == "prod"
    assert WorkFlowManager.normalize_execution_mode("remote") == "prod"


def test_update_bills_data_dry_run_does_not_build_db():
    df_bills = pd.DataFrame(
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

    manager = WorkFlowManager("dry_run")

    with patch.object(DataFetcher, "fetch_bills_data", return_value=df_bills), patch.object(
        DataProcessor, "process_congressman_bills", return_value=df_bills.copy()
    ), patch.object(WorkFlowManager, "_build_db_manager") as mock_db_builder:
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
