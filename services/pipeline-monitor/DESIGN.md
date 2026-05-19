# Pipeline Monitor Design System

이 문서는 `services/pipeline-monitor` 구현 에이전트를 위한 디자인 시스템 기준서다. 사람용 시각 문서는 같은 폴더의 `DESIGN.html`을 사용한다.

## Scope

이 디자인 시스템은 모두의입법 데이터 파이프라인 운영 모니터링 웹서비스를 위한 시각 언어, 레이아웃 규칙, 컴포넌트 기준, 상태 표현, 접근성 기준을 정의한다.

목표는 특정 화면 하나를 예쁘게 꾸미는 것이 아니라 다음 구현 단계에서 반복 가능한 제품 화면을 만들 수 있게 하는 것이다.

- 실시간 파이프라인 상태를 빠르게 판단한다.
- 실패, fallback, 실행 중 상태를 먼저 확인한다.
- Gemini CLI, Codex CLI, Claude CLI 같은 provider 차이를 명확히 드러낸다.
- 로그, 산출물, schema validation 결과를 추적 가능하게 보여준다.
- 기존 모두의입법 웹의 토큰과 브랜드 감각을 가져오되 운영 도구에 맞게 밀도와 위계를 재정의한다.

## Foundation

### Design Voice

`Civic Ops Ledger`

시민 서비스의 신뢰감과 운영 도구의 정밀함을 결합한다. 화면은 장식적인 대시보드가 아니라 실행 기록을 읽는 장부처럼 보여야 한다. 단, 장부라는 말이 건조함을 뜻하지는 않는다. typography, line, spacing, contrast가 살아 있어야 한다.

### Principles

- **Status first:** 첫 화면은 설명이 아니라 현재 상태 판단으로 시작한다.
- **Incident over filters:** 필터는 사용자가 상태를 본 뒤 쓰는 도구다. 필터가 화면을 지배하면 실패다.
- **Rows over blocks:** 실행 이력은 큰 카드가 아니라 compact row와 rule의 리듬으로 읽힌다.
- **Traceable by default:** 선택된 run은 로그와 산출물까지 이어져야 한다.
- **Minimal rainbow:** 레인보우는 브랜드 signature로만 쓴다. 상태, 버튼, 차트 장식에는 쓰지 않는다.
- **Human-grade finish:** 토큰 목록만 맞추고 미감이 죽어 있으면 실패다. 간격, 줄바꿈, 밀도, 균형을 구현 단계에서 계속 확인한다.

## Brand Extraction

기존 모두의입법 웹에서 가져올 것은 UI 구조가 아니라 재료다.

| Source | Use |
| --- | --- |
| `PRODUCT.md` | 시민적 신뢰, 중립성, 쉽게 시작하고 깊게 들어가는 원칙 |
| `DESIGN.md` | Pretendard, neutral-first palette, flat by default |
| `services/web/tailwind.config.js` | `#191919`, `#96BCFA`, `#E63946`, gray scale, dark tokens |
| `services/web/styles/globals.css` | Pretendard stack, Material Symbols, status colors |
| `services/web/public/images/logo.svg` | 1-2px rainbow signature only |

## Tokens

```css
--surface: #FCFCFA;
--surface-raised: #FFFFFF;
--surface-wash: #F5F7FD;
--line-soft: #ECECE8;
--line: #DCDCD6;
--muted: #707070;
--secondary: #555555;
--strong: #262626;
--ink: #191919;
--blue: #96BCFA;
--blue-strong: #305FBA;
--alert: #E63946;
--lime: #D7F963;
--dark: #101012;
--dark-panel: #1E1E1E;
--dark-line: #2E2E2E;
--success: #168A4A;
--warning: #9A5B05;
--brand-rainbow: linear-gradient(90deg, #FBEB59 0%, #FC56D8 31%, #10D9EF 65%, #6CF880 100%);
--font-sans: 'Pretendard Variable', Pretendard, -apple-system, BlinkMacSystemFont, system-ui, 'Noto Sans KR', sans-serif;
--font-mono: 'Fira Code', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
```

### Token Rules

- `#999999` is too weak for small text. Use `#707070` or darker for labels.
- Numbers use tabular figures.
- Large text exists only when it reflects priority. Do not enlarge every metric.
- Default radius is `8px`; shell radius can be `12px`; device/specimen radius can be larger only when it frames an example.
- Shadows are rare. Use line, tone, and spacing before shadow.

