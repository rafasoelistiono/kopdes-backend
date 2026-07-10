from app.core.database import execute_query
from app.repositories.schema_repository import table_exists


def get_village_profile(kode_wilayah: str) -> dict | None:
    if not table_exists("referensi_profil_desa"):
        return None
    sql = """
        SELECT kode_wilayah, tahun_populasi, total_penduduk,
               penduduk_laki_laki, penduduk_perempuan,
               tahun_pendanaan, anggaran_dana_desa
        FROM referensi_profil_desa
        WHERE kode_wilayah = :kode_wilayah
        LIMIT 1
    """
    rows = execute_query(sql, {"kode_wilayah": kode_wilayah})
    return rows[0] if rows else None


def get_village_commodities(kode_wilayah: str) -> list[dict]:
    if not table_exists("referensi_komoditas_desa"):
        return []
    sql = """
        SELECT komoditas_ref, kode_wilayah, nama_komoditas,
               luas_area, volume, jumlah_sdm_terlibat, nilai_potensi_desa
        FROM referensi_komoditas_desa
        WHERE kode_wilayah = :kode_wilayah
        ORDER BY nilai_potensi_desa DESC NULLS LAST
    """
    return execute_query(sql, {"kode_wilayah": kode_wilayah})


def get_village_commodities_by_koperasi_wilayah(koperasi_ref: str) -> list[dict]:
    if not table_exists("referensi_komoditas_desa") or not table_exists("referensi_koperasi_wilayah"):
        return []
    sql = """
        SELECT rkd.*
        FROM referensi_komoditas_desa rkd
        JOIN referensi_koperasi_wilayah rkw ON rkd.kode_wilayah = rkw.kode_wilayah
        WHERE rkw.koperasi_ref = :koperasi_ref
        ORDER BY rkd.nilai_potensi_desa DESC NULLS LAST
    """
    return execute_query(sql, {"koperasi_ref": koperasi_ref})
