"""Reports router — /api/v1/reports"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.schemas import ReportOut
from app.api.store import get_report, list_reports
from app.api.routers.auth import get_current_user
from app.db.models import UserDoc
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("", response_model=list[ReportOut])
async def list_reports_route(
    current_user: UserDoc = Depends(get_current_user),
) -> list[ReportOut]:
    return await list_reports(owner_id=str(current_user.id))


@router.get("/{report_id}", response_model=ReportOut)
async def get_report_route(
    report_id: str,
    current_user: UserDoc = Depends(get_current_user),
) -> ReportOut:
    report = await get_report(report_id, owner_id=str(current_user.id))
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return report
