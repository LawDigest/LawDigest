from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from ..bills.DataFetcher import DataFetcher


class LifecycleStatusFetcher:
    """Fetch lifecycle-oriented bill status snapshots from open assembly."""

    DATE_KEYS = (
        "PROM_DT",
        "GVRN_TRSF_DT",
        "RGS_RSLN_DT",
        "RGS_PRSNT_DT",
        "LAW_PROC_DT",
        "LAW_PRSNT_DT",
        "LAW_CMMT_DT",
        "JRCMIT_PROC_DT",
        "JRCMIT_PRSNT_DT",
        "JRCMIT_CMMT_DT",
        "PROC_DT",
        "PPSL_DT",
    )

    def __init__(self, fetcher: DataFetcher | None = None):
        self.fetcher = fetcher or DataFetcher()

    @staticmethod
    def _normalize_date(value: str | None) -> str | None:
        if not value:
            return None
        text = str(value).strip()
        if not text:
            return None
        for fmt in ("%Y-%m-%d", "%Y.%m.%d"):
            try:
                return datetime.strptime(text, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        return None

    @staticmethod
    def _should_backfill_review(row: Dict[str, Any]) -> bool:
        return not any(
            row.get(key)
            for key in (
                "JRCMIT_NM",
                "CURR_COMMITTEE",
                "JRCMIT_PRSNT_DT",
                "JRCMIT_PROC_DT",
                "LAW_PRSNT_DT",
                "LAW_PROC_DT",
            )
        )

    def fetch(self, start_date: str, end_date: str, age: str) -> Dict[str, Any]:
        start_bound = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_bound = datetime.strptime(end_date, "%Y-%m-%d").date()
        client = self.fetcher._build_open_assembly_client()
        if client is None:
            return {
                "start_date": start_date,
                "end_date": end_date,
                "age": age,
                "rows": [],
                "review_rows": {},
            }

        rows = self.fetcher._collect_incremental_rows(
            client,
            "ALLBILL",
            {"AGE": age},
            self.DATE_KEYS,
            start_bound,
            end_bound,
        )

        deduped: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            bill_id = str(row.get("BILL_ID") or "").strip()
            if not bill_id:
                continue
            normalized = dict(row)
            for key in self.DATE_KEYS:
                if key in normalized:
                    normalized[key] = self._normalize_date(normalized.get(key))
            deduped[bill_id] = normalized

        review_rows: Dict[str, List[Dict[str, Any]]] = {}
        for bill_id, row in deduped.items():
            if not self._should_backfill_review(row):
                continue
            bill_no = str(row.get("BILL_NO") or "").strip()
            if not bill_no:
                continue
            try:
                supplemental = client.fetch_rows("BILLJUDGE", {"BILL_NO": bill_no}, all_pages=False, page_size=20)
            except Exception:
                supplemental = []
            if supplemental:
                review_rows[bill_id] = [dict(item) for item in supplemental]

        return {
            "start_date": start_date,
            "end_date": end_date,
            "age": age,
            "rows": list(deduped.values()),
            "review_rows": review_rows,
        }
