import traceback
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

import devalert


class DevAlertFastAPIMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, service_name: str = "fastapi-service"):
        super().__init__(app)
        self.service_name = service_name

    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:
            # Capture request information
            req_data = {
                "url": str(request.url),
                "method": request.method,
                "headers": dict(request.headers),
                "client": request.client.host if request.client else None
            }
            devalert.capture_exception(
                exc=exc,
                severity="high",
                service=self.service_name,
                request_data=req_data,
                metadata={"framework": "FastAPI"}
            )
            # Re-raise so the app handles its own HTTP 500 responses
            raise exc
