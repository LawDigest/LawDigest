# Repository Guidelines

## Project Structure & Module Organization
- Core data pipeline: `src/lawdigest_data/` (collect, process, persist).
  - `bills/` — 의안 데이터 수집/가공 (`DataFetcher`, `DataProcessor`, `constants`)
  - `connectors/` — 외부 연동 (`DatabaseManager`, `APISender`, `Notifier`, `ReportManager`, `PollsDatabaseManager`)
  - `core/` — 파이프라인 오케스트레이션 (`WorkFlowManager`)
  - `polls/` — 여론조사 데이터 수집/파싱
- Legacy/miscellaneous scripts: `src/lawdigest_data/etc/`
- Runtime jobs: `jobs/`
- Manual/utility scripts: `tools/`, `scripts/`
- Tests and fixtures: `tests/`
- Operational artifacts: `data/`, `log/`, `reports/`, `backup/`

## Build, Test, and Development Commands
- Install dependencies:
  - `python -m venv .venv && source .venv/bin/activate`
  - `pip install -e ".[dev]"` (pyproject.toml 기반)
- Run pipeline scripts:
  - `python scripts/airflow_control.sh up`
  - `python scripts/airflow_control.sh list-dags`
  - `python scripts/airflow_control.sh unpause-main`
  - `python scripts/airflow_control.sh trigger-hourly YYYY-MM-DD YYYY-MM-DD 22`
  - `python scripts/airflow_control.sh trigger-status-sync YYYY-MM-DD YYYY-MM-DD 22`
- Tests:
  - `python -m pytest tests`
  - `python -m pytest tests/test_data_fetcher_integration.py`
- Java service build:
  - `cd src/Lawbag/lawmaking && ./gradlew test && ./gradlew bootRun`

## Coding Style & Naming Conventions
- Python: 4-space indentation, `snake_case` for functions/variables/modules, `PascalCase` for classes.
- Keep pandas column names stable and transform in one place (pipeline stages).
- Constants for reusable regex/keys should be module-level when reused.
- No enforced formatter; keep imports organized and use simple type hints.

## Testing Guidelines
- Frameworks: `pytest` and `unittest`.
- New test names: `tests/test_*.py`, function names `test_*`.
- Use mocks for network/db dependencies and assert branch behavior (`remote` vs `db` vs `local`).
- No strict coverage gate; add regression tests for changed branches and edge cases.

## Commit & Pull Request Guidelines
- Commit subjects usually follow conventional prefixes: `feat:`, `fix:`, `refactor:`, `test:`, `chore:`, `docs:`.
- PRs should include:
  - 변경 요약 및 목적
  - 실행 테스트/명령 목록 및 결과
  - `env`/DB/API 영향 범위
  - 배포 전 확인 항목(마이그레이션, 스케줄러 중복 실행 여부)

## Security & Configuration Tips
- Keep `.env` values and DB credentials out of git.
- Prefer dry-run/manual smoke execution in a non-production DB before enabling scheduled n8n/cron jobs.
- For n8n migration, disable legacy Airflow jobs during overlap window to avoid double insertion.

---

## 여론조사 신규 파서 개발 시 필수 확인 문서

> **⚠️ 작업 시작 전 반드시 [`docs/parser_development_guide.md`](docs/parser_development_guide.md)를 먼저 읽는다.**
> 도구 사용법, 개발 절차, 알려진 함정(pitfall), 기존 파서 이력이 모두 이 문서에 정리되어 있다.
> 문서를 읽지 않고 시작하면 이미 해결된 문제를 반복하게 된다.

새로운 여론조사 기관 파서를 개발하기 전에 반드시 아래 문서를 순서대로 읽는다.

### 1. 개발 가이드 (시작 전 필독)
- [`docs/parser_development_guide.md`](docs/parser_development_guide.md)
  - 5단계 개발 프로세스 (스크리닝 → 포맷 분석 → 파서 작성 → 픽스처 검증 → PR)
  - 비율 뭉침, 멀티페이지 merge 등 공통 패턴 코드 예시
  - 스크리닝 도구 CLI 사용법

### 2. 현황 및 포맷 카탈로그
- [`docs/parser_development_status.md`](docs/parser_development_status.md)
  - 기관별 개발 상태 (완료 / PR 대기 / 미개발)
  - 미개발 기관 포맷 요약 (질문마커, 전체행마커, 비율위치, 도전과제)

### 3. 스크리닝 결과 JSON
- `output/polls/screening/{기관명}/` — 각 PDF의 상세 포맷 분석 결과
  - `format_profile.key_challenges` : 파서 개발 시 주의사항
  - `text_samples` : 실제 텍스트/테이블 샘플 (정규식 패턴 검증에 활용)

### 4. 파서 구현 파일
- [`src/lawdigest_data/polls/parser.py`](src/lawdigest_data/polls/parser.py) — 모든 파서 클래스
- [`config/parser_registry.json`](config/parser_registry.json) — 기관명 → 파서 매핑

### 핵심 원칙
- **기관마다 반드시 새 파서 클래스를 작성한다.** 기존 파서를 다른 기관에 재사용하지 않는다.
- 스크리닝 도구로 포맷을 먼저 파악한 뒤 파서를 작성한다.
  ```bash
  python scripts/dev/diagnose_pdf.py --pdf "파일명.pdf" --pollster "기관명" --human --dump-text
  ```
