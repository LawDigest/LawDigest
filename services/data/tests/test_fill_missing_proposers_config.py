from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest


def _load_script_module():
    module_name = "fill_missing_proposers"
    script_path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "db"
        / "fill_missing_proposers.py"
    )
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_test_db_config_requires_environment_credentials(monkeypatch):
    fake_db_module = ModuleType("lawdigest_ai.db")

    def _missing_config():
        raise ValueError("DB 환경변수 누락: TEST_DB_PASSWORD")

    fake_db_module.get_test_db_config = _missing_config
    monkeypatch.setitem(sys.modules, "lawdigest_ai.db", fake_db_module)

    module = _load_script_module()

    with pytest.raises(ValueError, match="TEST_DB_PASSWORD"):
        module._resolve_test_db_config()
