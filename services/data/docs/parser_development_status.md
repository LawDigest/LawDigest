# PDF 파서 개발 현황

> 대상: 제9회 전국동시지방선거 경기도 광역단체장선거 여론조사 PDF (총 31건, 14개 조사기관 + 특수 1건)
> 기준일: 2026-04-01

---

## 개발 현황 요약

| 상태 | 기관 수 | PDF 건수 |
|------|---------|---------|
| ✅ 완료 (픽스처 검증까지) | 5 | 15 |
| 🔶 완료 (PR 머지 대기) | 1 | 4 |
| ❌ 미개발 | 7 | 11 |
| ❓ 보류 (선거 관련성 불명) | — | 1 |
| **합계** | — | **31** |

---

## 기관별 PDF 전체 목록

### ✅ 파서 완료 — 5개 기관, 15건

| 조사기관 | PDF 파일명 | 파서 | 브랜치 |
|---------|-----------|------|--------|
| 조원씨앤아이 | 더팩트_경기도 지선 여론조사 보고서_250930.pdf | `_TableFormatParser` | main |
| 조원씨앤아이 | 더팩트 경기교육신문_경기도 지선 여론조사 보고서_251027.pdf | `_TableFormatParser` | main |
| 조원씨앤아이 | 경기일보_경기 지선 여론조사 보고서_251201(1).pdf | `_TableFormatParser` | main |
| 조원씨앤아이 | 경기일보_경기 지선 여론조사 보고서_260105.pdf | `_TableFormatParser` | main |
| 조원씨앤아이 | 경기일보_경기 지선 여론조사 보고서_260202_수정.pdf | `_TableFormatParser` | main |
| 조원씨앤아이 | 경기일보_경기 지선 여론조사 보고서_260224.pdf | `_TableFormatParser` | main |
| 조원씨앤아이 | 프레시안_경기 지선 여론조사 보고서_260318_f.pdf | `_TableFormatParser` | main |
| (주)데일리리서치 | 등록_경기도_결과분석_데일리리서치2510011.pdf | `_TextFormatParser` | main |
| (주)리얼미터 | (리얼-오마이)결과표_경기도 지방선거 여론조사_최종.pdf | `_RealMeterParser` | main (PR#22) |
| (주)리얼미터 | 2. (리얼미터)결과표_오마이뉴스 경기도 지방선거 및 현안 조사_최종.pdf | `_RealMeterParser` | main (PR#22) |
| (주)한국리서치 | (경인일보)지방선거 경기도민 여론조사_결과표_2월 22일 보도용.pdf | `_KoreanResearchParser` | feat/codex/kr-signal-parsers |
| (주)한국리서치 | (경인일보)지방선거 경기도민 여론조사_결과표_2월 23일 보도용.pdf | `_KoreanResearchParser` | feat/codex/kr-signal-parsers |
| (주)시그널앤펄스 | 보도용_경기도 여론조사 보고서_프레시안_260212.pdf | `_SignalPulseParser` | feat/codex/kr-signal-parsers |
| (주)시그널앤펄스 | 보도용_경기도 여론조사 보고서_프레시안_251230(수정).pdf | `_SignalPulseParser` | feat/codex/kr-signal-parsers |
| (주)시그널앤펄스 | 보도용_경기도 여론조사 보고서_서울의소리_251215.pdf | `_SignalPulseParser` | feat/codex/kr-signal-parsers |

### 🔶 파서 완료 — PR 머지 대기, 1개 기관, 4건

| 조사기관 | PDF 파일명 | 파서 | 브랜치 |
|---------|-----------|------|--------|
| ㈜엠브레인퍼블릭 | [뉴스1 신년특집] 경기도민 여론조사 통계표_최종.pdf | `_EmbrainPublicParser` | feat/codex/embrain-parser |
| ㈜엠브레인퍼블릭 | [중부일보] 경기도민 여론조사 통계표_최종.pdf | `_EmbrainPublicParser` | feat/codex/embrain-parser |
| ㈜엠브레인퍼블릭 | [중부일보] 경기도민 여론조사 통계표_최종_2월 3주.pdf | `_EmbrainPublicParser` | feat/codex/embrain-parser |
| ㈜엠브레인퍼블릭 | [중부일보] 경기도민 여론조사 통계표_최종_3월 4주.pdf | `_EmbrainPublicParser` | feat/codex/embrain-parser |

### ❌ 파서 미개발 — 7개 기관, 11건

| 조사기관 | PDF 파일명 | 비고 |
|---------|-----------|------|
| (주)케이스탯리서치 | (결과표) KBS 지방선거 여론조사 [03. 경기].pdf | 포맷 미확인 |
| (주)케이스탯리서치 | 지방선거 관련 여론조사(경기)_한글통계표(12.31).pdf | 포맷 미확인 |
| (주)윈지코리아컨설팅 | 250915_보고서_드림투데이(경기)_v2.pdf | 포맷 미확인 |
| (주)윈지코리아컨설팅 | 260305_공표용보고서_경기도_정치지형조사_v2.pdf | 포맷 미확인 |
| (주)여론조사꽃 | 결과표_20260211_여론조사꽃_경기지사 2000_CATI조사_v01.pdf | cid: 인코딩 — pdfplumber 텍스트 추출 불가 |
| (주)여론조사꽃 | 결과표_20260326_여론조사꽃_경기도지사 2000_CATI조사_v01.pdf | cid: 인코딩 — pdfplumber 텍스트 추출 불가 |
| (주)여론조사꽃 | 결과표_20260317_여론조사꽃_경기도지사 1000_ARS조사_v01.pdf | ARS 방식 — 구조 상이 가능성 |
| 넥스트리서치 | (넥스트리서치_조사결과_등록_0319) 제9회 전국동시지방선거관련 경기지역 여론조사.pdf | 포맷 미확인 |
| ㈜에스티아이 | 통계표_에스티아이_경기도지사 선거 여론조사 0219.pdf | 포맷 미확인 |
| 입소스 주식회사 | (통계표) SBS 2026 설 특집 여론조사_경기.pdf | 포맷 미확인 |
| (주)한길리서치 | 결과분석_한길리서치1019.pdf | 포맷 미확인 |

### ❓ 보류 — 1건

| 파일명 | 사유 |
|--------|------|
| 2026 기후위기 국민 인식조사_09_경기_TABLE_등록_0306.pdf | 경기도지사 선거 여론조사 아님 (기후위기 인식조사, 140페이지) — 대상 포함 여부 확인 필요 |

---

## 파서 아키텍처

```
PollResultParser
├── _TableFormatParser        # 조원씨앤아이 등 — ▣ 전체 ▣ 테이블 직접 파싱
├── _TextFormatParser         # 데일리리서치 등 — N번) 질문 텍스트 섹션 기반
├── _RealMeterParser          # 리얼미터 — 헤더 선택지 + 텍스트 비율
├── _EmbrainPublicParser      # 엠브레인퍼블릭 — [표N], ■ 전체 ■, col4+ 선택지
├── _KoreanResearchParser     # 한국리서치 — [표N]/[문N], ▣ 전체 ▣ 텍스트, 페이지 분할 merge
└── _SignalPulseParser        # 시그널앤펄스 — [표N]/[QN] 두 버전 분기 처리
```

### 파서 선택 로직 (`parser_registry.json`)

1. **pollster_assignments**: 기관명 키워드 매칭 (priority=10)
2. **content_probes**: PDF 전문 특징 문자열 탐지 (priority=5)
3. **fallback_parser**: `_TextFormatParser` (priority=0)

---

## 알려진 이슈

| 이슈 | 대상 | 상태 |
|------|------|------|
| cid: 인코딩 — pdfplumber 텍스트 추출 불가 | 여론조사꽃 CATI 2건 | 미해결 — pymupdf(fitz) 등 대체 라이브러리 시도 필요 |
| ARS 방식 PDF 구조 상이 | 여론조사꽃 ARS 1건 | 미해결 |
| 기후위기 인식조사 선거 관련성 불명확 | 기후위기_09_경기.pdf (140p) | 대상 포함 여부 확인 필요 |

---

## PR 머지 대기 브랜치

| 브랜치 | 포함 기관 | 상태 |
|--------|----------|------|
| `feat/codex/embrain-parser` | 엠브레인퍼블릭 4건 | PR 작성 대기 |
| `feat/codex/kr-signal-parsers` | 한국리서치 2건, 시그널앤펄스 3건 + 검증 테스트 인프라 | PR 작성 대기 |

---

## 다음 단계

1. **즉시**: PR 두 개 작성 및 머지 (`embrain-parser`, `kr-signal-parsers`)
2. **단기**: 미개발 기관 순차 파서 개발
   - **1순위**: 윈지코리아컨설팅, 케이스탯리서치 (각 2건 — 기존 파서 적용 가능 여부 먼저 탐색)
   - **2순위**: 넥스트리서치, 에스티아이, 입소스, 한길리서치 (각 1건)
   - **별도**: 여론조사꽃 (cid 인코딩 문제 선결 필요, pymupdf 시도)
3. **보류 해제**: 기후위기 인식조사 대상 포함 여부 확인 후 결정
4. **이후**: 전체 파싱 완료 후 DB 적재 모듈 개발
