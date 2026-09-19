import asyncio
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.postgres import get_db
from app.repositories.question_repository import QuestionRepository
from app.schemas.ai import (
    AIExplainRequest,
    AIExplainResponse,
    AITutorRequest,
    AITutorResponse,
)
from app.services.llm_service import LLMService
from app.services.question_import_service import _embed

router = APIRouter(prefix="/api/ai", tags=["AI Tutor & Explanation"])

@router.post(
    "/explain",
    response_model=AIExplainResponse,
    summary="Generate deep AI explanation for student's answer",
    description="Uses Google Gemini to analyze the student's selected answer, explain why it was wrong or right, and summarize key takeaways."
)
async def explain_answer(req: AIExplainRequest, db: Session = Depends(get_db)):
    question = QuestionRepository.get_by_id(db, req.question_id)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question with ID '{req.question_id}' not found."
        )

    explanation_data = await LLMService.generate_explanation(question, req.user_answer)
    return AIExplainResponse(
        question_id=question.id,
        user_answer=req.user_answer,
        correct_answer=question.correct_answer or "",
        why_wrong=explanation_data["why_wrong"],
        why_correct=explanation_data["why_correct"],
        key_takeaway=explanation_data["key_takeaway"],
        full_explanation=explanation_data["full_explanation"]
    )

@router.post(
    "/tutor",
    response_model=AITutorResponse,
    summary="AI Tutor doubt resolver chatbot",
    description="Conversational academic tutor helping students resolve doubts about the current question, concepts, and syllabus."
)
async def tutor_chat(req: AITutorRequest, db: Session = Depends(get_db)):
    question = None
    if req.question_id:
        question = QuestionRepository.get_by_id(db, req.question_id)
    if question is None:
        try:
            query_embedding = await asyncio.to_thread(_embed, req.user_message)
            question = next(iter(QuestionRepository.search_by_embedding(
                db, query_embedding, subject=req.subject, limit=1
            )), None)
        except Exception:
            question = None

    reply = await LLMService.tutor_chat(
        question=question,
        user_message=req.user_message,
        chat_history=req.chat_history
    )

    return AITutorResponse(
        reply=reply,
        question_id=question.id if question else req.question_id
    )
