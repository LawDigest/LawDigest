# AGENTS

## 기본 원칙

- 작업 규모에 맞게 절차를 조절한다.
- 작은 변경에 큰 절차를 적용하지 않는다.
- 불확실하거나 위험한 작업은 먼저 확인한다.
- 작업을 마치면 복구 체크포인트를 남기기 위해 작업 규모와 관계없이 커밋하고 푸시한다.
- PR은 사용자가 요청하거나 확인한 경우에만 만든다.

## 작업 규모

### Tiny

문구, 프롬프트, 주석, 문서, 단일 설정값처럼 영향 범위가 작고 되돌리기 쉬운 변경.

- 브랜치와 워크트리는 생략할 수 있다.
- 새 테스트를 추가하지 않는다.
- 필요한 경우 관련 테스트 또는 diff 확인만 수행한다.
- 작업 완료 후 커밋하고 푸시한다.

### Normal

기능, 버그 수정, 동작 변경처럼 사용자 동작이나 코드 흐름에 영향을 주는 변경.

- 브랜치를 만든다.
- 워크트리는 사용자가 요청하거나 충돌 위험이 있을 때만 만든다.
- 관련 테스트를 실행한다.
- 명확한 린트 명령이 있으면 실행한다.
- 작업 완료 후 커밋하고 푸시한다.

### High-risk

DB, 배포, 인증, 데이터 삭제, 인프라, 대량 변경처럼 실패 비용이 큰 작업.

- 사용자 승인을 먼저 받는다.
- 브랜치와 워크트리를 사용한다.
- 로그, 실제 데이터, 문서, 배포 절차를 확인한다.
- 검증 방법과 롤백 방안을 포함한다.

## 작업 방식

- 확실하지 않은 것은 추측으로 진행하지 않는다.
- 프로젝트 문서를 먼저 확인하되, 현재 상태와 맞지 않는 레거시 문서일 수 있음을 감안한다.
- 디버깅은 실제 로그와 실제 데이터를 기준으로 한다.
- `apply_patch`가 실패하면 같은 대형 패치를 반복하지 말고, 대상 경로와 파일 상태를 다시 확인한다.
- 관련 없는 파일, 포맷, 죽은 코드는 요청받지 않는 한 건드리지 않는다.

## 완료 보고

- 변경 내용, 검증 결과, 남은 위험만 짧게 보고한다.
- Tiny 작업에서는 후속 작업 제안을 생략한다.
- 후속 작업은 실제로 도움이 될 때만 1~3개 제안한다.
- 기능 구현이 끝났더라도 PR 생성은 사용자에게 먼저 확인한다.

## 배포

- `test.lawdigest.kr` 테스트 웹 배포는 직접 `pm2` 또는 `nginx` 설정을 임의 변경하지 말고, `deploy/deploy-test-web.sh <target-worktree>`를 통해 수행한다.
- 웹 배포 기준은 먼저 [deploy/WEB_DEPLOY_ENVIRONMENTS.md](/home/ubuntu/project/Lawdigest/deploy/WEB_DEPLOY_ENVIRONMENTS.md)를 확인한다.
- 운영 웹 상세 절차는 [deploy/PROD_WEB_DEPLOY.md](/home/ubuntu/project/Lawdigest/deploy/PROD_WEB_DEPLOY.md), 테스트 웹 상세 절차는 [deploy/TEST_WEB_DEPLOY.md](/home/ubuntu/project/Lawdigest/deploy/TEST_WEB_DEPLOY.md), 개발 웹 상세 절차는 [deploy/DEV_WEB_DEPLOY.md](/home/ubuntu/project/Lawdigest/deploy/DEV_WEB_DEPLOY.md)를 따른다.
