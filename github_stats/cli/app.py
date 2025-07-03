"""Main CLI application using Typer."""

from datetime import datetime

import typer
from rich.console import Console
from rich.table import Table

from ..api import GitHubClient
from ..models import InteractionType
from ..reports import EmailReporter, ReportScheduler
from ..tracking import InteractionTracker
from ..utils import check_db_has_data, get_db, init_db, setup_logging
from ..utils.config import get_settings

app = typer.Typer(
    name="github-stats",
    help="Track interactions with GitHub organizations and repositories.",
    no_args_is_help=True,
)

console = Console()


@app.command()
def init():
    """Initialize the database."""
    setup_logging()

    # Check if database already has data
    data_counts = check_db_has_data()
    total_items = sum(data_counts.values())

    if total_items > 0:
        console.print("[yellow]⚠ Existing data found in database:[/yellow]")
        for data_type, count in data_counts.items():
            if count > 0:
                console.print(f"  • {count} {data_type}")

        console.print()
        console.print(
            "[yellow]Warning: Running init will not delete existing data, "
            "but may create duplicate entries if you re-track the same repositories.[/yellow]"
        )

        if not typer.confirm("Do you want to continue with database initialization?"):
            console.print("[yellow]Database initialization cancelled.[/yellow]")
            raise typer.Exit(0)

    console.print("[bold green]Initializing database...[/bold green]")
    init_db()
    console.print("[bold green]Database initialized successfully![/bold green]")


@app.command()
def track_org(
    org_name: str = typer.Argument(..., help="GitHub organization name"),
    fetch_repos: bool = typer.Option(
        False, "--fetch-repos", "-r", help="Also fetch all repositories"
    ),
):
    """Track a GitHub organization."""
    setup_logging()

    with GitHubClient() as client:
        tracker = InteractionTracker(client)

        console.print(f"[bold]Tracking organization: {org_name}[/bold]")
        org_info = tracker.track_organization(org_name)

        if org_info["exists"]:
            console.print(f"[green]✓[/green] Organization tracked: {org_info['name']}")
        else:
            if org_info["error"]:
                console.print(
                    f"[yellow]⚠[/yellow] Organization '{org_name}' may not "
                    "exist as an organization, but tracked locally"
                )
                console.print(f"[dim]Error: {org_info['error']}[/dim]")
            else:
                console.print(
                    f"[green]✓[/green] Organization tracked locally: {org_info['name']}"
                )

        if fetch_repos and org_info["exists"]:
            console.print("[bold]Fetching repositories...[/bold]")
            try:
                repos = client.list_organization_repos(org_name)
                for repo in repos:
                    console.print(f"[dim]Tracking {repo['full_name']}...[/dim]")
                    repo_info = tracker.track_repository(repo["full_name"], org_name)

                    if repo_info["exists"]:
                        # Track all interaction types for each repository
                        owner, repo_name = repo["full_name"].split("/")

                        # Track all interaction types for each repo
                        commits = tracker.track_commits(owner, repo_name)
                        issues = tracker.track_issues(owner, repo_name)
                        prs = tracker.track_pull_requests(owner, repo_name)
                        stars = tracker.track_stargazers(owner, repo_name)
                        forks = tracker.track_forks(owner, repo_name)
                        releases = tracker.track_releases(owner, repo_name)
                        workflows = tracker.track_workflow_runs(owner, repo_name)

                        total_interactions = (
                            len(commits)
                            + len(issues)
                            + len(prs)
                            + len(stars)
                            + len(forks)
                            + len(releases)
                            + len(workflows)
                        )
                        console.print(
                            f"[green]✓[/green] {repo['full_name']} - "
                            f"{total_interactions} total interactions"
                        )
                    else:
                        console.print(
                            f"[yellow]⚠[/yellow] {repo['full_name']} - "
                            "basic tracking only"
                        )

                console.print(
                    f"[bold green]Tracked {len(repos)} repositories with "
                    "full data[/bold green]"
                )
            except Exception as e:
                console.print(f"[red]Error fetching repositories: {e}[/red]")
        elif fetch_repos:
            console.print(
                "[yellow]Cannot fetch repositories for "
                "non-existent organization[/yellow]"
            )


