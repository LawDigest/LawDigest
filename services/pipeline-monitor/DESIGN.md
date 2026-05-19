# Pipeline Monitor Design System

이 문서는 `services/pipeline-monitor` 구현 에이전트를 위한 디자인 시스템 기준서다. 사람용 시각 문서는 같은 폴더의 `DESIGN.html`을 사용한다.

## 핵심 정정

Pipeline Monitor는 모두의입법의 디자인 토큰과 폰트를 사용하지만, 기존 모두의입법 시민용 웹의 UI/UX 구조를 모방하지 않는다.

적용 기준은 다음과 같다.

- 유지: Pretendard, `#191919` primary ink, 기존 gray scale, `#96BCFA`, `#E63946`, 흰색/회색 표면, 버튼의 단단한 질감, Material Symbols.
- 제한적 유지: 모두의입법 로고의 레인보우 그라디언트는 브랜드 서명으로만 쓴다.
- 변경: 화면 구조는 데이터 파이프라인 모니터링에 맞춘다. 실행 테이블, 상태 요약, 단계 타임라인, 로그 패널, 산출물 목록이 중심이다.
- 금지: 피드/타임라인/모바일 floating nav를 그대로 가져오는 것, 레인보우 pill/gradient button/gradient chart를 남용하는 것.

## 기존 웹에서 가져올 토큰

디자인 재료는 아래 파일을 기준으로 한다.

| Source | 가져올 것 | 가져오지 않을 것 |
| --- | --- | --- |
| `services/web/tailwind.config.js` | `primary`, `gray`, `theme`, `dark` 색상 토큰 | 시민용 페이지의 레이아웃 |
| `services/web/styles/globals.css` | Pretendard font stack, Material Symbols, snackbar status color | feed tab 구조 |
| `services/web/public/images/logo.svg` | 1-2px rainbow underline signature | 큰 gradient surface |
| `services/web/components/Bill/BillList/Bill/Bill.tsx` | 평평한 white surface, shadow 최소화 | 법안 카드 정보 구조 |
| `services/web/app/election/components/SeatSummaryCard.tsx` | white + border + compact summary language | 선거/피드형 화면 구성 |

## Product Posture

Pipeline Monitor는 운영자가 파이프라인 상태를 빠르게 판단하는 도구다.

- 사용자는 터미널 대신 브라우저에서 실행 이력과 실패 원인을 확인한다.
- 첫 화면에서 최근 상태, 실패 원인, 마지막 성공 시각, fallback 발생 여부, 산출물 위치를 확인할 수 있어야 한다.
- 1차 버전은 read-only다. 실행, 재시도, 삭제, 롤백 버튼은 제공하지 않는다.
- UI는 데스크톱 운영 화면을 우선하되, 모바일에서는 확인 가능한 읽기 화면으로 축약한다.

## Brand Tokens

### Font

```css
--font-sans: 'Pretendard Variable', Pretendard, -apple-system, BlinkMacSystemFont, system-ui, 'Noto Sans KR', sans-serif;
--font-mono: 'Fira Code', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
```

규칙:

- 한글 UI와 설명 텍스트는 Pretendard를 사용한다.
- 실행 ID, 파일 경로, JSON key, CLI 명령은 mono를 사용한다.
- 숫자 지표는 `font-variant-numeric: tabular-nums`를 적용한다.
- 대형 마케팅 헤드라인을 만들지 않는다.

### Color

| Token | Value | Pipeline Monitor Usage |
| --- | --- | --- |
| `primary-3` | `#191919` | 주요 텍스트, primary button, active nav |
| `primary-2` | `#96BCFA` | 실행 중, 정보 강조, focus ring |
| `primary-1` | `#F5F7FD` | 아주 연한 정보 배경 |
| `gray-0.5` | `#EBEBEB` | 앱 배경, table header |
| `gray-1` | `#E0E0E0` | border, divider, secondary button |
| `gray-2` | `#999999` | muted text, unknown state |
| `gray-3` | `#555555` | secondary text |
| `gray-4` | `#262626` | strong text |
| `theme-alert` | `#E63946` | failed, destructive warning |
| `theme-info` | `#D7F963` | new data, schedule due highlight |
| `dark-b` | `#101012` | code/log panel background |
| `dark-l` | `#2E2E2E` | code/log panel border |
| `dark-pb` | `#1E1E1E` | dark surface |

추가 상태색:

- `success`: `#16A34A`
- `warning`: `#B7791F`
- `unknown`: `gray-2`

