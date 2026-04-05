# 선거 탭 하위 피드/여론조사/내 지역구 UI/UX 설계

- **작성일:** 2026-04-04
- **대상:** `services/web/app/election/`
- **단계:** 목업(Mock) 우선 구현 → UI/UX 다듬기 → 기능 구현

---

## 1. 배경 및 목표

선거 탭(`/election`)은 현재 4개 서브탭을 가진다: **지도**(구현 완료), **피드**, **여론조사**, **내 지역구**(세 탭 모두 플레이스홀더 상태).

이 문서는 나머지 3개 탭의 UI/UX 설계를 정의한다.

**목표:**
- 일반 유권자의 선거 정보 브라우징 지원
- 적극적 유권자의 내 지역구 중심 개인화 정보 지원

---

## 2. 전체 구조 (접근 방식 A: 탭별 독립 컴포넌트)

```
ElectionMapShell
├── ElectionDdayHeader
├── ElectionInnerTabBar  (지도 | 피드 | 여론조사 | 내 지역구)
├── [공유 상태: confirmedRegion]
│
├── activeTab === 'map'      → ElectionMapTabView (기존, 변경 없음)
├── activeTab === 'feed'     → ElectionFeedView (신규)
├── activeTab === 'poll'     → ElectionPollView (신규)
└── activeTab === 'district' → ElectionDistrictView (신규)
```

### 공유 상태: confirmedRegion

`ElectionMapShell`에 `useState`로 `confirmedRegion`을 추가하고, 각 뷰 컴포넌트에 props로 내려준다.

```ts
// ElectionMapShell.tsx 추가
interface ConfirmedRegion {
  regionCode: string;   // e.g. '11'  (시/도 코드)
  regionName: string;   // e.g. '서울특별시'
}
const [confirmedRegion, setConfirmedRegion] = useState<ConfirmedRegion | null>(null);
```

각 뷰 컴포넌트 props 인터페이스:
```ts
interface ElectionFeedViewProps     { confirmedRegion: ConfirmedRegion | null }
interface ElectionPollViewProps     { confirmedRegion: ConfirmedRegion | null }
interface ElectionDistrictViewProps { confirmedRegion: ConfirmedRegion | null; onRegionChange: (r: ConfirmedRegion) => void }
```

| 상황 | 동작 |
|------|------|
| 로그인 사용자 | 프로필 API에서 저장된 지역구 로드, 변경 시 서버에 저장 |
| 비로그인 사용자 | 세션 내 임시 유지, 저장 시 로그인 유도 배너 표시 |
| 목업 단계 | `{ regionCode: '11', regionName: '서울특별시' }` 하드코딩 기본값 사용 |

> **주의:** 목업 기본값은 시/도 단위(`서울특별시`)로 설정한다. `MOCK_POLL_DATA`의 키가 시/도 단위이므로, 구 단위 키(`서울특별시 종로구`)를 사용하면 조회 결과가 빈 값이 된다.

지도 탭에서 지역구를 확정하면 다른 탭에도 즉시 반영된다.

---

## 3. 공유 컴포넌트

아래 두 컴포넌트는 피드/여론조사/내 지역구 탭에서 공통으로 재사용된다.

### PartyRingSelector (정당 원형 로고 선택)
- 인스타그램 스토리 방식의 가로 스크롤 원형 로고 리스트
- 선택 시 해당 정당 컬러 링으로 강조
- `components/common/PartyLogoReplacement/`의 `PartyLogoReplacement` 컴포넌트를 각 링 아이템에 활용
- 구현: 가로 스크롤 `flex` row + 각 아이템에 `selected` 상태 시 정당 컬러 토큰 border ring 적용

### DistrictMapPicker (인터랙티브 지도 depth 탐색)

> **구현 참고:** 기존 `KoreaMap`은 권역 인덱스(regionIndex) 기반으로 동작하며, 구/군 단위 드릴다운을 지원하지 않는다. **목업 단계에서는** 기존 `ManualRegionPicker` (시/도 → 구/군 2단계 드롭다운)를 래핑해서 구현한다. 이후 기능 구현 단계에서 실제 인터랙티브 지도 드릴다운으로 교체한다.

