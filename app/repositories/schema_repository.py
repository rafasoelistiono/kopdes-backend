from app.core.database import execute_query, execute_dashboard_query
from app.core.config import settings
from functools import lru_cache


@lru_cache(maxsize=1)
def list_tables() -> list[str]:
    sql = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name
    """
    rows = execute_query(sql)
    return [r["table_name"] for r in rows]


def list_columns(table_name: str) -> list[dict]:
    return _list_columns_cached(table_name)


@lru_cache(maxsize=256)
def _list_columns_cached(table_name: str) -> list[dict]:
    sql = """
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = :table_name
        ORDER BY ordinal_position
    """
    return execute_query(sql, {"table_name": table_name})


def table_exists(table_name: str) -> bool:
    tables = list_tables()
    return table_name in tables


@lru_cache(maxsize=1)
def list_dashboard_tables() -> list[str]:
    if settings.sync_dashboard_database_url.startswith("sqlite"):
        rows = execute_dashboard_query("""
            SELECT name AS table_name
            FROM sqlite_master
            WHERE type = 'table'
            ORDER BY name
        """)
        return [r["table_name"] for r in rows]
    sql = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name
    """
    rows = execute_dashboard_query(sql)
    return [r["table_name"] for r in rows]


def dashboard_table_exists(table_name: str) -> bool:
    return table_name in list_dashboard_tables()


def column_exists(table_name: str, column_name: str) -> bool:
    cols = list_columns(table_name)
    return any(c["column_name"] == column_name for c in cols)


def get_column_names(table_name: str) -> list[str]:
    cols = list_columns(table_name)
    return [c["column_name"] for c in cols]


def get_all_foreign_keys() -> list[dict]:
    sql = """
        SELECT
            tc.table_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND tc.table_schema = 'public'
    """
    return execute_query(sql)
