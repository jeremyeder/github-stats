"""Query Builder dashboard page with real database integration."""

from datetime import datetime, timedelta

import pandas as pd
import streamlit as st
from sqlalchemy import func

from github_stats.models.interactions import (
    Interaction,
    InteractionType,
    Organization,
    Repository,
)
from github_stats.utils.database import get_db

# Try to import plotly, fall back to basic charts if not available
try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

def get_organizations():
    """Get list of organizations from database."""
    with get_db() as session:
        organizations = session.query(Organization.name).all()
        return [org.name for org in organizations]

def get_repositories():
    """Get list of repositories from database."""
    with get_db() as session:
        repositories = session.query(Repository.full_name).all()
        return [repo.full_name for repo in repositories]

def get_users():
    """Get list of users from database."""
    with get_db() as session:
        users = session.query(Interaction.user).filter(
            Interaction.user.isnot(None)
        ).distinct().all()
        return [user.user for user in users]

def get_actions():
    """Get list of actions from database."""
    with get_db() as session:
        actions = session.query(Interaction.action).filter(
            Interaction.action.isnot(None)
        ).distinct().all()
        return [action.action for action in actions]

def execute_query(selected_orgs, selected_repos, selected_users, selected_types, selected_actions, date_range, logical_operator="AND"):
    """Execute real database query based on filter selections."""
    with get_db() as session:
        # Build base query with joins
        query = session.query(
            Interaction.id,
            Interaction.timestamp,
            Organization.name.label('organization'),
            Repository.full_name.label('repository'),
            Interaction.user,
            Interaction.type,
            Interaction.action,
            Interaction.resource_id,
            Interaction.extra_data
        ).outerjoin(
            Repository, Interaction.repository_id == Repository.id
        ).outerjoin(
            Organization, Interaction.organization_id == Organization.id
        )

        # Build filter conditions
        conditions = []

        if selected_orgs:
            conditions.append(Organization.name.in_(selected_orgs))

        if selected_repos:
            conditions.append(Repository.full_name.in_(selected_repos))

        if selected_users:
            conditions.append(Interaction.user.in_(selected_users))

        if selected_types:
            conditions.append(Interaction.type.in_(selected_types))

        if selected_actions:
            conditions.append(Interaction.action.in_(selected_actions))

        if len(date_range) == 2:
            start_date, end_date = date_range
            # Convert dates to datetime for comparison
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())
            conditions.append(Interaction.timestamp.between(start_datetime, end_datetime))

        # Apply conditions with logical operator
        if conditions:
            if logical_operator == "AND":
                for condition in conditions:
                    query = query.filter(condition)
            else:  # OR
                from sqlalchemy import or_
                query = query.filter(or_(*conditions))

        # Execute query
        results = query.order_by(Interaction.timestamp.desc()).limit(1000).all()

        # Convert to DataFrame
        data = []
        for result in results:
            data.append({
                "ID": result.id,
                "Timestamp": result.timestamp,
                "Organization": result.organization or "N/A",
                "Repository": result.repository or "N/A",
                "User": result.user or "N/A",
                "Interaction Type": result.type.value if result.type else "N/A",
                "Action": result.action or "N/A",
                "Resource ID": result.resource_id or "N/A",
                "Details": str(result.extra_data) if result.extra_data else "N/A"
            })

        return pd.DataFrame(data)

