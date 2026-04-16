# 국가선거정보 당선인 정보 조회 서비스

> 제공기관: 중앙선거관리위원회

---

## 제·개정 이력

| 제·개정 번호 | 제·개정 내용 | 제·개정 일자 |
|---|---|---|
| 3.9 | 제·개정 이력 추가 | 2024.11.01 |
| 3.10 | 서비스 제공자 정보 변경 | 2024.11.05 |
| 3.11 | 주의사항 위치 변경 (응답 메시지 명세 → 요청 메시지 명세) | 2025.02.12 |

---

## 서비스 명세

### 서비스 정보

| 항목 | 내용 |
|---|---|
| 서비스 ID | SC-IFT-05-05 |
| 서비스명(국문) | 당선인 정보 조회 서비스 |
| 서비스명(영문) | WinnerInfoInqireService2 |
| 서비스 설명 | 선거ID와 선거종류코드, 시도명, 선거구명을 입력하여 당선인 정보를 조회할 수 있는 서비스 |
| 서비스 인증/권한 | ✅ 서비스 Key |
| 인터페이스 표준 | ✅ REST (GET) |
| 교환 데이터 표준 | ✅ XML ✅ JSON |
| 서비스 URL(개발/운영) | `http://apis.data.go.kr/9760000/WinnerInfoInqireService2` |
| 서비스 버전 | 1.0 |
| 서비스 시작일 | 2018년 7월 23일 |
| 배포 일자 | 2018년 7월 23일 |
| 서비스 제공자 정보 | 중앙선거관리위원회 정보운영과 김현주 주무관 (ncesan715@nec.go.kr / 02-3294-1159) |
| 데이터 갱신 주기 | 매 선거 종료 후 두 달 이내 |
| 사용 제약 사항 | N/A |

---

## 오퍼레이션 목록

| 번호 | 오퍼레이션 | 설명 |
|---|---|---|
| 1 | getWinnerInfoInqire | 당선인 정보 조회 |

---

## 오퍼레이션 명세

### getWinnerInfoInqire — 당선인 정보 조회

| 항목 | 내용 |
|---|---|
| 오퍼레이션 번호 | 1 |
| 오퍼레이션 유형 | 조회(목록) |
| 오퍼레이션 설명 | 선거ID, 선거종류코드, 시도명, 선거구명을 입력받아 당선인 관련 정보를 조회할 수 있는 당선인정보 조회 서비스 |
| Call Back URL | `http://apis.data.go.kr/9760000/WinnerInfoInqireService2/getWinnerInfoInqire` |
| 최대 메시지 사이즈 | 123 bytes |
| 평균 응답 시간 | 0.5ms |
| 초당 최대 트랜잭션 | 30tps |
| 엔티티 | 당선인 |
| 테이블명 | WINNER |

---

## 요청 메시지 명세

### 요청 파라미터

| 항목명 | 항목설명 | 항목크기 | 항목구분 | 샘플데이터 | 비고 |
|---|---|---|---|---|---|
| serviceKey | 서비스키 | 255 | 필수(1) | | 공공데이터포털에서 발급받은 인증키 |
| pageNo | 페이지 번호 | 6 | 필수(1) | 1 | 페이지 번호 (최대값: 100000) |
| numOfRows | 목록 건수 | 3 | 필수(1) | 10 | 목록 건수 (최대값: 100) |
| resultType | 결과형식 | 4 | 옵션(0) | xml | default: xml |
| sgId | 선거ID | 10 | 필수(1) | 20220309 | 선거ID |
| sgTypecode | 선거종류코드 | 2 | 필수(1) | 1 | 선거종류코드 |
| sdName | 시도명 | 40 | 옵션(0) | 전국 | 시도명 |
| sggName | 선거구명 | 80 | 옵션(0) | 대한민국 | 선거구명 |

### 주의사항

- `sgId`, `sgTypecode`, `sdName`, `sggName`은 코드정보조회 서비스를 이용해서 조회 가능
- 선거통계 홈페이지(info.nec.go.kr)에 역대 선거로 이동된 선거의 후보자 주소는 제공되지 않음

---

## 응답 메시지 명세

### 응답 필드

