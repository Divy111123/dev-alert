# DevAlert — Production Deployment Guide

This guide provides instructions for deploying DevAlert in production environments.

---

## 1. Prerequisites

- Docker Engine 24+ and Docker Compose v2+
- A registered domain name with TLS/SSL certificate (e.g., Let's Encrypt or AWS ACM)
- SMTP credentials (e.g., Amazon SES, SendGrid, Mailgun, or Postmark)
- PostgreSQL 15+ database (managed RDS, Cloud SQL, or containerized)
- Redis 7+ instance

---

## 2. Environment Configuration

Copy `.env.example` to `.env` and fill in production secrets:

```bash
cp .env.example .env
```

Key production variables to configure:

```ini
# Security
SECRET_KEY="generate-a-strong-random-64-character-secret"
FRONTEND_URL="https://devalert.yourcompany.com"

# PostgreSQL
DATABASE_URL="postgresql://devalert_user:StrongPassword@pg-prod.internal:5432/devalert_production"

# Redis
REDIS_URL="redis://:RedisPassword@redis-prod.internal:6379/0"

# Production SMTP
EMAIL_MODE="smtp"
SMTP_HOST="email-smtp.us-east-1.amazonaws.com"
SMTP_PORT=587
SMTP_USER="AKIAEXAMPLE"
SMTP_PASSWORD="YourSmtpPassword"
SMTP_FROM_EMAIL="alerts@yourcompany.com"
SMTP_FROM_NAME="DevAlert Production Monitor"
SMTP_USE_TLS=true

# Optional AI Analysis
AI_ANALYSIS_ENABLED=true
AI_API_KEY="AIzaSy..."
```

---

## 3. Database Migrations

Apply database schema migrations via Alembic:

```bash
docker compose run --rm backend alembic upgrade head
```

---

## 4. Starting the Cluster

```bash
# Build and start all microservices
docker compose up -d --build

# Verify running services
docker compose ps
```

Health check verification:
```bash
curl -f http://localhost:8000/health
```

---

## 5. Reverse Proxy & SSL (Nginx / Cloudflare)

Configure your edge reverse proxy or load balancer to forward traffic:
- Routes `/api/*` -> Backend on port 8000
- All other routes -> Frontend on port 3000
- Enable HTTP/2 and gzip / Brotli compression.

