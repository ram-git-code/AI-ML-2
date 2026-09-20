import uuid
from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict

class DocumentChunkResponse(BaseModel):
    id: uuid.UUID
    page_number: int
    chunk_index: int
    chunk_text: str

    model_config = ConfigDict(from_attributes=True)

class DocumentResponse(BaseModel):
    id: uuid.UUID
    filename: str
    title: str
    file_size_bytes: int
    page_count: int
    summary: Optional[str] = None
    topics: Optional[List[str]] = None
    key_insights: Optional[List[str]] = None
    estimated_difficulty: str = "MEDIUM"
    status: str = "READY"
    created_at: datetime
    chunk_count: int = 0

    model_config = ConfigDict(from_attributes=True)

class DocumentDetailResponse(DocumentResponse):
    chunks: List[DocumentChunkResponse] = []

class DocumentQuizGenerateRequest(BaseModel):
    question_count: int = Field(default=5, ge=1, le=20)
    difficulty: str = Field(default="medium")
    focus_topic: Optional[str] = None
