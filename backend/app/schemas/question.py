import uuid
from datetime import datetime
from typing import Optional, List, Any, Union
from pydantic import BaseModel, Field, model_validator
from app.models.enums import QuestionType, Difficulty

class QuestionBase(BaseModel):
    question_type: QuestionType = Field(..., example=QuestionType.MCQ)
    question_text: str = Field(..., example="What is the capital of Rajasthan?")
    options: Optional[Any] = Field(
        default=None,
        example=["A. Jaipur", "B. Jodhpur", "C. Udaipur", "D. Kota"],
        description="Choice options for MCQ (List or JSON structure)"
    )
    correct_answer: Optional[str] = Field(default=None, example="A. Jaipur")
    explanation: Optional[str] = Field(
        default=None,
        example="Jaipur is the largest city and capital of Rajasthan state."
    )
    subject: str = Field(..., example="Rajasthan GK")
    chapter: str = Field(..., example="Geography")
    topic: str = Field(..., example="Capitals and Major Cities")
    difficulty: Difficulty = Field(default=Difficulty.MEDIUM, example=Difficulty.MEDIUM)
    tags: Optional[List[str]] = Field(default=[], example=["GK", "Rajasthan", "State Capital"])
    is_pyq: bool = Field(default=False, example=True)
    exam_name: Optional[str] = Field(default=None, example="REET")
    exam_year: Optional[int] = Field(default=None, example=2024)
    exam_month: Optional[int] = Field(default=None, example=5)
    exam_day: Optional[int] = Field(default=None, example=12)
    source: Optional[str] = Field(default=None, example="RPSC 2024 Official Paper")

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

    class Config:
        from_attributes = True

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
