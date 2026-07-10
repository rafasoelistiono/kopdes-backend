from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import parse_dashboard_filters
from app.schemas.filters import DashboardFilters
from app.services import (
    access_scope_service,
    pengurus_dashboard_service,
    kepala_desa_dashboard_service,
    satgas_dashboard_service,
)
from app.core.cache import dashboard_cache

router = APIRouter()

DASHBOARD_MAP = {
    "pengurus-koperasi": {
        "title": "Cooperative Performance & Finance",
        "role": "pengurus_koperasi",
        "builder": pengurus_dashboard_service.build_pengurus_dashboard,
    },
    "kepala-desa": {
        "title": "Village Cooperative Health",
        "role": "kepala_desa",
        "builder": kepala_desa_dashboard_service.build_kepala_desa_dashboard,
    },
    "satgas-kdmp": {
        "title": "KDMP Regional Monitoring & Priority",
        "role": "satgas_kdmp",
        "builder": satgas_dashboard_service.build_satgas_dashboard,
    },
}


def get_dashboard_info(dashboard_key: str):
    info = DASHBOARD_MAP.get(dashboard_key)
    if not info:
        raise HTTPException(status_code=404, detail=f"Unknown dashboard: {dashboard_key}")
    return info


def validate_scope(dashboard_key: str, filters: DashboardFilters):
    validators = {
        "pengurus-koperasi": access_scope_service.validate_pengurus_koperasi,
        "kepala-desa": access_scope_service.validate_kepala_desa,
        "satgas-kdmp": access_scope_service.validate_satgas_kdmp,
    }
    validator = validators.get(dashboard_key)
    if validator:
        validator(filters)


def _cached_dashboard(dashboard_key: str, filters: DashboardFilters):
    validate_scope(dashboard_key, filters)
    params = filters.model_dump()
    cached = dashboard_cache.get(dashboard_key, params)
    if cached is not None:
        return cached
    info = get_dashboard_info(dashboard_key)
    data = info["builder"](filters)
    dashboard_cache.set(dashboard_key, params, data)
    return data


@router.get("/dashboards/pengurus-koperasi")
def get_pengurus_koperasi(filters: DashboardFilters = Depends(parse_dashboard_filters)):
    return _cached_dashboard("pengurus-koperasi", filters)


@router.get("/dashboards/kepala-desa")
def get_kepala_desa(filters: DashboardFilters = Depends(parse_dashboard_filters)):
    return _cached_dashboard("kepala-desa", filters)


@router.get("/dashboards/satgas-kdmp")
def get_satgas_kdmp(filters: DashboardFilters = Depends(parse_dashboard_filters)):
    return _cached_dashboard("satgas-kdmp", filters)


@router.get("/dashboards/{dashboard_key}")
def get_dashboard_by_key(
    dashboard_key: str,
    filters: DashboardFilters = Depends(parse_dashboard_filters),
):
    return _cached_dashboard(dashboard_key, filters)

