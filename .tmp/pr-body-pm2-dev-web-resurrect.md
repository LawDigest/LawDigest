## 요약
- PM2 데몬 재시작 이후 `lawdigest-web-dev`가 복구되지 않아 `dev.lawdigest.kr`이 `502 Bad Gateway`가 되던 문제를 보강했습니다.
- dev 웹은 `dump.pm2`만 단독으로 믿지 않고 현재 런타임 심링크 기준으로 다시 복구할 수 있는 경로를 추가했습니다.
- cron watchdog이 빈 `PATH` 환경에서도 동작하도록 `node`/`npm`/`pm2` 경로 해석을 보강했습니다.

## 원인
- `dev.lawdigest.kr`는 nginx가 `127.0.0.1:3021`의 `lawdigest-web-dev` 프로세스로 프록시합니다.
- PM2 데몬이 다시 뜬 시점에 `dump.pm2`에 dev 웹 프로세스가 없으면 `3021` 업스트림이 비어 `502`가 발생합니다.
- 기존 watchdog cron은 cron 환경의 빈 `PATH` 때문에 `/usr/bin/env: 'node': No such file or directory`로 실패할 수 있었습니다.

## 변경 내용
- `deploy/ensure-dev-web-pm2.sh`
  - `.runtime/dev-web/current`를 기준으로 `lawdigest-web-dev`를 idempotent하게 복구하도록 추가
  - cron 같은 빈 환경에서도 `nvm.sh`를 로드해 `node`/`npm`/`pm2`를 찾도록 보강
- `deploy/install-dev-web-watchdog.sh`
  - 1분 주기 watchdog cron 등록
  - 기존 watchdog 엔트리가 있으면 새 형식으로 교체
  - `NVM_DIR`와 최소 `PATH`를 함께 넣어 복구 스크립트가 안정적으로 실행되도록 수정
- `deploy/deploy-dev-web.sh`
  - dev 배포 시 공통 복구 스크립트를 사용하도록 정리
- `deploy/deploy-web-release.sh`
  - prod/test 웹 배포 중에도 dev 웹 PM2 누락 여부를 한 번 더 점검하도록 보강
- 문서 및 명령
  - `deploy/DEV_WEB_DEPLOY.md`
  - `deploy/DEPLOY_OPERATIONS.md`
  - `deploy/WEB_DEPLOY_ENVIRONMENTS.md`
  - `Makefile`

## 검증
- `bash -n deploy/ensure-dev-web-pm2.sh deploy/install-dev-web-watchdog.sh deploy/deploy-dev-web.sh deploy/deploy-web-release.sh`
- `cd services/web && npm run lint`
- `./deploy/deploy-dev-web.sh fix/pm2-dev-web-resurrect/codex`
- `pm2 delete lawdigest-web-dev`
- `env -i HOME=$HOME USER=$USER SHELL=/bin/bash PATH=/usr/bin:/bin NVM_DIR=$HOME/.nvm bash /home/ubuntu/project/Lawdigest/deploy/ensure-dev-web-pm2.sh`
- `curl -sSI https://dev.lawdigest.kr/election?tab=district`
- `crontab -l | rg ensure-dev-web-pm2`