@app.command()
def track_repo(
    repo: str = typer.Argument(
        ..., help="Repository in format 'owner/repo' or just 'repo'"
    ),
    org: str | None = typer.Option(
        None, "--org", "-o", help="Organization name if not in repo format"
    ),
):
    """Track a GitHub repository."""
    setup_logging()

    # Parse repository format
    if "/" in repo:
        owner, repo_name = repo.split("/", 1)
    else:
        if not org:
            console.print(
                "[red]Error: Must provide --org or use owner/repo format[/red]"
            )
            raise typer.Exit(1)
        owner = org
        repo_name = repo
        repo = f"{owner}/{repo_name}"

    with GitHubClient() as client:
        tracker = InteractionTracker(client)

        console.print(f"[bold]Tracking repository: {repo}[/bold]")
        repo_info = tracker.track_repository(repo, owner)

        if repo_info["exists"]:
            console.print(
                f"[green]✓[/green] Repository tracked: {repo_info['full_name']}"
            )

            # Always track all interaction types for existing repositories
            console.print("[bold]Fetching commits...[/bold]")
            commit_interactions = tracker.track_commits(owner, repo_name)
            console.print(
                f"[green]✓[/green] Tracked {len(commit_interactions)} commits"
            )

            console.print("[bold]Fetching issues...[/bold]")
            issue_interactions = tracker.track_issues(owner, repo_name)
            console.print(f"[green]✓[/green] Tracked {len(issue_interactions)} issues")

            console.print("[bold]Fetching pull requests...[/bold]")
            pr_interactions = tracker.track_pull_requests(owner, repo_name)
            console.print(
                f"[green]✓[/green] Tracked {len(pr_interactions)} pull requests"
            )

            console.print("[bold]Fetching stargazers...[/bold]")
            star_interactions = tracker.track_stargazers(owner, repo_name)
            console.print(f"[green]✓[/green] Tracked {len(star_interactions)} stars")

            console.print("[bold]Fetching forks...[/bold]")
            fork_interactions = tracker.track_forks(owner, repo_name)
            console.print(f"[green]✓[/green] Tracked {len(fork_interactions)} forks")

            console.print("[bold]Fetching releases...[/bold]")
            release_interactions = tracker.track_releases(owner, repo_name)
            console.print(
                f"[green]✓[/green] Tracked {len(release_interactions)} releases"
            )

            console.print("[bold]Fetching workflow runs...[/bold]")
            workflow_interactions = tracker.track_workflow_runs(owner, repo_name)
            console.print(
                f"[green]✓[/green] Tracked {len(workflow_interactions)} workflow runs"
            )
        else:
            if repo_info["error"]:
                console.print(
                    f"[yellow]⚠[/yellow] Repository '{repo}' may not exist, "
                    "but tracked locally"
                )
                console.print(f"[dim]Error: {repo_info['error']}[/dim]")
            else:
                console.print(
                    f"[green]✓[/green] Repository tracked locally: "
                    f"{repo_info['full_name']}"
                )
            console.print(
                "[yellow]Cannot fetch data for non-existent repository[/yellow]"
            )


