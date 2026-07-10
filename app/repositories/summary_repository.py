from decimal import Decimal
import json
from typing import Any

from app.core.config import settings
from app.core.database import execute_dashboard_query
from app.repositories.etl_repository import prefixed, summary_tables
from app.repositories.schema_repository import dashboard_table_exists


def _clean(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, list):
        return [_clean(v) for v in value]
    if isinstance(value, dict):
        return {k: _clean(v) for k, v in value.items()}
    return value


def clean_row(row: dict | None) -> dict | None:
    return _clean(row) if row else None


def clean_rows(rows: list[dict]) -> list[dict]:
    return [_clean(row) for row in rows]


def limit_value(limit: int | None) -> int:
    if limit is None:
        return settings.default_page_size
    return max(1, min(limit, settings.max_page_size))


def ready(*bases: str) -> bool:
    return all(dashboard_table_exists(prefixed(base)) for base in bases)


def get_snapshot(koperasi_ref: str) -> dict | None:
    if not ready("koperasi_snapshot"):
        return None
    rows = execute_dashboard_query(
        f"SELECT * FROM {prefixed('koperasi_snapshot')} WHERE koperasi_ref = :koperasi_ref",
        {"koperasi_ref": koperasi_ref},
    )
    return clean_row(rows[0]) if rows else None


def get_koperasi_metric(koperasi_ref: str, period: str) -> dict | None:
    if not ready("koperasi_monthly_metrics"):
        return None
    rows = execute_dashboard_query(
        f"""
        SELECT * FROM {prefixed('koperasi_monthly_metrics')}
        WHERE koperasi_ref = :koperasi_ref AND period_month = :period
        """,
        {"koperasi_ref": koperasi_ref, "period": period},
    )
    return clean_row(rows[0]) if rows else None


def get_koperasi_trend(koperasi_ref: str, limit: int = 6) -> list[dict]:
    if not ready("koperasi_monthly_metrics"):
        return []
    rows = execute_dashboard_query(
        f"""
        SELECT period_month AS period, total_omzet AS value, total_transaksi
        FROM {prefixed('koperasi_monthly_metrics')}
        WHERE koperasi_ref = :koperasi_ref
        ORDER BY period_month DESC
        LIMIT :limit
        """,
        {"koperasi_ref": koperasi_ref, "limit": limit},
    )
    return list(reversed(clean_rows(rows)))


def get_products(koperasi_ref: str, period: str, limit: int | None = None) -> list[dict]:
    if not ready("product_monthly_metrics"):
        return []
    return clean_rows(execute_dashboard_query(
        f"""
        SELECT produk_ref, nama_produk, total_volume_keluar, total_nilai_keluar,
               stok_tersedia, estimated_margin, movement_status, days_without_sales
        FROM {prefixed('product_monthly_metrics')}
        WHERE koperasi_ref = :koperasi_ref AND period_month = :period
        ORDER BY total_volume_keluar DESC, total_nilai_keluar DESC
        LIMIT :limit
        """,
        {"koperasi_ref": koperasi_ref, "period": period, "limit": limit_value(limit)},
    ))


def get_rat(koperasi_ref: str) -> dict | None:
    if not ready("rat_compliance_snapshot"):
        return None
    rows = execute_dashboard_query(
        f"SELECT * FROM {prefixed('rat_compliance_snapshot')} WHERE koperasi_ref = :koperasi_ref",
        {"koperasi_ref": koperasi_ref},
    )
    return clean_row(rows[0]) if rows else None


def get_gerai(koperasi_ref: str) -> dict | None:
    if not ready("gerai_asset_snapshot"):
        return None
    rows = execute_dashboard_query(
        f"SELECT * FROM {prefixed('gerai_asset_snapshot')} WHERE koperasi_ref = :koperasi_ref",
        {"koperasi_ref": koperasi_ref},
    )
    return clean_row(rows[0]) if rows else None


def get_village(kode_wilayah: str | None) -> dict | None:
    if not kode_wilayah or not ready("village_potential_snapshot"):
        return None
    rows = execute_dashboard_query(
        f"SELECT * FROM {prefixed('village_potential_snapshot')} WHERE kode_wilayah = :kode_wilayah",
        {"kode_wilayah": kode_wilayah},
    )
    row = clean_row(rows[0]) if rows else None
    if row and isinstance(row.get("komoditas_utama"), str):
        row["komoditas_utama"] = json.loads(row["komoditas_utama"] or "[]")
    return row


def get_region(scope_level: str, scope_code: str, period: str) -> dict | None:
    if not ready("regional_monthly_metrics"):
        return None
    rows = execute_dashboard_query(
        f"""
        SELECT * FROM {prefixed('regional_monthly_metrics')}
        WHERE scope_level = :scope_level AND scope_code = :scope_code AND period_month = :period
        """,
        {"scope_level": scope_level, "scope_code": scope_code, "period": period},
    )
    return clean_row(rows[0]) if rows else None


