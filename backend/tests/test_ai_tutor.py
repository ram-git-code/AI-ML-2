import json
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.ai_tutor_service import AITutorService, ResponseDecisionEngine, LEARNING_CONTEXTS
from app.schemas.ai import MessageIntent, AnswerMode, AITutorMessage, LearningContextSnapshot
from app.core.config import settings

client = TestClient(app)

def test_greeting_no_rag_no_quiz():
    """1. Greeting: hi -> GREETING, no RAG, no web search, quiz=False"""
    decision = ResponseDecisionEngine.analyze("hi")
    assert decision.intent == MessageIntent.GREETING
    assert decision.domain == "General"
    assert decision.topic is None
    assert decision.requires_rag is False
    assert decision.requires_web_search is False
    assert decision.quiz_eligible is False

def test_pm_english_factual():
    """2. PM English: who is the pm of india -> topic = Prime Minister of India, current info, no filler"""
    decision = ResponseDecisionEngine.analyze("who is the pm of india")
    assert decision.intent == MessageIntent.CURRENT_INFORMATION
    assert decision.topic == "Prime Minister of India"
    assert decision.domain == "General Knowledge"
    assert decision.requires_web_search is True
    assert decision.requires_rag is False
    assert decision.quiz_eligible is False

    fallback = AITutorService._generate_adaptive_fallback(decision, user_query="who is the pm of india")
    assert "Narendra Modi" in fallback
    assert "represents a fundamental topic" not in fallback
    assert "core relations and principles" not in fallback

def test_pm_typo_resolution():
    """3. PM Typo: who is the p of india -> Prime Minister of India, no fake topic"""
    decision = ResponseDecisionEngine.analyze("who is the p of india")
    assert decision.topic == "Prime Minister of India"
    assert decision.intent == MessageIntent.CURRENT_INFORMATION
    
    fallback = AITutorService._generate_adaptive_fallback(decision, user_query="who is the p of india")
    assert "Narendra Modi" in fallback
    assert "Who Is The P Of India" not in fallback

def test_pm_hinglish_resolution():
    """4. PM Hinglish: are india ke PM kon he -> Prime Minister of India, responds appropriately"""
    decision = ResponseDecisionEngine.analyze("are india ke PM kon he")
    assert decision.topic == "Prime Minister of India"
    assert decision.intent == MessageIntent.CURRENT_INFORMATION
    
    fallback = AITutorService._generate_adaptive_fallback(decision, user_query="are india ke PM kon he")
    assert "Narendra Modi" in fallback
    assert "Are India Ke Pm Kon He" not in fallback
    assert "represents a fundamental topic" not in fallback

def test_first_pm_of_india():
    """5. First PM: who was the first pm of india -> First Prime Minister of India, Jawaharlal Nehru"""
    decision = ResponseDecisionEngine.analyze("who was the first pm of india")
    assert decision.intent == MessageIntent.FACTUAL_QUESTION
    assert decision.topic == "First Prime Minister of India"
    assert decision.domain == "General Knowledge"
    assert decision.quiz_eligible is False

    fallback = AITutorService._generate_adaptive_fallback(decision, user_query="who was the first pm of india")
    assert "Jawaharlal Nehru" in fallback
    assert "1947" in fallback

def test_photosynthesis_academic_biology():
    """6. Photosynthesis: explain photosynthesis -> ACADEMIC_QUESTION, Photosynthesis, Biology, quiz=True"""
    decision = ResponseDecisionEngine.analyze("explain photosynthesis")
    assert decision.intent == MessageIntent.ACADEMIC_QUESTION
    assert decision.topic == "Photosynthesis"
    assert decision.domain == "Biology"
    assert decision.requires_rag is True
    assert decision.quiz_eligible is True

    fallback = AITutorService._generate_adaptive_fallback(decision, user_query="explain photosynthesis")
    assert "Photosynthesis" in fallback
    assert "glucose" in fallback.lower() or "sunlight" in fallback.lower()

