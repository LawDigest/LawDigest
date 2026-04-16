from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import requests


class OpenAssemblyBillClient:
    BASE_URL = "https://open.assembly.go.kr/portal/openapi"
    SUCCESS_CODE = "INFO-000"
    NO_DATA_CODE = "INFO-200"

    def __init__(self, session: requests.Session, api_key: str):
        self.session = session
        self.api_key = api_key

    def _build_params(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        merged = {"KEY": self.api_key, "Type": "json"}
        if params:
            merged.update(params)
        return merged

    def _parse_response(self, endpoint: str, response_text: str) -> tuple[list[dict[str, Any]], int]:
        payload = json.loads(response_text)
        if "RESULT" in payload:
            result = payload["RESULT"] or {}
            code = result.get("CODE")
            if code == self.NO_DATA_CODE:
                return [], 0
            raise RuntimeError(f"{endpoint} API error: {code} {result.get('MESSAGE')}")

        root = payload.get(endpoint)
        if not root or len(root) < 2:
            return [], 0

        head = root[0].get("head", [])
        result = (head[1] or {}).get("RESULT", {}) if len(head) > 1 else {}
        code = result.get("CODE")
        if code == self.NO_DATA_CODE:
            return [], 0
        if code != self.SUCCESS_CODE:
            raise RuntimeError(f"{endpoint} API error: {code} {result.get('MESSAGE')}")

        total_count = int((head[0] or {}).get("list_total_count", 0)) if head else 0
        rows = root[1].get("row", []) if len(root) > 1 else []
        return rows, total_count

    def fetch_rows(self, endpoint: str, params: Optional[Dict[str, Any]] = None, *, all_pages: bool = True, page_size: int = 100) -> List[Dict[str, Any]]:
        query = self._build_params(params)
        query.setdefault("pIndex", 1)
        query.setdefault("pSize", page_size)

        all_rows: List[Dict[str, Any]] = []
        total_count = 0

        while True:
            response = self.session.get(f"{self.BASE_URL}/{endpoint}", params=query, timeout=30)
            response.raise_for_status()

            rows, parsed_total_count = self._parse_response(endpoint, response.text)
            total_count = parsed_total_count or total_count
            if not rows:
                break

            all_rows.extend(rows)
            if not all_pages:
                break
            if total_count and len(all_rows) >= total_count:
                break

            query["pIndex"] += 1

        return all_rows

    def fetch_bill_receipts(self, age: str) -> List[Dict[str, Any]]:
        return self.fetch_rows("BILLRCP", {"ERACO": f"제{age}대"})

    def fetch_pending_bills(self) -> List[Dict[str, Any]]:
        return self.fetch_rows("nwbqublzajtcqpdae")

    def fetch_processed_bills(self, age: str) -> List[Dict[str, Any]]:
        return self.fetch_rows("nzpltgfqabtcpsmai", {"AGE": age})

    def fetch_recent_plenary_bills(self, age: str) -> List[Dict[str, Any]]:
        return self.fetch_rows("nxjuyqnxadtotdrbw", {"AGE": age})

    def fetch_member_bills(self, age: str, **filters: Any) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {"AGE": age}
        params.update({k: v for k, v in filters.items() if v is not None})
        return self.fetch_rows("nzmimeepazxkubdpn", params, all_pages=not filters)

    def fetch_bill_detail(self, bill_id: str) -> Optional[Dict[str, Any]]:
        rows = self.fetch_rows("BILLINFODETAIL", {"BILL_ID": bill_id}, all_pages=False, page_size=1)
        return rows[0] if rows else None

    def fetch_bill_summary(self, bill_no: str) -> Optional[Dict[str, Any]]:
        rows = self.fetch_rows("BPMBILLSUMMARY", {"BILL_NO": bill_no}, all_pages=False, page_size=1)
        return rows[0] if rows else None

    def fetch_bill_lifecycle(self, bill_no: str) -> Optional[Dict[str, Any]]:
        rows = self.fetch_rows("ALLBILL", {"BILL_NO": bill_no}, all_pages=False, page_size=1)
        return rows[0] if rows else None