**목업 단계 구현:**
```
[시/도 드롭다운] → [구/군 드롭다운]  (ManualRegionPicker 기반)
```

**기능 구현 단계 목표 UX:**
- Depth 1: 전국 지도 → 시/도 터치
- Depth 2: 시/도 내 구/군 터치

**공통 동작:**
- 선택 완료 후 선택된 지역 칩이 필터 바에 표시되며 지도/드롭다운은 접힘
- **지역별 필터**: 지역 확정 즉시 필터링 적용
- **후보자별 필터**: 지역 확정 후 후보자 목록 추가 선택

---

## 4. 피드 탭 (ElectionFeedView)

### 레이아웃
```
[전체] [정당별] [후보자별] [지역별]  ← 서브 뷰 전환 탭
────────────────────────────────────
[서브 필터 영역]  ← 선택한 뷰에 따라 달라짐
────────────────────────────────────
피드 카드 리스트 (무한 스크롤)
```

### 서브 뷰별 필터 UI

| 뷰 | 필터 UI | 동작 |
|----|---------|------|
| 전체 | 없음 | 모든 콘텐츠 타입 시간순 통합 |
| 정당별 | PartyRingSelector | 선택 정당 관련 콘텐츠만 표시 |
| 후보자별 | DistrictMapPicker → 후보자 목록 | 지역 선택 후 후보자 선택 |
| 지역별 | DistrictMapPicker | 선택 지역 관련 콘텐츠만 표시 |

### 피드 카드 3종

**SNS 카드**
```
[플랫폼 아이콘] [후보자명]  [시간]
본문 미리보기 (2줄 clamp)
[원본 보기 →]
```
- 플랫폼: 페이스북, X(트위터), 인스타그램, 유튜브
- 좌측 상단 뱃지: `SNS`

**여론조사 카드**
```
[여론조사 뱃지]  [조사기관]  [날짜]
정당명  ████████░░  48%  ▲2.1%p
정당명  ███████░░░  41%  ▼0.8%p
```
- 미니 바차트 (CSS width % 방식, 별도 라이브러리 불필요)
- 변동폭 표시 (▲▼)

**법안 카드**
```
[법안 뱃지]  [stage 칩]  [날짜]
brief_summary (bold)
bill_name (gray, small)
```
- 기존 `Bill` 컴포넌트는 `BillProps` 전체 필드가 필요하므로 **재사용하지 않는다**
- 대신 `BillMiniCard` 경량 컴포넌트를 신규 작성: `brief_summary`, `bill_name`, `bill_stage`, `propose_date`만 필요

### 로딩/에러/빈 상태

| 상태 | 표시 |
|------|------|
| 로딩 | 카드 스켈레톤 3개 (NextUI Skeleton 컴포넌트) |
| 빈 상태 | "아직 등록된 선거 피드가 없습니다." |
| 에러 | "피드를 불러오지 못했습니다. 다시 시도해주세요." |

### 목업 데이터
- SNS 카드 4개 (플랫폼별 1개씩)
- 여론조사 카드 3개
- 법안 카드 3개 (`mockFeedData.ts`에 `BillMiniCardProps` 형태로 정의)

---

## 5. 여론조사 탭 (ElectionPollView)

### 레이아웃
```
[선거 선택 칩]  제9회 지방선거 | 대통령선거 | ...
[전체] [정당별] [지역별] [후보자별]  ← 서브 뷰 전환 탭
────────────────────────────────────
[서브 뷰 콘텐츠]
```

### 전체 뷰 — 선거 판세 종합 조망

| 영역 | 차트 | 설명 |
|------|------|------|
| 정당 지지율 현황 | Chart.js Bar (가로) | 정당별 최신 지지율, 정당 컬러 토큰 적용 |
| 지역별 우세 정당 | KoreaMap (히트맵 모드) | 지역별 1위 정당 색상으로 채색 |
| 지지율 추이 | Chart.js Line | 최근 30일, 주요 정당 3~4개 다중 선 |
| 최신 조사 리스트 | 카드 리스트 | 날짜순, 조사기관 + 지지율 요약 |

