"""Utility to create star count summaries from GitHub API without individual timestamps."""


from github_stats.models.interactions import Repository
from github_stats.utils.database import get_db


def get_star_counts_by_repository() -> list[dict[str, any]]:
    """Get current star counts for tracked repositories."""
    with get_db() as session:
        repos = session.query(Repository).all()

        star_data = []
        for repo in repos:
            # In a real implementation, you'd call GitHub API here to get current star count
            # For now, we'll note that this would need to be implemented
            star_data.append({
                'repository': repo.full_name,
                'organization': repo.organization.name if repo.organization else None,
                'stars': 0,  # Would be fetched from GitHub API
                'note': 'Star count would be fetched from GitHub API /repos/{owner}/{repo} endpoint'
            })

        return star_data


def create_star_summary_display() -> str:
    """Create a summary display for star information."""
    return """
    ⭐ **Star Information**
    
    Stars don't have individual timestamps in the GitHub API response, so they're tracked
    as current counts rather than individual interaction events.
    
    To get current star counts, the application would need to call:
    `GET /repos/{owner}/{repo}` and use the `stargazers_count` field.
    
    This provides more accurate data than synthetic timestamps.
    """
