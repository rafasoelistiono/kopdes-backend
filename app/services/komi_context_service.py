from typing import Any

from app.core.config import settings
from app.repositories import ui_backup_repository
from app.schemas.filters import DashboardFilters
from app.services import (
    kepala_desa_dashboard_service,
    pengurus_dashboard_service,
    satgas_dashboard_service,
)


DASHBOARD_BUILDERS = {
    "pengurus-koperasi": pengurus_dashboard_service.build_pengurus_dashboard,
    "kepala-desa": kepala_desa_dashboard_service.build_kepala_desa_dashboard,
    "satgas-kdmp": satgas_dashboard_service.build_satgas_dashboard,
}

WHITELISTED_FACTS_PENGURUS = [
    "omzet_bulan_ini", "jumlah_transaksi", "average_transaction_value",
    "growth_omzet_bulanan", "total_simpanan", "rasio_simpanan_terbayar",
    "status_rat_terakhir", "dokumen_wajib_lengkap", "gerai_status",
    "potensi_desa_utama", "total_modal",
]

WHITELISTED_FACTS_SATGAS = [
    "total_koperasi", "koperasi_memiliki_nib", "koperasi_memiliki_npwp",
    "simpanan_paid_ratio", "volume_transaksi", "nilai_transaksi",
    "rat_terverifikasi", "belum_rat", "gerai_aktif", "gerai_belum_aktif",
    "wilayah_prioritas_pembinaan",
]

WHITELISTED_FACTS_KEPALA_DESA = [
    "total_koperasi_desa", "koperasi_aktif", "koperasi_sudah_rat",
    "koperasi_belum_rat", "total_nilai_transaksi_desa", "gerai_aktif",
    "gerai_belum_aktif", "potensi_komoditas_utama",
]

WHITELISTED_TABLES = [
    "top_products", "slow_moving_products", "priority_koperasi_table",
    "priority_region_table", "koperasi_health_table", "village_potential",
]


def _num(value: Any) -> float:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _kpis(dashboard: dict | None) -> dict[str, dict]:
    return {item.get("key"): item for item in (dashboard or {}).get("kpis", [])}


def _tables(dashboard: dict | None) -> dict[str, dict]:
    return {item.get("key"): item for item in (dashboard or {}).get("tables", [])}


def _value(kpis: dict[str, dict], key: str) -> Any:
    return (kpis.get(key) or {}).get("value")


def _formatted(kpis: dict[str, dict], key: str) -> str:
    item = kpis.get(key) or {}
    return str(item.get("formatted_value") or item.get("value") or "-")


def build_context_pack(body: Any) -> dict:
    """Build a compact, structured context pack for LLM and agent use."""
    filters = _resolve_filters(body)
    dashboard_key = _resolve_dashboard_key(body)
    dashboard = _build_dashboard(dashboard_key, filters)
    kpis = _kpis(dashboard)
    tables = _tables(dashboard)
    backup = _backup_context(filters)

    facts = _extract_facts(kpis, dashboard_key)
    table_data = _extract_tables(tables, backup)
    sources = _extract_sources(dashboard, backup)
    health = _health_score(dashboard_key, dashboard)
    alerts = _extract_alerts(kpis, dashboard_key)
    actions = _extract_actions(kpis, dashboard_key, health)

    return {
        "scope": {
            "dashboard_key": dashboard_key,
            "koperasi_ref": filters.koperasi_ref,
            "kode_wilayah": filters.kode_wilayah,
            "scope_level": filters.scope_level,
            "scope_code": filters.scope_code,
            "period": filters.period,
        },
        "health_score": health,
        "facts": facts,
        "tables": table_data,
        "alerts": alerts,
        "recommended_actions": actions,
        "sources": sources,
        "warnings": (dashboard or {}).get("metadata", {}).get("warnings") or [],
    }


def _resolve_filters(body: Any) -> DashboardFilters:
    period = getattr(body, "period", None) or settings.default_period
    koperasi_ref = getattr(body, "koperasi_ref", None) or getattr(body, "koperasi_id", None)
    kode_wilayah = getattr(body, "kode_wilayah", None)
    scope_level = getattr(body, "scope_level", None)
    scope_code = getattr(body, "scope_code", None)
    dashboard_key = getattr(body, "dashboard_key", None) or ""

    if not koperasi_ref and not kode_wilayah:
        candidates = ui_backup_repository.scope_candidates(1)
        if candidates:
            koperasi_ref = candidates[0].get("koperasi_ref")
            kode_wilayah = candidates[0].get("kode_wilayah")

    if dashboard_key == "satgas-kdmp":
        scope_level = scope_level or "nasional"
        scope_code = scope_code or "nasional"

    return DashboardFilters(
        koperasi_ref=koperasi_ref,
        kode_wilayah=kode_wilayah,
        period=period,
        scope_level=scope_level,
        scope_code=scope_code,
        limit=20,
    )


