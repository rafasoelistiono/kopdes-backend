from app.core.config import settings
from app.repositories import etl_repository
from app.repositories import ui_backup_repository


SOURCE_TABLES = {
    "koperasi_snapshot": [
        "profil_koperasi", "referensi_koperasi_wilayah", "referensi_wilayah",
        "dokumen_koperasi", "referensi_dokumen_koperasi", "anggota_koperasi",
        "simpanan_anggota", "transaksi_penjualan", "rat_koperasi", "gerai_koperasi",
        "modal_koperasi", "akun_bank_koperasi",
    ],
    "koperasi_monthly_metrics": [
        "transaksi_penjualan", "barang_keluar_produk", "simpanan_anggota",
        "modal_koperasi", "pengajuan_pembiayaan", "pengajuan_kemitraan",
    ],
    "product_monthly_metrics": [
        "barang_keluar_produk", "produk_koperasi", "inventaris_produk", "barang_masuk_produk",
    ],
    "rat_compliance": ["rat_koperasi", "dokumen_koperasi", "referensi_dokumen_koperasi"],
    "gerai_asset": ["gerai_koperasi", "referensi_gerai_koperasi", "aset_koperasi"],
    "village_potential": ["referensi_profil_desa", "referensi_komoditas_desa", "referensi_wilayah"],
    "regional_monthly_metrics": [
        etl_repository.prefixed("koperasi_snapshot"),
        etl_repository.prefixed("koperasi_monthly_metrics"),
        etl_repository.prefixed("rat_compliance_snapshot"),
        etl_repository.prefixed("gerai_asset_snapshot"),
    ],
    "ui_screens": [
        "referensi_komoditas_desa", "referensi_profil_desa", "referensi_wilayah",
        "referensi_koperasi_wilayah", "profil_koperasi", "pengurus_koperasi",
        "kbli_koperasi", "modal_koperasi", "simpanan_anggota", "pengajuan_pembiayaan",
        "transaksi_penjualan", "barang_keluar_produk",
    ],
}


def refresh(job: str, period: str | None = None) -> dict:
    period = period or settings.default_period
    jobs = {
        "koperasi_snapshot": lambda: etl_repository.run_logged(
            "koperasi_snapshot", SOURCE_TABLES["koperasi_snapshot"], etl_repository.refresh_koperasi_snapshot
        ),
        "koperasi_monthly_metrics": lambda: etl_repository.run_logged(
            "koperasi_monthly_metrics", SOURCE_TABLES["koperasi_monthly_metrics"],
            lambda: etl_repository.refresh_koperasi_monthly_metrics(period), {"period": period}
        ),
        "product_monthly_metrics": lambda: etl_repository.run_logged(
            "product_monthly_metrics", SOURCE_TABLES["product_monthly_metrics"],
            lambda: etl_repository.refresh_product_monthly_metrics(period), {"period": period}
        ),
        "rat_compliance": lambda: etl_repository.run_logged(
            "rat_compliance", SOURCE_TABLES["rat_compliance"], etl_repository.refresh_rat_compliance
        ),
        "gerai_asset": lambda: etl_repository.run_logged(
            "gerai_asset", SOURCE_TABLES["gerai_asset"], etl_repository.refresh_gerai_asset
        ),
        "village_potential": lambda: etl_repository.run_logged(
            "village_potential", SOURCE_TABLES["village_potential"], etl_repository.refresh_village_potential
        ),
        "regional_monthly_metrics": lambda: etl_repository.run_logged(
            "regional_monthly_metrics", SOURCE_TABLES["regional_monthly_metrics"],
            lambda: etl_repository.refresh_regional_monthly_metrics(period), {"period": period}
        ),
        "ui_screens": lambda: etl_repository.run_logged(
            "ui_screens", SOURCE_TABLES["ui_screens"], ui_backup_repository.refresh_ui_backup
        ),
    }
    if job not in jobs:
        raise ValueError(f"Unknown ETL job: {job}")
    return jobs[job]()


def refresh_all(period: str | None = None) -> dict:
    period = period or settings.default_period
    order = [
        "koperasi_snapshot", "koperasi_monthly_metrics", "product_monthly_metrics",
        "rat_compliance", "gerai_asset", "village_potential", "regional_monthly_metrics", "ui_screens",
    ]
    return {"period": period, "runs": [refresh(job, period) for job in order]}


def status() -> dict:
    return {"summary_tables": etl_repository.summary_tables(), "runs": etl_repository.latest_runs()}
