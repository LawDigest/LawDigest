from __future__ import annotations

from typing import Any, Dict

from ..bills.DataFetcher import DataFetcher


class VoteStatusFetcher:
    """Fetch vote-oriented status data via the existing DataFetcher paths."""

    def __init__(self, fetcher: DataFetcher | None = None):
        self.fetcher = fetcher or DataFetcher()

    def fetch(self, start_date: str, end_date: str, age: str) -> Dict[str, Any]:
        df_vote = self.fetcher.fetch_bills_vote(start_date=start_date, end_date=end_date, age=age)
        if df_vote is None or df_vote.empty:
            return {
                "start_date": start_date,
                "end_date": end_date,
                "age": age,
                "vote_rows": [],
                "vote_party_rows": [],
            }

        df_vote_party = self.fetcher.fetch_vote_party(
            df_vote=df_vote,
            start_date=start_date,
            end_date=end_date,
            age=age,
        )

        return {
            "start_date": start_date,
            "end_date": end_date,
            "age": age,
            "vote_rows": df_vote.to_dict(orient="records"),
            "vote_party_rows": [] if df_vote_party is None or df_vote_party.empty else df_vote_party.to_dict(orient="records"),
        }
