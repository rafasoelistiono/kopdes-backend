import re


def safe_identifier(name: str) -> str:
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
        raise ValueError(f"Invalid identifier: {name}")
    return name


def safe_table_ref(table: str) -> str:
    parts = table.split(".")
    sanitized = [safe_identifier(p) for p in parts]
    return ".".join(sanitized)


def build_select(allowed: list[str], table: str, alias: str | None = None) -> str:
    cols = ", ".join(f'"{safe_identifier(c)}"' for c in allowed)
    tbl = safe_table_ref(table)
    if alias:
        return f"SELECT {cols} FROM {tbl} AS {safe_identifier(alias)}"
    return f"SELECT {cols} FROM {tbl}"


def build_where(conditions: list[str]) -> str:
    if not conditions:
        return ""
    return " WHERE " + " AND ".join(conditions)


def safe_param(key: str) -> str:
    k = safe_identifier(key.lstrip(":"))
    return f":{k}"
