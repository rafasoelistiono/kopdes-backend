from pydantic import BaseModel
from typing import Optional


class DashboardFilters(BaseModel):
    koperasi_ref: Optional[str] = None
    kode_wilayah: Optional[str] = None
    provinsi: Optional[str] = None
    kab_kota: Optional[str] = None
    kecamatan: Optional[str] = None
    desa_kelurahan: Optional[str] = None
    period: Optional[str] = None
    year: Optional[int] = None
    month: Optional[int] = None
    scope_level: Optional[str] = None
    scope_code: Optional[str] = None
    limit: Optional[int] = None
    pengajuan_pembiayaan_ref: Optional[str] = None
