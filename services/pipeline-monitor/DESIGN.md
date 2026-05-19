# Pipeline Monitor Design System

이 문서는 `services/pipeline-monitor` 구현 에이전트를 위한 디자인 시스템 기준서다. 사람용 시각 문서는 같은 폴더의 `DESIGN.html`을 사용한다.

## 방향 전환

Pipeline Monitor는 별도의 운영 SaaS처럼 보이면 안 된다. 기존 모두의입법 웹의 디자인 문법을 유지하면서 기능만 데이터 파이프라인 모니터링으로 바뀌어야 한다.

즉, 새 서비스는 다음처럼 보여야 한다.

- 모두의입법의 하위 운영 화면처럼 느껴진다.
- 레인보우 그라디언트 라인, Pretendard 기반 한글 타이포그래피, rounded-full 탭과 버튼, 흰색 카드 표면, 모바일 floating nav 감각을 이어받는다.
- 데이터 모니터링 기능은 표와 로그 중심이지만, 시각 언어는 기존 피드/타임라인/선거 탭의 문법과 연결된다.
- 운영 도구라고 해서 무채색 어드민 콘솔로 분리하지 않는다.

## 기존 모두의입법 디자인 소스

디자인 기준은 아래 기존 웹 파일에서 가져온다.

| Source | 가져올 문법 |
| --- | --- |
| `services/web/tailwind.config.js` | `primary`, `gray`, `theme`, `dark`, `party` 색상 토큰 |
| `services/web/styles/globals.css` | Pretendard 폰트, feed tab rainbow indicator, status snackbar 색 |
| `services/web/styles/mobile-floating-nav.css` | 모바일 floating nav의 glass surface, rounded-full, indicator motion |
| `services/web/public/images/logo.svg` | 레인보우 underline gradient |
| `services/web/components/Feed/FeedTab/FeedTab.tsx` | NextUI `Tabs`, rounded-full cursor, `bg-primary-3` active state |
| `services/web/components/Bill/BillList/Bill/Bill.tsx` | white card, `radius="none"`, `shadow="none"`, gray secondary button |
| `services/web/app/election/components/SeatSummaryCard.tsx` | rounded-xl, white surface, border-gray-1, small uppercase labels |

## 브랜드 토큰

### Font

기존 웹은 전역에서 Pretendard를 우선하고, 코드 계열은 `Fira Code`와 시스템 monospace를 사용한다.

```css
--font-sans: 'Pretendard Variable', Pretendard, -apple-system, BlinkMacSystemFont, system-ui, 'Noto Sans KR', sans-serif;
--font-mono: 'Fira Code', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
```

구현 규칙:

- 한글 UI 본문은 Pretendard 기준으로 잡는다.
- 실행 ID, 파일 경로, JSON key, CLI 명령은 mono로 표시한다.
- 화면 내 letter spacing은 기본적으로 0이다.
- 기존 웹처럼 작은 uppercase 라벨에는 제한적으로 tracking을 사용할 수 있다.

### Core Color

기존 Tailwind 토큰을 그대로 옮긴다.

| Token | Value | Usage |
| --- | --- | --- |
| `gray-0.5` | `#EBEBEB` | 연한 배경, inactive surface |
| `gray-1` | `#E0E0E0` | border, secondary button |
| `gray-2` | `#999999` | 보조 텍스트 |
| `gray-3` | `#555555` | 중간 텍스트 |
| `gray-4` | `#262626` | 강한 텍스트 |
| `primary-1` | `#F5F7FD` | 부드러운 배경 |
| `primary-2` | `#96BCFA` | 정보 강조, 실행 중 |
| `primary-3` | `#191919` | primary button, active tab, 핵심 텍스트 |
| `theme-alert` | `#E63946` | 실패, 위험 |
| `theme-info` | `#D7F963` | 신규/정보성 강조 |
| `dark-b` | `#101012` | dark page background |
| `dark-l` | `#2E2E2E` | dark border |
| `dark-pb` | `#1E1E1E` | dark panel background |

