# Pipeline Monitor Design System

이 문서는 `services/pipeline-monitor` 구현 에이전트를 위한 디자인 시스템 기준서다. 사람용 시각 문서는 같은 폴더의 `DESIGN.html`을 사용한다.

## Impeccable 적용 결과

이번 방향은 `impeccable extract`, `shape`, `bolder` 흐름을 기준으로 재정의했다.

### Extract

기존 모두의입법 웹에서 재사용할 재료만 추출한다.

| Source | Extract | Do not extract |
| --- | --- | --- |
| `PRODUCT.md` | 시민적 신뢰, 쉬운 진입과 깊은 탐색, 중립성 | 시민용 피드 IA |
| `DESIGN.md` | Pretendard, neutral-first palette, flat-by-default | 모바일 검색/피드 경험 |
| `services/web/tailwind.config.js` | `#191919`, `#96BCFA`, `#E63946`, gray scale, dark tokens | 선거/법안 화면의 컴포넌트 구조 |
| `services/web/styles/globals.css` | Pretendard stack, Material Symbols, status colors | feed tab indicator |
| `services/web/public/images/logo.svg` | 1-2px rainbow signature | rainbow UI system |

### Shape

Feature summary: Pipeline Monitor는 운영자가 최근 파이프라인 실행, 실패 단계, fallback, 산출물을 한 화면에서 추적하는 read-only 운영 도구다.

Primary user action: 최근 실행 테이블에서 이상 run을 선택하고, 오른쪽 trace stack에서 실패 단계와 원시 로그를 확인한다.

Design direction:

- Register: product
- Color strategy: Restrained. 모두의입법 토큰을 사용하되 `#191919` command surface와 흰색 ledger surface의 강한 대비로 특색을 만든다.
- Scene sentence: 운영자가 낮 시간대의 개발용 27-inch 모니터에서 배포 직후 파이프라인 정상 여부를 확인한다. 주변은 밝고, 화면은 빠르게 스캔되어야 한다.
- Anchor references: Linear issue table의 밀도, GitHub Actions run detail의 추적성, Raycast preferences의 단단한 컨트롤.

### Bolder

"더 과감하게"는 gradient나 장식이 아니라 더 분명한 구조, 강한 정보 위계, 더 독특한 표면 조합으로 처리한다.

- Dashboard를 generic KPI card grid가 아니라 `command ledger`로 만든다.
- 화면 왼쪽은 실행 ledger table, 오른쪽은 selected run trace stack이다.
- 상단에는 검정 command bar를 둬 모두의입법 `primary-ink`를 적극 사용한다.
- 레인보우는 브랜드 hairline 하나로 제한한다.
- 형태는 둥근 SaaS 카드가 아니라 1px ruled grid, 8px 이하 radius, 단단한 table row, bracket-like detail panel로 만든다.

## Product Posture

Pipeline Monitor는 모두의입법 시민용 웹처럼 탐색적인 경험을 제공하는 화면이 아니다. 운영자가 파이프라인 상태를 판단하는 도구다.

- 데이터 소스: 자체 런타임 JSONL, artifact metadata.
- 기본 성격: read-only.
- 첫 화면 목표: 10초 안에 마지막 성공, 마지막 실패, 현재 실행 중, fallback, 산출물 존재 여부를 확인한다.
- 1차 사용자: 개발자, 데이터 파이프라인 운영자, 배포 직후 smoke를 확인하는 관리자.
- 비목표: Airflow UI 재구현, Prometheus/Grafana 대체, 시민용 서비스 화면 통합.

## Visual System

### Tokens

```css
--font-sans: 'Pretendard Variable', Pretendard, -apple-system, BlinkMacSystemFont, system-ui, 'Noto Sans KR', sans-serif;
--font-mono: 'Fira Code', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;

--surface: #FFFFFF;
--surface-ruled: #F5F7FD;
--surface-muted: #EBEBEB;
--line: #E0E0E0;
--text-muted: #6F6F6F;
--text-secondary: #555555;
--text-strong: #262626;
--ink: #191919;
--soft-blue: #96BCFA;
--alert: #E63946;
--info-lime: #D7F963;
--dark: #101012;
--dark-panel: #1E1E1E;
--dark-line: #2E2E2E;
--success: #168A4A;
--warning: #9A5B05;
--brand-rainbow: linear-gradient(90deg, #FBEB59 0%, #FC56D8 31%, #10D9EF 65%, #6CF880 100%);
```

대비 보정:

- 기존 `#999999`는 본문/라벨로 쓰기에는 약하다. 작은 텍스트에는 `#6F6F6F` 이상을 사용한다.
- `#EBEBEB`는 텍스트 색으로 쓰지 않는다. 배경과 border에만 사용한다.
- 검정 표면 위 텍스트는 `#F5F7FD` 또는 `#EBEBEB`를 사용한다.

### Rainbow Policy

허용:

- 페이지 최상단 2px brand hairline.
- 모두의입법 wordmark 아래 1-2px underline.
- 문서 내 token sample 한 번.

금지:

- gradient button.
- gradient pill.
- gradient chart.
- rainbow status mapping.
- code panel top border 반복.
- 카드나 테이블 border 장식.

### Shape

- Base radius: 8px.
- Table, code, toolbar: 6px 또는 8px.
- Large shell: 12px까지만 허용.
- Primary button: 모니터링 서비스에서는 pill이 아니라 8px radius를 기본으로 한다.
- 정보 패널은 shadow 대신 1px border와 ruled background로 구분한다.
- colored side stripe는 사용하지 않는다.

