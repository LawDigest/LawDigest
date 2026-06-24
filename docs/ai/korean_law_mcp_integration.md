# korean-law MCP와 법제처 용어 API 적용 현황

작성일: 2026-06-23

이 문서는 `korean-law` MCP와 법제처 Open API를 Lawdigest 법안 리포트 생성 파이프라인에 어떻게 적용하고 있는지 정리한다. 예전 문서는 도입 검토 중심이었지만, 현재 기준에서는 **에이전트 기반 법안 리포트 생성 파이프라인의 법령·용어 확인 레이어**로 보는 것이 맞다.

## 1. 현재 적용 위치

현재 적용된 위치는 두 곳이다.

| 위치 | 역할 |
| --- | --- |
| `services/ai/src/lawdigest_ai/processor/agentic_bill_report.py` | Codex 세션에 `korean-law` MCP 서버를 주입한다. |
| `services/ai/src/lawdigest_ai/processor/law_open_api_terms.py` | `LAW_OC`로 법제처 용어 API를 호출한다. |
| `services/ai/src/lawdigest_ai/processor/legal_term_glossary.py` | API 조회 결과와 정적 보조 사전을 합쳐 프롬프트에 붙인다. |

실행 경로는 [bill-report-agent-pipeline.md](./bill-report-agent-pipeline.md)를 따른다.

## 2. 사용하는 MCP 서버

Codex 에이전트는 `korean-law` MCP를 다음 명령으로 실행한다.

```text
npx -y korean-law-mcp@latest
```

환경변수:

- `LAW_OC`: 국가법령정보센터 Open API 인증키

허용 도구:

- `search_law`
- `get_law_text`
- `get_annexes`
- `legal_research`
- `legal_analysis`
- `discover_tools`
- `execute_tool`
- `get_legal_term_kb`
- `get_legal_term_detail`
- `get_daily_term`
- `get_daily_to_legal`
- `get_legal_to_daily`
- `get_term_articles`
- `search_decisions`
- `get_decision_text`

최종 리포트에는 서버명, 도구명, 함수명을 쓰지 않는다. 사용자는 도구 호출 과정을 볼 필요가 없고, 결과 문장만 읽으면 된다.

## 3. 법안 리포트에서 맡는 일

`korean-law` MCP는 다음 확인에 쓴다.

- 현행법 조문 확인
- 개정 대상 조문의 위치 확인
- 법령 인용 검증
- 조문 체계와 관련 조문 확인
- 법령용어·일상용어 연결 확인
- 필요한 경우 판례·결정례 검색

리포트 본문에서는 이런 조사를 다음 섹션에 반영한다.

- `왜 나왔나`
- `무엇이 달라지나`
- `누구에게 영향이 있나`
- `봐야 할 점`
- `확인한 근거`

## 4. 법률 용어 자동 풀이

현재 구현은 `LAW_OC`가 있으면 법제처 Open API를 실제로 호출한다. 조회에 성공하면 프롬프트에 `법제처 API 조회 결과` 섹션을 넣고, 법령용어 정의와 일상어 연계어를 함께 제공한다. 실패하거나 키가 없으면 Lawdigest가 관리하는 정적 보조 사전만 fallback으로 넣는다.

현재 호출하는 API:

| API | 사용 방식 |
| --- | --- |
| `lawSearch.do?target=lstrmAI` | 법령정보지식베이스에서 법령용어 후보를 조회한다. |
| `lawService.do?target=lstrmRlt` | 법령용어와 연결된 일상어를 조회한다. |
| `lawSearch.do?target=lstrm` + `lawService.do?target=lstrm` | 법령용어 상세 정의를 조회한다. |

`dlytrmRlt` 역방향 조회 메서드는 클라이언트에 있지만, 자동 프롬프트 컨텍스트에는 넣지 않는다. 실제 스모크에서 `검토 → 검열`처럼 너무 넓은 관련 법령용어가 섞이는 문제가 확인되어, 현재 프롬프트에는 법령용어에서 직접 연결된 일상어만 넣는다.

