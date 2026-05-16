---
name: "모두의입법"
description: "복잡한 국회 법안과 정치 정보를 시민의 언어로 읽고 추적하는 제품 UI"
colors:
  surface-white: "#FFFFFF"
  surface-soft: "#F5F7FD"
  surface-muted: "#F7F7F9"
  border-soft: "#EBEBEB"
  border-default: "#E0E0E0"
  text-muted: "#999999"
  text-secondary: "#555555"
  text-strong: "#262626"
  primary-ink: "#191919"
  primary-soft-blue: "#96BCFA"
  alert-red: "#E63946"
  info-lime: "#D7F963"
  dark-bg: "#101012"
  dark-panel: "#1E1E1E"
  dark-line: "#2E2E2E"
  nav-active-blue: "#0088FF"
  rainbow-yellow: "#FBEB59"
  rainbow-magenta: "#FC56D8"
  rainbow-cyan: "#10D9EF"
  rainbow-green: "#6CF880"
  party-minjoo: "#152484"
  party-ppp: "#E61E2B"
  party-jk: "#0073CF"
  party-reform: "#FF7210"
  party-jinbo: "#D6001C"
  party-future: "#45BABD"
  party-basic: "#00D2C3"
  party-sdp: "#F58400"
  party-green: "#007C36"
  party-independent: "#797C85"
typography:
  display:
    fontFamily: "Pretendard Variable, Pretendard, -apple-system, BlinkMacSystemFont, system-ui, Roboto, Helvetica Neue, Segoe UI, Apple SD Gothic Neo, Noto Sans KR, Malgun Gothic, sans-serif"
    fontSize: "45px"
    fontWeight: 200
    lineHeight: 1.1
    letterSpacing: "0"
  headline:
    fontFamily: "Pretendard Variable, Pretendard, -apple-system, BlinkMacSystemFont, system-ui, Roboto, Helvetica Neue, Segoe UI, Apple SD Gothic Neo, Noto Sans KR, Malgun Gothic, sans-serif"
    fontSize: "26px"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "0"
  title:
    fontFamily: "Pretendard Variable, Pretendard, -apple-system, BlinkMacSystemFont, system-ui, Roboto, Helvetica Neue, Segoe UI, Apple SD Gothic Neo, Noto Sans KR, Malgun Gothic, sans-serif"
    fontSize: "20px"
    fontWeight: 600
    lineHeight: 1.35
    letterSpacing: "0"
  body:
    fontFamily: "Pretendard Variable, Pretendard, -apple-system, BlinkMacSystemFont, system-ui, Roboto, Helvetica Neue, Segoe UI, Apple SD Gothic Neo, Noto Sans KR, Malgun Gothic, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.55
    letterSpacing: "0"
  body-small:
    fontFamily: "Pretendard Variable, Pretendard, -apple-system, BlinkMacSystemFont, system-ui, Roboto, Helvetica Neue, Segoe UI, Apple SD Gothic Neo, Noto Sans KR, Malgun Gothic, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "0"
  label:
    fontFamily: "Pretendard Variable, Pretendard, -apple-system, BlinkMacSystemFont, system-ui, Roboto, Helvetica Neue, Segoe UI, Apple SD Gothic Neo, Noto Sans KR, Malgun Gothic, sans-serif"
    fontSize: "12px"
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: "0.01em"
rounded:
  none: "0px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "24px"
  full: "9999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "20px"
  xl: "24px"
  xxl: "40px"
  touch: "56px"
components:
  button-primary:
    backgroundColor: "{colors.primary-ink}"
    textColor: "{colors.surface-white}"
    typography: "{typography.body-small}"
    rounded: "{rounded.full}"
    padding: "16px 32px"
    height: "56px"
  button-secondary:
    backgroundColor: "{colors.border-default}"
    textColor: "{colors.text-secondary}"
    typography: "{typography.body-small}"
    rounded: "{rounded.sm}"
    padding: "8px 16px"
    height: "32px"
  chip-stage:
    backgroundColor: "{colors.surface-white}"
    textColor: "{colors.text-muted}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "3px 8px"
  card-bill:
    backgroundColor: "{colors.surface-white}"
    textColor: "{colors.primary-ink}"
    rounded: "{rounded.none}"
    padding: "24px 20px"
  search-field:
    backgroundColor: "{colors.surface-white}"
    textColor: "{colors.primary-ink}"
    typography: "{typography.body}"
    rounded: "{rounded.lg}"
    padding: "0 16px"
    height: "40px"
---

# Design System: 모두의입법

## 1. Overview

**Creative North Star: "시민의 해설 지도"**

