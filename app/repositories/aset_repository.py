from app.core.database import execute_query
from app.repositories.schema_repository import table_exists


def get_asset_progress(koperasi_ref: str) -> dict:
    result = {"total": 0, "not_started": 0, "in_progress": 0, "completed": 0}
    if not table_exists("aset_koperasi"):
        return result
    sql = """
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE progres_pembangunan IS NULL OR progres_pembangunan = 0) AS not_started,
            COUNT(*) FILTER (WHERE progres_pembangunan > 0 AND progres_pembangunan < 100) AS in_progress,
            COUNT(*) FILTER (WHERE progres_pembangunan = 100) AS completed
        FROM aset_koperasi
        WHERE koperasi_ref = :koperasi_ref
    """
    rows = execute_query(sql, {"koperasi_ref": koperasi_ref})
    if rows:
        r = rows[0]
        result = {
            "total": r["total"] or 0,
            "not_started": r["not_started"] or 0,
            "in_progress": r["in_progress"] or 0,
            "completed": r["completed"] or 0,
        }
    return result


def get_asset_progress_by_wilayah(kode_wilayah: str | None = None, provinsi: str | None = None,
                                   kab_kota: str | None = None, kecamatan: str | None = None) -> dict:
    result = {"total": 0, "not_started": 0, "in_progress": 0, "completed": 0}
    if not table_exists("aset_koperasi") or not table_exists("referensi_koperasi_wilayah"):
        return result

    conditions = ["ak.koperasi_ref = rkw.koperasi_ref"]
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
            COUNT(*) FILTER (WHERE ak.progres_pembangunan IS NULL OR ak.progres_pembangunan = 0) AS not_started,
            COUNT(*) FILTER (WHERE ak.progres_pembangunan > 0 AND ak.progres_pembangunan < 100) AS in_progress,
            COUNT(*) FILTER (WHERE ak.progres_pembangunan = 100) AS completed
        FROM aset_koperasi ak
        JOIN referensi_koperasi_wilayah rkw ON ak.koperasi_ref = rkw.koperasi_ref
        WHERE {where}
    """
    rows = execute_query(sql, params)
    if rows:
        r = rows[0]
        result = {
            "total": r["total"] or 0,
            "not_started": r["not_started"] or 0,
            "in_progress": r["in_progress"] or 0,
            "completed": r["completed"] or 0,
        }
    return result
