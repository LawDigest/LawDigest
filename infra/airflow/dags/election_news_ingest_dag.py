"""선거 뉴스 수집 DAG.

네이버 뉴스 검색 API를 통해 선거 관련 뉴스를 시간별로 수집한다.

스케줄: 매시간 정각 (0 * * * *)
의존성: NAVER_CLIENT_ID, NAVER_CLIENT_SECRET Airflow Variable 또는 환경변수 설정 필요
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta

from airflow.decorators import dag, task

logger = logging.getLogger(__name__)

# 수집 대상 선거 ID
TARGET_ELECTION_ID = "20260603"

default_args = {
    "owner": "lawdigest",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(minutes=30),
}


@dag(
    dag_id="election_news_ingest",
    description="선거 관련 네이버 뉴스 시간별 수집",
    schedule_interval="0 * * * *",
    start_date=datetime(2026, 4, 12),
    catchup=False,
    default_args=default_args,
    tags=["election", "news", "naver"],
)
def election_news_ingest_dag() -> None:
    @task()
    def collect_election_news(election_id: str) -> int:
        """네이버 뉴스 API로 선거 관련 뉴스를 수집하여 DB에 저장한다."""
        # Airflow Variable에서 API 키 로드 (설정된 경우)
        try:
            from airflow.models import Variable  # noqa: PLC0415

            os.environ.setdefault("NAVER_CLIENT_ID", Variable.get("NAVER_CLIENT_ID", default_var=""))
            os.environ.setdefault(
                "NAVER_CLIENT_SECRET", Variable.get("NAVER_CLIENT_SECRET", default_var="")
            )
        except Exception:
            pass  # Airflow Variable 없을 경우 환경변수 직접 사용

        from sqlalchemy import create_engine  # noqa: PLC0415
        from sqlalchemy.orm import sessionmaker  # noqa: PLC0415

        from lawdigest_data.elections.collectors.news_collector import NaverNewsCollector  # noqa: PLC0415

        db_url = os.environ["ELECTION_DB_URL"]
        engine = create_engine(db_url, pool_pre_ping=True)
        Session = sessionmaker(bind=engine)

        collector = NaverNewsCollector()
        with Session() as session:
            count = collector.collect_news(session, election_id)
            session.commit()

        logger.info("뉴스 수집 완료: %d건 (electionId=%s)", count, election_id)
        return count

    collect_election_news(election_id=TARGET_ELECTION_ID)


election_news_ingest_dag()
