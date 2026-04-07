"""미분류로 저장된 parsed JSON을 기관명 폴더로 재분류한다.

기본 동작은 dry-run이다.

사용법:
    cd services/data

    # 먼저 재분류 계획만 확인
    python scripts/polls/reclassify_parsed_files.py

    # 실제 파일 이동/수정 적용
    python scripts/polls/reclassify_parsed_files.py --apply

입력:
    output/parsed/{선거명}/{지역명}/미분류/*.json
    tests/polls/fixtures/*.json  (pdf_filename -> pollster 매핑 참고)

출력:
    output/parsed/{선거명}/{지역명}/{기관명}/*.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

_BASE = Path(__file__).resolve().parents[2]
_PARSED_ROOT = _BASE / "output" / "parsed"
_FIXTURES_ROOT = _BASE / "tests" / "polls" / "fixtures"

_UNSAFE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def _safe(name: str) -> str:
    name = _UNSAFE.sub("_", name)
    return name.strip(". ") or "_"


def _normalize_key(text: str) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣]+", "", text or "").lower()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_dt(value: Optional[str]) -> datetime:
    if not value:
        return datetime.min.replace(tzinfo=timezone.utc)
    try:
        cleaned = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(cleaned)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)


def _build_fixture_pollster_map() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for fixture in sorted(_FIXTURES_ROOT.glob("*.json")):
        data = _load_json(fixture)
        pdf_filename = data.get("pdf_filename")
        pollster = data.get("pollster")
        if not pdf_filename or not pollster:
            continue
        mapping[_normalize_key(str(pdf_filename))] = str(pollster)
    return mapping


def _infer_pollster(data: dict[str, Any], fixture_map: dict[str, str]) -> tuple[Optional[str], str]:
    current_pollster = str(data.get("pollster") or "").strip()
    if current_pollster and current_pollster != "미분류":
        return current_pollster, "already_classified"

    pdf_filename = str(data.get("pdf_filename") or "")
    stem = Path(pdf_filename).stem if pdf_filename else ""
    candidates = [
        _normalize_key(pdf_filename),
        _normalize_key(stem),
    ]
    for key in candidates:
        if key in fixture_map:
            return fixture_map[key], "fixture"

    filename = pdf_filename or stem
    hint_rules: list[tuple[str, str]] = [
        (r"여론조사꽃", "여론조사꽃"),
        (r"한길리서치", "한길리서치"),
        (r"드림투데이", "(주)윈지코리아컨설팅"),
        (r"기후위기\s*국민\s*인식조사", "메타보이스(주)"),
        (r"뉴스1", "(주)한국리서치"),
        (r"중부일보", "(주)한국리서치"),
        (r"경기일보", "조원씨앤아이"),
        (r"더팩트", "조원씨앤아이"),
    ]
    for pattern, pollster in hint_rules:
        if re.search(pattern, filename):
            return pollster, "filename_hint"

    return None, "unresolved"


def _choose_destination(source: Path, target_pollster: str) -> Path:
    parts = source.parts
    try:
        idx = parts.index("미분류")
    except ValueError:
        raise ValueError(f"미분류 경로가 아닙니다: {source}")
    dst_parts = list(parts)
    dst_parts[idx] = _safe(target_pollster)
    return Path(*dst_parts)


def _rewrite_payload(data: dict[str, Any], target_pollster: str) -> dict[str, Any]:
    updated = dict(data)
    updated["pollster"] = target_pollster
    return updated


def main() -> int:
    ap = argparse.ArgumentParser(description="미분류 parsed JSON을 기관명 폴더로 재분류")
    ap.add_argument(
        "--apply",
        action="store_true",
        help="실제 파일 이동과 JSON pollster 필드 수정을 적용",
    )
    args = ap.parse_args()

    fixture_map = _build_fixture_pollster_map()
    sources = sorted(_PARSED_ROOT.glob("**/미분류/*.json"))

    if not sources:
        print("재분류할 미분류 파일이 없습니다.")
        return 0

    moved = 0
    replaced = 0
    kept = 0
    unresolved = 0

    print(f"대상 파일 수: {len(sources)}")
    for source in sources:
        data = _load_json(source)
        target_pollster, reason = _infer_pollster(data, fixture_map)
        if not target_pollster:
            unresolved += 1
            print(f"[UNRESOLVED] {source.relative_to(_PARSED_ROOT)}")
            continue

        destination = _choose_destination(source, target_pollster)
        updated = _rewrite_payload(data, target_pollster)
        destination.parent.mkdir(parents=True, exist_ok=True)

        if destination.exists():
            existing = _load_json(destination)
            source_dt = _parse_dt(str(data.get("parsed_at") or ""))
            existing_dt = _parse_dt(str(existing.get("parsed_at") or ""))
            if source_dt > existing_dt:
                action = "replaced"
                if args.apply:
                    destination.write_text(json.dumps(updated, ensure_ascii=False, indent=2), encoding="utf-8")
                    source.unlink()
                replaced += 1
            else:
                action = "kept"
                if args.apply:
                    source.unlink()
                kept += 1
            print(
                f"[{action.upper()}] {source.relative_to(_PARSED_ROOT)} -> "
                f"{destination.relative_to(_PARSED_ROOT)} ({reason})"
            )
            continue

        moved += 1
        print(
            f"[MOVE] {source.relative_to(_PARSED_ROOT)} -> "
            f"{destination.relative_to(_PARSED_ROOT)} ({reason})"
        )
        if args.apply:
            destination.write_text(json.dumps(updated, ensure_ascii=False, indent=2), encoding="utf-8")
            source.unlink()

    print(
        f"\n요약: move={moved}, replaced={replaced}, kept={kept}, unresolved={unresolved}, "
        f"mode={'apply' if args.apply else 'dry-run'}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
