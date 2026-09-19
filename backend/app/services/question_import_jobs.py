import threading
import uuid
from dataclasses import dataclass
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.postgres import SessionLocal
from app.services.question_import_service import import_questions_in_batches


@dataclass
class ImportJob:
    job_id: str
    status: str = "queued"
    total: int = 0
    imported: int = 0
    embedded: int = 0
    error: Optional[str] = None


_jobs: dict[str, ImportJob] = {}
_jobs_lock = threading.Lock()


def create_import_job(payload: dict[str, Any]) -> ImportJob:
    job = ImportJob(job_id=str(uuid.uuid4()), total=len(payload.get("Questions", [])))
    with _jobs_lock:
        _jobs[job.job_id] = job
    thread = threading.Thread(target=_run_import, args=(job.job_id, payload), daemon=True)
    thread.start()
    return job


def get_import_job(job_id: str) -> Optional[ImportJob]:
    with _jobs_lock:
        return _jobs.get(job_id)


def _run_import(job_id: str, payload: dict[str, Any]) -> None:
    job = get_import_job(job_id)
    if not job:
        return
    job.status = "processing"
    db: Session = SessionLocal()
    try:
        def update_progress(imported: int, embedded: int) -> None:
            job.imported = imported
            job.embedded = embedded

        import_questions_in_batches(db, payload, update_progress)
        job.status = "completed"
    except Exception as error:
        job.status = "failed"
        job.error = str(error)
    finally:
        db.close()