# PDF 파서 개발 현황

> 대상: 제9회 전국동시지방선거 경기도 광역단체장선거 여론조사 PDF (총 31건, 14개 조사기관 + 특수 1건)
> 기준일: 2026-04-03

---

## 개발 현황 요약

| 상태 | 기관 수 | PDF 건수 |
|------|---------|---------|
| ✅ 완료 (픽스처 검증까지) | 5 | 15 |
| ✅ 완료 (PR 머지됨) | 2 | 7 |
| 🚧 완료 (현재 브랜치, PR 대기) | 1 | 3 |
| ❌ 미개발 | 6 | 8 |
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

### ✅ 파서 완료 — PR 머지됨, 2개 기관, 7건

| 조사기관 | PDF 파일명 | 파서 | PR |
|---------|-----------|------|----|
| ㈜엠브레인퍼블릭 | [뉴스1 신년특집] 경기도민 여론조사 통계표_최종.pdf | `_EmbrainPublicParser` | #23 |
| ㈜엠브레인퍼블릭 | [중부일보] 경기도민 여론조사 통계표_최종.pdf | `_EmbrainPublicParser` | #23 |
| ㈜엠브레인퍼블릭 | [중부일보] 경기도민 여론조사 통계표_최종_2월 3주.pdf | `_EmbrainPublicParser` | #23 |
| ㈜엠브레인퍼블릭 | [중부일보] 경기도민 여론조사 통계표_최종_3월 4주.pdf | `_EmbrainPublicParser` | #23 |
| (주)한국리서치 | (경인일보)지방선거 경기도민 여론조사_결과표_2월 22일 보도용.pdf | `_KoreanResearchParser` | #24 |
| (주)한국리서치 | (경인일보)지방선거 경기도민 여론조사_결과표_2월 23일 보도용.pdf | `_KoreanResearchParser` | #24 |
| (주)시그널앤펄스 | 보도용_경기도 여론조사 보고서_프레시안_260212.pdf | `_SignalPulseParser` | #24 |
| (주)시그널앤펄스 | 보도용_경기도 여론조사 보고서_프레시안_251230(수정).pdf | `_SignalPulseParser` | #24 |
| (주)시그널앤펄스 | 보도용_경기도 여론조사 보고서_서울의소리_251215.pdf | `_SignalPulseParser` | #24 |

### 🚧 파서 완료 — 현재 브랜치 (PR 대기), 1개 기관, 3건

| 조사기관 | PDF 파일명 | 파서 | 브랜치 |
|---------|-----------|------|--------|
| (주)여론조사꽃 | 결과표_20260211_여론조사꽃_경기지사 2000_CATI조사_v01.pdf | `_FlowerResearchParser` | feat/parser-diagnosis/claude |
| (주)여론조사꽃 | 결과표_20260326_여론조사꽃_경기도지사 2000_CATI조사_v01.pdf | `_FlowerResearchParser` | feat/parser-diagnosis/claude |
| (주)여론조사꽃 | 결과표_20260317_여론조사꽃_경기도지사 1000_ARS조사_v01.pdf | `_FlowerResearchParser` | feat/parser-diagnosis/claude |

> **기술 노트**: NotoSansCJKkr Identity-H 인코딩 문제 해결 — fonttools로 GID→Unicode 역맵핑, PyMuPDF rawdict 모드로 추출

### ❌ 파서 미개발 — 6개 기관, 8건

> 스크리닝 결과: `output/polls/screening/{기관명}/` — 상세 포맷 정보 및 도전 과제 참고

