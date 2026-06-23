# 에이전트 기반 법안 리포트 생성 파이프라인

작성일: 2026-06-23

이 문서는 현재 구현된 법안 리포트 생성 파이프라인을 설명한다. 예전 문서의 2단계 시각화 JSON 계획과 달리, 지금 운영 가능한 범위는 **Codex 에이전트가 Markdown 리포트를 만들고, 검증을 통과한 결과를 `brief_summary`, `gpt_summary`, `summary_tags` 계약에 맞춰 DB에 반영하는 흐름**이다.

## 1. 목적

기존 법안 요약은 짧은 설명을 빠르게 채우는 데 맞춰져 있었다. 새 파이프라인은 법안 하나를 더 깊게 읽고, 국회·법제처·통계 자료를 확인한 뒤 사용자가 이해할 수 있는 리포트를 만든다.

목표는 세 가지다.

- 법안이 바꾸려는 내용을 쉬운 문장으로 설명한다.
- 복합 개정안의 여러 변화가 하나의 쟁점으로 줄어들지 않게 한다.
- 생성 시간, 토큰 사용량, 사용량 계측값을 manifest로 남긴다.

## 2. 전체 흐름

```text
PipelineRuntime.run_bill_agent_report
→ run_agentic_bill_reports
→ DB에서 대상 법안 조회
→ CodexBillReportAgent가 법안별 Codex 세션 실행
→ Codex 세션이 MCP 서버로 국회·법령·통계 자료 확인
→ Markdown 리포트 파일 생성
→ 리포트 품질 검증
→ manifest.json 작성
→ dry_run이 아니면 DB 요약 필드 업데이트
```

진입점은 두 곳이다.

- CLI: `services/data/src/lawdigest_data/runtime/cli.py`의 `bill-agent-report`
- 런타임: `services/data/src/lawdigest_data/runtime/pipeline.py`의 `PipelineRuntime.run_bill_agent_report`

실제 생성 로직은 `services/ai/src/lawdigest_ai/processor/agentic_bill_report.py`에 있다.

## 3. 실행 명령

운영 DB를 읽되 DB에 쓰지 않고 결과 파일만 확인하려면 `dry_run`과 `--read-mode prod`를 함께 쓴다.

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

운영 DB에 반영하려면 `--mode prod`를 사용한다.

```bash
PYTHONPATH=services/data/src:services/ai/src python -m lawdigest_data.runtime.cli \
  bill-agent-report \
  --mode prod \
  --limit 3 \
  --target all \
  --concurrency 3 \
  --output-dir /tmp/lawdigest-bill-agent-reports
```

## 4. 주요 옵션

| 옵션 | 기본값 | 설명 |
| --- | --- | --- |
| `--mode` | `dry_run` | `dry_run`, `test`, `prod` 중 하나. `dry_run`은 파일과 manifest만 만든다. |
| `--read-mode` | mode 기준 | 읽기 DB를 따로 지정한다. `dry_run --read-mode prod` 조합으로 운영 데이터를 읽고 쓰기는 막을 수 있다. |
| `--limit` | `5` | 조회할 법안 수. |
| `--target` | `passed` | `passed`는 통과 법안 중심, `all`은 요약이 있는 전체 법안 대상이다. |
| `--concurrency` | `1` | 동시에 실행할 Codex 세션 수. 3개 병렬 실행은 `--concurrency 3`으로 지정한다. |
| `--codex-model` | 환경변수 또는 `gpt-5.4-mini` | 실행 모델 override. |
| `--stop-on-error` | 꺼짐 | 하나라도 실패하면 즉시 중단한다. 기본은 실패 항목을 manifest에 남기고 다음 법안을 계속 처리한다. |
| `--weekly-usage-before`, `--weekly-usage-after` | 없음 | 주간 사용량 퍼센트 계측값. |
| `--five-hour-usage-before`, `--five-hour-usage-after` | 없음 | 5시간 사용량 퍼센트 계측값. |

## 5. 환경변수

| 환경변수 | 필수 여부 | 설명 |
| --- | --- | --- |
| `ASSEMBLY_API_KEY` | 필수 | 열린국회정보 계열 MCP 서버가 사용한다. 없으면 `APIKEY_billsInfo`, `APIKEY_status`도 대체 키로 본다. |
| `LAW_OC` | 권장 | 법제처/국가법령정보센터 API 인증키. `korean-law` MCP에 전달한다. |
| `KOSIS_API_KEY` | 권장 | KOSIS 통계 조회 키. `korean-stats` MCP에 전달한다. |
| `BILL_AGENT_CODEX_MODEL` | 선택 | 기본 모델을 바꾼다. 기본값은 `gpt-5.4-mini`다. |
| `BILL_AGENT_CODEX_TIMEOUT_SECONDS` | 선택 | Codex 세션 제한 시간. 기본값은 900초다. |
| `BILL_AGENT_CODEX_WORKDIR` | 선택 | Codex 실행 디렉터리. 기본값은 `/tmp`다. |
| `CODEX_CLI_BIN` | 선택 | Codex CLI 실행 파일. 기본값은 `codex`다. |

