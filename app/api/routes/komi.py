import json
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.config import settings
from app.repositories import ui_backup_repository
from app.schemas.filters import DashboardFilters
from app.services import (
    kepala_desa_dashboard_service,
    komi_correlation_service,
    komi_context_service,
    komi_export_service,
    komi_llm_service,
    komi_safety_service,
    pengurus_dashboard_service,
    satgas_dashboard_service,
)

router = APIRouter()


class KomiInsightRequest(BaseModel):
    page: str = "/"
    role: str | None = None
    dashboard_key: str | None = None
    koperasi_ref: str | None = None
    koperasi_id: str | None = None
    kode_wilayah: str | None = None
    scope_level: str | None = None
    scope_code: str | None = None
    period: str | None = None
    question: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)
    requested_insights: list[str] = Field(default_factory=list)
    use_llm: bool | None = None


class KomiChatRequest(KomiInsightRequest):
    message: str
    history: list[dict[str, Any]] = Field(default_factory=list)


class KomiAgentRequest(BaseModel):
    message: str
    page: str = "/"
    role: str | None = None
    dashboard_key: str | None = None
    koperasi_ref: str | None = None
    koperasi_id: str | None = None
    kode_wilayah: str | None = None
    scope_level: str | None = None
    scope_code: str | None = None
    period: str | None = None
    mode: str = "analysis"
    use_llm: bool | None = None


class KomiExportRequest(BaseModel):
    message: str
    page: str = "/"
    role: str | None = None
    dashboard_key: str | None = None
    koperasi_ref: str | None = None
    koperasi_id: str | None = None
    kode_wilayah: str | None = None
    scope_level: str | None = None
    scope_code: str | None = None
    period: str | None = None
    format: str = "csv"
    limit: int = 100


DASHBOARD_BUILDERS = {
    "pengurus-koperasi": pengurus_dashboard_service.build_pengurus_dashboard,
    "kepala-desa": kepala_desa_dashboard_service.build_kepala_desa_dashboard,
    "satgas-kdmp": satgas_dashboard_service.build_satgas_dashboard,
}


def _dashboard_key(body: KomiInsightRequest) -> str | None:
    if body.dashboard_key in DASHBOARD_BUILDERS:
        return body.dashboard_key
    text = f"{body.page} {body.role or ''}".lower()
    if "pengurus" in text:
        return "pengurus-koperasi"
    if "kepala-desa" in text or "kepala_desa" in text:
        return "kepala-desa"
    if "satgas" in text:
        return "satgas-kdmp"
    return None


def _scope_fallback() -> dict | None:
    try:
        candidates = ui_backup_repository.scope_candidates(1)
    except Exception:
        return None
    return candidates[0] if candidates else None


def _filters(body: KomiInsightRequest, key: str | None) -> tuple[DashboardFilters, list[str]]:
    warnings = []
    period = body.period or settings.default_period
    koperasi_ref = body.koperasi_ref or body.koperasi_id
    kode_wilayah = body.kode_wilayah

    if key in {"pengurus-koperasi", "kepala-desa"} and not (koperasi_ref and kode_wilayah):
        fallback = _scope_fallback()
        if fallback:
            koperasi_ref = koperasi_ref or fallback.get("koperasi_ref")
            kode_wilayah = kode_wilayah or fallback.get("kode_wilayah")
            warnings.append("Scope tidak dikirim; KOMI memakai kandidat data backup terbaik.")

    scope_level = body.scope_level
    scope_code = body.scope_code
    if key == "satgas-kdmp":
        scope_level = scope_level or "nasional"
        scope_code = scope_code or "nasional"

    return DashboardFilters(
        koperasi_ref=koperasi_ref,
        kode_wilayah=kode_wilayah,
        period=period,
        scope_level=scope_level,
        scope_code=scope_code,
        limit=20,
    ), warnings


def _num(value: Any) -> float:
    if isinstance(value, bool):
        return 1 if value else 0
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0


def _kpis(dashboard: dict | None) -> dict[str, dict]:
    return {item.get("key"): item for item in (dashboard or {}).get("kpis", [])}


