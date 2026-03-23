# AI 서비스 독립화 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `services/ai`를 독립적인 AI 서비스로 확장하여 (1) DB 데이터의 AI 가공 및 (2) RAG 기반 챗봇 응답 두 가지 책임을 담당하게 하고, 데이터 파이프라인(`services/data`)은 수집→DB 적재에만 집중하도록 책임을 분리한다.

**Architecture:** `services/ai`는 두 개의 독립 모듈을 갖는다: `processor` (DB에서 미가공 데이터를 읽어 AI로 처리 후 다시 DB에 쓰는 배치 프로세서)와 `rag` (Qdrant 벡터 DB + LLM을 사용해 챗봇 질의응답을 제공하는 RAG 파이프라인). `services/data`에서는 AI 요약 호출 코드를 제거하고, 수집→정제→DB 적재 흐름만 남긴다. Airflow DAG은 두 서비스를 각각 독립적으로 오케스트레이션한다.

**Tech Stack:** Python 3.10+, pydantic-ai (OpenAI), pymysql (MySQL RDS), qdrant-client, sentence-transformers / OpenAI embeddings, langchain (RAG 체인), Airflow (오케스트레이션)

---

## 현재 상태 분석

### 현재 AI 기능 위치

| 기능 | 현재 위치 | 이관 대상 |
|------|---------|---------|
| 구조화 AI 요약 (즉시) | `services/ai/src/lawdigest_ai_summarizer/AISummarizer.py` | 유지 + 확장 |
| 배치 요약 유틸 | `services/data/src/lawdigest_data_pipeline/ai_batch_pipeline_utils.py` | → `services/ai` |
| WorkFlowManager의 `summarize_bill_step` | `services/data/src/lawdigest_data_pipeline/WorkFlowManager.py` | → DAG 레이어로 이동 |
| 임베딩 생성 | `services/data/src/lawdigest_ai/embedding_generator.py` | → `services/ai` |
| Qdrant 관리 | `services/data/src/lawdigest_ai/qdrant_manager.py` | → `services/ai` |
| 벡터 DB 업데이트 툴 | `services/data/tools/update_vector_db.py` | → `services/ai/tools/` |

### 현재 Airflow DAG의 AI 관련 항목

| DAG | 현재 import | 변경 방향 |
|-----|-----------|---------|
| `lawdigest_ai_summary_instant_dag.py` | `WorkFlowManager.summarize_bill_step` | `lawdigest_ai.processor.instant_summarizer` |
| `lawdigest_ai_batch_submit_dag.py` | `ai_batch_pipeline_utils.*` | `lawdigest_ai.processor.batch_submit` |
| `lawdigest_ai_batch_ingest_dag.py` | `ai_batch_pipeline_utils.*` | `lawdigest_ai.processor.batch_ingest` |
| `lawdigest_ai_summary_batch_dag.py` | `ai_batch_pipeline_utils.*` | `lawdigest_ai.processor.batch_repair` |
| `lawdigest_hourly_update_dag.py` | `WorkFlowManager` (AI 요약 포함) | `WorkFlowManager`에서 AI 호출 제거 |

---

## 목표 파일 구조

```
services/ai/
├── src/
│   └── lawdigest_ai/                         # 메인 패키지 (기존 lawdigest_ai_summarizer 대체)
│       ├── __init__.py
│       ├── config.py                          # 환경변수 통합 설정
│       ├── db.py                              # DB 연결 유틸 (ai_batch_pipeline_utils에서 이관)
│       │
│       ├── processor/                         # 책임 1: DB 데이터 AI 가공
│       │   ├── __init__.py
│       │   ├── summarizer.py                  # AISummarizer 이관 (기존 services/ai에서 이동)
│       │   ├── batch_utils.py                 # ai_batch_pipeline_utils 이관 (핵심 로직)
│       │   ├── instant_summarizer.py          # 즉시 요약 진입점 (DAG에서 호출)
│       │   ├── batch_submit.py                # 배치 제출 진입점 (DAG에서 호출)
│       │   └── batch_ingest.py                # 배치 결과 수집 진입점 (DAG에서 호출)
│       │
│       └── rag/                               # 책임 2: RAG 챗봇 파이프라인
│           ├── __init__.py
│           ├── embedding.py                   # EmbeddingGenerator 이관
│           ├── vector_store.py                # QdrantManager 이관 + 검색 기능 추가
│           └── chatbot.py                     # RAG 체인 (LLM + 검색 결합)
│
├── tools/
│   └── update_vector_db.py                    # 벡터 DB 업데이트 스크립트 (이관)
│
├── pyproject.toml                             # 패키지명 lawdigest-ai, 의존성 업데이트
├── requirements.txt
└── README.md

services/data/                                 # 변경: AI 코드 제거
├── src/
│   ├── lawdigest_data_pipeline/
│   │   ├── WorkFlowManager.py                 # 변경: summarize_bill_step, AISummarizer import 제거
│   │   ├── ai_batch_pipeline_utils.py         # 삭제 (services/ai로 이관 완료 후)
│   │   ├── AISummarizer.py                    # 삭제 (services/data 내 래퍼)
│   │   └── ...
│   └── lawdigest_ai/                          # 삭제 (services/ai로 이관 완료 후)
│       └── ...
└── tools/
    └── update_vector_db.py                    # 삭제 (services/ai/tools/로 이관)

infra/airflow/dags/                            # 변경: import 경로 업데이트
├── lawdigest_ai_summary_instant_dag.py        # import 경로: lawdigest_ai.processor.instant_summarizer
├── lawdigest_ai_batch_submit_dag.py           # import 경로: lawdigest_ai.processor.batch_submit
├── lawdigest_ai_batch_ingest_dag.py           # import 경로: lawdigest_ai.processor.batch_ingest
├── lawdigest_ai_summary_batch_dag.py          # import 경로: lawdigest_ai.processor.batch_ingest (repair 모드)
└── lawdigest_hourly_update_dag.py             # 변경: AI 요약 태스크 분리 (별도 DAG 또는 제거)
```

---

## Task 1: services/ai 패키지 기반 구조 설정

**Files:**
- Modify: `services/ai/pyproject.toml`
- Create: `services/ai/src/lawdigest_ai/__init__.py`
- Create: `services/ai/src/lawdigest_ai/config.py`
- Create: `services/ai/src/lawdigest_ai/db.py`
- Create: `services/ai/src/lawdigest_ai/processor/__init__.py`
- Create: `services/ai/src/lawdigest_ai/rag/__init__.py`

- [ ] **Step 1: 테스트 파일 작성 (RED)**

`services/ai/tests/test_config.py` 생성:

```python
import pytest
import os

def test_config_loads_openai_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    from lawdigest_ai.config import get_openai_api_key
    assert get_openai_api_key() == "test-key"

def test_config_raises_without_openai_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("APIKEY_OPENAI", raising=False)
    from lawdigest_ai import config
    import importlib
    importlib.reload(config)
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        config.get_openai_api_key()

def test_db_config_prod(monkeypatch):
    monkeypatch.setenv("DB_HOST", "prod-host")
    monkeypatch.setenv("DB_PORT", "3306")
    monkeypatch.setenv("DB_USER", "user")
    monkeypatch.setenv("DB_PASSWORD", "pass")
    monkeypatch.setenv("DB_NAME", "lawdb")
    from lawdigest_ai.db import get_prod_db_config
    cfg = get_prod_db_config()
    assert cfg["host"] == "prod-host"
    assert cfg["port"] == 3306
```

- [ ] **Step 2: 테스트 실행 - 실패 확인**

```bash
cd /home/ubuntu/project/Lawdigest/services/ai
python -m pytest tests/test_config.py -v
```

Expected: `ModuleNotFoundError: No module named 'lawdigest_ai'`

- [ ] **Step 3: pyproject.toml 업데이트**

`services/ai/pyproject.toml`를 다음으로 교체:

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "lawdigest-ai"
version = "0.2.0"
description = "모두의입법 AI 서비스 - 데이터 AI 가공 및 RAG 챗봇 파이프라인"
readme = "README.md"
authors = [
  { name = "Minjae Park", email = "parkmj9260@gmail.com" }
]
requires-python = ">=3.10"
dependencies = [
  "pandas>=2.2.0",
  "python-dotenv",
  "pydantic>=2.0",
  "pydantic-ai-slim[openai]>=0.7.0",
  "openai>=1.50.0",
  "pymysql>=1.1.0",
  "requests>=2.31.0",
  "qdrant-client>=1.12.0",
  "sentence-transformers",
  "langchain>=0.3.0",
  "langchain-openai>=0.2.0",
  "langchain-community>=0.3.0",
]

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]
```

- [ ] **Step 4: 패키지 디렉토리 구조 생성**

```bash
mkdir -p services/ai/src/lawdigest_ai/processor
mkdir -p services/ai/src/lawdigest_ai/rag
mkdir -p services/ai/tests
touch services/ai/src/lawdigest_ai/__init__.py
touch services/ai/src/lawdigest_ai/processor/__init__.py
touch services/ai/src/lawdigest_ai/rag/__init__.py
touch services/ai/tests/__init__.py
```

- [ ] **Step 5: `config.py` 작성**

`services/ai/src/lawdigest_ai/config.py`:

```python
from __future__ import annotations
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_USE_HTTPS = os.getenv("QDRANT_USE_HTTPS", "false").lower() in ("true", "1", "yes")


