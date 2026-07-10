from fastapi import APIRouter, HTTPException, Query

from app.repositories import ui_backup_repository

router = APIRouter()


@router.get("/ui-screens/{screen}")
def get_ui_screen(
    screen: str,
    koperasi_ref: str | None = Query(None),
    kode_wilayah: str | None = Query(None),
    period: str | None = Query(None),
    limit: int = Query(50),
):
    try:
        data = ui_backup_repository.get_screen(screen, koperasi_ref, kode_wilayah, period, limit)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"success": True, "data": data}


@router.get("/ui-screens/scope-candidates/list")
def get_scope_candidates(limit: int = Query(20)):
    return {"success": True, "data": ui_backup_repository.scope_candidates(limit)}
