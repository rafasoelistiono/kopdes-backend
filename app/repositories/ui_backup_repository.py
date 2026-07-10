import json
from datetime import datetime
from decimal import Decimal

from sqlalchemy import text

from app.core.config import settings
from app.core.database import execute_dashboard_query, execute_write, get_dashboard_engine, get_source_engine
from app.repositories.etl_repository import _upsert_rows, prefixed


SCREENS = ["potensi_desa", "pengurus", "kbli", "modal", "simpanan", "pinjaman", "penjualan"]


def _now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def _source_query(sql: str, params: dict | None = None) -> list[dict]:
    with get_source_engine().connect() as conn:
        conn.execute(text(f"SET LOCAL statement_timeout = {int(settings.etl_statement_timeout_ms)}"))
        result = conn.execute(text(sql), params or {})
        return [dict(row._mapping) for row in result]


def _clean_value(value):
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, default=str)
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime):
        return value.isoformat(sep=" ")
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _backup_rows(table: str, rows: list[dict], conflict_cols: list[str]) -> int:
    if not rows:
        return 0
    if settings.sync_dashboard_database_url.startswith("sqlite"):
        cols = list(rows[0].keys())
        sql = f"INSERT OR REPLACE INTO {table} ({', '.join(cols)}) VALUES ({', '.join(':' + c for c in cols)})"
        clean = [{k: _clean_value(v) for k, v in row.items()} for row in rows]
        with get_dashboard_engine().begin() as conn:
            conn.execute(text(sql), clean)
        return len(rows)
    return _upsert_rows(table, rows, conflict_cols)


def _mask_name_sql(column: str) -> str:
    return f"CASE WHEN {column} IS NULL OR {column} = '' THEN NULL ELSE left({column}, 1) || '***' END"


def _mask_phone_sql(column: str) -> str:
    return f"CASE WHEN {column} IS NULL OR {column} = '' THEN NULL ELSE '***' || right({column}, 4) END"


