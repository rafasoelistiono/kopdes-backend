from typing import Optional
from fastapi import Query
from app.schemas.filters import DashboardFilters


def parse_dashboard_filters(
    koperasi_ref: Optional[str] = Query(None, description="Koperasi reference"),
    kode_wilayah: Optional[str] = Query(None, description="Wilayah code"),
    provinsi: Optional[str] = Query(None, description="Province filter"),
    kab_kota: Optional[str] = Query(None, description="City/district filter"),
    kecamatan: Optional[str] = Query(None, description="Sub-district filter"),
    desa_kelurahan: Optional[str] = Query(None, description="Village filter"),
    period: Optional[str] = Query(None, description="Period (YYYY-MM)"),
    year: Optional[int] = Query(None, description="Year"),
    month: Optional[int] = Query(None, description="Month"),
    scope_level: Optional[str] = Query(None, description="Scope level"),
    scope_code: Optional[str] = Query(None, description="Scope code"),
    limit: Optional[int] = Query(None, description="Table row limit"),
    pengajuan_pembiayaan_ref: Optional[str] = Query(None, description="Financing application reference"),
) -> DashboardFilters:
    return DashboardFilters(
        koperasi_ref=koperasi_ref,
        kode_wilayah=kode_wilayah,
        provinsi=provinsi,
        kab_kota=kab_kota,
        kecamatan=kecamatan,
        desa_kelurahan=desa_kelurahan,
        period=period,
        year=year,
        month=month,
        scope_level=scope_level,
        scope_code=scope_code,
        limit=limit,
        pengajuan_pembiayaan_ref=pengajuan_pembiayaan_ref,
    )
