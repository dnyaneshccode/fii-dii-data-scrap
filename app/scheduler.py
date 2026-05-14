from apscheduler.schedulers.background import BackgroundScheduler
from .scraper import (
    scrape_fii_dii_data,
    scrape_historical_dii_data
)
from .database import SessionLocal
from .crud import (
    insert_fii_dii_data,
    insert_historical_dii_data
)
from .scraper import scrape_fii_derivatives_data
from .crud import insert_fii_derivatives_data
import traceback


def run_daily_job():

    db = SessionLocal()

    try:

        records = scrape_fii_dii_data()

        print("FII/DII records fetched:", records)

        insert_fii_dii_data(db, records)

        print("FII/DII data updated successfully")

    except Exception as e:

        db.rollback()

        print("Scheduler Error:", str(e))

        traceback.print_exc()

        raise

    finally:

        db.close()


def run_historical_dii_job():

    db = SessionLocal()

    try:

        records = scrape_historical_dii_data()

        print(
            "Historical DII records fetched:",
            len(records)
        )

        insert_historical_dii_data(
            db,
            records
        )

        print(
            "Historical DII data updated successfully"
        )

    except Exception as e:

        db.rollback()

        print(
            "Historical DII Scheduler Error:",
            str(e)
        )

        traceback.print_exc()

        raise

    finally:

        db.close()


def run_fii_derivatives_job():

    db = SessionLocal()

    try:

        result = scrape_fii_derivatives_data()

        # Handle file not available case
        if isinstance(result, dict):

            print(result["message"])

            return result

        records = result

        print(
            "FII Derivative records fetched:",
            len(records)
        )

        insert_fii_derivatives_data(
            db,
            records
        )

        print(
            "FII Derivative data updated successfully"
        )

    except Exception as e:

        db.rollback()

        print(
            "FII Derivative Scheduler Error:",
            str(e)
        )

        traceback.print_exc()

        raise

    finally:

        db.close()


scheduler = BackgroundScheduler()

# Requirement 1 scheduler
scheduler.add_job(
    run_daily_job,
    trigger='cron',
    hour=19,
    minute=0
)

# Requirement 2 scheduler
scheduler.add_job(
    run_historical_dii_job,
    trigger='cron',
    hour=20,
    minute=0
)

scheduler.add_job(
    run_fii_derivatives_job,
    trigger='cron',
    hour=21,
    minute=0
)