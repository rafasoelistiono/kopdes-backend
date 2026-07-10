from fastapi import APIRouter, Query
from typing import Optional
from app.repositories import lookup_repository, summary_repository

router = APIRouter()


@router.get("/lookups/wilayah")
def get_wilayah(
    provinsi: Optional[str] = Query(None),
    kab_kota: Optional[str] = Query(None),
    kecamatan: Optional[str] = Query(None),
):
    data = lookup_repository.get_wilayah_options(provinsi, kab_kota, kecamatan)
    return {"success": True, "data": data}


@router.get("/lookups/koperasi")
def get_koperasi(
    provinsi: Optional[str] = Query(None),
    kab_kota: Optional[str] = Query(None),
    kecamatan: Optional[str] = Query(None),
    desa_kelurahan: Optional[str] = Query(None),
):
    data = lookup_repository.get_koperasi_options(provinsi, kab_kota, kecamatan, desa_kelurahan)
    return {"success": True, "data": data}


@router.get("/lookups/status-options")
def get_status_options():
    data = lookup_repository.get_status_options()
    return {"success": True, "data": data}


@router.get("/lookups/periods")
def get_periods():
    return {"success": True, "data": summary_repository.available_periods()}
