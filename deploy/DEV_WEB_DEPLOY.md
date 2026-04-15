# Dev Web Deploy Guide

`dev.lawdigest.kr` 개발용 프론트엔드 배포 절차 문서다.

운영 전체 기준은 [WEB_DEPLOY_ENVIRONMENTS.md](./WEB_DEPLOY_ENVIRONMENTS.md)를 먼저 참고한다.

## 목적

- `dev.lawdigest.kr`을 지정한 브랜치/커밋 기준으로 빠르게 전환
- 반드시 `next dev` 개발모드로 실행
- `react-grab` 같은 개발 전용 오버레이와 hot reload를 유지

## 구성

- 도메인: `https://dev.lawdigest.kr`
- PM2 프로세스: `lawdigest-web-dev`
- 포트: `3021`
- 배포 스크립트: [`deploy-dev-web.sh`](./deploy-dev-web.sh)
- 런타임 심링크: `/home/ubuntu/project/Lawdigest/.runtime/dev-web/current`
- 기본 worktree 경로: `/home/ubuntu/project/Lawdigest/.worktrees/dev-web-live`

## 동작 방식

1. 입력한 git ref를 `fetch`한다.
2. 전용 worktree를 해당 ref로 `detach checkout`한다.
3. `npm install`을 수행한다.
4. `.runtime/dev-web/current` 심링크를 해당 worktree로 전환한다.
5. PM2에서 `npm run dev -- --hostname 0.0.0.0 --port 3021`로 재기동한다.

즉, `dev.lawdigest.kr`은 빌드 산출물 고정 배포가 아니라, 선택한 소스 트리를 개발모드로 직접 서비스한다.

## 사용법

```bash
./deploy/deploy-dev-web.sh <git-ref>
```

예시:

```bash
./deploy/deploy-dev-web.sh main
./deploy/deploy-dev-web.sh feat/election-map-refresh
./deploy/deploy-dev-web.sh 49e57ea
```

## 확인 방법

```bash
pm2 list
curl -sSI https://dev.lawdigest.kr/election | sed -n '1,20p'
```

정상이라면:

- `lawdigest-web-dev` 프로세스가 `online`
- `dev.lawdigest.kr` 응답이 `200 OK`

## 주의사항

- 개발모드이므로 production build보다 자원 사용량이 클 수 있다.
- 현재 서비스 대상은 `.runtime/dev-web/current` 심링크가 가리키는 worktree다.
- dev용 worktree를 지우기 전에 다른 ref로 재배포하거나 심링크를 옮겨야 한다.