## Information Architecture

### Dashboard

목표: 현재 상태를 빠르게 판단한다.

구성:

1. Command bar: environment, log source, refresh, auto refresh state.
2. Health ledger: last success, last failure, running, fallback.
3. Run ledger table: latest runs.
4. Trace stack: selected run details.
5. Raw log drawer or lower panel.

### Runs

목표: 실행 이력을 필터링하고 비교한다.

필수 필터:

- Time range.
- Status.
- Command.
- Provider.
- Search: run id, command, artifact path.

기본 표현은 table이다. 카드 목록은 모바일 보조 표현이다.

### Run Detail

목표: 실패 원인과 산출물을 추적한다.

구성:

- Metadata strip.
- Step stack.
- Result diff.
- Artifact list.
- Error block.
- Raw JSONL.

### Artifacts

목표: 산출물 위치와 내용을 확인한다.

구성:

- File name.
- Type.
- Size.
- Created at.
- Related run id.
- Preview action.

### Runtime Settings

목표: 모니터링 앱이 무엇을 보고 있는지 확인한다.

구성:

- Log directory.
- Runtime version.
- CLI paths.
- Model defaults.
- Refresh interval.
- Deployment target.

## Component Specifications

### CommandBar

상단의 검정 command surface다.

- Height: 64px.
- Background: `--ink`.
- Text: `#F5F7FD`.
- Contains: wordmark, service name, env badge, refresh button, updated time.
- Rainbow: wordmark underline only.

### HealthLedger

KPI card grid가 아니라 네 칸짜리 ledger row다.

- Border: 1px `--line`.
- Background: `--surface`.
- Each cell has label, value, supporting note.
- Failure cell can use alert text, but background 전체를 빨갛게 칠하지 않는다.

### ControlToolbar

테이블 바로 위에 붙는 compact toolbar다.

- Height: 48px.
- Controls: time range, status, command, provider, search, refresh.
- Radius: 8px.
- Focus ring: `--soft-blue`.
- No gradient, no pill overload.

### RunLedgerTable

핵심 탐색 컴포넌트다.

Columns:

- Status.
- Started at.
- Command.
- Provider.
- Duration.
- Items.
- Fallback.
- Error.
- Artifacts.

Rules:

- Default sort: started_at desc.
- Selected row uses `--surface-ruled` background and 1px border treatment.
- Status badge radius 6px.
- Error summary is one line, full traceback in TraceStack.

### TraceStack

선택한 run의 오른쪽 detail panel이다.

- Desktop: sticky right panel.
- Mobile: table 아래 single column.
- Sections: metadata, steps, artifacts, error, raw event.
- Shape: bracket-like solid panel using full border, not side stripe.
- Step marker: small square marker, not decorative gradient line.

### LogPanel

JSONL 원문 확인 영역이다.

- Background: `--dark`.
- Border: `--dark-line`.
- Font: mono.
- Modes: pretty JSON, raw line.
- Copy button required.
- Secrets are masked.

## State Language

| Status | Label | Color |
| --- | --- | --- |
| `success` | 성공 | `#168A4A` |
| `failed` | 실패 | `#E63946` |
| `running` | 실행 중 | `#96BCFA` |
| `warning` | 경고 | `#9A5B05` |
| `fallback` | fallback | `#191919` text, `#E0E0E0` border |
| `unknown` | 알 수 없음 | `#6F6F6F` |

상태 메시지 예시:

- `성공 - 5건 요약, JSON 산출물 생성`
- `실패 - structured validation 실패`
- `실행 중 - 2분 14초 경과`
- `fallback - Codex CLI로 1건 재처리`
- `알 수 없음 - 종료 이벤트 누락`

## Responsive Rules

| Width | Layout |
| --- | --- |
| `< 768px` | command bar, health ledger stack, horizontal table, detail below |
| `768px - 1199px` | full table, detail below or collapsible |
| `>= 1200px` | ledger table left, trace stack right |

모바일에서 table을 카드로 완전히 바꾸지 않는다. run 간 비교를 위해 horizontal scroll을 허용한다.

## Accessibility

- 모든 상태는 색상과 텍스트 라벨을 함께 제공한다.
- `#999999` 이하 대비의 텍스트를 본문에 쓰지 않는다.
- Table header는 `th scope`를 사용한다.
- Keyboard focus는 명확한 outline을 제공한다.
- LogPanel은 복사 없이도 텍스트 선택이 가능해야 한다.

## Implementation Checklist

- [ ] 기존 모두의입법 토큰을 복제하거나 공유한다.
- [ ] `CommandBar`, `HealthLedger`, `ControlToolbar`, `RunLedgerTable`, `TraceStack`, `LogPanel`을 우선 구현한다.
- [ ] 레인보우는 brand hairline과 wordmark underline에만 사용한다.
- [ ] primary button은 8px radius를 기본으로 한다.
- [ ] status badge는 6px radius, 한글 라벨, 충분한 대비를 유지한다.
- [ ] MVP에는 실행, 재시도, 삭제, 롤백 버튼을 넣지 않는다.
- [ ] 실제 집계 없는 차트를 만들지 않는다.
- [ ] `impeccable detect`에서 low contrast가 나오지 않게 검증한다.
