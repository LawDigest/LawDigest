# 국가선거정보 — 선거공약 정보 조회 서비스

> 제공기관: 중앙선거관리위원회  
> 문서 버전: v2.15 (2025-02-12)  
> 원본 파일: `OpenAPI활용가이드(선거공약정보)_v2.15.hwpx`

---

## 목차

1. [제·개정 이력](#제개정-이력)
2. [서비스 명세](#서비스-명세)
3. [오퍼레이션 목록](#오퍼레이션-목록)
4. [오퍼레이션 명세: 후보자 선거공약 정보 조회](#오퍼레이션-명세-후보자-선거공약-정보-조회)
   - [요청 메시지 명세](#가-요청-메시지-명세)
   - [응답 메시지 명세](#나-응답-메시지-명세)
   - [요청/응답 메시지 예제](#다-요청응답-메시지-예제)
5. [에러 코드](#에러-코드)
   - [공공데이터 포털 에러코드](#2-1-공공데이터-포털-에러코드)
   - [제공기관 에러코드](#2-2-제공기관-에러코드)

---

## 제·개정 이력

| 제·개정 번호 | 제·개정 내용 | 제·개정 일자 |
|---|---|---|
| 2.13 | 제·개정 이력 추가 | 2024-11-01 |
| 2.14 | 서비스 제공자 정보 변경 | 2024-11-05 |
| 2.15 | 주의사항 위치 변경 및 내용 추가 / 응답 메시지 명세 → 요청 메시지 명세 | 2025-02-12 |

---

## 서비스 명세

### API 기본 정보

| 항목 | 내용 |
|---|---|
| API 명(영문) | `ElecPrmsInfoInqireService` |
| API 명(국문) | 선거공약 정보 조회 서비스 |
| API 설명 | 선거ID와 선거종류코드, 후보자ID를 입력하여 선거공약 정보를 조회할 수 있는 서비스 |

### 보안 및 인터페이스

| 항목 | 내용 |
|---|---|
| 서비스 인증/권한 | 서비스 Key 사용 |
| 메시지 레벨 암호화 | 없음 |
| 전송 레벨 암호화 | 없음 |
| 인터페이스 표준 | REST (GET, POST, PUT, DELETE) |
| 교환 데이터 표준 | XML / JSON |

### 배포 정보

| 항목 | 내용 |
|---|---|
| 서비스 URL | `http://apis.data.go.kr/9760000/ElecPrmsInfoInqireService` |
| 서비스 명세 URL (WSDL/WADL) | N/A |
| 서비스 버전 | 1.0 |
| 서비스 시작일 | 2020-01-20 |
| 서비스 배포일 | 2020-01-20 |
| 서비스 이력 | 2020-01-20: 서비스 시작 |
| 데이터 갱신 주기 | 매 선거 종료 후 두 달 이내 |

### 서비스 제공자

- 중앙선거관리위원회 정보운영과 김현주 주무관
- 이메일: ncesan715@nec.go.kr
- 전화: 02-3294-1159

---

## 오퍼레이션 목록

| 번호 | API명(국문) | 상세기능명(영문) | 상세기능명(국문) |
|---|---|---|---|
| 1 | 선거공약 정보 조회 서비스 | `getCnddtElecPrmsInfoInqire` | 후보자 선거공약 정보 조회 |

---

## 오퍼레이션 명세: 후보자 선거공약 정보 조회

| 항목 | 내용 |
|---|---|
| 상세기능 번호 | 1 |
| 상세기능 유형 | 조회(목록) |
| 상세기능명(국문) | 후보자 선거공약 정보 조회 |
| 상세기능 설명 | 선거ID와 선거종류코드, 후보자ID를 입력하여 선거공약 정보를 조회할 수 있는 서비스 |
| Call Back URL | `http://apis.data.go.kr/9760000/ElecPrmsInfoInqireService/getCnddtElecPrmsInfoInqire` |
| 최대 메시지 사이즈 | 123 bytes |
| 평균 응답 시간 | 0.5 ms |
| 초당 최대 트랜잭션 | 30 tps |

---

### (가) 요청 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
|---|---|---|---|---|---|
| `serviceKey` | 서비스키 | 255 | 필수 | — | 공공데이터포털에서 발급받은 인증키 |
| `pageNo` | 페이지 번호 | 6 | 필수 | `1` | 페이지 번호 (최대값: 100,000) |
| `numOfRows` | 목록 건수 | 3 | 필수 | `10` | 목록 건수 (최대값: 100) |
| `resultType` | 결과 형식 | 4 | 옵션 | `xml` | 기본값: `xml` |
| `sgId` | 선거ID | 10 | 필수 | `20220309` | 선거ID |
| `sgTypecode` | 선거종류코드 | 2 | 필수 | `1` | 선거종류코드 |
| `cnddtId` | 후보자ID | 10 | 필수 | `100000000` | 후보자ID |

> **항목구분**: 필수(1), 옵션(0)

#### 주의사항

- 후보자ID(`cnddtId`)는 **후보자 정보 조회 서비스** 또는 **당선인 정보 조회 서비스**의 `huboid` 필드를 통해 확인 가능
- 선거종류코드 및 후보자에 따라 공약 개수가 다를 수 있음
  - 후보자(당선인)가 공약 미제출 시 데이터가 없을 수 있음
- 선거 종료 이전: 후보자 공약 정보 제공
- 선거 종료 및 데이터 갱신 이후: 당선인(당선된 후보자) 정보만 제공
- **선거종류코드(`sgTypecode`) 목록:**

  | 코드 | 선거 종류 |
  |---|---|
  | `1` | 대통령선거 |
  | `3` | 시·도지사선거 |
  | `4` | 구·시·군의장선거 |
  | `11` | 교육감선거 |

  > 이외 코드(예: `2` 국회의원선거)는 공약서를 제출하지 않습니다. 국회의원 선거의 경우 공약이 아닌 선거공보를 제출하며, 아래에서 확인 가능합니다:
  > 1. [선거관리위원회도서관 > 선거자료 > 후보자선전물]
  > 2. [중앙선거관리위원회 정책·공약마당 > 당선인공약]

---

### (나) 응답 메시지 명세

#### 공통 헤더 필드

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
|---|---|---|---|---|---|
| `resultCode` | 결과코드 | 2 | 필수 | `00` | `00`: 성공 |
| `resultMsg` | 결과메시지 | 10 | 필수 | `NORMAL SERVICE` | 결과 메시지 |
| `numOfRows` | 한 페이지 결과 수 | 3 | 필수 | `10` | 한 페이지 결과 수 |
| `pageNo` | 페이지 번호 | 6 | 필수 | `1` | 페이지 번호 |
| `totalCount` | 전체 결과 수 | 10 | 필수 | `3` | 전체 결과 수 |

#### Items 필드 (반복)

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
|---|---|---|---|---|---|
| `num` | 결과순서 | 8 | 필수 | `1` | 결과순서 |
| `sgId` | 선거ID | 10 | 필수 | `20220309` | 선거ID |
| `sgTypecode` | 선거종류코드 | 2 | 필수 | `1` | 선거종류코드 |
| `cnddtId` | 후보자ID | 10 | 필수 | `100000000` | 후보자ID |
| `sggName` | 선거구명 | 80 | 필수 | `대한민국` | 선거구명 |
| `sidoName` | 시도명 | 40 | 필수 | `전국` | 시도명 (대선: 전국 / 그 외: 선거구를 관할하는 시도명) |
| `wiwName` | 구시군명 | 40 | 옵션 | — | 구시군명 (대선·시도지사·교육감: 공란 / 그 외: 선거구를 관할하는 구시군명) |
| `partyName` | 정당명 | 50 | 옵션 | `00당` | 정당명 |
| `krName` | 한글명 | 50 | 필수 | `홍길동` | 한글명 |
| `cnName` | 한자명 | 50 | 필수 | `洪吉童` | 한자명 |
| `prmsCnt` | 공약개수 | 2 | 필수 | `10` | 공약개수 |
| `prmsOrd1` | 공약순번1 | 2 | 필수 | `1` | 공약순번1 |
| `prmsRealmName1` | 공약분야명1 | 255 | 옵션 | `노동` | 공약분야명1 |
| `prmsTitle1` | 공약제목명1 | 255 | 필수 | `일자리를 책임지는 대한민국` | 공약제목명1 |
| `prmsCont1` | 공약내용1 | 255 | 옵션 | `일자리 확대, 국민께 드리는 최고의 선물입니다` | 공약내용1 |
| … | … | … | … | … | … |
| `prmsOrd10` | 공약순번10 | 2 | 옵션 | `10` | 공약순번10 |
| `prmsRealmName10` | 공약분야명10 | 255 | 옵션 | `환경` | 공약분야명10 |
| `prmsTitle10` | 공약제목명10 | 255 | 옵션 | `안전하고 건강한 대한민국` | 공약제목명10 |
| `prmsCont10` | 공약내용10 | 255 | 옵션 | `국가가 국민의 생명과 안전을 책임지겠습니다` | 공약내용10 |

> **항목구분**: 필수(1), 옵션(0)
>
> 공약 필드는 `prmsOrd1`~`prmsOrd10`, `prmsRealmName1`~`prmsRealmName10`, `prmsTitle1`~`prmsTitle10`, `prmsCont1`~`prmsCont10` 구조로 최대 10개 공약까지 제공됩니다.

---

### (다) 요청/응답 메시지 예제

#### 요청 메시지

```
http://apis.data.go.kr/9760000/ElecPrmsInfoInqireService/getCnddtElecPrmsInfoInqire
  ?pageNo=1
  &numOfRows=10
  &resultType=xml
  &sgId=20220309
  &sgTypecode=1
  &cnddtId=100000000
  &serviceKey=서비스키
```

> **주의**: 위의 요청 메시지는 존재하지 않는 후보자ID(`cnddtId`)를 사용한 샘플입니다. 실제 활용 시에는 실제 존재하는 후보자ID를 사용해야 합니다.

#### 응답 메시지

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
        <cnddtId>100000000</cnddtId>
        <sggName>대한민국</sggName>
        <sidoName>전국</sidoName>
        <wiwName/>
        <partyName>00당</partyName>
        <krName>홍길동</krName>
        <cnName>洪吉童</cnName>
        <prmsCnt>10</prmsCnt>
        <prmsOrd1>1</prmsOrd1>
        <prmsRealmName1>환경</prmsRealmName1>
        <prmsTitle1>안전하고 건강한 대한민국</prmsTitle1>
        <prmsCont1>국가가 국민의 생명과 안전을 책임지겠습니다</prmsCont1>
        <!-- ... -->
        <prmsOrd10>10</prmsOrd10>
        <prmsRealmName10>환경</prmsRealmName10>
        <prmsTitle10>안전하고 건강한 대한민국</prmsTitle10>
        <prmsCont10>국가가 국민의 생명과 안전을 책임지겠습니다</prmsCont10>
      </item>
      <!-- ... -->
    </items>
    <numOfRows>10</numOfRows>
    <pageNo>1</pageNo>
    <totalCount>1</totalCount>
  </body>
</response>
```

---

## 에러 코드

### 2-1 공공데이터 포털 에러코드

| 에러코드 | 에러메시지 | 설명 |
|---|---|---|
| `1` | `APPLICATION_ERROR` | 어플리케이션 에러 |
| `04` | `HTTP_ERROR` | HTTP 에러 |
| `12` | `NO_OPENAPI_SERVICE_ERROR` | 해당 오픈API 서비스가 없거나 폐기됨 |
| `20` | `SERVICE_ACCESS_DENIED_ERROR` | 서비스 접근 거부 |
| `22` | `LIMITED_NUMBER_OF_SERVICE_REQUESTS_EXCEEDS_ERROR` | 서비스 요청 제한 횟수 초과 에러 |
| `30` | `SERVICE_KEY_IS_NOT_REGISTERED_ERROR` | 등록되지 않은 서비스 키 |
| `31` | `DEADLINE_HAS_EXPIRED_ERROR` | 활용기간 만료 |
| `32` | `UNREGISTERED_IP_ERROR` | 등록되지 않은 IP |
| `99` | `UNKNOWN_ERROR` | 기타 에러 |

> 공공데이터포털에서 출력되는 오류 메시지는 XML로만 출력됩니다.

```xml
<OpenAPI_ServiceResponse>
  <cmmMsgHeader>
    <errMsg>SERVICE ERROR</errMsg>
    <returnAuthMsg>SERVICE_KEY_IS_NOT_REGISTERED_ERROR</returnAuthMsg>
    <returnReasonCode>30</returnReasonCode>
  </cmmMsgHeader>
</OpenAPI_ServiceResponse>
```

---

### 2-2 제공기관 에러코드

| 에러코드 | 에러메시지 |
|---|---|
| `ERROR-03` | 데이터가 정보가 없습니다. 활용문서를 확인해 주시기 바랍니다. |
| `ERROR-301` | 파일타입 값이 누락 혹은 유효하지 않습니다. 요청인자 중 TYPE를 확인하십시오. |
| `ERROR-310` | 해당하는 서비스를 찾을 수 없습니다. |
| `ERROR-333` | 요청위치 값의 타입이 유효하지 않습니다. 요청위치 값은 정수를 입력하세요. |
| `ERROR-340` | 필수 파라미터가 누락되었습니다. |
| `ERROR-500` | 서버 오류입니다. 지속적으로 발생 시 관리자에게 문의 바랍니다. |
| `ERROR-601` | SQL 문장 오류입니다. 지속적으로 발생 시 관리자에게 문의 바랍니다. |

> 제공기관에서 출력되는 오류 메시지는 XML로만 출력됩니다.

```xml
<response>
  <header>
    <resultCode>ERROR-310</resultCode>
    <resultMsg>해당하는 서비스를 찾을 수 없습니다.</resultMsg>
  </header>
</response>
```
