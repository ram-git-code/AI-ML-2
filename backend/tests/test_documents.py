import io
import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.document import DocumentModel, DocumentChunkModel
from app.models.enums import Difficulty

client = TestClient(app)

def _create_dummy_pdf() -> bytes:
    from pypdf import PdfWriter
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()

def test_document_list_endpoint():
    res = client.get("/api/documents")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

def test_document_not_found():
    random_id = str(uuid.uuid4())
    res = client.get(f"/api/documents/{random_id}")
    assert res.status_code == 404

def test_document_upload_non_pdf_fails():
    files = {"file": ("test.txt", b"Hello world", "text/plain")}
    res = client.post("/api/documents/upload", files=files)
    assert res.status_code == 400
    assert "Only PDF" in res.json()["detail"]

def test_document_quiz_generation_lifecycle(db):
    # Create test document directly in DB
    doc_id = uuid.uuid4()
    doc = DocumentModel(
        id=doc_id,
        filename="thermodynamics_intro.pdf",
        title="Thermodynamics Introduction",
        file_size_bytes=1024,
        page_count=2,
        summary="Covers laws of thermodynamics, heat engines, and entropy.",
        topics=["First Law of Thermodynamics", "Entropy", "Heat Engines"],
        key_insights=["Energy is conserved: dU = dQ - dW", "Entropy of isolated system increases."],
        estimated_difficulty="MEDIUM",
        status="READY"
    )
    db.add(doc)

    # Add 2 chunks
    chunk1 = DocumentChunkModel(
        id=uuid.uuid4(),
        document_id=doc_id,
        page_number=1,
        chunk_index=0,
        chunk_text="The First Law of Thermodynamics states that energy cannot be created or destroyed, only transferred or converted from one form to another. Equation: delta U = Q - W.",
        embedding=[0.1] * 768,
        embedding_model="nvidia/embed-qa-4"
    )
    chunk2 = DocumentChunkModel(
        id=uuid.uuid4(),
        document_id=doc_id,
        page_number=2,
        chunk_index=1,
        chunk_text="The Second Law of Thermodynamics introduces entropy, stating that total entropy in an isolated system always increases over time. Heat flows spontaneously from hotter to colder bodies.",
        embedding=[0.2] * 768,
        embedding_model="nvidia/embed-qa-4"
    )
    db.add(chunk1)
    db.add(chunk2)
    db.commit()

    # Get document details
    res_get = client.get(f"/api/documents/{doc_id}")
    assert res_get.status_code == 200
    data = res_get.json()
    assert data["title"] == "Thermodynamics Introduction"
    assert len(data["chunks"]) == 2

    # Generate quiz from document
    res_quiz = client.post(f"/api/documents/{doc_id}/quiz", json={
        "question_count": 2,
        "difficulty": "medium",
        "focus_topic": "First Law of Thermodynamics"
    })
    assert res_quiz.status_code == 200
    quiz_data = res_quiz.json()
    assert "id" in quiz_data
    assert "questions" in quiz_data
    assert len(quiz_data["questions"]) > 0

    # Delete document
    res_del = client.delete(f"/api/documents/{doc_id}")
    assert res_del.status_code == 204
