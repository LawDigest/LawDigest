# Test Backend Deploy Guide

`test.api.lawdigest.net`용 백엔드 테스트 배포 절차 문서다.

이 테스트 백엔드는 host에서 직접 `java -jar`로 띄우지 않는다.
대신 `services/backend/.env`를 그대로 읽어서 Docker 컨테이너를 올리고,
컨테이너를 `law_prod_network`에 붙인 뒤 host 808 포트로 노출한다.

## 목적
- `services/backend/.env`를 기준으로 테스트 백엔드를 빠르게 재배포
- `mysql` / `redis` 같은 Docker 네트워크 호스트명을 그대로 사용
- nginx가 바라보는 host 808 포트만 유지
- backend 코드는 worktree 기준으로 빌드하고 실행은 고정 컨테이너에서 수행

## 구성
- 도메인: `http://127.0.0.1:808`
- 실제 테스트 API 도메인: `https://test.api.lawdigest.net`
- 컨테이너 이름: `lawdigest-backend-test`
- host 포트: `808`
- Docker 네트워크: `law_prod_network`
- 배포 스크립트: [deploy-test-backend.sh](/home/ubuntu/project/Lawdigest/.worktrees/feat-codex-deploy-test-backend/deploy/deploy-test-backend.sh)

## 동작 방식
스크립트는 아래 순서로 동작한다.

1. 배포 대상 워크트리 경로를 입력받는다.
2. 루트 저장소의 `services/backend/.env`를 읽는다.
3. 대상 워크트리의 `services/backend`에서 `./gradlew clean bootJar`를 수행한다.
4. 대상 워크트리의 `services/backend`를 빌드 컨텍스트로 Docker 이미지를 생성한다.
5. 기존 `lawdigest-backend-test` 컨테이너가 있으면 제거한다.
6. 새 컨테이너를 `law_prod_network`에 붙이고 host 808 포트로 노출한다.
7. `curl`로 127.0.0.1:808 응답을 확인한다.

## 기본 사용법
루트 저장소 또는 아무 위치에서 아래처럼 실행한다.

```bash
PORT=808 ACTIVE=test ./deploy/deploy-test-backend.sh /path/to/target-worktree
```

예시:

```bash
cd /home/ubuntu/project/Lawdigest/.worktrees/feat-codex-deploy-test-backend
PORT=808 ACTIVE=test ./deploy/deploy-test-backend.sh /home/ubuntu/project/Lawdigest/.worktrees/feat-codex-deploy-test-backend
```

위 명령을 실행하면:
- 대상 워크트리 기준으로 backend JAR를 빌드
- Docker 이미지 생성
- `lawdigest-backend-test` 컨테이너 재기동
- `test.api.lawdigest.net`이 host 808을 통해 그 컨테이너를 서비스

## 인자와 환경변수
스크립트는 첫 번째 인자로 배포 대상 워크트리 경로를 받는다.

```bash
./deploy/deploy-test-backend.sh <target-worktree>
```

지정 가능한 주요 환경변수:

- `PORT`
  - 기본값: `808`
- `CONTAINER_NAME`
  - 기본값: `lawdigest-backend-test`
- `IMAGE_NAME`
  - 기본값: `lawdigest-backend-test`
- `DOCKER_NETWORK`
  - 기본값: `law_prod_network`
- `ACTIVE`
  - 기본값: `test`

## 배포 확인
배포 후 아래 순서로 확인한다.

```bash
docker ps --filter "name=lawdigest-backend-test"
curl -sSI http://127.0.0.1:808/ | sed -n '1,20p'
```

정상이라면:
- `lawdigest-backend-test` 컨테이너가 `Up`
- `curl`이 HTTP 헤더를 반환

## 로그 확인
컨테이너 로그 확인:

```bash
docker logs -f lawdigest-backend-test
```

## 주의사항
- `services/backend/.env`는 루트 저장소 기준 파일을 사용한다.
- 테스트 백엔드는 `ACTIVE=test`를 사용한다.
- `.env` 안의 `mysql` / `redis` 호스트명은 `law_prod_network`에서 해석된다.
- `mysql` / `redis` 컨테이너는 이미 `law_prod_network`에 붙어 있어야 한다.
- host의 `127.0.0.1:808`는 nginx가 바라보는 진입점이다.
- `test.lawdigest.net`은 프론트엔드 도메인이고, 백엔드 진입점은 `test.api.lawdigest.net`이다.
- `.runtime/`은 git 추적 대상이 아니다.

## 권장 운영 방식
1. 배포할 브랜치용 worktree 생성
2. 해당 worktree에서 기능 확인 및 테스트 수행
3. `deploy-test-backend.sh <worktree>` 실행
4. `docker ps`와 `curl`로 상태 확인
5. 문제 없으면 PR 또는 merge 진행
