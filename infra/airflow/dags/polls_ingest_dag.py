# -*- coding: utf-8 -*-
"""NESDC 여론조사 타겟 기반 수집 DAG.

config/poll_targets.json에 지정된 타겟만 선택적으로 수집하여
PollSurvey / PollQuestion / PollOption 테이블에 저장한다.
"""
from __future__ import annotations

import sys
from time import monotonic

import pendulum

from airflow.models.dag import DAG
from airflow.models.param import Param
from airflow.operators.python import PythonOperator

_PROJECT_ROOT = "/opt/airflow/project"
_DATA_PROJECT_ROOT = f"{_PROJECT_ROOT}/services/data"
_RUN_STARTED_AT: float | None = None


def fetch_polls(**context):
    global _RUN_STARTED_AT
    _RUN_STARTED_AT = monotonic()
    if _DATA_PROJECT_ROOT not in sys.path:
        sys.path.append(_DATA_PROJECT_ROOT)
    data_src = f"{_DATA_PROJECT_ROOT}/src"
    if data_src not in sys.path:
        sys.path.append(data_src)

    from lawdigest_data.polls.workflow import PollsWorkflowManager

    params = context.get("params", {})
    manager = PollsWorkflowManager(params.get("execution_mode") or "dry_run")
    return manager.fetch_polls_step(
        targets_path=params.get("targets_path") or None,
        max_pages_per_target=int(params.get("max_pages_per_target") or 50),
    )


def crawl_details(**context):
    if _DATA_PROJECT_ROOT not in sys.path:
        sys.path.append(_DATA_PROJECT_ROOT)
    data_src = f"{_DATA_PROJECT_ROOT}/src"
    if data_src not in sys.path:
        sys.path.append(data_src)

    from lawdigest_data.polls.workflow import PollsWorkflowManager

    params = context.get("params", {})
    task_instance = context["ti"]
    fetched = task_instance.xcom_pull(task_ids="fetch_polls") or {}
    artifact_path = fetched.get("artifact_path")
    if not artifact_path:
        return {"mode": params.get("execution_mode") or "dry_run", "total": 0, "artifact_path": None}

    manager = PollsWorkflowManager(params.get("execution_mode") or "dry_run")
    return manager.crawl_details_step(
        artifact_path=artifact_path,
        detail_limit=int(params.get("detail_limit") or 0),
    )


def parse_results(**context):
    if _DATA_PROJECT_ROOT not in sys.path:
        sys.path.append(_DATA_PROJECT_ROOT)
    data_src = f"{_DATA_PROJECT_ROOT}/src"
    if data_src not in sys.path:
        sys.path.append(data_src)

    from lawdigest_data.polls.workflow import PollsWorkflowManager

    params = context.get("params", {})
    task_instance = context["ti"]
    detailed = task_instance.xcom_pull(task_ids="crawl_details") or {}
    artifact_path = detailed.get("artifact_path")

    # crawl_results 파라미터가 false이면 이 단계를 스킵
    if not params.get("crawl_results", True):
        return {"mode": params.get("execution_mode") or "dry_run", "parsed": 0, "questions_total": 0, "artifact_path": None}

    if not artifact_path:
        return {"mode": params.get("execution_mode") or "dry_run", "parsed": 0, "questions_total": 0, "artifact_path": None}

    manager = PollsWorkflowManager(params.get("execution_mode") or "dry_run")
    return manager.parse_results_step(
        artifact_path=artifact_path,
        registry_path=params.get("registry_path") or None,
        pdf_dir=params.get("pdf_dir") or None,
    )


def upsert_polls(**context):
    if _DATA_PROJECT_ROOT not in sys.path:
        sys.path.append(_DATA_PROJECT_ROOT)
    data_src = f"{_DATA_PROJECT_ROOT}/src"
    if data_src not in sys.path:
        sys.path.append(data_src)

    from lawdigest_data.polls.workflow import PollsWorkflowManager

    params = context.get("params", {})
    task_instance = context["ti"]
    parsed = task_instance.xcom_pull(task_ids="parse_results") or {}
    artifact_path = parsed.get("artifact_path")
    if not artifact_path:
        return {"mode": params.get("execution_mode") or "dry_run", "upserted_surveys": 0, "upserted_questions": 0}

    manager = PollsWorkflowManager(params.get("execution_mode") or "dry_run")
    return manager.upsert_polls_step(artifact_path=artifact_path)


