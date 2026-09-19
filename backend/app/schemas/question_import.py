from pydantic import BaseModel


class QuestionImportResponse(BaseModel):
    job_id: str
    status: str
    imported: int
    embedded: int
    total: int
    collection: str = "postgresql"
    message: str = ""