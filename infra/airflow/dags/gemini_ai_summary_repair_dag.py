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


def run_gemini_ai_summary_repair(**context):
    params = context.get("params", {})
    mode = params.get("execution_mode") or "dry_run"

    print(f"[gemini-ai-summary-repair] Current Mode: {mode}")

    project_root = "/opt/airflow/project"
    if project_root not in sys.path:
        sys.path.append(project_root)

    from lawdigest_ai.processor.gemini_repair_pipeline import run_gemini_repair_pipeline

    return run_gemini_repair_pipeline(
        mode=mode,
        limit=int(params.get("limit") or 20),
        batch_size=int(params.get("batch_size") or 5),
        output_path=params.get("output_path") or "/tmp/gemini_ai_summary_results.json",
        stop_on_error=_as_bool(params.get("stop_on_error", False)),
        read_mode=params.get("read_mode") or None,
        target_mode=params.get("target_mode") or "missing",
    )


with DAG(
    dag_id="gemini_ai_summary_repair_dag",
    schedule=None,
    start_date=pendulum.datetime(2024, 1, 1, tz="Asia/Seoul"),
    catchup=False,
    tags=["lawdigest", "ai-summary", "gemini", "repair"],
    params={
        "execution_mode": Param(
            "dry_run",
            type="string",
            enum=["dry_run", "test", "prod"],
            title="실행 모드",
            description="dry_run: DB 반영 안 함, test: 테스트 DB 사용, prod: 운영 DB 사용",
        ),
        "limit": Param(
            20,
            type="integer",
            title="처리 최대 건수",
            description="이번 실행에서 조회할 미요약 법안 최대 건수",
        ),
        "batch_size": Param(
            5,
            type="integer",
            title="Gemini 처리 묶음 크기",
            description="한 번에 Gemini 요약기로 넘길 최대 법안 수",
        ),
        "read_mode": Param(
            "",
            type="string",
            title="조회 DB 모드",
            description="비우면 execution_mode 기준으로 조회하고, test/prod를 지정하면 조회 DB만 별도로 고정합니다.",
        ),
        "target_mode": Param(
            "missing",
            type="string",
            enum=["missing", "latest"],
            title="대상 선택 방식",
            description="missing: 미요약 법안 조회, latest: 최신 법안 조회 후 재요약",
        ),
        "output_path": Param(
            "/tmp/gemini_ai_summary_results.json",
            type="string",
            title="산출물 JSON 경로",
            description="요약 결과와 실패 내역을 저장할 JSON 파일 경로",
        ),
        "stop_on_error": Param(
            False,
            type="boolean",
            title="오류 시 즉시 중단",
            description="True면 일부 실패가 발생해도 DB 반영을 멈추고 DAG를 실패 처리합니다.",
        ),
    },
    doc_md="""
    ## 🤖 Gemini CLI 기반 법안 AI 요약 복구 파이프라인

    기존 OpenAI Batch 경로와 분리된 독립 실행용 DAG입니다.  
    DB에서 AI 요약이 누락된 법안을 조회하고, Gemini CLI 경로로 요약을 생성한 뒤 JSON 산출물을 남기고 필요 시 DB에 반영합니다.

    ### 🚀 주요 기능
    1. **미요약 대상 자동 조회**: `Bill` 테이블에서 `brief_summary` 또는 `gpt_summary`가 비어 있는 법안을 최대 `limit`건 조회합니다.
    2. **Gemini CLI 요약 생성**: 조회된 법안을 `batch_size` 단위로 Gemini CLI 요약기에 전달합니다.
    3. **산출물 저장**: 성공/실패 여부와 생성된 `ai_title`, `ai_summary`, `summary_tags`를 JSON으로 저장합니다.
    4. **선택적 DB 반영**: `test` 또는 `prod` 모드에서는 성공 건을 DB에 업데이트합니다.

    ### ⚙️ 실행 모드
    - `dry_run`: JSON 산출물만 저장하고 DB는 건드리지 않습니다.
    - `test`: 테스트 DB 기준으로 조회하고 성공 건을 테스트 DB에 반영합니다.
    - `prod`: 운영 DB 기준으로 조회하고 성공 건을 운영 DB에 반영합니다.

    ### 📅 파라미터 가이드
    - `execution_mode`: 실행 환경 선택
    - `limit`: 이번 실행에서 처리할 최대 법안 수
    - `batch_size`: 한 번에 Gemini에 보낼 법안 수
    - `read_mode`: 조회 대상 DB를 별도로 지정할 때 사용 (`test` 또는 `prod`)
    - `target_mode`: 미요약 법안 복구(`missing`) 또는 최신 법안 재요약(`latest`)
    - `output_path`: 결과 JSON 저장 위치
    - `stop_on_error`: 실패 발생 시 DB 반영 중단 여부

    ---
    *참고: 이 DAG는 수동 실행용으로 시작하지만, 내부 pipeline 모듈은 추후 스케줄 DAG에서도 재사용할 수 있습니다.*
    """,
) as dag:
    gemini_ai_summary_repair = PythonOperator(
        task_id="gemini_ai_summary_repair",
        python_callable=run_gemini_ai_summary_repair,
    )
