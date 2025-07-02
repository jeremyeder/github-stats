"""GitHub API exceptions."""


class GitHubAPIError(Exception):
    """Base exception for GitHub API errors."""
    
    pass


class RateLimitError(GitHubAPIError):
    """Raised when GitHub API rate limit is exceeded."""
    
    def __init__(self, reset_time: int):
        """Initialize with reset time."""
        self.reset_time = reset_time
        super().__init__(f"Rate limit exceeded. Resets at {reset_time}")