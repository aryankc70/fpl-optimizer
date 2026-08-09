import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("scheduler")


def scheduled_job():
    from scripts.weekly_refresh import run_weekly_refresh
    try:
        run_weekly_refresh()
    except Exception:
        # Log and swallow — a failed run should NOT crash the scheduler
        # process itself, or all future scheduled runs die with it.
        logger.exception("Scheduled weekly refresh failed; will retry next scheduled run.")


def main():
    scheduler = BlockingScheduler()

    # FPL gameweeks typically finish by early Monday morning (last matches
    # are usually Sunday). Tuesday 03:00 UTC gives a safety buffer for late
    # kickoffs/VAR delays/data provider lag before we pull "finished" results.
    scheduler.add_job(
        scheduled_job,
        trigger=CronTrigger(day_of_week="tue", hour=3, minute=0),
        id="weekly_refresh",
        name="Weekly FPL data refresh, retrain, and predict",
        misfire_grace_time=3600,  # if the container was down at trigger time, still run within 1hr of restart
    )

    logger.info("Scheduler started. Weekly refresh scheduled for Tuesdays 03:00 UTC.")
    logger.info("Running an initial refresh now on startup...")
    scheduled_job()  # run once immediately on startup, don't wait a full week for the first run

    scheduler.start()


if __name__ == "__main__":
    main()