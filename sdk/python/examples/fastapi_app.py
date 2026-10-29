"""
DevAlert FastAPI Integration Example
Run with: uvicorn sdk.python.examples.fastapi_app:app --port 8080 --reload
"""
from fastapi import FastAPI
import devalert
from devalert.integrations.fastapi import DevAlertFastAPIMiddleware

# Initialize DevAlert
devalert.init(
    api_key="da_live_YOUR_PROJECT_API_KEY",
    endpoint="http://localhost:8000/api/v1/events",
    environment="development",
    service="payment-checkout-api",
    release="v1.0.0"
)

app = FastAPI(title="Payment Checkout Service")
app.add_middleware(DevAlertFastAPIMiddleware, service_name="payment-checkout-api")


@app.get("/")
def read_root():
    return {"status": "ok", "service": "payment-checkout-api"}


@app.get("/trigger-error")
def trigger_error():
    # Simulate an unhandled database exception
    raise ConnectionRefusedError("Could not connect to PostgreSQL primary host at 10.0.1.4:5432")


@app.get("/manual-report")
def manual_report():
    try:
        1 / 0
    except ZeroDivisionError as e:
        devalert.capture_exception(
            exc=e,
            severity="medium",
            metadata={"user_action": "calculate_discount", "cart_id": "cart_99128"}
        )
        return {"error": "Handled gracefully, reported to DevAlert"}
