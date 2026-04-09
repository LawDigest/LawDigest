from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def test_check_pdfs_script_imports_current_package() -> None:
    script_path = (
        Path(__file__).resolve().parents[2]
        / "scripts"
        / "polls"
        / "check_pdfs.py"
    )
    module_name = "polls_check_pdfs_script"
    sys.modules.pop(module_name, None)

    spec = importlib.util.spec_from_file_location(module_name, script_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert hasattr(module, "main")


def test_download_pdfs_builds_ascii_safe_referer() -> None:
    script_path = (
        Path(__file__).resolve().parents[2]
        / "scripts"
        / "polls"
        / "download_pdfs.py"
    )
    module_name = "polls_download_pdfs_script"
    sys.modules.pop(module_name, None)

    spec = importlib.util.spec_from_file_location(module_name, script_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    safe_url = module._ascii_header_value(
        "https://www.nesdc.go.kr/portal/bbs/B0000005/view.do?searchWrd=서울특별시&pageIndex=1"
    )

    assert safe_url.endswith("searchWrd=%EC%84%9C%EC%9A%B8%ED%8A%B9%EB%B3%84%EC%8B%9C&pageIndex=1")
    assert all(ord(ch) < 128 for ch in safe_url)
