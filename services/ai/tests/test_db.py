from __future__ import annotations

from unittest.mock import MagicMock


def test_update_bill_summary_updates_bill_and_replaces_summary_tags(monkeypatch):
    from lawdigest_ai import db

    conn = MagicMock()
    cursor = MagicMock()
    cursor.__enter__ = MagicMock(return_value=cursor)
    cursor.__exit__ = MagicMock(return_value=False)
    conn.cursor.return_value = cursor
    monkeypatch.setattr(db, "get_db_connection", lambda mode="test": conn)

    db.update_bill_summary(
        bill_id="B001",
        brief_summary="제목 요약",
        gpt_summary="내용 요약",
        summary_tags='["태그1", "태그2"]',
        mode="prod",
    )

    executed_sql = [call.args[0] for call in cursor.execute.call_args_list]
    bill_update_sql = next(sql for sql in executed_sql if "UPDATE Bill SET" in sql)
    assert "brief_summary=%s" in bill_update_sql
    assert "gpt_summary=%s" in bill_update_sql
    assert "summary_tags" not in bill_update_sql
    assert any("DELETE FROM BillSummaryTag WHERE bill_id=%s" in sql for sql in executed_sql)
    cursor.executemany.assert_called_once()
    insert_sql, insert_params = cursor.executemany.call_args.args
    assert "INSERT INTO BillSummaryTag" in insert_sql
    assert insert_params == [("B001", "태그1"), ("B001", "태그2")]
    conn.commit.assert_called_once()
    conn.close.assert_called_once()
