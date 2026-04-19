# Gemini Batch Provider Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** OpenAI 요약 경로를 유지한 채 Gemini native Batch API를 추가하고, Airflow DAG에서 provider를 선택할 수 있게 만든다.

**Architecture:** AI 요약 엔트리포인트를 provider-aware 공통 서비스로 재구성하고, 실제 API 차이는 OpenAI/Gemini adapter가 흡수한다. 배치 상태 테이블은 `provider + batch_id` 복합 식별로 확장하고, submit/ingest/instant/repair 4개 흐름을 같은 선택 규약으로 맞춘다.

**Tech Stack:** Python, Airflow DAG, MySQL, OpenAI Batch API, Gemini Batch API, Gemini Files API, pytest, requests, google-genai

---

## File Map

### Create

- `services/ai/src/lawdigest_ai/processor/providers/__init__.py`
- `services/ai/src/lawdigest_ai/processor/providers/types.py`
- `services/ai/src/lawdigest_ai/processor/providers/router.py`
- `services/ai/src/lawdigest_ai/processor/providers/openai_batch.py`
- `services/ai/src/lawdigest_ai/processor/providers/gemini_batch.py`
- `services/ai/src/lawdigest_ai/processor/providers/openai_instant.py`
- `services/ai/src/lawdigest_ai/processor/providers/gemini_instant.py`
- `services/ai/src/lawdigest_ai/processor/provider_batch_service.py`
- `services/ai/src/lawdigest_ai/processor/provider_instant_service.py`
- `services/ai/src/lawdigest_ai/processor/provider_repair_service.py`
- `services/ai/tests/processor/test_provider_router.py`
- `services/ai/tests/processor/test_provider_batch_service.py`
- `services/ai/tests/processor/test_provider_instant_service.py`
- `services/ai/tests/processor/test_provider_repair_service.py`
- `services/ai/tests/processor/test_gemini_batch_provider.py`
- `infra/db/migrations/20260419_add_provider_to_ai_batch_jobs.sql`

### Modify

- `services/ai/pyproject.toml`
- `services/ai/src/lawdigest_ai/config.py`
- `services/ai/src/lawdigest_ai/processor/batch_submit.py`
- `services/ai/src/lawdigest_ai/processor/batch_ingest.py`
- `services/ai/src/lawdigest_ai/processor/batch_utils.py`
- `services/ai/src/lawdigest_ai/processor/instant_summarizer.py`
- `infra/airflow/dags/ai_batch_submit_dag.py`
- `infra/airflow/dags/ai_batch_ingest_dag.py`
- `infra/airflow/dags/manual_ai_summary_instant_dag.py`
- `infra/airflow/dags/manual_ai_summary_repair_dag.py`
- `services/ai/tests/processor/test_entrypoints.py`
- `services/ai/tests/test_config.py`
- `docs/data/pipeline_architecture.md`
- `docs/data/pipeline_restart_runbook.md`

## Implementation Notes

- 모든 구현은 TDD로 진행한다.
- 기존 OpenAI 경로는 regression 없이 유지한다.
- `gemini_ai_summary_repair_dag`는 건드리지 않는다.
- `manual_ai_summary_repair_dag`는 레거시 script import 대신 provider-aware service를 호출하도록 바꾼다.
- `ai_batch_ingest_dag` 기본 provider는 `all`, 나머지 DAG 기본 provider는 `openai`로 둔다.

### Task 1: 설정과 Provider 타입 골격 추가

