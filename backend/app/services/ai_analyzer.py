import os
import httpx
from typing import Optional, Dict, Any, Tuple
from app.core.config import settings
from app.services.fingerprint import sanitize_text


def generate_heuristic_analysis(error_type: str, message: str, service: str) -> Tuple[str, str]:
    """Generates intelligent heuristic analysis if external AI is disabled or key not present."""
    msg_lower = message.lower()
    err_lower = error_type.lower()
    
    causes = []
    steps = []

    if "connection" in msg_lower or "connect" in err_lower or "timeout" in msg_lower:
        causes.append("Network partition, downstream service outage, or incorrect host/port configuration.")
        steps.append("Verify network connectivity and check target host/port.")
        steps.append("Inspect firewall, security groups, or container DNS resolution.")
        steps.append("Check if the downstream service is healthy and accepting connections.")
    elif "not found" in msg_lower or "404" in msg_lower or "keyerror" in err_lower:
        causes.append("Missing database record, invalid resource ID, or missing configuration key.")
        steps.append("Validate input parameters passed to service.")
        steps.append("Check database migrations or seed data.")
    elif "auth" in msg_lower or "permission" in msg_lower or "forbidden" in msg_lower:
        causes.append("Expired authentication token, invalid credentials, or insufficient role permissions.")
        steps.append("Check API credentials and token expiration times.")
        steps.append("Verify role-based access control (RBAC) policies.")
    elif "syntax" in err_lower or "typeerror" in err_lower:
        causes.append("Type mismatch or invalid schema during data serialization/deserialization.")
        steps.append("Check input payload validation and schema definitions.")
        steps.append("Inspect recent code deployment or schema migrations.")
    else:
        causes.append(f"Unexpected runtime failure in '{service}' while handling '{error_type}'.")
        steps.append("Inspect the sanitized stack trace for the failing line.")
        steps.append("Verify recent code releases and deployment logs.")

    summary = f"[AI Suggestion] The service '{service}' encountered a '{error_type}'. Primary likely cause: {causes[0]}"
    debug_plan = "\n".join([f"{i+1}. {step}" for i, step in enumerate(steps)])
    
    return summary, debug_plan


async def analyze_error(
    error_type: str,
    message: str,
    service: str,
    sanitized_stack_trace: Optional[str] = None
) -> Tuple[str, str]:
    """
    Analyzes error using configured AI provider (or heuristic fallback).
    Secrets are always redacted before sending.
    Returns (ai_summary, ai_suggested_fix).
    """
    clean_msg = sanitize_text(message) or ""
    clean_trace = sanitize_text(sanitized_stack_trace) or ""

    if not settings.AI_ANALYSIS_ENABLED or not settings.AI_API_KEY:
        return generate_heuristic_analysis(error_type, clean_msg, service)

    # If external AI API configured (e.g. Gemini), query securely
    try:
        # Prompt construction with strict safety rules
        prompt = (
            f"Analyze this software error for developer troubleshooting:\n"
            f"Service: {service}\n"
            f"Error Type: {error_type}\n"
            f"Message: {clean_msg[:500]}\n"
            f"Sanitized Stack Trace:\n{clean_trace[:1500]}\n\n"
            f"Provide:\n"
            f"1. Concise summary (2 sentences max)\n"
            f"2. Recommended debugging steps (numbered list)"
        )
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.AI_API_KEY}",
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.2, "maxOutputTokens": 350}
                }
            )
            if resp.status_code == 200:
                result = resp.json()
                text = result["candidates"][0]["content"]["parts"][0]["text"]
                return f"[AI Assistant Suggestion]\n{text}", "See AI suggestion above."
    except Exception:
        pass

    return generate_heuristic_analysis(error_type, clean_msg, service)

