# GitHub Actions 운영 배포

LawDigest 운영 웹과 백엔드는 PR이 `main`에 머지되어 새 커밋이 push되는 시점을
운영 배포 기준점으로 사용한다.

## 워크플로

- 파일: [`.github/workflows/deploy-production.yml`](../.github/workflows/deploy-production.yml)
- 이벤트: `main` 브랜치 `push`
- 환경: GitHub `production` environment
- 동시성 그룹: `production-deployment`
- 권한: `contents: read`

문서나 데이터 파이프라인만 변경된 경우 운영 웹과 백엔드는 배포하지 않는다.

| 변경 경로 | 검증 및 배포 대상 |
| --- | --- |
| `services/web/**` 및 운영 웹 배포 스크립트 | 웹 |
| `services/backend/**` 및 운영 백엔드 배포 스크립트 | 백엔드 |
| 운영 배포 워크플로 또는 공통 원격 배포 스크립트 | 웹과 백엔드 |
| `services/data/**`, `services/ai/**` | 대상 없음 |

## 실행 순서

1. 직전 `main` SHA와 새 `main` SHA 사이의 변경 파일을 확인한다.
2. 변경된 웹은 Node.js `22.17.1`에서 `npm ci`, lint, test, build를 실행한다.
3. 변경된 백엔드는 Java 17에서 Gradle test와 `bootJar`를 실행한다.
4. 대상 검증이 모두 성공하면 production 환경의 SSH 설정으로 Oracle 서버에 접속한다.
5. [`deploy-github-main.sh`](./deploy-github-main.sh)를 SSH 표준입력으로 전달한다.
6. 서버는 배포 SHA가 `origin/main`에 포함되는지 검증한다.
7. `.worktrees/github-actions-<sha>` 전용 worktree를 만들고 변경된 서비스만 배포한다.
8. 배포가 끝나면 worktree를 제거한다.

백엔드와 웹이 동시에 변경되면 백엔드를 먼저 배포한다. 백엔드 배포는 staging
컨테이너 헬스체크와 실패 시 복구를 사용한다. 웹 배포는 새 release의 로컬
헬스체크가 실패하면 이전 release 심링크와 PM2 프로세스를 복구한다.

## GitHub production 환경 설정

다음 environment variable이 필요하다.

| 이름 | 설명 |
| --- | --- |
| `PROD_SSH_HOST` | Oracle 서버 SSH 호스트 |
| `PROD_SSH_PORT` | SSH 포트 |
| `PROD_SSH_USER` | 배포 사용자 |

다음 environment secret이 필요하다.

| 이름 | 설명 |
| --- | --- |
| `PROD_SSH_PRIVATE_KEY` | 운영 배포 전용 SSH private key |
| `PROD_SSH_KNOWN_HOSTS` | 검증된 Oracle 서버 SSH host key |

배포 키는 일반 개발 키와 분리하고 포트·에이전트·X11 forwarding과 PTY를 허용하지
않는다. 애플리케이션 DB/API 비밀값은 GitHub에 복사하지 않고 기존 Oracle 서버의
비추적 `.env`에만 유지한다.

## 서버 전제

- 저장소: `/home/ubuntu/project/Lawdigest`
- NVM Node.js: `22.17.1`
- Java: 17
- Docker 및 Docker Compose
- PM2
- `flock`
- `services/web/.env`
- `services/backend/.env`

서버의 기본 checkout이 다른 브랜치이거나 수정된 상태여도 배포는 별도 detached
worktree를 사용하므로 해당 파일을 덮어쓰지 않는다.

## 수동 복구

GitHub Actions를 사용할 수 없는 경우 서버에서 깨끗한 대상 worktree를 준비한 뒤
기존 스크립트를 실행한다.

```bash
./deploy/deploy-prod-backend.sh /path/to/target-worktree
./deploy/deploy-prod-web.sh /path/to/target-worktree
```

배포 실패 시 GitHub Actions 로그와 서버의 다음 상태를 함께 확인한다.

```bash
pm2 list
docker ps --filter "name=lawdigest-backend-test"
curl -fsSI https://api.lawdigest.kr/ | sed -n '1,20p'
curl -fsSI https://lawdigest.kr/election | sed -n '1,20p'
```
