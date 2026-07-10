from app.core.database import execute_query
from app.repositories.schema_repository import table_exists


def get_latest_rat_status(koperasi_ref: str) -> dict | None:
    if not table_exists("rat_koperasi"):
        return None
    sql = """
        SELECT
            rat_sample_id, koperasi_ref, urutan_rat, tahun_buku,
            tanggal_rat, status_rat, tahap_rat, jumlah_peserta_rat
        FROM rat_koperasi
        WHERE koperasi_ref = :koperasi_ref
        ORDER BY tahun_buku DESC NULLS LAST, tanggal_rat DESC NULLS LAST
        LIMIT 1
    """
    rows = execute_query(sql, {"koperasi_ref": koperasi_ref})
    return rows[0] if rows else None


def get_rat_summary_by_wilayah(kode_wilayah: str | None = None, provinsi: str | None = None,
                                kab_kota: str | None = None, kecamatan: str | None = None,
                                year: int | None = None) -> dict:
    result = {"total_rat": 0, "verified": 0, "draft": 0, "none": 0}
    if not table_exists("rat_koperasi") or not table_exists("referensi_koperasi_wilayah"):
        return result

    conditions = ["rk.koperasi_ref = rkw.koperasi_ref"]
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
    if year:
        conditions.append("(rk.tahun_buku = :year OR rk.tahun_rencana_kerja = :year)")
        params["year"] = year

    where = " AND ".join(conditions)
    sql = f"""
        SELECT
            COUNT(*) AS total_rat,
            COUNT(*) FILTER (WHERE rk.status_rat = 'verified') AS verified,
            COUNT(*) FILTER (WHERE rk.status_rat = 'draft') AS draft
        FROM rat_koperasi rk
        JOIN referensi_koperasi_wilayah rkw ON rk.koperasi_ref = rkw.koperasi_ref
        WHERE {where}
    """
    rows = execute_query(sql, params)
    if rows:
        r = rows[0]
        result = {
            "total_rat": r["total_rat"] or 0,
            "verified": r["verified"] or 0,
            "draft": r["draft"] or 0,
        }
    return result
