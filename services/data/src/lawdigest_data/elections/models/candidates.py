"""후보자 및 당선인 ORM 모델.

PofelcddInfoInqireService (후보자정보) 및
WinnerInfoInqireService2 (당선인정보) API 응답에 대응하는 테이블을 정의한다.
"""

import enum
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lawdigest_data.elections.database import Base


class CandidateType(str, enum.Enum):
    """후보자 구분."""
    PRELIMINARY = "preliminary"  # 예비후보자
    CONFIRMED = "confirmed"      # 확정 후보자


class Candidate(Base):
    """후보자 (예비후보자 + 확정후보자 통합)."""

    __tablename__ = "election_candidates"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # API 식별자
    huboid: Mapped[str] = mapped_column(String(20), nullable=False, comment="후보자ID")
    sg_id: Mapped[str] = mapped_column(String(20), nullable=False, comment="선거ID")
    sg_typecode: Mapped[int] = mapped_column(SmallInteger, nullable=False, comment="선거종류코드")
    candidate_type: Mapped[str] = mapped_column(
        Enum(CandidateType), nullable=False, comment="예비/확정 구분",
    )

    # 선거구 정보
    sgg_name: Mapped[str] = mapped_column(String(100), nullable=False, comment="선거구명")
    sd_name: Mapped[str] = mapped_column(String(50), nullable=False, comment="시도명")
    wiw_name: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="구시군명")

    # 후보자 기본정보
    giho: Mapped[str | None] = mapped_column(String(10), nullable=True, comment="기호")
    giho_sangse: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="기호상세")
    jd_name: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="정당명")
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="한글성명")
    hanja_name: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="한자성명")
    gender: Mapped[str | None] = mapped_column(String(10), nullable=True, comment="성별")
    birthday: Mapped[str | None] = mapped_column(String(10), nullable=True, comment="생년월일")
    age: Mapped[int | None] = mapped_column(SmallInteger, nullable=True, comment="연령(선거일 기준)")

    # 주소/직업/학력/경력
    addr: Mapped[str | None] = mapped_column(String(200), nullable=True, comment="주소(상세 제외)")
    job_id: Mapped[str | None] = mapped_column(String(10), nullable=True, comment="직업ID")
    job: Mapped[str | None] = mapped_column(String(200), nullable=True, comment="직업")
    edu_id: Mapped[str | None] = mapped_column(String(10), nullable=True, comment="학력ID")
    edu: Mapped[str | None] = mapped_column(String(200), nullable=True, comment="학력")
    career1: Mapped[str | None] = mapped_column(Text, nullable=True, comment="경력1")
    career2: Mapped[str | None] = mapped_column(Text, nullable=True, comment="경력2")

    # 예비후보자 전용 필드
    regdate: Mapped[str | None] = mapped_column(String(10), nullable=True, comment="등록일")
    status: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="등록상태(등록/사퇴/사망/등록무효)")

    # 여론조사 연계용 정규화 필드
    normalized_region: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="polls 연계용 정규화 지역명")
    normalized_election_name: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="polls 연계용 정규화 선거명")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계
    winner: Mapped["Winner | None"] = relationship("Winner", back_populates="candidate", uselist=False)

    __table_args__ = (
        UniqueConstraint("huboid", "sg_id", "candidate_type", name="uq_candidate"),
    )


class Winner(Base):
    """당선인."""

    __tablename__ = "election_winners"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # Candidate FK (nullable — 당선인이 후보자 테이블에 없을 수도 있음)
    candidate_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("election_candidates.id"), nullable=True, comment="후보자 FK",
    )

    # API 식별자
    huboid: Mapped[str] = mapped_column(String(20), nullable=False, comment="후보자ID")
    sg_id: Mapped[str] = mapped_column(String(20), nullable=False, comment="선거ID")
    sg_typecode: Mapped[int] = mapped_column(SmallInteger, nullable=False, comment="선거종류코드")

    # 선거구 정보
    sgg_name: Mapped[str] = mapped_column(String(100), nullable=False, comment="선거구명")
    sd_name: Mapped[str] = mapped_column(String(50), nullable=False, comment="시도명")
    wiw_name: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="구시군명")

    # 당선인 기본정보
    giho: Mapped[str | None] = mapped_column(String(10), nullable=True, comment="기호")
    giho_sangse: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="기호상세")
    jd_name: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="정당명")
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="한글성명")
    hanja_name: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="한자성명")
    gender: Mapped[str | None] = mapped_column(String(10), nullable=True, comment="성별")
    birthday: Mapped[str | None] = mapped_column(String(10), nullable=True, comment="생년월일")
    age: Mapped[int | None] = mapped_column(SmallInteger, nullable=True, comment="연령")

    # 주소/직업/학력/경력
    addr: Mapped[str | None] = mapped_column(String(200), nullable=True, comment="주소")
    job_id: Mapped[str | None] = mapped_column(String(10), nullable=True)
    job: Mapped[str | None] = mapped_column(String(200), nullable=True)
    edu_id: Mapped[str | None] = mapped_column(String(10), nullable=True)
    edu: Mapped[str | None] = mapped_column(String(200), nullable=True)
    career1: Mapped[str | None] = mapped_column(Text, nullable=True)
    career2: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 득표 정보
    dugsu: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="득표수")
    dugyul: Mapped[str | None] = mapped_column(String(10), nullable=True, comment="득표율(%)")

    # 여론조사 연계용
    normalized_region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    normalized_election_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계
    candidate: Mapped[Candidate | None] = relationship("Candidate", back_populates="winner")

    __table_args__ = (
        UniqueConstraint("huboid", "sg_id", name="uq_winner"),
    )
