import httpx
from qdrant_client import QdrantClient
from app.core.config import settings
from app.core.logging import logger

def get_qdrant_client() -> QdrantClient:
    return QdrantClient(url=settings.QDRANT_URL)

def check_qdrant_connection() -> dict:
    """Executes a real health check against Qdrant Vector DB service."""
    try:
        # Check via httpx HTTP endpoint
        with httpx.Client(timeout=3.0) as client:
            response = client.get(f"{settings.QDRANT_URL}/healthz")
            if response.status_code == 200:
                # Also verify Qdrant Python SDK client can list collections
                q_client = get_qdrant_client()
                collections = q_client.get_collections().collections
                collection_names = [c.name for c in collections]
                return {
                    "status": "CONNECTED",
                    "url": settings.QDRANT_URL,
                    "target_collection": settings.QDRANT_COLLECTION_NAME,
                    "collection_exists": settings.QDRANT_COLLECTION_NAME in collection_names,
                    "existing_collections": collection_names,
                    "details": "Qdrant vector engine operational"
                }
        return {
            "status": "DISCONNECTED",
            "error": f"HTTP status {response.status_code}"
        }
    except Exception as e:
        logger.error(f"Qdrant connection check failed: {str(e)}")
        return {
            "status": "DISCONNECTED",
            "error": str(e)
        }
