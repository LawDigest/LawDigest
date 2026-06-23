# lawdigest-ai

Lawdigest의 AI 가공 파이프라인 코드다. 법안 요약, provider batch 처리, RAG 챗봇, 에이전트 기반 법안 리포트 생성을 포함한다.

## 주요 구성

| 경로 | 역할 |
| --- | --- |
| `src/lawdigest_ai/processor/` | 법안 요약, provider 처리, 에이전트 리포트 생성 |
| `src/lawdigest_ai/processor/agentic_bill_report.py` | Codex MCP 에이전트 기반 법안 리포트 생성 |
| `src/lawdigest_ai/processor/legal_term_glossary.py` | 법률·행정용어 풀이 사전 |
| `src/lawdigest_ai/rag/` | RAG 챗봇과 벡터 검색 |
| `tests/` | AI 서비스 단위 테스트 |

## 에이전트 기반 법안 리포트

자세한 운영 문서는 아래를 기준으로 본다.

- [에이전트 기반 법안 리포트 생성 파이프라인](../../docs/ai/bill-report-agent-pipeline.md)
- [법안 리포트 프롬프트·검증 계약](../../docs/ai/bill-report-agent-prompt-contract.md)
- [korean-law MCP와 법제처 용어 API 적용 현황](../../docs/ai/korean_law_mcp_integration.md)

기본 실행 예:

```bash
PYTHONPATH=services/data/src:services/ai/src python -m lawdigest_data.runtime.cli \
  bill-agent-report \
  --mode dry_run \
  --read-mode prod \
  --limit 3 \
  --target all \
  --concurrency 3 \
  --output-dir /tmp/lawdigest-bill-agent-reports
```

## 주요 환경변수

| 환경변수 | 설명 |
| --- | --- |
| `ASSEMBLY_API_KEY` | 열린국회정보 계열 MCP 서버용 API 키 |
| `LAW_OC` | 법제처/국가법령정보센터 Open API 키 |
| `KOSIS_API_KEY` | KOSIS 통계 API 키 |
| `BILL_AGENT_CODEX_MODEL` | 법안 리포트 생성 모델 override. 기본값은 `gpt-5.4-mini` |
| `BILL_AGENT_CODEX_TIMEOUT_SECONDS` | Codex 세션 timeout. 기본값은 900초 |

## 테스트

```bash
PYTHONPATH=services/ai/src pytest services/ai/tests -q
```

에이전트 리포트만 확인할 때:

```bash
PYTHONPATH=services/ai/src pytest services/ai/tests/processor/test_agentic_bill_report.py -q
```
