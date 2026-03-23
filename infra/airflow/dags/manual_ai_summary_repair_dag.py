# -*- coding: utf-8 -*-
from __future__ import annotations

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


def run_batch_ai_summary(**context):
    params = context.get("params", {})
    output_path = params.get("output_path") or "/tmp/lawdigest_missing_summaries.json"
    batch_size = int(params.get("batch_size") or 10)
    mode = params.get("execution_mode") or "dry_run"
    dry_run = (mode == "dry_run")

    print(f"[ai-summary-batch] Current Mode: {mode}")

    project_root = "/opt/airflow/project"
    if project_root not in sys.path:
        sys.path.append(project_root)

    # 파서 단계 import 실패를 피하기 위해 실행 시점에 import
    from scripts.find_missing_summaries import find_missing_summaries
    from scripts.repair_missing_summaries import repair_missing_summaries
    from lawdigest_ai.db import get_prod_db_config, get_test_db_config

    if mode == "prod":
        db_cfg = get_prod_db_config()
        print("[ai-summary-batch] Using PRODUCTION database")
    else:
        db_cfg = get_test_db_config()
        print("[ai-summary-batch] Using TEST database")

    find_missing_summaries(output_path=output_path, db_config=db_cfg)
    repair_missing_summaries(
        input_path=output_path,
        dry_run=dry_run,
        batch_size=batch_size,
        db_config=db_cfg,
    )


with DAG(
    dag_id="manual_ai_summary_repair_dag",
    schedule=None,
    start_date=pendulum.datetime(2024, 1, 1, tz="Asia/Seoul"),
    catchup=False,
    tags=["lawdigest", "ai-summary", "batch"],
    params={
        "execution_mode": Param(
            "dry_run",
            type="string",
            enum=["dry_run", "test", "prod"],
            title="실행 모드",
            description="dry_run: DB 업데이트 안 함, test: 테스트 DB 사용, prod: 운영 DB 사용",
        ),
        "output_path": Param(
            "/tmp/lawdigest_missing_summaries.json",
            type="string",
            title="결측치 JSON 경로",
            description="결측치 추출/복구 작업에 사용할 JSON 파일 경로",
        ),
        "batch_size": Param(
            10,
            type="integer",
            title="배치 크기",
            description="한 번에 처리할 법안 수",
        ),
    },
    doc_md="""
    ## 🛠️ Lawdigest AI Summary 배치 복구 (Fallback)

    이미 DB에 수집되어 있으나 AI 요약 데이터가 누락된 법안들을 찾아내어 일괄적으로 요약을 생성하고 채워넣는 DAG입니다.

    ### 🚀 주요 기능
    1. **누락 대상 추출**: `Bill` 테이블에서 `brief_summary` 또는 `gpt_summary`가 `NULL`이거나 비어 있는 법안들을 모두 추출합니다.
    2. **요약 생성**: 누락된 법안들에 대해 OpenAI API를 호출하여 요약 내용을 새롭게 생성합니다.
    3. **DB 업데이트**: 생성된 요약 정보를 `Bill` 테이블에 다시 저장합니다.

    ### ⚙️ 실행 모드 (Execution Mode)
    - `dry_run` (기본값): 실제 DB 업데이트를 하지 않고, 어떤 데이터들이 복구 대상인지와 가상의 요약 결과만 로그로 확인합니다.
    - `test`: 테스트용 DB를 조회하여 결측치를 찾고 결과를 테스트 DB에 저장합니다.
    - `prod`: 실제 서비스 운영 DB를 대상으로 대규모 결측치 복구를 수행합니다. (실제 요금 발생 주의)

    ### 📅 파라미터 가이드
    - `execution_mode`: 실행 환경 및 실제 DB 반영 여부 선택
    - `output_path`: 작업 중 생성되는 임시 JSON 파일 저장 경로 (기본값: /tmp/lawdigest_missing_summaries.json)
    - `batch_size`: 한 번에 처리할 법안 개수 (기본값: 10)

    ---
    *참고: 이 DAG는 실시간 연동보다 과거에 누적된 결측치를 일괄 복구할 때 주로 사용됩니다.*
    """,
) as dag:
    batch_ai_summary = PythonOperator(
        task_id="batch_ai_summary_repair",
        python_callable=run_batch_ai_summary,
    )

