# Test Backend Deploy Guide

`test.api.lawdigest.net`용 백엔드 테스트 배포 절차 문서다.

현재 테스트 백엔드는 `release/symlink` 구조로 배포된다.
즉, 특정 브랜치나 워크트리의 `services/backend`를 직접 서비스하지 않고,
배포 시점에 빌드된 JAR와 런타임 환경 파일을 고정 디렉터리에 저장한 뒤 `current` 심링크만 전환한다.

## 목적
- `test.api.lawdigest.net`을 특정 브랜치/워크트리 기준 상태로 손쉽게 전환
- PM2 프로세스명과 런타임 경로를 고정해 운영 일관성 유지
- 롤백 시 심링크 기준으로 되돌리기 쉽게 유지
- 워크트리 삭제와 서비스 실행 기준을 분리

## 구성
- 도메인: `http://127.0.0.1:<PORT>` 기준으로 PM2 기동
- PM2 프로세스: `lawdigest-backend-test`
- 기본 포트: `18080`
- 배포 스크립트: [deploy-test-backend.sh](/home/ubuntu/project/Lawdigest/deploy/deploy-test-backend.sh)
- 런타임 루트: `/home/ubuntu/project/Lawdigest/.runtime/test-backend`
- release 디렉터리: `/home/ubuntu/project/Lawdigest/.runtime/test-backend/releases/<release-id>`
- 현재 활성 release 심링크: `/home/ubuntu/project/Lawdigest/.runtime/test-backend/current`

## 동작 방식
스크립트는 아래 순서로 동작한다.

1. 배포 대상 워크트리 경로를 입력받는다.
2. 해당 워크트리의 `services/backend`에서 `./gradlew clean bootJar`를 수행한다.
3. 새 release 디렉터리를 생성한다.
4. 생성된 JAR와 `.env`를 release 디렉터리 아래로 복사한다.
5. `.env`를 바탕으로 `ACTIVE`, `SERVER_PORT`, DB/Redis 호스트를 release 런타임 값으로 덮어쓴다.
6. `current` 심링크를 새 release로 원자적으로 전환한다.
7. PM2 `lawdigest-backend-test`를 새 release 기준으로 재기동한다.

## 기본 사용법
루트 저장소 또는 아무 위치에서 아래처럼 실행한다.

```bash
PORT=18080 ACTIVE=test PM2_NAME=lawdigest-backend-test ./deploy/deploy-test-backend.sh /path/to/target-worktree
```

예시:

```bash
cd /home/ubuntu/project/Lawdigest/.worktrees/feat-codex-deploy-test-backend
PORT=18080 ACTIVE=test PM2_NAME=lawdigest-backend-test ./deploy/deploy-test-backend.sh /home/ubuntu/project/Lawdigest/.worktrees/feat-codex-deploy-test-backend
```

위 명령을 실행하면:
- 대상 워크트리 기준으로 JAR 빌드
- 새 release 생성
- `current` 심링크 전환
- PM2 기준으로 백엔드 재기동

## 인자와 환경변수
스크립트는 첫 번째 인자로 배포 대상 워크트리 경로를 받는다.

```bash
./deploy/deploy-test-backend.sh <target-worktree>
```

지정 가능한 주요 환경변수:

- `PORT`
  - 기본값: `18080`
- `PM2_NAME`
  - 기본값: `lawdigest-backend-test`
- `RUNTIME_ROOT`
  - 기본값: `/home/ubuntu/project/Lawdigest/.runtime/test-backend`
- `ACTIVE`
  - 기본값: `test`
- `DB_HOSTNAME`, `BIN_LOG_HOST`, `ELASTIC_CACHE_HOST`
  - 기본값: `127.0.0.1`

## 배포 확인
배포 후 아래 순서로 확인한다.

```bash
pm2 list
curl -sSI http://127.0.0.1:18080/ | sed -n '1,20p'
```

정상이라면:
- `lawdigest-backend-test` 프로세스가 `online`
- `curl` 응답이 HTTP 헤더를 반환

## 현재 release 확인
현재 심링크 대상 확인:

```bash
readlink -f /home/ubuntu/project/Lawdigest/.runtime/test-backend/current
```

release 목록 확인:

```bash
ls -1 /home/ubuntu/project/Lawdigest/.runtime/test-backend/releases
```

## 수동 롤백
현재는 심링크를 이전 release로 되돌린 뒤 PM2를 다시 띄우는 방식으로 롤백할 수 있다.

예시:

```bash
ln -sfn /home/ubuntu/project/Lawdigest/.runtime/test-backend/releases/<old-release> /home/ubuntu/project/Lawdigest/.runtime/test-backend/.current.tmp
mv -Tf /home/ubuntu/project/Lawdigest/.runtime/test-backend/.current.tmp /home/ubuntu/project/Lawdigest/.runtime/test-backend/current
cd /home/ubuntu/project/Lawdigest/.runtime/test-backend/current
pm2 delete lawdigest-backend-test || true
pm2 start run.sh --name lawdigest-backend-test
pm2 save
```

## 주의사항
- 테스트 백엔드는 기본적으로 `ACTIVE=test`를 사용한다.
- `.env`에 들어 있는 `JAVA_HOME`은 호스트 환경에 따라 무시될 수 있다. 런처는 `JAVA_HOME/bin/java`가 실제로 존재할 때만 사용한다.
- 배포 시 DB와 Redis 호스트는 로컬 포트 매핑을 사용하도록 `127.0.0.1`로 덮어쓴다.
- `test.api.lawdigest.net` 앞단의 nginx 설정은 이 스크립트가 직접 바꾸지 않는다.
- `.runtime/`은 git 추적 대상이 아니다.

## 권장 운영 방식
1. 배포할 브랜치용 worktree 생성
2. 해당 worktree에서 기능 확인 및 테스트 수행
3. `deploy-test-backend.sh <worktree>` 실행
4. `pm2 list`와 `curl`로 상태 확인
5. 문제 없으면 PR 또는 merge 진행
