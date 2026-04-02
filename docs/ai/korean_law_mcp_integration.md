# korean-law-mcp 도입 검토

## 1. 개요

[korean-law-mcp](https://github.com/chrisryugj/korean-law-mcp)는 법제처 Open API를 기반으로 **87개의 구조화된 도구**를 제공하는 MCP 서버 + CLI 프로젝트다. 법령, 판례, 행정규칙, 자치법규, 조약, 해석례를 AI 어시스턴트나 스크립트에서 직접 호출할 수 있다.

모두의입법 서비스에 도입할 경우 RAG 챗봇 강화, 법안 요약 품질 향상, 법률 용어 풀이 등 여러 기능 개선이 가능하다.

---

## 2. korean-law-mcp 핵심 기능

### 2.1 도구 카테고리 (87개)

| 카테고리 | 개수 | 주요 도구 |
|----------|------|-----------|
| 검색 | 11 | `search_law`, `search_precedents`, `search_all`, `get_annexes` |
| 조회 | 9 | `get_law_text`, `get_batch_articles`, `compare_old_new`, `get_three_tier` |
| 분석 | 10 | `compare_articles`, `get_law_tree`, `summarize_precedent`, `analyze_document` |
| 전문: 조세/관세 | 4 | `search_tax_tribunal_decisions`, `search_customs_interpretations` |
| 전문: 헌재/행심 | 4 | `search_constitutional_decisions`, `search_admin_appeals` |
| 전문: 위원회 결정 | 8 | 공정위, 개보위, 노동위, 감사원 |
| 법령-자치법규 연계 | 4 | `get_linked_ordinances`, `get_delegated_laws` |
| 조약 | 2 | `search_treaties`, `get_treaty_text` |
| 지식베이스 | 7 | `get_legal_term_kb`, `get_daily_to_legal`, `get_related_laws` |
| 체인 | 8 | `chain_full_research`, `chain_law_system`, `chain_document_review` |
| 기타 | 10 | AI 검색, 영문법령, 연혁법령, 법령용어, 약칭, 법체계도 |

### 2.2 주요 체인 도구

- **`chain_full_research`**: AI검색 → 법령 → 판례 → 해석 — 복합 리서치를 한 번의 호출로
- **`chain_document_review`**: 계약서/MOU 입력 → 법적 리스크 8종 분류, 금액/기간 추출, 조항 충돌 탐지
- **`chain_amendment_track`**: 법령 개정 이력 추적
- **`chain_ordinance_compare`**: 자치법규와 상위 법령 비교

---

## 3. 모두의입법 적용 방안

### 3.1 RAG 챗봇 강화 ⭐⭐⭐

**현황**: 법안 원문 벡터 검색(Qdrant) 기반 LLM 질의응답

**개선 방향**: 챗봇 도구로 법제처 API 실시간 조회 추가

| 사용자 질문 예시 | 활용 도구 |
|-----------------|-----------|
| "이 법안이 개정하는 현행법 38조가 뭔가요?" | `get_law_text` |
| "이 조항 관련 대법원 판례 있어요?" | `search_precedents` |
| "직접강제가 뭔가요?" | `get_daily_to_legal`, `get_legal_term_kb` |
| "이 법의 시행령에선 어떻게 위임하나요?" | `get_three_tier` |

**구현 위치**: `services/ai/rag` — 기존 RAG 파이프라인에 도구 레이어 추가

---

### 3.2 법안 요약 품질 향상 ⭐⭐⭐

**현황**: 법안 원문만 참조해 GPT-5로 요약

**개선 방향**: 요약 전 현행법 조문을 함께 불러와 맥락 강화

```
[현재 흐름]
법안 원문 → GPT-5 요약

[개선 흐름]
법안 원문 → 현행법 조문 조회(get_law_text) → 개정 전/후 비교(compare_old_new) → GPT-5 요약
```

- 개정안 요약에 "현행 조문 vs 개정안" 비교 자동 첨부 가능
- "어떤 조항이 어떻게 바뀌는지" 구조화된 비교 제공

**구현 위치**: `services/ai/processor` — Airflow DAG의 요약 태스크 전처리 단계

---

### 3.3 법률 용어 자동 풀이 ⭐⭐⭐

**현황**: AI 요약에 법률 용어가 그대로 노출

**개선 방향**: 요약 후처리로 법률 용어 일상어 변환 삽입

- `get_daily_to_legal` / `get_legal_term_kb` 활용
- "직접강제", "재량행위", "대집행" 같은 용어 옆에 팝업 또는 인라인 설명 자동 추가
- 비전문가 접근성 향상

**구현 위치**: `services/ai/processor` 또는 `services/backend` API 응답 레이어

---

### 3.4 연관 법령 맵 시각화 ⭐⭐

**현황**: 법안 단독 표시

**개선 방향**: `get_related_laws`로 해당 법안이 영향을 미치는 다른 법령 네트워크 표시

- "이 법안이 바뀌면 함께 봐야 할 법령" 안내
- 법령 간 관계 그래프 시각화 (선택적 기능)

**구현 위치**: `services/backend` 법안 상세 API + `services/web` 프론트엔드

---

### 3.5 법령 3단계 위임 구조 시각화 ⭐⭐

**현황**: 법안 타임라인(발의→위원회→본회의) 제공

**개선 방향**: `get_three_tier`로 법률-시행령-시행규칙 체계 트리 제공

- 법안 상세 페이지 옆 패널에 위임 체계도 표시
- "이 법이 실제 적용되려면 어떤 시행령/규칙이 연결되나요?" 파악 가능

**구현 위치**: `services/web` 법안 상세 페이지

---

### 3.6 계약서/문서 법적 리스크 분석 (신규 기능 후보) ⭐

현재 서비스 스코프 밖이지만 `chain_document_review` + `analyze_document`를 활용하면:
- 계약서나 MOU 업로드 → 법적 리스크 8종 분류, 금액/기간 자동 추출, 조항 충돌 탐지
- B2B 확장 포인트 또는 별도 프리미엄 기능으로 고려 가능

---

## 4. 통합 방식

| 방식 | 설명 | 적합한 용도 |
|------|------|-------------|
| **MCP 서버 직접 연동** | `npm install -g korean-law-mcp` + 환경 설정 | 개발/기획 내부 활용 |
| **원격 엔드포인트** | `https://korean-law-mcp.fly.dev/mcp` 연결 (설치 불필요) | PoC 빠른 검증 |
| **Python 래퍼 직접 통합** | 법제처 API 직접 호출하는 Python 서비스 모듈 작성 | `services/ai` 파이프라인 정식 통합 |

> 정식 도입 시 **Python 래퍼 방식**을 권장. 외부 MCP 서버 의존성 없이 법제처 API 키(`LAW_OC`)만 있으면 자체 관리 가능.

---

## 5. 도입 우선순위

임팩트 대비 구현 난이도 기준:

| 순위 | 기능 | 임팩트 | 난이도 |
|------|------|--------|--------|
| 1 | RAG 챗봇에 법령 조회 도구 추가 | 높음 | 낮음 |
| 2 | 법안 요약 프롬프트에 현행법 컨텍스트 추가 | 높음 | 낮음 |
| 3 | 법률 용어 설명 레이어 | 중간 | 낮음 |
| 4 | 연관 법령 맵 | 중간 | 중간 |
| 5 | 3단계 위임 구조 시각화 | 중간 | 중간 |
| 6 | 계약서 리스크 분석 (신규) | 높음 | 높음 |

---

## 6. 참고

- [korean-law-mcp GitHub](https://github.com/chrisryugj/korean-law-mcp)
- [법제처 Open API](https://open.law.go.kr/LSO/openApi/guideResult.do) — API 키 무료 발급
- [도구 전체 레퍼런스](https://github.com/chrisryugj/korean-law-mcp/blob/main/docs/API.md)
