from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import engine, Base
import app.models  # Ensure all models are registered with Base

from app.api.v1.auth import router as auth_router
from app.api.v1.organizations import router as org_router
from app.api.v1.projects import router as project_router
from app.api.v1.events import router as event_router
from app.api.v1.incidents import router as incident_router
from app.api.v1.routing import router as routing_router
from app.api.v1.webhooks import router as webhook_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.audit import router as audit_router

# Initialize database schema on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Universal Error Monitoring and Automated Developer Reporting Platform",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Payload size protection middleware (e.g. max 5MB)
MAX_BODY_SIZE = 5 * 1024 * 1024  # 5MB


@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_BODY_SIZE:
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={"detail": "Payload too large. Maximum allowed size is 5MB."}
        )
    return await call_next(request)


# Include API v1 Routers
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(org_router, prefix=f"{settings.API_V1_STR}/organizations", tags=["Organizations"])
app.include_router(project_router, prefix=f"{settings.API_V1_STR}/projects", tags=["Projects"])
app.include_router(event_router, prefix=f"{settings.API_V1_STR}/events", tags=["Error Ingestion"])
app.include_router(incident_router, prefix=f"{settings.API_V1_STR}/incidents", tags=["Incidents"])
app.include_router(routing_router, prefix=f"{settings.API_V1_STR}/routing", tags=["Developer Routing"])
app.include_router(webhook_router, prefix=f"{settings.API_V1_STR}/webhooks", tags=["Integrations & Webhooks"])
app.include_router(analytics_router, prefix=f"{settings.API_V1_STR}/analytics", tags=["Analytics"])
app.include_router(audit_router, prefix=f"{settings.API_V1_STR}/audit", tags=["Audit Logs"])


@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": "connected"
    }


@app.get("/", tags=["System"])
def root():
    return {
        "message": "DevAlert API is operational.",
        "docs": f"{settings.API_V1_STR}/docs"
    }

