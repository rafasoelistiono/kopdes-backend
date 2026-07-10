from pydantic import BaseModel
from typing import Any, Optional


class TrendData(BaseModel):
    direction: str
    percentage: Optional[float] = None
    label: str


class KPIItem(BaseModel):
    key: str
    label: str
    value: Any
    formatted_value: str
    unit: str
    trend: Optional[TrendData] = None
    status: str = "neutral"


class ChartItem(BaseModel):
    key: str
    title: str
    type: str
    x_key: str
    y_key: str
    data: list[dict]


class TableColumn(BaseModel):
    key: str
    label: str


class TableItem(BaseModel):
    key: str
    title: str
    columns: list[TableColumn]
    rows: list[dict]


class ScopeInfo(BaseModel):
    koperasi_ref: Optional[str] = None
    kode_wilayah: Optional[str] = None


class FilterState(BaseModel):
    period: Optional[str] = None
    year: Optional[int] = None
    provinsi: Optional[str] = None
    kab_kota: Optional[str] = None
    kecamatan: Optional[str] = None
    desa_kelurahan: Optional[str] = None


class MetadataInfo(BaseModel):
    source_tables: list[str] = []
    generated_at: str
    data_freshness: Optional[str] = None
    warnings: list[str] = []


class DashboardResponse(BaseModel):
    success: bool
    dashboard_key: Optional[str] = None
    dashboard_title: Optional[str] = None
    role: Optional[str] = None
    scope: Optional[ScopeInfo] = None
    filters: Optional[FilterState] = None
    kpis: list[KPIItem] = []
    sections: list[str] = []
    charts: list[ChartItem] = []
    tables: list[TableItem] = []
    metadata: MetadataInfo
