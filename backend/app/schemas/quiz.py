import uuid
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import QuestionType, Difficulty

class QuizGenerateRequest(BaseModel):
    query: Optional[str] = Field(default=None, description="Natural language prompt like '5 Rajasthan GK PYQs'")
    subject: Optional[str] = Field(default=None, description="Subject filter e.g. Rajasthan GK, Physics")
    difficulty: Optional[Difficulty] = Field(default=None, description="Difficulty filter")
    is_pyq: Optional[bool] = Field(default=None, description="Only Previous Year Questions")
    number_of_questions: int = Field(default=5, ge=1, le=50, description="Target question count")

class QuizPublicQuestion(BaseModel):
    id: uuid.UUID
    question_type: QuestionType
    question_text: str
    options: Optional[Any] = None
    subject: str
    chapter: str
    topic: str
    difficulty: Difficulty
    is_pyq: bool = False
    exam_name: Optional[str] = None
    exam_year: Optional[int] = None
    exam_month: Optional[int] = None
    exam_day: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

class QuizResponse(BaseModel):
    id: uuid.UUID
    title: str
    total_questions: int
    questions: List[QuizPublicQuestion]

    model_config = ConfigDict(from_attributes=True)

class QuizAnswerRequest(BaseModel):
    question_id: uuid.UUID
    selected_answer: Any

class QuizAnswerResponse(BaseModel):
    question_id: uuid.UUID
    selected_answer: Any
    is_correct: bool
    correct_answer: str
    explanation: Optional[str] = None
    score: int
    total_answered: int
    total_questions: int
    quiz_completed: bool

class QuizSummaryResponse(BaseModel):
    id: uuid.UUID
    title: str
    total_questions: int
    score: int
    completed: bool
    answers: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)
