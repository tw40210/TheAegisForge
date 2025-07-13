"""Unit tests for the GachaController class."""

import os
import tempfile
from unittest.mock import Mock, patch

import pytest
import yaml
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.py_libs.controllers.gacha_controller import GachaController
from src.py_libs.controllers.sql_db_controller import (
    Account,
    AccountItem,
    Base,
    Hero,
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
def sample_gacha_pools():
    """Sample gacha pool configuration for testing."""
    return {
        "gacha_pools": {
            "test_pool": {
                "name": "Test Pool",
                "description": "A test gacha pool",
                "requiring_item_id": 1,
                "num_requiring_item": 1,
                "heroes": [
                    {"hero_id": 1, "probability": 0.6},
                    {"hero_id": 2, "probability": 0.3},
                    {"hero_id": 3, "probability": 0.1},
                ],
            },
            "premium_test_pool": {
                "name": "Premium Test Pool",
                "description": "A premium test gacha pool",
                "requiring_item_id": 2,
                "num_requiring_item": 1,
                "heroes": [
                    {"hero_id": 4, "probability": 0.5},
                    {"hero_id": 5, "probability": 0.3},
                    {"hero_id": 6, "probability": 0.2},
                ],
            },
            "ten_pull_pool": {
                "name": "Ten Pull Pool",
                "description": "Ten pull test pool",
                "requiring_item_id": 2,
                "num_requiring_item": 10,
                "heroes": [
                    {"hero_id": 7, "probability": 0.7},
                    {"hero_id": 8, "probability": 0.3},
                ],
            },
            "empty_pool": {
                "name": "Empty Pool",
                "description": "Pool with no heroes",
                "requiring_item_id": 3,
                "num_requiring_item": 1,
                "heroes": [],
            },
        }
    }


@pytest.fixture
def sample_heroes_config():
    """Sample heroes configuration for testing."""
    return {
        "heroes": {
            1: {"name": "Common Hero"},
            2: {"name": "Rare Hero"},
            3: {"name": "Legendary Hero"},
            4: {"name": "Epic Hero"},
            5: {"name": "Mythic Hero"},
            6: {"name": "Divine Hero"},
            7: {"name": "Guaranteed Rare"},
            8: {"name": "Guaranteed Epic"},
        }
    }


@pytest.fixture
def temp_config_file(sample_gacha_pools):
    """Create a temporary YAML config file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(sample_gacha_pools, f)
        temp_file = f.name

    yield temp_file

    # Cleanup
    if os.path.exists(temp_file):
        os.unlink(temp_file)


@pytest.fixture
def gacha_controller(engine, temp_config_file, sample_heroes_config):
    """Create a GachaController instance with test database and config."""
    with patch("src.py_libs.controllers.gacha_controller.Path") as mock_path:
        # Mock the config file path to use our temporary file
        mock_path.return_value.parent.parent.parent = Mock()
        mock_path.return_value.parent.parent.parent.__truediv__ = Mock()
        mock_path.return_value.parent.parent.parent.__truediv__.return_value.__truediv__ = Mock()
        mock_path.return_value.parent.parent.parent.__truediv__.return_value.__truediv__.return_value = (
            temp_config_file
        )

        controller = GachaController()
        # Set the test engine BEFORE loading pools to ensure consistency
        controller.engine = engine
        controller._ensure_engine_consistency()

        # Manually set the pools and heroes config since Path mocking might not work perfectly
        with open(temp_config_file) as f:
            config = yaml.safe_load(f)
            controller.gacha_pools = config.get("gacha_pools", {})

        # Set the heroes config
        controller.heroes_config = sample_heroes_config["heroes"]

        return controller


@pytest.fixture
def sample_account_data():
    """Sample account data for testing."""
    return {"name": "test_player", "stories": [], "status": "active", "party_sets": []}


@pytest.fixture
def sample_items_data():
    """Sample items data for testing."""
    return [
        {"id": 1, "name": "Basic Ticket"},
        {"id": 2, "name": "Premium Ticket"},
        {"id": 3, "name": "Special Ticket"},
    ]


@pytest.fixture
def setup_test_data(gacha_controller, sample_account_data, sample_items_data):
    """Set up test account and items."""
    with Session(gacha_controller.engine) as session:
        # Create account
        account = Account(**sample_account_data)
        session.add(account)
        session.commit()
        account_id = account.id

        # Create items
        for item_data in sample_items_data:
            item = Item(**item_data)
            session.add(item)
        session.commit()

        # Give account some items
        for item_data in sample_items_data:
            account_item = AccountItem(account_id=account_id, item_id=item_data["id"], amount=10)
            session.add(account_item)
        session.commit()

        return {"account_id": account_id}


class TestGachaController:
    """Test cases for GachaController."""

    def test_initialization(self, gacha_controller):
        """Test that gacha controller initializes correctly."""
        assert gacha_controller.gacha_pools is not None
        assert "test_pool" in gacha_controller.gacha_pools
        assert "premium_test_pool" in gacha_controller.gacha_pools

    def test_load_gacha_pools_file_not_found(self, engine):
        """Test gacha pool loading when config file doesn't exist."""
        with patch("src.py_libs.controllers.gacha_controller.Path") as mock_path:
            mock_path.return_value.parent.parent.parent.__truediv__.return_value.__truediv__.return_value = (
                "/nonexistent/path.yaml"
            )
            controller = GachaController()
            controller.engine = engine
            assert controller.gacha_pools == {}

    def test_get_available_pools(self, gacha_controller):
        """Test getting list of available gacha pools."""
        pools = gacha_controller.get_available_pools()

        assert len(pools) == 4
        pool_ids = [pool["pool_id"] for pool in pools]
        assert "test_pool" in pool_ids
        assert "premium_test_pool" in pool_ids
        assert "ten_pull_pool" in pool_ids
        assert "empty_pool" in pool_ids

        # Check structure of first pool
        test_pool = next(pool for pool in pools if pool["pool_id"] == "test_pool")
        assert test_pool["name"] == "Test Pool"
        assert test_pool["requiring_item_id"] == 1
        assert test_pool["num_requiring_item"] == 1
        assert (
            "Common Hero" in test_pool["heroes"]
        )  # This should now work with hero names from config

    def test_get_gacha_pool_info_existing(self, gacha_controller):
        """Test getting info for an existing gacha pool."""
        result = gacha_controller.get_gacha_pool_info("test_pool")

        assert result["success"] is True
        assert result["pool_info"]["pool_id"] == "test_pool"
        assert result["pool_info"]["name"] == "Test Pool"
        assert len(result["pool_info"]["heroes"]) == 3

        # Verify the first hero has full information
        first_hero = result["pool_info"]["heroes"][0]
        assert first_hero["hero_id"] == 1
        assert first_hero["name"] == "Common Hero"
        assert first_hero["probability"] == 0.6
        assert "description" in first_hero
        assert "rarity" in first_hero
        assert "element" in first_hero
        assert "class" in first_hero
        assert "stats" in first_hero
        assert "skills" in first_hero

    def test_get_gacha_pool_info_nonexistent(self, gacha_controller):
        """Test getting info for a non-existent gacha pool."""
        result = gacha_controller.get_gacha_pool_info("nonexistent_pool")

        assert result["success"] is False
        assert "does not exist" in result["message"]
        assert result["pool_info"] is None

    def test_get_hero_info_by_id_existing(self, gacha_controller):
        """Test getting hero info for an existing hero."""
        hero_info = gacha_controller._get_hero_info_by_id(1)

        assert hero_info["hero_id"] == 1
        assert hero_info["name"] == "Common Hero"
        assert "description" in hero_info
        assert "rarity" in hero_info
        assert "element" in hero_info
        assert "class" in hero_info
        assert "stats" in hero_info
        assert "skills" in hero_info

    def test_get_hero_info_by_id_nonexistent(self, gacha_controller):
        """Test getting hero info for a non-existent hero."""
        hero_info = gacha_controller._get_hero_info_by_id(999)

        assert hero_info["hero_id"] == 999
        assert hero_info["name"] == "Hero 999"
        assert hero_info["description"] == ""
        assert hero_info["rarity"] == "unknown"
        assert hero_info["element"] == "unknown"
        assert hero_info["class"] == "unknown"
        assert hero_info["stats"] == {}
        assert hero_info["skills"] == []

    def test_gacha_success(self, gacha_controller, setup_test_data):
        """Test successful gacha pull."""
        data = setup_test_data

        # Mock random to ensure we get the first hero
        with patch("src.py_libs.controllers.gacha_controller.random.random", return_value=0.1):
            result = gacha_controller.gacha(data["account_id"], "test_pool")

        assert result["success"] is True
        assert result["hero_name"] == "Common Hero"  # Now comes from heroes config
        assert result["hero_obtained"]["name"] == "Common Hero"
        assert result["hero_obtained"]["probability"] == 0.6
        assert result["hero_obtained"]["hero_id"] == 1
        assert result["items_consumed"]["item_id"] == 1
        assert result["items_consumed"]["amount_consumed"] == 1

    def test_gacha_nonexistent_account(self, gacha_controller):
        """Test gacha with non-existent account."""
        result = gacha_controller.gacha(99999, "test_pool")

        assert result["success"] is False
        assert "Account 99999 does not exist" in result["message"]
        assert result["hero_obtained"] is None

    def test_gacha_nonexistent_pool(self, gacha_controller, setup_test_data):
        """Test gacha with non-existent pool."""
        data = setup_test_data
        result = gacha_controller.gacha(data["account_id"], "nonexistent_pool")

        assert result["success"] is False
        assert "does not exist" in result["message"]
        assert result["hero_obtained"] is None

    def test_gacha_insufficient_items(self, gacha_controller, setup_test_data):
        """Test gacha when account doesn't have enough items."""
        data = setup_test_data

        # Remove all items from account
        with Session(gacha_controller.engine) as session:
            session.query(AccountItem).filter_by(account_id=data["account_id"]).delete()
            session.commit()

        result = gacha_controller.gacha(data["account_id"], "test_pool")

        assert result["success"] is False
        assert "Insufficient" in result["message"]
        assert result["hero_obtained"] is None

    def test_gacha_empty_pool(self, gacha_controller, setup_test_data):
        """Test gacha with empty hero pool."""
        data = setup_test_data
        result = gacha_controller.gacha(data["account_id"], "empty_pool")

        assert result["success"] is False
        assert "no heroes configured" in result["message"]
        assert result["hero_obtained"] is None

    def test_select_random_hero_probability_distribution(self, gacha_controller):
        """Test hero selection probability distribution."""
        heroes = [
            {"hero_id": 1, "probability": 0.8},
            {"hero_id": 2, "probability": 0.2},
        ]

        # Test with different random values
        with patch("src.py_libs.controllers.gacha_controller.random.random", return_value=0.5):
            selected = gacha_controller._select_random_hero(heroes)
            assert selected["hero_id"] == 1

        with patch("src.py_libs.controllers.gacha_controller.random.random", return_value=0.9):
            selected = gacha_controller._select_random_hero(heroes)
            assert selected["hero_id"] == 2

    def test_select_random_hero_empty_list(self, gacha_controller):
        """Test hero selection with empty list."""
        result = gacha_controller._select_random_hero([])
        assert result is None

    def test_select_random_hero_zero_probability(self, gacha_controller):
        """Test hero selection with zero total probability."""
        heroes = [
            {"hero_id": 1, "probability": 0},
            {"hero_id": 2, "probability": 0},
        ]
        result = gacha_controller._select_random_hero(heroes)
        assert result is None

    def test_add_hero_to_account_success(self, gacha_controller, setup_test_data):
        """Test successfully adding hero to account."""
        data = setup_test_data
        result = gacha_controller._add_hero_to_account(data["account_id"], "Test Hero")

        assert result["success"] is True
        assert result["hero_id"] is not None

        # Verify hero was added to database
        with Session(gacha_controller.engine) as session:
            hero = session.get(Hero, result["hero_id"])
            assert hero is not None
            assert hero.name == "Test Hero"
            assert hero.level == 1
            assert hero.account_id == data["account_id"]

    def test_multi_gacha_success(self, gacha_controller, setup_test_data):
        """Test successful multi-gacha pull."""
        data = setup_test_data
        num_pulls = 3

        # Mock random to ensure consistent results
        with patch("src.py_libs.controllers.gacha_controller.random.random", return_value=0.1):
            result = gacha_controller.multi_gacha(data["account_id"], "test_pool", num_pulls)

        assert result["success"] is True
        assert result["num_pulls"] == num_pulls
        assert len(result["heroes_obtained"]) == num_pulls
        assert all(hero["name"] == "Common Hero" for hero in result["heroes_obtained"])
        assert result["items_consumed"][1]["amount_consumed"] == num_pulls

    def test_multi_gacha_zero_pulls(self, gacha_controller, setup_test_data):
        """Test multi-gacha with zero pulls."""
        data = setup_test_data
        result = gacha_controller.multi_gacha(data["account_id"], "test_pool", 0)

        assert result["success"] is False
        assert "greater than 0" in result["message"]
        assert result["num_pulls"] == 0
        assert len(result["heroes_obtained"]) == 0

    def test_multi_gacha_insufficient_items(self, gacha_controller, setup_test_data):
        """Test multi-gacha when account runs out of items."""
        data = setup_test_data

        # Set account to have only 2 items
        with Session(gacha_controller.engine) as session:
            account_item = (
                session.query(AccountItem)
                .filter_by(account_id=data["account_id"], item_id=1)
                .first()
            )
            account_item.amount = 2
            session.commit()

        result = gacha_controller.multi_gacha(data["account_id"], "test_pool", 5)

        assert result["success"] is False
        assert len(result["heroes_obtained"]) == 2  # Should have succeeded twice
        assert "Insufficient" in result["message"]

    def test_gacha_ten_pull_requirement(self, gacha_controller, setup_test_data):
        """Test gacha pool with higher item requirement."""
        data = setup_test_data

        # Mock random for consistent results
        with patch("src.py_libs.controllers.gacha_controller.random.random", return_value=0.1):
            result = gacha_controller.gacha(data["account_id"], "ten_pull_pool")

        assert result["success"] is True
        assert result["hero_name"] == "Guaranteed Rare"  # Now comes from heroes config
        assert result["hero_obtained"]["name"] == "Guaranteed Rare"
        assert result["items_consumed"]["amount_consumed"] == 10

    def test_gacha_ten_pull_insufficient_items(self, gacha_controller, setup_test_data):
        """Test ten-pull gacha when account has insufficient items."""
        data = setup_test_data

        # Set account to have only 5 premium tickets
        with Session(gacha_controller.engine) as session:
            account_item = (
                session.query(AccountItem)
                .filter_by(account_id=data["account_id"], item_id=2)
                .first()
            )
            account_item.amount = 5
            session.commit()

        result = gacha_controller.gacha(data["account_id"], "ten_pull_pool")

        assert result["success"] is False
        assert "Required: 10, Have: 5" in result["message"]

    def test_gacha_item_consumption_verification(self, gacha_controller, setup_test_data):
        """Test that items are correctly consumed during gacha."""
        data = setup_test_data

        # Check initial item count
        initial_amount = gacha_controller.item_controller.get_account_item_amount(
            data["account_id"], 1
        )

        # Perform gacha
        with patch("src.py_libs.controllers.gacha_controller.random.random", return_value=0.1):
            result = gacha_controller.gacha(data["account_id"], "test_pool")

        assert result["success"] is True

        # Check final item count
        final_amount = gacha_controller.item_controller.get_account_item_amount(
            data["account_id"], 1
        )

        assert final_amount == initial_amount - 1
        assert result["items_consumed"]["amount_consumed"] == 1

    def test_gacha_hero_probability_normalization(self, gacha_controller):
        """Test that hero selection works with non-normalized probabilities."""
        # Create heroes with probabilities that don't sum to 1.0
        heroes = [
            {"hero_id": 1, "probability": 3.0},  # 75% when normalized
            {"hero_id": 2, "probability": 1.0},  # 25% when normalized
        ]

        # Test selection with value that should select first hero
        with patch("src.py_libs.controllers.gacha_controller.random.random", return_value=0.5):
            selected = gacha_controller._select_random_hero(heroes)
            assert selected["hero_id"] == 1

        # Test selection with value that should select second hero
        with patch("src.py_libs.controllers.gacha_controller.random.random", return_value=0.8):
            selected = gacha_controller._select_random_hero(heroes)
            assert selected["hero_id"] == 2

    def test_gacha_with_mock_item_controller_failure(self, gacha_controller, setup_test_data):
        """Test gacha behavior when item removal fails."""
        data = setup_test_data

        # Mock item controller to fail on removal
        with patch.object(
            gacha_controller.item_controller, "remove_item_from_account"
        ) as mock_remove:
            mock_remove.return_value = {"success": False}

            with patch("src.py_libs.controllers.gacha_controller.random.random", return_value=0.1):
                result = gacha_controller.gacha(data["account_id"], "test_pool")

        assert result["success"] is True  # Gacha should still succeed
        assert result["hero_name"] == "Common Hero"
        assert result["items_consumed"] == {}  # No items consumed due to failure

    def test_gacha_with_database_error_on_hero_creation(self, gacha_controller, setup_test_data):
        """Test gacha behavior when hero creation fails."""
        data = setup_test_data

        # Mock _add_hero_to_account to fail
        with patch.object(gacha_controller, "_add_hero_to_account") as mock_add_hero:
            mock_add_hero.return_value = {"success": False, "message": "Database error"}

            with patch("src.py_libs.controllers.gacha_controller.random.random", return_value=0.1):
                result = gacha_controller.gacha(data["account_id"], "test_pool")

        assert result["success"] is False
        assert "Failed to add hero to account" in result["message"]
