# 🎓 AI Question Bank & Intelligent Quiz Tutor

An AI-powered Question Bank, Quiz Generation, and Intelligent Tutor platform. The application combines **FastAPI**, **PostgreSQL** (with vector/embedding storage), **Google Gemini LLM**, and a modern **React + Vite** frontend.

---

## 🏗️ Architecture Overview

```mermaid
flowchart TD
    subgraph Frontend ["Frontend (React 18 + Vite + TypeScript)"]
        UI[Dashboard & Quiz Generator]
        Player[Interactive Quiz Player]
        AITutor[AI Master Tutor Chat with SSE Streaming]
        ImportUI[JSON Question Bank Ingestion]
    end

    subgraph Backend ["Backend (FastAPI + Python 3.12+)"]
        API[FastAPI REST & Streaming Endpoints]
        DecisionEngine["ResponseDecisionEngine\n(Intent, Semantic Topic, Domain, AnswerMode)"]
        QuizSvc[Quiz Generation Service]
        RAG[Targeted RAG & Vector Retrieval]
        LLMSvc[Gemini LLM Service]
        Repo[PostgreSQL Repository]
    end

    subgraph Database ["Persistence Layer"]
        PG[(PostgreSQL Database)]
    end

    subgraph External ["External AI Services"]
        Gemini[Google Gemini API]
    end

    UI --> API
    Player --> API
    AITutor --> API
    ImportUI --> API

    API --> DecisionEngine
    DecisionEngine --> RAG
    DecisionEngine --> QuizSvc
    DecisionEngine --> LLMSvc
    API --> Repo

    QuizSvc --> Repo
    Repo --> PG
    RAG --> PG
    LLMSvc --> Gemini
```

---

## 🌟 Key Features

- **🧠 Intelligent AI Master Tutor Chat**:
  - **Natural Teaching**: Answers actual student questions directly and pedagogically without rigid templates.
  - **Query Understanding & Semantic Topic Extraction**: Accurately extracts concepts (e.g. `"Prime Minister of India"`, `"Photosynthesis"`, `"Newton's Second Law"`) instead of copying raw user sentences.
  - **Conversational Anaphora & Context Resolution**: Seamlessly resolves pronouns (`"it"`, `"him"`) and expansion directives (`"explain in the large way"`, `"tell me more"`, `"give an example"`) referencing active learning context.
  - **Adaptive Answer Modes**: Dynamically modulates depth (`SHORT`, `MEDIUM`, `DETAILED`, `PROBLEM_SOLVING` for math/equations).
  - **Real-Time Token Streaming**: Server-Sent Events (SSE) streaming for real-time responses.
  - **Context-Bound Quiz Practice**: Generates 5-question targeted quizzes bound specifically to the student's learning interaction.
- **🎯 Dynamic Quiz Generation**: Create custom quizzes using natural language prompts (e.g. *"Give me 5 hard math questions"*) or structured filters (Subject, Difficulty, PYQ).
- **📝 Instant Authoritative Feedback**: Answer validation against PostgreSQL records with immediate explanations, scoring, and Gemini-powered deep explanations.
- **🔍 Targeted RAG Vector Retrieval**: Embedding-based similarity search against syllabus question banks for curriculum grounding.
- **📊 Interactive Dashboard**: Real-time database health check, subject statistics, and quiz analytics.
- **📥 Dataset Ingestion**: Bulk JSON question ingestion pipeline with automated vector embeddings.

---

## 📁 Repository Structure

