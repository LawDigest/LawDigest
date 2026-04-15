"""선거 뉴스 ORM 모델.

네이버 뉴스 검색 API를 통해 수집한 선거 관련 뉴스 기사를 저장한다.
"""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from lawdigest_data.elections.database import Base


class ElectionNews(Base):
    """선거 뉴스 — 네이버 뉴스 검색 API 응답.

    election_id 기준으로 선거별 뉴스 기사를 저장한다.
    link 컬럼에 UNIQUE 제약으로 중복 수집을 방지한다.
    """

    __tablename__ = "election_news"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    election_id: Mapped[str] = mapped_column(String(50), nullable=False, comment="선거ID")
    title: Mapped[str] = mapped_column(String(500), nullable=False, comment="기사 제목")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="기사 요약")

    link: Mapped[str] = mapped_column(String(1000), nullable=False, comment="뉴스 링크")
    original_link: Mapped[str | None] = mapped_column(String(1000), nullable=True, comment="원본 링크")
    source: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="출처 (언론사)")
    thumbnail_url: Mapped[str | None] = mapped_column(String(1000), nullable=True, comment="썸네일 URL")

    pub_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="기사 발행일시")
    search_keyword: Mapped[str | None] = mapped_column(String(200), nullable=True, comment="수집 검색어")
    matched_party: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="매칭 정당명")
    matched_region: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="매칭 지역명")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("link", name="uk_news_link"),
        Index("idx_election_pubdate", "election_id", "pub_date"),
    )
