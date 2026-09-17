import uuid
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.quiz import QuizModel

class QuizRepository:

    @staticmethod
    def create(db: Session, title: str, query_prompt: Optional[str], question_ids: list) -> QuizModel:
        quiz = QuizModel(
            title=title,
            query_prompt=query_prompt,
            question_ids=[str(qid) for qid in question_ids],
            total_questions=len(question_ids),
            score=0,
            completed=False,
            answers={}
        )
        db.add(quiz)
        db.commit()
        db.refresh(quiz)
        return quiz

    @staticmethod
    def get_by_id(db: Session, quiz_id: uuid.UUID) -> Optional[QuizModel]:
        stmt = select(QuizModel).where(QuizModel.id == quiz_id)
        return db.scalar(stmt)

    @staticmethod
    def record_answer(db: Session, quiz: QuizModel, question_id: str, selected_answer: str, is_correct: bool) -> QuizModel:
        # Create a copy of the answers dict to trigger SQLAlchemy change tracking
        answers = dict(quiz.answers) if quiz.answers else {}
        
        # If answering for the first time or updating
        was_previously_correct = answers.get(question_id, {}).get("is_correct", False)
        
        answers[question_id] = {
            "selected_answer": selected_answer,
            "is_correct": is_correct
        }
        quiz.answers = answers

        # Recalculate score
        quiz.score = sum(1 for a in answers.values() if a.get("is_correct"))

        # Check if all questions are answered
        if len(answers) >= quiz.total_questions:
            quiz.completed = True

        db.commit()
        db.refresh(quiz)
        return quiz
