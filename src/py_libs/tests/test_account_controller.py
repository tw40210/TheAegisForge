"""Unit tests for the AccountController class."""

from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.py_libs.controllers.account_controller import (
    AccountController,
    InvalidTokenError,
)
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
def mock_firebase_token():
    """Mock Firebase ID token for testing."""
    return "mock_firebase_token"


@pytest.fixture
def mock_decoded_token():
    """Mock decoded Firebase token data."""
    return {"uid": "firebase_uid_123", "email": "test@example.com", "name": "Test User"}


@pytest.fixture
def sample_hero_data():
    """Sample hero data for testing."""
    return {"name": "Test Hero", "level": 1}


@pytest.fixture
def sample_item_data():
    """Sample item data for testing."""
    return {"id": 1, "name": "Test Item"}


@patch("src.py_libs.controllers.account_controller.auth.verify_id_token")
def test_create_account(
    mock_verify_token,
    account_controller,
    sample_account_data,
    mock_firebase_token,
    mock_decoded_token,
):
    """Test account creation with Firebase ID token."""
    # Mock Firebase token verification
    mock_verify_token.return_value = mock_decoded_token

    account = account_controller.create_account(
        name=sample_account_data["name"],
        id_token=mock_firebase_token,
        stories=sample_account_data["stories"],
        status=sample_account_data["status"],
        party_sets=sample_account_data["party_sets"],
    )

    assert account is not None
    assert account["name"] == sample_account_data["name"]
    assert account["firebaseUID"] == mock_decoded_token["uid"]
    assert account["email"] == mock_decoded_token["email"]
    assert account["user_name"] == mock_decoded_token["name"]
    assert account["stories"] == sample_account_data["stories"]
    assert account["status"] == sample_account_data["status"]
    assert account["party_sets"] == sample_account_data["party_sets"]

    # Verify Firebase token was called
    mock_verify_token.assert_called_once_with(mock_firebase_token)


@patch("src.py_libs.controllers.account_controller.auth.verify_id_token")
def test_create_account_invalid_token(
    mock_verify_token, account_controller, sample_account_data, mock_firebase_token
):
    """Test account creation with invalid Firebase ID token."""
    # Mock Firebase token verification to raise exception
    mock_verify_token.side_effect = Exception("Invalid token")

    with pytest.raises(InvalidTokenError):
        account_controller.create_account(
            name=sample_account_data["name"], id_token=mock_firebase_token
        )


@patch("src.py_libs.controllers.account_controller.auth.verify_id_token")
def test_create_account_missing_optional_fields(
    mock_verify_token, account_controller, sample_account_data, mock_firebase_token
):
    """Test account creation when optional fields are missing from token."""
    # Mock Firebase token without email and name
    mock_decoded_token = {
        "uid": "firebase_uid_123"
        # email and name are missing
    }
    mock_verify_token.return_value = mock_decoded_token

    account = account_controller.create_account(
        name=sample_account_data["name"], id_token=mock_firebase_token
    )

    assert account is not None
    assert account["firebaseUID"] == mock_decoded_token["uid"]
    assert account["email"] is None
    assert account["user_name"] is None


@patch("src.py_libs.controllers.account_controller.auth.verify_id_token")
def test_create_duplicate_account(
    mock_verify_token,
    account_controller,
    sample_account_data,
    mock_firebase_token,
    mock_decoded_token,
):
    """Test creating account with duplicate name."""
    # Mock Firebase token verification
    mock_verify_token.return_value = mock_decoded_token

    # Create first account
    account_controller.create_account(
        name=sample_account_data["name"], id_token=mock_firebase_token
    )

    # Try to create duplicate account
    duplicate_account = account_controller.create_account(
        name=sample_account_data["name"], id_token=mock_firebase_token
    )
    assert duplicate_account is None