**Files:**
- Create: `services/ai/src/lawdigest_ai/processor/providers/__init__.py`
- Create: `services/ai/src/lawdigest_ai/processor/providers/types.py`
- Create: `services/ai/src/lawdigest_ai/processor/providers/router.py`
- Test: `services/ai/tests/processor/test_provider_router.py`
- Modify: `services/ai/src/lawdigest_ai/config.py`
- Modify: `services/ai/pyproject.toml`
- Modify: `services/ai/tests/test_config.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_router_returns_openai_batch_provider():
    provider = get_batch_provider("openai")
    assert provider.provider_name == "openai"

def test_router_returns_gemini_instant_provider():
    provider = get_instant_provider("gemini")
    assert provider.provider_name == "gemini"

def test_config_loads_gemini_key(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-test-key")
    assert config.get_gemini_api_key() == "gemini-test-key"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd services/ai && pytest tests/processor/test_provider_router.py tests/test_config.py -v`
Expected: FAIL because router module / Gemini config accessors do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
class ProviderName(str, Enum):
    OPENAI = "openai"
    GEMINI = "gemini"

def get_gemini_api_key() -> str:
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError("GEMINI_API_KEY 환경변수가 설정되어야 합니다.")
    return key
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd services/ai && pytest tests/processor/test_provider_router.py tests/test_config.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add services/ai/pyproject.toml services/ai/src/lawdigest_ai/config.py services/ai/src/lawdigest_ai/processor/providers services/ai/tests/processor/test_provider_router.py services/ai/tests/test_config.py
git commit -m "feat: 프로바이더 라우터와 Gemini 설정 추가"
```

### Task 2: 배치 상태 테이블 provider 확장

**Files:**
- Create: `infra/db/migrations/20260419_add_provider_to_ai_batch_jobs.sql`
- Modify: `services/ai/src/lawdigest_ai/processor/batch_utils.py`
- Test: `services/ai/tests/processor/test_provider_batch_service.py`

- [ ] **Step 1: Write the failing test**

```python
def test_ensure_status_tables_adds_provider_columns():
    sql = load_migration_sql("20260419_add_provider_to_ai_batch_jobs.sql")
    assert "provider VARCHAR(32)" in sql
    assert "uq_ai_batch_jobs_provider_batch" in sql
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd services/ai && pytest tests/processor/test_provider_batch_service.py::test_ensure_status_tables_adds_provider_columns -v`
Expected: FAIL because migration file and new assertions do not exist.

- [ ] **Step 3: Write minimal implementation**

```sql
ALTER TABLE ai_batch_jobs
  ADD COLUMN provider VARCHAR(32) NOT NULL DEFAULT 'openai';
```

Also update `ensure_status_tables()` to create the column and composite unique in fresh installs.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd services/ai && pytest tests/processor/test_provider_batch_service.py::test_ensure_status_tables_adds_provider_columns -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add infra/db/migrations/20260419_add_provider_to_ai_batch_jobs.sql services/ai/src/lawdigest_ai/processor/batch_utils.py services/ai/tests/processor/test_provider_batch_service.py
git commit -m "feat: 배치 상태 테이블에 provider 컬럼 추가"
```

### Task 3: OpenAI batch adapter 추출

**Files:**
- Create: `services/ai/src/lawdigest_ai/processor/providers/openai_batch.py`
- Modify: `services/ai/src/lawdigest_ai/processor/batch_utils.py`
- Modify: `services/ai/tests/processor/test_batch_utils.py`
- Test: `services/ai/tests/processor/test_provider_batch_service.py`

- [ ] **Step 1: Write the failing test**

```python
def test_openai_batch_provider_builds_request_rows():
    provider = OpenAIBatchProvider()
    rows = provider.build_request_rows([sample_bill()], model="gpt-4o-mini")
    assert rows[0]["custom_id"] == "B001"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd services/ai && pytest tests/processor/test_provider_batch_service.py::test_openai_batch_provider_builds_request_rows -v`
