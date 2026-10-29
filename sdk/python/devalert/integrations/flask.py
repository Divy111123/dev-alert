from typing import Optional
import devalert


class DevAlertFlask:
    def __init__(self, app=None, service_name: str = "flask-service"):
        self.service_name = service_name
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        from flask import request

        @app.errorhandler(Exception)
        def handle_exception(exc):
            req_data = {}
            try:
                req_data = {
                    "url": request.url,
                    "method": request.method,
                    "headers": dict(request.headers),
                    "remote_addr": request.remote_addr
                }
            except Exception:
                pass

            devalert.capture_exception(
                exc=exc,
                severity="high",
                service=self.service_name,
                request_data=req_data,
                metadata={"framework": "Flask"}
            )
            # Re-raise so Flask processes standard error response or custom handler
            raise exc
