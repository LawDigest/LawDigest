# Gemini Batch Provider Design

작성일: 2026-04-19

## 1. 배경

현재 Lawdigest AI 요약 파이프라인은 OpenAI 경로와 Gemini CLI 경로가 분리되어 있다.

- 배치 요약은 OpenAI Batch API 전용 구현이다.
- 단건 즉시 요약은 OpenAI 기반 `AISummarizer`를 사용한다.
- Gemini는 `gemini_ai_summary_repair_dag`와 CLI 요약기 중심의 별도 fallback 경로로만 존재한다.

이 구조에서는 다음 문제가 있다.

- Airflow DAG에서 프로바이더를 고를 수 없다.
- OpenAI 배치 상태 테이블이 단일 프로바이더를 전제로 설계되어 있다.
- 수동 결측 복구 DAG는 레거시 스크립트 import 의존이 있어 구조가 불안정하다.
- Gemini native Batch API를 활용하지 못하고 있다.

이번 작업의 목적은 기존 OpenAI 경로를 유지하면서 Gemini native Batch API를 추가하고, Airflow DAG 수준에서 프로바이더를 선택 가능하게 만드는 것이다.

## 2. 목표

- 기존 OpenAI batch submit / ingest 경로를 유지한다.
- Gemini native Batch API 기반의 batch submit / ingest 경로를 추가한다.
- Airflow DAG 파라미터로 `provider`를 선택할 수 있게 한다.
- 적용 범위는 아래 네 개의 DAG이다.
  - `ai_batch_submit_dag`
  - `ai_batch_ingest_dag`
  - `manual_ai_summary_instant_dag`
  - `manual_ai_summary_repair_dag`
- 공통 인터페이스 뒤에 프로바이더별 구현을 배치하는 adapter 구조로 리팩터링한다.

## 3. 비목표

- `gemini_ai_summary_repair_dag` 제거 또는 공통 구조로 통합하지 않는다.
- RAG / 임베딩 provider 확장은 이번 범위에 포함하지 않는다.
- UI에서 provider를 선택하는 기능은 추가하지 않는다.
- 다중 provider 동시 submit 스케줄링은 다루지 않는다.

## 4. 현재 구조 요약

### 4.1 OpenAI 배치

- `services/ai/src/lawdigest_ai/processor/batch_submit.py`
- `services/ai/src/lawdigest_ai/processor/batch_ingest.py`
- `services/ai/src/lawdigest_ai/processor/batch_utils.py`

현재 배치 유틸은 다음 책임을 함께 가진다.

- OpenAI 배치 요청 JSONL 생성
- 파일 업로드 / batch 생성 / 상태 조회 / 결과 다운로드
- 상태 테이블 생성 및 갱신
- 결과 JSONL 파싱 및 `Bill` 반영

### 4.2 즉시 요약

- `services/ai/src/lawdigest_ai/processor/instant_summarizer.py`
- `services/ai/src/lawdigest_ai/processor/summarizer.py`

즉시 요약은 OpenAI 기반 `AISummarizer`와 Gemini CLI 전용 함수가 혼재한다.

### 4.3 Gemini CLI 복구

- `infra/airflow/dags/gemini_ai_summary_repair_dag.py`
- `services/ai/src/lawdigest_ai/processor/gemini_repair_pipeline.py`

이 경로는 batch API가 아니라 `batch_size` 단위의 내부 묶음 처리이다.

## 5. 제안 구조

핵심 원칙은 "DAG는 프로바이더만 선택하고, 프로바이더별 API 차이는 adapter가 흡수한다"이다.

### 5.1 공통 서비스 엔트리포인트

아래 네 개의 공통 엔트리포인트를 제공한다.

- `submit_batch(provider, limit, model, mode)`
- `ingest_batch_results(provider, max_jobs, mode)`
- `summarize_single_bill(provider, bill_data, model=None)`
- `repair_missing_summaries(provider, mode, batch_size, output_path, model=None)`

Airflow DAG는 이 엔트리포인트만 호출한다.

### 5.2 Adapter 계층

새 디렉터리 구조를 추가한다.

```text
services/ai/src/lawdigest_ai/processor/providers/
  __init__.py
  types.py
  batch_base.py
  instant_base.py
  router.py
  openai_batch.py
  gemini_batch.py
  openai_instant.py
  gemini_instant.py
```

역할은 다음과 같다.

- `types.py`
  - provider enum / 공통 request / 공통 result 타입 정의
- `batch_base.py`
  - batch provider가 구현해야 하는 인터페이스 정의
- `instant_base.py`
  - 즉시 요약 provider 인터페이스 정의