모두의입법의 시각 시스템은 복잡한 입법·정치 정보를 시민이 바로 읽을 수 있는 지도처럼 펼쳐야 한다. 첫 화면은 단순하고 차분해야 하지만, 사용자가 더 들어가면 법안, 의원, 정당, 선거, 타임라인, 출처를 정확히 추적할 수 있어야 한다. 이 제품은 `PRODUCT.md`의 원칙처럼 "쉽게 시작하고, 깊이는 점진적으로 드러낸다."

미학은 과시보다 신뢰에 가깝다. 기본 화면은 흰색과 옅은 회색, `#191919` 잉크, 명확한 Pretendard 계층으로 구성한다. 레인보우 시그니처와 정당 색상은 장식이 아니라 분류, 탐색, 정체성 표시를 위해 제한적으로 사용한다. 모바일 플로팅 내비게이션처럼 특별한 조작부만 유리 질감과 회전 그라디언트를 허용한다.

이 시스템은 관공서 포털, 정치적으로 편향된 커뮤니티, 과하게 SaaS 같은 대시보드를 거부한다. 정보가 빽빽해질 수는 있지만 관료적으로 보여서는 안 되고, 정치색을 표시할 수는 있지만 특정 입장을 미는 듯 보여서는 안 된다.

**Key Characteristics:**
- 단일 한국어 산세리프 중심의 명확한 정보 위계
- 평평한 카드, 얇은 경계선, 절제된 그림자
- 정당 색상은 데이터 표식으로만 사용
- 레인보우 시그니처는 브랜드와 검색 진입점에만 제한적으로 사용
- 모바일은 플로팅 내비게이션과 터치 친화적 높이를 우선

## 2. Colors

팔레트는 무채색 정보 표면 위에 시민적 신뢰를 주는 검은 잉크, 부드러운 파란 보조색, 그리고 정치 정보를 구분하는 정당 색상으로 구성한다.

### Primary
- **Civic Ink**: 기본 텍스트, 주요 CTA, 선택 상태의 기준색이다. 순수 검정 대신 `primary-ink`를 사용해 딱딱한 대비를 줄인다.
- **Soft Assembly Blue**: 선거 D-day, 보조 강조, 정보성 상태에 쓰는 차분한 파란 계열이다. 화면 전체를 지배하지 않는다.
- **Mobile Active Blue**: 모바일 플로팅 내비게이션의 활성 아이콘과 검색 상태에서만 사용하는 선명한 액션 색이다.

### Secondary
- **Rainbow Signature Set**: 노랑, 마젠타, 시안, 그린으로 구성된 브랜드 시그니처다. 피드 탭 인디케이터, 검색 버튼, 브랜딩 표식처럼 사용자가 "탐색을 시작하는 곳"에서만 쓴다.
- **Info Lime**: 특별한 정보성 표식에만 사용한다. 법안·정치 정보의 기본 강조색으로 남발하지 않는다.

### Tertiary
- **Party Spectrum**: 정당 색상은 후보, 정당, 발의자, 여론조사, 타임라인 표식에 사용한다. 색은 정보의 출처와 소속을 보여주는 데이터 레이어이며 감정적 강조가 아니다. 구현의 source of truth는 `services/web/constants/party/party.ts`의 `PARTY_COLOR`와 `getPartyColor()`다.
- **Alert Red**: 오류, 경고, AI 요약 주의 문구, 선거 임박 상태처럼 사용자의 주의가 필요한 순간에만 사용한다.

### Neutral
- **Paper White**: 기본 앱 표면이다. 정보가 많아도 숨 쉴 수 있게 카드와 본문 배경을 밝게 유지한다.
- **Soft Civic Wash**: 보조 배경, 팔로잉·마이페이지 패널, 브랜딩 섹션의 낮은 대비 표면이다.
- **Quiet Dividers**: `border-soft`와 `border-default`는 카드와 섹션을 나누되 레이아웃을 강하게 가두지 않는다.
- **Muted Text Ladder**: `text-muted`, `text-secondary`, `text-strong`, `primary-ink` 순서로 정보의 중요도를 만든다.
- **Dark Reading Layer**: 다크 모드에서는 `dark-bg`, `dark-panel`, `dark-line`을 사용해 본문과 패널을 분리한다.

### Named Rules

**The Neutral First Rule.** 화면의 80% 이상은 무채색 정보 표면이어야 한다. 정치색과 레인보우는 정보 구조가 요구할 때만 등장한다.

**The Party Color Is Data Rule.** 정당 색상은 소속, 비교, 지도, 차트, 타임라인 표식에만 사용한다. CTA, 배경 장식, 감정적 강조에 사용하지 않는다. 새 구현은 `PARTY_COLOR`를 직접 참조하거나 `getPartyColor()`를 통해 색을 가져온다.

**The Rainbow Entry Rule.** 레인보우는 브랜드 서명과 검색·탐색 진입점에만 사용한다. 본문 카드 안의 텍스트 강조나 정치 정보 강조에 쓰지 않는다.

