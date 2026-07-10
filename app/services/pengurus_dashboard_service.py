from app.core.config import settings
from app.repositories import summary_repository
from app.schemas.filters import DashboardFilters
from app.services.dashboard_common_service import build_dashboard_base, add_kpi, add_section, add_chart, add_table, finalize
from app.services.data_freshness_service import get_data_freshness
from app.utils.date_utils import previous_period
from app.utils.number_utils import growth_percent
from app.utils.response import make_chart, make_kpi, make_table, trend


DASHBOARD_KEY = "pengurus-koperasi"
DASHBOARD_TITLE = "Cooperative Performance & Finance"
ROLE = "pengurus_koperasi"
SUMMARY_TABLES = [
    "koperasi_snapshot", "koperasi_monthly_metrics", "product_monthly_metrics",
    "rat_compliance_snapshot", "gerai_asset_snapshot", "village_potential_snapshot",
]


def _base(filters: DashboardFilters, warnings: list[str]) -> dict:
    period = filters.period or settings.default_period
    return build_dashboard_base(
        DASHBOARD_KEY,
        DASHBOARD_TITLE,
        ROLE,
        {"koperasi_ref": filters.koperasi_ref, "kode_wilayah": None, "scope_level": None, "scope_code": None},
        {**filters.model_dump(), "period": period},
        [],
        warnings,
        summary_repository.summary_table_names(),
        get_data_freshness(),
    )


