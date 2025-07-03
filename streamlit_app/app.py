"""Main Streamlit application entry point."""

import streamlit as st

from streamlit_app.pages import developer_stats, overview, repository_stats


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
        st.title("Navigation")
        page = st.radio(
            "Select a page:",
            ["Overview", "Repository Stats", "Developer Stats"],
            index=0
        )

    if page == "Overview":
        overview.show()
    elif page == "Repository Stats":
        repository_stats.show()
    elif page == "Developer Stats":
        developer_stats.show()


if __name__ == "__main__":
    main()
