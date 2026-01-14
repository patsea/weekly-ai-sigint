"""APScheduler service for weekly briefing automation."""
import logging
from datetime import datetime
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from app.config import settings

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler: Optional[AsyncIOScheduler] = None

# Job execution history (in-memory, resets on restart)
job_history: list[dict] = []


async def run_daily_pipeline():
    """Execute the full daily briefing pipeline.

    Pipeline steps:
    1. Fetch content from all active sources
    2. Synthesize briefing with Claude
    3. Export to Notion (if configured)
    4. Send Slack notification (if configured)
    """
    from app.models.database import async_session_maker
    from app.services.fetcher import fetch_from_all_sources
    from app.services.synthesizer import synthesize_weekly_briefing
    from app.services.notion_export import export_briefing_to_notion
    from app.services.slack_notify import send_briefing_to_slack

    start_time = datetime.now()
    result = {
        "started_at": start_time.isoformat(),
        "steps": {},
        "success": False,
        "error": None,
    }

    try:
        async with async_session_maker() as session:
            # Step 1: Fetch content
            logger.info("Pipeline Step 1: Fetching content from sources...")
            fetch_results = await fetch_from_all_sources(session)
            total_items = sum(r.get("items_fetched", 0) for r in fetch_results)
            result["steps"]["fetch"] = {
                "success": True,
                "items_fetched": total_items,
            }

            # Step 2: Synthesize briefing
            logger.info("Pipeline Step 2: Synthesizing briefing with Claude...")
            briefing = await synthesize_weekly_briefing(session, days_back=settings.BRIEFING_DAYS_BACK)
            result["steps"]["synthesize"] = {
                "success": True,
                "briefing_id": briefing.id if briefing else None,
            }

            if not briefing:
                raise Exception("No briefing generated")

            # Step 3: Export to Notion (if configured)
            if settings.NOTION_TOKEN and settings.NOTION_PAGE_ID:
                logger.info("Pipeline Step 3: Exporting to Notion...")
                try:
                    notion_result = await export_briefing_to_notion(session, briefing.id)
                    result["steps"]["notion"] = {
                        "success": True,
                        "page_url": notion_result.get("notion_url"),
                    }
                except Exception as e:
                    logger.warning(f"Notion export failed: {e}")
                    result["steps"]["notion"] = {"success": False, "error": str(e)}
            else:
                result["steps"]["notion"] = {"success": False, "error": "Not configured"}

            # Step 4: Send Slack notification (if configured)
            if settings.SLACK_WEBHOOK_URL:
                logger.info("Pipeline Step 4: Sending Slack notification...")
                try:
                    slack_result = await send_briefing_to_slack(session, briefing.id)
                    result["steps"]["slack"] = {
                        "success": True,
                    }
                except Exception as e:
                    logger.warning(f"Slack notification failed: {e}")
                    result["steps"]["slack"] = {"success": False, "error": str(e)}
            else:
                result["steps"]["slack"] = {"success": False, "error": "Not configured"}

            result["success"] = True

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        result["error"] = str(e)

    result["completed_at"] = datetime.now().isoformat()
    result["duration_seconds"] = (datetime.now() - start_time).total_seconds()

    # Store in history (keep last 10)
    job_history.insert(0, result)
    if len(job_history) > 10:
        job_history.pop()

    logger.info(f"Pipeline completed: success={result['success']}")
    return result


def job_listener(event):
    """Listen for job execution events."""
    if event.exception:
        logger.error(f"Scheduled job failed: {event.exception}")
    else:
        logger.info(f"Scheduled job completed successfully")


def get_scheduler() -> Optional[AsyncIOScheduler]:
    """Get the global scheduler instance."""
    return scheduler


def init_scheduler() -> AsyncIOScheduler:
    """Initialize the APScheduler instance."""
    global scheduler

    if scheduler is not None:
        return scheduler

    scheduler = AsyncIOScheduler()

    # Add job listener for logging
    scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

    # Get schedule from settings
    hour = settings.DAILY_RUN_HOUR
    minute = settings.DAILY_RUN_MINUTE
    timezone = settings.TIMEZONE

    # Add the daily job
    scheduler.add_job(
        run_daily_pipeline,
        CronTrigger(
            hour=hour,
            minute=minute,
            timezone=timezone,
        ),
        id='daily_briefing',
        name='Daily AI Sigint Briefing',
        replace_existing=True,
    )

    logger.info(f"Scheduler initialized: Daily at {hour:02d}:{minute:02d} {timezone}")
    return scheduler


def start_scheduler():
    """Start the scheduler."""
    global scheduler
    if scheduler is None:
        scheduler = init_scheduler()

    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started")


def stop_scheduler():
    """Stop the scheduler."""
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")


def pause_scheduler():
    """Pause the scheduler (jobs won't run but scheduler stays active)."""
    global scheduler
    if scheduler:
        scheduler.pause()
        logger.info("Scheduler paused")


def resume_scheduler():
    """Resume the scheduler."""
    global scheduler
    if scheduler:
        scheduler.resume()
        logger.info("Scheduler resumed")


def get_scheduler_status() -> dict:
    """Get current scheduler status."""
    global scheduler, job_history

    if scheduler is None:
        return {
            "running": False,
            "paused": False,
            "next_run": None,
            "last_run": None,
            "job_count": 0,
            "history": [],
        }

    job = scheduler.get_job('daily_briefing')
    next_run = job.next_run_time.isoformat() if job and job.next_run_time else None

    return {
        "running": scheduler.running,
        "paused": scheduler.state == 2,  # STATE_PAUSED = 2
        "next_run": next_run,
        "last_run": job_history[0] if job_history else None,
        "job_count": len(scheduler.get_jobs()),
        "history": job_history[:5],  # Last 5 runs
    }