- `router.py`
  - `provider` 문자열을 받아 적절한 adapter 반환
- `openai_batch.py`
  - 기존 `batch_utils.py` 책임 중 OpenAI API 호출과 포맷 처리만 이관
- `gemini_batch.py`
  - Gemini Files / Batch API 연동과 응답 파싱 구현
- `openai_instant.py`
  - 기존 `AISummarizer` 기반 단건/복수 요약 래핑
- `gemini_instant.py`
  - Gemini native 텍스트 생성 기반 단건/복수 요약 구현

### 5.3 기존 파일 정리 방향

- `batch_submit.py`, `batch_ingest.py`는 provider 공통 서비스 진입점으로 축소한다.
- `batch_utils.py`는 더 이상 "공통 배치 유틸"이 아니므로 OpenAI 전용 유틸로 역할을 축소하거나 `providers/openai_batch.py`로 분해한다.
- `instant_summarizer.py`는 provider 공통 서비스 또는 어댑터 래퍼를 호출하도록 정리한다.

## 6. Gemini 경로 설계

### 6.1 Batch submit

Gemini native Batch API를 사용한다.

- 입력은 JSONL 파일 기반으로 생성한다.
- 각 행은 `bill_id`를 식별 키로 포함한다.
- 본문은 Gemini `GenerateContentRequest` 포맷으로 작성한다.
- File API 업로드 후 batch job을 생성한다.

공통 정규화 기준은 기존 DB 저장 형식에 맞춘다.

- `brief_summary`
- `gpt_summary`
- `summary_tags`

### 6.2 Batch ingest

batch job 상태를 조회하고 완료 시 결과 파일을 다운로드한다.

- 진행 중 상태는 상태 테이블만 갱신한다.
- 완료 상태는 결과 파일을 파싱해 `Bill`과 `ai_batch_items`를 갱신한다.
- 실패 상태는 `ai_batch_items.error_message`와 `ai_batch_jobs.error_message`에 반영한다.

### 6.3 Instant / Repair

Gemini 단건 요약과 수동 결측 복구는 CLI가 아니라 native text generation 경로를 사용한다.

이유는 다음과 같다.

- Airflow에서 provider 선택의 의미를 "실제 API provider 선택"으로 맞출 수 있다.
- Gemini Batch와 Gemini Instant가 같은 인증 체계와 모델 설정을 공유할 수 있다.
- CLI 경로는 별도 fallback DAG로 남겨 역할을 분리할 수 있다.

## 7. OpenAI 경로 유지 전략

OpenAI는 동작을 바꾸지 않는다.

- 기존 JSONL 포맷 유지
- 기존 상태 테이블 사용
- 기존 batch submit / ingest semantics 유지
- 기존 `AISummarizer` 기반 즉시 요약 유지

다만 외부에서 볼 때는 모두 provider 공통 엔트리포인트 뒤로 들어가게 만든다.

## 8. DB 스키마 변경

현재 `ai_batch_jobs`는 `batch_id` 단일 유니크 구조라서 OpenAI와 Gemini를 동시에 저장하기 어렵다.

### 8.1 변경안

`ai_batch_jobs`에 다음 컬럼을 추가한다.

- `provider VARCHAR(32) NOT NULL DEFAULT 'openai'`

기존 `batch_id` 컬럼은 이름을 유지한다.

- 의미는 "원격 provider batch job id"로 재해석한다.
- 이름을 `remote_job_id`로 바꾸지 않는 이유는 기존 코드와 마이그레이션 리스크를 줄이기 위해서다.

제약 조건은 다음으로 변경한다.

- 기존: `batch_id UNIQUE`
- 변경: `UNIQUE KEY uq_ai_batch_jobs_provider_batch (provider, batch_id)`

인덱스는 다음을 추가한다.

- `INDEX idx_ai_batch_jobs_provider_status_created (provider, status, created_at)`

### 8.2 유지 항목

아래 컬럼은 공통으로 유지한다.

- `input_file_id`
- `output_file_id`
- `error_file_id`
- `model_name`
- `status`
- `success_count`
- `failed_count`

Gemini와 OpenAI 모두 파일 기반 식별자와 상태 카운트를 공통으로 기록할 수 있다.

### 8.3 ai_batch_items

`ai_batch_items`는 1차 범위에서 스키마 변경 없이 유지한다.

- `job_id`를 통해 provider 문맥을 얻는다.
- `custom_id`에는 내부 식별자(`bill_id`)를 저장한다.

## 9. Airflow DAG 설계

### 9.1 ai_batch_submit_dag

새 파라미터를 추가한다.

- `provider: openai | gemini`
- `model: string`

기본값:

- `provider = openai`

