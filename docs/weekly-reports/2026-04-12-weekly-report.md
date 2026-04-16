# 주간 작업 리포트 — 2026년 4월 7일(월) ~ 4월 12일(토)

**총 커밋**: 56개 | **PR**: 12개 (머지 10개, 오픈 2개)

---

## 요약

이번 주는 **선거 데이터 인프라 전체 스택 구축**에 집중한 한 주였습니다. 중앙선거관리위원회 OpenAPI 파이프라인 구축부터 여론조사 PDF 파서 커버리지 100% 달성, 백엔드 API 구현, 프론트엔드 실데이터 연동까지 선거 기능의 주요 레이어가 순차적으로 완성되었습니다.

---

## 일별 작업 흐름

```
4/7 (월)  ─ 경기도 파이프라인 정리 + 문서 최신화
4/8 (화)  ─ 도메인 이전 + 피드 탭 UI 리디자인 착수
4/10 (목) ─ 선거 파이프라인 구축 + 여론조사 파서 14종 대량 추가 + 피드 UI 머지
4/11 (금) ─ 여론조사 탭 실데이터 연동 + 파서 커버리지 100% + 버그픽스
4/12 (토) ─ 선거 피드 통합 API PR 오픈 + 디자인 복구 픽스
```

---

## 영역별 작업 내역

### 1. 여론조사 파서 — 커버리지 100% 달성

이번 주 가장 많은 커밋이 집중된 영역. 10개 이상의 신규 파서를 추가해 전국 여론조사 PDF 자동 파싱 커버리지를 완성했습니다.

| PR | 내용 |
|----|------|
| [#36](https://github.com/LawDigest/Lawdigest/pull/36) 머지 (4/10) | 코리아정보리서치 86건 + 한국갤럽조사연구소 74건 파서 추가 |
| [#39](https://github.com/LawDigest/Lawdigest/pull/39) 오픈 (4/10) | 이너텍시스템즈 54건 파서 개발 |
| [#40](https://github.com/LawDigest/Lawdigest/pull/40) 머지 (4/11) | KRI(코리아리서치인터내셔널) 파서로 커버리지 100% 달성 |

4/10 단일 브랜치 커밋에서 추가된 파서 (19종):
`리서치제이`, `아이소프트뱅크`, `서던포스트`, `한민리서치`, `피앰아이`, `미디어리서치`, `우리리서치`, `경남통계리서치`, `디오피니언`, `유앤미리서치`, `한국정책연구원`, `KPO리서치`, `리서치웰`, `알앤써치`, `에브리리서치`, `비전코리아`, `모노커뮤니케이션즈`, `리서치뷰`, `이너텍시스템즈`

---

### 2. 선거 데이터 파이프라인 구축

중앙선거관리위원회 OpenAPI를 활용한 선거 데이터 수집 인프라를 전체 구현했습니다.

| PR | 내용 |
|----|------|
| [#35](https://github.com/LawDigest/Lawdigest/pull/35) 머지 (4/10) | 중앙선관위 OpenAPI 수집 파이프라인 구축 — SQLAlchemy ORM, 코드정보 6종, 후보자/당선인/공약 수집기, 제8회(15,750건)·제9회(8,158건) 데이터 적재 |
| [#37](https://github.com/LawDigest/Lawdigest/pull/37) 머지 (4/10) | Airflow DAG 추가 — 매일 새벽 4시 자동 수집, `collect_codes → collect_candidates → collect_winners → collect_pledges` 체인 |

**주요 성과**: 여론조사 테이블과 `normalized_region` 기반 조인 검증 완료 (후보자명 ↔ PollOption 지지율 직접 매칭)

---

### 3. 선거 백엔드 API 8개 엔드포인트 구현

| PR | 내용 |
|----|------|
| [#38](https://github.com/LawDigest/Lawdigest/pull/38) 머지 (4/10) | `/v1/election/selector`, `/overview`, `/map`, `/region-panel`, `/candidates`, `/candidates/{id}`, `/regions/resolve`, `/regions/confirm` |

Spring Boot 엔티티 5개, Repository 4개, DTO 7개, Service/Controller 신규 구현.

---

### 4. 여론조사 탭 실데이터 연동

| PR | 내용 |
|----|------|
| [#41](https://github.com/LawDigest/Lawdigest/pull/41) 머지 (4/11) | 백엔드 여론조사 API 구현 (`overview / party / region / candidate`) + 프론트 실데이터 연동, `PollNormalizationService` / `PollQuestionClassifier` 추가 |

Mock fallback에서 실 API 데이터로 전환 완료. 의뢰처·표본수·오차범위·질문 제목 메타 노출.

---

### 5. 선거 피드 통합 API + 무한 스크롤 (진행 중)

| PR | 내용 |
|----|------|
| [#52](https://github.com/LawDigest/Lawdigest/pull/52) 오픈 (4/12) | 공약/여론조사/일정/법안 4개 소스 단일 커서 기반 피드 통합 API, Base64 opaque 커서, IntersectionObserver 무한 스크롤, PledgeCard·ScheduleCard 신규 |

---

### 6. 피드 탭 UI 리디자인

| PR | 내용 |
|----|------|
| [#34](https://github.com/LawDigest/Lawdigest/pull/34) 머지 (4/10) | SNS/YouTube/법안/여론조사/이미지 5종 카드 시각적 통일, `FeedTypeChip`, `ActiveFilterBadge`, 정당 컬러 바 차트, 공유 유틸(`timeAgo`, `formatCount`) 추가 |

---

### 7. 기타

| PR | 내용 |
|----|------|
| [#33](https://github.com/LawDigest/Lawdigest/pull/33) 머지 (4/8) | `lawdigest.net` → `lawdigest.kr` 도메인 전면 교체 (16개 파일) |
| [#32](https://github.com/LawDigest/Lawdigest/pull/32) 머지 (4/7) | 경기도 여론조사 수집 파이프라인 정리 (DB 업서트 버그 4건 수정) |
| [#31](https://github.com/LawDigest/Lawdigest/pull/31) 머지 (4/7) | 파서 개발 현황 문서 최신화 (11개 기관 완료 반영) |
| 브랜치 직커밋 (4/11~12) | 선거 여론조사 탭·헤더·지도 디자인 복구, dev API 라우팅·인증 픽스 6건 |

---

## 통계 요약

| 항목 | 수치 |
|------|------|
| 총 커밋 | 56개 |
| 머지된 PR | 10개 |
| 오픈 PR | 2개 (#39 이너텍 파서, #52 선거 피드 통합) |
| 신규 여론조사 파서 추가 | ~20종 (커버리지 → 100%) |
| 선거 데이터 수집 건수 | 제8회+제9회 합산 약 27,000건 |
| 신규 백엔드 API 엔드포인트 | 8개 |

---

## 다음 주 예상 작업

1. **PR #52 완성** — 선거 피드 통합 API Sprint 2 (뉴스 피드, 북마크)
2. **PR #39 머지** — 이너텍시스템즈 파서 리뷰 및 머지
3. **여론조사 파서 품질 픽스** — FlowerResearch 등 9개 PDF 0건 반환 이슈 (현재 `fix/poll-quality-fix/codex` 브랜치 완성, PR 대기)
4. **선거 SNS/YouTube 피드 파이프라인** — election_youtube_sns 테이블 마이그레이션 및 수집 DAG 추가
