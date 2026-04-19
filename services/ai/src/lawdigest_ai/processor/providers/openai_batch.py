from __future__ import annotations

import json
import os
from typing import Any, Dict, List

import requests
from pydantic import BaseModel, ConfigDict, Field
from pydantic import ValidationError

from lawdigest_ai.config import OPENAI_BASE_URL, get_openai_api_key
from lawdigest_ai.processor.providers.types import (
    BatchProviderBase,
    BatchProviderParseResult,
    ProviderName,
)


class BatchStructuredSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")
    brief_summary: str = Field(alias="briefSummary")
    gpt_summary: str = Field(alias="gptSummary")
    tags: List[str] = Field(alias="tags", min_length=5, max_length=5)


def _build_prompt_for_bill(row: Dict[str, Any]) -> str:
    payload = {
        "bill_id": row.get("bill_id"),
        "bill_name": row.get("bill_name"),
        "proposers": row.get("proposers"),
        "proposer_kind": row.get("proposer_kind"),
        "propose_date": str(row.get("propose_date") or ""),
        "stage": row.get("stage"),
        "summary": row.get("summary"),
    }
    return (
        "다음 법안 정보를 보고 JSON으로만 응답하세요.\n"
        "키는 briefSummary, gptSummary, tags 세 개만 포함해야 합니다.\n"
        "briefSummary는 1문장 요약, gptSummary는 3~7개 핵심 항목 중심 상세 요약입니다.\n"
        "tags는 중복 없는 한국어 태그 정확히 5개입니다.\n\n"
        f"{json.dumps(payload, ensure_ascii=False)}"
    )


def _extract_message_content(choice_message: Any) -> str:
    if isinstance(choice_message, str):
        return choice_message
    if isinstance(choice_message, list):
        return "".join(item.get("text", "") for item in choice_message if isinstance(item, dict))
    if isinstance(choice_message, dict):
        content = choice_message.get("content")
        return _extract_message_content(content) if content else ""
    return ""


class OpenAIBatchProvider(BatchProviderBase):
    def __init__(self) -> None:
        super().__init__(ProviderName.OPENAI)

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {get_openai_api_key()}"}

    def build_request_rows(self, bills: List[Dict[str, Any]], model: str) -> List[Dict[str, Any]]:
        summary_schema = BatchStructuredSummary.model_json_schema(by_alias=True)
        return [
            {
                "custom_id": bill["bill_id"],
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "당신은 한국 법안 요약 전문가입니다. 반드시 JSON 객체로만 응답하세요.",
                        },
                        {"role": "user", "content": _build_prompt_for_bill(bill)},
                    ],
                    "temperature": 0.2,
                    "response_format": {
                        "type": "json_schema",
                        "json_schema": {"name": "bill_summary", "strict": True, "schema": summary_schema},
                    },
                },
            }
            for bill in bills
        ]

    def upload_batch_file(self, jsonl_path: str, display_name: str | None = None) -> str:
        del display_name
        with open(jsonl_path, "rb") as file_handle:
            response = requests.post(
                f"{OPENAI_BASE_URL}/files",
                headers=self._headers(),
                data={"purpose": "batch"},
                files={"file": (os.path.basename(jsonl_path), file_handle, "application/jsonl")},
                timeout=60,
            )
        response.raise_for_status()
        return response.json()["id"]

    def create_batch_job(
        self,
        *,
        model: str,
        source_file_name: str,
        display_name: str | None = None,
    ) -> Dict[str, Any]:
        metadata = {"model": model, "pipeline": "lawdigest_ai_batch"}
        if display_name:
            metadata["display_name"] = display_name
        payload = {
            "input_file_id": source_file_name,
            "endpoint": "/v1/chat/completions",
            "completion_window": "24h",
            "metadata": metadata,
        }
        response = requests.post(
            f"{OPENAI_BASE_URL}/batches",
            headers={**self._headers(), "Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=60,
        )
        response.raise_for_status()
        return response.json()

    def get_batch_job(self, name: str) -> Dict[str, Any]:
        response = requests.get(f"{OPENAI_BASE_URL}/batches/{name}", headers=self._headers(), timeout=60)
        response.raise_for_status()
        return response.json()

    def download_output_file(self, file_name: str) -> str:
        response = requests.get(
            f"{OPENAI_BASE_URL}/files/{file_name}/content",
            headers=self._headers(),
            timeout=120,
        )
        response.raise_for_status()
        return response.text

    def parse_output_line(self, line: str) -> BatchProviderParseResult:
        row = json.loads(line)
        bill_id = row.get("custom_id")
        response = row.get("response") or {}
        if response.get("status_code") != 200:
            return BatchProviderParseResult(
                bill_id=bill_id,
                brief_summary=None,
                gpt_summary=None,
                tags=None,
                error=f"status_code={response.get('status_code')}",
            )
        choices = (response.get("body") or {}).get("choices") or []
        if not choices:
            return BatchProviderParseResult(
                bill_id=bill_id,
                brief_summary=None,
                gpt_summary=None,
                tags=None,
                error="choices가 비어있습니다.",
            )
        content = _extract_message_content(choices[0].get("message", {}).get("content", ""))
        if not content:
            return BatchProviderParseResult(
                bill_id=bill_id,
                brief_summary=None,
                gpt_summary=None,
                tags=None,
                error="message content가 비어있습니다.",
            )
        try:
            parsed = BatchStructuredSummary.model_validate_json(content)
        except ValidationError as exc:
            return BatchProviderParseResult(
                bill_id=bill_id,
                brief_summary=None,
                gpt_summary=None,
                tags=None,
                error=f"Structured Output 검증 실패: {exc}",
            )
        return BatchProviderParseResult(
            bill_id=bill_id,
            brief_summary=parsed.brief_summary,
            gpt_summary=parsed.gpt_summary,
            tags=parsed.tags,
            error=None,
        )
