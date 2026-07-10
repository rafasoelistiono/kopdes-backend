from fastapi import APIRouter, HTTPException, Query

from app.core.config import settings
from app.services import etl_service

router = APIRouter()


def _enabled():
    if not settings.enable_admin_etl_endpoint:
        raise HTTPException(status_code=404, detail="ETL endpoints disabled")


@router.get("/etl/status")
def get_etl_status():
    _enabled()
    return {"success": True, "data": etl_service.status()}


@router.post("/etl/refresh-all")
def refresh_all(period: str | None = Query(None)):
    _enabled()
    return {"success": True, "data": etl_service.refresh_all(period)}


@router.post("/etl/refresh")
def refresh(job: str = Query(...), period: str | None = Query(None)):
    _enabled()
    try:
        data = etl_service.refresh(job, period)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"success": True, "data": data}
