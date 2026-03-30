# Dev Web Deploy Guide

`dev.lawdigest.net` 프론트엔드 배포 절차 문서다.

운영 전체 기준은 [DEPLOY_OPERATIONS.md](./DEPLOY_OPERATIONS.md)를 먼저 참고한다.

현재 dev 웹은 `release/symlink` 구조로 배포된다.
즉, 특정 브랜치나 워크트리의 `services/web`를 직접 서비스하지 않고,
배포 시점에 빌드된 결과를 고정 런타임 디렉터리로 옮긴 뒤 `current` 심링크만 전환한다.

## 목적
- `dev.lawdigest.net`을 특정 브랜치/워크트리 기준 상태로 손쉽게 전환
- nginx, 도메인, PM2 이름은 고정 유지
- 배포 대상을 바꿀 때 운영 설정 변경 최소화
- 롤백 시 심링크 기준으로 되돌리기 쉽게 유지

## 구성
- 도메인: `https://dev.lawdigest.net`
- PM2 프로세스: `lawdigest-web`
- 포트: `3010`
- 배포 스크립트: [deploy-test-web.sh](/home/ubuntu/project/Lawdigest/.worktrees/test-release-deploy/deploy/deploy-test-web.sh)
- 런타임 루트: `/home/ubuntu/project/Lawdigest/.runtime/test-web`
- release 디렉터리: `/home/ubuntu/project/Lawdigest/.runtime/test-web/releases/<release-id>`
- 현재 활성 release 심링크: `/home/ubuntu/project/Lawdigest/.runtime/test-web/current`
- 서버 환경 파일: `/home/ubuntu/project/Lawdigest/services/web/.env`

## 동작 방식
스크립트는 아래 순서로 동작한다.

1. 배포 대상 워크트리 경로를 입력받는다.
2. 서버의 `services/web/.env`를 읽어 공통 환경값을 로드한다.
3. 해당 워크트리의 `services/web`에서 `npm install`을 수행한다.
4. 해당 워크트리 기준으로 `npm run build`를 수행한다.
5. 새 release 디렉터리를 생성한다.
6. 대상 워크트리의 `services/web`를 release 디렉터리 아래로 복사한다.
7. `current` 심링크를 새 release로 원자적으로 전환한다.
8. PM2 `lawdigest-web`를 새 release 기준으로 재기동한다.

이 구조 때문에 nginx 설정을 건드리지 않고도 test 웹의 기준 상태를 바꿀 수 있다.

## 기본 사용법
루트 저장소 또는 아무 위치에서 아래처럼 실행한다.

```bash
PORT=3010 PM2_NAME=lawdigest-web ./deploy/deploy-test-web.sh /path/to/target-worktree
```

예시:

```bash
cd /home/ubuntu/project/Lawdigest/.worktrees/test-release-deploy
PORT=3010 PM2_NAME=lawdigest-web ./deploy/deploy-test-web.sh /home/ubuntu/project/Lawdigest/.worktrees/feat-preview-deploy
```

위 명령을 실행하면:
- `/home/ubuntu/project/Lawdigest/.worktrees/feat-preview-deploy` 기준으로 빌드
- 새 release 생성
- `current` 심링크 전환
- `dev.lawdigest.net`이 그 상태를 서비스

## 인자와 환경변수
스크립트는 첫 번째 인자로 배포 대상 워크트리 경로를 받는다.

```bash
./deploy/deploy-test-web.sh <target-worktree>
```

지정 가능한 주요 환경변수:

- `PORT`
  - 기본값: `3010`
- `APP_HOST`
  - 기본값: `0.0.0.0`
- `PM2_NAME`
  - 기본값: `lawdigest-web`
- `RUNTIME_ROOT`
  - 기본값: `/home/ubuntu/project/Lawdigest/.runtime/test-web`
- `NEXT_PUBLIC_URL`
  - 기본값: `https://api.lawdigest.net/`
- `NEXT_PUBLIC_IMAGE_URL`
  - 기본값: `https://api.lawdigest.net`
- `NEXT_PUBLIC_HOSTNAME`
  - 기본값: `api.lawdigest.net`
- `NEXT_PUBLIC_DOMAIN`
  - 기본값: `https://dev.lawdigest.net`

필요하면 배포 대상 워크트리 루트나 `services/web/.env.preview`를 두고 값을 override할 수 있다.

## 배포 확인
배포 후 아래 순서로 확인한다.

```bash
pm2 list
curl -sSI https://dev.lawdigest.net/election | sed -n '1,20p'
```

정상이라면:
- `lawdigest-web` 프로세스가 `online`
- `https://dev.lawdigest.net/election` 응답이 `200 OK`

## 현재 release 확인
현재 심링크 대상 확인:

```bash
readlink -f /home/ubuntu/project/Lawdigest/.runtime/test-web/current
```

release 목록 확인:

```bash
ls -1 /home/ubuntu/project/Lawdigest/.runtime/test-web/releases
```

## 수동 롤백
전용 롤백 스크립트는 아직 없다.
현재는 심링크를 이전 release로 되돌린 뒤 PM2를 다시 띄우는 방식으로 롤백할 수 있다.

예시:

```bash
ln -sfn /home/ubuntu/project/Lawdigest/.runtime/test-web/releases/<old-release> /home/ubuntu/project/Lawdigest/.runtime/test-web/.current.tmp
mv -Tf /home/ubuntu/project/Lawdigest/.runtime/test-web/.current.tmp /home/ubuntu/project/Lawdigest/.runtime/test-web/current
cd /home/ubuntu/project/Lawdigest/.runtime/test-web/current/services/web
PORT=3010 HOSTNAME=0.0.0.0 pm2 delete lawdigest-web || true
PORT=3010 HOSTNAME=0.0.0.0 pm2 start npm --name lawdigest-web -- run start
pm2 save
```

## 주의사항
- `dev.lawdigest.net`은 이제 특정 worktree를 직접 바라보지 않는다.
- 실제 서비스 기준은 항상 `.runtime/test-web/current`이다.
- worktree를 삭제해도 현재 서비스는 유지된다. 단, 해당 release를 직접 삭제하면 안 된다.
- `.runtime/`은 git 추적 대상이 아니다.
- 배포 스크립트는 production build 기준이다. `next dev` 배포가 아니다.

## 권장 운영 방식
1. 배포할 브랜치용 worktree 생성
2. 해당 worktree에서 기능 확인 및 테스트 수행
3. `deploy-test-web.sh <worktree>` 실행
4. `dev.lawdigest.net`에서 확인
5. 문제 없으면 PR 또는 merge 진행

## 후속 개선 제안
- release 보존 개수 제한
- `.env.preview.example` 추가
- PM2 ecosystem 파일로 test 배포 설정 코드화
