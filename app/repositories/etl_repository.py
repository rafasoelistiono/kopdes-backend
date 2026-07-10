import json
import time
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from app.core.config import settings
from app.core.database import execute_dashboard_query, execute_query, execute_write, get_dashboard_engine
from app.repositories import schema_repository
from app.utils.safe_sql import safe_identifier
from sqlalchemy import text


SUMMARY_BASES = [
    "etl_run_log",
    "koperasi_snapshot",
    "koperasi_monthly_metrics",
    "product_monthly_metrics",
    "rat_compliance_snapshot",
    "gerai_asset_snapshot",
    "village_potential_snapshot",
    "regional_monthly_metrics",
]


def prefixed(base: str) -> str:
    return safe_identifier(f"{settings.table_prefix}{base}")


def summary_tables() -> list[str]:
    return [prefixed(base) for base in SUMMARY_BASES]


def _dashboard_is_sqlite() -> bool:
    return settings.sync_dashboard_database_url.startswith("sqlite")


def _execute_many(sql_statements: list[str]) -> None:
    for sql in sql_statements:
        execute_write(sql)


def _ensure_summary_tables_sqlite(t: dict[str, str]) -> None:
    _execute_many([
        f"""CREATE TABLE IF NOT EXISTS {t['etl_run_log']} (
            run_ref text PRIMARY KEY, job_name text NOT NULL, status text NOT NULL,
            started_at text DEFAULT CURRENT_TIMESTAMP, finished_at text NULL, duration_ms integer NULL,
            source_tables text DEFAULT '[]', rows_extracted integer DEFAULT 0,
            rows_upserted integer DEFAULT 0, error_message text NULL, metadata text DEFAULT '{{}}'
        )""",
        f"""CREATE TABLE IF NOT EXISTS {t['koperasi_snapshot']} (
            koperasi_ref text PRIMARY KEY, nama_koperasi text, status_registrasi text,
            bentuk_koperasi text, kategori_usaha text, pola_pengelolaan text NULL,
            kode_wilayah text, provinsi text, kab_kota text, kecamatan text, desa_kelurahan text,
            has_npwp_doc integer DEFAULT 0, has_nib_doc integer DEFAULT 0, has_badan_hukum_doc integer DEFAULT 0,
            has_bank_account integer DEFAULT 0, has_rat integer DEFAULT 0, latest_rat_status text NULL,
            has_gerai integer DEFAULT 0, gerai_status text NULL, total_anggota integer DEFAULT 0,
            total_simpanan real DEFAULT 0, total_modal real DEFAULT 0, total_transaksi real DEFAULT 0,
            last_transaction_at text NULL, updated_at text DEFAULT CURRENT_TIMESTAMP
        )""",
        f"""CREATE TABLE IF NOT EXISTS {t['koperasi_monthly_metrics']} (
            metric_ref text PRIMARY KEY, koperasi_ref text NOT NULL, period_month text NOT NULL,
            year integer NOT NULL, month integer NOT NULL, kode_wilayah text, provinsi text, kab_kota text,
            kecamatan text, desa_kelurahan text, total_omzet real DEFAULT 0, total_transaksi integer DEFAULT 0,
            total_volume_produk real DEFAULT 0, average_transaction_value real DEFAULT 0,
            total_simpanan real DEFAULT 0, simpanan_paid real DEFAULT 0, simpanan_unpaid real DEFAULT 0,
            simpanan_paid_ratio real DEFAULT 0, total_modal real DEFAULT 0,
            total_pengajuan_pembiayaan integer DEFAULT 0, total_nominal_pembiayaan real DEFAULT 0,
            total_pengajuan_kemitraan integer DEFAULT 0, created_at text DEFAULT CURRENT_TIMESTAMP,
            updated_at text DEFAULT CURRENT_TIMESTAMP, UNIQUE (koperasi_ref, period_month)
        )""",
        f"""CREATE TABLE IF NOT EXISTS {t['product_monthly_metrics']} (
            metric_ref text PRIMARY KEY, koperasi_ref text NOT NULL, period_month text NOT NULL,
            produk_ref text NULL, nama_produk text NULL, kategori_produk text NULL,
            total_volume_keluar real DEFAULT 0, total_nilai_keluar real DEFAULT 0,
            stok_tersedia real DEFAULT 0, harga_beli_avg real DEFAULT 0, harga_jual_avg real DEFAULT 0,
            estimated_margin real DEFAULT 0, last_sold_at text NULL, days_without_sales integer NULL,
            movement_status text NULL, updated_at text DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (koperasi_ref, period_month, produk_ref)
        )""",
        f"""CREATE TABLE IF NOT EXISTS {t['rat_compliance_snapshot']} (
            koperasi_ref text PRIMARY KEY, latest_rat_year integer NULL, latest_rat_status text NULL,
            rat_verified integer DEFAULT 0, rat_draft integer DEFAULT 0,
            has_laporan_posisi_keuangan integer DEFAULT 0, has_laporan_hasil_usaha integer DEFAULT 0,
            total_dokumen integer DEFAULT 0, has_npwp_doc integer DEFAULT 0, has_nib_doc integer DEFAULT 0,
            has_badan_hukum_doc integer DEFAULT 0, expired_documents_count integer DEFAULT 0,
            expired_soon_documents_count integer DEFAULT 0, compliance_score real DEFAULT 0,
            updated_at text DEFAULT CURRENT_TIMESTAMP
        )""",
        f"""CREATE TABLE IF NOT EXISTS {t['gerai_asset_snapshot']} (
            koperasi_ref text PRIMARY KEY, kode_wilayah text, status_gerai text NULL, jenis_gerai text NULL,
            akses_listrik integer NULL, akses_internet integer NULL, total_gerai integer DEFAULT 0,
            gerai_aktif integer DEFAULT 0, gerai_belum_aktif integer DEFAULT 0, asset_status text NULL,
            progres_pembangunan real DEFAULT 0, pembangunan_bucket text NULL,
            updated_at text DEFAULT CURRENT_TIMESTAMP
        )""",
        f"""CREATE TABLE IF NOT EXISTS {t['village_potential_snapshot']} (
            kode_wilayah text PRIMARY KEY, provinsi text, kab_kota text, kecamatan text, desa_kelurahan text,
            total_penduduk integer DEFAULT 0, jumlah_keluarga integer DEFAULT 0,
            anggaran_dana_desa real DEFAULT 0, luas_wilayah real DEFAULT 0,
            komoditas_utama text DEFAULT '[]', total_potensi real DEFAULT 0,
            updated_at text DEFAULT CURRENT_TIMESTAMP
        )""",
        f"""CREATE TABLE IF NOT EXISTS {t['regional_monthly_metrics']} (
            metric_ref text PRIMARY KEY, scope_level text NOT NULL, scope_code text NOT NULL,
            provinsi text NULL, kab_kota text NULL, kecamatan text NULL, desa_kelurahan text NULL,
            kode_wilayah text NULL, period_month text NOT NULL, year integer NOT NULL, month integer NOT NULL,
            total_koperasi integer DEFAULT 0, koperasi_aktif integer DEFAULT 0,
            koperasi_has_npwp integer DEFAULT 0, koperasi_has_nib integer DEFAULT 0,
            total_anggota integer DEFAULT 0, total_simpanan real DEFAULT 0,
            total_simpanan_paid real DEFAULT 0, simpanan_paid_ratio real DEFAULT 0,
            total_omzet real DEFAULT 0, total_transaksi integer DEFAULT 0, total_volume_produk real DEFAULT 0,
            total_rat integer DEFAULT 0, rat_verified integer DEFAULT 0, rat_draft integer DEFAULT 0,
            belum_rat integer DEFAULT 0, total_gerai integer DEFAULT 0, gerai_aktif integer DEFAULT 0,
            gerai_belum_aktif integer DEFAULT 0, pembangunan_belum_mulai integer DEFAULT 0,
            pembangunan_berjalan integer DEFAULT 0, pembangunan_selesai integer DEFAULT 0,
            total_pengajuan_pembiayaan integer DEFAULT 0, total_nominal_pembiayaan real DEFAULT 0,
            total_pengajuan_kemitraan integer DEFAULT 0, priority_score real DEFAULT 0,
            updated_at text DEFAULT CURRENT_TIMESTAMP, UNIQUE (scope_level, scope_code, period_month)
        )""",
    ])
    for table, cols in [
        (t['koperasi_snapshot'], 'kode_wilayah'), (t['koperasi_monthly_metrics'], 'period_month'),
        (t['koperasi_monthly_metrics'], 'koperasi_ref'), (t['product_monthly_metrics'], 'period_month'),
        (t['product_monthly_metrics'], 'koperasi_ref'), (t['regional_monthly_metrics'], 'scope_level, scope_code'),
        (t['regional_monthly_metrics'], 'period_month'), (t['regional_monthly_metrics'], 'priority_score'),
    ]:
        execute_write(f"CREATE INDEX IF NOT EXISTS idx_{table}_{cols.replace(', ', '_').replace(' ', '_')} ON {table} ({cols})")