@app.command()
def stats(
    org: str | None = typer.Option(None, "--org", "-o", help="Filter by organization"),
    repo: str | None = typer.Option(None, "--repo", "-r", help="Filter by repository"),
    interaction_type: str | None = typer.Option(
        None, "--type", "-t", help="Filter by interaction type"
    ),
    days: int = typer.Option(7, "--days", "-d", help="Number of days to look back"),
):
    """Show interaction statistics."""
    setup_logging()

    from sqlalchemy import func

    from ..models import Interaction, Organization, Repository

    with get_db() as db:
        # Build query
        query = db.query(Interaction.type, func.count(Interaction.id).label("count"))

        # Apply filters
        if days:
            from datetime import timedelta

            since = datetime.utcnow() - timedelta(days=days)
            query = query.filter(Interaction.timestamp >= since)

        if org:
            org_obj = db.query(Organization).filter_by(name=org).first()
            if org_obj:
                query = query.filter(Interaction.organization_id == org_obj.id)

        if repo:
            repo_obj = db.query(Repository).filter_by(full_name=repo).first()
            if repo_obj:
                query = query.filter(Interaction.repository_id == repo_obj.id)

        if interaction_type:
            try:
                type_enum = InteractionType(interaction_type)
                query = query.filter(Interaction.type == type_enum)
            except ValueError:
                console.print(
                    f"[red]Invalid interaction type: {interaction_type}[/red]"
                )
                raise typer.Exit(1) from None

        # Group by type
        results = query.group_by(Interaction.type).all()

        # Create table
        table = Table(title=f"Interaction Statistics (last {days} days)")
        table.add_column("Type", style="cyan")
        table.add_column("Count", style="green")

        total = 0
        for interaction_type, count in results:
            table.add_row(interaction_type.value, str(count))
            total += count

        table.add_row("[bold]Total[/bold]", f"[bold]{total}[/bold]")

        console.print(table)


@app.command()
def list_orgs():
    """List all tracked organizations."""
    setup_logging()

    from ..models import Organization

    with get_db() as db:
        orgs = db.query(Organization).order_by(Organization.name).all()

        if not orgs:
            console.print("[yellow]No organizations tracked yet.[/yellow]")
            return

        table = Table(title="Tracked Organizations")
        table.add_column("Name", style="cyan")
        table.add_column("GitHub ID", style="green")
        table.add_column("Repositories", style="yellow")
        table.add_column("Added", style="magenta")

        for org in orgs:
            repo_count = len(org.repositories)
            table.add_row(
                org.name,
                str(org.github_id) if org.github_id else "-",
                str(repo_count),
                org.created_at.strftime("%Y-%m-%d %H:%M"),
            )

        console.print(table)


@app.command()
def list_repos(
    org: str | None = typer.Option(None, "--org", "-o", help="Filter by organization"),
):
    """List all tracked repositories."""
    setup_logging()

    from ..models import Organization, Repository

    with get_db() as db:
        query = db.query(Repository).order_by(Repository.full_name)

        if org:
            org_obj = db.query(Organization).filter_by(name=org).first()
            if org_obj:
                query = query.filter(Repository.organization_id == org_obj.id)

        repos = query.all()

        if not repos:
            console.print("[yellow]No repositories tracked yet.[/yellow]")
            return

        table = Table(title="Tracked Repositories")
        table.add_column("Full Name", style="cyan")
        table.add_column("GitHub ID", style="green")
        table.add_column("Private", style="yellow")
        table.add_column("Interactions", style="magenta")
        table.add_column("Added", style="blue")

        for repo in repos:
            interaction_count = len(repo.interactions)
            table.add_row(
                repo.full_name,
                str(repo.github_id) if repo.github_id else "-",
                "Yes" if repo.is_private else "No",
                str(interaction_count),
                repo.created_at.strftime("%Y-%m-%d %H:%M"),
            )

        console.print(table)


@app.command()
def rate_limit():
    """Check GitHub API rate limit status."""
    setup_logging()

    with GitHubClient() as client:
        try:
            limit_info = client.get_rate_limit()

            table = Table(title="GitHub API Rate Limit")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Limit", str(limit_info.limit))
            table.add_row("Remaining", str(limit_info.remaining))
            table.add_row("Used", str(limit_info.used))

            reset_time = datetime.fromtimestamp(limit_info.reset)
            table.add_row("Reset Time", reset_time.strftime("%Y-%m-%d %H:%M:%S"))

            console.print(table)

            if limit_info.remaining < 100:
                console.print("[yellow]Warning: Low rate limit remaining![/yellow]")

        except Exception as e:
            console.print(f"[red]Error checking rate limit: {e}[/red]")