def get_openai_api_key() -> str:
    key = os.getenv("OPENAI_API_KEY") or os.getenv("APIKEY_OPENAI")
    if not key:
        raise ValueError("OPENAI_API_KEY 또는 APIKEY_OPENAI 환경변수가 설정되어야 합니다.")
    return key
```

- [ ] **Step 6: `db.py` 작성 (ai_batch_pipeline_utils에서 DB 연결 로직 이관)**

`services/ai/src/lawdigest_ai/db.py`:

```python
from __future__ import annotations
import os
from typing import Any, Dict
import pymysql
from dotenv import load_dotenv

load_dotenv()

_ENV_DOTENV_PATH = "/opt/airflow/project/.env"


def _read_dotenv(path: str) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if not os.path.exists(path):
        return values
    with open(path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            normalized = value.strip().strip("\"'")
            values[key.strip()] = normalized
    return values


def get_prod_db_config() -> Dict[str, Any]:
    env = _read_dotenv(_ENV_DOTENV_PATH)
    host = os.getenv("DB_HOST") or env.get("DB_HOST")
    port = os.getenv("DB_PORT") or env.get("DB_PORT")
    user = os.getenv("DB_USER") or env.get("DB_USER")
    password = os.getenv("DB_PASSWORD") or env.get("DB_PASSWORD")
    database = os.getenv("DB_NAME") or env.get("DB_NAME")
    missing = [k for k, v in {"DB_HOST": host, "DB_PORT": port, "DB_USER": user,
                               "DB_PASSWORD": password, "DB_NAME": database}.items() if not v]
    if missing:
        raise ValueError(f"운영 DB 환경변수 누락: {', '.join(missing)}")
    return {"host": host, "port": int(port), "user": user, "password": password, "database": database}


def get_test_db_config() -> Dict[str, Any]:
    env = _read_dotenv(_ENV_DOTENV_PATH)
    host = os.getenv("TEST_DB_HOST") or env.get("TEST_DB_HOST")
    port = os.getenv("TEST_DB_PORT") or env.get("TEST_DB_PORT")
    user = os.getenv("TEST_DB_USER") or env.get("TEST_DB_USER")
    password = os.getenv("TEST_DB_PASSWORD") or env.get("TEST_DB_PASSWORD")
    database = os.getenv("TEST_DB_NAME") or env.get("TEST_DB_NAME")
    missing = [k for k, v in {"TEST_DB_HOST": host, "TEST_DB_PORT": port, "TEST_DB_USER": user,
                               "TEST_DB_PASSWORD": password, "TEST_DB_NAME": database}.items() if not v]
    if missing:
        raise ValueError(f"테스트 DB 환경변수 누락: {', '.join(missing)}")
    return {"host": host, "port": int(port), "user": user, "password": password, "database": database}


def get_db_connection(mode: str = "test") -> pymysql.connections.Connection:
    cfg = get_prod_db_config() if mode == "prod" else get_test_db_config()
    return pymysql.connect(
        host=cfg["host"], port=cfg["port"], user=cfg["user"],
        password=cfg["password"], db=cfg["database"],
        charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )
```

- [ ] **Step 7: 테스트 재실행 - 통과 확인**

```bash
cd /home/ubuntu/project/Lawdigest/services/ai
pip install -e . -q
python -m pytest tests/test_config.py -v
```

Expected: 모든 테스트 PASS

- [ ] **Step 8: 커밋**

```bash
git add services/ai/pyproject.toml services/ai/src/lawdigest_ai/ services/ai/tests/
git commit -m "feat: services/ai 패키지 기반 구조 설정 및 config/db 모듈 추가"
```

---

## Task 2: processor 모듈 - AI 요약 코드 이관

**Files:**
- Create: `services/ai/src/lawdigest_ai/processor/summarizer.py` (기존 AISummarizer 이관)
- Create: `services/ai/src/lawdigest_ai/processor/batch_utils.py` (ai_batch_pipeline_utils 핵심 로직 이관)
- Create: `services/ai/tests/processor/test_summarizer.py`
- Create: `services/ai/tests/processor/test_batch_utils.py`

- [ ] **Step 1: 테스트 파일 작성 (RED)**

`services/ai/tests/processor/test_summarizer.py`:

```python
import pytest
from unittest.mock import MagicMock, patch
import pandas as pd

def test_summarizer_skips_already_summarized():
    from lawdigest_ai.processor.summarizer import AISummarizer
    summarizer = AISummarizer()
    df = pd.DataFrame([{
        "bill_id": "B001", "bill_name": "테스트법", "summary": "내용",
        "brief_summary": "이미 요약됨", "gpt_summary": "상세 요약 있음",
        "proposers": "홍길동", "proposer_kind": "의원발의",
        "proposeDate": "2024-01-01", "stage": "위원회"
    }])
    result = summarizer.AI_structured_summarize(df)
    assert len(result) == 1
    assert result.iloc[0]["brief_summary"] == "이미 요약됨"

def test_summarizer_processes_unsummarized():
    from lawdigest_ai.processor.summarizer import AISummarizer, StructuredBillSummary
    mock_result = StructuredBillSummary(
        brief_summary="요약 제목",
        gpt_summary="상세 요약 내용",
        tags=["세금", "부동산", "의회", "법안", "개정"]
    )
    with patch.object(AISummarizer, "_summarize_one", return_value=mock_result):
        summarizer = AISummarizer()
        df = pd.DataFrame([{
            "bill_id": "B002", "bill_name": "새법안", "summary": "원문",
            "brief_summary": None, "gpt_summary": None,
            "proposers": "김의원", "proposer_kind": "의원발의",
            "proposeDate": "2024-01-01", "stage": "본회의"
        }])
        result = summarizer.AI_structured_summarize(df)
    assert result.iloc[0]["brief_summary"] == "요약 제목"
    assert result.iloc[0]["gpt_summary"] == "상세 요약 내용"
```

`services/ai/tests/processor/test_batch_utils.py`:

```python
import json
import pytest
from lawdigest_ai.processor.batch_utils import (
    build_batch_request_rows,
    parse_output_jsonl_line,
    BatchStructuredSummary,
)

def test_build_batch_request_rows_structure():
    bills = [{"bill_id": "B001", "bill_name": "테스트법", "summary": "내용",
               "proposers": "홍길동", "proposer_kind": "의원", "propose_date": "2024-01-01", "stage": "위원회"}]
    rows = build_batch_request_rows(bills, model="gpt-4o-mini")
    assert len(rows) == 1
    assert rows[0]["custom_id"] == "B001"
    assert rows[0]["body"]["model"] == "gpt-4o-mini"

def test_parse_output_jsonl_line_success():
    summary = BatchStructuredSummary(
        brief_summary="요약", gpt_summary="상세", tags=["a","b","c","d","e"]
    )
    content = summary.model_dump_json(by_alias=True)
    line = json.dumps({
        "custom_id": "B001",
        "response": {
            "status_code": 200,
            "body": {"choices": [{"message": {"content": content}}]}
        }
    })
    bill_id, brief, gpt, tags, err = parse_output_jsonl_line(line)
    assert bill_id == "B001"
    assert brief == "요약"
    assert err is None

def test_parse_output_jsonl_line_error():
    line = json.dumps({
        "custom_id": "B001",
        "response": {"status_code": 500, "body": {}}
    })
    bill_id, brief, gpt, tags, err = parse_output_jsonl_line(line)
    assert err is not None
    assert brief is None

def test_apply_batch_results_success_and_partial_failure():
    """성공 라인과 실패 라인이 섞인 JSONL에서 각각 올바르게 처리되는지 확인."""
    from lawdigest_ai.processor.batch_utils import apply_batch_results, BatchStructuredSummary
    import json

    summary = BatchStructuredSummary(
        brief_summary="요약", gpt_summary="상세", tags=["a","b","c","d","e"]
    )
    success_line = json.dumps({
        "custom_id": "B001",
        "response": {"status_code": 200, "body": {"choices": [{"message": {"content": summary.model_dump_json(by_alias=True)}}]}}
    })
    fail_line = json.dumps({
        "custom_id": "B002",
        "response": {"status_code": 500, "body": {}}
    })
    output_jsonl = success_line + "\n" + fail_line

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
    mock_cursor.__exit__ = MagicMock(return_value=False)
    mock_cursor.rowcount = 0
    mock_conn.cursor.return_value = mock_cursor

    success, failed = apply_batch_results(mock_conn, job_id=1, output_jsonl=output_jsonl)
    assert success == 1
    assert failed == 1
```

- [ ] **Step 2: 테스트 실행 - 실패 확인**

```bash
cd /home/ubuntu/project/Lawdigest/services/ai
python -m pytest tests/processor/ -v
```

Expected: `ModuleNotFoundError: No module named 'lawdigest_ai.processor.summarizer'`

- [ ] **Step 3: summarizer.py 작성 (기존 AISummarizer 이관)**

`services/ai/src/lawdigest_ai/processor/summarizer.py`:

기존 `services/ai/src/lawdigest_ai_summarizer/AISummarizer.py`의 내용을 복사하되, import 경로를 새 패키지 구조에 맞게 수정:

```python
# services/ai/src/lawdigest_ai/processor/summarizer.py
# 기존 services/ai/src/lawdigest_ai_summarizer/AISummarizer.py에서 이관
from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional

import pandas as pd
from pydantic import BaseModel, Field

try:
    from pydantic_ai import Agent
except ImportError as exc:
    raise ImportError("pydantic-ai가 설치되어야 합니다.") from exc


class StructuredBillSummary(BaseModel):
    brief_summary: str = Field(description="법안 핵심을 한 문장으로 요약한 짧은 제목형 요약문")
    gpt_summary: str = Field(description="법안에서 달라지는 핵심 내용을 3~7개 항목으로 정리한 상세 요약문")
    tags: list[str] = Field(min_length=5, max_length=5, description="법안 주제를 나타내는 짧은 한국어 태그 5개")


class AISummarizer:
    def __init__(self):
        self.failed_bills: List[dict] = []
        self.logger = logging.getLogger(__name__)
        self.primary_model = os.environ.get("SUMMARY_STRUCTURED_MODEL", "openai:gpt-4o-mini")
        self.fallback_model = os.environ.get("SUMMARY_STRUCTURED_FALLBACK_MODEL", "openai:gpt-4o-mini")
        self.style_prompt = (
            "법률개정안 텍스트에서 달라지는 핵심 내용을 항목별로 정리하세요. "
            "각 항목은 이해하기 쉬운 공식 문체로 작성하고, 3~7개 항목을 권장합니다."
        )

    def _build_agent(self, model_name: str) -> Agent:
        return Agent(
            model=model_name,
            output_type=StructuredBillSummary,
            system_prompt="당신은 대한민국 법안 요약 전문가입니다. 반드시 structured output 스키마에 맞춰 응답하세요.",
        )

    def _build_user_prompt(self, row: Dict[str, Any]) -> str:
        intro = (
            f"[법안명] {row.get('bill_name') or '법안명 미상'}\n"
            f"[발의주체] {row.get('proposer_kind') or ''}\n"
            f"[발의자] {row.get('proposers') or '발의자 미상'}\n"
            f"[발의일] {row.get('proposeDate') or row.get('propose_date') or ''}\n"
            f"[단계] {row.get('stage') or ''}\n"
        )
        task = (
            f"{self.style_prompt}\n"
            "1) brief_summary: 한 문장 제목형 요약\n"
            "2) gpt_summary: 핵심 변경사항 상세 요약\n"
            "3) tags: 한국어 태그 정확히 5개 (중복 금지, 각 2~12자)\n"
        )
        return f"{intro}\n[원문 요약]\n{row.get('summary') or ''}\n\n{task}"

    def _summarize_one(self, row: Dict[str, Any], model: Optional[str] = None) -> Optional[StructuredBillSummary]:
        model_to_use = model or self.primary_model
        prompt = self._build_user_prompt(row)
        bill_id = row.get("bill_id")
        try:
            result = self._build_agent(model_to_use).run_sync(prompt)
            return result.output
        except Exception as e:
            self.logger.warning(f"[1차 실패] bill_id={bill_id}: {e}")
            if self.fallback_model and self.fallback_model != model_to_use:
                try:
                    result = self._build_agent(self.fallback_model).run_sync(prompt)
                    return result.output
                except Exception as e2:
                    self.logger.error(f"[2차 실패] bill_id={bill_id}: {e2}")
                    self.failed_bills.append({"bill_id": bill_id, "error": f"primary={e}; fallback={e2}"})
                    return None
            self.failed_bills.append({"bill_id": bill_id, "error": str(e)})
            return None

    def AI_structured_summarize(self, df_bills: pd.DataFrame, model: Optional[str] = None) -> pd.DataFrame:
        if df_bills is None or len(df_bills) == 0:
            return df_bills
        for col in ("brief_summary", "gpt_summary"):
            if col not in df_bills.columns:
                df_bills[col] = None

        to_process = df_bills[
            df_bills["brief_summary"].isnull() | (df_bills["brief_summary"] == "") |
            df_bills["gpt_summary"].isnull() | (df_bills["gpt_summary"] == "")
        ]
        if len(to_process) == 0:
            return df_bills

        success = 0
        for idx, row in to_process.iterrows():
            result = self._summarize_one(row.to_dict(), model=model)
            if result is None:
                continue
            df_bills.loc[idx, "brief_summary"] = result.brief_summary
            df_bills.loc[idx, "gpt_summary"] = result.gpt_summary
            df_bills.loc[idx, "summary_tags"] = json.dumps(result.tags, ensure_ascii=False)
            success += 1

        print(f"[AI 구조화 요약 완료] 성공={success}, 실패={len(to_process) - success}")
        return df_bills
```

- [ ] **Step 4: batch_utils.py 작성 (ai_batch_pipeline_utils 이관)**

`services/ai/src/lawdigest_ai/processor/batch_utils.py`:

기존 `services/data/src/lawdigest_data_pipeline/ai_batch_pipeline_utils.py`에서 DB 연결 코드를 제외한 핵심 배치 로직 이관:

```python
# services/ai/src/lawdigest_ai/processor/batch_utils.py
# 기존 services/data/src/lawdigest_data_pipeline/ai_batch_pipeline_utils.py에서 이관
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pymysql
import requests
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from lawdigest_ai.config import get_openai_api_key, OPENAI_BASE_URL

ACTIVE_BATCH_STATES = ("VALIDATING", "IN_PROGRESS", "FINALIZING", "SUBMITTED")


class BatchStructuredSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")
    brief_summary: str = Field(alias="briefSummary")
    gpt_summary: str = Field(alias="gptSummary")
    tags: List[str] = Field(alias="tags", min_length=5, max_length=5)


def _headers() -> Dict[str, str]:
    return {"Authorization": f"Bearer {get_openai_api_key()}"}


def _build_prompt_for_bill(row: Dict[str, Any]) -> str:
    payload = {
        "bill_id": row.get("bill_id"),
        "bill_name": row.get("bill_name"),
        "proposers": row.get("proposers"),
        "proposer_kind": row.get("proposer_kind"),
        "propose_date": str(row.get("propose_date") or ""),
        "stage": row.get("stage"),
        "summary": row.get("summary"),
    }
    return (
        "다음 법안 정보를 보고 JSON으로만 응답하세요.\n"
        "키는 briefSummary, gptSummary, tags 세 개만 포함해야 합니다.\n"
        "briefSummary는 1문장 요약, gptSummary는 3~7개 핵심 항목 중심 상세 요약입니다.\n"
        "tags는 중복 없는 한국어 태그 정확히 5개입니다.\n\n"
        f"{json.dumps(payload, ensure_ascii=False)}"
    )


def build_batch_request_rows(bills: List[Dict[str, Any]], model: str) -> List[Dict[str, Any]]:
    summary_schema = BatchStructuredSummary.model_json_schema(by_alias=True)
    return [
        {
            "custom_id": bill["bill_id"],
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": model,
                "messages": [
                    {"role": "system", "content": "당신은 한국 법안 요약 전문가입니다. 반드시 JSON 객체로만 응답하세요."},
                    {"role": "user", "content": _build_prompt_for_bill(bill)},
                ],
                "temperature": 0.2,
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {"name": "bill_summary", "strict": True, "schema": summary_schema},
                },
            },
        }
        for bill in bills
    ]


