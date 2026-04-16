from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_querydsl_main_bill_feed_filters_ready_only():
    source = (
        REPO_ROOT / "services/backend/src/main/java/com/everyones/lawmaking/repository/BillRepositoryImpl.java"
    ).read_text(encoding="utf-8")

    assert "ingestStatus" in source
    assert "READY" in source


def test_bill_search_query_filters_ready_only():
    source = (
        REPO_ROOT / "services/backend/src/main/java/com/everyones/lawmaking/repository/BillRepository.java"
    ).read_text(encoding="utf-8")

    assert "ingest_status = 'READY'" in source
