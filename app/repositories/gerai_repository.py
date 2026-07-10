from app.core.database import execute_query
from app.repositories.schema_repository import table_exists


def get_gerai_status(koperasi_ref: str) -> dict:
    result = {"total": 0, "active": 0, "inactive": 0, "with_electricity": 0, "with_internet": 0}
    if not table_exists("gerai_koperasi"):
        return result
    sql = """
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE status_gerai = 'active') AS active,
            COUNT(*) FILTER (WHERE status_gerai = 'inactive') AS inactive,
            COUNT(*) FILTER (WHERE akses_listrik = 'yes') AS with_electricity,
            COUNT(*) FILTER (WHERE akses_internet = 'yes') AS with_internet
        FROM gerai_koperasi
        WHERE koperasi_ref = :koperasi_ref
    """
    rows = execute_query(sql, {"koperasi_ref": koperasi_ref})
    if rows:
        r = rows[0]
        result = {
            "total": r["total"] or 0,
            "active": r["active"] or 0,
            "inactive": r["inactive"] or 0,
            "with_electricity": r["with_electricity"] or 0,
            "with_internet": r["with_internet"] or 0,
        }
    return result


def get_gerai_summary_by_wilayah(kode_wilayah: str | None = None, provinsi: str | None = None,
                                  kab_kota: str | None = None, kecamatan: str | None = None) -> dict:
    result = {"total": 0, "active": 0, "inactive": 0}
    if not table_exists("gerai_koperasi") or not table_exists("referensi_koperasi_wilayah"):
        return result

    conditions = ["gk.koperasi_ref = rkw.koperasi_ref"]
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
            COUNT(*) FILTER (WHERE gk.status_gerai = 'active') AS active,
            COUNT(*) FILTER (WHERE gk.status_gerai = 'inactive') AS inactive
        FROM gerai_koperasi gk
        JOIN referensi_koperasi_wilayah rkw ON gk.koperasi_ref = rkw.koperasi_ref
        WHERE {where}
    """
    rows = execute_query(sql, params)
    if rows:
        r = rows[0]
        result = {
            "total": r["total"] or 0,
            "active": r["active"] or 0,
            "inactive": r["inactive"] or 0,
        }
    return result


def get_gerai_details_by_wilayah(filters: dict) -> list[dict]:
    if not table_exists("gerai_koperasi") or not table_exists("referensi_koperasi_wilayah"):
        return []

    conditions = ["gk.koperasi_ref = rkw.koperasi_ref"]
    params = {}
    for key, col in [("kode_wilayah", "rkw.kode_wilayah = :kode_wilayah"),
                      ("provinsi", "rkw.kode_wilayah LIKE :prov"),
                      ("kab_kota", "rkw.kode_wilayah LIKE :kab"),
                      ("kecamatan", "rkw.kode_wilayah LIKE :kec")]:
        val = filters.get(key)
        if val:
            conditions.append(col)
            param_key = col.split(":")[1]
            params[param_key] = val + "%" if key != "kode_wilayah" else val

    where = " AND ".join(conditions)
    sql = f"""
        SELECT gk.*, rkw.kode_wilayah
        FROM gerai_koperasi gk
        JOIN referensi_koperasi_wilayah rkw ON gk.koperasi_ref = rkw.koperasi_ref
        WHERE {where}
        ORDER BY gk.koperasi_ref
    """
    return execute_query(sql, params)
