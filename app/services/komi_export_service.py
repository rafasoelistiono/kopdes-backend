import csv
import io
from typing import Any

from app.repositories import summary_repository, ui_backup_repository
from app.schemas.filters import DashboardFilters


EXPORT_INTENTS = {
    "export_belum_rat",
    "export_prioritas_koperasi",
    "export_prioritas_wilayah",
    "export_simpanan_unpaid",
    "export_produk_lambat",
    "export_transaksi_bulan_ini",
    "export_potensi_desa",
    "export_pengurus_masked",
}

EXPORT_COLUMNS = {
    "export_belum_rat": [
        "koperasi_ref", "nama_koperasi", "kode_wilayah",
        "latest_rat_status", "total_transaksi", "total_omzet", "simpanan_paid_ratio",
    ],
    "export_prioritas_koperasi": [
        "koperasi_ref", "nama_koperasi", "kode_wilayah", "priority_score",
        "latest_rat_status", "total_transaksi", "total_omzet", "simpanan_paid_ratio",
    ],
    "export_prioritas_wilayah": [
        "scope_level", "scope_code", "provinsi", "kab_kota",
        "kecamatan", "kode_wilayah", "total_koperasi", "priority_score",
    ],
    "export_simpanan_unpaid": [
        "koperasi_ref", "periode_pembayaran", "status",
        "row_count", "total_pembayaran", "unpaid_count",
    ],
    "export_produk_lambat": [
        "koperasi_ref", "nama_produk", "stok_tersedia",
        "days_without_sales", "movement_status",
    ],
    "export_transaksi_bulan_ini": [
        "koperasi_ref", "tanggal_dibuat", "period_month",
        "total_pembayaran", "status_transaksi", "metode_pembayaran",
        "total_item", "total_volume",
    ],
    "export_potensi_desa": [
        "kode_wilayah", "koperasi_ref", "nama_koperasi",
        "provinsi", "kab_kota", "kecamatan", "desa_kelurahan",
        "nama_komoditas", "volume", "nilai_potensi_desa",
    ],
    "export_pengurus_masked": [
        "koperasi_ref", "nama_masked", "jabatan", "status", "no_hp_masked",
    ],
}

MAX_LIMIT = 1000
DEFAULT_LIMIT = 100


def parse_export_intent(message: str) -> str | None:
    text = message.lower()

    if any(w in text for w in ["belum rat", "belum_rat", "belum-rat"]):
        return "export_belum_rat"
    if any(w in text for w in ["prioritas koperasi", "koperasi prioritas"]):
        return "export_prioritas_koperasi"
    if any(w in text for w in ["prioritas wilayah", "wilayah prioritas"]):
        return "export_prioritas_wilayah"
    if any(w in text for w in ["simpanan unpaid", "simpanan belum", "unpaid simpanan"]):
        return "export_simpanan_unpaid"
    if any(w in text for w in ["produk lambat", "produk tidak", "slow moving", "stok tertahan"]):
        return "export_produk_lambat"
    if any(w in text for w in ["transaksi bulan", "transaksi ini", "penjualan bulan"]):
        return "export_transaksi_bulan_ini"
    if any(w in text for w in ["potensi desa", "komoditas desa"]):
        return "export_potensi_desa"
    if any(w in text for w in ["pengurus", "struktur pengurus"]):
        return "export_pengurus_masked"

    if any(w in text for w in ["export", "csv", "download", "buatkan csv"]):
        return None

    return None


def _safe_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "Ya" if value else "Tidak"
    if isinstance(value, (dict, list)):
        return str(value)[:100]
    return str(value)


