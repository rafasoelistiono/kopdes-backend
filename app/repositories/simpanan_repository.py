from app.core.database import execute_query
from app.repositories.schema_repository import table_exists


def get_simpanan_summary(koperasi_ref: str, period: str | None = None) -> dict:
    result = {"total": 0, "paid": 0, "unpaid": 0, "total_amount": 0, "paid_amount": 0}
    if not table_exists("simpanan_anggota"):
        return result

    params = {"koperasi_ref": koperasi_ref}
    period_filter = ""
    if period:
        period_filter = " AND periode_pembayaran = :period"
        params["period"] = period

    sql = f"""
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE status = 'paid') AS paid,
            COUNT(*) FILTER (WHERE status = 'unpaid') AS unpaid,
            COALESCE(SUM(jumlah_simpanan), 0) AS total_amount,
            COALESCE(SUM(jumlah_simpanan) FILTER (WHERE status = 'paid'), 0) AS paid_amount
        FROM simpanan_anggota
        WHERE koperasi_ref = :koperasi_ref{period_filter}
    """
    rows = execute_query(sql, params)
    if rows:
        r = rows[0]
        result = {
            "total": r["total"] or 0,
            "paid": r["paid"] or 0,
            "unpaid": r["unpaid"] or 0,
            "total_amount": float(r["total_amount"] or 0),
            "paid_amount": float(r["paid_amount"] or 0),
        }
    return result


def get_simpanan_summary_by_wilayah(kode_wilayah: str | None = None, provinsi: str | None = None,
                                     kab_kota: str | None = None, kecamatan: str | None = None,
                                     period: str | None = None) -> dict:
    result = {"total": 0, "paid": 0, "unpaid": 0, "total_amount": 0, "paid_amount": 0}
    if not table_exists("simpanan_anggota") or not table_exists("referensi_koperasi_wilayah"):
        return result

    conditions = ["sa.koperasi_ref = rkw.koperasi_ref"]
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
    if period:
        conditions.append("sa.periode_pembayaran = :period")
        params["period"] = period

    where = " AND ".join(conditions)
    sql = f"""
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE sa.status = 'paid') AS paid,
            COUNT(*) FILTER (WHERE sa.status = 'unpaid') AS unpaid,
            COALESCE(SUM(sa.jumlah_simpanan), 0) AS total_amount,
            COALESCE(SUM(sa.jumlah_simpanan) FILTER (WHERE sa.status = 'paid'), 0) AS paid_amount
        FROM simpanan_anggota sa
        JOIN referensi_koperasi_wilayah rkw ON sa.koperasi_ref = rkw.koperasi_ref
        WHERE {where}
    """
    rows = execute_query(sql, params)
    if rows:
        r = rows[0]
        result = {
            "total": r["total"] or 0,
            "paid": r["paid"] or 0,
            "unpaid": r["unpaid"] or 0,
            "total_amount": float(r["total_amount"] or 0),
            "paid_amount": float(r["paid_amount"] or 0),
        }
    return result