def _tables(dashboard: dict | None) -> dict[str, dict]:
    return {item.get("key"): item for item in (dashboard or {}).get("tables", [])}


def _value(kpis: dict[str, dict], key: str) -> Any:
    return (kpis.get(key) or {}).get("value")


def _formatted(kpis: dict[str, dict], key: str) -> str:
    item = kpis.get(key) or {}
    return str(item.get("formatted_value") or item.get("value") or "-")


def _ratio(part: Any, total: Any) -> float:
    total_num = _num(total)
    return 0 if total_num <= 0 else max(0, min(1, _num(part) / total_num))


def _status(score: int) -> tuple[str, str]:
    if score >= 80:
        return "success", "Sehat"
    if score >= 60:
        return "warning", "Perlu Perhatian"
    return "danger", "Prioritas Pembinaan"


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
            "total": sum(_num(row.get("jumlah") or row.get("total_pembayaran") or row.get("nominal_permohonan")) for row in rows),
        }
        sources.append(f"ui_{screen}")
    return {"screens": screens, "sources": sources}


def _score_pengurus(kpis: dict[str, dict]) -> dict[str, float]:
    rat_status = str(_value(kpis, "status_rat_terakhir") or "").lower()
    return {
        "legalitas": 20 if _value(kpis, "dokumen_wajib_lengkap") else 10,
        "rat": 20 if "verified" in rat_status else 14 if "reported" in rat_status else 0,
        "simpanan": max(0, min(20, _num(_value(kpis, "rasio_simpanan_terbayar")) * 0.2)),
        "transaksi": 20 if _num(_value(kpis, "jumlah_transaksi")) > 0 else 0,
        "gerai": 10 if "aktif" in str(_value(kpis, "gerai_status") or "").lower() else 0,
        "potensi": 10 if _value(kpis, "potensi_desa_utama") else 0,
    }


def _score_kepala_desa(kpis: dict[str, dict]) -> dict[str, float]:
    total = _value(kpis, "total_koperasi_desa")
    return {
        "cakupan": _ratio(_value(kpis, "koperasi_aktif"), total) * 20,
        "anggota": max(0, min(20, _num(_value(kpis, "rasio_anggota_terhadap_penduduk")) * 2)),
        "rat": _ratio(_value(kpis, "koperasi_sudah_rat"), total) * 20,
        "transaksi": 20 if _num(_value(kpis, "total_nilai_transaksi_desa")) > 0 else 0,
        "gerai": _ratio(_value(kpis, "gerai_aktif"), total) * 10,
        "potensi": 10 if _value(kpis, "potensi_komoditas_utama") else 0,
    }


def _score_satgas(kpis: dict[str, dict]) -> dict[str, float]:
    total = _value(kpis, "total_koperasi")
    return {
        "legalitas": (_ratio(_value(kpis, "koperasi_memiliki_nib"), total) + _ratio(_value(kpis, "koperasi_memiliki_npwp"), total)) * 10,
        "rat": _ratio(_value(kpis, "rat_terverifikasi"), total) * 20,
        "simpanan": max(0, min(20, _num(_value(kpis, "simpanan_paid_ratio")) * 0.2)),
        "transaksi": 20 if _num(_value(kpis, "volume_transaksi")) > 0 or _num(_value(kpis, "nilai_transaksi")) > 0 else 0,
        "gerai": _ratio(_value(kpis, "gerai_aktif"), total) * 10,
        "cakupan": 10 if _num(total) > 0 else 0,
    }


def _health_score(key: str | None, dashboard: dict | None) -> dict:
    kpis = _kpis(dashboard)
    parts = {
        "pengurus-koperasi": _score_pengurus,
        "kepala-desa": _score_kepala_desa,
        "satgas-kdmp": _score_satgas,
    }.get(key, lambda _kpis: {})(kpis)
    score = int(round(sum(parts.values()))) if parts else 0
    status, label = _status(score)
    return {"score": score, "status": status, "label": label, "components": {k: round(v, 2) for k, v in parts.items()}}


