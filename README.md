# DevAlert — Universal Error Monitoring & Automated Developer Reporting Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Celery](https://img.shields.io/badge/Celery-5.4-37814A?logo=celery&logoColor=white)](https://docs.celeryq.dev)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com)
[![Pytest](https://img.shields.io/badge/Pytest-16%20Passed-0A9EDC?logo=pytest&logoColor=white)](https://pytest.org)

DevAlert is a production-oriented, extensible web platform designed to automatically collect application errors, identify affected projects and development phases, determine responsible developers through configurable ownership rules, generate rich HTML error reports, and dispatch notifications asynchronously without blocking host applications.

---

## 1. System Architecture

```
                             +-------------------------------+
                             |    Monitored Applications     |
                             | (Python SDK / FastAPI / Flask)|
                             +---------------+---------------+
                                             |
+--------------------+   +-------------------+---+   +--------------------+
| Jenkins Pipelines  |-->|  DevAlert Ingestion   |<--|   GitHub Actions   |
| (Stage Failures)   |   |   POST /events        |   | (CI Test Failures) |
+--------------------+   +---------+---------+---+   +--------------------+
                                   |
                     +-------------v-------------+
                     | 1. API Key Authentication  |
                     | 2. Input Sanitization      |
                     | 3. Phase Detection Engine  |
                     | 4. Error Fingerprinting    |
                     | 5. Duplicate Suppression   |
                     | 6. Rule-Based Routing      |
                     +-------------+-------------+
                                   |
         +-------------------------+-------------------------+
         |                                                   |
+--------v---------+                               +---------v--------+
| PostgreSQL / DB  |                               | Redis Queue      |
| - Incidents      |                               | & Celery Worker  |
| - Events         |                               +---------+--------+
| - Routing Rules  |                                         |
| - Audit Logs     |                               +---------v--------+
+--------+---------+                               | Email Dispatcher |
         |                                         | (HTML Templates) |
+--------v---------+                               +------------------+
| React Dashboard  |
| (Vite/TypeScript)|
+------------------+
```

---

## 2. Core Features

- **Multi-Tenant Organization Isolation**: Strict organization-scoped data boundaries. Users never access projects, logs, or API keys outside their organization.
- **Project Registration & Secure Key Rotation**: Monitored projects with hashed API key storage (SHA-256), prefix displays, and instant revocation.
- **High-Throughput Ingestion API**:
  - Single event: `POST /api/v1/events`
  - Batch ingestion: `POST /api/v1/events/batch` (up to 50 events)
  - Sliding-window rate limiting per project.
  - Idempotency control via `event_id`.
- **Automatic Development Phase Classification**: Prioritizes explicit metadata -> trusted CI/CD metadata (`Build`, `Testing`, `Deployment`) -> environment mapping -> inferred classification -> `Unknown`.
- **Intelligent Error Fingerprinting & Grouping**: Groups duplicate code occurrences by code frame and normalized signature. Increments occurrence counters and automatically reopens resolved issues upon regression.
- **Rule-Based Developer Routing Engine**:
  - Component ownership, environment ownership, error category, CI/CD stage, severity.
  - Priority ordering (Priority 1 = highest).
  - Explicit tracking of why a developer was selected.
  - Interactive simulator for testing routing policies.
- **Asynchronous Email Notification Service**:
  - Celery background queue with exponential backoff retries.
  - Multi-part HTML & plain-text fallback templates (New Incident, Critical Alert, Escalation, Summary, Resolved, Test).
  - Suppression cooldowns to prevent alert fatigue.
  - Local verification modes (`console`, `file`, `smtp`, `mock`).
- **AI-Assisted Error Diagnosis**: Automatic heuristic and optional LLM-assisted root-cause diagnosis and debugging recommendations with strict credential scrubbing.
- **Modern Responsive Dashboard**: Light and dark themes, error volume trends, phase distributions, live audit trail, and incident drill-down.

---

## 3. Technology Stack

- **Frontend**: React 18, TypeScript, Vite, Lucide Icons, responsive CSS design.
- **Backend**: Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic.
- **Database**: PostgreSQL 16 (SQLite fallback for zero-dependency local testing).
- **Background Processing**: Celery & Redis.
- **Email**: SMTP / Transactional Provider + MailHog local mail-catcher.
- **Packaging & Deployment**: Docker, Docker Compose, Production Nginx.

---

## 4. Quick Start (Local Setup)

### Option A: Running with Docker Compose (Recommended)

```bash
# 1. Clone repository
git clone <repo-url> devalert
cd devalert

# 2. Configure environment
cp .env.example .env

# 3. Start all services (Backend, Frontend, PostgreSQL, Redis, Worker, MailHog)
docker compose up -d --build
```

Access the applications:
- **DevAlert Dashboard**: `http://localhost:3000` (or `http://localhost:5173` in dev mode)
- **FastAPI Interactive Docs**: `http://localhost:8000/api/v1/docs`
- **MailHog Email Catcher**: `http://localhost:8025`

---

### Option B: Running Natively for Development

#### Backend:
```bash
python -m venv venv
.\venv\Scripts\activate       # Windows PowerShell
# source venv/bin/activate    # Linux / macOS

pip install -r backend/requirements.txt

# Start backend server (SQLite by default, zero config required!)
uvicorn app.main:app --app-dir backend --port 8000 --reload
```

#### Frontend:
```bash
cd frontend
npm install
npm run dev
```

---

## 5. End-to-End Demonstration Script

DevAlert includes an automated end-to-end demonstration script that seeds sample organizations, registers projects, configures routing rules, and simulates real-world runtime errors:

```bash
python demo.py
```

Demo output:
- Registers Admin: `lead-dev@acme.com` (Password: `DevAlertDemo2026!`)
- Creates Organization: `Acme Financial Technologies`
- Creates Project: `Payment Gateway API`
- Generates high-entropy API key: `da_live_...`
- Simulates Event 1 (Critical Database Error) -> Automatically routed to `dba-squad@acme.com`
- Simulates Event 2 (Duplicate Error) -> Deduplicated into same incident, occurrence counter incremented to `2`
- Simulates Event 3 (Jenkins CI Build Failure) -> Detected as `Deployment` phase, routed to `devops@acme.com`

---

## 6. Automated Testing

DevAlert has a comprehensive Pytest test suite covering all specifications:

```bash
pytest backend/tests -v
```

### Verified Test Cases:
1. `test_user_registration_and_login`: User signup, password hashing, JWT issue.
2. `test_organization_isolation`: Multi-tenant data segregation between organizations.
3. `test_api_key_creation_and_revocation`: Key generation, hash lookup, instant revocation.
4. `test_email_template_rendering`: HTML & plain-text generation for all incident types.
5. `test_send_test_email_endpoint`: Email verification delivery workflow.
6. `test_authentication_required`: Ingestion rejection for unauthenticated payloads.
7. `test_invalid_payload_rejection`: Schema and field validation enforcement.
8. `test_idempotency_control`: Idempotent deduplication via client `event_id`.
9. `test_incident_grouping_and_occurrence_count`: Fingerprint code-frame grouping.
10. `test_incident_resolution_and_reopening`: Automatic reopening on new occurrence.
11. `test_batch_event_ingestion`: Ingestion of up to 50 batched events.
12. `test_phase_detector_priority`: 5-level phase detection priority hierarchy.
13. `test_routing_rules_and_fallback`: Priority-based rule evaluation & fallback owner.
14. `test_jenkins_webhook_integration`: Jenkins stage failure normalization.
15. `test_github_actions_webhook_integration`: GitHub Actions workflow failure ingestion.
16. `test_generic_webhook_integration`: Third-party generic alert integration.

---

## 7. Python SDK Overview

Install into any Python application:
```bash
pip install ./sdk/python
```

Initialize once at startup:
```python
import devalert
from devalert.integrations.fastapi import DevAlertFastAPIMiddleware
from fastapi import FastAPI

devalert.init(
    api_key="da_live_YOUR_PROJECT_API_KEY",
    endpoint="http://localhost:8000/api/v1/events",
    environment="production",
    service="payment-checkout-api"
)

app = FastAPI()
app.add_middleware(DevAlertFastAPIMiddleware, service_name="payment-checkout-api")
```

See [INTEGRATION_GUIDE.md](file:///c:/Users/divya/Downloads/new/INTEGRATION_GUIDE.md) for Jenkins, GitHub Actions, and Generic Webhook guides.

---

## 8. Repository Structure

```
devalert/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # Endpoints (auth, orgs, projects, events, incidents, routing, webhooks, audit)
│   │   ├── core/            # Config, database, security, celery
│   │   ├── models/          # SQLAlchemy database models
│   │   ├── schemas/         # Pydantic v2 schemas
│   │   ├── services/        # Routing engine, phase detector, fingerprinting, AI analyzer, email service
│   │   ├── tasks/           # Celery notification worker tasks
│   │   ├── templates/       # Jinja2 HTML email templates
│   │   └── main.py          # FastAPI application entrypoint
│   ├── tests/               # Pytest automated test suite
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/      # Badges, TrendChart, Navbar, Sidebar, Modals
│   │   ├── context/         # AuthContext, ThemeContext
│   │   ├── pages/           # Overview, Incidents, Details, Projects, Routing, Integrations, Settings, Audit
│   │   └── services/        # API client
│   ├── Dockerfile
│   └── package.json
├── sdk/
│   └── python/              # Reusable Python SDK package & FastAPI/Flask middlewares
├── integrations/
│   ├── jenkins/             # Jenkinsfile example
│   ├── github-actions/      # GitHub Actions workflow example
│   └── generic-webhook/     # Webhook payload contract
├── demo.py                  # End-to-end data seeding and live demo script
├── docker-compose.yml       # Production/development container orchestration
├── .env.example             # Documented environment variables
├── INTEGRATION_GUIDE.md     # Step-by-step developer integration manual
├── TROUBLESHOOTING.md       # Diagnostic guide for common issues
└── DEPLOYMENT.md            # Production deployment instructions
```

---

## 9. Security & Compliance

- **Role-Based Access Control**: Org Admin, Project Manager, Developer, Viewer roles.
- **Hashed Secrets**: API keys are hashed with SHA-256 before database storage.
- **PII / Secret Scrubbing**: All messages, stack traces, and metadata are cleansed of API keys, passwords, bearer tokens, and credentials.
- **Rate-Limiting**: Enforced per project to prevent API abuse.
- **Audit Logging**: Every project creation, member invitation, API key rotation, and incident resolution is recorded with timestamp and actor attribution.

