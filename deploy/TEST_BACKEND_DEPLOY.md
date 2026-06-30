# Legacy Backend Deploy Script Note

이 문서는 기존 `deploy-test-backend.sh` 이름의 호환성을 설명한다.
현재 운영 API 배포 절차는 [PROD_BACKEND_DEPLOY.md](./PROD_BACKEND_DEPLOY.md)를 기준으로 한다.

## 현재 기준

- 운영 API 도메인: `https://api.lawdigest.kr`
- nginx site 파일: `/etc/nginx/sites-enabled/test-back.conf`
- nginx upstream: `test_backend` -> `127.0.0.1:808`
- live 컨테이너: `lawdigest-backend-test`
- 운영 Spring profile: `ACTIVE=prod`
- 운영 API 배포 wrapper: [deploy-prod-backend.sh](./deploy-prod-backend.sh)
- 기존 배포 본체: [deploy-test-backend.sh](./deploy-test-backend.sh)

`deploy-test-backend.sh`는 기존 이름 때문에 남아 있는 배포 본체다.
운영 API 배포에서는 `deploy-prod-backend.sh`가 `ACTIVE=prod`를 지정한 뒤 이 스크립트에 위임한다.

## 직접 실행이 필요한 경우

일반 운영 API 배포는 아래 명령을 사용한다.

```bash
./deploy/deploy-prod-backend.sh /path/to/target-worktree
```

`deploy-test-backend.sh`를 직접 실행하면 기본 `ACTIVE` 값은 `test`다.
운영 API 배포를 위해 직접 실행해야 하는 예외 상황에서는 반드시 `ACTIVE=prod`를 명시한다.

```bash
ACTIVE=prod ./deploy/deploy-test-backend.sh /path/to/target-worktree
```

## 주의사항

- 이 문서는 `.env` 값이나 비밀값을 기록하지 않는다.
- 현재 운영 API 경로에는 `test_backend`, `lawdigest-backend-test`, `.runtime/test-backend/logs` 같은 기존 명칭이 남아 있다.
- 별도 nginx/container 마이그레이션 없이 이 이름들을 바꾸면 운영 API 경로가 끊길 수 있다.
- 실제 운영 배포 절차와 확인 명령은 [PROD_BACKEND_DEPLOY.md](./PROD_BACKEND_DEPLOY.md)를 따른다.
