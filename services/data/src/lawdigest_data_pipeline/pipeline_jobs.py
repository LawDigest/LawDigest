from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import pandas as pd


def _normalize_execution_mode(execution_mode: str | None) -> str:
    normalized = str(execution_mode or "dry_run").strip().lower().replace("-", "_")

    alias_map = {
        "dry_run": "dry_run",
        "dryrun": "dry_run",
        "test": "test",
        "test_db": "test",
        "testdb": "test",
        "prod": "prod",
        "remote": "prod",
        "db": "prod",
    }

    if normalized not in alias_map:
        raise ValueError("execution_mode must be one of dry_run, test_db/test, or prod")

    return alias_map[normalized]


def _coerce_optional_text(value: object) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def _safe_to_int(value: object, default: int = 0) -> int:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return default

    try:
        return int(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return default


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


def _normalize_bill_proposer_kind(proposer_kind: object) -> str:
    normalized = str(proposer_kind or "").strip()
    if normalized == "의원":
        return "CONGRESSMAN"
    if normalized == "위원장":
        return "CHAIRMAN"
    if normalized == "정부":
        return "GOVERNMENT"
    return "CONGRESSMAN"


def _build_db_manager(execution_mode: str):
    from lawdigest_ai.db import get_prod_db_config, get_test_db_config
    from .DatabaseManager import DatabaseManager

    db_config = get_prod_db_config() if execution_mode == "prod" else get_test_db_config()
    return DatabaseManager(
        host=db_config["host"],
        port=db_config["port"],
        username=db_config["user"],
        password=db_config["password"],
        database=db_config["database"],
    )


def _build_bill_rows(df_bills: pd.DataFrame) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for row in df_bills.to_dict(orient="records"):
        bill_id = _coerce_optional_text(row.get("bill_id"))
        if not bill_id:
            continue

        rows.append(
            {
                "bill_id": bill_id,
                "bill_name": _coerce_optional_text(row.get("bill_name")),
                "committee": _coerce_optional_text(row.get("committee")),
                "gpt_summary": _coerce_optional_text(row.get("gpt_summary")),
                "propose_date": _coerce_optional_text(row.get("proposeDate")),
                "summary": _coerce_optional_text(row.get("summary")),
                "stage": _coerce_optional_text(row.get("stage")),
                "proposers": _coerce_optional_text(row.get("proposers")),
                "bill_pdf_url": _coerce_optional_text(row.get("billPdfUrl")) or _coerce_optional_text(row.get("bill_link")),
                "brief_summary": _coerce_optional_text(row.get("brief_summary")),
                "summary_tags": row.get("summary_tags"),
                "bill_number": _safe_to_int(row.get("billNumber")),
                "bill_link": _coerce_optional_text(row.get("bill_link")),
                "bill_result": _coerce_optional_text(row.get("billResult")),
                "proposer_kind": _normalize_bill_proposer_kind(row.get("proposer_kind") or row.get("proposerKind")),
                "public_proposer_ids": _coerce_string_list(row.get("publicProposerIdList")),
                "rst_proposer_ids": _coerce_string_list(row.get("rstProposerIdList")),
            }
        )

    return rows


def _build_lawmaker_rows(df_lawmakers: pd.DataFrame) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for row in df_lawmakers.to_dict(orient="records"):
        assembly_number = _safe_to_int(row.get("assemblyNumber"), default=22)
        congressman_id = _coerce_optional_text(row.get("congressmanId"))
        if not congressman_id:
            continue

        rows.append(
            {
                "congressman_id": congressman_id,
                "name": _coerce_optional_text(row.get("congressmanName")),
                "party_name": _coerce_optional_text(row.get("partyName")),
                "district": _coerce_optional_text(row.get("district")),
                "elect_sort": _coerce_optional_text(row.get("electSort")),
                "commits": _coerce_optional_text(row.get("commits")),
                "elected": _coerce_optional_text(row.get("elected")),
                "homepage": _coerce_optional_text(row.get("homepage")),
                "congressman_image_url": _coerce_optional_text(row.get("congressmanImage"))
                or f"/congressman/{assembly_number}/{congressman_id}.jpg",
                "email": _coerce_optional_text(row.get("email")),
                "sex": _coerce_optional_text(row.get("sex")),
                "congressman_age": _coerce_optional_text(row.get("congressmanBirth")),
                "congressman_office": _coerce_optional_text(row.get("congressmanOffice")),
                "congressman_telephone": _coerce_optional_text(row.get("congressmanTelephone")),
                "brief_history": _coerce_optional_text(row.get("briefHistory")),
            }
        )

    return rows


def _build_bill_stage_rows(df_stage: pd.DataFrame) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for row in df_stage.to_dict(orient="records"):
        rows.append(
            {
                "bill_id": _coerce_optional_text(row.get("billId")) or _coerce_optional_text(row.get("bill_id")),
                "stage": _coerce_optional_text(row.get("stage")),
                "committee": _coerce_optional_text(row.get("committee")),
                "status_update_date": _coerce_optional_text(row.get("statusUpdateDate"))
                or _coerce_optional_text(row.get("status_update_date"))
                or _coerce_optional_text(row.get("DT")),
            }
        )
    return rows


def _build_bill_result_rows(df_result: pd.DataFrame) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for row in df_result.to_dict(orient="records"):
        rows.append(
            {
                "bill_id": _coerce_optional_text(row.get("billId")) or _coerce_optional_text(row.get("bill_id")),
                "bill_result": _coerce_optional_text(row.get("billProposeResult"))
                or _coerce_optional_text(row.get("bill_result")),
            }
        )
    return rows


def _build_vote_rows(df_vote: pd.DataFrame) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for row in df_vote.to_dict(orient="records"):
        rows.append(
            {
                "bill_id": _coerce_optional_text(row.get("billId")) or _coerce_optional_text(row.get("bill_id")),
                "votes_for_count": _safe_to_int(row.get("voteForCount") if row.get("voteForCount") is not None else row.get("votes_for_count")),
                "votes_againt_count": _safe_to_int(row.get("voteAgainstCount") if row.get("voteAgainstCount") is not None else row.get("votes_againt_count")),
                "abstention_count": _safe_to_int(row.get("abstentionCount") if row.get("abstentionCount") is not None else row.get("abstention_count")),
                "total_vote_count": _safe_to_int(row.get("totalVoteCount") if row.get("totalVoteCount") is not None else row.get("total_vote_count")),
            }
        )
    return rows


def _build_vote_party_rows(df_vote_party: pd.DataFrame) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for row in df_vote_party.to_dict(orient="records"):
        bill_id = _coerce_optional_text(row.get("billId")) or _coerce_optional_text(row.get("bill_id"))
        party_name = _coerce_optional_text(row.get("partyName"))
        if not bill_id or not party_name:
            continue

        rows.append(
            {
                "bill_id": bill_id,
                "party_name": party_name,
                "votes_for_count": _safe_to_int(row.get("voteForCount") if row.get("voteForCount") is not None else row.get("votes_for_count")),
            }
        )
    return rows


def run_bill_ingest_job(
    start_date: str | None = None,
    end_date: str | None = None,
    age: str | None = None,
    execution_mode: str = "dry_run",
) -> Dict[str, Any]:
    from src.lawdigest_data_pipeline.DataFetcher import DataFetcher
    from src.lawdigest_data_pipeline.DataProcessor import DataProcessor

    mode = _normalize_execution_mode(execution_mode)
    today = pd.Timestamp.now().strftime("%Y-%m-%d")
    start_date = start_date or today
    end_date = end_date or today
    age = str(age or "22")

    print(f"[bill_ingest] mode={mode} start={start_date} end={end_date} age={age}")

    fetcher = DataFetcher()
    df_bills = fetcher.fetch_bills_data(start_date=start_date, end_date=end_date, age=age)

    if df_bills is None or df_bills.empty:
        print("[bill_ingest] 수집된 법안이 없습니다.")
        return {"mode": mode, "fetched": 0, "upserted": 0}

    if "bill_id" in df_bills.columns:
        df_bills = df_bills.drop_duplicates(subset=["bill_id"], keep="last")

    processor = DataProcessor(fetcher)
    df_cong = processor.process_congressman_bills(df_bills.copy())

    if df_cong is not None and not df_cong.empty and "bill_id" in df_cong.columns:
        merge_cols = [
            c
            for c in ["bill_id", "bill_name", "proposers", "publicProposerIdList", "rstProposerIdList"]
            if c in df_cong.columns
        ]
        if len(merge_cols) > 1:
            df_map = df_cong[merge_cols].drop_duplicates(subset=["bill_id"], keep="last")
            df_bills = df_bills.merge(df_map, on="bill_id", how="left", suffixes=("", "_enriched"))
            for col in ["bill_name", "proposers", "publicProposerIdList", "rstProposerIdList"]:
                enriched = f"{col}_enriched"
                if enriched in df_bills.columns:
                    df_bills[col] = df_bills[enriched].where(df_bills[enriched].notna(), df_bills.get(col))
                    df_bills.drop(columns=[enriched], inplace=True)

    mapped_rows = _build_bill_rows(df_bills)
    if not mapped_rows:
        print("[bill_ingest] 수집된 법안이 없습니다.")
        return {"mode": mode, "fetched": 0, "upserted": 0}

    if mode == "dry_run":
        print(f"[bill_ingest] [DRY_RUN] {len(mapped_rows)}개의 법안을 수집했으나 DB에 반영하지 않습니다.")
        return {"mode": mode, "fetched": len(mapped_rows), "upserted": 0}

    db = _build_db_manager(mode)
    db.insert_bill_info(mapped_rows)
    print(f"[bill_ingest] [{mode}] fetched={len(mapped_rows)} upserted={len(mapped_rows)}")
    return {"mode": mode, "fetched": len(mapped_rows), "upserted": len(mapped_rows)}


def run_manual_bill_collect_job(
    start_date: str | None = None,
    end_date: str | None = None,
    age: str | None = None,
    execution_mode: str = "prod",
) -> Dict[str, Any]:
    return run_bill_ingest_job(
        start_date=start_date,
        end_date=end_date,
        age=age,
        execution_mode=execution_mode,
    )


def run_bill_status_sync_step(
    method_name: str,
    start_date: str | None = None,
    end_date: str | None = None,
    age: str | None = None,
    execution_mode: str = "dry_run",
) -> Dict[str, Any]:
    from src.lawdigest_data_pipeline.DataFetcher import DataFetcher

    mode = _normalize_execution_mode(execution_mode)
    print(f"[bill_status_sync] step={method_name} mode={mode}")

    fetcher = DataFetcher()
    db = None if mode == "dry_run" else _build_db_manager(mode)

    if method_name == "update_lawmakers_data":
        df_lawmakers = fetcher.fetch_lawmakers_data()
        if df_lawmakers is None or df_lawmakers.empty:
            print("[bill_status_sync] 수집된 의원 데이터가 없습니다.")
            return {"step": method_name, "mode": mode, "count": 0}

        columns_to_drop = [
            "ENG_NM",
            "HJ_NM",
            "BTH_GBN_NM",
            "ELECT_GBN_NM",
            "STAFF",
            "CMITS",
            "SECRETARY",
            "SECRETARY2",
            "JOB_RES_NM",
        ]
        df_lawmakers = df_lawmakers.drop(columns=columns_to_drop, errors="ignore")

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

        rows = _build_lawmaker_rows(df_lawmakers)
        if mode != "dry_run" and rows:
            db.update_lawmaker_info(rows)
        print(f"[bill_status_sync] lawmakers count={len(rows)}")
        return {"step": method_name, "mode": mode, "count": len(rows)}

    if method_name == "update_bills_timeline":
        if start_date is None:
            if mode == "dry_run":
                start_date = (pd.Timestamp.now() - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
            else:
                latest_date = db.get_latest_timeline_date()
                start_date = (
                    latest_date.strftime("%Y-%m-%d")
                    if latest_date
                    else (pd.Timestamp.now() - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
                )
        if end_date is None:
            end_date = pd.Timestamp.now().strftime("%Y-%m-%d")
        if age is None:
            age = os.getenv("AGE")

        df_stage = fetcher.fetch_bills_timeline(start_date=start_date, end_date=end_date, age=age)
        if df_stage is None or df_stage.empty:
            print("[bill_status_sync] 수집된 타임라인 데이터가 없습니다.")
            return {"step": method_name, "mode": mode, "count": 0, "duplicate": 0, "not_found": 0}

        keep_cols = [c for c in ["DT", "BILL_ID", "STAGE", "COMMITTEE"] if c in df_stage.columns]
        df_stage = df_stage[keep_cols].copy()
        df_stage.rename(
            columns={"DT": "statusUpdateDate", "BILL_ID": "billId", "STAGE": "stage", "COMMITTEE": "committee"},
            inplace=True,
        )
        rows = _build_bill_stage_rows(df_stage)
        result = {"duplicate_bill": [], "not_found_bill": []}
        if mode != "dry_run" and rows:
            result = db.update_bill_stage(rows)
        print(
            f"[bill_status_sync] stage count={len(rows)} duplicate={len(result['duplicate_bill'])} "
            f"not_found={len(result['not_found_bill'])}"
        )
        return {
            "step": method_name,
            "mode": mode,
            "count": len(rows),
            "duplicate": len(result["duplicate_bill"]),
            "not_found": len(result["not_found_bill"]),
        }

    if method_name == "update_bills_result":
        if start_date is None:
            start_date = (pd.Timestamp.now() - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        if end_date is None:
            end_date = pd.Timestamp.now().strftime("%Y-%m-%d")
        if age is None:
            age = os.getenv("AGE")

        df_result = fetcher.fetch_bills_result(start_date=start_date, end_date=end_date, age=age)
        if df_result is None or df_result.empty:
            print("[bill_status_sync] 수집된 처리결과 데이터가 없습니다.")
            return {"step": method_name, "mode": mode, "count": 0}

        keep_cols = [c for c in ["BILL_ID", "PROC_RESULT_CD"] if c in df_result.columns]
        df_result = df_result[keep_cols].copy()
        df_result.rename(columns={"BILL_ID": "billId", "PROC_RESULT_CD": "billProposeResult"}, inplace=True)
        rows = _build_bill_result_rows(df_result)
        if mode != "dry_run" and rows:
            db.update_bill_result(rows)
        print(f"[bill_status_sync] result count={len(rows)}")
        return {"step": method_name, "mode": mode, "count": len(rows)}

    if method_name == "update_bills_vote":
        if start_date is None:
            start_date = (pd.Timestamp.now() - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        if end_date is None:
            end_date = pd.Timestamp.now().strftime("%Y-%m-%d")
        if age is None:
            age = os.getenv("AGE")

        df_vote_raw = fetcher.fetch_bills_vote(start_date=start_date, end_date=end_date, age=age)
        if df_vote_raw is None or df_vote_raw.empty:
            print("[bill_status_sync] 수집된 표결 결과 데이터가 없습니다.")
            return {"step": method_name, "mode": mode, "vote_count": 0, "party_count": 0}

        df_vote_party = fetcher.fetch_vote_party(df_vote=df_vote_raw, start_date=start_date, end_date=end_date, age=age)

        df_vote = df_vote_raw.copy()
        keep_cols = [c for c in ["BILL_ID", "VOTE_TCNT", "YES_TCNT", "NO_TCNT", "BLANK_TCNT"] if c in df_vote.columns]
        df_vote = df_vote[keep_cols].copy()
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

        vote_rows = _build_vote_rows(df_vote)
        party_rows = _build_vote_party_rows(df_vote_party) if df_vote_party is not None and not df_vote_party.empty else []

        if mode != "dry_run" and vote_rows:
            db.insert_vote_record(vote_rows)
        if mode != "dry_run" and party_rows:
            db.insert_vote_party(party_rows)

        print(f"[bill_status_sync] vote_count={len(vote_rows)} party_count={len(party_rows)}")
        return {
            "step": method_name,
            "mode": mode,
            "vote_count": len(vote_rows),
            "party_count": len(party_rows),
        }

    raise ValueError(f"Unsupported sync step: {method_name}")
