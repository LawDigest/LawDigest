"""SQLAlchemy 기반 DB 엔진 및 세션 설정.

기존 connectors/DatabaseManager(pymysql 직접 사용)와 독립적으로 운영되며,
elections 모듈 전용 ORM 인프라를 제공한다.
"""

import os
from contextlib import contextmanager
from typing import Generator
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

load_dotenv()


def _build_database_url() -> str:
    """환경변수에서 MySQL 접속 URL을 구성한다."""
    host = os.environ["DB_HOST"]
    port = os.environ.get("DB_PORT", "3306")
    user = os.environ["DB_USER"]
    password = quote_plus(os.environ["DB_PASSWORD"])
    db_name = os.environ.get("DB_NAME", "lawDB")
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}?charset=utf8mb4"


class Base(DeclarativeBase):
    """모든 elections ORM 모델의 베이스 클래스."""
    pass


engine = create_engine(
    _build_database_url(),
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """세션 컨텍스트 매니저. 정상 종료 시 커밋, 예외 시 롤백."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """등록된 모든 ORM 모델의 테이블을 생성한다."""
    Base.metadata.create_all(bind=engine)