def ensure_summary_tables() -> None:
    t = {base: prefixed(base) for base in SUMMARY_BASES}
    if _dashboard_is_sqlite():
        _ensure_summary_tables_sqlite(t)
        schema_repository.list_dashboard_tables.cache_clear()
        return
    ddl = f"""
    CREATE TABLE IF NOT EXISTS {t['etl_run_log']} (
        run_ref text PRIMARY KEY,
        job_name text NOT NULL,
        status text NOT NULL,
        started_at timestamp DEFAULT now(),
        finished_at timestamp NULL,
        duration_ms integer NULL,
        source_tables jsonb DEFAULT '[]'::jsonb,
        rows_extracted integer DEFAULT 0,
        rows_upserted integer DEFAULT 0,
        error_message text NULL,
        metadata jsonb DEFAULT '{{}}'::jsonb
    );

    CREATE TABLE IF NOT EXISTS {t['koperasi_snapshot']} (
        koperasi_ref text PRIMARY KEY,
        nama_koperasi text,
        status_registrasi text,
        bentuk_koperasi text,
        kategori_usaha text,
        pola_pengelolaan text NULL,
        kode_wilayah text,
        provinsi text,
        kab_kota text,
        kecamatan text,
        desa_kelurahan text,
        has_npwp_doc boolean DEFAULT false,
        has_nib_doc boolean DEFAULT false,
        has_badan_hukum_doc boolean DEFAULT false,
        has_bank_account boolean DEFAULT false,
        has_rat boolean DEFAULT false,
        latest_rat_status text NULL,
        has_gerai boolean DEFAULT false,
        gerai_status text NULL,
        total_anggota integer DEFAULT 0,
        total_simpanan numeric DEFAULT 0,
        total_modal numeric DEFAULT 0,
        total_transaksi numeric DEFAULT 0,
        last_transaction_at timestamp NULL,
        updated_at timestamp DEFAULT now()
    );

    CREATE TABLE IF NOT EXISTS {t['koperasi_monthly_metrics']} (
        metric_ref text PRIMARY KEY,
        koperasi_ref text NOT NULL,
        period_month text NOT NULL,
        year integer NOT NULL,
        month integer NOT NULL,
        kode_wilayah text,
        provinsi text,
        kab_kota text,
        kecamatan text,
        desa_kelurahan text,
        total_omzet numeric DEFAULT 0,
        total_transaksi integer DEFAULT 0,
        total_volume_produk numeric DEFAULT 0,
        average_transaction_value numeric DEFAULT 0,
        total_simpanan numeric DEFAULT 0,
        simpanan_paid numeric DEFAULT 0,
        simpanan_unpaid numeric DEFAULT 0,
        simpanan_paid_ratio numeric DEFAULT 0,
        total_modal numeric DEFAULT 0,
        total_pengajuan_pembiayaan integer DEFAULT 0,
        total_nominal_pembiayaan numeric DEFAULT 0,
        total_pengajuan_kemitraan integer DEFAULT 0,
        created_at timestamp DEFAULT now(),
        updated_at timestamp DEFAULT now(),
        UNIQUE (koperasi_ref, period_month)
    );

    CREATE TABLE IF NOT EXISTS {t['product_monthly_metrics']} (
        metric_ref text PRIMARY KEY,
        koperasi_ref text NOT NULL,
        period_month text NOT NULL,
        produk_ref text NULL,
        nama_produk text NULL,
        kategori_produk text NULL,
        total_volume_keluar numeric DEFAULT 0,
        total_nilai_keluar numeric DEFAULT 0,
        stok_tersedia numeric DEFAULT 0,
        harga_beli_avg numeric DEFAULT 0,
        harga_jual_avg numeric DEFAULT 0,
        estimated_margin numeric DEFAULT 0,
        last_sold_at timestamp NULL,
        days_without_sales integer NULL,
        movement_status text NULL,
        updated_at timestamp DEFAULT now(),
        UNIQUE (koperasi_ref, period_month, produk_ref)
    );

    CREATE TABLE IF NOT EXISTS {t['rat_compliance_snapshot']} (
        koperasi_ref text PRIMARY KEY,
        latest_rat_year integer NULL,
        latest_rat_status text NULL,
        rat_verified boolean DEFAULT false,
        rat_draft boolean DEFAULT false,
        has_laporan_posisi_keuangan boolean DEFAULT false,
        has_laporan_hasil_usaha boolean DEFAULT false,
        total_dokumen integer DEFAULT 0,
        has_npwp_doc boolean DEFAULT false,
        has_nib_doc boolean DEFAULT false,
        has_badan_hukum_doc boolean DEFAULT false,
        expired_documents_count integer DEFAULT 0,
        expired_soon_documents_count integer DEFAULT 0,
        compliance_score numeric DEFAULT 0,
        updated_at timestamp DEFAULT now()
    );

    CREATE TABLE IF NOT EXISTS {t['gerai_asset_snapshot']} (
        koperasi_ref text PRIMARY KEY,
        kode_wilayah text,
        status_gerai text NULL,
        jenis_gerai text NULL,
        akses_listrik boolean NULL,
        akses_internet boolean NULL,
        total_gerai integer DEFAULT 0,
        gerai_aktif integer DEFAULT 0,
        gerai_belum_aktif integer DEFAULT 0,
        asset_status text NULL,
        progres_pembangunan numeric DEFAULT 0,
        pembangunan_bucket text NULL,
        updated_at timestamp DEFAULT now()
    );

    CREATE TABLE IF NOT EXISTS {t['village_potential_snapshot']} (
        kode_wilayah text PRIMARY KEY,
        provinsi text,
        kab_kota text,
        kecamatan text,
        desa_kelurahan text,
        total_penduduk integer DEFAULT 0,
        jumlah_keluarga integer DEFAULT 0,
        anggaran_dana_desa numeric DEFAULT 0,
        luas_wilayah numeric DEFAULT 0,
        komoditas_utama jsonb DEFAULT '[]'::jsonb,
        total_potensi numeric DEFAULT 0,
        updated_at timestamp DEFAULT now()
    );

    CREATE TABLE IF NOT EXISTS {t['regional_monthly_metrics']} (
        metric_ref text PRIMARY KEY,
        scope_level text NOT NULL,
        scope_code text NOT NULL,
        provinsi text NULL,
        kab_kota text NULL,
        kecamatan text NULL,
        desa_kelurahan text NULL,
        kode_wilayah text NULL,
        period_month text NOT NULL,
        year integer NOT NULL,
        month integer NOT NULL,
        total_koperasi integer DEFAULT 0,
        koperasi_aktif integer DEFAULT 0,
        koperasi_has_npwp integer DEFAULT 0,
        koperasi_has_nib integer DEFAULT 0,
        total_anggota integer DEFAULT 0,
        total_simpanan numeric DEFAULT 0,
        total_simpanan_paid numeric DEFAULT 0,
        simpanan_paid_ratio numeric DEFAULT 0,
        total_omzet numeric DEFAULT 0,
        total_transaksi integer DEFAULT 0,
        total_volume_produk numeric DEFAULT 0,
        total_rat integer DEFAULT 0,
        rat_verified integer DEFAULT 0,
        rat_draft integer DEFAULT 0,
        belum_rat integer DEFAULT 0,
        total_gerai integer DEFAULT 0,
        gerai_aktif integer DEFAULT 0,
        gerai_belum_aktif integer DEFAULT 0,
        pembangunan_belum_mulai integer DEFAULT 0,
        pembangunan_berjalan integer DEFAULT 0,
        pembangunan_selesai integer DEFAULT 0,
        total_pengajuan_pembiayaan integer DEFAULT 0,
        total_nominal_pembiayaan numeric DEFAULT 0,
        total_pengajuan_kemitraan integer DEFAULT 0,
        priority_score numeric DEFAULT 0,
        updated_at timestamp DEFAULT now(),
        UNIQUE (scope_level, scope_code, period_month)
    );

    CREATE INDEX IF NOT EXISTS idx_{t['koperasi_snapshot']}_wilayah ON {t['koperasi_snapshot']} (kode_wilayah);
    CREATE INDEX IF NOT EXISTS idx_{t['koperasi_snapshot']}_region ON {t['koperasi_snapshot']} (provinsi, kab_kota, kecamatan, desa_kelurahan);
    CREATE INDEX IF NOT EXISTS idx_{t['koperasi_snapshot']}_rat ON {t['koperasi_snapshot']} (latest_rat_status);
    CREATE INDEX IF NOT EXISTS idx_{t['koperasi_snapshot']}_gerai ON {t['koperasi_snapshot']} (gerai_status);
    CREATE INDEX IF NOT EXISTS idx_{t['koperasi_monthly_metrics']}_period ON {t['koperasi_monthly_metrics']} (period_month);
    CREATE INDEX IF NOT EXISTS idx_{t['koperasi_monthly_metrics']}_koperasi ON {t['koperasi_monthly_metrics']} (koperasi_ref);
    CREATE INDEX IF NOT EXISTS idx_{t['koperasi_monthly_metrics']}_region ON {t['koperasi_monthly_metrics']} (provinsi, kab_kota, kode_wilayah);
    CREATE INDEX IF NOT EXISTS idx_{t['product_monthly_metrics']}_period ON {t['product_monthly_metrics']} (period_month);
    CREATE INDEX IF NOT EXISTS idx_{t['product_monthly_metrics']}_koperasi ON {t['product_monthly_metrics']} (koperasi_ref);
    CREATE INDEX IF NOT EXISTS idx_{t['product_monthly_metrics']}_status ON {t['product_monthly_metrics']} (movement_status);
    CREATE INDEX IF NOT EXISTS idx_{t['rat_compliance_snapshot']}_status ON {t['rat_compliance_snapshot']} (latest_rat_status);
    CREATE INDEX IF NOT EXISTS idx_{t['rat_compliance_snapshot']}_score ON {t['rat_compliance_snapshot']} (compliance_score);
    CREATE INDEX IF NOT EXISTS idx_{t['gerai_asset_snapshot']}_wilayah ON {t['gerai_asset_snapshot']} (kode_wilayah);
    CREATE INDEX IF NOT EXISTS idx_{t['gerai_asset_snapshot']}_status ON {t['gerai_asset_snapshot']} (status_gerai);
    CREATE INDEX IF NOT EXISTS idx_{t['village_potential_snapshot']}_region ON {t['village_potential_snapshot']} (provinsi, kab_kota, kecamatan, desa_kelurahan);
    CREATE INDEX IF NOT EXISTS idx_{t['regional_monthly_metrics']}_scope ON {t['regional_monthly_metrics']} (scope_level, scope_code);
    CREATE INDEX IF NOT EXISTS idx_{t['regional_monthly_metrics']}_period ON {t['regional_monthly_metrics']} (period_month);
    CREATE INDEX IF NOT EXISTS idx_{t['regional_monthly_metrics']}_region ON {t['regional_monthly_metrics']} (provinsi, kab_kota, kecamatan, kode_wilayah);
    CREATE INDEX IF NOT EXISTS idx_{t['regional_monthly_metrics']}_priority ON {t['regional_monthly_metrics']} (priority_score);
    """
    execute_write(ddl)
    schema_repository.list_tables.cache_clear()
    schema_repository.list_dashboard_tables.cache_clear()
    schema_repository._list_columns_cached.cache_clear()


