import os
import sys
from unittest.mock import patch

import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import lawdigest_data.bills.DataFetcher as data_fetcher_module  # noqa: E402
from lawdigest_data.bills.DataFetcher import DataFetcher  # noqa: E402


class _FakeClient:
    def __init__(self, session, api_key):
        self.session = session
        self.api_key = api_key

    def fetch_rows(self, endpoint, params=None, all_pages=True, page_size=100):
        if endpoint == "nwbqublzajtcqpdae":
            return self.fetch_pending_bills()
        if endpoint == "nzpltgfqabtcpsmai":
            return self.fetch_processed_bills(str((params or {}).get("AGE", "22")))
        if endpoint == "nxjuyqnxadtotdrbw":
            return self.fetch_recent_plenary_bills(str((params or {}).get("AGE", "22")))
        if endpoint == "BILLRCP":
            return self.fetch_bill_receipts(str((params or {}).get("ERACO", "22")))
        return []

    def fetch_bill_receipts(self, age):
        return []

    def fetch_pending_bills(self):
        return [
            {
                "BILL_ID": "BILL-1",
                "BILL_NO": "2200001",
                "PROPOSE_DT": "2026-04-15",
                "BILL_NM": "테스트 법안",
            }
        ]

    def fetch_processed_bills(self, age):
        return []

    def fetch_recent_plenary_bills(self, age):
        return []

    def fetch_member_bills(self, age, **filters):
        return []

    def fetch_bill_detail(self, bill_id):
        return {
            "BILL_ID": bill_id,
            "BILL_NO": "2200001",
            "BILL_NM": "테스트 법안",
            "PPSR_KIND": "의원",
            "PPSR": "홍길동의원 등 10인",
            "PPSL_DT": "2026-04-15",
        }

    def fetch_bill_summary(self, bill_no):
        return {
            "BILL_NO": bill_no,
            "SUMMARY": "열린국회정보 요약",
        }

    def fetch_bill_lifecycle(self, bill_no):
        return {
            "BILL_NO": bill_no,
            "JRCMIT_NM": "정무위원회",
            "LINK_URL": "https://example.com/bill/2200001",
            "PDF_LINK_URL": "https://example.com/bill/2200001.pdf",
        }


class _FakeClientWithoutSummary(_FakeClient):
    def fetch_bill_summary(self, bill_no):
        return {}


class _FakeClientWithMissingOptionalResponses(_FakeClient):
    def fetch_bill_summary(self, bill_no):
        return None

    def fetch_bill_lifecycle(self, bill_no):
        return None


def test_discover_bill_candidates_collects_base_bill_rows(monkeypatch):
    monkeypatch.setenv("APIKEY_billsInfo", "test-key")
    monkeypatch.setattr(data_fetcher_module, "OpenAssemblyBillClient", _FakeClient)

    fetcher = DataFetcher(filter_data=False)
    df = fetcher.discover_bill_candidates(start_date="2026-04-15", end_date="2026-04-15", age="22")

    assert len(df) == 1
    row = df.iloc[0]
    assert row["bill_id"] == "BILL-1"
    assert row["bill_name"] == "테스트 법안"
    assert row["summary"] is None
    assert row["stage"] == "접수"
    assert row["assemblyNumber"] == "22"


def test_fetch_bills_data_uses_open_assembly_hydration(monkeypatch):
    monkeypatch.setenv("APIKEY_billsInfo", "test-key")
    monkeypatch.setattr(data_fetcher_module, "OpenAssemblyBillClient", _FakeClient)

    fetcher = DataFetcher(filter_data=False)
    df = fetcher.fetch_bills_data(start_date="2026-04-15", end_date="2026-04-15", age="22")

    assert len(df) == 1
    row = df.iloc[0]
    assert row["bill_id"] == "BILL-1"
    assert row["bill_name"] == "테스트 법안"
    assert row["summary"] == "열린국회정보 요약"
    assert row["stage"] == "위원회 심사"
    assert row["committee"] == "정무위원회"
    assert row["bill_link"] == "https://example.com/bill/2200001"
    assert row["billPdfUrl"] == "https://example.com/bill/2200001.pdf"
    assert row["proposer_kind"] == "의원"
    assert row["assemblyNumber"] == "22"


def test_fetch_bills_data_keeps_partial_bill_without_summary(monkeypatch):
    monkeypatch.setenv("APIKEY_billsInfo", "test-key")
    monkeypatch.setattr(data_fetcher_module, "OpenAssemblyBillClient", _FakeClientWithoutSummary)

    fetcher = DataFetcher(filter_data=False)
    df = fetcher.fetch_bills_data(start_date="2026-04-15", end_date="2026-04-15", age="22")

    assert len(df) == 1
    row = df.iloc[0]
    assert row["bill_id"] == "BILL-1"
    assert row["summary"] is None
    assert row["stage"] == "위원회 심사"


def test_fetch_bills_data_keeps_partial_bill_when_optional_open_assembly_rows_are_missing(monkeypatch):
    monkeypatch.setenv("APIKEY_billsInfo", "test-key")
    monkeypatch.setattr(data_fetcher_module, "OpenAssemblyBillClient", _FakeClientWithMissingOptionalResponses)

    fetcher = DataFetcher(filter_data=False)
    df = fetcher.fetch_bills_data(start_date="2026-04-15", end_date="2026-04-15", age="22")

    assert len(df) == 1
    row = df.iloc[0]
    assert row["bill_id"] == "BILL-1"
    assert row["bill_name"] == "테스트 법안"
    assert row["summary"] is None
    assert row["stage"] == "접수"
    assert row["proposer_kind"] == "의원"


def test_fetch_bills_coactors_retries_empty_bill_response():
    fetcher = DataFetcher()
    fetcher.df_lawmakers = pd.DataFrame(
        {
            "HG_NM": ["홍길동"],
            "MONA_CD": ["M1"],
        }
    )
    empty_response = pd.DataFrame()
    valid_response = pd.DataFrame(
        [
            {
                "BILL_ID": "BILL-1",
                "PUBL_PROPOSER": "대표발의",
                "PPSR_CD": "M1",
                "PPSR_NM": "홍길동",
            }
        ]
    )

    with patch.dict("os.environ", {"APIKEY_billProposers": "test-key"}), patch.object(
        fetcher,
        "fetch_data_generic",
        side_effect=[empty_response, valid_response],
    ) as fetch_data, patch("lawdigest_data.bills.DataFetcher.time.sleep"):
        result = fetcher.fetch_bills_coactors(
            df_bills=pd.DataFrame({"bill_id": ["BILL-1"]}),
            max_retry=1,
        )

    assert result["bill_id"].tolist() == ["BILL-1"]
    assert fetch_data.call_count == 2
    assert "max_retry" not in fetch_data.call_args_list[0].kwargs["params"]