def ensure_ui_backup_tables() -> None:
    tables = {
        "scope": prefixed("ui_scope_candidates"),
        "potensi": prefixed("ui_potensi_desa"),
        "pengurus": prefixed("ui_pengurus"),
        "kbli": prefixed("ui_kbli"),
        "modal": prefixed("ui_modal"),
        "simpanan": prefixed("ui_simpanan_summary"),
        "pinjaman": prefixed("ui_pinjaman"),
        "penjualan": prefixed("ui_penjualan"),
    }
    ddl = [
        f"""CREATE TABLE IF NOT EXISTS {tables['scope']} (
            koperasi_ref text PRIMARY KEY, nama_koperasi text, kode_wilayah text,
            potensi_count integer DEFAULT 0, pengurus_count integer DEFAULT 0,
            pengurus_pengurus_count integer DEFAULT 0, pengurus_pengawas_count integer DEFAULT 0,
            kbli_count integer DEFAULT 0, modal_count integer DEFAULT 0, simpanan_count integer DEFAULT 0,
            pinjaman_count integer DEFAULT 0, pinjaman_active_count integer DEFAULT 0,
            match_score integer DEFAULT 0, updated_at text DEFAULT CURRENT_TIMESTAMP
        )""",
        f"""CREATE TABLE IF NOT EXISTS {tables['potensi']} (
            komoditas_ref text PRIMARY KEY, kode_wilayah text, koperasi_ref text, nama_koperasi text,
            provinsi text, kab_kota text, kecamatan text, desa_kelurahan text,
            total_penduduk integer, penduduk_laki_laki integer, penduduk_perempuan integer,
            anggaran_dana_desa real, nama_komoditas text, luas_area text, volume text,
            jumlah_sdm_terlibat real, nilai_potensi_desa real, updated_at text DEFAULT CURRENT_TIMESTAMP
        )""",
        f"""CREATE TABLE IF NOT EXISTS {tables['pengurus']} (
            pengurus_ref text PRIMARY KEY, koperasi_ref text, nama_masked text, jabatan text,
            status text, no_hp_masked text, updated_at text DEFAULT CURRENT_TIMESTAMP
        )""",
        f"""CREATE TABLE IF NOT EXISTS {tables['kbli']} (
            metric_ref text PRIMARY KEY, koperasi_ref text, kode_kbli text, nama_kbli text,
            tipe_izin_usaha text, tahun_kbli integer, updated_at text DEFAULT CURRENT_TIMESTAMP
        )""",
        f"""CREATE TABLE IF NOT EXISTS {tables['modal']} (
            modal_ref text PRIMARY KEY, koperasi_ref text, nomor_perjanjian text,
            tipe_sumber text, nama_sumber text, tipe_modal text, jumlah real,
            tanggal_diterima text, updated_at text DEFAULT CURRENT_TIMESTAMP
        )""",
        f"""CREATE TABLE IF NOT EXISTS {tables['simpanan']} (
            metric_ref text PRIMARY KEY, koperasi_ref text, periode_pembayaran text, status text,
            row_count integer DEFAULT 0, total_pembayaran real DEFAULT 0,
            paid_count integer DEFAULT 0, unpaid_count integer DEFAULT 0, updated_at text DEFAULT CURRENT_TIMESTAMP
        )""",
        f"""CREATE TABLE IF NOT EXISTS {tables['pinjaman']} (
            pengajuan_pembiayaan_ref text PRIMARY KEY, koperasi_ref text, status_permohonan text,
            nominal_permohonan real, tenor integer, tujuan_permohonan text,
            dibuat_pada text, updated_at text DEFAULT CURRENT_TIMESTAMP
        )""",
        f"""CREATE TABLE IF NOT EXISTS {tables['penjualan']} (
            transaksi_sample_id text PRIMARY KEY, koperasi_ref text, tanggal_dibuat text,
            period_month text, total_pembayaran real, status_transaksi text, metode_pembayaran text,
            total_item integer DEFAULT 0, total_volume real DEFAULT 0, produk_ringkas text DEFAULT '[]',
            updated_at text DEFAULT CURRENT_TIMESTAMP
        )""",
    ]
    for sql in ddl:
        execute_write(sql)
    for table, cols in [
        (tables["scope"], "match_score"), (tables["potensi"], "kode_wilayah"),
        (tables["potensi"], "koperasi_ref"), (tables["pengurus"], "koperasi_ref"),
        (tables["kbli"], "koperasi_ref"), (tables["modal"], "koperasi_ref"),
        (tables["simpanan"], "koperasi_ref"), (tables["pinjaman"], "koperasi_ref"),
        (tables["penjualan"], "koperasi_ref"), (tables["penjualan"], "period_month"),
    ]:
        execute_write(f"CREATE INDEX IF NOT EXISTS idx_{table}_{cols} ON {table} ({cols})")


def refresh_ui_backup() -> dict:
    ensure_ui_backup_tables()
    updated_at = _now()
    results = {
        "scope_candidates": refresh_scope_candidates(updated_at),
        "potensi_desa": refresh_potensi_desa(updated_at),
        "pengurus": refresh_pengurus(updated_at),
        "kbli": refresh_kbli(updated_at),
        "modal": refresh_modal(updated_at),
        "simpanan": refresh_simpanan(updated_at),
        "pinjaman": refresh_pinjaman(updated_at),
        "penjualan": refresh_penjualan(updated_at),
    }
    return results


