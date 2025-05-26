"""Unit tests for the AccountController class."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.py_libs.controllers.account_controller import AccountController
from src.py_libs.controllers.sql_db_controller import (
    Account,
    AccountItem,
    Base,
    Hero,
    HeroTrait,
    HeroTraitSet,
    Item,
)

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
def account_controller(engine):
    """Create an AccountController instance with test database."""
    controller = AccountController()
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
def sample_hero_data():
    """Sample hero data for testing."""
    return {"name": "Test Hero", "level": 1}


@pytest.fixture
def sample_item_data():
    """Sample item data for testing."""
    return {"id": 1, "name": "Test Item"}


def test_create_account(account_controller, sample_account_data):
    """Test account creation."""
    account = account_controller.create_account(**sample_account_data)

    assert account is not None
    assert account["name"] == sample_account_data["name"]
    assert account["stories"] == sample_account_data["stories"]
    assert account["status"] == sample_account_data["status"]
    assert account["party_sets"] == sample_account_data["party_sets"]


def test_create_duplicate_account(account_controller, sample_account_data):
    """Test creating account with duplicate name."""
    # Create first account
    account_controller.create_account(**sample_account_data)

    # Try to create duplicate account
    duplicate_account = account_controller.create_account(**sample_account_data)
    assert duplicate_account is None


def test_get_account(account_controller, sample_account_data):
    """Test retrieving account by ID."""
    created_account = account_controller.create_account(**sample_account_data)
    retrieved_account = account_controller.get_account(created_account["id"])

    assert retrieved_account is not None
    assert retrieved_account["id"] == created_account["id"]
    assert retrieved_account["name"] == sample_account_data["name"]


def test_get_account_by_name(account_controller, sample_account_data):
    """Test retrieving account by name."""
    created_account = account_controller.create_account(**sample_account_data)
    retrieved_account = account_controller.get_account_by_name(sample_account_data["name"])

    assert retrieved_account is not None
    assert retrieved_account["id"] == created_account["id"]
    assert retrieved_account["name"] == sample_account_data["name"]


def test_update_account(account_controller, sample_account_data):
    """Test updating account attributes."""
    account = account_controller.create_account(**sample_account_data)

    # Update account
    new_status = "inactive"
    new_stories = [{"story_id": 1, "progress": 100}]
    success = account_controller.update_account(
        account["id"], status=new_status, stories=new_stories
    )

    assert success is True

    # Verify updates
    updated_account = account_controller.get_account(account["id"])
    assert updated_account["status"] == new_status
    assert updated_account["stories"] == new_stories


def test_delete_account(account_controller, sample_account_data):
    """Test account deletion."""
    account = account_controller.create_account(**sample_account_data)

    # Delete account
    success = account_controller.delete_account(account["id"])
    assert success is True

    # Verify deletion
    deleted_account = account_controller.get_account(account["id"])
    assert deleted_account is None


def test_list_accounts(account_controller, sample_account_data):
    """Test listing all accounts."""
    # Create multiple accounts
    account1 = account_controller.create_account(**sample_account_data)
    account2 = account_controller.create_account(name="test_player2", status="active")

    accounts = account_controller.list_accounts()
    assert len(accounts) == 2
    assert any(acc["id"] == account1["id"] for acc in accounts)
    assert any(acc["id"] == account2["id"] for acc in accounts)


def test_get_account_heroes(account_controller, sample_account_data, sample_hero_data):
    """Test retrieving account heroes."""
    # Create account and hero
    with Session(account_controller.engine) as session:
        account = Account(**sample_account_data)
        session.add(account)
        session.commit()
        account_id = account.id  # Save before session closes

        hero = Hero(
            account_id=account_id, name=sample_hero_data["name"], level=sample_hero_data["level"]
        )
        session.add(hero)
        session.commit()  # Commit to get hero.id

        # Add trait set and trait
        trait_set = HeroTraitSet(hero_id=hero.id, slot=0)
        session.add(trait_set)
        session.commit()  # Commit to get trait_set.id

        trait = HeroTrait(trait_set_id=trait_set.id, slot=0, trait_id=1, trait_level=1)
        session.add(trait)
        session.commit()

    # Get heroes
    heroes = account_controller.get_account_heroes(account_id)

    assert len(heroes) == 1
    assert heroes[0]["name"] == sample_hero_data["name"]
    assert heroes[0]["level"] == sample_hero_data["level"]
    assert len(heroes[0]["trait_sets"]) == 1
    assert len(heroes[0]["trait_sets"][0]["traits"]) == 1


def test_get_account_inventory(account_controller, sample_account_data, sample_item_data):
    """Test retrieving account inventory."""
    # Create account and item
    with Session(account_controller.engine) as session:
        account = Account(**sample_account_data)
        session.add(account)
        session.commit()
        account_id = account.id  # Save before session closes

        item = Item(**sample_item_data)
        session.add(item)
        session.commit()

        # Add item to account inventory
        account_item = AccountItem(account_id=account_id, item_id=item.id, amount=5)
        session.add(account_item)
        session.commit()

    # Get inventory
    inventory = account_controller.get_account_inventory(account_id)

    assert len(inventory) == 1
    assert inventory[0]["item_id"] == sample_item_data["id"]
    assert inventory[0]["name"] == sample_item_data["name"]
    assert inventory[0]["amount"] == 5


def test_get_nonexistent_account(account_controller):
    """Test retrieving non-existent account."""
    account = account_controller.get_account(999)
    assert account is None


def test_update_nonexistent_account(account_controller):
    """Test updating non-existent account."""
    success = account_controller.update_account(999, status="active")
    assert success is False


def test_delete_nonexistent_account(account_controller):
    """Test deleting non-existent account."""
    success = account_controller.delete_account(999)
    assert success is False
