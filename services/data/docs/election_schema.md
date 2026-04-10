# 선거 데이터 DB 스키마 문서

중앙선거관리위원회 OpenAPI에서 수집한 선거 데이터를 저장하는 테이블 구조.
모든 테이블은 `sg_id`(선거ID)로 선거별 데이터가 분리된다.

## 선거종류코드 (sgTypecode) 참조

| 코드 | 선거종류 |
|------|---------|
| 0 | 대표선거명 |
| 1 | 대통령 |
| 2 | 국회의원 |
| 3 | 시도지사 |
| 4 | 구시군장 |
| 5 | 시도의원 |
| 6 | 구시군의회의원 |
| 7 | 국회의원비례대표 |
| 8 | 광역의원비례대표 |
| 9 | 기초의원비례대표 |
| 10 | 교육의원 |
| 11 | 교육감 |

---

## 코드정보 테이블 (6종)

API 출처: `CommonCodeService`

### election_codes — 선거코드

역대 모든 선거의 기본 코드 목록. 다른 API 호출 시 `sg_id`와 `sg_typecode`를 참조하는 기준 테이블.

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | bigint (PK) | 자동증가 ID |
| sg_id | varchar(20) | 선거ID. 투표일 기반 (예: `20260603`) |
| sg_typecode | smallint | 선거종류코드 (위 참조표) |
| sg_name | varchar(100) | 선거명 (예: `제9회 전국동시지방선거`, `시도지사선거`) |
| sg_vote_date | varchar(10) | 선거일자 (YYYYMMDD) |
| created_at | datetime | 레코드 생성 시각 |
| updated_at | datetime | 레코드 갱신 시각 |

> UNIQUE: `(sg_id, sg_typecode)`

### election_districts — 선거구코드

선거종류별 선거구 목록. 후보자/당선인 조회 시 선거구 범위를 파악하는 데 사용.

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | bigint (PK) | 자동증가 ID |
| sg_id | varchar(20) | 선거ID |
| sg_typecode | smallint | 선거종류코드 |
| sgg_name | varchar(100) | 선거구명 (예: `서울특별시`, `종로구제1선거구`) |
| sd_name | varchar(50) | 시도명 (예: `서울특별시`) |
| wiw_name | varchar(50) | 구시군명 (예: `종로구`). 시도지사/교육감 등은 NULL |
| sgg_jungsu | int | 선거구 정수 — 해당 선거구의 당선인 수 |
| s_order | int | 정렬순서 |
| created_at / updated_at | datetime | 타임스탬프 |

> UNIQUE: `(sg_id, sg_typecode, sgg_name, sd_name)`

### election_gusiguns — 구시군코드

시도 하위의 구시군 행정구역 목록. `sd_name`이 빈 문자열인 행은 시도 자체를 나타내는 상위 항목.

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | bigint (PK) | 자동증가 ID |
| sg_id | varchar(20) | 선거ID |
| sd_name | varchar(50) | 시도명. 상위 시도 항목은 빈값 |
| wiw_name | varchar(50) | 구시군명 (예: `종로구`) |
| w_order | int | 정렬순서 |
| created_at / updated_at | datetime | 타임스탬프 |

> UNIQUE: `(sg_id, sd_name, wiw_name)`

### election_parties — 정당코드

해당 선거에 참여한 정당 목록.

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | bigint (PK) | 자동증가 ID |
| sg_id | varchar(20) | 선거ID |
| jd_name | varchar(100) | 정당명 (예: `더불어민주당`) |
| p_order | int | 정렬순서 |
| created_at / updated_at | datetime | 타임스탬프 |

> UNIQUE: `(sg_id, jd_name)`

### election_jobs — 직업코드

후보자 직업 분류 코드. `election_candidates.job_id`와 매핑.

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | bigint (PK) | 자동증가 ID |
| sg_id | varchar(20) | 선거ID |
| job_id | varchar(10) | 직업ID (예: `81`) |
| job_name | varchar(100) | 직업명 (예: `정당인`) |
| j_order | int | 정렬순서 |
| created_at / updated_at | datetime | 타임스탬프 |