def _resolve_dashboard_key(body: Any) -> str | None:
    explicit = getattr(body, "dashboard_key", None)
    if explicit in DASHBOARD_BUILDERS:
        return explicit
    page = getattr(body, "page", "") or ""
    role = getattr(body, "role", "") or ""
    text = f"{page} {role}".lower()
    if "pengurus" in text:
        return "pengurus-koperasi"
    if "kepala-desa" in text or "kepala_desa" in text:
        return "kepala-desa"
    if "satgas" in text:
        return "satgas-kdmp"
    return None


def _build_dashboard(dashboard_key: str | None, filters: DashboardFilters) -> dict | None:
    if not dashboard_key or dashboard_key not in DASHBOARD_BUILDERS:
        return None
    try:
        return DASHBOARD_BUILDERS[dashboard_key](filters)
    except Exception:
        return None


def _backup_context(filters: DashboardFilters) -> dict:
    if not filters.koperasi_ref:
        return {"screens": {}, "sources": []}
    screens: dict[str, dict] = {}
    sources = []
    for screen in ["potensi_desa", "pengurus", "kbli", "modal", "simpanan", "pinjaman", "penjualan"]:
        try:
            data = ui_backup_repository.get_screen(
                screen,
                filters.koperasi_ref,
                filters.kode_wilayah,
                filters.period if screen == "penjualan" else None,
                20,
            )
        except Exception:
            continue
        rows = data.get("rows", [])
        screens[screen] = {
            "count": data.get("count", 0),
            "rows": rows[:5],
            "total": sum(_num(row.get("jumlah") or row.get("total_pembayaran") or row.get("nominal_permohonan")) for row in rows),
        }
        sources.append(f"ui_{screen}")
    return {"screens": screens, "sources": sources}


def _extract_facts(kpis: dict[str, dict], dashboard_key: str | None) -> list[dict]:
    whitelist = {
        "pengurus-koperasi": WHITELISTED_FACTS_PENGURUS,
        "satgas-kdmp": WHITELISTED_FACTS_SATGAS,
        "kepala-desa": WHITELISTED_FACTS_KEPALA_DESA,
    }.get(dashboard_key, [])

    facts = []
    for key in whitelist:
        item = kpis.get(key)
        if not item:
            continue
        value = item.get("value")
        facts.append({
            "key": key,
            "label": item.get("label", key),
            "value": value,
            "formatted": _formatted(kpis, key),
            "source": "dashboard_kpis",
        })
    return facts


def _extract_tables(tables: dict[str, dict], backup: dict) -> list[dict]:
    result = []
    for key in WHITELISTED_TABLES:
        item = tables.get(key)
        if item and item.get("rows"):
            result.append({
                "key": key,
                "rows": item["rows"][:5],
            })
    screens = backup.get("screens", {})
    for screen_name in ["potensi_desa", "pengurus", "penjualan"]:
        screen = screens.get(screen_name)
        if screen and screen.get("rows"):
            result.append({
                "key": f"backup_{screen_name}",
                "rows": screen["rows"][:3],
            })
    return result


def _extract_alerts(kpis: dict[str, dict], dashboard_key: str | None) -> list[dict]:
    alerts = []
    if dashboard_key == "pengurus-koperasi":
        if _num(_value(kpis, "jumlah_transaksi")) == 0:
            alerts.append({"key": "no_transactions", "message": "Transaksi bulan ini belum tercatat."})
        if _num(_value(kpis, "rasio_simpanan_terbayar")) < 60:
            alerts.append({"key": "low_savings_ratio", "message": "Rasio simpanan terbayar di bawah 60%."})
        if not _value(kpis, "dokumen_wajib_lengkap"):
            alerts.append({"key": "incomplete_docs", "message": "Dokumen wajib koperasi belum lengkap."})
    elif dashboard_key == "satgas-kdmp":
        if _num(_value(kpis, "belum_rat")) > 0:
            alerts.append({"key": "belum_rat", "message": f"{_formatted(kpis, 'belum_rat')} koperasi belum RAT di scope ini."})
        if _num(_value(kpis, "wilayah_prioritas_pembinaan")) > 0:
            alerts.append({"key": "priority_regions", "message": "Ada wilayah prioritas pembinaan."})
    elif dashboard_key == "kepala-desa":
        if _num(_value(kpis, "koperasi_belum_rat")) > 0:
            alerts.append({"key": "belum_rat", "message": f"{_formatted(kpis, 'koperasi_belum_rat')} koperasi belum RAT."})
    return alerts


