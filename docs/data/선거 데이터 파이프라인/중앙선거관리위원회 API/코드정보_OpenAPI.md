# 국가선거정보 코드 정보 조회 서비스 OpenAPI 활용 가이드

> 중앙선거관리위원회 제공 / 문서 버전 v3.12

---

## 제·개정 이력

| 제·개정 번호 | 제·개정 내용 | 제·개정 일자 |
|---|---|---|
| 3.10 | 제·개정 이력 추가 | 2024.11.01 |
| 3.11 | 서비스 제공자 정보 변경 | 2024.11.05 |
| 3.12 | 주의사항 위치 변경 — 응답 메시지 명세 → 요청 메시지 명세 | 2025.02.12 |

---

## 서비스 명세

### 서비스 기본 정보

| 항목 | 내용 |
|---|---|
| 서비스 ID | SC-IFT-05-01 |
| 서비스명(국문) | 코드정보조회서비스 |
| 서비스명(영문) | CommonCodeService |
| 서비스 설명 | 선거ID와 선거종류코드, 선거명을 입력하여 선거관련 코드정보를 조회할 수 있는 서비스 |

### 서비스 보안

| 항목 | 내용 |
|---|---|
| 서비스 인증/권한 | 서비스 Key 사용 |
| 메시지 레벨 암호화 | 없음 |
| 전송 레벨 암호화 | 없음 |

### 적용 기술 수준

| 항목 | 내용 |
|---|---|
| 인터페이스 표준 | REST (GET) |
| 교환 데이터 표준 | (해당 없음) |

### 서비스 URL

| 환경 | URL |
|---|---|
| 개발환경 | `http://apis.data.go.kr/9760000/CommonCodeService` |
| 운영환경 | `http://apis.data.go.kr/9760000/CommonCodeService` |
| 서비스 WADL | N/A |

### 서비스 배포 정보

| 항목 | 내용 |
|---|---|
| 서비스 버전 | 1.0 |
| 서비스 시작일 | 2018년 4월 26일 |
| 배포 일자 | 2018년 4월 26일 |
| 데이터 갱신 주기 | 매 선거 예비후보자 등록일 이후 |
| 서비스 제공자 | 중앙선거관리위원회 정보운영과 김현주 주무관 (ncesan715@nec.go.kr / 02-3294-1159) |

### 메시지 교환 및 로깅

| 항목 | 내용 |
|---|---|
| 메시지 교환 유형 | (해당 없음) |
| 메시지 로깅 — 성공 | Header 로깅 |
| 메시지 로깅 — 실패 | Header + Body 로깅 |
| 사용 제약 사항 | N/A |

---

## 오퍼레이션 목록

| NO | 서비스명(국문) | 오퍼레이션명(영문) | 오퍼레이션명(국문) |
|---|---|---|---|
| 1 | 코드정보조회 서비스 | getCommonSgCodeList | 선거코드 조회 |
| 2 | 코드정보조회 서비스 | getCommonGusigunCodeList | 구시군코드 조회 |
| 3 | 코드정보조회 서비스 | getCommonSggCodeList | 선거구코드 조회 |
| 4 | 코드정보조회 서비스 | getCommonPartyCodeList | 정당코드 조회 |
| 5 | 코드정보조회 서비스 | getCommonJobCodeList | 직업코드 조회 |
| 6 | 코드정보조회 서비스 | getCommonEduBckgrdCodeList | 학력코드 조회 |

---

## 오퍼레이션 명세

### 오퍼레이션 1: 선거코드 조회 (`getCommonSgCodeList`)

#### 오퍼레이션 정보

| 항목 | 내용 |
|---|---|
| 오퍼레이션 번호 | 1 |
| 오퍼레이션명(국문) | 선거코드 조회 |
| 오퍼레이션 유형 | 조회(목록) |
| 오퍼레이션명(영문) | getCommonSgCodeList |
| 오퍼레이션 설명 | 선거ID, 선거종류코드, 선거명을 조회할 수 있는 서비스 |
| Call Back URL | `http://apis.data.go.kr/9760000/CommonCodeService/getCommonSgCodeList` |
| 최대 메시지 사이즈 | 123 bytes |
| 평균 응답 시간 | 0.5 ms |
| 초당 최대 트랜잭션 | 30 tps |
| 엔티티 | 선거코드 |
| 테이블명 | COMMONSGCODE |

