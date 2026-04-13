#!/usr/bin/env python3
"""후보자/당선인 정보 수집 스크립트.

사용법::

    cd services/data
    python scripts/elections/collect_candidates.py
    python scripts/elections/collect_candidates.py --type confirmed
    python scripts/elections/collect_candidates.py --type winner
    python scripts/elections/collect_candidates.py --type all
"""

import argparse
import logging
import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent.parent / "src"
sys.path.insert(0, str(_project_root))

DEFAULT_SG_ID = "20220601"


def main() -> None:
    from lawdigest_data.elections.api_client import NecApiClient
    from lawdigest_data.elections.collectors.candidate_collector import (
        CandidateCollector,
        WinnerCollector,
    )
    from lawdigest_data.elections.database import get_session, init_db
    from lawdigest_data.elections.models.candidates import CandidateType

    parser = argparse.ArgumentParser(description="후보자/당선인 정보 수집")
    parser.add_argument("--sg-id", default=DEFAULT_SG_ID, help="대상 선거 ID")
    parser.add_argument(
        "--type",
        default="all",
        choices=["preliminary", "confirmed", "winner", "all"],
        help="수집 유형 (기본값: all)",
    )
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    logger = logging.getLogger("collect_candidates")

    init_db()
    client = NecApiClient()
    results: dict[str, int] = {}

    with get_session() as session:
        if args.type in ("preliminary", "all"):
            logger.info("예비후보자 수집 시작")
            collector = CandidateCollector(client)
            results["예비후보자"] = collector.collect_candidates(
                session, args.sg_id, CandidateType.PRELIMINARY,
            )

        if args.type in ("confirmed", "all"):
            logger.info("확정후보자 수집 시작")
            collector = CandidateCollector(client)
            results["확정후보자"] = collector.collect_candidates(
                session, args.sg_id, CandidateType.CONFIRMED,
            )

        if args.type in ("winner", "all"):
            logger.info("당선인 수집 시작")
            winner_collector = WinnerCollector(client)
            results["당선인"] = winner_collector.collect_winners(session, args.sg_id)

    logger.info("=" * 50)
    logger.info("수집 결과 요약")
    logger.info("=" * 50)
    total = 0
    for name, count in results.items():
        logger.info("  %-10s: %d건", name, count)
        total += count
    logger.info("  %-10s: %d건", "합계", total)


if __name__ == "__main__":
    main()
