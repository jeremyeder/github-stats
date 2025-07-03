"""Tests for database utility functions."""

from github_stats.utils.database import check_db_has_data


def test_check_db_has_data_returns_counts():
    """Test that check_db_has_data returns count dictionary."""
    counts = check_db_has_data()

    # Should return a dictionary with the expected keys
    assert isinstance(counts, dict)
    assert "organizations" in counts
    assert "repositories" in counts
    assert "interactions" in counts

    # All counts should be non-negative integers
    for count in counts.values():
        assert isinstance(count, int)
        assert count >= 0


def test_check_db_has_data_handles_missing_database():
    """Test that check_db_has_data handles missing database gracefully."""
    # This test ensures the function doesn't crash with missing database
    counts = check_db_has_data()

    # Should return zero counts for missing database
    assert isinstance(counts, dict)
    assert all(isinstance(count, int) for count in counts.values())
