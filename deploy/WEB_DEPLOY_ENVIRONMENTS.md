# Web Deploy Environments

LawDigest 웹 프론트엔드 배포 기준을 도메인별로 정리한 문서다.

## 배포 기준표

| 도메인 | 역할 | 기준 브랜치 / ref | 실행 모드 | 스크립트 |
| --- | --- | --- | --- | --- |
| `lawdigest.kr`, `www.lawdigest.kr` | 운영용 | `main` | production build | [`deploy-prod-web.sh`](./deploy-prod-web.sh) |
| `test.lawdigest.kr` | 테스트용 | `dev` | production build | [`deploy-test-web.sh`](./deploy-test-web.sh) |
| `dev.lawdigest.kr` | 개발용 | 임의 git ref | `next dev` 개발모드 | [`deploy-dev-web.sh`](./deploy-dev-web.sh) |

## 원칙

- 운영 도메인은 항상 `main` 기준만 배포한다.
- 테스트 도메인은 항상 `dev` 기준만 배포한다.
- 개발 도메인은 배포 시점에 선택한 ref를 그대로 개발모드로 띄운다.
- `dev.lawdigest.kr`은 hot reload와 개발자 오버레이를 유지해야 하므로 production build로 배포하지 않는다.

## 자동 배포 / 수동 배포

- 운영 자동 배포: [`.github/workflows/deploy-web-prod.yml`](../.github/workflows/deploy-web-prod.yml)
- 테스트 자동 배포: [`.github/workflows/deploy-web-dev.yml`](../.github/workflows/deploy-web-dev.yml)
- 개발 수동 배포: [`.github/workflows/deploy-web-dev-mode.yml`](../.github/workflows/deploy-web-dev-mode.yml)

## 세부 절차 문서

- 운영 웹: [PROD_WEB_DEPLOY.md](./PROD_WEB_DEPLOY.md)
- 테스트 웹: [TEST_WEB_DEPLOY.md](./TEST_WEB_DEPLOY.md)
- 개발 웹: [DEV_WEB_DEPLOY.md](./DEV_WEB_DEPLOY.md)