## 6. MCP 서버 구성

Codex 세션은 `--ignore-user-config`, `--disable plugins`, `--disable apps`, `--disable memories`, `--sandbox read-only`, `--ephemeral`로 실행한다. 사용자 설정과 저장된 기억이 결과에 섞이지 않게 하기 위한 설정이다.

세션마다 다음 MCP 서버가 임시 설정으로 주입된다.

| 서버 | 패키지/엔드포인트 | 주 용도 |
| --- | --- | --- |
| `open-assembly` | `uvx open-assembly-mcp@latest` | 의안 검색, 의안 상세, 발의자, 표결, 위원회 심사 정보 |
| `assembly-api` | `npx -y assembly-api-mcp@latest` | 열린국회 API 상세 조회와 보조 질의 |
| `korean-law` | `npx -y korean-law-mcp@latest` | 현행법 조문, 법령 맥락, 법령용어·일상용어 연계 |
| `korean-stats` | `npx -y mcp-remote https://korean-stats-mcp.fly.dev/mcp` | 정책 배경에 필요한 공식 통계 |

도구는 서버별 허용 목록만 `approval_mode = "approve"`로 연다. MCP 서버명이나 도구명은 최종 리포트에 쓰면 안 된다.

## 7. 대상 법안 선정

`_fetch_bill_report_targets`가 `Bill` 테이블에서 대상 법안을 가져온다.

공통 조건:

- `summary IS NOT NULL`
- `summary != ''`
- 정렬: `propose_date DESC, bill_id DESC`

`--target passed`는 다음 조건을 추가한다.

- `bill_result`에 `원안가결`, `수정가결`, `가결` 중 하나가 포함되거나, `stage`에 `공포`, `본회의 의결` 중 하나가 포함된다.
- `bill_result`에 `폐기`, `철회`, `부결`, `임기만료`가 포함된 법안은 제외한다.

`--target all`은 통과 여부를 제한하지 않는다. 현재 사용자 피드 품질이 좋아져 통과 법안뿐 아니라 전체 법안에도 적용할 수 있다는 판단을 반영한 옵션이다.

## 8. 생성 프롬프트

프롬프트는 코드에서 `build_bill_report_prompt`가 만든다. 입력 payload에는 다음 값이 들어간다.

- `bill_id`, `bill_number`, `bill_name`
- `bill_result`, `stage`, `committee`
- `propose_date`, `proposers`
- `summary`, `bill_link`, `bill_pdf_url`

프롬프트는 에이전트에게 네 가지 조사를 요구한다.

- `open-assembly`, `assembly-api`로 법안명, 의안번호, 처리결과, 통과 경로, 위원회, 표결 정보를 확인한다.
- `korean-law`로 현행법, 개정 법령 맥락, 관련 조문, 법령 인용을 확인한다.
- `korean-stats`는 정책 배경 설명에 직접 도움이 될 때만 쓴다.
- 입력과 도구 결과가 다르면 도구 결과를 우선하되, 불확실한 내용은 단정하지 않는다.

출력은 Markdown 리포트만 허용한다. 자세한 형식 계약은 [bill-report-agent-prompt-contract.md](./bill-report-agent-prompt-contract.md)를 따른다.

## 9. 법률 용어 풀이

`legal_term_glossary.py`는 프롬프트에 짧은 용어 사전 컨텍스트를 붙인다. `LAW_OC`가 있으면 `law_open_api_terms.py`의 `LawOpenApiTermClient`가 법제처 Open API를 실제로 호출해 법령용어와 일상어 연계어를 조회한다.

현재 기본 사전:

- `청문 규정`: 처분을 받기 전에 당사자가 설명하고 반론할 수 있는 절차
- `과태료`: 행정질서 위반에 대해 부과하는 금전 제재
- `위임·위탁`: 행정기관의 권한이나 업무 일부를 다른 기관이 맡아 처리하는 방식

조회하는 API:

- `lawSearch.do?target=lstrmAI`: 법령정보지식베이스 법령용어 조회
- `lawService.do?target=lstrmRlt`: 법령용어-일상용어 연계 조회

API 조회에 성공하면 프롬프트에 `법제처 API 조회 결과` 섹션이 들어간다. `LAW_OC`가 없거나 호출에 실패하면 API 결과를 넣지 않고, Lawdigest가 관리하는 정적 보조 사전만 fallback으로 넣는다. 이 경우 프롬프트에는 `정적 보조 사전`이라고 명시한다.

`허위정보`, `필수정보`, `표시·광고`처럼 뜻이 바로 드러나는 말은 설명하지 않을 용어로 분류한다. 너무 당연한 말까지 설명해 리포트가 늘어지는 문제를 막기 위해서다.

## 10. 품질 검증

생성된 Markdown은 `_validate_report_body`를 통과해야 성공으로 처리된다.

검증 항목:

