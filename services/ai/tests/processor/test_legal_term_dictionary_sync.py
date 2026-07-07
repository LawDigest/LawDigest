from lawdigest_ai.processor.legal_term_dictionary_sync import (
    fetch_legal_term_dictionary_items,
    normalize_legal_term,
    run_legal_term_dictionary_sync,
)


def test_normalize_legal_term_compacts_spacing_and_middle_dot():
    assert normalize_legal_term("위임 ㆍ 위탁") == "위임·위탁"


def test_fetch_legal_term_dictionary_items_reads_list_and_body_definitions():
    class FakeClient:
        enabled = True

        def search_legal_dictionary_terms(self, query, *, display, page):
            assert query == "결격"
            assert display == 10
            assert page == 1
            return [
                {"법령용어명": "결격사유", "법령용어ID": "123"},
                {"법령용어명": "정의없는용어", "법령용어ID": "456"},
            ]

        def get_legal_term_definitions(self, query):
            if query == "결격사유":
                return ("일정한 자격을 가질 수 없게 하는 법정 사유를 말한다.",), ("법령용어사전",)
            return (), ()

    items = fetch_legal_term_dictionary_items(query="결격", page_size=10, max_pages=1, client=FakeClient())

    assert items == [
        {
            "source": "law.go.kr",
            "source_term_id": "123",
            "term": "결격사유",
            "normalized_term": "결격사유",
            "definition": "일정한 자격을 가질 수 없게 하는 법정 사유를 말한다.",
            "definition_sources": '["법령용어사전"]',
            "raw_payload": '{"법령용어명": "결격사유", "법령용어ID": "123"}',
        }
    ]


def test_run_legal_term_dictionary_sync_dry_run_does_not_upsert():
    class FakeClient:
        enabled = True

        def search_legal_dictionary_terms(self, query, *, display, page):
            return [{"법령용어명": "결격사유", "법령용어ID": "123"}]

        def get_legal_term_definitions(self, query):
            return ("일정한 자격을 가질 수 없게 하는 법정 사유를 말한다.",), ()

    result = run_legal_term_dictionary_sync(
        mode="dry_run",
        query="결격",
        page_size=10,
        max_pages=1,
        client=FakeClient(),
    )

    assert result["dry_run"] is True
    assert result["fetched_count"] == 1
    assert result["upserted_count"] == 0
    assert result["terms"] == ["결격사유"]


def test_run_legal_term_dictionary_sync_starts_from_requested_page_and_upserts_per_page(monkeypatch):
    class FakeClient:
        enabled = True

        def search_legal_dictionary_terms(self, query, *, display, page):
            assert query == ""
            assert display == 2
            return {
                3: [
                    {"법령용어명": "세번째페이지용어", "법령용어ID": "300"},
                    {"법령용어명": "세번째페이지중복", "법령용어ID": "301"},
                ],
                4: [
                    {"법령용어명": "네번째페이지용어", "법령용어ID": "400"},
                ],
            }[page]

        def get_legal_term_definitions(self, query):
            return (f"{query} 정의",), ("법령용어사전",)

    upserted_batches = []

    def fake_upsert(items, *, mode):
        upserted_batches.append((mode, [item["term"] for item in items]))
        return len(items)

    monkeypatch.setattr("lawdigest_ai.processor.legal_term_dictionary_sync._upsert_dictionary_items", fake_upsert)

    result = run_legal_term_dictionary_sync(
        mode="test",
        query="",
        page_size=2,
        start_page=3,
        max_pages=2,
        client=FakeClient(),
    )

    assert upserted_batches == [
        ("test", ["세번째페이지용어", "세번째페이지중복"]),
        ("test", ["네번째페이지용어"]),
    ]
    assert result["start_page"] == 3
    assert result["pages_processed"] == 2
    assert result["fetched_count"] == 3
    assert result["upserted_count"] == 3
    assert result["page_results"] == [
        {"page": 3, "rows_count": 2, "items_count": 2, "upserted_count": 2, "attempts": 1},
        {"page": 4, "rows_count": 1, "items_count": 1, "upserted_count": 1, "attempts": 1},
    ]


def test_run_legal_term_dictionary_sync_retries_failed_page_and_records_attempts(monkeypatch):
    class FakeClient:
        enabled = True

        def __init__(self):
            self.calls = 0

        def search_legal_dictionary_terms(self, query, *, display, page):
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("temporary api failure")
            return [{"법령용어명": "재시도용어", "법령용어ID": "500"}]

        def get_legal_term_definitions(self, query):
            return ("재시도 후 정의",), ()

    monkeypatch.setattr(
        "lawdigest_ai.processor.legal_term_dictionary_sync._upsert_dictionary_items",
        lambda items, *, mode: len(items),
    )

    result = run_legal_term_dictionary_sync(
        mode="test",
        query="",
        page_size=1,
        max_pages=1,
        max_retries=1,
        client=FakeClient(),
    )

    assert result["failed_pages"] == []
    assert result["page_results"] == [
        {"page": 1, "rows_count": 1, "items_count": 1, "upserted_count": 1, "attempts": 2}
    ]
