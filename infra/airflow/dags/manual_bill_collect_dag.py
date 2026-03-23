# -*- coding: utf-8 -*-
from __future__ import annotations

import pendulum

from airflow.models.dag import DAG
from airflow.operators.python import PythonOperator
from airflow.models.param import Param

# Airflow 환경에서 DAG 파일이 있는 디렉토리의 상위 디렉토리를
# 파이썬 경로에 추가하여 'tools' 모듈을 찾을 수 있도록 합니다.
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- Task Function ---
# Airflow의 context에서 파라미터를 받아 원래의 main 함수를 호출하는 래퍼 함수입니다.
def collect_bills_task(**context):
    """
    Airflow UI에서 전달된 파라미터를 사용하여 법안 데이터 수집 스크립트를 실행합니다.
    """
    start_date = context["params"]["start_date"]
    end_date = context["params"]["end_date"]
    age = context["params"]["age"]
    
    print(f"Airflow-triggered execution with params: start_date={start_date}, end_date={end_date}, age={age}")
    
    # Airflow 파서 단계에서 import 오류를 피하기 위해 실행 시점에 import
    from project.tools.collect_bills import main as collect_bills_main

    collect_bills_main(start_date=start_date, end_date=end_date, age=age)

# --- DAG Definition ---
with DAG(
    dag_id="manual_bill_collect_dag",
    schedule=None,  # 수동 실행 전용
    start_date=pendulum.datetime(2024, 1, 1, tz="Asia/Seoul"),
    catchup=False,
    tags=["lawdigest", "manual-run", "tools"],
    doc_md="""
    ## 🛠️ Lawdigest 수동 법안 데이터 수집 도구

    스케줄에 의존하지 않고, 사용자가 직접 범위를 지정하여 법안 데이터를 강제 수집할 때 사용하는 도구용 DAG입니다.

    ### 🚀 주요 기능
    1. **범위 지정 수집**: `start_date`와 `end_date`를 지정하여 특정 기간의 법안을 수집합니다.
    2. **국회 대수 선택**: 특정 국회 대수(`age`)를 지정하여 대량 수집이 가능합니다.
    3. **데이터 보정**: 자동 수집 과정에서 누락된 데이터를 수동으로 메울 때 유용합니다.

    ### ⚙️ 실행 방법
    - **수동 실행 전용** (`schedule=None`)
    - `Trigger DAG w/ Config`를 통해 파라미터를 입력하고 실행하세요.

    ### 📅 파라미터 가이드
    - `start_date`: 수집 시작 날짜 (YYYY-MM-DD)
    - `end_date`: 수집 종료 날짜 (YYYY-MM-DD)
    - `age`: 국회 대수 (예: 21, 22)

    ---
    *주의: 대량 데이터를 수집할 때는 API 속도 제한이나 DB 부하를 고려하여 적절한 기간으로 나누어 실행하십시오.*
    """,
) as dag:
    manual_collect_task = PythonOperator(
        task_id="collect_bills_with_params",
        python_callable=collect_bills_task,
    )
