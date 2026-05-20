# Pipeline Monitor

Lawdigest 데이터 파이프라인 실행 이력을 read-only로 확인하는 독립 웹서비스입니다.

## 실행

```bash
cd services/pipeline-monitor
PORT=32240 PIPELINE_RUNS_PATH=/path/to/pipeline-runs.jsonl npm start
```

환경변수:

- `PORT`: HTTP 포트. 기본값은 `32240`.
- `PIPELINE_RUNS_PATH`: 읽을 JSONL 실행 로그 경로. 기본값은 이 폴더의 `pipeline-runs.jsonl`.
- `PIPELINE_ARTIFACT_ROOT`: artifact API에서 허용할 추가 루트. 기본값은 이 폴더.

## API

- `GET /api/health`: 서비스 상태와 읽은 run 수.
- `GET /api/runs`: JSONL을 파싱한 run 목록과 summary.
- `GET /api/runs/:runId`: 단일 run 상세.
- `GET /api/artifacts/:path`: 허용 루트 아래 artifact 텍스트 preview.

## 데이터 형식

초기 저장소는 append-only JSONL입니다. 각 라인은 다음 필드를 우선 사용합니다.

- `run_id`
- `command`
- `status`
- `provider`
- `started_at`
- `finished_at`
- `duration_seconds`
- `items`
- `artifacts`
- `steps`
- `logs`

API key, token, password, secret 계열 key는 응답에서 redaction됩니다.