def build_csv(intent: str, rows: list[dict], columns: list[str]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        clean = {col: _safe_str(row.get(col)) for col in columns}
        writer.writerow(clean)
    return output.getvalue()


def export_belum_rat(period: str, filters: DashboardFilters, limit: int) -> list[dict]:
    koperasi_list = summary_repository.get_priority_koperasi(period, filters, limit)
    return [
        row for row in koperasi_list
        if "belum" in str(row.get("latest_rat_status", "")).lower()
        or str(row.get("latest_rat_status", "")).lower() in ("draft", "tidak ada", "")
    ]


def export_prioritas_koperasi(period: str, filters: DashboardFilters, limit: int) -> list[dict]:
    return summary_repository.get_priority_koperasi(period, filters, limit)


def export_prioritas_wilayah(period: str, filters: DashboardFilters, limit: int) -> list[dict]:
    return summary_repository.get_priority_regions(period, limit)


def export_simpanan_unpaid(koperasi_ref: str | None, period: str, limit: int) -> list[dict]:
    if not koperasi_ref:
        candidates = ui_backup_repository.scope_candidates(1)
        koperasi_ref = candidates[0].get("koperasi_ref") if candidates else None
    if not koperasi_ref:
        return []

    data = ui_backup_repository.get_screen("simpanan", koperasi_ref, None, None, limit)
    rows = data.get("rows", [])
    return [r for r in rows if str(r.get("status", "")).lower() not in ("paid", "lunas", "terbayar", "success", "berhasil")]


def export_produk_lambat(koperasi_ref: str | None, period: str, limit: int) -> list[dict]:
    if not koperasi_ref:
        candidates = ui_backup_repository.scope_candidates(1)
        koperasi_ref = candidates[0].get("koperasi_ref") if candidates else None
    if not koperasi_ref:
        return []

    products = summary_repository.get_products(koperasi_ref, period, limit)
    return [
        p for p in products
        if p.get("movement_status") in ("dead_stock", "slow_moving")
    ]


def export_transaksi_bulan_ini(koperasi_ref: str | None, period: str, limit: int) -> list[dict]:
    if not koperasi_ref:
        candidates = ui_backup_repository.scope_candidates(1)
        koperasi_ref = candidates[0].get("koperasi_ref") if candidates else None
    if not koperasi_ref:
        return []

    data = ui_backup_repository.get_screen("penjualan", koperasi_ref, None, period, limit)
    return data.get("rows", [])


def export_potensi_desa(kode_wilayah: str | None, koperasi_ref: str | None, limit: int) -> list[dict]:
    data = ui_backup_repository.get_screen("potensi_desa", koperasi_ref, kode_wilayah, None, limit)
    return data.get("rows", [])


def export_pengurus_masked(koperasi_ref: str | None, limit: int) -> list[dict]:
    if not koperasi_ref:
        candidates = ui_backup_repository.scope_candidates(1)
        koperasi_ref = candidates[0].get("koperasi_ref") if candidates else None
    if not koperasi_ref:
        return []

    data = ui_backup_repository.get_screen("pengurus", koperasi_ref, None, None, limit)
    return data.get("rows", [])


EXPORT_HANDLERS = {
    "export_belum_rat": lambda f, period, limit: export_belum_rat(period, f, limit),
    "export_prioritas_koperasi": lambda f, period, limit: export_prioritas_koperasi(period, f, limit),
    "export_prioritas_wilayah": lambda f, period, limit: export_prioritas_wilayah(period, f, limit),
    "export_simpanan_unpaid": lambda f, period, limit: export_simpanan_unpaid(f.koperasi_ref, period, limit),
    "export_produk_lambat": lambda f, period, limit: export_produk_lambat(f.koperasi_ref, period, limit),
    "export_transaksi_bulan_ini": lambda f, period, limit: export_transaksi_bulan_ini(f.koperasi_ref, period, limit),
    "export_potensi_desa": lambda f, period, limit: export_potensi_desa(f.kode_wilayah, f.koperasi_ref, limit),
    "export_pengurus_masked": lambda f, period, limit: export_pengurus_masked(f.koperasi_ref, limit),
}


def execute_export(intent: str, filters: DashboardFilters, period: str, limit: int) -> dict:
    if intent not in EXPORT_INTENTS:
        return {
            "success": False,
            "intent": intent,
            "filename": "",
            "content_type": "text/csv",
            "csv": "",
            "row_count": 0,
            "columns": [],
            "error": f"Export intent '{intent}' tidak dikenali.",
        }

    handler = EXPORT_HANDLERS[intent]
    rows = handler(filters, period, limit)
    columns = EXPORT_COLUMNS[intent]
    csv_content = build_csv(intent, rows, columns)
    safe_period = (period or "unknown").replace("/", "-")
    filename = f"komi-{intent.replace('export_', '')}-{safe_period}.csv"

    return {
        "success": True,
        "intent": intent,
        "filename": filename,
        "content_type": "text/csv",
        "csv": csv_content,
        "row_count": len(rows),
        "columns": columns,
    }
