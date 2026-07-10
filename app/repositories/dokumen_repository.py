from app.core.database import execute_query
from app.repositories.schema_repository import table_exists, column_exists


def get_document_compliance(koperasi_ref: str) -> dict:
    result = {"total_required": 0, "uploaded": 0, "missing": 0, "expiring_soon": 0}
    if not table_exists("dokumen_koperasi"):
        return result

    sql = """
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE unggahan_dokumen IS NOT NULL) AS uploaded
        FROM dokumen_koperasi
        WHERE koperasi_ref = :koperasi_ref
    """
    rows = execute_query(sql, {"koperasi_ref": koperasi_ref})
    if rows:
        r = rows[0]
        total = r["total"] or 0
        uploaded = r["uploaded"] or 0
        result = {
            "total_required": total,
            "uploaded": uploaded,
            "missing": total - uploaded,
            "expiring_soon": 0,
        }

    if column_exists("dokumen_koperasi", "tanggal_kadaluarsa"):
        exp_sql = """
            SELECT COUNT(*) AS expiring
            FROM dokumen_koperasi
            WHERE koperasi_ref = :koperasi_ref
              AND tanggal_kadaluarsa IS NOT NULL
              AND tanggal_kadaluarsa <= CURRENT_DATE + INTERVAL '30 days'
              AND tanggal_kadaluarsa >= CURRENT_DATE
        """
        exp_rows = execute_query(exp_sql, {"koperasi_ref": koperasi_ref})
        if exp_rows:
            result["expiring_soon"] = exp_rows[0]["expiring"] or 0
    return result


def get_document_summary_by_wilayah(kode_wilayah: str | None = None, provinsi: str | None = None,
                                     kab_kota: str | None = None, kecamatan: str | None = None) -> dict:
    result = {"total_required": 0, "uploaded": 0, "missing": 0}
    if not table_exists("dokumen_koperasi") or not table_exists("referensi_koperasi_wilayah"):
        return result

    conditions = ["dk.koperasi_ref = rkw.koperasi_ref"]
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
            COUNT(*) FILTER (WHERE dk.unggahan_dokumen IS NOT NULL) AS uploaded
        FROM dokumen_koperasi dk
        JOIN referensi_koperasi_wilayah rkw ON dk.koperasi_ref = rkw.koperasi_ref
        WHERE {where}
    """
    rows = execute_query(sql, params)
    if rows:
        r = rows[0]
        total = r["total"] or 0
        uploaded = r["uploaded"] or 0
        result = {"total_required": total, "uploaded": uploaded, "missing": total - uploaded}
    return result
