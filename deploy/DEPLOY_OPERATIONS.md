# 배포 운영 가이드

이 문서는 LawDigest의 현재 배포 운영 기준을 한 곳에 모아둔 문서다.

## 적용 범위

- 웹 프론트엔드 도메인별 배포
- 테스트 백엔드
- GitHub Actions 기반 자동 배포

개별 절차는 아래 문서를 함께 참고한다.

- [Web Deploy Environments](./WEB_DEPLOY_ENVIRONMENTS.md)
- [Prod Web Deploy Guide](./PROD_WEB_DEPLOY.md)
- [Test Web Deploy Guide](./TEST_WEB_DEPLOY.md)
- [Dev Web Deploy Guide](./DEV_WEB_DEPLOY.md)
- [Test Backend Deploy Guide](./TEST_BACKEND_DEPLOY.md)

## 전체 구조

### 프론트엔드

- 운영 자동 배포: [`.github/workflows/deploy-web-prod.yml`](../.github/workflows/deploy-web-prod.yml)
- 테스트 자동 배포: [`.github/workflows/deploy-web-test.yml`](../.github/workflows/deploy-web-test.yml)
- 개발 수동 배포: [`.github/workflows/deploy-web-dev-mode.yml`](../.github/workflows/deploy-web-dev-mode.yml)
- 운영 배포 스크립트: [`deploy/deploy-prod-web.sh`](./deploy-prod-web.sh)
- 테스트 배포 스크립트: [`deploy/deploy-test-web.sh`](./deploy-test-web.sh)
- 개발 배포 스크립트: [`deploy/deploy-dev-web.sh`](./deploy-dev-web.sh)
- 개발 PM2 복구 스크립트: [`deploy/ensure-dev-web-pm2.sh`](./ensure-dev-web-pm2.sh)
- 개발 PM2 watchdog 설치 스크립트: [`deploy/install-dev-web-watchdog.sh`](./install-dev-web-watchdog.sh)

### 백엔드

- 자동 배포 워크플로우: [`.github/workflows/deploy-backend-dev.yml`](../.github/workflows/deploy-backend-dev.yml)
- 배포 스크립트: [`deploy/deploy-test-backend.sh`](./deploy-test-backend.sh)
- 테스트 API 진입점: `https://test.api.lawdigest.kr`
- 런타임 구조: Docker 컨테이너 재기동

### 서버 전제

- GitHub Actions는 GitHub-hosted runner에서 실행되고, SSH로 이 서버에 접속한다.
- 배포 스크립트는 서버의 `.env` 파일을 기준으로 동작한다.
- 프론트는 `services/web/.env`
- 백엔드는 `services/backend/.env`

## 자동 배포 흐름

### 프론트 배포

- 운영 웹
  - `main` 푸시 시 자동 실행
  - `deploy-prod-web.sh`로 production build 배포
- 테스트 웹
  - `dev` 푸시 시 자동 실행
  - `deploy-test-web.sh`로 production build 배포
- 개발 웹
  - 수동 dispatch 시 원하는 `git_ref`를 지정
  - `deploy-dev-web.sh`로 `next dev` 배포
  - PM2 데몬 재시작 후 누락될 수 있으므로 `install-dev-web-watchdog.sh`로 watchdog cron을 유지

### 백엔드 배포

1. GitHub Actions에서 백엔드 변경 여부를 감지한다.
2. 서버의 `dev-backend-release` worktree를 최신 `main` 기준으로 맞춘다.
3. `deploy-test-backend.sh`를 실행한다.
4. 스크립트는 staging 컨테이너를 먼저 띄운다.
5. staging 헬스체크가 통과해야 live 컨테이너를 교체한다.
6. live 헬스체크가 실패하면 이전 컨테이너를 자동 복구한다.

## 수동 배포

직접 서버에서 돌릴 때는 아래 형태를 사용한다.

```bash
./deploy/deploy-prod-web.sh /path/to/target-worktree
./deploy/deploy-test-web.sh /path/to/target-worktree
./deploy/deploy-dev-web.sh <git-ref>
./deploy/install-dev-web-watchdog.sh
./deploy/deploy-test-backend.sh /path/to/target-worktree
```

## 확인 방법

### 프론트

```bash
pm2 list
curl -sSI https://lawdigest.kr/election | sed -n '1,20p'
curl -sSI https://test.lawdigest.kr/election | sed -n '1,20p'
curl -sSI https://dev.lawdigest.kr/election | sed -n '1,20p'
```

### 백엔드

```bash
docker ps --filter "name=lawdigest-backend-test"
curl -sSI http://127.0.0.1:808/ | sed -n '1,20p'
```

## 운영 메모

- 테스트 웹은 `.runtime/test-web/current`가 기준이다.
- 개발 웹은 `.runtime/dev-web/current` 심링크가 가리키는 source worktree가 기준이다.
- 개발 웹은 PM2 dump만 단독으로 신뢰하지 않고 watchdog cron으로 재복구한다.
- 백엔드는 live 컨테이너가 기준이다.
