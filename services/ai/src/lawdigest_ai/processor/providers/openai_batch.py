from __future__ import annotations

import json
from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field

from lawdigest_ai.processor.providers.types import BatchProviderBase, ProviderName


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


class OpenAIBatchProvider(BatchProviderBase):
    def __init__(self) -> None:
        super().__init__(ProviderName.OPENAI)

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
