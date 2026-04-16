from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_bill_status_sync_dag_uses_capability_steps():
    source = (REPO_ROOT / "infra/airflow/dags/bill_status_sync_dag.py").read_text(encoding="utf-8")

    assert "fetch_lifecycle_step" in source
    assert "upsert_lifecycle_step" in source
    assert "fetch_vote_step" in source
    assert "upsert_vote_step" in source
    assert "sync_lifecycle" in source
    assert "sync_vote" in source