def run_logged(job_name: str, source_tables: list[str], fn, metadata: dict | None = None) -> dict:
    ensure_summary_tables()
    run_ref = str(uuid4())
    started = time.monotonic()
    execute_write(
        f"""
        INSERT INTO {prefixed('etl_run_log')}
            (run_ref, job_name, status, source_tables, metadata)
        VALUES (:run_ref, :job_name, 'running', CAST(:source_tables AS jsonb), CAST(:metadata AS jsonb))
        """,
        {
            "run_ref": run_ref,
            "job_name": job_name,
            "source_tables": json.dumps(source_tables),
            "metadata": json.dumps(metadata or {}),
        },
    )
    try:
        rows = fn()
        duration_ms = int((time.monotonic() - started) * 1000)
        execute_write(
            f"""
            UPDATE {prefixed('etl_run_log')}
            SET status = 'success', finished_at = {_now_sql()}, duration_ms = :duration_ms,
                rows_extracted = :rows, rows_upserted = :rows
            WHERE run_ref = :run_ref
            """,
            {"run_ref": run_ref, "duration_ms": duration_ms, "rows": max(rows, 0)},
        )
        return {"run_ref": run_ref, "job_name": job_name, "status": "success", "rows": rows}
    except Exception as exc:
        duration_ms = int((time.monotonic() - started) * 1000)
        execute_write(
            f"""
            UPDATE {prefixed('etl_run_log')}
            SET status = 'failed', finished_at = {_now_sql()}, duration_ms = :duration_ms,
                error_message = :error_message
            WHERE run_ref = :run_ref
            """,
            {"run_ref": run_ref, "duration_ms": duration_ms, "error_message": str(exc)[:4000]},
        )
        raise


def _execute_etl(sql: str, params: dict | None = None) -> int:
    with get_dashboard_engine().begin() as conn:
        if conn.dialect.name != "sqlite":
            conn.execute(text(f"SET LOCAL statement_timeout = {int(settings.etl_statement_timeout_ms)}"))
        result = conn.execute(text(sql), params or {})
        return result.rowcount or 0


