"""Unit tests for the ItemController class."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.py_libs.controllers.item_controller import ItemController
from src.py_libs.controllers.sql_db_controller import Account, AccountItem, Base, Item

# Test database URL
TEST_DB_URL = "sqlite:///:memory:"


@pytest.fixture
def engine():
    """Create a test database engine."""
    engine = create_engine(TEST_DB_URL)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def item_controller(engine):
    """Create an ItemController instance with test database."""
    controller = ItemController()
    controller.engine = engine
    return controller


@pytest.fixture
def sample_account_data():
    """Sample account data for testing."""
    return {
        "name": "test_player",
        "stories": [{"story_id": 1, "progress": 50}],
        "status": "active",
        "party_sets": [{"party_id": 1, "name": "Main Party"}],
    }


@pytest.fixture
def sample_item_data():
    """Sample item data for testing."""
    return {"id": 1, "name": "Test Item"}


@pytest.fixture
def sample_item_data_2():
    """Second sample item data for testing."""
    return {"id": 2, "name": "Another Item"}


@pytest.fixture
def setup_account_and_item(item_controller, sample_account_data, sample_item_data):
    """Create a test account and item for testing."""
    with Session(item_controller.engine) as session:
        account = Account(**sample_account_data)
        session.add(account)
        session.commit()

        item = Item(**sample_item_data)
        session.add(item)
        session.commit()

        return {"account_id": account.id, "item_id": item.id}


def test_send_item_to_account_new_item(item_controller, setup_account_and_item):
    """Test sending items to an account that doesn't have the item yet."""
    data = setup_account_and_item
    result = item_controller.send_item_to_account(data["item_id"], 5, data["account_id"])

    assert result is not None
    assert result["success"] is True
    assert result["amount_added"] == 5
    assert result["total_amount"] == 5
    assert result["account_id"] == data["account_id"]
    assert result["item_id"] == data["item_id"]
    assert "Test Item" in result["message"]


def test_send_item_to_account_existing_item(item_controller, setup_account_and_item):
    """Test sending items to an account that already has the item."""
    data = setup_account_and_item

    # First, add some items to the account
    with Session(item_controller.engine) as session:
        account_item = AccountItem(account_id=data["account_id"], item_id=data["item_id"], amount=3)
        session.add(account_item)
        session.commit()

    # Now send more items
    result = item_controller.send_item_to_account(data["item_id"], 5, data["account_id"])

    assert result is not None
    assert result["success"] is True
    assert result["amount_added"] == 5
    assert result["total_amount"] == 8  # 3 + 5
    assert result["account_id"] == data["account_id"]
    assert result["item_id"] == data["item_id"]


def test_send_item_to_nonexistent_account(item_controller, sample_item_data):
    """Test sending items to a non-existent account."""
    with Session(item_controller.engine) as session:
        item = Item(**sample_item_data)
        session.add(item)
        session.commit()
        item_id = item.id

    result = item_controller.send_item_to_account(item_id, 5, 99999)

    assert result is not None
    assert result["success"] is False
    assert "Account 99999 does not exist" in result["message"]
    assert result["amount_added"] == 0
    assert result["total_amount"] == 0


def test_send_nonexistent_item_to_account(item_controller, sample_account_data):
    """Test sending a non-existent item to an account."""
    with Session(item_controller.engine) as session:
        account = Account(**sample_account_data)
        session.add(account)
        session.commit()
        account_id = account.id

    result = item_controller.send_item_to_account(99999, 5, account_id)

    assert result is not None
    assert result["success"] is False
    assert "Item 99999 does not exist" in result["message"]
    assert result["amount_added"] == 0
    assert result["total_amount"] == 0


def test_send_zero_items(item_controller, setup_account_and_item):
    """Test sending zero items to an account."""
    data = setup_account_and_item
    result = item_controller.send_item_to_account(data["item_id"], 0, data["account_id"])

    assert result is not None
    assert result["success"] is False
    assert "Invalid number of items to send: 0" in result["message"]
    assert result["amount_added"] == 0


