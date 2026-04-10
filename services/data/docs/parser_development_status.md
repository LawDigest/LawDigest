# PDF 파서 개발 현황

> 대상: 제9회 전국동시지방선거 전국 전체 지역 여론조사 PDF (총 1,313건, 46개 조사기관)
> 기준일: 2026-04-11
> 원본 데이터: `output/polls/lists/all_regions_9th.json` | 커버리지: `output/polls/coverage/coverage_report.json`

---

## 개발 현황 요약

| 상태 | 기관 수 | PDF 건수 | 비율 |
|------|---------|---------|------|
| ✅ 파서 대응 완료 | 46 | 1,317 | 100.0% |
| ⚠️ 결과보고서 미공개 (파서 있음, 데이터 없음) | 1 | 3 | 0.2% |
| ⛔ 구조적 파싱 불가 | 0 | 0 | 0.0% |
| **합계** | **46** | **1,317** | |

---

## 1. 파서 대응 완료 (46개 기관, 1,317건)

| 조사기관 | 파서 클래스 | 건수 | 주요 지역 | 기술 특이사항 |
|---------|-----------|------|----------|-------------|
| 조원씨앤아이 | `_TableFormatParser` | 138 | 전국 광역 | 표준 크로스탭, `META_COLS=3`, 마지막 `계` 컬럼 제외 |
| 메타보이스(주) | `_TableFormatParser` | 25 | 전국 광역 | `_TableFormatParser` 별칭 공유 |
| 주)메타서치 / (주)메타서치 | `_TableFormatParser` | 3 | 경기, 충남 | `_TableFormatParser` 별칭 공유 |
| (주)리얼미터 | `_RealMeterParser` | 108 | 전국 광역 | 헤더 선택지 + 텍스트 전체 비율 혼합, col2에 (N완료)(N가중) 쌍 |
| (주)코리아정보리서치 | `_KIRParser` | 86 | 전국 광역·기초 | `%` 포함 셀, 가중값 컬럼 위치 동적 감지 (포맷A/B) |
| (주)데일리리서치 | `_DailyResearchParser` | 81 | 전국 광역 | `META_COLS=4`, 가중값 통계표(배율 포함) 자동 스킵 |
| (주)여론조사꽃 | `_FlowerResearchParser` | 76 | 전국 광역 | NotoSansKR Identity-H GID 디코딩, col3 뭉침 비율 |
| (주)한국리서치 | `_KoreanResearchParser` | 58 | 전국 광역 | `[표N]` 제목, `▣ 전체 ▣` 마커, colspan 해제, 멀티페이지 merge |
| (주)코리아리서치인터내셔널 | `_KoreaResearchInternationalParser` | 58 | 광주, 서울, 전국, 전남, 전북, 제주 외 3개 | ASCII-art 텍스트 표 복원, 2-line total row, words x좌표 fallback, 요약 컬럼(T2/B2/종합결과) 제거 |
| 한길리서치 | `_HangilResearchParser` | 51 | 전국 광역·기초 | `문N)` 질문 마커, `header[0][2]=='합계'` 테이블 식별, col4+ 개별 셀 |
| 케이에스오아이 주식회사(한국사회여론연구소) | `_KSOIParser` | 35 | 전국 광역 | `[ 제목 ]` 질문 마커, row[2]='전체', 질문당 2페이지 중복 제거 |
| 여론조사공정(주) | `_FairPollParser` | 34 | 전국 광역·기초 | `【 표 N 】` 질문 마커, tables[0]=헤더/tables[1]=데이터, 2페이지 중복 제거 |
| 윈지코리아컨설팅 | `_WinjiKoreaParser` | 33 | 전국 광역 | 포맷 A(개별 셀) / 포맷 B(뭉침 비율) 자동 감지 |
| 케이스탯리서치 | `_KStatResearchParser` | 31 | 전국 광역 | KBS 포맷(`전 체`+테이블) / 12.31 포맷(`▩전체▩`+fitz 헤더) 분기 |
| (주)케이스탯컨설팅 | `_KStatResearchParser` | 1 | 전국 | `_KStatResearchParser` 별칭 공유 |
| (주)엠브레인퍼블릭 | `_EmbrainPublicParser` | 28 | 전국 광역 | `[표N]` 제목, `■ 전체 ■` 마커, `META_COLS=4`, `row[1]`에 선택지 |
| (주)시그널앤펄스 | `_SignalPulseParser` | 21 | 전국 광역 | `[표N]` / `[QN]` 두 버전 분기 |
| KOPRA(한국여론평판연구소) | `_KopraParser` | 20 | 전국 광역 | `N. 제목` 섹션 마커, `▣ 전체 ▣` 마커, col5+ 정수 비율 |
| 미디어토마토 | `_MediaTomatoParser` | 17 | 전국 광역 | `교차표N_제목` 질문 마커, 전체 행 텍스트 추출 |
| (주)에이스리서치 | `_AceResearchParser` | 15 | 전국 광역 | `<표N>` 질문 마커, `■ 전  체 ■` 마커, col4+ 개별 셀 |
| (주)에스티아이 | `_STIParser` | 10 | 전국 광역 | `QN.` 질문 마커, `전 체` 마커, col4+ 개별 셀, 멀티페이지 중복 방지 |
| (주)리서치앤리서치 | `_ResearchAndResearchParser` | 8 | 전국 광역 | `표 ... N 【】` 제목, `전체` 행, col4+ 개별 셀 |
| 입소스 주식회사 | `_IpsosParser` | 8 | 전국 | `NEEDS_FITZ_WORDS=True`, x좌표 컬럼 분리, 멀티페이지 merge |
| 한국갤럽조사연구소 | `_GallupParser` | 73 | 강원, 경기, 경남, 광주 외 4개 | 통계표/결과집계표(`표 N. 제목`, `■ 전      체 ■`) + 결과분석 데일리(text_bundled) 두 포맷 자동 감지 |
| (주)한국갤럽조사연구소 | `_GallupParser` | 1 | 경남 | `_GallupParser` 별칭 공유 (별개 법인 여부 무관하게 동일 포맷) |
| 넥스트리서치 | `_NextResearchParser` | 2 | 경기도 | `■ 표N.` 질문 마커, `[전체]` 마커, col4+ 개별 셀 |
| (주)이너텍시스템즈 | `_InnertecParser` | 54 | 강원, 경기, 경남, 경북 외 5개 | 챕터 4(교차분석통계표) 전용, 3행 heading 테이블, `N. 제목` 마커, `합 계` 전체 행, col3~N-2 비율 |
| (주)리서치뷰 | `_ResearchViewParser` | 46 | 경기, 광주, 서울, 전국 외 3개 | 1질문 1페이지 1테이블, `N. 제목(%)` 마커, row[2][0]='전 체', col4+ 선택지 비율 |
| 모노커뮤니케이션즈(모노리서치) | `_MonoCommunicationsParser` | 38 | 경기, 경남, 경북, 서울 외 2개 | `[QN – 제목상세결과]` 마커, row[1][0]=None 크로스탭, 완료/가중/비율 동적 위치 |
| (주)비전코리아 | `_VisionKoreaParser` | 34 | 강원, 경기, 경남, 경북 외 6개 | 챕터 감지, `QN. 제목`+`Base=전체` 크로스탭, `750\n.`→75.0% 비율 포맷, ★컬럼 필터링 |
| (주)에브리리서치 | `_EveryResearchParser` | 31 | 경기, 경북, 대구, 서울 외 1개 | `\nQN\n` 마커+다음 페이지 크로스탭, row[0][0]='구분', ①②③ 원문자 마커 제거 |
| (주)알앤써치 | `_RNRParser` | 23 | 경기, 경남, 경북, 광주 외 5개 | `표N. 제목` 마커, row[0][0]=None/row[1][4+]='%'/row[2][0]='전체', 연속 페이지 자동 스킵 |
| 리서치웰 | `_ResearchwelParser` | 14 | 경북, 대구, 전국, 충남 | `【표N[-N]?】 제목` 마커, row[1][0]='전 체', col4+ 비율 |
| 한국정책연구원 | `_KPRIParser` | 12 | 광주, 전남, 전북 | 포맷A(2025: `【표N】`+`전 체`) / 포맷B(2026: `[그림N]`+다음페이지+`%`접미사) 자동 분기 |
| (주)유앤미리서치 | `_UNMParser` | 11 | 강원, 경기, 경남, 전남 외 2개 | `문. 제목` 마커, `전\s*체\s*▣` 동적 전체 행 탐색, 순차 질문 번호 |
| KPO리서치 | `_KPOParser` | 11 | 경북, 대구 | `Q\d+\.` 마커, row[0][0]='구분'/row[2][0]='전체', col4+ 비율 |
| (주)디오피니언 | `_DiOpinionParser` | 4 | 경기, 전북 | `[표N] 제목` 마커(대괄호), row[1][0]='전 체', col4+ 비율 |
| 미디어리서치 | `_MediaResearchParser` | 1 | 전북 | `(문 N) 제목` 마커, `■ 전체 ■` 동적 전체 행, col4+ 비율 |
| (주)우리리서치 | `_UriResearchParser` | 1 | 광주 | `표N. 제목` 마커, row[1][0]='전 체', col4+ 비율 |
| (주)경남통계리서치 | `_GyeongnamStatParser` | 2 | 경남 | `[ N. ] 질문)` 이중 마커, row[2][0]='전체', col4+ 비율 |
| (주)아이소프트뱅크 | `_ISoftBankParser` | 1 | 경남 | Q페이지+교차분석표 교대 구조, '교차분석표' 텍스트 감지, row[1][2]=N, row[0][4:]=선택지 |
| 서던포스트 | `_SouthernPostParser` | 2 | 경남, 부산 | `N. 제목 <표M>` 마커, 두 번째 테이블 데이터, `◈ 전 체 ◈` 전체 행, 마지막 가중값 컬럼 제외 |
| 주식회사 한민리서치 | `_HanMinParser` | 2 | 전국, 충남 | 그래프 페이지 1행 테이블 `option\n%` 셀, `[n=N]` 텍스트 사례수, 순차 질문 번호 |
| (주)피앰아이 | `_PMIParser` | 2 | 전국 | 포맷A(BASE:ALL)+포맷B(사례수행) 자동 감지, `▣ 전 체 ▣` 마커, Top/Bottom 소계 필터 |
| 리서치제이 | `_ResearchJParser` | 3 | 서울, 전남, 충북 | Q/데이터 교대 페이지, row[2]='전체', D/D-1/D+1 헤더 탐색. nttId=18088은 결과보고서 미공개(설문지만 존재) |

