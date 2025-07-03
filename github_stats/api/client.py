"""GitHub API client implementation."""

import logging
from datetime import datetime
from typing import Any

import httpx
from pydantic import BaseModel

from ..utils import get_settings
from .exceptions import GitHubAPIError, RateLimitError

logger = logging.getLogger(__name__)


class RateLimit(BaseModel):
    """GitHub API rate limit information."""

    limit: int
    remaining: int
    reset: int
    used: int


class GitHubClient:
    """Client for interacting with GitHub API."""

    def __init__(self, token: str | None = None):
        """Initialize GitHub client."""
        self.token = token or get_settings().github_token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"Bearer {self.token}",
            "User-Agent": "github-stats/0.1.0",
        }
        self._client = httpx.Client(headers=self.headers, timeout=30.0)

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self._client.close()

    def _check_rate_limit(self, response: httpx.Response) -> None:
        """Check and handle rate limiting."""
        if response.status_code == 403:
            reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
            if reset_time:
                raise RateLimitError(reset_time)

        remaining = response.headers.get("X-RateLimit-Remaining")
        if remaining and int(remaining) < 10:
            logger.warning(f"Low rate limit remaining: {remaining}")

    def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> dict[str, Any]:
        """Make authenticated request to GitHub API."""
        url = f"{self.base_url}{endpoint}"

        try:
            response = self._client.request(method, url, **kwargs)
            self._check_rate_limit(response)
            response.raise_for_status()
            return response.json() if response.content else {}
        except httpx.HTTPStatusError as e:
            logger.error(f"GitHub API error: {e}")
            raise GitHubAPIError(f"API request failed: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

    def get_rate_limit(self) -> RateLimit:
        """Get current rate limit status."""
        data = self._request("GET", "/rate_limit")
        core = data.get("rate", {}).get(
            "core", data.get("resources", {}).get("core", {})
        )
        return RateLimit(**core)

    def get_organization(self, org_name: str) -> dict[str, Any]:
        """Get organization details."""
        return self._request("GET", f"/orgs/{org_name}")

    def get_repository(self, owner: str, repo: str) -> dict[str, Any]:
        """Get repository details."""
        return self._request("GET", f"/repos/{owner}/{repo}")

    def list_organization_repos(
        self,
        org_name: str,
        per_page: int = 100
    ) -> list[dict[str, Any]]:
        """List all repositories for an organization."""
        repos = []
        page = 1

        while True:
            response = self._request(
                "GET",
                f"/orgs/{org_name}/repos",
                params={"per_page": per_page, "page": page}
            )

            if not response:
                break

            repos.extend(response)

            if len(response) < per_page:
                break

            page += 1

        return repos

    def get_repository_commits(
        self,
        owner: str,
        repo: str,
        since: datetime | None = None,
        until: datetime | None = None,
        per_page: int = 100
    ) -> list[dict[str, Any]]:
        """Get repository commits."""
        params = {"per_page": per_page}

        if since:
            params["since"] = since.isoformat()
        if until:
            params["until"] = until.isoformat()

        commits = []
        page = 1

        while True:
            params["page"] = page
            response = self._request(
                "GET",
                f"/repos/{owner}/{repo}/commits",
                params=params
            )

            if not response:
                break

            commits.extend(response)

            if len(response) < per_page:
                break

            page += 1

        return commits

    def get_repository_issues(
        self,
        owner: str,
        repo: str,
        state: str = "all",
        since: datetime | None = None,
        per_page: int = 100
    ) -> list[dict[str, Any]]:
        """Get repository issues."""
        params = {"state": state, "per_page": per_page}

        if since:
            params["since"] = since.isoformat()

        issues = []
        page = 1

        while True:
            params["page"] = page
            response = self._request(
                "GET",
                f"/repos/{owner}/{repo}/issues",
                params=params
            )

            if not response:
                break

            issues.extend(response)

            if len(response) < per_page:
                break

            page += 1

        return issues

    def get_repository_pulls(
        self,
        owner: str,
        repo: str,
        state: str = "all",
        per_page: int = 100
    ) -> list[dict[str, Any]]:
        """Get repository pull requests."""
        params = {"state": state, "per_page": per_page}

        pulls = []
        page = 1

        while True:
            params["page"] = page
            response = self._request(
                "GET",
                f"/repos/{owner}/{repo}/pulls",
                params=params
            )

            if not response:
                break

            pulls.extend(response)

            if len(response) < per_page:
                break

            page += 1

        return pulls

    def get_repository_stargazers(
        self,
        owner: str,
        repo: str,
        per_page: int = 100
    ) -> list[dict[str, Any]]:
        """Get repository stargazers."""
        stars = []
        page = 1

        while True:
            params = {"per_page": per_page, "page": page}
            response = self._request(
                "GET",
                f"/repos/{owner}/{repo}/stargazers",
                params=params
            )

            if not response:
                break

            stars.extend(response)

            if len(response) < per_page:
                break

            page += 1

        return stars

    def get_repository_forks(
        self,
        owner: str,
        repo: str,
        per_page: int = 100
    ) -> list[dict[str, Any]]:
        """Get repository forks."""
        forks = []
        page = 1

        while True:
            params = {"per_page": per_page, "page": page}
            response = self._request(
                "GET",
                f"/repos/{owner}/{repo}/forks",
                params=params
            )

            if not response:
                break

            forks.extend(response)

            if len(response) < per_page:
                break

            page += 1

        return forks

    def get_repository_releases(
        self,
        owner: str,
        repo: str,
        per_page: int = 100
    ) -> list[dict[str, Any]]:
        """Get repository releases."""
        releases = []
        page = 1

        while True:
            params = {"per_page": per_page, "page": page}
            response = self._request(
                "GET",
                f"/repos/{owner}/{repo}/releases",
                params=params
            )

            if not response:
                break

            releases.extend(response)

            if len(response) < per_page:
                break

            page += 1

        return releases

    def get_repository_workflows(
        self,
        owner: str,
        repo: str,
        per_page: int = 100
    ) -> list[dict[str, Any]]:
        """Get repository workflows."""
        workflows = []
        page = 1

        while True:
            params = {"per_page": per_page, "page": page}
            response = self._request(
                "GET",
                f"/repos/{owner}/{repo}/actions/workflows",
                params=params
            )

            if not response:
                break

            # GitHub returns workflows in a 'workflows' key
            workflow_data = response.get("workflows", [])
            workflows.extend(workflow_data)

            if len(workflow_data) < per_page:
                break

            page += 1

        return workflows

    def get_repository_workflow_runs(
        self,
        owner: str,
        repo: str,
        per_page: int = 100
    ) -> list[dict[str, Any]]:
        """Get repository workflow runs."""
        runs = []
        page = 1

        while True:
            params = {"per_page": per_page, "page": page}
            response = self._request(
                "GET",
                f"/repos/{owner}/{repo}/actions/runs",
                params=params
            )

            if not response:
                break

            # GitHub returns runs in a 'workflow_runs' key
            run_data = response.get("workflow_runs", [])
            runs.extend(run_data)

            if len(run_data) < per_page:
                break

            page += 1

        return runs
