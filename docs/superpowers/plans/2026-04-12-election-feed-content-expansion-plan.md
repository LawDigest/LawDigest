# Plan: 선거 피드 탭 콘텐츠 확장

**Generated**: 2026-04-12
**Estimated Complexity**: High
**Target**: 제9회 전국동시지방선거 (2026-06-03) 이전 완료
**Deadline**: 2026-05-25 (선거 1주 전 안정화 기간 확보)

## Overview

선거 피드 탭(`/election?tab=feed`)에 **뉴스, 공약, 선거 일정** 등 새로운 콘텐츠 소스를 추가하고, **무한 스크롤**과 **북마크/저장** 기능을 구현한다. 기존 Mock 데이터 기반의 SNS/YouTube/법안 카드도 실제 데이터 소스로 전환한다.

**핵심 설계 원칙:**
- 커서 기반 통합 피드 API로 모든 소스를 하나의 타임라인에 병합
- Airflow DAG 기반 자동 수집 (뉴스, SNS, YouTube)
- 기존 파이프라인 활용 극대화 (공약: election_ingest_dag, 법안: bill_ingest_dag)
- 범용 북마크 모델로 모든 피드 아이템 저장 가능

**현재 상태:**

| 소스 | 데이터 | 수집 파이프라인 | 백엔드 API | 프론트 카드 |
|------|--------|---------------|-----------|-----------|
| 여론조사 | 실시간 | ✅ polls_ingest_dag | ✅ /election/polls/* | ✅ PollCard |
| 후보자/공약 | 실데이터 | ✅ election_ingest_dag | ✅ /election/candidates/* | ⚠️ 상세만 |
| 법안 | 실데이터 | ✅ bill_ingest_dag | ✅ /bill/* | ⚠️ Mock 카드 |
| 뉴스 | 없음 | ❌ | ❌ | ❌ |
| SNS | Mock | ❌ | ❌ | ✅ SnsCard |
| YouTube | Mock | ❌ | ❌ | ✅ YoutubeCard |
| 선거 일정 | 부분 | ⚠️ sgVotedate만 | ❌ | ❌ |

---

## 구현 우선순위

| 순위 | Sprint | 콘텐츠 | 이유 |
|------|--------|--------|------|
| **P0** | Sprint 1 | 통합 피드 API + 무한 스크롤 | 모든 소스 통합의 기반 인프라 |
| **P0** | Sprint 1 | 공약 피드 | 파이프라인 완성, API 노출만 필요 |
| **P0** | Sprint 1 | 선거 일정 | 정적 데이터, 즉시 구현 가능 |
| **P0** | Sprint 1 | 법안 연결 | 기존 데이터 활용, 필터링 추가 |
| **P1** | Sprint 2 | 뉴스 | 새 파이프라인 필요하나 네이버 API 간단 |
| **P1** | Sprint 2 | 북마크/저장 | 범용 모델 설계 필요 |
| **P2** | Sprint 3 | YouTube | API quota 관리 필요 |
| **P2** | Sprint 3 | SNS | 플랫폼 API 제약 큼, 주요 후보만 |

---

## Prerequisites

### 공통
- MySQL DB 접속 정보 (기존 `.env` 활용)
- Spring Boot 백엔드 (`services/backend/`)
- Next.js 14 프론트엔드 (`services/web/`)
- Airflow 인프라 (`infra/airflow/`)

### API 키 (필요 시 발급)
- **네이버 검색 API**: Client ID + Client Secret (Sprint 2)
- **YouTube Data API v3**: API Key (Sprint 3)
- **X (트위터) API v2**: Bearer Token — Free 또는 Basic tier (Sprint 3)

---

## Sprint 1: 기반 인프라 + 기존 데이터 연동 (P0)

**Goal**: 통합 피드 API, 무한 스크롤, 공약/일정/법안 피드 카드 구현
**기간**: 1주

### Task 1.1: 통합 피드 API 설계 — 커서 기반 페이지네이션

**백엔드 (Spring Boot)**

- **Location**: `services/backend/src/main/java/com/everyones/lawmaking/controller/ElectionFeedController.java`

- **엔드포인트**:
```
GET /v1/election/feed
  ?election_id={string}        — 필수: 선거 ID
  &cursor={string}             — 선택: 페이지네이션 커서 (첫 요청 시 생략)
  &size={int, default=20}      — 선택: 페이지 크기
  &type={string}               — 선택: 콘텐츠 필터 (all|news|poll|pledge|sns|youtube|bill|schedule)
  &party={string}              — 선택: 정당 필터
  &region_code={string}        — 선택: 지역 필터
```

- **응답 DTO**:
```java
public record ElectionFeedResponse(
    List<ElectionFeedItem> items,
    String nextCursor,       // null이면 마지막 페이지
    boolean hasMore
) {}

public record ElectionFeedItem(
    String id,               // "{type}-{sourceId}" (예: "pledge-123")
    String type,             // news, poll, pledge, sns, youtube, bill, schedule
    String publishedAt,      // ISO 8601
    Object payload           // 타입별 다형 JSON
) {}
```

- **커서 구현**:
  - cursor = Base64(`publishedAt|id`) — publishedAt 내림차순 정렬 시 중복 없는 페이지네이션 보장
  - 각 소스 테이블에서 `WHERE published_at < :cursorDate OR (published_at = :cursorDate AND id < :cursorId)` 조건으로 쿼리
  - 모든 소스에서 size+1개를 가져와 merge sort → 상위 size개 반환, 나머지가 있으면 hasMore=true

- **서비스 구조**:
```
ElectionFeedController
  └── ElectionFeedService
        ├── ElectionFeedPledgeProvider   — 공약 피드
        ├── ElectionFeedBillProvider     — 법안 피드
        ├── ElectionFeedPollProvider     — 여론조사 피드
        ├── ElectionFeedScheduleProvider — 일정 피드
        ├── ElectionFeedNewsProvider     — 뉴스 피드 (Sprint 2)
        ├── ElectionFeedYoutubeProvider  — YouTube 피드 (Sprint 3)
        └── ElectionFeedSnsProvider      — SNS 피드 (Sprint 3)
```

  각 Provider는 공통 인터페이스를 구현:
```java
public interface ElectionFeedProvider {
    String getType();
    List<ElectionFeedItem> fetch(String electionId, String cursorDate, String cursorId, 
                                  int limit, String party, String regionCode);
}
```

  ElectionFeedService는 활성화된 Provider들에서 각각 limit개를 가져와 publishedAt 기준 merge sort 후 상위 size개를 반환한다.

- **Files**:
  - Create: `controller/ElectionFeedController.java`
  - Create: `service/election/feed/ElectionFeedService.java`
  - Create: `service/election/feed/ElectionFeedProvider.java` (인터페이스)
  - Create: `common/dto/response/election/ElectionFeedResponse.java`
  - Create: `common/dto/response/election/ElectionFeedItem.java`

---

### Task 1.2: 프론트엔드 — 무한 스크롤 + 통합 피드 훅

**프론트엔드 (Next.js)**

- **API 함수**:
  - Location: `services/web/app/election/apis/apis.ts`
```typescript
export const getElectionFeed = (
  electionId: ElectionId,
  cursor?: string,
  size?: number,
  type?: FeedContentType,
  party?: string,
  regionCode?: ElectionRegionCode,
) =>
  http.get<ElectionFeedResponse>({
    url: '/election/feed',
    params: {
      election_id: electionId,
      cursor,
      size: size ?? 20,
      type: type ?? 'all',
      party,
      region_code: regionCode,
    },
  });
```

- **React Query 무한 스크롤 훅**:
  - Location: `services/web/app/election/apis/queries.ts`
```typescript
export const useElectionFeedInfinite = (
  electionId: ElectionId,
  type?: FeedContentType,
  party?: string,
  regionCode?: ElectionRegionCode,
) =>
  useInfiniteQuery({
    queryKey: ['election', 'feed', electionId, type, party, regionCode],
    queryFn: ({ pageParam }) =>
      getElectionFeed(electionId, pageParam, 20, type, party, regionCode),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (lastPage) =>
      lastPage.data.hasMore ? lastPage.data.nextCursor : undefined,
    enabled: !!electionId,
  });
```

- **IntersectionObserver 트리거**:
  - Location: `services/web/app/election/components/ElectionFeedView.tsx`
  - 마지막 카드 아래에 sentinel div를 두고, IntersectionObserver로 화면에 진입 시 `fetchNextPage()` 호출
  - 로딩 중 스켈레톤 카드 3개 표시
  - 에러 시 "다시 시도" 버튼

- **타입 정의**:
  - Location: `services/web/types/type/election/election.ts`
```typescript
export type FeedContentType = 'all' | 'news' | 'poll' | 'pledge' | 'sns' | 'youtube' | 'bill' | 'schedule';

export interface ElectionFeedResponse {
  items: ElectionFeedItemDto[];
  nextCursor: string | null;
  hasMore: boolean;
}

export interface ElectionFeedItemDto {
  id: string;
  type: FeedContentType;
  publishedAt: string;
  payload: NewsFeedPayload | PollFeedPayload | PledgeFeedPayload
         | SnsFeedPayload | YoutubeFeedPayload | BillFeedPayload | ScheduleFeedPayload;
}
```

- **ElectionFeedView 수정**:
  - 기존 Mock 데이터 + realPollItems 조합 로직 제거
  - `useElectionFeedInfinite` 훅으로 전환
  - 서브탭(전체/정당별/후보자별/지역별) 변경 시 type/party/regionCode 파라미터 변경
  - `ElectionFeedCardList`는 `ElectionFeedItemDto[]` 기반으로 렌더링

- **Files**:
  - Modify: `services/web/app/election/apis/apis.ts` — getElectionFeed 추가
  - Modify: `services/web/app/election/apis/queries.ts` — useElectionFeedInfinite 추가
  - Modify: `services/web/types/type/election/election.ts` — 피드 타입 추가
  - Modify: `services/web/app/election/components/ElectionFeedView.tsx` — 무한 스크롤 전환
  - Modify: `services/web/app/election/components/ElectionFeedCardList.tsx` — DTO 기반 렌더링
  - Modify: `services/web/app/election/data/mockFeedData.ts` — 통합 DTO 대응 mock 추가

---

### Task 1.3: 공약 피드 — 기존 파이프라인 연동

**수집**: ✅ 이미 완료 (election_ingest_dag → `collect_pledges` → `election_pledges`, `election_party_policies` 테이블)

**백엔드 Provider**:
- Location: `services/backend/src/main/java/com/everyones/lawmaking/service/election/feed/ElectionFeedPledgeProvider.java`

- 쿼리 로직:
  - `election_pledges` JOIN `election_candidates` → 후보자명, 정당명, 지역 포함
  - `election_party_policies` → 정당 정책도 함께 제공
  - `publishedAt` = `election_pledges.created_at` (DB 등록 시점)

- Payload 구조:
```java
public record PledgeFeedPayload(
    Long candidateId,
    String candidateName,
    String partyName,
    String region,
    int pledgeOrder,
    String pledgeTitle,
    String pledgeContent,
    String summary          // LLM 요약 (있으면)
) {}
```

**프론트엔드 카드**:
- Location: `services/web/app/election/components/feed/PledgeCard.tsx` (신규)
- 디자인:
  - 타입칩: `공약` (bg-teal-50 / text-teal-600)
  - 헤더: 후보자명 · 정당명 · 지역
  - 본문: 공약 제목 (bold) + 공약 내용 요약 (2줄 truncate)
  - 액션: "전문 보기" → `/election/candidates/{candidateId}` 상세 페이지

- **Files**:
  - Create: `service/election/feed/ElectionFeedPledgeProvider.java`
  - Create: `repository/election/ElectionPledgeRepository.java` (JPA)
  - Create: `services/web/app/election/components/feed/PledgeCard.tsx`
  - Create: `services/web/app/election/components/feed/PledgeCard.test.tsx`

---

### Task 1.4: 선거 일정 피드 — 정적 config 기반

**수집**: 정적 JSON config (선관위 공식 발표 기반 수동 관리)

- Location: `services/backend/src/main/resources/election/schedule_local_2026.json`

```json
{
  "electionId": "local-2026",
  "events": [
    {
      "date": "2026-03-24",
      "endDate": null,
      "label": "예비후보 등록 개시",
      "category": "registration",
      "description": "광역·기초단체장, 교육감 예비후보 등록 시작"
    },
    {
      "date": "2026-05-14",
      "endDate": "2026-05-15",
      "label": "후보자 등록",
      "category": "registration",
      "description": "공식 후보자 등록 기간"
    },
    {
      "date": "2026-05-16",
      "endDate": "2026-06-02",
      "label": "선거운동 기간",
      "category": "campaign",
      "description": "공식 선거운동 기간"
    },
    {
      "date": "2026-05-29",
      "endDate": "2026-05-30",
      "label": "사전투표",
      "category": "voting",
      "description": "전국 사전투표소에서 투표 가능"
    },
    {
      "date": "2026-06-03",
      "endDate": null,
      "label": "투표일",
      "category": "voting",
      "description": "제9회 전국동시지방선거 투표일"
    }
  ]
}
```

**백엔드 Provider**:
- Location: `service/election/feed/ElectionFeedScheduleProvider.java`
- 로직:
  - JSON config에서 이벤트 로드 (앱 시작 시 캐시)
  - 다가오는 일정(D-day 기준)을 피드에 노출
  - `publishedAt` = 이벤트 date (미래 일정은 현재 시각으로 취급하여 피드 상단에 고정)

- Payload 구조:
```java
public record ScheduleFeedPayload(
    String date,
    String endDate,
    String label,
    String category,       // registration, campaign, voting
    String description,
    int dDay               // 오늘 기준 D-day (음수면 지남)
) {}
```

**프론트엔드 카드**:
- Location: `services/web/app/election/components/feed/ScheduleCard.tsx` (신규)
- 디자인:
  - 타입칩: `일정` (bg-yellow-50 / text-yellow-700)
  - D-day 카운트다운 배지 (D-7 이내면 강조)
  - 일정명 + 날짜 범위 + 설명
  - 투표일은 특별 강조 스타일 (그래디언트 보더)

- **Files**:
  - Create: `service/election/feed/ElectionFeedScheduleProvider.java`
  - Create: `src/main/resources/election/schedule_local_2026.json`
  - Create: `services/web/app/election/components/feed/ScheduleCard.tsx`
  - Create: `services/web/app/election/components/feed/ScheduleCard.test.tsx`

---

### Task 1.5: 법안 연결 — 기존 bill 데이터 필터링

**수집**: ✅ 이미 완료 (bill_ingest_dag → `bill` 테이블)

**백엔드 Provider**:
- Location: `service/election/feed/ElectionFeedBillProvider.java`

- 필터링 전략:
  1. **키워드 매칭**: bill_name 또는 summary에 선거 관련 키워드 포함
     - 키워드: "선거", "지방자치", "교육감", "공직선거법", "정당법", "정치자금법", "투표", "개표"
  2. **후보자 발의 법안**: `bill_proposer` → `congressman` 매핑으로, 현재 선거 후보자가 대표발의한 법안
  3. `publishedAt` = `bill.propose_date`

- Payload 구조:
```java
public record BillFeedPayload(
    String billId,
    String billName,
    String briefSummary,
    String stage,
    String proposeDate,
    String partyName,
    String proposerName
) {}
```

**프론트엔드**: 기존 `BillCard.tsx` 컴포넌트 활용 (payload 매핑만 수정)

- **Files**:
  - Create: `service/election/feed/ElectionFeedBillProvider.java`
  - Modify: `services/web/app/election/components/feed/BillCard.tsx` — payload 인터페이스 대응

---

### Task 1.6: 여론조사 Provider 통합

**수집**: ✅ 이미 완료 (polls_ingest_dag)

**백엔드 Provider**:
- Location: `service/election/feed/ElectionFeedPollProvider.java`
- 기존 `PollQueryService.getOverview()`의 `latest_surveys` 데이터를 피드 형태로 변환
- `publishedAt` = `survey_end_date`

**프론트엔드**: 기존 `PollCard.tsx` 활용

- **Files**:
  - Create: `service/election/feed/ElectionFeedPollProvider.java`

---

## Sprint 2: 뉴스 수집 + 북마크 (P1)

**Goal**: 네이버 뉴스 API 기반 실시간 뉴스 수집 + 범용 북마크 시스템
**기간**: 1주
**의존성**: Sprint 1 완료 (통합 피드 API)

### Task 2.1: 뉴스 수집 파이프라인

**수집 대상**:
- 선거 관련 뉴스 기사
- 대상 매체: 종합지, 방송사, 통신사, **지역 매체 포함**
- 검색 키워드: 후보자명, 정당명, 선거구명 조합

**API**: 네이버 검색 API (`openapi.naver.com/v1/search/news.json`)
- 무료 일 25,000건 (충분)
- 검색어 조합:
  - 전국: `"지방선거" OR "6.3 선거"`
  - 정당별: `"더불어민주당 지방선거"`, `"국민의힘 지방선거"`
  - 지역별: `"서울시장" OR "서울 지방선거"`, `"경기도지사"` 등
  - 후보자별: `"홍길동 후보"` (주요 후보 한정)

**수집 주기**: 1시간 간격 (Airflow DAG)

**DB 테이블**:
```sql
CREATE TABLE election_news (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    election_id     VARCHAR(50) NOT NULL,

    -- 기사 정보
    title           VARCHAR(500) NOT NULL,
    description     TEXT,
    link            VARCHAR(1000) NOT NULL,
    original_link   VARCHAR(1000),
    source          VARCHAR(100),          -- 매체명
    thumbnail_url   VARCHAR(1000),
    pub_date        DATETIME NOT NULL,

    -- 매핑 정보
    search_keyword  VARCHAR(200),          -- 검색에 사용된 키워드
    matched_party   VARCHAR(100),          -- 매칭된 정당명 (nullable)
    matched_region  VARCHAR(100),          -- 매칭된 지역명 (nullable)

    -- 메타
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,

    UNIQUE KEY uk_news_link (link(500)),
    INDEX idx_election_pubdate (election_id, pub_date DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**Airflow DAG**:
- Location: `infra/airflow/dags/election_news_ingest_dag.py`
- 스케줄: `0 * * * *` (매시간)
- Tasks:
  1. `build_search_queries` — 후보자/정당/지역 기반 검색어 목록 생성
  2. `fetch_news` — 네이버 API 호출 + 중복 제거 + DB 저장
  3. `tag_news` — 기사 제목/본문에서 정당명·지역명 매칭

**Python 수집기**:
- Location: `services/data/src/lawdigest_data/elections/collectors/news_collector.py`

```python
class NaverNewsCollector:
    """네이버 검색 API를 이용한 선거 뉴스 수집기."""

    BASE_URL = "https://openapi.naver.com/v1/search/news.json"

    def __init__(self, client_id: str, client_secret: str, session: Session):
        self.client_id = client_id
        self.client_secret = client_secret
        self.session = session

    def collect(self, keyword: str, display: int = 100, sort: str = "date") -> list[dict]:
        """키워드 기반 뉴스 검색 및 DB 저장."""
        ...

    def _build_election_queries(self, election_id: str) -> list[str]:
        """선거 ID 기반 검색 키워드 조합 생성.

        전국 단위, 정당별, 17개 시도별, 주요 후보별 쿼리를 생성한다.
        지역 매체 기사도 포함되도록 지역명 키워드를 적극 활용한다.
        """
        ...
```

**백엔드 Provider**:
- Location: `service/election/feed/ElectionFeedNewsProvider.java`
- Payload:
```java
public record NewsFeedPayload(
    Long newsId,
    String title,
    String description,
    String link,
    String source,
    String thumbnailUrl,
    String matchedParty,
    String matchedRegion
) {}
```

**프론트엔드 카드**:
- Location: `services/web/app/election/components/feed/NewsCard.tsx` (신규)
- 디자인:
  - 타입칩: `뉴스` (bg-orange-50 / text-orange-600)
  - 레이아웃: 좌측 텍스트(제목 + 요약 2줄 + 출처 · 시간) + 우측 썸네일(80x80)
  - 클릭 → 원본 기사 링크 (`target="_blank"`)

- **Files**:
  - Create: DB 마이그레이션 (`election_news` 테이블)
  - Create: `services/data/src/lawdigest_data/elections/collectors/news_collector.py`
  - Create: `services/data/src/lawdigest_data/elections/models/news.py` (SQLAlchemy ORM)
  - Create: `infra/airflow/dags/election_news_ingest_dag.py`
  - Create: `service/election/feed/ElectionFeedNewsProvider.java`
  - Create: `domain/entity/election/ElectionNews.java` (JPA Entity)
  - Create: `repository/election/ElectionNewsRepository.java`
  - Create: `services/web/app/election/components/feed/NewsCard.tsx`
  - Create: `services/web/app/election/components/feed/NewsCard.test.tsx`

---

### Task 2.2: 북마크/저장 기능

**DB 테이블**:
```sql
CREATE TABLE election_feed_bookmark (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id         BIGINT NOT NULL,
    feed_type       VARCHAR(20) NOT NULL,     -- news, poll, pledge, sns, youtube, bill, schedule
    feed_item_id    VARCHAR(100) NOT NULL,     -- 각 소스 테이블의 PK
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,

    UNIQUE KEY uk_user_feed (user_id, feed_type, feed_item_id),
    INDEX idx_user_created (user_id, created_at DESC),
    CONSTRAINT fk_bookmark_user FOREIGN KEY (user_id) REFERENCES user(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**백엔드 API**:
- Location: `controller/ElectionFeedController.java`에 추가

```
POST   /v1/election/feed/bookmark
  Body: { "feedType": "news", "feedItemId": "123" }
  → 201 Created

DELETE /v1/election/feed/bookmark
  Body: { "feedType": "news", "feedItemId": "123" }
  → 200 OK

GET    /v1/election/feed/bookmarks
  ?cursor={}&size=20
  → 북마크한 피드 아이템 목록 (커서 기반 페이지네이션)
```

- 인증 필요: Spring Security의 `@AuthenticationPrincipal`로 user_id 추출
- 기존 `BillLike`와 유사한 패턴이나, 범용 피드 타입 지원

**프론트엔드**:
- 각 피드 카드 우측 상단에 북마크 아이콘 (빈 하트/채워진 하트 토글)
- `useElectionFeedBookmark()` mutation 훅
- 저장한 피드 모아보기: 서브탭 추가 또는 별도 페이지

- **Files**:
  - Create: DB 마이그레이션 (`election_feed_bookmark` 테이블)
  - Create: `domain/entity/election/ElectionFeedBookmark.java`
  - Create: `repository/election/ElectionFeedBookmarkRepository.java`
  - Create: `service/election/feed/ElectionFeedBookmarkService.java`
  - Modify: `controller/ElectionFeedController.java` — 북마크 엔드포인트 추가
  - Modify: `services/web/app/election/apis/apis.ts` — 북마크 API 함수
  - Modify: `services/web/app/election/apis/queries.ts` — 북마크 mutation 훅
  - Modify: 각 피드 카드 컴포넌트 — 북마크 아이콘 추가

---

## Sprint 3: YouTube + SNS 실데이터 전환 (P2)

**Goal**: YouTube/SNS Mock 데이터를 실제 API 기반으로 전환
**기간**: 1.5주
**의존성**: Sprint 1 완료

### Task 3.1: YouTube 영상 수집

**수집 대상**:
- 주요 정당 공식 채널 (더불어민주당, 국민의힘, 조국혁신당, 개혁신당 등)
- 주요 후보 개인 채널
- 중앙선관위 공식 채널 (토론회 영상)

**API**: YouTube Data API v3
- 일 10,000 quota 무료
- `playlistItems.list` (1 quota/요청) 사용 → 채널별 업로드 재생목록 조회
- `search.list` (100 quota/요청) 대비 100배 효율

**Quota 관리**:
- 20개 채널 × 2시간마다 = 일 240 요청 = 240 quota (10,000의 2.4%)
- 넉넉한 여유 확보

**DB 테이블**:
```sql
CREATE TABLE election_youtube_videos (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    election_id     VARCHAR(50) NOT NULL,
    video_id        VARCHAR(20) NOT NULL,
    channel_id      VARCHAR(30) NOT NULL,
    candidate_id    BIGINT,                   -- FK nullable
    party_name      VARCHAR(100),

    title           VARCHAR(500) NOT NULL,
    description     TEXT,
    thumbnail_url   VARCHAR(1000),
    published_at    DATETIME NOT NULL,
    view_count      BIGINT DEFAULT 0,
    like_count      BIGINT DEFAULT 0,
    comment_count   BIGINT DEFAULT 0,

    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uk_video (video_id),
    INDEX idx_election_published (election_id, published_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**채널 목록 config**:
- Location: `services/data/config/election_youtube_channels.json`
```json
[
  { "channelId": "UCxxxxx", "partyName": "더불어민주당", "label": "더불어민주당 공식" },
  { "channelId": "UCyyyyy", "partyName": "국민의힘", "label": "국민의힘 공식" },
  { "channelId": "UCzzzzz", "partyName": null, "label": "중앙선거관리위원회" }
]
```

**Airflow DAG**:
- Location: `infra/airflow/dags/election_youtube_ingest_dag.py`
- 스케줄: `0 */2 * * *` (2시간마다)

**프론트엔드**: 기존 `YoutubeCard.tsx` 활용 (payload 매핑만 수정)

- **Files**:
  - Create: DB 마이그레이션
  - Create: `services/data/src/lawdigest_data/elections/collectors/youtube_collector.py`
  - Create: `services/data/src/lawdigest_data/elections/models/youtube.py`
  - Create: `services/data/config/election_youtube_channels.json`
  - Create: `infra/airflow/dags/election_youtube_ingest_dag.py`
  - Create: `service/election/feed/ElectionFeedYoutubeProvider.java`
  - Create: `domain/entity/election/ElectionYoutubeVideo.java`
  - Create: `repository/election/ElectionYoutubeVideoRepository.java`
  - Modify: `services/web/app/election/components/feed/YoutubeCard.tsx`

---

### Task 3.2: SNS 수집 — 정당 및 주요 후보만

**수집 대상**:
- **정당 공식 계정**: 더불어민주당, 국민의힘, 조국혁신당, 개혁신당 등 원내정당
- **주요 후보**: 광역단체장(시도지사) 후보 위주 (약 30~50명)
- **플랫폼**: X(트위터) + 페이스북 공식 페이지

**X (트위터) API**:
- Free tier: 월 1,500건 읽기 → 정당(~5) + 주요 후보(~30) = 35개 계정
- 30분 간격 수집 시 월 35×48×30 = 50,400건 → **Free tier 초과**
- **대안**: Basic tier ($100/월, 월 10,000건 읽기) 또는 수집 간격 조정
- **권장**: Basic tier 사용하거나, **4시간 간격으로 줄여 월 35×6×30 = 6,300건** (Free tier 범위)

**페이스북 Graph API**:
- 공식 페이지의 공개 게시물만 (Page Public Content Access)
- 앱 리뷰 필요 → 시간 소요 가능
- **1차 MVP: X만 수집, 페이스북은 2차**

**DB 테이블**:
```sql
CREATE TABLE election_sns_posts (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    election_id     VARCHAR(50) NOT NULL,
    platform        VARCHAR(20) NOT NULL,       -- twitter, facebook, instagram
    post_id         VARCHAR(100) NOT NULL,       -- 플랫폼별 고유 ID
    account_id      VARCHAR(100) NOT NULL,       -- 계정 ID
    candidate_id    BIGINT,                      -- FK nullable
    party_name      VARCHAR(100),

    author_name     VARCHAR(200) NOT NULL,
    content         TEXT NOT NULL,
    media_urls      JSON,                        -- 첨부 이미지/영상 URL 배열
    original_url    VARCHAR(1000),
    published_at    DATETIME NOT NULL,

    like_count      INT DEFAULT 0,
    reply_count     INT DEFAULT 0,
    repost_count    INT DEFAULT 0,
    region          VARCHAR(100),

    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,

    UNIQUE KEY uk_platform_post (platform, post_id),
    INDEX idx_election_published (election_id, published_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**SNS 계정 config**:
- Location: `services/data/config/election_sns_accounts.json`
```json
[
  {
    "platform": "twitter",
    "accountId": "theminjoo_kr",
    "partyName": "더불어민주당",
    "label": "더불어민주당 공식",
    "candidateId": null
  },
  {
    "platform": "twitter",
    "accountId": "powerofpeople21",
    "partyName": "국민의힘",
    "label": "국민의힘 공식",
    "candidateId": null
  }
]
```

**Airflow DAG**:
- Location: `infra/airflow/dags/election_sns_ingest_dag.py`
- 스케줄: `0 */4 * * *` (4시간마다 — Free tier 고려)

**프론트엔드**: 기존 `SnsCard.tsx` 활용

- **Files**:
  - Create: DB 마이그레이션
  - Create: `services/data/src/lawdigest_data/elections/collectors/sns_collector.py`
  - Create: `services/data/src/lawdigest_data/elections/models/sns.py`
  - Create: `services/data/config/election_sns_accounts.json`
  - Create: `infra/airflow/dags/election_sns_ingest_dag.py`
  - Create: `service/election/feed/ElectionFeedSnsProvider.java`
  - Create: `domain/entity/election/ElectionSnsPost.java`
  - Create: `repository/election/ElectionSnsPostRepository.java`
  - Modify: `services/web/app/election/components/feed/SnsCard.tsx`

---

## 전체 아키텍처 요약

```
┌─────────────────────────────────────────────────────────────┐
│                        Data Sources                         │
├──────────┬──────────┬──────────┬──────────┬────────────────┤
│ 중앙선관위 │ 네이버뉴스 │ YouTube  │ X(트위터) │  국회 의안 API  │
│  OpenAPI  │ Search   │ Data API │  API v2  │   (기존)       │
└────┬─────┴────┬─────┴────┬─────┴────┬─────┴───────┬────────┘
     │          │          │          │             │
┌────▼──────────▼──────────▼──────────▼─────────────▼────────┐
│                    Airflow DAGs                              │
├─────────────┬──────────┬────────────┬───────────┬──────────┤
│ election_   │ election_│ election_  │ election_ │ bill_    │
│ ingest_dag  │ news_dag │ youtube_dag│ sns_dag   │ ingest   │
│ (공약/후보) │ (뉴스)   │ (YouTube)  │ (SNS)     │ (법안)   │
└──────┬──────┴────┬─────┴─────┬─────┴─────┬─────┴────┬─────┘
       │           │           │           │          │
┌──────▼───────────▼───────────▼───────────▼──────────▼──────┐
│                         MySQL DB                            │
├──────────────┬───────────┬──────────────┬──────────────────┤
│ election_    │ election_ │ election_    │ election_sns_    │
│ pledges      │ news      │ youtube_     │ posts            │
│ party_       │           │ videos       │                  │
│ policies     │           │              │ bill (기존)      │
│ candidates   │           │              │ poll_surveys     │
└──────┬───────┴─────┬─────┴──────┬───────┴────────┬─────────┘
       │             │            │                │
┌──────▼─────────────▼────────────▼────────────────▼─────────┐
│              Spring Boot Backend                            │
│  ElectionFeedService                                        │
│    ├── PledgeProvider   ── merge sort ──┐                   │
│    ├── BillProvider                     │                   │
│    ├── PollProvider                     ├→ GET /feed        │
│    ├── ScheduleProvider                 │   (cursor-based)  │
│    ├── NewsProvider                     │                   │
│    ├── YoutubeProvider                  │                   │
│    └── SnsProvider     ────────────────┘                   │
│                                                             │
│  ElectionFeedBookmarkService ────→ POST/DELETE /bookmark    │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│              Next.js 14 Frontend                            │
│                                                             │
│  ElectionFeedView                                           │
│    ├── SubTabBar (전체/정당별/후보자별/지역별)              │
│    ├── useElectionFeedInfinite (React Query)                │
│    ├── IntersectionObserver (무한 스크롤 트리거)            │
│    └── ElectionFeedCardList                                 │
│          ├── ScheduleCard  (일정 — 상단 고정)              │
│          ├── PollCard      (여론조사)                       │
│          ├── PledgeCard    (공약)      ← 신규              │
│          ├── NewsCard      (뉴스)      ← 신규              │
│          ├── BillCard      (법안)                           │
│          ├── YoutubeCard   (YouTube)                        │
│          ├── SnsCard       (SNS)                            │
│          └── 🔖 BookmarkButton (각 카드 공통)              │
└─────────────────────────────────────────────────────────────┘
```

---

## 타임라인

```
W1 (04/14~04/18)  Sprint 1: 통합 피드 API + 무한 스크롤 + 공약/일정/법안
W2 (04/21~04/25)  Sprint 2: 뉴스 수집 + 북마크                [네이버 API 키 필요]
W3 (04/28~05/09)  Sprint 3: YouTube + SNS 실데이터             [YouTube/X API 키 필요]
W4 (05/12~05/16)  QA 및 안정화
W5 (05/25~)       선거 1주 전 — 모니터링 모드
```

---

## 리스크 및 대응

| 리스크 | 영향 | 대응 |
|--------|------|------|
| X API Free tier 한도 초과 | SNS 수집 불가 | 4시간 간격으로 조정 또는 Basic tier($100/월) 발급 |
| 네이버 뉴스 API 중복 기사 | 피드 품질 저하 | URL 기반 unique + 제목 유사도 기반 중복 제거 |
| YouTube quota 소진 | 영상 수집 중단 | playlistItems.list 사용으로 quota 최적화 (일 240/10,000) |
| 페이스북 앱 리뷰 지연 | FB SNS 수집 불가 | 1차 MVP에서 X만 수집, FB는 2차로 연기 |
| 공약 데이터 미등록 | 공약 피드 비어있음 | 후보자 등록 기간(5/14) 이후 본격 노출, 그 전까지 정당 정책으로 대체 |
| 통합 피드 정렬 불일치 | UX 혼란 | 모든 소스의 publishedAt을 UTC로 통일 + 일정은 상단 고정 |
