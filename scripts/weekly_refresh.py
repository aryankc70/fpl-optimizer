import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("weekly_refresh")


def run_weekly_refresh():
    logger.info("=== Starting weekly refresh ===")

    try:
        logger.info("Step 1/5: Refreshing bootstrap data (prices, status, gameweeks)...")
        from fpl_optimizer.ingestion.load_bootstrap import run as load_bootstrap_run
        load_bootstrap_run()

        logger.info("Step 2/5: Refreshing fixtures...")
        from fpl_optimizer.ingestion.load_fixtures import run as load_fixtures_run
        load_fixtures_run()

        logger.info("Step 3/5: Ingesting newly finished gameweek results...")
        from fpl_optimizer.ingestion.ingest_live_gameweek import run as ingest_live_run
        ingest_live_run()

        logger.info("Step 4/5: Retraining model...")
        from fpl_optimizer.models.train import train
        train()

        logger.info("Step 5/5: Regenerating predictions for next gameweek...")
        from fpl_optimizer.models.predict import generate_predictions
        generate_predictions()

        logger.info("=== Weekly refresh completed successfully ===")
    except Exception:
        logger.exception("Weekly refresh FAILED")
        raise


if __name__ == "__main__":
    run_weekly_refresh()