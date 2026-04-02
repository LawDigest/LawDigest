"""Lazy package exports for lawdigest_data.

초기 import 시점에 무거운 의존성(langchain 등) 로드로 실패하지 않도록
필요한 클래스가 실제로 접근될 때 모듈을 import 한다.

패키지 구조:
  bills/        - 의안 데이터 수집/가공 (DataFetcher, DataProcessor, constants)
  connectors/   - 외부 연동 (DatabaseManager, APISender, Notifier, ReportManager, PollsDatabaseManager)
  core/         - 파이프라인 오케스트레이션 (WorkFlowManager)
  polls/        - 여론조사 데이터 수집/파싱
"""

from importlib import import_module
from pathlib import Path
import sys
from typing import Any

_AI_SRC_PATH = Path(__file__).resolve().parents[3] / "ai" / "src"
if _AI_SRC_PATH.exists():
    ai_src = str(_AI_SRC_PATH)
    if ai_src not in sys.path:
        sys.path.insert(0, ai_src)

__all__ = [
    "DatabaseManager",
    "DataFetcher",
    "DataProcessor",
    "WorkFlowManager",
    "AISummarizer",
    "APISender",
    "Notifier",
    "ReportManager",
    "PollsDatabaseManager",
    "PollsWorkflowManager",
]

_CLASS_TO_MODULE = {
    "DatabaseManager": "connectors.DatabaseManager",
    "DataFetcher": "bills.DataFetcher",
    "DataProcessor": "bills.DataProcessor",
    "WorkFlowManager": "core.WorkFlowManager",
    "AISummarizer": "AISummarizer",
    "APISender": "connectors.APISender",
    "Notifier": "connectors.Notifier",
    "ReportManager": "connectors.ReportManager",
    "PollsDatabaseManager": "connectors.PollsDatabaseManager",
    "PollsWorkflowManager": "polls.workflow",
}


def __getattr__(name: str) -> Any:
    module_name = _CLASS_TO_MODULE.get(name)
    if not module_name:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module = import_module(f".{module_name}", __name__)
    return getattr(module, name)