#### (가) 요청 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
|---|---|---|---|---|---|
| serviceKey | 서비스키 | 255 | 필수(1) | — | 공공데이터포털에서 발급받은 인증키 |
| pageNo | 페이지 번호 | 6 | 필수(1) | 1 | 페이지 번호 (최대값: 100000) |
| numOfRows | 목록 건수 | 3 | 필수(1) | 10 | 목록 건수 (최대값: 100) |
| resultType | 데이터포맷 | 4 | 옵션(0) | xml | default: xml |

> **항목구분 범례:** 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

> **선거종류코드(sgTypecode) 참고:**
> - (0) 대표선거명
> - (1) 대통령
> - (2) 국회의원
> - (3) 시도지사
> - (4) 구시군장
> - (5) 시도의원
> - (6) 구시군의회의원
> - (7) 국회의원비례대표
> - (8) 광역의원비례대표
> - (9) 기초의원비례대표
> - (10) 교육의원
> - (11) 교육감

> **주의사항:** 재·보궐선거의 경우 선거가 추가될 수 있습니다.

#### (나) 응답 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
|---|---|---|---|---|---|
| resultCode | 결과코드 | 10 | 필수(1) | INFO-00 | 00: 성공 |
| resultMsg | 결과메시지 | 50 | 필수(1) | NORMAL SERVICE | — |
| Items | — | — | 0..n | — | — |
| num | 결과순서 | 8 | 필수(1) | 1 | 결과순서 |
| sgId | 선거코드 | 10 | 필수(1) | 20220309 | 선거코드 |
| sgTypecode | 선거종류코드 | 2 | 필수(1) | 1 | 선거종류코드 |
| sgName | 선거명 | 50 | 필수(1) | 제20대 대통령선거 | 선거명 |
| sgVotedate | 선거일자 | 8 | 필수(1) | 20220309 | 선거일자 |
| numOfRows | 목록건수 | 3 | 필수(1) | 10 | 목록건수 |
| pageNo | 페이지 번호 | 6 | 필수(1) | 1 | 페이지 번호 |
| totalCount | 총건수 | 10 | 필수(1) | 10 | 총건수 |

#### (다) 요청 / 응답 메시지 예제

**REST(URI)**

```
http://apis.data.go.kr/9760000/CommonCodeService/getCommonSgCodeList?pageNo=1&numOfRows=10&resultType=xml&serviceKey=서비스키
```

**응답 메시지**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<response>
  <header>
    <resultCode>00</resultCode>
    <resultMsg>NORMAL SERVICE</resultMsg>
  </header>
  <body>
    <items>
      <item>
        <num>1</num>
        <sgId>20220309</sgId>
        <sgTypecode>0</sgTypecode>
        <sgName>제20대 대통령선거</sgName>
        <sgVotedate>20220309</sgVotedate>
      </item>
      <item>
        <num>2</num>
        <sgId>20220309</sgId>
        <sgTypecode>1</sgTypecode>
        <sgName>대통령선거</sgName>
        <sgVotedate>20220309</sgVotedate>
      </item>
      ...
    </items>
    <numOfRows>10</numOfRows>
    <pageNo>1</pageNo>
    <totalCount>10</totalCount>
  </body>
</response>
```

---

### 오퍼레이션 2: 구시군코드 조회 (`getCommonGusigunCodeList`)

#### 오퍼레이션 정보

| 항목 | 내용 |
|---|---|
| 오퍼레이션 번호 | 2 |
| 오퍼레이션명(국문) | 구시군코드 조회 |
| 오퍼레이션 유형 | 조회(목록) |
| 오퍼레이션명(영문) | getCommonGusigunCodeList |
| 오퍼레이션 설명 | 선거ID를 입력하여 구시군명, 순서, 상위시도명을 조회할 수 있는 서비스 |
| Call Back URL | `http://apis.data.go.kr/9760000/CommonCodeService/getCommonGusigunCodeList` |
| 최대 메시지 사이즈 | 123 bytes |
| 평균 응답 시간 | 0.5 ms |
| 초당 최대 트랜잭션 | 30 tps |
| 엔티티 | 구시군코드 |
| 테이블명 | COMMONGUSIGUNCODE |

