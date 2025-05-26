import os

import pytest

from src.py_libs.controllers.sqlite_db_controller import SQLiteDatabaseController


@pytest.fixture
def test_db():
    """Fixture to create a test database and clean it up after tests."""
    db_name = "test_db"
    controller = SQLiteDatabaseController(db_name)
    yield controller
    # Cleanup
    if os.path.exists(f"{db_name}.db"):
        os.remove(f"{db_name}.db")


def test_init_db(test_db):
    """Test database initialization."""
    assert os.path.exists("test_db.db")
    # Verify table exists
    test_db.cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='data_store'"
    )
    assert test_db.cursor.fetchone() is not None


def test_save_and_get_data(test_db):
    """Test saving and retrieving data."""
    test_data = {"key": "value", "nested": {"data": 123}}
    test_path = "test.path"

    # Save data
    result = test_db.save_data(test_data, test_path)
    assert result == 0

    # Get data
    retrieved_data = test_db.get_data(test_path)
    assert retrieved_data == test_data


def test_delete_data(test_db):
    """Test deleting data."""
    test_data = {"key": "value"}
    test_path = "test.path"

    # Save data
    test_db.save_data(test_data, test_path)

    # Delete data
    result = test_db.delete_data(test_path)
    assert result == 0

    # Verify data is deleted
    assert test_db.get_data(test_path) is None


def test_update_data(test_db):
    """Test updating existing data."""
    initial_data = {"key": "old_value"}
    updated_data = {"key": "new_value"}
    test_path = "test.path"

    # Save initial data
    test_db.save_data(initial_data, test_path)

    # Update data
    result = test_db.update_data(updated_data, test_path)
    assert result == 0

    # Verify data is updated
    retrieved_data = test_db.get_data(test_path)
    assert retrieved_data == updated_data


def test_get_target_path():
    """Test path list to string conversion."""
    path_list = ["root", "branch", "leaf"]
    expected_path = "root.branch.leaf"
    assert SQLiteDatabaseController.get_target_path(path_list) == expected_path


def test_nested_data(test_db):
    """Test handling of nested data structures."""
    nested_data = {"level1": {"level2": {"level3": "deep_value"}}}
    test_path = "nested.test"

    # Save nested data
    test_db.save_data(nested_data, test_path)

    # Retrieve and verify
    retrieved_data = test_db.get_data(test_path)
    assert retrieved_data == nested_data
    assert retrieved_data["level1"]["level2"]["level3"] == "deep_value"


def test_multiple_paths(test_db):
    """Test handling multiple different paths."""
    paths = ["path1", "path2", "path3"]
    for i, path in enumerate(paths):
        test_db.save_data({"value": i}, path)

    # Verify all paths
    for i, path in enumerate(paths):
        data = test_db.get_data(path)
        assert data["value"] == i


def test_nonexistent_path(test_db):
    """Test behavior when accessing nonexistent path."""
    assert test_db.get_data("nonexistent.path") is None
