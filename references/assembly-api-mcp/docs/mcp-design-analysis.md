# MCP 도구 설계 분석 및 통합 계획

작성일: 2026-04-04

---

## 1. 배경

assembly-api-mcp 프로젝트는 현재 23개 개별 MCP 도구를 제공합니다. 다양한 AI 에이전트(Claude Desktop, Cursor, VS Code Copilot, ChatGPT 등)에서 효율적으로 사용할 수 있도록 최적의 도구 설계를 검토했습니다.

### 핵심 질문

> "23개 도구를 그대로 유지할 것인가, 통합할 것인가, 어떤 방식이 AI 에이전트에 가장 효율적인가?"

---

## 2. MCP 생태계 리서치

### 2.1 도구 수와 LLM 효율성 — 실측 데이터

| 도구 수 | 토큰 소비 | LLM 정확도 | 출처 |
|---------|----------|-----------|------|
| 8개 | ~5,600 | 최적 | Speakeasy 벤치마크 |
| 20개 | ~14,200 | 양호 | Speakeasy 벤치마크 |
| 30개+ | ~25,000+ | 저하 시작 | Docker 6개 LLM 테스트 |
| 50개+ | ~77,000 | 심각 저하 | Claude Code 측정 |
| 동적 검색 활용 | ~2,500 (고정) | 높음 | Speakeasy (도구 수 무관) |

**주요 발견:**

- **30개 도구** 초과 시 도구 설명 겹침(semantic overlap)으로 LLM 선택 정확도 저하
- **46개 도구** 지점에서 대부분 모델의 성능 저하가 명확히 관측됨
- 각 도구 설명은 약 **400~800 토큰**을 소비 (스키마 + 설명 포함)
- 동적 검색(Tool Search) 활용 시 토큰 사용량 **160배 감소** 가능

### 2.2 클라이언트별 도구 제한

| MCP 클라이언트 | 도구 제한 | 특징 |
|--------------|---------|------|
| Cursor | **40개** | 하드 리미트, 초과 시 무시 |
| GitHub Copilot | **128개** | OpenAI 호환 제한 |
| Claude Desktop | 제한 없음 | 전체 도구 목록을 프롬프트에 삽입 |
| Claude Code | 제한 없음 | Tool Search로 동적 로딩 (85% 토큰 절감) |
| VS Code (기타) | 제한 없음 | 대규모 코드베이스 최적화 |

### 2.3 실제 MCP 서버 사례 분석

#### Block Square MCP — Layered Pattern (3개 도구)

200+ API 엔드포인트를 **3개 레이어 도구**로 추상화:

```
1. Discovery Tool → 사용 가능한 서비스 탐색
2. Planning Tool  → 필요 파라미터 및 호출 방법 확인
3. Execution Tool → 실제 API 호출
```

- **장점**: 토큰 최소, 무한 확장 가능, 실전 검증
- **단점**: 단순 쿼리에도 2-3회 왕복 필요

#### korean-law-mcp — 프로필 분리 (Lite 14개 / Full 89개)

89개 도구를 프로필로 분리:

- **Lite 프로필**: 웹 클라이언트 최적화 (14개 도구)
- **Full 프로필**: 데스크톱 앱 (89개 도구)
- **체인 도구**: 내부적으로 여러 저수준 도구를 자동 호출
- **메타 도구**: `discover_tools`, `execute_tool`로 나머지 접근

#### data-go-mcp-servers — 마이크로서비스식 분리

각 API 통합을 독립 MCP 서버 패키지로 분리:

- NPS 사업자 등록, NTS 검증, PPS 나라장터 등 각각 독립 서버
- PyPI를 통해 필요한 서비스만 선택 설치
- **장점**: 완벽한 모듈성, 장애 격리
- **단점**: 여러 서버 관리 오버헤드

#### GitHub MCP — 선택적 Toolset

`--toolsets` 플래그로 필요한 도구셋만 활성화:

```bash
# PR 관련 도구만 활성화
github-mcp --toolsets=pulls,reviews
```

### 2.4 MCP 스펙 권장사항

공식 MCP 스펙 및 커뮤니티 합의:

1. **"REST 엔드포인트가 아닌 기능(capability)을 노출하라"**
2. **"각 도구 설명은 400-800 토큰을 소비한다고 가정하라"**
3. **"사용자의 작업을 완성하는 도구를 설계하라"** (API 1:1 매핑 금지)
4. **단일 목적 원칙**: 각 MCP 서버는 명확한 단일 도메인
5. **도구 수 < 30**: 30개 초과 시 모든 벤치마크에서 정확도 저하

