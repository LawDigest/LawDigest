from unittest.mock import Mock

import pandas as pd

from lawdigest_data.bills.DataProcessor import DataProcessor


def test_process_congressman_bills_requests_coactors_for_current_bills_only():
    fetcher = Mock()
    fetcher.fetch_bills_coactors.return_value = pd.DataFrame(
        {
            "bill_id": ["BILL-1"],
            "publicProposerIdList": [["P1"]],
        }
    )

    processor = DataProcessor(fetcher)
    df_bills = pd.DataFrame(
        {
            "bill_id": ["BILL-1"],
            "bill_name": ["테스트법안(홍길동의원 등 1인)"],
            "proposer_kind": ["의원"],
        }
    )

    processor.process_congressman_bills(df_bills)

    passed_df = fetcher.fetch_bills_coactors.call_args.kwargs["df_bills"]
    assert passed_df["bill_id"].tolist() == ["BILL-1"]


def test_process_congressman_bills_keeps_bills_when_coactors_api_is_empty():
    fetcher = Mock()
    fetcher.fetch_bills_coactors.return_value = pd.DataFrame(
        columns=["bill_id", "representativeProposerIdList", "publicProposerIdList", "ProposerName"]
    )

    processor = DataProcessor(fetcher)
    df_bills = pd.DataFrame(
        {
            "bill_id": ["BILL-1"],
            "bill_name": ["테스트법안(홍길동의원 등 1인)"],
            "proposer_kind": ["의원"],
        }
    )

    result = processor.process_congressman_bills(df_bills)

    assert result["bill_id"].tolist() == ["BILL-1"]
    assert result["publicProposerIdList"].tolist() == [[]]
    assert result["rstProposerIdList"].tolist() == [[]]


def test_process_congressman_bills_preserves_existing_proposers_when_bill_name_has_no_suffix():
    fetcher = Mock()
    fetcher.fetch_bills_coactors.return_value = pd.DataFrame(
        columns=["bill_id", "representativeProposerIdList", "publicProposerIdList", "ProposerName"]
    )

    processor = DataProcessor(fetcher)
    df_bills = pd.DataFrame(
        {
            "bill_id": ["BILL-1"],
            "bill_name": ["테스트법안"],
            "proposer_kind": ["의원"],
            "proposers": ["홍길동의원 등 10인"],
        }
    )

    result = processor.process_congressman_bills(df_bills)

    assert result.iloc[0]["proposers"] == "홍길동의원 등 10인"
