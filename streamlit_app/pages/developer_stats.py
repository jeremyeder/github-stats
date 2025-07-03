"""Developer statistics dashboard page."""

from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import func

from github_stats.models.interactions import Interaction, Repository
from github_stats.utils.database import get_db


def show():
    """Display developer statistics."""
    st.header("👨‍💻 Developer Statistics")

    with get_db() as session:
        # Get unique usernames from interactions
        developers = session.query(Interaction.user).filter(
            Interaction.user.isnot(None)
        ).distinct().all()
        dev_usernames = [dev.user for dev in developers]

        if not dev_usernames:
            st.warning("No developers found. Start tracking some developers first!")
            return

        selected_dev = st.selectbox("Select a developer:", dev_usernames)

        if selected_dev:
            # We don't have a developer model, so we'll work with the username directly
            developer_username = selected_dev

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                total_interactions = session.query(func.count(Interaction.id)).filter(
                    Interaction.user == developer_username
                ).scalar()
                st.metric("Total Interactions", total_interactions)

            with col2:
                unique_repos = session.query(
                    func.count(func.distinct(Interaction.repository_id))
                ).filter(
                    Interaction.user == developer_username
                ).scalar()
                st.metric("Repositories Contributed To", unique_repos)

            with col3:
                recent_interactions = session.query(func.count(Interaction.id)).filter(
                    Interaction.user == developer_username,
                    Interaction.timestamp >= datetime.now() - timedelta(days=7)
                ).scalar()
                st.metric("Interactions (Last 7 Days)", recent_interactions)

            with col4:
                most_common_action = session.query(
                    Interaction.action,
                    func.count(Interaction.id).label('count')
                ).filter(
                    Interaction.user == developer_username
                ).group_by(
                    Interaction.action
                ).order_by(
                    func.count(Interaction.id).desc()
                ).first()

                if most_common_action and most_common_action.action:
                    st.metric("Most Common Action", most_common_action.action)
                else:
                    st.metric("Most Common Action", "N/A")

            st.markdown("---")

            st.subheader("📅 Activity Timeline")

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

            activity_data = session.query(
                func.date(Interaction.timestamp).label('date'),
                func.count(Interaction.id).label('count')
            ).filter(
                Interaction.user == developer_username,
                Interaction.timestamp >= date_filter
            ).group_by(
                func.date(Interaction.timestamp)
            ).all()

            if activity_data:
                df = pd.DataFrame([
                    {'date': a.date, 'interactions': a.count}
                    for a in activity_data
                ])

                fig = px.bar(
                    df,
                    x='date',
                    y='interactions',
                    title=f"Daily Activity for {selected_dev}",
                    labels={'interactions': 'Number of Interactions', 'date': 'Date'}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No activity found for the selected time range.")

            st.markdown("---")

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("🎯 Action Types Distribution")

                action_dist = session.query(
                    Interaction.action,
                    func.count(Interaction.id).label('count')
                ).filter(
                    Interaction.user == developer_username
                ).group_by(
                    Interaction.action
                ).all()

                if action_dist:
                    action_df = pd.DataFrame([
                        {'Action Type': a.action or 'Unknown', 'Count': a.count}
                        for a in action_dist
                    ])

                    fig_pie = px.pie(
                        action_df,
                        values='Count',
                        names='Action Type',
                        title="Distribution of Actions"
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    st.info("No actions found.")

            with col2:
                st.subheader("🏢 Top Repositories")

                top_repos = session.query(
                    Repository.full_name,
                    func.count(Interaction.id).label('interaction_count')
                ).join(Interaction).filter(
                    Interaction.user == developer_username
                ).group_by(
                    Repository.id
                ).order_by(
                    func.count(Interaction.id).desc()
                ).limit(5).all()

                if top_repos:
                    for repo in top_repos:
                        st.write(
                            f"**{repo.full_name}**: "
                            f"{repo.interaction_count} interactions"
                        )
                else:
                    st.info("No repository interactions found.")

            st.markdown("---")

            st.subheader("📊 Detailed Activity Log")

            recent_activities = session.query(Interaction).filter(
                Interaction.user == developer_username
            ).order_by(
                Interaction.timestamp.desc()
            ).limit(20).all()

            if recent_activities:
                activity_list = []
                for activity in recent_activities:
                    repo = session.query(Repository).get(activity.repository_id)
                    activity_list.append({
                        'Date': activity.timestamp.strftime('%Y-%m-%d %H:%M'),
                        'Repository': repo.full_name if repo else 'Unknown',
                        'Action': activity.action or 'Unknown',
                        'Details': getattr(activity, 'extra_data', {}) or 'N/A'
                    })

                activity_df = pd.DataFrame(activity_list)
                st.dataframe(activity_df, use_container_width=True)
            else:
                st.info("No recent activities found.")
