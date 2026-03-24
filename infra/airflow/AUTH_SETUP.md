# Airflow 3.x SimpleAuthManager 인증 설정 가이드

Airflow 3.x에서 도입된 `SimpleAuthManager`는 데이터베이스 대신 설정 파일과 로컬 JSON 파일을 사용하여 사용자를 관리하는 가벼운 인증 방식입니다. 개발 및 테스트 환경에서 사용하기 적합합니다.

## 1. 환경 변수 설정

환경 변수는 **반드시 `docker-compose.yaml`의 `x-airflow-common.environment` 블록에 직접 명시**해야 합니다. `.env` 파일에만 정의하면 컨테이너에 전달되지 않습니다.

```yaml
# docker-compose.yaml 의 x-airflow-common.environment 블록에 추가
AIRFLOW__CORE__SIMPLE_AUTH_MANAGER_USERS: 'airflow:ADMIN'
AIRFLOW__CORE__SIMPLE_AUTH_MANAGER_PASSWORDS_FILE: '/opt/airflow/config/simple_auth_manager_passwords.json'
```

- `AIRFLOW__CORE__SIMPLE_AUTH_MANAGER_USERS`: 사용자명과 역할(Role)을 지정합니다.
  - 형식: `사용자명:ROLE` (여러 명인 경우 쉼표로 구분)
  - **주의**: 역할 명칭은 반드시 **대문자**여야 합니다 (`ADMIN`, `OP`, `USER`, `VIEWER`).
  - 예: `airflow:ADMIN,viewer:VIEWER`
- `AIRFLOW__CORE__SIMPLE_AUTH_MANAGER_PASSWORDS_FILE`: 비밀번호가 저장될 JSON 파일의 경로입니다.
  - 예: `/opt/airflow/config/simple_auth_manager_passwords.json`
- `AIRFLOW__CORE__SIMPLE_AUTH_MANAGER_ALL_ADMINS`: `True`로 설정 시 모든 접속자를 관리자로 취급하며 인증을 우회합니다 (디버깅용).

## 2. 비밀번호 파일 형식 (`simple_auth_manager_passwords.json`)

비밀번호는 **평문(Plain Text)으로 저장**합니다. Airflow의 `SimpleAuthManager`는 내부적으로 단순 문자열 비교로 인증하므로, bcrypt 등 해시 형식으로 저장하면 로그인이 **불가능**합니다.

```json
{
  "airflow": "mypassword"
}
```

## 3. 비밀번호 변경 방법

### 방법 A: 파일 직접 수정 (추천)

`infra/airflow/config/simple_auth_manager_passwords.json` 파일을 열어 원하는 비밀번호로 수정한 후 웹서버를 재시작합니다.

```bash
docker compose restart airflow-webserver
```

### 방법 B: 자동 생성 기능 활용

비밀번호 파일이 없거나 해당 사용자가 파일에 정의되어 있지 않은 경우, Airflow가 기동 시 임의의 비밀번호를 자동으로 생성합니다. 자동 생성된 비밀번호도 평문으로 파일에 저장되며 로그에 출력됩니다.

1. `simple_auth_manager_passwords.json` 파일을 삭제하거나 백업합니다.
2. `docker compose restart airflow-webserver`를 실행합니다.
3. 웹서버 로그에서 생성된 비밀번호를 확인합니다.
   ```bash
   docker compose logs airflow-webserver | grep "Password for user"
   ```
   *로그 출력 예시: `Simple auth manager | Password for user 'airflow': yE3b8uHhXN3C8xt6`*

## 4. 환경 변수 변경 시 컨테이너 재생성

`docker-compose.yaml`의 환경 변수를 변경한 경우 `docker compose restart`만으로는 반영되지 않습니다. 반드시 컨테이너를 재생성해야 합니다.

```bash
# 웹서버만 재생성 (다른 서비스 영향 없음)
docker compose up -d --no-deps airflow-webserver
```

## 5. 주의사항 및 트러블슈팅

1. **로그인 실패 (401 Unauthorized)**:
   - 비밀번호 파일에 평문으로 저장되어 있는지 확인합니다. bcrypt 해시 형식이면 로그인이 불가합니다.
   - 역할(Role)이 대문자인지 확인합니다 (예: `admin` → `ADMIN`).
   - `docker-compose.yaml`에 `AIRFLOW__CORE__SIMPLE_AUTH_MANAGER_USERS`와 `AIRFLOW__CORE__SIMPLE_AUTH_MANAGER_PASSWORDS_FILE`이 명시되어 있는지 확인합니다.
   - 환경 변수 변경 후에는 `docker compose up -d --no-deps airflow-webserver`로 컨테이너를 재생성합니다.
2. **서버 기동 대기**: Airflow 3.x는 초기화 과정이 이전 버전보다 오래 걸릴 수 있으므로, 재시작 후 약 30초~1분 정도 대기한 뒤 접속을 시도하십시오.
3. **InsecureKeyLengthWarning**: HMAC 키 길이가 짧다는 경고가 발생할 수 있으나, 인증 기능 자체를 차단하지는 않습니다. 보안을 위해 `AIRFLOW__API__SECRET_KEY`를 64바이트 이상으로 설정하는 것을 권장합니다.
