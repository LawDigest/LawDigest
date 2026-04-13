"""기존 parsed 결과를 현재 파서로 재생성하고 Polls DB에 반영한다.

기본 동작은 dry-run이며, ``--apply`` 를 주면 디스크 JSON을 덮어쓰고
DB upsert까지 수행한다.

기본 대상:
  - 엠브레인퍼블릭
  - 윈지코리아컨설팅

사용법:
    cd services/data

    # 변경 대상 미리보기
    python scripts/polls/backfill_parsed_polls.py

    # 테스트 DB에 실제 반영
    python scripts/polls/backfill_parsed_polls.py --apply

    # 운영 DB 반영
    python scripts/polls/backfill_parsed_polls.py --mode prod --apply
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[4]
DATA_SRC = PROJECT_ROOT / "services" / "data" / "src"
AI_SRC = PROJECT_ROOT / "services" / "ai" / "src"

for path in (str(DATA_SRC), str(AI_SRC)):
    if path not in sys.path:
        sys.path.insert(0, path)

from lawdigest_ai.db import get_prod_db_config, get_test_db_config  # noqa: E402
from lawdigest_data.connectors.PollsDatabaseManager import PollsDatabaseManager  # noqa: E402
from lawdigest_data.core.WorkFlowManager import WorkFlowManager  # noqa: E402
from lawdigest_data.polls.normalization import normalize_party_name  # noqa: E402
from lawdigest_data.polls.parser import PollResultParser  # noqa: E402

POLLSTER_FILTERS = ("엠브레인퍼블릭", "윈지코리아컨설팅")
PARSED_ROOT = PROJECT_ROOT / "services" / "data" / "output" / "parsed"
PDF_ROOT = PROJECT_ROOT / "services" / "data" / "output" / "pdfs"
REGISTRY_PATH = PROJECT_ROOT / "services" / "data" / "config" / "parser_registry.json"
_UNSAFE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def _safe(name: str) -> str:
    name = _UNSAFE.sub("_", name)
    return name.strip(". ") or "_"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _matches_pollster(pollster: str, filters: Iterable[str]) -> bool:
    return any(token in pollster for token in filters)


def _iter_candidate_files(
    parsed_root: Path,
    pollster_filters: Iterable[str],
) -> list[Path]:
    files: list[Path] = []
    for path in sorted(parsed_root.rglob("*.json")):
        try:
            data = _load_json(path)
        except Exception:
            continue
        pollster = str(data.get("pollster") or "")
        if not pollster or not _matches_pollster(pollster, pollster_filters):
            continue
        files.append(path)
    return files


def _build_pdf_path(parsed_path: Path, data: dict[str, Any]) -> Path:
    election_name = str(data.get("election_name") or parsed_path.parents[2].name)
    region = str(data.get("region") or parsed_path.parents[1].name)
    pdf_filename = str(data.get("pdf_filename") or f"{parsed_path.stem}.pdf")
    return PDF_ROOT / election_name / region / pdf_filename


def _merge_survey_row(
    parsed: dict[str, Any],
    pdf_path: Path,
    existing: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    existing = existing or {}

    def pick(*values):
        for value in values:
            if value not in (None, ""):
                return value
        return None

    row = {
        "registration_number": parsed.get("registration_number"),
        "election_type": pick(parsed.get("election_type"), existing.get("election_type"), ""),
        "region": pick(parsed.get("region"), existing.get("region"), ""),
        "election_name": pick(parsed.get("election_name"), existing.get("election_name"), ""),
        "pollster": pick(parsed.get("pollster"), existing.get("pollster"), ""),
        "sponsor": pick(parsed.get("sponsor"), existing.get("sponsor"), ""),
        "survey_start_date": pick(parsed.get("survey_start_date"), existing.get("survey_start_date")),
        "survey_end_date": pick(parsed.get("survey_end_date"), existing.get("survey_end_date")),
        "sample_size": pick(parsed.get("sample_size"), existing.get("sample_size")),
        "margin_of_error": pick(parsed.get("margin_of_error"), existing.get("margin_of_error"), ""),
        "source_url": pick(parsed.get("source_url"), existing.get("source_url"), ""),
        "pdf_path": pick(parsed.get("pdf_path"), existing.get("pdf_path"), str(pdf_path)),
    }
    return row


def _load_existing_survey_row(db: PollsDatabaseManager, registration_number: str) -> dict[str, Any]:
    row = db.execute_query(
        "SELECT * FROM PollSurvey WHERE registration_number = %s",
        (registration_number,),
        fetch_one=True,
    )
    return dict(row or {})


def _normalize_options(options: list[str], percentages: list[float]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for option, pct in zip(options, percentages):
        try:
            normalized_pct = float(pct)
        except (TypeError, ValueError):
            continue
        if normalized_pct < 0 or normalized_pct > 100:
            continue
        normalized.append(
            {
                "option_name": normalize_party_name(option),
                "percentage": round(normalized_pct, 2),
            }
        )
    return normalized


def _resolve_db_config(mode: str) -> dict[str, Any]:
    normalized = WorkFlowManager.normalize_execution_mode(mode)
    if normalized == "prod":
        cfg = get_prod_db_config()
    else:
        cfg = get_test_db_config()
    return cfg


def _build_db_manager(mode: str) -> PollsDatabaseManager:
    cfg = _resolve_db_config(mode)
    return PollsDatabaseManager(
        host=cfg["host"],
        port=cfg["port"],
        username=cfg["user"],
        password=cfg["password"],
        database=cfg["database"],
    )


def run_backfill(
    *,
    mode: str,
    apply: bool,
    pollster_filters: Iterable[str] = POLLSTER_FILTERS,
    limit: Optional[int] = None,
) -> dict[str, Any]:
    normalized_mode = WorkFlowManager.normalize_execution_mode(mode)
    parser = PollResultParser(registry_path=REGISTRY_PATH)
    candidate_files = _iter_candidate_files(PARSED_ROOT, pollster_filters)
    if limit and limit > 0:
        candidate_files = candidate_files[:limit]

    db = _build_db_manager(normalized_mode) if apply else None
    if db is not None:
        db.ensure_tables()

    summary = {
        "mode": normalized_mode,
        "apply": apply,
        "candidate_files": len(candidate_files),
        "updated_files": 0,
        "skipped_files": 0,
        "failed_files": 0,
        "updated_questions": 0,
        "updated_options": 0,
        "files": [],
    }

    for path in candidate_files:
        try:
            parsed = _load_json(path)
            pdf_path = _build_pdf_path(path, parsed)
            if not pdf_path.exists():
                summary["failed_files"] += 1
                summary["files"].append(
                    {"path": str(path), "status": "missing_pdf", "pdf_path": str(pdf_path)}
                )
                continue

            pollster_hint = parsed.get("pollster") or None
            results = parser.parse_pdf(pdf_path, pollster_hint=pollster_hint)
            if not results:
                summary["skipped_files"] += 1
                summary["files"].append(
                    {
                        "path": str(path),
                        "status": "empty_result",
                        "question_count": 0,
                    }
                )
                continue

            rebuilt = dict(parsed)
            rebuilt["question_count"] = len(results)
            rebuilt["questions"] = [asdict(result) for result in results]

            if apply:
                _write_json(path, rebuilt)

            summary["updated_files"] += 1
            summary["updated_questions"] += len(results)

            if db is not None:
                existing_row = _load_existing_survey_row(db, str(rebuilt.get("registration_number") or ""))
                survey_row = _merge_survey_row(rebuilt, pdf_path, existing_row)
                db.upsert_surveys([survey_row])
                for question in results:
                    q_id = db.upsert_questions(
                        [
                            {
                                "registration_number": rebuilt.get("registration_number"),
                                "question_number": question.question_number,
                                "question_title": question.question_title,
                                "n_completed": question.overall_n_completed,
                                "n_weighted": question.overall_n_weighted,
                            }
                        ]
                    )
                    if not q_id:
                        continue
                    options = _normalize_options(
                        question.response_options,
                        question.overall_percentages,
                    )
                    summary["updated_options"] += db.replace_options(q_id, options)

            summary["files"].append(
                {
                    "path": str(path),
                    "status": "updated",
                    "pdf_path": str(pdf_path),
                    "question_count": len(results),
                }
            )
        except Exception as exc:  # pragma: no cover - defensive guard for batch runs
            summary["failed_files"] += 1
            summary["files"].append(
                {"path": str(path), "status": "error", "error": str(exc)}
            )

    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="parsed JSON 백필 및 Polls DB 반영")
    parser.add_argument(
        "--mode",
        default="test",
        choices=["dry_run", "test", "test_db", "prod"],
        help="DB 실행 모드",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="실제 파일 덮어쓰기와 DB upsert 수행",
    )
    parser.add_argument(
        "--pollster",
        action="append",
        default=[],
        help="대상 조사기관 필터(부분 문자열). 여러 번 지정 가능",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="처리 대상 제한 수 (0이면 전체)",
    )
    args = parser.parse_args()

    pollster_filters = tuple(args.pollster) or POLLSTER_FILTERS
    summary = run_backfill(
        mode=args.mode,
        apply=args.apply,
        pollster_filters=pollster_filters,
        limit=args.limit or None,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
