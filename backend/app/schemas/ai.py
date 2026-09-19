import uuid
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field

class MessageIntent(str, Enum):
    GREETING = "GREETING"
    SMALL_TALK = "SMALL_TALK"
    ACADEMIC_QUESTION = "ACADEMIC_QUESTION"
    ACADEMIC_EXPLANATION = "ACADEMIC_EXPLANATION"
    EXPLANATION_REQUEST = "EXPLANATION_REQUEST"
    ACADEMIC_PROBLEM = "ACADEMIC_PROBLEM"
    ACADEMIC_FOLLOW_UP = "ACADEMIC_FOLLOW_UP"
    EXPAND_PREVIOUS_ANSWER = "EXPAND_PREVIOUS_ANSWER"
    FACTUAL_QUESTION = "FACTUAL_QUESTION"
    CURRENT_INFORMATION = "CURRENT_INFORMATION"
    GENERAL_QUESTION = "GENERAL_QUESTION"
    QUIZ_REQUEST = "QUIZ_REQUEST"
    CLARIFICATION_REQUEST = "CLARIFICATION_REQUEST"
    THANKS = "THANKS"
    GOODBYE = "GOODBYE"
    UNCLEAR = "UNCLEAR"

class AnswerMode(str, Enum):
    SHORT = "SHORT"
    MEDIUM = "MEDIUM"
    DETAILED = "DETAILED"
    PROBLEM_SOLVING = "PROBLEM_SOLVING"

class ResponseDecision(BaseModel):
    intent: MessageIntent
    domain: str
    topic: Optional[str] = None
    subtopic: Optional[str] = None
    normalized_question: Optional[str] = None
    concepts: List[str] = Field(default_factory=list)
    answer_mode: AnswerMode = AnswerMode.MEDIUM
    style: str = "NATURAL"
    include_examples: bool = False
    include_formula: bool = False
    include_steps: bool = False
    requires_rag: bool = False
    requires_web_search: bool = False
    search_query: Optional[str] = None
    quiz_eligible: bool = False
    language: str = "en"

class LearningContextSnapshot(BaseModel):
    learning_context_id: str
    conversation_id: str
    intent: MessageIntent
    domain: str = "General"
    topic: Optional[str] = None
    subtopic: Optional[str] = None
    normalized_question: Optional[str] = None
    concepts: List[str] = Field(default_factory=list)
    answer_mode: AnswerMode = AnswerMode.MEDIUM
    style: str = "NATURAL"
    include_examples: bool = False
    include_formula: bool = False
    include_steps: bool = False
    quiz_available: bool = False
    source_message: Optional[str] = None

class AIExplainRequest(BaseModel):
    question_id: uuid.UUID
    user_answer: str

class AIExplainResponse(BaseModel):
    question_id: uuid.UUID
    user_answer: str
    correct_answer: str
    why_wrong: str
    why_correct: str
    key_takeaway: str
    full_explanation: str

class AITutorMessage(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str
    learning_context_id: Optional[str] = None

class AITutorRequest(BaseModel):
    question_id: Optional[uuid.UUID] = None
    subject: Optional[str] = None
    user_message: str
    chat_history: Optional[List[AITutorMessage]] = Field(default_factory=list)

class AITutorResponse(BaseModel):
    reply: str
    question_id: Optional[uuid.UUID] = None

class AIChatStreamRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Student's query or doubt")
    conversation_id: Optional[str] = Field(default=None, description="Optional conversation identifier")
    subject: Optional[str] = Field(default=None, description="Optional subject context")
    topic: Optional[str] = Field(default=None, description="Optional topic context")
    chat_history: Optional[List[AITutorMessage]] = Field(default_factory=list, description="Prior conversation messages")

class AIChatCreateQuizRequest(BaseModel):
    learning_context_id: Optional[str] = Field(default=None, description="Unique ID of the learning context to generate quiz from")
    topic: Optional[str] = Field(default=None, description="Optional fallback topic or concept")
    subject: Optional[str] = Field(default=None, description="Optional subject category")
    question_count: int = Field(default=5, ge=1, le=20, description="Number of questions in quiz")
    difficulty: Optional[str] = Field(default="medium", description="Quiz difficulty level")
    conversation_id: Optional[str] = Field(default=None, description="Optional conversation identifier")
    chat_history: Optional[List[AITutorMessage]] = Field(default_factory=list, description="Recent conversation messages")
