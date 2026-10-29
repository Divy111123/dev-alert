"""
DevAlert - End-to-End Demonstration and Data Seeding Script
Run with: python demo.py
"""
import sys
import os
from pathlib import Path

# Configure local standalone execution
os.environ["CELERY_ALWAYS_EAGER"] = "True"
os.environ["EMAIL_MODE"] = "console"
os.environ["PYTHONUNBUFFERED"] = "1"

# Add backend to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))

from app.core.config import settings
from app.core.database import SessionLocal, engine, Base
import app.models
from app.models.user import User
from app.models.organization import Organization, OrganizationMember, OrgRole
from app.models.project import Project, ApiKey
from app.models.routing import RoutingRule
from app.core.security import get_password_hash, generate_api_key, hash_api_key
from app.services.incident_service import process_event_ingestion
from app.schemas.event import EventIngest


def run_demo():
    print("=========================================================")
    print("[DevAlert] Starting DevAlert Demonstration & Seed Simulation")
    print("=========================================================")

    # Initialize tables
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Create Demo Admin User
        admin_email = "lead-dev@acme.com"
        user = db.query(User).filter(User.email == admin_email).first()
        if not user:
            print(f"Creating Demo Admin: {admin_email}...")
            user = User(
                email=admin_email,
                full_name="Sarah Connor (Tech Lead)",
                hashed_password=get_password_hash("DevAlertDemo2026!"),
                is_active=True,
                is_superuser=True
            )
            db.add(user)
            db.flush()

        # 2. Create Organization
        org = db.query(Organization).filter(Organization.slug == "acme-fintech").first()
        if not org:
            print("Creating Organization: Acme Financial Technologies...")
            org = Organization(
                name="Acme Financial Technologies",
                slug="acme-fintech",
                description="High-throughput payment processing infrastructure"
            )
            db.add(org)
            db.flush()

            member = OrganizationMember(
                organization_id=org.id,
                user_id=user.id,
                role=OrgRole.ADMIN.value
            )
            db.add(member)
            db.flush()

        # 3. Create Monitored Project: Payment Gateway API
        proj = db.query(Project).filter(Project.organization_id == org.id, Project.name == "Payment Gateway API").first()
        if not proj:
            print("Creating Monitored Project: Payment Gateway API...")
            proj = Project(
                organization_id=org.id,
                name="Payment Gateway API",
                slug="payment-gateway-api",
                description="Handles card authorisations and settlement flows",
                repository_url="https://github.com/acme/payment-api",
                default_owner_id=user.id,
                default_owner_email="ops-oncall@acme.com",
                default_team="Payment Engineering",
                environments=["development", "testing", "staging", "production"],
                settings={
                    "cooldown_minutes": 15,
                    "notify_on_new": True,
                    "notify_on_escalation": True,
                    "min_severity_to_notify": "medium",
                    "rate_limit_per_minute": 120
                }
            )
            db.add(proj)
            db.flush()

        # Create Project API Key
        raw_key = generate_api_key(prefix="da_live")
        key_record = ApiKey(
            project_id=proj.id,
            name="Production Ingestion Key",
            key_hash=hash_api_key(raw_key),
            prefix=raw_key[:12] + "..."
        )
        db.add(key_record)
        db.flush()

        # 4. Create Developer Routing Rules
        print("Configuring Smart Developer Routing Rules...")
        # Rule 1: Database errors -> Database Administrator
        r1 = RoutingRule(
            project_id=proj.id,
            name="Database Outage Routing",
            priority=1,
            conditions={"error_type": "DatabaseConnectionError", "service": "payment-api"},
            target_type="email",
            target_email="dba-squad@acme.com",
            is_active=True
        )
        # Rule 2: Deployment failures -> DevOps SRE
        r2 = RoutingRule(
            project_id=proj.id,
            name="Deployment Pipeline Routing",
            priority=2,
            conditions={"phase": "Deployment"},
            target_type="team",
            target_team="DevOps OnCall",
            target_email="devops@acme.com",
            is_active=True
        )
        db.add_all([r1, r2])
        db.commit()

        print(f"\n[Generated Demo API Key]: {raw_key}")
        print(f"[Monitored Project ID]:   {proj.id}")

        # 5. Simulate Ingestion of Diverse Real-World Errors
        print("\n--- Simulating Live Error Ingestion Pipeline ---")

        # Event 1: Critical Database Deadlock in Production (Triggers Rule #1)
        print("\n[Event 1]: Simulating Critical Database Failure in Production...")
        res1 = process_event_ingestion(
            db=db,
            project=proj,
            event_in=EventIngest(
                environment="production",
                phase="Production",
                service="payment-api",
                source="python-sdk",
                error_type="DatabaseConnectionError",
                message="FATAL: remaining connection slots are reserved for non-replication superuser connections",
                severity="critical",
                stack_trace="File 'db/pool.py', line 112, in acquire_connection\n  raise DatabaseConnectionError('Pool exhausted')",
                metadata={"pool_size": 50, "active_connections": 50}
            )
        )
        print(f" -> Incident Created: ID={res1.incident_id} | Status={res1.status} | Phase={res1.phase}")
        print(f" -> Routed To:        {res1.assigned_to}")

        # Event 2: Duplicate occurrence of Event 1 (Tests Fingerprint Grouping & Suppression)
        print("\n[Event 2]: Simulating Duplicate Error (Testing Occurrence Deduplication)...")
        res2 = process_event_ingestion(
            db=db,
            project=proj,
            event_in=EventIngest(
                environment="production",
                phase="Production",
                service="payment-api",
                source="python-sdk",
                error_type="DatabaseConnectionError",
                message="FATAL: remaining connection slots are reserved (retry 2)",
                severity="critical",
                stack_trace="File 'db/pool.py', line 112, in acquire_connection\n  raise DatabaseConnectionError('Pool exhausted')"
            )
        )
        print(f" -> Grouped to ID:    {res2.incident_id} (Is New={res2.is_new_incident})")
        print(f" -> Occurrence Count: {res2.occurrence_count} times")

        # Event 3: Jenkins CI Build Failure (Triggers Rule #2)
        print("\n[Event 3]: Simulating Jenkins Pipeline Failure in Deployment Phase...")
        res3 = process_event_ingestion(
            db=db,
            project=proj,
            event_in=EventIngest(
                environment="staging",
                service="k8s-rollout",
                source="jenkins",
                error_type="KubernetesDeploymentFailure",
                message="Helm upgrade timed out waiting for pods to reach Ready state",
                severity="high",
                stack_trace="error: deployment 'payment-api' exceeded its progress deadline",
                metadata={"stage": "deploy-to-staging", "build_number": 142, "branch": "main"}
            )
        )
        print(f" -> Incident Created: ID={res3.incident_id} | Phase={res3.phase}")
        print(f" -> Routed To:        {res3.assigned_to}")

        print("\n=========================================================")
        print("[SUCCESS] Demo Simulation Complete!")
        print("Default Login Credentials:")
        print(f"Email:    {admin_email}")
        print(f"Password: DevAlertDemo2026!")
        print("=========================================================\n")

    finally:
        db.close()


if __name__ == "__main__":
    run_demo()
