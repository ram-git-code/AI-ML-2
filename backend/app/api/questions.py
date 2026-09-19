import json
import uuid
from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session
from app.db.postgres import get_db
from app.schemas.question import (
    QuestionCreate,
    QuestionUpdate,
    QuestionResponse,
    QuestionFilterParams,
)
from app.models.enums import QuestionType, Difficulty
from app.services.question_service import QuestionService
from app.repositories.question_repository import QuestionRepository
from app.services.question_import_jobs import create_import_job, get_import_job
from app.schemas.question_import import QuestionImportResponse

router = APIRouter(prefix="/api/questions", tags=["Question Management"])

@router.get("/subjects", response_model=List[str], summary="List subjects available in PostgreSQL")
def list_subjects(db: Session = Depends(get_db)):
    return QuestionRepository.list_subjects(db)

@router.post("/import", response_model=QuestionImportResponse, status_code=status.HTTP_201_CREATED)
async def import_question_file(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".json"):
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="Upload a .json file.")
    try:
        payload = json.loads(await file.read())
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail=f"Invalid JSON file: {error}") from error
    if not isinstance(payload.get("Questions"), list) or not payload["Questions"]:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="JSON must contain a non-empty 'Questions' array.")
    job = create_import_job(payload)
    return QuestionImportResponse(job_id=job.job_id, status=job.status, total=job.total, imported=0, embedded=0, message="Import started in the background.")

@router.get("/import/{job_id}", response_model=QuestionImportResponse)
def import_status(job_id: str):
    from fastapi import HTTPException
    job = get_import_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Import job not found or expired.")
    return QuestionImportResponse(job_id=job.job_id, status=job.status, total=job.total, imported=job.imported, embedded=job.embedded, message=job.error or "")

@router.post(
    "",
    response_model=QuestionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new question or note",
    description="Creates a new MCQ, SINGLE_ANSWER, or NOTE question item in PostgreSQL."
)
def create_question(payload: QuestionCreate, db: Session = Depends(get_db)):
    return QuestionService.create_question(db, payload)

@router.get(
    "",
    response_model=List[QuestionResponse],
    summary="List questions with metadata filtering & pagination",
    description="Retrieves a list of questions filtered by subject, chapter, topic, difficulty, pyq, or exam info."
)
def list_questions(
    subject: Optional[str] = Query(None, description="Filter by subject"),
    chapter: Optional[str] = Query(None, description="Filter by chapter"),
    topic: Optional[str] = Query(None, description="Filter by topic"),
    difficulty: Optional[Difficulty] = Query(None, description="Filter by difficulty"),
    question_type: Optional[QuestionType] = Query(None, description="Filter by question type"),
    is_pyq: Optional[bool] = Query(None, description="Filter by Previous Year Question status"),
    exam_name: Optional[str] = Query(None, description="Filter by exam name (e.g. REET, RPSC)"),
    exam_year: Optional[int] = Query(None, description="Filter by exam year"),
    skip: int = Query(0, ge=0, description="Pagination skip offset"),
    limit: int = Query(50, ge=1, le=200, description="Pagination limit per page"),
    db: Session = Depends(get_db)
):
    filters = QuestionFilterParams(
        subject=subject,
        chapter=chapter,
        topic=topic,
        difficulty=difficulty,
        question_type=question_type,
        is_pyq=is_pyq,
        exam_name=exam_name,
        exam_year=exam_year,
        skip=skip,
        limit=limit,
    )
    items, _ = QuestionService.list_questions(db, filters)
    return items

@router.get(
    "/{id}",
    response_model=QuestionResponse,
    summary="Get question by ID",
    description="Fetches full details of a specific question by UUID."
)
def get_question(id: uuid.UUID, db: Session = Depends(get_db)):
    return QuestionService.get_question(db, id)

@router.put(
    "/{id}",
    response_model=QuestionResponse,
    summary="Update an existing question",
    description="Updates specific fields of an existing question by UUID."
)
def update_question(id: uuid.UUID, payload: QuestionUpdate, db: Session = Depends(get_db)):
    return QuestionService.update_question(db, id, payload)

@router.delete(
    "/{id}",
    summary="Delete a question",
    description="Permanently deletes a question from PostgreSQL by UUID."
)
def delete_question(id: uuid.UUID, db: Session = Depends(get_db)):
    return QuestionService.delete_question(db, id)