#### (가) 요청 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
|---|---|---|---|---|---|
| serviceKey | 서비스키 | 255 | 필수(1) | — | 공공데이터포털에서 발급받은 인증키 |
| pageNo | 페이지 번호 | 6 | 필수(1) | 1 | 페이지 번호 (최대값: 100000) |
| numOfRows | 목록 건수 | 3 | 필수(1) | 10 | 목록 건수 (최대값: 100) |
| resultType | 데이터포맷 | 4 | 옵션(0) | xml | default: xml |
| sgId | 선거ID | 10 | 필수(1) | 20220309 | 선거ID |
| sdName | 시도명 | 40 | 옵션(0) | 서울특별시 | 시도명 |

> **주의사항:** 재·보궐선거의 경우 추가적으로 구시군이 추가될 수 있습니다.

#### (나) 응답 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
|---|---|---|---|---|---|
| resultCode | 결과코드 | 10 | 필수(1) | INFO-00 | INFO-00: 성공 |
| resultMsg | 결과메시지 | 50 | 필수(1) | NORMAL SERVICE | — |
| Items | — | — | 0..n | — | — |
| num | 결과순서 | 8 | 필수(1) | 1 | 결과순서 |
| sgId | 선거ID | 10 | 필수(1) | 20220309 | 선거ID |
| wiwName | 구시군명 | 40 | 필수(1) | 종로구 | 구시군명 |
| wOrder | 순서 | 3 | 옵션(0) | 3 | 순서 |
| sdName | 상위시도명 | 40 | 옵션(0) | 서울특별시 | 상위시도명 (구시군명이 시도이면 공란) |
| numOfRows | 목록건수 | 3 | 필수(1) | 10 | 목록건수 |
| pageNo | 페이지 번호 | 6 | 필수(1) | 1 | 페이지 번호 |
| totalCount | 총건수 | 10 | 필수(1) | 10 | 총건수 |

#### (다) 요청 / 응답 메시지 예제

**REST(URI)**

```
http://apis.data.go.kr/9760000/CommonCodeService/getCommonGusigunCodeList?sgId=20220309&sdName=서울특별시&pageNo=1&numOfRows=10&resultType=xml&serviceKey=서비스키
```

**응답 메시지**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<response>
  <header>
    <resultCode>INFO-00</resultCode>
    <resultMsg>NORMAL SERVICE</resultMsg>
  </header>
  <body>
    <items>
      <item>
        <num>1</num>
        <sgId>20220309</sgId>
        <wiwName>종로구</wiwName>
        <wOrder>3</wOrder>
        <sdName>서울특별시</sdName>
      </item>
      <item>
        <num>2</num>
        <sgId>20220309</sgId>
        <wiwName>중구</wiwName>
        <wOrder>4</wOrder>
        <sdName>서울특별시</sdName>
      </item>
      ...
    </items>
    <numOfRows>10</numOfRows>
    <pageNo>1</pageNo>
    <totalCount>25</totalCount>
  </body>
</response>
```

---

### 오퍼레이션 3: 선거구코드 조회 (`getCommonSggCodeList`)

#### 오퍼레이션 정보

| 항목 | 내용 |
|---|---|
| 오퍼레이션 번호 | 3 |
| 오퍼레이션명(국문) | 선거구코드 조회 |
| 오퍼레이션 유형 | 조회(목록) |
| 오퍼레이션명(영문) | getCommonSggCodeList |
| 오퍼레이션 설명 | 선거ID와 선거종류코드를 입력하여 선거구명, 시도명, 구시군명, 선출정수, 순서를 조회할 수 있는 서비스 |
| Call Back URL | `http://apis.data.go.kr/9760000/CommonCodeService/getCommonSggCodeList` |
| 최대 메시지 사이즈 | 123 bytes |
| 평균 응답 시간 | 0.5 ms |
| 초당 최대 트랜잭션 | 30 tps |
| 엔티티 | 선거구코드 |
| 테이블명 | COMMONSGGCODE |