def refresh_scope_candidates(updated_at: str) -> int:
    rows = _source_query("""
        WITH base AS (
          SELECT pk.koperasi_ref, pk.nama_koperasi, rkw.kode_wilayah
          FROM profil_koperasi pk
          LEFT JOIN referensi_koperasi_wilayah rkw ON rkw.koperasi_ref = pk.koperasi_ref
        ), pengurus AS (
          SELECT koperasi_ref, count(*) total,
                 count(*) FILTER (WHERE upper(coalesce(status,''))='PENGURUS') pengurus,
                 count(*) FILTER (WHERE upper(coalesce(status,''))='PENGAWAS') pengawas
          FROM pengurus_koperasi GROUP BY koperasi_ref
        ), kbli AS (SELECT koperasi_ref, count(*) total FROM kbli_koperasi GROUP BY koperasi_ref),
        modal AS (SELECT koperasi_ref, count(*) total FROM modal_koperasi GROUP BY koperasi_ref),
        simpanan AS (SELECT koperasi_ref, count(*) total FROM simpanan_anggota GROUP BY koperasi_ref),
        pinjaman AS (
          SELECT koperasi_ref, count(*) total,
                 count(*) FILTER (WHERE lower(coalesce(status_permohonan,'')) NOT IN ('lunas','selesai','rejected','ditolak')) active
          FROM pengajuan_pembiayaan GROUP BY koperasi_ref
        ), potensi AS (SELECT kode_wilayah, count(*) total FROM referensi_komoditas_desa GROUP BY kode_wilayah)
        SELECT base.koperasi_ref, base.nama_koperasi, base.kode_wilayah,
               coalesce(potensi.total,0) potensi_count, coalesce(pengurus.total,0) pengurus_count,
               coalesce(pengurus.pengurus,0) pengurus_pengurus_count,
               coalesce(pengurus.pengawas,0) pengurus_pengawas_count,
               coalesce(kbli.total,0) kbli_count, coalesce(modal.total,0) modal_count,
               coalesce(simpanan.total,0) simpanan_count, coalesce(pinjaman.total,0) pinjaman_count,
               coalesce(pinjaman.active,0) pinjaman_active_count,
               ((coalesce(potensi.total,0)=8)::int + (coalesce(pengurus.total,0)=8)::int +
                (coalesce(pengurus.pengurus,0)=5)::int + (coalesce(pengurus.pengawas,0)=3)::int +
                (coalesce(kbli.total,0)=27)::int + (coalesce(modal.total,0)=3)::int +
                (coalesce(pinjaman.total,0)=4)::int + (coalesce(pinjaman.active,0)=2)::int) match_score,
               :updated_at updated_at
        FROM base
        LEFT JOIN pengurus ON pengurus.koperasi_ref=base.koperasi_ref
        LEFT JOIN kbli ON kbli.koperasi_ref=base.koperasi_ref
        LEFT JOIN modal ON modal.koperasi_ref=base.koperasi_ref
        LEFT JOIN simpanan ON simpanan.koperasi_ref=base.koperasi_ref
        LEFT JOIN pinjaman ON pinjaman.koperasi_ref=base.koperasi_ref
        LEFT JOIN potensi ON potensi.kode_wilayah=base.kode_wilayah
    """, {"updated_at": updated_at})
    return _backup_rows(prefixed("ui_scope_candidates"), rows, ["koperasi_ref"])


def refresh_potensi_desa(updated_at: str) -> int:
    rows = _source_query("""
        SELECT k.komoditas_ref, k.kode_wilayah, rkw.koperasi_ref, pk.nama_koperasi,
               rw.provinsi, rw.kab_kota, rw.kecamatan, rw.desa_kelurahan,
               rpd.total_penduduk, rpd.penduduk_laki_laki, rpd.penduduk_perempuan,
               rpd.anggaran_dana_desa, k.nama_komoditas, k.luas_area, k.volume,
               k.jumlah_sdm_terlibat, k.nilai_potensi_desa, :updated_at updated_at
        FROM referensi_komoditas_desa k
        LEFT JOIN referensi_wilayah rw ON rw.kode_wilayah = k.kode_wilayah
        LEFT JOIN referensi_profil_desa rpd ON rpd.kode_wilayah = k.kode_wilayah
        LEFT JOIN referensi_koperasi_wilayah rkw ON rkw.kode_wilayah = k.kode_wilayah
        LEFT JOIN profil_koperasi pk ON pk.koperasi_ref = rkw.koperasi_ref
    """, {"updated_at": updated_at})
    return _backup_rows(prefixed("ui_potensi_desa"), rows, ["komoditas_ref"])


