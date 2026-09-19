import uuid
from typing import Optional, List
from pydantic import BaseModel, Field

class AIExplainRequest(BaseModel):
    question_id: uuid.UUID
    user_answer: str

class AIExplainResponse(BaseModel):
    question_id: uuid.UUID
    user_answer: str
    correct_answer: str
    why_wrong: str
    why_correct: str
    key_takeaway: str
    full_explanation: str

class AITutorMessage(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str

class AITutorRequest(BaseModel):
    question_id: Optional[uuid.UUID] = None
    subject: Optional[str] = None
    user_message: str
    chat_history: Optional[List[AITutorMessage]] = Field(default_factory=list)

class AITutorResponse(BaseModel):
    reply: str
    question_id: Optional[uuid.UUID] = None