> UNIQUE: `(sg_id, job_id)`

### election_educations — 학력코드

후보자 학력 분류 코드. `election_candidates.edu_id`와 매핑.

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | bigint (PK) | 자동증가 ID |
| sg_id | varchar(20) | 선거ID |
| edu_id | varchar(10) | 학력ID (예: `68`) |
| edu_name | varchar(100) | 학력명 (예: `대학원졸`) |
| e_order | int | 정렬순서 |
| created_at / updated_at | datetime | 타임스탬프 |

> UNIQUE: `(sg_id, edu_id)`

---

## 후보자/당선인 테이블

### election_candidates — 후보자

예비후보자와 확정후보자를 `candidate_type`으로 구분하여 통합 저장.

API 출처: `PofelcddInfoInqireService`
- 예비후보자: `getPoelpcddRegistSttusInfoInqire`
- 확정후보자: `getPofelcddRegistSttusInfoInqire`

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | bigint (PK) | 자동증가 ID |
| huboid | varchar(20) | 후보자ID. 선거관리위 API 기준 고유 식별자 |
| sg_id | varchar(20) | 선거ID |
| sg_typecode | smallint | 선거종류코드 |
| candidate_type | enum | `PRELIMINARY` (예비) / `CONFIRMED` (확정) |
| sgg_name | varchar(100) | 선거구명 |
| sd_name | varchar(50) | 시도명 |
| wiw_name | varchar(50) | 구시군명. 시도지사/교육감 등은 NULL |
| giho | varchar(10) | 기호 번호. 예비후보자/비례대표는 NULL |
| giho_sangse | varchar(50) | 기호상세. 구시군의원만 해당 (가, 나, …) |
| jd_name | varchar(100) | 정당명 |
| name | varchar(50) | 한글 성명 |
| hanja_name | varchar(50) | 한자 성명 |
| gender | varchar(10) | 성별 (`남` / `여`) |
| birthday | varchar(10) | 생년월일 (YYYYMMDD) |
| age | smallint | 연령 (선거일 기준) |
| addr | varchar(200) | 주소 (상세주소 제외). 선거 종료 후 비공개될 수 있음 |
| job_id | varchar(10) | 직업ID → `election_jobs.job_id` 참조 |
| job | varchar(200) | 직업 (직업분류가 아닌 실제 직업명) |
| edu_id | varchar(10) | 학력ID → `election_educations.edu_id` 참조 |
| edu | varchar(200) | 학력 (학력분류가 아닌 실제 학력) |
| career1 | text | 경력1 |
| career2 | text | 경력2 |
| regdate | varchar(10) | 등록일 (YYYYMMDD). 예비후보자에만 존재 |
| status | varchar(20) | 등록상태: `등록`, `사퇴`, `사망`, `등록무효` |
| normalized_region | varchar(100) | 여론조사(polls) 연계용 정규화 지역명 (예: `서울특별시 전체`) |
| normalized_election_name | varchar(100) | 여론조사(polls) 연계용 정규화 선거명 (예: `광역단체장선거`) |
| created_at / updated_at | datetime | 타임스탬프 |

> UNIQUE: `(huboid, sg_id, candidate_type)`

### election_winners — 당선인

선거 종료 후 당선 확정된 후보자 정보 + 득표 결과.