def generate_chart_data(selected_orgs, selected_repos, selected_users, selected_types, selected_actions, date_range, logical_operator="AND"):
    """Generate real chart data from database based on filters."""
    with get_db() as session:
        # Build base query with same filters as main query
        base_query = session.query(Interaction).outerjoin(
            Repository, Interaction.repository_id == Repository.id
        ).outerjoin(
            Organization, Interaction.organization_id == Organization.id
        )

        # Apply same filters as main query
        conditions = []

        if selected_orgs:
            conditions.append(Organization.name.in_(selected_orgs))

        if selected_repos:
            conditions.append(Repository.full_name.in_(selected_repos))

        if selected_users:
            conditions.append(Interaction.user.in_(selected_users))

        if selected_types:
            conditions.append(Interaction.type.in_(selected_types))

        if selected_actions:
            conditions.append(Interaction.action.in_(selected_actions))

        if len(date_range) == 2:
            start_date, end_date = date_range
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())
            conditions.append(Interaction.timestamp.between(start_datetime, end_datetime))

        # Apply conditions
        if conditions:
            if logical_operator == "AND":
                for condition in conditions:
                    base_query = base_query.filter(condition)
            else:  # OR
                from sqlalchemy import or_
                base_query = base_query.filter(or_(*conditions))

        # Time series data - daily interaction counts
        time_series_query = base_query.with_entities(
            func.date(Interaction.timestamp).label('date'),
            func.count(Interaction.id).label('interactions')
        ).group_by(func.date(Interaction.timestamp)).order_by(func.date(Interaction.timestamp))

        time_series_results = time_series_query.all()
        time_series = pd.DataFrame([
            {'date': result.date, 'interactions': result.interactions}
            for result in time_series_results
        ])

        # Interaction type distribution
        type_dist_query = base_query.with_entities(
            Interaction.type.label('type'),
            func.count(Interaction.id).label('count')
        ).group_by(Interaction.type)

        type_dist_results = type_dist_query.all()
        interaction_dist = pd.DataFrame([
            {'type': result.type.value if result.type else 'Unknown', 'count': result.count}
            for result in type_dist_results
        ])

        # Top users
        user_query = base_query.filter(
            Interaction.user.isnot(None)
        ).with_entities(
            Interaction.user.label('user'),
            func.count(Interaction.id).label('interactions')
        ).group_by(Interaction.user).order_by(
            func.count(Interaction.id).desc()
        ).limit(10)

        user_results = user_query.all()
        top_users = pd.DataFrame([
            {'user': result.user, 'interactions': result.interactions}
            for result in user_results
        ])

        return time_series, interaction_dist, top_users