def summarize_run(**context):
    if _DATA_PROJECT_ROOT not in sys.path:
        sys.path.append(_DATA_PROJECT_ROOT)
    data_src = f"{_DATA_PROJECT_ROOT}/src"
    if data_src not in sys.path:
        sys.path.append(data_src)

    from lawdigest_data.polls.workflow import _write_artifact

    params = context.get("params", {})
    ti = context["ti"]
    fetched = ti.xcom_pull(task_ids="fetch_polls") or {}
    detailed = ti.xcom_pull(task_ids="crawl_details") or {}
    parsed = ti.xcom_pull(task_ids="parse_results") or {}
    upserted = ti.xcom_pull(task_ids="upsert_polls") or {}

    started_at = _RUN_STARTED_AT
    total_elapsed = round(monotonic() - started_at, 3) if started_at is not None else None

    summary = {
        "mode": params.get("execution_mode") or "dry_run",
        "targets_path": params.get("targets_path") or None,
        "target_count": fetched.get("targets", 0),
        "target_slugs": fetched.get("target_slugs", []),
        "fetched_total": fetched.get("total", 0),
        "details_total": detailed.get("total", 0),
        "parsed_total": parsed.get("parsed", 0),
        "questions_total": parsed.get("questions_total", 0),
        "saved_paths_count": len(parsed.get("saved_paths") or []),
        "upserted_surveys": upserted.get("upserted_surveys", 0),
        "upserted_questions": upserted.get("upserted_questions", 0),
        "total_elapsed_seconds": total_elapsed,
        "step_elapsed_seconds": {
            "fetch_polls": fetched.get("elapsed_seconds"),
            "crawl_details": detailed.get("elapsed_seconds"),
            "parse_results": parsed.get("elapsed_seconds"),
            "upsert_polls": upserted.get("elapsed_seconds"),
        },
        "artifacts": {
            "fetch": fetched.get("artifact_path"),
            "details": detailed.get("artifact_path"),
            "results": parsed.get("artifact_path"),
        },
    }
    summary["artifact_path"] = _write_artifact("polls_ingest_summary", summary)
    print(f"[polls_ingest.summary] {summary}")
    return summary


with DAG(
    dag_id="polls_ingest_dag",
    schedule="0 3 * * *",  # 매일 새벽 3시
    start_date=pendulum.datetime(2024, 1, 1, tz="Asia/Seoul"),
    catchup=False,
    tags=["lawdigest", "polls", "ingest"],
    params={
        "execution_mode": Param(
            "dry_run",
            type="string",
            enum=["dry_run", "test", "prod"],
            title="실행 모드",
            description="dry_run: DB 미반영, test: 테스트 DB, prod: 운영 DB",
        ),
        "targets_path": Param(
            None,
            type=["null", "string"],
            title="타겟 설정 파일 경로",
            description="비우면 config/poll_targets.json 사용",
        ),
        "max_pages_per_target": Param(
            50,
            type="integer",
            title="타겟당 최대 스캔 페이지 수",
        ),
        "detail_limit": Param(
            0,
            type="integer",
            title="상세 수집 제한 건수",
            description="0이면 제한 없음. 테스트 시 소수 지정 권장",
        ),
        "crawl_results": Param(
            True,
            type="boolean",
            title="결과 PDF 수집 여부",
            description="False이면 PDF 다운로드 및 파싱을 건너뜁니다",
        ),
        "registry_path": Param(
            None,
            type=["null", "string"],
            title="파서 레지스트리 경로",
            description="비우면 config/parser_registry.json 사용",
        ),
        "pdf_dir": Param(
            None,
            type=["null", "string"],
            title="PDF 저장 디렉터리",
            description="비우면 ./pdfs 사용",
        ),
    },
    doc_md="""
    ## 📥 NESDC 여론조사 타겟 기반 수집 DAG

    `config/poll_targets.json`에 지정된 수집 대상만 선택적으로 크롤링하여
    데이터베이스에 저장하는 DAG입니다.

    ### 🚀 주요 기능
    1. **타겟 기반 수집**: `poll_targets.json`에 명시된 (선거구분, 지역, 선거명, 조사기관) 조합만 수집합니다.
    2. **상세 수집**: 목록 페이지에서 개별 여론조사 상세 정보를 가져옵니다.
    3. **PDF 파싱**: 결과 PDF를 다운로드하고 조사기관별 파서로 문항/응답 데이터를 추출합니다.
    4. **DB 저장**: `PollSurvey`, `PollQuestion`, `PollOption` 테이블에 upsert합니다.

    ### ⚙️ 실행 모드
    - `dry_run` (기본값): DB 미반영, 수집 결과 artifact JSON만 생성
    - `test`: 테스트 DB에 반영
    - `prod`: 운영 DB에 반영

    ### 📋 사전 준비
    1. `polls_catalog_dag`를 먼저 실행하여 존재하는 값을 확인합니다.
    2. `config/poll_targets.json`에 원하는 타겟을 지정합니다.
    3. `config/parser_registry.json`에 조사기관별 파서가 올바르게 설정되어 있는지 확인합니다.
    """,
) as dag:
    t_fetch = PythonOperator(
        task_id="fetch_polls",
        python_callable=fetch_polls,
    )

    t_details = PythonOperator(
        task_id="crawl_details",
        python_callable=crawl_details,
    )

    t_parse = PythonOperator(
        task_id="parse_results",
        python_callable=parse_results,
    )

    t_upsert = PythonOperator(
        task_id="upsert_polls",
        python_callable=upsert_polls,
    )

    t_summary = PythonOperator(
        task_id="summarize_run",
        python_callable=summarize_run,
    )

    t_fetch >> t_details >> t_parse >> t_upsert >> t_summary