#### (가) 요청 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
|---|---|---|---|---|---|
| serviceKey | 서비스키 | 255 | 필수(1) | — | 공공데이터포털에서 발급받은 인증키 |
| pageNo | 페이지 번호 | 6 | 필수(1) | 1 | 페이지 번호 (최대값: 100000) |
| numOfRows | 목록 건수 | 3 | 필수(1) | 10 | 목록 건수 (최대값: 100) |
| resultType | 데이터포맷 | 4 | 옵션(0) | xml | default: xml |
| sgId | 선거ID | 10 | 필수(1) | 20220309 | 선거ID |
| sgTypecode | 선거종류코드 | 2 | 필수(1) | 1 | 선거종류코드 |

> **주의사항:** 재·보궐선거의 경우 선거구지역이 추가될 수 있습니다.

#### (나) 응답 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
|---|---|---|---|---|---|
| resultCode | 결과코드 | 10 | 필수(1) | INFO-00 | INFO-00: 성공 |
| resultMsg | 결과메시지 | 50 | 필수(1) | NORMAL SERVICE | — |
| Items | — | — | 0..n | — | — |
| num | 결과순서 | 8 | 필수(1) | 1 | 결과순서 |
| sgId | 선거ID | 10 | 필수(1) | 20220309 | 선거ID |
| sgTypecode | 선거종류코드 | 2 | 필수(1) | 1 | 선거종류코드 |
| sggName | 선거구명 | 80 | 필수(1) | 대한민국 | 선거구명 |
| sdName | 시도명 | 40 | 옵션(0) | 전국 | 대선·비례국선: 전국 / 그 외: 선거구를 관할하는 시도명 |
| wiwName | 구시군명 | 40 | 옵션(0) | — | 대선·시도지사·비례국선·비례광역·교육감: 공란 / 그 외: 선거구를 관할하는 구시군명 |
| sggJungsu | 선출정수 | 2 | 필수(1) | 1 | 선출정수(명) |
| sOrder | 순서 | 3 | 옵션(0) | 1 | 순서 |
| numOfRows | 목록건수 | 3 | 필수(1) | 10 | 목록건수 |
| pageNo | 페이지 번호 | 6 | 필수(1) | 1 | 페이지 번호 |
| totalCount | 총건수 | 10 | 필수(1) | 10 | 총건수 |

#### (다) 요청 / 응답 메시지 예제

**REST(URI)**

```
http://apis.data.go.kr/9760000/CommonCodeService/getCommonSggCodeList?sgId=20220309&sgTypecode=1&pageNo=1&numOfRows=10&resultType=xml&serviceKey=서비스키
```

**응답 메시지**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<response>
  <header>
    <resultCode>INFO-00</resultCode>
    <resultMsg>NORMAL SERVICE</resultMsg>
  </header>
  <body>
    <items>
      <item>
        <num>1</num>
        <sgId>20220309</sgId>
        <sgTypecode>1</sgTypecode>
        <sggName>대한민국</sggName>
        <sdName>전국</sdName>
        <wiwName/>
        <sggJungsu>1</sggJungsu>
        <sOrder>1</sOrder>
      </item>
      ...
    </items>
    <numOfRows>10</numOfRows>
    <pageNo>1</pageNo>
    <totalCount>17</totalCount>
  </body>
</response>
```

---

### 오퍼레이션 4: 정당코드 조회 (`getCommonPartyCodeList`)

#### 오퍼레이션 정보

| 항목 | 내용 |
|---|---|
| 오퍼레이션 번호 | 4 |
| 오퍼레이션명(국문) | 정당코드 조회 |
| 오퍼레이션 유형 | 조회(목록) |
| 오퍼레이션명(영문) | getCommonPartyCodeList |
| 오퍼레이션 설명 | 선거ID를 입력하여 정당명, 순서를 조회할 수 있는 서비스 |
| Call Back URL | `http://apis.data.go.kr/9760000/CommonCodeService/getCommonPartyCodeList` |
| 최대 메시지 사이즈 | 123 bytes |
| 평균 응답 시간 | 0.5 ms |
| 초당 최대 트랜잭션 | 30 tps |
| 엔티티 | 정당코드 |
| 테이블명 | COMMONPARTYCODE |

