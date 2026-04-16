# 국가선거정보 후보자 정보 조회 서비스 OpenAPI 활용가이드 (v4.3)

> 출처: 중앙선거관리위원회  
> 원본 파일: `OpenAPI활용가이드(후보자정보)_v4.3.hwpx`

---

## 목차

1. [제·개정 이력](#제개정-이력)
2. [서비스 명세](#서비스-명세)
3. [오퍼레이션 목록](#오퍼레이션-목록)
4. [예비후보자 정보 조회 오퍼레이션 명세](#예비후보자-정보-조회-오퍼레이션-명세)
5. [후보자 정보 조회 오퍼레이션 명세](#후보자-정보-조회-오퍼레이션-명세)
6. [에러 코드](#에러-코드)

---

## 제·개정 이력

| 제·개정 번호 | 제·개정 내용 | 제·개정 일자 |
|---|---|---|
| 4.1 | 제·개정 이력 추가 | 2024.11.01 |
| 4.2 | 서비스 제공자 정보 변경 | 2024.11.05 |
| 4.3 | 주의사항 위치 변경 (응답 메시지 명세 → 요청 메시지 명세) | 2025.02.12 |

---

## 서비스 명세

### 서비스 기본 정보

| 항목 | 내용 |
|---|---|
| 서비스 ID | SC-IFT-05-02 |
| 서비스명(국문) | 후보자 정보 조회서비스 |
| 서비스명(영문) | PofelcddInfoInqireService |
| 서비스 설명 | 선거ID와 선거종류코드, 선거구명, 시도명을 입력하여 예비후보자 및 후보자 정보를 조회할 수 있는 서비스 |

### 보안 정보

| 항목 | 내용 |
|---|---|
| 서비스 인증/권한 | 서비스 Key |
| 메시지 레벨 암호화 | 없음 |
| 전송 레벨 암호화 | 없음 |

### 인터페이스 및 URL

| 항목 | 내용 |
|---|---|
| 인터페이스 표준 | REST (GET) |
| 교환 데이터 표준 | - |
| 서비스 URL (개발환경) | `http://apis.data.go.kr/9760000/PofelcddInfoInqireService` |
| 서비스 URL (운영환경) | `http://apis.data.go.kr/9760000/PofelcddInfoInqireService` |
| 서비스 WADL (개발환경) | N/A |
| 서비스 WADL (운영환경) | N/A |

### 배포 및 제공 정보

| 항목 | 내용 |
|---|---|
| 서비스 버전 | 1.0 |
| 서비스 시작일 | 2018년 4월 26일 |
| 배포 일자 | 2018년 4월 26일 |
| 서비스 제공자 | 중앙선거관리위원회 정보운영과 김현주 주무관 (ncesan715@nec.go.kr / 02-3294-1159) |
| 데이터 갱신 주기 | 매 선거 예비후보자등록일 및 후보자 등록일 |

### 메시지 교환 및 로깅

| 항목 | 내용 |
|---|---|
| 메시지 교환 유형 | - |
| 메시지 로깅 (성공) | Header |
| 메시지 로깅 (실패) | Header, Body |

### 사용 제약 사항

> 예비후보자정보는 후보자등록 개시일부터 조회 불가

---

## 오퍼레이션 목록

| NO | 서비스명(국문) | 오퍼레이션명(영문) | 오퍼레이션명(국문) |
|---|---|---|---|
| 1 | 후보자 정보 조회 서비스 | `getPoelpcddRegistSttusInfoInqire` | 예비후보자 정보 조회 |
| 2 | 후보자 정보 조회 서비스 | `getPofelcddRegistSttusInfoInqire` | 후보자 정보 조회 |

---

## 예비후보자 정보 조회 오퍼레이션 명세

### 오퍼레이션 기본 정보

| 항목 | 내용 |
|---|---|
| 오퍼레이션 번호 | 1 |
| 오퍼레이션명(국문) | 예비후보자 정보 조회 |
| 오퍼레이션 유형 | 조회(목록) |
| 오퍼레이션명(영문) | `getPoelpcddRegistSttusInfoInqire` |
| 오퍼레이션 설명 | 선거ID와 선거종류코드, 선거구명, 시도명을 입력하여 예비후보자 정보를 조회할 수 있는 서비스 |
| Call Back URL | `http://apis.data.go.kr/9760000/PofelcddInfoInqireService/getPoelpcddRegistSttusInfoInqire` |
| 최대 메시지 사이즈 | 123 bytes |
| 평균 응답 시간 | 0.5 ms |
| 초당 최대 트랜잭션 | 30 tps |
| 엔티티 | 예비후보자 |
| 테이블명 | `POELPCDDREGISTSTTUS` |

### (가) 요청 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
|---|---|---|---|---|---|
| `serviceKey` | 서비스키 | 255 | 필수(1) | - | 공공데이터포털에서 발급받은 인증키 |
| `pageNo` | 페이지 번호 | 6 | 필수(1) | `1` | 페이지 번호 (최대값: 100000) |
| `numOfRows` | 목록 건수 | 3 | 필수(1) | `10` | 목록 건수 (최대값: 100) |
| `resultType` | 결과 유형 | 4 | 옵션(0) | `xml` | default: xml |
| `sgId` | 선거ID | 10 | 필수(1) | `20220309` | 선거ID |
| `sgTypecode` | 선거종류코드 | 2 | 필수(1) | `1` | 선거종류코드 |
| `sggName` | 선거구명 | 80 | 옵션(0) | `종로구` | 선거구명 |
| `sdName` | 시도명 | 40 | 옵션(0) | `서울특별시` | 시도명 |

> **항목구분** : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

> **주의사항**
> 1. `sgId`, `sgTypecode`, `sggName`, `sdName`은 코드정보조회 서비스를 이용해서 조회 가능
> 2. 예비후보자의 경우는 실시간으로 자료가 변경될 수 있음. 예비후보자 정보는 후보자등록 개시일부터 조회되지 않음

### (나) 응답 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
|---|---|---|---|---|---|
| `resultCode` | 결과코드 | 10 | 필수(1) | `INFO-00` | INFO-00: 성공 |
| `resultMsg` | 결과메시지 | 50 | 필수(1) | `NORMAL SERVICE` | - |
| `Items` | 항목 목록 | - | 0..n | - | - |
| `num` | 결과순서 | 8 | 필수(1) | `1` | 결과순서 |
| `sgId` | 선거ID | 10 | 필수(1) | `20220309` | 선거ID |
| `sgTypecode` | 선거종류코드 | 2 | 필수(1) | `1` | 선거종류코드 |
| `huboid` | 후보자ID | 10 | 필수(1) | `10000000` | 후보자ID |
| `sggName` | 선거구명 | 80 | 필수(1) | `대한민국` | 선거구명 |
| `sdName` | 시도명 | 40 | 필수(1) | `전국` | 시도명 (대선: 전국으로 표기 / 그 외: 선거구를 관할하는 시도명) |
| `wiwName` | 구시군명 | 40 | 옵션(0) | - | 구시군명 (대선, 시도지사, 교육감: 공란 / 그 외: 선거구를 관할하는 구시군명) |
| `jdName` | 정당명 | 50 | 필수(1) | `00당` | 정당명 |
| `name` | 한글성명 | 50 | 필수(1) | `홍길동` | 한글성명 |
| `hanjaName` | 한자성명 | 50 | 필수(1) | `洪吉童` | 한자성명 |
| `gender` | 성별 | 2 | 필수(1) | `남` | 성별 |
| `birthday` | 생년월일 | 8 | 필수(1) | `19600101` | 생년월일 |
| `age` | 연령 | 3 | 필수(1) | `57` | 연령 (선거일 기준) |
| `addr` | 주소 | 100 | 옵션(0) | `서울특별시 종로구 청운효자동` | 주소 (상세주소 제외) |
| `jobId` | 직업ID | 2 | 필수(1) | `81` | 직업ID |
| `job` | 직업 | 200 | 필수(1) | `00회사 대표` | 직업 (직업분류 아님) |
| `eduId` | 학력ID | 2 | 필수(1) | `68` | 학력ID |
| `edu` | 학력 | 200 | 필수(1) | `00대학교 졸업` | 학력 (학력분류 아님) |
| `career1` | 경력1 | 200 | 필수(1) | `00협회장` | 경력1 |
| `career2` | 경력2 | 200 | 옵션(0) | `-` | 경력2 |
| `regdate` | 등록일 | 8 | 필수(1) | `20220213` | 등록일 |
| `status` | 등록상태 | 20 | 필수(1) | `등록` | 등록상태 (등록, 사퇴, 사망, 등록무효) |
| `numOfRows` | 목록건수 | 3 | 필수(1) | `10` | 목록건수 |
| `pageNo` | 페이지 번호 | 6 | 필수(1) | `1` | 페이지 번호 |
| `totalCount` | 총건수 | 10 | 필수(1) | `10` | 총건수 |

> **항목구분** : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

### (다) 요청/응답 메시지 예제

**요청 URL (REST/URI)**

```
http://apis.data.go.kr/9760000/PofelcddInfoInqireService/getPoelpcddRegistSttusInfoInqire?sgId=20220309&sgTypecode=1&sdName=전국&sggName=대한민국&pageNo=1&numOfRows=10&resultType=xml&serviceKey=서비스키
```

**응답 메시지 예제**

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
        <huboid>1000000</huboid>
        <sggName>대한민국</sggName>
        <sdName>전국</sdName>
        <wiwName></wiwName>
        <jdName>00당</jdName>
        <name>홍길동</name>
        <hanjaName>洪吉童</hanjaName>
        <gender>남</gender>
        <birthday>19600101</birthday>
        <age>57</age>
        <addr>서울특별시 종로구 청운효자동</addr>
        <jobId>81</jobId>
        <job>00회사 대표</job>
        <eduId>68</eduId>
        <edu>00대학교 졸업</edu>
        <career1>00협회장</career1>
        <career2/>
        <regdate>20220213</regdate>
        <status>등록</status>
      </item>
      <!-- ... 이하 항목 반복 ... -->
    </items>
    <numOfRows>10</numOfRows>
    <pageNo>1</pageNo>
    <totalCount>22</totalCount>
  </body>
</response>
```

---

## 후보자 정보 조회 오퍼레이션 명세

### 오퍼레이션 기본 정보

| 항목 | 내용 |
|---|---|
| 오퍼레이션 번호 | 2 |
| 오퍼레이션명(국문) | 후보자 정보 조회 |
| 오퍼레이션 유형 | 조회(목록) |
| 오퍼레이션명(영문) | `getPofelcddRegistSttusInfoInqire` |
| 오퍼레이션 설명 | 선거ID와 선거종류코드, 선거구명, 시도명을 입력하여 후보자 정보를 조회할 수 있는 서비스 |
| Call Back URL | `http://apis.data.go.kr/9760000/PofelcddInfoInqireService/getPofelcddRegistSttusInfoInqire` |
| 최대 메시지 사이즈 | 123 bytes |
| 평균 응답 시간 | 0.5 ms |
| 초당 최대 트랜잭션 | 30 tps |
| 엔티티 | 후보자 |
| 테이블명 | `POFELCDDREGISTSTTUS` |

### (가) 요청 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
|---|---|---|---|---|---|
| `serviceKey` | 서비스키 | 255 | 필수(1) | - | 공공데이터포털에서 발급받은 인증키 |
| `pageNo` | 페이지 번호 | 6 | 필수(1) | `1` | 페이지 번호 (최대값: 100000) |
| `numOfRows` | 목록 건수 | 3 | 필수(1) | `10` | 목록 건수 (최대값: 100) |
| `resultType` | 결과 유형 | 4 | 옵션(0) | `xml` | default: xml |
| `sgId` | 선거ID | 10 | 필수(1) | `20220309` | 선거ID |
| `sgTypecode` | 선거종류 | 2 | 필수(1) | `1` | 선거종류코드 |
| `sggName` | 선거구명 | 80 | 옵션(0) | `대한민국` | 선거구명 |
| `sdName` | 시도명 | 40 | 옵션(0) | `전국` | 시도명 |

> **항목구분** : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

> **주의사항**
> 1. `sgId`, `sgTypecode`, `sggName`, `sdName`은 코드정보조회 서비스를 이용해서 조회 가능
> 2. 후보자등록일 이후에도 실시간으로 정보변경이 있을 수 있음

### (나) 응답 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
|---|---|---|---|---|---|
| `resultCode` | 결과코드 | 10 | 필수(1) | `INFO-00` | INFO-00: 성공 |
| `resultMsg` | 결과메시지 | 50 | 필수(1) | `NORMAL SERVICE` | - |
| `Items` | 항목 목록 | - | 0..n | - | - |
| `num` | 결과순서 | 8 | 필수(1) | `1` | 결과순서 |
| `sgId` | 선거ID | 10 | 필수(1) | `20220309` | 선거ID |
| `sgTypecode` | 선거종류코드 | 2 | 필수(1) | `1` | 선거종류코드 |
| `huboid` | 후보자ID | 10 | 필수(1) | `10000000` | 후보자ID |
| `sggName` | 선거구명 | 80 | 필수(1) | `대한민국` | 선거구명 |
| `sdName` | 시도명 | 40 | 필수(1) | `전국` | 시도명 (대선, 비례국선: 전국으로 표기 / 그 외: 선거구를 관할하는 시도명) |
| `wiwName` | 구시군명 | 40 | 옵션(0) | `종로구` | 구시군명 (대선, 시도지사, 비례국선, 비례광역, 교육감: 공란 / 그 외: 선거구를 관할하는 구시군명) |
| `giho` | 기호 | 2 | 옵션(0) | `1` | 기호 (비례대표는 추천순위임 / 교육감, 교육의원선거는 제공되지 않음) |
| `gihoSangse` | 기호상세 | 50 | 옵션(0) | - | 기호상세 (구시군의원만 해당 / 가, 나, …) |
| `jdName` | 정당명 | 50 | 필수(1) | `00당` | 정당명 |
| `name` | 한글성명 | 50 | 필수(1) | `홍길동` | 한글성명 |
| `hanjaName` | 한자성명 | 50 | 필수(1) | `洪吉童` | 한자성명 |
| `gender` | 성별 | 2 | 필수(1) | `남` | 성별 |
| `birthday` | 생년월일 | 8 | 필수(1) | `19600101` | 생년월일 |
| `age` | 연령 | 3 | 필수(1) | `57` | 연령 (선거일 기준) |
| `addr` | 주소 | 100 | 옵션(0) | `서울특별시 종로구 청운효자동` | 주소 (상세주소 제외) |
| `jobId` | 직업ID | 2 | 필수(1) | `81` | 직업ID |
| `job` | 직업 | 200 | 필수(1) | `00회사 대표` | 직업 (직업분류 아님) |
| `eduId` | 학력ID | 2 | 필수(1) | `68` | 학력ID |
| `edu` | 학력 | 200 | 필수(1) | `00대학교 졸업` | 학력 (학력분류 아님) |
| `career1` | 경력1 | 200 | 필수(1) | `00협회장` | 경력1 |
| `career2` | 경력2 | 200 | 옵션(0) | `-` | 경력2 |
| `status` | 등록상태 | 20 | 필수(1) | `등록` | 등록상태 (등록, 사퇴, 사망, 등록무효) |
| `numOfRows` | 목록건수 | 3 | 필수(1) | `10` | 목록건수 |
| `pageNo` | 페이지 번호 | 6 | 필수(1) | `1` | 페이지 번호 |
| `totalCount` | 총건수 | 10 | 필수(1) | `10` | 총건수 |

> **항목구분** : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

> **주의사항** : 선거 종료 이후 후보자 주소는 제공되지 않음

### (다) 요청/응답 메시지 예제

**요청 URL (REST/URI)**

```
http://apis.data.go.kr/9760000/PofelcddInfoInqireService/getPofelcddRegistSttusInfoInqire?sgId=20220309&sgTypecode=1&sdName=전국&sggName=대한민국&pageNo=1&numOfRows=10&resultType=xml&serviceKey=서비스키
```

**응답 메시지 예제**

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
        <huboid>10000000</huboid>
        <sggName>대한민국</sggName>
        <sdName>전국</sdName>
        <wiwName></wiwName>
        <giho>1</giho>
        <gihoSangse/>
        <jdName>00당</jdName>
        <name>홍길동</name>
        <hanjaName>洪吉童</hanjaName>
        <gender>남</gender>
        <birthday>19600101</birthday>
        <age>57</age>
        <addr>서울특별시 종로구 청운효자동</addr>
        <jobId>81</jobId>
        <job>00회사 대표</job>
        <eduId>68</eduId>
        <edu>00대학교 졸업</edu>
        <career1>00협회장</career1>
        <career2/>
        <status>등록</status>
      </item>
      <!-- ... 이하 항목 반복 ... -->
    </items>
    <numOfRows>10</numOfRows>
    <pageNo>1</pageNo>
    <totalCount>1</totalCount>
  </body>
</response>
```

---

## 에러 코드

### 2-1. 공공데이터 포털 에러코드

| 에러코드 | 에러메시지 | 설명 |
|---|---|---|
| `1` | `APPLICATION_ERROR` | 어플리케이션 에러 |
| `04` | `HTTP_ERROR` | HTTP 에러 |
| `12` | `NO_OPENAPI_SERVICE_ERROR` | 해당 오픈API 서비스가 없거나 폐기됨 |
| `20` | `SERVICE_ACCESS_DENIED_ERROR` | 서비스 접근거부 |
| `22` | `LIMITED_NUMBER_OF_SERVICE_REQUESTS_EXCEEDS_ERROR` | 서비스 요청제한횟수 초과에러 |
| `30` | `SERVICE_KEY_IS_NOT_REGISTERED_ERROR` | 등록되지 않은 서비스키 |
| `31` | `DEADLINE_HAS_EXPIRED_ERROR` | 활용기간 만료 |
| `32` | `UNREGISTERED_IP_ERROR` | 등록되지 않은 IP |
| `99` | `UNKNOWN_ERROR` | 기타에러 |

> 공공데이터포털에서 출력되는 오류메세지는 XML로만 출력되며, 형태는 아래와 같습니다.

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
| `ERROR-03` | 데이터가 정보가 없습니다. 활용문서를 확인해 주시기 바랍니다. |
| `ERROR-301` | 파일타입 값이 누락 혹은 유효하지 않습니다. 요청인자 중 TYPE를 확인하십시오. |
| `ERROR-310` | 해당하는 서비스를 찾을 수 없습니다. |
| `ERROR-333` | 요청위치 값의 타입이 유효하지 않습니다. 요청위치 값은 정수를 입력하세요. |
| `ERROR-340` | 필수 파라미터가 누락되었습니다. |
| `ERROR-500` | 서버 오류입니다. 지속적으로 발생 시 관리자에게 문의 바랍니다. |
| `ERROR-601` | SQL 문장 오류입니다. 지속적으로 발생 시 관리자에게 문의 바랍니다. |

> 제공기관에서 출력되는 오류메세지는 XML로만 출력되며, 형태는 아래와 같습니다.

```xml
<response>
  <header>
    <resultCode>ERROR-310</resultCode>
    <resultMsg>해당하는 서비스를 찾을 수 없습니다.</resultMsg>
  </header>
</response>
```
