import io
import json
import uuid
import math
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from pypdf import PdfReader

from app.core.config import settings
from app.core.logging import logger
from app.models.document import DocumentModel, DocumentChunkModel
from app.models.quiz import QuizModel
from app.models.question import QuestionModel
from app.models.enums import Difficulty, QuestionType
from app.services.llm_service import LLMService
from app.services.question_import_service import _embed
from app.schemas.quiz import QuizResponse, QuizPublicQuestion

class DocumentService:

    @classmethod
    def _chunk_text(cls, text: str, page_num: int, chunk_size: int = 900, overlap: int = 150) -> List[Dict[str, Any]]:
        """
        Splits extracted page text into overlapping semantic windows.
        """
        cleaned = " ".join(text.split())
        if not cleaned:
            return []

        chunks = []
        start = 0
        while start < len(cleaned):
            end = min(start + chunk_size, len(cleaned))
            # Try to break on a sentence boundary or space
            if end < len(cleaned):
                last_period = cleaned.rfind(". ", start, end)
                if last_period != -1 and last_period > start + (chunk_size // 2):
                    end = last_period + 1
                else:
                    last_space = cleaned.rfind(" ", start, end)
                    if last_space != -1 and last_space > start + (chunk_size // 2):
                        end = last_space

            chunk_content = cleaned[start:end].strip()
            if len(chunk_content) > 30:  # Ignore trivial snippets
                chunks.append({
                    "page_number": page_num,
                    "chunk_text": chunk_content
                })

            if end >= len(cleaned):
                break
            start = end - overlap
            if start < 0:
                start = 0

        return chunks

    @classmethod
    async def process_pdf(cls, file_bytes: bytes, filename: str, db: Session) -> DocumentModel:
        """
        Extracts PDF text, chunks it, generates vector embeddings, runs AI analysis, and saves to PostgreSQL.
        """
        try:
            reader = PdfReader(io.BytesIO(file_bytes))
            page_count = len(reader.pages)
        except Exception as e:
            logger.error(f"Failed to read PDF file {filename}: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not parse PDF file. Ensure it is a valid, uncorrupted PDF document. Error: {str(e)}"
            )

        if page_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The uploaded PDF contains no pages."
            )

        extracted_chunks: List[Dict[str, Any]] = []
        full_text_sample = []

        for page_idx, page in enumerate(reader.pages, start=1):
            try:
                page_text = page.extract_text() or ""
                if page_text.strip():
                    if len(full_text_sample) < 5:
                        full_text_sample.append(page_text[:1200])
                    page_chunks = cls._chunk_text(page_text, page_idx)
                    extracted_chunks.extend(page_chunks)
            except Exception as extract_err:
                logger.warning(f"Error extracting text from page {page_idx}: {extract_err}")

        if not extracted_chunks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No readable text could be extracted from this PDF. (If it contains only scanned images, text OCR is required)."
            )

        doc_title = filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").title()
        sample_context = "\n\n".join(full_text_sample[:4])

        # AI Document Analysis via NVIDIA NIM
        analysis_prompt = (
            "You are a master academic document analyzer. Analyze the following excerpts from an educational document. "
            "Return ONLY a valid JSON object with the following exact keys:\n"
            "{\n"
            '  "title": "A concise, descriptive title for this document",\n'
            '  "summary": "A clear, comprehensive 2-3 paragraph executive summary of the document\'s core subject and concepts",\n'
            '  "topics": ["List", "of", "4-8", "key", "topics", "covered"],\n'
            '  "key_insights": ["Key formula or principle 1", "Important definition or rule 2", "Key takeaway 3", "Practical insight 4"],\n'
            '  "estimated_difficulty": "EASY or MEDIUM or HARD"\n'
            "}\n"
            "Return ONLY the JSON string without markdown quotes or backticks."
        )

        messages = [
            {"role": "system", "content": analysis_prompt},
            {"role": "user", "content": f"Document Filename: {filename}\n\nDocument Text Excerpt:\n{sample_context[:3500]}"}
        ]

        summary_text = f"Educational document containing {len(extracted_chunks)} sections across {page_count} pages covering {doc_title}."
        topics = [doc_title]
        key_insights = ["Covers foundational and applied principles detailed in the document."]
        difficulty = "MEDIUM"

        try:
            ai_response = await LLMService._call_nvidia(messages, temperature=0.2, max_tokens=1500)
            if ai_response:
                cleaned = ai_response.strip()
                if cleaned.startswith("```json"):
                    cleaned = cleaned[7:]
                if cleaned.startswith("```"):
                    cleaned = cleaned[3:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                parsed = json.loads(cleaned.strip())
                if "title" in parsed and parsed["title"]:
                    doc_title = parsed["title"]
                if "summary" in parsed and parsed["summary"]:
                    summary_text = parsed["summary"]
                if "topics" in parsed and isinstance(parsed["topics"], list) and parsed["topics"]:
                    topics = parsed["topics"]
                if "key_insights" in parsed and isinstance(parsed["key_insights"], list) and parsed["key_insights"]:
                    key_insights = parsed["key_insights"]
                if "estimated_difficulty" in parsed:
                    diff_val = str(parsed["estimated_difficulty"]).upper()
                    if diff_val in ("EASY", "MEDIUM", "HARD"):
                        difficulty = diff_val
        except Exception as ai_err:
            logger.warning(f"Could not complete AI document analysis: {ai_err}")

        # Create DocumentModel
        doc_model = DocumentModel(
            id=uuid.uuid4(),
            filename=filename,
            title=doc_title,
            file_size_bytes=len(file_bytes),
            page_count=page_count,
            summary=summary_text,
            topics=topics,
            key_insights=key_insights,
            estimated_difficulty=difficulty,
            status="READY"
        )
        db.add(doc_model)
        db.flush()

        # Batch embed and insert chunks
        chunk_models = []
        for idx, chunk in enumerate(extracted_chunks):
            chunk_text = chunk["chunk_text"]
            chunk_vector = _embed(chunk_text)
            chunk_m = DocumentChunkModel(
                id=uuid.uuid4(),
                document_id=doc_model.id,
                page_number=chunk["page_number"],
                chunk_index=idx,
                chunk_text=chunk_text,
                embedding=chunk_vector,
                embedding_model=settings.NVIDIA_EMBEDDING_MODEL
            )
            chunk_models.append(chunk_m)

        db.add_all(chunk_models)
        db.commit()
        db.refresh(doc_model)

        logger.info(f"Successfully processed and embedded PDF {filename} with {len(chunk_models)} chunks.")
        return doc_model

    @classmethod
    def search_document_chunks(
        cls,
        db: Session,
        document_id: uuid.UUID,
        query: str,
        limit: int = 6
    ) -> List[DocumentChunkModel]:
        """
        Retrieves the most semantically relevant chunks from the target document.
        """
        chunks = db.query(DocumentChunkModel).filter(DocumentChunkModel.document_id == document_id).all()
        if not chunks:
            return []

        query_emb = _embed(query)
        query_norm = math.sqrt(sum(x * x for x in query_emb)) or 1.0

        scored = []
        for c in chunks:
            cand = c.embedding
            if isinstance(cand, list) and len(cand) == len(query_emb):
                cand_norm = math.sqrt(sum(y * y for y in cand)) or 1.0
                dot = sum(a * b for a, b in zip(query_emb, cand))
                score = dot / (query_norm * cand_norm)
                scored.append((score, c))
            else:
                scored.append((0.0, c))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:limit]]

    @classmethod
    async def generate_quiz_from_document(
        cls,
        db: Session,
        document_id: uuid.UUID,
        question_count: int = 5,
        difficulty: str = "medium",
        focus_topic: Optional[str] = None
    ) -> QuizResponse:
        """
        Generates interactive MCQs strictly grounded in the uploaded PDF document chunks.
        Saves questions and quiz in PostgreSQL for seamless playability.
        """
        doc = db.get(DocumentModel, document_id)
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

        # Gather relevant context chunks
        if focus_topic and focus_topic.strip():
            relevant_chunks = cls.search_document_chunks(db, document_id, focus_topic.strip(), limit=8)
        else:
            chunks_all = db.query(DocumentChunkModel).filter(DocumentChunkModel.document_id == document_id).order_by(DocumentChunkModel.chunk_index).all()
            # Pick evenly distributed chunks across pages
            step = max(1, len(chunks_all) // min(question_count * 2, len(chunks_all) or 1))
            relevant_chunks = chunks_all[::step][:8] if chunks_all else []

        if not relevant_chunks:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No chunks found for this document.")

        context_sections = []
        for i, chunk in enumerate(relevant_chunks, start=1):
            context_sections.append(f"[Excerpt {i} - Page {chunk.page_number}]:\n{chunk.chunk_text}")

        context_str = "\n\n".join(context_sections)

        system_prompt = (
            "You are a master academic exam creator. Create rigorous, high-quality Multiple Choice Questions (MCQs) "
            "STRICTLY grounded in the provided document excerpts. Do not invent facts outside the text.\n"
            "Output ONLY a valid JSON array of objects. Do not include markdown formatting or extra text outside the JSON array.\n"
            "Each object MUST have the following keys:\n"
            "[\n"
            "  {\n"
            '    "question_text": "Clear question based directly on the document excerpt",\n'
            '    "options": ["A. Option 1", "B. Option 2", "C. Option 3", "D. Option 4"],\n'
            '    "correct_answer": "A",\n'
            '    "explanation": "Detailed explanation explaining why this option is correct citing the document context",\n'
            f'    "subject": "{doc.title}",\n'
            f'    "chapter": "Page reference or Section",\n'
            f'    "topic": "{focus_topic or (doc.topics[0] if doc.topics else doc.title)}",\n'
            f'    "difficulty": "{difficulty.upper() if difficulty.upper() in ["EASY", "MEDIUM", "HARD"] else "MEDIUM"}"\n'
            "  }\n"
            "]"
        )

        user_prompt = (
            f"Generate exactly {question_count} distinct multiple-choice questions from this document.\n"
            f"Document Title: '{doc.title}'\n"
            f"Difficulty: '{difficulty}'\n\n"
            f"DOCUMENT EXCERPTS:\n{context_str}\n\n"
            "Ensure options are labeled 'A. ...', 'B. ...', 'C. ...', 'D. ...' and correct_answer is just the single letter ('A', 'B', 'C', or 'D')."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        llm_reply = await LLMService._call_nvidia(messages, temperature=0.2, max_tokens=3000)
        generated_items = []
        if llm_reply:
            try:
                cleaned = llm_reply.strip()
                if cleaned.startswith("```json"):
                    cleaned = cleaned[7:]
                if cleaned.startswith("```"):
                    cleaned = cleaned[3:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                parsed = json.loads(cleaned.strip())
                if isinstance(parsed, list) and len(parsed) > 0:
                    generated_items = parsed
            except Exception as parse_err:
                logger.warning(f"Error parsing NVIDIA generated document quiz JSON: {parse_err}. Response: {llm_reply}")

        # Fallback question generation if LLM was unavailable
        if not generated_items:
            for idx, ch in enumerate(relevant_chunks[:question_count], start=1):
                snippet = ch.chunk_text[:120].strip()
                generated_items.append({
                    "question_text": f"According to page {ch.page_number} of the document, which statement is supported regarding: '{snippet}...'?",
                    "options": [
                        f"A. The document establishes this principle on Page {ch.page_number}",
                        "B. The document contradicts this statement",
                        "C. This concept is irrelevant to the document",
                        "D. None of the above"
                    ],
                    "correct_answer": "A",
                    "explanation": f"Grounded in page {ch.page_number}: {ch.chunk_text[:200]}...",
                    "subject": doc.title,
                    "chapter": f"Page {ch.page_number}",
                    "topic": doc.title,
                    "difficulty": difficulty.upper()
                })

        # Save questions into PostgreSQL
        diff_enum = Difficulty.MEDIUM
        if difficulty.upper() in Difficulty.__members__:
            diff_enum = Difficulty[difficulty.upper()]

        saved_questions: List[QuestionModel] = []
        for item in generated_items:
            q_id = uuid.uuid4()
            q_model = QuestionModel(
                id=q_id,
                question_type=QuestionType.MCQ,
                question_text=item.get("question_text", f"Question on {doc.title}"),
                options=item.get("options", ["A. 1", "B. 2", "C. 3", "D. 4"]),
                correct_answer=str(item.get("correct_answer", "A")),
                explanation=item.get("explanation", f"Based on {doc.title}"),
                subject=doc.title[:150],
                chapter=item.get("chapter", f"Doc {doc.filename}")[:150],
                topic=item.get("topic", doc.title)[:150],
                difficulty=diff_enum,
                is_pyq=False,
                embedding=_embed(item.get("question_text", "")),
                embedding_model=settings.NVIDIA_EMBEDDING_MODEL
            )
            db.add(q_model)
            saved_questions.append(q_model)

        db.flush()

        # Create QuizModel
        quiz_id = uuid.uuid4()
        quiz_model = QuizModel(
            id=quiz_id,
            title=f"DocuQuiz: {doc.title}",
            query_prompt=f"Document Quiz: {focus_topic or doc.title}",
            question_ids=[str(q.id) for q in saved_questions],
            total_questions=len(saved_questions),
            score=0,
            completed=False,
            answers={}
        )
        db.add(quiz_model)
        db.commit()
        db.refresh(quiz_model)

        quiz_questions = [
            QuizPublicQuestion(
                id=q.id,
                question_type=q.question_type,
                question_text=q.question_text,
                options=q.options,
                subject=q.subject,
                chapter=q.chapter,
                topic=q.topic,
                difficulty=q.difficulty,
                is_pyq=q.is_pyq,
            )
            for q in saved_questions
        ]

        logger.info(f"Generated Document Quiz {quiz_id} with {len(quiz_questions)} questions from {doc.filename}.")
        return QuizResponse(
            id=quiz_model.id,
            title=f"DocuQuiz: {doc.title}",
            total_questions=len(quiz_questions),
            questions=quiz_questions
        )
