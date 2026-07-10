from pydantic import BaseModel
from typing import Optional


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str


class MetaTableResponse(BaseModel):
    table_name: str


class MetaColumnResponse(BaseModel):
    column_name: str
    data_type: str
    is_nullable: str


class WilayahOption(BaseModel):
    kode_wilayah: str
    provinsi: Optional[str] = None
    kab_kota: Optional[str] = None
    kecamatan: Optional[str] = None
    desa_kelurahan: Optional[str] = None


class KoperasiOption(BaseModel):
    koperasi_ref: str
    nama_koperasi: Optional[str] = None


class StatusOption(BaseModel):
    key: str
    label: str
