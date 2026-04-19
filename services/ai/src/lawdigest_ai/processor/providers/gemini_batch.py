from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from pydantic import ValidationError

from lawdigest_ai.config import get_gemini_api_key
from lawdigest_ai.processor.providers.openai_batch import (
    BatchStructuredSummary,
    _build_prompt_for_bill,
)
from lawdigest_ai.processor.providers.types import (
    BatchProviderBase,
    BatchProviderParseResult,
    ProviderName,
)

SYSTEM_INSTRUCTION = "당신은 한국 법안 요약 전문가입니다. 반드시 JSON 객체로만 응답하세요."
GeminiBatchResult = BatchProviderParseResult


def _build_gemini_client() -> Any:
    from google import genai

    return genai.Client(api_key=get_gemini_api_key())


def _extract_text_from_response(response: dict[str, Any]) -> str:
    candidates = response.get("candidates") or []
    if not candidates:
        return ""
    content = (candidates[0] or {}).get("content") or {}
    parts = content.get("parts") or []
    texts = [
        part.get("text", "")
        for part in parts
        if isinstance(part, dict) and isinstance(part.get("text"), str)
    ]
    return "".join(texts).strip()


def _resolve_response_payload(row: dict[str, Any]) -> dict[str, Any]:
    response = row.get("response")
    if isinstance(response, dict):
        return response
    return row


def _extract_error_payload(row: dict[str, Any], response_payload: dict[str, Any]) -> Any | None:
    if row.get("error") is not None:
        return row["error"]
    if response_payload.get("error") is not None:
        return response_payload["error"]
    if response_payload is row and not response_payload.get("candidates"):
        error_keys = {"status", "code", "message", "details"}
        if error_keys.intersection(response_payload):
            return response_payload
    return None


def _default_display_name(source_file_name: str) -> str:
    return f"lawdigest-gemini-{source_file_name.replace('/', '-')}"


def _format_error(error: Any) -> str:
    if isinstance(error, str):
        return error
    if isinstance(error, dict):
        message = error.get("message")
        if isinstance(message, str) and message:
            return message
        return json.dumps(error, ensure_ascii=False)
    return str(error)


class GeminiBatchProvider(BatchProviderBase):
    def __init__(
        self,
        client: Any | None = None,
        client_factory: Callable[[], Any] | None = None,
    ) -> None:
        super().__init__(ProviderName.GEMINI)
        object.__setattr__(self, "_client", client)
        object.__setattr__(self, "_client_factory", client_factory or _build_gemini_client)

    def _get_client(self) -> Any:
        if self._client is None:
            object.__setattr__(self, "_client", self._client_factory())
        return self._client

    def build_request_rows(self, bills: list[dict[str, Any]], model: str) -> list[dict[str, Any]]:
        del model
        summary_schema = BatchStructuredSummary.model_json_schema(by_alias=True)
        return [
            {
                "key": bill["bill_id"],
                "request": {
                    "system_instruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
                    "contents": [{"role": "user", "parts": [{"text": _build_prompt_for_bill(bill)}]}],
                    "generation_config": {
                        "temperature": 0.2,
                        "response_mime_type": "application/json",
                        "response_json_schema": summary_schema,
                    },
                },
            }
            for bill in bills
        ]

    def upload_batch_file(self, jsonl_path: str, display_name: str | None = None) -> str:
        upload = self._get_client().files.upload(
            file=jsonl_path,
            config={
                "display_name": display_name or Path(jsonl_path).stem,
                "mime_type": "jsonl",
            },
        )
        return upload.name

    def create_batch_job(
        self,
        *,
        model: str,
        source_file_name: str,
        display_name: str | None = None,
    ) -> Any:
        config = {"display_name": display_name or _default_display_name(source_file_name)}
        return self._get_client().batches.create(model=model, src=source_file_name, config=config)

    def get_batch_job(self, name: str) -> Any:
        return self._get_client().batches.get(name=name)

    def download_output_file(self, file_name: str) -> str:
        content = self._get_client().files.download(file=file_name)
        if isinstance(content, bytes):
            return content.decode("utf-8")
        return str(content)

    def parse_output_line(self, line: str) -> GeminiBatchResult:
        row = json.loads(line)
        bill_id = row.get("key") or row.get("custom_id")
        response_payload = _resolve_response_payload(row)
        error_payload = _extract_error_payload(row, response_payload)
        if error_payload is not None:
            return GeminiBatchResult(
                bill_id=bill_id,
                brief_summary=None,
                gpt_summary=None,
                tags=None,
                error=_format_error(error_payload),
            )

        content = _extract_text_from_response(response_payload)
        if not content:
            return GeminiBatchResult(
                bill_id=bill_id,
                brief_summary=None,
                gpt_summary=None,
                tags=None,
                error="response text가 비어있습니다.",
            )

        try:
            parsed = BatchStructuredSummary.model_validate_json(content)
        except ValidationError as exc:
            return GeminiBatchResult(
                bill_id=bill_id,
                brief_summary=None,
                gpt_summary=None,
                tags=None,
                error=f"Structured Output 검증 실패: {exc}",
            )

        return GeminiBatchResult(
            bill_id=bill_id,
            brief_summary=parsed.brief_summary,
            gpt_summary=parsed.gpt_summary,
            tags=parsed.tags,
            error=None,
        )