@app.command()
def send_report(
    to_emails: list[str] = typer.Argument(
        ..., help="Email addresses to send report to"
    ),
    days: int = typer.Option(
        7, "--days", "-d", help="Number of days to include in report"
    ),
    org: str | None = typer.Option(None, "--org", "-o", help="Filter by organization"),
    repo: str | None = typer.Option(None, "--repo", "-r", help="Filter by repository"),
    subject: str | None = typer.Option(
        None, "--subject", "-s", help="Custom email subject"
    ),
):
    """Send email report manually."""
    setup_logging()
    settings = get_settings()

    # Check email configuration
    if not settings.smtp_server:
        console.print("[red]Error: SMTP_SERVER not configured in environment[/red]")
        console.print("Set SMTP_SERVER, SMTP_USERNAME, SMTP_PASSWORD in your .env file")
        raise typer.Exit(1)

    # Create email reporter
    reporter = EmailReporter(
        smtp_server=settings.smtp_server,
        smtp_port=settings.smtp_port,
        username=settings.smtp_username,
        password=settings.smtp_password,
        use_tls=settings.smtp_use_tls,
    )

    # Send report
    console.print(f"[bold]Sending report to {', '.join(to_emails)}...[/bold]")

    success = reporter.send_summary_report(
        to_emails=to_emails,
        days=days,
        organization=org,
        repository=repo,
        subject_prefix=subject or "GitHub Stats",
    )

    if success:
        console.print("[green]✓[/green] Email report sent successfully!")
    else:
        console.print("[red]✗[/red] Failed to send email report")
        raise typer.Exit(1)


@app.command()
def schedule_reports(
    to_emails: list[str] = typer.Argument(
        ..., help="Email addresses to send reports to"
    ),
    daily: bool = typer.Option(False, "--daily", help="Schedule daily reports"),
    weekly: bool = typer.Option(False, "--weekly", help="Schedule weekly reports"),
    monthly: bool = typer.Option(False, "--monthly", help="Schedule monthly reports"),
    time_str: str = typer.Option(
        "09:00", "--time", "-t", help="Time to send reports (HH:MM)"
    ),
    org: str | None = typer.Option(None, "--org", "-o", help="Filter by organization"),
    repo: str | None = typer.Option(None, "--repo", "-r", help="Filter by repository"),
):
    """Schedule automated email reports."""
    setup_logging()
    settings = get_settings()

    # Check email configuration
    if not settings.smtp_server:
        console.print("[red]Error: SMTP_SERVER not configured in environment[/red]")
        console.print("Set SMTP_SERVER, SMTP_USERNAME, SMTP_PASSWORD in your .env file")
        raise typer.Exit(1)

    if not any([daily, weekly, monthly]):
        console.print(
            "[red]Error: Must specify at least one of --daily, --weekly, or --monthly[/red]"
        )
        raise typer.Exit(1)

    # Create email reporter and scheduler
    reporter = EmailReporter(
        smtp_server=settings.smtp_server,
        smtp_port=settings.smtp_port,
        username=settings.smtp_username,
        password=settings.smtp_password,
        use_tls=settings.smtp_use_tls,
    )
    scheduler = ReportScheduler(reporter)

    # Schedule reports
    if daily:
        scheduler.schedule_daily_report(to_emails, time_str, org, repo)
        console.print(f"[green]✓[/green] Scheduled daily reports at {time_str}")

    if weekly:
        scheduler.schedule_weekly_report(to_emails, "monday", time_str, org, repo)
        console.print(
            f"[green]✓[/green] Scheduled weekly reports on Monday at {time_str}"
        )

    if monthly:
        scheduler.schedule_monthly_report(to_emails, 1, time_str, org, repo)
        console.print(
            f"[green]✓[/green] Scheduled monthly reports on 1st at {time_str}"
        )

    # Show scheduled jobs
    jobs = scheduler.list_jobs()
    if jobs:
        console.print("\n[bold]Scheduled jobs:[/bold]")
        for job in jobs:
            console.print(f"  • {job}")

    # Run scheduler
    console.print("\n[bold]Starting scheduler... Press Ctrl+C to stop[/bold]")
    try:
        scheduler.run_continuously()
    except KeyboardInterrupt:
        console.print("\n[yellow]Scheduler stopped[/yellow]")


if __name__ == "__main__":
    app()
