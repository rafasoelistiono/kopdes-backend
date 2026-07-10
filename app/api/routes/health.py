from fastapi import APIRouter
from app.core.database import execute_query

router = APIRouter()


@router.get("/health")
def health_check():
    db_ok = False
    try:
        rows = execute_query("SELECT 1 AS ok")
        db_ok = len(rows) > 0
    except Exception:
        db_ok = False
    return {
        "status": "ok" if db_ok else "degraded",
        "version": "0.1.0",
        "database": "connected" if db_ok else "disconnected",
    }
