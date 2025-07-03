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

from github_stats.models.interactions import Interaction, Repository
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

        selected_repo = st.selectbox("Select a repository:", repo_names)

        if selected_repo:
            repo = session.query(Repository).filter_by(full_name=selected_repo).first()

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Stars", getattr(repo, "stars_count", "N/A"))

            with col2:
                st.metric("Forks", getattr(repo, "forks_count", "N/A"))

            with col3:
                st.metric("Open Issues", getattr(repo, "open_issues_count", "N/A"))

            st.markdown("---")

            st.subheader("📊 Interaction Timeline")

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
                    Interaction.repository_id == repo.id,
                    Interaction.timestamp >= date_filter,
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
                    fig = px.line(
                        df,
                        x="date",
                        y="count",
                        color="action_type",
                        title=f"Interactions over time for {selected_repo}",
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

            st.subheader("👥 Top Contributors to this Repository")

            top_contributors = (
                session.query(
                    Interaction.user,
                    func.count(Interaction.id).label("interaction_count"),
                )
                .filter(
                    Interaction.repository_id == repo.id, Interaction.user.isnot(None)
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