@patch("src.py_libs.controllers.account_controller.auth.verify_id_token")
def test_get_account(
    mock_verify_token,
    account_controller,
    sample_account_data,
    mock_firebase_token,
    mock_decoded_token,
):
    """Test retrieving account by ID."""
    # Mock Firebase token verification
    mock_verify_token.return_value = mock_decoded_token

    created_account = account_controller.create_account(
        name=sample_account_data["name"], id_token=mock_firebase_token
    )
    retrieved_account = account_controller.get_account(created_account["id"])

    assert retrieved_account is not None
    assert retrieved_account["id"] == created_account["id"]
    assert retrieved_account["name"] == sample_account_data["name"]
    assert retrieved_account["firebaseUID"] == mock_decoded_token["uid"]
    assert retrieved_account["email"] == mock_decoded_token["email"]
    assert retrieved_account["user_name"] == mock_decoded_token["name"]


@patch("src.py_libs.controllers.account_controller.auth.verify_id_token")
def test_get_account_by_name(
    mock_verify_token,
    account_controller,
    sample_account_data,
    mock_firebase_token,
    mock_decoded_token,
):
    """Test retrieving account by name."""
    # Mock Firebase token verification
    mock_verify_token.return_value = mock_decoded_token

    created_account = account_controller.create_account(
        name=sample_account_data["name"], id_token=mock_firebase_token
    )
    retrieved_account = account_controller.get_account_by_name(sample_account_data["name"])

    assert retrieved_account is not None
    assert retrieved_account["id"] == created_account["id"]
    assert retrieved_account["name"] == sample_account_data["name"]
    assert retrieved_account["firebaseUID"] == mock_decoded_token["uid"]
    assert retrieved_account["email"] == mock_decoded_token["email"]
    assert retrieved_account["user_name"] == mock_decoded_token["name"]


@patch("src.py_libs.controllers.account_controller.auth.verify_id_token")
def test_update_account(
    mock_verify_token,
    account_controller,
    sample_account_data,
    mock_firebase_token,
    mock_decoded_token,
):
    """Test updating account attributes."""
    # Mock Firebase token verification
    mock_verify_token.return_value = mock_decoded_token

    account = account_controller.create_account(
        name=sample_account_data["name"], id_token=mock_firebase_token
    )

    # Update account
    new_status = "inactive"
    new_stories = [{"story_id": 1, "progress": 100}]
    new_user_name = "Updated User"
    success = account_controller.update_account(
        account["id"], status=new_status, stories=new_stories, user_name=new_user_name
    )

    assert success is True

    # Verify updates
    updated_account = account_controller.get_account(account["id"])
    assert updated_account["status"] == new_status
    assert updated_account["stories"] == new_stories
    assert updated_account["user_name"] == new_user_name
    # Original Firebase fields should remain unchanged
    assert updated_account["firebaseUID"] == mock_decoded_token["uid"]
    assert updated_account["email"] == mock_decoded_token["email"]


@patch("src.py_libs.controllers.account_controller.auth.verify_id_token")
def test_delete_account(
    mock_verify_token,
    account_controller,
    sample_account_data,
    mock_firebase_token,
    mock_decoded_token,
):
    """Test account deletion."""
    # Mock Firebase token verification
    mock_verify_token.return_value = mock_decoded_token

    account = account_controller.create_account(
        name=sample_account_data["name"], id_token=mock_firebase_token
    )

    # Delete account
    success = account_controller.delete_account(account["id"])
    assert success is True

    # Verify deletion
    deleted_account = account_controller.get_account(account["id"])
    assert deleted_account is None


@patch("src.py_libs.controllers.account_controller.auth.verify_id_token")
def test_list_accounts(
    mock_verify_token,
    account_controller,
    sample_account_data,
    mock_firebase_token,
    mock_decoded_token,
):
    """Test listing all accounts."""
    # Mock Firebase token verification
    mock_verify_token.return_value = mock_decoded_token

    # Create multiple accounts
    account1 = account_controller.create_account(
        name=sample_account_data["name"], id_token=mock_firebase_token
    )

    # Create second account with different mock data
    mock_decoded_token2 = {
        "uid": "firebase_uid_456",
        "email": "test2@example.com",
        "name": "Test User 2",
    }
    mock_verify_token.return_value = mock_decoded_token2

    account2 = account_controller.create_account(
        name="test_player2", id_token=mock_firebase_token, status="active"
    )

    accounts = account_controller.list_accounts()
    assert len(accounts) == 2

    # Check that both accounts are returned with Firebase fields
    account_ids = [acc["id"] for acc in accounts]
    assert account1["id"] in account_ids
    assert account2["id"] in account_ids

    # Check Firebase fields are present
    for account in accounts:
        assert "firebaseUID" in account
        assert "email" in account
        assert "user_name" in account


