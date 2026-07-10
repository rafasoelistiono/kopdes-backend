from typing import Any
from datetime import datetime


def api_response(
    success: bool,
    dashboard_key: str | None = None,
    dashboard_title: str | None = None,
    role: str | None = None,
    scope: dict | None = None,
    filters: dict | None = None,
    kpis: list | None = None,
    sections: list | None = None,
    charts: list | None = None,
    tables: list | None = None,
    metadata: dict | None = None,
    data: Any = None,
    message: str | None = None,
) -> dict:
    base = {"success": success}
    if dashboard_key is not None:
        base["dashboard_key"] = dashboard_key
    if dashboard_title is not None:
        base["dashboard_title"] = dashboard_title
    if role is not None:
        base["role"] = role
    if scope is not None:
        base["scope"] = scope
    if filters is not None:
        base["filters"] = filters
    if kpis is not None:
        base["kpis"] = kpis
    if sections is not None:
        base["sections"] = sections
    if charts is not None:
        base["charts"] = charts
    if tables is not None:
        base["tables"] = tables
    if metadata is not None:
        base["metadata"] = metadata
    if data is not None:
        base["data"] = data
    if message is not None:
        base["message"] = message
    return base


def make_metadata(
    source_tables: list[str] | None = None,
    warnings: list[str] | None = None,
    summary_tables: list[str] | None = None,
    data_freshness: dict | None = None,
) -> dict:
    return {
        "source_mode": "summary_tables",
        "source_tables": source_tables or [],
        "summary_tables": summary_tables or [],
        "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "data_freshness": data_freshness,
        "warnings": warnings or [],
    }


def make_kpi(
    key: str,
    label: str,
    value: Any,
    unit: str = "number",
    trend: dict | None = None,
    status: str = "neutral",
) -> dict:
    from app.utils.number_utils import format_currency, format_number

    if value is None:
        formatted = "-"
    elif isinstance(value, str):
        formatted = value
    elif unit == "currency":
        formatted = format_currency(value)
    elif unit == "percent":
        formatted = f"{value}%" if value is not None else "0%"
    else:
        formatted = format_number(value)
    return {
        "key": key,
        "label": label,
        "value": value,
        "formatted_value": formatted,
        "unit": unit,
        "trend": trend,
        "status": status,
    }


def make_chart(key: str, title: str, chart_type: str, x_key: str, y_key: str, data: list) -> dict:
    return {
        "key": key,
        "title": title,
        "type": chart_type,
        "x_key": x_key,
        "y_key": y_key,
        "data": data,
    }


def make_table(key: str, title: str, columns: list[dict], rows: list[dict]) -> dict:
    return {
        "key": key,
        "title": title,
        "columns": columns,
        "rows": rows,
    }


def trend(direction: str, percentage: float | None, label: str) -> dict | None:
    return {
        "direction": direction,
        "percentage": percentage,
        "label": label,
    }
