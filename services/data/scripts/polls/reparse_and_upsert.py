"""14964, 15366, 15891 여론조사 재파싱 후 dev DB에 upsert 하는 one-shot 스크립트.

사용법:
    cd /home/ubuntu/project/Lawdigest/.worktrees/poll-quality-fix-codex/services/data
    PYTHONPATH=src python scripts/polls/reparse_and_upsert.py [--dry-run]
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

_BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_BASE / "src"))

from lawdigest_data.polls.parser import PollResultParser  # noqa: E402
from lawdigest_data.connectors.PollsDatabaseManager import PollsDatabaseManager  # noqa: E402
from lawdigest_data.polls.validation import quality_screen_question_result  # noqa: E402

# ── 대상 여론조사 정의 ─────────────────────────────────────────────────────────
TARGETS = [
    {
        "registration_number": "14964",
        "pdf_path": Path(
            "/home/ubuntu/project/Lawdigest/services/data/output/pdfs"
            "/제9회 전국동시지방선거/서울특별시 전체"
            "/[뉴스1 신년특집] 서울시민 여론조사 통계표_최종.pdf"
        ),
        "pollster": "(주)엠브레인퍼블릭",
        "election_type": "지방선거",
        "region": "서울특별시",
        "election_name": "제9회 전국동시지방선거",
        "sponsor": "뉴스1",
        "survey_start_date": None,
        "survey_end_date": None,
        "sample_size": None,
        "margin_of_error": "",
        "source_url": "",
        "pdf_path_str": "",
    },
    {
        "registration_number": "15366",
        "pdf_path": Path(
            "/home/ubuntu/project/Lawdigest/services/data/output/pdfs"
            "/제9회 전국동시지방선거/서울특별시 전체"
            "/(결과표) KBS 지방선거 여론조사 [02. 서울].pdf"
        ),
        "pollster": "케이스탯리서치",
        "election_type": "지방선거",
        "region": "서울특별시",
        "election_name": "제9회 전국동시지방선거",
        "sponsor": "KBS",
        "survey_start_date": None,
        "survey_end_date": None,
        "sample_size": None,
        "margin_of_error": "",
        "source_url": "",
        "pdf_path_str": "",
    },
    {
        "registration_number": "15891",
        "pdf_path": Path(
            "/home/ubuntu/project/Lawdigest/services/data/output/pdfs"
            "/제9회 전국동시지방선거/서울특별시 전체"
            "/결과표_20260331_여론조사꽃_서울시장_2000_ARS조사_v01.pdf"
        ),
        "pollster": "(주)여론조사꽃",
        "election_type": "지방선거",
        "region": "서울특별시",
        "election_name": "제9회 전국동시지방선거",
        "sponsor": "",
        "survey_start_date": None,
        "survey_end_date": None,
        "sample_size": None,
        "margin_of_error": "",
        "source_url": "",
        "pdf_path_str": "",
    },
]

# ── dev DB 접속 정보 ──────────────────────────────────────────────────────────
TEST_DB = dict(
    host="140.245.74.246",
    port=2812,
    username="root",
    password="eLL-@hjm3K7CgFDV-MKp",
    database="lawTestDB",
)

REGISTRY_PATH = _BASE / "config" / "parser_registry.json"


def _normalize_pct(value) -> float | None:
    try:
        pct = float(value)
    except (TypeError, ValueError):
        return None
    if pct < 0 or pct > 100:
        return None
    return round(pct, 2)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="파싱만 하고 DB 저장 안 함")
    args = ap.parse_args()

    parser = PollResultParser(registry_path=REGISTRY_PATH)

    db = None
    if not args.dry_run:
        db = PollsDatabaseManager(**TEST_DB)
        db.ensure_tables()
        logger.info("dev DB 연결: %s:%s/%s", TEST_DB["host"], TEST_DB["port"], TEST_DB["database"])

    total_surveys = 0
    total_questions = 0

    for t in TARGETS:
        reg = t["registration_number"]
        pdf = t["pdf_path"]

        if not pdf.exists():
            logger.error("[%s] PDF 없음: %s", reg, pdf)
            continue

        logger.info("[%s] 파싱 시작: %s", reg, pdf.name)
        results = parser.parse_pdf(pdf, pollster_hint=t["pollster"])
        logger.info("[%s] 파싱 결과: %d개 질문", reg, len(results))

        if not results:
            logger.warning("[%s] 파싱 결과 0건 — 건너뜀", reg)
            continue

        if args.dry_run:
            for r in results:
                screened = quality_screen_question_result(r)
                status = "PASS" if not screened else f"FAIL({[e.message for e in screened]})"
                logger.info("  Q%s %s  options=%d  pcts=%s  → %s",
                            r.question_number,
                            (r.question_title or "")[:40],
                            len(r.response_options),
                            r.overall_percentages[:3],
                            status)
            continue

        # ── PollSurvey upsert ──────────────────────────────────────────────
        survey_row = {
            "registration_number": reg,
            "election_type": t["election_type"],
            "region": t["region"],
            "election_name": t["election_name"],
            "pollster": t["pollster"],
            "sponsor": t["sponsor"],
            "survey_start_date": t.get("survey_start_date"),
            "survey_end_date": t.get("survey_end_date"),
            "sample_size": t.get("sample_size"),
            "margin_of_error": t.get("margin_of_error", ""),
            "source_url": t.get("source_url", ""),
            "pdf_path": str(pdf),
        }
        db.upsert_surveys([survey_row])
        total_surveys += 1
        logger.info("[%s] PollSurvey upsert 완료", reg)

        # ── PollQuestion + PollOption upsert ───────────────────────────────
        for r in results:
            screened = quality_screen_question_result(r)
            if screened:
                logger.warning("[%s] Q%s 품질 탈락: %s", reg, r.question_number,
                               [e.message for e in screened])
                continue

            q_rows = [{
                "registration_number": reg,
                "question_number": r.question_number,
                "question_title": r.question_title,
                "n_completed": r.overall_n_completed,
                "n_weighted": r.overall_n_weighted,
            }]
            q_id = db.upsert_questions(q_rows)
            if not q_id:
                logger.warning("[%s] Q%s question upsert 실패", reg, r.question_number)
                continue

            options = []
            for opt, pct in zip(r.response_options, r.overall_percentages):
                normalized = _normalize_pct(pct)
                if normalized is None:
                    logger.debug("[%s] Q%s option '%s' pct=%s 스킵", reg, r.question_number, opt, pct)
                    continue
                options.append({"option_name": opt, "percentage": normalized})

            replaced = db.replace_options(q_id, options)
            total_questions += replaced
            logger.info("[%s] Q%s '%s' → %d개 선택지 저장",
                        reg, r.question_number,
                        (r.question_title or "")[:30],
                        replaced)

    if not args.dry_run:
        logger.info("=== 완료: surveys=%d  questions=%d ===", total_surveys, total_questions)
    else:
        logger.info("=== dry-run 완료 (DB 미반영) ===")


if __name__ == "__main__":
    main()
