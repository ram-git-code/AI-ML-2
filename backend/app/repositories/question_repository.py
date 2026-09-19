import uuid
import math
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.models.question import QuestionModel
from app.schemas.question import QuestionCreate, QuestionUpdate, QuestionFilterParams

class QuestionRepository:

    @staticmethod
    def search_by_embedding(db: Session, embedding: list[float], subject: Optional[str] = None, limit: int = 5, min_similarity: float = 0.0) -> List[QuestionModel]:
        scored = QuestionRepository.search_by_embedding_with_scores(db, embedding, subject=subject, limit=limit, min_similarity=min_similarity)
        return [q for _, q in scored]

    @staticmethod
    def search_by_embedding_with_scores(db: Session, embedding: list[float], subject: Optional[str] = None, limit: int = 5, min_similarity: float = 0.0) -> List[Tuple[float, QuestionModel]]:
        filters = QuestionFilterParams(subject=subject, skip=0, limit=200)
        questions, _ = QuestionRepository.list(db, filters)
        query_norm = math.sqrt(sum(value * value for value in embedding))
        if not query_norm:
            return []

        scored: List[Tuple[float, QuestionModel]] = []
        for question in questions:
            candidate = question.embedding
            if not isinstance(candidate, list) or len(candidate) != len(embedding):
                continue
            candidate_norm = math.sqrt(sum(value * value for value in candidate))
            if not candidate_norm:
                continue
            score = sum(left * right for left, right in zip(embedding, candidate)) / (query_norm * candidate_norm)
            if score >= min_similarity:
                scored.append((score, question))
        scored.sort(key=lambda item: item[0], reverse=True)
        return scored[:limit]

    @staticmethod
    def list_subjects(db: Session) -> List[str]:
        stmt = (
            select(QuestionModel.subject)
            .where(QuestionModel.subject.is_not(None))
            .distinct()
            .order_by(QuestionModel.subject)
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def create(db: Session, schema: QuestionCreate) -> QuestionModel:
        db_obj = QuestionModel(**schema.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def get_by_id(db: Session, question_id: uuid.UUID) -> Optional[QuestionModel]:
        stmt = select(QuestionModel).where(QuestionModel.id == question_id)
        return db.scalar(stmt)

    @staticmethod
    def list(db: Session, filters: QuestionFilterParams) -> Tuple[List[QuestionModel], int]:
        stmt = select(QuestionModel)

        if filters.subject:
            stmt = stmt.where(QuestionModel.subject.ilike(f"%{filters.subject}%"))
        if filters.chapter:
            stmt = stmt.where(QuestionModel.chapter.ilike(f"%{filters.chapter}%"))
        if filters.topic:
            stmt = stmt.where(QuestionModel.topic.ilike(f"%{filters.topic}%"))
        if filters.difficulty:
            stmt = stmt.where(QuestionModel.difficulty == filters.difficulty)
        if filters.question_type:
            stmt = stmt.where(QuestionModel.question_type == filters.question_type)
        if filters.is_pyq is not None:
            stmt = stmt.where(QuestionModel.is_pyq == filters.is_pyq)
        if filters.exam_name:
            stmt = stmt.where(QuestionModel.exam_name.ilike(f"%{filters.exam_name}%"))
        if filters.exam_year:
            stmt = stmt.where(QuestionModel.exam_year == filters.exam_year)

        # Count query
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_count = db.scalar(count_stmt) or 0

        # Pagination and order
        stmt = stmt.order_by(QuestionModel.created_at.desc()).offset(filters.skip).limit(filters.limit)
        items = list(db.scalars(stmt).all())

        return items, total_count

    @staticmethod
    def update(db: Session, db_obj: QuestionModel, schema: QuestionUpdate) -> QuestionModel:
        update_data = schema.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_obj, key, value)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def delete(db: Session, db_obj: QuestionModel) -> None:
        db.delete(db_obj)
        db.commit()
