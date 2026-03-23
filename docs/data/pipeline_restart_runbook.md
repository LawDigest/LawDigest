# 데이터 파이프라인 재가동 런북

> 작성일: 2026-03-23
> 현재 상태: Airflow 실행 중, **모든 DAG 일시정지(paused=True)** 상태

---

## 현재 상태 요약

```
마지막 성공 실행: 2025-12-22 (lawdigest_hourly_update_dag - success 1회)
마지막 실패 원인: update_bills 태스크 반복 실패 (2025-12-21~22)
현재 queued 상태: lawdigest_bill_ingest_dag (2026-03-22 12:34 UTC)
                  lawdigest_hourly_update (2026-03-22, 구 DAG ID)
```

**모든 DAG은 현재 일시정지 상태입니다. 재가동 전 아래 체크리스트를 확인하세요.**

---

## 1. 재가동 전 체크리스트

### 1.1 서비스 상태 확인

```bash
# Airflow 컨테이너 상태 확인
docker ps --format "table {{.Names}}\t{{.Status}}" | grep airflow

# 예상 결과:
# airflow-airflow-webserver-1    Up XX hours (unhealthy)  ← 정상 (헬스체크 경로 이슈)
# airflow-airflow-scheduler-1    Up XX hours (healthy)
# airflow-airflow-worker-1       Up XX hours (healthy)
# airflow-airflow-triggerer-1    Up XX hours (healthy)
# airflow-postgres-1             Up XX hours (healthy)
# airflow-redis-1                Up XX hours (healthy)
```

### 1.2 DAG 목록 및 일시정지 상태 확인

```bash
docker exec airflow-airflow-webserver-1 airflow dags list
```

### 1.3 DB 연결 확인

```bash
# 프로덕션 DB (lawDB)
docker exec airflow-airflow-webserver-1 python3 -c "
import pymysql
conn = pymysql.connect(host='140.245.74.246', port=2835, user='root',
    password='d@X!qbhQgXE62ibPc!hti', database='lawDB')
print('lawDB 연결 성공:', conn.get_server_info())
conn.close()
"
```

### 1.4 큐잉된 DAG 정리 (필요 시)

재가동 전 이전 queued 상태로 남아있는 실행을 정리합니다.

```bash
# 현재 실행 상태 확인
docker exec airflow-postgres-1 psql -U airflow -d airflow -c \
  "SELECT dag_id, state, logical_date FROM dag_run WHERE state IN ('queued','running') ORDER BY logical_date;"
```

---

## 2. DAG 재가동 순서

### 단계 1: 데이터 수집 DAG 활성화 (우선)

```bash
# 1-1. 법안 수집 DAG 활성화
docker exec airflow-airflow-webserver-1 airflow dags unpause lawdigest_bill_ingest_dag

# 1-2. 시간별 업데이트 DAG 활성화
docker exec airflow-airflow-webserver-1 airflow dags unpause lawdigest_hourly_update_dag
```

### 단계 2: AI 배치 DAG 활성화

```bash
# 2-1. AI 배치 제출 DAG
docker exec airflow-airflow-webserver-1 airflow dags unpause lawdigest_ai_batch_submit_dag

# 2-2. AI 배치 결과 수신 DAG
docker exec airflow-airflow-webserver-1 airflow dags unpause lawdigest_ai_batch_ingest_dag
```

### 단계 3: DB 백업 DAG 활성화

```bash
docker exec airflow-airflow-webserver-1 airflow dags unpause lawdigest_daily_db_backup_dag
```

> **수동 실행 DAG** (`lawdigest_ai_summary_batch_dag`, `lawdigest_ai_summary_instant_dag`, `manual_collect_bills`)은 스케줄 없이 필요 시 수동 트리거하므로 별도 활성화 불필요.

---

## 3. 수동 테스트 실행

재가동 직후 정상 동작 여부를 확인하려면 `dry_run` 모드로 수동 트리거합니다.

```bash
# 법안 수집 dry-run 테스트 (DB 저장 없이 수집만)
docker exec airflow-airflow-webserver-1 airflow dags trigger \
  lawdigest_bill_ingest_dag \
  --conf '{"execution_mode": "dry_run", "start_date": "2026-03-22", "end_date": "2026-03-23"}'
```

```bash
# 실행 상태 모니터링
docker exec airflow-postgres-1 psql -U airflow -d airflow -c \
  "SELECT dag_id, state, logical_date FROM dag_run ORDER BY logical_date DESC LIMIT 5;"
```

---

## 4. 이전 실패 원인 분석 및 조치

### 4.1 update_bills 태스크 반복 실패 (2025-12-21~22)

**증상**: `lawdigest_hourly_update_dag`의 `update_bills` 태스크가 약 50초 후 실패
**후속 태스크**: `update_timeline`, `update_results`, `update_votes` → `upstream_failed`

**확인 방법**:

```bash
# 실패 태스크 로그 확인
docker exec airflow-airflow-webserver-1 airflow tasks logs \
  lawdigest_hourly_update_dag update_bills <실행_날짜>
```

**가능한 원인**:
1. DB 연결 타임아웃 (DB 서버 재시작/점검)
2. 국회 Open API 응답 오류 또는 변경
3. WorkFlowManager 코드 오류

---

## 5. Airflow 웹 UI 접속

- **URL**: http://localhost:8081 (또는 https://airflow.lawdigest.cloud)
- **계정**: airflow
- **비밀번호**: oracleserver2220!

UI에서 DAG 활성화/비활성화 및 수동 트리거가 가능합니다.

---

## 6. 전체 재가동 스크립트 (한 번에)

```bash
#!/bin/bash
# 모든 자동 스케줄 DAG 활성화

AIRFLOW="docker exec airflow-airflow-webserver-1 airflow dags unpause"

echo "=== 데이터 수집 DAG 활성화 ==="
$AIRFLOW lawdigest_bill_ingest_dag
$AIRFLOW lawdigest_hourly_update_dag

echo "=== AI 배치 DAG 활성화 ==="
$AIRFLOW lawdigest_ai_batch_submit_dag
$AIRFLOW lawdigest_ai_batch_ingest_dag

echo "=== DB 백업 DAG 활성화 ==="
$AIRFLOW lawdigest_daily_db_backup_dag

echo "=== 활성화 결과 확인 ==="
docker exec airflow-airflow-webserver-1 airflow dags list
```

---

## 7. 롤백 (필요 시)

문제 발생 시 전체 DAG을 다시 일시정지합니다.

```bash
for dag in lawdigest_bill_ingest_dag lawdigest_hourly_update_dag \
           lawdigest_ai_batch_submit_dag lawdigest_ai_batch_ingest_dag \
           lawdigest_daily_db_backup_dag; do
  docker exec airflow-airflow-webserver-1 airflow dags pause $dag
  echo "Paused: $dag"
done
```

---

## 8. 참고 문서

- [파이프라인 아키텍처](./pipeline_architecture.md)
- Airflow 롤백 런북: `docs/data/legacy/airflow_rollback_runbook.md`
