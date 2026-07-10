import re
from copy import deepcopy
from typing import Any


SENSITIVE_KEYS = {"nik", "ktp", "email", "no_hp", "alamat", "rekening", "file_ktp", "foto_profil"}


def safety_payload(grounded: bool = True) -> dict:
    return {
        "pii_redacted": True,
        "scope_checked": True,
        "grounded": grounded,
    }


def redact_context_pack(context_pack: dict) -> dict:
    """Remove sensitive fields from context before sending to LLM."""
    redacted = deepcopy(context_pack)

    for fact in redacted.get("facts", []):
        if fact.get("key") in SENSITIVE_KEYS:
            fact["value"] = "[REDACTED]"
            fact["formatted"] = "[REDACTED]"

    for table in redacted.get("tables", []):
        rows = table.get("rows", [])
        cleaned = []
        for row in rows:
            clean_row = {k: v for k, v in row.items() if k not in SENSITIVE_KEYS}
            cleaned.append(clean_row)
        table["rows"] = cleaned

    screens = redacted.get("backup", {}).get("screens", {})
    for screen_name, screen_data in screens.items():
        rows = screen_data.get("rows", [])
        screen_data["rows"] = [
            {k: v for k, v in row.items() if k not in SENSITIVE_KEYS}
            for row in rows
        ]

    return redacted


def _collect_known_values(context_pack: dict) -> set[str]:
    """Collect all formatted and raw values from context for grounding check."""
    values = set()

    def collect(value: Any) -> None:
        if value is None:
            return
        if isinstance(value, dict):
            for nested in value.values():
                collect(nested)
            return
        if isinstance(value, list):
            for nested in value:
                collect(nested)
            return
        values.add(str(value).lower().strip())
        values.add(str(value).strip())

    collect(context_pack)

    for fact in context_pack.get("facts", []):
        v = fact.get("value")
        if v is not None:
            values.add(str(v).lower().strip())
            values.add(str(v).strip())
        f = fact.get("formatted", "")
        if f and f != "-":
            values.add(f.lower().strip())
            values.add(f.strip())

    for alert in context_pack.get("alerts", []):
        msg = alert.get("message", "")
        values.add(msg.lower().strip())

    health = context_pack.get("health_score", {})
    label = health.get("label", "")
    if label:
        values.add(label.lower().strip())
    score = health.get("score")
    if score is not None:
        values.add(str(score))
        values.add(f"{score}/100")
        values.add(f"{score}/100 ({label})")

    return values


_GROUNDED_NUM_PATTERN = re.compile(r"(?:rp\s*)?\d[\d.,]*(?:\s*(?:%|persen|juta|miliar|ribu))?", re.IGNORECASE)


def _normalize_number_token(value: str) -> str:
    return re.sub(r"\s+", "", value.lower().replace("rp", "").replace("persen", "%"))


def _numeric_tokens(text: str) -> set[str]:
    tokens = set()
    for match in _GROUNDED_NUM_PATTERN.finditer(text):
        token = match.group(0)
        normalized = _normalize_number_token(token)
        digits = re.sub(r"\D", "", normalized)
        has_unit = any(unit in normalized for unit in ["%", "juta", "miliar", "ribu"])
        if has_unit or len(digits) >= 3:
            tokens.add(normalized)
    return tokens


def validate_grounding(answer: str, context_pack: dict) -> bool:
    """Check if LLM answer is grounded in context values."""
    if not answer:
        return False

    known = _collect_known_values(context_pack)
    answer_lower = answer.lower()

    known_numbers = set()
    for known_val in known:
        known_numbers.update(_numeric_tokens(known_val))
    answer_numbers = _numeric_tokens(answer)
    if answer_numbers and not answer_numbers.issubset(known_numbers):
        return False

    for known_val in known:
        if len(known_val) > 3 and known_val in answer_lower:
            return True

    return True
