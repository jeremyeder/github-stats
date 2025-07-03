"""Data management page for tracking organizations and repositories."""

import streamlit as st
from sqlalchemy import func

from github_stats.models.interactions import Interaction, Organization, Repository
from github_stats.utils.database import get_db


def show():
    """Display the data management interface."""
    st.header("🗄️ Data Management")
    st.markdown("Manage tracked organizations and repositories")

    with get_db() as session:
        # Current tracking status
        st.subheader("📊 Current Tracking Status")
        
        # Get statistics
        total_orgs = session.query(Organization).count()
        total_repos = session.query(Repository).count()
        total_interactions = session.query(Interaction).count()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Tracked Organizations", total_orgs)
        with col2:
            st.metric("Tracked Repositories", total_repos)
        with col3:
            st.metric("Total Interactions", total_interactions)
        
        st.markdown("---")
        
        # Organizations management
        st.subheader("🏢 Organizations")
        
        # List current organizations
        organizations = session.query(Organization).all()
        
        if organizations:
            org_data = []
            for org in organizations:
                repo_count = session.query(Repository).filter_by(organization_id=org.id).count()
                interaction_count = session.query(Interaction).filter_by(organization_id=org.id).count()
                
                org_data.append({
                    "Name": org.name,
                    "GitHub ID": org.github_id,
                    "Repositories": repo_count,
                    "Interactions": interaction_count,
                    "Description": org.description or "N/A"
                })
            
            st.dataframe(org_data, use_container_width=True, height=200)
        else:
            st.info("No organizations currently tracked")
        
        # Add new organization
        with st.expander("➕ Add New Organization"):
            new_org_name = st.text_input("Organization name (e.g., 'microsoft', 'google'):")
            if st.button("Add Organization", disabled=not new_org_name):
                st.info(f"Would add organization: {new_org_name}")
                st.warning("⚠️ Adding organizations requires implementation of tracking logic")
        
        st.markdown("---")
        
        # Repositories management  
        st.subheader("📁 Repositories")
        
        # List current repositories
        repositories = session.query(Repository).all()
        
        if repositories:
            repo_data = []
            for repo in repositories:
                interaction_count = session.query(Interaction).filter_by(repository_id=repo.id).count()
                last_activity = session.query(func.max(Interaction.timestamp)).filter_by(repository_id=repo.id).scalar()
                
                repo_data.append({
                    "Repository": repo.full_name,
                    "Organization": repo.organization.name if repo.organization else "N/A",
                    "GitHub ID": repo.github_id,
                    "Interactions": interaction_count,
                    "Last Activity": last_activity.strftime("%Y-%m-%d %H:%M") if last_activity else "Never",
                    "Private": "Yes" if repo.is_private else "No"
                })
            
            st.dataframe(repo_data, use_container_width=True, height=300)
        else:
            st.info("No repositories currently tracked")
        
        # Add new repository
        with st.expander("➕ Add New Repository"):
            new_repo_name = st.text_input("Repository full name (e.g., 'microsoft/vscode', 'facebook/react'):")
            if st.button("Add Repository", disabled=not new_repo_name):
                st.info(f"Would add repository: {new_repo_name}")
                st.warning("⚠️ Adding repositories requires implementation of tracking logic")
        
        st.markdown("---")
        
        # Data collection management
        st.subheader("🔄 Data Collection")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Manual Data Collection**")
            if st.button("🚀 Trigger Full Sync", type="primary"):
                st.warning("⚠️ Manual sync requires implementation of tracking triggers")
                st.info("This would trigger a full data collection cycle for all tracked repositories")
        
        with col2:
            st.markdown("**Bulk Operations**")
            if st.button("📤 Export Configuration"):
                st.warning("⚠️ Export functionality requires implementation")
                st.info("This would export the current tracking configuration as JSON")
            
            if st.button("📥 Import Configuration"):
                st.warning("⚠️ Import functionality requires implementation")
                st.info("This would allow importing tracking configuration from JSON")
        
        st.markdown("---")
        
        # Data health monitoring
        st.subheader("🏥 Data Health")
        
        # Calculate data freshness
        if total_interactions > 0:
            latest_interaction = session.query(func.max(Interaction.timestamp)).scalar()
            if latest_interaction:
                import datetime
                days_since_update = (datetime.datetime.now() - latest_interaction).days
                
                if days_since_update == 0:
                    st.success(f"✅ Data is fresh (last update: today)")
                elif days_since_update <= 1:
                    st.success(f"✅ Data is fresh (last update: {days_since_update} day ago)")
                elif days_since_update <= 7:
                    st.warning(f"⚠️ Data is {days_since_update} days old")
                else:
                    st.error(f"❌ Data is stale ({days_since_update} days old)")
            else:
                st.error("❌ No interaction timestamps found")
        else:
            st.error("❌ No data collected yet")
        
        # Data quality checks
        st.markdown("**Data Quality Checks:**")
        
        # Check for interactions without timestamps
        interactions_without_timestamps = session.query(Interaction).filter(Interaction.timestamp.is_(None)).count()
        if interactions_without_timestamps > 0:
            st.warning(f"⚠️ {interactions_without_timestamps} interactions missing timestamps")
        else:
            st.success("✅ All interactions have timestamps")
        
        # Check for interactions without users
        interactions_without_users = session.query(Interaction).filter(Interaction.user.is_(None)).count()
        if interactions_without_users > 0:
            st.info(f"ℹ️ {interactions_without_users} interactions without user information (normal for some interaction types)")
        
        # Check for orphaned interactions
        orphaned_interactions = session.query(Interaction).filter(
            Interaction.repository_id.is_(None),
            Interaction.organization_id.is_(None)
        ).count()
        if orphaned_interactions > 0:
            st.warning(f"⚠️ {orphaned_interactions} interactions not linked to any repository or organization")
        else:
            st.success("✅ All interactions properly linked")


if __name__ == "__main__":
    show()