def _alerts_and_actions(key: str | None, dashboard: dict | None, health: dict) -> tuple[list[str], list[str]]:
    kpis = _kpis(dashboard)
    alerts: list[str] = []
    actions: list[str] = []

    metadata = (dashboard or {}).get("metadata", {})
    freshness = metadata.get("data_freshness") or {}
    if freshness.get("is_stale"):
        alerts.append("Data dashboard stale; insight perlu dilihat sebagai indikasi sementara.")
        actions.append("Jalankan ETL refresh sebelum mengambil keputusan final.")
    alerts.extend(metadata.get("warnings") or [])

    if key == "pengurus-koperasi":
        if _num(_value(kpis, "jumlah_transaksi")) == 0:
            alerts.append("Transaksi bulan ini belum tercatat.")
            actions.append("Cek penjualan bulan berjalan dan pastikan transaksi masuk ke sistem.")
        if _num(_value(kpis, "rasio_simpanan_terbayar")) < 60:
            alerts.append("Rasio simpanan terbayar di bawah 60%.")
            actions.append("Prioritaskan penagihan simpanan unpaid.")
        if not _value(kpis, "dokumen_wajib_lengkap"):
            alerts.append("Dokumen wajib koperasi belum lengkap.")
            actions.append("Lengkapi NPWP, NIB, dan badan hukum.")
        if "belum" in str(_value(kpis, "status_rat_terakhir") or "").lower():
            alerts.append("RAT terakhir belum tersedia.")
            actions.append("Jadwalkan dan unggah dokumen RAT.")

    if key == "kepala-desa":
        if _num(_value(kpis, "koperasi_belum_rat")) > 0:
            alerts.append(f"{_formatted(kpis, 'koperasi_belum_rat')} koperasi belum RAT.")
            actions.append("Buat daftar pembinaan koperasi yang belum RAT.")
        if _num(_value(kpis, "gerai_belum_aktif")) > 0:
            alerts.append(f"{_formatted(kpis, 'gerai_belum_aktif')} gerai belum aktif.")
            actions.append("Monitoring hambatan aktivasi gerai: listrik, internet, dan progres aset.")

    if key == "satgas-kdmp":
        if _num(_value(kpis, "belum_rat")) > 0:
            alerts.append(f"{_formatted(kpis, 'belum_rat')} koperasi belum RAT di scope ini.")
            actions.append("Prioritaskan wilayah/koperasi dengan status belum RAT.")
        if _num(_value(kpis, "wilayah_prioritas_pembinaan")) > 0:
            alerts.append("Ada wilayah prioritas pembinaan.")
            actions.append("Gunakan tabel prioritas wilayah dan koperasi sebagai daftar kerja satgas.")

    if health["score"] < 60:
        actions.append("Lakukan verifikasi data dan pembinaan langsung pada indikator skor terendah.")
    return list(dict.fromkeys(alerts)), list(dict.fromkeys(actions))


