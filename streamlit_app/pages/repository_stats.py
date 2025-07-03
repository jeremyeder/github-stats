"""Repository statistics dashboard page."""

from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import func

from github_stats.models.interactions import Developer, Interaction, Repository
from github_stats.utils.database import get_session


def show():
    """Display repository statistics."""
    st.header("🏢 Repository Statistics")

    with get_session() as session:
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
                st.metric("Stars", repo.stars_count)

            with col2:
                st.metric("Forks", repo.forks_count)

            with col3:
                st.metric("Open Issues", repo.open_issues_count)

            st.markdown("---")

            st.subheader("📊 Interaction Timeline")

            time_range = st.selectbox(
                "Time Range:",
                ["Last 7 days", "Last 30 days", "Last 90 days", "All time"],
                index=1
            )

            if time_range == "Last 7 days":
                date_filter = datetime.now() - timedelta(days=7)
            elif time_range == "Last 30 days":
                date_filter = datetime.now() - timedelta(days=30)
            elif time_range == "Last 90 days":
                date_filter = datetime.now() - timedelta(days=90)
            else:
                date_filter = datetime.min

            interactions_data = session.query(
                func.date(Interaction.date).label('date'),
                Interaction.action_type,
                func.count(Interaction.id).label('count')
            ).filter(
                Interaction.repository_id == repo.id,
                Interaction.date >= date_filter
            ).group_by(
                func.date(Interaction.date),
                Interaction.action_type
            ).all()

            if interactions_data:
                df = pd.DataFrame([
                    {'date': i.date, 'action_type': i.action_type, 'count': i.count}
                    for i in interactions_data
                ])

                fig = px.line(
                    df,
                    x='date',
                    y='count',
                    color='action_type',
                    title=f"Interactions over time for {selected_repo}",
                    labels={'count': 'Number of Interactions', 'date': 'Date'}
                )
                st.plotly_chart(fig, use_container_width=True)

                st.subheader("📈 Interaction Breakdown")

                action_summary = df.groupby('action_type')['count'].sum().reset_index()
                fig_pie = px.pie(
                    action_summary,
                    values='count',
                    names='action_type',
                    title="Distribution of Interaction Types"
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No interactions found for the selected time range.")

            st.markdown("---")

            st.subheader("👥 Top Contributors to this Repository")

            top_contributors = session.query(
                Developer.username,
                func.count(Interaction.id).label('interaction_count')
            ).join(Interaction).filter(
                Interaction.repository_id == repo.id
            ).group_by(
                Developer.id
            ).order_by(
                func.count(Interaction.id).desc()
            ).limit(10).all()

            if top_contributors:
                contrib_df = pd.DataFrame([
                    {'Developer': c.username, 'Interactions': c.interaction_count}
                    for c in top_contributors
                ])

                fig_bar = px.bar(
                    contrib_df,
                    x='Developer',
                    y='Interactions',
                    title="Top 10 Contributors"
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("No contributors found for this repository.")
