# 법안 시각 리포트 연구/PoC

작성일: 2026-06-09

## 1. 목적

현재 AI 요약은 `brief_summary`, `gpt_summary`, `summary_tags`를 생성해 `Bill`에 반영한다. 이 PoC의 목적은 기존 텍스트 요약을 유지하면서, 법안 상세 화면에서 바로 조합할 수 있는 **근거 기반 시각 리포트 JSON** 계약을 검증하는 것이다.

1차 대상은 일반 시민이다. 리포트는 찬반 판단을 대신하지 않고, 법안이 무엇을 바꾸는지와 근거가 어디에서 왔는지를 중립적으로 보여준다.

## 2. 현재 확인한 기준

- 표준 AI 요약 경로는 `lawdigest-pipeline ai-summary`이며 Gemini CLI 실시간 처리와 Codex CLI fallback을 사용한다.
- 구조화 출력 계약은 `BatchStructuredSummary`이고, 허용 필드는 `briefSummary`, `gptSummary`, `tags` 세 개다.
- DB 반영은 `Bill.brief_summary`, `Bill.gpt_summary`, `BillSummaryTag`로 나뉜다.
- 법안 상세 API는 `BillDetailResponse -> BillInfoDto`를 통해 요약 텍스트를 내려준다.
- 웹 상세 화면은 `services/web/components/Bill/BillList/Bill/Bill.tsx`에서 `gpt_summary`를 표시한다.
- 기존 프론트 스택은 Next.js, NextUI, Tailwind, D3, Chart.js다.

이 기준 때문에 시각 리포트는 기존 요약 필드를 대체하지 않고 별도 계약으로 추가해야 한다.

## 3. 외부 근거 우선순위

### 필수 근거

1. 열린국회정보 의안 근거
   - 저장소 기준: `references/assembly-api-mcp`
   - 우선 도구: `bill_detail`, `assembly_bill`, `assembly_session`
   - 최소 필드: 의안 상세, 제안이유, 주요내용, 발의자, 소관위, 심사 단계, 표결 정보

2. 법제처/국가법령정보센터 근거
   - 공식 기준: 국가법령정보 공동활용 OPEN API 활용가이드
   - URL: https://open.law.go.kr/LSO/openApi/guideList.do
   - 최소 필드: 현행 법령 본문, 조문, 관련 법령, 법령용어

3. MCP 구현 참고
   - `korean-law-mcp` 공개 저장소는 2026-06-09 검색 기준 v4.0 설명에서 법제처 42개 API를 17개 MCP 도구로 제공한다고 밝힌다.
   - URL: https://github.com/chrisryugj/korean-law-mcp
   - 정식 구현 전에는 공식 API 문서와 로컬 `references/assembly-api-mcp`를 source of truth로 우선한다.

### 실패 정책

- 열린국회 의안 상세 조회가 실패하면 `status: "needs_review"`로 둔다.
- 개정 대상 법률이 식별되었는데 법제처/국가법령정보센터 조회가 실패하면 `status: "needs_review"`로 둔다.
- 제정안처럼 현행 조문 비교가 성립하지 않는 경우는 `not_applicable` 근거로 표시한다.
- 표결 정보가 없는 계류안은 리포트 실패가 아니다. `vote_chart`를 만들지 않거나 `source_notes`에 “표결 전”으로 적는다.

## 4. JSON 계약

스키마 파일: `docs/ai/bill-visual-report-schema.json`

최상위 필드:

- `version`: 현재 `1.0`
- `status`: `ready` 또는 `needs_review`
- `billId`, `billName`
- `generatedAt`
- `audience`: `general_public`
- `tone`: `neutral_explanatory`
- `qualityGate`: 필수 근거 충족 여부와 검수 메모
- `evidence`: 출처 목록
- `blocks`: 프론트가 렌더링할 블록 배열

허용 블록:

- `summary_callout`: 리포트 첫 줄 핵심
- `change_points`: 무엇이 바뀌는지 1~5개 항목
- `before_after`: 현행과 개정안 비교
- `impact_list`: 영향을 받는 주체와 효과
- `process_timeline`: 발의부터 심사/표결/공포까지 절차
- `vote_chart`: 표결 수치가 있을 때만 사용
- `law_links`: 관련 법령 링크
- `term_glossary`: 어려운 법률 용어 풀이
- `source_notes`: 근거 한계, 조회 실패, 검수 필요 사항

## 5. AI 생성 규칙

AI는 UI를 만들지 않는다. AI는 스키마에 맞는 JSON만 생성한다.

