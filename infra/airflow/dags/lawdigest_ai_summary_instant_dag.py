# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import sys

import pendulum

from airflow.models.dag import DAG
from airflow.models.param import Param
from airflow.operators.python import PythonOperator


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "y", "yes", "on"}
    return False


def run_instant_ai_summary(**context):
    params = context.get("params", {})

    bill_json = params.get("bill_json")
    if bill_json:
        try:
            bill_data = json.loads(bill_json)
        except json.JSONDecodeError as exc:
            raise ValueError(f"bill_json이 유효한 JSON이 아닙니다: {exc}") from exc
    else:
        bill_data = {
            "bill_id": params.get("bill_id"),
            "bill_name": params.get("bill_name"),
            "summary": params.get("summary"),
            "proposers": params.get("proposers"),
            "proposer_kind": params.get("proposer_kind"),
            "proposeDate": params.get("propose_date"),
            "stage": params.get("stage"),
        }

    if not bill_data.get("bill_id"):
        raise ValueError("bill_id는 필수입니다.")
    if not bill_data.get("summary"):
        raise ValueError("summary는 필수입니다.")

    project_root = "/opt/airflow/project"
    if project_root not in sys.path:
        sys.path.append(project_root)

    # 파서 단계 import 실패를 피하기 위해 실행 시점에 import
    from src.lawdigest_data_pipeline.WorkFlowManager import WorkFlowManager

    workflow = WorkFlowManager(mode="db")
    summarized_rows = workflow.summarize_bill_step(bill_data)

    if _as_bool(params.get("upsert", True)):
        workflow.upsert_bill_step(summarized_rows)

    result = summarized_rows[0] if summarized_rows else {}
    print(json.dumps(result, ensure_ascii=False))
    return result


with DAG(
    dag_id="lawdigest_ai_summary_instant_dag",
    schedule=None,
    start_date=pendulum.datetime(2024, 1, 1, tz="Asia/Seoul"),
    catchup=False,
    tags=["lawdigest", "ai-summary", "instant"],
    params={
        "bill_json": Param(
            "",
            type="string",
            title="법안 JSON",
            description="단일 법안 payload(JSON 문자열). 설정 시 아래 개별 필드는 무시됩니다.",
        ),
        "bill_id": Param("", type="string", title="법안 ID"),
        "bill_name": Param("", type="string", title="법안명"),
        "summary": Param("", type="string", title="원문 요약"),
        "proposers": Param("", type="string", title="발의자"),
        "proposer_kind": Param("CONGRESSMAN", type="string", title="발의자 구분"),
        "propose_date": Param("", type="string", title="발의일(YYYY-MM-DD)"),
        "stage": Param("", type="string", title="단계"),
        "upsert": Param(
            True,
            type="boolean",
            title="DB upsert",
            description="True면 요약 결과를 Bill 테이블에 즉시 반영",
        ),
    },
    doc_md="""
    ### Lawdigest AI Summary 즉시 실행 DAG

    - 스케줄링 없음 (`schedule=None`)
    - 수동 트리거로 단일 법안을 즉시 요약합니다.
    - `upsert=True`이면 요약 결과를 DB에 즉시 반영합니다.
    """,
) as dag:
    instant_ai_summary = PythonOperator(
        task_id="instant_ai_summary",
        python_callable=run_instant_ai_summary,
    )

