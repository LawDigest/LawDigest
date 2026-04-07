# 경기도 여론조사 수집 파이프라인 계측 설계

**목표:** `polls_ingest_dag`를 경기도 타깃으로 `test` 모드 실행할 수 있게 고정하고, 수집 대상 개수와 전체 실행시간을 로그, XCom, artifact JSON으로 남긴다.

## 범위

- `polls_ingest_dag`의 단계별 반환값에 계측 메타데이터를 추가한다.
- 경기도 전용 타깃 파일을 별도로 둔다.
- DAG 마지막에 실행 요약 태스크를 추가해 전체 실행시간과 단계별 카운트를 집계한다.
- `test` 모드로 실제 실행해 결과 저장과 artifact 생성까지 확인한다.

## 설계

### 1. 타깃 고정

- 새 파일 `services/data/config/poll_targets.gyeonggi.json`을 추가한다.
- 기존 `poll_targets.json`과 동일한 경기도 타깃을 담되, 이번 DAG 실행에서 명시적으로 이 파일을 사용한다.

### 2. 단계별 계측

- `services/data/src/lawdigest_data/polls/workflow.py` 각 step 메서드에서 실행 시작 시각과 종료 시각을 기록한다.
- 각 단계 반환값에 최소한 아래 메타를 넣는다.
  - `elapsed_seconds`
  - `artifact_path`
  - 단계별 주요 건수
- 기존 artifact payload 구조는 깨지 않는다. 단계 artifact는 그대로 저장하고, 최종 요약 artifact만 별도 생성한다.

### 3. 최종 요약

- `infra/airflow/dags/polls_ingest_dag.py`에 `summarize_run` 태스크를 추가한다.
- 이 태스크는 앞선 4개 태스크의 XCom을 읽어 다음 값을 집계한다.
  - `target_count`
  - `fetched_total`
  - `details_total`
  - `parsed_total`
  - `questions_total`
  - `upserted_surveys`
  - `upserted_questions`
  - `total_elapsed_seconds`
- 요약 결과는 로그 출력, XCom 반환, artifact JSON 저장을 모두 수행한다.

### 4. 검증

- 관련 테스트를 먼저 갱신 또는 추가해 계측 필드가 반환값에 포함되는지 확인한다.
- 이후 `polls_ingest_dag`를 `test` 모드 + 경기도 전용 타깃 파일로 1회 실행한다.
- 생성된 artifact와 저장 결과를 확인한다.

## 리스크

- 실제 `test` 모드 실행은 외부 NESDC 응답 상태와 테스트 DB 연결 상태에 영향을 받는다.
- 기존 artifact 소비 코드가 단계 반환값을 엄격하게 기대한다면 메타 필드 추가 시 영향이 없는지 확인이 필요하다.