### Rainbow Gradient

모두의입법 로고와 피드 탭 인디케이터의 핵심 문법이다.

```css
--rainbow: linear-gradient(90deg, #FBEB59 0%, #FC56D8 31%, #10D9EF 65%, #6CF880 100%);
--rainbow-soft: linear-gradient(
  90deg,
  rgba(251, 235, 89, 0.15) 0%,
  rgba(252, 86, 216, 0.15) 31%,
  rgba(16, 217, 239, 0.15) 65%,
  rgba(108, 248, 128, 0.15) 100%
);
```

사용 규칙:

- 레인보우는 underline, active tab border, thin divider, 핵심 상태 accent에 사용한다.
- 큰 배경 전체를 레인보우로 채우지 않는다.
- 운영 상태 색상을 레인보우 하나로 대체하지 않는다. 상태 색은 별도로 둔다.
- 레인보우는 "모두의입법 브랜드 연결"을 만드는 신호다.

### Status Color

운영 상태는 기존 웹의 snackbar/status 문법과 브랜드 토큰을 조합한다.

| Status | Label | Color | Note |
| --- | --- | --- | --- |
| `success` | 성공 | `#16A34A` | 기존 `.SUCCESS` 계열 |
| `failed` | 실패 | `#E63946` | `theme-alert` |
| `running` | 실행 중 | `#96BCFA` | `primary-2` |
| `warning` | 경고 | `#FBEB59` | rainbow yellow |
| `fallback` | fallback | `#FC56D8` | rainbow magenta |
| `unknown` | 알 수 없음 | `#999999` | `gray-2` |

색상만으로 상태를 전달하지 않는다. 항상 한글 라벨을 함께 표시한다.

## 화면 구조

### Product Mapping

기존 모두의입법 화면 문법을 데이터 모니터링 기능으로 치환한다.

| 모두의입법 문법 | Pipeline Monitor 치환 |
| --- | --- |
| `피드` | 최근 파이프라인 실행 피드 |
| `시간순 / HOT` 탭 | `최근순 / 실패 우선` 탭 |
| `리포트 / 법안 / 팔로잉` content tab | `실행 / 산출물 / 알림` content tab |
| `타임라인` | run step timeline |
| `선거 D-day header` | scheduler / next run countdown |
| `법안 카드` | run card |
| `정당 ring / colored bar` | provider / command accent |
| `원문 확인하기` primary button | 산출물 확인하기 |

### Navigation

독립 운영 서비스이지만 모두의입법의 모바일 floating nav 문법을 유지한다.

권장 nav item:

- `피드`: 최근 실행 피드
- `타임라인`: 단계별 실행 이력
- `산출물`: JSON/Markdown artifact
- `설정`: 런타임 설정 확인

모바일:

- 기존 `mobile-floating-nav`와 같은 bottom floating shell을 사용한다.
- active indicator는 glass pill 또는 rainbow outline pill을 사용한다.
- 검색 대신 command/run id 검색을 연결할 수 있다.

데스크톱:

- 모두의입법 웹의 모바일 우선 정체성을 유지하되, 운영 화면에서는 좌측 narrow rail 또는 상단 pill nav를 사용할 수 있다.
- 데스크톱에서도 floating nav를 억지로 크게 늘리지 않는다.

## Typography

| Role | Class 느낌 | Guideline |
| --- | --- | --- |
| Page title | `text-[26px] font-bold` | 모바일 기본 화면 제목 |
| Desktop title | `md:text-[48px] md:font-bold` | 타임라인형 큰 제목에만 사용 |
| Section title | `text-2xl font-semibold` | 상세 섹션 제목 |
| Card title | `text-xl font-semibold` | run card 핵심 요약 |
| Body | `text-sm md:text-base` | 로그 전 설명, 카드 본문 |
| Caption | `text-xs font-semibold text-gray-2` | 상태/시간/보조 정보 |
| Metric | `text-2xl font-semibold tabular-nums` | 처리 건수, 소요 시간 |
| D-day style metric | `text-4xl font-black` | 다음 스케줄 countdown 등 제한적 사용 |