---

## 2. 결과보고서 미공개 (1개 기관, 3건)

> 파서는 등록되어 있으나, NESDC에서 결과보고서 PDF를 제공하지 않아 실제 데이터 추출 불가.

| 조사기관 | 건수 | 주요 지역 | 사유 |
|---------|------|----------|------|
| 리서치제이 | 3 | 서울(1), 전남(1), 충북(1) | nttId=18088(괴산군)은 설문지 PDF만 공개됨. nttId=17606·17221은 결과보고서 파싱 가능(파서 정상 동작). 전체 3건 중 1건 데이터 없음 |

---

## 3. 구조적 파싱 불가 (0개 기관, 0건)

현재 구조적 파싱 불가로 분류된 기관은 없다.

---

## 4. 지역별 커버리지

| 지역 | 전체 | 대응 | 미개발 | 불가 | 커버율 |
|------|------|------|--------|------|--------|
| 대전광역시 | 20 | 20 | 0 | 0 | 100.0% |
| 세종특별자치시 | 13 | 13 | 0 | 0 | 100.0% |
| 울산광역시 | 9 | 9 | 0 | 0 | 100.0% |
| 서울특별시 | 60 | 53 | 5 | 2 | 88.3% |
| 인천광역시 | 16 | 14 | 2 | 0 | 87.5% |
| 제주특별자치도 | 20 | 17 | 1 | 2 | 85.0% |
| 충청남도 | 49 | 41 | 7 | 1 | 83.7% |
| 경기도 | 185 | 152 | 33 | 0 | 82.2% |
| 부산광역시 | 38 | 30 | 8 | 0 | 78.9% |
| 전라북도 | 4 | 3 | 0 | 1 | 75.0% |
| 강원특별자치도 | 38 | 27 | 11 | 0 | 71.1% |
| 전국 | 163 | 110 | 48 | 5 | 67.5% |
| 경상남도 | 56 | 38 | 18 | 0 | 67.9% |
| 전북특별자치도 | 172 | 118 | 17 | 37 | 68.6% |
| 충청북도 | 27 | 18 | 8 | 1 | 66.7% |
| 전라남도 | 196 | 109 | 82 | 5 | 55.6% |
| 경상북도 | 144 | 69 | 75 | 0 | 47.9% |
| 광주광역시 | 62 | 30 | 28 | 4 | 48.4% |
| 대구광역시 | 41 | 18 | 23 | 0 | 43.9% |

