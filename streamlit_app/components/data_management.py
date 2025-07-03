"""Data management page for tracking organizations and repositories."""

import streamlit as st
from sqlalchemy import func

from github_stats.models.interactions import Interaction, Organization, Repository
from github_stats.tracking.tracker import InteractionTracker
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
        
        # Add new organization
        col1, col2 = st.columns([3, 1])
        with col1:
            new_org_name = st.text_input("Organization name (e.g., 'microsoft', 'google'):", key="new_org_input")
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)  # Add spacing to align with input
            if st.button("➕ Add Organization", disabled=not new_org_name):
                try:
                    tracker = InteractionTracker()
                    with st.spinner(f"Adding organization '{new_org_name}'..."):
                        result = tracker.track_organization(new_org_name)
                        if result["exists"]:
                            st.success(f"✅ Successfully added organization: {new_org_name}")
                        else:
                            st.warning(f"⚠️ Organization '{new_org_name}' added but may not exist on GitHub")
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Failed to add organization: {str(e)}")
        
        # List current organizations
        organizations = session.query(Organization).all()
        
        if organizations:
            st.markdown("**Tracked Organizations:**")
            for org in organizations:
                repo_count = session.query(Repository).filter_by(organization_id=org.id).count()
                interaction_count = session.query(Interaction).filter_by(organization_id=org.id).count()
                last_synced = org.last_synced_at.strftime("%Y-%m-%d %H:%M") if org.last_synced_at else "Never"
                
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    st.write(f"**{org.name}** - {repo_count} repos, {interaction_count} interactions")
                    st.caption(f"Last synced: {last_synced}")
                
                with col2:
                    if st.button("🔄 Sync", key=f"sync_org_{org.id}"):
                        try:
                            tracker = InteractionTracker()
                            with st.spinner(f"Syncing {org.name}..."):
                                result = tracker.track_organization(org.name)
                                st.success(f"✅ Synced {org.name}")
                                st.rerun()
                        except Exception as e:
                            st.error(f"❌ Sync failed: {str(e)}")
                
                with col3:
                    if st.button("🗑️ Delete", key=f"delete_org_{org.id}"):
                        st.session_state[f"confirm_delete_org_{org.id}"] = True
                
                with col4:
                    if st.session_state.get(f"confirm_delete_org_{org.id}", False):
                        if st.button("✅ Confirm", key=f"confirm_org_{org.id}"):
                            try:
                                session.delete(org)
                                session.commit()
                                st.success(f"✅ Deleted organization: {org.name}")
                                if f"confirm_delete_org_{org.id}" in st.session_state:
                                    del st.session_state[f"confirm_delete_org_{org.id}"]
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Delete failed: {str(e)}")
                
                st.markdown("---")
        else:
            st.info("No organizations currently tracked")
        
        st.markdown("---")
        
        # Repositories management  
        st.subheader("📁 Repositories")
        
        # Add new repository
        col1, col2 = st.columns([3, 1])
        with col1:
            new_repo_name = st.text_input("Repository full name (e.g., 'microsoft/vscode', 'facebook/react'):", key="new_repo_input")
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)  # Add spacing to align with input
            if st.button("➕ Add Repository", disabled=not new_repo_name):
                try:
                    if "/" not in new_repo_name:
                        st.error("❌ Repository name must be in 'owner/repo' format")
                    else:
                        tracker = InteractionTracker()
                        with st.spinner(f"Adding repository '{new_repo_name}'..."):
                            result = tracker.track_repository(new_repo_name)
                            if result["exists"]:
                                st.success(f"✅ Successfully added repository: {new_repo_name}")
                            else:
                                st.warning(f"⚠️ Repository '{new_repo_name}' added but may not exist on GitHub")
                            st.rerun()
                except Exception as e:
                    st.error(f"❌ Failed to add repository: {str(e)}")
        
        # List current repositories
        repositories = session.query(Repository).all()
        
        if repositories:
            st.markdown("**Tracked Repositories:**")
            for repo in repositories:
                interaction_count = session.query(Interaction).filter_by(repository_id=repo.id).count()
                last_synced = repo.last_synced_at.strftime("%Y-%m-%d %H:%M") if repo.last_synced_at else "Never"
                org_name = repo.organization.name if repo.organization else "No org"
                
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    st.write(f"**{repo.full_name}** ({org_name}) - {interaction_count} interactions")
                    st.caption(f"Last synced: {last_synced}")
                
                with col2:
                    if st.button("🔄 Sync", key=f"sync_repo_{repo.id}"):
                        try:
                            tracker = InteractionTracker()
                            owner, repo_name = repo.full_name.split('/')
                            with st.spinner(f"Syncing {repo.full_name}..."):
                                # Run full sync for all interaction types
                                result = tracker.track_repository(repo.full_name)
                                tracker.track_commits(owner, repo_name)
                                tracker.track_issues(owner, repo_name)
                                tracker.track_pull_requests(owner, repo_name)
                                tracker.track_stargazers(owner, repo_name)
                                tracker.track_forks(owner, repo_name)
                                tracker.track_releases(owner, repo_name)
                                tracker.track_workflow_runs(owner, repo_name)
                                st.success(f"✅ Synced {repo.full_name}")
                                st.rerun()
                        except Exception as e:
                            st.error(f"❌ Sync failed: {str(e)}")
                
                with col3:
                    if st.button("🗑️ Delete", key=f"delete_repo_{repo.id}"):
                        st.session_state[f"confirm_delete_repo_{repo.id}"] = True
                
                with col4:
                    if st.session_state.get(f"confirm_delete_repo_{repo.id}", False):
                        if st.button("✅ Confirm", key=f"confirm_repo_{repo.id}"):
                            try:
                                session.delete(repo)
                                session.commit()
                                st.success(f"✅ Deleted repository: {repo.full_name}")
                                if f"confirm_delete_repo_{repo.id}" in st.session_state:
                                    del st.session_state[f"confirm_delete_repo_{repo.id}"]
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Delete failed: {str(e)}")
                
                st.markdown("---")
        else:
            st.info("No repositories currently tracked")
        
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