def write_jsonl_tempfile(rows: List[Dict[str, Any]]) -> str:
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8") as tmp:
        for row in rows:
            tmp.write(json.dumps(row, ensure_ascii=False) + "\n")
        return tmp.name


def openai_upload_batch_file(jsonl_path: str) -> str:
    with open(jsonl_path, "rb") as f:
        resp = requests.post(
            f"{OPENAI_BASE_URL}/files", headers=_headers(),
            data={"purpose": "batch"},
            files={"file": (os.path.basename(jsonl_path), f, "application/jsonl")},
            timeout=60,
        )
    resp.raise_for_status()
    return resp.json()["id"]


def openai_create_batch(input_file_id: str, model: str) -> Dict[str, Any]:
    payload = {"input_file_id": input_file_id, "endpoint": "/v1/chat/completions",
                "completion_window": "24h", "metadata": {"model": model, "pipeline": "lawdigest_ai_batch"}}
    resp = requests.post(f"{OPENAI_BASE_URL}/batches",
                          headers={**_headers(), "Content-Type": "application/json"},
                          data=json.dumps(payload), timeout=60)
    resp.raise_for_status()
    return resp.json()


def openai_get_batch(batch_id: str) -> Dict[str, Any]:
    resp = requests.get(f"{OPENAI_BASE_URL}/batches/{batch_id}", headers=_headers(), timeout=60)
    resp.raise_for_status()
    return resp.json()