---

## 3. 아키텍처 패턴 비교

### 3.1 세 가지 후보

| 패턴 | 도구 수 | 토큰 | 호출 횟수 | 구현 난이도 |
|------|---------|------|----------|-----------|
| A. 단일 도구 (action 라우팅) | 1개 | ~800 | 1회 | 높음 |
| B. 프로필 기반 + 체인 | 8개 (Lite) | ~5,000 | 1회 | 중간 |
| C. 현행 유지 | 23개 | ~14,000 | 1회 | 없음 |

### 3.2 상세 비교

#### 패턴 A: 단일 `national_assembly` 도구

```typescript
server.tool("national_assembly", {
  action: z.enum(["search_members", "search_bills", ...]),
  params: z.record(z.string(), z.any()),
});
```

| 장점 | 단점 |
|------|------|
| 컨텍스트 최소화 (~800 토큰) | action별 파라미터 설명 부재 |
| 확장 시 도구 수 불변 | LLM이 action+params 조합을 추론해야 함 |
| 깔끔한 인터페이스 | 디버깅 어려움 (어떤 action이 실패했는지) |

#### 패턴 B: 프로필 기반 + 체인 도구 (채택)

```
MCP_PROFILE=lite  → 핵심 5개 + 범용 2개 + 체인 1개 = 8개
MCP_PROFILE=full  → 기존 23개 전부
```

| 장점 | 단점 |
|------|------|
| 토큰 60% 절감 (14,000 → 5,000) | 2가지 모드 유지 필요 |
| 도구별 명확한 파라미터 스키마 | Lite에서 세밀한 제어 불가 (query_assembly로 보완) |
| Cursor 40개 제한 충분히 여유 | Full 모드에서 기존 문제 여전 |
| 체인 도구로 복합 분석 1회 호출 | 체인 도구 내부 오류 처리 복잡 |
| 기존 코드 대부분 재사용 | - |

#### 패턴 C: 현행 유지

| 장점 | 단점 |
|------|------|
| 변경 없음, 리스크 제로 | 23개 도구 → ~14,000 토큰 소비 |
| 각 도구 의미 명확 | 30개 근접 시 확장 한계 |
| - | Cursor에서 다른 MCP와 병용 시 제한 도달 가능 |

### 3.3 선택: 패턴 B

**근거:**

1. **실증 데이터**: 8개 도구 = LLM 최적 성능 구간
2. **실전 검증**: korean-law-mcp가 동일 패턴으로 89→14개 성공
3. **하위 호환**: Full 모드로 기존 사용자 영향 없음
4. **확장성**: discover_apis + query_assembly로 276개 API 100% 접근 유지
5. **Cursor 안전**: 8개 도구 = 40개 제한의 20%만 사용

---

## 4. 구현 계획

### 4.1 Lite 프로필 도구 구성 (8개)

| # | 도구명 | 병합 대상 | 역할 |
|---|--------|----------|------|
| 1 | `search_members` | get_members + get_member_detail | 의원 검색 및 상세 조회 |
| 2 | `search_bills` | search_bills + get_bill_detail | 의안 검색 및 상세 조회 |
| 3 | `get_schedule` | get_schedule (그대로) | 국회 일정 |
| 4 | `search_meetings` | search_meeting_records (그대로) | 회의록 검색 |
| 5 | `get_votes` | get_vote_results (그대로) | 표결 결과 |
| 6 | `discover_apis` | discover_apis (그대로) | 276개 API 탐색 |
| 7 | `query_assembly` | query_assembly (그대로) | 범용 API 호출 |
| 8 | `analyze_legislator` | **신규 체인 도구** | 의원 종합 분석 |

### 4.2 Lite에서 제외되는 도구 (15개)

Lite에서 제외되지만 `query_assembly`로 동일 기능 접근 가능:

| 카테고리 | 제외 도구 | query_assembly 대체 |
|---------|----------|-------------------|
| 의원 | search_member_activity | analyze_legislator가 대체 |
| 의안 | get_pending_bills, get_processed_bills, get_recent_bills, get_bill_review, get_bill_history, search_all_bills, get_plenary_votes | `query_assembly(api_code: "BILLRCP", ...)` |
| 위원회 | get_committees | `query_assembly(api_code: "nxrvzonlafugpqjuh")` |
| 청원 | search_petitions | `query_assembly(api_code: "nvqbafvaajdiqhehi")` |
| 입법예고 | get_legislation_notices | `query_assembly(api_code: "nknalejkafmvgzmpt")` |
| 부속기관 | search_library, get_budget_analysis, search_research_reports | `query_assembly` 또는 전용 API |

