import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.postgres import get_db
from app.schemas.quiz import (
    QuizGenerateRequest,
    QuizResponse,
    QuizAnswerRequest,
    QuizAnswerResponse,
    QuizSummaryResponse,
)
from app.services.quiz_service import QuizService

router = APIRouter(prefix="/api/quizzes", tags=["Quiz System"])

@router.post(
    "/generate",
    response_model=QuizResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a new quiz",
    description="Generates an interactive quiz from PostgreSQL questions matching natural language queries or explicit filters."
)
def generate_quiz(req: QuizGenerateRequest, db: Session = Depends(get_db)):
    return QuizService.generate_quiz(db, req)

@router.get(
    "/{id}",
    response_model=QuizResponse,
    summary="Get quiz by ID",
    description="Retrieves the public quiz details (questions and options without revealing correct answers)."
)
def get_quiz(id: uuid.UUID, db: Session = Depends(get_db)):
    return QuizService.get_quiz(db, id)

@router.post(
    "/{id}/answers",
    response_model=QuizAnswerResponse,
    summary="Submit answer for a question in a quiz",
    description="Validates selected answer against authoritative PostgreSQL records, returns green/red evaluation and explanation."
)
def submit_answer(id: uuid.UUID, payload: QuizAnswerRequest, db: Session = Depends(get_db)):
    return QuizService.submit_answer(db, id, payload)

@router.get(
    "/{id}/summary",
    response_model=QuizSummaryResponse,
    summary="Get quiz summary & final score",
    description="Retrieves the completed answers map and current score for a quiz."
)
def get_quiz_summary(id: uuid.UUID, db: Session = Depends(get_db)):
    return QuizService.get_summary(db, id)