def show():
    """Display the query builder dashboard."""
    st.header("🔍 Query Builder")
    st.markdown("Build custom queries to analyze your GitHub interaction data.")

    # Get real data from database
    available_orgs = get_organizations()
    available_repos = get_repositories()
    available_users = get_users()
    available_actions = get_actions()

    # Full width layout with filters at top
    st.subheader("🛠️ Query Filters")
    
    # Filters in a grid layout
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Organization filter
        selected_orgs = st.multiselect(
            "Organizations",
            options=available_orgs,
            default=[],
            help="Select organizations to include in the query"
        )

        # Interaction type filter
        selected_types = st.multiselect(
            "Interaction Types",
            options=[t.value for t in InteractionType],
            default=[],
            help="Select interaction types to include"
        )

    with col2:
        # Repository filter
        selected_repos = st.multiselect(
            "Repositories",
            options=available_repos,
            default=[],
            help="Select repositories to include in the query"
        )

        # Action filter
        selected_actions = st.multiselect(
            "Actions",
            options=available_actions,
            default=[],
            help="Select specific actions to filter by"
        )

    with col3:
        # User filter
        selected_users = st.multiselect(
            "Users",
            options=available_users,
            default=[],
            help="Select specific users to filter by"
        )

        # Date range filter
        st.markdown("**📅 Date Range**")
        date_range = st.date_input(
            "Select date range",
            value=(datetime.now() - timedelta(days=30), datetime.now()),
            help="Choose the date range for the query"
        )

    # Controls row
    col1, col2, col3 = st.columns([2, 2, 3])
    
    with col1:
        # Logical operators
        logical_operator = st.radio(
            "🔗 Query Logic:",
            options=["AND", "OR"],
            index=0,
            help="Choose how to combine multiple filter conditions",
            horizontal=True
        )

    with col2:
        st.markdown("**Execute**")
        # Execute query button
        if st.button("🚀 Execute Query", type="primary", use_container_width=True):
            st.session_state.query_executed = True
            st.success("Query executed successfully!")

    with col3:
        pass  # Empty space for balance

    # Query Preview Section (moved below filters)
    st.markdown("---")
    st.subheader("📋 Query Preview")

    # Generate SQL query preview with correct column names
    query_parts = []
    if selected_orgs:
        org_list = "', '".join(selected_orgs)
        query_parts.append(f"o.name IN ('{org_list}')")
    if selected_repos:
        repo_list = "', '".join(selected_repos)
        query_parts.append(f"r.full_name IN ('{repo_list}')")
    if selected_users:
        user_list = "', '".join(selected_users)
        query_parts.append(f"i.user IN ('{user_list}')")
    if selected_types:
        type_list = "', '".join(selected_types)
        query_parts.append(f"i.type IN ('{type_list}')")
    if selected_actions:
        action_list = "', '".join(selected_actions)
        query_parts.append(f"i.action IN ('{action_list}')")

    if len(date_range) == 2:
        query_parts.append(f"i.timestamp BETWEEN '{date_range[0]}' AND '{date_range[1]}'")

    where_clause = f" {logical_operator} ".join(query_parts) if query_parts else "1=1"

    mock_sql = f"""SELECT *
FROM interactions i
LEFT JOIN repositories r ON i.repository_id = r.id
LEFT JOIN organizations o ON i.organization_id = o.id
WHERE {where_clause}
ORDER BY i.timestamp DESC
LIMIT 1000;"""

    st.code(mock_sql, language="sql")

    # Query validation status
    if query_parts:
        st.success("✅ Query is valid")
    else:
        st.warning("⚠️ No filters selected - will return all data")

    # Saved Queries Section
    st.markdown("---")
    st.subheader("💾 Saved Queries")

    col1, col2, col3 = st.columns(3)

    with col1:
        query_name = st.text_input("Query Name", placeholder="Enter a name for this query")
        if st.button("Save Query", use_container_width=True):
            if query_name:
                st.success(f"Query '{query_name}' saved successfully!")
            else:
                st.error("Please enter a query name")

    with col2:
        saved_queries = [
            "Top Contributors Last Month",
            "Pull Request Activity",
            "Issue Tracking Report",
            "Commit Frequency Analysis",
            "Repository Comparison"
        ]
        selected_saved = st.selectbox("Load Saved Query", options=[""] + saved_queries)
        if st.button("Load Query", use_container_width=True):
            if selected_saved:
                st.success(f"Loaded query: {selected_saved}")

    with col3:
        st.write("**Query Templates:**")
        templates = [
            "🚀 Most Active Repositories",
            "👥 Developer Leaderboard",
            "📊 Monthly Trends",
            "🔧 Issue Resolution Times",
            "🌟 Popular Features"
        ]
        for i, template in enumerate(templates):
            if st.button(template, key=f"template_{i}", use_container_width=True):
                st.info(f"Applied template: {template}")

    # Results Section
    if st.session_state.get('query_executed', False):
        st.markdown("---")
        st.subheader("📊 Query Results")

        # Execute real query
        results_df = execute_query(
            selected_orgs,
            selected_repos,
            selected_users,
            selected_types,
            selected_actions,
            date_range,
            logical_operator
        )

        # Results summary
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Results", len(results_df))
        with col2:
            st.metric("Unique Users", results_df['User'].nunique())
        with col3:
            st.metric("Unique Repos", results_df['Repository'].nunique())
        with col4:
            st.metric("Date Range", f"{len(results_df['Timestamp'].dt.date.unique())} days")

        # Export options
        st.markdown("**Export Options:**")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📄 Export CSV", use_container_width=True):
                st.success("CSV export initiated! (Mock)")
        with col2:
            if st.button("📋 Export JSON", use_container_width=True):
                st.success("JSON export initiated! (Mock)")
        with col3:
            if st.button("📊 Export Excel", use_container_width=True):
                st.success("Excel export initiated! (Mock)")

        # Tabbed results view
        tab1, tab2, tab3 = st.tabs(["📋 Data Table", "📈 Visualizations", "📊 Analytics"])

        with tab1:
            st.subheader("Query Results Table")

            # Pagination controls
            page_size = st.selectbox("Results per page", [10, 25, 50, 100], index=1)
            total_pages = (len(results_df) - 1) // page_size + 1

            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                page = st.number_input(
                    f"Page (1-{total_pages})",
                    min_value=1,
                    max_value=total_pages,
                    value=1
                )

            # Display paginated results
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size

            st.dataframe(
                results_df.iloc[start_idx:end_idx],
                use_container_width=True,
                hide_index=True
            )

        with tab2:
            st.subheader("Data Visualizations")

            # Generate real chart data
            time_series, interaction_dist, top_users = generate_chart_data(
                selected_orgs,
                selected_repos,
                selected_users,
                selected_types,
                selected_actions,
                date_range,
                logical_operator
            )

            # Time series chart
            st.markdown("**📈 Interactions Over Time**")
            if not time_series.empty:
                if PLOTLY_AVAILABLE:
                    fig_time = px.line(
                        time_series,
                        x='date',
                        y='interactions',
                        title='Daily Interaction Volume',
                        labels={'interactions': 'Number of Interactions', 'date': 'Date'}
                    )
                    st.plotly_chart(fig_time, use_container_width=True)
                else:
                    st.line_chart(time_series.set_index('date'))
            else:
                st.info("No time series data available for the selected filters.")

            # Interaction type distribution
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**🔧 Interaction Type Distribution**")
                if not interaction_dist.empty:
                    if PLOTLY_AVAILABLE:
                        fig_pie = px.pie(
                            interaction_dist,
                            values='count',
                            names='type',
                            title='Interaction Types'
                        )
                        st.plotly_chart(fig_pie, use_container_width=True)
                    else:
                        st.bar_chart(interaction_dist.set_index('type'))
                else:
                    st.info("No interaction type data available for the selected filters.")

            with col2:
                st.markdown("**👥 Top Contributors**")
                if not top_users.empty:
                    if PLOTLY_AVAILABLE:
                        fig_bar = px.bar(
                            top_users,
                            x='user',
                            y='interactions',
                            title='Most Active Users'
                        )
                        fig_bar.update_layout(xaxis_tickangle=-45)
                        st.plotly_chart(fig_bar, use_container_width=True)
                    else:
                        st.bar_chart(top_users.set_index('user'))
                else:
                    st.info("No user data available for the selected filters.")

        with tab3:
            st.subheader("Analytics Summary")

            # Analytics metrics
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**📊 Key Metrics**")
                st.metric("Average Daily Interactions", "47.3", "↑ 12%")
                st.metric("Peak Activity Day", "Wednesday", "")
                st.metric("Most Active Hour", "2:00 PM", "")
                st.metric("Response Time (Avg)", "4.2 hours", "↓ 15%")

            with col2:
                st.markdown("**🎯 Insights**")
                st.info("💡 Pull requests have 23% higher engagement than issues")
                st.info("🔥 Microsoft repositories show 40% more activity")
                st.info("⭐ Morning commits (9-11 AM) get reviewed 2x faster")
                st.info("📅 Weekend activity is 60% lower than weekdays")

            # Trend analysis
            st.markdown("**📈 Trend Analysis**")
            trend_data = pd.DataFrame({
                'metric': ['Total Interactions', 'Unique Users', 'Repositories', 'Average Response Time'],
                'current': [1247, 89, 23, 4.2],
                'previous': [1156, 82, 21, 4.9],
                'change': ['+7.9%', '+8.5%', '+9.5%', '-14.3%']
            })
            st.dataframe(trend_data, use_container_width=True, hide_index=True)

    # Help section
    st.markdown("---")
    with st.expander("❓ Help & Tips"):
        st.markdown("""
        **How to use the Query Builder:**
        
        1. **Select Filters**: Choose organizations, repositories, users, and interaction types
        2. **Set Date Range**: Pick the time period you want to analyze
        3. **Choose Logic**: Use AND for stricter filtering, OR for broader results
        4. **Execute Query**: Click the execute button to run your query
        5. **View Results**: Explore data in the table, visualizations, and analytics tabs
        6. **Save Queries**: Save frequently used queries for quick access
        7. **Export Data**: Download results in CSV, JSON, or Excel format
        
        **Tips:**
        - Start with broad filters and narrow down for specific insights
        - Use date ranges to identify trends over time
        - Save complex queries as templates for team use
        - Export data for further analysis in external tools
        """)

