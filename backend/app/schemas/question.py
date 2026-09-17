import uuid
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field, ConfigDict, model_validator
from app.models.enums import QuestionType, Difficulty

class QuestionBase(BaseModel):
    question_type: QuestionType = Field(..., examples=[QuestionType.MCQ])
    question_text: str = Field(..., examples=["What is the capital of Rajasthan?"])
    options: Optional[Any] = Field(
        default=None,
        examples=[["A. Jaipur", "B. Jodhpur", "C. Udaipur", "D. Kota"]],
        description="Choice options for MCQ (List or JSON structure)"
    )
    correct_answer: Optional[str] = Field(default=None, examples=["A. Jaipur"])
    explanation: Optional[str] = Field(
        default=None,
        examples=["Jaipur is the largest city and capital of Rajasthan state."]
    )
    subject: str = Field(..., examples=["Rajasthan GK"])
    chapter: str = Field(..., examples=["Geography"])
    topic: str = Field(..., examples=["Capitals and Major Cities"])
    difficulty: Difficulty = Field(default=Difficulty.MEDIUM, examples=[Difficulty.MEDIUM])
    tags: Optional[List[str]] = Field(default=[], examples=[["GK", "Rajasthan", "State Capital"]])
    is_pyq: bool = Field(default=False, examples=[True])
    exam_name: Optional[str] = Field(default=None, examples=["REET"])
    exam_year: Optional[int] = Field(default=None, examples=[2024])
    exam_month: Optional[int] = Field(default=None, examples=[5])
    exam_day: Optional[int] = Field(default=None, examples=[12])
    source: Optional[str] = Field(default=None, examples=["RPSC 2024 Official Paper"])

class QuestionCreate(QuestionBase):

    @model_validator(mode="after")
    def validate_type_requirements(self):
        if self.question_type == QuestionType.MCQ:
            if not self.options:
                raise ValueError("MCQ questions require 'options' to be provided.")
            if not self.correct_answer:
                raise ValueError("MCQ questions require 'correct_answer' to be provided.")
        elif self.question_type == QuestionType.SINGLE_ANSWER:
            if not self.correct_answer:
                raise ValueError("SINGLE_ANSWER questions require 'correct_answer' to be provided.")
        return self

class QuestionUpdate(BaseModel):
    question_type: Optional[QuestionType] = None
    question_text: Optional[str] = None
    options: Optional[Any] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    subject: Optional[str] = None
    chapter: Optional[str] = None
    topic: Optional[str] = None
    difficulty: Optional[Difficulty] = None
    tags: Optional[List[str]] = None
    is_pyq: Optional[bool] = None
    exam_name: Optional[str] = None
    exam_year: Optional[int] = None
    exam_month: Optional[int] = None
    exam_day: Optional[int] = None
    source: Optional[str] = None

class QuestionResponse(QuestionBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class QuestionFilterParams(BaseModel):
    subject: Optional[str] = None
    chapter: Optional[str] = None
    topic: Optional[str] = None
    difficulty: Optional[Difficulty] = None
    question_type: Optional[QuestionType] = None
    is_pyq: Optional[bool] = None
    exam_name: Optional[str] = None
    exam_year: Optional[int] = None
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=50, ge=1, le=200)
