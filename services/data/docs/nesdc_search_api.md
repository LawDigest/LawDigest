# NESDC 여론조사 목록 검색 API

> 기준일: 2026-04-03  
> 대상: https://www.nesdc.go.kr/portal/bbs/B0000005/list.do

---

## 엔드포인트

```
GET https://www.nesdc.go.kr/portal/bbs/B0000005/list.do
```

---

## 검색 파라미터

| 파라미터 | 설명 | 예시 |
|---------|------|------|
| `menuNo` | 고정값 | `200467` |
| `pageIndex` | 페이지 번호 (1부터) | `1` |
| `pollGubuncd` | 선거구분 코드 | `VT026` |
| `searchCnd` | 검색 카테고리 코드 | `4` |
| `searchWrd` | 검색어 (텍스트) | `경기도` |
| `searchTime` | 날짜구분 | `1` |
| `sdate` | 시작일 (YYYY-MM-DD) | `2025-01-01` |
| `edate` | 종료일 (YYYY-MM-DD) | `2026-04-01` |

---

## searchCnd 코드표

| 값 | 검색 카테고리 | 설명 |
|----|------------|------|
| `1` | 조사기관명 | 여론조사 수행 기관 |
| `2` | 조사의뢰자 | 조사를 의뢰한 언론사/단체 |
| `3` | 여론조사명칭(지역) | 조사명 + 지역 통합 텍스트 검색 |
| `4` | **시·도** | 시도 단위 지역 필터 (권장) |
| `5` | 등록번호 | 고유 등록번호 |
| `6` | 조사방법 | 전화/온라인 등 조사방법 |
| `11` | 표본 추출틀 | 표본 추출 방법 |

---

## pollGubuncd 코드 (확인된 값)

| 값 | 선거구분 |
|----|---------|
| `VT026` | 제9회 전국동시지방선거 |

> 전체 코드는 NESDC 검색 페이지 HTML의 `<select name="pollGubuncd">` 옵션에서 확인 가능.

---

## searchTime 코드표

| 값 | 날짜구분 |
|----|---------|
| `1` | 등록일 |
| `2` | 최초공표일 |
| `3` | 조사일시 |

---

## 필터링 전략

### 서버 사이드 필터 (NESDC 검색 파라미터)

- `pollGubuncd`: 선거 단위로 1차 축소
- `searchCnd=4` + `searchWrd={시도명}`: 시·도 단위로 2차 축소

```
pollGubuncd=VT026 + searchCnd=4 + searchWrd=경기도
→ 서버가 경기도 관련 170건만 반환
```

### 클라이언트 사이드 필터 (`matches_target()`)

서버 반환 결과에서 `election_names`, `region` 조건으로 추가 필터링.

```python
# poll_targets.json 기준
election_names: ["광역단체장선거"]  # 기초단체장, 교육감 등 제외
region: "경기도 전체"               # 시/군 단위 제외
```

---

## 권장 요청 예시

경기도 제9회 전국동시지방선거 광역단체장 여론조사:

```
GET /portal/bbs/B0000005/list.do
  ?menuNo=200467
  &pollGubuncd=VT026
  &searchCnd=4
  &searchWrd=경기도
  &pageIndex=1
```

결과: 경기도 170건 (필터 없이 요청 시 전체 1221건)

---

## 현재 코드 현황

`collect_poll_list.py`는 현재 `pollGubuncd`만 전달하고 `searchCnd`/`searchWrd`를 전달하지 않아 전체 1221건을 수집한다.

`PollTarget`의 `search_keyword` 필드를 `search_cnd` + `search_wrd`로 교체하고, `collect_poll_list.py`에서 해당 파라미터를 전달하도록 개선이 필요하다.

> 관련 이슈: 서버 사이드 필터링 미적용으로 불필요한 크롤링 발생
