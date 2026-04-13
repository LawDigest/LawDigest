#!/usr/bin/env python3
"""선거공약/정당정책 수집 스크립트.

사용법::

    cd services/data
    python scripts/elections/collect_pledges.py
    python scripts/elections/collect_pledges.py --type pledge
    python scripts/elections/collect_pledges.py --type policy
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
    from lawdigest_data.elections.collectors.pledge_collector import (
        PartyPolicyCollector,
        PledgeCollector,
    )
    from lawdigest_data.elections.database import get_session, init_db

    parser = argparse.ArgumentParser(description="선거공약/정당정책 수집")
    parser.add_argument("--sg-id", default=DEFAULT_SG_ID, help="대상 선거 ID")
    parser.add_argument(
        "--type", default="all", choices=["pledge", "policy", "all"],
        help="수집 유형 (기본값: all)",
    )
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    logger = logging.getLogger("collect_pledges")

    init_db()
    client = NecApiClient()
    results: dict[str, int] = {}

    with get_session() as session:
        if args.type in ("pledge", "all"):
            logger.info("선거공약 수집 시작")
            results["선거공약"] = PledgeCollector(client).collect_pledges(session, args.sg_id)

        if args.type in ("policy", "all"):
            logger.info("정당정책 수집 시작")
            results["정당정책"] = PartyPolicyCollector(client).collect_policies(session, args.sg_id)

    logger.info("=" * 50)
    logger.info("수집 결과 요약")
    logger.info("=" * 50)
    for name, count in results.items():
        logger.info("  %-10s: %d건", name, count)


if __name__ == "__main__":
    main()
