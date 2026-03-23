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
    mode = params.get("execution_mode") or "dry_run"
    print(f"[ai-summary-instant] Current Mode: {mode}")

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
    from lawdigest_ai.processor.instant_summarizer import summarize_single_bill

    result = summarize_single_bill(bill_data)

    if mode != "dry_run" and _as_bool(params.get("upsert", True)):
        from lawdigest_ai.db import update_bill_summary

        if mode == "prod":
            print("[ai-summary-instant] Using PRODUCTION database")
        else:
            print("[ai-summary-instant] Using TEST database")

        update_bill_summary(
            bill_id=result["bill_id"],
            brief_summary=result.get("brief_summary"),
            gpt_summary=result.get("gpt_summary"),
            summary_tags=result.get("summary_tags"),
            mode=mode,
        )
        print(f"[ai-summary-instant] [{mode}] DB upsert completed.")
    else:
        print(f"[ai-summary-instant] [{mode}] DB upsert skipped.")

    print(json.dumps(result, ensure_ascii=False, default=str))
    return result


with DAG(
    dag_id="lawdigest_ai_summary_instant_dag",
    schedule=None,
    start_date=pendulum.datetime(2024, 1, 1, tz="Asia/Seoul"),
    catchup=False,
    tags=["lawdigest", "ai-summary", "instant"],
    params={
        "execution_mode": Param(
            "dry_run",
            type="string",
            enum=["dry_run", "test", "prod"],
            title="실행 모드",
            description="dry_run: DB 반영 안 함, test: 테스트 DB 사용, prod: 운영 DB 사용",
        ),
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
            description="True면 요약 결과를 Bill 테이블에 즉시 반영 (dry_run 모드에서는 무시됨)",
        ),
    },
    doc_md="""
    ## ⚡ Lawdigest AI Summary 즉시 실행 (Single)

    특정 법안 하나에 대해 즉시 AI 요약을 생성하고 확인하거나 DB에 반영하는 도구 성격의 DAG입니다.

    ### 🚀 주요 기능
    1. **단일 법안 요약**: 입력받은 법안 데이터(ID, 이름, 요약 원문 등)를 기반으로 즉시 OpenAI 요약을 수행합니다.
    2. **결과 확인**: 요약된 `brief_summary`, `gpt_summary`, `tags`를 로그와 XCom 결과로 즉시 확인할 수 있습니다.
    3. **선택적 DB 반영**: `upsert=True` 파라미터를 통해 결과를 DB에 즉시 업데이트할 수 있습니다.

    ### ⚙️ 실행 모드 (Execution Mode)
    - `dry_run` (기본값): AI 요약까지만 수행하고 **DB에는 절대 저장하지 않습니다.** (단순 결과 테스트용)
    - `test`: 요약 결과를 테스트 데이터베이스의 `Bill` 테이블에 반영합니다.
    - `prod`: 요약 결과를 실제 운영 데이터베이스에 즉시 업데이트합니다.

    ### 📅 파라미터 가이드
    - `execution_mode`: 실행 환경 및 실제 DB 반영 여부 선택
    - `bill_json`: (권장) 법안 전체 데이터를 JSON 문자열로 입력
    - `bill_id` ~ `stage`: 개별 필드로 법안 데이터를 직접 입력 (bill_json이 없을 때 사용)
    - `upsert`: 결과를 DB에 업데이트할지 여부 (기본값: True, dry_run 시 무시됨)

    ---
    *참고: 특정 법안의 요약 내용이 마음에 들지 않아 다시 생성하고 싶을 때 유용합니다.*
    """,
) as dag:
    instant_ai_summary = PythonOperator(
        task_id="instant_ai_summary",
        python_callable=run_instant_ai_summary,
    )
