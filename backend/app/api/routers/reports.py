"""
Reports router — /api/v1/reports

Endpoints:
  GET  /api/v1/reports          List all reports
  GET  /api/v1/reports/{id}     Get a single report by ID
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.schemas import ReportOut
from app.api.store import store
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("", response_model=list[ReportOut])
def list_reports() -> list[ReportOut]:
    """Return all generated reports."""
    return sorted(
        store.reports.values(),
        key=lambda r: r.generatedAt,
        reverse=True,
    )


@router.get("/{report_id}", response_model=ReportOut)
def get_report(report_id: str) -> ReportOut:
    """Return a single report by ID."""
    report = store.reports.get(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return report