기본 사전:

| 용어 | 사용자용 설명 |
| --- | --- |
| 청문 규정 | 처분을 받기 전에 당사자가 설명하고 반론할 수 있는 절차 |
| 과태료 | 행정질서 위반에 대해 부과하는 금전 제재 |
| 위임·위탁 | 행정기관의 권한이나 업무 일부를 다른 기관이 맡아 처리하는 방식 |

설명하지 않을 용어:

- 허위정보
- 허위정보 유포
- 필수정보
- 표시·광고

이 목록은 사용자가 읽기에 자명한 용어까지 설명이 붙어 리포트가 늘어지는 문제를 막기 위한 장치다.

## 5. 법제처 Open API 참조

용어 사전 보강 출처로 다음 API를 둔다.

| 목적 | API |
| --- | --- |
| 법령용어 목록 | `https://www.law.go.kr/DRF/lawSearch.do?target=lstrm` |
| 법령정보지식베이스 법령용어 | `https://www.law.go.kr/DRF/lawSearch.do?target=lstrmAI` |
| 법령용어-일상용어 연계 | `https://www.law.go.kr/DRF/lawService.do?target=lstrmRlt` |
| 일상용어-법령용어 연계 | `https://www.law.go.kr/DRF/lawService.do?target=dlytrmRlt` |

현재 `law_open_api_terms.py`가 이 중 `lstrmAI`, `lstrmRlt`, `lstrm` 상세 조회를 호출한다. 다음 단계에서는 자주 등장하는 용어를 캐시하고, 법안 원문에서 어려운 용어 후보를 더 넓게 추출하는 쪽을 보강한다.

## 6. 출력 형식 규칙

용어 설명은 괄호가 아니라 별도 불릿으로 쓴다.

좋은 예:

```markdown
- 청문 규정: 여기서 `청문`은 처분을 받기 전에 당사자가 설명하고 반론할 수 있는 절차에요.
- 사용자 입장에서는, 처분을 받기 전에 자기 입장을 말할 기회가 보장된다는 뜻이에요.
```

피해야 할 예:

```markdown
제23조(청문)는 처분 전에 의견을 듣는 규정입니다.
```

이유:

- 괄호식 조문 표기는 일반 사용자가 읽기 어렵다.
- `청문` 같은 말은 문장 안에 끼워 넣기보다 바로 아래에서 풀어줘야 한다.
- 설명 불릿은 실제 용어명으로 시작해야 한다. `용어 설명:` 같은 메타 라벨은 쓰지 않는다.

## 7. 검증 규칙

`_validate_report_body`는 다음 상황을 실패로 본다.

- `청문`이 나오는데 `청문 규정:`, `청문 절차:`, `청문:` 설명 불릿이 없다.
- `과태료`, `위임·위탁`이 나오는데 해당 용어 설명 불릿이 없다.
- `용어 설명:`, `법령 체계:`, `쉬운 풀이:` 같은 메타 라벨이 남아 있다.
- `허위정보:`, `필수정보:` 같은 불필요한 사전식 설명이 들어 있다.
- 설명 문장이 Markdown 불릿이 아니다.

검증 테스트는 `services/ai/tests/processor/test_agentic_bill_report.py`에 있다.

## 8. 향후 보강

우선순위는 다음 순서다.

1. 용어 조회 결과 캐시 테이블 또는 파일 캐시 추가
2. 생성 전에 법안 원문에서 어려운 용어 후보 추출
3. 법제처 API 결과와 정적 설명의 충돌 여부 점검
4. 설명하지 않을 용어 목록을 실제 리포트 품질 리뷰 결과로 갱신
5. API 실패율과 fallback 사용 여부를 manifest에 기록

이 보강은 리포트 본문의 길이를 늘리는 작업이 아니다. 목적은 어려운 용어만 골라 정확히 설명하고, 쉬운 말에는 설명을 붙이지 않는 것이다.
