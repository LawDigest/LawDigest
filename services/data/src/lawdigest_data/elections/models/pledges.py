"""선거공약 및 정당정책 ORM 모델.

ElecPrmsInfoInqireService (선거공약) 및
PartyPlcInfoInqireService (정당정책) API 응답에 대응하는 테이블을 정의한다.
"""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from lawdigest_data.elections.database import Base


class ElectionPledge(Base):
    """선거공약 — getCnddtElecPrmsInfoInqire 응답.

    후보자별 공약 (최대 10건).
    sgTypecode 1(대통령), 3(시도지사), 4(구시군장), 11(교육감)만 제공.
    """

    __tablename__ = "election_pledges"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # 후보자 연결
    candidate_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("election_candidates.id"), nullable=True, comment="후보자 FK",
    )

    # API 식별자
    sg_id: Mapped[str] = mapped_column(String(20), nullable=False, comment="선거ID")
    sg_typecode: Mapped[int] = mapped_column(SmallInteger, nullable=False, comment="선거종류코드")
    cnddt_id: Mapped[str] = mapped_column(String(20), nullable=False, comment="후보자ID(huboid)")

    # 공약 내용
    prms_ord: Mapped[int] = mapped_column(SmallInteger, nullable=False, comment="공약순서 (1~10)")
    prms_title: Mapped[str | None] = mapped_column(Text, nullable=True, comment="공약제목")
    prms_content: Mapped[str | None] = mapped_column(Text, nullable=True, comment="공약내용")

    # 여론조사 연계용
    normalized_region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    normalized_election_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # LLM 확장 대비
    summary: Mapped[str | None] = mapped_column(Text, nullable=True, comment="LLM 요약")
    embedding_id: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="벡터 임베딩 참조ID")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("sg_id", "cnddt_id", "prms_ord", name="uq_election_pledge"),
    )


class PartyPolicy(Base):
    """정당정책 — getPartyPlcInfoInqire 응답.

    정당별 정책 (최대 10건).
    """

    __tablename__ = "election_party_policies"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # API 식별자
    sg_id: Mapped[str] = mapped_column(String(20), nullable=False, comment="선거ID")
    party_name: Mapped[str] = mapped_column(String(100), nullable=False, comment="정당명")
    prms_cnt: Mapped[int | None] = mapped_column(SmallInteger, nullable=True, comment="정책수")

    # 정책 내용
    prms_ord: Mapped[int] = mapped_column(SmallInteger, nullable=False, comment="정책순서 (1~10)")
    prms_title: Mapped[str | None] = mapped_column(Text, nullable=True, comment="정책제목")
    prms_content: Mapped[str | None] = mapped_column(Text, nullable=True, comment="정책내용")

    # LLM 확장 대비
    summary: Mapped[str | None] = mapped_column(Text, nullable=True, comment="LLM 요약")
    embedding_id: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="벡터 임베딩 참조ID")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("sg_id", "party_name", "prms_ord", name="uq_party_policy"),
    )
