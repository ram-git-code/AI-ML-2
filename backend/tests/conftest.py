import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.postgres import SessionLocal

@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

