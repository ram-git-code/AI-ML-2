# AI Question Bank and Quiz Tutor

Backend for the educational question-bank application. It provides a FastAPI HTTP API, PostgreSQL persistence, Qdrant vector indexing, Google Gemini explanations, quiz sessions, and a React frontend integration.

## Architecture

```mermaid
flowchart LR
		UI[React and Vite frontend] --> API[FastAPI API]
		API --> QRepo[Question repository]
		QRepo --> PG[(PostgreSQL)]
		API --> Quiz[Quiz service]
		Quiz --> PG
		API --> Tutor[AI tutor service]
		Tutor --> PG
		Tutor --> Gemini[Google Gemini]
		Upload[JSON upload] --> Jobs[Background import job]
		Jobs --> PG
		Jobs --> Embed[Gemini embeddings]
		Embed --> Qdrant[(Qdrant question_bank)]
		API --> Health[PostgreSQL and Qdrant health checks]
		Health --> PG
		Health --> Qdrant
```

### Source of truth

All runtime questions used by quiz generation, answer validation, subject selection, and tutor context come from PostgreSQL. The original JSON file is an import source, not a runtime question source.

PostgreSQL stores the normalized question record and its answer/explanation. Qdrant stores embeddings and metadata for indexing and future semantic retrieval. Gemini generates educational explanations and tutor responses; it does not decide the authoritative correct answer.

### Main modules

| Module | Responsibility |
| --- | --- |
| `app/main.py` | Creates FastAPI, CORS, and router registration |
| `app/api/` | HTTP routes for health, questions, quizzes, and AI |
| `app/schemas/` | Pydantic request and response contracts |
| `app/models/` | SQLAlchemy PostgreSQL models and enums |
| `app/repositories/` | Database access and filtering |
| `app/services/` | Quiz logic, import normalization, background jobs, and Gemini calls |
| `app/db/postgres.py` | SQLAlchemy engine and request-scoped sessions |
| `app/db/qdrant.py` | Qdrant client and connectivity checks |
| `alembic/` | Database migrations |

## Requirements

- Python 3.12+
- PostgreSQL 14+ with a database named `ai_project`
- Qdrant at `http://localhost:6333`
- Google AI Studio API key for Gemini explanations and embeddings
- Node.js 18+ for the frontend

## Configuration

Create `backend/.env`:

```env
DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/ai_project
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION_NAME=question_bank
GOOGLE_API_KEY=your_google_ai_studio_key
GOOGLE_MODEL=gemini-3.6-flash
GOOGLE_EMBEDDING_MODEL=gemini-embedding-001
CORS_ORIGINS=["http://localhost:5173"]
```

Do not commit `.env` or expose `GOOGLE_API_KEY` in frontend code.

## Installation and startup

From the repository root:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Alternatively:

```powershell
cd backend
python run.py
```

