import uuid
from typing import List, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.repositories.question_repository import QuestionRepository
from app.models.question import QuestionModel
from app.schemas.question import QuestionCreate, QuestionUpdate, QuestionFilterParams

class QuestionService:

    @staticmethod
    def create_question(db: Session, schema: QuestionCreate) -> QuestionModel:
        return QuestionRepository.create(db, schema)

    @staticmethod
    def get_question(db: Session, question_id: uuid.UUID) -> QuestionModel:
        question = QuestionRepository.get_by_id(db, question_id)
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Question with ID '{question_id}' not found."
            )
        return question

    @staticmethod
    def list_questions(db: Session, filters: QuestionFilterParams) -> Tuple[List[QuestionModel], int]:
        return QuestionRepository.list(db, filters)

    @staticmethod
    def update_question(db: Session, question_id: uuid.UUID, schema: QuestionUpdate) -> QuestionModel:
        question = QuestionService.get_question(db, question_id)

        # Validate updating type vs requirements
        target_type = schema.question_type or question.question_type
        target_options = schema.options if schema.options is not None else question.options
        target_correct = schema.correct_answer if schema.correct_answer is not None else question.correct_answer

        if target_type == "MCQ":
            if not target_options:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="MCQ questions require non-empty 'options'."
                )
            if not target_correct:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="MCQ questions require 'correct_answer'."
                )
        elif target_type == "SINGLE_ANSWER":
            if not target_correct:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="SINGLE_ANSWER questions require 'correct_answer'."
                )

        return QuestionRepository.update(db, question, schema)

    @staticmethod
    def delete_question(db: Session, question_id: uuid.UUID) -> dict:
        question = QuestionService.get_question(db, question_id)
        QuestionRepository.delete(db, question)
        return {"detail": f"Question '{question_id}' successfully deleted."}
