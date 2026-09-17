# AI Question Bank Backend (FastAPI + RAG + Qdrant)

FastAPI application serving as the backend core for the AI Question Bank & Quiz Tutor.

## 🚀 Setup & Execution (Phase 2)

```bash
# 1. Activate Virtual Environment
cd backend
.\.venv\Scripts\Activate.ps1

# 2. Run Database Migrations
alembic upgrade head

# 3. Start Backend Server
python run.py
```

- **Swagger Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Question CRUD Endpoints**:
  - `POST /api/questions` - Create MCQ, SINGLE_ANSWER, or NOTE
  - `GET /api/questions` - List questions with metadata filtering
  - `GET /api/questions/{id}` - Get question details by UUID
  - `PUT /api/questions/{id}` - Update existing question
  - `DELETE /api/questions/{id}` - Delete question
