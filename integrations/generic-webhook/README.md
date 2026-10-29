# DevAlert Generic Webhook Integration

Integrate any custom service, APM tool (Datadog, Prometheus Alertmanager, CloudWatch), or backend system with DevAlert using the Generic Webhook contract.

## Endpoint

`POST /api/v1/webhooks/generic`

## Authentication

Provide your project API Key in the `X-API-Key` request header.

## Payload Schema

```json
{
  "event_type": "string (e.g. MemoryPressureWarning)",
  "summary": "string (short description of the incident)",
  "component": "string (name of the affected service/component)",
  "environment": "production | staging | testing | development",
  "phase": "optional explicit phase",
  "severity": "low | medium | high | critical",
  "trace": "optional sanitized stack trace or log excerpt",
  "metadata": {
    "key": "value"
  }
}
```
