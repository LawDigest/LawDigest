"""여론조사 관련 DB 테이블 관리 클래스.

DatabaseManager를 상속하여 여론조사 전용 테이블 (PollCatalog, PollSurvey,
PollQuestion, PollOption)의 생성 및 upsert 기능을 제공한다.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .DatabaseManager import DatabaseManager

logger = logging.getLogger(__name__)


class PollsDatabaseManager(DatabaseManager):
    """여론조사 파이프라인 전용 DB 매니저."""

    # ── DDL ───────────────────────────────────────────────────────────────────

    _DDL_CATALOG = """
    CREATE TABLE IF NOT EXISTS PollCatalog (
        catalog_id       BIGINT AUTO_INCREMENT PRIMARY KEY,
        election_type    VARCHAR(100),
        region           VARCHAR(200),
        election_name    VARCHAR(200),
        pollster         VARCHAR(100),
        first_seen_date  DATE,
        last_seen_date   DATE,
        count            INT DEFAULT 1,
        created_date     DATETIME DEFAULT NOW(),
        modified_date    DATETIME DEFAULT NOW() ON UPDATE NOW(),
        UNIQUE KEY uq_catalog (election_type, region, election_name, pollster)
    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    """

    _DDL_SURVEY = """
    CREATE TABLE IF NOT EXISTS PollSurvey (
        registration_number  VARCHAR(50) PRIMARY KEY,
        election_type        VARCHAR(100),
        region               VARCHAR(200),
        election_name        VARCHAR(200),
        pollster             VARCHAR(100),
        sponsor              VARCHAR(200),
        survey_start_date    DATE,
        survey_end_date      DATE,
        sample_size          INT,
        margin_of_error      VARCHAR(50),
        source_url           VARCHAR(500),
        pdf_path             VARCHAR(500),
        created_date         DATETIME DEFAULT NOW(),
        modified_date        DATETIME DEFAULT NOW() ON UPDATE NOW()
    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    """

    _DDL_QUESTION = """
    CREATE TABLE IF NOT EXISTS PollQuestion (
        question_id          BIGINT AUTO_INCREMENT PRIMARY KEY,
        registration_number  VARCHAR(50),
        question_number      INT,
        question_title       TEXT,
        n_completed          INT,
        n_weighted           INT,
        created_date         DATETIME DEFAULT NOW(),
        modified_date        DATETIME DEFAULT NOW() ON UPDATE NOW(),
        UNIQUE KEY uq_question (registration_number, question_number),
        INDEX idx_reg_num (registration_number)
    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    """

    _DDL_OPTION = """
    CREATE TABLE IF NOT EXISTS PollOption (
        option_id     BIGINT AUTO_INCREMENT PRIMARY KEY,
        question_id   BIGINT,
        option_name   VARCHAR(200),
        percentage    DECIMAL(5,2),
        created_date  DATETIME DEFAULT NOW(),
        modified_date DATETIME DEFAULT NOW() ON UPDATE NOW(),
        INDEX idx_question_id (question_id)
    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    """

    # ── 테이블 생성 ───────────────────────────────────────────────────────────

    def ensure_tables(self) -> None:
        """여론조사 관련 테이블이 없으면 생성한다."""
        with self.transaction() as cursor:
            for ddl in (
                self._DDL_CATALOG,
                self._DDL_SURVEY,
                self._DDL_QUESTION,
                self._DDL_OPTION,
            ):
                cursor.execute(ddl)
        logger.info("[PollsDB] 테이블 확인/생성 완료")

    # ── PollCatalog ───────────────────────────────────────────────────────────

    def upsert_catalog(self, rows: List[Dict[str, Any]]) -> int:
        """고유 (election_type, region, election_name, pollster) 조합을 upsert.

        Args:
            rows: [{"election_type", "region", "election_name", "pollster",
                    "last_seen_date"}, ...]

        Returns:
            처리된 행 수
        """
        if not rows:
            return 0

        sql = """
        INSERT INTO PollCatalog
            (election_type, region, election_name, pollster, first_seen_date, last_seen_date, count)
        VALUES
            (%(election_type)s, %(region)s, %(election_name)s, %(pollster)s,
             %(last_seen_date)s, %(last_seen_date)s, 1)
        ON DUPLICATE KEY UPDATE
            last_seen_date = VALUES(last_seen_date),
            count          = count + 1,
            modified_date  = NOW()
        """
        with self.transaction() as cursor:
            cursor.executemany(sql, rows)
        logger.debug("[PollsDB] upsert_catalog: %d행", len(rows))
        return len(rows)

    # ── PollSurvey ────────────────────────────────────────────────────────────

    def upsert_surveys(self, rows: List[Dict[str, Any]]) -> int:
        """개별 여론조사 메타 정보를 upsert.

        Args:
            rows: [{"registration_number", "election_type", "region",
                    "election_name", "pollster", "sponsor",
                    "survey_start_date", "survey_end_date",
                    "sample_size", "margin_of_error",
                    "source_url", "pdf_path"}, ...]

        Returns:
            처리된 행 수
        """
        if not rows:
            return 0

        sql = """
        INSERT INTO PollSurvey
            (registration_number, election_type, region, election_name,
             pollster, sponsor, survey_start_date, survey_end_date,
             sample_size, margin_of_error, source_url, pdf_path)
        VALUES
            (%(registration_number)s, %(election_type)s, %(region)s, %(election_name)s,
             %(pollster)s, %(sponsor)s, %(survey_start_date)s, %(survey_end_date)s,
             %(sample_size)s, %(margin_of_error)s, %(source_url)s, %(pdf_path)s)
        ON DUPLICATE KEY UPDATE
            election_type      = VALUES(election_type),
            region             = VALUES(region),
            election_name      = VALUES(election_name),
            pollster           = VALUES(pollster),
            sponsor            = VALUES(sponsor),
            survey_start_date  = VALUES(survey_start_date),
            survey_end_date    = VALUES(survey_end_date),
            sample_size        = VALUES(sample_size),
            margin_of_error    = VALUES(margin_of_error),
            source_url         = VALUES(source_url),
            pdf_path           = VALUES(pdf_path),
            modified_date      = NOW()
        """
        with self.transaction() as cursor:
            cursor.executemany(sql, rows)
        logger.debug("[PollsDB] upsert_surveys: %d행", len(rows))
        return len(rows)

    # ── PollQuestion ──────────────────────────────────────────────────────────

    def upsert_questions(self, rows: List[Dict[str, Any]]) -> Optional[int]:
        """설문 질문을 upsert하고 마지막으로 처리된 question_id를 반환.

        Args:
            rows: [{"registration_number", "question_number",
                    "question_title", "n_completed", "n_weighted"}, ...]

        Returns:
            마지막 question_id (단건 처리 시 활용). 행이 없으면 None.
        """
        if not rows:
            return None

        sql = """
        INSERT INTO PollQuestion
            (registration_number, question_number, question_title, n_completed, n_weighted)
        VALUES
            (%(registration_number)s, %(question_number)s, %(question_title)s,
             %(n_completed)s, %(n_weighted)s)
        ON DUPLICATE KEY UPDATE
            question_title = VALUES(question_title),
            n_completed    = VALUES(n_completed),
            n_weighted     = VALUES(n_weighted),
            modified_date  = NOW()
        """
        last_id: Optional[int] = None
        with self.transaction() as cursor:
            for row in rows:
                cursor.execute(sql, row)
                # 신규 삽입 시 lastrowid, 중복 키 업데이트 시 기존 id 조회
                if cursor.lastrowid:
                    last_id = cursor.lastrowid
                else:
                    cursor.execute(
                        "SELECT question_id FROM PollQuestion "
                        "WHERE registration_number = %(registration_number)s "
                        "  AND question_number = %(question_number)s",
                        row,
                    )
                    result = cursor.fetchone()
                    if result:
                        last_id = result["question_id"]
        logger.debug("[PollsDB] upsert_questions: %d행, last_id=%s", len(rows), last_id)
        return last_id

    # ── PollOption ────────────────────────────────────────────────────────────

    def replace_options(self, question_id: int, options: List[Dict[str, Any]]) -> int:
        """특정 question_id의 선택지를 전부 교체한다 (DELETE + INSERT).

        Args:
            question_id: PollQuestion.question_id
            options: [{"option_name": str, "percentage": float}, ...]

        Returns:
            삽입된 행 수
        """
        if not options:
            return 0

        delete_sql = "DELETE FROM PollOption WHERE question_id = %s"
        insert_sql = """
        INSERT INTO PollOption (question_id, option_name, percentage)
        VALUES (%(question_id)s, %(option_name)s, %(percentage)s)
        """
        rows = [{"question_id": question_id, **opt} for opt in options]

        with self.transaction() as cursor:
            cursor.execute(delete_sql, (question_id,))
            cursor.executemany(insert_sql, rows)

        logger.debug("[PollsDB] replace_options: question_id=%d, %d개", question_id, len(rows))
        return len(rows)