def _insights(key: str | None, dashboard: dict | None, health: dict, backup: dict) -> list[dict]:
    kpis = _kpis(dashboard)
    screens = backup.get("screens", {})
    result = [
        {
            "type": "health_koperasi",
            "title": "Health Koperasi",
            "message": f"Skor health {health['score']} ({health['label']}). Komponen terendah: {', '.join(k for k, v in health.get('components', {}).items() if v <= 5) or 'tidak ada indikator kritis'}. ",
        }
    ]

    if key == "pengurus-koperasi":
        result.extend([
            {"type": "transaksi", "title": "Transaksi", "message": f"Omzet bulan ini {_formatted(kpis, 'omzet_bulan_ini')} dari {_formatted(kpis, 'jumlah_transaksi')} transaksi."},
            {"type": "rat", "title": "RAT", "message": f"Status RAT terakhir: {_formatted(kpis, 'status_rat_terakhir')}."},
            {"type": "kelembagaan", "title": "Kelembagaan", "message": f"Pengurus backup: {screens.get('pengurus', {}).get('count', 0)} baris, KBLI: {screens.get('kbli', {}).get('count', 0)} baris."},
            {"type": "potensi_desa", "title": "Potensi Desa", "message": f"Potensi utama: {_formatted(kpis, 'potensi_desa_utama')}."},
        ])
    elif key == "kepala-desa":
        result.extend([
            {"type": "rat", "title": "RAT Desa", "message": f"Koperasi sudah RAT {_formatted(kpis, 'koperasi_sudah_rat')}; belum RAT {_formatted(kpis, 'koperasi_belum_rat')}."},
            {"type": "transaksi", "title": "Aktivitas Ekonomi", "message": f"Total nilai transaksi desa {_formatted(kpis, 'total_nilai_transaksi_desa')}."},
            {"type": "potensi_desa", "title": "Potensi Desa", "message": f"Komoditas utama: {_formatted(kpis, 'potensi_komoditas_utama')}."},
        ])
    elif key == "satgas-kdmp":
        result.extend([
            {"type": "kelembagaan", "title": "Legalitas", "message": f"NIB {_formatted(kpis, 'koperasi_memiliki_nib')}, NPWP {_formatted(kpis, 'koperasi_memiliki_npwp')} dari {_formatted(kpis, 'total_koperasi')} koperasi."},
            {"type": "rat", "title": "RAT", "message": f"Terverifikasi {_formatted(kpis, 'rat_terverifikasi')}; belum RAT {_formatted(kpis, 'belum_rat')}."},
            {"type": "transaksi", "title": "Dampak Ekonomi", "message": f"Nilai transaksi {_formatted(kpis, 'nilai_transaksi')} dengan volume {_formatted(kpis, 'volume_transaksi')}."},
        ])
    return result


def _build_context(body: KomiInsightRequest) -> dict:
    key = _dashboard_key(body)
    filters, scope_warnings = _filters(body, key)
    dashboard = None
    sources: list[str] = []

    if key:
        try:
            dashboard = DASHBOARD_BUILDERS[key](filters)
            dashboard.setdefault("metadata", {}).setdefault("warnings", []).extend(scope_warnings)
            sources.extend(dashboard.get("metadata", {}).get("summary_tables", []))
        except Exception as exc:
            scope_warnings.append(f"Dashboard context gagal dibaca: {exc}")

    backup = _backup_context(filters)
    sources.extend(backup.get("sources", []))
    health = _health_score(key, dashboard)
    alerts, actions = _alerts_and_actions(key, dashboard, health)
    if scope_warnings and not dashboard:
        alerts.extend(scope_warnings)

    return {
        "key": key,
        "filters": filters,
        "dashboard": dashboard,
        "backup": backup,
        "health": health,
        "alerts": list(dict.fromkeys(alerts)),
        "actions": actions,
        "sources": list(dict.fromkeys(sources)),
    }


def _scope_payload(ctx: dict) -> dict:
    filters = ctx["filters"]
    return {
        "dashboard_key": ctx["key"],
        "koperasi_ref": filters.koperasi_ref,
        "kode_wilayah": filters.kode_wilayah,
        "scope_level": filters.scope_level,
        "scope_code": filters.scope_code,
        "period": filters.period,
    }


def _intent(message: str) -> str:
    text = message.lower()
    groups = [
        ("solusi", ["solusi", "rekomendasi", "saran", "perbaikan", "tindakan", "langkah"]),
        ("data", ["grab", "ambil data", "tampilkan data", "data terkait", "lihat data"]),
        ("rat", ["rat", "rapat anggota"]),
        ("simpanan", ["simpanan", "unpaid", "paid", "tagihan"]),
        ("transaksi", ["transaksi", "omzet", "penjualan", "atv", "pendapatan"]),
        ("produk", ["produk", "stok", "barang", "slow", "lambat", "laris"]),
        ("gerai", ["gerai", "listrik", "internet", "aset", "pembangunan"]),
        ("potensi", ["potensi", "komoditas", "desa", "peluang"]),
        ("prioritas", ["prioritas", "pembinaan", "wilayah", "koperasi mana"]),
        ("kelembagaan", ["legalitas", "dokumen", "nib", "npwp", "badan hukum", "pengurus", "kbli", "kelembagaan"]),
    ]
    for intent, words in groups:
        if any(word in text for word in words):
            return intent
    return "health"