def test_send_negative_items(item_controller, setup_account_and_item):
    """Test sending negative number of items to an account."""
    data = setup_account_and_item
    result = item_controller.send_item_to_account(data["item_id"], -5, data["account_id"])

    assert result is not None
    assert result["success"] is False
    assert "Invalid number of items to send: -5" in result["message"]
    assert result["amount_added"] == 0


def test_get_item(item_controller, sample_item_data):
    """Test retrieving an item by ID."""
    with Session(item_controller.engine) as session:
        item = Item(**sample_item_data)
        session.add(item)
        session.commit()
        item_id = item.id

    result = item_controller.get_item(item_id)

    assert result is not None
    assert result["success"] is True
    assert result["id"] == item_id
    assert result["name"] == sample_item_data["name"]


def test_get_nonexistent_item(item_controller):
    """Test retrieving a non-existent item."""
    result = item_controller.get_item(99999)
    assert result is not None
    assert result["success"] is False
    assert "Item 99999 does not exist" in result["message"]
    assert result["id"] == 99999
    assert result["name"] is None


def test_get_account_item_amount_existing(item_controller, setup_account_and_item):
    """Test getting the amount of an item an account has."""
    data = setup_account_and_item

    # Add some items to the account
    with Session(item_controller.engine) as session:
        account_item = AccountItem(account_id=data["account_id"], item_id=data["item_id"], amount=7)
        session.add(account_item)
        session.commit()

    amount = item_controller.get_account_item_amount(data["account_id"], data["item_id"])
    assert amount == 7


def test_get_account_item_amount_nonexistent(item_controller, setup_account_and_item):
    """Test getting the amount of an item an account doesn't have."""
    data = setup_account_and_item
    amount = item_controller.get_account_item_amount(data["account_id"], data["item_id"])
    assert amount == 0


def test_remove_item_from_account_partial(item_controller, setup_account_and_item):
    """Test removing some items from an account (partial removal)."""
    data = setup_account_and_item

    # Add items to the account first
    with Session(item_controller.engine) as session:
        account_item = AccountItem(
            account_id=data["account_id"], item_id=data["item_id"], amount=10
        )
        session.add(account_item)
        session.commit()

    # Remove some items
    result = item_controller.remove_item_from_account(data["item_id"], 3, data["account_id"])

    assert result is not None
    assert result["success"] is True
    assert result["amount_removed"] == 3
    assert result["total_amount"] == 7  # 10 - 3
    assert "Removed 3 Test Item(s)" in result["message"]


def test_remove_item_from_account_complete(item_controller, setup_account_and_item):
    """Test removing all items from an account (complete removal)."""
    data = setup_account_and_item

    # Add items to the account first
    with Session(item_controller.engine) as session:
        account_item = AccountItem(account_id=data["account_id"], item_id=data["item_id"], amount=5)
        session.add(account_item)
        session.commit()

    # Remove all items
    result = item_controller.remove_item_from_account(data["item_id"], 5, data["account_id"])

    assert result is not None
    assert result["success"] is True
    assert result["amount_removed"] == 5
    assert result["total_amount"] == 0
    assert "Removed 5 Test Item(s)" in result["message"]

    # Verify the item was completely removed from inventory
    amount = item_controller.get_account_item_amount(data["account_id"], data["item_id"])
    assert amount == 0


def test_remove_item_insufficient_amount(item_controller, setup_account_and_item):
    """Test removing more items than the account has."""
    data = setup_account_and_item

    # Add fewer items than we'll try to remove
    with Session(item_controller.engine) as session:
        account_item = AccountItem(account_id=data["account_id"], item_id=data["item_id"], amount=3)
        session.add(account_item)
        session.commit()

    # Try to remove more items than available
    result = item_controller.remove_item_from_account(data["item_id"], 5, data["account_id"])

    assert result is not None
    assert result["success"] is False
    assert "Not enough Test Item(s) to remove" in result["message"]
    assert result["amount_removed"] == 0
    assert result["total_amount"] == 3


def test_remove_item_from_empty_inventory(item_controller, setup_account_and_item):
    """Test removing items from an account that doesn't have the item."""
    data = setup_account_and_item

    # Try to remove items from empty inventory
    result = item_controller.remove_item_from_account(data["item_id"], 5, data["account_id"])

    assert result is not None
    assert result["success"] is False
    assert "does not have any Test Item(s) to remove" in result["message"]
    assert result["amount_removed"] == 0
    assert result["total_amount"] == 0


