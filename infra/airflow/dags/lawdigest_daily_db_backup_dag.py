# -*- coding: utf-8 -*-
from __future__ import annotations

import pendulum
import os
import sys

from airflow.models.dag import DAG
from airflow.operators.python import PythonOperator

# 프로젝트 루트 경로를 sys.path에 추가하여 module을 찾을 수 있도록 합니다.
sys.path.append('/opt/airflow/project')

# database_backup.py의 main 함수를 import
# airflow/dags 폴더 입장에서 상위 폴더인 project 루트를 기준으로 import
from jobs.database_backup import main as db_backup_main

with DAG(
    dag_id="lawdigest_daily_db_backup_dag",
    schedule="0 0 * * *",  # 매일 자정 실행
    start_date=pendulum.datetime(2024, 1, 1, tz="Asia/Seoul"),
    catchup=False,
    tags=["lawdigest", "daily", "backup"],
    doc_md="""
    ## 💾 Lawdigest 데이터베이스 정기 백업

    매일 정기적으로 Lawdigest의 전체 데이터베이스를 백업하여 데이터 안전성을 보장하는 DAG입니다.

    ### 🚀 주요 기능
    1. **DB 덤프 생성**: MySQL 서버에서 `mysqldump`를 실행하여 전체 데이터를 추출합니다.
    2. **백업 파일 저장**: 생성된 백업 파일(`.sql`)을 지정된 로컬 또는 외부 스토리지 경로에 저장합니다.
    3. **성공 여부 확인**: 백업 프로세스의 종료 상태를 확인하여 성공 여부를 로그에 남깁니다.

    ### ⚙️ 실행 스케줄
    - **매일 오전 0시(KST)**에 자동으로 실행됩니다.

    ---
    *주의: 백업 파일이 저장되는 경로의 용량이 충분한지 주기적으로 확인이 필요합니다.*
    """,
) as dag:

    db_backup = PythonOperator(
        task_id="database_backup",
        python_callable=db_backup_main,
    )