### Rainbow Policy

레인보우 그라디언트는 모두의입법 브랜드 서명이다. Pipeline Monitor에서는 최소한으로만 사용한다.

허용:

- 상단 wordmark 아래 1-2px underline
- active focus 위치를 알려주는 아주 얇은 hairline
- 문서/브랜드 설명에서 색상 토큰 예시 1회

금지:

- gradient button
- gradient pill
- gradient chart
- status color를 rainbow stop으로 매핑
- 페이지 배경 전체 gradient
- 코드 패널, 카드, 표 border에 반복 적용

권장 CSS:

```css
--brand-rainbow: linear-gradient(90deg, #FBEB59 0%, #FC56D8 31%, #10D9EF 65%, #6CF880 100%);
```

## Information Architecture

### Dashboard

목적: 현재 파이프라인 상태를 10초 안에 판단한다.

주요 영역:

- Health strip: 마지막 성공, 마지막 실패, 현재 실행 중, fallback 발생 여부
- Run table: 최근 실행 이력
- Failure focus: 최근 실패 1건의 단계와 오류 요약
- Artifact snapshot: 마지막 산출물 경로와 파일 수

### Runs

목적: 실행 이력을 비교하고 필터링한다.

필터:

- 기간: 최근 1시간, 24시간, 7일, 사용자 지정
- 상태: success, failed, running, warning, unknown
- 명령: `bill.ingest`, `bill.status_sync`, `summary:latest`, `ai.summary`
- provider: Gemini CLI, Codex CLI, Claude CLI, API

기본 표현은 table이다. 카드 목록은 모바일 보조 표현에만 사용한다.

### Run Detail

목적: 단일 실행의 원인과 결과를 추적한다.

구성:

- Run metadata
- Step timeline
- Structured result
- Error and traceback
- Artifacts
- Raw JSONL events

### Artifacts

목적: 실행 결과 파일을 찾고 미리 본다.

구성:

- 파일명
- 파일 형식
- 파일 크기
- 생성 시각
- 관련 run id
- preview 가능한 경우 JSON/Markdown 미리보기

### Runtime Settings

목적: 모니터링 앱이 어떤 런타임과 로그 경로를 보고 있는지 확인한다.

구성:

- Log directory
- Pipeline runtime version
- CLI paths
- Default model
- Refresh interval
- Deployment target

## Layout Model

### Desktop

Pipeline Monitor는 데스크톱 운영 화면을 우선한다.

```text
Top brand bar
Toolbar: time range / status filter / command filter / refresh
Main grid:
  Left: run table
  Right: selected run detail, failure focus, artifacts
Bottom or drawer: raw log panel
```

규칙:

- 최대 본문 너비는 `1440px`까지 허용한다.
- 기본 화면은 table-first다.
- 좌측 사이드바는 필수 아님. 사용한다면 220-240px 이하의 단순 navigation만 둔다.
- 섹션을 과도하게 카드화하지 않는다. table, detail panel, log panel처럼 역할이 있는 컨테이너만 경계선을 둔다.
- mobile floating nav, feed content tab, 시민용 carousel 패턴을 사용하지 않는다.

### Mobile

모바일은 운영 확인용 보조 화면이다.

- 상단에 status summary를 먼저 둔다.
- run table은 가로 스크롤을 허용한다.
- detail은 single column으로 쌓는다.
- 로그 패널은 접힘 상태로 시작한다.
- 하단 floating nav를 재사용하지 않는다. 간단한 top segmented nav나 menu를 사용한다.

## Components

### SystemHeader

역할: 브랜드와 현재 모니터링 대상 표시.

구성:

- 모두의입법 wordmark
- 1-2px rainbow underline
- `Pipeline Monitor`
- 환경: prod/test/dev
- 마지막 갱신 시각

### ControlToolbar

역할: 운영자가 테이블을 빠르게 좁혀 본다.

구성:

- Time range select
- Status segmented filter
- Command select
- Text search: run id, command, artifact path
- Refresh button

스타일:

- 높이 48-56px
- border-bottom 또는 contained toolbar
- 버튼 radius 8px 이하
- primary action은 refresh 하나만 둔다.

### HealthStrip

역할: 현재 상태 요약.

항목:

- 마지막 성공
- 마지막 실패
- 실행 중
- fallback

규칙:

- 4개 이하로 유지한다.
- 색상보다 텍스트를 우선한다.
- 실패가 있으면 failure focus panel로 연결한다.

### RunTable

