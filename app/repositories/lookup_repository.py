from app.core.database import execute_query
from app.repositories.schema_repository import table_exists


def get_wilayah_options(provinsi: str | None = None, kab_kota: str | None = None,
                         kecamatan: str | None = None) -> list[dict]:
    if not table_exists("referensi_wilayah"):
        return []
    conditions = []
    params = {}
    if provinsi:
        conditions.append("provinsi = :provinsi")
        params["provinsi"] = provinsi
    if kab_kota:
        conditions.append("kab_kota = :kab_kota")
        params["kab_kota"] = kab_kota
    if kecamatan:
        conditions.append("kecamatan = :kecamatan")
        params["kecamatan"] = kecamatan

    where = " AND ".join(conditions) if conditions else "TRUE"
    sql = f"""
        SELECT DISTINCT kode_wilayah, provinsi, kab_kota, kecamatan, desa_kelurahan
        FROM referensi_wilayah
        WHERE {where}
        ORDER BY kode_wilayah
        LIMIT 500
    """
    return execute_query(sql, params)


def get_koperasi_options(provinsi: str | None = None, kab_kota: str | None = None,
                          kecamatan: str | None = None, desa_kelurahan: str | None = None,
                          limit: int = 200) -> list[dict]:
    if not table_exists("profil_koperasi"):
        return []

    if not table_exists("referensi_koperasi_wilayah"):
        sql = """
            SELECT koperasi_ref, nama_koperasi
            FROM profil_koperasi
            ORDER BY nama_koperasi
            LIMIT :limit
        """
        return execute_query(sql, {"limit": limit})

    conditions = ["pk.koperasi_ref = rkw.koperasi_ref"]
    params = {"limit": limit}
    if provinsi:
        conditions.append("rkw.kode_wilayah LIKE :prov")
        params["prov"] = provinsi + "%"
    if kab_kota:
        conditions.append("rkw.kode_wilayah LIKE :kab")
        params["kab"] = kab_kota + "%"
    if kecamatan:
        conditions.append("rkw.kode_wilayah LIKE :kec")
        params["kec"] = kecamatan + "%"
    if desa_kelurahan:
        conditions.append("rkw.kode_wilayah = :desa")
        params["desa"] = desa_kelurahan

    where = " AND ".join(conditions)
    sql = f"""
        SELECT pk.koperasi_ref, pk.nama_koperasi
        FROM profil_koperasi pk
        JOIN referensi_koperasi_wilayah rkw ON pk.koperasi_ref = rkw.koperasi_ref
        WHERE {where}
        ORDER BY pk.nama_koperasi
        LIMIT :limit
    """
    return execute_query(sql, params)


def get_status_options() -> list[dict]:
    return [
        {"key": "all", "label": "Semua"},
        {"key": "active", "label": "Aktif"},
        {"key": "inactive", "label": "Tidak Aktif"},
        {"key": "pending", "label": "Pending"},
        {"key": "verified", "label": "Terverifikasi"},
        {"key": "draft", "label": "Draft"},
        {"key": "approved", "label": "Disetujui"},
        {"key": "rejected", "label": "Ditolak"},
    ]