| 항목명 | 항목설명 | 항목크기 | 항목구분 | 샘플데이터 | 비고 |
|---|---|---|---|---|---|
| resultCode | 결과코드 | 2 | 필수(1) | INFO-00 | INFO-00: 성공 |
| resultMsg | 결과메시지 | 10 | 필수(1) | NORMAL SERVICE | |
| num | 결과순서 | 8 | 필수(1) | 1 | |
| sgId | 선거ID | 10 | 필수(1) | 20220309 | |
| sgTypecode | 선거종류코드 | 2 | 필수(1) | 1 | |
| huboid | 후보자ID | 10 | 필수(1) | 10000000 | |
| sggName | 선거구명 | 80 | 필수(1) | 대한민국 | |
| sdName | 시도명 | 40 | 필수(1) | 전국 | 대선/비례국선: 전국, 그 외: 선거구 관할 시도명 |
| wiwName | 구시군명 | 40 | 옵션(0) | | 대선/시도지사/비례국선/비례광역/교육감: 공란, 그 외: 구시군명 |
| giho | 기호 | 2 | 옵션(0) | 1 | 기호 (비례대표는 추천순위) |
| gihoSangse | 기호상세 | 50 | 옵션(0) | | 구시군의원만 해당 (가, 나, …) |
| jdName | 정당명 | 50 | 필수(1) | 00당 | |
| name | 한글성명 | 50 | 필수(1) | 홍길동 | |
| hanjaName | 한자성명 | 50 | 필수(1) | 洪吉童 | |
| gender | 성별 | 2 | 필수(1) | 남 | |
| birthday | 생년월일 | 8 | 필수(1) | 19600101 | |
| age | 연령 | 2 | 필수(1) | 57 | 선거일 기준 |
| addr | 주소 | 100 | 옵션(0) | 서울특별시 종로구 청운효자동 | 상세주소 제외 |
| jobId | 직업ID | 2 | 필수(1) | 81 | |
| job | 직업 | 200 | 필수(1) | 00회사 대표 | 직업분류 아님 |
| eduId | 학력ID | 2 | 필수(1) | 68 | |
| edu | 학력 | 200 | 필수(1) | 00대학교 졸업 | 학력분류 아님 |
| career1 | 경력1 | 200 | 필수(1) | 00협회장 | |
| career2 | 경력2 | 200 | 옵션(0) | - | |
| dugsu | 득표수 | 10 | 옵션(0) | 1000 | |
| dugyul | 득표율 | 10 | 옵션(0) | 10.00 | (%) |
| numOfRows | 목록건수 | 3 | 필수(1) | 10 | |
| pageNo | 페이지 번호 | 6 | 필수(1) | 1 | |
| totalCount | 총건수 | 10 | 필수(1) | 10 | |

---

## API 호출 예제

### 요청 URL

```
http://apis.data.go.kr/9760000/WinnerInfoInqireService2/getWinnerInfoInqire?sgId=20220309&sgTypecode=1&sdName=전국&sggName=대한민국&pageNo=1&numOfRows=10&resultType=xml&serviceKey=서비스키
```

### 응답 예제 (XML)

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
        <dugsu>1000</dugsu>
        <dugyul>10</dugyul>
      </item>
    </items>
    <numOfRows>10</numOfRows>
    <pageNo>1</pageNo>
    <totalCount>1</totalCount>
  </body>
</response>
```

---

## 에러코드

### 공공데이터포털 에러코드

| 에러코드 | 에러명 | 설명 |
|---|---|---|
| 1 | APPLICATION_ERROR | 어플리케이션 에러 |
| 04 | HTTP ERROR | HTTP 에러 |
| 12 | NO_OPENAPI_SERVICE_ERROR | 해당 오픈API 서비스가 없거나 폐기됨 |
| 20 | SERVICE_ACCESS_DENIED_ERROR | 서비스 접근거부 |
| 22 | LIMITED_NUMBER_OF_SERVICE_REQUESTS_EXCEEDS_ERROR | 서비스 요청제한횟수 초과에러 |
| 30 | SERVICE_KEY_IS_NOT_REGISTERED_ERROR | 등록되지 않은 서비스키 |
| 31 | DEADLINE_HAS_EXPIRED_ERROR | 활용기간 만료 |
| 32 | UNREGISTERED_IP_ERROR | 등록되지 않은 IP |
| 99 | UNKNOWN_ERROR | 기타에러 |

### 제공기관 에러코드

| 에러코드 | 설명 |
|---|---|
| ERROR-03 | 데이터가 정보가 없습니다. 활용문서를 확인해 주시기 바랍니다. |
| ERROR-301 | 파일타입 값이 누락 혹은 유효하지 않습니다. 요청인자 중 TYPE를 확인하십시오. |
| ERROR-310 | 해당하는 서비스를 찾을 수 없습니다. |
| ERROR-333 | 요청위치 값의 타입이 유효하지 않습니다. 요청위치 값은 정수를 입력하세요. |
| ERROR-340 | 필수 파라미터가 누락되었습니다. |
| ERROR-500 | 서버 오류입니다. 지속적으로 발생 시 관리자에게 문의 바랍니다. |
| ERROR-601 | SQL 문장 오류입니다. 지속적으로 발생 시 관리자에게 문의 바랍니다. |

### 에러 응답 예제 (XML)

```xml
<!-- 공공데이터포털 에러 -->
<OpenAPI_ServiceResponse>
  <cmmMsgHeader>
    <errMsg>SERVICE ERROR</errMsg>
    <returnAuthMsg>SERVICE_KEY_IS_NOT_REGISTERED_ERROR</returnAuthMsg>
    <returnReasonCode>30</returnReasonCode>
  </cmmMsgHeader>
</OpenAPI_ServiceResponse>

<!-- 제공기관 에러 -->
<response>
  <header>
    <resultCode>ERROR-310</resultCode>
    <resultMsg>해당하는 서비스를 찾을 수 없습니다.</resultMsg>
  </header>
</response>
```
