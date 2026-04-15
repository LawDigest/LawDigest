# Prod Web Deploy Guide

`lawdigest.kr` / `www.lawdigest.kr` 운영 프론트엔드 배포 절차 문서다.

운영 전체 기준은 [WEB_DEPLOY_ENVIRONMENTS.md](./WEB_DEPLOY_ENVIRONMENTS.md)를 먼저 참고한다.

## 기준

- 대상 브랜치: `main`
- 배포 도메인: `https://lawdigest.kr`, `https://www.lawdigest.kr`
- 배포 모드: production build + `npm run start`
- 스크립트: [`deploy-prod-web.sh`](./deploy-prod-web.sh)

## 사용법

```bash
./deploy/deploy-prod-web.sh <target-worktree>
```

예시:

```bash
PORT=3010 PM2_NAME=lawdigest-web-prod ./deploy/deploy-prod-web.sh /home/ubuntu/project/Lawdigest/.worktrees/prod-web-release
```

## 메모

- 운영 배포는 `main` 기준 상태만 올린다.
- PM2/포트/nginx 실제 운영 값은 서버 환경에 맞춰 override할 수 있다.
- 상세 런타임 구조는 공통 release/symlink 방식으로 [deploy-web-release.sh](./deploy-web-release.sh)를 따른다.
