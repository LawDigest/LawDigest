# PDF 파서 개발 현황

> 대상: 제9회 전국동시지방선거 경기도 광역단체장선거 여론조사 PDF (총 31건, 14개 조사기관 + 특수 1건)
> 기준일: 2026-04-05

---

## 개발 현황 요약

| 상태 | 기관 수 | PDF 건수 |
|------|---------|---------|
| ✅ 완료 — 픽스처 검증까지 | 11 | 28 |
| ❌ 미개발 | 2 | 2 |
| ❓ 보류 (선거 관련성 불명) | — | 1 |
| **합계** | — | **31** |

---

## 1. 대응 완료 — 파서 (11개 기관, 28건)

> 대부분 `_unmerge_table` + `table_utils` 기반. colspan 병합 셀 자동 해제.
> 입소스·케이스탯리서치는 PyMuPDF 텍스트/words 기반 (테이블 미감지 포맷).

| 조사기관 | 파서 | PDF 건수 | 브랜치 / PR | 기술 특이사항 |
|---------|------|---------|------------|-------------|
| 조원씨앤아이 | `_TableFormatParser` | 7 | main | 표준 크로스탭, `META_COLS=3`, 마지막 `계` 컬럼 제외 |
| ㈜데일리리서치 | `_DailyResearchParser` | 1 | main | `META_COLS=4`, 가중값 통계표(배율 포함) 자동 스킵 |
| ㈜엠브레인퍼블릭 | `_EmbrainPublicParser` | 4 | main (PR #23) | `[표N]` 제목, `■ 전체 ■` 마커, `META_COLS=4`, `row[1]`에 선택지 |
| ㈜한국리서치 | `_KoreanResearchParser` | 2 | main (PR #24) + 현재 브랜치 재작성 | `[표N]` 제목, `▣ 전체 ▣` 마커, colspan 해제 후 개별 셀 추출, 멀티페이지 merge |
| ㈜시그널앤펄스 | `_SignalPulseParser` | 3 | main (PR #24) | `[표N]` / `[QN]` 두 버전 분기, `[표N]`은 테이블 기반, `[QN]`은 `합계` 행 |
| ㈜여론조사꽃 | `_FlowerResearchParser` | 3 | `feat/parser-diagnosis/claude` (PR 대기) | NotoSansKR Identity-H GID 디코딩 필요, col3에 뭉침 비율, `bunched_cell` 추출 |
| ㈜윈지코리아컨설팅 | `_WinjiKoreaParser` | 2 | 현재 브랜치 (PR 대기) | 포맷 A(개별 셀, 8열+), 포맷 B(뭉침 비율, 5열) 자동 감지 |
| ㈜한길리서치 | `_HangilResearchParser` | 1 | `feat/parser-hangil-realmeter-migration/claude` (PR 대기) | `문N)` 질문 마커, `header[0][2]=='합계'` 테이블 식별, col4+ 개별 셀 비율 |
| ㈜리얼미터 | `_RealMeterParser` | 2 | main | 테이블 헤더 선택지 + 텍스트 전체 비율 혼합 방식, `find_total_row` + `extract_percentages_from_cells` 전환 완료 |
| 입소스 주식회사 | `_IpsosParser` | 1 | main (PR #30) | fitz 테이블 0개, `NEEDS_FITZ_WORDS=True`로 `get_text("words")` 활용, x좌표 컬럼 그룹화, `*없음/모름/무응답*` 합산 컬럼 자동 감지, 멀티페이지 merge |
| ㈜케이스탯리서치 | `_KStatResearchParser` | 2 | main (PR #30) | KBS 포맷: `전 체` 마커+테이블, 12.31 포맷: `▩전체▩` 마커+fitz 테이블 헤더에서 선택지 직접 추출 |

<details>
<summary>PDF 파일 목록</summary>

| 조사기관 | PDF 파일명 |
|---------|-----------|
| 조원씨앤아이 | 더팩트_경기도 지선 여론조사 보고서_250930.pdf |
| 조원씨앤아이 | 더팩트 경기교육신문_경기도 지선 여론조사 보고서_251027.pdf |
| 조원씨앤아이 | 경기일보_경기 지선 여론조사 보고서_251201(1).pdf |
| 조원씨앤아이 | 경기일보_경기 지선 여론조사 보고서_260105.pdf |
| 조원씨앤아이 | 경기일보_경기 지선 여론조사 보고서_260202_수정.pdf |
| 조원씨앤아이 | 경기일보_경기 지선 여론조사 보고서_260224.pdf |
| 조원씨앤아이 | 프레시안_경기 지선 여론조사 보고서_260318_f.pdf |
| ㈜데일리리서치 | 등록_경기도_결과분석_데일리리서치2510011.pdf |
| ㈜엠브레인퍼블릭 | [뉴스1 신년특집] 경기도민 여론조사 통계표_최종.pdf |
| ㈜엠브레인퍼블릭 | [중부일보] 경기도민 여론조사 통계표_최종.pdf |
| ㈜엠브레인퍼블릭 | [중부일보] 경기도민 여론조사 통계표_최종_2월 3주.pdf |
| ㈜엠브레인퍼블릭 | [중부일보] 경기도민 여론조사 통계표_최종_3월 4주.pdf |
| ㈜한국리서치 | (경인일보)지방선거 경기도민 여론조사_결과표_2월 22일 보도용.pdf |
| ㈜한국리서치 | (경인일보)지방선거 경기도민 여론조사_결과표_2월 23일 보도용.pdf |
| ㈜시그널앤펄스 | 보도용_경기도 여론조사 보고서_프레시안_260212.pdf |
| ㈜시그널앤펄스 | 보도용_경기도 여론조사 보고서_프레시안_251230(수정).pdf |
| ㈜시그널앤펄스 | 보도용_경기도 여론조사 보고서_서울의소리_251215.pdf |
| ㈜여론조사꽃 | 결과표_20260211_여론조사꽃_경기지사 2000_CATI조사_v01.pdf |
| ㈜여론조사꽃 | 결과표_20260326_여론조사꽃_경기도지사 2000_CATI조사_v01.pdf |
| ㈜여론조사꽃 | 결과표_20260317_여론조사꽃_경기도지사 1000_ARS조사_v01.pdf |
| ㈜윈지코리아컨설팅 | 260305_공표용보고서_경기도_정치지형조사_v2.pdf |
| ㈜윈지코리아컨설팅 | 250915_보고서_드림투데이(경기)_v2.pdf |
| 입소스 주식회사 | (통계표) SBS 2026 설 특집 여론조사_경기.pdf |
| ㈜케이스탯리서치 | (결과표) KBS 지방선거 여론조사 [03. 경기].pdf |
| ㈜케이스탯리서치 | 지방선거 관련 여론조사(경기)_한글통계표(12.31).pdf |

</details>

---

## 2. 마이그레이션 완료 — ✅ 리얼미터 테이블 기반 전환

> 리얼미터 파서는 위의 `대응 완료 — 파서` 섹션으로 이동했다.

**완료 내용**:
- `_TOTAL_ROW_RE` 제거, `_N_PAIR_RE`로 col2 내 `(N완료) (N가중)` 두 값 파싱
- `_extract_from_tables()` 메서드로 테이블 전체 행 기반 비율 추출
- `_SignalPulseParser._TOTAL_TEXT_RE` dead code 제거

---

## 3. 미개발 파서 (2개 기관, 2건)

> 스크리닝 결과: `output/polls/screening/{기관명}/` — 상세 포맷 정보 및 도전 과제 참고

| 조사기관 | PDF 건수 | 질문마커 | 전체행마커 | 비율위치 | 주요 도전 과제 | 우선순위 |
|---------|---------|---------|-----------|---------|-------------|--------|
| 넥스트리서치 | 1 | `N.` | `계` | mixed+뭉침 | 비율 뭉침 셀 분리 | 1 |
| ㈜에스티아이 | 1 | `QN.` | `계` | mixed+뭉침 | 비율 뭉침 셀 분리 + 멀티페이지 merge | 2 |

**우선순위 근거**:
- **1순위** (넥스트리서치): `extract_percentages_from_bunched_cell` 패턴 동일, 파서 가이드 예시 코드 바로 적용 가능
- **2순위** (에스티아이): 비율 뭉침 셀 분리 + 멀티페이지 merge 필요

<details>
<summary>PDF 파일 목록</summary>

| 조사기관 | PDF 파일명 |
|---------|-----------|
| 넥스트리서치 | (넥스트리서치_조사결과_등록_0319) 제9회 전국동시지방선거관련 경기지역 여론조사.pdf |
| ㈜에스티아이 | 통계표_에스티아이_경기도지사 선거 여론조사 0219.pdf |

</details>

---

## ❓ 보류 — 1건

| 파일명 | 사유 |
|--------|------|
| 2026 기후위기 국민 인식조사_09_경기_TABLE_등록_0306.pdf | 경기도지사 선거 여론조사 아님 (기후위기 인식조사, 140페이지) — 대상 포함 여부 확인 필요 |

---

## 파서 아키텍처

```
PollResultParser
├── _TableFormatParser        ✅ 테이블 — 조원씨앤아이: 표준 크로스탭
├── _DailyResearchParser      ✅ 테이블 — 데일리리서치: META_COLS=4, 가중값 표 스킵
├── _EmbrainPublicParser      ✅ 테이블 — 엠브레인퍼블릭: [표N], row[1] 선택지
├── _KoreanResearchParser     ✅ 테이블 — 한국리서치: [표N], colspan 해제, 멀티페이지
├── _SignalPulseParser        ✅ 테이블 — 시그널앤펄스: [표N]/[QN] 분기
├── _FlowerResearchParser     ✅ 테이블 — 여론조사꽃: GID 디코딩 + 뭉침 비율
├── _WinjiKoreaParser         ✅ 테이블 — 윈지코리아: A/B 포맷 자동 감지
├── _RealMeterParser          ✅ 테이블 — 리얼미터: col4+ 개별 셀, col2에 (N완료)(N가중) 쌍
├── _HangilResearchParser     ✅ 테이블 — 한길리서치: header[0][2]=='합계' 식별, col4+ 개별 셀
├── _IpsosParser              ✅ fitz words — 입소스: NEEDS_FITZ_WORDS, x좌표 컬럼 분리, 멀티페이지 merge
└── _KStatResearchParser      ✅ 혼합 — 케이스탯리서치: KBS(전 체+테이블) / 12.31(▩전체▩+fitz 테이블 헤더) 분기
```

### 공통 인프라 (`table_utils.py` + `parser.py`)

| 함수 | 역할 |
|------|------|
| `_unmerge_table(fitz_table, page)` | colspan 병합 셀 해제 — 숫자 데이터만 재분배 |
| `_infer_col_x_ranges(fitz_table)` | 비병합 행 기준 열 x 경계 추론 |
| `find_total_row(table, markers, ...)` | 전체 행 탐지 (7종 변형 마커 지원) |
| `extract_percentages_from_cells(row, ...)` | 개별 셀에서 비율 리스트 추출 |
| `extract_percentages_from_bunched_cell(text, ...)` | 뭉침 셀 비율 파싱 |
| `extract_sample_count(text)` | `(1,007)` 등 사례수 추출 |
| `extract_options_from_row(row, ...)` | 헤더 행에서 선택지 추출 |
| `filter_summary_columns(opts, pcts, ...)` | `(합)`, `합계`, `T1/B2`, `①+②` 등 소계 컬럼 제거 |

---

## PR / 브랜치 현황

| 브랜치 | 포함 기관 | 상태 |
|--------|----------|----|
| `main` | 조원씨앤아이, 데일리리서치, 리얼미터, 엠브레인퍼블릭(#23), 한국리서치(#24), 시그널앤펄스(#24) | ✅ 머지됨 |
| `feat/parser-diagnosis/claude` | 여론조사꽃 (3건) | 🚧 PR 대기 |
| `refactor/parser-infra/claude` | 윈지코리아 (2건) + `_unmerge_table` 인프라 + KoreanResearch 테이블 기반 재작성 | 🚧 PR 대기 |
| `feat/parser-hangil-realmeter-migration/claude` | 한길리서치 신규 + 리얼미터 테이블 기반 마이그레이션 | 🚧 PR 대기 |

---

## 이슈 이력

| 이슈 | 대상 | 상태 |
|------|------|------|
| ~~cid: 인코딩 — 텍스트 추출 불가~~ | 여론조사꽃 3건 | ✅ 해결 — fonttools GID→Unicode 역맵핑 |
| ~~colspan 병합 셀 — 비율 추출 불가~~ | 한국리서치, 윈지코리아 | ✅ 해결 — `_unmerge_table` (get_text("words") 기반) |
| 기후위기 인식조사 선거 관련성 불명확 | 기후위기_09_경기.pdf (140p) | ❓ 보류 |

---

## 다음 단계

1. **즉시**: `feat/parser-diagnosis/claude` PR 작성 → 여론조사꽃 머지
2. **즉시**: `refactor/parser-infra/claude` PR 작성 → 윈지코리아 + 인프라 머지
3. **즉시**: `feat/parser-hangil-realmeter-migration/claude` PR 작성 → 한길리서치 + 리얼미터 머지
4. **단기**: 미개발 1순위 파서 개발 (넥스트리서치)
   - `output/polls/screening/{기관명}/` 스크리닝 JSON 참고
   - `extract_percentages_from_bunched_cell` 활용
5. **단기**: 미개발 2순위 파서 개발 (에스티아이)
   - 비율 뭉침 셀 분리 + 멀티페이지 merge 필요
6. **보류 해제**: 기후위기 인식조사 대상 포함 여부 확인 후 결정
