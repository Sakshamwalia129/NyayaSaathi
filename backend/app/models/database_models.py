from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.database import Base


class RightsQuery(Base):
    __tablename__ = "rights_queries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    query = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)

    # Complete structured Rights Explorer response
    response = Column(JSONB, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user = relationship(
        "User",
        back_populates="rights_queries",
    )


class JudgmentAnalysis(Base):
    __tablename__ = "judgment_analyses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    filename = Column(String(255), nullable=False)

    # Complete structured Judgment Simplifier response
    response = Column(JSONB, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user = relationship(
        "User",
        back_populates="judgment_analyses",
    )


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    password_hash = Column(String(255), nullable=True)
    auth_provider = Column(
        String(50),
        nullable=False,
        default="local",
    )
    google_sub = Column(
        String(255),
        unique=True,
        nullable=True,
        index=True,
    )
    profile_picture_url = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    rights_queries = relationship(
        "RightsQuery",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    judgment_analyses = relationship(
        "JudgmentAnalysis",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class LatestJudgment(Base):
    """
    Stores judgments discovered from the official
    Supreme Court of India website.

    AI-generated content is stored separately from
    official Supreme Court metadata.
    """

    __tablename__ = "latest_judgments"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    # Stable identifier generated from official judgment metadata.
    official_id = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    # Official Supreme Court metadata
    case_title = Column(
        Text,
        nullable=False,
    )

    case_number = Column(
        String(255),
        nullable=True,
        index=True,
    )

    diary_number = Column(
        String(100),
        nullable=True,
        index=True,
    )

    judgment_date = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    uploaded_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    official_pdf_url = Column(
        Text,
        nullable=False,
    )

    source_url = Column(
        Text,
        nullable=True,
    )

    # Used as an additional duplicate/integrity check.
    pdf_sha256 = Column(
        String(64),
        nullable=True,
        index=True,
    )

    # AI-generated content.
    # This must never be presented as official Supreme Court text.
    ai_headline = Column(
        Text,
        nullable=True,
    )

    ai_summary = Column(
        Text,
        nullable=True,
    )

    # pending / processed / failed
    processing_status = Column(
        String(50),
        nullable=False,
        default="pending",
        index=True,
    )

    processing_error = Column(
        Text,
        nullable=True,
    )

    # Extra official metadata if SCI exposes useful fields later.
    metadata_json = Column(
        JSONB,
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )