from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings
from app.core.logging import logger

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_postgres_connection() -> dict:
    """Executes a real test query against PostgreSQL database."""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1")).scalar()
            if result == 1:
                return {
                    "status": "CONNECTED",
                    "url": settings.DATABASE_URL.split("@")[-1],  # Safe URL without password
                    "details": "PostgreSQL operational and responsive"
                }
            return {
                "status": "DISCONNECTED",
                "error": "Query returned unexpected result"
            }
    except Exception as e:
        logger.error(f"PostgreSQL connection check failed: {str(e)}")
        return {
            "status": "DISCONNECTED",
            "error": str(e)
        }
