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
