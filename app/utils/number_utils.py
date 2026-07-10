def format_currency(value: float | int | None) -> str:
    if value is None:
        return "Rp0"
    return f"Rp{value:,.0f}".replace(",", ".")


def format_number(value: float | int | None) -> str:
    if value is None:
        return "0"
    return f"{value:,.0f}".replace(",", ".")


def format_percent(value: float | None, decimals: int = 2) -> str:
    if value is None:
        return "0%"
    return f"{value:.{decimals}f}%".replace(".", ",")


def growth_percent(current: float | int | None, previous: float | int | None) -> float | None:
    if current is None or previous is None or previous == 0:
        return None
    return round((current - previous) / previous * 100, 2)


def paid_ratio(paid: float | int | None, total: float | int | None) -> float | None:
    if total is None or total == 0:
        return None
    return round((paid or 0) / total * 100, 2)


def avg_transaction_value(total: float | int | None, count: int | None) -> float | None:
    if total is None or count is None or count == 0:
        return None
    return round(total / count, 2)


def safe_division(numerator: float | int | None, denominator: float | int | None) -> float | None:
    if numerator is None or denominator is None or denominator == 0:
        return None
    return round(numerator / denominator, 4)
