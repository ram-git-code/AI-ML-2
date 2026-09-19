# AI Question Bank and Quiz Tutor - Backend

Backend for the AI-powered educational question-bank and quiz platform. It provides a FastAPI HTTP & SSE streaming API, PostgreSQL persistence with Gemini embeddings, semantic RAG retrieval, Gemini LLM tutoring & explanations, dynamic quiz sessions, and React client integration.

---

## Architecture

```mermaid
flowchart LR
    UI[React + Vite Frontend] --> API[FastAPI API Layer]
    API --> DecisionEngine["ResponseDecisionEngine\n(Intent, Semantic Topic, Domain, Mode)"]
    DecisionEngine --> RAG[RAG Retrieval]
    DecisionEngine --> LLM[Gemini LLM Service]
    API --> Quiz[Quiz Generation Service]
    API --> QRepo[Question Repository]
    QRepo --> PG[(PostgreSQL)]
    Quiz --> PG
    RAG --> PG
    LLM --> Gemini[Google Gemini API]
    Upload[JSON Upload] --> Jobs[Background Import Job]
    Jobs --> PG
    Jobs --> Embed[Gemini Embeddings]
    Embed --> PG
    API --> Health[PostgreSQL Health Check]
    Health --> PG
```

### Source of Truth

All runtime questions used by quiz generation, answer validation, subject selection, and tutor context come from **PostgreSQL**. The original JSON file is an import source, not a runtime question source.

PostgreSQL stores the normalized question record, answer, explanation, and Gemini embedding. Targeted RAG retrieval embeds the user query, compares it with stored embeddings using vector similarity, and supplies curriculum questions to Gemini. Gemini generates educational explanations and tutor responses; it does not decide the authoritative correct answer.

---

### Main Modules

| Module | Responsibility |
| --- | --- |
| `app/main.py` | Creates FastAPI, CORS configuration, and router registration |
| `app/api/` | HTTP & SSE routes for health, questions, quizzes, and AI tutor |
| `app/schemas/` | Pydantic request, response, decision, and context snapshot contracts |
| `app/models/` | SQLAlchemy PostgreSQL models and enums |
| `app/repositories/` | Database access, vector search, and filtering |
| `app/services/ai_tutor_service.py` | `ResponseDecisionEngine`, semantic topic extractor, prompt builder, and SSE streaming |
| `app/services/llm_service.py` | Google Gemini streaming and text generation clients |
| `app/services/quiz_service.py` | Quiz session generation, scoring, and answer validation |
| `app/services/question_import_service.py` | Background dataset normalization and batch embedding |
| `app/db/postgres.py` | SQLAlchemy engine, sessions, and database health check |
| `alembic/` | Database migrations |

---

## Requirements

- Python 3.12+ (Python 3.13 supported)
- PostgreSQL 14+ with a database named `ai_project`
- Google AI Studio API key for Gemini explanations and embeddings
- Node.js 18+ for the frontend

---

## Configuration

Create `backend/.env`:

```env
DATABASE_URL=postgresql+psycopg://postgres:your_password@localhost:5432/ai_project
GOOGLE_API_KEY=your_google_ai_studio_key
GOOGLE_MODEL=gemini-3.6-flash
GOOGLE_EMBEDDING_MODEL=gemini-embedding-001
ENVIRONMENT=development
CORS_ORIGINS=["http://localhost:5173", "http://127.0.0.1:5173"]
```

---

## Installation and Startup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m alembic upgrade head
python run.py
```

The API is available at `http://localhost:8000`. Interactive documentation is available at [`/docs`](http://localhost:8000/docs) and [`/redoc`](http://localhost:8000/redoc).

---

## API Reference

### 1. AI Tutor Chat & Streaming

#### `POST /api/ai/chat/stream`

Server-Sent Events (SSE) streaming endpoint for AI Tutor Chat. Analyzes student intent, detects domain, extracts semantic topic, resolves conversation follow-ups, and streams token responses in real-time.

**Request:**
```json
{
  "message": "Can you explain about the PM of India?",
  "conversation_id": "optional-uuid",
  "subject": "optional-subject",
  "chat_history": [
    {"role": "user", "content": "Hi"},
    {"role": "assistant", "content": "Hello! What would you like to learn today?"}
  ]
}
```

**SSE Events Streamed:**
- `event: start` $\rightarrow$ contains `conversation_id`, `learning_context_id`, `intent`, `domain`, `topic`, `quiz_available`.
- `event: token` $\rightarrow$ chunks of generated text: `{"text": "..."}`.
- `event: complete` $\rightarrow$ final metadata payload with snapshot details.
- `event: error` $\rightarrow$ error notification if streaming fails.

---

#### `POST /api/ai/chat/create-quiz`

Generates an interactive 5-question practice quiz specifically bound to the student's unique learning context.

**Request:**
```json
{
  "learning_context_id": "learning-context-uuid",
  "topic": "Newton's Second Law",
  "subject": "Physics",
  "question_count": 5,
  "difficulty": "medium"
}
```

**Response: `201 Created`** returns the generated `QuizResponse` session.

---

### 2. AI Explanations

#### `POST /api/ai/explain`

Generates a deep Gemini explanation for a selected quiz answer based on authoritative PostgreSQL question records.

**Request:**
```json
{
  "question_id": "question-uuid",
  "user_answer": "B. Jodhpur"
}
```

**Response:**
```json
{
  "question_id": "question-uuid",
  "user_answer": "B. Jodhpur",
  "correct_answer": "A. Jaipur",
  "why_wrong": "...",
  "why_correct": "...",
  "key_takeaway": "...",
  "full_explanation": "..."
}
```

---

### 3. Questions & Quizzes

#### `POST /api/quizzes/generate`
Generates a quiz from natural-language prompts or filters.

#### `POST /api/quizzes/{id}/answers`
Evaluates an answer against PostgreSQL and updates the session score.

#### `GET /api/questions/subjects`
Returns distinct available subjects.

#### `POST /api/questions/import`
Starts background multipart JSON question import.

---

## 🧪 Tests

Run the complete test suite:

```bash
cd backend
python -m pytest -v
```

All 22 test cases in `tests/` test intent classification, topic extraction, follow-up reference resolution, problem solving, streaming, and database CRUD.