## Surface

기존 모두의입법은 화면별로 다음 표면을 섞어 사용한다.

- 법안 카드: 흰색, shadow none, radius none에 가까운 평평한 카드
- 선거 카드: 흰색, `rounded-xl`, `border-gray-1`, shadow none
- 모바일 nav: 반투명 흰색, 강한 blur, rounded-full, 미세한 inset shadow
- 탭 indicator: rainbow outline + soft rainbow fill

Pipeline Monitor 적용:

- run feed card는 기존 법안 카드처럼 흰색/평면/텍스트 중심으로 만든다.
- dashboard summary는 선거 요약 카드처럼 rounded-xl과 border를 사용한다.
- active filter와 content tab은 feed tab의 rainbow pill indicator를 따른다.
- 로그/JSON 블록은 어두운 코드 표면을 쓰되, 주변 UI는 모두의입법의 밝은 표면을 유지한다.

## Component Rules

### BrandHeader

목적: 운영 서비스가 모두의입법 계열임을 첫 화면에서 명확히 보여준다.

구성:

- `모두의입법` wordmark 또는 text logo
- 아래 2px rainbow underline
- `Pipeline Monitor` subtitle
- 마지막 갱신 시각

규칙:

- headline은 과도하게 마케팅 문구화하지 않는다.
- 레인보우는 underline으로 사용한다.

### ContentTypeTabs

기존 `Feed`의 `리포트 / 법안 / 팔로잉` 탭을 계승한다.

권장 탭:

- `실행`
- `산출물`
- `알림`

스타일:

- 전체 탭 wrapper는 `relative flex items-center gap-[5px]`
- active indicator는 `feed-tab-indicator` 방식
- tab width는 85px에서 시작하되 한글 길이에 따라 92px까지 허용
- active text는 `#191919`, inactive text는 `rgba(25, 25, 25, 0.4)`

### SortTabs

기존 `시간순 / HOT` 탭을 계승한다.

권장 탭:

- `최근순`
- `실패 우선`

스타일:

- NextUI Tabs `variant="light"` 또는 동일한 DOM/CSS
- active cursor: `rounded-full bg-primary-3 dark:bg-gray-0.5`
- active text: white
- height: 36px

### RunFeedCard

기존 법안 카드의 정보 구조를 모니터링 run에 맞게 바꾼다.

구성:

- 상단 caption: relative time 또는 started_at
- 제목: run summary. 예: `최신 법안 5건 요약 성공`
- 보조 제목: command/run_id
- 본문: 처리 건수, provider, fallback 여부, 오류 요약
- footer: 처리 시간, artifact count, `자세히 보기`

스타일:

- `bg-white`
- `dark:bg-dark-b dark:lg:bg-dark-pb`
- `shadow-none`
- feed에서는 radius를 크게 주지 않는다.
- proposer card처럼 오른쪽 또는 하단에 provider/command accent panel을 붙일 수 있다.

### StatusChip

상태 표시용 chip이다.

스타일:

- `text-xs`
- `border-1`
- radius는 `sm` 또는 `full`
- failed/fallback/running은 색상 border와 light fill을 함께 사용

규칙:

- 색상 점만 쓰지 않는다.
- `성공`, `실패`, `실행 중`, `경고`, `fallback`, `알 수 없음` 라벨을 유지한다.

### TimelineBoard

기존 `TimelineBoard`의 큰 제목, D-day, 세 가지 수치 요약 문법을 사용한다.

모니터링 치환:

- 제목: `파이프라인 타임라인`
- 보조: `최근 24시간`
- D-day 영역: `다음 실행까지 04:21` 또는 `지연 +12분`
- 요약 지표: `성공`, `실패`, `fallback`

### StepTimeline