Expected: FAIL because `OpenAIBatchProvider` does not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
class OpenAIBatchProvider:
    provider_name = "openai"

    def build_request_rows(self, bills, model):
        return build_batch_request_rows(bills, model=model)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd services/ai && pytest tests/processor/test_batch_utils.py tests/processor/test_provider_batch_service.py -v`
Expected: PASS and no OpenAI regression

- [ ] **Step 5: Commit**

```bash
git add services/ai/src/lawdigest_ai/processor/providers/openai_batch.py services/ai/src/lawdigest_ai/processor/batch_utils.py services/ai/tests/processor/test_batch_utils.py services/ai/tests/processor/test_provider_batch_service.py
git commit -m "refactor: OpenAI 배치 어댑터 분리"
```

### Task 4: Gemini batch adapter 구현

**Files:**
- Create: `services/ai/src/lawdigest_ai/processor/providers/gemini_batch.py`
- Test: `services/ai/tests/processor/test_gemini_batch_provider.py`
- Modify: `services/ai/src/lawdigest_ai/config.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_gemini_batch_provider_builds_jsonl_requests():
    provider = GeminiBatchProvider()
    rows = provider.build_request_rows([sample_bill()], model="gemini-2.5-flash")
    assert rows[0]["key"] == "B001"

def test_gemini_batch_provider_parses_success_output():
    line = gemini_success_line("B001")
    parsed = GeminiBatchProvider().parse_output_line(line)
    assert parsed.bill_id == "B001"
    assert parsed.error is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd services/ai && pytest tests/processor/test_gemini_batch_provider.py -v`
Expected: FAIL because Gemini adapter does not exist.

- [ ] **Step 3: Write minimal implementation**

```python
class GeminiBatchProvider:
    provider_name = "gemini"

    def build_request_rows(self, bills, model):
        return [{"key": bill["bill_id"], "request": build_generate_content_request(bill, model)} for bill in bills]
```

Implement provider methods for:
- request row generation
- file upload
- batch job create
- job status fetch
- output download
- output line parse

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd services/ai && pytest tests/processor/test_gemini_batch_provider.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add services/ai/src/lawdigest_ai/processor/providers/gemini_batch.py services/ai/src/lawdigest_ai/config.py services/ai/tests/processor/test_gemini_batch_provider.py
git commit -m "feat: Gemini 배치 어댑터 구현"
```

### Task 5: Provider-aware batch submit service 연결

**Files:**
- Create: `services/ai/src/lawdigest_ai/processor/provider_batch_service.py`
- Modify: `services/ai/src/lawdigest_ai/processor/batch_submit.py`
- Modify: `infra/airflow/dags/ai_batch_submit_dag.py`
- Modify: `services/ai/tests/processor/test_entrypoints.py`
- Test: `services/ai/tests/processor/test_provider_batch_service.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_submit_batch_routes_to_gemini_provider():
    with patch("...get_batch_provider") as mock_router:
        submit_batch(limit=10, model="gemini-2.5-flash", mode="dry_run", provider="gemini")
    mock_router.assert_called_once_with("gemini")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd services/ai && pytest tests/processor/test_provider_batch_service.py::test_submit_batch_routes_to_gemini_provider tests/processor/test_entrypoints.py -v`
Expected: FAIL because `submit_batch()` has no provider parameter.

- [ ] **Step 3: Write minimal implementation**

```python
def submit_batch(limit=200, model="gpt-4o-mini", mode="dry_run", provider="openai"):
    batch_provider = get_batch_provider(provider)
    return submit_batch_with_provider(batch_provider, limit=limit, model=model, mode=mode)
```

