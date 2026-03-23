# -*- coding: utf-8 -*-
from __future__ import annotations

import sys

import pendulum

from airflow.models.dag import DAG
from airflow.models.param import Param
from airflow.operators.python import PythonOperator


def submit_ai_batch(**context):
    params = context.get("params", {})
    mode = params.get("execution_mode") or "dry_run"

    print(f"[batch-submit] Current Mode: {mode}")

    project_root = "/opt/airflow/project"
    if project_root not in sys.path:
        sys.path.append(project_root)

    from lawdigest_ai.processor.batch_submit import submit_batch

    return submit_batch(
        limit=int(params.get("limit") or 200),
        model=params.get("model") or "gpt-4o-mini",
        mode=mode,
    )


with DAG(
    dag_id="ai_batch_submit_dag",
    schedule="10 * * * *",
    start_date=pendulum.datetime(2024, 1, 1, tz="Asia/Seoul"),
    catchup=False,
    tags=["lawdigest", "ai-summary", "batch-submit"],
    params={
        "execution_mode": Param(
            "dry_run",
            type="string",
            enum=["dry_run", "test", "prod"],
            title="실행 모드",
            description="dry_run: 제출 없이 대상만 확인, test: 테스트 DB 사용, prod: 운영 DB 사용",
        ),
        "limit": Param(200, type="integer", title="배치 최대 건수"),
        "model": Param("gpt-4o-mini", type="string", title="모델명"),
    },
    doc_md="""
    ## 🤖 Lawdigest AI Batch 요청 제출 (OpenAI)

    대량의 미요약 법안을 한꺼번에 OpenAI Batch API로 보내어 요약을 요청하는 DAG입니다.

    ### 🚀 주요 기능
    1. **미요약 대상 식별**: DB에서 `brief_summary` 또는 `gpt_summary`가 누락된 법안을 지정된 개수(`limit`)만큼 조회합니다.
    2. **요청 파일 생성**: OpenAI Batch 규격에 맞는 JSONL 파일을 생성합니다.
    3. **OpenAI 업로드**: 생성된 파일을 OpenAI에 업로드하고 Batch 작업을 생성합니다.
    4. **상태 관리**: 생성된 Batch ID와 작업 정보를 DB(`ai_batch_jobs`, `ai_batch_items`)에 저장하여 추후 결과를 수신할 수 있게 합니다.

    ### ⚙️ 실행 모드 (Execution Mode)
    - `dry_run` (기본값): OpenAI API를 호출하지 않고, 어떤 법안들이 요약 대상으로 선정되었는지만 확인합니다. (비용 발생 방지)
    - `test`: 테스트용 DB를 조회하여 요약 대상을 찾고, OpenAI Batch를 실행합니다. 결과는 테스트 DB의 상태 테이블에 기록됩니다.
    - `prod`: 실제 운영 DB를 조회하여 대량의 운영 데이터를 요약 요청합니다.

    ### 📅 파라미터 가이드
    - `execution_mode`: 실행 환경 및 실제 API 호출 여부 선택
    - `limit`: 한 번에 보낼 최대 법안 수 (기본값: 200)
    - `model`: 사용할 OpenAI 모델명 (기본값: gpt-4o-mini)

    ---
    *참고: Batch API는 비용이 50% 저렴하지만 결과 수신까지 최대 24시간이 소요될 수 있습니다.*
    """,
) as dag:
    submit_batch = PythonOperator(
        task_id="submit_ai_batch",
        python_callable=submit_ai_batch,
    )

