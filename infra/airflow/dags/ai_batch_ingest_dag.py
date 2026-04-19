# -*- coding: utf-8 -*-
from __future__ import annotations

import sys

import pendulum

from airflow.models.dag import DAG
from airflow.models.param import Param
from airflow.operators.python import PythonOperator


def poll_and_ingest_batch_results(**context):
    params = context.get("params", {})
    mode = params.get("execution_mode") or "dry_run"
    provider = params.get("provider") or "all"

    print(f"[batch-ingest] Current Mode: {mode}, Provider: {provider}")

    project_root = "/opt/airflow/project"
    if project_root not in sys.path:
        sys.path.append(project_root)

    from lawdigest_ai.processor.batch_ingest import ingest_batch_results

    return ingest_batch_results(
        max_jobs=int(params.get("max_jobs") or 10),
        mode=mode,
        provider=provider,
    )


with DAG(
    dag_id="ai_batch_ingest_dag",
    schedule="*/10 * * * *",
    start_date=pendulum.datetime(2024, 1, 1, tz="Asia/Seoul"),
    catchup=False,
    tags=["lawdigest", "ai-summary", "batch-ingest"],
    params={
        "execution_mode": Param(
            "dry_run",
            type="string",
            enum=["dry_run", "test", "prod"],
            title="실행 모드",
            description="dry_run: 상태 조회만 하고 DB 업데이트 안 함, test: 테스트 DB 사용, prod: 운영 DB 사용",
        ),
        "max_jobs": Param(20, type="integer", title="한 번에 조회할 batch 개수"),
        "provider": Param(
            "all",
            type="string",
            enum=["all", "openai", "gemini"],
            title="배치 제공자",
            description="all이면 모든 provider를, 그 외에는 선택한 provider만 적재합니다.",
        ),
    },
    doc_md="""
    ## 📥 Lawdigest AI Batch 결과 수신 및 반영

    provider-aware Batch API로 요청했던 작업의 상태를 확인하고, 완료된 요약 결과를 DB에 자동으로 업데이트하는 DAG입니다.

    ### 🚀 주요 기능
    1. **Batch 상태 모니터링**: 진행 중인(`SUBMITTED`, `IN_PROGRESS` 등) 작업의 상태를 provider 서버에서 조회합니다.
    2. **결과 다운로드**: 작업 상태가 `COMPLETED`이면 요약 결과(JSONL)를 다운로드하여 파싱합니다.
    3. **DB 최종 업데이트**: 파싱된 요약(`gpt_summary`, `brief_summary`, `tags`)을 `Bill` 테이블에 영구적으로 반영합니다.
    4. **작업 완료 처리**: 상태 테이블(`ai_batch_jobs`, `ai_batch_items`)의 정보를 최종 상태로 업데이트합니다.

    ### ⚙️ 실행 모드 (Execution Mode)
    - `dry_run` (기본값): 작업 상태만 provider에서 조회하여 로그로 표시하고, **실제 DB 업데이트는 수행하지 않습니다.**
    - `test`: 테스트용 DB 설정을 사용하여 테스트 데이터를 업데이트합니다.
    - `prod`: 실제 서비스가 운영 중인 DB에 요약 결과를 즉시 반영합니다.

    ### 📅 파라미터 가이드
    - `execution_mode`: 실행 환경 및 실제 DB 반영 여부 선택
    - `max_jobs`: 한 번의 DAG 실행에서 체크할 최대 Batch 작업 개수 (기본값: 20)
    - `provider`: 적재 대상으로 조회할 provider. `all`이면 전체 조회 (기본값: all)

    ---
    *주의: 결과 파일은 OpenAI 서버에 30일 동안만 보관되므로, 작업이 완료된 후 주기적으로 실행하여 수집해야 합니다.*
    """,
) as dag:
    ingest_batch_results = PythonOperator(
        task_id="poll_and_ingest_batch_results",
        python_callable=poll_and_ingest_batch_results,
    )