## 3. Typography

**Display Font:** Pretendard Variable, Pretendard, system sans fallback
**Body Font:** Pretendard Variable, Pretendard, system sans fallback
**Label/Mono Font:** 기본은 Pretendard, 코드성 메타 정보는 ui-monospace 보조 사용 가능

**Character:** 하나의 한국어 산세리프가 제품 전체를 끌고 간다. 타이포그래피는 화려한 브랜드 표현보다 "정확히 읽히는 시민 정보"에 우선순위를 둔다.

### Hierarchy

- **Display** (200, 45px, 1.1): 오류 화면, 특수 상태, 큰 D-day 숫자처럼 예외적 장면에만 사용한다.
- **Headline** (700, 26px, 1.2): 피드 제목, 타임라인 단계, 법안 상세 제목, 선거 헤더에 사용한다.
- **Title** (600, 20px, 1.35): 법안 카드의 핵심 요약, 섹션 제목, 팔로잉·마이페이지 묶음 제목에 사용한다.
- **Body** (400, 16px, 1.55): 법안 요약, 본문 설명, 검색 결과의 기본 읽기 텍스트에 사용한다. 긴 설명은 65-75ch를 넘기지 않는다.
- **Body Small** (400, 14px, 1.5): 보조 설명, 카드 메타, 목록 설명, 비어 있는 상태 안내에 사용한다.
- **Label** (600, 12px, 0.01em): 칩, 날짜, 정당명, 단계명, 작은 액션 라벨에 사용한다.

### Named Rules

**The One Family Rule.** 제품 UI에서는 Pretendard 계열 하나로 충분하다. 법안과 선거 정보의 신뢰성을 해치는 장식 서체를 추가하지 않는다.

**The Korean Readability Rule.** 한국어 본문에는 음수 자간을 쓰지 않는다. 짧은 라벨에만 최대 `0.01em` 수준의 자간을 허용한다.

## 4. Elevation

기본 철학은 flat by default다. 법안 카드와 피드 표면은 대부분 그림자 없이 경계선, 여백, 타이포그래피로 층위를 만든다. 그림자는 모바일 플로팅 내비게이션, 스낵바, 툴팁, 타임라인의 작은 정당 표식처럼 떠 있는 조작부와 피드백성 요소에만 사용한다.

### Shadow Vocabulary

- **Card Rest** (`shadow: none`): 법안 피드 카드, 상세 카드, 기본 정보 컨테이너에 사용한다.
- **Subtle Surface** (`0 1px 3px rgba(0, 0, 0, 0.10)`): 검색 입력, 작은 버튼, 가벼운 입력 표면에 사용한다.
- **Floating Glass** (`0 4px 32px rgba(0, 0, 0, 0.12), 0 1px 8px rgba(0, 0, 0, 0.06)`): 모바일 플로팅 내비게이션에만 사용한다.
- **Feedback Toast** (`0 10px 15px -3px rgba(0, 0, 0, 0.10)`): 스낵바와 일시적 피드백에 사용한다.

### Named Rules

**The Flat Trust Rule.** 정보 카드는 기본적으로 뜨지 않는다. 카드가 떠 보이면 정보보다 장식이 먼저 보이는지 검사한다.

**The Floating Control Exception.** 유리 질감, 블러, 깊은 그림자는 모바일 플로팅 내비게이션과 일시적 피드백 레이어에서만 허용한다.

## 5. Components

### Buttons

- **Shape:** 주요 CTA는 완전한 pill 형태(`9999px`)를 사용한다. 오류 화면의 큰 선택 버튼처럼 엄격한 액션 쌍은 각진 형태(`0px`)도 허용한다.
- **Primary:** `primary-ink` 배경과 흰색 텍스트를 사용한다. 법안 원문 확인, 로그인, 핵심 이동처럼 사용자의 다음 행동이 명확할 때만 쓴다.
- **Hover / Focus:** 색보다 명확한 focus ring과 약한 배경 변화로 상태를 표현한다. 장식적 확대나 튀는 모션은 금지한다.
- **Secondary / Ghost:** 보조 액션은 `border-default`, `text-secondary`, 투명 배경을 기본으로 한다. 아이콘 버튼은 배경을 비워 정보 표면을 방해하지 않는다.

### Chips

- **Style:** 법안 단계 칩은 투명 배경, 얇은 회색 경계선, `text-muted` 라벨을 사용한다.
- **State:** 선택형 탭은 검은 cursor와 흰 텍스트로만 선택을 표시한다. 정당명 칩은 정당색 자체보다 데이터와 함께 노출될 때만 사용한다.

### Cards / Containers

