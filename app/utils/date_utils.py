from datetime import datetime, date


def parse_period(period: str) -> tuple[int, int] | None:
    try:
        parts = period.split("-")
        return int(parts[0]), int(parts[1])
    except (IndexError, ValueError):
        return None


def period_range(start_period: str, end_period: str) -> list[str]:
    start = parse_period(start_period)
    end = parse_period(end_period)
    if not start or not end:
        return []
    periods = []
    year, month = start
    end_year, end_month = end
    while (year < end_year) or (year == end_year and month <= end_month):
        periods.append(f"{year}-{month:02d}")
        month += 1
        if month > 12:
            month = 1
            year += 1
    return periods


def previous_period(period: str) -> str:
    p = parse_period(period)
    if not p:
        return period
    year, month = p
    month -= 1
    if month < 1:
        month = 12
        year -= 1
    return f"{year}-{month:02d}"


def months_ago(months: int) -> str:
    today = date.today()
    m = today.month - months
    y = today.year
    while m < 1:
        m += 12
        y -= 1
    return f"{y}-{m:02d}"


def today_str() -> str:
    return date.today().isoformat()


def now_iso() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
