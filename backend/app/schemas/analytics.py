from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class MetricCount(BaseModel):
    name: str
    count: int


class TrendPoint(BaseModel):
    date: str
    count: int
    critical_count: int = 0


class OverviewAnalytics(BaseModel):
    total_events: int
    open_incidents: int
    critical_incidents: int
    resolved_incidents: int
    errors_by_project: List[MetricCount]
    errors_by_environment: List[MetricCount]
    errors_by_phase: List[MetricCount]
    errors_by_severity: List[MetricCount]
    error_trends: List[TrendPoint]