def _extract_actions(kpis: dict[str, dict], dashboard_key: str | None, health: dict) -> list[str]:
    actions = []
    if dashboard_key == "pengurus-koperasi":
        if _num(_value(kpis, "jumlah_transaksi")) == 0:
            actions.append("Cek penjualan bulan berjalan dan pastikan transaksi masuk ke sistem.")
        if _num(_value(kpis, "rasio_simpanan_terbayar")) < 60:
            actions.append("Prioritaskan penagihan simpanan unpaid.")
        if not _value(kpis, "dokumen_wajib_lengkap"):
            actions.append("Lengkapi NPWP, NIB, dan badan hukum.")
        if "belum" in str(_value(kpis, "status_rat_terakhir") or "").lower():
            actions.append("Jadwalkan dan unggah dokumen RAT.")
    elif dashboard_key == "kepala-desa":
        if _num(_value(kpis, "koperasi_belum_rat")) > 0:
            actions.append("Buat daftar pembinaan koperasi yang belum RAT.")
        if _num(_value(kpis, "gerai_belum_aktif")) > 0:
            actions.append("Monitoring hambatan aktivasi gerai: listrik, internet, dan progres aset.")
    elif dashboard_key == "satgas-kdmp":
        if _num(_value(kpis, "belum_rat")) > 0:
            actions.append("Prioritaskan wilayah/koperasi dengan status belum RAT.")
        if _num(_value(kpis, "wilayah_prioritas_pembinaan")) > 0:
            actions.append("Gunakan tabel prioritas wilayah dan koperasi sebagai daftar kerja satgas.")
    if health.get("score", 0) < 60:
        actions.append("Lakukan verifikasi data dan pembinaan langsung pada indikator skor terendah.")
    return list(dict.fromkeys(actions))


def _extract_sources(dashboard: dict | None, backup: dict) -> list[str]:
    sources = []
    sources.extend((dashboard or {}).get("metadata", {}).get("summary_tables") or [])
    sources.extend(backup.get("sources", []))
    return list(dict.fromkeys(sources))


def _num_score(value: Any) -> float:
    return _num(value)


def _ratio(part: Any, total: Any) -> float:
    t = _num(total)
    return 0 if t <= 0 else max(0, min(1, _num(part) / t))


def _score_pengurus(kpis: dict[str, dict]) -> dict[str, float]:
    rat_status = str(_value(kpis, "status_rat_terakhir") or "").lower()
    return {
        "legalitas": 20 if _value(kpis, "dokumen_wajib_lengkap") else 10,
        "rat": 20 if "verified" in rat_status else 14 if "reported" in rat_status else 0,
        "simpanan": max(0, min(20, _num_score(_value(kpis, "rasio_simpanan_terbayar")) * 0.2)),
        "transaksi": 20 if _num_score(_value(kpis, "jumlah_transaksi")) > 0 else 0,
        "gerai": 10 if "aktif" in str(_value(kpis, "gerai_status") or "").lower() else 0,
        "potensi": 10 if _value(kpis, "potensi_desa_utama") else 0,
    }


def _score_satgas(kpis: dict[str, dict]) -> dict[str, float]:
    total = _value(kpis, "total_koperasi")
    return {
        "legalitas": (_ratio(_value(kpis, "koperasi_memiliki_nib"), total) + _ratio(_value(kpis, "koperasi_memiliki_npwp"), total)) * 10,
        "rat": _ratio(_value(kpis, "rat_terverifikasi"), total) * 20,
        "simpanan": max(0, min(20, _num_score(_value(kpis, "simpanan_paid_ratio")) * 0.2)),
        "transaksi": 20 if _num_score(_value(kpis, "volume_transaksi")) > 0 or _num_score(_value(kpis, "nilai_transaksi")) > 0 else 0,
        "gerai": _ratio(_value(kpis, "gerai_aktif"), total) * 10,
        "cakupan": 10 if _num_score(total) > 0 else 0,
    }


def _score_kepala_desa(kpis: dict[str, dict]) -> dict[str, float]:
    total = _value(kpis, "total_koperasi_desa")
    return {
        "cakupan": _ratio(_value(kpis, "koperasi_aktif"), total) * 20,
        "anggota": max(0, min(20, _num_score(_value(kpis, "rasio_anggota_terhadap_penduduk")) * 2)),
        "rat": _ratio(_value(kpis, "koperasi_sudah_rat"), total) * 20,
        "transaksi": 20 if _num_score(_value(kpis, "total_nilai_transaksi_desa")) > 0 else 0,
        "gerai": _ratio(_value(kpis, "gerai_aktif"), total) * 10,
        "potensi": 10 if _value(kpis, "potensi_komoditas_utama") else 0,
    }


def _health_score(key: str | None, dashboard: dict | None) -> dict:
    kpis = _kpis(dashboard)
    parts = {
        "pengurus-koperasi": _score_pengurus,
        "kepala-desa": _score_kepala_desa,
        "satgas-kdmp": _score_satgas,
    }.get(key, lambda _: {})(kpis)
    score = int(round(sum(parts.values()))) if parts else 0
    if score >= 80:
        status, label = "success", "Sehat"
    elif score >= 60:
        status, label = "warning", "Perlu Perhatian"
    else:
        status, label = "danger", "Prioritas Pembinaan"
    return {"score": score, "status": status, "label": label, "components": {k: round(v, 2) for k, v in parts.items()}}
