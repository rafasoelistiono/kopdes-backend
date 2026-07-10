from app.core.config import settings
from app.repositories import summary_repository
from app.schemas.filters import DashboardFilters
from app.services.dashboard_common_service import build_dashboard_base, add_kpi, add_section, add_chart, add_table, finalize
from app.services.data_freshness_service import get_data_freshness
from app.utils.response import make_chart, make_kpi, make_table


DASHBOARD_KEY = "satgas-kdmp"
DASHBOARD_TITLE = "KDMP Regional Monitoring & Priority"
ROLE = "satgas_kdmp"


def build_satgas_dashboard(filters: DashboardFilters) -> dict:
    period = filters.period or (f"{filters.year}-{filters.month:02d}" if filters.year and filters.month else settings.default_period)
    region = summary_repository.get_region_by_filters(filters, period) or {}
    priority_regions = summary_repository.get_priority_regions(period, filters.limit)
    priority_koperasi = summary_repository.get_priority_koperasi(period, filters, filters.limit)
    warnings = [] if region else [f"Regional summary not found for period {period}"]
    scope_level = filters.scope_level or ("desa" if filters.kode_wilayah else "nasional")
    scope_code = filters.scope_code or filters.kode_wilayah or "nasional"
    base = build_dashboard_base(
        DASHBOARD_KEY,
        DASHBOARD_TITLE,
        ROLE,
        {"koperasi_ref": None, "kode_wilayah": filters.kode_wilayah, "scope_level": scope_level, "scope_code": scope_code},
        {**filters.model_dump(), "period": period},
        [],
        warnings,
        summary_repository.summary_table_names(),
        get_data_freshness(),
    )

    for section in [
        "regional_coverage", "account_legality_summary", "economic_impact", "rat_activity",
        "savings_summary", "gerai_readiness", "asset_development", "financing_summary",
        "partnership_summary", "priority_region_table", "priority_koperasi_table",
    ]:
        add_section(base, section)

    add_kpi(base, make_kpi("total_koperasi", "Total Koperasi", region.get("total_koperasi", 0)))
    add_kpi(base, make_kpi("koperasi_memiliki_nib", "Koperasi Memiliki NIB", region.get("koperasi_has_nib", 0)))
    add_kpi(base, make_kpi("koperasi_memiliki_npwp", "Koperasi Memiliki NPWP", region.get("koperasi_has_npwp", 0)))
    add_kpi(base, make_kpi("total_simpanan", "Total Simpanan", region.get("total_simpanan", 0), "currency"))
    add_kpi(base, make_kpi("simpanan_paid_ratio", "Rasio Simpanan Terbayar", region.get("simpanan_paid_ratio", 0), "percent"))
    add_kpi(base, make_kpi("volume_transaksi", "Volume Transaksi", region.get("total_transaksi", 0)))
    add_kpi(base, make_kpi("nilai_transaksi", "Nilai Transaksi", region.get("total_omzet", 0), "currency"))
    add_kpi(base, make_kpi("total_rat", "Total RAT", region.get("total_rat", 0)))
    add_kpi(base, make_kpi("rat_draft", "RAT Draft", region.get("rat_draft", 0), status="warning"))
    add_kpi(base, make_kpi("rat_terverifikasi", "RAT Terverifikasi", region.get("rat_verified", 0), status="success"))
    add_kpi(base, make_kpi("belum_rat", "Belum RAT", region.get("belum_rat", 0), status="warning"))
    add_kpi(base, make_kpi("total_gerai", "Total Gerai", region.get("total_gerai", 0)))
    add_kpi(base, make_kpi("gerai_aktif", "Gerai Aktif", region.get("gerai_aktif", 0)))
    add_kpi(base, make_kpi("gerai_belum_aktif", "Gerai Belum Aktif", region.get("gerai_belum_aktif", 0)))
    add_kpi(base, make_kpi("pembangunan_belum_mulai", "Pembangunan Belum Mulai", region.get("pembangunan_belum_mulai", 0)))
    add_kpi(base, make_kpi("pembangunan_berjalan", "Pembangunan Berjalan", region.get("pembangunan_berjalan", 0)))
    add_kpi(base, make_kpi("pembangunan_100_persen", "Pembangunan 100%", region.get("pembangunan_selesai", 0)))
    add_kpi(base, make_kpi("total_pengajuan_pembiayaan", "Total Pengajuan Pembiayaan", region.get("total_pengajuan_pembiayaan", 0)))
    add_kpi(base, make_kpi("total_nominal_pembiayaan", "Total Nominal Pembiayaan", region.get("total_nominal_pembiayaan", 0), "currency"))
    add_kpi(base, make_kpi("kemitraan_diajukan", "Kemitraan Diajukan", region.get("total_pengajuan_kemitraan", 0)))
    add_kpi(base, make_kpi("wilayah_prioritas_pembinaan", "Wilayah Prioritas Pembinaan", len(priority_regions), status="warning" if priority_regions else "success"))

    add_chart(base, make_chart("rat_activity", "Aktivitas RAT", "bar", "status", "count", [
        {"status": "Terverifikasi", "count": region.get("rat_verified", 0)},
        {"status": "Draft", "count": region.get("rat_draft", 0)},
        {"status": "Belum", "count": region.get("belum_rat", 0)},
    ]))
    add_chart(base, make_chart("asset_development", "Pembangunan Aset", "bar", "status", "count", [
        {"status": "Belum Mulai", "count": region.get("pembangunan_belum_mulai", 0)},
        {"status": "Berjalan", "count": region.get("pembangunan_berjalan", 0)},
        {"status": "Selesai", "count": region.get("pembangunan_selesai", 0)},
    ]))
    add_chart(base, make_chart("priority_regions", "Wilayah Prioritas", "bar", "scope_code", "priority_score", priority_regions))

    add_table(base, make_table("priority_region_table", "Prioritas Wilayah Pembinaan", [
        {"key": "scope_level", "label": "Level"}, {"key": "scope_code", "label": "Kode"},
        {"key": "priority_score", "label": "Skor"}, {"key": "total_koperasi", "label": "Koperasi"},
    ], priority_regions))
    add_table(base, make_table("priority_koperasi_table", "Prioritas Koperasi", [
        {"key": "koperasi_ref", "label": "Ref"}, {"key": "nama_koperasi", "label": "Koperasi"},
        {"key": "priority_score", "label": "Skor"}, {"key": "latest_rat_status", "label": "RAT"},
        {"key": "total_omzet", "label": "Omzet"},
    ], priority_koperasi))
    return finalize(base)