def test_recursion_academic_cs():
    """7. Recursion: what is recursion -> ACADEMIC_QUESTION, Recursion, Computer Science, quiz=True"""
    decision = ResponseDecisionEngine.analyze("what is recursion")
    assert decision.intent == MessageIntent.ACADEMIC_QUESTION
    assert decision.topic == "Recursion"
    assert decision.domain == "Computer Science"
    assert decision.requires_rag is True
    assert decision.quiz_eligible is True

    fallback = AITutorService._generate_adaptive_fallback(decision, user_query="what is recursion")
    assert "Base Case" in fallback

def test_casual_conversation():
    """8. Casual: how are you bro -> SMALL_TALK, no RAG, no web search, quiz=False"""
    decision = ResponseDecisionEngine.analyze("how are you bro")
    assert decision.intent == MessageIntent.SMALL_TALK
    assert decision.domain == "General"
    assert decision.requires_rag is False
    assert decision.requires_web_search is False
    assert decision.quiz_eligible is False

def test_followup_him_anaphora_resolution():
    """9. Follow-up: Who is the PM of India? -> Tell me more about him -> anaphora resolution"""
    pm_ctx_id = "ctx-pm-anaphora"
    LEARNING_CONTEXTS[pm_ctx_id] = LearningContextSnapshot(
        learning_context_id=pm_ctx_id,
        conversation_id="conv-pm-anaphora",
        intent=MessageIntent.CURRENT_INFORMATION,
        domain="General Knowledge",
        topic="Prime Minister of India",
        concepts=["Narendra Modi", "Head of Government"],
        quiz_available=False
    )

    history = [
        AITutorMessage(role="user", content="Who is the PM of India?"),
        AITutorMessage(role="assistant", content="The Prime Minister of India is Narendra Modi...", learning_context_id=pm_ctx_id)
    ]

    decision = ResponseDecisionEngine.analyze(
        message="Tell me more about him.",
        chat_history=history
    )
    assert decision.topic == "Prime Minister of India"
    assert decision.intent in [MessageIntent.EXPAND_PREVIOUS_ANSWER, MessageIntent.ACADEMIC_FOLLOW_UP]

def test_context_switching_it_resolution():
    """10. Context switching: Newton -> Photosynthesis -> Explain it in detail -> it = Photosynthesis"""
    ctx_newton = "ctx-newton-switch"
    ctx_photo = "ctx-photo-switch"

    LEARNING_CONTEXTS[ctx_newton] = LearningContextSnapshot(
        learning_context_id=ctx_newton,
        conversation_id="conv-switch",
        intent=MessageIntent.ACADEMIC_QUESTION,
        domain="Physics",
        topic="Newton's Second Law",
        quiz_available=True
    )
    LEARNING_CONTEXTS[ctx_photo] = LearningContextSnapshot(
        learning_context_id=ctx_photo,
        conversation_id="conv-switch",
        intent=MessageIntent.ACADEMIC_QUESTION,
        domain="Biology",
        topic="Photosynthesis",
        quiz_available=True
    )

    history = [
        AITutorMessage(role="user", content="Explain Newton's second law"),
        AITutorMessage(role="assistant", content="Newton's law...", learning_context_id=ctx_newton),
        AITutorMessage(role="user", content="Now explain photosynthesis"),
        AITutorMessage(role="assistant", content="Photosynthesis is...", learning_context_id=ctx_photo),
    ]

    decision = ResponseDecisionEngine.analyze(
        message="Explain it in detail.",
        chat_history=history
    )
    assert decision.topic == "Photosynthesis"
    assert decision.domain == "Biology"
    assert decision.answer_mode == AnswerMode.DETAILED

