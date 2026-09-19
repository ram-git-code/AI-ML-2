import re
import uuid
import random
from dataclasses import dataclass, field
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from fastapi import HTTPException, status

from app.models.question import QuestionModel
from app.models.enums import QuestionType, Difficulty
from app.models.quiz import QuizModel
from app.schemas.quiz import (
    QuizGenerateRequest,
    QuizPublicQuestion,
    QuizResponse,
    QuizAnswerRequest,
    QuizAnswerResponse,
    QuizSummaryResponse,
)
from app.schemas.question import QuestionFilterParams
from app.repositories.quiz_repository import QuizRepository
from app.repositories.question_repository import QuestionRepository


@dataclass
class JsonQuizSession:
    id: uuid.UUID
    title: str
    query_prompt: Optional[str]
    question_ids: list[str]
    total_questions: int
    score: int = 0
    completed: bool = False
    answers: dict = field(default_factory=dict)


JSON_QUIZ_SESSIONS: dict[uuid.UUID, JsonQuizSession] = {}

class QuizService:

    @staticmethod
    def _parse_natural_query(query: str):
        """Extracts subject, PYQ intent, difficulty, and count from natural query."""
        lowered = query.lower()
        extracted_is_pyq = None
        extracted_diff = None
        extracted_count = None
        extracted_subject = None

        # PYQ check
        if any(w in lowered for w in ["pyq", "previous year", "past year", "reet", "rpsc", "ras", "cet"]):
            extracted_is_pyq = True

        # Difficulty check
        if "easy" in lowered:
            extracted_diff = Difficulty.EASY
        elif "hard" in lowered:
            extracted_diff = Difficulty.HARD
        elif "medium" in lowered:
            extracted_diff = Difficulty.MEDIUM

        # Count check
        count_match = re.search(r'\b(\d+)\s*(?:questions?|mcqs?|q)?\b', lowered)
        if count_match:
            try:
                extracted_count = int(count_match.group(1))
            except ValueError:
                pass

        # Subject detection
        if "rajasthan" in lowered or "gk" in lowered:
            extracted_subject = "Rajasthan GK"
        elif "physics" in lowered:
            extracted_subject = "Physics"
        elif "chemistry" in lowered:
            extracted_subject = "Chemistry"
        elif "math" in lowered:
            extracted_subject = "Mathematics"
        elif "computer" in lowered or "cs" in lowered:
            extracted_subject = "Computer Science"
        elif "ai" in lowered or "artificial intelligence" in lowered:
            extracted_subject = "Artificial Intelligence"

        return extracted_subject, extracted_is_pyq, extracted_diff, extracted_count

    @classmethod
    def generate_quiz(cls, db: Session, req: QuizGenerateRequest) -> QuizResponse:
        subject = req.subject
        is_pyq = req.is_pyq
        difficulty = req.difficulty
        count = req.number_of_questions

        if req.query:
            q_subj, q_pyq, q_diff, q_count = cls._parse_natural_query(req.query)
            if q_subj and not subject:
                subject = q_subj
            if q_pyq is not None and is_pyq is None:
                is_pyq = q_pyq
            if q_diff and not difficulty:
                difficulty = q_diff
            if q_count and count == 5:  # default was 5
                count = min(max(q_count, 1), 50)

        filters = QuestionFilterParams(
            subject=subject,
            difficulty=difficulty,
            question_type=QuestionType.MCQ,
            is_pyq=is_pyq,
            skip=0,
            limit=50,
        )
        questions, _ = QuestionRepository.list(db, filters)

        if not questions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No suitable questions found in the Question Bank to build this quiz."
            )

        # Shuffle and sample up to count
        random.shuffle(questions)
        selected_questions = questions[:count]

        # Generate meaningful title
        title_parts = []
        if subject:
            title_parts.append(subject)
        if is_pyq:
            title_parts.append("PYQ")
        if difficulty:
            title_parts.append(difficulty.value)
        title_parts.append(f"Quiz ({len(selected_questions)} Questions)")
        quiz_title = " ".join(title_parts)

        quiz = JsonQuizSession(
            id=uuid.uuid4(),
            title=quiz_title,
            query_prompt=req.query,
            question_ids=[str(q.id) for q in selected_questions],
            total_questions=len(selected_questions),
        )
        JSON_QUIZ_SESSIONS[quiz.id] = quiz

        # Build public response (without correct_answer or explanation)
        public_questions = [
            QuizPublicQuestion(
                id=q.id,
                question_type=q.question_type,
                question_text=q.question_text,
                options=q.options,
                subject=q.subject,
                chapter=q.chapter,
                topic=q.topic,
                difficulty=q.difficulty,
                is_pyq=q.is_pyq,
                exam_name=q.exam_name,
                exam_year=q.exam_year,
                exam_month=q.exam_month,
                exam_day=q.exam_day,
            )
            for q in selected_questions
        ]

        return QuizResponse(
            id=quiz.id,
            title=quiz.title,
            total_questions=quiz.total_questions,
            questions=public_questions
        )

    @classmethod
    def get_quiz(cls, db: Session, quiz_id: uuid.UUID) -> QuizResponse:
        quiz = JSON_QUIZ_SESSIONS.get(quiz_id)
        if quiz is None:
            quiz = QuizRepository.get_by_id(db, quiz_id)
        if not quiz:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quiz '{quiz_id}' not found."
            )

        question_uuids = [uuid.UUID(qid) for qid in quiz.question_ids]
        stmt = select(QuestionModel).where(QuestionModel.id.in_(question_uuids))
        questions_dict = {q.id: q for q in db.scalars(stmt).all()}

        ordered_questions = [
            questions_dict[qid] for qid in question_uuids if qid in questions_dict
        ]

        public_questions = [
            QuizPublicQuestion(
                id=q.id,
                question_type=q.question_type,
                question_text=q.question_text,
                options=q.options,
                subject=q.subject,
                chapter=q.chapter,
                topic=q.topic,
                difficulty=q.difficulty,
                is_pyq=q.is_pyq,
                exam_name=q.exam_name,
                exam_year=q.exam_year,
                exam_month=q.exam_month,
                exam_day=q.exam_day,
            )
            for q in ordered_questions
        ]

        return QuizResponse(
            id=quiz.id,
            title=quiz.title,
            total_questions=quiz.total_questions,
            questions=public_questions
        )

    @classmethod
    def submit_answer(cls, db: Session, quiz_id: uuid.UUID, payload: QuizAnswerRequest) -> QuizAnswerResponse:
        quiz = JSON_QUIZ_SESSIONS.get(quiz_id)
        if quiz is None:
            quiz = QuizRepository.get_by_id(db, quiz_id)
        if not quiz:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quiz '{quiz_id}' not found."
            )

        question = QuestionRepository.get_by_id(db, payload.question_id)
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Question '{payload.question_id}' not found."
            )

        # Verification logic: strict or prefix match
        # Handles string, {"Key": "A", "Text": "..."}, or "A. Jaipur"
        candidates = []
        if isinstance(payload.selected_answer, dict):
            if "Key" in payload.selected_answer:
                candidates.append(str(payload.selected_answer["Key"]).strip().lower())
            if "Text" in payload.selected_answer:
                candidates.append(str(payload.selected_answer["Text"]).strip().lower())
            if "text" in payload.selected_answer:
                candidates.append(str(payload.selected_answer["text"]).strip().lower())
        elif payload.selected_answer is not None:
            candidates.append(str(payload.selected_answer).strip().lower())

        corr = (question.correct_answer or "").strip().lower()

        is_correct = False
        for sel in candidates:
            if sel == corr:
                is_correct = True
                break
            # E.g. "A" matches "A. Jaipur" or "A: Jaipur"
            if len(sel) == 1 and (corr.startswith(f"{sel}.") or corr.startswith(f"{sel}:") or corr.startswith(f"{sel} ")):
                is_correct = True
                break
            if len(corr) == 1 and (sel.startswith(f"{corr}.") or sel.startswith(f"{corr}:") or sel.startswith(f"{corr} ")):
                is_correct = True
                break
            # E.g. "Jaipur" in "A. Jaipur"
            if len(sel) > 2 and sel in corr:
                is_correct = True
                break
            if len(corr) > 2 and corr in sel:
                is_correct = True
                break

        if isinstance(quiz, JsonQuizSession):
            quiz.answers[str(question.id)] = {
                "selected_answer": payload.selected_answer,
                "is_correct": is_correct,
            }
            quiz.score = sum(1 for answer in quiz.answers.values() if answer.get("is_correct"))
            quiz.completed = len(quiz.answers) >= quiz.total_questions
            updated_quiz = quiz
        else:
            updated_quiz = QuizRepository.record_answer(
                db=db,
                quiz=quiz,
                question_id=str(question.id),
                selected_answer=payload.selected_answer,
                is_correct=is_correct
            )

        return QuizAnswerResponse(
            question_id=question.id,
            selected_answer=payload.selected_answer,
            is_correct=is_correct,
            correct_answer=question.correct_answer or "",
            explanation=question.explanation,
            score=updated_quiz.score,
            total_answered=len(updated_quiz.answers),
            total_questions=updated_quiz.total_questions,
            quiz_completed=updated_quiz.completed
        )

    @classmethod
    def get_summary(cls, db: Session, quiz_id: uuid.UUID) -> QuizSummaryResponse:
        quiz = JSON_QUIZ_SESSIONS.get(quiz_id)
        if quiz is None:
            quiz = QuizRepository.get_by_id(db, quiz_id)
        if not quiz:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")
        return QuizSummaryResponse.model_validate(quiz)
