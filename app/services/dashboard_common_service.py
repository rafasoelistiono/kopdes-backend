from app.utils.response import make_metadata
from app.utils.privacy import redact_nested_payload
from app.utils.date_utils import now_iso


def build_dashboard_base(
    dashboard_key: str,
    dashboard_title: str,
    role: str,
    scope: dict,
    filters: dict,
    source_tables: list[str],
    warnings: list[str] | None = None,
    summary_tables: list[str] | None = None,
    data_freshness: dict | None = None,
) -> dict:
    return {
        "success": True,
        "dashboard_key": dashboard_key,
        "dashboard_title": dashboard_title,
        "role": role,
        "scope": scope,
        "filters": filters,
        "kpis": [],
        "sections": [],
        "charts": [],
        "tables": [],
        "metadata": make_metadata(source_tables, warnings, summary_tables, data_freshness),
    }


def add_kpi(base: dict, kpi: dict):
    base["kpis"].append(kpi)


def add_section(base: dict, section: str):
    if section not in base["sections"]:
        base["sections"].append(section)


def add_chart(base: dict, chart: dict):
    base["charts"].append(chart)


def add_table(base: dict, table: dict):
    base["tables"].append(table)


def finalize(base: dict) -> dict:
    base["metadata"]["generated_at"] = now_iso()
    return redact_nested_payload(base)