API 출처: `WinnerInfoInqireService2` → `getWinnerInfoInqire`

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | bigint (PK) | 자동증가 ID |
| candidate_id | bigint (FK) | `election_candidates.id` 외래키. 확정후보자 레코드와 연결 |
| huboid | varchar(20) | 후보자ID |
| sg_id | varchar(20) | 선거ID |
| sg_typecode | smallint | 선거종류코드 |
| sgg_name | varchar(100) | 선거구명 |
| sd_name | varchar(50) | 시도명 |
| wiw_name | varchar(50) | 구시군명 |
| giho | varchar(10) | 기호 |
| giho_sangse | varchar(50) | 기호상세 |
| jd_name | varchar(100) | 정당명 |
| name | varchar(50) | 한글 성명 |
| hanja_name | varchar(50) | 한자 성명 |
| gender | varchar(10) | 성별 |
| birthday | varchar(10) | 생년월일 |
| age | smallint | 연령 |
| addr | varchar(200) | 주소 |
| job_id | varchar(10) | 직업ID |
| job | varchar(200) | 직업 |
| edu_id | varchar(10) | 학력ID |
| edu | varchar(200) | 학력 |
| career1 | text | 경력1 |
| career2 | text | 경력2 |
| dugsu | int | 득표수 |
| dugyul | varchar(10) | 득표율 (%, 예: `59.05`) |
| normalized_region | varchar(100) | 여론조사 연계용 정규화 지역명 |
| normalized_election_name | varchar(100) | 여론조사 연계용 정규화 선거명 |
| created_at / updated_at | datetime | 타임스탬프 |

> UNIQUE: `(huboid, sg_id)`
> FK: `candidate_id` → `election_candidates.id`

---

## 공약/정책 테이블

### election_pledges — 선거공약

후보자별 선거공약 (최대 10건). sgTypecode 1(대통령), 3(시도지사), 4(구시군장), 11(교육감)만 제공.

API 출처: `ElecPrmsInfoInqireService` → `getCnddtElecPrmsInfoInqire`

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | bigint (PK) | 자동증가 ID |
| candidate_id | bigint (FK) | `election_candidates.id` 외래키 |
| sg_id | varchar(20) | 선거ID |
| sg_typecode | smallint | 선거종류코드 |
| cnddt_id | varchar(20) | 후보자ID (= huboid) |
| prms_ord | smallint | 공약 순서 (1~10) |
| prms_title | text | 공약 제목 |
| prms_content | text | 공약 내용 |
| normalized_region | varchar(100) | 여론조사 연계용 정규화 지역명 |
| normalized_election_name | varchar(100) | 여론조사 연계용 정규화 선거명 |
| summary | text | LLM 요약 (추후 채움) |
| embedding_id | varchar(100) | 벡터 임베딩 참조 ID (추후 채움) |
| created_at / updated_at | datetime | 타임스탬프 |

> UNIQUE: `(sg_id, cnddt_id, prms_ord)`
> FK: `candidate_id` → `election_candidates.id`

### election_party_policies — 정당정책

정당별 정책 공약 (최대 10건).

API 출처: `PartyPlcInfoInqireService` → `getPartyPlcInfoInqire`

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | bigint (PK) | 자동증가 ID |
| sg_id | varchar(20) | 선거ID |
| party_name | varchar(100) | 정당명 |
| prms_cnt | smallint | 해당 정당의 정책 수 |
| prms_ord | smallint | 정책 순서 (1~10) |
| prms_title | text | 정책 제목 |
| prms_content | text | 정책 내용 |
| summary | text | LLM 요약 (추후 채움) |
| embedding_id | varchar(100) | 벡터 임베딩 참조 ID (추후 채움) |
| created_at / updated_at | datetime | 타임스탬프 |

> UNIQUE: `(sg_id, party_name, prms_ord)`

---

## 테이블 관계도

```
election_codes (sg_id, sg_typecode)
    │
    ├── election_districts (sg_id, sg_typecode → 선거구 목록)
    ├── election_gusiguns  (sg_id → 행정구역 목록)
    ├── election_parties   (sg_id → 정당 목록)
    ├── election_jobs      (sg_id → 직업코드)
    └── election_educations(sg_id → 학력코드)

election_candidates (huboid, sg_id)
    │
    ├── election_winners  (candidate_id FK → 당선인)
    └── election_pledges  (candidate_id FK → 공약)

election_parties (sg_id, jd_name)
    │
    └── election_party_policies (sg_id, party_name → 정당정책)
```

## 여론조사(polls) 연계

`election_candidates`와 `election_winners`에 있는 정규화 필드를 통해 기존 여론조사 테이블과 조인 가능:

- `normalized_region` → `poll_surveys.region` (예: `서울특별시 전체`)
- `normalized_election_name` → `poll_surveys.election_name` (예: `광역단체장선거`)
