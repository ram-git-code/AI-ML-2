from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from app.core.config import settings
from app.core.logging import setup_logging
from app.api import health, questions

setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="""
🎓 **AI Question Bank + RAG + AI Quiz Tutor**

Production-grade Educational Engine supporting MCQs, PYQs, Qdrant Vector Search, and RAG AI Tutor.
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
