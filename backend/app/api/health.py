from fastapi import APIRouter, status, Response
from app.db.postgres import check_postgres_connection
from app.core.config import settings

router = APIRouter(tags=["Health & Infrastructure"])

@router.get(
    "/health",
    summary="General Backend Health Status",
    description="Returns basic operational health status of FastAPI backend server."
)
async def get_general_health():
    return {
        "status": "ok",
        "app_name": settings.PROJECT_NAME,
        "version": settings.VERSION
    }

@router.get(
    "/health/postgres",
    summary="PostgreSQL Connectivity Health Check",
    description="Tests live database query execution against PostgreSQL."
)
async def get_postgres_health(response: Response):
    result = check_postgres_connection()
    if result["status"] != "CONNECTED":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return result