def openai_download_file_content(file_id: str) -> str:
    resp = requests.get(f"{OPENAI_BASE_URL}/files/{file_id}/content", headers=_headers(), timeout=120)
    resp.raise_for_status()
    return resp.text


def _extract_message_content(choice_message: Any) -> str:
    if isinstance(choice_message, str):
        return choice_message
    if isinstance(choice_message, list):
        return "".join(item.get("text", "") for item in choice_message if isinstance(item, dict))
    if isinstance(choice_message, dict):
        content = choice_message.get("content")
        return _extract_message_content(content) if content else ""
    return ""


def parse_output_jsonl_line(
    line: str,
) -> Tuple[str, Optional[str], Optional[str], Optional[List[str]], Optional[str]]:
    row = json.loads(line)
    bill_id = row.get("custom_id")
    response = row.get("response") or {}
    if response.get("status_code") != 200:
        return bill_id, None, None, None, f"status_code={response.get('status_code')}"
    choices = (response.get("body") or {}).get("choices") or []
    if not choices:
        return bill_id, None, None, None, "choices가 비어있습니다."
    content = _extract_message_content(choices[0].get("message", {}).get("content", ""))
    if not content:
        return bill_id, None, None, None, "message content가 비어있습니다."
    try:
        parsed = BatchStructuredSummary.model_validate_json(content)
    except ValidationError as exc:
        return bill_id, None, None, None, f"Structured Output 검증 실패: {exc}"
    return bill_id, parsed.brief_summary, parsed.gpt_summary, parsed.tags, None


# DB 조작 함수들 (ai_batch_pipeline_utils에서 이관)
def ensure_status_tables(conn: pymysql.connections.Connection) -> None:
    ddl = [
        """CREATE TABLE IF NOT EXISTS ai_batch_jobs (
          id BIGINT AUTO_INCREMENT PRIMARY KEY,
          batch_id VARCHAR(128) NOT NULL UNIQUE,
          status VARCHAR(32) NOT NULL,
          input_file_id VARCHAR(128) NULL,
          output_file_id VARCHAR(128) NULL,
          error_file_id VARCHAR(128) NULL,
          endpoint VARCHAR(64) NOT NULL DEFAULT '/v1/chat/completions',
          model_name VARCHAR(64) NOT NULL,
          total_count INT NOT NULL DEFAULT 0,
          success_count INT NOT NULL DEFAULT 0,
          failed_count INT NOT NULL DEFAULT 0,
          submitted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          completed_at DATETIME NULL,
          error_message TEXT NULL,
          created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          INDEX idx_ai_batch_jobs_status (status),
          INDEX idx_ai_batch_jobs_created_at (created_at)
        )""",
        """CREATE TABLE IF NOT EXISTS ai_batch_items (
          id BIGINT AUTO_INCREMENT PRIMARY KEY,
          job_id BIGINT NOT NULL,
          bill_id VARCHAR(100) NOT NULL,
          custom_id VARCHAR(150) NOT NULL,
          status VARCHAR(32) NOT NULL DEFAULT 'SUBMITTED',
          retry_count INT NOT NULL DEFAULT 0,
          error_message TEXT NULL,
          processed_at DATETIME NULL,
          created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          UNIQUE KEY uq_ai_batch_items_job_bill (job_id, bill_id),
          INDEX idx_ai_batch_items_bill (bill_id),
          INDEX idx_ai_batch_items_status (status),
          CONSTRAINT fk_ai_batch_items_job FOREIGN KEY (job_id) REFERENCES ai_batch_jobs(id) ON DELETE CASCADE
        )""",
    ]
    with conn.cursor() as cursor:
        for stmt in ddl:
            cursor.execute(stmt)
    conn.commit()


def fetch_unsummarized_bills(conn: pymysql.connections.Connection, limit: int) -> List[Dict[str, Any]]:
    sql = f"""
    SELECT b.bill_id, b.bill_name, b.summary, b.proposers, b.proposer_kind, b.propose_date, b.stage
    FROM Bill b
    WHERE b.summary IS NOT NULL AND b.summary <> ''
      AND (b.brief_summary IS NULL OR b.brief_summary = '' OR b.gpt_summary IS NULL OR b.gpt_summary = '')
      AND NOT EXISTS (
        SELECT 1 FROM ai_batch_items i JOIN ai_batch_jobs j ON j.id = i.job_id
        WHERE i.bill_id = b.bill_id AND j.status IN ({",".join(["%s"] * len(ACTIVE_BATCH_STATES))})
      )
    ORDER BY b.propose_date DESC LIMIT %s
    """
    with conn.cursor() as cursor:
        cursor.execute(sql, list(ACTIVE_BATCH_STATES) + [limit])
        return cursor.fetchall()