의도:

- 현재 운영 기본 동작을 유지한다.
- 필요 시 수동 트리거 또는 기본값 변경으로 Gemini submit을 사용할 수 있다.

### 9.2 ai_batch_ingest_dag

새 파라미터를 추가한다.

- `provider: openai | gemini | all`

기본값:

- `provider = all`

의도:

- 스케줄 ingest가 두 provider의 pending job을 모두 회수할 수 있게 한다.
- 수동으로 특정 provider만 조회하고 싶을 때도 지원한다.

### 9.3 manual_ai_summary_instant_dag

새 파라미터를 추가한다.

- `provider: openai | gemini`
- 선택적으로 `model: string`

기본값:

- `provider = openai`

### 9.4 manual_ai_summary_repair_dag

새 파라미터를 추가한다.

- `provider: openai | gemini`
- 선택적으로 `model: string`

기본값:

- `provider = openai`

## 10. manual_ai_summary_repair_dag 정리

현재 DAG는 레거시 스크립트 import 의존을 가진다.

- `scripts.find_missing_summaries`
- `scripts.repair_missing_summaries`

이번 설계에서는 이 DAG를 공통 서비스로 교체한다.

- 누락 법안 조회
- provider별 요약 수행
- dry_run / test / prod 반영
- JSON 산출물 저장

이렇게 하면 OpenAI와 Gemini 모두 동일한 수동 복구 UX를 제공할 수 있고, 현재 import 경로 의존도 제거된다.

## 11. 설정과 의존성

### 11.1 config.py

다음 설정을 추가한다.

- `get_gemini_api_key()`
- `GEMINI_API_KEY`
- `GEMINI_BATCH_MODEL`
- `GEMINI_INSTANT_MODEL`

기존 설정은 유지한다.

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `SUMMARY_STRUCTURED_MODEL`
- `SUMMARY_STRUCTURED_FALLBACK_MODEL`
- `GEMINI_CLI_*`

### 11.2 의존성

`services/ai/pyproject.toml`에 Gemini native SDK를 추가한다.

- `google-genai`

기존 OpenAI / pydantic-ai 의존성은 그대로 유지한다.

## 12. 테스트 전략

TDD로 진행한다.

### 12.1 먼저 추가할 실패 테스트

- provider router가 `openai`, `gemini`를 올바르게 반환하는지
- Gemini batch request JSONL 행 생성이 기대 구조를 따르는지
- Gemini batch output parser가 성공 / 실패 케이스를 올바르게 정규화하는지
- `provider=all` ingest가 두 provider job을 함께 조회하는지
- instant summarize가 provider에 따라 다른 adapter를 호출하는지
- manual repair가 provider에 따라 다른 repair 경로를 호출하는지

### 12.2 유지할 회귀 테스트

- 기존 OpenAI batch utils 테스트
- 기존 instant summarize 테스트
- 기존 Gemini CLI repair 테스트

## 13. 롤아웃 순서

1. DB migration 추가
2. provider interface와 router 추가
3. OpenAI adapter 추출
4. Gemini batch adapter 구현
5. Gemini instant adapter 구현
6. 공통 submit / ingest / instant / repair 서비스 연결
7. Airflow DAG 파라미터 변경
8. 테스트 / 문서 / 런북 업데이트

## 14. 리스크와 대응

### 14.1 Gemini 응답 포맷 차이

대응:

- provider별 output parser 분리
- 공통 결과 타입으로 정규화 후 DB 반영

### 14.2 상태 테이블 마이그레이션 리스크

대응:

- 컬럼명 rename 대신 `provider` 확장 방식 채택
- 기존 OpenAI job과 backward compatibility 유지

### 14.3 운영 기본값 변경 리스크

대응:

- submit 기본값은 `openai` 유지
- ingest는 `all` 기본값으로 안전하게 회수

### 14.4 Gemini CLI 경로와의 역할 중첩

대응:

- CLI 경로는 `gemini_ai_summary_repair_dag` fallback 용도로 남긴다.
- 새 DAG provider 선택은 native API 경로로 제한한다.

## 15. 결정 사항 요약

- 구현 방식은 provider adapter 구조를 채택한다.
- Gemini는 native Batch API를 사용한다.
- OpenAI 경로는 유지한다.
- Airflow에서 provider를 선택할 수 있게 한다.
- `ai_batch_jobs`는 `provider + batch_id` 복합 유니크로 확장한다.
- `ai_batch_ingest_dag`는 `provider=all` 기본값을 사용한다.
- `manual_ai_summary_repair_dag`는 레거시 스크립트 의존을 걷어내고 공통 provider-aware 서비스로 교체한다.
