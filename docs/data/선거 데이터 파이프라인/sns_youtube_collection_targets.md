# 선거 피드 SNS/YouTube 수집 대상 목록

**작성일**: 2026-04-12  
**대상 선거**: 제9회 전국동시지방선거 (2026-06-03)  
**기준일**: 2026-04-12 (후보 등록 완료 2026-05-15 이후 전면 업데이트 예정)  
**관련 config 파일**:
- `services/data/config/election_sns_accounts.json`
- `services/data/config/election_youtube_channels.json`

---

## 개요

2026 지방선거 피드 탭의 SNS/YouTube 콘텐츠 수집을 위한 대상 계정 목록.  
Sprint 3에서 구현 예정 (API 키 발급 후 진행).

**수집 플랫폼**:
- **X(트위터)**: 정당 공식 + 제9회 지방선거 광역단체장 후보
- **Facebook**: 정당 공식 페이지 + 후보 개인 페이지 (2차)
- **YouTube**: 정당 공식 채널 + 후보 개인 채널 (Data API v3, 2시간 간격)

**검증 상태 범례**:
- ✅ 확인됨 (계정/채널 직접 확인)
- ⚠️ 미확인 (핸들 추정 또는 계정 존재 불명)
- 🔄 결선/경선 진행 중 (확정 후 업데이트 필요)

---

## X(트위터) — 정당 공식 계정

