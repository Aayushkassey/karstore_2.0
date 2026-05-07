from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def start_scheduler():
    scheduler = BackgroundScheduler()

    #DAILY JOB — score all users
    scheduler.add_job(
        _score_all_users_job,
        trigger=CronTrigger(hour=0, minute=0),  # midnight daily
        id='daily_churn_scoring',
        name='Daily Churn Scoring',
        replace_existing=True,
    )

    # WEEKLY JOB — send retention emails 
    scheduler.add_job(
        _send_retention_emails_job,
        trigger=CronTrigger(day_of_week='sun', hour=9, minute=0),  # Sunday 9am
        id='weekly_retention_emails',
        name='Weekly Retention Emails',
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler started — daily scoring + weekly emails active")
    return scheduler


def _score_all_users_job():
    try:
        from retention.tasks import score_all_users
        result = score_all_users()
        logger.info(f"Daily churn scoring done: {result}")
    except Exception as e:
        logger.error(f"Daily churn scoring failed: {e}")


def _send_retention_emails_job():
    try:
        from retention.tasks import send_retention_emails
        result = send_retention_emails()
        logger.info(f"Weekly retention emails done: {result}")
    except Exception as e:
        logger.error(f"Weekly retention emails failed: {e}")