Update DAG params:
- add `provider`
- default `openai`

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd services/ai && pytest tests/processor/test_provider_batch_service.py tests/processor/test_entrypoints.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add services/ai/src/lawdigest_ai/processor/provider_batch_service.py services/ai/src/lawdigest_ai/processor/batch_submit.py infra/airflow/dags/ai_batch_submit_dag.py services/ai/tests/processor/test_provider_batch_service.py services/ai/tests/processor/test_entrypoints.py
git commit -m "feat: 배치 제출에 provider 선택 추가"
```

### Task 6: Provider-aware batch ingest service 연결

**Files:**
- Modify: `services/ai/src/lawdigest_ai/processor/provider_batch_service.py`
- Modify: `services/ai/src/lawdigest_ai/processor/batch_ingest.py`
- Modify: `infra/airflow/dags/ai_batch_ingest_dag.py`
- Test: `services/ai/tests/processor/test_provider_batch_service.py`
- Modify: `services/ai/tests/processor/test_entrypoints.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_ingest_batch_results_supports_provider_all():
    with patch("...fetch_jobs_for_polling") as mock_fetch:
        ingest_batch_results(max_jobs=20, mode="dry_run", provider="all")
    assert mock_fetch.call_args.kwargs["provider"] == "all"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd services/ai && pytest tests/processor/test_provider_batch_service.py::test_ingest_batch_results_supports_provider_all tests/processor/test_entrypoints.py -v`
Expected: FAIL because ingest has no provider parameter.

- [ ] **Step 3: Write minimal implementation**

```python
def ingest_batch_results(max_jobs=10, mode="dry_run", provider="all"):
    jobs = fetch_jobs_for_polling(conn, max_jobs=max_jobs, provider=provider)
    ...
```

Update DAG params:
- add `provider`
- enum includes `all`
- default `all`

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd services/ai && pytest tests/processor/test_provider_batch_service.py tests/processor/test_entrypoints.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add services/ai/src/lawdigest_ai/processor/provider_batch_service.py services/ai/src/lawdigest_ai/processor/batch_ingest.py infra/airflow/dags/ai_batch_ingest_dag.py services/ai/tests/processor/test_provider_batch_service.py services/ai/tests/processor/test_entrypoints.py
git commit -m "feat: 배치 적재에 provider 선택 추가"
```

### Task 7: Provider-aware instant summarize 연결

**Files:**
- Create: `services/ai/src/lawdigest_ai/processor/providers/openai_instant.py`
- Create: `services/ai/src/lawdigest_ai/processor/providers/gemini_instant.py`
- Create: `services/ai/src/lawdigest_ai/processor/provider_instant_service.py`
- Modify: `services/ai/src/lawdigest_ai/processor/instant_summarizer.py`
- Modify: `infra/airflow/dags/manual_ai_summary_instant_dag.py`
- Test: `services/ai/tests/processor/test_provider_instant_service.py`
- Modify: `services/ai/tests/processor/test_entrypoints.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_summarize_single_bill_routes_to_gemini_provider():
    with patch("...get_instant_provider") as mock_router:
        summarize_single_bill({"bill_id": "B001", "summary": "원문"}, provider="gemini")
    mock_router.assert_called_once_with("gemini")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd services/ai && pytest tests/processor/test_provider_instant_service.py tests/processor/test_entrypoints.py -v`
Expected: FAIL because `provider` is unsupported in instant summarize path.

- [ ] **Step 3: Write minimal implementation**

```python
def summarize_single_bill(bill_data, provider="openai", model=None):
    instant_provider = get_instant_provider(provider)
    return instant_provider.summarize_single_bill(bill_data, model=model)
```

