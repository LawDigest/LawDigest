from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
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
    ) -> Any:
        raise NotImplementedError

    @abstractmethod
    def get_batch_job(self, name: str) -> Any:
        raise NotImplementedError

    @abstractmethod
    def download_output_file(self, file_name: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def parse_output_line(self, line: str) -> BatchProviderParseResult:
        raise NotImplementedError


class InstantProviderBase(ProviderBase):
    pass


class OpenAIInstantProvider(InstantProviderBase):
    def __init__(self) -> None:
        super().__init__(ProviderName.OPENAI)


class GeminiInstantProvider(InstantProviderBase):
    def __init__(self) -> None:
        super().__init__(ProviderName.GEMINI)