| 정당 | X 핸들 | 상태 |
|------|--------|------|
| 더불어민주당 | [@TheMinjoo_Kr](https://x.com/TheMinjoo_Kr) | ✅ |
| 국민의힘 | 미확인 | ⚠️ [peoplepowerparty.kr](https://www.peoplepowerparty.kr/) 에서 확인 필요 |
| 조국혁신당 | 미확인 | ⚠️ [rebuildingkoreaparty.kr](https://rebuildingkoreaparty.kr/) 에서 확인 필요 |
| 개혁신당 | 미확인 | ⚠️ [reformparty.kr](https://www.reformparty.kr/) 에서 확인 필요 |
| 정의당 | [@Kr_Justice](https://x.com/Kr_Justice) | ✅ |
| 중앙선거관리위원회 | [@nec_korea](https://x.com/nec_korea) | ✅ |

---

## X(트위터) — 제9회 지방선거 광역단체장 후보

> **주의**: 2026-04-12 기준 공천 현황. 공식 후보 등록(2026-05-14~15) 이후 전면 업데이트 필요.

### 더불어민주당

| 지역 | 후보 | 공천 상태 | X 핸들 | 상태 |
|------|------|-----------|--------|------|
| 서울 | 정원오 | ✅ 확정 | 미확인 | ⚠️ |
| 경기 | 추미애 | ✅ 확정 | [@ChooMiAe](https://x.com/ChooMiAe) | ✅ |
| 인천 | 박찬대 | ✅ 확정 | [@ALchandae](https://x.com/ALchandae) | ✅ |
| 부산 | 전재수 | ✅ 확정 | 미확인 | ⚠️ |
| 대구 | 김부겸 | ✅ 확정 | 미확인 | ⚠️ |
| 강원 | 우상호 | ✅ 확정 | 미확인 | ⚠️ (FB: @woosangho 확인) |
| 울산 | 김상욱 | ✅ 확정 | 미확인 | ⚠️ |
| 경남 | 김경수 | ✅ 확정 | 미확인 | ⚠️ |
| 충북 | 신용한 | ✅ 확정 | 미확인 | ⚠️ |
| 전북 | 이원택 | ✅ 확정 | 미확인 | ⚠️ |
| 경북 | 오중기 | ✅ 확정 | 미확인 | ⚠️ |
| 대전 | 장철민 or 허태정 | 🔄 결선 | 미확인 | ⚠️ |
| 광주·전남 | 민형배 or 김영록 | 🔄 결선 | 미확인 | ⚠️ |
| 충남 | 미정 | — | — | — |
| 세종 | 미정 | — | — | — |
| 제주 | 미정 | — | — | — |

### 국민의힘

| 지역 | 후보 | 공천 상태 | X 핸들 | 상태 |
|------|------|-----------|--------|------|
| 서울 | 오세훈 | 🔄 경선(4/18 확정) | [@ohsehoon_seoul](https://x.com/ohsehoon_seoul) | ✅ |
| 부산 | 박형준 | ✅ 확정 | 미확인 | ⚠️ |
| 인천 | 유정복 | ✅ 확정 | 미확인 | ⚠️ |
| 경남 | 박완수 | ✅ 확정 | 미확인 | ⚠️ |
| 대전 | 미정 | — | — | — |
| 대구 | 미정 | — | — | — |
| 그 외 | 미정 | — | — | — |

---

## Facebook — 확인된 계정

| 구분 | 계정 | 상태 |
|------|------|------|
| 국민의힘 공식 | [@peoplepowerpartyfb](https://www.facebook.com/peoplepowerpartyfb/) | ✅ |
| 조국혁신당 공식 | [@RebuildingKorea](https://www.facebook.com/RebuildingKorea/) | ✅ |
| 오세훈 (서울) | [@ohsehoon4you](https://www.facebook.com/ohsehoon4you/) | ✅ |
| 추미애 (경기) | [@choomiae](https://www.facebook.com/choomiae/) | ✅ |
| 우상호 (강원) | [@woosangho](https://www.facebook.com/woosangho/) | ✅ |

---

## YouTube — 정당 공식 채널

| 채널명 | 정당 | 채널 ID | 상태 |
|--------|------|---------|------|
| 델리민주 | 더불어민주당 | `UCoQD2xsqwzJA93PTIYERokg` | ✅ |
| 국민의힘TV | 국민의힘 | `UCGd1rNecfS_MND8PQsKOJhQ` | ✅ |
| 조국혁신당 | 조국혁신당 | 미확인 | ⚠️ @RebuildingKorea 추정 |
| 개혁신당 | 개혁신당 | 미확인 | ⚠️ |
| 정의당 | 정의당 | 미확인 | ⚠️ |
| 중앙선거관리위원회 | — | 미확인 | ⚠️ |

## YouTube — 제9회 지방선거 후보 개인 채널

| 후보 | 지역 | 정당 | 채널 ID | 상태 |
|------|------|------|---------|------|
| 오세훈 | 서울 | 국민의힘 | 미확인 | ⚠️ 오세훈TV (2019 개설) |
| 정원오 | 서울 | 더불어민주당 | 미확인 | ⚠️ 채널 존재 여부 불명 |
| 추미애 | 경기 | 더불어민주당 | 미확인 | ⚠️ |
| 김부겸 | 대구 | 더불어민주당 | 미확인 | ⚠️ |
| 김경수 | 경남 | 더불어민주당 | 미확인 | ⚠️ |
| 박형준 | 부산 | 국민의힘 | 미확인 | ⚠️ |

---

## API 계획

### X(트위터) API
- **Free tier** (월 1,500건 읽기) 기준: 정당 6 + 후보 최대 34명 = 40개 계정
- 4시간 간격 수집 → 월 40 × 6 × 30 = **7,200건** (Free tier 초과 가능)
- **권장**: Basic tier ($100/월) 또는 수집 후보 30명 이내로 제한
- **필요 자격증명**: X API v2 Bearer Token

### YouTube Data API v3
- `playlistItems.list` (1 quota/요청) 사용
- 채널 12개 × 2시간 간격 = 일 144 quota (무료 한도 10,000의 1.4%)
- **필요 자격증명**: YouTube Data API v3 Key (Google Cloud Console)

---

## 미확인 계정 검증 방법

### X 핸들 찾기
1. 각 정당/후보 공식 홈페이지 하단 소셜 링크 확인
2. X에서 이름 검색 → 인증 배지(파란 체크) 확인
3. 확인 후 `election_sns_accounts.json`의 `"verified": false` 항목 업데이트

### YouTube 채널 ID 찾기
1. YouTube 채널 페이지 방문
2. 채널 URL에서 `/channel/UC...` 부분 추출  
   또는 페이지 소스에서 `"channelId":"UC..."` 검색
3. 확인 후 `election_youtube_channels.json`의 `"channelId": null` 항목 업데이트

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-04-12 | 초안 작성 (현직 단체장 기준) |
| 2026-04-12 | **재수집: 제9회 지방선거 공천 현황 기준으로 전면 교체** |
| — | 후보 등록 완료 후 (2026-05-15) 실제 등록 후보로 전면 업데이트 예정 |

---

## 참고 자료

- [선거 피드 콘텐츠 확장 계획](../../../docs/superpowers/plans/2026-04-12-election-feed-content-expansion-plan.md)
- [더불어민주당 2026WIN 선거 페이지](https://2026win.kr/)
- [중앙선거관리위원회](https://www.nec.go.kr)
- [X API v2 공식 문서](https://developer.x.com/en/docs/x-api)
- [YouTube Data API v3 공식 문서](https://developers.google.com/youtube/v3)