- **Corner Style:** 법안 피드 카드는 각진 형태(`0px`)를 유지한다. 선거 후보 카드, 마이페이지 묶음, 패널형 컨테이너는 `8px-16px` 범위에서만 둥글린다.
- **Background:** 기본은 흰색, 다크 모드는 `dark-bg`와 `dark-panel`을 구분해서 쓴다.
- **Shadow Strategy:** 정보 카드는 `shadow: none`이 기본이다. 선택 후보 카드처럼 상호작용이 필요한 경우에만 ring이나 얇은 경계선 변화를 쓴다.
- **Border:** 정당 관련 카드의 색 경계선은 데이터 표식이다. 한쪽 stripe처럼 꾸미지 말고 전체 경계나 작은 dot, avatar ring으로 처리한다.
- **Internal Padding:** 주요 카드 안쪽 여백은 `20px-24px`를 기본으로 한다. 데이터 밀도가 높은 패널은 `16px`까지 줄일 수 있다.

### Inputs / Fields

- **Style:** 검색 입력은 `40px` 높이, `16px` radius, 흰색 표면, 약한 그림자를 기본으로 한다.
- **Focus:** focus 상태는 배경을 살짝 올리고 입력 가능성이 보이게 한다. 색이 강한 outline은 검색 확장 UI처럼 특별한 진입점에만 사용한다.
- **Error / Disabled:** 오류는 `alert-red`, 비활성은 `text-muted`와 낮은 대비 배경을 사용한다. 에러 문구는 짧고 행동 가능해야 한다.

### Navigation

- **Desktop:** 상단 내비게이션은 `98px` 높이, 중앙 탭, 활성 탭 뒤의 시그니처 border 아이콘으로 구성한다. 기본 라벨은 `text-muted`, 활성 라벨은 `primary-ink`와 semibold다.
- **Mobile:** 하단 플로팅 내비게이션은 glass shell, pill indicator, 검색 전용 레인보우 버튼을 사용한다. 터치 높이는 기본 `62px`, compact는 `43px` 안팎을 유지한다.
- **Tabs:** 피드와 선거 탭은 NextUI Tabs를 기반으로 하되, 선택 상태는 검은 cursor 또는 밑줄로 명확히 표시한다.

### Signature Component: Bill Feed Card

법안 카드는 제품의 기본 독해 단위다. 한 문장 요약을 먼저 두고, 원제목, 처리 단계, 발의 시점, AI 요약, 스크랩·조회·공유 액션을 차례로 배치한다. 전문적 정보가 많아도 첫 시선은 "이 법안이 무엇인가"에 고정되어야 한다.

### Signature Component: Mobile Search Entry

모바일 검색 버튼은 모두의입법에서 가장 표현적인 컴포넌트다. 레인보우 conic gradient, glass inner, 추천 질문 bubble을 허용하지만 검색이라는 명확한 행동을 벗어나면 같은 효과를 재사용하지 않는다.

## 6. Do's and Don'ts

### Do:

- **Do** `PRODUCT.md`의 "Easy to learn, Hard to master" 원칙을 화면 계층에 반영한다. 첫 줄은 쉽게, 상세는 깊게 만든다.
- **Do** 법안 요약, 원문 링크, 처리 단계, 날짜, 출처, AI 주의 문구를 신뢰 정보로 다룬다.
- **Do** 정당 색상을 전체 경계선, avatar ring, 차트 bar, dot처럼 데이터 표식으로 사용한다.
- **Do** 모바일 조작부는 `56px` 안팎의 터치 크기를 지키고, 검색 입력은 iOS 확대를 피하기 위해 `16px` 이상으로 유지한다.
- **Do** 다크 모드에서도 본문, 경계선, 카드 층위가 유지되도록 `dark-bg`, `dark-panel`, `dark-line`을 구분한다.

### Don't:

- **Don't** 관공서 포털처럼 보이게 만들지 않는다. 과도한 표, 딱딱한 안내문, 절차명만 나열하는 화면은 금지한다.
- **Don't** 정치적으로 편향된 커뮤니티처럼 보이게 만들지 않는다. 특정 정당 색을 CTA나 화면 배경의 주색으로 쓰지 않는다.
- **Don't** 과하게 SaaS 같은 대시보드로 만들지 않는다. 의미 없는 metric card, marketing hero, 장식용 gradient text를 금지한다.
- **Don't** 레인보우 시그니처를 본문 강조나 법안 중요도 표시에 쓰지 않는다. 검색과 브랜드 진입점 밖에서는 드물어야 한다.
- **Don't** 정보 카드에 두꺼운 side-stripe border를 쓰지 않는다. 정당색이 필요하면 전체 border, dot, avatar ring, chart bar로 표현한다.
- **Don't** 모달을 첫 선택으로 쓰지 않는다. 검색, 필터, 상세 확장은 가능하면 inline 또는 progressive disclosure로 처리한다.
