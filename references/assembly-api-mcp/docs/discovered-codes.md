# Discovered API Codes

Verified on 2026-04-04 by downloading official API spec sheets (xlsx) from
`open.assembly.go.kr/portal/data/openapi/downloadOpenApiSpec.do` and testing
each code with a live API key. Every code below returned `INFO-000` (success).

Discovery method: Called the `OPENSRVAPI` meta-endpoint (276 total APIs) to get
`INF_ID` values, then downloaded each API's Excel specification to extract the
actual endpoint code from the "요청주소" (request URL) field.

---

## 1. Schedule (일정)

| API Name | Code | Type | Required Params | Total Count |
|---|---|---|---|---|
| 국회일정 통합 API | `ALLSCHEDULE` | UPPERCASE | (none) | 90,201 |
| 본회의 일정 | `nekcaiymatialqlxr` | 17-char | `UNIT_CD` (대수, e.g. `100022`) | 103 (@22대) |
| 위원회별 일정 | `nrsldhjpaemrmolla` | 17-char | `UNIT_CD` (대수, e.g. `100022`) | 1,554 (@22대) |
| 위원회별 전체회의 일정 | `nttmdfdcaakvibdar` | 17-char | TBD | - |
| 위원회별 소위원회 일정 | `nrkqqbvfanfybishu` | 17-char | TBD | - |
| 위원회별 공청회 일정 | `napvpafracrdkxmoq` | 17-char | TBD | - |
| 전원위원회 일정 | `nomxleneanjcruaez` | 17-char | TBD | - |
| 의사일정공지 | `njlyptmbatwuwjtxf` | 17-char | TBD | - |

**Key parameters for `ALLSCHEDULE`:**
- `SCH_KIND` (선택): 일정종류 (e.g. "국회행사")
- `SCH_DT` (선택): 일자 (e.g. "2024")

**Key parameters for `nekcaiymatialqlxr` (본회의 일정):**
- `UNIT_CD` (필수): 대수코드 (e.g. "100022" = 제22대)
- `MEETINGSESSION` (선택): 회기
- `CHA` (선택): 차수
- `MEETTING_DATE` (선택): 일자 (e.g. "2024-03-15")

**Key parameters for `nrsldhjpaemrmolla` (위원회별 일정):**
- `UNIT_CD` (필수): 대수코드 (e.g. "100022")
- `COMMITTEE_NAME` (선택): 위원회명
- `MEETING_DATE` (선택): 회의일자
- `HR_DEPT_CD` (선택): 위원회코드

**Output fields for `ALLSCHEDULE`:**
`SCH_KIND`, `SCH_CN`, `SCH_DT`, `SCH_TM`, `CONF_DIV`, `CMIT_NM`,
`CONF_SESS`, `CONF_DGR`, `EV_INST_NM`, `EV_PLC`

---

## 2. Meeting Records (회의록)

| API Name | Code | Type | Required Params | Total Count |
|---|---|---|---|---|
| 본회의 회의록 | `nzbyfwhwaoanttzje` | 17-char | `DAE_NUM`, `CONF_DATE` | 661 (@22대, 2024) |
| 위원회 회의록 | `ncwgseseafwbuheph` | 17-char | `DAE_NUM`, `CONF_DATE` | 12,822 (@22대, 2024) |
| 전원위원회 회의록 | `ngytonzwavydlbbha` | 17-char | TBD | - |
| 공청회 회의록 | `VCONFPHCONFLIST` | UPPERCASE | `ERACO` (e.g. "제22대") | 51 (@22대) |
| 소위원회 회의록 | `VCONFSUBCCONFLIST` | UPPERCASE | `ERACO` | - |
| 예결산특별위원회 회의록 | `VCONFBUDGETCONFLIST` | UPPERCASE | `ERACO` | - |
| 특별위원회 회의록 | `VCONFSPCCONFLIST` | UPPERCASE | `ERACO` | - |
| 국정감사 회의록 | `VCONFAPIGCONFLIST` | UPPERCASE | `ERACO` | - |
| 국정조사 회의록 | `VCONFPIPCONFLIST` | UPPERCASE | `ERACO` | - |
| 인사청문회 회의록 | `VCONFCFRMCONFLIST` | UPPERCASE | `ERACO` | - |
| 청문회 회의록 | `VCONFCHCONFLIST` | UPPERCASE | `ERACO` | - |
| 회의록별 상세정보 | `VCONFDETAIL` | UPPERCASE | TBD | - |
| 회의별 안건목록 | `VCONFBLLLIST` | UPPERCASE | TBD | - |
| 회의별 의안목록 | `VCONFBILLLIST` | UPPERCASE | TBD | - |
| 의안별 회의록 목록 | `VCONFBILLCONFLIST` | UPPERCASE | TBD | - |
| 회의록 대별 위원회 목록 | `nkimylolanvseqagq` | 17-char | TBD | - |

