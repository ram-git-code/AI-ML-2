from enum import Enum

class QuestionType(str, Enum):
    MCQ = "MCQ"
    SINGLE_ANSWER = "SINGLE_ANSWER"
    NOTE = "NOTE"

class Difficulty(str, Enum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"
