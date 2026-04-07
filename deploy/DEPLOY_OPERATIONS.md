# 배포 운영 가이드

이 문서는 LawDigest의 현재 배포 운영 기준을 한 곳에 모아둔 문서다.

## 적용 범위

- `dev.lawdigest.kr` 프론트엔드
- 테스트 백엔드
- GitHub Actions 기반 자동 배포
- 배포 실패 시 자동 롤백

개별 절차는 아래 문서를 함께 참고한다.

- [Dev Web Deploy Guide](./TEST_WEB_DEPLOY.md)
- [Test Backend Deploy Guide](./TEST_BACKEND_DEPLOY.md)

## 전체 구조

### 프론트엔드

- 자동 배포 워크플로우: [`.github/workflows/deploy-web-dev.yml`](../.github/workflows/deploy-web-dev.yml)
- 배포 스크립트: [`deploy/deploy-test-web.sh`](./deploy-test-web.sh)
- 운영 도메인: `https://dev.lawdigest.kr`
- 런타임 구조: `release/symlink`

### 백엔드

- 자동 배포 워크플로우: [`.github/workflows/deploy-web-dev.yml`](../.github/workflows/deploy-web-dev.yml)
- 배포 스크립트: [`deploy/deploy-test-backend.sh`](./deploy-test-backend.sh)
- 테스트 API 진입점: `https://test.api.lawdigest.kr`
- 런타임 구조: Docker 컨테이너 재기동

### 서버 전제

- GitHub Actions는 GitHub-hosted runner에서 실행되고, SSH로 이 서버에 접속한다.
- 배포 스크립트는 서버의 `.env` 파일을 기준으로 동작한다.
- 프론트는 `services/web/.env`
- 백엔드는 `services/backend/.env`

## 자동 배포 흐름

### 트리거

- `main` 브랜치에 머지되면 자동 실행된다.
- `Deploy Dev` 워크플로우는 변경 파일을 검사해 프론트/백엔드 중 필요한 쪽만 배포한다.
- 수동 실행 시 `target=web | backend | both`를 지정할 수 있다.

### 프론트 배포

1. GitHub Actions에서 프론트 변경 여부를 감지한다.
2. 서버의 `dev-web-release` worktree를 최신 `main` 기준으로 맞춘다.
3. `deploy-test-web.sh`를 실행한다.
4. 스크립트는 새 release를 만든 뒤 staging PM2를 먼저 띄운다.
5. staging 헬스체크가 통과해야 live PM2로 전환한다.
6. live 헬스체크가 실패하면 이전 release로 자동 복구한다.
7. `current` 심링크는 검증 성공 후에만 새 release를 가리킨다.

### 백엔드 배포

1. GitHub Actions에서 백엔드 변경 여부를 감지한다.
2. 서버의 `dev-backend-release` worktree를 최신 `main` 기준으로 맞춘다.
3. `deploy-test-backend.sh`를 실행한다.
4. 스크립트는 staging 컨테이너를 먼저 띄운다.
5. staging 헬스체크가 통과해야 live 컨테이너를 교체한다.
6. live 헬스체크가 실패하면 이전 컨테이너를 자동 복구한다.

## 실패 처리 원칙

- staging 헬스체크가 실패하면 live는 건드리지 않는다.
- live 전환 후 헬스체크가 실패하면 이전 정상 상태로 되돌린다.
- dirty worktree면 배포를 중단한다.
- 배포 스크립트는 서버의 현재 상태를 덮어쓰지 않고, 검증된 경우에만 전환한다.

## 수동 배포

직접 서버에서 돌릴 때는 아래 형태를 사용한다.

```bash
./deploy/deploy-test-web.sh /path/to/target-worktree
./deploy/deploy-test-backend.sh /path/to/target-worktree
```

수동 실행도 자동 배포와 같은 원칙을 따른다.

- 먼저 최신 `main`과 동기화
- staging에서 검증
- 실패 시 자동 롤백

## 확인 방법

### 프론트

```bash
pm2 list
curl -sSI https://dev.lawdigest.kr/election | sed -n '1,20p'
```

### 백엔드

```bash
docker ps --filter "name=lawdigest-backend-test"
curl -sSI http://127.0.0.1:808/ | sed -n '1,20p'
```

## 운영 메모

- 프론트 런타임은 `.runtime/test-web/current`가 기준이다.
- 백엔드는 live 컨테이너가 기준이다.
- 운영자가 수동으로 release 디렉터리나 live 컨테이너를 임의 변경하지 않는 것을 전제로 한다.
- 문제 발생 시 먼저 staging 헬스체크 로그와 live 전환 로그를 확인한다.
