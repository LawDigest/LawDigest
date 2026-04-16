from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List


class BillLifecycleProjector:
    STAGE_DATES = (
        ("접수", ("PPSL_DT",)),
        ("위원회 심사", ("JRCMIT_CMMT_DT", "JRCMIT_PRSNT_DT", "JRCMIT_PROC_DT")),
        ("체계자구 심사", ("LAW_CMMT_DT", "LAW_PRSNT_DT", "LAW_PROC_DT")),
        ("본회의 심의", ("RGS_PRSNT_DT", "RGS_RSLN_DT")),
        ("정부이송", ("GVRN_TRSF_DT",)),
        ("공포", ("PROM_DT",)),
    )

    def _text(self, value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    def _safe_int(self, value: Any, default: int = 22) -> int:
        try:
            return int(str(value).strip())
        except (TypeError, ValueError):
            return default

    def _parse_date(self, value: Any) -> datetime | None:
        text = self._text(value)
        if not text:
            return None
        for fmt in ("%Y-%m-%d", "%Y.%m.%d"):
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue
        return None

    def _normalize_date(self, value: Any) -> str | None:
        parsed = self._parse_date(value)
        return parsed.strftime("%Y-%m-%d") if parsed else None

    def _first_text(self, *values: Any) -> str | None:
        for value in values:
            text = self._text(value)
            if text:
                return text
        return None

    def _build_committee(self, row: Dict[str, Any], review_rows: List[Dict[str, Any]]) -> str | None:
        review_committee = None
        for review_row in review_rows:
            review_committee = self._first_text(
                review_row.get("JRCMIT_NM"),
                review_row.get("COMMITTEE"),
                review_row.get("CURR_COMMITTEE"),
            )
            if review_committee:
                break
        return self._first_text(row.get("JRCMIT_NM"), row.get("CURR_COMMITTEE"), review_committee)

    def _build_result(self, row: Dict[str, Any], review_rows: List[Dict[str, Any]]) -> str | None:
        review_result = None
        for review_row in review_rows:
            review_result = self._first_text(
                review_row.get("PROC_RSLT"),
                review_row.get("PROC_RESULT_CD"),
                review_row.get("RGS_CONF_RSLT"),
            )
            if review_result:
                break
        return self._first_text(
            row.get("RGS_CONF_RSLT"),
            row.get("PROC_RESULT_CD"),
            row.get("PROC_RSLT"),
            review_result,
        )

    def _build_events(self, row: Dict[str, Any], review_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        bill_id = self._text(row.get("BILL_ID"))
        if not bill_id:
            return []

        committee = self._build_committee(row, review_rows)
        bill_result = self._build_result(row, review_rows)
        bill_name = self._first_text(row.get("BILL_NAME"), row.get("BILL_NM"))
        source_reference_date = self._first_text(
            row.get("PROM_DT"),
            row.get("GVRN_TRSF_DT"),
            row.get("RGS_RSLN_DT"),
            row.get("RGS_PRSNT_DT"),
            row.get("LAW_PROC_DT"),
            row.get("JRCMIT_PROC_DT"),
            row.get("PROC_DT"),
            row.get("PPSL_DT"),
        )

        events: List[Dict[str, Any]] = []
        for stage, keys in self.STAGE_DATES:
            date_value = None
            for key in keys:
                date_value = self._normalize_date(row.get(key))
                if date_value:
                    break
            if not date_value:
                continue
            event = {
                "bill_id": bill_id,
                "bill_name": bill_name,
                "assembly_number": self._safe_int(row.get("AGE") or row.get("assemblyNumber")),
                "stage": stage,
                "committee": committee,
                "status_update_date": date_value,
                "bill_result": bill_result if stage == "본회의 심의" else None,
                "source_name": "bill_status_lifecycle",
                "source_reference_date": self._normalize_date(source_reference_date) or date_value,
            }
            events.append(event)

        if not events:
            fallback_date = self._normalize_date(source_reference_date)
            if fallback_date:
                events.append(
                    {
                        "bill_id": bill_id,
                        "bill_name": bill_name,
                        "assembly_number": self._safe_int(row.get("AGE") or row.get("assemblyNumber")),
                        "stage": "접수",
                        "committee": committee,
                        "status_update_date": fallback_date,
                        "bill_result": None,
                        "source_name": "bill_status_lifecycle",
                        "source_reference_date": fallback_date,
                    }
                )

        events.sort(key=lambda item: (item["status_update_date"], item["stage"]))
        return events

    def project(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        review_map = payload.get("review_rows") or {}
        lifecycle_events: List[Dict[str, Any]] = []
        lifecycle_updates: List[Dict[str, Any]] = []

        for row in payload.get("rows") or []:
            bill_id = self._text(row.get("BILL_ID"))
            review_rows = review_map.get(bill_id, [])
            events = self._build_events(row, review_rows)
            if not events:
                continue
            lifecycle_events.extend(events)
            latest = events[-1]
            lifecycle_updates.append(
                {
                    "bill_id": latest["bill_id"],
                    "committee": latest.get("committee"),
                    "stage": latest.get("stage"),
                    "bill_result": self._build_result(row, review_rows),
                    "source_reference_date": latest.get("source_reference_date"),
                    "assembly_number": latest.get("assembly_number"),
                }
            )

        return {
            "events": lifecycle_events,
            "updates": lifecycle_updates,
            "age": payload.get("age"),
            "start_date": payload.get("start_date"),
            "end_date": payload.get("end_date"),
        }


class BillVoteProjector:
    def _text(self, value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    def _safe_int(self, value: Any) -> int:
        if value is None:
            return 0
        try:
            return int(str(value).replace(",", "").strip())
        except (TypeError, ValueError):
            return 0

    def project(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        vote_rows: List[Dict[str, Any]] = []
        for row in payload.get("vote_rows") or []:
            bill_id = self._text(row.get("BILL_ID") or row.get("billId") or row.get("bill_id"))
            if not bill_id:
                continue
            vote_rows.append(
                {
                    "bill_id": bill_id,
                    "votes_for_count": self._safe_int(row.get("YES_TCNT") if row.get("YES_TCNT") is not None else row.get("voteForCount")),
                    "votes_againt_count": self._safe_int(row.get("NO_TCNT") if row.get("NO_TCNT") is not None else row.get("voteAgainstCount")),
                    "abstention_count": self._safe_int(row.get("BLANK_TCNT") if row.get("BLANK_TCNT") is not None else row.get("abstentionCount")),
                    "total_vote_count": self._safe_int(row.get("VOTE_TCNT") if row.get("VOTE_TCNT") is not None else row.get("totalVoteCount")),
                }
            )

        party_rows: List[Dict[str, Any]] = []
        for row in payload.get("vote_party_rows") or []:
            bill_id = self._text(row.get("BILL_ID") or row.get("billId") or row.get("bill_id"))
            party_name = self._text(row.get("POLY_NM") or row.get("partyName") or row.get("PARTY_NAME"))
            if not bill_id or not party_name:
                continue
            party_rows.append(
                {
                    "bill_id": bill_id,
                    "party_name": party_name,
                    "votes_for_count": self._safe_int(row.get("YES_TCNT") if row.get("YES_TCNT") is not None else row.get("voteForCount") if row.get("voteForCount") is not None else row.get("votes_for_count")),
                }
            )

        return {
            "vote_rows": vote_rows,
            "vote_party_rows": party_rows,
            "age": payload.get("age"),
            "start_date": payload.get("start_date"),
            "end_date": payload.get("end_date"),
        }
