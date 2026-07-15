# 법안 제목 필드 전체 마이그레이션 런북

작성일: 2026-07-15

## 목적

법안 카드 제목을 의미하던 `brief_summary` 계열 이름을 `title` 계열로 통일한다.

| 계층 | 이전 계약 | 새 계약 |
| --- | --- | --- |
| `Bill` DB 컬럼 | `brief_summary` | `title` |
| 검색 문서 DB 컬럼 | `brief_summary_text` | `title_text` |
| Python/JSON | `brief_summary`, `briefSummary` | `title` |
| Java | `briefSummary`, `billBriefSummary` | `title`, `billTitle` |
| API JSON | `brief_summary`, `bill_brief_summary`, `billBriefSummary` | `title`, `bill_title`, `billTitle` |

컬럼 이름만 바꾸므로 값은 다시 쓰거나 복사하지 않는다. MySQL 8.0.35에서
`RENAME COLUMN ... ALGORITHM=INSTANT`를 사용한다.

참고: [MySQL 8.0 ALTER TABLE](https://dev.mysql.com/doc/refman/8.0/en/alter-table.html)

## 배포 특성

이 마이그레이션은 구 API와 신 API가 동시에 호환되지 않는 계약 변경이다.

- 구 백엔드는 `Bill.brief_summary`가 사라지면 조회할 수 없다.
- 구 웹은 신 백엔드의 `title` JSON 키를 읽지 못한다.
- 구 AI/data 작업은 사라진 컬럼에 쓰기를 시도한다.
- 운영 백엔드의 `spring.jpa.hibernate.ddl-auto=update` 때문에 신 백엔드를 먼저
  기동하면 `title`이 자동 추가되어 두 컬럼이 공존할 수 있다.

따라서 유지보수 창에서 쓰기 작업과 사용자 트래픽을 멈춘 뒤 DB와 모든 소비자를
함께 전환한다. 신 백엔드 staging 헬스체크도 DB 마이그레이션 이후에만 수행한다.

## 1. 사전 준비

1. 대상 커밋의 AI, data, backend, web 테스트와 린트가 모두 통과했는지 확인한다.
2. DB 백업을 생성하고 복구 가능한 백업인지 확인한다.
3. 새 백엔드와 웹 빌드에 필요한 환경 파일이 준비됐는지 확인한다.
4. `deploy-production.yml`의 변경 감지가 이 마이그레이션을
   `coordinated_migration=true`로 판별해 push 자동 배포를 건너뛰는지 확인한다.
5. 아래 작업을 pause하고 실행 중인 task가 끝났는지 확인한다.

```bash
airflow dags pause bill_ingest_dag
airflow dags pause manual_bill_collect_dag
airflow dags pause bill_status_sync_dag
airflow dags pause ai_batch_submit_dag
airflow dags pause ai_batch_ingest_dag
airflow dags pause gemini_ai_summary_repair_dag
airflow dags pause manual_ai_summary_instant_dag
airflow dags pause manual_ai_summary_repair_dag
```

Airflow 밖에서 실행 중인 AI batch ingest, 수동 repair, data ingest 프로세스도 종료한다.
새 batch 제출은 마이그레이션 완료 전까지 금지한다.

## 2. DB 사전 점검

운영 DB에서 다음 쿼리를 실행한다.

```sql
SELECT VERSION();

SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND (
      (TABLE_NAME = 'Bill' AND COLUMN_NAME IN ('brief_summary', 'title'))
      OR
      (TABLE_NAME = 'BillSearchDocument' AND COLUMN_NAME IN ('brief_summary_text', 'title_text'))
  );

SELECT COUNT(*) AS bill_count,
       SUM(brief_summary IS NULL) AS null_title_count,
       SUM(brief_summary = '') AS empty_title_count
FROM Bill;

SELECT TABLE_NAME
FROM information_schema.VIEWS
WHERE TABLE_SCHEMA = DATABASE()
  AND VIEW_DEFINITION LIKE '%brief_summary%';

SELECT TRIGGER_NAME
FROM information_schema.TRIGGERS
WHERE TRIGGER_SCHEMA = DATABASE()
  AND ACTION_STATEMENT LIKE '%brief_summary%';

SELECT ROUTINE_NAME, ROUTINE_TYPE
FROM information_schema.ROUTINES
WHERE ROUTINE_SCHEMA = DATABASE()
  AND ROUTINE_DEFINITION LIKE '%brief_summary%';

SELECT TABLE_NAME, COLUMN_NAME
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND GENERATION_EXPRESSION LIKE '%brief_summary%';

SHOW FULL PROCESSLIST;
```

진행 조건은 다음과 같다.

- MySQL 8.0.28 이상이다.
- `Bill.brief_summary`와 `BillSearchDocument.brief_summary_text`만 존재한다.
- `title`, `title_text`는 아직 존재하지 않는다.
- 이전 이름을 참조하는 view, trigger, routine, generated column이 없다.
- 장시간 실행 중인 `Bill`/`BillSearchDocument` 쿼리와 대기 중인 쓰기가 없다.

조건이 다르면 마이그레이션을 실행하지 말고 원인을 먼저 해결한다.

## 3. 유지보수 창 진입

1. 웹을 유지보수 응답으로 전환해 API 계약이 다른 구 웹의 접근을 막는다.
2. 운영 백엔드 컨테이너를 중지한다.
3. AI/data/Airflow 쓰기 프로세스가 모두 중지됐는지 다시 확인한다.
4. 백업 시각과 대상 DB 이름을 작업 기록에 남긴다.

## 4. 컬럼 이름 변경

비밀번호를 명령행에 직접 넣지 말고 MySQL defaults 파일이나 환경별 보안 연결 방식을
사용한다.

```bash
mysql --defaults-extra-file=/secure/path/mysql.cnf "$DB_NAME" \
  < infra/db/migrations/20260715_rename_bill_brief_summary_to_title.sql
```

이 스크립트는 각 컬럼이 이미 변경된 경우 해당 단계만 건너뛴다. 이전 이름과 새 이름이
동시에 있거나 둘 다 없으면 실패한다. metadata lock을 10초 안에 얻지 못해도 실패하므로,
대기 시간을 무작정 늘리지 말고 blocker를 확인한다.

## 5. DB 검증

```sql
SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND (
      (TABLE_NAME = 'Bill' AND COLUMN_NAME IN ('brief_summary', 'title'))
      OR
      (TABLE_NAME = 'BillSearchDocument' AND COLUMN_NAME IN ('brief_summary_text', 'title_text'))
  );

SELECT COUNT(*) AS bill_count,
       SUM(title IS NULL) AS null_title_count,
       SUM(title = '') AS empty_title_count
FROM Bill;

SELECT COUNT(*) AS search_document_count,
       SUM(title_text IS NULL) AS null_title_text_count
FROM BillSearchDocument;

SHOW FULL PROCESSLIST;
```

사전 점검의 행 수와 NULL/빈 문자열 수가 동일해야 한다. 이전 컬럼은 없어야 하고 새
컬럼만 있어야 한다.

## 6. 애플리케이션 전환

다음 순서로 같은 커밋을 배포한다.

1. backend: `deploy/deploy-prod-backend.sh <target-worktree>`
2. web: `deploy/deploy-prod-web.sh <target-worktree>`
3. Airflow DAG와 `services/data`, `services/ai` 실행 환경

운영 루트 체크아웃에 다른 작업이 있으면 이를 수정하지 않는다. `main`의 정확한
커밋으로 깨끗한 전용 worktree를 만든 뒤 backend/web 배포 스크립트의 인자로 넘기고,
Airflow는 `AIRFLOW_SKIP_GIT_PULL=true`와 `LAWDIGEST_PROJECT_DIR=<worktree>`로 같은
worktree를 마운트한다.

DB 변경 후 구 백엔드로 자동 rollback하면 구 컬럼이 없어 기동할 수 없다. 백엔드 배포
스크립트의 컨테이너 rollback만 단독으로 신뢰하지 말고 아래 DB rollback까지 함께
수행할 준비를 유지한다.

## 7. 기능 검증

```bash
curl -fsS 'https://api.lawdigest.kr/v1/bill/mainfeed?page=0&size=5' \
  | jq '.data.bill_list[].bill_info_dto | {bill_id, title, old_key: has("brief_summary")}'

curl -fsS 'https://api.lawdigest.kr/v1/timeline?page=0&size=1' \
  | jq '.. | objects | select(has("bill_title")) | {bill_id, bill_title}'
```

확인 항목:

- main feed의 `title`이 비어 있지 않고 설명문이 아니라 제목형 문자열이다.
- main feed에 `brief_summary`가 없다.
- 상세 페이지, 유사 법안, 북마크, 타임라인이 새 제목 키를 표시한다.
- AI instant/batch 결과 JSON에 `title`이 있고 이전 키가 없다.
- 새 법안 ingest 후 `Bill.title`과 `BillSearchDocument.title_text`가 채워진다.
- 백엔드, Airflow, AI/data 로그에 unknown column 또는 JSON 역직렬화 오류가 없다.

모든 검증이 끝난 뒤 유지보수 응답을 해제하고 pause한 DAG를 다시 unpause한다.

## 8. Rollback

애플리케이션 전환에 실패하면 신 프로세스를 중지한 뒤 컬럼명을 원복한다.

```sql
SET SESSION lock_wait_timeout = 10;

ALTER TABLE Bill
    RENAME COLUMN title TO brief_summary,
    ALGORITHM=INSTANT;

ALTER TABLE BillSearchDocument
    RENAME COLUMN title_text TO brief_summary_text,
    ALGORITHM=INSTANT;
```

그 다음 이전 backend, web, data, AI, Airflow 코드를 배포하고 기능 검증 후 작업을
재개한다. 컬럼 rename 자체는 값을 복사하지 않으므로 성공적으로 원복되면 기존 데이터도
같이 보존된다.
