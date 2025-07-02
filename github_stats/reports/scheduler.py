"""Report scheduling functionality."""

import logging
import time
from datetime import datetime
from typing import List, Optional

import schedule

from .email_reporter import EmailReporter

logger = logging.getLogger(__name__)


class ReportScheduler:
    """Schedule and manage automated email reports."""
    
    def __init__(self, email_reporter: EmailReporter):
        """Initialize scheduler with email reporter."""
        self.email_reporter = email_reporter
        self.jobs = []
    
    def schedule_daily_report(
        self,
        to_emails: List[str],
        time_str: str = "09:00",
        organization: Optional[str] = None,
        repository: Optional[str] = None
    ) -> None:
        """Schedule daily summary report."""
        def send_daily():
            logger.info("Sending scheduled daily report")
            self.email_reporter.send_summary_report(
                to_emails=to_emails,
                days=1,
                organization=organization,
                repository=repository,
                subject_prefix="Daily GitHub Stats"
            )
        
        job = schedule.every().day.at(time_str).do(send_daily)
        self.jobs.append(job)
        logger.info(f"Scheduled daily report at {time_str} for {', '.join(to_emails)}")
    
    def schedule_weekly_report(
        self,
        to_emails: List[str],
        day_of_week: str = "monday",
        time_str: str = "09:00",
        organization: Optional[str] = None,
        repository: Optional[str] = None
    ) -> None:
        """Schedule weekly summary report."""
        def send_weekly():
            logger.info("Sending scheduled weekly report")
            self.email_reporter.send_summary_report(
                to_emails=to_emails,
                days=7,
                organization=organization,
                repository=repository,
                subject_prefix="Weekly GitHub Stats"
            )
        
        # Get the schedule method for the day
        day_method = getattr(schedule.every(), day_of_week.lower())
        job = day_method.at(time_str).do(send_weekly)
        self.jobs.append(job)
        logger.info(f"Scheduled weekly report on {day_of_week} at {time_str} for {', '.join(to_emails)}")
    
    def schedule_monthly_report(
        self,
        to_emails: List[str],
        day_of_month: int = 1,
        time_str: str = "09:00",
        organization: Optional[str] = None,
        repository: Optional[str] = None
    ) -> None:
        """Schedule monthly summary report."""
        def send_monthly():
            # Only send if today is the specified day of month
            if datetime.now().day == day_of_month:
                logger.info("Sending scheduled monthly report")
                self.email_reporter.send_summary_report(
                    to_emails=to_emails,
                    days=30,
                    organization=organization,
                    repository=repository,
                    subject_prefix="Monthly GitHub Stats"
                )
        
        job = schedule.every().day.at(time_str).do(send_monthly)
        self.jobs.append(job)
        logger.info(f"Scheduled monthly report on day {day_of_month} at {time_str} for {', '.join(to_emails)}")
    
    def clear_all_jobs(self) -> None:
        """Clear all scheduled jobs."""
        schedule.clear()
        self.jobs.clear()
        logger.info("Cleared all scheduled jobs")
    
    def list_jobs(self) -> List[str]:
        """List all scheduled jobs."""
        job_descriptions = []
        for job in schedule.jobs:
            job_descriptions.append(str(job))
        return job_descriptions
    
    def run_pending(self) -> None:
        """Run pending scheduled jobs."""
        schedule.run_pending()
    
    def run_continuously(self, interval: int = 1) -> None:
        """Run scheduler continuously with specified interval."""
        logger.info(f"Starting report scheduler with {interval}s interval")
        while True:
            try:
                self.run_pending()
                time.sleep(interval)
            except KeyboardInterrupt:
                logger.info("Scheduler stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in scheduler: {e}")
                time.sleep(interval)