"""Core tracking functionality for GitHub interactions."""

import logging
from datetime import datetime
from typing import Any

from dateutil import parser as date_parser
from sqlalchemy.orm import Session

from ..api import GitHubClient
from ..constants import ERROR_MESSAGES, LOG_MESSAGES
from ..models import Interaction, InteractionType, Organization, Repository
from ..utils import get_db

logger = logging.getLogger(__name__)


class InteractionTracker:
    """Track and record GitHub interactions."""

    def __init__(self, github_client: GitHubClient | None = None):
        """Initialize tracker with GitHub client."""
        self.client = github_client or GitHubClient()

    def track_api_call(
        self,
        endpoint: str,
        method: str = "GET",
        organization: str | None = None,
        repository: str | None = None,
        extra_data: dict | None = None,
    ) -> None:
        """Track a generic API call interaction."""
        with get_db() as db:
            org_id = None
            repo_id = None

            if organization:
                org_id = self._get_or_create_organization(db, organization).id

            if repository:
                repo_id = self._get_or_create_repository(
                    db, repository, organization
                ).id

            # Skip API call tracking to avoid synthetic timestamps
            # API calls are meta-interactions and don't need to be tracked as data points
            return

            db.add(interaction)
            db.commit()

            logger.debug(f"Tracked API call: {method} {endpoint}")

    def track_organization(self, org_name: str) -> dict[str, Any]:
        """Track organization and fetch its details."""
        org_info = {"name": org_name, "exists": False, "error": None}

        with get_db() as db:
            org = self._get_or_create_organization(db, org_name)
            org_info["id"] = org.id
            org_info["name"] = org.name

            # Fetch and update organization details
            try:
                org_data = self.client.get_organization(org_name)
                org.github_id = org_data.get("id")
                org.description = org_data.get("description")
                org_info["exists"] = True
                org_info["github_id"] = org_data.get("id")
                org_info["description"] = org_data.get("description")
                db.commit()

                # Track the API call
                self.track_api_call(
                    f"/orgs/{org_name}",
                    organization=org_name,
                    extra_data={"github_id": org_data.get("id")},
                )
            except Exception as e:
                logger.error(f"Failed to fetch organization {org_name}: {e}")
                org_info["error"] = str(e)

            return org_info

    def track_repository(
        self,
        repo_full_name: str,
        organization: str | None = None,
    ) -> dict[str, Any]:
        """Track repository and fetch its details."""
        repo_info = {"full_name": repo_full_name, "exists": False, "error": None}

        with get_db() as db:
            repo = self._get_or_create_repository(db, repo_full_name, organization)

            repo_info["id"] = repo.id
            repo_info["full_name"] = repo.full_name

            # Parse owner and repo name
            parts = repo_full_name.split("/")
            if len(parts) == 2:
                owner, repo_name = parts
            else:
                owner = organization
                repo_name = repo_full_name

            # Fetch and update repository details
            try:
                repo_data = self.client.get_repository(owner, repo_name)
                repo.github_id = repo_data.get("id")
                repo.description = repo_data.get("description")
                repo.is_private = repo_data.get("private", False)
                repo_info["exists"] = True
                repo_info["github_id"] = repo_data.get("id")
                repo_info["description"] = repo_data.get("description")
                repo_info["is_private"] = repo_data.get("private", False)
                db.commit()

                # Track the API call
                self.track_api_call(
                    f"/repos/{owner}/{repo_name}",
                    organization=organization,
                    repository=repo_full_name,
                    extra_data={"github_id": repo_data.get("id")},
                )
            except Exception as e:
                logger.error(f"Failed to fetch repository {repo_full_name}: {e}")
                repo_info["error"] = str(e)

            return repo_info

    def track_commits(
        self,
        owner: str,
        repo: str,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[Interaction]:
        """Track commits for a repository."""
        interactions = []

        try:
            commits = self.client.get_repository_commits(owner, repo, since, until)

            with get_db() as db:
                repo_obj = self._get_or_create_repository(db, f"{owner}/{repo}", owner)

                for commit in commits:
                    # Extract commit timestamp from GitHub API
                    commit_date_str = (
                        commit.get("commit", {}).get("author", {}).get("date")
                    )
                    commit_timestamp = None
                    if commit_date_str:
                        try:
                            commit_timestamp = date_parser.parse(commit_date_str)
                        except (ValueError, TypeError):
                            commit_timestamp = None

                    interaction = Interaction(
                        type=InteractionType.COMMIT,
                        repository_id=repo_obj.id,
                        organization_id=repo_obj.organization_id,
                        timestamp=commit_timestamp,  # Use real GitHub timestamp
                        user=commit.get("commit", {}).get("author", {}).get("name"),
                        action="commit",
                        resource_id=commit.get("sha"),
                        resource_url=commit.get("html_url"),
                        extra_data={
                            "message": commit.get("commit", {}).get("message"),
                            "sha": commit.get("sha"),
                            "committer_date": commit.get("commit", {})
                            .get("committer", {})
                            .get("date"),
                            "author_date": commit_date_str,
                        },
                    )
                    db.add(interaction)
                    interactions.append(interaction)

                db.commit()

                # Track the API call
                self.track_api_call(
                    f"/repos/{owner}/{repo}/commits",
                    organization=owner,
                    repository=f"{owner}/{repo}",
                    extra_data={"count": len(commits)},
                )

                logger.debug(f"Tracked {len(commits)} commits for {owner}/{repo}")

        except Exception as e:
            logger.error(f"Failed to track commits for {owner}/{repo}: {e}")

        return interactions

    def track_issues(
        self,
        owner: str,
        repo: str,
        state: str = "all",
        since: datetime | None = None,
    ) -> list[Interaction]:
        """Track issues for a repository."""
        interactions = []

        try:
            issues = self.client.get_repository_issues(owner, repo, state, since)

            with get_db() as db:
                repo_obj = self._get_or_create_repository(db, f"{owner}/{repo}", owner)

                for issue in issues:
                    # Skip pull requests (they come in issues endpoint too)
                    if "pull_request" in issue:
                        continue

                    # Extract issue timestamp from GitHub API
                    issue_date_str = issue.get("created_at")
                    issue_timestamp = None
                    if issue_date_str:
                        try:
                            issue_timestamp = date_parser.parse(issue_date_str)
                        except (ValueError, TypeError):
                            issue_timestamp = None

                    interaction = Interaction(
                        type=InteractionType.ISSUE,
                        repository_id=repo_obj.id,
                        organization_id=repo_obj.organization_id,
                        timestamp=issue_timestamp,  # Use real GitHub timestamp
                        user=issue.get("user", {}).get("login"),
                        action=f"issue_{issue.get('state')}",
                        resource_id=str(issue.get("number")),
                        resource_url=issue.get("html_url"),
                        extra_data={
                            "title": issue.get("title"),
                            "state": issue.get("state"),
                            "created_at": issue.get("created_at"),
                            "updated_at": issue.get("updated_at"),
                            "closed_at": issue.get("closed_at"),
                            "labels": [
                                label.get("name") for label in issue.get("labels", [])
                            ],
                        },
                    )
                    db.add(interaction)
                    interactions.append(interaction)

                db.commit()

                # Track the API call
                self.track_api_call(
                    f"/repos/{owner}/{repo}/issues",
                    organization=owner,
                    repository=f"{owner}/{repo}",
                    extra_data={"count": len(interactions), "state": state},
                )

                logger.debug(f"Tracked {len(interactions)} issues for {owner}/{repo}")

        except Exception as e:
            logger.error(f"Failed to track issues for {owner}/{repo}: {e}")

        return interactions

    def track_pull_requests(
        self,
        owner: str,
        repo: str,
        state: str = "all",
    ) -> list[Interaction]:
        """Track pull requests for a repository."""
        interactions = []

        try:
            pulls = self.client.get_repository_pulls(owner, repo, state)

            with get_db() as db:
                repo_obj = self._get_or_create_repository(db, f"{owner}/{repo}", owner)

                for pr in pulls:
                    # Extract PR timestamp from GitHub API
                    created_at_str = pr.get("created_at")
                    pr_timestamp = None
                    if created_at_str:
                        try:
                            pr_timestamp = date_parser.parse(created_at_str)
                        except (ValueError, TypeError):
                            pr_timestamp = None

                    interaction = Interaction(
                        type=InteractionType.PULL_REQUEST,
                        repository_id=repo_obj.id,
                        organization_id=repo_obj.organization_id,
                        timestamp=pr_timestamp,  # Use real GitHub timestamp
                        user=pr.get("user", {}).get("login"),
                        action=f"pr_{pr.get('state')}",
                        resource_id=str(pr.get("number")),
                        resource_url=pr.get("html_url"),
                        extra_data={
                            "title": pr.get("title"),
                            "state": pr.get("state"),
                            "merged": pr.get("merged", False),
                            "base": pr.get("base", {}).get("ref"),
                            "head": pr.get("head", {}).get("ref"),
                            "created_at": created_at_str,
                            "updated_at": pr.get("updated_at"),
                            "merged_at": pr.get("merged_at"),
                            "closed_at": pr.get("closed_at"),
                        },
                    )
                    db.add(interaction)
                    interactions.append(interaction)

                db.commit()

                # Track the API call
                self.track_api_call(
                    f"/repos/{owner}/{repo}/pulls",
                    organization=owner,
                    repository=f"{owner}/{repo}",
                    extra_data={"count": len(pulls), "state": state},
                )

                logger.debug(f"Tracked {len(pulls)} pull requests for {owner}/{repo}")

        except Exception as e:
            logger.error(f"Failed to track pull requests for {owner}/{repo}: {e}")

        return interactions

    def track_stargazers(
        self,
        owner: str,
        repo: str,
    ) -> list[Interaction]:
        """Track stargazers for a repository."""

        def extract_star_data(star: dict[str, Any]) -> dict[str, Any]:
            # Extract star timestamp from GitHub API
            starred_at_str = star.get("starred_at")
            star_timestamp = None
            if starred_at_str:
                try:
                    star_timestamp = date_parser.parse(starred_at_str)
                except (ValueError, TypeError):
                    star_timestamp = None

            return {
                "timestamp": star_timestamp,  # Use real GitHub timestamp
                "user": star.get("user", {}).get("login") if star.get("user") else star.get("login"),
                "action": "star",
                "resource_id": str(star.get("user", {}).get("id")) if star.get("user") else str(star.get("id")),
                "resource_url": star.get("user", {}).get("html_url") if star.get("user") else star.get("html_url"),
                "extra_data": {
                    "starred_at": starred_at_str,
                    "user_type": star.get("user", {}).get("type") if star.get("user") else star.get("type"),
                },
            }

        return self._track_with_error_handling(
            "stargazers",
            owner,
            repo,
            lambda: self.client.get_repository_stargazers(owner, repo),
            InteractionType.STAR,
            extract_star_data,
        )

    def track_forks(
        self,
        owner: str,
        repo: str,
    ) -> list[Interaction]:
        """Track forks for a repository."""

        def extract_fork_data(fork: dict[str, Any]) -> dict[str, Any]:
            # Extract fork timestamp from GitHub API
            created_at_str = fork.get("created_at")
            fork_timestamp = None
            if created_at_str:
                try:
                    fork_timestamp = date_parser.parse(created_at_str)
                except (ValueError, TypeError):
                    fork_timestamp = None

            return {
                "timestamp": fork_timestamp,  # Use real GitHub timestamp
                "user": fork.get("owner", {}).get("login"),
                "action": "fork",
                "resource_id": str(fork.get("id")),
                "resource_url": fork.get("html_url"),
                "extra_data": {
                    "fork_name": fork.get("full_name"),
                    "created_at": created_at_str,
                    "private": fork.get("private", False),
                },
            }

        return self._track_with_error_handling(
            "forks",
            owner,
            repo,
            lambda: self.client.get_repository_forks(owner, repo),
            InteractionType.FORK,
            extract_fork_data,
        )

    def track_releases(
        self,
        owner: str,
        repo: str,
    ) -> list[Interaction]:
        """Track releases for a repository."""

        def extract_release_data(release: dict[str, Any]) -> dict[str, Any]:
            # Extract release timestamp from GitHub API
            published_at_str = release.get("published_at")
            release_timestamp = None
            if published_at_str:
                try:
                    release_timestamp = date_parser.parse(published_at_str)
                except (ValueError, TypeError):
                    release_timestamp = None

            return {
                "timestamp": release_timestamp,  # Use real GitHub timestamp
                "user": release.get("author", {}).get("login"),
                "action": "release",
                "resource_id": str(release.get("id")),
                "resource_url": release.get("html_url"),
                "extra_data": {
                    "tag_name": release.get("tag_name"),
                    "name": release.get("name"),
                    "draft": release.get("draft", False),
                    "prerelease": release.get("prerelease", False),
                    "published_at": published_at_str,
                    "created_at": release.get("created_at"),
                },
            }

        return self._track_with_error_handling(
            "releases",
            owner,
            repo,
            lambda: self.client.get_repository_releases(owner, repo),
            InteractionType.RELEASE,
            extract_release_data,
        )

    def track_workflow_runs(
        self,
        owner: str,
        repo: str,
    ) -> list[Interaction]:
        """Track workflow runs for a repository."""

        def extract_workflow_data(run: dict[str, Any]) -> dict[str, Any]:
            # Extract workflow run timestamp from GitHub API
            created_at_str = run.get("created_at")
            workflow_timestamp = None
            if created_at_str:
                try:
                    workflow_timestamp = date_parser.parse(created_at_str)
                except (ValueError, TypeError):
                    workflow_timestamp = None

            return {
                "timestamp": workflow_timestamp,  # Use real GitHub timestamp
                "user": run.get("actor", {}).get("login"),
                "action": f"workflow_{run.get('status')}",
                "resource_id": str(run.get("id")),
                "resource_url": run.get("html_url"),
                "extra_data": {
                    "workflow_id": run.get("workflow_id"),
                    "status": run.get("status"),
                    "conclusion": run.get("conclusion"),
                    "run_number": run.get("run_number"),
                    "event": run.get("event"),
                    "created_at": created_at_str,
                    "updated_at": run.get("updated_at"),
                },
            }

        return self._track_with_error_handling(
            "workflow_runs",
            owner,
            repo,
            lambda: self.client.get_repository_workflow_runs(owner, repo),
            InteractionType.WORKFLOW_RUN,
            extract_workflow_data,
        )

    def _get_or_create_organization(
        self,
        db: Session,
        org_name: str,
    ) -> Organization:
        """Get or create organization in database."""
        org = db.query(Organization).filter_by(name=org_name).first()

        if not org:
            org = Organization(name=org_name)
            db.add(org)
            db.commit()
            db.refresh(org)
            logger.debug(f"Created new organization: {org_name}")

        return org

    def _get_or_create_repository(
        self,
        db: Session,
        repo_name: str,
        organization: str | None = None,
    ) -> Repository:
        """Get or create repository in database."""
        # Handle full name format (owner/repo)
        if "/" in repo_name:
            full_name = repo_name
            parts = repo_name.split("/")
            if len(parts) == 2:
                organization = parts[0]
                repo_name = parts[1]
        else:
            full_name = f"{organization}/{repo_name}" if organization else repo_name

        repo = db.query(Repository).filter_by(full_name=full_name).first()

        if not repo:
            org_id = None
            if organization:
                org = self._get_or_create_organization(db, organization)
                org_id = org.id

            repo = Repository(
                name=repo_name, full_name=full_name, organization_id=org_id
            )
            db.add(repo)
            db.commit()
            db.refresh(repo)
            logger.debug(f"Created new repository: {full_name}")

        return repo

    def _create_interactions_batch(
        self,
        db: Session,
        interaction_type: InteractionType,
        repo_obj: Repository,
        items: list[dict[str, Any]],
        extract_fn: callable,
    ) -> list[Interaction]:
        """Create a batch of interactions from API response items."""
        interactions = []

        for item in items:
            interaction_data = extract_fn(item)
            
            # Skip interactions without valid timestamps to avoid synthetic data
            if interaction_data.get("timestamp") is None:
                logger.debug(f"Skipping {interaction_type} interaction without timestamp")
                continue
                
            interaction = Interaction(
                type=interaction_type,
                repository_id=repo_obj.id,
                organization_id=repo_obj.organization_id,
                **interaction_data,
            )
            db.add(interaction)
            interactions.append(interaction)

        return interactions

    def _track_with_error_handling(
        self,
        operation_name: str,
        owner: str,
        repo: str,
        api_call: callable,
        interaction_type: InteractionType,
        extract_fn: callable,
    ) -> list[Interaction]:
        """Generic method to track interactions with error handling."""
        interactions = []

        try:
            # Call the API
            items = api_call()

            # Store interactions in database
            with get_db() as db:
                repo_obj = self._get_or_create_repository(db, f"{owner}/{repo}", owner)

                interactions = self._create_interactions_batch(
                    db, interaction_type, repo_obj, items, extract_fn
                )

                db.commit()

                # Track the API call
                endpoint = self._get_api_endpoint(operation_name, owner, repo)
                self.track_api_call(
                    endpoint,
                    organization=owner,
                    repository=f"{owner}/{repo}",
                    extra_data={"count": len(items)},
                )

                # Log the result
                self._log_tracking_result(operation_name, len(items), owner, repo)

        except Exception as e:
            error_msg = ERROR_MESSAGES.get(
                "api_request_failed", "Failed to track {operation}: {error}"
            )
            logger.error(error_msg.format(operation=operation_name, error=e))

        return interactions

    def _get_api_endpoint(self, operation_name: str, owner: str, repo: str) -> str:
        """Get API endpoint path for operation."""
        endpoints = {
            "commits": f"/repos/{owner}/{repo}/commits",
            "issues": f"/repos/{owner}/{repo}/issues",
            "pull_requests": f"/repos/{owner}/{repo}/pulls",
            "stargazers": f"/repos/{owner}/{repo}/stargazers",
            "forks": f"/repos/{owner}/{repo}/forks",
            "releases": f"/repos/{owner}/{repo}/releases",
            "workflow_runs": f"/repos/{owner}/{repo}/actions/runs",
        }
        return endpoints.get(operation_name, f"/repos/{owner}/{repo}/{operation_name}")

    def _log_tracking_result(
        self, operation_name: str, count: int, owner: str, repo: str
    ) -> None:
        """Log tracking result in standardized format."""
        message = LOG_MESSAGES.get(
            "interactions_tracked", "Tracked {count} {interaction_type} for {repo}"
        )
        logger.debug(
            message.format(
                count=count, interaction_type=operation_name, repo=f"{owner}/{repo}"
            )
        )
