"""GitHub API client module."""

from .client import GitHubClient
from .exceptions import GitHubAPIError, RateLimitError

__all__ = ["GitHubClient", "GitHubAPIError", "RateLimitError"]
