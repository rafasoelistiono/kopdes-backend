from app.core.database import execute_query
from app.repositories.schema_repository import table_exists


def get_member_summary(koperasi_ref: str) -> dict:
    result = {"total": 0, "approved": 0, "requested": 0, "pending": 0, "male": 0, "female": 0}
    if not table_exists("anggota_koperasi"):
        return result
    sql = """
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE status_keanggotaan = 'approved') AS approved,
            COUNT(*) FILTER (WHERE status_keanggotaan = 'requested') AS requested,
            COUNT(*) FILTER (WHERE status_keanggotaan = 'pending') AS pending
        FROM anggota_koperasi
        WHERE koperasi_ref = :koperasi_ref
    """
    rows = execute_query(sql, {"koperasi_ref": koperasi_ref})
    if rows:
        r = rows[0]
        result.update({
            "total": r["total"] or 0,
            "approved": r["approved"] or 0,
            "requested": r["requested"] or 0,
            "pending": r["pending"] or 0,
        })
    return result


def get_member_summary_by_wilayah(kode_wilayah: str | None = None, provinsi: str | None = None,
                                   kab_kota: str | None = None, kecamatan: str | None = None) -> dict:
    result = {"total": 0, "approved": 0}
    if not table_exists("anggota_koperasi") or not table_exists("referensi_koperasi_wilayah"):
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
            COUNT(*) FILTER (WHERE ak.status_keanggotaan = 'approved') AS approved
        FROM anggota_koperasi ak
        JOIN referensi_koperasi_wilayah rkw ON ak.koperasi_ref = rkw.koperasi_ref
        WHERE {where}
    """
    rows = execute_query(sql, params)
    if rows:
        r = rows[0]
        result = {"total": r["total"] or 0, "approved": r["approved"] or 0}
    return result


def get_total_members_by_koperasi(koperasi_refs: list[str]) -> dict[str, int]:
    if not table_exists("anggota_koperasi") or not koperasi_refs:
        return {}
    placeholders = ", ".join(f":kr{i}" for i in range(len(koperasi_refs)))
    params = {f"kr{i}": ref for i, ref in enumerate(koperasi_refs)}
    sql = f"""
        SELECT koperasi_ref, COUNT(*) AS total
        FROM anggota_koperasi
        WHERE koperasi_ref IN ({placeholders})
        GROUP BY koperasi_ref
    """
    rows = execute_query(sql, params)
    return {r["koperasi_ref"]: r["total"] or 0 for r in rows}
