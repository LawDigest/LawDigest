from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_backfill_module():
    module_name = "poll_option_party_backfill"
    script_path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "db"
        / "backfill_poll_party_option_names.py"
    )
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_build_backfill_updates_only_returns_changed_rows():
    module = _load_backfill_module()

    rows = [
        {"option_id": 1, "option_name": "조국 혁신당"},
        {"option_id": 2, "option_name": "조국혁 신당"},
        {"option_id": 3, "option_name": "국민의 힘"},
        {"option_id": 4, "option_name": "더불어민주당"},
        {"option_id": 5, "option_name": "기타"},
    ]

    updates = module.build_backfill_updates(rows)

    assert updates == [
        {"option_id": 1, "before": "조국 혁신당", "after": "조국혁신당"},
        {"option_id": 2, "before": "조국혁 신당", "after": "조국혁신당"},
        {"option_id": 3, "before": "국민의 힘", "after": "국민의힘"},
    ]


def test_summarize_updates_counts_before_and_after_names():
    module = _load_backfill_module()

    updates = [
        {"option_id": 1, "before": "조국 혁신당", "after": "조국혁신당"},
        {"option_id": 2, "before": "조국혁 신당", "after": "조국혁신당"},
        {"option_id": 3, "before": "국민의 힘", "after": "국민의힘"},
    ]

    summary = module.summarize_updates(updates)

    assert summary["update_count"] == 3
    assert summary["before_counts"] == {
        "조국 혁신당": 1,
        "조국혁 신당": 1,
        "국민의 힘": 1,
    }
    assert summary["after_counts"] == {
        "조국혁신당": 2,
        "국민의힘": 1,
    }
