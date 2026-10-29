# DevAlert — Troubleshooting Guide

This guide covers resolution steps for common errors and operational challenges.

---

## 1. Authentication & API Key Issues

### Symptom: `401 Unauthorized` during event ingestion
- **Cause**: Missing or revoked `X-API-Key` or `Authorization` header.
- **Resolution**:
  1. Verify the project API key in the DevAlert UI under **Projects > [Your Project] > API Keys**.
  2. Ensure the key format starts with `da_live_` or `da_test_`.
  3. Include either header:
     - `X-API-Key: da_live_...`
     - `Authorization: Bearer da_live_...`

### Symptom: `429 Too Many Requests`
- **Cause**: Project request rate limit exceeded (default 120 requests/minute).
- **Resolution**: Adjust `rate_limit_per_minute` in project settings or use batched ingestion (`POST /api/v1/events/batch`, up to 50 events per batch).

---

## 2. Developer Routing & Ownership

### Symptom: Errors routed to fallback owner instead of target developer
- **Cause**: Routing rules evaluated in priority order (1 = highest). If conditions don't match exactly, fallback is triggered.
- **Resolution**:
  1. Open **Teams & Routing** in the dashboard.
  2. Use the **Interactive Routing Simulator** to test your error payload against existing rules.
  3. Verify that matching fields (such as `service`, `environment`, `error_type`, or `phase`) match the ingested telemetry.
  4. Wildcard matching: Leave fields blank or set to `*` to match any value.

---

## 3. Email Delivery & Notifications

### Symptom: Notifications not arriving in inbox
- **Cause**:
  1. In local development, `EMAIL_MODE` defaults to `console` or `mock`.
  2. Cooldown suppression: Repeated occurrences of the same error fingerprint are suppressed according to `cooldown_minutes` (default 15 minutes) to prevent alert flooding.
- **Resolution**:
  1. In Docker Compose, inspect MailHog UI at `http://localhost:8025` to view all captured notification emails.
  2. Trigger a test email from **Projects > Test Alert**.
  3. Check `notification_records` table in PostgreSQL or the **Dispatched Alerts** tab in Incident Details.

---

## 4. Background Workers & Celery

### Symptom: Notifications delayed or queue backed up
- **Cause**: Celery worker is stopped or Redis broker unreachable.
- **Resolution**:
  1. Check worker container status: `docker compose logs -f worker`.
  2. Check Redis connectivity: `docker compose exec redis redis-cli ping`.
  3. For zero-dependency local testing without Redis, set `CELERY_ALWAYS_EAGER=true` in `.env`.