- 블록 타입은 스키마에 있는 값만 사용한다.
- 각 주장은 최소 하나 이상의 `evidenceRefs`를 가져야 한다.
- 근거가 없으면 단정하지 않고 `source_notes`에 남긴다.
- 일반 시민 대상이므로 한 문장은 짧게 쓴다.
- 정당, 의원, 단체, 정부 기관에 대한 찬반 평가를 만들지 않는다.
- “실효성 강화”, “국민 삶의 질 향상” 같은 추상 표현만 반복하지 않고 무엇이 어떻게 바뀌는지 쓴다.
- 숫자, 날짜, 조문 번호는 근거에서 확인된 경우에만 쓴다.

## 6. 프론트 컴포넌트 매핑

1차 구현 시 추천 위치:

- 타입: `services/web/types/type/bill/visualReport.ts`
- 렌더러: `services/web/app/bill/[id]/components/VisualReport/VisualReport.tsx`
- 블록 registry: `services/web/app/bill/[id]/components/VisualReport/blocks.tsx`
- 상세 화면 연결: `services/web/app/bill/[id]/components/BillDetail/BillDetail.tsx`

렌더링 원칙:

- `block.type`별 고정 컴포넌트를 사용한다.
- 카드 안에 카드를 넣지 않는다.
- 텍스트는 모바일 375px에서 줄바꿈되어야 한다.
- `vote_chart`는 기존 `HalfDonutChart` 또는 Chart.js 계열 컴포넌트를 재사용한다.
- `source_notes`는 접힌 영역이나 낮은 시각 강도로 표시한다.
- AI가 색상, 크기, 레이아웃 클래스를 내려주지 않는다.

## 7. 백엔드/DB 구현 기본안

연구 이후 제품 구현에 들어갈 때의 기본안:

- `Bill`에 `bill_visual_report` JSON/TEXT 컬럼을 추가한다.
- `BillInfoDto`와 프론트 `BillResponse` 타입에 `bill_visual_report`를 추가한다.
- AI 서비스에는 `update_bill_visual_report(bill_id, report_json, mode)`를 추가한다.
- 기존 `update_bill_summary`는 변경하지 않는다.
- 리포트 생성 실패는 기존 요약 성공 여부를 덮어쓰지 않는다.

별도 테이블은 2차 후보로 둔다. 버전 이력, 검수자, 재생성 로그가 필요해지는 시점에 `BillVisualReport` 테이블로 분리한다.

## 8. PoC 샘플

샘플 파일: `docs/ai/samples/bill-visual-report-samples.json`

샘플은 기존 dry-run 리포트의 최신 5건을 기준으로 한다.

- 공공외교법 일부개정법률안
- 상법 일부개정법률안
- 남녀고용평등과 일·가정 양립 지원에 관한 법률 일부개정법률안
- 농어업인 삶의 질 향상 및 농어촌지역 개발촉진에 관한 특별법 일부개정법률안
- 해양폐기물 및 해양오염퇴적물 관리법 일부개정법률안

주의: 샘플 fixture는 스키마와 화면 조합 검증용이다. 실제 제품 데이터로 승격하려면 열린국회정보와 국가법령정보센터 조회 결과로 `evidence`를 다시 채워야 한다.

## 9. 검증 방법

문서/스키마 검증:

```bash
python -m json.tool docs/ai/bill-visual-report-schema.json >/tmp/bill-visual-report-schema.pretty.json
python -m json.tool docs/ai/samples/bill-visual-report-samples.json >/tmp/bill-visual-report-samples.pretty.json
```

구현 단계 검증:

- `services/ai` 테스트에 스키마 검증 테스트를 추가한다.
- `services/backend` 테스트에서 상세 응답에 리포트 JSON이 포함되는지 확인한다.
- `services/web` 테스트에서 허용 블록 타입별 렌더링과 알 수 없는 타입 fallback을 확인한다.
- 브라우저에서 375px, 768px, 데스크톱 폭을 확인한다.

## 10. 다음 구현 순서

1. AI 서비스에 리포트 스키마 모델과 프롬프트를 추가한다.
2. MCP/외부 API 조회 결과를 정규화하는 evidence collector를 만든다.
3. `Bill` 새 컬럼과 API 응답 필드를 추가한다.
4. 프론트에 VisualReport registry와 기본 블록을 추가한다.
5. 5개 샘플로 리포트 품질 리뷰 후 배치 생성 대상을 넓힌다.
