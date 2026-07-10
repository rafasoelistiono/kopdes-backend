from app.core.config import settings
from app.repositories import summary_repository
from app.schemas.filters import DashboardFilters
from app.services.dashboard_common_service import build_dashboard_base, add_kpi, add_section, add_chart, add_table, finalize
from app.services.data_freshness_service import get_data_freshness
from app.utils.response import make_chart, make_kpi, make_table


DASHBOARD_KEY = "kepala-desa"
DASHBOARD_TITLE = "Village Cooperative Health"
ROLE = "kepala_desa"


def build_kepala_desa_dashboard(filters: DashboardFilters) -> dict:
    period = filters.period or settings.default_period
    region = summary_repository.get_region("desa", filters.kode_wilayah, period) or {}
    village = summary_repository.get_village(filters.kode_wilayah) or {}
    koperasi = summary_repository.get_koperasi_by_wilayah(filters.kode_wilayah, filters.limit)
    warnings = [] if region else [f"Regional summary not found for desa {filters.kode_wilayah} period {period}"]
    base = build_dashboard_base(
        DASHBOARD_KEY,
        DASHBOARD_TITLE,
        ROLE,
        {"koperasi_ref": None, "kode_wilayah": filters.kode_wilayah, "scope_level": "desa", "scope_code": filters.kode_wilayah},
        {**filters.model_dump(), "period": period},
        [],
        warnings,
        summary_repository.summary_table_names(),
        get_data_freshness(),
    )
    total_penduduk = village.get("total_penduduk", 0) or 0
    total_anggota = region.get("total_anggota", 0) or 0
    ratio = round(total_anggota / total_penduduk * 100, 2) if total_penduduk else 0
    komoditas = village.get("komoditas_utama") or []

    for section in [
        "village_profile", "koperasi_coverage", "compliance_summary", "economic_activity",
        "gerai_readiness", "asset_progress", "village_potential", "financing_risk_summary",
        "koperasi_health_table",
    ]:
        add_section(base, section)

    add_kpi(base, make_kpi("total_koperasi_desa", "Total Koperasi Desa", region.get("total_koperasi", 0)))
    add_kpi(base, make_kpi("koperasi_aktif", "Koperasi Aktif", region.get("koperasi_aktif", 0)))
    add_kpi(base, make_kpi("total_anggota_agregat", "Total Anggota Agregat", total_anggota))
    add_kpi(base, make_kpi("rasio_anggota_terhadap_penduduk", "Rasio Anggota terhadap Penduduk", ratio, "percent"))
    add_kpi(base, make_kpi("total_nilai_transaksi_desa", "Total Nilai Transaksi Desa", region.get("total_omzet", 0), "currency"))
    add_kpi(base, make_kpi("koperasi_sudah_rat", "Koperasi Sudah RAT", region.get("rat_verified", 0)))
    add_kpi(base, make_kpi("koperasi_belum_rat", "Koperasi Belum RAT", region.get("belum_rat", 0), status="warning" if region.get("belum_rat", 0) else "success"))
    add_kpi(base, make_kpi("gerai_aktif", "Gerai Aktif", region.get("gerai_aktif", 0)))
    add_kpi(base, make_kpi("gerai_belum_aktif", "Gerai Belum Aktif", region.get("gerai_belum_aktif", 0)))
    add_kpi(base, make_kpi("gerai_akses_listrik", "Gerai Akses Listrik", None))
    add_kpi(base, make_kpi("gerai_akses_internet", "Gerai Akses Internet", None))
    add_kpi(base, make_kpi("pembangunan_100_persen", "Pembangunan 100%", region.get("pembangunan_selesai", 0)))
    add_kpi(base, make_kpi("potensi_komoditas_utama", "Potensi Komoditas Utama", komoditas[0].get("nama_komoditas") if komoditas else None))

    add_chart(base, make_chart("koperasi_status", "Status Koperasi", "donut", "status", "count", [
        {"status": "Aktif", "count": region.get("koperasi_aktif", 0)},
        {"status": "Lainnya", "count": max((region.get("total_koperasi", 0) or 0) - (region.get("koperasi_aktif", 0) or 0), 0)},
    ]))
    add_chart(base, make_chart("rat_status", "Status RAT", "donut", "status", "count", [
        {"status": "Terverifikasi", "count": region.get("rat_verified", 0)},
        {"status": "Draft", "count": region.get("rat_draft", 0)},
        {"status": "Belum", "count": region.get("belum_rat", 0)},
    ]))
    add_chart(base, make_chart("gerai_readiness", "Kesiapan Gerai", "bar", "status", "count", [
        {"status": "Aktif", "count": region.get("gerai_aktif", 0)},
        {"status": "Belum Aktif", "count": region.get("gerai_belum_aktif", 0)},
    ]))

    add_table(base, make_table("koperasi_health_table", "Kesehatan Koperasi", [
        {"key": "koperasi_ref", "label": "Ref"}, {"key": "nama_koperasi", "label": "Koperasi"},
        {"key": "status_registrasi", "label": "Status"}, {"key": "latest_rat_status", "label": "RAT"},
        {"key": "total_transaksi", "label": "Transaksi"},
    ], koperasi))
    add_table(base, make_table("village_potential", "Potensi Desa", [
        {"key": "nama_komoditas", "label": "Komoditas"}, {"key": "volume", "label": "Volume"},
        {"key": "nilai_potensi", "label": "Nilai Potensi"},
    ], komoditas[:summary_repository.limit_value(filters.limit)]))
    return finalize(base)
