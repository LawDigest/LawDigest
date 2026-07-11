---
title: 에이전트 법안 리포트
sources:
  - services/ai/src/lawdigest_ai/processor/agentic_bill_report.py
  - services/ai/src/lawdigest_ai/processor/agentic_bill_tooltip.py
  - services/ai/src/lawdigest_ai/processor/bill_tooltip_store.py
  - services/ai/src/lawdigest_ai/processor/legal_term_glossary.py
  - services/ai/src/lawdigest_ai/processor/law_open_api_terms.py
  - services/data/src/lawdigest_data/runtime/cli.py
  - services/data/src/lawdigest_data/runtime/pipeline.py
  - services/backend/src/main/java/com/everyones/lawmaking/repository/BillReportTooltipQueryRepository.java
  - services/backend/src/main/java/com/everyones/lawmaking/service/BillService.java
  - infra/db/migrations/20260711_create_bill_report_tooltip.sql
  - docs/ai/bill-report-agent-pipeline.md
  - docs/ai/bill-report-agent-prompt-contract.md
  - docs/ai/korean_law_mcp_integration.md
---

```mermaid
flowchart LR
    Target["대상 법안"] --> ReportAgent["리포트 생성"]
    ReportAgent --> Validate["본문 검증"]
    Validate --> ReportStore[("원본 리포트")]
    Validate --> ReportManifest["생성 기록"]
    ReportStore --> Claim["해시 확인과 작업 선점"]
    Claim --> TooltipAgent["별도 용어 판정"]
    TooltipAgent --> TooltipValidate["원문 보존 검증"]
    TooltipValidate --> TooltipStore[("툴팁 적용본과 상태")]
    ReportStore --> API["API 응답 선택"]
    TooltipStore --> API
    TooltipValidate --> TooltipManifest["툴팁 기록"]
```

## Abstract

에이전트 법안 리포트는 법안 하나를 더 깊게 읽어 쉬운 요약과 주요 내용을 만드는 기능이다. 본문 생성과 법률용어 툴팁 보강은 서로 다른 저장 상태와 실행 주기를 가지며, 사용자 응답은 현재 원본과 일치하는 툴팁 결과만 선택한다.

## Introduction

짧은 요약만으로는 복합 개정안의 의미가 잘리지 않을 때가 있다. 이 기능은 법안의 처리 결과, 위원회 경과, 관련 법령, 필요한 통계를 확인한 뒤 사용자가 읽을 수 있는 리포트를 만든다.

## Related Work

- [AI 입법 지능](../README.md)
- [법안 상세 읽기](../../bill-reading/bill-detail/README.md)
- [입법 데이터 파이프라인](../../data-pipeline/README.md)

## Description

리포트 생성은 대상 선정에서 시작한다. 통과 법안 중심 또는 전체 법안 대상으로 실행할 수 있고, 읽기와 쓰기 모드를 분리해 운영 데이터를 읽으면서 저장은 막는 검토 흐름도 가능하다. 툴팁 과정은 생성 기록에 의존하지 않고 저장된 최신 원본을 입력으로 독립 실행한다.

```mermaid
sequenceDiagram
    autonumber
    participant Runtime as 실행 흐름
    participant Store as 서비스 데이터
    participant ReportAgent as 리포트 에이전트
    participant TooltipAgent as 툴팁 에이전트
    participant Sources as 공식 자료
    participant Output as 산출물
    Runtime->>Store: 대상 법안 조회
    Runtime->>Sources: 국회·법령 자료 확인
    Sources-->>Runtime: 근거 자료
    Runtime->>ReportAgent: 법안별 리포트 요청
    ReportAgent-->>Runtime: 리포트 본문
    Runtime->>Output: 본문 파일과 생성 기록 저장
    Runtime->>Store: 원본 본문 통과 결과 즉시 반영
    Runtime->>Store: 원본 해시 조정과 대기 작업 선점
    Runtime->>TooltipAgent: 최신 본문과 사전 후보 판정 요청
    TooltipAgent-->>Runtime: 후보별 문맥 적합성
    Runtime->>Output: 툴팁 적용본과 별도 기록 저장
    Runtime->>Store: 원본 해시 재확인 후 파생 결과 반영
```

본문 검증은 형식과 문체를 본다. 필수 섹션이 있는지, 내부 조사 표현이 남지 않았는지, 화면에 바로 보여도 되는 문체인지 확인한다. 툴팁 검증은 후보 정의의 문맥 적합성과 표면어 일치를 확인하고, 적용 후 툴팁을 제거했을 때 원문이 그대로인지 확인한다.

```text
검증 관문
├─ 필수 섹션 존재
├─ 내부 도구명과 조사 메모 제거
├─ 사용자 화면용 문체
├─ 툴팁 문맥·표면어 판정
├─ 툴팁 제거 후 원문 일치
└─ 단계별 실행 기록
```

이 기능은 실패를 숨기지 않는다. 본문 생성과 툴팁 보강은 각자의 실행 기록에 성공·건너뜀·실패를 남긴다. 툴팁 실패는 이미 저장된 리포트의 성공을 취소하거나 기존 본문을 덮어쓰지 않는다.

툴팁 작업은 대기, 실행, 적용, 건너뜀, 실패 상태를 가진다. 여러 실행기가 동시에 시작돼도 하나의 법안은 한 실행기만 선점하며, 중단된 실행은 lease가 만료된 뒤 다시 처리할 수 있다. 처리 중 원본이 바뀌면 이전 결과는 게시되지 않고 API는 깨끗한 원본 리포트를 반환한다.

## Conclusion

에이전트 법안 리포트는 AI 설명 품질을 높이는 정밀 경로다. 핵심은 많은 말을 생성하는 것이 아니라, 공식 자료 확인과 검증을 통과한 설명만 사용자 데이터로 보내는 것이다.