역할: 핵심 탐색 컴포넌트.

필수 열:

- Status
- Started at
- Command
- Provider
- Duration
- Items
- Fallback
- Error
- Artifacts

규칙:

- 기본 정렬은 started_at desc.
- run id는 두 번째 줄 또는 detail panel에 표시한다.
- 오류는 첫 줄만 노출하고 detail에서 전문을 보여준다.
- status chip은 6-8px radius의 작은 badge다. pill 남용 금지.

### RunDetailPanel

역할: 선택한 실행의 상세 정보 확인.

구성:

- Metadata grid
- Step timeline
- Result summary
- Artifact list
- Error block

스타일:

- 화면 오른쪽 panel 또는 route page.
- desktop에서는 sticky detail panel 가능.
- mobile에서는 table 아래 single column.

### StepTimeline

역할: 어떤 단계에서 멈췄는지 확인.

구성:

- Step name
- Status
- Started at
- Duration
- Result count
- Error summary

스타일:

- 단순 vertical list.
- marker는 작은 square/dot 둘 중 하나만 사용한다.
- gradient line 사용 금지.

### LogPanel

역할: JSONL 원문과 traceback 확인.

구성:

- Pretty JSON
- Raw line view
- Copy button
- Masked secret indication

스타일:

- `dark-b` background
- mono font
- 가로 스크롤 허용
- 상단에 1px border만 사용한다. rainbow top border 금지.

### ArtifactList

역할: 산출물 탐색.

구성:

- file name
- type
- size
- created at
- related run
- preview/open action

규칙:

- 내부 서버 경로와 사용자 다운로드 링크를 구분한다.
- MVP에서 삭제 버튼은 없다.

## Status Language

| Status | Label | Color |
| --- | --- | --- |
| `success` | 성공 | `#16A34A` |
| `failed` | 실패 | `theme-alert` |
| `running` | 실행 중 | `primary-2` |
| `warning` | 경고 | `#B7791F` |
| `fallback` | fallback | `primary-3` text + `gray-1` border |
| `unknown` | 알 수 없음 | `gray-2` |

상태 메시지 예시:

- `성공 - 5건 요약, JSON 산출물 생성`
- `실패 - Gemini CLI 응답 validation 실패`
- `실행 중 - 2분 14초 경과`
- `fallback - Codex CLI로 1건 재처리`
- `알 수 없음 - 종료 이벤트 누락`

## Button Rules

- Primary: `bg-primary-3`, `text-white`, radius 8px.
- Secondary: white or `gray-0.5`, `border-gray-1`, `text-gray-4`.
- Destructive: `theme-alert`, 단 MVP에서는 쓰기 액션이 없으므로 기본적으로 등장하지 않는다.
- 버튼은 pill shape을 기본값으로 쓰지 않는다. 모두의입법 기존 버튼 감각은 색과 weight로 가져오고, 모니터링 도구에서는 더 절제한다.

## Data Display Rules

- 시간은 KST 기준으로 표시하고, 필요 시 UTC 원본을 tooltip 또는 detail에 둔다.
- duration은 `830ms`, `2분 14초`처럼 읽기 쉬운 단위로 표시한다.
- 숫자는 comma와 tabular nums를 사용한다.
- 긴 path는 가운데를 줄여 표시하고 hover/detail에서 전체를 보여준다.
- JSON은 pretty print하되 원문 raw line 접근도 제공한다.

## Accessibility

- 상태를 색상만으로 표현하지 않는다.
- table header에는 `th scope`를 사용한다.
- filter control은 현재 선택 상태를 스크린 리더가 알 수 있어야 한다.
- keyboard focus는 `primary-2` outline으로 표시한다.
- log panel의 텍스트 대비는 충분히 높게 유지한다.

## Implementation Checklist

- [ ] 기존 모두의입법 색상/폰트 토큰을 복제하거나 공유한다.
- [ ] 레인보우 그라디언트는 wordmark underline 정도로 제한한다.
- [ ] Dashboard는 table-first layout으로 구현한다.
- [ ] HealthStrip, ControlToolbar, RunTable, RunDetailPanel, LogPanel을 우선 구현한다.
- [ ] status chip은 작은 badge로 만들고 pill/gradient를 남용하지 않는다.
- [ ] MVP에는 실행/재시도/삭제 버튼을 넣지 않는다.
- [ ] 모바일에서는 table 가로 스크롤과 접힘 log panel을 제공한다.
- [ ] 실제 데이터 없는 차트는 만들지 않는다.
