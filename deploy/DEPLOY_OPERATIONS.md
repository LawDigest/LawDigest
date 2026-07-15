# 배포 운영 가이드

이 문서는 LawDigest의 현재 배포 운영 기준을 한 곳에 모아둔 문서다.

## 적용 범위

- 웹 프론트엔드 도메인별 배포
- 운영 API 백엔드
- 서버 로컬 셸에서 실행하는 배포 스크립트

Airflow는 적용 범위에 포함되지 않는다. `infra/airflow/`는 과거 구성을 확인하기
위한 legacy reference이며 빌드·배포·운영 서버 기동 대상으로 사용하지 않는다.
데이터 파이프라인은 `services/data/src/lawdigest_data/runtime/`의 자체 런타임을
사용한다.

개별 절차는 아래 문서를 함께 참고한다.

- [Web Deploy Environments](./WEB_DEPLOY_ENVIRONMENTS.md)
- [Prod Web Deploy Guide](./PROD_WEB_DEPLOY.md)
- [Test Web Deploy Guide](./TEST_WEB_DEPLOY.md)
- [Dev Web Deploy Guide](./DEV_WEB_DEPLOY.md)
- [Prod Backend Deploy Guide](./PROD_BACKEND_DEPLOY.md)
- [GitHub Actions Production Deploy](./GITHUB_ACTIONS_DEPLOY.md)

## 전체 구조

### 프론트엔드

- 운영 배포 스크립트: [`deploy/deploy-prod-web.sh`](./deploy-prod-web.sh)
- 테스트 배포 스크립트: [`deploy/deploy-test-web.sh`](./deploy-test-web.sh)
- 개발 배포 스크립트: [`deploy/deploy-dev-web.sh`](./deploy-dev-web.sh)
- 개발 PM2 복구 스크립트: [`deploy/ensure-dev-web-pm2.sh`](./ensure-dev-web-pm2.sh)
- 개발 PM2 watchdog 설치 스크립트: [`deploy/install-dev-web-watchdog.sh`](./install-dev-web-watchdog.sh)

### 백엔드

- 운영 API 배포 wrapper: [`deploy/deploy-prod-backend.sh`](./deploy-prod-backend.sh)
- 기존 배포 본체: [`deploy/deploy-test-backend.sh`](./deploy-test-backend.sh)
- 운영 API 진입점: `https://api.lawdigest.kr`
- nginx 경로: `/etc/nginx/sites-enabled/test-back.conf`
- nginx upstream: `test_backend` -> `127.0.0.1:808`
- live 컨테이너: `lawdigest-backend-test` (`ACTIVE=prod`)
- 런타임 구조: Docker 컨테이너 재기동

### 서버 전제

- 운영 웹과 백엔드는 `main` push를 기준으로 GitHub Actions에서 배포한다.
- GitHub Actions는 변경된 서비스만 검증하고 정확한 `main` 커밋을 서버 worktree로 배포한다.
- Airflow는 자동·수동 배포 대상이 아니며 Airflow 배포 스크립트를 두지 않는다.
- 서버 로컬 배포 스크립트는 GitHub Actions의 실행 본체이자 장애 시 수동 복구 경로로 유지한다.
- 배포 스크립트는 서버의 `.env` 파일을 기준으로 동작한다.
- 프론트는 `services/web/.env`
- 백엔드는 `services/backend/.env`

## 배포 흐름

### GitHub Actions 운영 배포

1. PR이 `main`에 머지된다.
2. 워크플로가 직전 `main` 커밋과 새 커밋 사이의 변경 경로를 확인한다.
3. 웹 또는 백엔드 중 변경된 서비스만 lint/test/build 검증한다.
4. 모든 대상 검증이 통과하면 SSH로 Oracle 서버에 접속한다.
5. 서버는 커밋이 `origin/main`에 포함됐는지 확인하고 전용 worktree에서 배포한다.
6. 백엔드는 staging 헬스체크와 rollback, 웹은 release 헬스체크와 이전 release 복구를 수행한다.

### 프론트 배포

- 운영 웹
  - `main` 기준 worktree를 준비한다.
  - `deploy-prod-web.sh`로 production build 배포
- 테스트 웹
  - `dev` 기준 worktree를 준비한다.
  - `deploy-test-web.sh`로 production build 배포
- 개발 웹
  - 원하는 `git_ref`를 지정한다.
  - `deploy-dev-web.sh`로 `next dev` 배포
  - PM2 데몬 재시작 후 누락될 수 있으므로 `install-dev-web-watchdog.sh`로 watchdog cron을 유지

### 백엔드 배포

1. 배포 대상 worktree를 배포할 ref 기준으로 맞춘다.
2. `deploy-prod-backend.sh`를 실행한다.
3. 스크립트는 staging 컨테이너를 먼저 띄운다.
4. staging 헬스체크가 통과해야 live 컨테이너를 교체한다.
5. live 헬스체크가 실패하면 이전 컨테이너를 자동 복구한다.

## 수동 배포

직접 서버에서 돌릴 때는 아래 형태를 사용한다.

```bash
./deploy/deploy-prod-web.sh /path/to/target-worktree
./deploy/deploy-test-web.sh /path/to/target-worktree
./deploy/deploy-dev-web.sh <git-ref>
./deploy/install-dev-web-watchdog.sh
./deploy/deploy-prod-backend.sh /path/to/target-worktree
```

## 확인 방법

### 프론트

```bash
pm2 list
curl -sSI https://lawdigest.kr/ | sed -n '1,20p'
curl -sSI https://test.lawdigest.kr/ | sed -n '1,20p'
curl -sSI https://dev.lawdigest.kr/ | sed -n '1,20p'
```

### 백엔드

```bash
docker ps --filter "name=lawdigest-backend-test"
docker inspect lawdigest-backend-test --format '{{range .Config.Env}}{{if eq . "ACTIVE=prod"}}{{.}}{{end}}{{end}}'
curl -sSI http://127.0.0.1:808/ | sed -n '1,20p'
curl -sSI https://api.lawdigest.kr/ | sed -n '1,20p'
```

## 운영 메모

- 테스트 웹은 `.runtime/test-web/current`가 기준이다.
- 개발 웹은 `.runtime/dev-web/current` 심링크가 가리키는 source worktree가 기준이다.
- 개발 웹은 PM2 dump만 단독으로 신뢰하지 않고 watchdog cron으로 재복구한다.
- 백엔드는 `api.lawdigest.kr` 운영 API를 처리하는 live 컨테이너가 기준이다.
- 현재 운영 API 경로에는 `test_backend`, `lawdigest-backend-test` 같은 기존 명칭이 남아 있다.
