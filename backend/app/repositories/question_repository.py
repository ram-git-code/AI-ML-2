import uuid
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.models.question import QuestionModel
from app.schemas.question import QuestionCreate, QuestionUpdate, QuestionFilterParams

class QuestionRepository:

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
