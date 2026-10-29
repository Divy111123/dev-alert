import sys
import os
import random
import traceback
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Dict, Any, Union
import httpx

from devalert.sanitizer import sanitize_dict

logger = logging.getLogger("devalert")


class DevAlertClient:
    def __init__(
        self,
        api_key: str,
        endpoint: str = "http://localhost:8000/api/v1/events",
        environment: str = "production",
        service: str = "default-service",
        release: Optional[str] = None,
        sample_rate: float = 1.0,
        timeout: float = 5.0,
        async_delivery: bool = True,
        auto_capture_uncaught: bool = True
    ):
        self.api_key = api_key
        self.endpoint = endpoint.rstrip("/")
        self.environment = environment
        self.service = service
        self.release = release
        self.sample_rate = max(0.0, min(1.0, sample_rate))
        self.timeout = timeout
        self.async_delivery = async_delivery
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="devalert-worker") if async_delivery else None

        if auto_capture_uncaught:
            self._install_excepthook()

    def _install_excepthook(self):
        original_excepthook = sys.excepthook

        def devalert_excepthook(exc_type, exc_value, exc_traceback):
            try:
                self.capture_exception(
                    exc=exc_value,
                    severity="critical",
                    metadata={"uncaught": True}
                )
            except Exception as e:
                logger.error(f"DevAlert uncaught exception handler error: {e}")
            original_excepthook(exc_type, exc_value, exc_traceback)

        sys.excepthook = devalert_excepthook

    def _send_payload(self, payload: Dict[str, Any]):
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": "devalert-python/1.0.0"
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(self.endpoint, json=payload, headers=headers)
                if resp.status_code >= 400:
                    logger.warning(f"DevAlert event ingestion failed with status {resp.status_code}: {resp.text}")
        except Exception as e:
            # Graceful degradation: never crash host app if DevAlert is down
            logger.debug(f"DevAlert network error during delivery: {e}")

    def _dispatch(self, payload: Dict[str, Any]):
        if self.sample_rate < 1.0 and random.random() > self.sample_rate:
            return  # Discard due to sampling

        if self.async_delivery and self.executor:
            self.executor.submit(self._send_payload, payload)
        else:
            self._send_payload(payload)

    def capture_exception(
        self,
        exc: Exception,
        severity: str = "high",
        environment: Optional[str] = None,
        service: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        request_data: Optional[Dict[str, Any]] = None,
        event_id: Optional[str] = None
    ):
        """Captures and reports an exception to DevAlert."""
        try:
            error_type = type(exc).__name__
            message = str(exc) or error_type
            tb_str = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))

            payload = {
                "environment": environment or self.environment,
                "service": service or self.service,
                "source": "python-sdk",
                "error_type": error_type,
                "message": message,
                "severity": severity,
                "stack_trace": tb_str,
                "release": self.release,
                "event_id": event_id,
                "metadata": sanitize_dict(metadata or {}),
                "request_data": sanitize_dict(request_data or {})
            }
            self._dispatch(payload)
        except Exception as e:
            logger.error(f"DevAlert failed to capture exception: {e}")

    def capture_message(
        self,
        message: str,
        severity: str = "medium",
        error_type: str = "ApplicationMessage",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Captures an informational or alert message without a raised exception."""
        try:
            payload = {
                "environment": self.environment,
                "service": self.service,
                "source": "python-sdk",
                "error_type": error_type,
                "message": message,
                "severity": severity,
                "release": self.release,
                "metadata": sanitize_dict(metadata or {})
            }
            self._dispatch(payload)
        except Exception as e:
            logger.error(f"DevAlert failed to capture message: {e}")


# Global client singleton pattern
_global_client: Optional[DevAlertClient] = None


def init(
    api_key: str,
    endpoint: str = "http://localhost:8000/api/v1/events",
    environment: str = "production",
    service: str = "default-service",
    release: Optional[str] = None,
    sample_rate: float = 1.0,
    timeout: float = 5.0,
    async_delivery: bool = True,
    auto_capture_uncaught: bool = True
) -> DevAlertClient:
    global _global_client
    _global_client = DevAlertClient(
        api_key=api_key,
        endpoint=endpoint,
        environment=environment,
        service=service,
        release=release,
        sample_rate=sample_rate,
        timeout=timeout,
        async_delivery=async_delivery,
        auto_capture_uncaught=auto_capture_uncaught
    )
    return _global_client


def capture_exception(exc: Exception, **kwargs):
    if _global_client:
        _global_client.capture_exception(exc, **kwargs)
    else:
        logger.warning("DevAlert is not initialized. Call devalert.init(...) first.")


def capture_message(message: str, **kwargs):
    if _global_client:
        _global_client.capture_message(message, **kwargs)
    else:
        logger.warning("DevAlert is not initialized. Call devalert.init(...) first.")
