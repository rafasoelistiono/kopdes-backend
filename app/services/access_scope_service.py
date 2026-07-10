from fastapi import HTTPException
from app.schemas.filters import DashboardFilters


def validate_pengurus_koperasi(filters: DashboardFilters):
    if not filters.koperasi_ref:
        raise HTTPException(
            status_code=400,
            detail="pengurus_koperasi requires koperasi_ref"
        )


def validate_kepala_desa(filters: DashboardFilters):
    if not filters.kode_wilayah:
        raise HTTPException(
            status_code=400,
            detail="kepala_desa requires kode_wilayah"
        )


def validate_satgas_kdmp(filters: DashboardFilters):
    pass