### 정당별 뷰
```
PartyRingSelector
────────────────────────────────────
선택 정당 지지율 추이 (꺾은선)
지역별 지지율 분포 (가로 바차트)
```

### 지역별 뷰
```
DistrictMapPicker
────────────────────────────────────
선택 지역 조사 리스트
후보별 지지율 추이 차트
```

### 후보자별 뷰
```
DistrictMapPicker → 후보자 선택
────────────────────────────────────
선택 후보 지지율 추이
경쟁 후보와 나란히 비교 차트
```

### 조사 카드 상세
```
[조사기관]  [조사기간]  표본 N명  오차 ±N%p
정당명  ██████  48%
정당명  █████   41%
[펼치기 ▼]  → PollQuestion/PollOption 상세 결과
```

### 차트 라이브러리 정리

| 용도 | 라이브러리 | 이유 |
|------|-----------|------|
| 바차트, 꺾은선 | Chart.js (기존 설치됨) | 이미 `package.json`에 포함 |
| 지역 히트맵 | D3 + KoreaMap (기존) | 기존 선거 지도 컴포넌트 재활용 |
| 조사 카드 미니 바 | Tailwind CSS width % | 별도 라이브러리 불필요 |

### 로딩/에러/빈 상태

| 상태 | 표시 |
|------|------|
| 로딩 | 차트 영역 스켈레톤 (NextUI Skeleton) |
| 빈 상태 | "해당 지역/선거의 여론조사 결과가 없습니다." |
| 에러 | "여론조사 데이터를 불러오지 못했습니다." |

### 목업 데이터
- 기존 `MOCK_POLL_DATA` 활용 (17개 시/도, `c1Pct`/`c2Pct`/`otherPct` 구조)
- 전체 뷰 바차트는 c1=더불어민주당, c2=국민의힘, other=기타로 레이블 매핑
- 추이 차트용 30일치 시계열 모킹 데이터 추가 필요 (`mockPollTimeseriesData.ts`)
- 전체 뷰 다당 지지율 차트가 필요한 경우, 별도 `mockPartyPollData.ts`에 정당명 키 배열 구조로 정의

---

## 6. 내 지역구 탭 (ElectionDistrictView)

### 레이아웃
```
[지역구 헤더]
────────────────────────────────────
후보자 비교 섹션 (핵심)
────────────────────────────────────
내 지역구 여론조사
────────────────────────────────────
내 지역구 피드
```

### 지역구 헤더

**설정됨:**
```
📍 서울특별시 종로구  [변경]
```

**미설정 (비로그인):**
```
┌─────────────────────────────────┐
│ 내 지역구를 설정해보세요        │
│ [📍 자동 감지]  [🗺 직접 선택] │
│ 저장하려면 로그인이 필요합니다  │  ← 비로그인 배너
└─────────────────────────────────┘
```

**지역구 설정 플로우:**
```
자동 감지(GPS) → 지역구 제안 → RegionConfirmCard → 확정
       ↘ 실패 시 → DistrictMapPicker 수동 선택
```

> **구현 참고:** `usePostElectionRegionResolve`, `RegionConfirmCard`, `ManualRegionPicker`는 현재 `ElectionShell.tsx` 내부에 위치한다. `ElectionDistrictView`에서 재사용하려면 GPS resolve 로직을 **`useRegionResolver` 커스텀 훅으로 추출**한 뒤 가져다 쓴다. **목업 단계에서는** 훅 추출 없이 `ElectionMapShell`에서 내려오는 `confirmedRegion` props를 사용하고, GPS/수동 설정 UI는 `confirmedRegion === null`일 때만 표시한다.

### 후보자 비교 섹션

