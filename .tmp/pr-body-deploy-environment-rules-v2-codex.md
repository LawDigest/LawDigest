## 요약
- 웹 배포 환경 기준을 운영, 테스트, 개발으로 분리해 스크립트와 문서 기준을 맞췄습니다.
- `dev.lawdigest.kr` 개발 배포가 상속된 `PORT` 환경변수에 흔들리지 않도록 포트 변수를 정리했습니다.
- 테스트 웹 자동 배포 워크플로우 이름을 실제 역할에 맞게 정리했습니다.

## 변경 내용
- `deploy-web-dev.yml`을 `deploy-web-test.yml`로 변경하고 테스트 배포 역할에 맞게 정리했습니다.
- 운영, 테스트, 개발 웹 배포 문서와 운영 가이드를 최신 기준으로 갱신했습니다.
- `deploy/deploy-dev-web.sh`, `deploy/deploy-prod-web.sh`, `deploy/deploy-test-web.sh`, `deploy/deploy-web-release.sh`의 포트 변수 규칙을 정리했습니다.
- 개발 배포 후 `dev.lawdigest.kr`가 `NODE_ENV=development`, `PORT=3021`로 올라오도록 검증했습니다.

## 검증
- `cd services/web && npm run lint`
- `bash -n deploy/deploy-web-release.sh deploy/deploy-prod-web.sh deploy/deploy-test-web.sh deploy/deploy-dev-web.sh`
- `./deploy/deploy-dev-web.sh chore/deploy-environment-rules-v2/codex`
- `curl -sSI https://dev.lawdigest.kr/election?tab=district`
