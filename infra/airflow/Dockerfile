FROM apache/airflow:3.1.8-python3.12

# Airflow 사용자 권한으로 작업 수행
USER airflow

# Airflow 3.1.8 전용 constraints 파일을 활용하여 의존성 충돌 방지
ARG AIRFLOW_CONSTRAINTS_REFERENCE="constraints-3.1.8"
ARG PYTHON_VERSION="3.12"

# requirements 파일 복사
COPY --chown=airflow:root requirements-airflow.txt /requirements-airflow.txt
COPY --chown=airflow:root requirements-runtime.txt /requirements-runtime.txt

# Airflow와 함께 고정해도 되는 의존성은 공식 constraints로 재현성을 확보한다.
RUN pip install --no-cache-dir \
    -r /requirements-airflow.txt \
    --constraint "https://raw.githubusercontent.com/apache/airflow/${AIRFLOW_CONSTRAINTS_REFERENCE}/constraints-${PYTHON_VERSION}.txt"

# pydantic-ai-slim 등 앱 런타임 의존성은 Airflow constraints보다 높은
# opentelemetry-api 버전을 요구하므로 별도 단계에서 해결한다.
RUN pip install --no-cache-dir \
    -r /requirements-runtime.txt
