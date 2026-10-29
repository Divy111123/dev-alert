import re
import hashlib
from typing import Optional


# Regular expressions for scrubbing sensitive data and dynamic tokens
RE_SECRET_KEY = re.compile(r'(?i)(password|secret|token|api[_-]?key|auth|bearer|credentials)[\s:=]+["\']?([^"\'\s,;]+)["\']?')
RE_HEX_ADDR = re.compile(r'0x[0-9a-fA-F]+')
RE_UUID = re.compile(r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}')
RE_TIMESTAMP = re.compile(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?')
RE_IP_ADDR = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
RE_NUMBERS = re.compile(r'\b\d{5,}\b')  # Large integers like IDs


def sanitize_text(text: Optional[str]) -> Optional[str]:
    """Sanitizes sensitive information such as secrets, auth tokens, passwords."""
    if not text:
        return text
    
    # Redact secret patterns
    sanitized = RE_SECRET_KEY.sub(r'\1: [REDACTED]', text)
    return sanitized


def normalize_for_fingerprint(text: Optional[str]) -> str:
    """Normalizes message or trace by removing transient values (timestamps, addresses, IDs)."""
    if not text:
        return ""
    
    normalized = RE_HEX_ADDR.sub('<HEX_ADDR>', text)
    normalized = RE_UUID.sub('<UUID>', normalized)
    normalized = RE_TIMESTAMP.sub('<TIMESTAMP>', normalized)
    normalized = RE_IP_ADDR.sub('<IP>', normalized)
    normalized = RE_NUMBERS.sub('<ID>', normalized)
    return normalized.strip()


def compute_fingerprint(
    project_id: str,
    error_type: str,
    message: str,
    service: str,
    stack_trace: Optional[str] = None
) -> str:
    """
    Computes a stable fingerprint hash for grouping duplicate errors.
    Uses project_id, normalized error_type, normalized service, normalized message,
    and the top significant stack frame if present.
    """
    clean_error_type = error_type.strip().lower()
    clean_service = (service or "default").strip().lower()
    clean_message = normalize_for_fingerprint(message)
    
    top_frame = ""
    if stack_trace:
        # Extract the last few lines or first error frame from stack trace
        lines = [line.strip() for line in stack_trace.splitlines() if line.strip()]
        for line in reversed(lines):
            if line.startswith("File ") or "line " in line or "at " in line:
                top_frame = normalize_for_fingerprint(line)
                break
        if not top_frame and lines:
            top_frame = normalize_for_fingerprint(lines[-1])

    # When a stack trace frame is available, group on the code location (top frame)
    # rather than variable message strings. If no stack frame, group on normalized message.
    if top_frame:
        raw_key = f"{project_id}|{clean_service}|{clean_error_type}|{top_frame}"
    else:
        raw_key = f"{project_id}|{clean_service}|{clean_error_type}|{clean_message[:200]}"

    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
