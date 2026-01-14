"""API routes for scheduler management."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.services.scheduler import (
    get_scheduler_status,
    pause_scheduler,
    resume_scheduler,
    run_daily_pipeline,
    job_history,
)

router = APIRouter(prefix="/api/scheduler", tags=["scheduler"])


class SchedulerStatus(BaseModel):
    """Scheduler status response."""
    running: bool
    paused: bool
    next_run: Optional[str]
    last_run: Optional[dict]
    job_count: int
    history: List[dict]


class ActionResult(BaseModel):
    """Result of scheduler action."""
    success: bool
    message: str
    status: Optional[dict] = None


@router.get("/status", response_model=SchedulerStatus)
async def get_status():
    """Get scheduler status including next run time and history."""
    return get_scheduler_status()


@router.post("/pause", response_model=ActionResult)
async def pause():
    """Pause the scheduler (jobs won't execute)."""
    try:
        pause_scheduler()
        return ActionResult(
            success=True,
            message="Scheduler paused",
            status=get_scheduler_status(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resume", response_model=ActionResult)
async def resume():
    """Resume the scheduler."""
    try:
        resume_scheduler()
        return ActionResult(
            success=True,
            message="Scheduler resumed",
            status=get_scheduler_status(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run-now", response_model=ActionResult)
async def run_now():
    """Manually trigger the daily pipeline immediately."""
    try:
        result = await run_daily_pipeline()
        return ActionResult(
            success=result.get("success", False),
            message="Pipeline executed" if result.get("success") else f"Pipeline failed: {result.get('error')}",
            status=get_scheduler_status(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_history():
    """Get job execution history."""
    return {
        "history": job_history,
        "count": len(job_history),
    }
