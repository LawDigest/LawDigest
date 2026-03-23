FROM apache/airflow:3.1.8-python3.12

# Airflow 사용자 권한으로 작업 수행
USER airflow

# Airflow 3.1.8 전용 constraints 파일을 활용하여 의존성 충돌 방지
ARG AIRFLOW_CONSTRAINTS_REFERENCE="constraints-3.1.8"
ARG PYTHON_VERSION="3.12"

# requirements.txt 복사
COPY requirements.txt /requirements.txt

# 패키지 설치 시 공식 constraints 파일을 참조하여 무한 루프 방지
RUN pip install --no-cache-dir \
    -r /requirements.txt \
    --constraint "https://raw.githubusercontent.com/apache/airflow/${AIRFLOW_CONSTRAINTS_REFERENCE}/constraints-${PYTHON_VERSION}.txt"
