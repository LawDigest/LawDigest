import json
from types import SimpleNamespace
from unittest.mock import MagicMock


def _sample_bill():
    return {
        "bill_id": "B001",
        "bill_name": "테스트법",
        "summary": "법안의 핵심 내용",
        "proposers": "홍길동",
        "proposer_kind": "의원",
        "propose_date": "2024-01-01",
        "stage": "위원회",
    }


def test_build_request_rows_uses_gemini_batch_shape_with_shared_schema():
    from lawdigest_ai.processor.providers.gemini_batch import GeminiBatchProvider
    from lawdigest_ai.processor.providers.openai_batch import BatchStructuredSummary

    provider = GeminiBatchProvider(client=MagicMock())

    rows = provider.build_request_rows([_sample_bill()], model="models/gemini-2.5-flash")

    assert len(rows) == 1
    assert rows[0]["key"] == "B001"
    assert rows[0]["request"]["generation_config"]["response_mime_type"] == "application/json"
    assert (
        rows[0]["request"]["generation_config"]["response_json_schema"]
        == BatchStructuredSummary.model_json_schema(by_alias=True)
    )
    assert "B001" in rows[0]["request"]["contents"][0]["parts"][0]["text"]


def test_upload_batch_file_uses_jsonl_mime_type_and_returns_file_name(tmp_path):
    from lawdigest_ai.processor.providers.gemini_batch import GeminiBatchProvider

    jsonl_path = tmp_path / "batch.jsonl"
    jsonl_path.write_text('{"key":"B001"}\n', encoding="utf-8")
    client = SimpleNamespace(
        files=SimpleNamespace(upload=MagicMock(return_value=SimpleNamespace(name="files/input-123"))),
        batches=SimpleNamespace(),
    )
    provider = GeminiBatchProvider(client=client)

    uploaded_name = provider.upload_batch_file(str(jsonl_path))

    assert uploaded_name == "files/input-123"
    client.files.upload.assert_called_once_with(
        file=str(jsonl_path),
        config={"display_name": "batch", "mime_type": "jsonl"},
    )


def test_create_batch_job_uses_uploaded_file_name_as_src():
    from lawdigest_ai.processor.providers.gemini_batch import GeminiBatchProvider

    batch_job = SimpleNamespace(name="batches/job-123")
    client = SimpleNamespace(
        files=SimpleNamespace(),
        batches=SimpleNamespace(create=MagicMock(return_value=batch_job)),
    )
    provider = GeminiBatchProvider(client=client)

    created_job = provider.create_batch_job(
        model="models/gemini-2.5-flash",
        source_file_name="files/input-123",
        display_name="lawdigest-batch",
    )

    assert created_job is batch_job
    client.batches.create.assert_called_once_with(
        model="models/gemini-2.5-flash",
        src="files/input-123",
        config={"display_name": "lawdigest-batch"},
    )


def test_get_batch_job_delegates_to_sdk_client():
    from lawdigest_ai.processor.providers.gemini_batch import GeminiBatchProvider

    batch_job = SimpleNamespace(name="batches/job-123")
    client = SimpleNamespace(
        files=SimpleNamespace(),
        batches=SimpleNamespace(get=MagicMock(return_value=batch_job)),
    )
    provider = GeminiBatchProvider(client=client)

    fetched_job = provider.get_batch_job("batches/job-123")

    assert fetched_job is batch_job
    client.batches.get.assert_called_once_with(name="batches/job-123")


def test_download_output_file_decodes_utf8_bytes():
    from lawdigest_ai.processor.providers.gemini_batch import GeminiBatchProvider

    client = SimpleNamespace(
        files=SimpleNamespace(download=MagicMock(return_value="결과".encode("utf-8"))),
        batches=SimpleNamespace(),
    )
    provider = GeminiBatchProvider(client=client)

    content = provider.download_output_file("files/output-123")

    assert content == "결과"
    client.files.download.assert_called_once_with(file="files/output-123")


def test_parse_output_line_reads_text_parts_and_validates_shared_schema():
    from lawdigest_ai.processor.providers.gemini_batch import GeminiBatchProvider
    from lawdigest_ai.processor.providers.openai_batch import BatchStructuredSummary

    provider = GeminiBatchProvider(client=MagicMock())
    summary = BatchStructuredSummary(
        brief_summary="요약",
        gpt_summary="상세",
        tags=["태그1", "태그2", "태그3", "태그4", "태그5"],
    ).model_dump_json(by_alias=True)
    split_at = len(summary) // 2
    line = json.dumps(
        {
            "key": "B001",
            "response": {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {"text": summary[:split_at]},
                                {"text": summary[split_at:]},
                            ]
                        }
                    }
                ]
            },
        },
        ensure_ascii=False,
    )

    result = provider.parse_output_line(line)

    assert result.bill_id == "B001"
    assert result.brief_summary == "요약"
    assert result.gpt_summary == "상세"
    assert result.tags == ["태그1", "태그2", "태그3", "태그4", "태그5"]
    assert result.error is None


def test_parse_output_line_surfaces_row_error():
    from lawdigest_ai.processor.providers.gemini_batch import GeminiBatchProvider

    provider = GeminiBatchProvider(client=MagicMock())
    line = json.dumps(
        {"key": "B002", "error": {"code": 400, "message": "invalid request"}},
        ensure_ascii=False,
    )

    result = provider.parse_output_line(line)

    assert result.bill_id == "B002"
    assert result.brief_summary is None
    assert result.gpt_summary is None
    assert result.tags is None
    assert "invalid request" in (result.error or "")


def test_parse_output_line_reports_schema_validation_failure():
    from lawdigest_ai.processor.providers.gemini_batch import GeminiBatchProvider

    provider = GeminiBatchProvider(client=MagicMock())
    line = json.dumps(
        {
            "key": "B003",
            "response": {"candidates": [{"content": {"parts": [{"text": '{"briefSummary":"요약"}'}]}}]},
        },
        ensure_ascii=False,
    )

    result = provider.parse_output_line(line)

    assert result.bill_id == "B003"
    assert result.brief_summary is None
    assert result.gpt_summary is None
    assert result.tags is None
    assert "검증 실패" in (result.error or "")
