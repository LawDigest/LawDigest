import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd

sys.path.append(str(Path(__file__).parents[1] / "scripts" / "db"))

import fill_missing_proposers as repair  # noqa: E402


def test_fetch_and_process_proposers_passes_current_bill_id_column():
    fetcher = Mock()
    fetcher.fetch_bills_coactors.return_value = pd.DataFrame(
        {
            "bill_id": ["BILL-1"],
            "representativeProposerIdList": [["REP-1"]],
            "publicProposerIdList": [["REP-1", "PUB-1"]],
        }
    )

    with patch.object(repair, "DataFetcher", return_value=fetcher):
        result = repair.fetch_and_process_proposers(["BILL-1"], Mock())

    passed_df = fetcher.fetch_bills_coactors.call_args.kwargs["df_bills"]
    assert passed_df["bill_id"].tolist() == ["BILL-1"]
    assert result["bill_id"].tolist() == ["BILL-1"]


def test_update_database_delegates_relation_write_as_one_operation():
    db_manager = Mock()
    db_manager.replace_proposer_relations.return_value = {
        "bills": 1,
        "representative_rows": 1,
        "public_rows": 2,
    }
    proposer_rows = pd.DataFrame(
        {
            "bill_id": ["BILL-1"],
            "representativeProposerIdList": [["REP-1"]],
            "publicProposerIdList": [["REP-1", "PUB-1"]],
        }
    )

    repair.update_database(db_manager, proposer_rows, {"REP-1": 1, "PUB-1": 1}, db_update=True)

    db_manager.replace_proposer_relations.assert_called_once_with(
        [
            {
                "bill_id": "BILL-1",
                "representative_proposer_ids": ["REP-1"],
                "public_proposer_ids": ["REP-1", "PUB-1"],
            }
        ]
    )
