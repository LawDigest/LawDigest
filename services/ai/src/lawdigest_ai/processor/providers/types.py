from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ProviderName(str, Enum):
    OPENAI = "openai"
    GEMINI = "gemini"


@dataclass(frozen=True, slots=True)
class ProviderBase:
    provider_name: ProviderName


class BatchProviderBase(ProviderBase):
    pass


class InstantProviderBase(ProviderBase):
    pass


class OpenAIBatchProvider(BatchProviderBase):
    def __init__(self) -> None:
        super().__init__(ProviderName.OPENAI)


class GeminiBatchProvider(BatchProviderBase):
    def __init__(self) -> None:
        super().__init__(ProviderName.GEMINI)


class OpenAIInstantProvider(InstantProviderBase):
    def __init__(self) -> None:
        super().__init__(ProviderName.OPENAI)


class GeminiInstantProvider(InstantProviderBase):
    def __init__(self) -> None:
        super().__init__(ProviderName.GEMINI)
