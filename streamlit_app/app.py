"""Main Streamlit application entry point."""

import streamlit as st

from streamlit_app.components import (
    data_management,
    developer_stats,
    query_builder,
    repository_stats,
    visualization,
)


def main():
    """Main application entry point."""
    st.set_page_config(
        page_title="GitHub Stats Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("📊 GitHub Stats Dashboard")
    st.markdown("---")

    with st.sidebar:
        st.title("GitHub Stats")
        page = st.radio(
            "Select a page:",
            [
                "GitHub Analytics",
                "Query Builder",
                "Repository Stats",
                "Developer Stats",
                "Data",
            ],
            index=0,
        )

    if page == "GitHub Analytics":
        visualization.show()
    elif page == "Query Builder":
        query_builder.show()
    elif page == "Repository Stats":
        repository_stats.show()
    elif page == "Developer Stats":
        developer_stats.show()
    elif page == "Data":
        data_management.show()


if __name__ == "__main__":
    main()
