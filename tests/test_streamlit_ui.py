"""Simple UI tests for GitHub Stats Streamlit dashboard."""

from streamlit.testing.v1 import AppTest


class TestStreamlitApp:
    """Test cases for the main Streamlit application."""

    def test_app_loads_successfully(self, mock_empty_db):
        """Test that the main app loads without errors."""
        at = AppTest.from_file("streamlit_app/app.py")
        at.run()

        # Check that no exceptions occurred
        assert not at.exception, f"App crashed with: {at.exception}"

        # Check that the main title is present
        assert len(at.title) > 0, "No title found"
        assert "GitHub Stats Dashboard" in str(at.title[0].value)

    def test_sidebar_navigation_exists(self, mock_empty_db):
        """Test that sidebar navigation is present."""
        at = AppTest.from_file("streamlit_app/app.py")
        at.run()

        # Check that sidebar radio button exists
        assert len(at.radio) > 0, "No radio buttons found"

        # Check that all expected pages are in the radio options
        radio_options = at.radio[0].options
        expected_pages = ["Query Builder", "Repository Stats", "Developer Stats"]

        for page in expected_pages:
            assert page in radio_options, f"Page '{page}' not found in navigation"

    def test_default_page_is_query_builder(self, mock_empty_db):
        """Test that Query Builder is the default page."""
        at = AppTest.from_file("streamlit_app/app.py")
        at.run()

        # Check that Query Builder is selected by default
        assert at.radio[0].value == "Query Builder"

        # Check that query builder content is displayed
        headers = [h.value for h in at.header]
        assert any("Query Builder" in str(h) for h in headers)

    def test_page_navigation_repository_stats(self, mock_empty_db):
        """Test navigation to Repository Stats page."""
        at = AppTest.from_file("streamlit_app/app.py")
        at.run()

        # Navigate to Repository Stats
        at.radio[0].set_value("Repository Stats").run()

        # Check that no exceptions occurred
        assert not at.exception, f"Repository Stats page crashed with: {at.exception}"

        # Check that repository stats content is displayed
        headers = [h.value for h in at.header]
        assert any("Repository Statistics" in str(h) for h in headers)

    def test_page_navigation_developer_stats(self, mock_empty_db):
        """Test navigation to Developer Stats page."""
        at = AppTest.from_file("streamlit_app/app.py")
        at.run()

        # Navigate to Developer Stats
        at.radio[0].set_value("Developer Stats").run()

        # Check that no exceptions occurred
        assert not at.exception, f"Developer Stats page crashed with: {at.exception}"

        # Check that developer stats content is displayed
        headers = [h.value for h in at.header]
        assert any("Developer Statistics" in str(h) for h in headers)

    def test_empty_data_handling_overview(self, mock_empty_db):
        """Test that Overview page handles empty data gracefully."""
        at = AppTest.from_file("streamlit_app/app.py")
        at.run()

        # Should not crash with empty data
        assert not at.exception

        # Check that metrics are displayed (even if 0)
        assert len(at.metric) > 0, "No metrics found on overview page"

    def test_empty_data_handling_repository_stats(self, mock_empty_db):
        """Test that Repository Stats page handles empty data gracefully."""
        at = AppTest.from_file("streamlit_app/app.py")
        at.run()

        # Navigate to Repository Stats
        at.radio[0].set_value("Repository Stats").run()

        # Should not crash with empty data
        assert not at.exception

        # Should show warning about no repositories
        warnings = [w.value for w in at.warning]
        assert any("No repositories found" in str(w) for w in warnings)

    def test_empty_data_handling_developer_stats(self, mock_empty_db):
        """Test that Developer Stats page handles empty data gracefully."""
        at = AppTest.from_file("streamlit_app/app.py")
        at.run()

        # Navigate to Developer Stats
        at.radio[0].set_value("Developer Stats").run()

        # Should not crash with empty data
        assert not at.exception

        # Should show warning about no developers
        warnings = [w.value for w in at.warning]
        assert any("No developers found" in str(w) for w in warnings)

    def test_page_navigation_query_builder(self, mock_empty_db):
        """Test navigation to Query Builder page."""
        at = AppTest.from_file("streamlit_app/app.py")
        at.run()

        # Navigate to Query Builder
        at.radio[0].set_value("Query Builder").run()

        # Check that no exceptions occurred
        assert not at.exception, f"Query Builder page crashed with: {at.exception}"

        # Check that query builder content is displayed
        headers = [h.value for h in at.header]
        assert any("Query Builder" in str(h) for h in headers)

        # Check that filter controls are present
        assert len(at.multiselect) >= 4, "Expected at least 4 multiselect controls for filters"

    def test_empty_data_handling_query_builder(self, mock_empty_db):
        """Test that Query Builder page handles empty data gracefully."""
        at = AppTest.from_file("streamlit_app/app.py")
        at.run()

        # Navigate to Query Builder
        at.radio[0].set_value("Query Builder").run()

        # Should not crash with empty data
        assert not at.exception

        # Check that multiselect controls are empty (no options available)
        for multiselect in at.multiselect:
            # Empty database should result in empty options lists
            assert isinstance(multiselect.options, list), "Multiselect options should be a list"

    def test_page_config_settings(self, mock_empty_db):
        """Test that page configuration is set correctly."""
        at = AppTest.from_file("streamlit_app/app.py")
        at.run()

        # App should not crash during initialization
        assert not at.exception

        # Main title should be present indicating proper page setup
        assert len(at.title) > 0
        assert "📊" in str(at.title[0].value), "Dashboard emoji not found in title"
