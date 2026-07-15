from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, replace
from enum import Enum
import json
from typing import Any


class ProviderName(str, Enum):
    OPENAI = "openai"
    GEMINI = "gemini"


@dataclass(frozen=True, slots=True)
class ProviderBase:
    provider_name: ProviderName


@dataclass(frozen=True, slots=True)
class BatchProviderParseResult:
    bill_id: str | None
    title: str | None
    gpt_summary: str | None
    tags: list[str] | None
    error: str | None
    category: str | None = None


@dataclass(frozen=True, slots=True)
class BatchProviderJobState:
    batch_id: str
    status: str
    output_file_id: str | None
    error_file_id: str | None
    error_message: str | None


@dataclass(frozen=True, slots=True)
class InstantProviderResult:
    bill_id: str | None
    title: str | None
    gpt_summary: str | None
    summary_tags: str | None
    error: str | None
    category: str | None = None


class BatchProviderBase(ProviderBase, ABC):
    @abstractmethod
    def build_request_rows(self, bills: list[dict[str, Any]], model: str) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def upload_batch_file(self, jsonl_path: str, display_name: str | None = None) -> str:
        raise NotImplementedError

    @abstractmethod
    def create_batch_job(
        self,
        *,
        model: str,
        source_file_name: str,
        display_name: str | None = None,
    ) -> BatchProviderJobState:
        raise NotImplementedError

    @abstractmethod
    def get_batch_job(self, name: str) -> BatchProviderJobState:
        raise NotImplementedError

    @abstractmethod
    def download_output_file(self, file_name: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def parse_output_line(self, line: str) -> BatchProviderParseResult:
        raise NotImplementedError

    def parse_output_lines(
        self,
        output_jsonl: str,
        expected_bill_ids: list[str] | None = None,
    ) -> list[BatchProviderParseResult]:
        results: list[BatchProviderParseResult] = []
        normalized_lines = [line for line in output_jsonl.splitlines() if line.strip()]

        for index, line in enumerate(normalized_lines):
            result = self.parse_output_line(line)
            if result.bill_id is None and expected_bill_ids is not None and index < len(expected_bill_ids):
                result = replace(result, bill_id=expected_bill_ids[index])
            results.append(result)

        return results


def _normalize_summary_tags(value: Any) -> str | None:
    if value is None or value == "":
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return json.dumps(value, ensure_ascii=False)
    return json.dumps(value, ensure_ascii=False)


class InstantProviderBase(ProviderBase, ABC):
    @abstractmethod
    def summarize_bills(
        self,
        bills: list[dict[str, Any]],
        *,
        model: str | None = None,
    ) -> list[InstantProviderResult]:
        raise NotImplementedError

    def summarize_bill(
        self,
        bill: dict[str, Any],
        *,
        model: str | None = None,
    ) -> InstantProviderResult:
        results = self.summarize_bills([bill], model=model)
        if not results:
            return InstantProviderResult(
                bill_id=bill.get("bill_id"),
                title=None,
                gpt_summary=None,
                summary_tags=None,
                error="요약 결과가 없습니다.",
            )
        return results[0]


class OpenAIInstantProvider(InstantProviderBase):
    def __init__(self) -> None:
        super().__init__(ProviderName.OPENAI)

    def summarize_bills(
        self,
        bills: list[dict[str, Any]],
        *,
        model: str | None = None,
    ) -> list[InstantProviderResult]:
        if not bills:
            return []

        import pandas as pd

        from lawdigest_ai.processor.summarizer import AISummarizer
        from lawdigest_ai.observability import trace_generation, trace_span

        summarizer = AISummarizer()
        with trace_span(
            "openai_instant_summarize",
            input={"provider": "openai", "model": model, "count": len(bills)},
        ) as span:
            with trace_generation(
                span,
                name="openai_summarize_batch",
                model=model or "default",
            ) as generation:
                result_df = summarizer.AI_structured_summarize(
                    pd.DataFrame(bills),
                    model=model,
                )
                if generation is not None:
                    generation.update(output=result_df.shape[0])

        failure_map = {
            str(entry.get("bill_id")): str(entry.get("error"))
            for entry in summarizer.failed_bills
            if entry.get("bill_id") is not None
        }

        results: list[InstantProviderResult] = []
        for row in result_df.to_dict("records"):
            bill_id = row.get("bill_id")
            error = failure_map.get(str(bill_id))
            if not error and (not row.get("title") or not row.get("gpt_summary")):
                error = "OpenAI 요약 결과에 필수 필드가 비어 있습니다."
            results.append(
                InstantProviderResult(
                    bill_id=str(bill_id) if bill_id is not None else None,
                    title=row.get("title"),
                    gpt_summary=row.get("gpt_summary"),
                    summary_tags=_normalize_summary_tags(row.get("summary_tags")),
                    error=error,
                    category=row.get("category"),
                )
            )
        return results


class GeminiInstantProvider(InstantProviderBase):
    def __init__(self, client: Any | None = None) -> None:
        super().__init__(ProviderName.GEMINI)
        object.__setattr__(self, "_client", client)

    def _get_client(self) -> Any:
        if self._client is None:
            from lawdigest_ai.processor.providers.gemini_batch import _build_gemini_client

            object.__setattr__(self, "_client", _build_gemini_client())
        return self._client

    def summarize_bills(
        self,
        bills: list[dict[str, Any]],
        *,
        model: str | None = None,
    ) -> list[InstantProviderResult]:
        if not bills:
            return []

        from lawdigest_ai.processor.providers.gemini_batch import SYSTEM_INSTRUCTION
        from lawdigest_ai.processor.providers.openai_batch import BatchStructuredSummary, _build_prompt_for_bill
        from lawdigest_ai.processor.category_taxonomy import category_label_to_code
        from lawdigest_ai.observability import trace_generation, trace_span

        if not model:
            raise ValueError("Gemini instant provider에는 model이 필요합니다.")

        config = {
            "system_instruction": SYSTEM_INSTRUCTION,
            "temperature": 0.2,
            "response_mime_type": "application/json",
            "response_json_schema": BatchStructuredSummary.model_json_schema(by_alias=True),
        }

        results: list[InstantProviderResult] = []
        client = self._get_client()

        with trace_span(
            "gemini_instant_summarize",
            input={"provider": "gemini", "model": model, "count": len(bills)},
        ) as span:
            for bill in bills:
                bill_id = bill.get("bill_id")
                with trace_generation(
                    span,
                    name="gemini_generate_content",
                    model=model,
                    input={"bill_id": bill_id},
                ) as generation:
                    try:
                        response = client.models.generate_content(
                            model=model,
                            contents=_build_prompt_for_bill(bill),
                            config=config,
                        )
                        parsed = BatchStructuredSummary.model_validate_json(response.text)
                        results.append(
                            InstantProviderResult(
                                bill_id=str(bill_id) if bill_id is not None else None,
                                title=parsed.title,
                                gpt_summary=parsed.gpt_summary,
                                summary_tags=_normalize_summary_tags(parsed.tags),
                                error=None,
                                category=category_label_to_code(parsed.category),
                            )
                        )
                        if generation is not None:
                            generation.update(output={"bill_id": bill_id})
                    except Exception as exc:
                        if generation is not None:
                            generation.update(output=None)
                        results.append(
                            InstantProviderResult(
                                bill_id=str(bill_id) if bill_id is not None else None,
                                title=None,
                                gpt_summary=None,
                                summary_tags=None,
                                error=str(exc),
                            )
                        )
        return results
