from unittest.mock import MagicMock, patch


def _mock_connection(fetch_rows=None):
    conn = MagicMock()
    cur = conn.cursor.return_value.__enter__.return_value
    cur.fetchall.return_value = fetch_rows or []
    return conn


def test_update_bill_summary_skips_summary_tags_when_column_absent():
    from lawdigest_ai.db import update_bill_summary

    conn = _mock_connection()
    cur = conn.cursor.return_value.__enter__.return_value

    with patch("lawdigest_ai.db.get_db_connection", return_value=conn), patch(
        "lawdigest_ai.db.get_bill_table_columns",
        return_value={"bill_id", "title", "gpt_summary"},
    ):
        update_bill_summary(
            bill_id="B001",
            title="짧은 요약",
            gpt_summary="상세 요약",
            summary_tags='["태그"]',
            mode="prod",
        )

    query, params = cur.execute.call_args.args
    assert "summary_tags" not in query
    assert params == ("짧은 요약", "상세 요약", "B001")
