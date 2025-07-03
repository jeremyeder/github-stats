"""Advanced visualization dashboard with comprehensive charts and analytics."""

from datetime import datetime, timedelta

import streamlit as st

from github_stats.models.interactions import (
    Interaction,
    InteractionType,
    Organization,
    Repository,
)
from github_stats.ui.charts import ChartGenerator, display_metrics_cards, export_to_csv
from github_stats.utils.database import get_db


def get_filter_options():
    """Get filter options from database."""
    with get_db() as session:
        organizations = session.query(Organization.name).all()
        repositories = session.query(Repository.full_name).all()
        users = session.query(Interaction.user).filter(
            Interaction.user.isnot(None)
        ).distinct().all()

        return {
            'organizations': [org.name for org in organizations],
            'repositories': [repo.full_name for repo in repositories],
            'users': [user.user for user in users],
            'interaction_types': [t.value for t in InteractionType]
        }


def create_sidebar_filters() -> dict:
    """Create sidebar filters and return filter values."""
    st.sidebar.title("🎛️ Visualization Controls")

    # Get filter options
    options = get_filter_options()

    # Date range filter
    st.sidebar.subheader("📅 Date Range")
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)

    date_range = st.sidebar.date_input(
        "Select date range:",
        value=(start_date, end_date),
        max_value=end_date,
        help="Select the date range for analysis"
    )

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date = date_range
        end_date = date_range

    # Interaction type filter
    st.sidebar.subheader("🔧 Interaction Types")
    selected_types = st.sidebar.multiselect(
        "Filter by interaction types:",
        options=options['interaction_types'],
        default=options['interaction_types'],
        help="Select which interaction types to include"
    )

    # Repository filter
    st.sidebar.subheader("📁 Repositories")
    selected_repos = st.sidebar.multiselect(
        "Filter by repositories:",
        options=options['repositories'],
        help="Leave empty to include all repositories"
    )

    # Organization filter
    st.sidebar.subheader("🏢 Organizations")
    selected_orgs = st.sidebar.multiselect(
        "Filter by organizations:",
        options=options['organizations'],
        help="Leave empty to include all organizations"
    )

    # Chart configuration
    st.sidebar.subheader("📊 Chart Settings")

    time_grouping = st.sidebar.selectbox(
        "Time grouping for charts:",
        options=['date', 'week', 'month', 'hour'],
        index=0,
        help="How to group data by time"
    )

    top_n = st.sidebar.slider(
        "Number of items in top charts:",
        min_value=5,
        max_value=50,
        value=15,
        help="Number of top items to show in ranking charts"
    )

    # Data view options
    st.sidebar.subheader("🔍 Data View")
    show_raw_data = st.sidebar.checkbox(
        "Show raw data table",
        value=False,
        help="Display the raw data table below charts"
    )

    include_stars = st.sidebar.checkbox(
        "⭐ Include stars",
        value=False,
        help="Include star interactions in analysis"
    )

    enable_export = st.sidebar.checkbox(
        "Enable data export",
        value=True,
        help="Allow CSV export of filtered data"
    )

    return {
        'start_date': datetime.combine(start_date, datetime.min.time()),
        'end_date': datetime.combine(end_date, datetime.max.time()),
        'interaction_types': [InteractionType(t) for t in selected_types] if selected_types else None,
        'repositories': None,  # Will need to convert to IDs
        'organizations': None,  # Will need to convert to IDs
        'selected_repo_names': selected_repos,
        'selected_org_names': selected_orgs,
        'time_grouping': time_grouping,
        'top_n': top_n,
        'show_raw_data': show_raw_data,
        'include_stars': include_stars,
        'enable_export': enable_export
    }


def convert_names_to_ids(filters: dict) -> dict:
    """Convert repository and organization names to IDs."""
    with get_db() as session:
        # Convert repository names to IDs
        if filters['selected_repo_names']:
            repo_ids = session.query(Repository.id).filter(
                Repository.full_name.in_(filters['selected_repo_names'])
            ).all()
            filters['repositories'] = [r.id for r in repo_ids]

        # Convert organization names to IDs
        if filters['selected_org_names']:
            org_ids = session.query(Organization.id).filter(
                Organization.name.in_(filters['selected_org_names'])
            ).all()
            filters['organizations'] = [o.id for o in org_ids]

    return filters