Update DAG params:
- add `provider`
- default `openai`

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd services/ai && pytest tests/processor/test_provider_instant_service.py tests/processor/test_entrypoints.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add services/ai/src/lawdigest_ai/processor/providers/openai_instant.py services/ai/src/lawdigest_ai/processor/providers/gemini_instant.py services/ai/src/lawdigest_ai/processor/provider_instant_service.py services/ai/src/lawdigest_ai/processor/instant_summarizer.py infra/airflow/dags/manual_ai_summary_instant_dag.py services/ai/tests/processor/test_provider_instant_service.py services/ai/tests/processor/test_entrypoints.py
git commit -m "feat: 즉시 요약에 provider 선택 추가"
```

### Task 8: manual_ai_summary_repair_dag를 provider-aware service로 교체

**Files:**
- Create: `services/ai/src/lawdigest_ai/processor/provider_repair_service.py`
- Modify: `infra/airflow/dags/manual_ai_summary_repair_dag.py`
- Test: `services/ai/tests/processor/test_provider_repair_service.py`
- Modify: `services/ai/tests/processor/test_entrypoints.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_repair_missing_summaries_routes_to_openai_or_gemini():
    with patch("...get_instant_provider") as mock_router:
        repair_missing_summaries(provider="gemini", mode="dry_run", batch_size=5, output_path="/tmp/out.json")
    mock_router.assert_called_once_with("gemini")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd services/ai && pytest tests/processor/test_provider_repair_service.py -v`
Expected: FAIL because provider-aware repair service does not exist.

- [ ] **Step 3: Write minimal implementation**

```python
def repair_missing_summaries(provider, mode, batch_size, output_path, model=None):
    rows = fetch_missing_bills(...)
    summaries = get_instant_provider(provider).summarize_many(rows, model=model)
    write_report(output_path, summaries)
    if mode != "dry_run":
        upsert_successful_rows(...)
```

Update DAG params:
- add `provider`
- remove dependency on `scripts.find_missing_summaries`
- remove dependency on `scripts.repair_missing_summaries`

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd services/ai && pytest tests/processor/test_provider_repair_service.py tests/processor/test_entrypoints.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add services/ai/src/lawdigest_ai/processor/provider_repair_service.py infra/airflow/dags/manual_ai_summary_repair_dag.py services/ai/tests/processor/test_provider_repair_service.py services/ai/tests/processor/test_entrypoints.py
git commit -m "feat: 수동 요약 복구를 provider 공통 서비스로 전환"
```

### Task 9: 문서와 운영 런북 업데이트

**Files:**
- Modify: `docs/data/pipeline_architecture.md`
- Modify: `docs/data/pipeline_restart_runbook.md`

- [ ] **Step 1: Write the failing doc assertions**

```python
def test_pipeline_docs_mention_provider_selection():
    text = Path("docs/data/pipeline_architecture.md").read_text(encoding="utf-8")
    assert "provider" in text
    assert "Gemini" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest -q docs_doctest_placeholder`
Expected: FAIL or skip if no doc test harness exists. If no harness exists, manually verify diff against spec instead.

- [ ] **Step 3: Write minimal documentation updates**

Update docs to cover:
- provider-aware DAG params
- Gemini native batch path
- ingest `provider=all` default
- Gemini CLI fallback DAG remains separate

- [ ] **Step 4: Verify docs**

Run: `git diff -- docs/data/pipeline_architecture.md docs/data/pipeline_restart_runbook.md`
Expected: provider-aware flow documented with no contradictions to spec.

- [ ] **Step 5: Commit**

```bash
git add docs/data/pipeline_architecture.md docs/data/pipeline_restart_runbook.md
git commit -m "docs: 프로바이더 선택형 AI 파이프라인 문서 반영"
```

### Task 10: 최종 검증

**Files:**
- Verify only

- [ ] **Step 1: Run focused AI processor tests**

Run: `cd services/ai && pytest tests/processor -v`
Expected: PASS

- [ ] **Step 2: Run config and critical regression tests**

Run: `cd services/ai && pytest tests/test_config.py tests/rag/test_embedding.py -v`
Expected: PASS

- [ ] **Step 3: Review DAG parameter diffs**

Run: `git diff -- infra/airflow/dags/ai_batch_submit_dag.py infra/airflow/dags/ai_batch_ingest_dag.py infra/airflow/dags/manual_ai_summary_instant_dag.py infra/airflow/dags/manual_ai_summary_repair_dag.py`
Expected: each DAG exposes intended provider options and defaults.

- [ ] **Step 4: Review working tree**

Run: `git status --short`
Expected: only intended implementation files remain modified.

- [ ] **Step 5: Final commit or squash decision**

```bash
git log --oneline --max-count=10
```

Confirm the commit stack is reviewable before PR or execution handoff.
