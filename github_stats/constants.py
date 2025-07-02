"""Constants for GitHub Stats application."""

# HTTP Status Codes
HTTP_OK = 200
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_RATE_LIMIT_EXCEEDED = 429

# API Configuration
DEFAULT_PER_PAGE = 100
DEFAULT_TIMEOUT = 30.0
MIN_RATE_LIMIT_WARNING = 10

# Database Configuration
DEFAULT_DATABASE_URL = "sqlite:///./github_stats.db"

# Email Configuration
DEFAULT_SMTP_PORT = 587
DEFAULT_EMAIL_TIME = "09:00"

# Error Messages
ERROR_MESSAGES = {
    "rate_limit_exceeded": "GitHub API rate limit exceeded. Reset at {reset_time}",
    "api_request_failed": "GitHub API request failed: {error}",
    "organization_not_found": "Organization '{org_name}' not found on GitHub",
    "repository_not_found": "Repository '{repo_name}' not found on GitHub",
    "invalid_token": "Invalid GitHub token provided",
    "database_error": "Database operation failed: {error}",
    "email_config_missing": "Email configuration missing: {config}",
    "email_send_failed": "Failed to send email: {error}",
}

# Success Messages
SUCCESS_MESSAGES = {
    "database_initialized": "Database initialized successfully!",
    "organization_tracked": "Organization '{org_name}' tracked successfully",
    "repository_tracked": "Repository '{repo_name}' tracked successfully",
    "email_sent": "Email report sent successfully to {recipients}",
    "scheduler_started": "Report scheduler started successfully",
}

# Log Messages
LOG_MESSAGES = {
    "api_call_tracked": "Tracked API call: {method} {endpoint}",
    "interactions_tracked": "Tracked {count} {interaction_type} for {repo}",
    "rate_limit_warning": "Low rate limit remaining: {remaining}",
    "email_report_generated": "Generated email report for {days} days",
    "scheduler_job_added": "Added scheduled job: {job_description}",
}

# GitHub API Endpoints
GITHUB_API_BASE = "https://api.github.com"
GITHUB_API_VERSION = "application/vnd.github.v3+json"

# User Agent
USER_AGENT = "github-stats/0.1.0"

# Time Formats
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
TIME_FORMAT = "%H:%M"

# Pagination Limits
MAX_API_PAGES = 100  # Safety limit to prevent infinite loops
MAX_ITEMS_PER_REQUEST = 5000  # Reasonable limit for single requests

# Retry Configuration
MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 2

# Report Configuration
DEFAULT_REPORT_DAYS = 7
MAX_REPORT_DAYS = 365
DEFAULT_TOP_ITEMS = 10