def _upsert_rows(table: str, rows: list[dict], conflict_cols: list[str], jsonb_cols: set[str] | None = None) -> int:
    if not rows:
        return 0
    jsonb_cols = jsonb_cols or set()
    columns = list(rows[0].keys())
    if _dashboard_is_sqlite() and len(rows) * len(columns) > 900:
        chunk_size = max(1, 900 // len(columns))
        return sum(_upsert_rows(table, rows[i:i + chunk_size], conflict_cols, jsonb_cols) for i in range(0, len(rows), chunk_size))
    placeholders = []
    params = {}
    for row_idx, row in enumerate(rows):
        values = []
        for col in columns:
            key = f"r{row_idx}_{col}"
            value = _normalize_value(row.get(col))
            if col in jsonb_cols and value is not None:
                value = json.dumps(value)
                values.append(f":{key}" if _dashboard_is_sqlite() else f"CAST(:{key} AS jsonb)")
            else:
                values.append(f":{key}")
            params[key] = value
        placeholders.append("(" + ", ".join(values) + ")")
    updates = [f"{col} = EXCLUDED.{col}" for col in columns if col not in conflict_cols]
    sql = f"""
        INSERT INTO {table} ({", ".join(columns)})
        VALUES {", ".join(placeholders)}
        ON CONFLICT ({", ".join(conflict_cols)}) DO UPDATE SET {", ".join(updates)}
    """
    return _execute_etl(sql, params)


def _normalize_value(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime):
        return value.replace(tzinfo=None).isoformat(sep=" ")
    if isinstance(value, date):
        return value.isoformat()
    return value


def _now_sql() -> str:
    return "CURRENT_TIMESTAMP" if _dashboard_is_sqlite() else "now()"


def refresh_koperasi_snapshot() -> int:
    t = {base: prefixed(base) for base in SUMMARY_BASES}
    rows = execute_query("""
    WITH docs AS (
        SELECT dk.koperasi_ref,
               bool_or(lower(coalesce(rd.nama_dokumen, dk.jenis_dokumen_ref)) LIKE '%npwp%') AS has_npwp_doc,
               bool_or(lower(coalesce(rd.nama_dokumen, dk.jenis_dokumen_ref)) LIKE '%nib%') AS has_nib_doc,
               bool_or(lower(coalesce(rd.nama_dokumen, dk.jenis_dokumen_ref)) LIKE '%badan%hukum%') AS has_badan_hukum_doc
        FROM dokumen_koperasi dk
        LEFT JOIN referensi_dokumen_koperasi rd ON rd.jenis_dokumen_ref = dk.jenis_dokumen_ref
        GROUP BY dk.koperasi_ref
    ), anggota AS (
        SELECT koperasi_ref, count(*)::int AS total_anggota FROM anggota_koperasi GROUP BY koperasi_ref
    ), simpanan AS (
        SELECT koperasi_ref, coalesce(sum(jumlah_simpanan), 0) AS total_simpanan FROM simpanan_anggota GROUP BY koperasi_ref
    ), modal AS (
        SELECT koperasi_ref, coalesce(sum(jumlah), 0) AS total_modal FROM modal_koperasi GROUP BY koperasi_ref
    ), trx AS (
        SELECT koperasi_ref, coalesce(sum(total_pembayaran), 0) AS total_transaksi, max(tanggal_dibuat) AS last_transaction_at
        FROM transaksi_penjualan GROUP BY koperasi_ref
    ), latest_rat AS (
        SELECT DISTINCT ON (koperasi_ref) koperasi_ref, status_rat
        FROM rat_koperasi
        ORDER BY koperasi_ref, tahun_buku DESC NULLS LAST, tanggal_rat DESC NULLS LAST
    ), gerai AS (
        SELECT koperasi_ref, bool_or(true) AS has_gerai, max(status_gerai) AS gerai_status
        FROM gerai_koperasi GROUP BY koperasi_ref
    ), bank AS (
        SELECT koperasi_ref, bool_or(true) AS has_bank_account FROM akun_bank_koperasi GROUP BY koperasi_ref
    )
    SELECT pk.koperasi_ref, pk.nama_koperasi, pk.status_registrasi, pk.bentuk_koperasi,
           pk.kategori_usaha, pk.pola_pengelolaan, rkw.kode_wilayah, rw.provinsi, rw.kab_kota,
           rw.kecamatan, rw.desa_kelurahan,
           coalesce(docs.has_npwp_doc, false) AS has_npwp_doc,
           coalesce(docs.has_nib_doc, false) AS has_nib_doc,
           coalesce(docs.has_badan_hukum_doc, false) AS has_badan_hukum_doc,
           coalesce(bank.has_bank_account, false) AS has_bank_account,
           latest_rat.koperasi_ref IS NOT NULL AS has_rat,
           latest_rat.status_rat AS latest_rat_status,
           coalesce(gerai.has_gerai, false) AS has_gerai,
           gerai.gerai_status,
           coalesce(anggota.total_anggota, 0) AS total_anggota,
           coalesce(simpanan.total_simpanan, 0) AS total_simpanan,
           coalesce(modal.total_modal, 0) AS total_modal,
           coalesce(trx.total_transaksi, 0) AS total_transaksi,
           trx.last_transaction_at, now() AS updated_at
    FROM profil_koperasi pk
    LEFT JOIN referensi_koperasi_wilayah rkw ON rkw.koperasi_ref = pk.koperasi_ref
    LEFT JOIN referensi_wilayah rw ON rw.kode_wilayah = rkw.kode_wilayah
    LEFT JOIN docs ON docs.koperasi_ref = pk.koperasi_ref
    LEFT JOIN anggota ON anggota.koperasi_ref = pk.koperasi_ref
    LEFT JOIN simpanan ON simpanan.koperasi_ref = pk.koperasi_ref
    LEFT JOIN modal ON modal.koperasi_ref = pk.koperasi_ref
    LEFT JOIN trx ON trx.koperasi_ref = pk.koperasi_ref
    LEFT JOIN latest_rat ON latest_rat.koperasi_ref = pk.koperasi_ref
    LEFT JOIN gerai ON gerai.koperasi_ref = pk.koperasi_ref
    LEFT JOIN bank ON bank.koperasi_ref = pk.koperasi_ref
    """)
    return _upsert_rows(t["koperasi_snapshot"], rows, ["koperasi_ref"])


def refresh_koperasi_monthly_metrics(period: str) -> int:
    t = {base: prefixed(base) for base in SUMMARY_BASES}
    year, month = map(int, period.split("-"))
    rows = execute_query("""
    WITH trx AS (
        SELECT koperasi_ref, coalesce(sum(total_pembayaran), 0) total_omzet, count(*)::int total_transaksi
        FROM transaksi_penjualan WHERE to_char(tanggal_dibuat, 'YYYY-MM') = :period GROUP BY koperasi_ref
    ), produk AS (
        SELECT koperasi_ref, coalesce(sum(jumlah_keluar), 0) total_volume_produk
        FROM barang_keluar_produk WHERE to_char(tanggal_keluar, 'YYYY-MM') = :period GROUP BY koperasi_ref
    ), simpanan AS (
        SELECT koperasi_ref,
               coalesce(sum(jumlah_simpanan), 0) total_simpanan,
               coalesce(sum(jumlah_simpanan) FILTER (WHERE lower(coalesce(status, '')) IN ('paid','lunas','terbayar','success','berhasil')), 0) simpanan_paid,
               coalesce(sum(jumlah_simpanan) FILTER (WHERE lower(coalesce(status, '')) NOT IN ('paid','lunas','terbayar','success','berhasil')), 0) simpanan_unpaid
        FROM simpanan_anggota WHERE left(periode_pembayaran::text, 7) = :period GROUP BY koperasi_ref
    ), modal AS (
        SELECT koperasi_ref, coalesce(sum(jumlah), 0) total_modal FROM modal_koperasi GROUP BY koperasi_ref
    ), pembiayaan AS (
        SELECT koperasi_ref, count(*)::int total_pengajuan_pembiayaan, coalesce(sum(nominal_permohonan), 0) total_nominal_pembiayaan
        FROM pengajuan_pembiayaan WHERE to_char(dibuat_pada, 'YYYY-MM') = :period GROUP BY koperasi_ref
    ), kemitraan AS (
        SELECT koperasi_ref, count(*)::int total_pengajuan_kemitraan
        FROM pengajuan_kemitraan WHERE to_char(dibuat_pada, 'YYYY-MM') = :period GROUP BY koperasi_ref
    )
    SELECT pk.koperasi_ref || '-' || :period AS metric_ref, pk.koperasi_ref, :period AS period_month,
           :year AS year, :month AS month, rkw.kode_wilayah, rw.provinsi, rw.kab_kota,
           rw.kecamatan, rw.desa_kelurahan,
           coalesce(trx.total_omzet, 0) AS total_omzet,
           coalesce(trx.total_transaksi, 0) AS total_transaksi,
           coalesce(produk.total_volume_produk, 0) AS total_volume_produk,
           CASE WHEN coalesce(trx.total_transaksi, 0) > 0 THEN coalesce(trx.total_omzet, 0) / trx.total_transaksi ELSE 0 END AS average_transaction_value,
           coalesce(simpanan.total_simpanan, 0) AS total_simpanan,
           coalesce(simpanan.simpanan_paid, 0) AS simpanan_paid,
           coalesce(simpanan.simpanan_unpaid, 0) AS simpanan_unpaid,
           CASE WHEN coalesce(simpanan.total_simpanan, 0) > 0 THEN round(simpanan.simpanan_paid / simpanan.total_simpanan * 100, 2) ELSE 0 END AS simpanan_paid_ratio,
           coalesce(modal.total_modal, 0) AS total_modal,
           coalesce(pembiayaan.total_pengajuan_pembiayaan, 0) AS total_pengajuan_pembiayaan,
           coalesce(pembiayaan.total_nominal_pembiayaan, 0) AS total_nominal_pembiayaan,
           coalesce(kemitraan.total_pengajuan_kemitraan, 0) AS total_pengajuan_kemitraan,
           now() AS updated_at
    FROM profil_koperasi pk
    LEFT JOIN referensi_koperasi_wilayah rkw ON rkw.koperasi_ref = pk.koperasi_ref
    LEFT JOIN referensi_wilayah rw ON rw.kode_wilayah = rkw.kode_wilayah
    LEFT JOIN trx ON trx.koperasi_ref = pk.koperasi_ref
    LEFT JOIN produk ON produk.koperasi_ref = pk.koperasi_ref
    LEFT JOIN simpanan ON simpanan.koperasi_ref = pk.koperasi_ref
    LEFT JOIN modal ON modal.koperasi_ref = pk.koperasi_ref
    LEFT JOIN pembiayaan ON pembiayaan.koperasi_ref = pk.koperasi_ref
    LEFT JOIN kemitraan ON kemitraan.koperasi_ref = pk.koperasi_ref
    """, {"period": period, "year": year, "month": month})
    return _upsert_rows(t["koperasi_monthly_metrics"], rows, ["koperasi_ref", "period_month"])


def refresh_product_monthly_metrics(period: str) -> int:
    t = {base: prefixed(base) for base in SUMMARY_BASES}
    rows = execute_query("""
    WITH products AS (
        SELECT koperasi_ref, produk_sample_id produk_ref, max(nama_produk) nama_produk FROM produk_koperasi GROUP BY koperasi_ref, produk_sample_id
        UNION
        SELECT koperasi_ref, produk_sample_id, max(nama_produk) FROM inventaris_produk GROUP BY koperasi_ref, produk_sample_id
        UNION
        SELECT koperasi_ref, produk_sample_id, max(nama_produk) FROM barang_keluar_produk GROUP BY koperasi_ref, produk_sample_id
    ), keluar AS (
        SELECT koperasi_ref, produk_sample_id produk_ref, coalesce(sum(jumlah_keluar), 0) volume_keluar,
               coalesce(sum(total_nilai), 0) nilai_keluar, max(tanggal_keluar) last_sold_at
        FROM barang_keluar_produk WHERE to_char(tanggal_keluar, 'YYYY-MM') = :period GROUP BY koperasi_ref, produk_sample_id
    ), stok AS (
        SELECT koperasi_ref, produk_sample_id produk_ref, coalesce(sum(stok), 0) stok_tersedia
        FROM inventaris_produk GROUP BY koperasi_ref, produk_sample_id
    ), masuk AS (
        SELECT koperasi_ref, produk_sample_id produk_ref, avg(harga_beli) harga_beli_avg, avg(harga_jual) harga_jual_avg
        FROM barang_masuk_produk GROUP BY koperasi_ref, produk_sample_id
    )
    SELECT p.koperasi_ref || '-' || :period || '-' || coalesce(p.produk_ref, 'unknown') AS metric_ref,
           p.koperasi_ref, :period AS period_month, p.produk_ref, p.nama_produk,
           NULL AS kategori_produk, coalesce(k.volume_keluar, 0) AS total_volume_keluar,
           coalesce(k.nilai_keluar, 0) AS total_nilai_keluar,
           coalesce(s.stok_tersedia, 0) AS stok_tersedia,
           coalesce(m.harga_beli_avg, 0) AS harga_beli_avg,
           coalesce(m.harga_jual_avg, 0) AS harga_jual_avg,
           coalesce(m.harga_jual_avg, 0) - coalesce(m.harga_beli_avg, 0) AS estimated_margin,
           k.last_sold_at,
           CASE WHEN k.last_sold_at IS NULL THEN NULL ELSE (current_date - k.last_sold_at::date)::int END AS days_without_sales,
           CASE
             WHEN coalesce(s.stok_tersedia, 0) = 0 THEN 'understock'
             WHEN k.last_sold_at IS NULL THEN 'dead_stock'
             WHEN (current_date - k.last_sold_at::date) > 60 THEN 'slow_moving'
             WHEN coalesce(k.volume_keluar, 0) >= 100 THEN 'fast_moving'
             ELSE 'normal'
           END AS movement_status,
           now() AS updated_at
    FROM products p
    LEFT JOIN keluar k ON k.koperasi_ref = p.koperasi_ref AND k.produk_ref = p.produk_ref
    LEFT JOIN stok s ON s.koperasi_ref = p.koperasi_ref AND s.produk_ref = p.produk_ref
    LEFT JOIN masuk m ON m.koperasi_ref = p.koperasi_ref AND m.produk_ref = p.produk_ref
    """, {"period": period})
    return _upsert_rows(t["product_monthly_metrics"], rows, ["koperasi_ref", "period_month", "produk_ref"])


def refresh_rat_compliance() -> int:
    t = {base: prefixed(base) for base in SUMMARY_BASES}
    rows = execute_query("""
    WITH latest AS (
        SELECT DISTINCT ON (koperasi_ref) koperasi_ref, tahun_buku, status_rat,
               laporan_posisi_keuangan IS NOT NULL has_laporan_posisi_keuangan,
               laporan_hasil_usaha IS NOT NULL has_laporan_hasil_usaha
        FROM rat_koperasi ORDER BY koperasi_ref, tahun_buku DESC NULLS LAST, tanggal_rat DESC NULLS LAST
    ), docs AS (
        SELECT dk.koperasi_ref, count(*)::int total_dokumen,
               bool_or(lower(coalesce(rd.nama_dokumen, dk.jenis_dokumen_ref)) LIKE '%npwp%') has_npwp_doc,
               bool_or(lower(coalesce(rd.nama_dokumen, dk.jenis_dokumen_ref)) LIKE '%nib%') has_nib_doc,
               bool_or(lower(coalesce(rd.nama_dokumen, dk.jenis_dokumen_ref)) LIKE '%badan%hukum%') has_badan_hukum_doc,
               count(*) FILTER (WHERE dk.tanggal_kadaluarsa < current_date)::int expired_documents_count,
               count(*) FILTER (WHERE dk.tanggal_kadaluarsa BETWEEN current_date AND current_date + interval '30 days')::int expired_soon_documents_count
        FROM dokumen_koperasi dk LEFT JOIN referensi_dokumen_koperasi rd ON rd.jenis_dokumen_ref = dk.jenis_dokumen_ref
        GROUP BY dk.koperasi_ref
    )
    SELECT pk.koperasi_ref, latest.tahun_buku AS latest_rat_year,
           latest.status_rat AS latest_rat_status,
           lower(coalesce(latest.status_rat, '')) IN ('verified','terverifikasi','approved') AS rat_verified,
           lower(coalesce(latest.status_rat, '')) IN ('draft','pending') AS rat_draft,
           coalesce(latest.has_laporan_posisi_keuangan, false) AS has_laporan_posisi_keuangan,
           coalesce(latest.has_laporan_hasil_usaha, false) AS has_laporan_hasil_usaha,
           coalesce(docs.total_dokumen, 0) AS total_dokumen,
           coalesce(docs.has_npwp_doc, false) AS has_npwp_doc,
           coalesce(docs.has_nib_doc, false) AS has_nib_doc,
           coalesce(docs.has_badan_hukum_doc, false) AS has_badan_hukum_doc,
           coalesce(docs.expired_documents_count, 0) AS expired_documents_count,
           coalesce(docs.expired_soon_documents_count, 0) AS expired_soon_documents_count,
           (CASE WHEN lower(coalesce(latest.status_rat, '')) IN ('verified','terverifikasi','approved') THEN 35 ELSE 0 END) +
           (CASE WHEN coalesce(docs.has_npwp_doc, false) THEN 20 ELSE 0 END) +
           (CASE WHEN coalesce(docs.has_nib_doc, false) THEN 20 ELSE 0 END) +
           (CASE WHEN coalesce(docs.has_badan_hukum_doc, false) THEN 25 ELSE 0 END) AS compliance_score,
           now() AS updated_at
    FROM profil_koperasi pk
    LEFT JOIN latest ON latest.koperasi_ref = pk.koperasi_ref
    LEFT JOIN docs ON docs.koperasi_ref = pk.koperasi_ref
    """)
    return _upsert_rows(t["rat_compliance_snapshot"], rows, ["koperasi_ref"])


def refresh_gerai_asset() -> int:
    t = {base: prefixed(base) for base in SUMMARY_BASES}
    rows = execute_query("""
    WITH gerai AS (
        SELECT g.koperasi_ref, max(g.status_gerai) status_gerai, max(rg.nama_jenis_gerai) jenis_gerai,
               bool_or(lower(coalesce(g.akses_listrik::text, '')) IN ('true','t','1','ya','yes','ada')) akses_listrik,
               bool_or(lower(coalesce(g.akses_internet::text, '')) IN ('true','t','1','ya','yes','ada')) akses_internet,
               count(*)::int total_gerai,
               count(*) FILTER (WHERE lower(coalesce(g.status_gerai, '')) IN ('aktif','active','verified'))::int gerai_aktif,
               count(*) FILTER (WHERE lower(coalesce(g.status_gerai, '')) NOT IN ('aktif','active','verified'))::int gerai_belum_aktif
        FROM gerai_koperasi g LEFT JOIN referensi_gerai_koperasi rg ON rg.jenis_gerai_ref = g.jenis_gerai_ref
        GROUP BY g.koperasi_ref
    ), aset AS (
        SELECT koperasi_ref, max(status) asset_status, coalesce(avg(progres_pembangunan), 0) progres_pembangunan
        FROM aset_koperasi GROUP BY koperasi_ref
    )
    SELECT pk.koperasi_ref, rkw.kode_wilayah, gerai.status_gerai, gerai.jenis_gerai,
           gerai.akses_listrik, gerai.akses_internet,
           coalesce(gerai.total_gerai, 0) AS total_gerai,
           coalesce(gerai.gerai_aktif, 0) AS gerai_aktif,
           coalesce(gerai.gerai_belum_aktif, 0) AS gerai_belum_aktif,
           aset.asset_status, coalesce(aset.progres_pembangunan, 0) AS progres_pembangunan,
           CASE WHEN coalesce(aset.progres_pembangunan, 0) >= 100 THEN 'selesai'
                WHEN coalesce(aset.progres_pembangunan, 0) > 0 THEN 'berjalan'
                ELSE 'belum_mulai' END AS pembangunan_bucket,
           now() AS updated_at
    FROM profil_koperasi pk
    LEFT JOIN referensi_koperasi_wilayah rkw ON rkw.koperasi_ref = pk.koperasi_ref
    LEFT JOIN gerai ON gerai.koperasi_ref = pk.koperasi_ref
    LEFT JOIN aset ON aset.koperasi_ref = pk.koperasi_ref
    """)
    return _upsert_rows(t["gerai_asset_snapshot"], rows, ["koperasi_ref"])


def refresh_village_potential() -> int:
    t = {base: prefixed(base) for base in SUMMARY_BASES}
    rows = execute_query("""
    WITH kom AS (
        SELECT kode_wilayah,
               jsonb_agg(jsonb_build_object('nama_komoditas', nama_komoditas, 'volume', volume, 'nilai_potensi', nilai_potensi_desa) ORDER BY nilai_potensi_desa DESC NULLS LAST) komoditas_utama,
               coalesce(sum(nullif(regexp_replace(nilai_potensi_desa::text, '[^0-9.-]', '', 'g'), '')::numeric), 0) total_potensi,
               coalesce(sum(nullif(regexp_replace(luas_area::text, '[^0-9.-]', '', 'g'), '')::numeric), 0) luas_wilayah
        FROM referensi_komoditas_desa GROUP BY kode_wilayah
    )
    SELECT rw.kode_wilayah, rw.provinsi, rw.kab_kota, rw.kecamatan, rw.desa_kelurahan,
           coalesce(nullif(regexp_replace(rpd.total_penduduk::text, '[^0-9.-]', '', 'g'), '')::numeric, 0) AS total_penduduk,
           0 AS jumlah_keluarga,
           coalesce(nullif(regexp_replace(rpd.anggaran_dana_desa::text, '[^0-9.-]', '', 'g'), '')::numeric, 0) AS anggaran_dana_desa,
           coalesce(kom.luas_wilayah, 0) AS luas_wilayah,
           coalesce(kom.komoditas_utama, '[]'::jsonb) AS komoditas_utama,
           coalesce(kom.total_potensi, 0) AS total_potensi,
           now() AS updated_at
    FROM referensi_wilayah rw
    LEFT JOIN referensi_profil_desa rpd ON rpd.kode_wilayah = rw.kode_wilayah
    LEFT JOIN kom ON kom.kode_wilayah = rw.kode_wilayah
    """)
    return _upsert_rows(t["village_potential_snapshot"], rows, ["kode_wilayah"], {"komoditas_utama"})


def _priority_score(row: dict) -> float:
    score = 0
    if not row.get("rat_verified"):
        score += 25
    if not (row.get("total_transaksi") or 0):
        score += 20
    if (row.get("simpanan_paid_ratio") or 0) < 60:
        score += 15
    if not (row.get("has_npwp_doc") and row.get("has_nib_doc") and row.get("has_badan_hukum_doc")):
        score += 15
    if not row.get("gerai_aktif") or not row.get("akses_listrik") or not row.get("akses_internet"):
        score += 10
    if row.get("pembangunan_bucket") == "selesai" and not (row.get("total_transaksi") or 0):
        score += 10
    return min(score, 100)


def _regional_rows_from_dashboard(period: str, year: int, month: int, t: dict[str, str]) -> list[dict]:
    base_rows = execute_dashboard_query(f"""
        SELECT ks.*, km.period_month, COALESCE(km.total_omzet, 0) AS total_omzet,
               COALESCE(km.total_transaksi, 0) AS total_transaksi,
               COALESCE(km.total_volume_produk, 0) AS total_volume_produk,
               COALESCE(km.total_simpanan, 0) AS monthly_simpanan,
               COALESCE(km.simpanan_paid, 0) AS simpanan_paid,
               COALESCE(km.simpanan_paid_ratio, 0) AS simpanan_paid_ratio,
               COALESCE(km.total_pengajuan_pembiayaan, 0) AS total_pengajuan_pembiayaan,
               COALESCE(km.total_nominal_pembiayaan, 0) AS total_nominal_pembiayaan,
               COALESCE(km.total_pengajuan_kemitraan, 0) AS total_pengajuan_kemitraan,
               COALESCE(rc.rat_verified, 0) AS rat_verified,
               COALESCE(rc.rat_draft, 0) AS rat_draft,
               COALESCE(ga.total_gerai, 0) AS total_gerai,
               COALESCE(ga.gerai_aktif, 0) AS gerai_aktif,
               COALESCE(ga.gerai_belum_aktif, 0) AS gerai_belum_aktif,
               COALESCE(ga.akses_listrik, 0) AS akses_listrik,
               COALESCE(ga.akses_internet, 0) AS akses_internet,
               ga.pembangunan_bucket
        FROM {t['koperasi_snapshot']} ks
        LEFT JOIN {t['koperasi_monthly_metrics']} km
          ON km.koperasi_ref = ks.koperasi_ref AND km.period_month = :period
        LEFT JOIN {t['rat_compliance_snapshot']} rc ON rc.koperasi_ref = ks.koperasi_ref
        LEFT JOIN {t['gerai_asset_snapshot']} ga ON ga.koperasi_ref = ks.koperasi_ref
    """, {"period": period})
    grouped: dict[tuple, list[dict]] = {}
    for row in base_rows:
        scopes = [
            ("nasional", "nasional", None, None, None, None, None),
            ("provinsi", row.get("provinsi") or "unknown", row.get("provinsi"), None, None, None, None),
            ("kab_kota", row.get("kab_kota") or "unknown", row.get("provinsi"), row.get("kab_kota"), None, None, None),
            ("kecamatan", row.get("kecamatan") or "unknown", row.get("provinsi"), row.get("kab_kota"), row.get("kecamatan"), None, None),
            ("desa", row.get("kode_wilayah") or "unknown", row.get("provinsi"), row.get("kab_kota"), row.get("kecamatan"), row.get("desa_kelurahan"), row.get("kode_wilayah")),
        ]
        for scope in scopes:
            grouped.setdefault(scope, []).append(row)
    rows = []
    for (level, code, prov, kab, kec, desa, kode), items in grouped.items():
        total_simpanan = sum(float(i.get("monthly_simpanan") or 0) for i in items)
        paid = sum(float(i.get("simpanan_paid") or 0) for i in items)
        priority_scores = [_priority_score(i) for i in items]
        rows.append({
            "metric_ref": f"{level}-{code}-{period}", "scope_level": level, "scope_code": code,
            "provinsi": prov, "kab_kota": kab, "kecamatan": kec, "desa_kelurahan": desa,
            "kode_wilayah": kode, "period_month": period, "year": year, "month": month,
            "total_koperasi": len(items),
            "koperasi_aktif": sum(1 for i in items if (i.get("status_registrasi") or "").lower() in {"verified", "aktif", "active"}),
            "koperasi_has_npwp": sum(1 for i in items if i.get("has_npwp_doc")),
            "koperasi_has_nib": sum(1 for i in items if i.get("has_nib_doc")),
            "total_anggota": sum(int(i.get("total_anggota") or 0) for i in items),
            "total_simpanan": total_simpanan, "total_simpanan_paid": paid,
            "simpanan_paid_ratio": round(paid / total_simpanan * 100, 2) if total_simpanan else 0,
            "total_omzet": sum(float(i.get("total_omzet") or 0) for i in items),
            "total_transaksi": sum(int(i.get("total_transaksi") or 0) for i in items),
            "total_volume_produk": sum(float(i.get("total_volume_produk") or 0) for i in items),
            "total_rat": sum(1 for i in items if i.get("has_rat")),
            "rat_verified": sum(1 for i in items if i.get("rat_verified")),
            "rat_draft": sum(1 for i in items if i.get("rat_draft")),
            "belum_rat": sum(1 for i in items if not i.get("has_rat")),
            "total_gerai": sum(int(i.get("total_gerai") or 0) for i in items),
            "gerai_aktif": sum(int(i.get("gerai_aktif") or 0) for i in items),
            "gerai_belum_aktif": sum(int(i.get("gerai_belum_aktif") or 0) for i in items),
            "pembangunan_belum_mulai": sum(1 for i in items if i.get("pembangunan_bucket") == "belum_mulai"),
            "pembangunan_berjalan": sum(1 for i in items if i.get("pembangunan_bucket") == "berjalan"),
            "pembangunan_selesai": sum(1 for i in items if i.get("pembangunan_bucket") == "selesai"),
            "total_pengajuan_pembiayaan": sum(int(i.get("total_pengajuan_pembiayaan") or 0) for i in items),
            "total_nominal_pembiayaan": sum(float(i.get("total_nominal_pembiayaan") or 0) for i in items),
            "total_pengajuan_kemitraan": sum(int(i.get("total_pengajuan_kemitraan") or 0) for i in items),
            "priority_score": round(sum(priority_scores) / len(priority_scores), 2) if priority_scores else 0,
            "updated_at": __import__("datetime").datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        })
    return rows


def refresh_regional_monthly_metrics(period: str) -> int:
    t = {base: prefixed(base) for base in SUMMARY_BASES}
    year, month = map(int, period.split("-"))
    if _dashboard_is_sqlite():
        rows = _regional_rows_from_dashboard(period, year, month, t)
        return _upsert_rows(t["regional_monthly_metrics"], rows, ["scope_level", "scope_code", "period_month"])
    return _execute_etl(f"""
    WITH base AS (
        SELECT ks.koperasi_ref, ks.status_registrasi, ks.kode_wilayah, ks.provinsi, ks.kab_kota,
               ks.kecamatan, ks.desa_kelurahan, ks.has_npwp_doc, ks.has_nib_doc, ks.has_badan_hukum_doc,
               ks.has_rat, ks.total_anggota,
               km.period_month, coalesce(km.total_omzet, 0) total_omzet,
               coalesce(km.total_transaksi, 0) total_transaksi, coalesce(km.total_volume_produk, 0) total_volume_produk,
               coalesce(km.total_simpanan, 0) monthly_simpanan, coalesce(km.simpanan_paid, 0) simpanan_paid,
               coalesce(km.total_pengajuan_pembiayaan, 0) total_pengajuan_pembiayaan,
               coalesce(km.total_nominal_pembiayaan, 0) total_nominal_pembiayaan,
               coalesce(km.total_pengajuan_kemitraan, 0) total_pengajuan_kemitraan,
               coalesce(rc.rat_verified, false) rat_verified, coalesce(rc.rat_draft, false) rat_draft,
               coalesce(ga.total_gerai, 0) total_gerai, coalesce(ga.gerai_aktif, 0) gerai_aktif,
               coalesce(ga.gerai_belum_aktif, 0) gerai_belum_aktif, ga.pembangunan_bucket,
               least(100,
                 (CASE WHEN coalesce(rc.rat_verified, false) THEN 0 ELSE 25 END) +
                 (CASE WHEN coalesce(km.total_transaksi, 0) = 0 THEN 20 ELSE 0 END) +
                 (CASE WHEN coalesce(km.simpanan_paid_ratio, 0) < 60 THEN 15 ELSE 0 END) +
                 (CASE WHEN NOT (coalesce(ks.has_npwp_doc, false) AND coalesce(ks.has_nib_doc, false) AND coalesce(ks.has_badan_hukum_doc, false)) THEN 15 ELSE 0 END) +
                 (CASE WHEN coalesce(ga.gerai_aktif, 0) = 0 OR coalesce(ga.akses_listrik, false) = false OR coalesce(ga.akses_internet, false) = false THEN 10 ELSE 0 END) +
                 (CASE WHEN ga.pembangunan_bucket = 'selesai' AND coalesce(km.total_transaksi, 0) = 0 THEN 10 ELSE 0 END)
               ) priority_score
        FROM {t['koperasi_snapshot']} ks
        LEFT JOIN {t['koperasi_monthly_metrics']} km ON km.koperasi_ref = ks.koperasi_ref AND km.period_month = :period
        LEFT JOIN {t['rat_compliance_snapshot']} rc ON rc.koperasi_ref = ks.koperasi_ref
        LEFT JOIN {t['gerai_asset_snapshot']} ga ON ga.koperasi_ref = ks.koperasi_ref
    ), scoped AS (
        SELECT 'nasional' scope_level, 'nasional' scope_code, NULL::text scope_provinsi, NULL::text scope_kab_kota, NULL::text scope_kecamatan, NULL::text scope_desa_kelurahan, NULL::text scope_kode_wilayah, b.* FROM base b
        UNION ALL SELECT 'provinsi', coalesce(b.provinsi, 'unknown'), b.provinsi, NULL, NULL, NULL, NULL, b.* FROM base b
        UNION ALL SELECT 'kab_kota', coalesce(b.kab_kota, 'unknown'), b.provinsi, b.kab_kota, NULL, NULL, NULL, b.* FROM base b
        UNION ALL SELECT 'kecamatan', coalesce(b.kecamatan, 'unknown'), b.provinsi, b.kab_kota, b.kecamatan, NULL, NULL, b.* FROM base b
        UNION ALL SELECT 'desa', coalesce(b.kode_wilayah, 'unknown'), b.provinsi, b.kab_kota, b.kecamatan, b.desa_kelurahan, b.kode_wilayah, b.* FROM base b
    )
    INSERT INTO {t['regional_monthly_metrics']} (
        metric_ref, scope_level, scope_code, provinsi, kab_kota, kecamatan, desa_kelurahan,
        kode_wilayah, period_month, year, month, total_koperasi, koperasi_aktif,
        koperasi_has_npwp, koperasi_has_nib, total_anggota, total_simpanan,
        total_simpanan_paid, simpanan_paid_ratio, total_omzet, total_transaksi,
        total_volume_produk, total_rat, rat_verified, rat_draft, belum_rat, total_gerai,
        gerai_aktif, gerai_belum_aktif, pembangunan_belum_mulai, pembangunan_berjalan,
        pembangunan_selesai, total_pengajuan_pembiayaan, total_nominal_pembiayaan,
        total_pengajuan_kemitraan, priority_score, updated_at
    )
    SELECT scope_level || '-' || scope_code || '-' || :period, scope_level, scope_code, scoped.scope_provinsi,
           scoped.scope_kab_kota, scoped.scope_kecamatan, scoped.scope_desa_kelurahan, scoped.scope_kode_wilayah,
           :period, :year, :month, count(*)::int,
           count(*) FILTER (WHERE lower(coalesce(status_registrasi, '')) IN ('verified','aktif','active'))::int,
           count(*) FILTER (WHERE has_npwp_doc)::int, count(*) FILTER (WHERE has_nib_doc)::int,
           coalesce(sum(total_anggota), 0)::int, coalesce(sum(monthly_simpanan), 0), coalesce(sum(simpanan_paid), 0),
           CASE WHEN coalesce(sum(monthly_simpanan), 0) > 0 THEN round(sum(simpanan_paid) / sum(monthly_simpanan) * 100, 2) ELSE 0 END,
           coalesce(sum(total_omzet), 0), coalesce(sum(total_transaksi), 0)::int, coalesce(sum(total_volume_produk), 0),
           count(*) FILTER (WHERE has_rat)::int, count(*) FILTER (WHERE rat_verified)::int,
           count(*) FILTER (WHERE rat_draft)::int, count(*) FILTER (WHERE NOT has_rat)::int,
           coalesce(sum(total_gerai), 0)::int, coalesce(sum(gerai_aktif), 0)::int, coalesce(sum(gerai_belum_aktif), 0)::int,
           count(*) FILTER (WHERE pembangunan_bucket = 'belum_mulai')::int,
           count(*) FILTER (WHERE pembangunan_bucket = 'berjalan')::int,
           count(*) FILTER (WHERE pembangunan_bucket = 'selesai')::int,
           coalesce(sum(total_pengajuan_pembiayaan), 0)::int, coalesce(sum(total_nominal_pembiayaan), 0),
           coalesce(sum(total_pengajuan_kemitraan), 0)::int, round(avg(priority_score), 2), now()
    FROM scoped
    GROUP BY scope_level, scope_code, scoped.scope_provinsi, scoped.scope_kab_kota, scoped.scope_kecamatan, scoped.scope_desa_kelurahan, scoped.scope_kode_wilayah
    ON CONFLICT (scope_level, scope_code, period_month) DO UPDATE SET
        total_koperasi = EXCLUDED.total_koperasi, koperasi_aktif = EXCLUDED.koperasi_aktif,
        koperasi_has_npwp = EXCLUDED.koperasi_has_npwp, koperasi_has_nib = EXCLUDED.koperasi_has_nib,
        total_anggota = EXCLUDED.total_anggota, total_simpanan = EXCLUDED.total_simpanan,
        total_simpanan_paid = EXCLUDED.total_simpanan_paid, simpanan_paid_ratio = EXCLUDED.simpanan_paid_ratio,
        total_omzet = EXCLUDED.total_omzet, total_transaksi = EXCLUDED.total_transaksi,
        total_volume_produk = EXCLUDED.total_volume_produk, total_rat = EXCLUDED.total_rat,
        rat_verified = EXCLUDED.rat_verified, rat_draft = EXCLUDED.rat_draft, belum_rat = EXCLUDED.belum_rat,
        total_gerai = EXCLUDED.total_gerai, gerai_aktif = EXCLUDED.gerai_aktif,
        gerai_belum_aktif = EXCLUDED.gerai_belum_aktif, pembangunan_belum_mulai = EXCLUDED.pembangunan_belum_mulai,
        pembangunan_berjalan = EXCLUDED.pembangunan_berjalan, pembangunan_selesai = EXCLUDED.pembangunan_selesai,
        total_pengajuan_pembiayaan = EXCLUDED.total_pengajuan_pembiayaan,
        total_nominal_pembiayaan = EXCLUDED.total_nominal_pembiayaan,
        total_pengajuan_kemitraan = EXCLUDED.total_pengajuan_kemitraan,
        priority_score = EXCLUDED.priority_score, updated_at = now()
    """, {"period": period, "year": year, "month": month})


def latest_runs(limit: int = 20) -> list[dict]:
    if not schema_repository.dashboard_table_exists(prefixed("etl_run_log")):
        return []
    return execute_dashboard_query(
        f"""
        SELECT run_ref, job_name, status, started_at, finished_at, duration_ms,
               rows_extracted, rows_upserted, error_message, metadata
        FROM {prefixed('etl_run_log')}
        ORDER BY started_at DESC
        LIMIT :limit
        """,
        {"limit": limit},
    )