## Typography

- Font family: Pretendard first, system sans fallback.
- Mono family: Fira Code for log, run id, artifact path, schema output.
- Page title: 48-56px desktop, 30-34px mobile.
- Section title: 24-28px desktop, 22-24px mobile.
- Body: 14-16px.
- Metadata and chips: never below 12px.
- Korean line breaks must be inspected on mobile. Do not rely on accidental browser wrapping.

## Layout Patterns

### Mobile: Pocket Ops

Mobile is not a collapsed desktop table. It has its own hierarchy.

1. `OpsHeader`: brand, environment, updated time, refresh.
2. `IncidentStrip`: one compact line showing current health and the single thing to inspect.
3. `FilterRail`: horizontal chips, 32-36px high.
4. `RunStack`: compact run rows with status, command, time, duration, artifact count.
5. `TraceSheet`: selected run detail, collapsed by default below the list.

Never stack filters as full-width form boxes.

### Desktop: Ledger + Trace

1. `OpsHeader`.
2. `HealthRail`: four compact counters, not KPI cards.
3. `ControlBar`: filters and search.
4. `RunLedger`: table-first execution list.
5. `TracePanel`: selected run details.
6. `LogPanel`: raw JSONL / traceback.

## Components

### OpsHeader

- Black command surface.
- Brand wordmark with thin rainbow underline.
- Environment, log source, updated time, refresh.
- Mobile height target: 56-64px.

### IncidentStrip

- Mobile-first component.
- Shows current status in one sentence.
- Example: `주의 필요: bill.ingest 실패, Codex fallback 1회`.
- Contains one action: `trace 보기`.
- Uses alert color only for text or tiny marker, not full red panel.

### FilterRail

- Horizontal scroll rail.
- Chips are 32-36px high.
- Selected chip uses `--ink` fill and white text.
- Search can expand into a full input, but default state is compact.

### HealthRail

- Four compact cells.
- Labels are 12px; values are 20-24px.
- No giant stacked blocks on mobile.
- On mobile it becomes a 2x2 compact grid or a horizontal rail.

### RunLedger

Desktop table:

- Status
- Started
- Command
- Provider
- Duration
- Items
- Error
- Artifacts

Mobile rows:

- Left status marker.
- Main line: command + status.
- Meta line: started, duration, provider.
- Right: artifact count or error token.

### TracePanel / TraceSheet

- Metadata.
- Step stack.
- Artifact list.
- Error summary.
- Raw JSONL preview.

Mobile starts collapsed after selected row; desktop is right-side panel.

### LogPanel

- Dark panel.
- Mono.
- Pretty/raw toggle.
- Copy button.
- No rainbow top border.

## State Language

| Status | Label | Color |
| --- | --- | --- |
| `success` | 성공 | `#168A4A` |
| `failed` | 실패 | `#E63946` |
| `running` | 실행 중 | `#305FBA` text with `#96BCFA` tint |
| `warning` | 경고 | `#9A5B05` |
| `fallback` | fallback | `#191919` text, `#DCDCD6` border |
| `unknown` | 알 수 없음 | `#707070` |

## Accessibility

- Body contrast must satisfy WCAG AA.
- Interactive controls must have visible focus states.
- Icon-only buttons require `aria-label`.
- Run rows must not rely on color alone; include text status.
- Log panels must preserve selectable text.
- Mobile screenshots must be checked at 390px width before handoff.

## Implementation Checklist

- [ ] Mobile first: filters must not occupy the first viewport as stacked blocks.
- [ ] Create `OpsHeader`, `IncidentStrip`, `FilterRail`, `RunStack`, `TraceSheet` for mobile.
- [ ] Create `HealthRail`, `ControlBar`, `RunLedger`, `TracePanel`, `LogPanel` for desktop.
- [ ] Keep rainbow usage to brand hairline and wordmark underline.
- [ ] Use `#707070` or darker for small labels.
- [ ] No generic KPI card grid as first screen.
- [ ] No fake charts without real data.
- [ ] No write actions in MVP.
- [ ] Inspect mobile and desktop screenshots before merging UI changes.