def _supporting(kpis: dict[str, dict], keys: list[str]) -> list[dict]:
    result = []
    for key in keys:
        item = kpis.get(key)
        if item:
            result.append({"key": key, "label": item.get("label"), "value": _formatted(kpis, key)})
    return result


def _table_rows(tables: dict[str, dict], key: str, limit: int = 3) -> list[dict]:
    return (tables.get(key) or {}).get("rows", [])[:limit]


def _names(rows: list[dict], keys: list[str]) -> str:
    values = []
    for row in rows:
        for key in keys:
            if row.get(key):
                values.append(str(row[key]))
                break
    return ", ".join(values) if values else "belum ada data rinci"


def _chat_answer(intent: str, ctx: dict) -> tuple[str, list[dict], list[str]]:
    key = ctx["key"]
    dashboard = ctx["dashboard"]
    kpis = _kpis(dashboard)
    tables = _tables(dashboard)
    health = ctx["health"]
    actions = ctx["actions"]
    screens = ctx["backup"].get("screens", {})

    if intent == "health":
        low = [name for name, value in health.get("components", {}).items() if value <= 5]
        reason = ", ".join(low) if low else "tidak ada komponen kritis"
        return (
            f"Health score {health['score']}/100 ({health['label']}). Faktor terlemah: {reason}. "
            f"Alert utama: {'; '.join(ctx['alerts'][:3]) or 'tidak ada alert utama'}.",
            [{"key": "health_score", "label": "Health Score", "value": health["score"]}],
            actions,
        )

    if intent == "rat":
        keys = ["status_rat_terakhir", "koperasi_sudah_rat", "koperasi_belum_rat", "total_rat", "rat_terverifikasi", "belum_rat"]
        if key == "pengurus-koperasi":
            answer = f"Status RAT terakhir: {_formatted(kpis, 'status_rat_terakhir')}."
        elif key == "kepala-desa":
            answer = f"RAT desa: {_formatted(kpis, 'koperasi_sudah_rat')} sudah RAT, {_formatted(kpis, 'koperasi_belum_rat')} belum RAT."
        else:
            answer = f"RAT scope ini: {_formatted(kpis, 'rat_terverifikasi')} terverifikasi, {_formatted(kpis, 'belum_rat')} belum RAT."
        return answer, _supporting(kpis, keys), [a for a in actions if "RAT" in a or "rat" in a]

    if intent == "simpanan":
        keys = ["total_simpanan", "rasio_simpanan_terbayar", "simpanan_paid_ratio"]
        answer = f"Simpanan tercatat {_formatted(kpis, 'total_simpanan')}. Rasio terbayar {_formatted(kpis, 'rasio_simpanan_terbayar') if key == 'pengurus-koperasi' else _formatted(kpis, 'simpanan_paid_ratio')}."
        return answer, _supporting(kpis, keys), [a for a in actions if "simpanan" in a.lower()]

    if intent == "transaksi":
        if key == "pengurus-koperasi":
            keys = ["omzet_bulan_ini", "growth_omzet_bulanan", "jumlah_transaksi", "average_transaction_value"]
            answer = f"Omzet bulan ini {_formatted(kpis, 'omzet_bulan_ini')} dari {_formatted(kpis, 'jumlah_transaksi')} transaksi. Growth {_formatted(kpis, 'growth_omzet_bulanan')}."
        elif key == "kepala-desa":
            keys = ["total_nilai_transaksi_desa"]
            answer = f"Total nilai transaksi desa {_formatted(kpis, 'total_nilai_transaksi_desa')}."
        else:
            keys = ["nilai_transaksi", "volume_transaksi"]
            answer = f"Nilai transaksi {_formatted(kpis, 'nilai_transaksi')} dengan volume {_formatted(kpis, 'volume_transaksi')}."
        return answer, _supporting(kpis, keys), [a for a in actions if "transaksi" in a.lower() or "penjualan" in a.lower()]

    if intent == "produk":
        top = _table_rows(tables, "top_products")
        slow = _table_rows(tables, "slow_moving_products")
        answer = f"Produk teratas: {_names(top, ['nama_produk'])}. Produk lambat/stok tertahan: {_names(slow, ['nama_produk'])}."
        return answer, _supporting(kpis, ["produk_terlaris", "produk_tidak_bergerak", "nilai_stok_tertahan"]), actions

    if intent == "gerai":
        keys = ["gerai_status", "gerai_aktif", "gerai_belum_aktif", "pembangunan_100_persen", "pembangunan_berjalan"]
        if key == "pengurus-koperasi":
            answer = f"Status gerai: {_formatted(kpis, 'gerai_status')}."
        else:
            answer = f"Gerai aktif {_formatted(kpis, 'gerai_aktif')}; gerai belum aktif {_formatted(kpis, 'gerai_belum_aktif')}."
        return answer, _supporting(kpis, keys), [a for a in actions if "gerai" in a.lower() or "aset" in a.lower()]

    if intent == "potensi":
        keys = ["potensi_desa_utama", "potensi_komoditas_utama"]
        table_key = "village_potential"
        rows = _table_rows(tables, table_key)
        answer = f"Potensi utama: {_formatted(kpis, 'potensi_desa_utama') if key == 'pengurus-koperasi' else _formatted(kpis, 'potensi_komoditas_utama')}. Data backup potensi: {screens.get('potensi_desa', {}).get('count', 0)} baris. Komoditas tabel: {_names(rows, ['nama_komoditas'])}."
        return answer, _supporting(kpis, keys), actions

    if intent == "prioritas":
        rows = _table_rows(tables, "priority_koperasi_table") or _table_rows(tables, "koperasi_health_table") or _table_rows(tables, "priority_region_table")
        answer = f"Prioritas pembinaan: {_names(rows, ['nama_koperasi', 'scope_code', 'koperasi_ref'])}."
        return answer, _supporting(kpis, ["wilayah_prioritas_pembinaan", "koperasi_belum_rat", "belum_rat"]), [a for a in actions if "prioritas" in a.lower() or "pembinaan" in a.lower()]

    keys = ["dokumen_wajib_lengkap", "koperasi_memiliki_nib", "koperasi_memiliki_npwp"]
    answer = (
        f"Kelembagaan/legalitas: dokumen wajib {_formatted(kpis, 'dokumen_wajib_lengkap')}; "
        f"NIB {_formatted(kpis, 'koperasi_memiliki_nib')}; NPWP {_formatted(kpis, 'koperasi_memiliki_npwp')}. "
        f"Backup pengurus {screens.get('pengurus', {}).get('count', 0)} baris, KBLI {screens.get('kbli', {}).get('count', 0)} baris."
    )
    return answer, _supporting(kpis, keys), [a for a in actions if "dokumen" in a.lower() or "legal" in a.lower()]