**Key parameters for `nzbyfwhwaoanttzje` (본회의 회의록):**
- `DAE_NUM` (필수): 대수 (e.g. "22")
- `CONF_DATE` (필수): 회의날짜 (e.g. "2024")
- `TITLE` (선택): 회의명
- `CLASS_NAME` (선택): 회의종류명
- `SUB_NUM` (선택): 안건번호
- `SUB_NAME` (선택): 안건명

**Output fields:** `CONFER_NUM`, `TITLE`, `CLASS_NAME`, `DAE_NUM`, `CONF_DATE`,
`SUB_NAME`, `VOD_LINK_URL`, `CONF_LINK_URL`, `PDF_LINK_URL`, `CONF_ID`

**Key parameters for `ncwgseseafwbuheph` (위원회 회의록):**
- `DAE_NUM` (필수): 대수 (e.g. "22")
- `CONF_DATE` (필수): 회의날짜 (e.g. "2024")
- `COMM_NAME` (선택): 위원회명
- `DEPT_CD` (선택): 위원회코드

**Output fields:** `CONFER_NUM`, `TITLE`, `CLASS_NAME`, `DAE_NUM`, `COMM_NAME`,
`VODCOMM_CODE`, `CONF_DATE`, `SUB_NAME`, `VOD_LINK_URL`, `CONF_LINK_URL`,
`PDF_LINK_URL`, `PDF_FILE_ID`, `DEPT_CD`, `CONF_ID`

---

## 3. Committees (위원회)

| API Name | Code | Type | Required Params | Total Count |
|---|---|---|---|---|
| 위원회 현황 정보 | `nxrvzonlafugpqjuh` | 17-char | (none) | 356 |
| 위원회 위원 명단 | `nktulghcadyhmiqxi` | 17-char | (none) | 524 |

**Key parameters for `nxrvzonlafugpqjuh` (위원회 현황 정보):**
- `CMT_DIV_NM` (선택): 위원회구분 (e.g. "특별위원")
- `HR_DEPT_CD` (선택): 위원회코드
- `COMMITTEE_NAME` (선택): 위원회명
- `HG_NM` (선택): 위원장
- `HG_NM_LIST` (선택): 간사

**Output fields:** `CMT_DIV_CD`, `CMT_DIV_NM`, `HR_DEPT_CD`, `COMMITTEE_NAME`,
`HG_NM`, `HG_NM_LIST`, `LIMIT_CNT`, `CURR_CNT`, `POLY99_CNT`, `POLY_CNT`

---

## 4. Petitions (청원)

| API Name | Code | Type | Required Params | Total Count |
|---|---|---|---|---|
| 청원 계류현황 | `nvqbafvaajdiqhehi` | 17-char | (none) | 276 |
| 청원 처리현황 | `ncryefyuaflxnqbqo` | 17-char | (none) | - |
| 청원 접수목록 | `PTTRCP` | UPPERCASE | `ERACO` (e.g. "제22대") | 287 (@22대) |
| 청원 상세정보 | `PTTINFODETAIL` | UPPERCASE | `PTT_ID` (필수) | - |
| 청원 소개의원 정보 | `PTTINFOPPSR` | UPPERCASE | TBD | - |
| 청원 심사정보 | `PTTJUDGE` | UPPERCASE | TBD | - |
| 청원 통계 | `PTTCNTMAIN` | UPPERCASE | TBD | - |

**Key parameters for `nvqbafvaajdiqhehi` (청원 계류현황):**
- `BILL_NO` (선택): 청원번호
- `BILL_ID` (선택): 의안ID
- `BILL_NAME` (선택): 청원명
- `PROPOSER` (선택): 청원인
- `APPROVER` (선택): 소개의원
- `CURR_COMMITTEE` (선택): 소관위
- `PASS_GUBUN` (선택): 의안구분

**Output fields:** `BILL_NO`, `BILL_ID`, `AGE`, `BILL_NAME`, `PROPOSER`,
`APPROVER`, `PROPOSE_DT`, `CURR_COMMITTEE_ID`, `CURR_COMMITTEE`,
`COMMITTEE_DT`, `LINK_URL`

