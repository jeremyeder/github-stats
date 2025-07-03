"""Email reporting functionality."""

import logging
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

from jinja2 import Template
from sqlalchemy import func

from ..constants import DEFAULT_TOP_ITEMS
from ..models import Interaction, Organization, Repository
from ..utils import get_db

logger = logging.getLogger(__name__)


class EmailReporter:
    """Generate and send email reports for GitHub interactions."""

    def __init__(
        self,
        smtp_server: str,
        smtp_port: int = 587,
        username: str | None = None,
        password: str | None = None,
        use_tls: bool = True
    ):
        """Initialize email reporter."""
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_tls = use_tls

    def generate_summary_report(
        self,
        days: int = 7,
        organization: str | None = None,
        repository: str | None = None
    ) -> dict[str, Any]:
        """Generate summary report data."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        with get_db() as db:
            # Base query
            query = db.query(
                Interaction.type,
                func.count(Interaction.id).label("count")
            ).filter(
                Interaction.timestamp >= start_date,
                Interaction.timestamp <= end_date
            )

            # Apply filters
            if organization:
                org_obj = db.query(Organization).filter_by(name=organization).first()
                if org_obj:
                    query = query.filter(Interaction.organization_id == org_obj.id)

            if repository:
                repo_obj = db.query(Repository).filter_by(full_name=repository).first()
                if repo_obj:
                    query = query.filter(Interaction.repository_id == repo_obj.id)

            # Get interaction counts by type
            interaction_counts = dict(query.group_by(Interaction.type).all())

            # Get total count
            total_interactions = sum(interaction_counts.values())

            # Get top repositories
            repo_query = db.query(
                Repository.full_name,
                func.count(Interaction.id).label("count")
            ).join(
                Interaction, Repository.id == Interaction.repository_id
            ).filter(
                Interaction.timestamp >= start_date,
                Interaction.timestamp <= end_date
            )

            if organization:
                org_obj = db.query(Organization).filter_by(name=organization).first()
                if org_obj:
                    repo_query = repo_query.filter(Repository.organization_id == org_obj.id)

            top_repos = repo_query.group_by(Repository.full_name).order_by(
                func.count(Interaction.id).desc()
            ).limit(DEFAULT_TOP_ITEMS).all()

            # Get top users
            user_query = db.query(
                Interaction.user,
                func.count(Interaction.id).label("count")
            ).filter(
                Interaction.timestamp >= start_date,
                Interaction.timestamp <= end_date,
                Interaction.user.isnot(None)
            )

            if organization:
                org_obj = db.query(Organization).filter_by(name=organization).first()
                if org_obj:
                    user_query = user_query.filter(Interaction.organization_id == org_obj.id)

            if repository:
                repo_obj = db.query(Repository).filter_by(full_name=repository).first()
                if repo_obj:
                    user_query = user_query.filter(Interaction.repository_id == repo_obj.id)

            top_users = user_query.group_by(Interaction.user).order_by(
                func.count(Interaction.id).desc()
            ).limit(DEFAULT_TOP_ITEMS).all()

            return {
                "period": {
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d"),
                    "days": days
                },
                "filters": {
                    "organization": organization,
                    "repository": repository
                },
                "summary": {
                    "total_interactions": total_interactions,
                    "interaction_counts": {
                        interaction_type.value: count
                        for interaction_type, count in interaction_counts.items()
                    }
                },
                "top_repositories": [
                    {"name": repo_name, "count": count}
                    for repo_name, count in top_repos
                ],
                "top_users": [
                    {"username": username, "count": count}
                    for username, count in top_users
                ]
            }

    def render_html_report(self, report_data: dict[str, Any]) -> str:
        """Render HTML email report from data."""
        template_path = Path(__file__).parent.parent / "templates" / "email_report.html"

        try:
            with open(template_path, encoding='utf-8') as f:
                template_content = f.read()

            template = Template(template_content)
            return template.render(report_data=report_data, now=datetime.utcnow())

        except FileNotFoundError:
            logger.error(f"Email template not found at {template_path}")
            # Fallback to simple HTML
            return f"""
            <html>
            <body>
            <h1>GitHub Stats Report</h1>
            <p>Period: {report_data['period']['start_date']} to {report_data['period']['end_date']}</p>
            <p>Total Interactions: {report_data['summary']['total_interactions']}</p>
            <p>Template file missing - please check installation.</p>
            </body>
            </html>
            """
        except Exception as e:
            logger.error(f"Error rendering HTML template: {e}")
            raise

    def render_text_report(self, report_data: dict[str, Any]) -> str:
        """Render plain text email report from data."""
        lines = []
        lines.append("GitHub Stats Report")
        lines.append("=" * 50)
        lines.append(f"Period: {report_data['period']['start_date']} to {report_data['period']['end_date']} ({report_data['period']['days']} days)")

        if report_data['filters']['organization']:
            lines.append(f"Organization: {report_data['filters']['organization']}")
        if report_data['filters']['repository']:
            lines.append(f"Repository: {report_data['filters']['repository']}")

        lines.append("")
        lines.append("SUMMARY")
        lines.append("-" * 20)
        lines.append(f"Total Interactions: {report_data['summary']['total_interactions']}")
        lines.append("")

        for interaction_type, count in report_data['summary']['interaction_counts'].items():
            lines.append(f"{interaction_type.replace('_', ' ').title()}: {count}")

        if report_data['top_repositories']:
            lines.append("")
            lines.append("TOP REPOSITORIES")
            lines.append("-" * 20)
            for repo in report_data['top_repositories']:
                lines.append(f"{repo['name']}: {repo['count']} interactions")

        if report_data['top_users']:
            lines.append("")
            lines.append("TOP CONTRIBUTORS")
            lines.append("-" * 20)
            for user in report_data['top_users']:
                lines.append(f"{user['username']}: {user['count']} interactions")

        lines.append("")
        lines.append(f"Generated by GitHub Stats at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")

        return "\n".join(lines)

    def send_report(
        self,
        to_emails: list[str],
        subject: str,
        report_data: dict[str, Any],
        include_html: bool = True
    ) -> bool:
        """Send email report."""
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.username
            msg["To"] = ", ".join(to_emails)

            # Create text part
            text_content = self.render_text_report(report_data)
            text_part = MIMEText(text_content, "plain")
            msg.attach(text_part)

            # Create HTML part if requested
            if include_html:
                html_content = self.render_html_report(report_data)
                html_part = MIMEText(html_content, "html")
                msg.attach(html_part)

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()

                if self.username and self.password:
                    server.login(self.username, self.password)

                server.send_message(msg, to_addrs=to_emails)

            logger.info(f"Email report sent successfully to {', '.join(to_emails)}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email report: {e}")
            return False

    def send_summary_report(
        self,
        to_emails: list[str],
        days: int = 7,
        organization: str | None = None,
        repository: str | None = None,
        subject_prefix: str = "GitHub Stats"
    ) -> bool:
        """Generate and send summary report."""
        try:
            # Generate report data
            report_data = self.generate_summary_report(days, organization, repository)

            # Create subject
            subject = f"{subject_prefix} - {days} Day Summary"
            if organization:
                subject += f" ({organization})"
            if repository:
                subject += f" ({repository})"

            # Send report
            return self.send_report(to_emails, subject, report_data)

        except Exception as e:
            logger.error(f"Failed to generate and send summary report: {e}")
            return False
