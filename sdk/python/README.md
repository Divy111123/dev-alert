# DevAlert Python SDK (`devalert-python`)

The official Python client for DevAlert — Universal Error Monitoring and Automated Developer Reporting.

## Features

- 🚀 **Zero Overhead**: Asynchronous, non-blocking delivery via background thread pool.
- 🛡️ **Fail-Safe**: Network or ingestion outages never block or crash the monitored application.
- 🔒 **Automatic Redaction**: Redacts sensitive fields (`password`, `token`, `secret`, `api_key`, `credentials`) before dispatch.
- 🎯 **Phase & Environment Aware**: Detects phases and tags releases.
- ⚙️ **Automatic Uncaught Exception Interception**: Captures unhandled crashes via `sys.excepthook`.
- 🔌 **Framework Middlewares**: First-class support for FastAPI and Flask.

## Installation

```bash
pip install ./sdk/python
# Or in development
pip install -e ./sdk/python
```

## Quick Start

```python
import devalert

# 1. Initialize once at application startup
devalert.init(
    api_key="da_live_your_project_api_key_here",
    endpoint="http://localhost:8000/api/v1/events",
    environment="production",
    service="billing-api",
    release="1.2.0"
)

# 2. Explicitly capture an exception
try:
    process_payment()
except Exception as e:
    devalert.capture_exception(
        exc=e,
        severity="high",
        metadata={"order_id": "ord_12345"}
    )
```

## FastAPI Middleware

```python
from fastapi import FastAPI
import devalert
from devalert.integrations.fastapi import DevAlertFastAPIMiddleware

devalert.init(api_key="da_live_...", service="users-api")

app = FastAPI()
app.add_middleware(DevAlertFastAPIMiddleware, service_name="users-api")
```

## Flask Integration

```python
from flask import Flask
import devalert
from devalert.integrations.flask import DevAlertFlask

devalert.init(api_key="da_live_...", service="catalog-service")

app = Flask(__name__)
DevAlertFlask(app, service_name="catalog-service")
```