> **전남·경북·광주·대구 커버율이 낮은 이유**: 한국갤럽·이너텍시스템즈·비전코리아·에브리리서치 등 아직 파서가 없는 기관들이 해당 지역에 집중 등록되어 있기 때문.

---

## 5. 파서 아키텍처 개요

```
PollResultParser
├── _TableFormatParser           ✅ — 조원씨앤아이, 메타보이스, 메타서치
├── _DailyResearchParser         ✅ — 데일리리서치
├── _RealMeterParser             ✅ — 리얼미터
├── _KoreaResearchInternationalParser ✅ — 코리아리서치인터내셔널 (ASCII-art 텍스트 표 + words fallback)
├── _KoreanResearchParser        ✅ — 한국리서치
├── _SignalPulseParser           ✅ — 시그널앤펄스
├── _EmbrainPublicParser         ✅ — 엠브레인퍼블릭
├── _FlowerResearchParser        ✅ — 여론조사꽃 (GID 디코딩)
├── _WinjiKoreaParser            ✅ — 윈지코리아컨설팅
├── _ResearchAndResearchParser   ✅ — 리서치앤리서치
├── _HangilResearchParser        ✅ — 한길리서치
├── _NextResearchParser          ✅ — 넥스트리서치
├── _STIParser                   ✅ — 에스티아이
├── _IpsosParser                 ✅ — 입소스 (NEEDS_FITZ_WORDS)
├── _KStatResearchParser         ✅ — 케이스탯리서치, 케이스탯컨설팅
├── _AceResearchParser           ✅ — 에이스리서치
├── _KopraParser                 ✅ — KOPRA
├── _MediaTomatoParser           ✅ — 미디어토마토
├── _KSOIParser                  ✅ — 케이에스오아이(한국사회여론연구소)
├── _FairPollParser              ✅ — 여론조사공정(주)
├── _KIRParser                   ✅ — 코리아정보리서치
├── _GallupParser                ✅ — 한국갤럽조사연구소 (통계표+데일리 두 포맷)
├── _InnertecParser              ✅ — 이너텍시스템즈 (챕터 4 전용)
├── _ResearchViewParser          ✅ — 리서치뷰 (1질문 1페이지)
├── _MonoCommunicationsParser    ✅ — 모노커뮤니케이션즈
├── _VisionKoreaParser           ✅ — 비전코리아 (조사결과집계표 챕터)
├── _EveryResearchParser         ✅ — 에브리리서치 (Q크로스페이지)
├── _RNRParser                   ✅ — 알앤써치
├── _ResearchwelParser           ✅ — 리서치웰
├── _KPRIParser                  ✅ — 한국정책연구원 (2025/2026 포맷 분기)
├── _UNMParser                   ✅ — 유앤미리서치
├── _KPOParser                   ✅ — KPO리서치
├── _DiOpinionParser             ✅ — 디오피니언
├── _MediaResearchParser         ✅ — 미디어리서치
├── _UriResearchParser           ✅ — 우리리서치
├── _GyeongnamStatParser         ✅ — 경남통계리서치
├── _ISoftBankParser             ✅ — 아이소프트뱅크 (Q/교차분석표 교대 페이지)
├── _SouthernPostParser          ✅ — 서던포스트 (N.제목<표M> 마커, ◈전체◈ 행)
├── _HanMinParser                ✅ — 한민리서치 (그래프 1행 테이블, [n=N] 텍스트)
├── _PMIParser                   ✅ — 피앰아이 (포맷A/B 자동 감지, Top/Bottom 필터)
└── _ResearchJParser             ✅ — 리서치제이 (Q/데이터 교대 페이지, row[2]=전체, D/D±1 헤더 탐색)
```