def _build_deterministic_agent_answer(ctx: dict, context_pack: dict, correlations: list[dict], message: str) -> str:
    health = ctx["health"]
    alerts = ctx["alerts"]
    actions = ctx["actions"]
    facts = context_pack.get("facts", [])
    tables = context_pack.get("tables", [])

    parts = [
        f"Health score: {health['score']}/100 ({health['label']}).",
    ]

    if facts:
        fact_texts = [f"{fact.get('label')}: {fact.get('formatted') or fact.get('value')}" for fact in facts[:6]]
        parts.append("Data terkait: " + "; ".join(fact_texts) + ".")

    row_summaries = []
    for table in tables[:2]:
        rows = table.get("rows") or []
        if rows:
            row_summaries.append(f"{table.get('key')}: {len(rows)} baris tersedia")
    if row_summaries:
        parts.append("Tabel pendukung: " + "; ".join(row_summaries) + ".")

    if alerts:
        parts.append("Alert: " + "; ".join(alerts[:3]) + ".")

    if correlations:
        corr_texts = [f"- {c['title']}: {c['meaning']}" for c in correlations[:5]]
        parts.append("Korelasi ditemukan:\n" + "\n".join(corr_texts))

    if actions:
        parts.append("Rekomendasi perbaikan: " + "; ".join(actions[:5]) + ".")

    return "\n".join(parts)