run detail의 단계별 타임라인이다.

스타일:

- 기존 timeline list처럼 세로 라인과 원형 marker를 사용한다.
- marker에는 status color를 적용한다.
- 단계 제목은 `text-sm font-bold`, 결과 요약은 `text-xs font-semibold text-gray-2`.

### ArtifactCard

산출물 파일을 보여주는 카드다.

구성:

- 파일명
- 형식: JSON/MD/log
- 생성 시각
- 파일 크기
- 관련 run id
- `산출물 확인하기` primary full pill button

스타일:

- primary button은 기존 `원문 확인하기`처럼 `h-[56px]`, `rounded-full`, `bg-primary-3`, `text-white`.
- 보조 버튼은 `bg-gray-1 text-gray-3`.

### JsonBlock

로그/JSON은 운영 화면에 꼭 필요하지만 브랜드 표면과 충돌하지 않게 제한적으로 사용한다.

스타일:

- `background: #101012`
- text: `#EBEBEB`
- radius: 12px 이하
- 내부는 mono
- 주변에는 rainbow top border 또는 small label을 붙여 브랜드 연결을 만든다.

## Motion

기존 웹의 motion을 계승한다.

| Motion | Source | Usage |
| --- | --- | --- |
| `fade-in 0.35s ease-out` | Tailwind keyframes | 새 run feed 등장 |
| `fade-up 0.35s ease-out` | Tailwind keyframes | summary card 등장 |
| `slide-in-left/right 0.3s` | Tailwind keyframes | timeline 전환 |
| `bar-grow 0.4s` | Tailwind keyframes | 처리량 bar |
| tab indicator spring | `feed-tab-indicator` | content tab active 이동 |

motion은 상태 이해를 보조해야 한다. 로그가 계속 움직이거나 수치가 과하게 튀는 애니메이션은 쓰지 않는다.

## Responsive

기존 웹은 모바일 우선이다. Pipeline Monitor도 모바일에서 먼저 완성되어야 한다.

| Width | Behavior |
| --- | --- |
| `< 768px` | feed-first 단일 열, bottom floating nav, summary는 세로 스택 |
| `768px - 1023px` | 카드와 표를 혼합, table은 horizontal scroll 허용 |
| `>= 1024px` | 본문 최대폭을 유지하고 detail 화면만 2열 허용 |

표는 모바일에서 완전히 카드로 바꾸지 않는다. 비교가 필요한 run history는 가로 스크롤 표를 허용한다.

## Data Monitoring Constraints

브랜드 문법을 유지하더라도 기능 제약은 유지한다.

- MVP는 read-only다.
- 파이프라인 실행/재시도/삭제 버튼은 넣지 않는다.
- 실제 데이터 없는 차트는 만들지 않는다.
- run feed, timeline, artifact, JSON log가 우선이다.
- 장애 상태는 감성 문구가 아니라 원인과 경로를 보여준다.

## Implementation Checklist

- [ ] `services/web/tailwind.config.js`의 색상 토큰을 새 앱에 복제하거나 공유한다.
- [ ] Pretendard CDN 또는 같은 font stack을 적용한다.
- [ ] `#191919` primary button과 rounded-full CTA를 사용한다.
- [ ] logo/feed tab의 rainbow gradient를 active tab, underline, divider에 적용한다.
- [ ] 기존 `FeedTab`의 `시간순 / HOT` 문법을 `최근순 / 실패 우선`으로 치환한다.
- [ ] 기존 content tab 문법을 `실행 / 산출물 / 알림`으로 치환한다.
- [ ] mobile floating nav 문법을 유지한다.
- [ ] run card는 기존 법안 카드처럼 텍스트 중심, 흰색 표면, 낮은 장식으로 만든다.
- [ ] status chip은 색상과 한글 라벨을 함께 제공한다.
- [ ] 로그/JSON은 어두운 코드 블록을 사용하되 전체 화면 톤은 모두의입법과 맞춘다.