@patch("src.py_libs.controllers.account_controller.auth.verify_id_token")
def test_get_account_heroes(
    mock_verify_token,
    account_controller,
    sample_account_data,
    sample_hero_data,
    mock_firebase_token,
    mock_decoded_token,
):
    """Test retrieving account heroes."""
    # Mock Firebase token verification
    mock_verify_token.return_value = mock_decoded_token

    # Create account and hero
    with Session(account_controller.engine) as session:
        account = Account(
            name=sample_account_data["name"],
            firebaseUID=mock_decoded_token["uid"],
            email=mock_decoded_token["email"],
            user_name=mock_decoded_token["name"],
            stories=sample_account_data["stories"],
            status=sample_account_data["status"],
            party_sets=sample_account_data["party_sets"],
        )
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


@patch("src.py_libs.controllers.account_controller.auth.verify_id_token")
def test_get_account_inventory(
    mock_verify_token,
    account_controller,
    sample_account_data,
    sample_item_data,
    mock_firebase_token,
    mock_decoded_token,
):
    """Test retrieving account inventory."""
    # Mock Firebase token verification
    mock_verify_token.return_value = mock_decoded_token

    # Create account and item
    with Session(account_controller.engine) as session:
        account = Account(
            name=sample_account_data["name"],
            firebaseUID=mock_decoded_token["uid"],
            email=mock_decoded_token["email"],
            user_name=mock_decoded_token["name"],
            stories=sample_account_data["stories"],
            status=sample_account_data["status"],
            party_sets=sample_account_data["party_sets"],
        )
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


@patch("src.py_libs.controllers.account_controller.auth.verify_id_token")
def test_get_account_by_firebase_uid(
    mock_verify_token,
    account_controller,
    sample_account_data,
    mock_firebase_token,
    mock_decoded_token,
):
    """Test retrieving account by Firebase UID."""
    # Mock Firebase token verification
    mock_verify_token.return_value = mock_decoded_token

    # Create account
    created_account = account_controller.create_account(
        name=sample_account_data["name"], id_token=mock_firebase_token
    )

    # Retrieve by Firebase UID
    retrieved_account = account_controller.get_account_by_firebase_uid(mock_decoded_token["uid"])

    assert retrieved_account is not None
    assert retrieved_account["id"] == created_account["id"]
    assert retrieved_account["firebaseUID"] == mock_decoded_token["uid"]
    assert retrieved_account["email"] == mock_decoded_token["email"]
    assert retrieved_account["user_name"] == mock_decoded_token["name"]


@patch("src.py_libs.controllers.account_controller.auth.verify_id_token")
def test_create_account_duplicate_firebase_uid(
    mock_verify_token,
    account_controller,
    sample_account_data,
    mock_firebase_token,
    mock_decoded_token,
):
    """Test creating account with duplicate Firebase UID."""
    # Mock Firebase token verification
    mock_verify_token.return_value = mock_decoded_token

    # Create first account
    account1 = account_controller.create_account(name="test_player1", id_token=mock_firebase_token)
    assert account1 is not None

    # Try to create second account with same Firebase UID but different name
    duplicate_account = account_controller.create_account(
        name="test_player2", id_token=mock_firebase_token
    )
    # Should fail due to unique constraint on firebaseUID
    assert duplicate_account is None


def test_get_account_by_firebase_uid_not_found(account_controller):
    """Test retrieving account by non-existent Firebase UID."""
    retrieved_account = account_controller.get_account_by_firebase_uid("non_existent_uid")
    assert retrieved_account is None