def _agent_llm_prompt(user_message: str, deterministic_answer: str, context_pack: dict, correlations: list[dict]) -> str:
    context_summary = {
        "scope": context_pack.get("scope"),
        "health_score": context_pack.get("health_score"),
        "facts": context_pack.get("facts", [])[:10],
        "tables": context_pack.get("tables", [])[:3],
        "alerts": context_pack.get("alerts", [])[:5],
        "recommended_actions": context_pack.get("recommended_actions", [])[:5],
        "correlations": correlations[:5],
    }
    return (
        "Kamu KOMI, asisten insight internal SIMKOPDES.\n"
        "Tugas: jawab pertanyaan user berdasarkan CONTEXT yang diberikan.\n"
        "Aturan wajib:\n"
        "- Jawab hanya berdasarkan CONTEXT.\n"
        "- Jangan membuat angka, status, nama koperasi, atau rekomendasi baru.\n"
        "- Jika data tidak ada di CONTEXT, bilang data belum tersedia.\n"
        "- Jelaskan korelasi secara natural.\n"
        "- Jika user meminta data, tampilkan data terkait dari facts/tables secara ringkas.\n"
        "- Jika user meminta solusi, langsung beri rekomendasi perbaikan yang spesifik dari recommended_actions/correlations.\n"
        "- Jangan menjawab dengan template umum tentang ETL; gunakan data yang tersedia di CONTEXT.\n"
        "- Berikan prioritas langkah berikutnya.\n"
        "- Jawab langsung. Jangan tulis proses berpikir, analisis prompt, atau daftar aturan.\n"
        "- Jangan mulai dengan 'The user wants', 'I need', atau penjelasan instruksi.\n"
        "- Maksimal 6 kalimat.\n"
        "- Bahasa Indonesia, ringkas, actionable.\n\n"
        f"PERTANYAAN USER:\n{user_message}\n\n"
        f"JAWABAN DETERMINISTIK:\n{deterministic_answer}\n\n"
        f"CONTEXT:\n{json.dumps(context_summary, ensure_ascii=False, default=str)}"
    )


def _looks_like_prompt_leak(text: str) -> bool:
    lowered = text.lower()
    markers = [
        "the user wants",
        "i need to",
        "strict rules",
        "provided context",
        "pertanyaan user",
        "jawaban deterministik",
        "context:",
        "aturan wajib",
    ]
    return any(marker in lowered for marker in markers)


@router.post("/insight")
def komi_insight(body: KomiInsightRequest):
    ctx = _build_context(body)
    dashboard = ctx["dashboard"]
    health = ctx["health"]
    insights = _insights(ctx["key"], dashboard, health, ctx["backup"])

    title = (dashboard or {}).get("dashboard_title") or body.context.get("page_title") or "Halaman SIMKOPDES"
    summary = f"KOMI membaca {title}. Status health: {health['label']} ({health['score']}/100)."

    return {
        "summary": summary,
        "health_score": health,
        "insights": insights,
        "alerts": ctx["alerts"],
        "recommended_actions": ctx["actions"],
        "sources": ctx["sources"],
        "scope": _scope_payload(ctx),
        "generated_by": "rule",
        "llm_used": False,
        "llm_provider": settings.komi_llm_provider,
        "llm_model": settings.komi_llm_model,
    }


@router.post("/chat")
def komi_chat(body: KomiChatRequest):
    ctx = _build_context(body)
    intent = _intent(body.message)
    rule_answer, supporting_data, actions = _chat_answer(intent, ctx)
    rewrite = komi_llm_service.rewrite_answer(
        body.message,
        rule_answer,
        supporting_data,
        ctx["alerts"],
        actions,
        body.use_llm,
    )
    answer = rewrite.get("text") or rule_answer

    return {
        "answer": answer,
        "rule_answer": rule_answer,
        "intent": intent,
        "confidence": "rule",
        "supporting_data": supporting_data,
        "recommended_actions": actions,
        "sources": ctx["sources"],
        "scope": _scope_payload(ctx),
        "generated_by": rewrite["generated_by"],
        "llm_used": rewrite["llm_used"],
        "llm_provider": rewrite["llm_provider"],
        "llm_model": rewrite["llm_model"],
        "llm_error": rewrite["llm_error"],
    }


