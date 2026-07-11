# Bill Report Prompt-Only Temporal Handling Design

## 목표

법안 리포트 본문의 시점 표현을 코드 정규식과 confidence 게이트로 차단하지 않고 프롬프트 지침으로 처리한다. 동시에 정식 법령명이 `법률`로 끝나는 일부개정법률안도 법제처 조회 대상으로 정확히 추출한다.

## 현재 문제

`temporal_consistency`, `current_law_snapshot`, 본문 정규식 검증이 같은 목적을 여러 층에서 반복한다. 이 구조는 `현재 시행 조문을 확인하지 못했다` 같은 근거 부재 고지까지 현재 법령 주장으로 오인했다. 또한 `_extract_target_law_names()`는 `...법 일부개정법률안`만 인식해 `...에 관한 법률 일부개정법률안`에서 법제처 조회 자체를 건너뛴다.

## 설계

### 시점 처리

- evidence packet에는 기존 `bill_text`와 `current_law`만 유지한다.
- `temporal_context`와 `current_law_snapshot` 파생 메타데이터를 제거한다.
- 프롬프트에는 다음 원칙만 남긴다.
  - 제안이유의 법령 설명은 발의 당시 기준으로 읽는다.
  - `current_law`에 실제 조문이 있을 때만 현재 시행 내용을 쓴다.
  - 두 근거가 다르면 본문에서 기준 시점을 자연스럽게 구분한다.
  - 현재 조문이 없으면 이를 추정하지 않는다.
- structured output의 `temporal_consistency` 필드와 `confidence=high` 요구를 제거한다.
- `현행법`, `현재 시행` 문자열을 검사하는 코드 게이트를 제거한다.

Markdown 구조, 제목 일치, 문체, 툴팁 표기, 분량 상한 검증은 그대로 유지한다.

### 법령명 추출

일부개정·전부개정·폐지 법률안에서 대상 이름의 끝을 `법률|법` 순서로 인식한다. 예를 들어 `치유농업 연구개발 및 육성에 관한 법률 일부개정법률안`은 `치유농업 연구개발 및 육성에 관한 법률`로 추출한다.

## 성공 기준

- `법`, `법률`로 끝나는 정식 법령명이 모두 추출된다.
- evidence에 `temporal_context`가 생성되지 않는다.
- 출력 스키마는 `report_body`만 요구한다.
- 현재법 관련 문구 때문에 코드 validation 실패가 발생하지 않는다.
- 분량 상한과 기존 Markdown QA는 계속 작동한다.
- 이전 실패 7건 재생성에서 법제처 조회와 DB upsert가 정상 수행된다.
