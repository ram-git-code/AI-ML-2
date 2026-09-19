import json
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


QUESTIONS_FILE = Path(__file__).resolve().parents[1] / "db" / "questions.json"
QUESTION_NAMESPACE = uuid.UUID("b7c2f6a6-779e-4c88-9ef8-9b4f80d8bb3e")


@dataclass
class JsonQuestion:
    id: uuid.UUID
    question_type: str
    question_text: str
    options: Optional[list[str]]
    correct_answer: Optional[str]
    explanation: Optional[str]
    subject: str
    chapter: str
    topic: str
    difficulty: str
    is_pyq: bool
    exam_name: Optional[str] = None
    exam_year: Optional[int] = None
    exam_month: Optional[int] = None
    exam_day: Optional[int] = None


class JsonQuestionService:
    @staticmethod
    def _load() -> list[JsonQuestion]:
        with QUESTIONS_FILE.open("r", encoding="utf-8") as file:
            payload = json.load(file)

        questions = []
        for item in payload.get("Questions", []):
            translation = next(
                (entry for entry in item.get("translations", []) if entry.get("lang_id") == "en"),
                item.get("translations", [{}])[0] if item.get("translations") else {},
            )
            options = translation.get("options") or None
            answer_number = translation.get("correct_answer_number")
            correct_answer = None
            if options and isinstance(answer_number, int):
                answer_index = answer_number if answer_number == 0 else answer_number - 1
                if 0 <= answer_index < len(options):
                    correct_answer = str(options[answer_index])

            pyq = next((exam for exam in item.get("pyq_exams", []) if exam.get("exam_name")), None)
            metadata = item.get("meta_data", {})
            questions.append(
                JsonQuestion(
                    id=uuid.uuid5(QUESTION_NAMESPACE, str(item["question_id"])),
                    question_type=item.get("question_type", "MCQ"),
                    question_text=translation.get("question", ""),
                    options=options,
                    correct_answer=correct_answer,
                    explanation=translation.get("solution"),
                    subject=item.get("subject_name", ""),
                    chapter=item.get("chapter_name", ""),
                    topic=item.get("topic_name", ""),
                    difficulty=str(metadata.get("difficulty_level", "medium")).upper(),
                    is_pyq=pyq is not None,
                    exam_name=pyq.get("exam_name") if pyq else None,
                    exam_year=pyq.get("year") if pyq and pyq.get("year") else None,
                    exam_month=pyq.get("month") if pyq and pyq.get("month") else None,
                    exam_day=pyq.get("day") if pyq and pyq.get("day") else None,
                )
            )
        return questions

    @classmethod
    def list_questions(
        cls,
        subject: Optional[str] = None,
        difficulty: Optional[str] = None,
        is_pyq: Optional[bool] = None,
        question_type: Optional[str] = None,
    ) -> list[JsonQuestion]:
        questions = cls._load()
        return [
            question for question in questions
            if (not subject or subject.lower() in question.subject.lower())
            and (not difficulty or question.difficulty == str(difficulty).upper())
            and (is_pyq is None or question.is_pyq == is_pyq)
            and (not question_type or question.question_type == question_type)
        ]

    @classmethod
    def find_relevant(cls, text: str) -> Optional[JsonQuestion]:
        terms = {term for term in text.lower().split() if len(term) > 2}
        if not terms:
            return None

        best_question = None
        best_score = 0
        for question in cls._load():
            searchable = " ".join((
                question.question_text,
                question.subject,
                question.chapter,
                question.topic,
                " ".join(question.options or []),
            )).lower()
            score = sum(1 for term in terms if term in searchable)
            if question.question_text.lower() in text.lower():
                score += 5
            if score > best_score:
                best_question = question
                best_score = score
        return best_question

    @classmethod
    def get_by_id(cls, question_id: uuid.UUID) -> Optional[JsonQuestion]:
        return next((q for q in cls._load() if q.id == question_id), None)