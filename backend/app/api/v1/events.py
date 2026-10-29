from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.project import Project
from app.schemas.event import EventIngest, EventBatchIngest, IngestResult
from app.api.deps import authenticate_api_key
from app.services.incident_service import process_event_ingestion

router = APIRouter()


@router.post(
    "",
    response_model=IngestResult,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a single application error event",
    description="Authenticates incoming error events using a Project API Key (via X-API-Key or Bearer token)."
)
def ingest_event(
    event_in: EventIngest,
    project: Project = Depends(authenticate_api_key),
    db: Session = Depends(get_db)
):
    try:
        result = process_event_ingestion(db=db, project=project, event_in=event_in)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process event ingestion: {str(e)}"
        )


@router.post(
    "/batch",
    response_model=List[IngestResult],
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a batch of error events",
    description="Accepts up to 50 error events in a single HTTP request for high-throughput pipelines."
)
def ingest_event_batch(
    batch_in: EventBatchIngest,
    project: Project = Depends(authenticate_api_key),
    db: Session = Depends(get_db)
):
    if len(batch_in.events) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch limit exceeded. Maximum 50 events allowed per request."
        )

    results = []
    for evt in batch_in.events:
        res = process_event_ingestion(db=db, project=project, event_in=evt)
        results.append(res)
    return results

