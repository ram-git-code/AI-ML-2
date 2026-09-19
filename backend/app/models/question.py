import uuid
from datetime import datetime, timezone
from typing import Optional, Any
from sqlalchemy import String, Text, Boolean, Integer, DateTime, Enum as SQLEnum, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.db.postgres import Base
from app.models.enums import QuestionType, Difficulty

class QuestionModel(Base):
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    question_type: Mapped[QuestionType] = mapped_column(
        SQLEnum(QuestionType, name="questiontype"), nullable=False, index=True
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    correct_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    embedding: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    embedding_model: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)

    subject: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    chapter: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    topic: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    difficulty: Mapped[Difficulty] = mapped_column(
        SQLEnum(Difficulty, name="difficulty"), nullable=False, default=Difficulty.MEDIUM, index=True
    )
    tags: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True, default=list)

    is_pyq: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    exam_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    exam_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    exam_month: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    exam_day: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    __table_args__ = (
        Index("ix_questions_subject_chapter_topic", "subject", "chapter", "topic"),
        Index("ix_questions_pyq_search", "is_pyq", "exam_name", "exam_year"),
    )
