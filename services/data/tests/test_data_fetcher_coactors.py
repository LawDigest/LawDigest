import pandas as pd

from lawdigest_data.bills.DataFetcher import DataFetcher


def test_fetch_bills_coactors_uses_nass_cd_for_older_assembly_rows(monkeypatch):
    monkeypatch.setenv("APIKEY_billProposers", "test-key")
    fetcher = DataFetcher()
    fetcher.df_lawmakers = pd.DataFrame(
        {
            "HG_NM": ["대표의원", "공동의원"],
            "MONA_CD": ["CURRENT-1", "CURRENT-2"],
        }
    )

    def fake_fetch_data_generic(*args, **kwargs):
        return pd.DataFrame(
            [
                {
                    "BILL_ID": "BILL-21",
                    "REP_DIV": "대표발의",
                    "PPSR_NM": "대표의원",
                    "NASS_CD": "HISTORICAL-1",
                },
                {
                    "BILL_ID": "BILL-21",
                    "REP_DIV": "",
                    "PPSR_NM": "공동의원",
                    "NASS_CD": "HISTORICAL-2",
                },
            ]
        )

    monkeypatch.setattr(fetcher, "fetch_data_generic", fake_fetch_data_generic)

    result = fetcher.fetch_bills_coactors(pd.DataFrame({"bill_id": ["BILL-21"]}))

    assert result.to_dict(orient="records") == [
        {
            "bill_id": "BILL-21",
            "representativeProposerIdList": ["HISTORICAL-1"],
            "publicProposerIdList": ["HISTORICAL-1", "HISTORICAL-2"],
            "ProposerName": ["대표의원", "공동의원"],
        }
    ]