def create_batch_job_with_items(
    conn: pymysql.connections.Connection, batch_id: str, input_file_id: str,
    model: str, bill_ids: List[str], status: str = "SUBMITTED",
) -> int:
    with conn.cursor() as cursor:
        cursor.execute(
            """INSERT INTO ai_batch_jobs (batch_id, status, input_file_id, endpoint, model_name, total_count, submitted_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (batch_id, status, input_file_id, "/v1/chat/completions", model,
             len(bill_ids), datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")),
        )
        job_id = cursor.lastrowid
        cursor.executemany(
            "INSERT INTO ai_batch_items (job_id, bill_id, custom_id, status) VALUES (%s, %s, %s, %s)",
            [(job_id, bid, bid, "SUBMITTED") for bid in bill_ids],
        )
    conn.commit()
    return int(job_id)


def fetch_jobs_for_polling(conn: pymysql.connections.Connection, max_jobs: int) -> List[Dict[str, Any]]:
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM ai_batch_jobs WHERE status IN ('SUBMITTED','VALIDATING','IN_PROGRESS','FINALIZING') "
            "ORDER BY created_at ASC LIMIT %s", (max_jobs,)
        )
        return cursor.fetchall()


def update_job_status(
    conn: pymysql.connections.Connection, job_id: int, status: str,
    output_file_id: Optional[str], error_file_id: Optional[str], error_message: Optional[str] = None,
) -> None:
    with conn.cursor() as cursor:
        cursor.execute(
            """UPDATE ai_batch_jobs SET status=%s, output_file_id=%s, error_file_id=%s, error_message=%s,
               completed_at=CASE WHEN %s IN ('COMPLETED','FAILED','CANCELED','EXPIRED') THEN NOW() ELSE completed_at END
               WHERE id=%s""",
            (status, output_file_id, error_file_id, error_message, status, job_id),
        )
    conn.commit()


def apply_batch_results(
    conn: pymysql.connections.Connection, job_id: int, output_jsonl: str,
) -> Tuple[int, int]:
    success = failed = 0
    with conn.cursor() as cursor:
        for line in [l for l in output_jsonl.splitlines() if l.strip()]:
            bill_id, brief, gpt, tags, err = parse_output_jsonl_line(line)
            if not bill_id:
                failed += 1
                continue
            if err:
                failed += 1
                cursor.execute(
                    "UPDATE ai_batch_items SET status='FAILED', retry_count=retry_count+1, "
                    "error_message=%s, processed_at=NOW() WHERE job_id=%s AND bill_id=%s",
                    (err, job_id, bill_id),
                )
                continue
            cursor.execute(
                "UPDATE Bill SET brief_summary=%s, gpt_summary=%s, summary_tags=%s, modified_date=NOW() "
                "WHERE bill_id=%s",
                (brief, gpt, json.dumps(tags or [], ensure_ascii=False), bill_id),
            )
            cursor.execute(
                "UPDATE ai_batch_items SET status='DONE', error_message=NULL, processed_at=NOW() "
                "WHERE job_id=%s AND bill_id=%s",
                (job_id, bill_id),
            )
            success += 1
        cursor.execute(
            "UPDATE ai_batch_items SET status='FAILED', retry_count=retry_count+1, "
            "error_message=COALESCE(error_message, 'output에 결과가 없습니다.'), processed_at=NOW() "
            "WHERE job_id=%s AND status='SUBMITTED'", (job_id,)
        )
        failed += cursor.rowcount
        cursor.execute(
            "UPDATE ai_batch_jobs SET success_count=%s, failed_count=%s WHERE id=%s",
            (success, failed, job_id),
        )
    conn.commit()
    return success, failed
```

- [ ] **Step 5: 테스트 재실행 - 통과 확인**

```bash
cd /home/ubuntu/project/Lawdigest/services/ai
python -m pytest tests/processor/ -v
```

Expected: 모든 테스트 PASS

- [ ] **Step 6: 커밋**

```bash
git add services/ai/src/lawdigest_ai/processor/ services/ai/tests/processor/
git commit -m "feat: processor 모듈 추가 - AISummarizer 및 batch_utils 이관"
```

---

## Task 3: processor 진입점 모듈 작성 (DAG에서 호출하는 함수)

**Files:**
- Create: `services/ai/src/lawdigest_ai/processor/instant_summarizer.py`
- Create: `services/ai/src/lawdigest_ai/processor/batch_submit.py`
- Create: `services/ai/src/lawdigest_ai/processor/batch_ingest.py`
- Create: `services/ai/tests/processor/test_entrypoints.py`

- [ ] **Step 1: 테스트 작성 (RED)**

`services/ai/tests/processor/test_entrypoints.py`:

```python
import pytest
from unittest.mock import MagicMock, patch

def test_instant_summarize_returns_summary():
    from lawdigest_ai.processor.instant_summarizer import summarize_single_bill
    mock_summary = {"brief_summary": "요약", "gpt_summary": "상세", "summary_tags": '["a","b","c","d","e"]'}
    with patch("lawdigest_ai.processor.instant_summarizer.AISummarizer") as MockSummarizer:
        instance = MockSummarizer.return_value
        instance.AI_structured_summarize.return_value = __import__("pandas").DataFrame([{
            "bill_id": "B001", "brief_summary": "요약", "gpt_summary": "상세",
            "summary_tags": '["a","b","c","d","e"]'
        }])
        result = summarize_single_bill({"bill_id": "B001", "summary": "원문 내용"})
    assert result["brief_summary"] == "요약"

def test_batch_submit_dry_run():
    from lawdigest_ai.processor.batch_submit import submit_batch
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    mock_cursor.fetchall.return_value = [
        {"bill_id": "B001", "bill_name": "테스트법", "summary": "내용",
         "proposers": "홍길동", "proposer_kind": "의원", "propose_date": "2024-01-01", "stage": "위원회"}
    ]
    with patch("lawdigest_ai.processor.batch_submit.get_db_connection", return_value=mock_conn):
        result = submit_batch(limit=10, model="gpt-4o-mini", mode="dry_run")
    assert result["mode"] == "dry_run"
    assert result["submitted"] >= 0
```

- [ ] **Step 2: instant_summarizer.py 작성**

`services/ai/src/lawdigest_ai/processor/instant_summarizer.py`:

```python
from __future__ import annotations

import pandas as pd
from typing import Any, Dict, List

from lawdigest_ai.processor.summarizer import AISummarizer


def summarize_single_bill(bill_data: Dict[str, Any]) -> Dict[str, Any]:
    """단일 법안에 대해 AI 요약을 수행하고 결과 dict를 반환합니다."""
    df = pd.DataFrame([bill_data])
    summarizer = AISummarizer()
    result_df = summarizer.AI_structured_summarize(df)
    return result_df.to_dict("records")[0]


def summarize_bills(bills: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """복수의 법안에 대해 AI 요약을 수행하고 결과 리스트를 반환합니다."""
    df = pd.DataFrame(bills)
    summarizer = AISummarizer()
    result_df = summarizer.AI_structured_summarize(df)
    return result_df.to_dict("records")
```

- [ ] **Step 3: batch_submit.py 작성**

`services/ai/src/lawdigest_ai/processor/batch_submit.py`:

```python
from __future__ import annotations

import os
from typing import Any, Dict

from lawdigest_ai.db import get_db_connection
from lawdigest_ai.processor.batch_utils import (
    build_batch_request_rows,
    create_batch_job_with_items,
    ensure_status_tables,
    fetch_unsummarized_bills,
    openai_create_batch,
    openai_upload_batch_file,
    write_jsonl_tempfile,
)


def submit_batch(limit: int = 200, model: str = "gpt-4o-mini", mode: str = "dry_run") -> Dict[str, Any]:
    """미요약 법안을 OpenAI Batch API에 제출합니다.

    Args:
        limit: 한 번에 처리할 최대 법안 수
        model: 사용할 OpenAI 모델명
        mode: 'dry_run' | 'test' | 'prod'
    """
    conn = get_db_connection(mode=mode if mode == "prod" else "test")
    try:
        ensure_status_tables(conn)
        bills = fetch_unsummarized_bills(conn, limit=limit)
        if not bills:
            print("[batch-submit] 제출 대상 법안이 없습니다.")
            return {"submitted": 0, "mode": mode}

        if mode == "dry_run":
            print(f"[batch-submit] [DRY_RUN] {len(bills)}개 법안 제출 대상 선정. (실제 제출 안 함)")
            return {"submitted": len(bills), "mode": "dry_run"}

        request_rows = build_batch_request_rows(bills, model=model)
        jsonl_path = write_jsonl_tempfile(request_rows)
        try:
            input_file_id = openai_upload_batch_file(jsonl_path)
            batch_obj = openai_create_batch(input_file_id=input_file_id, model=model)
            batch_id = batch_obj["id"]
            job_id = create_batch_job_with_items(
                conn=conn, batch_id=batch_id, input_file_id=input_file_id,
                model=model, bill_ids=[b["bill_id"] for b in bills],
                status=(batch_obj.get("status") or "SUBMITTED").upper(),
            )
            print(f"[batch-submit] [{mode}] job_id={job_id} batch_id={batch_id} count={len(bills)}")
            return {"submitted": len(bills), "batch_id": batch_id, "job_id": job_id, "mode": mode}
        finally:
            if os.path.exists(jsonl_path):
                os.remove(jsonl_path)
    finally:
        conn.close()
```

- [ ] **Step 4: batch_ingest.py 작성**

`services/ai/src/lawdigest_ai/processor/batch_ingest.py`:

```python
from __future__ import annotations

from typing import Any, Dict

from lawdigest_ai.db import get_db_connection
from lawdigest_ai.processor.batch_utils import (
    apply_batch_results,
    fetch_jobs_for_polling,
    openai_download_file_content,
    openai_get_batch,
    update_job_status,
)

TERMINAL_STATES = {"COMPLETED", "FAILED", "CANCELED", "EXPIRED"}


def ingest_batch_results(max_jobs: int = 10, mode: str = "dry_run") -> Dict[str, Any]:
    """완료된 OpenAI Batch 작업의 결과를 수집하여 DB에 적재합니다.

    Args:
        max_jobs: 한 번에 처리할 최대 작업 수
        mode: 'dry_run' | 'test' | 'prod'
    """
    conn = get_db_connection(mode=mode if mode == "prod" else "test")
    total_success = total_failed = 0
    try:
        jobs = fetch_jobs_for_polling(conn, max_jobs=max_jobs)
        if not jobs:
            print("[batch-ingest] 폴링 대상 작업이 없습니다.")
            return {"processed_jobs": 0, "mode": mode}

        for job in jobs:
            job_id = job["id"]
            batch_id = job["batch_id"]
            batch_obj = openai_get_batch(batch_id)
            status = (batch_obj.get("status") or "").upper()
            output_file_id = batch_obj.get("output_file_id")
            error_file_id = batch_obj.get("error_file_id")

            update_job_status(conn, job_id=job_id, status=status,
                              output_file_id=output_file_id, error_file_id=error_file_id)

            if status != "COMPLETED" or not output_file_id:
                print(f"[batch-ingest] batch_id={batch_id} status={status} - 아직 완료되지 않음")
                continue

            if mode == "dry_run":
                print(f"[batch-ingest] [DRY_RUN] batch_id={batch_id} COMPLETED - 결과 적재 생략")
                continue

            output_jsonl = openai_download_file_content(output_file_id)
            success, failed = apply_batch_results(conn, job_id=job_id, output_jsonl=output_jsonl)
            total_success += success
            total_failed += failed
            print(f"[batch-ingest] batch_id={batch_id} 적재 완료: 성공={success}, 실패={failed}")

    finally:
        conn.close()

    return {"processed_jobs": len(jobs), "total_success": total_success,
            "total_failed": total_failed, "mode": mode}
```

- [ ] **Step 5: 테스트 재실행**

```bash
cd /home/ubuntu/project/Lawdigest/services/ai
python -m pytest tests/processor/ -v
```

Expected: 모든 테스트 PASS

- [ ] **Step 6: 커밋**

```bash
git add services/ai/src/lawdigest_ai/processor/
git commit -m "feat: processor 진입점 모듈 추가 (instant_summarizer, batch_submit, batch_ingest)"
```

---

## Task 4: rag 모듈 작성 (임베딩 + Qdrant + RAG 챗봇)

**Files:**
- Create: `services/ai/src/lawdigest_ai/rag/embedding.py` (EmbeddingGenerator 이관)
- Create: `services/ai/src/lawdigest_ai/rag/vector_store.py` (QdrantManager 이관 + 검색 기능)
- Create: `services/ai/src/lawdigest_ai/rag/chatbot.py` (RAG 체인)
- Create: `services/ai/tests/rag/test_embedding.py`
- Create: `services/ai/tests/rag/test_vector_store.py`
- Create: `services/ai/tests/rag/test_chatbot.py`

- [ ] **Step 1: 테스트 작성 (RED)**

`services/ai/tests/rag/test_embedding.py`:

```python
import pytest
from unittest.mock import patch, MagicMock

def test_embedding_generator_openai_init(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    from lawdigest_ai.rag.embedding import EmbeddingGenerator
    with patch("lawdigest_ai.rag.embedding.OpenAI"):
        gen = EmbeddingGenerator(model_type="openai")
    assert gen.model_type == "openai"

def test_embedding_generator_returns_none_for_empty_text(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    from lawdigest_ai.rag.embedding import EmbeddingGenerator
    with patch("lawdigest_ai.rag.embedding.OpenAI"):
        gen = EmbeddingGenerator(model_type="openai")
    result = gen.generate("")
    assert result is None
```

`services/ai/tests/rag/test_vector_store.py`:

```python
import pytest
from unittest.mock import MagicMock, patch

def test_vector_store_search_returns_list(monkeypatch):
    monkeypatch.setenv("QDRANT_HOST", "localhost")
    from lawdigest_ai.rag.vector_store import VectorStore
    with patch("lawdigest_ai.rag.vector_store.QdrantClient") as MockClient:
        instance = MockClient.return_value
        instance.search.return_value = []
        store = VectorStore()
        results = store.search(collection_name="bills", query_vector=[0.1]*10, limit=5)
    assert isinstance(results, list)
```

`services/ai/tests/rag/test_chatbot.py`:

```python
import pytest
from unittest.mock import MagicMock, patch

def test_chatbot_answer_returns_string(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("QDRANT_HOST", "localhost")
    from lawdigest_ai.rag.chatbot import LawdigestionChatbot
    with patch("lawdigest_ai.rag.chatbot.VectorStore") as MockVS, \
         patch("lawdigest_ai.rag.chatbot.EmbeddingGenerator") as MockEG:
        mock_vs = MockVS.return_value
        mock_vs.search.return_value = [
            MagicMock(payload={"bill_id": "B001", "bill_name": "테스트법", "brief_summary": "요약", "gpt_summary": "상세"})
        ]
        mock_eg = MockEG.return_value
        mock_eg.generate.return_value = [0.1] * 1536

        chatbot = LawdigestionChatbot()
        with patch.object(chatbot, "_call_llm", return_value="이것은 답변입니다."):
            result = chatbot.answer("세금 관련 법안이 있나요?")
    assert isinstance(result, str)
```

- [ ] **Step 2: 테스트 실행 - 실패 확인**

```bash
cd /home/ubuntu/project/Lawdigest/services/ai
python -m pytest tests/rag/ -v
```

Expected: `ModuleNotFoundError`

- [ ] **Step 3: embedding.py 작성 (EmbeddingGenerator 이관)**

`services/ai/src/lawdigest_ai/rag/embedding.py`:

기존 `services/data/src/lawdigest_ai/embedding_generator.py`에서 이관, config import 경로 수정:

```python
from __future__ import annotations

from typing import List, Optional
from openai import OpenAI
from lawdigest_ai import config


class EmbeddingGenerator:
    """OpenAI 또는 HuggingFace 임베딩 모델로 텍스트 벡터를 생성합니다."""

    def __init__(self, model_type: str = "openai", model_name: Optional[str] = None):
        self.model_type = model_type
        self.client = None
        self.huggingface_model = None

        if model_type == "openai":
            try:
                self.client = OpenAI(api_key=config.get_openai_api_key())
            except Exception as e:
                print(f"OpenAI 클라이언트 초기화 실패: {e}")
        elif model_type == "huggingface":
            if not model_name:
                raise ValueError("HuggingFace 모델을 사용하려면 model_name을 지정해야 합니다.")
            try:
                from sentence_transformers import SentenceTransformer
                self.huggingface_model = SentenceTransformer(model_name)
            except Exception as e:
                print(f"HuggingFace 모델 로드 실패: {e}")

    def generate(self, text: str) -> Optional[List[float]]:
        """텍스트에 대한 임베딩 벡터를 반환합니다."""
        if not text or not isinstance(text, str):
            return None

        if self.model_type == "openai":
            if not self.client:
                return None
            try:
                response = self.client.embeddings.create(
                    input=[text.replace("\n", " ")],
                    model=config.EMBEDDING_MODEL,
                )
                return response.data[0].embedding
            except Exception as e:
                print(f"OpenAI 임베딩 생성 실패: {e}")
                return None

        elif self.model_type == "huggingface":
            if not self.huggingface_model:
                return None
            try:
                return self.huggingface_model.encode(text).tolist()
            except Exception as e:
                print(f"HuggingFace 임베딩 생성 실패: {e}")
                return None
        return None
```

- [ ] **Step 4: vector_store.py 작성 (QdrantManager 이관 + 검색 기능 추가)**

`services/ai/src/lawdigest_ai/rag/vector_store.py`:

```python
from __future__ import annotations

from typing import Any, Dict, List, Optional
import qdrant_client
from qdrant_client.http import models
from lawdigest_ai import config


class VectorStore:
    """Qdrant 벡터 DB와의 연결 및 상호작용을 관리합니다."""

    def __init__(self):
        try:
            self.client = qdrant_client.QdrantClient(
                host=config.QDRANT_HOST,
                api_key=config.QDRANT_API_KEY,
                port=6333,
                https=config.QDRANT_USE_HTTPS,
            )
        except Exception as e:
            print(f"Qdrant 클라이언트 초기화 실패: {e}")
            self.client = None

    def create_collection(self, collection_name: str, vector_size: int, recreate: bool = False) -> None:
        if not self.client:
            return
        if recreate:
            self.client.recreate_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
            )
            return
        existing = [c.name for c in self.client.get_collections().collections]
        if collection_name not in existing:
            self.client.recreate_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
            )

    def upsert(self, collection_name: str, points: list) -> None:
        if not self.client or not points:
            return
        self.client.upsert(collection_name=collection_name, points=points, wait=True)

    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 5,
        score_threshold: Optional[float] = None,
    ) -> List[Any]:
        """벡터 유사도 검색을 수행하고 결과를 반환합니다."""
        if not self.client:
            return []
        kwargs: Dict[str, Any] = {"collection_name": collection_name,
                                   "query_vector": query_vector, "limit": limit}
        if score_threshold is not None:
            kwargs["score_threshold"] = score_threshold
        return self.client.search(**kwargs)
```

- [ ] **Step 5: chatbot.py 작성 (RAG 체인)**

`services/ai/src/lawdigest_ai/rag/chatbot.py`:

```python
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from openai import OpenAI
from lawdigest_ai import config
from lawdigest_ai.rag.embedding import EmbeddingGenerator
from lawdigest_ai.rag.vector_store import VectorStore

BILL_COLLECTION = os.getenv("QDRANT_BILL_COLLECTION", "bills")
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "5"))
RAG_MODEL = os.getenv("RAG_MODEL", "gpt-4o-mini")


class LawdigestionChatbot:
    """Qdrant 벡터 검색 + OpenAI LLM을 결합한 법안 RAG 챗봇."""

    def __init__(
        self,
        collection_name: str = BILL_COLLECTION,
        top_k: int = RAG_TOP_K,
        model: str = RAG_MODEL,
    ):
        self.collection_name = collection_name
        self.top_k = top_k
        self.model = model
        self.embedder = EmbeddingGenerator(model_type="openai")
        self.vector_store = VectorStore()
        self.llm = OpenAI(api_key=config.get_openai_api_key())

    def _retrieve(self, query: str) -> List[Dict[str, Any]]:
        """쿼리에 관련된 법안을 벡터 DB에서 검색합니다."""
        vector = self.embedder.generate(query)
        if not vector:
            return []
        results = self.vector_store.search(
            collection_name=self.collection_name,
            query_vector=vector,
            limit=self.top_k,
        )
        return [r.payload for r in results if r.payload]

    def _build_context(self, documents: List[Dict[str, Any]]) -> str:
        """검색된 법안 문서로 LLM 컨텍스트를 구성합니다."""
        if not documents:
            return "관련 법안 정보를 찾을 수 없습니다."
        lines = []
        for i, doc in enumerate(documents, 1):
            lines.append(
                f"[법안 {i}]\n"
                f"법안명: {doc.get('bill_name', '미상')}\n"
                f"한줄요약: {doc.get('brief_summary', '')}\n"
                f"상세요약: {doc.get('gpt_summary', '')}\n"
            )
        return "\n".join(lines)

    def _call_llm(self, query: str, context: str) -> str:
        """LLM에 쿼리와 컨텍스트를 전달하여 답변을 생성합니다."""
        system_prompt = (
            "당신은 대한민국 법안 전문 AI 어시스턴트입니다. "
            "제공된 법안 정보를 바탕으로 사용자 질문에 명확하고 친절하게 답변하세요. "
            "법안 정보에 없는 내용은 추측하지 마세요."
        )
        user_prompt = f"[참고 법안 정보]\n{context}\n\n[질문]\n{query}"
        response = self.llm.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content or ""

    def answer(self, query: str) -> str:
        """사용자 질문에 대한 RAG 기반 답변을 반환합니다."""
        documents = self._retrieve(query)
        context = self._build_context(documents)
        return self._call_llm(query, context)
```

- [ ] **Step 6: 테스트 재실행**

```bash
cd /home/ubuntu/project/Lawdigest/services/ai
python -m pytest tests/rag/ -v
```

Expected: 모든 테스트 PASS

- [ ] **Step 7: 커밋**

```bash
git add services/ai/src/lawdigest_ai/rag/ services/ai/tests/rag/
git commit -m "feat: rag 모듈 추가 - EmbeddingGenerator, VectorStore, LawdigestionChatbot"
```

---

## Task 5: services/data에서 AI 코드 제거 및 WorkFlowManager 정리

> **⚠️ 실행 순서 주의:** Task 5의 파일 삭제(Step 3)는 반드시 **Task 6이 완전히 완료된 후**에 실행해야 합니다. Task 5 Step 1~2는 Task 6 이전에 실행 가능합니다.

**Files:**
- Modify: `services/data/src/lawdigest_data_pipeline/WorkFlowManager.py` (AISummarizer import 및 summarize_bill_step 제거)
- Modify: `services/data/scripts/run_n8n_db_pipeline.py` (bills_summarize 스텝 lawdigest_ai로 교체)
- Delete: `services/data/src/lawdigest_data_pipeline/AISummarizer.py` (래퍼 파일) ← Task 6 완료 후
- Delete: `services/data/src/lawdigest_data_pipeline/ai_batch_pipeline_utils.py` ← Task 6 완료 후
- Delete: `services/data/src/lawdigest_ai/` (디렉토리 전체) ← Task 6 완료 후
- Delete: `services/data/tools/update_vector_db.py` ← Task 6 완료 후

- [ ] **Step 1: WorkFlowManager에서 AI 관련 import 및 코드 제거**

`services/data/src/lawdigest_data_pipeline/WorkFlowManager.py`에서:
- `from .AISummarizer import AISummarizer` 제거
- `summarize_bill_step` 메서드 제거 (Airflow DAG이 직접 `lawdigest_ai.processor.instant_summarizer`를 사용하도록 변경)
- `update_bills_data`에서 AI 요약 호출 코드 제거 (수집→DB 적재만 남김)

변경 후 `update_bills_data`의 책임: 수집 → 중복 제거 → DB 적재

- [ ] **Step 2: run_n8n_db_pipeline.py의 bills_summarize 스텝 교체**

`services/data/scripts/run_n8n_db_pipeline.py`의 `bills_summarize` 스텝(현재 `wfm.summarize_bill_step(input_data)` 호출)을 다음으로 교체:

```python
# 변경 전
import sys
sys.path.insert(0, "/opt/airflow/project")
summarized_rows = wfm.summarize_bill_step(input_data)

# 변경 후
from lawdigest_ai.processor.instant_summarizer import summarize_bills
summarized_rows = summarize_bills(input_data if isinstance(input_data, list) else [input_data])
```

- [ ] **Step 3: WorkFlowManager 단위 테스트 실행**

```bash
cd /home/ubuntu/project/Lawdigest/services/data
python -m pytest tests/ -v -k "workflow"
```

Expected: 기존 테스트 모두 PASS (AI 관련 테스트는 services/ai로 이미 이전됨)

- [ ] **Step 4: 불필요한 파일 삭제 (Task 6 완료 후에만 실행)**

> **⚠️ 선행 조건: Task 6의 모든 DAG import 경로 변경 및 검증이 완료된 후 실행할 것**

```bash
# services/data 내 AI 코드 삭제
rm services/data/src/lawdigest_data_pipeline/AISummarizer.py
rm services/data/src/lawdigest_data_pipeline/ai_batch_pipeline_utils.py
rm -rf services/data/src/lawdigest_ai/
rm services/data/tools/update_vector_db.py
```

- [ ] **Step 5: 커밋**

```bash
git add -u services/data/
git commit -m "refactor: services/data에서 AI 코드 제거 - 수집/적재 책임만 유지"
```

---

## Task 6: Airflow DAG 업데이트 (import 경로 변경)

**Files:**
- Modify: `infra/airflow/dags/lawdigest_ai_summary_instant_dag.py`
- Modify: `infra/airflow/dags/lawdigest_ai_batch_submit_dag.py`
- Modify: `infra/airflow/dags/lawdigest_ai_batch_ingest_dag.py`
- Modify: `infra/airflow/dags/lawdigest_ai_summary_batch_dag.py`
- Modify: `infra/airflow/dags/lawdigest_hourly_update_dag.py`

- [ ] **Step 1: instant DAG 업데이트**

`infra/airflow/dags/lawdigest_ai_summary_instant_dag.py`의 `run_instant_ai_summary` 함수를 다음으로 교체:

```python
def run_instant_ai_summary(**context):
    params = context.get("params", {})
    mode = params.get("execution_mode") or "dry_run"
    print(f"[ai-summary-instant] Current Mode: {mode}")

    bill_json = params.get("bill_json")
    if bill_json:
        try:
            bill_data = json.loads(bill_json)
        except json.JSONDecodeError as exc:
            raise ValueError(f"bill_json이 유효한 JSON이 아닙니다: {exc}") from exc
    else:
        bill_data = {
            "bill_id": params.get("bill_id"),
            "bill_name": params.get("bill_name"),
            "summary": params.get("summary"),
            "proposers": params.get("proposers"),
            "proposer_kind": params.get("proposer_kind"),
            "proposeDate": params.get("propose_date"),
            "stage": params.get("stage"),
        }

    if not bill_data.get("bill_id"):
        raise ValueError("bill_id는 필수입니다.")
    if not bill_data.get("summary"):
        raise ValueError("summary는 필수입니다.")

    project_root = "/opt/airflow/project"
    if project_root not in sys.path:
        sys.path.append(project_root)

    # AI 요약: lawdigest_ai 서비스 사용
    from lawdigest_ai.processor.instant_summarizer import summarize_single_bill
    result = summarize_single_bill(bill_data)

    if mode != "dry_run" and _as_bool(params.get("upsert", True)):
        # DB 적재: DatabaseManager는 data 파이프라인 책임이므로 유지
        from src.lawdigest_data_pipeline.DatabaseManager import DatabaseManager
        from lawdigest_ai.db import get_prod_db_config, get_test_db_config
        import json as _json

        db_cfg = get_prod_db_config() if mode == "prod" else get_test_db_config()
        db = DatabaseManager(
            host=db_cfg["host"], port=db_cfg["port"],
            username=db_cfg["user"], password=db_cfg["password"],
            database=db_cfg["database"],
        )
        # brief_summary, gpt_summary, summary_tags를 Bill 테이블에 업데이트
        db.update_bill_summary(
            bill_id=result["bill_id"],
            brief_summary=result.get("brief_summary"),
            gpt_summary=result.get("gpt_summary"),
            summary_tags=result.get("summary_tags"),
        )
        print(f"[ai-summary-instant] [{mode}] DB upsert completed.")
    else:
        print(f"[ai-summary-instant] [{mode}] DB upsert skipped.")

    print(json.dumps(result, ensure_ascii=False, default=str))
    return result
```

> **Note:** `DatabaseManager.update_bill_summary()` 메서드가 없다면 `services/data`에 추가하거나, 기존 `insert_bill_info()`를 활용하는 방식으로 조정한다. `_build_bill_row()`는 `WorkFlowManager`에서 `DatabaseManager`의 메서드로 이동시키는 것을 권장한다.

- [ ] **Step 2: batch_submit DAG 업데이트**

`infra/airflow/dags/lawdigest_ai_batch_submit_dag.py`에서:

```python
# 변경 전
from src.lawdigest_data_pipeline.ai_batch_pipeline_utils import (...)

# 변경 후
from lawdigest_ai.processor.batch_submit import submit_batch

def submit_ai_batch(**context):
    params = context.get("params", {})
    return submit_batch(
        limit=int(params.get("limit") or 200),
        model=params.get("model") or "gpt-4o-mini",
        mode=params.get("execution_mode") or "dry_run",
    )
```

- [ ] **Step 3: batch_ingest DAG 업데이트**

`infra/airflow/dags/lawdigest_ai_batch_ingest_dag.py`에서:

```python
# 변경 전
from src.lawdigest_data_pipeline.ai_batch_pipeline_utils import (...)

# 변경 후
from lawdigest_ai.processor.batch_ingest import ingest_batch_results

def ingest_batch(**context):
    params = context.get("params", {})
    return ingest_batch_results(
        max_jobs=int(params.get("max_jobs") or 10),
        mode=params.get("execution_mode") or "dry_run",
    )
```

- [ ] **Step 3: batch_summary_repair DAG 업데이트**

`infra/airflow/dags/lawdigest_ai_summary_batch_dag.py`에서:

```python
# 변경 전
from src.lawdigest_data_pipeline.ai_batch_pipeline_utils import (
    fetch_unsummarized_bills, get_db_connection, ...
)

# 변경 후
from lawdigest_ai.processor.batch_ingest import ingest_batch_results
from lawdigest_ai.db import get_db_connection
from lawdigest_ai.processor.batch_utils import fetch_unsummarized_bills, ensure_status_tables
```

- [ ] **Step 4: hourly_update DAG에서 AI 요약 태스크 분리**

`infra/airflow/dags/lawdigest_hourly_update_dag.py`에서:
- `WorkFlowManager`가 AI 요약을 하지 않도록 수정되었으므로, 이 DAG에서 별도의 AI 요약 트리거가 필요한 경우 TriggerDagRunOperator로 `lawdigest_ai_batch_submit_dag`를 연결하거나, 단순히 제거 (법안 수집→DB 적재만 수행)

- [ ] **Step 5: DAG 문법 검증**

```bash
cd /home/ubuntu/project/Lawdigest
# Airflow가 실행 중인 경우
docker exec airflow-webserver airflow dags list
# 또는 파이썬 import 검증
cd infra/airflow
python -c "import dags.lawdigest_ai_batch_submit_dag"
python -c "import dags.lawdigest_ai_batch_ingest_dag"
python -c "import dags.lawdigest_ai_summary_instant_dag"
```

Expected: 오류 없이 import 성공

- [ ] **Step 6: 커밋**

```bash
git add infra/airflow/dags/
git commit -m "refactor: Airflow DAG import 경로를 lawdigest_ai 패키지로 변경"
```

---

## Task 7: update_vector_db 툴 이관 및 전체 검증

**Files:**
- Create: `services/ai/tools/update_vector_db.py` (기존 `services/data/tools/update_vector_db.py` 이관)
- Create: `services/ai/tools/__init__.py`

- [ ] **Step 1: update_vector_db.py 이관**

기존 `services/data/tools/update_vector_db.py`를 `services/ai/tools/update_vector_db.py`로 복사하고, import 경로를 새 패키지에 맞게 수정:

```python
# 변경 전
from lawdigest_ai.embedding_generator import EmbeddingGenerator
from lawdigest_ai.qdrant_manager import QdrantManager

# 변경 후
from lawdigest_ai.rag.embedding import EmbeddingGenerator
from lawdigest_ai.rag.vector_store import VectorStore
```

- [ ] **Step 2: 전체 테스트 실행**

```bash
cd /home/ubuntu/project/Lawdigest/services/ai
python -m pytest tests/ -v --tb=short
```

Expected: 모든 테스트 PASS

- [ ] **Step 3: services/ai 패키지 import 종합 검증**

```bash
cd /home/ubuntu/project/Lawdigest/services/ai
python -c "
from lawdigest_ai.processor.summarizer import AISummarizer
from lawdigest_ai.processor.batch_utils import build_batch_request_rows, BatchStructuredSummary
from lawdigest_ai.processor.instant_summarizer import summarize_single_bill
from lawdigest_ai.processor.batch_submit import submit_batch
from lawdigest_ai.processor.batch_ingest import ingest_batch_results
from lawdigest_ai.rag.embedding import EmbeddingGenerator
from lawdigest_ai.rag.vector_store import VectorStore
from lawdigest_ai.rag.chatbot import LawdigestionChatbot
print('모든 모듈 import 성공')
"
```

- [ ] **Step 4: 최종 커밋**

```bash
git add services/ai/tools/ services/ai/
git commit -m "feat: services/ai 독립 서비스 완성 - processor/rag 모듈 및 벡터DB 업데이트 툴 이관"
```

---

## 마이그레이션 체크리스트

> **삭제 항목은 Task 6 (DAG 업데이트 + 검증) 완전 완료 후에만 실행할 것**

작업 완료 후 다음 항목을 확인한다:

- [ ] `services/ai`에서 `python -m pytest tests/ -v` 전체 통과
- [ ] Airflow DAG import 오류 없음 (Task 6 Step 5 검증 통과)
- [ ] `services/data/scripts/run_n8n_db_pipeline.py`의 `wfm.summarize_bill_step` 호출 제거됨
- [ ] `services/data`에서 AI import 관련 코드 없음:
  ```bash
  grep -r "AISummarizer\|ai_batch_pipeline_utils\|from.*lawdigest_ai" services/data/src/
  ```
- [ ] (Task 6 완료 후) `services/data/src/lawdigest_ai/` 디렉토리 삭제 완료
- [ ] (Task 6 완료 후) `services/data/src/lawdigest_data_pipeline/AISummarizer.py` 삭제 완료
- [ ] (Task 6 완료 후) `services/data/src/lawdigest_data_pipeline/ai_batch_pipeline_utils.py` 삭제 완료

---

## 주요 의사결정 및 근거

1. **패키지명을 `lawdigest_ai_summarizer` → `lawdigest_ai`로 변경**: 챗봇 RAG 기능이 추가됨에 따라 "요약기"라는 이름이 서비스 전체를 표현하지 못함

2. **DB 적재 책임은 data 파이프라인에 유지**: instant DAG에서 요약 후 DB 저장 시 여전히 `DatabaseManager`(services/data)를 사용함 - 법안 DB 스키마와 적재 로직이 data 서비스에 있으므로 AI 서비스는 결과를 반환하고 적재는 data 서비스나 DAG 레이어가 담당

3. **batch_utils의 DB 함수 포함 + Bill 테이블 직접 UPDATE 허용**: AI 배치 상태 테이블(`ai_batch_jobs`, `ai_batch_items`)은 AI 서비스 전용이므로 services/ai에 함께 이관. `apply_batch_results()`는 `Bill` 테이블의 AI 요약 전용 컬럼(`brief_summary`, `gpt_summary`, `summary_tags`)에만 쓰기를 허용한다. 이 경계를 넘어(법안 기본 정보 컬럼 수정 등) services/ai가 Bill 테이블에 쓰는 것은 금지한다.

4. **RAG 챗봇은 읽기 전용**: Qdrant 검색 + LLM 호출만 수행하며 MySQL DB 쓰기는 없음

5. **Tech Debt 기록**: `batch_utils.py`는 OpenAI HTTP 호출과 MySQL DB 조작이 혼재한다. 장기적으로 `batch_openai.py`와 `batch_db.py`로 분리하면 테스트 격리 및 유지보수가 용이해진다. 이번 범위에서는 기존 구조를 유지한다.