### 공통 인프라 (`table_utils.py` + `parser.py`)

| 함수 | 역할 |
|------|------|
| `_unmerge_table(fitz_table, page)` | colspan 병합 셀 해제 |
| `find_total_row(table, markers, ...)` | 전체 행 탐지 (7종 변형 마커 지원) |
| `extract_percentages_from_cells(row, ...)` | 개별 셀 비율 추출 (순수 숫자만. `%` 포함 셀 주의) |
| `extract_percentages_from_bunched_cell(text, ...)` | 뭉침 셀 비율 파싱 |
| `extract_sample_count(text)` | `(1,007)` 등 사례수 추출 |
| `filter_summary_columns(opts, pcts, ...)` | `(합)`, `합계`, `T1/B2` 등 소계 컬럼 제거 |

---

## 6. 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-04-11 | `_KoreaResearchInternationalParser` 추가 — `(주)코리아리서치인터내셔널` 58건 대응 완료. `find_tables()` 미인식 ASCII-art 통계표를 텍스트 표 복원 + words fallback으로 처리. **커버리지 100.0%, 구조적 파싱 불가 0건** |
| 2026-04-10 | `_ResearchJParser` 추가 — 리서치제이 3건. NESDC HTML에서 파라미터를 파싱해 PDF 다운로드 성공. nttId=18088은 설문지 전용이라 데이터 없음. **커버리지 95.6%, 파서 미개발 0건** |
| 2026-04-10 | `_ISoftBankParser`·`_SouthernPostParser`·`_HanMinParser`·`_PMIParser` 추가 — 아이소프트뱅크·서던포스트·한민리서치·피앰아이 총 7건. 리서치제이(3건)는 NESDC PDF 비공개로 개발 불가. **커버리지 95.4%** |
| 2026-04-10 | `_MediaResearchParser`·`_UriResearchParser`·`_GyeongnamStatParser` 추가 — 미디어리서치·우리리서치·경남통계리서치 총 4건. **커버리지 94.8%** |
| 2026-04-10 | `_KPOParser`·`_KPRIParser`·`_UNMParser`·`_DiOpinionParser` 추가 — KPO리서치·한국정책연구원·유앤미리서치·디오피니언 총 38건 |
| 2026-04-10 | `_ResearchwelParser`·`_RNRParser`·`_EveryResearchParser`·`_VisionKoreaParser`·`_MonoCommunicationsParser`·`_ResearchViewParser`·`_InnertecParser` 추가 — 7개 기관 246건 |
| 2026-04-10 | `_GallupParser` 추가 — 한국갤럽조사연구소 73건 + (주)한국갤럽조사연구소 1건. 통계표/결과집계표·결과분석 데일리 두 포맷 통합 처리 |
| 2026-04-10 | 전국 기준으로 문서 전면 개정. 기준 데이터: `all_regions_9th.json` 1,313건, 46개 기관 |
| 2026-04-10 | `_KIRParser` 추가 — (주)코리아정보리서치 86건 대응 |
| 2026-04-05 | 경기도 기준 초판 작성 (13개 기관, 30건) |
