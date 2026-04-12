# 여론조사 정당명 정규화 규칙

## 목적

여론조사 파이프라인에서 같은 정당이 공백 차이만으로 서로 다른 `PollOption.option_name`으로 적재되는 문제를 막는다. 이 규칙은 적재 단계, 백엔드 조회 단계, 프런트 표시 단계가 같은 canonical 정당명을 쓰도록 맞추기 위한 기준 문서다.

## 적용 지점

- 적재 단계: `services/data/src/lawdigest_data/polls/workflow.py`
- 적재용 유틸: `services/data/src/lawdigest_data/polls/normalization.py`
- 백필 스크립트: `services/data/scripts/db/backfill_poll_party_option_names.py`
- 조회 단계: `services/backend/src/main/java/com/everyones/lawmaking/service/election/poll/PollNormalizationService.java`
- 표시 단계: `services/web/app/election/utils/partyName.ts`

## 정규화 규칙

1. 원본 문자열 앞뒤 공백을 제거한다.
2. 공백을 모두 제거한 비교 키를 만든다.
3. 비교 키가 canonical 정당명 목록과 일치하면 canonical 이름으로 치환한다.
4. 일치하지 않으면 원본 trimmed 값을 유지한다.
5. `undecided`는 그대로 유지한다.

## canonical 정당명 목록

- 더불어민주당
- 국민의힘
- 개혁신당
- 조국혁신당
- 진보당
- 정의당
- 기본소득당
- 새로운미래
- 자유통일당
- 민주노동당
- 노동당
- 녹색당
- 무소속

## 현재 보장하는 예시

- `더불어 민주당` -> `더불어민주당`
- `국민의 힘` -> `국민의힘`
- `조국 혁신당` -> `조국혁신당`
- `조국혁 신당` -> `조국혁신당`

## 운영 원칙

- 새 변형 표기가 발견되면 먼저 canonical 목록으로 흡수 가능한지 확인한다.
- 공백 차이 외 별도 별칭이 필요한 경우에는 데이터/백엔드/프런트 정규화 구현을 함께 갱신한다.
- parser 결과 JSON은 원문 보존이 가능하지만, `PollOption.option_name`에는 canonical 값이 적재되도록 유지한다.

## 기존 데이터 백필

- preview:
  `python3 services/data/scripts/db/backfill_poll_party_option_names.py --mode test`
- apply:
  `python3 services/data/scripts/db/backfill_poll_party_option_names.py --mode test --apply`
- 운영 DB 반영 시에는 `--mode prod --apply`를 사용하되, preview를 먼저 실행한다.
