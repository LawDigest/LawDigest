from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_bill_related_dags_import_workflow_manager_from_current_package():
    expected_import = "from lawdigest_data.core.WorkFlowManager import WorkFlowManager"

    dag_paths = [
        REPO_ROOT / "infra/airflow/dags/bill_ingest_dag.py",
        REPO_ROOT / "infra/airflow/dags/manual_bill_collect_dag.py",
        REPO_ROOT / "infra/airflow/dags/bill_status_sync_dag.py",
    ]

    for dag_path in dag_paths:
        source = dag_path.read_text(encoding="utf-8")
        assert expected_import in source, f"{dag_path} should import WorkFlowManager from lawdigest_data.core"


def test_airflow_pythonpath_includes_services_data_src():
    compose_path = REPO_ROOT / "infra/airflow/docker-compose.yaml"
    compose_text = compose_path.read_text(encoding="utf-8")

    assert "/opt/airflow/project/services/data/src" in compose_text