@router.post("/agent")
def komi_agent(body: KomiAgentRequest):
    context_pack = komi_context_service.build_context_pack(body)
    correlations = komi_correlation_service.build_correlations(context_pack)
    deterministic_answer = _build_deterministic_agent_answer(ctx=_build_context(body), context_pack=context_pack, correlations=correlations, message=body.message)

    redacted = komi_safety_service.redact_context_pack(context_pack)
    generated_by = "rule"
    llm_used = False
    llm_error = None
    answer = deterministic_answer

    if body.use_llm is not False and settings.komi_llm_enabled:
        try:
            prompt = _agent_llm_prompt(body.message, deterministic_answer, redacted, correlations)
            if settings.komi_llm_provider == "openrouter" and settings.komi_openrouter_api_key:
                llm_text = komi_llm_service._openrouter_generate(prompt)
                grounding_context = {**context_pack, "correlations": correlations}
                grounded = komi_safety_service.validate_grounding(llm_text, grounding_context) and not _looks_like_prompt_leak(llm_text)
                if grounded:
                    answer = llm_text
                    generated_by = "openrouter_rewrite"
                    llm_used = True
                else:
                    llm_error = "LLM response ungrounded, using deterministic answer"
            elif settings.komi_llm_provider == "gemini" and settings.komi_llm_api_key:
                llm_text = komi_llm_service._gemini_generate(prompt)
                grounding_context = {**context_pack, "correlations": correlations}
                grounded = komi_safety_service.validate_grounding(llm_text, grounding_context) and not _looks_like_prompt_leak(llm_text)
                if grounded:
                    answer = llm_text
                    generated_by = "gemini_flash_rewrite"
                    llm_used = True
                else:
                    llm_error = "LLM response ungrounded, using deterministic answer"
        except Exception as exc:
            llm_error = f"{settings.komi_llm_provider}_{type(exc).__name__}"

    safety = komi_safety_service.safety_payload(grounded=llm_error is None)
    citations = [{"source": src, "fields": []} for src in context_pack.get("sources", [])]

    return {
        "answer": answer,
        "mode": body.mode,
        "intent": _intent(body.message),
        "health_score": context_pack.get("health_score", {}),
        "correlations": correlations,
        "recommended_actions": context_pack.get("recommended_actions", []),
        "citations": citations,
        "sources": context_pack.get("sources", []),
        "safety": safety,
        "generated_by": generated_by,
        "llm_used": llm_used,
        "llm_provider": settings.komi_llm_provider,
        "llm_model": settings.komi_llm_model,
        "llm_error": llm_error,
    }


@router.post("/export")
def komi_export(body: KomiExportRequest):
    limit = max(1, min(body.limit or 100, 1000))
    period = body.period or settings.default_period

    export_intent = komi_export_service.parse_export_intent(body.message)
    if not export_intent:
        return {
            "success": False,
            "intent": None,
            "filename": "",
            "content_type": "text/csv",
            "csv": "",
            "row_count": 0,
            "columns": [],
            "error": "Permintaan export tidak dikenali. Coba: 'buatkan CSV koperasi yang belum RAT', 'export produk lambat', atau 'download simpanan unpaid'.",
            "safety": komi_safety_service.safety_payload(grounded=True),
        }

    filters = DashboardFilters(
        koperasi_ref=body.koperasi_ref or body.koperasi_id,
        kode_wilayah=body.kode_wilayah,
        scope_level=body.scope_level,
        scope_code=body.scope_code,
        period=period,
        limit=limit,
    )

    result = komi_export_service.execute_export(export_intent, filters, period, limit)

    return {
        **result,
        "safety": komi_safety_service.safety_payload(grounded=True),
    }
