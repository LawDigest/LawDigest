"""중앙선거관리위원회 코드정보 ORM 모델.

CommonCodeService API의 6개 오퍼레이션 응답에 대응하는 테이블을 정의한다.
"""

import enum
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    Integer,
    SmallInteger,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from lawdigest_data.elections.database import Base


class SgTypecode(enum.IntEnum):
    """선거종류코드."""
    대표선거명 = 0
    대통령 = 1
    국회의원 = 2
    시도지사 = 3
    구시군장 = 4
    시도의원 = 5
    구시군의회의원 = 6
    국회의원비례대표 = 7
    광역의원비례대표 = 8
    기초의원비례대표 = 9
    교육의원 = 10
    교육감 = 11


class ElectionCode(Base):
    """선거코드 — getCommonSgCodeList 응답."""

    __tablename__ = "election_codes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    sg_id: Mapped[str] = mapped_column(String(20), nullable=False, comment="선거ID (예: 20220601)")
    sg_typecode: Mapped[int] = mapped_column(SmallInteger, nullable=False, comment="선거종류코드")
    sg_name: Mapped[str] = mapped_column(String(100), nullable=False, comment="선거명")
    sg_vote_date: Mapped[str] = mapped_column(String(10), nullable=True, comment="선거일자")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("sg_id", "sg_typecode", name="uq_election_code"),
    )


class DistrictCode(Base):
    """선거구코드 — getCommonSggCodeList 응답."""

    __tablename__ = "election_districts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    sg_id: Mapped[str] = mapped_column(String(20), nullable=False)
    sg_typecode: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    sgg_name: Mapped[str] = mapped_column(String(100), nullable=False, comment="선거구명")
    sd_name: Mapped[str] = mapped_column(String(50), nullable=False, comment="시도명")
    wiw_name: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="구시군명")
    sgg_jungsu: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="선거구정수(당선인수)")
    s_order: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="정렬순서")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("sg_id", "sg_typecode", "sgg_name", "sd_name", name="uq_district_code"),
    )


class GusigunCode(Base):
    """구시군코드 — getCommonGusigunCodeList 응답."""

    __tablename__ = "election_gusiguns"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    sg_id: Mapped[str] = mapped_column(String(20), nullable=False)
    sd_name: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="시도명 (상위 시도 항목은 빈값)")
    wiw_name: Mapped[str] = mapped_column(String(50), nullable=False, comment="구시군명")
    w_order: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="정렬순서")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("sg_id", "sd_name", "wiw_name", name="uq_gusigun_code"),
    )


class PartyCode(Base):
    """정당코드 — getCommonPartyCodeList 응답."""

    __tablename__ = "election_parties"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    sg_id: Mapped[str] = mapped_column(String(20), nullable=False)
    jd_name: Mapped[str] = mapped_column(String(100), nullable=False, comment="정당명")
    p_order: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="정렬순서")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("sg_id", "jd_name", name="uq_party_code"),
    )


class JobCode(Base):
    """직업코드 — getCommonJobCodeList 응답."""

    __tablename__ = "election_jobs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    sg_id: Mapped[str] = mapped_column(String(20), nullable=False)
    job_id: Mapped[str] = mapped_column(String(10), nullable=False, comment="직업ID")
    job_name: Mapped[str] = mapped_column(String(100), nullable=False, comment="직업명")
    j_order: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="정렬순서")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("sg_id", "job_id", name="uq_job_code"),
    )


class EduCode(Base):
    """학력코드 — getCommonEduBckgrdCodeList 응답."""

    __tablename__ = "election_educations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    sg_id: Mapped[str] = mapped_column(String(20), nullable=False)
    edu_id: Mapped[str] = mapped_column(String(10), nullable=False, comment="학력ID")
    edu_name: Mapped[str] = mapped_column(String(100), nullable=False, comment="학력명")
    e_order: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="정렬순서")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("sg_id", "edu_id", name="uq_edu_code"),
    )
