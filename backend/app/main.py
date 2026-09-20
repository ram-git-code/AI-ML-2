from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from app.core.config import settings
from app.core.logging import setup_logging
from app.api import health, questions, quizzes, ai, documents
from app.db.postgres import engine, Base
import app.models.document  # Register models with Base metadata
import app.models.question
import app.models.quiz

setup_logging()

# Initialize DB tables on application load
try:
    Base.metadata.create_all(bind=engine)
except Exception as db_init_err:
    pass

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="""
🎓 **AI Question Bank + NVIDIA NIM RAG + DocuQuiz AI Engine**

    Production-grade Educational Engine supporting MCQs, PYQs, PostgreSQL embeddings, PDF Quiz Engine, and NVIDIA NIM AI Tutor.
""",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")

# Include Routers
app.include_router(health.router)
app.include_router(questions.router)
app.include_router(quizzes.router)
app.include_router(ai.router)
app.include_router(documents.router)

