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
