from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, replace
from enum import Enum
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
    brief_summary: str | None
    gpt_summary: str | None
    tags: list[str] | None
    error: str | None


@dataclass(frozen=True, slots=True)
class BatchProviderJobState:
    batch_id: str
    status: str
    output_file_id: str | None
    error_file_id: str | None
    error_message: str | None


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


class InstantProviderBase(ProviderBase):
    pass


class OpenAIInstantProvider(InstantProviderBase):
    def __init__(self) -> None:
        super().__init__(ProviderName.OPENAI)


class GeminiInstantProvider(InstantProviderBase):
    def __init__(self) -> None:
        super().__init__(ProviderName.GEMINI)
