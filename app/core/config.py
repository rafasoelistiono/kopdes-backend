import os
from pathlib import Path
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()


class Settings:
    app_name: str = os.getenv("APP_NAME", "kopdes-backend")
    app_env: str = os.getenv("APP_ENV", "local")
    app_debug: bool = os.getenv("APP_DEBUG", "true").lower() == "true"
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")
    app_port: int = int(os.getenv("APP_PORT", "8000"))

    db_connection: str = os.getenv("DB_CONNECTION", "pgsql")
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", "5432"))
    db_database: str = os.getenv("DB_DATABASE", "hackathon_2026")
    db_username: str = os.getenv("DB_USERNAME", "")
    db_password: str = os.getenv("DB_PASSWORD", "")
    database_url: str = os.getenv("DATABASE_URL", "")
    source_database_url: str = os.getenv("SOURCE_DATABASE_URL", "")
    dashboard_database_url: str = os.getenv("DASHBOARD_DATABASE_URL", "")
    dashboard_sqlite_path: str = os.getenv("DASHBOARD_SQLITE_PATH", "data_backup/dashboard.db")

    table_prefix: str = os.getenv("TABLE_PREFIX", "group9_")

    api_prefix: str = os.getenv("API_PREFIX", "/api/v1")
    enable_meta_endpoint: bool = os.getenv("ENABLE_META_ENDPOINT", "true").lower() == "true"
    enable_admin_etl_endpoint: bool = os.getenv("ENABLE_ADMIN_ETL_ENDPOINT", "true").lower() == "true"
    enable_slow_fallback: bool = os.getenv("ENABLE_SLOW_FALLBACK", "false").lower() == "true"

    cors_origins: list[str] = [
        o.strip()
        for o in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
        if o.strip()
    ]

    default_period: str = os.getenv("DEFAULT_PERIOD", "2026-07")
    default_year: int = int(os.getenv("DEFAULT_YEAR", "2026"))
    default_page_size: int = int(os.getenv("DEFAULT_PAGE_SIZE", "20"))
    max_page_size: int = int(os.getenv("MAX_PAGE_SIZE", "100"))
    stale_after_minutes: int = int(os.getenv("STALE_AFTER_MINUTES", "15"))
    api_statement_timeout_ms: int = int(os.getenv("API_STATEMENT_TIMEOUT_MS", "3000"))
    etl_statement_timeout_ms: int = int(os.getenv("ETL_STATEMENT_TIMEOUT_MS", "120000"))

    enable_privacy_redaction: bool = os.getenv("ENABLE_PRIVACY_REDACTION", "true").lower() == "true"
    block_sensitive_fields: bool = os.getenv("BLOCK_SENSITIVE_FIELDS", "true").lower() == "true"

    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_sql: bool = os.getenv("LOG_SQL", "false").lower() == "true"

    @property
    def sync_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        encoded_password = quote_plus(self.db_password)
        return f"postgresql://{self.db_username}:{encoded_password}@{self.db_host}:{self.db_port}/{self.db_database}"

    @property
    def sync_source_database_url(self) -> str:
        return self.source_database_url or self.sync_database_url

    @property
    def sync_dashboard_database_url(self) -> str:
        if self.dashboard_database_url:
            return self.dashboard_database_url
        return f"sqlite:///{Path(self.dashboard_sqlite_path)}"


settings = Settings()