def refresh_pengurus(updated_at: str) -> int:
    rows = _source_query(f"""
        SELECT pengurus_ref, koperasi_ref, {_mask_name_sql('nama')} nama_masked,
               jabatan, status, {_mask_phone_sql('no_hp')} no_hp_masked, :updated_at updated_at
        FROM pengurus_koperasi
    """, {"updated_at": updated_at})
    return _backup_rows(prefixed("ui_pengurus"), rows, ["pengurus_ref"])


def refresh_kbli(updated_at: str) -> int:
    rows = _source_query("""
        SELECT koperasi_ref || '-' || __row_id::text metric_ref, koperasi_ref, kode_kbli,
               nama_kbli, tipe_izin_usaha, tahun_kbli, :updated_at updated_at
        FROM kbli_koperasi
    """, {"updated_at": updated_at})
    return _backup_rows(prefixed("ui_kbli"), rows, ["metric_ref"])


def refresh_modal(updated_at: str) -> int:
    rows = _source_query("""
        SELECT modal_ref, koperasi_ref, nomor_perjanjian, tipe_sumber, nama_sumber,
               tipe_modal, jumlah, tanggal_diterima, :updated_at updated_at
        FROM modal_koperasi
    """, {"updated_at": updated_at})
    return _backup_rows(prefixed("ui_modal"), rows, ["modal_ref"])


def refresh_simpanan(updated_at: str) -> int:
    rows = _source_query("""
        SELECT koperasi_ref || '-' || coalesce(periode_pembayaran, 'unknown') || '-' || coalesce(status, 'unknown') metric_ref,
               koperasi_ref, periode_pembayaran, status, count(*)::int row_count,
               coalesce(sum(jumlah_simpanan),0) total_pembayaran,
               count(*) FILTER (WHERE lower(coalesce(status,'')) IN ('paid','lunas','terbayar','success','berhasil'))::int paid_count,
               count(*) FILTER (WHERE lower(coalesce(status,'')) NOT IN ('paid','lunas','terbayar','success','berhasil'))::int unpaid_count,
               :updated_at updated_at
        FROM simpanan_anggota
        GROUP BY koperasi_ref, periode_pembayaran, status
    """, {"updated_at": updated_at})
    return _backup_rows(prefixed("ui_simpanan_summary"), rows, ["metric_ref"])


def refresh_pinjaman(updated_at: str) -> int:
    rows = _source_query("""
        SELECT pengajuan_pembiayaan_ref, koperasi_ref, status_permohonan, nominal_permohonan,
               tenor, tujuan_permohonan, dibuat_pada, :updated_at updated_at
        FROM pengajuan_pembiayaan
    """, {"updated_at": updated_at})
    return _backup_rows(prefixed("ui_pinjaman"), rows, ["pengajuan_pembiayaan_ref"])


def refresh_penjualan(updated_at: str) -> int:
    rows = _source_query("""
        WITH items AS (
            SELECT transaksi_sample_id,
                   count(*)::int AS total_item,
                   coalesce(sum(jumlah_keluar), 0) AS total_volume,
                   jsonb_agg(jsonb_build_object(
                       'produk_sample_id', produk_sample_id,
                       'nama_produk', nama_produk,
                       'jumlah_keluar', jumlah_keluar,
                       'harga', harga,
                       'total_nilai', total_nilai,
                       'status', status
                   ) ORDER BY nama_produk) AS produk_ringkas
            FROM barang_keluar_produk
            GROUP BY transaksi_sample_id
        )
        SELECT t.transaksi_sample_id, t.koperasi_ref, t.tanggal_dibuat,
               to_char(t.tanggal_dibuat, 'YYYY-MM') AS period_month,
               t.total_pembayaran, t.status_transaksi, t.metode_pembayaran,
               coalesce(items.total_item, 0) AS total_item,
               coalesce(items.total_volume, 0) AS total_volume,
               coalesce(items.produk_ringkas, '[]'::jsonb) AS produk_ringkas,
               :updated_at updated_at
        FROM transaksi_penjualan t
        LEFT JOIN items ON items.transaksi_sample_id = t.transaksi_sample_id
    """, {"updated_at": updated_at})
    return _backup_rows(prefixed("ui_penjualan"), rows, ["transaksi_sample_id"])