### 4.3 체인 도구 설계: `analyze_legislator`

```
입력: { name: "고민정", age?: 22 }

내부 실행 (Promise.all 병렬):
  ├── get_members(name) → 인적사항
  ├── search_bills(proposer=name) → 발의 법안 목록
  └── get_vote_results(member=name) → 표결 참여 기록

출력: 통합 의정활동 리포트
  ├── 기본정보 (정당, 선거구, 당선횟수, 소속위원회)
  ├── 발의법안 요약 (총 N건, 주요 법안 5건)
  └── 표결 참여 요약 (참여율, 찬성/반대 비율)
```

### 4.4 최종 결정: 7개 도구 (토론 결과)

AI 에이전트 관점(토큰 최소화) vs 사용자 관점(첫 시도 완전 응답) 토론을 거쳐 7개로 최종 결정:

| # | 도구 | 유형 | 병합 대상 |
|---|------|------|----------|
| 1 | `search_members` | 핵심 | get_members + get_member_detail |
| 2 | `search_bills` | 핵심 | search_bills + get_bill_detail + pending/processed/recent |
| 3 | `search_records` | 핵심 | get_schedule + search_meetings + get_votes (type 파라미터) |
| 4 | `analyze_legislator` | 체인 | 의원 인적+발의+표결 Promise.all |
| 5 | `track_legislation` | 체인 | 다중 키워드 법안 추적 + 심사이력 |
| 6 | `discover_apis` | 범용 | 기존 유지 |
| 7 | `query_assembly` | 범용 | 기존 유지 |

### 4.5 프로필 전환

```typescript
// config.ts — profile 필드 추가
profile: envOrDefault("MCP_PROFILE", "lite") as "lite" | "full"

// server.ts — 분기
if (config.profile === "full") {
  // 기존 23개 도구 전부 등록
} else {
  registerLiteTools(server, config); // 7개 도구
}
```

### 4.6 구현된 파일 구조

```
src/tools/
├── lite/                    ← 신규
│   ├── members.ts           ← search_members (검색+상세 통합)
│   ├── bills.ts             ← search_bills (검색+상세+상태필터)
│   ├── records.ts           ← search_records (일정+회의록+표결)
│   ├── chains.ts            ← analyze_legislator + track_legislation
│   └── index.ts             ← registerLiteTools (7개 등록)
├── members.ts               ← 기존 유지 (Full 모드)
├── bills.ts                 ← 기존 유지
├── discover.ts              ← 양쪽 공용
├── query.ts                 ← 양쪽 공용
└── ...                      ← 나머지 기존 파일 유지
```

---

## 5. 구현 결과

| 지표 | 현재 (Full) | Lite 적용 후 | 개선율 |
|------|-----------|-------------|-------|
| 도구 수 | 23개 | 7개 | **-70%** |
| 토큰 소비 (도구 목록) | ~14,000 | ~3,800 | **-73%** |
| LLM 도구 선택 정확도 | 양호 | 최적 | 향상 |
| Cursor 도구 슬롯 사용 | 23/40 (58%) | 7/40 (17.5%) | **-40%p** |
| 276개 API 접근성 | 100% | 100% (query_assembly) | 유지 |
| 의원 분석 호출 횟수 | 4회 | 1회 (체인) | **-75%** |
| 법안 추적 호출 횟수 | 5-10회 | 1회 (체인) | **-80%** |
| 테스트 | 60개 | 69개 | +9개 |

---

## 6. 참고 자료

- [Block Layered MCP Pattern](https://engineering.block.xyz/blog/build-mcp-tools-like-ogres-with-layers) — 200+ API를 3개 도구로
- [MCP Best Practices](https://modelcontextprotocol.info/docs/best-practices/) — 공식 권장사항
- [Speakeasy: 160x 토큰 감소](https://www.speakeasy.com/blog/how-we-reduced-token-usage-by-100x-dynamic-toolsets-v2) — 동적 도구 검색
- [Docker MCP 벤치마크](https://www.docker.com/blog/mcp-server-best-practices/) — 6개 LLM 도구 정확도 테스트
- [korean-law-mcp](https://github.com/chrisryugj/korean-law-mcp) — Lite/Full 프로필 사례
- [Cursor 도구 제한 논의](https://forum.cursor.com/t/about-limitation-of-the-number-of-mcp-tools/107844) — 40개 제한
- [Why Less is More for MCP](https://www.speakeasy.com/mcp/tool-design/less-is-more) — 도구 수 최소화 원칙
