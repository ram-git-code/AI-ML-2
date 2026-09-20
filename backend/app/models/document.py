import uuid
from datetime import datetime
from typing import Optional, List, Any
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, Float
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.postgres import Base

class DocumentModel(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    page_count: Mapped[int] = mapped_column(Integer, default=0)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    topics: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)  # List of topic strings
    key_insights: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)  # List of key takeaways
    estimated_difficulty: Mapped[str] = mapped_column(String(50), default="MEDIUM")
    status: Mapped[str] = mapped_column(String(50), default="READY")  # PROCESSING, READY, ERROR
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    chunks: Mapped[List["DocumentChunkModel"]] = relationship(
        "DocumentChunkModel",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentChunkModel.chunk_index"
    )

class DocumentChunkModel(Base):
    __tablename__ = "document_chunks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, default=1)
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)  # Vector array
    embedding_model: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    document: Mapped["DocumentModel"] = relationship("DocumentModel", back_populates="chunks")