The API is available at `http://localhost:8000`. Interactive documentation is available at [`/docs`](http://localhost:8000/docs), and ReDoc is available at [`/redoc`](http://localhost:8000/redoc).

## API reference

Unless stated otherwise, JSON request and response bodies use `application/json`. UUID values are returned as strings.

### Health and infrastructure

#### `GET /health`

Checks that the FastAPI process is running.

Response:

```json
{
	"status": "ok",
	"app_name": "AI Question Bank & RAG Tutor",
	"version": "1.0.0"
}
```

#### `GET /health/postgres`

Runs a live `SELECT 1` against PostgreSQL. Returns `503` when the database is unavailable.

#### `GET /health/qdrant`

Checks Qdrant HTTP health and lists collections. Returns the configured URL, target collection, collection existence, and existing collections. Returns `503` when Qdrant is unavailable.

### Questions

#### `GET /api/questions/subjects`

Returns distinct subjects currently stored in PostgreSQL. The frontend uses this endpoint for quiz and tutor dropdowns.

Response:

```json
["Chemistry", "Mathematics", "Physics"]
```

#### `POST /api/questions/import`

Starts a background import from a JSON multipart upload. The upload must contain a non-empty `Questions` array. Each question is normalized, validated, upserted into PostgreSQL in batches of 50, and embedded into Qdrant in batches of 10.

Request:

```text
Content-Type: multipart/form-data
file: questions.json
```

The importer supports English translations, options, `correct_answer_number`, subject/chapter/topic metadata, difficulty, and PYQ exam metadata. It accepts both zero-based and one-based answer indexes.

Response: `201 Created`

```json
{
	"job_id": "job-uuid",
	"status": "queued",
	"imported": 0,
	"embedded": 0,
	"total": 650,
	"collection": "question_bank",
	"message": "Import started in the background."
}
```

#### `GET /api/questions/import/{job_id}`

Returns import progress. `status` is one of `queued`, `processing`, `completed`, or `failed`.

Important: job status is currently stored in process memory. Restarting the backend loses the status record, although already committed PostgreSQL rows remain.

#### `POST /api/questions`

Creates one question directly in PostgreSQL. Supported types are `MCQ`, `SINGLE_ANSWER`, and `NOTE`.

Required fields include `question_type`, `question_text`, `subject`, `chapter`, and `topic`. MCQ records require `options` and `correct_answer`; single-answer records require `correct_answer`.

Example:

```json
{
	"question_type": "MCQ",
	"question_text": "What is the capital of Rajasthan?",
	"options": ["A. Jaipur", "B. Jodhpur", "C. Kota", "D. Udaipur"],
	"correct_answer": "A. Jaipur",
	"explanation": "Jaipur is the capital of Rajasthan.",
	"subject": "Rajasthan GK",
	"chapter": "Geography",
	"topic": "Capitals",
	"difficulty": "EASY",
	"is_pyq": false
}
```

#### `GET /api/questions`

Lists PostgreSQL questions. Supported query parameters:

| Parameter | Meaning |
| --- | --- |
| `subject` | Case-insensitive subject filter |
| `chapter` | Case-insensitive chapter filter |
| `topic` | Case-insensitive topic filter |
| `difficulty` | `EASY`, `MEDIUM`, or `HARD` |
| `question_type` | `MCQ`, `SINGLE_ANSWER`, or `NOTE` |
| `is_pyq` | `true` or `false` |
| `exam_name` | Case-insensitive exam filter |
| `exam_year` | Exam year |
| `skip` | Offset, default `0` |
| `limit` | Page size, default `50`, maximum `200` |

#### `GET /api/questions/{id}`

Returns one complete PostgreSQL question, including its answer and explanation.

#### `PUT /api/questions/{id}`

Partially updates an existing question. Send only fields that should change. Type-specific validation is applied again.

#### `DELETE /api/questions/{id}`

Deletes a question from PostgreSQL. Existing Qdrant vectors are not currently removed automatically and may require separate cleanup.

### Quizzes

#### `POST /api/quizzes/generate`

Creates an in-memory quiz session from PostgreSQL MCQs. The response intentionally omits `correct_answer` and `explanation` from public question objects.

Request:

```json
{
	"query": "Give me 5 medium Physics questions",
	"subject": "Physics",
	"difficulty": "MEDIUM",
	"is_pyq": false,
	"number_of_questions": 5
}
```

All fields except `number_of_questions` are optional. Natural-language parsing can infer subject, difficulty, PYQ intent, and requested count from `query`.

Response: `201 Created`, containing `id`, `title`, `total_questions`, and public question data.

#### `GET /api/quizzes/{id}`

Returns the public questions for an existing quiz session without revealing answers.

#### `POST /api/quizzes/{id}/answers`

Evaluates one answer against the authoritative PostgreSQL record, updates the score, and returns the stored explanation.

Request:

```json
{
	"question_id": "question-uuid",
	"selected_answer": "A. Jaipur"
}
```

Response includes `is_correct`, `correct_answer`, `explanation`, `score`, `total_answered`, `total_questions`, and `quiz_completed`.

#### `GET /api/quizzes/{id}/summary`

Returns the current score, completion state, and answer map for the quiz session.

### AI tutor and explanations

#### `POST /api/ai/explain`

Generates a deep Gemini explanation for a selected answer. The question is loaded from PostgreSQL first, so Gemini receives the database answer and stored explanation as authoritative context.

Request:

```json
{
	"question_id": "question-uuid",
	"user_answer": "B. Jodhpur"
}
```

Response fields:

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

#### `POST /api/ai/tutor`

Answers a student question using Gemini and a PostgreSQL question as context. If `question_id` is not supplied, the backend searches database questions, optionally restricted by `subject`, and selects the best text match.

Request:

```json
{
	"question_id": "question-uuid",
	"subject": "Physics",
	"user_message": "Explain this in simple words",
	"chat_history": [
		{"role": "user", "content": "What does this mean?"},
		{"role": "assistant", "content": "It means..."}
	]
}
```

`question_id`, `subject`, and `chat_history` are optional. The response contains `reply` and the resolved `question_id`.

## Data flows

### Import flow

1. The frontend uploads a JSON file to `POST /api/questions/import`.
2. FastAPI validates the file and creates an in-memory job record.
3. A daemon worker opens its own PostgreSQL session.
4. Questions are normalized and committed to PostgreSQL in batches.
5. Gemini creates embeddings for normalized question text.
6. Vectors and question metadata are upserted into Qdrant collection `question_bank`.
7. The frontend polls `GET /api/questions/import/{job_id}` every 1.5 seconds.

PostgreSQL commits happen before embedding work, so a temporary Gemini or Qdrant failure does not discard already stored question rows.

### Quiz flow

1. The frontend loads subjects from PostgreSQL through `/api/questions/subjects`.
2. The user selects a subject or writes a natural-language request.
3. `/api/quizzes/generate` filters PostgreSQL MCQs and creates a quiz session.
4. The frontend submits each answer to `/api/quizzes/{id}/answers`.
5. The backend validates the answer against PostgreSQL and returns the official explanation.
6. For an incorrect answer, the frontend calls `/api/ai/explain` for a deeper Gemini explanation.

### Tutor flow

The tutor uses the current quiz question when available. For a general question, it uses the selected subject and message terms to find a PostgreSQL question, then sends the question, answer, official explanation, and recent chat history to Gemini.

## Frontend

From the repository root:

```powershell
cd frontend
npm install
npm run dev
```

The Vite frontend runs at `http://localhost:5173`. The health client supports `VITE_API_BASE_URL`; the current quiz, AI, and import clients default to `http://localhost:8000`, so update those API clients as well when deploying the frontend against another backend URL.

Production build:

```powershell
npm run build
```

The main screens are:

- AI Quiz Studio: subject selection, quiz generation, answer evaluation, and AI explanations.
- Question Bank: JSON upload and import progress polling.
- Infrastructure: backend, PostgreSQL, and Qdrant health status.

## Tests and troubleshooting

Run backend tests:

```powershell
cd backend
pytest -v
```

Useful checks:

```powershell
curl http://localhost:8000/health
curl http://localhost:8000/health/postgres
curl http://localhost:8000/health/qdrant
```

If quiz generation returns `404 No suitable questions found`, import questions first and confirm `GET /api/questions?limit=1` returns rows. If AI explanations fall back to non-Gemini text, verify `GOOGLE_API_KEY` and the configured Gemini model. If import progress disappears after a backend restart, remember that job metadata is currently process-local.
