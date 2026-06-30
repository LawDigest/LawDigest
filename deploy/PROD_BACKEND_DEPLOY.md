# Prod Backend Deploy Guide

`api.lawdigest.kr` 운영 API 백엔드 배포 절차다.

운영 전체 기준은 [DEPLOY_OPERATIONS.md](./DEPLOY_OPERATIONS.md)를 먼저 참고한다.
이 문서는 서버의 비밀값이나 `.env` 내용을 기록하지 않는다.

## 현재 구조

- 운영 API 도메인: `https://api.lawdigest.kr`
- nginx site 파일: `/etc/nginx/sites-enabled/test-back.conf`
- nginx upstream 이름: `test_backend`
- nginx upstream 대상: `127.0.0.1:808`
- Docker 컨테이너 이름: `lawdigest-backend-test`
- Docker 이미지 이름: `lawdigest-backend-test`
- host 포트: `808`
- 컨테이너 내부 포트: `8080`
- Docker 네트워크: `law_prod_network`
- Spring profile: `ACTIVE=prod`
- 배포 wrapper: [deploy-prod-backend.sh](./deploy-prod-backend.sh)
- 기존 배포 본체: [deploy-test-backend.sh](./deploy-test-backend.sh)

`test_backend` upstream과 `lawdigest-backend-test` 컨테이너 이름은 현재 서버에 남아 있는
기존 명칭이다. 실제로는 `api.lawdigest.kr` 운영 API 요청을 처리한다.

## 동작 방식

`deploy-prod-backend.sh`는 운영 API 배포용 wrapper다.
이 wrapper는 `ACTIVE=prod`와 배포 라벨만 지정한 뒤 기존 `deploy-test-backend.sh`에 위임한다.
따라서 staging 컨테이너 헬스체크, live 전환, 실패 시 rollback 복구 동작은 기존 스크립트와 같다.

기존 `deploy-test-backend.sh`는 이름 호환성을 위해 유지한다.
운영 API 배포에서는 직접 실행하지 말고 `deploy-prod-backend.sh`를 사용한다.

## 배포 명령

```bash
cd /home/ubuntu/project/Lawdigest/.worktrees/hydrate-missing-summary-codex
./deploy/deploy-prod-backend.sh /home/ubuntu/project/Lawdigest/.worktrees/hydrate-missing-summary-codex
```

다른 worktree를 배포할 때는 첫 번째 인자만 대상 worktree 경로로 바꾼다.

```bash
./deploy/deploy-prod-backend.sh /path/to/target-worktree
```

## 배포 확인

```bash
docker ps --filter "name=lawdigest-backend-test"
docker inspect lawdigest-backend-test --format '{{range .Config.Env}}{{if eq . "ACTIVE=prod"}}{{.}}{{end}}{{end}}'
curl -sSI http://127.0.0.1:808/ | sed -n '1,20p'
curl -sSI https://api.lawdigest.kr/ | sed -n '1,20p'
```

정상 기준:

- `lawdigest-backend-test` 컨테이너가 `Up`
- 컨테이너 환경에 `ACTIVE=prod`가 적용됨
- `127.0.0.1:808`이 HTTP 헤더를 반환
- `https://api.lawdigest.kr/`이 HTTP 헤더를 반환

## 주의사항

- `services/backend/.env`는 루트 저장소 기준 파일을 사용하지만, 파일 내용은 출력하거나 문서화하지 않는다.
- 운영 API는 현재 `test_backend`, `lawdigest-backend-test`, `.runtime/test-backend/logs` 같은 기존 명칭을 재사용한다.
- 이 명칭은 현재 서버 구조를 반영한 호환 이름이며, 별도 마이그레이션 없이 바꾸면 nginx나 운영 컨테이너 경로가 끊길 수 있다.
- host의 `127.0.0.1:808`은 nginx가 바라보는 운영 API 진입점이다.
- `mysql` / `redis` 같은 Docker 네트워크 호스트명은 `law_prod_network`에서 해석된다.
- DB 삭제, 볼륨 초기화, 컨테이너 일괄 삭제 같은 파괴적 작업은 이 절차에 포함하지 않는다.
