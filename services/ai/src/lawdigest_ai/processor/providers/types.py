from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ProviderName(str, Enum):
    OPENAI = "openai"
    GEMINI = "gemini"


@dataclass(frozen=True, slots=True)
class ProviderStub:
    provider_name: ProviderName


class OpenAIBatchProvider(ProviderStub):
    def __init__(self) -> None:
        super().__init__(ProviderName.OPENAI)


class GeminiBatchProvider(ProviderStub):
    def __init__(self) -> None:
        super().__init__(ProviderName.GEMINI)


class OpenAIInstantProvider(ProviderStub):
    def __init__(self) -> None:
        super().__init__(ProviderName.OPENAI)


class GeminiInstantProvider(ProviderStub):
    def __init__(self) -> None:
        super().__init__(ProviderName.GEMINI)
