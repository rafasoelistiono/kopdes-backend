import logging
from app.core.config import settings


def setup_logging():
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    if settings.log_sql:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)


logger = logging.getLogger("kopdes-backend")
