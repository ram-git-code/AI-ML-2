# AI Question Bank Backend (FastAPI + PostgreSQL + RAG + Qdrant)

FastAPI application serving as the backend core for the AI Question Bank & Quiz Tutor.

## 🚀 Setup & Execution (Phase 2: Question Bank CRUD & Database)

### 1. Prerequisites
- Python 3.12+
- PostgreSQL running locally on port 5432 with database `ai_project`
- Qdrant running locally on port 6333

### 2. Environment Activation & Dependencies
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Run Database Migrations
```powershell
alembic upgrade head
```

### 4. Run Automated Tests
```powershell
pytest -v
```

### 5. Start Backend Server
```powershell
python run.py
# Or:
# uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 📖 API Documentation & Swagger

Interactive Swagger docs: **[http://localhost:8000/docs](http://localhost:8000/docs)**
ReDoc: **[http://localhost:8000/redoc](http://localhost:8000/redoc)**

### Question CRUD Endpoints:
- `POST /api/questions`: Create an MCQ, SINGLE_ANSWER, or NOTE
- `GET /api/questions`: List questions with metadata filters (`subject`, `chapter`, `topic`, `difficulty`, `question_type`, `is_pyq`, `exam_name`, `exam_year`) & pagination
- `GET /api/questions/{id}`: Fetch single question by UUID
- `PUT /api/questions/{id}`: Update specific fields of a question
- `DELETE /api/questions/{id}`: Delete question from PostgreSQL
