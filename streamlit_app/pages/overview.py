"""Overview dashboard page."""

from datetime import datetime, timedelta

import streamlit as st
from sqlalchemy import func

from github_stats.models.interactions import Interaction, Repository
from github_stats.utils.database import get_db


def show():
    """Display the overview dashboard."""
    st.header("📈 GitHub Stats Overview")

    with get_db() as session:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_devs = session.query(func.count(func.distinct(Interaction.user))).filter(
                Interaction.user.isnot(None)
            ).scalar()
            st.metric("Total Developers", total_devs)

        with col2:
            total_repos = session.query(func.count(Repository.id)).scalar()
            st.metric("Total Repositories", total_repos)

        with col3:
            total_interactions = session.query(func.count(Interaction.id)).scalar()
            st.metric("Total Interactions", total_interactions)

        with col4:
            recent_interactions = session.query(func.count(Interaction.id)).filter(
                Interaction.timestamp >= datetime.now() - timedelta(days=7)
            ).scalar()
            st.metric("Interactions (Last 7 Days)", recent_interactions)

        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📊 Recent Activity")
            recent_activity = session.query(
                Interaction.action,
                func.count(Interaction.id).label('count')
            ).filter(
                Interaction.timestamp >= datetime.now() - timedelta(days=30)
            ).group_by(Interaction.action).all()

            if recent_activity:
                for activity in recent_activity:
                    action_name = activity.action or 'Unknown'
                    st.write(f"**{action_name}**: {activity.count}")
            else:
                st.info("No activity in the last 30 days")

        with col2:
            st.subheader("👥 Top Contributors")
            top_contributors = session.query(
                Interaction.user,
                func.count(Interaction.id).label('interaction_count')
            ).filter(
                Interaction.user.isnot(None)
            ).group_by(
                Interaction.user
            ).order_by(
                func.count(Interaction.id).desc()
            ).limit(5).all()

            if top_contributors:
                for contributor in top_contributors:
                    st.write(
                        f"**{contributor.user}**: "
                        f"{contributor.interaction_count} interactions"
                    )
            else:
                st.info("No contributors found")

        st.markdown("---")
        st.info(
            "Use the sidebar to navigate to detailed repository "
            "or developer statistics."
        )
