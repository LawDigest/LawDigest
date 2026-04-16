from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

import pandas as pd

from ..bills.DataFetcher import DataFetcher
from ..bills.DataProcessor import DataProcessor
from ..connectors.DatabaseManager import DatabaseManager
from ..bills.constants import ProposerKindType


class WorkFlowManager:
    """Airflow DAG가 사용하는 법안 파이프라인 오케스트레이터."""

    def __init__(self, mode: str):
        self.mode = self.normalize_execution_mode(mode)

    @staticmethod
    def normalize_execution_mode(execution_mode: str | None) -> str:
        normalized = str(execution_mode or "dry_run").strip().lower().replace("-", "_")
        alias_map = {
            "dry_run": "dry_run",
            "dryrun": "dry_run",
            "test": "test_db",
            "test_db": "test_db",
            "testdb": "test_db",
            "prod": "prod",
            "remote": "prod",
            "db": "prod",
        }

        if normalized not in alias_map:
            raise ValueError("execution_mode must be one of dry_run, test_db/test, or prod")

        return alias_map[normalized]

    @staticmethod
    def _coerce_optional_text(value: object) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, float) and pd.isna(value):
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _safe_to_int(value: object, default: int = 0) -> int:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return default
        try:
            return int(str(value).replace(",", "").strip())
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _coerce_string_list(value: object) -> List[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(v).strip() for v in value if str(v).strip()]
        if isinstance(value, tuple):
            return [str(v).strip() for v in value if str(v).strip()]
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return []
            return [part.strip() for part in text.split(",") if part.strip()]
        text = str(value).strip()
        return [text] if text else []

    @staticmethod
    def _normalize_bill_proposer_kind(proposer_kind: object) -> str:
        normalized = str(proposer_kind or "").strip()
        if not normalized:
            return ProposerKindType.CONGRESSMAN.name

        for kind in ProposerKindType:
            if normalized == kind.value or normalized == kind.name:
                return kind.name

        if normalized == "정부":
            return "GOVERNMENT"

        return ProposerKindType.CONGRESSMAN.name

    @staticmethod
    def _default_bill_start_date() -> str:
        return datetime.now().strftime("%Y-%m-%d")

    @staticmethod
    def _default_sync_start_date() -> str:
        return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    @staticmethod
    def _default_end_date() -> str:
        return datetime.now().strftime("%Y-%m-%d")

    @staticmethod
    def _artifact_dir() -> Path:
        artifact_dir = Path(__file__).resolve().parents[4] / ".airflow_artifacts"
        artifact_dir.mkdir(parents=True, exist_ok=True)
        return artifact_dir

    def _write_artifact(self, prefix: str, payload: Any) -> str:
        path = self._artifact_dir() / f"{prefix}_{uuid4().hex}.json"
        with path.open("w", encoding="utf-8") as fp:
            json.dump(payload, fp, ensure_ascii=False)
        return str(path)

    @staticmethod
    def _read_artifact(artifact_path: str) -> Any:
        with open(artifact_path, "r", encoding="utf-8") as fp:
            return json.load(fp)

    @staticmethod
    def _build_db_manager(execution_mode: str) -> DatabaseManager:
        from lawdigest_ai.db import get_prod_db_config, get_test_db_config

        db_config = get_prod_db_config() if execution_mode == "prod" else get_test_db_config()
        return DatabaseManager(
            host=db_config["host"],
            port=db_config["port"],
            username=db_config["user"],
            password=db_config["password"],
            database=db_config["database"],
        )

    def _build_bill_rows(self, df_bills: pd.DataFrame) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        for row in df_bills.to_dict(orient="records"):
            bill_id = self._coerce_optional_text(row.get("bill_id"))
            if not bill_id:
                continue

            bill_name = self._coerce_optional_text(row.get("bill_name"))
            propose_date = self._coerce_optional_text(row.get("proposeDate"))
            summary = self._coerce_optional_text(row.get("summary"))
            stage = self._coerce_optional_text(row.get("stage"))
            assembly_number = self._safe_to_int(row.get("assemblyNumber"), default=22)

            rows.append(
                {
                    "bill_id": bill_id,
                    "bill_name": bill_name,
                    "assembly_number": assembly_number,
                    "committee": self._coerce_optional_text(row.get("committee")),
                    "gpt_summary": self._coerce_optional_text(row.get("gpt_summary")),
                    "propose_date": propose_date,
                    "summary": summary,
                    "stage": stage,
                    "proposers": self._coerce_optional_text(row.get("proposers")),
                    "bill_pdf_url": self._coerce_optional_text(row.get("billPdfUrl"))
                    or self._coerce_optional_text(row.get("bill_link")),
                    "brief_summary": self._coerce_optional_text(row.get("brief_summary")),
                    "summary_tags": row.get("summary_tags"),
                    "bill_number": self._safe_to_int(row.get("billNumber")),
                    "bill_link": self._coerce_optional_text(row.get("bill_link")),
                    "bill_result": self._coerce_optional_text(row.get("billResult")),
                    "proposer_kind": self._normalize_bill_proposer_kind(
                        row.get("proposer_kind") or row.get("proposerKind")
                    ),
                    "ingest_status": self._determine_bill_ingest_status(
                        bill_name=bill_name,
                        propose_date=propose_date,
                        stage=stage,
                        summary=summary,
                    ),
                    "public_proposer_ids": self._coerce_string_list(row.get("publicProposerIdList")),
                    "rst_proposer_ids": self._coerce_string_list(row.get("rstProposerIdList")),
                }
            )
        return rows

    @staticmethod
    def _determine_bill_ingest_status(
        bill_name: Optional[str],
        propose_date: Optional[str],
        stage: Optional[str],
        summary: Optional[str],
    ) -> str:
        if bill_name and propose_date and stage and summary:
            return "READY"
        if bill_name or propose_date or stage or summary:
            return "PARTIAL"
        return "PENDING"

    def _build_lawmaker_rows(self, df_lawmakers: pd.DataFrame) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        for row in df_lawmakers.to_dict(orient="records"):
            assembly_number = self._safe_to_int(row.get("assemblyNumber"), default=22)
            congressman_id = self._coerce_optional_text(row.get("congressmanId"))
            if not congressman_id:
                continue

            rows.append(
                {
                    "congressman_id": congressman_id,
                    "name": self._coerce_optional_text(row.get("congressmanName")),
                    "party_name": self._coerce_optional_text(row.get("partyName")),
                    "district": self._coerce_optional_text(row.get("district")),
                    "elect_sort": self._coerce_optional_text(row.get("electSort")),
                    "commits": self._coerce_optional_text(row.get("commits")),
                    "elected": self._coerce_optional_text(row.get("elected")),
                    "homepage": self._coerce_optional_text(row.get("homepage")),
                    "congressman_image_url": self._coerce_optional_text(row.get("congressmanImage"))
                    or f"/congressman/{assembly_number}/{congressman_id}.jpg",
                    "email": self._coerce_optional_text(row.get("email")),
                    "sex": self._coerce_optional_text(row.get("sex")),
                    "congressman_age": self._coerce_optional_text(row.get("congressmanBirth")),
                    "congressman_office": self._coerce_optional_text(row.get("congressmanOffice")),
                    "congressman_telephone": self._coerce_optional_text(row.get("congressmanTelephone")),
                    "brief_history": self._coerce_optional_text(row.get("briefHistory")),
                }
            )
        return rows

    def _build_bill_stage_rows(self, df_stage: pd.DataFrame) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        for row in df_stage.to_dict(orient="records"):
            rows.append(
                {
                    "bill_id": self._coerce_optional_text(row.get("billId"))
                    or self._coerce_optional_text(row.get("bill_id")),
                    "stage": self._coerce_optional_text(row.get("stage")),
                    "committee": self._coerce_optional_text(row.get("committee")),
                    "status_update_date": self._coerce_optional_text(row.get("statusUpdateDate"))
                    or self._coerce_optional_text(row.get("status_update_date"))
                    or self._coerce_optional_text(row.get("DT")),
                }
            )
        return rows

    def _build_bill_result_rows(self, df_result: pd.DataFrame) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        for row in df_result.to_dict(orient="records"):
            rows.append(
                {
                    "bill_id": self._coerce_optional_text(row.get("billId"))
                    or self._coerce_optional_text(row.get("bill_id")),
                    "bill_result": self._coerce_optional_text(row.get("billProposeResult"))
                    or self._coerce_optional_text(row.get("bill_result")),
                }
            )
        return rows

    def _build_vote_rows(self, df_vote: pd.DataFrame) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        for row in df_vote.to_dict(orient="records"):
            rows.append(
                {
                    "bill_id": self._coerce_optional_text(row.get("billId"))
                    or self._coerce_optional_text(row.get("bill_id")),
                    "votes_for_count": self._safe_to_int(
                        row.get("voteForCount")
                        if row.get("voteForCount") is not None
                        else row.get("votes_for_count")
                    ),
                    "votes_againt_count": self._safe_to_int(
                        row.get("voteAgainstCount")
                        if row.get("voteAgainstCount") is not None
                        else row.get("votes_againt_count")
                    ),
                    "abstention_count": self._safe_to_int(
                        row.get("abstentionCount")
                        if row.get("abstentionCount") is not None
                        else row.get("abstention_count")
                    ),
                    "total_vote_count": self._safe_to_int(
                        row.get("totalVoteCount")
                        if row.get("totalVoteCount") is not None
                        else row.get("total_vote_count")
                    ),
                }
            )
        return rows

    def _build_vote_party_rows(self, df_vote_party: pd.DataFrame) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        for row in df_vote_party.to_dict(orient="records"):
            bill_id = self._coerce_optional_text(row.get("billId")) or self._coerce_optional_text(
                row.get("bill_id")
            )
            party_name = self._coerce_optional_text(row.get("partyName"))
            if not bill_id or not party_name:
                continue

            rows.append(
                {
                    "bill_id": bill_id,
                    "party_name": party_name,
                    "votes_for_count": self._safe_to_int(
                        row.get("voteForCount")
                        if row.get("voteForCount") is not None
                        else row.get("votes_for_count")
                    ),
                }
            )
        return rows

    def update_bills_data(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        age: str | None = None,
    ) -> Dict[str, Any]:
        fetched = self.fetch_bills_data_step(start_date=start_date, end_date=end_date, age=age)
        if fetched["fetched"] == 0:
            return {"mode": self.mode, "fetched": 0, "upserted": 0}

        processed = self.process_bills_data_step(fetched["artifact_path"])
        result = self.upsert_bills_data_step(processed["artifact_path"])
        return {
            "mode": self.mode,
            "fetched": fetched["fetched"],
            "processed": processed["processed"],
            "upserted": result["upserted"],
        }

    def _persist_bill_rows(
        self,
        rows: List[Dict[str, Any]],
        *,
        source_name: str,
        metadata: Dict[str, Any],
    ) -> int:
        if not rows or self.mode == "dry_run":
            return 0

        db = self._build_db_manager(self.mode)
        db.insert_bill_info(rows)
        max_propose_date = max((row.get("propose_date") for row in rows if row.get("propose_date")), default=None)
        db.upsert_ingest_checkpoint(
            source_name=source_name,
            assembly_number=self._safe_to_int(rows[0].get("assembly_number"), default=22),
            last_reference_date=max_propose_date,
            metadata=metadata,
        )
        return len(rows)

    def fetch_bills_data_step(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        age: str | None = None,
    ) -> Dict[str, Any]:
        end_date = end_date or self._default_end_date()
        age = str(age or "22")

        if start_date is None and self.mode != "dry_run":
            db = self._build_db_manager(self.mode)
            checkpoint = db.get_ingest_checkpoint("bill_ingest", int(age))
            if checkpoint and checkpoint.get("last_reference_date"):
                start_date = checkpoint["last_reference_date"].strftime("%Y-%m-%d")
            else:
                start_date = self._default_bill_start_date()
        else:
            start_date = start_date or self._default_bill_start_date()

        print(f"[bill_ingest.fetch] mode={self.mode} start={start_date} end={end_date} age={age}")

        fetcher = DataFetcher()
        df_candidates = fetcher.discover_bill_candidates(start_date=start_date, end_date=end_date, age=age)
        if df_candidates is None or df_candidates.empty:
            print("[bill_ingest.fetch] 수집된 법안 후보가 없습니다.")
            return {"mode": self.mode, "fetched": 0, "artifact_path": None}

        if "bill_id" in df_candidates.columns:
            df_candidates = df_candidates.drop_duplicates(subset=["bill_id"], keep="last")

        candidate_rows = self._build_bill_rows(df_candidates)
        discovered = self._persist_bill_rows(
            candidate_rows,
            source_name="bill_discovery",
            metadata={"discovered": len(candidate_rows)},
        )

        artifact_path = self._write_artifact("bill_ingest_fetch", df_candidates.to_dict(orient="records"))
        return {
            "mode": self.mode,
            "fetched": len(df_candidates),
            "discovered": discovered,
            "artifact_path": artifact_path,
        }

    def process_bills_data_step(self, artifact_path: str) -> Dict[str, Any]:
        print(f"[bill_ingest.process] mode={self.mode} artifact={artifact_path}")

        records = self._read_artifact(artifact_path)
        if not records:
            print("[bill_ingest.process] 처리할 법안이 없습니다.")
            return {"mode": self.mode, "processed": 0, "artifact_path": None}

        df_candidates = pd.DataFrame(records)
        fetcher = DataFetcher()
        hydrate_age = None
        if not df_candidates.empty and "assemblyNumber" in df_candidates.columns:
            hydrate_age = self._coerce_optional_text(df_candidates.iloc[0].get("assemblyNumber"))

        df_bills = fetcher.hydrate_bill_candidates(df_candidates, age=hydrate_age)
        if df_bills is None or df_bills.empty:
            print("[bill_ingest.process] hydrate 결과가 없습니다.")
            return {"mode": self.mode, "processed": 0, "artifact_path": None}

        processor = DataProcessor(fetcher)
        df_congressman_bills = processor.process_congressman_bills(df_bills.copy())

        if (
            df_congressman_bills is not None
            and not df_congressman_bills.empty
            and "bill_id" in df_congressman_bills.columns
        ):
            merge_cols = [
                column
                for column in [
                    "bill_id",
                    "bill_name",
                    "proposers",
                    "publicProposerIdList",
                    "rstProposerIdList",
                ]
                if column in df_congressman_bills.columns
            ]
            if len(merge_cols) > 1:
                df_map = df_congressman_bills[merge_cols].drop_duplicates(subset=["bill_id"], keep="last")
                df_bills = df_bills.merge(df_map, on="bill_id", how="left", suffixes=("", "_enriched"))
                for column in ["bill_name", "proposers", "publicProposerIdList", "rstProposerIdList"]:
                    enriched = f"{column}_enriched"
                    if enriched in df_bills.columns:
                        df_bills[column] = df_bills[enriched].where(
                            df_bills[enriched].notna(), df_bills.get(column)
                        )
                        df_bills.drop(columns=[enriched], inplace=True)

        rows = self._build_bill_rows(df_bills)
        processed_artifact_path = self._write_artifact("bill_ingest_process", rows)
        return {
            "mode": self.mode,
            "processed": len(rows),
            "artifact_path": processed_artifact_path,
        }

    def upsert_bills_data_step(self, artifact_path: str) -> Dict[str, Any]:
        print(f"[bill_ingest.upsert] mode={self.mode} artifact={artifact_path}")

        rows = self._read_artifact(artifact_path)
        if not rows:
            print("[bill_ingest.upsert] 적재할 법안이 없습니다.")
            return {"mode": self.mode, "upserted": 0}

        if self.mode == "dry_run":
            print(f"[bill_ingest.upsert] [DRY_RUN] {len(rows)}개의 법안을 수집했으나 DB에 반영하지 않습니다.")
            return {"mode": self.mode, "upserted": 0}

        upserted = self._persist_bill_rows(
            rows,
            source_name="bill_ingest",
            metadata={"upserted": len(rows)},
        )
        print(f"[bill_ingest.upsert] [{self.mode}] upserted={upserted}")
        return {"mode": self.mode, "upserted": upserted}

    def update_lawmakers_data(self) -> Dict[str, Any]:
        print(f"[bill_status_sync] step=update_lawmakers_data mode={self.mode}")

        fetcher = DataFetcher()
        df_lawmakers = fetcher.fetch_lawmakers_data()
        if df_lawmakers is None or df_lawmakers.empty:
            print("[bill_status_sync] 수집된 의원 데이터가 없습니다.")
            return {"step": "update_lawmakers_data", "mode": self.mode, "count": 0}

        df_lawmakers = df_lawmakers.drop(
            columns=[
                "ENG_NM",
                "HJ_NM",
                "BTH_GBN_NM",
                "ELECT_GBN_NM",
                "STAFF",
                "CMITS",
                "SECRETARY",
                "SECRETARY2",
                "JOB_RES_NM",
            ],
            errors="ignore",
        )

        if "UNITS" in df_lawmakers.columns:
            extracted = df_lawmakers["UNITS"].astype(str).str.extract(r"(\d+)(?=\D*$)")[0]
            df_lawmakers["UNITS"] = pd.to_numeric(extracted, errors="coerce").fillna(22).astype(int)

        df_lawmakers.rename(
            columns={
                "MONA_CD": "congressmanId",
                "HG_NM": "congressmanName",
                "CMIT_NM": "commits",
                "POLY_NM": "partyName",
                "REELE_GBN_NM": "elected",
                "HOMEPAGE": "homepage",
                "ORIG_NM": "district",
                "UNITS": "assemblyNumber",
                "BTH_DATE": "congressmanBirth",
                "SEX_GBN_NM": "sex",
                "E_MAIL": "email",
                "ASSEM_ADDR": "congressmanOffice",
                "TEL_NO": "congressmanTelephone",
                "MEM_TITLE": "briefHistory",
            },
            inplace=True,
        )

        rows = self._build_lawmaker_rows(df_lawmakers)
        if self.mode != "dry_run" and rows:
            db = self._build_db_manager(self.mode)
            db.update_lawmaker_info(rows)

        print(f"[bill_status_sync] lawmakers count={len(rows)}")
        return {"step": "update_lawmakers_data", "mode": self.mode, "count": len(rows)}

    def update_bills_timeline(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        age: str | None = None,
    ) -> Dict[str, Any]:
        print(f"[bill_status_sync] step=update_bills_timeline mode={self.mode}")

        db = None if self.mode == "dry_run" else self._build_db_manager(self.mode)
        if start_date is None:
            if self.mode == "dry_run":
                start_date = self._default_sync_start_date()
            else:
                latest_date = db.get_latest_timeline_date()
                start_date = (
                    latest_date.strftime("%Y-%m-%d")
                    if latest_date
                    else self._default_sync_start_date()
                )
        end_date = end_date or self._default_end_date()
        age = age or os.getenv("AGE")

        fetcher = DataFetcher()
        df_stage = fetcher.fetch_bills_timeline(start_date=start_date, end_date=end_date, age=age)
        if df_stage is None or df_stage.empty:
            print("[bill_status_sync] 수집된 타임라인 데이터가 없습니다.")
            return {"step": "update_bills_timeline", "mode": self.mode, "count": 0, "duplicate": 0, "not_found": 0}

        keep_cols = [column for column in ["DT", "BILL_ID", "STAGE", "COMMITTEE"] if column in df_stage.columns]
        df_stage = df_stage[keep_cols].copy()
        df_stage.rename(
            columns={"DT": "statusUpdateDate", "BILL_ID": "billId", "STAGE": "stage", "COMMITTEE": "committee"},
            inplace=True,
        )

        rows = self._build_bill_stage_rows(df_stage)
        result = {"duplicate_bill": [], "not_found_bill": []}
        if self.mode != "dry_run" and rows:
            result = db.update_bill_stage(rows)

        print(
            f"[bill_status_sync] stage count={len(rows)} duplicate={len(result['duplicate_bill'])} "
            f"not_found={len(result['not_found_bill'])}"
        )
        return {
            "step": "update_bills_timeline",
            "mode": self.mode,
            "count": len(rows),
            "duplicate": len(result["duplicate_bill"]),
            "not_found": len(result["not_found_bill"]),
        }

    def update_bills_result(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        age: str | None = None,
    ) -> Dict[str, Any]:
        print(f"[bill_status_sync] step=update_bills_result mode={self.mode}")

        start_date = start_date or self._default_sync_start_date()
        end_date = end_date or self._default_end_date()
        age = age or os.getenv("AGE")

        fetcher = DataFetcher()
        df_result = fetcher.fetch_bills_result(start_date=start_date, end_date=end_date, age=age)
        if df_result is None or df_result.empty:
            print("[bill_status_sync] 수집된 처리결과 데이터가 없습니다.")
            return {"step": "update_bills_result", "mode": self.mode, "count": 0}

        keep_cols = [column for column in ["BILL_ID", "PROC_RESULT_CD"] if column in df_result.columns]
        df_result = df_result[keep_cols].copy()
        df_result.rename(columns={"BILL_ID": "billId", "PROC_RESULT_CD": "billProposeResult"}, inplace=True)

        rows = self._build_bill_result_rows(df_result)
        if self.mode != "dry_run" and rows:
            db = self._build_db_manager(self.mode)
            db.update_bill_result(rows)

        print(f"[bill_status_sync] result count={len(rows)}")
        return {"step": "update_bills_result", "mode": self.mode, "count": len(rows)}

    def update_bills_vote(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        age: str | None = None,
    ) -> Dict[str, Any]:
        print(f"[bill_status_sync] step=update_bills_vote mode={self.mode}")

        start_date = start_date or self._default_sync_start_date()
        end_date = end_date or self._default_end_date()
        age = age or os.getenv("AGE")

        fetcher = DataFetcher()
        df_vote_raw = fetcher.fetch_bills_vote(start_date=start_date, end_date=end_date, age=age)
        if df_vote_raw is None or df_vote_raw.empty:
            print("[bill_status_sync] 수집된 표결 결과 데이터가 없습니다.")
            return {"step": "update_bills_vote", "mode": self.mode, "vote_count": 0, "party_count": 0}

        df_vote_party = fetcher.fetch_vote_party(df_vote=df_vote_raw, start_date=start_date, end_date=end_date, age=age)

        keep_cols = [
            column
            for column in ["BILL_ID", "VOTE_TCNT", "YES_TCNT", "NO_TCNT", "BLANK_TCNT"]
            if column in df_vote_raw.columns
        ]
        df_vote = df_vote_raw[keep_cols].copy()
        if "VOTE_TCNT" in df_vote.columns:
            df_vote.dropna(subset=["VOTE_TCNT"], inplace=True)
        df_vote.fillna(0, inplace=True)
        df_vote.rename(
            columns={
                "BILL_ID": "billId",
                "VOTE_TCNT": "totalVoteCount",
                "YES_TCNT": "voteForCount",
                "NO_TCNT": "voteAgainstCount",
                "BLANK_TCNT": "abstentionCount",
            },
            inplace=True,
        )

        vote_rows = self._build_vote_rows(df_vote)
        party_rows = (
            self._build_vote_party_rows(df_vote_party)
            if df_vote_party is not None and not df_vote_party.empty
            else []
        )

        if self.mode != "dry_run":
            db = self._build_db_manager(self.mode)
            if vote_rows:
                db.insert_vote_record(vote_rows)
            if party_rows:
                db.insert_vote_party(party_rows)

        print(f"[bill_status_sync] vote_count={len(vote_rows)} party_count={len(party_rows)}")
        return {
            "step": "update_bills_vote",
            "mode": self.mode,
            "vote_count": len(vote_rows),
            "party_count": len(party_rows),
        }
