from __future__ import annotations

import json
import importlib.util
import sys
import types
from dataclasses import asdict
from pathlib import Path

from lawdigest_data.polls.models import PollDetail, PollResultSet, QuestionResult


def _install_fake_workflow_dependencies():
    core_module = types.ModuleType("lawdigest_data.core.WorkFlowManager")

    class _FakeWorkFlowManager:
        @staticmethod
        def normalize_execution_mode(mode: str) -> str:
            mode = (mode or "").replace("-", "_").lower()
            if mode in {"test", "test_db"}:
                return "test_db"
            if mode in {"prod", "remote"}:
                return "prod"
            return "dry_run"

    core_module.WorkFlowManager = _FakeWorkFlowManager
    sys.modules["lawdigest_data.core.WorkFlowManager"] = core_module

    connectors_module = types.ModuleType(
        "lawdigest_data.connectors.PollsDatabaseManager"
    )

    class _FakePollsDatabaseManager:
        def __init__(self, *args, **kwargs):
            pass

    connectors_module.PollsDatabaseManager = _FakePollsDatabaseManager
    sys.modules["lawdigest_data.connectors.PollsDatabaseManager"] = connectors_module


def _load_workflow_module():
    _install_fake_workflow_dependencies()
    module_name = "lawdigest_data.polls.workflow"
    sys.modules.pop(module_name, None)
    workflow_path = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "lawdigest_data"
        / "polls"
        / "workflow.py"
    )
    spec = importlib.util.spec_from_file_location(module_name, workflow_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_fetch_polls_step_returns_metrics(monkeypatch, tmp_path):
    workflow_module = _load_workflow_module()

    targets_path = tmp_path / "targets.json"
    targets_path.write_text(
        """
        {
          "regions": {
            "gyeonggi": {
              "search_cnd": "4",
              "search_wrd": "경기도",
              "region": "경기도 전체"
            }
          },
          "elections": {
            "local_9th_governor": {
              "poll_gubuncd": "VT026",
              "election_type": "제9회 전국동시지방선거",
              "election_names": ["광역단체장선거"]
            }
          },
          "targets": [
            {
              "slug": "gyeonggi_governor_9th",
              "region_key": "gyeonggi",
              "election_key": "local_9th_governor"
            }
          ]
        }
        """.strip(),
        encoding="utf-8",
    )

    artifact_path = tmp_path / "fetch_artifact.json"
    list_record_cls = workflow_module.ListRecord

    class _StubCrawler:
        def __init__(self, verify_connectivity: bool = True, registry_path=None):
            self.verify_connectivity = verify_connectivity
            self.registry_path = registry_path

        def crawl_for_targets(
            self, targets, max_pages_per_target: int, skip_errors: bool = True
        ):
            assert max_pages_per_target == 7
            return {
                targets[0].slug: [
                    list_record_cls(
                        registration_number="REG-1",
                        pollster="테스트기관",
                        sponsor="테스트스폰서",
                        method="CATI",
                        sample_frame="유선+무선",
                        title_region="경기도 광역단체장선거",
                        registered_date="2026-04-05",
                        province="제9회 전국동시지방선거",
                        detail_url="https://example.com/detail/1",
                    )
                ]
            }

    monkeypatch.setattr(workflow_module, "NesdcCrawler", _StubCrawler)
    monkeypatch.setattr(
        workflow_module, "_write_artifact", lambda prefix, payload: str(artifact_path)
    )
    monotonic_values = iter([10.0, 12.5])
    monkeypatch.setattr(workflow_module, "monotonic", lambda: next(monotonic_values))

    result = workflow_module.PollsWorkflowManager("test").fetch_polls_step(
        targets_path=str(targets_path),
        max_pages_per_target=7,
    )

    assert result["mode"] == "test_db"
    assert result["targets"] == 1
    assert result["target_slugs"] == ["gyeonggi_governor_9th"]
    assert result["total"] == 1
    assert result["artifact_path"] == str(artifact_path)
    assert result["elapsed_seconds"] == 2.5


def test_fetch_polls_step_empty_targets_returns_metrics(monkeypatch, tmp_path):
    workflow_module = _load_workflow_module()
    targets_path = tmp_path / "targets.json"
    targets_path.write_text('{"targets": []}', encoding="utf-8")

    monotonic_values = iter([20.0, 20.2])
    monkeypatch.setattr(workflow_module, "monotonic", lambda: next(monotonic_values))

    result = workflow_module.PollsWorkflowManager("dry_run").fetch_polls_step(
        targets_path=str(targets_path)
    )

    assert result["targets"] == 0
    assert result["total"] == 0
    assert result["target_slugs"] == []
    assert result["artifact_path"] is None
    assert result["elapsed_seconds"] == 0.2


def test_save_parsed_result_prefers_list_pollster(monkeypatch, tmp_path):
    workflow_module = _load_workflow_module()
    monkeypatch.setattr(workflow_module, "_PARSED_DIR", tmp_path)

    detail = workflow_module.PollDetail(
        source_url="https://example.com/detail/1",
        list_pollster="테스트기관",
        pollster="",
        election_name="광역단체장선거",
        region="경기도 전체",
        analysis_filename="결과표_테스트.pdf",
    )

    out_path = workflow_module._save_parsed_result({"questions": []}, detail)

    assert "테스트기관" in str(out_path)
    assert out_path.exists()


def test_parse_results_step_enriches_survey_metadata(monkeypatch, tmp_path):
    workflow_module = _load_workflow_module()
    monkeypatch.setattr(workflow_module, "_PARSED_DIR", tmp_path)

    detail = PollDetail(
        source_url="https://example.com/detail/1",
        registration_number="REG-1",
        list_pollster="테스트기관",
        pollster="",
        election_type="제9회 전국동시지방선거",
        region="경기도 전체",
        election_name="광역단체장선거",
        sponsor="테스트스폰서",
        survey_datetimes=["2026-03-20 09시 00분 ~ 2026-03-21 18시 00분"],
        sample_size_completed=1000,
        margin_of_error="±3.1%",
        analysis_filename="결과표_테스트.pdf",
    )

    result_set = PollResultSet(
        registration_number="REG-1",
        source_url=detail.source_url,
        pdf_path="/tmp/result.pdf",
        questions=[
            QuestionResult(
                question_number=1,
                question_title="Q1",
                question_text="Q1",
                response_options=["A", "B"],
                overall_n_completed=500,
                overall_n_weighted=500,
                overall_percentages=[40.0, 60.0],
            )
        ],
    )

    artifact_path = tmp_path / "details.json"
    artifact_path.write_text(
        json.dumps([asdict(detail)], ensure_ascii=False), encoding="utf-8"
    )
    captured: dict[str, object] = {}

    class _StubCrawler:
        def __init__(self, verify_connectivity: bool = True, registry_path=None):
            self.verify_connectivity = verify_connectivity
            self.registry_path = registry_path

        def crawl_results(
            self, details, pdf_dir, skip_errors: bool = True, registry_path=None
        ):
            return [result_set]

    monkeypatch.setattr(workflow_module, "NesdcCrawler", _StubCrawler)

    def _capture_artifact(prefix, payload):
        captured["payload"] = payload
        return "/tmp/results.json"

    monkeypatch.setattr(workflow_module, "_write_artifact", _capture_artifact)

    result = workflow_module.PollsWorkflowManager("test").parse_results_step(
        artifact_path=str(artifact_path),
        pdf_dir=str(tmp_path),
    )

    assert result["parsed"] == 1
    assert result["questions_total"] == 1
    payload = captured["payload"]
    assert isinstance(payload, list)
    assert payload[0]["election_type"] == "제9회 전국동시지방선거"
    assert payload[0]["region"] == "경기도 전체"
    assert payload[0]["pollster"] == "테스트기관"
    assert payload[0]["survey_start_date"] == "2026-03-20"
    assert payload[0]["survey_end_date"] == "2026-03-21"
    assert payload[0]["sample_size"] == 1000
    assert payload[0]["margin_of_error"] == "±3.1%"
    assert "detail" in payload[0]


def test_upsert_polls_step_uses_survey_metadata(monkeypatch, tmp_path):
    workflow_module = _load_workflow_module()

    artifact_path = tmp_path / "results.json"
    artifact_path.write_text(
        json.dumps(
            [
                {
                    "registration_number": "REG-1",
                    "source_url": "https://example.com/detail/1",
                    "pdf_path": "/tmp/result.pdf",
                    "election_type": "제9회 전국동시지방선거",
                    "region": "경기도 전체",
                    "election_name": "광역단체장선거",
                    "pollster": "테스트기관",
                    "sponsor": "테스트스폰서",
                    "survey_start_date": "2026-03-20",
                    "survey_end_date": "2026-03-21",
                    "sample_size": 1000,
                    "margin_of_error": "±3.1%",
                    "questions": [
                        {
                            "question_number": 1,
                            "question_title": "Q1",
                            "response_options": ["A", "B"],
                            "overall_n_completed": 500,
                            "overall_n_weighted": 500,
                            "overall_percentages": [40.0, 60.0],
                        }
                    ],
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    captured: dict[str, object] = {}

    class _FakeDB:
        def ensure_tables(self):
            captured["ensured"] = True

        def upsert_surveys(self, rows):
            captured["survey_rows"] = rows
            return len(rows)

        def upsert_questions(self, rows):
            captured["question_rows"] = rows
            return 99

        def replace_options(self, question_id, options):
            captured["options"] = options
            return len(options)

    monkeypatch.setattr(
        workflow_module.PollsWorkflowManager,
        "_build_db_manager",
        lambda self: _FakeDB(),
    )

    result = workflow_module.PollsWorkflowManager("test").upsert_polls_step(
        str(artifact_path)
    )

    assert result["mode"] == "test_db"
    assert result["upserted_surveys"] == 1
    assert result["upserted_questions"] == 2
    survey_row = captured["survey_rows"][0]
    assert survey_row["election_type"] == "제9회 전국동시지방선거"
    assert survey_row["region"] == "경기도 전체"
    assert survey_row["election_name"] == "광역단체장선거"
    assert survey_row["pollster"] == "테스트기관"
    assert survey_row["sponsor"] == "테스트스폰서"
    assert survey_row["survey_start_date"] == "2026-03-20"
    assert survey_row["survey_end_date"] == "2026-03-21"
    assert survey_row["sample_size"] == 1000
    assert survey_row["margin_of_error"] == "±3.1%"
    assert captured["question_rows"][0]["question_number"] == 1
    assert captured["options"] == [
        {"option_name": "A", "percentage": 40.0},
        {"option_name": "B", "percentage": 60.0},
    ]


def test_upsert_polls_step_normalizes_party_option_names(monkeypatch, tmp_path):
    workflow_module = _load_workflow_module()

    artifact_path = tmp_path / "results.json"
    artifact_path.write_text(
        json.dumps(
            [
                {
                    "registration_number": "REG-2",
                    "source_url": "https://example.com/detail/2",
                    "pdf_path": "/tmp/result2.pdf",
                    "election_type": "제9회 전국동시지방선거",
                    "region": "서울특별시 전체",
                    "election_name": "광역단체장선거",
                    "pollster": "테스트기관",
                    "sponsor": "테스트스폰서",
                    "survey_start_date": "2026-04-01",
                    "survey_end_date": "2026-04-02",
                    "sample_size": 1000,
                    "margin_of_error": "±3.1%",
                    "questions": [
                        {
                            "question_number": 1,
                            "question_title": "정당지지도",
                            "response_options": [
                                "조국 혁신당",
                                "조국혁 신당",
                                "국민의 힘",
                                "기타",
                            ],
                            "overall_n_completed": 500,
                            "overall_n_weighted": 500,
                            "overall_percentages": [4.1, 1.3, 25.0, 3.0],
                        }
                    ],
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    captured: dict[str, object] = {}

    class _FakeDB:
        def ensure_tables(self):
            captured["ensured"] = True

        def upsert_surveys(self, rows):
            return len(rows)

        def upsert_questions(self, rows):
            return 100

        def replace_options(self, question_id, options):
            captured["options"] = options
            return len(options)

    monkeypatch.setattr(
        workflow_module.PollsWorkflowManager,
        "_build_db_manager",
        lambda self: _FakeDB(),
    )

    result = workflow_module.PollsWorkflowManager("test").upsert_polls_step(
        str(artifact_path)
    )

    assert result["upserted_surveys"] == 1
    assert captured["options"] == [
        {"option_name": "조국혁신당", "percentage": 4.1},
        {"option_name": "조국혁신당", "percentage": 1.3},
        {"option_name": "국민의힘", "percentage": 25.0},
        {"option_name": "기타", "percentage": 3.0},
    ]


def _load_polls_ingest_dag_module():
    pendulum_module = types.ModuleType("pendulum")
    pendulum_module.datetime = lambda *args, **kwargs: None
    sys.modules["pendulum"] = pendulum_module

    airflow_module = types.ModuleType("airflow")
    airflow_models = types.ModuleType("airflow.models")
    airflow_models_dag = types.ModuleType("airflow.models.dag")
    airflow_models_param = types.ModuleType("airflow.models.param")
    airflow_operators = types.ModuleType("airflow.operators")
    airflow_operators_python = types.ModuleType("airflow.operators.python")

    class _FakeDAG:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class _FakeParam:
        def __init__(self, default=None, **kwargs):
            self.default = default

    class _FakePythonOperator:
        def __init__(self, *args, **kwargs):
            self.kwargs = kwargs

        def __rshift__(self, other):
            return other

    airflow_models_dag.DAG = _FakeDAG
    airflow_models_param.Param = _FakeParam
    airflow_operators_python.PythonOperator = _FakePythonOperator

    sys.modules["airflow"] = airflow_module
    sys.modules["airflow.models"] = airflow_models
    sys.modules["airflow.models.dag"] = airflow_models_dag
    sys.modules["airflow.models.param"] = airflow_models_param
    sys.modules["airflow.operators"] = airflow_operators
    sys.modules["airflow.operators.python"] = airflow_operators_python

    dag_path = (
        Path(__file__).resolve().parents[4]
        / "infra"
        / "airflow"
        / "dags"
        / "polls_ingest_dag.py"
    )
    spec = importlib.util.spec_from_file_location(
        "test_polls_ingest_dag_module", dag_path
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_summarize_run_returns_aggregate_metrics(monkeypatch):
    module = _load_polls_ingest_dag_module()

    fake_workflow_module = types.ModuleType("workflow")
    fake_workflow_module._write_artifact = (
        lambda prefix, payload: "/tmp/polls_summary.json"
    )

    sys.modules["src"] = types.ModuleType("src")
    sys.modules["src.lawdigest_data_pipeline"] = types.ModuleType(
        "lawdigest_data_pipeline"
    )
    sys.modules["src.lawdigest_data_pipeline.polls"] = types.ModuleType("polls")
    sys.modules["src.lawdigest_data_pipeline.polls.workflow"] = fake_workflow_module

    class _FakeTI:
        def xcom_pull(self, task_ids: str):
            return {
                "fetch_polls": {
                    "targets": 1,
                    "target_slugs": ["gyeonggi_governor_9th"],
                    "total": 12,
                    "artifact_path": "/tmp/fetch.json",
                    "elapsed_seconds": 1.1,
                },
                "crawl_details": {
                    "total": 10,
                    "artifact_path": "/tmp/details.json",
                    "elapsed_seconds": 2.2,
                },
                "parse_results": {
                    "parsed": 8,
                    "questions_total": 42,
                    "saved_paths": ["/tmp/a.json", "/tmp/b.json"],
                    "artifact_path": "/tmp/results.json",
                    "elapsed_seconds": 3.3,
                },
                "upsert_polls": {
                    "upserted_surveys": 8,
                    "upserted_questions": 42,
                    "elapsed_seconds": 4.4,
                },
            }[task_ids]

    module._RUN_STARTED_AT = 100.0
    monkeypatch.setattr(module, "monotonic", lambda: 112.345)

    summary = module.summarize_run(
        params={
            "execution_mode": "test",
            "targets_path": "services/data/config/poll_targets.gyeonggi.json",
        },
        ti=_FakeTI(),
    )

    assert summary["mode"] == "test"
    assert summary["target_count"] == 1
    assert summary["fetched_total"] == 12
    assert summary["details_total"] == 10
    assert summary["parsed_total"] == 8
    assert summary["questions_total"] == 42
    assert summary["saved_paths_count"] == 2
    assert summary["upserted_surveys"] == 8
    assert summary["upserted_questions"] == 42
    assert summary["total_elapsed_seconds"] == 12.345
    assert summary["artifact_path"].endswith(".json")
