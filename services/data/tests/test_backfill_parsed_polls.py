from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


def _load_module():
    module_name = "backfill_parsed_polls"
    sys.modules.pop(module_name, None)
    script_path = (
        Path(__file__).resolve().parents[2]
        / "data"
        / "scripts"
        / "polls"
        / "backfill_parsed_polls.py"
    )
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_iter_candidate_files_filters_pollsters(tmp_path, monkeypatch):
    module = _load_module()
    parsed_root = tmp_path / "parsed"
    parsed_root.mkdir()

    embrain = parsed_root / "a" / "b" / "c" / "one.json"
    embrain.parent.mkdir(parents=True)
    embrain.write_text(
        json.dumps({"pollster": "(주)엠브레인퍼블릭"}, ensure_ascii=False),
        encoding="utf-8",
    )

    other = parsed_root / "a" / "b" / "c" / "two.json"
    other.write_text(json.dumps({"pollster": "기타"}, ensure_ascii=False), encoding="utf-8")

    files = module._iter_candidate_files(parsed_root, module.POLLSTER_FILTERS)

    assert files == [embrain]


def test_merge_survey_row_preserves_existing_metadata():
    module = _load_module()
    parsed = {
        "registration_number": "REG-1",
        "election_type": "제9회 전국동시지방선거",
        "region": "경기도 전체",
        "election_name": "광역단체장선거",
        "pollster": "(주)엠브레인퍼블릭",
        "sponsor": "중부일보",
        "sample_size": 800,
    }
    existing = {
        "source_url": "https://example.com/detail/1",
        "pdf_path": "/old/path.pdf",
        "sponsor": "기존스폰서",
    }

    merged = module._merge_survey_row(parsed, Path("/tmp/new.pdf"), existing)

    assert merged["source_url"] == "https://example.com/detail/1"
    assert merged["pdf_path"] == "/old/path.pdf"
    assert merged["sponsor"] == "중부일보"
    assert merged["sample_size"] == 800
