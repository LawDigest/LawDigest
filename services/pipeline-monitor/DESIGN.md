# Pipeline Monitor Design System

이 문서는 `services/pipeline-monitor` 구현 에이전트를 위한 디자인 시스템 기준서다. 사람용 시각 문서는 같은 폴더의 `DESIGN.html`을 사용한다.

## Design Reset

이전 시안의 실패 원인은 토큰 문제가 아니라 미감과 구조 문제였다.

- 필터가 모바일 첫 화면을 점유했다.
- 상태 요약이 거대한 박스 네 개로 쌓이며 초보자 예제처럼 보였다.
- 정보 위계가 `font-weight: bold`에만 의존했다.
- 운영 화면인데 실행 흐름과 실패 추적이 먼저 보이지 않았다.
- 모두의입법 토큰을 썼지만 모두의입법답지도, 모니터링 도구답지도 않았다.

이번 재설계는 다음을 기준으로 한다.

- **Mobile first:** 모바일은 데스크톱 table의 축소판이 아니라 `Pocket Ops` 화면이다.
- **Incident first:** 마지막 성공보다 "지금 확인할 문제"가 먼저 보인다.
- **Filters recede:** 필터는 큰 input stack이 아니라 얇은 horizontal rail이다.
- **Run rows, not blocks:** 실행 목록은 compact row로 읽힌다.
- **Aesthetic discipline:** 검정 command surface, 종이 같은 off-white surface, 얇은 rule, 정확한 숫자, 작은 accent만 사용한다.
- **Rainbow minimal:** 레인보우는 브랜드 hairline과 wordmark underline만 허용한다.

## Extracted Brand Materials

기존 모두의입법 웹에서 가져올 것은 UI 구조가 아니라 재료다.

| Source | Use |
| --- | --- |
| `PRODUCT.md` | 시민적 신뢰, 중립성, 쉽게 시작하고 깊게 들어가는 원칙 |
| `DESIGN.md` | Pretendard, neutral-first palette, flat by default |
| `services/web/tailwind.config.js` | `#191919`, `#96BCFA`, `#E63946`, gray scale, dark tokens |
| `services/web/styles/globals.css` | Pretendard stack, Material Symbols, status colors |
| `services/web/public/images/logo.svg` | 1-2px rainbow signature only |

## Visual Direction

### Scene

운영자가 배포 직후 노트북이나 27-inch 모니터에서 파이프라인 상태를 빠르게 확인한다. 화면은 밝은 환경에서도 읽혀야 하고, 모바일에서는 걸어가며 "문제가 있는지"만 즉시 판단할 수 있어야 한다.

### References

- GitHub Actions: 실행 단위와 로그 추적성.
- Linear: 밀도 있는 row와 선택 상태.
- Raycast: 단단한 control surface.
- 모두의입법: Pretendard, neutral surfaces, `#191919` ink, 제한적 rainbow signature.

### Aesthetic Lane

`Civic Ops Ledger`: 시민 서비스의 신뢰감과 운영 도구의 정밀함을 합친다. 차트 장식이 아니라 실행 기록 장부처럼 보이되, typography와 spacing은 정제되어야 한다.

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

Rules:

- `#999999` is too weak for small text. Use `#707070` or darker for labels.
- Numbers use tabular figures.
- Large text exists only when it reflects priority. Do not enlarge every metric.
- Default radius is `8px`; shell radius can be `12px`.
- Shadows are rare. Use lines and tone before shadow.

## Rainbow Policy

Allowed:

- Top page hairline.
- Wordmark underline.

Disallowed:

- Gradient buttons.
- Gradient pills.
- Gradient charts.
- Status colors mapped to rainbow stops.
- Repeated rainbow borders.

## UX Structure

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

## Implementation Checklist

- [ ] Mobile first: filters must not occupy the first viewport as stacked blocks.
- [ ] Create `OpsHeader`, `IncidentStrip`, `FilterRail`, `RunStack`, `TraceSheet` for mobile.
- [ ] Create `HealthRail`, `ControlBar`, `RunLedger`, `TracePanel`, `LogPanel` for desktop.
- [ ] Keep rainbow usage to brand hairline and wordmark underline.
- [ ] Use `#707070` or darker for small labels.
- [ ] No generic KPI card grid as first screen.
- [ ] No fake charts without real data.
- [ ] No write actions in MVP.
