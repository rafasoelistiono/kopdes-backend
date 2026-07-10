from datetime import datetime, timezone

from app.core.config import settings
from app.repositories import summary_repository


def get_data_freshness() -> dict:
    last = summary_repository.latest_etl_at()
    stale = True
    if last:
        parsed = datetime.strptime(last, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        stale = (datetime.now(timezone.utc) - parsed).total_seconds() > settings.stale_after_minutes * 60
    return {
        "last_etl_at": last,
        "is_stale": stale,
        "stale_after_minutes": settings.stale_after_minutes,
    }