**Key parameters for `PTTRCP` (청원 접수목록):**
- `ERACO` (필수): 대수 (e.g. "제22대")

**Output fields:** `CITZN_AGM_CNT`, `ERACO`, `LINK_URL`, `INTD_ASBLM_NM`,
`RCP_DT`, `PTT_ID`, `PTT_NM`, `PTT_NO`, `PTTR_NM`, `PTT_KIND`

---

## 5. Legislation Notices (입법예고)

| API Name | Code | Type | Required Params | Total Count |
|---|---|---|---|---|
| 진행중 입법예고 | `nknalejkafmvgzmpt` | 17-char | (none) | 265 |
| 종료된 입법예고 | `nohgwtzsamojdozky` | 17-char | `AGE` (필수) | 16,565 (@22대) |

**Key parameters for `nknalejkafmvgzmpt` (진행중 입법예고):**
- `BILL_ID` (선택): 의안 ID
- `BILL_NO` (선택): 의안번호
- `BILL_NAME` (선택): 법률안명
- `PROPOSER_KIND_CD` (선택): 제안자구분
- `CURR_COMMITTEE` (선택): 소관위원회
- `NOTI_ED_DT` (선택): 게시종료일

**Output fields:** `BILL_ID`, `BILL_NO`, `BILL_NAME`, `AGE`,
`PROPOSER_KIND_CD`, `CURR_COMMITTEE`, `NOTI_ED_DT`, `LINK_URL`,
`PROPOSER`, `CURR_COMMITTEE_ID`

**Key parameters for `nohgwtzsamojdozky` (종료된 입법예고):**
- `AGE` (필수): 대수 (e.g. "22")
- `BILL_ID`, `BILL_NO`, `BILL_NAME`, `PROPOSER_KIND_CD`,
  `PROPOSER`, `CURR_COMMITTEE`, `CURR_COMMITTEE_ID` (all optional)

---

## 6. Additional Discovered Codes (Bonus)

These codes were also found from spec downloads:

| API Name | Code | Notes |
|---|---|---|
| 인사청문회 (인적사항) | `nrvsawtaauyihadij` | 인사청문회 정보 |
| 의사일정공지 | `njlyptmbatwuwjtxf` | 의사일정 공지 정보 |
| 회기정보 | `BILLSESSPROD` | 회기 정보 |
| 국회의원 정보 통합 API | `ALLNAMEMBER` | 3,286건 |
| (영문) 위원회 정보 | `ENCMITINFO` | English committee info |
| 위원회 계류법률안 | discovered via INF_ID `OY18U4001075AG16626` | spec not downloaded |
| 날짜별 의정활동 | discovered via INF_ID `O8U5BW001076JT16522` | spec not downloaded |

---

## 7. Fabricated Codes in Current Codebase

The following codes in `src/tools/schedule.ts` and `src/tools/meetings.ts` appear
fabricated and should be replaced:

| File | Current Code | Claimed Purpose | Correct Replacement |
|---|---|---|---|
| schedule.ts:42 | `nekcaiymatialqlxr` | 본회의 일정 | **CORRECT** (verified) |
| schedule.ts:43 | `niktlnofmsbmeorkq` | 위원회 일정 | `nrsldhjpaemrmolla` (위원회별 일정) or `ALLSCHEDULE` |
| meetings.ts:47 | `nkbgracaapyvowziy` | 본회의 회의록 | `nzbyfwhwaoanttzje` |
| meetings.ts:50 | `nvioxqxwikemzhsvy` | 국정감사 회의록 | `VCONFAPIGCONFLIST` |
| meetings.ts:53 | `nyqzphnlqtcafpbam` | 인사청문회 회의록 | `VCONFCFRMCONFLIST` |
| meetings.ts:56 | `nradonlafmaqcvtna` | 위원회 회의록 | `ncwgseseafwbuheph` |

---

## 8. How These Codes Were Discovered

1. Called `OPENSRVAPI` (meta API) with a valid API key to get all 276 API entries
2. Each entry has an `INF_ID` (e.g. `ORDPSW001070QH19059`) and a `DDC_URL` for
   downloading the specification Excel file
3. Downloaded each spec xlsx via `downloadOpenApiSpec.do?infId={INF_ID}&infSeq=2`
4. Parsed the xlsx to extract the "요청주소" (request URL) which contains the
   actual API code
5. The INF_ID is NOT the API code -- the actual code is embedded in the spec file

This process can be repeated for any of the 276 APIs to discover more codes.