#### (가) 요청 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
|---|---|---|---|---|---|
| serviceKey | 서비스키 | 255 | 필수(1) | — | 공공데이터포털에서 발급받은 인증키 |
| pageNo | 페이지 번호 | 6 | 필수(1) | 1 | 페이지 번호 (최대값: 100000) |
| numOfRows | 목록 건수 | 3 | 필수(1) | 10 | 목록 건수 (최대값: 100) |
| resultType | 데이터포맷 | 4 | 옵션(0) | xml | default: xml |
| sgId | 선거ID | 10 | 필수(1) | 20220309 | 선거ID |

> **주의사항:** 정당명에는 무소속도 포함됩니다. 정당이 추가적으로 늘어날 경우 실시간으로 반영되지 않을 수 있습니다.

#### (나) 응답 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
|---|---|---|---|---|---|
| resultCode | 결과코드 | 10 | 필수(1) | INFO-00 | 00: 성공 |
| resultMsg | 결과메시지 | 50 | 필수(1) | NORMAL SERVICE | — |
| Items | — | — | 0..n | — | — |
| num | 결과순서 | 8 | 필수(1) | 1 | 결과순서 |
| sgId | 선거ID | 10 | 필수(1) | 20220309 | 선거ID |
| jdName | 정당명 | 50 | 필수(1) | OO당 | 정당명 |
| pOrder | 순서 | 3 | 필수(1) | 1 | 순서 |
| numOfRows | 목록건수 | 3 | 필수(1) | 10 | 목록건수 |
| pageNo | 페이지 번호 | 6 | 필수(1) | 1 | 페이지 번호 |
| totalCount | 총건수 | 10 | 필수(1) | 10 | 총건수 |

#### (다) 요청 / 응답 메시지 예제

**REST(URI)**

```
http://apis.data.go.kr/9760000/CommonCodeService/getCommonPartyCodeList?sgId=20220309&pageNo=1&numOfRows=10&resultType=xml&serviceKey=서비스키
```

**응답 메시지**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<response>
  <header>
    <resultCode>INFO-00</resultCode>
    <resultMsg>NORMAL SERVICE</resultMsg>
  </header>
  <body>
    <items>
      <item>
        <num>1</num>
        <sgId>20220309</sgId>
        <jdName>OO당</jdName>
        <pOrder>1</pOrder>
      </item>
      <item>
        <num>2</num>
        <sgId>20220309</sgId>
        <jdName>XX당</jdName>
        <pOrder>2</pOrder>
      </item>
      ...
    </items>
    <numOfRows>10</numOfRows>
    <pageNo>1</pageNo>
    <totalCount>52</totalCount>
  </body>
</response>
```

---

### 오퍼레이션 5: 직업코드 조회 (`getCommonJobCodeList`)

#### 오퍼레이션 정보

| 항목 | 내용 |
|---|---|
| 오퍼레이션 번호 | 5 |
| 오퍼레이션명(국문) | 직업코드 조회 |
| 오퍼레이션 유형 | 조회(목록) |
| 오퍼레이션명(영문) | getCommonJobCodeList |
| 오퍼레이션 설명 | 선거ID를 입력하여 직업코드, 직업명, 순서를 조회할 수 있는 서비스 |
| Call Back URL | `http://apis.data.go.kr/9760000/CommonCodeService/getCommonJobCodeList` |
| 최대 메시지 사이즈 | 123 bytes |
| 평균 응답 시간 | 0.5 ms |
| 초당 최대 트랜잭션 | 30 tps |
| 엔티티 | 직업코드 |
| 테이블명 | COMMONJOBCODE |

#### (가) 요청 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
|---|---|---|---|---|---|
| serviceKey | 서비스키 | 255 | 필수(1) | — | 공공데이터포털에서 발급받은 인증키 |
| pageNo | 페이지 번호 | 6 | 필수(1) | 1 | 페이지 번호 (최대값: 100000) |
| numOfRows | 목록 건수 | 3 | 필수(1) | 10 | 목록 건수 (최대값: 100) |
| resultType | 데이터포맷 | 4 | 옵션(0) | xml | default: xml |
| sgId | 선거ID | 10 | 필수(1) | 20220309 | 선거ID |

