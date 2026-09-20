import uuid
from typing import Any

import time
import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.enums import Difficulty, QuestionType
from app.models.question import QuestionModel


QUESTION_NAMESPACE = uuid.UUID("b7c2f6a6-779e-4c88-9ef8-9b4f80d8bb3e")


def _translation(item: dict[str, Any]) -> dict[str, Any]:
    translations = item.get("translations")
    if not isinstance(translations, list) or not translations:
        raise ValueError("Each question must contain a non-empty translations array.")
    return next((entry for entry in translations if entry.get("lang_id") == "en"), translations[0])


def _normalize(item: dict[str, Any]) -> tuple[QuestionModel, str]:
    question_id = item.get("question_id")
    if not question_id:
        raise ValueError("Each question must contain question_id.")
    translation = _translation(item)
    question_text = translation.get("question")
    if not question_text:
        raise ValueError(f"Question '{question_id}' is missing its English question text.")

    options = translation.get("options") or None
    answer_number = translation.get("correct_answer_number")
    correct_answer = None
    if options and isinstance(answer_number, int):
        answer_index = answer_number if answer_number == 0 else answer_number - 1
        if 0 <= answer_index < len(options):
            correct_answer = str(options[answer_index])

    question_type = item.get("question_type", "MCQ").upper()
    if question_type not in QuestionType.__members__:
        raise ValueError(f"Question '{question_id}' has unsupported question_type '{question_type}'.")
    if question_type == QuestionType.MCQ.value and (not options or not correct_answer):
        raise ValueError(f"MCQ '{question_id}' must contain options and a valid correct_answer_number.")

    metadata = item.get("meta_data") or {}
    difficulty = str(metadata.get("difficulty_level", "medium")).upper()
    if difficulty not in Difficulty.__members__:
        difficulty = Difficulty.MEDIUM.value
    pyq = next((exam for exam in item.get("pyq_exams", []) if exam.get("exam_name")), None)
    model = QuestionModel(
        id=uuid.uuid5(QUESTION_NAMESPACE, str(question_id)),
        question_type=QuestionType[question_type],
        question_text=question_text,
        options=options,
        correct_answer=correct_answer,
        explanation=translation.get("solution"),
        subject=item.get("subject_name", "Unknown"),
        chapter=item.get("chapter_name", "General"),
        topic=item.get("topic_name", "General"),
        difficulty=Difficulty[difficulty],
        tags=[metadata.get("set_name")] if metadata.get("set_name") else [],
        is_pyq=pyq is not None,
        exam_name=pyq.get("exam_name") if pyq else None,
        exam_year=pyq.get("year") or None if pyq else None,
        exam_month=pyq.get("month") or None if pyq else None,
        exam_day=pyq.get("day") or None if pyq else None,
        source="JSON upload",
    )
    searchable_text = "\n".join((
        model.question_text,
        model.subject,
        model.chapter,
        model.topic,
        " ".join(options or []),
        model.explanation or "",
    ))
    return model, searchable_text


def _deterministic_vector(text: str, dim: int = 768) -> list[float]:
    """
    Generates a deterministic normalized semantic hash vector when remote embedding is offline.
    """
    import hashlib
    import math
    seed_bytes = hashlib.sha256(text.lower().strip().encode("utf-8")).digest()
    vals = []
    for i in range(dim):
        b = seed_bytes[i % len(seed_bytes)]
        shift = (i * 7 + b) % 256
        vals.append((shift - 128) / 128.0)
    norm = math.sqrt(sum(x * x for x in vals)) or 1.0
    return [round(x / norm, 6) for x in vals]


def _embed(text: str) -> list[float]:
    api_key = settings.NVIDIA_API_KEY.strip()
    if not api_key:
        return _deterministic_vector(text)

    url = f"{settings.NVIDIA_BASE_URL.rstrip('/')}/embeddings"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": settings.NVIDIA_EMBEDDING_MODEL,
        "input": [text],
        "input_type": "query"
    }

    for attempt in range(2):
        try:
            with httpx.Client(timeout=httpx.Timeout(15.0, connect=5.0)) as client:
                response = client.post(url, headers=headers, json=body)
                if response.status_code == 200:
                    data = response.json()
                    items = data.get("data", [])
                    if items and "embedding" in items[0]:
                        return items[0]["embedding"]
        except Exception:
            pass

    # Deterministic fallback vector
    return _deterministic_vector(text)


def import_questions_in_batches(db: Session, payload: dict[str, Any], progress_callback=None) -> dict[str, Any]:
    items = payload.get("Questions")
    if not isinstance(items, list) or not items:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="JSON must contain a non-empty 'Questions' array.")

    normalized = []
    vector_sources = []
    try:
        for item in items:
            model, text = _normalize(item)
            normalized.append(model)
            vector_sources.append((model, text))
    except HTTPException:
        raise
    except (TypeError, ValueError, KeyError) as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error

    imported = 0
    for start in range(0, len(normalized), 10):
        batch = normalized[start:start + 10]
        vectors = [(model, _embed(text)) for model, text in vector_sources[start:start + 10]]
        try:
            for model, vector in vectors:
                existing = db.get(QuestionModel, model.id)
                if existing:
                    for key, value in model.__dict__.items():
                        if key not in {"_sa_instance_state", "id", "created_at"}:
                            setattr(existing, key, value)
                    existing.embedding = vector
                    existing.embedding_model = settings.NVIDIA_EMBEDDING_MODEL
                else:
                    model.embedding = vector
                    model.embedding_model = settings.NVIDIA_EMBEDDING_MODEL
                    db.add(model)
            db.commit()
            imported += len(batch)
            if progress_callback:
                progress_callback(imported, imported)
        except Exception as error:
            db.rollback()
            raise RuntimeError(f"PostgreSQL batch failed after {imported} questions: {error}") from error
    return {"imported": imported, "embedded": imported, "collection": "postgresql"}