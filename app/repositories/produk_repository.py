from app.core.database import execute_query
from app.repositories.schema_repository import table_exists


def get_top_products(koperasi_ref: str, period: str | None = None, limit: int = 10) -> list[dict]:
    if not table_exists("barang_keluar_produk"):
        return []
    params = {"koperasi_ref": koperasi_ref, "limit": limit}
    period_filter = ""
    if period:
        period_filter = " AND to_char(tanggal_keluar, 'YYYY-MM') = :period"
        params["period"] = period

    sql = f"""
        SELECT
            nama_produk,
            COALESCE(SUM(jumlah_keluar), 0) AS volume,
            COALESCE(SUM(total_nilai), 0) AS nilai
        FROM barang_keluar_produk
        WHERE koperasi_ref = :koperasi_ref{period_filter}
        GROUP BY nama_produk
        ORDER BY volume DESC
        LIMIT :limit
    """
    return execute_query(sql, params)


def get_slow_moving_products(koperasi_ref: str, period: str | None = None, limit: int = 10) -> list[dict]:
    if not table_exists("barang_keluar_produk"):
        return []
    params = {"koperasi_ref": koperasi_ref, "limit": limit}
    period_filter = ""
    if period:
        period_filter = " AND to_char(tanggal_keluar, 'YYYY-MM') = :period"
        params["period"] = period

    sql = f"""
        SELECT
            nama_produk,
            COALESCE(SUM(jumlah_keluar), 0) AS volume,
            COALESCE(SUM(total_nilai), 0) AS nilai
        FROM barang_keluar_produk
        WHERE koperasi_ref = :koperasi_ref{period_filter}
        GROUP BY nama_produk
        ORDER BY volume ASC
        LIMIT :limit
    """
    return execute_query(sql, params)


def get_inventory_summary(koperasi_ref: str) -> dict:
    result = {"total_products": 0, "out_of_stock": 0, "low_stock": 0, "overstock": 0}
    if not table_exists("inventaris_produk"):
        return result
    sql = """
        SELECT
            COUNT(*) AS total_products,
            COUNT(*) FILTER (WHERE stok = 0 OR stok IS NULL) AS out_of_stock,
            COUNT(*) FILTER (WHERE stok > 0 AND stok <= 10) AS low_stock,
            COUNT(*) FILTER (WHERE stok > 100) AS overstock
        FROM inventaris_produk
        WHERE koperasi_ref = :koperasi_ref
    """
    rows = execute_query(sql, {"koperasi_ref": koperasi_ref})
    if rows:
        r = rows[0]
        result = {
            "total_products": r["total_products"] or 0,
            "out_of_stock": r["out_of_stock"] or 0,
            "low_stock": r["low_stock"] or 0,
            "overstock": r["overstock"] or 0,
        }
    return result


def get_stock_problem_products(koperasi_ref: str) -> list[dict]:
    if not table_exists("inventaris_produk"):
        return []
    sql = """
        SELECT
            nama_produk, stok,
            CASE
                WHEN stok = 0 OR stok IS NULL THEN 'out_of_stock'
                WHEN stok <= 10 THEN 'low_stock'
                WHEN stok > 100 THEN 'overstock'
                ELSE 'normal'
            END AS status
        FROM inventaris_produk
        WHERE koperasi_ref = :koperasi_ref
          AND (stok = 0 OR stok IS NULL OR stok <= 10 OR stok > 100)
        ORDER BY stok ASC
    """
    return execute_query(sql, {"koperasi_ref": koperasi_ref})