- `## 쉬운 요약`, `## 주요 내용` 필수 섹션이 있어야 한다.
- 내부 조사 표현, MCP 서버명, 도구명, 함수명이 본문에 남으면 실패한다.
- `원문 요약:`, `용어 설명:`, `쉬운 풀이:` 같은 메타 라벨이 남으면 실패한다.
- `청문`, `과태료`, `위임·위탁` 같은 어려운 용어는 필요한 설명 불릿이 있어야 한다.
- `허위정보:`, `필수정보:`처럼 당연한 용어 설명 불릿은 실패한다.
- `무엇이 달라지나` 섹션은 `### 1) 제목` 형식의 번호 헤딩을 써야 한다.
- 변화 제목은 짧은 명사형이어야 한다.
- `주요 내용`의 콜론 앞 핵심 라벨은 `**볼드체**`여야 한다.
- 본문 어딘가에 중요 단어 볼드체와 `<mark>...</mark>` 하이라이트가 있어야 한다.
- `합니다`, `됩니다`, `입니다` 같은 격식체 종결이 남으면 실패한다.
- `줄어드어요`처럼 어색한 해요체가 남으면 실패한다.

검증 실패 시 해당 항목은 `status: failed`로 manifest에 기록된다. `--stop-on-error`가 켜져 있으면 즉시 중단한다.

## 11. 산출물

`--output-dir` 아래에 법안별 Markdown과 `manifest.json`이 생성된다.

예시:

```text
/tmp/lawdigest-bill-agent-reports/
├── PRC_X2Y6W0W4U1R4R1P1Q0O8P2N7O7V1U5.md
├── PRC_U2K6I0H3I2N7V1U5S5T7S4A7Z9X2Y1.md
└── manifest.json
```

manifest에는 다음 정보가 들어간다.

- 실행 모드, 읽기 모드, 모델, 대상 범위, 병렬도
- 시작/종료 시각, 전체 소요 시간
- 대상 수, 성공 수, 실패 수
- DB 반영 수
- 법안별 파일 경로, exit code, output bytes, 소요 시간
- Codex thread id, JSON 이벤트 수
- token usage가 있으면 `usage`와 `usage_totals`
- 주간/5시간 사용량 퍼센트 전후값이 있으면 `usage_meter`

## 12. DB 반영

`mode != "dry_run"`이면 성공한 항목만 DB에 반영한다.

반영 방식:

- Markdown 최상단 `# 법안명`은 제거한다.
- `## 확인한 근거` 이후는 DB용 `gpt_summary`에서 제거한다.
- 기존 `brief_summary`가 있으면 유지한다.
- 기존 `brief_summary`가 없으면 `## 쉬운 요약`의 첫 번째 불릿을 평문으로 바꿔 사용한다.
- `summary_tags`는 기존 값을 유지한다.
- 최종적으로 `update_bill_summary`가 `brief_summary`, `gpt_summary`, `summary_tags`를 업데이트한다.

현재 심사 단계, 처리 결과, 투표 결과, 조회수, 스크랩 수는 AI 텍스트에 고정하지 않는다. 프론트와 API가 최신 데이터로 별도 표시한다.

## 13. 운영 절차

1. `dry_run --read-mode prod`로 소량 실행한다.
2. Markdown 파일을 직접 열어 문체, 길이, 용어 풀이, 하이라이트를 확인한다.
3. `manifest.json`에서 실패 항목, 소요 시간, token usage를 확인한다.
4. 필요하면 같은 옵션으로 `--mode prod`를 실행한다.
5. 운영 반영 뒤 웹 피드와 상세 페이지에서 렌더링을 확인한다.

권장 확인 명령:

```bash
jq '.stats, .usage_meter, .items[] | {bill_id, status, duration_seconds, usage, error}' \
  /tmp/lawdigest-bill-agent-reports/manifest.json
```

## 14. 테스트

핵심 테스트는 아래 파일에 있다.

- `services/ai/tests/processor/test_agentic_bill_report.py`
- `services/data/tests/test_pipeline_runtime.py`

대표 확인 명령:

```bash
PYTHONPATH=services/ai/src pytest services/ai/tests/processor/test_agentic_bill_report.py -q

PYTHONPATH=services/data/src:services/ai/src pytest services/data/tests/test_pipeline_runtime.py -q
```

## 15. 아직 구현되지 않은 범위

예전 계획에는 2차 에이전트가 `visualize_guide.md`를 읽고 프론트용 시각화 JSON을 만드는 단계가 있었다. 현재 브랜치에는 그 단계가 운영 코드로 남아 있지 않다.

따라서 지금 기준의 완료 범위는 다음과 같다.

- 구현됨: 텍스트 리포트 생성, MCP 조사, 용어 풀이 컨텍스트, Markdown 검증, manifest, 사용량 계측, 병렬 실행, DB 반영
- 미구현: 텍스트 리포트 기반 시각화 JSON 생성, 프론트 컴포넌트 선택 자동화, 시각 리포트 스키마 운영 반영