**후보자 카드 슬라이드 (좌우 스크롤):**
```
◀  [후보자 사진]  [후보자 사진]  [후보자 사진]  ▶
   홍길동           이순신           강감찬
   더불어민주당      국민의힘         조국혁신당
   "함께 만드는..."  "강한 종로..."   "새로운 시작..."
   지지율 48%        지지율 41%       지지율 7%
```

**후보자 나란히 비교 테이블 (2명 선택 후):**

| 항목 | 후보 A | 후보 B |
|------|--------|--------|
| 정당 | 더불어민주당 | 국민의힘 |
| 최신 지지율 | 48% | 41% |
| 주요 공약 | ... | ... |
| 전직 경력 | ... | ... |

### 하단 섹션 컴포넌트 재사용

| 섹션 | 재사용 컴포넌트 | 필수 props |
|------|--------------|-----------|
| 내 지역구 여론조사 | `PollRegionPanel` (ElectionPollView에서 추출) | `region: string` |
| 내 지역구 피드 | `FeedRegionPanel` (ElectionFeedView에서 추출) | `region: string` |

`ElectionPollView`와 `ElectionFeedView`는 지역별 뷰 섹션을 **독립적으로 export 가능한 서브컴포넌트**로 구현해야 한다. 인라인으로 작성하면 `ElectionDistrictView`에서 재사용할 수 없다.

### 빈 상태
> "지역구를 설정하면 해당 지역의 선거 정보를 확인할 수 있습니다."

---

## 7. 구현 범위 및 순서

### 1단계: 목업 구현 (이번 작업)
- 하드코딩된 모킹 데이터로 3개 탭 UI 구현
- 공유 컴포넌트 (`PartyRingSelector`, `DistrictMapPicker`) 우선 개발
- 인터랙션 동작 (탭 전환, 필터 선택, 지도 depth 탐색) 구현

### 2단계: 기능 구현 (추후)
- 피드 API 연결 (SNS 크롤러는 별도 프로젝트)
- 여론조사 DB 연결 (`PollCatalog`, `PollSurvey`, `PollQuestion`, `PollOption`)
- 내 지역구 계정 기반 저장 API 연결

---

## 8. 파일 구조 (예상)

```
services/web/app/election/
├── components/
│   ├── ElectionFeedView.tsx          (신규)
│   ├── ElectionPollView.tsx          (신규)
│   ├── ElectionDistrictView.tsx      (신규)
│   ├── PollRegionPanel.tsx           (신규, ElectionDistrictView에서 재사용)
│   ├── FeedRegionPanel.tsx           (신규, ElectionDistrictView에서 재사용)
│   ├── BillMiniCard.tsx              (신규, 피드 탭 법안 카드)
│   ├── shared/
│   │   ├── PartyRingSelector.tsx     (신규, 공유)
│   │   └── DistrictMapPicker.tsx     (신규, 공유)
│   └── index.ts                      (업데이트: 아래 export 추가)
└── data/
    ├── mockPollData.ts               (기존, 활용)
    ├── mockPollTimeseriesData.ts     (신규, 추이 차트용 30일 시계열)
    ├── mockPartyPollData.ts          (신규, 다당 지지율 차트용)
    ├── mockFeedData.ts               (신규)
    └── mockDistrictData.ts           (신규)
```

### index.ts 추가 export 목록
```ts
export { default as ElectionFeedView } from './ElectionFeedView';
export { default as ElectionPollView } from './ElectionPollView';
export { default as ElectionDistrictView } from './ElectionDistrictView';
export { default as PollRegionPanel } from './PollRegionPanel';
export { default as FeedRegionPanel } from './FeedRegionPanel';
export { default as BillMiniCard } from './BillMiniCard';
export { default as PartyRingSelector } from './shared/PartyRingSelector';
export { default as DistrictMapPicker } from './shared/DistrictMapPicker';
```

### 다크 모드
모든 신규 컴포넌트에 `dark:` prefix Tailwind 토큰을 기존 컴포넌트 패턴에 맞게 적용한다.
- 배경: `dark:bg-dark-b`, `dark:bg-dark-pb`
- 보더: `dark:border-dark-l`
- 텍스트: `dark:text-white`, `dark:text-gray-2`
