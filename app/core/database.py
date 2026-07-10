from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from app.core.config import settings


source_engine: Engine | None = None
dashboard_engine: Engine | None = None


def get_engine() -> Engine:
    return get_source_engine()


def _create_engine(url: str) -> Engine:
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    if url.startswith("sqlite"):
        from pathlib import Path

        db_path = url.replace("sqlite:///", "", 1)
        if db_path and db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    return create_engine(
        url,
        pool_pre_ping=True,
        echo=settings.log_sql,
    )


def _is_sqlite(conn) -> bool:
    return conn.dialect.name == "sqlite"


def get_source_engine() -> Engine:
    global source_engine
    if source_engine is None:
        source_engine = _create_engine(settings.sync_source_database_url)
    return source_engine


def get_dashboard_engine() -> Engine:
    global dashboard_engine
    if dashboard_engine is None:
        dashboard_engine = _create_engine(settings.sync_dashboard_database_url)
    return dashboard_engine


def get_connection():
    return get_source_engine().connect()


def get_dashboard_connection():
    return get_dashboard_engine().connect()


def execute_query(sql: str, params: dict | None = None) -> list[dict]:
    with get_connection() as conn:
        conn.execute(text(f"SET LOCAL statement_timeout = {int(settings.api_statement_timeout_ms)}"))
        result = conn.execute(text(sql), params or {})
        if result.returns_rows:
            return [dict(row._mapping) for row in result]
        return []


def execute_dashboard_query(sql: str, params: dict | None = None) -> list[dict]:
    with get_dashboard_connection() as conn:
        if not _is_sqlite(conn):
            conn.execute(text(f"SET LOCAL statement_timeout = {int(settings.api_statement_timeout_ms)}"))
        result = conn.execute(text(sql), params or {})
        if result.returns_rows:
            return [dict(row._mapping) for row in result]
        return []


def execute_write(sql: str, params: dict | None = None, timeout_ms: int | None = None) -> int:
    with get_dashboard_engine().begin() as conn:
        if not _is_sqlite(conn):
            conn.execute(text(f"SET LOCAL statement_timeout = {int(timeout_ms or settings.etl_statement_timeout_ms)}"))
        result = conn.execute(text(sql), params or {})
        return result.rowcount or 0


def execute_scalar(sql: str, params: dict | None = None):
    with get_connection() as conn:
        conn.execute(text(f"SET LOCAL statement_timeout = {int(settings.api_statement_timeout_ms)}"))
        result = conn.execute(text(sql), params or {})
        row = result.fetchone()
        if row:
            return row[0]
        return None