def get_region_by_filters(filters, period: str) -> dict | None:
    if filters.scope_level and filters.scope_code:
        return get_region(filters.scope_level, filters.scope_code, period)
    if filters.kode_wilayah:
        return get_region("desa", filters.kode_wilayah, period)
    if filters.kecamatan:
        return get_region("kecamatan", filters.kecamatan, period)
    if filters.kab_kota:
        return get_region("kab_kota", filters.kab_kota, period)
    if filters.provinsi:
        return get_region("provinsi", filters.provinsi, period)
    return get_region("nasional", "nasional", period)


def get_koperasi_by_wilayah(kode_wilayah: str, limit: int | None = None) -> list[dict]:
    if not ready("koperasi_snapshot"):
        return []
    return clean_rows(execute_dashboard_query(
        f"""
        SELECT koperasi_ref, nama_koperasi, status_registrasi, latest_rat_status,
               total_anggota, total_simpanan, total_transaksi, has_npwp_doc, has_nib_doc
        FROM {prefixed('koperasi_snapshot')}
        WHERE kode_wilayah = :kode_wilayah
        ORDER BY total_transaksi DESC, nama_koperasi
        LIMIT :limit
        """,
        {"kode_wilayah": kode_wilayah, "limit": limit_value(limit)},
    ))


def get_priority_regions(period: str, limit: int | None = None) -> list[dict]:
    if not ready("regional_monthly_metrics"):
        return []
    return clean_rows(execute_dashboard_query(
        f"""
        SELECT scope_level, scope_code, provinsi, kab_kota, kecamatan, kode_wilayah,
               total_koperasi, priority_score
        FROM {prefixed('regional_monthly_metrics')}
        WHERE period_month = :period AND scope_level <> 'nasional'
        ORDER BY priority_score DESC NULLS LAST, total_koperasi DESC
        LIMIT :limit
        """,
        {"period": period, "limit": limit_value(limit)},
    ))


def get_priority_koperasi(period: str, filters, limit: int | None = None) -> list[dict]:
    if not ready("koperasi_snapshot", "koperasi_monthly_metrics", "rat_compliance_snapshot", "gerai_asset_snapshot"):
        return []
    conditions = ["km.period_month = :period"]
    params = {"period": period, "limit": limit_value(limit)}
    for field in ["provinsi", "kab_kota", "kecamatan", "kode_wilayah"]:
        value = getattr(filters, field, None)
        if value:
            conditions.append(f"ks.{field} = :{field}")
            params[field] = value
    where = " AND ".join(conditions)
    score_expr = """
        (CASE WHEN coalesce(rc.rat_verified, false) THEN 0 ELSE 25 END) +
        (CASE WHEN coalesce(km.total_transaksi, 0) = 0 THEN 20 ELSE 0 END) +
        (CASE WHEN coalesce(km.simpanan_paid_ratio, 0) < 60 THEN 15 ELSE 0 END) +
        (CASE WHEN NOT (coalesce(ks.has_npwp_doc, false) AND coalesce(ks.has_nib_doc, false) AND coalesce(ks.has_badan_hukum_doc, false)) THEN 15 ELSE 0 END) +
        (CASE WHEN coalesce(ga.gerai_aktif, 0) = 0 OR coalesce(ga.akses_listrik, false) = false OR coalesce(ga.akses_internet, false) = false THEN 10 ELSE 0 END)
    """
    capped_score = f"min(100, {score_expr})" if settings.sync_dashboard_database_url.startswith("sqlite") else f"least(100, {score_expr})"
    return clean_rows(execute_dashboard_query(
        f"""
        SELECT ks.koperasi_ref, ks.nama_koperasi, ks.kode_wilayah,
               {capped_score} AS priority_score,
               rc.latest_rat_status, km.total_transaksi, km.total_omzet, km.simpanan_paid_ratio
        FROM {prefixed('koperasi_snapshot')} ks
        JOIN {prefixed('koperasi_monthly_metrics')} km ON km.koperasi_ref = ks.koperasi_ref
        LEFT JOIN {prefixed('rat_compliance_snapshot')} rc ON rc.koperasi_ref = ks.koperasi_ref
        LEFT JOIN {prefixed('gerai_asset_snapshot')} ga ON ga.koperasi_ref = ks.koperasi_ref
        WHERE {where}
        ORDER BY priority_score DESC, km.total_omzet ASC
        LIMIT :limit
        """,
        params,
    ))


def latest_etl_at() -> str | None:
    if not ready("etl_run_log"):
        return None
    rows = execute_dashboard_query(
        f"""
        SELECT max(finished_at) AS last_etl_at
        FROM {prefixed('etl_run_log')}
        WHERE status = 'success'
        """
    )
    value = rows[0]["last_etl_at"] if rows else None
    if not value:
        return None
    return value.strftime("%Y-%m-%dT%H:%M:%SZ") if hasattr(value, "strftime") else str(value).replace(" ", "T") + "Z"


def summary_table_names() -> list[str]:
    return [name for name in summary_tables() if dashboard_table_exists(name)]


def available_periods(limit: int = 24) -> list[dict]:
    if not ready("koperasi_monthly_metrics"):
        return []
    return clean_rows(execute_dashboard_query(
        f"""
        SELECT DISTINCT period_month AS period, year, month
        FROM {prefixed('koperasi_monthly_metrics')}
        ORDER BY period_month DESC
        LIMIT :limit
        """,
        {"limit": limit},
    ))