def show():
    """Main visualization dashboard page."""
    st.title("📈 Advanced Analytics Dashboard")
    st.markdown("Comprehensive visualization and analysis of GitHub interactions")
    
    # Data integrity info
    st.info("📊 **Data Integrity**: Showing only interactions with real GitHub timestamps (forks, workflow runs). Stars excluded due to lack of individual timestamps in GitHub API.")
    st.markdown("---")

    # Create sidebar filters
    filters = create_sidebar_filters()
    filters = convert_names_to_ids(filters)

    # Initialize chart generator
    with get_db() as session:
        chart_gen = ChartGenerator(session)

        # Get filtered data
        try:
            df = chart_gen.get_interactions_data(filters)

            if df.empty:
                st.warning("No data found for the selected filters. Try expanding your date range or removing some filters.")
                return

            # Display metrics cards
            st.subheader("📊 Key Metrics")
            metrics = chart_gen.create_metrics_cards(df)
            display_metrics_cards(metrics)
            st.markdown("---")

            # Create chart layout
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("📈 Interactions Over Time")
                time_series_chart = chart_gen.create_time_series_chart(df, filters['time_grouping'])
                st.plotly_chart(time_series_chart, use_container_width=True)

                st.subheader("🥧 Interaction Types Distribution")
                pie_chart = chart_gen.create_interaction_type_pie(df)
                st.plotly_chart(pie_chart, use_container_width=True)

            with col2:
                st.subheader("📊 Interactions by Type (Stacked)")
                stacked_chart = chart_gen.create_stacked_bar_chart(df, filters['time_grouping'])
                st.plotly_chart(stacked_chart, use_container_width=True)

                st.subheader("🌡️ Activity Heatmap")
                heatmap = chart_gen.create_heatmap(df)
                st.plotly_chart(heatmap, use_container_width=True)

            # Top charts section
            st.markdown("---")
            st.subheader("🏆 Top Rankings")

            tab1, tab2, tab3 = st.tabs(["Top Repositories", "Top Users", "Top Organizations"])

            with tab1:
                if 'repository_name' in df.columns:
                    repo_chart = chart_gen.create_horizontal_bar_chart(
                        df, 'repository_name', filters['top_n']
                    )
                    st.plotly_chart(repo_chart, use_container_width=True)
                else:
                    st.info("No repository data available")

            with tab2:
                if 'user' in df.columns:
                    user_chart = chart_gen.create_horizontal_bar_chart(
                        df, 'user', filters['top_n']
                    )
                    st.plotly_chart(user_chart, use_container_width=True)
                else:
                    st.info("No user data available")

            with tab3:
                if 'organization_name' in df.columns:
                    org_chart = chart_gen.create_horizontal_bar_chart(
                        df, 'organization_name', filters['top_n']
                    )
                    st.plotly_chart(org_chart, use_container_width=True)
                else:
                    st.info("No organization data available")

            # Export functionality
            if filters['enable_export']:
                st.markdown("---")
                st.subheader("💾 Export Data")

                col1, col2 = st.columns([3, 1])

                with col1:
                    st.info(f"Export {len(df):,} filtered interactions to CSV")

                with col2:
                    csv_data = export_to_csv(df)
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv_data,
                        file_name=f"github_stats_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        help="Download the filtered data as CSV"
                    )

            # Raw data table
            if filters['show_raw_data']:
                st.markdown("---")
                st.subheader("🗃️ Raw Data")

                # Display summary
                st.info(f"Showing {len(df):,} interactions (filtered results)")

                # Column selector for display
                display_columns = st.multiselect(
                    "Select columns to display:",
                    options=df.columns.tolist(),
                    default=['timestamp', 'type', 'user', 'repository_name', 'action'],
                    help="Choose which columns to show in the table"
                )

                if display_columns:
                    # Show paginated data
                    page_size = st.selectbox("Rows per page:", [25, 50, 100, 500], index=1)

                    total_pages = (len(df) - 1) // page_size + 1
                    page = st.number_input(
                        f"Page (1 of {total_pages}):",
                        min_value=1,
                        max_value=total_pages,
                        value=1
                    )

                    start_idx = (page - 1) * page_size
                    end_idx = start_idx + page_size

                    st.dataframe(
                        df[display_columns].iloc[start_idx:end_idx],
                        use_container_width=True,
                        height=400
                    )
                else:
                    st.warning("Please select at least one column to display")

        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
            st.info("Please check your database connection and try again.")


if __name__ == "__main__":
    show()