def test_remove_zero_items(item_controller, setup_account_and_item):
    """Test removing zero items from an account."""
    data = setup_account_and_item
    result = item_controller.remove_item_from_account(data["item_id"], 0, data["account_id"])
    assert result is not None
    assert result["success"] is False
    assert "Invalid number of items to remove: 0" in result["message"]


def test_remove_negative_items(item_controller, setup_account_and_item):
    """Test removing negative number of items from an account."""
    data = setup_account_and_item
    result = item_controller.remove_item_from_account(data["item_id"], -3, data["account_id"])
    assert result is not None
    assert result["success"] is False
    assert "Invalid number of items to remove: -3" in result["message"]


def test_remove_from_nonexistent_account(item_controller, sample_item_data):
    """Test removing items from a non-existent account."""
    with Session(item_controller.engine) as session:
        item = Item(**sample_item_data)
        session.add(item)
        session.commit()
        item_id = item.id

    result = item_controller.remove_item_from_account(item_id, 5, 99999)
    assert result is not None
    assert result["success"] is False
    assert "Account 99999 does not exist" in result["message"]


def test_remove_nonexistent_item(item_controller, sample_account_data):
    """Test removing a non-existent item from an account."""
    with Session(item_controller.engine) as session:
        account = Account(**sample_account_data)
        session.add(account)
        session.commit()
        account_id = account.id

    result = item_controller.remove_item_from_account(99999, 5, account_id)
    assert result is not None
    assert result["success"] is False
    assert "Item 99999 does not exist" in result["message"]


def test_list_items_empty(item_controller):
    """Test listing items when no items exist."""
    items = item_controller.list_items()
    assert items == []


def test_list_items_with_data(item_controller, sample_item_data, sample_item_data_2):
    """Test listing items when items exist."""
    with Session(item_controller.engine) as session:
        item1 = Item(**sample_item_data)
        item2 = Item(**sample_item_data_2)
        session.add_all([item1, item2])
        session.commit()

    items = item_controller.list_items()

    assert len(items) == 2
    assert any(item["name"] == "Test Item" for item in items)
    assert any(item["name"] == "Another Item" for item in items)
    assert any(item["id"] == 1 for item in items)
    assert any(item["id"] == 2 for item in items)


def test_send_and_remove_item_integration(item_controller, setup_account_and_item):
    """Integration test: send items and then remove them."""
    data = setup_account_and_item

    # Send items
    send_result = item_controller.send_item_to_account(data["item_id"], 10, data["account_id"])
    assert send_result["success"] is True
    assert send_result["total_amount"] == 10

    # Verify amount
    amount = item_controller.get_account_item_amount(data["account_id"], data["item_id"])
    assert amount == 10

    # Remove some items
    remove_result = item_controller.remove_item_from_account(data["item_id"], 3, data["account_id"])
    assert remove_result["success"] is True
    assert remove_result["total_amount"] == 7

    # Verify final amount
    final_amount = item_controller.get_account_item_amount(data["account_id"], data["item_id"])
    assert final_amount == 7


def test_multiple_accounts_same_item(item_controller, sample_item_data):
    """Test sending the same item to multiple accounts."""
    # Create multiple accounts
    with Session(item_controller.engine) as session:
        account1 = Account(name="player1", stories=[], status="active", party_sets=[])
        account2 = Account(name="player2", stories=[], status="active", party_sets=[])
        item = Item(**sample_item_data)
        session.add_all([account1, account2, item])
        session.commit()

        account1_id = account1.id
        account2_id = account2.id
        item_id = item.id

    # Send items to both accounts
    result1 = item_controller.send_item_to_account(item_id, 5, account1_id)
    result2 = item_controller.send_item_to_account(item_id, 3, account2_id)

    assert result1["success"] is True
    assert result1["total_amount"] == 5
    assert result2["success"] is True
    assert result2["total_amount"] == 3

    # Verify both accounts have their respective amounts
    amount1 = item_controller.get_account_item_amount(account1_id, item_id)
    amount2 = item_controller.get_account_item_amount(account2_id, item_id)
    assert amount1 == 5
    assert amount2 == 3
