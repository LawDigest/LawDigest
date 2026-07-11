from unittest.mock import MagicMock, patch


def _connection_with_cursor():
    connection = MagicMock()
    cursor = MagicMock()
    connection.cursor.return_value.__enter__.return_value = cursor
    return connection, cursor


def test_claim_targets_uses_skip_locked_and_marks_rows_running():
    from lawdigest_ai.processor.bill_tooltip_store import claim_bill_tooltip_targets

    connection, cursor = _connection_with_cursor()
    cursor.fetchall.return_value = [
        {
            "bill_id": "BILL-1",
            "bill_name": "법안 1",
            "gpt_summary": "리포트",
            "source_report_hash": "a" * 64,
        }
    ]

    with patch(
        "lawdigest_ai.processor.bill_tooltip_store.get_db_connection",
        return_value=connection,
    ):
        targets = claim_bill_tooltip_targets(mode="test", limit=1)

    executed_sql = [call.args[0] for call in cursor.execute.call_args_list]
    assert any("FOR UPDATE SKIP LOCKED" in sql for sql in executed_sql)
    assert any("status = 'RUNNING'" in sql for sql in executed_sql)
    assert targets[0]["report_body"].startswith("# 법안 1")
    connection.commit.assert_called_once()


def test_complete_target_rejects_stale_source_report():
    from lawdigest_ai.processor.bill_tooltip_store import complete_bill_tooltip_target

    connection, cursor = _connection_with_cursor()
    cursor.rowcount = 0

    with patch(
        "lawdigest_ai.processor.bill_tooltip_store.get_db_connection",
        return_value=connection,
    ):
        completed = complete_bill_tooltip_target(
            mode="prod",
            bill_id="BILL-1",
            source_report_hash="a" * 64,
            status="APPLIED",
            rendered_summary="툴팁 본문",
            applied_count=1,
            model_name="gpt-5.4",
        )

    assert completed is False
    update_sql = cursor.execute.call_args.args[0]
    assert "SHA2(bill.gpt_summary, 256)" in update_sql
    assert "tooltip.source_report_hash" in update_sql
    connection.commit.assert_called_once()


def test_empty_bill_id_filter_cannot_claim_all_bills():
    from lawdigest_ai.processor.bill_tooltip_store import claim_bill_tooltip_targets

    connection, cursor = _connection_with_cursor()
    cursor.fetchall.return_value = []

    with patch(
        "lawdigest_ai.processor.bill_tooltip_store.get_db_connection",
        return_value=connection,
    ):
        claim_bill_tooltip_targets(mode="prod", limit=5, bill_ids=[])

    executed_sql = [call.args[0] for call in cursor.execute.call_args_list]
    assert all("AND 1 = 0" in sql for sql in executed_sql[:2])
