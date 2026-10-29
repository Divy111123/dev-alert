import re
from typing import Any, Dict

RE_SENSITIVE = re.compile(
    r'(?i)(password|secret|token|api[_-]?key|auth|bearer|credentials|private[_-]?key|card[_-]?number|cvv)'
)


def sanitize_value(key: str, value: Any) -> Any:
    if RE_SENSITIVE.search(str(key)):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {k: sanitize_value(k, v) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize_value(key, v) for v in value]
    return value


def sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict):
        return {}
    return {k: sanitize_value(k, v) for k, v in data.items()}
