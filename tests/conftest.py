"""Test configuration and fixtures for GitHub Stats tests."""

import os
import tempfile
from unittest.mock import patch

import pytest


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
        temp_db_path = temp_file.name

    # Mock the database URL to use our temp database
    with patch("github_stats.utils.config.get_settings") as mock_settings:
        mock_settings.return_value.database_url = f"sqlite:///{temp_db_path}"
        mock_settings.return_value.log_level = "ERROR"

        # Initialize the database
        from github_stats.utils.database import init_db

        init_db()

        yield temp_db_path

    # Cleanup
    if os.path.exists(temp_db_path):
        os.unlink(temp_db_path)


@pytest.fixture
def mock_empty_db():
    """Mock database with no data."""
    with patch("github_stats.utils.database.get_db") as mock_get_db:
        from unittest.mock import MagicMock

        # Create a mock session that returns empty results
        mock_session = MagicMock()
        mock_session.query.return_value.all.return_value = []
        mock_session.query.return_value.count.return_value = 0
        mock_session.query.return_value.scalar.return_value = 0
        # Chain query return values
        query_return = mock_session.query.return_value
        query_return.filter.return_value = query_return
        query_return.group_by.return_value = query_return
        query_return.order_by.return_value = query_return
        query_return.limit.return_value = query_return
        query_return.distinct.return_value = query_return
        mock_session.query.return_value.first.return_value = None

        # Mock the context manager
        mock_get_db.return_value.__enter__.return_value = mock_session
        mock_get_db.return_value.__exit__.return_value = None

        yield mock_session
