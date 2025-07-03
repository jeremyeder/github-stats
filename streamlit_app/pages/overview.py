"""Overview dashboard page."""

from datetime import datetime, timedelta

import streamlit as st
from sqlalchemy import func

from github_stats.models.interactions import Developer, Interaction, Repository
from github_stats.utils.database import get_session


def show():
    """Display the overview dashboard."""
    st.header("📈 GitHub Stats Overview")

    with get_session() as session:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_devs = session.query(func.count(Developer.id)).scalar()
            st.metric("Total Developers", total_devs)

        with col2:
            total_repos = session.query(func.count(Repository.id)).scalar()
            st.metric("Total Repositories", total_repos)

        with col3:
            total_interactions = session.query(func.count(Interaction.id)).scalar()
            st.metric("Total Interactions", total_interactions)

        with col4:
            recent_interactions = session.query(func.count(Interaction.id)).filter(
                Interaction.date >= datetime.now() - timedelta(days=7)
            ).scalar()
            st.metric("Interactions (Last 7 Days)", recent_interactions)

        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📊 Recent Activity")
            recent_activity = session.query(
                Interaction.action_type,
                func.count(Interaction.id).label('count')
            ).filter(
                Interaction.date >= datetime.now() - timedelta(days=30)
            ).group_by(Interaction.action_type).all()

            if recent_activity:
                for activity in recent_activity:
                    st.write(f"**{activity.action_type}**: {activity.count}")
            else:
                st.info("No activity in the last 30 days")

        with col2:
            st.subheader("👥 Top Contributors")
            top_contributors = session.query(
                Developer.username,
                func.count(Interaction.id).label('interaction_count')
            ).join(Interaction).group_by(
                Developer.id
            ).order_by(
                func.count(Interaction.id).desc()
            ).limit(5).all()

            if top_contributors:
                for contributor in top_contributors:
                    st.write(
                        f"**{contributor.username}**: "
                        f"{contributor.interaction_count} interactions"
                    )
            else:
                st.info("No contributors found")

        st.markdown("---")
        st.info(
            "Use the sidebar to navigate to detailed repository "
            "or developer statistics."
        )