def build_pengurus_dashboard(filters: DashboardFilters) -> dict:
    period = filters.period or settings.default_period
    warnings = []
    snapshot = summary_repository.get_snapshot(filters.koperasi_ref)
    metric = summary_repository.get_koperasi_metric(filters.koperasi_ref, period)
    prev = summary_repository.get_koperasi_metric(filters.koperasi_ref, previous_period(period))
    products = summary_repository.get_products(filters.koperasi_ref, period, filters.limit)
    rat = summary_repository.get_rat(filters.koperasi_ref) or {}
    gerai = summary_repository.get_gerai(filters.koperasi_ref) or {}
    village = summary_repository.get_village(snapshot.get("kode_wilayah") if snapshot else None) or {}

    if not snapshot:
        warnings.append("Summary table empty or koperasi_ref not found; slow source fallback disabled")
    if not metric:
        warnings.append(f"Monthly summary not found for period {period}")
    snapshot = snapshot or {}
    metric = metric or {}
    prev = prev or {}

    base = _base(filters, warnings)
    current_omzet = metric.get("total_omzet", 0) or 0
    previous_omzet = prev.get("total_omzet", 0) or 0
    growth = growth_percent(current_omzet, previous_omzet)
    top_product = products[0]["nama_produk"] if products else None
    dead_stock = [p for p in products if p.get("movement_status") in {"dead_stock", "slow_moving"}]
    stok_tertahan = sum((p.get("stok_tersedia") or 0) * max(p.get("estimated_margin") or 0, 0) for p in dead_stock)

    for section in [
        "business_performance", "product_performance", "inventory_optimization",
        "savings_liquidity", "capital_summary", "rat_compliance", "financing_summary",
        "gerai_asset_summary", "village_potential",
    ]:
        add_section(base, section)

    add_kpi(base, make_kpi("omzet_bulan_ini", "Omzet Bulan Ini", current_omzet, "currency"))
    add_kpi(base, make_kpi("omzet_bulan_lalu", "Omzet Bulan Lalu", previous_omzet, "currency"))
    add_kpi(base, make_kpi("growth_omzet_bulanan", "Growth Omzet Bulanan", growth, "percent", trend=trend("up" if (growth or 0) >= 0 else "down", growth, f"{growth or 0}% dari bulan lalu")))
    add_kpi(base, make_kpi("jumlah_transaksi", "Jumlah Transaksi", metric.get("total_transaksi", 0)))
    add_kpi(base, make_kpi("average_transaction_value", "Rata-rata Nilai Transaksi", metric.get("average_transaction_value", 0), "currency"))
    add_kpi(base, make_kpi("produk_terlaris", "Produk Terlaris", top_product))
    add_kpi(base, make_kpi("produk_tidak_bergerak", "Produk Tidak Bergerak", len(dead_stock), status="warning" if dead_stock else "success"))
    add_kpi(base, make_kpi("nilai_stok_tertahan", "Nilai Stok Tertahan", stok_tertahan, "currency", status="warning" if stok_tertahan else "success"))
    add_kpi(base, make_kpi("total_simpanan", "Total Simpanan", metric.get("total_simpanan", 0), "currency"))
    add_kpi(base, make_kpi("rasio_simpanan_terbayar", "Rasio Simpanan Terbayar", metric.get("simpanan_paid_ratio", 0), "percent"))
    add_kpi(base, make_kpi("total_modal", "Total Modal", metric.get("total_modal", snapshot.get("total_modal", 0)), "currency"))
    add_kpi(base, make_kpi("status_rat_terakhir", "Status RAT Terakhir", rat.get("latest_rat_status") or snapshot.get("latest_rat_status") or "Belum Ada"))
    add_kpi(base, make_kpi("status_pengajuan_pembiayaan_terakhir", "Status Pengajuan Pembiayaan", "Ada Pengajuan" if metric.get("total_pengajuan_pembiayaan", 0) else "Tidak Ada"))
    docs_complete = bool(rat.get("has_npwp_doc") and rat.get("has_nib_doc") and rat.get("has_badan_hukum_doc"))
    add_kpi(base, make_kpi("dokumen_wajib_lengkap", "Dokumen Wajib Lengkap", docs_complete, status="success" if docs_complete else "warning"))
    add_kpi(base, make_kpi("gerai_status", "Status Gerai", gerai.get("status_gerai") or snapshot.get("gerai_status") or "Belum Ada"))
    komoditas = village.get("komoditas_utama") or []
    add_kpi(base, make_kpi("potensi_desa_utama", "Potensi Desa Utama", komoditas[0].get("nama_komoditas") if komoditas else None))

    trend_rows = summary_repository.get_koperasi_trend(filters.koperasi_ref)
    add_chart(base, make_chart("omzet_trend", "Tren Omzet", "line", "period", "value", trend_rows))
    add_chart(base, make_chart("product_movement", "Pergerakan Produk", "bar", "nama_produk", "total_volume_keluar", products))
    add_chart(base, make_chart("savings_paid_unpaid", "Simpanan Paid vs Unpaid", "donut", "status", "value", [
        {"status": "paid", "value": metric.get("simpanan_paid", 0)},
        {"status": "unpaid", "value": metric.get("simpanan_unpaid", 0)},
    ]))

    add_table(base, make_table("top_products", "Produk Terlaris", [
        {"key": "nama_produk", "label": "Produk"}, {"key": "total_volume_keluar", "label": "Volume"},
        {"key": "total_nilai_keluar", "label": "Nilai"}, {"key": "movement_status", "label": "Status"},
    ], products))
    add_table(base, make_table("slow_moving_products", "Produk Tidak Bergerak", [
        {"key": "nama_produk", "label": "Produk"}, {"key": "stok_tersedia", "label": "Stok"},
        {"key": "days_without_sales", "label": "Hari Tanpa Penjualan"},
    ], dead_stock[:summary_repository.limit_value(filters.limit)]))
    add_table(base, make_table("rat_compliance", "Kepatuhan RAT", [
        {"key": "indikator", "label": "Indikator"}, {"key": "nilai", "label": "Nilai"},
    ], [
        {"indikator": "Status RAT", "nilai": rat.get("latest_rat_status")},
        {"indikator": "Skor Kepatuhan", "nilai": rat.get("compliance_score", 0)},
    ]))
    return finalize(base)