def get_screen(
    screen: str,
    koperasi_ref: str | None = None,
    kode_wilayah: str | None = None,
    period: str | None = None,
    limit: int = 50,
) -> dict:
    if screen not in SCREENS:
        raise ValueError(f"Unknown screen: {screen}")
    limit = max(1, min(limit, 100))
    if screen == "potensi_desa":
        where, params = [], {"limit": limit}
        if kode_wilayah:
            where.append("kode_wilayah = :kode_wilayah")
            params["kode_wilayah"] = kode_wilayah
        if koperasi_ref:
            where.append("koperasi_ref = :koperasi_ref")
            params["koperasi_ref"] = koperasi_ref
        rows = _select(prefixed("ui_potensi_desa"), where, params)
    else:
        table = {
            "pengurus": prefixed("ui_pengurus"), "kbli": prefixed("ui_kbli"),
            "modal": prefixed("ui_modal"), "simpanan": prefixed("ui_simpanan_summary"),
            "pinjaman": prefixed("ui_pinjaman"), "penjualan": prefixed("ui_penjualan"),
        }[screen]
        params = {"limit": limit}
        where = []
        if koperasi_ref:
            where.append("koperasi_ref = :koperasi_ref")
            params["koperasi_ref"] = koperasi_ref
        if period:
            where.append("period_month = :period")
            params["period"] = period
        rows = _select(table, where, params)
        if screen == "penjualan":
            for row in rows:
                if isinstance(row.get("produk_ringkas"), str):
                    row["produk_ringkas"] = json.loads(row["produk_ringkas"] or "[]")
    return {"screen": screen, "rows": rows, "count": len(rows)}


def _select(table: str, where: list[str], params: dict) -> list[dict]:
    sql = f"SELECT * FROM {table}"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " LIMIT :limit"
    return execute_dashboard_query(sql, params)


def scope_candidates(limit: int = 20) -> list[dict]:
    return execute_dashboard_query(
        f"""
        SELECT * FROM {prefixed('ui_scope_candidates')}
        ORDER BY match_score DESC, pengurus_count DESC, kbli_count DESC
        LIMIT :limit
        """,
        {"limit": max(1, min(limit, 100))},
    )


def export_mapping_json() -> dict:
    top = scope_candidates(1)
    active = top[0] if top else None
    screens = {}
    for screen in SCREENS:
        if active:
            screens[screen] = get_screen(screen, active.get("koperasi_ref"), active.get("kode_wilayah"), None, 20)
        else:
            screens[screen] = {"screen": screen, "rows": [], "count": 0}
    return {
        "active_scope_candidate": active,
        "screens": screens,
        "joins": [
            "profil_koperasi.koperasi_ref -> child tables.koperasi_ref",
            "profil_koperasi.koperasi_ref -> referensi_koperasi_wilayah.koperasi_ref -> kode_wilayah",
            "kode_wilayah -> referensi_komoditas_desa/referensi_profil_desa/referensi_wilayah",
        ],
        "sensitive_columns": {
            "pengurus_koperasi": ["no_hp", "nik", "email", "alamat", "foto_profil", "file_ktp"],
            "pengajuan_pembiayaan": ["nik", "penanggung_jawab", "nomor_penanggung_jawab", "formulir_permohonan_pembiayaan"],
            "simpanan_anggota": ["anggota_ref"],
            "modal_koperasi": ["file_perjanjian"],
        },
    }


def export_mapping_json_text() -> str:
    return json.dumps(export_mapping_json(), ensure_ascii=False, indent=2, default=str)
