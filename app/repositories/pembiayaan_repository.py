from app.core.database import execute_query
from app.repositories.schema_repository import table_exists


def get_financing_summary(koperasi_ref: str) -> dict:
    result = {"total": 0, "pending": 0, "approved": 0, "rejected": 0, "total_nominal": 0}
    if not table_exists("pengajuan_pembiayaan"):
        return result
    sql = """
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE status_permohonan = 'pending') AS pending,
            COUNT(*) FILTER (WHERE status_permohonan = 'approved') AS approved,
            COUNT(*) FILTER (WHERE status_permohonan = 'rejected') AS rejected,
            COALESCE(SUM(nominal_permohonan), 0) AS total_nominal
        FROM pengajuan_pembiayaan
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
            "total_nominal": float(r["total_nominal"] or 0),
        }
    return result


def get_financing_summary_by_wilayah(kode_wilayah: str | None = None, provinsi: str | None = None,
                                      kab_kota: str | None = None, kecamatan: str | None = None) -> dict:
    result = {"total": 0, "pending": 0, "approved": 0, "rejected": 0, "total_nominal": 0}
    if not table_exists("pengajuan_pembiayaan") or not table_exists("referensi_koperasi_wilayah"):
        return result

    conditions = ["pp.koperasi_ref = rkw.koperasi_ref"]
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
            COUNT(*) FILTER (WHERE pp.status_permohonan = 'pending') AS pending,
            COUNT(*) FILTER (WHERE pp.status_permohonan = 'approved') AS approved,
            COUNT(*) FILTER (WHERE pp.status_permohonan = 'rejected') AS rejected,
            COALESCE(SUM(pp.nominal_permohonan), 0) AS total_nominal
        FROM pengajuan_pembiayaan pp
        JOIN referensi_koperasi_wilayah rkw ON pp.koperasi_ref = rkw.koperasi_ref
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
            "total_nominal": float(r["total_nominal"] or 0),
        }
    return result


def get_latest_financing_application(koperasi_ref: str) -> dict | None:
    if not table_exists("pengajuan_pembiayaan"):
        return None
    sql = """
        SELECT
            pengajuan_pembiayaan_ref, koperasi_ref,
            status_permohonan, nominal_permohonan, tenor,
            tujuan_permohonan, dibuat_pada
        FROM pengajuan_pembiayaan
        WHERE koperasi_ref = :koperasi_ref
        ORDER BY dibuat_pada DESC NULLS LAST
        LIMIT 1
    """
    rows = execute_query(sql, {"koperasi_ref": koperasi_ref})
    return rows[0] if rows else None


def get_financing_list(koperasi_ref: str, limit: int = 10) -> list[dict]:
    if not table_exists("pengajuan_pembiayaan"):
        return []
    sql = """
        SELECT
            pengajuan_pembiayaan_ref, status_permohonan,
            nominal_permohonan, tenor, tujuan_permohonan, dibuat_pada
        FROM pengajuan_pembiayaan
        WHERE koperasi_ref = :koperasi_ref
        ORDER BY dibuat_pada DESC NULLS LAST
        LIMIT :limit
    """
    return execute_query(sql, {"koperasi_ref": koperasi_ref, "limit": limit})
