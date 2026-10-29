"""
DevAlert Flask Integration Example
Run with: python sdk/python/examples/flask_app.py
"""
import devalert
from devalert.integrations.flask import DevAlertFlask

# Initialize DevAlert
devalert.init(
    api_key="da_live_YOUR_PROJECT_API_KEY",
    endpoint="http://localhost:8000/api/v1/events",
    environment="staging",
    service="auth-service",
    release="v2.1.0"
)

try:
    from flask import Flask
    app = Flask(__name__)
    DevAlertFlask(app, service_name="auth-service")

    @app.route("/")
    def index():
        return {"status": "ok"}

    @app.route("/crash")
    def crash():
        raise ValueError("Invalid JWT signature received from authentication gateway")

    if __name__ == "__main__":
        app.run(port=5000)
except ImportError:
    pass
