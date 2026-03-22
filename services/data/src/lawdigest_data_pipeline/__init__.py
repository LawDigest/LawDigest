"""Lazy package exports for lawdigest_data_pipeline.

초기 import 시점에 무거운 의존성(langchain 등) 로드로 실패하지 않도록
필요한 클래스가 실제로 접근될 때 모듈을 import 한다.
"""

from importlib import import_module
from typing import Any

__all__ = [
    "DatabaseManager",
    "DataFetcher",
    "DataProcessor",
    "AISummarizer",
    "APISender",
    "WorkFlowManager",
    "Notifier",
    "ReportManager",
]

_CLASS_TO_MODULE = {
    "DatabaseManager": "DatabaseManager",
    "DataFetcher": "DataFetcher",
    "DataProcessor": "DataProcessor",
    "AISummarizer": "AISummarizer",
    "APISender": "APISender",
    "WorkFlowManager": "WorkFlowManager",
    "Notifier": "Notifier",
    "ReportManager": "ReportManager",
}


def __getattr__(name: str) -> Any:
    module_name = _CLASS_TO_MODULE.get(name)
    if not module_name:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module = import_module(f".{module_name}", __name__)
    return getattr(module, name)
