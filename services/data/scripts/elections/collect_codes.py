#!/usr/bin/env python3
"""선거 코드정보 수집 스크립트.

중앙선거관리위원회 CommonCodeService API를 호출하여
선거코드, 선거구, 구시군, 정당, 직업, 학력 코드를 수집·저장한다.

사용법::

    cd services/data
    python scripts/elections/collect_codes.py
    python scripts/elections/collect_codes.py --sg-id 20220601
"""

import argparse
import logging
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
_project_root = Path(__file__).resolve().parent.parent.parent / "src"
sys.path.insert(0, str(_project_root))

from lawdigest_data.elections.api_client import NecApiClient
from lawdigest_data.elections.collectors.code_collector import CodeCollector
from lawdigest_data.elections.database import get_session, init_db

# 제9회 전국동시지방선거 sgId (추정값 — 실행 시 실제 확인)
DEFAULT_SG_ID = "20220601"


def main() -> None:
    parser = argparse.ArgumentParser(description="선거 코드정보 수집")
    parser.add_argument(
        "--sg-id",
        default=DEFAULT_SG_ID,
        help=f"대상 선거 ID (기본값: {DEFAULT_SG_ID})",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="로그 레벨 (기본값: INFO)",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    logger = logging.getLogger("collect_codes")
    logger.info("선거 코드정보 수집 시작 (sgId=%s)", args.sg_id)

    # DB 테이블 생성
    init_db()
    logger.info("DB 테이블 초기화 완료")

    # 수집 실행
    client = NecApiClient()
    collector = CodeCollector(client)

    with get_session() as session:
        results = collector.collect_all(session, sg_id=args.sg_id)

    # 결과 출력
    logger.info("=" * 50)
    logger.info("수집 결과 요약")
    logger.info("=" * 50)
    total = 0
    for name, count in results.items():
        logger.info("  %-12s: %d건", name, count)
        total += count
    logger.info("  %-12s: %d건", "합계", total)
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
