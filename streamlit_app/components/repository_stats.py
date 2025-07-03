"""Repository statistics dashboard page."""

from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

# Try to import plotly, fall back to basic charts if not available
try:
    import plotly.express as px

    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
from sqlalchemy import func

from github_stats.models.interactions import Interaction, InteractionType, Repository
from github_stats.utils.database import get_db


def show():
    """Display repository statistics."""
    st.header("🏢 Repository Statistics")

    with get_db() as session:
        repos = session.query(Repository).all()
        repo_names = [repo.full_name for repo in repos]

        if not repo_names:
            st.warning("No repositories found. Start tracking some repositories first!")
            return

        selected_repos = st.multiselect(
            "Select repositories:", 
            repo_names, 
            default=repo_names[:1] if repo_names else [],
            help="Select one or more repositories to analyze"
        )

        if selected_repos:
            repos = session.query(Repository).filter(Repository.full_name.in_(selected_repos)).all()
            repo_ids = [repo.id for repo in repos]

            # Display aggregate metrics for selected repositories
            col1, col2, col3 = st.columns(3)

            with col1:
                total_stars = sum(getattr(repo, "stars_count", 0) or 0 for repo in repos)
                st.metric("Total Stars", total_stars)

            with col2:
                total_forks = sum(getattr(repo, "forks_count", 0) or 0 for repo in repos)
                st.metric("Total Forks", total_forks)

            with col3:
                total_issues = sum(getattr(repo, "open_issues_count", 0) or 0 for repo in repos)
                st.metric("Total Open Issues", total_issues)

            st.markdown("---")

            repo_names_str = ", ".join(selected_repos)
            if len(selected_repos) == 1:
                st.subheader(f"📊 Interaction Timeline - {repo_names_str}")
            else:
                st.subheader(f"📊 Interaction Timeline - {len(selected_repos)} Repositories")

            time_range = st.selectbox(
                "Time Range:",
                ["Last 7 days", "Last 30 days", "Last 90 days", "All time"],
                index=1,
            )

            if time_range == "Last 7 days":
                date_filter = datetime.now() - timedelta(days=7)
            elif time_range == "Last 30 days":
                date_filter = datetime.now() - timedelta(days=30)
            elif time_range == "Last 90 days":
                date_filter = datetime.now() - timedelta(days=90)
            else:
                date_filter = datetime.min

            interactions_data = (
                session.query(
                    func.date(Interaction.timestamp).label("date"),
                    Interaction.action,
                    func.count(Interaction.id).label("count"),
                )
                .filter(
                    Interaction.repository_id.in_(repo_ids),
                    Interaction.timestamp >= date_filter,
                    Interaction.type != InteractionType.STAR,  # Exclude stars by default
                )
                .group_by(func.date(Interaction.timestamp), Interaction.action)
                .all()
            )

            if interactions_data:
                df = pd.DataFrame(
                    [
                        {
                            "date": i.date,
                            "action_type": i.action or "Unknown",
                            "count": i.count,
                        }
                        for i in interactions_data
                    ]
                )

                if PLOTLY_AVAILABLE:
                    title = f"Interactions over time for {repo_names_str}" if len(selected_repos) == 1 else f"Interactions over time for {len(selected_repos)} repositories"
                    fig = px.line(
                        df,
                        x="date",
                        y="count",
                        color="action_type",
                        title=title,
                        labels={"count": "Number of Interactions", "date": "Date"},
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    st.subheader("📈 Interaction Breakdown")

                    action_summary = (
                        df.groupby("action_type")["count"].sum().reset_index()
                    )
                    fig_pie = px.pie(
                        action_summary,
                        values="count",
                        names="action_type",
                        title="Distribution of Interaction Types",
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    # Fallback to basic Streamlit charts
                    pivot_df = df.pivot_table(
                        values="count",
                        index="date",
                        columns="action_type",
                        fill_value=0,
                    )
                    st.line_chart(pivot_df)

                    st.subheader("📈 Interaction Breakdown")
                    action_summary = (
                        df.groupby("action_type")["count"].sum().reset_index()
                    )
                    st.write("**Distribution of Interaction Types**")
                    for _, row in action_summary.iterrows():
                        st.write(f"- {row['action_type']}: {row['count']}")
            else:
                st.info("No interactions found for the selected time range.")

            st.markdown("---")

            contributors_title = "👥 Top Contributors to these Repositories" if len(selected_repos) > 1 else f"👥 Top Contributors to {repo_names_str}"
            st.subheader(contributors_title)

            top_contributors = (
                session.query(
                    Interaction.user,
                    func.count(Interaction.id).label("interaction_count"),
                )
                .filter(
                    Interaction.repository_id.in_(repo_ids), 
                    Interaction.user.isnot(None),
                    Interaction.type != InteractionType.STAR,  # Exclude stars by default
                )
                .group_by(Interaction.user)
                .order_by(func.count(Interaction.id).desc())
                .limit(10)
                .all()
            )

            if top_contributors:
                contrib_df = pd.DataFrame(
                    [
                        {"Developer": c.user, "Interactions": c.interaction_count}
                        for c in top_contributors
                    ]
                )

                if PLOTLY_AVAILABLE:
                    fig_bar = px.bar(
                        contrib_df,
                        x="Developer",
                        y="Interactions",
                        title="Top 10 Contributors",
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
                else:
                    st.bar_chart(contrib_df.set_index("Developer"))
            else:
                st.info("No contributors found for this repository.")
