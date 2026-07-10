from app.core.database import execute_query
from app.repositories.schema_repository import table_exists


def get_transaction_summary(koperasi_ref: str, period: str | None = None) -> dict:
    result = {"total_transactions": 0, "total_value": 0, "average_value": 0}
    if not table_exists("transaksi_penjualan"):
        return result

    params = {"koperasi_ref": koperasi_ref}
    period_filter = ""
    if period:
        period_filter = " AND to_char(tanggal_dibuat, 'YYYY-MM') = :period"
        params["period"] = period

    sql = f"""
        SELECT
            COUNT(*) AS total_transactions,
            COALESCE(SUM(total_pembayaran), 0) AS total_value
        FROM transaksi_penjualan
        WHERE koperasi_ref = :koperasi_ref{period_filter}
    """
    rows = execute_query(sql, params)
    if rows:
        r = rows[0]
        total = r["total_transactions"] or 0
        value = float(r["total_value"] or 0)
        result = {
            "total_transactions": total,
            "total_value": value,
            "average_value": round(value / total, 2) if total > 0 else 0,
        }
    return result


def get_transaction_trend(koperasi_ref: str, months: int = 6) -> list[dict]:
    if not table_exists("transaksi_penjualan"):
        return []
    sql = """
        SELECT
            to_char(tanggal_dibuat, 'YYYY-MM') AS period,
            COUNT(*) AS total_transactions,
            COALESCE(SUM(total_pembayaran), 0) AS total_value
        FROM transaksi_penjualan
        WHERE koperasi_ref = :koperasi_ref
          AND tanggal_dibuat >= CURRENT_DATE - INTERVAL '6 months'
        GROUP BY to_char(tanggal_dibuat, 'YYYY-MM')
        ORDER BY period
    """
    return execute_query(sql, {"koperasi_ref": koperasi_ref})


def get_transaction_summary_by_wilayah(kode_wilayah: str | None = None, provinsi: str | None = None,
                                        kab_kota: str | None = None, kecamatan: str | None = None,
                                        period: str | None = None) -> dict:
    result = {"total_transactions": 0, "total_value": 0}
    if not table_exists("transaksi_penjualan") or not table_exists("referensi_koperasi_wilayah"):
        return result

    conditions = ["tp.koperasi_ref = rkw.koperasi_ref"]
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
        conditions.append("to_char(tp.tanggal_dibuat, 'YYYY-MM') = :period")
        params["period"] = period

    where = " AND ".join(conditions)
    sql = f"""
        SELECT
            COUNT(*) AS total_transactions,
            COALESCE(SUM(tp.total_pembayaran), 0) AS total_value
        FROM transaksi_penjualan tp
        JOIN referensi_koperasi_wilayah rkw ON tp.koperasi_ref = rkw.koperasi_ref
        WHERE {where}
    """
    rows = execute_query(sql, params)
    if rows:
        r = rows[0]
        result = {
            "total_transactions": r["total_transactions"] or 0,
            "total_value": float(r["total_value"] or 0),
        }
    return result


def get_transactions_by_period(koperasi_ref: str, start_period: str, end_period: str) -> list[dict]:
    if not table_exists("transaksi_penjualan"):
        return []
    sql = """
        SELECT
            to_char(tanggal_dibuat, 'YYYY-MM') AS period,
            COUNT(*) AS total_transactions,
            COALESCE(SUM(total_pembayaran), 0) AS total_value
        FROM transaksi_penjualan
        WHERE koperasi_ref = :koperasi_ref
          AND to_char(tanggal_dibuat, 'YYYY-MM') >= :start_period
          AND to_char(tanggal_dibuat, 'YYYY-MM') <= :end_period
        GROUP BY to_char(tanggal_dibuat, 'YYYY-MM')
        ORDER BY period
    """
    return execute_query(sql, {
        "koperasi_ref": koperasi_ref,
        "start_period": start_period,
        "end_period": end_period,
    })
