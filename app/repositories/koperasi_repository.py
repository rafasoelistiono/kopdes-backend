from app.core.database import execute_query
from app.repositories.schema_repository import table_exists


def get_koperasi_profile(koperasi_ref: str) -> dict | None:
    if not table_exists("profil_koperasi"):
        return None
    sql = """
        SELECT
            koperasi_ref, nama_koperasi, status_registrasi,
            bentuk_koperasi, kategori_usaha
        FROM profil_koperasi
        WHERE koperasi_ref = :koperasi_ref
        LIMIT 1
    """
    rows = execute_query(sql, {"koperasi_ref": koperasi_ref})
    return rows[0] if rows else None


def get_koperasi_by_wilayah(kode_wilayah: str | None = None, provinsi: str | None = None,
                             kab_kota: str | None = None, kecamatan: str | None = None,
                             desa_kelurahan: str | None = None) -> list[dict]:
    if not table_exists("profil_koperasi") or not table_exists("referensi_koperasi_wilayah"):
        return []
    conditions = ["pk.koperasi_ref = rkw.koperasi_ref"]
    params = {}
    if kode_wilayah:
        conditions.append("rkw.kode_wilayah = :kode_wilayah")
        params["kode_wilayah"] = kode_wilayah
    if provinsi:
        conditions.append("rkw.kode_wilayah LIKE :provinsi_prefix")
        params["provinsi_prefix"] = provinsi + "%"
    if kab_kota:
        conditions.append("rkw.kode_wilayah LIKE :kab_kota_prefix")
        params["kab_kota_prefix"] = kab_kota + "%"
    if kecamatan:
        conditions.append("rkw.kode_wilayah LIKE :kecamatan_prefix")
        params["kecamatan_prefix"] = kecamatan + "%"
    if desa_kelurahan:
        conditions.append("rkw.kode_wilayah LIKE :desa_prefix")
        params["desa_prefix"] = desa_kelurahan + "%"

    where = " AND ".join(conditions)
    sql = f"""
        SELECT pk.koperasi_ref, pk.nama_koperasi, pk.status_registrasi,
               pk.bentuk_koperasi, rkw.kode_wilayah
        FROM profil_koperasi pk
        JOIN referensi_koperasi_wilayah rkw ON pk.koperasi_ref = rkw.koperasi_ref
        WHERE {where}
        ORDER BY pk.nama_koperasi
    """
    return execute_query(sql, params)


def get_koperasi_counts_by_region(provinsi: str | None = None, kab_kota: str | None = None,
                                   kecamatan: str | None = None, kode_wilayah: str | None = None) -> dict:
    result = {"total": 0, "aktif": 0, "terdaftar": 0, "pending": 0}
    if not table_exists("profil_koperasi") or not table_exists("referensi_koperasi_wilayah"):
        return result

    conditions = ["pk.koperasi_ref = rkw.koperasi_ref"]
    params = {}
    if kode_wilayah:
        conditions.append("rkw.kode_wilayah = :kode_wilayah")
        params["kode_wilayah"] = kode_wilayah
    if provinsi:
        conditions.append("rkw.kode_wilayah LIKE :prov")
        params["prov"] = provinsi + "%"
    if kab_kota:
        conditions.append("rkw.kode_wilayah LIKE :kab")
        params["kab"] = kab_kota + "%"
    if kecamatan:
        conditions.append("rkw.kode_wilayah LIKE :kec")
        params["kec"] = kecamatan + "%"

    where = " AND ".join(conditions)
    sql = f"""
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE pk.status_registrasi = 'verified') AS aktif,
            COUNT(*) FILTER (WHERE pk.status_registrasi = 'registered') AS terdaftar,
            COUNT(*) FILTER (WHERE pk.status_registrasi = 'pending') AS pending
        FROM profil_koperasi pk
        JOIN referensi_koperasi_wilayah rkw ON pk.koperasi_ref = rkw.koperasi_ref
        WHERE {where}
    """
    rows = execute_query(sql, params)
    if rows:
        r = rows[0]
        result = {
            "total": r["total"] or 0,
            "aktif": r["aktif"] or 0,
            "terdaftar": r["terdaftar"] or 0,
            "pending": r["pending"] or 0,
        }
    return result
