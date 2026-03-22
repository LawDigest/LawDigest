# -*- coding: utf-8 -*-
from __future__ import annotations

import pendulum
import os
import sys

from airflow.models.dag import DAG
from airflow.operators.python import PythonOperator
from airflow.models.param import Param

# 프로젝트 루트 경로를 sys.path에 추가하여 src 모듈을 찾을 수 있도록 합니다.
sys.path.append('/opt/airflow/project')

def run_workflow_step(method_name, **context):
    """
    WorkFlowManager의 특정 메서드를 실행하는 함수.
    수동 실행 시 입력받은 params가 있으면 이를 우선적으로 사용합니다.
    """
    # UI에서 입력받은 params 가져오기
    params = context.get("params", {})
    start_date = params.get("start_date")
    end_date = params.get("end_date")
    age = params.get("age")

    print(f"--- Calling {method_name} ---")
    if start_date or end_date:
        print(f"Custom range detected: {start_date} ~ {end_date} (Age: {age})")
    else:
        print("No custom range detected. Using default scheduling/latest data logic.")

    # Airflow 파서 단계에서 외부 의존 import 실패를 피하기 위해 실행 시점에 import
    from src.lawdigest_data_pipeline.WorkFlowManager import WorkFlowManager

    wfm = WorkFlowManager(mode='remote')
    method = getattr(wfm, method_name)
    
    # 메서드별 인자 처리
    if method_name == "update_lawmakers_data":
        # 의원 정보는 보통 기간 필터 없이 전체 또는 변경분 수집
        method()
    else:
        # 법안, 타임라인, 결과, 표결 정보는 입력받은 날짜 정보를 전달
        # (날짜가 None이면 WorkFlowManager 내부에서 최신 날짜를 자동으로 계산함)
        method(start_date=start_date, end_date=end_date, age=age)
        
    print(f"--- Finished {method_name} ---")

with DAG(
    dag_id="lawdigest_hourly_update_dag",
    schedule="0 * * * *",  # 매 정시 실행
    start_date=pendulum.datetime(2024, 1, 1, tz="Asia/Seoul"),
    catchup=False,
    tags=["lawdigest", "hourly", "update"],
    # UI에서 입력받을 수 있는 파라미터 정의
    params={
        "start_date": Param(
            None, 
            type=["null", "string"], 
            title="시작 날짜", 
            description="데이터를 수집할 시작 날짜 (YYYY-MM-DD). 비워두면 최신 데이터부터 가져옵니다."
        ),
        "end_date": Param(
            None, 
            type=["null", "string"], 
            title="종료 날짜", 
            description="데이터를 수집할 종료 날짜 (YYYY-MM-DD). 비워두면 오늘 날짜까지 가져옵니다."
        ),
        "age": Param(
            "22", 
            type="string", 
            title="국회 대수", 
            description="수집할 국회 대수 (기본값: 22)"
        ),
    },
    doc_md="""
    ## 🔄 Lawdigest 시간별 데이터 동기화

    매시간 정기적으로 법안의 최신 상태, 타임라인, 국회의원 정보 등을 종합적으로 업데이트하는 핵심 동기화 DAG입니다.

    ### 🚀 주요 기능
    1. **의원 정보 갱신**: 신규 국회의원 정보나 변동된 소속 정당 등을 업데이트합니다.
    2. **법안 상세 업데이트**: 수집된 법안의 최신 진행 상태(계류, 가결 등)를 동기화합니다.
    3. **타임라인 및 표결 정보**: 법안의 처리 과정(타임라인)과 의원별 표결 결과를 수집하여 반영합니다.

    ### ⚙️ 실행 스케줄
    - **매시간 정시(0분)**에 자동으로 실행됩니다.

    ### 📅 수동 실행 가이드
    특정 기간의 데이터가 누락되었거나 대규모 소급 업데이트가 필요할 때 사용합니다.
    - `Trigger DAG w/ Config` 클릭 후 다음 파라미터를 입력하세요:
      - `start_date`: 시작 날짜 (YYYY-MM-DD)
      - `end_date`: 종료 날짜 (YYYY-MM-DD)
      - `age`: 수집 대상 국회 대수 (기본값: 22)

    ---
    *참고: 이 DAG는 실시간 서비스의 데이터 정합성을 유지하기 위한 최상위 워크플로우입니다.*
    """,
) as dag:

    update_lawmakers = PythonOperator(
        task_id="update_lawmakers",
        python_callable=run_workflow_step,
        op_kwargs={"method_name": "update_lawmakers_data"},
    )

    update_bills = PythonOperator(
        task_id="update_bills",
        python_callable=run_workflow_step,
        op_kwargs={"method_name": "update_bills_data"},
    )

    update_timeline = PythonOperator(
        task_id="update_timeline",
        python_callable=run_workflow_step,
        op_kwargs={"method_name": "update_bills_timeline"},
    )

    update_results = PythonOperator(
        task_id="update_results",
        python_callable=run_workflow_step,
        op_kwargs={"method_name": "update_bills_result"},
    )

    update_votes = PythonOperator(
        task_id="update_votes",
        python_callable=run_workflow_step,
        op_kwargs={"method_name": "update_bills_vote"},
    )

    # 실행 순서 정의: 의원 -> 법안 -> [타임라인, 처리결과, 표결정보]
    update_lawmakers >> update_bills >> [update_timeline, update_results, update_votes]
