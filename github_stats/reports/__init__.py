"""Email reporting functionality for GitHub Stats."""

from .email_reporter import EmailReporter
from .scheduler import ReportScheduler

__all__ = ["EmailReporter", "ReportScheduler"]
