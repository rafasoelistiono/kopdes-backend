from app.core.database import execute_query
from app.repositories.schema_repository import table_exists


def get_partnership_summary(koperasi_ref: str) -> dict:
    result = {"total": 0, "pending": 0, "approved": 0, "rejected": 0}
    if not table_exists("pengajuan_kemitraan"):
        return result
    sql = """
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE status_permohonan = 'pending') AS pending,
            COUNT(*) FILTER (WHERE status_permohonan = 'approved') AS approved,
            COUNT(*) FILTER (WHERE status_permohonan = 'rejected') AS rejected
        FROM pengajuan_kemitraan
        WHERE koperasi_ref = :koperasi_ref
    """
    rows = execute_query(sql, {"koperasi_ref": koperasi_ref})
    if rows:
        r = rows[0]
        result = {
            "total": r["total"] or 0,
            "pending": r["pending"] or 0,
            "approved": r["approved"] or 0,
            "rejected": r["rejected"] or 0,
        }
    return result


def get_partnership_summary_by_wilayah(kode_wilayah: str | None = None, provinsi: str | None = None,
                                        kab_kota: str | None = None, kecamatan: str | None = None) -> dict:
    result = {"total": 0, "pending": 0, "approved": 0, "rejected": 0}
    if not table_exists("pengajuan_kemitraan") or not table_exists("referensi_koperasi_wilayah"):
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
            COUNT(*) FILTER (WHERE pk.status_permohonan = 'pending') AS pending,
            COUNT(*) FILTER (WHERE pk.status_permohonan = 'approved') AS approved,
            COUNT(*) FILTER (WHERE pk.status_permohonan = 'rejected') AS rejected
        FROM pengajuan_kemitraan pk
        JOIN referensi_koperasi_wilayah rkw ON pk.koperasi_ref = rkw.koperasi_ref
        WHERE {where}
    """
    rows = execute_query(sql, params)
    if rows:
        r = rows[0]
        result = {
            "total": r["total"] or 0,
            "pending": r["pending"] or 0,
            "approved": r["approved"] or 0,
            "rejected": r["rejected"] or 0,
        }
    return result