#### (나) 응답 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
|---|---|---|---|---|---|
| resultCode | 결과코드 | 10 | 필수(1) | INFO-00 | INFO-00: 성공 |
| resultMsg | 결과메시지 | 50 | 필수(1) | NORMAL SERVICE | — |
| Items | — | — | 0..n | — | — |
| num | 결과순서 | 8 | 필수(1) | 1 | 결과순서 |
| sgId | 선거ID | 10 | 필수(1) | 20220309 | 선거ID |
| jobId | 직업코드 | 3 | 필수(1) | 72 | 직업코드 |
| jobName | 직업명 | 50 | 필수(1) | 국회의원 | 직업명 |
| jOrder | 순서 | 3 | 필수(1) | 1 | 순서 |
| numOfRows | 목록건수 | 3 | 필수(1) | 10 | 목록건수 |
| pageNo | 페이지 번호 | 6 | 필수(1) | 1 | 페이지 번호 |
| totalCount | 총건수 | 10 | 필수(1) | 10 | 총건수 |

#### (다) 요청 / 응답 메시지 예제

**REST(URI)**

```
http://apis.data.go.kr/9760000/CommonCodeService/getCommonJobCodeList?sgId=20220309&pageNo=1&numOfRows=10&resultType=xml&serviceKey=서비스키
```

**응답 메시지**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<response>
  <header>
    <resultCode>INFO-00</resultCode>
    <resultMsg>NORMAL SERVICE</resultMsg>
  </header>
  <body>
    <items>
      <item>
        <num>1</num>
        <sgId>20220309</sgId>
        <jobId>72</jobId>
        <jobName>국회의원</jobName>
        <jOrder>1</jOrder>
      </item>
      <item>
        <num>2</num>
        <sgId>20220309</sgId>
        <jobId>74</jobId>
        <jobName>지방의원</jobName>
        <jOrder>2</jOrder>
      </item>
      ...
    </items>
    <numOfRows>10</numOfRows>
    <pageNo>1</pageNo>
    <totalCount>23</totalCount>
  </body>
</response>
```

---

### 오퍼레이션 6: 학력코드 조회 (`getCommonEduBckgrdCodeList`)

#### 오퍼레이션 정보

| 항목 | 내용 |
|---|---|
| 오퍼레이션 번호 | 6 |
| 오퍼레이션명(국문) | 학력코드 조회 |
| 오퍼레이션 유형 | 조회(목록) |
| 오퍼레이션명(영문) | getCommonEduBckgrdCodeList |
| 오퍼레이션 설명 | 선거ID를 입력하여 학력코드, 학력명, 순서를 조회할 수 있는 서비스 |
| Call Back URL | `http://apis.data.go.kr/9760000/CommonCodeService/getCommonEduBckgrdCodeList` |
| 최대 메시지 사이즈 | 123 bytes |
| 평균 응답 시간 | 0.5 ms |
| 초당 최대 트랜잭션 | 30 tps |
| 엔티티 | 학력코드 |
| 테이블명 | COMMONEDUBCKGRDCODE |

#### (가) 요청 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
|---|---|---|---|---|---|
| serviceKey | 서비스키 | 255 | 필수(1) | — | 공공데이터포털에서 발급받은 인증키 |
| pageNo | 페이지 번호 | 6 | 필수(1) | 1 | 페이지 번호 (최대값: 100000) |
| numOfRows | 목록 건수 | 3 | 필수(1) | 10 | 목록 건수 (최대값: 100) |
| resultType | 데이터포맷 | 4 | 옵션(0) | xml | default: xml |
| sgId | 선거ID | 10 | 필수(1) | 20220309 | 선거ID |

#### (나) 응답 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
|---|---|---|---|---|---|
| resultCode | 결과코드 | 10 | 필수(1) | INFO-00 | INFO-00: 성공 |
| resultMsg | 결과메시지 | 50 | 필수(1) | NORMAL SERVICE | — |
| Items | — | — | 0..n | — | — |
| num | 결과순서 | 8 | 필수(1) | 1 | 결과순서 |
| sgId | 선거ID | 10 | 필수(1) | 20220309 | 선거ID |
| eduId | 학력코드 | 3 | 필수(1) | 68 | 학력코드 |
| eduName | 학력명 | 50 | 필수(1) | 대졸 | 학력명 |
| eOrder | 순서 | 3 | 필수(1) | 1 | 순서 |
| numOfRows | 목록건수 | 3 | 필수(1) | 10 | 목록건수 |
| pageNo | 페이지 번호 | 6 | 필수(1) | 1 | 페이지 번호 |
| totalCount | 총건수 | 10 | 필수(1) | 10 | 총건수 |

