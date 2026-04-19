from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ProviderName(str, Enum):
    OPENAI = "openai"
    GEMINI = "gemini"


@dataclass(frozen=True, slots=True)
class ProviderBase:
    provider_name: ProviderName


class BatchProviderBase(ProviderBase):
    def build_request_rows(self, bills: list[dict[str, Any]], model: str) -> list[dict[str, Any]]:
        raise NotImplementedError


class InstantProviderBase(ProviderBase):
    pass


class GeminiBatchProvider(BatchProviderBase):
    def __init__(self) -> None:
        super().__init__(ProviderName.GEMINI)


class OpenAIInstantProvider(InstantProviderBase):
    def __init__(self) -> None:
        super().__init__(ProviderName.OPENAI)


class GeminiInstantProvider(InstantProviderBase):
    def __init__(self) -> None:
        super().__init__(ProviderName.GEMINI)