```text
.
├── backend/                # FastAPI Backend Application
│   ├── alembic/            # Database migrations
│   ├── app/                # Application source code
│   │   ├── api/            # Route controllers (health, questions, quizzes, ai)
│   │   ├── db/             # PostgreSQL connection & session management
│   │   ├── models/         # SQLAlchemy ORM models
│   │   ├── repositories/   # Data access layer
│   │   ├── schemas/        # Pydantic schemas (decisions, snapshots, requests)
│   │   └── services/       # Business logic (decision engine, RAG, LLM, quiz)
│   ├── tests/              # Comprehensive test suite (pytest - 22 test cases)
│   ├── .env.example        # Backend environment sample
│   ├── requirements.txt    # Python dependencies
│   ├── run.py              # Application entrypoint script
│   └── README.md           # Backend-specific documentation
│
├── frontend/               # React + Vite Frontend Application
│   ├── src/
│   │   ├── api/            # Axios API clients & SSE streaming handlers
│   │   ├── components/     # UI components (Dashboard, Quiz Player, AITutorChat)
│   │   ├── App.tsx         # Main application component & tab routing
│   │   └── index.css       # Global styling & tailored design system
│   ├── package.json        # Frontend dependencies & npm scripts
│   ├── tsconfig.json       # TypeScript configuration
│   ├── vite.config.ts      # Vite configuration
│   └── README.md           # Frontend-specific documentation
│
└── README.md               # Root Project Documentation
```

---

## ⚡ Quick Start Guide

### Prerequisites
- **Python**: 3.12+ (Python 3.13 supported)
- **Node.js**: 18+ (Node 24 supported) & npm
- **PostgreSQL**: 14+ installed and running
- **Google AI Studio API Key**: For Gemini AI Tutor & Embeddings

---

### 1. Database Setup
Create a PostgreSQL database:
```sql
CREATE DATABASE ai_project;
```

---

### 2. Backend Setup

1. Open a terminal in the `backend/` directory:
   ```bash
   cd backend
   ```

2. (Optional) Create and activate a Python virtual environment:
   ```bash
   python -m venv .venv
   # Windows (PowerShell):
   .\.venv\Scripts\Activate.ps1
   # macOS / Linux:
   source .venv/bin/activate
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables in `backend/.env`:
   ```env
   DATABASE_URL=postgresql+psycopg://postgres:your_password@localhost:5432/ai_project
   GOOGLE_API_KEY=your_gemini_api_key_here
   GOOGLE_MODEL=gemini-3.6-flash
   GOOGLE_EMBEDDING_MODEL=gemini-embedding-001
   ENVIRONMENT=development
   CORS_ORIGINS=["http://localhost:5173", "http://127.0.0.1:5173"]
   ```

5. Run database migrations:
   ```bash
   python -m alembic upgrade head
   ```

6. Start the FastAPI backend server:
   ```bash
   python run.py
   ```
   - **Backend API**: `http://localhost:8000`
   - **Swagger UI Docs**: `http://localhost:8000/docs`
   - **ReDoc**: `http://localhost:8000/redoc`

---

### 3. Frontend Setup

1. Open a new terminal in the `frontend/` directory:
   ```bash
   cd frontend
   ```

2. Install Node dependencies:
   ```bash
   npm install
   ```

3. Configure environment variables in `frontend/.env`:
   ```env
   VITE_API_BASE_URL=http://localhost:8000
   ```

4. Start the frontend development server:
   ```bash
   npm run dev
   ```
   - **Frontend Application**: `http://localhost:5173/`

---

## 🧪 Running Automated Tests

Run the complete backend unit and integration test suite:
```bash
cd backend
python -m pytest -v
```

All 22 test cases cover:
- Intent classification (`GREETING`, `SMALL_TALK`, `FACTUAL_QUESTION`, `CURRENT_INFORMATION`, `ACADEMIC_QUESTION`, `ACADEMIC_PROBLEM`, `EXPAND_PREVIOUS_ANSWER`)
- Semantic topic extraction & conversation anaphora resolution
- SSE streaming response validation & context snapshot binding
- Question Bank CRUD, Quiz generation, answer evaluation, and AI explanations.

---

## 📖 Sub-project Documentation

- [Backend Documentation](file:///c:/Users/Lenovo/Desktop/AI%20ML/AI%20ML/backend/README.md)
- [Frontend Documentation](file:///c:/Users/Lenovo/Desktop/AI%20ML/AI%20ML/frontend/README.md)