#### (다) 요청 / 응답 메시지 예제

**REST(URI)**

```
http://apis.data.go.kr/9760000/CommonCodeService/getCommonEduBckgrdCodeList?sgId=20220309&pageNo=1&numOfRows=10&resultType=xml&serviceKey=서비스키
```

**응답 메시지**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<response>
  <header>
    <resultCode>INFO-00</resultCode>
    <resultMsg>NORMAL SERVICE</resultMsg>
  </header>
  <body>
    <items>
      <item>
        <num>1</num>
        <sgId>20220309</sgId>
        <eduId>58</eduId>
        <eduName>미기재</eduName>
        <eOrder>1</eOrder>
      </item>
      <item>
        <num>2</num>
        <sgId>20220309</sgId>
        <eduId>59</eduId>
        <eduName>무학(독학)</eduName>
        <eOrder>2</eOrder>
      </item>
      ...
    </items>
    <numOfRows>10</numOfRows>
    <pageNo>1</pageNo>
    <totalCount>21</totalCount>
  </body>
</response>
```

---

## 에러 코드 정리

### 2-1. 공공데이터 포털 에러코드

| 에러코드 | 에러메시지 | 설명 |
|---|---|---|
| 1 | APPLICATION_ERROR | 어플리케이션 에러 |
| 04 | HTTP_ERROR | HTTP 에러 |
| 12 | NO_OPENAPI_SERVICE_ERROR | 해당 오픈API 서비스가 없거나 폐기됨 |
| 20 | SERVICE_ACCESS_DENIED_ERROR | 서비스 접근거부 |
| 22 | LIMITED_NUMBER_OF_SERVICE_REQUESTS_EXCEEDS_ERROR | 서비스 요청제한횟수 초과에러 |
| 30 | SERVICE_KEY_IS_NOT_REGISTERED_ERROR | 등록되지 않은 서비스키 |
| 31 | DEADLINE_HAS_EXPIRED_ERROR | 활용기간 만료 |
| 32 | UNREGISTERED_IP_ERROR | 등록되지 않은 IP |
| 99 | UNKNOWN_ERROR | 기타에러 |

> 공공데이터포털에서 출력되는 오류 메시지는 XML로만 출력되며, 형태는 아래와 같습니다.

```xml
<OpenAPI_ServiceResponse>
  <cmmMsgHeader>
    <errMsg>SERVICE ERROR</errMsg>
    <returnAuthMsg>SERVICE_KEY_IS_NOT_REGISTERED_ERROR</returnAuthMsg>
    <returnReasonCode>30</returnReasonCode>
  </cmmMsgHeader>
</OpenAPI_ServiceResponse>
```

### 2-2. 제공기관 에러코드

| 에러코드 | 에러메시지 |
|---|---|
| ERROR-03 | 데이터가 정보가 없습니다. 활용문서를 확인해 주시기 바랍니다. |
| ERROR-301 | 파일타입 값이 누락 혹은 유효하지 않습니다. 요청인자 중 TYPE를 확인하십시오. |
| ERROR-310 | 해당하는 서비스를 찾을 수 없습니다. |
| ERROR-333 | 요청위치 값의 타입이 유효하지 않습니다. 요청위치 값은 정수를 입력하세요. |
| ERROR-340 | 필수 파라미터가 누락되었습니다. |
| ERROR-500 | 서버 오류입니다. 지속적으로 발생 시 관리자에게 문의 바랍니다. |
| ERROR-601 | SQL 문장 오류입니다. 지속적으로 발생 시 관리자에게 문의 바랍니다. |

> 제공기관에서 출력되는 오류 메시지는 XML로만 출력되며, 형태는 아래와 같습니다.

```xml
<response>
  <header>
    <resultCode>ERROR-310</resultCode>
    <resultMsg>해당하는 서비스를 찾을 수 없습니다.</resultMsg>
  </header>
</response>
```
