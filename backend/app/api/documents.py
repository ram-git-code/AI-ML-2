import uuid
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session

from app.db.postgres import get_db
from app.models.document import DocumentModel, DocumentChunkModel
from app.schemas.document import (
    DocumentResponse,
    DocumentDetailResponse,
    DocumentChunkResponse,
    DocumentQuizGenerateRequest,
)
from app.schemas.quiz import QuizResponse
from app.services.document_service import DocumentService
from app.core.logging import logger

router = APIRouter(prefix="/api/documents", tags=["Documents & PDF Quiz Engine"])

@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a PDF document. Extracts text, chunks, computes vector embeddings, and runs AI summarization & topic analysis.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF (.pdf) files are supported for document analysis and quiz generation."
        )

    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty."
        )

    logger.info(f"Received PDF upload: {file.filename} ({len(file_bytes)} bytes)")
    doc = await DocumentService.process_pdf(file_bytes=file_bytes, filename=file.filename, db=db)
    
    chunk_count = db.query(DocumentChunkModel).filter(DocumentChunkModel.document_id == doc.id).count()
    return DocumentResponse(
        id=doc.id,
        filename=doc.filename,
        title=doc.title,
        file_size_bytes=doc.file_size_bytes,
        page_count=doc.page_count,
        summary=doc.summary,
        topics=doc.topics or [],
        key_insights=doc.key_insights or [],
        estimated_difficulty=doc.estimated_difficulty,
        status=doc.status,
        created_at=doc.created_at,
        chunk_count=chunk_count
    )

@router.get("", response_model=List[DocumentResponse])
def list_documents(db: Session = Depends(get_db)):
    """
    Lists all processed PDF documents with analysis metadata.
    """
    docs = db.query(DocumentModel).order_by(DocumentModel.created_at.desc()).all()
    results = []
    for d in docs:
        chunk_count = db.query(DocumentChunkModel).filter(DocumentChunkModel.document_id == d.id).count()
        results.append(DocumentResponse(
            id=d.id,
            filename=d.filename,
            title=d.title,
            file_size_bytes=d.file_size_bytes,
            page_count=d.page_count,
            summary=d.summary,
            topics=d.topics or [],
            key_insights=d.key_insights or [],
            estimated_difficulty=d.estimated_difficulty,
            status=d.status,
            created_at=d.created_at,
            chunk_count=chunk_count
        ))
    return results

@router.get("/{document_id}", response_model=DocumentDetailResponse)
def get_document(document_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Fetches full document analysis and semantic vector chunks.
    """
    doc = db.get(DocumentModel, document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    chunks = db.query(DocumentChunkModel).filter(DocumentChunkModel.document_id == doc.id).order_by(DocumentChunkModel.chunk_index).all()
    chunk_responses = [
        DocumentChunkResponse(
            id=c.id,
            page_number=c.page_number,
            chunk_index=c.chunk_index,
            chunk_text=c.chunk_text
        )
        for c in chunks
    ]

    return DocumentDetailResponse(
        id=doc.id,
        filename=doc.filename,
        title=doc.title,
        file_size_bytes=doc.file_size_bytes,
        page_count=doc.page_count,
        summary=doc.summary,
        topics=doc.topics or [],
        key_insights=doc.key_insights or [],
        estimated_difficulty=doc.estimated_difficulty,
        status=doc.status,
        created_at=doc.created_at,
        chunk_count=len(chunk_responses),
        chunks=chunk_responses
    )

@router.post("/{document_id}/quiz", response_model=QuizResponse)
async def generate_document_quiz(
    document_id: uuid.UUID,
    req: DocumentQuizGenerateRequest,
    db: Session = Depends(get_db)
):
    """
    Generates an interactive, MCQ quiz strictly grounded in the content of the target PDF document.
    """
    return await DocumentService.generate_quiz_from_document(
        db=db,
        document_id=document_id,
        question_count=req.question_count,
        difficulty=req.difficulty,
        focus_topic=req.focus_topic
    )

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Deletes a document and all associated semantic chunks.
    """
    doc = db.get(DocumentModel, document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    db.delete(doc)
    db.commit()
    logger.info(f"Deleted document {document_id} and its associated vector chunks.")
    return None