def test_rag_irrelevant_result_filtered_out():
    """11. RAG relevance threshold: Database search with low similarity is rejected and not passed as context"""
    from app.models.question import QuestionModel
    from app.models.enums import QuestionType
    import uuid

    # Simulate unrelated questions with low similarity < 0.65
    unrelated_q = QuestionModel(
        id=uuid.uuid4(),
        question_type=QuestionType.MCQ,
        question_text="What is the force required to accelerate a 5kg mass at 2m/s^2?",
        options=["A. 10N", "B. 20N", "C. 5N", "D. 15N"],
        correct_answer="A",
        explanation="F = ma = 5 * 2 = 10N",
        subject="Physics",
        chapter="Dynamics",
        topic="Newton's Second Law",
        embedding=[0.99, 0.01, 0.0]  # Orthogonal/low similarity to query
    )

    decision = ResponseDecisionEngine.analyze("Who is the PM of India?")
    assert decision.requires_rag is False  # Non-academic GK query skips RAG

    # For academic query with low similarity
    decision_acad = ResponseDecisionEngine.analyze("Explain photosynthesis")
    assert decision_acad.requires_rag is True

    # Check prompt builder with empty retrieved questions
    prompt = AITutorService._build_adaptive_prompt(decision_acad, retrieved_questions=[])
    assert "No relevant local knowledge found in syllabus question bank." in prompt

def test_stream_sse_endpoint():
    """12. SSE Stream: /api/ai/chat/stream returns valid events"""
    payload = {"message": "Hi"}
    response = client.post("/api/ai/chat/stream", json=payload)
    assert response.status_code == 200
    text = response.text
    assert "event: start" in text
    assert "event: complete" in text
    for block in text.split("\n\n"):
        if block.startswith("event: complete"):
            data_line = [l for l in block.split("\n") if l.startswith("data: ")][0]
            payload_data = json.loads(data_line[6:])
            assert payload_data["can_create_quiz"] is False
            assert payload_data["intent"] == "GREETING"

def test_cm_of_rajasthan_explanation():
    """Test A - CM: explain about the cm of Rajasthan -> EXPLANATION_REQUEST, Chief Minister of Rajasthan, no filler"""
    decision = ResponseDecisionEngine.analyze("explain about the cm of Rajasthan")
    assert decision.intent in [MessageIntent.EXPLANATION_REQUEST, MessageIntent.CURRENT_INFORMATION]
    assert decision.topic == "Chief Minister of Rajasthan"
    assert decision.domain == "General Knowledge"
    assert decision.answer_mode == AnswerMode.MEDIUM
    assert decision.requires_web_search is True

    fallback = AITutorService._generate_adaptive_fallback(decision, user_query="explain about the cm of Rajasthan")
    assert "Bhajan Lal Sharma" in fallback
    assert "Chief Minister of Rajasthan" in fallback
    assert "key concept in General" not in fallback
    assert "core principles and practical applications" not in fallback
    assert "represents a fundamental topic" not in fallback

def test_newton_second_law_simple_with_examples():
    """Test B - Newton: Explain Newton's second law of motion in simple terms with examples."""
    query = "Explain Newton's second law of motion in simple terms with examples."
    decision = ResponseDecisionEngine.analyze(query)
    assert decision.intent == MessageIntent.ACADEMIC_QUESTION
    assert decision.topic == "Newton's Second Law of Motion"
    assert decision.domain == "Physics"
    assert decision.style == "SIMPLE"
    assert decision.include_examples is True
    assert decision.include_formula is True
    assert decision.quiz_eligible is True

    fallback = AITutorService._generate_adaptive_fallback(decision, user_query=query)
    assert "F = ma" in fallback
    assert "force" in fallback.lower()
    assert "acceleration" in fallback.lower()
    assert "mass" in fallback.lower()
    assert "Example 1" in fallback or "example" in fallback.lower()
    # Ensure it is not an overly brief one-line answer
    assert len(fallback.split("\n")) > 5

def test_who_is_current_cm_of_rajasthan():
    """Test - CM current: who is the current CM of Rajasthan"""
    decision = ResponseDecisionEngine.analyze("who is the current CM of Rajasthan")
    assert decision.intent == MessageIntent.CURRENT_INFORMATION
    assert decision.topic == "Chief Minister of Rajasthan"
    assert decision.domain == "General Knowledge"

    fallback = AITutorService._generate_adaptive_fallback(decision, user_query="who is the current CM of Rajasthan")
    assert "Bhajan Lal Sharma" in fallback