| 조사기관 | PDF 파일명 | 질문마커 | 전체행마커 | 비율위치 | 주요 도전 과제 |
|---------|-----------|---------|-----------|---------|-------------|
| (주)케이스탯리서치 | (결과표) KBS 지방선거 여론조사 [03. 경기].pdf | `N)` | `전 체` | text_bundled | 멀티페이지 merge 필요 |
| (주)케이스탯리서치 | 지방선거 관련 여론조사(경기)_한글통계표(12.31).pdf | 탐지 안 됨 | `계` | text_bundled | 질문 마커 수동 확인 필요 |
| (주)윈지코리아컨설팅 | 250915_보고서_드림투데이(경기)_v2.pdf | `QN.` | `전 체` | mixed+뭉침 | 비율 셀 분리 + 멀티페이지 merge |
| (주)윈지코리아컨설팅 | 260305_공표용보고서_경기도_정치지형조사_v2.pdf | `QN.` | `전체` | mixed+뭉침 | 비율 셀 분리 필요 |
| 넥스트리서치 | (넥스트리서치_조사결과_등록_0319) 제9회 전국동시지방선거관련 경기지역 여론조사.pdf | `N.` | `계` | mixed+뭉침 | 비율 셀 분리 필요 |
| ㈜에스티아이 | 통계표_에스티아이_경기도지사 선거 여론조사 0219.pdf | `QN.` | `계` | mixed+뭉침 | 비율 셀 분리 + 멀티페이지 merge |
| 입소스 주식회사 | (통계표) SBS 2026 설 특집 여론조사_경기.pdf | `문N.` | `전 체` | text_bundled | 멀티페이지 merge 필요 |
| (주)한길리서치 | 결과분석_한길리서치1019.pdf | `문N)` | `합계` | mixed+뭉침 | 비율 셀 분리 필요 |

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
├── _SignalPulseParser        # 시그널앤펄스 — [표N]/[QN] 두 버전 분기 처리
└── _FlowerResearchParser     # 여론조사꽃 — GID→Unicode 역맵핑, rawdict 추출, ① 합산행 건너뜀
```

### 파서 선택 로직 (`parser_registry.json`)

1. **pollster_names**: 기관명 키워드 매칭 (각 파서에 명시)
2. **fallback_parser**: `_TextFormatParser` (기관명 미매칭 시)

---

## 알려진 이슈

| 이슈 | 대상 | 상태 |
|------|------|------|
| ~~cid: 인코딩 — 텍스트 추출 불가~~ | 여론조사꽃 3건 | ✅ 해결 — fonttools GID→Unicode 역맵핑으로 처리 |
| 기후위기 인식조사 선거 관련성 불명확 | 기후위기_09_경기.pdf (140p) | 대상 포함 여부 확인 필요 |

---

## 머지 완료 브랜치

| 브랜치 | 포함 기관 | PR |
|--------|----------|----|
| `feat/codex/embrain-parser` | 엠브레인퍼블릭 4건 | #23 ✅ |
| `feat/codex/kr-signal-parsers` | 한국리서치 2건, 시그널앤펄스 3건 + 검증 테스트 인프라 | #24 ✅ |

---

## 다음 단계

1. ~~**즉시**: PR 두 개 작성 및 머지 (`embrain-parser`, `kr-signal-parsers`)~~ ✅ PR #23, #24 머지 완료
2. ~~**별도**: 여론조사꽃 (cid 인코딩 문제 선결 필요)~~ ✅ `_FlowerResearchParser` 개발 완료 (현재 브랜치)
3. **즉시**: 여론조사꽃 파서 PR 작성 및 머지 (`feat/parser-diagnosis/claude`)
4. **단기**: 미개발 기관 순차 파서 개발 (스크리닝 결과 기반, 기관마다 새 파서 작성)
   - 각 기관 스크리닝 JSON: `output/polls/screening/{기관명}/` 참고
   - **1순위**: 한길리서치, 넥스트리서치, 에스티아이 (비율 뭉침 패턴 유사 — 파서 개발 가이드 참고)
   - **2순위**: 윈지코리아컨설팅 (2건, 멀티페이지 merge 추가 필요)
   - **3순위**: 케이스탯리서치 (2건, 질문 마커 수동 확인 필요), 입소스 (text_bundled 패턴)
5. **보류 해제**: 기후위기 인식조사 대상 포함 여부 확인 후 결정
6. **이후**: 전체 파싱 완료 후 DB 적재 모듈 개발
