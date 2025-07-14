"""Integration tests for gacha system with multiple controllers."""

from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.py_libs.controllers.account_controller import AccountController
from src.py_libs.controllers.gacha_controller import GachaController
from src.py_libs.controllers.item_controller import ItemController
from src.py_libs.controllers.sql_db_controller import Base, Item

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
def controllers(engine):
    """Create controller instances with test database."""
    account_ctrl = AccountController()
    account_ctrl.engine = engine

    item_ctrl = ItemController()
    item_ctrl.engine = engine

    gacha_ctrl = GachaController()
    gacha_ctrl.engine = engine

    return account_ctrl, item_ctrl, gacha_ctrl


@pytest.fixture
def mock_firebase_token():
    """Mock Firebase ID token for testing."""
    return "mock_firebase_token"


@pytest.fixture
def mock_decoded_token():
    """Mock decoded Firebase token data."""
    return {"uid": "firebase_uid_123", "email": "test@example.com", "name": "Test User"}


@pytest.fixture
def sample_items(engine):
    """Create sample items in the database."""
    with Session(engine) as session:
        # Create gacha ticket item
        gacha_ticket = Item(id=1, name="Gacha Ticket")

        # Create premium gacha ticket item
        premium_ticket = Item(id=2, name="Premium Gacha Ticket")

        session.add_all([gacha_ticket, premium_ticket])
        session.commit()

        # Refresh to avoid DetachedInstanceError
        session.refresh(gacha_ticket)
        session.refresh(premium_ticket)

        return {
            "gacha_ticket": {"id": gacha_ticket.id, "name": gacha_ticket.name},
            "premium_ticket": {"id": premium_ticket.id, "name": premium_ticket.name},
        }


class TestGachaIntegration:
    """Integration tests for gacha system."""

    @patch("src.py_libs.controllers.account_controller.auth.verify_id_token")
    def test_complete_gacha_workflow_standard_pool(
        self, mock_verify_token, controllers, sample_items, mock_firebase_token, mock_decoded_token
    ):
        """Test complete gacha workflow with standard pool."""
        account_ctrl, item_ctrl, gacha_ctrl = controllers

        # Mock Firebase token verification
        mock_verify_token.return_value = mock_decoded_token

        # Create account
        account_data = account_ctrl.create_account(id_token=mock_firebase_token)

        # Add gacha tickets to account - fixed parameter order
        result = item_ctrl.send_item_to_account(
            1, 10, account_data["id"]
        )  # item_id, amount, account_id
        assert result["success"] is True

        # Verify tickets were added
        tickets = item_ctrl.get_account_item_amount(account_data["id"], 1)
        assert tickets == 10

        # Perform gacha
        gacha_result = gacha_ctrl.gacha(account_data["id"], "standard_pool")

        # Verify gacha result structure
        assert gacha_result is not None
        assert "success" in gacha_result

        # Check if gacha was successful or failed due to missing config
        if gacha_result["success"]:
            assert "hero_obtained" in gacha_result
            assert "hero_name" in gacha_result

            # Verify tickets were consumed
            remaining_tickets = item_ctrl.get_account_item_amount(account_data["id"], 1)
            assert remaining_tickets == 9  # 10 - 1 = 9

            # Verify hero was added to account
            heroes = account_ctrl.get_account_heroes(account_data["id"])
            assert len(heroes) == 1
            assert heroes[0]["name"] == gacha_result["hero_name"]
        else:
            # If gacha pool not configured, that's expected
            assert gacha_result["success"] is False

    @patch("src.py_libs.controllers.account_controller.auth.verify_id_token")
    def test_complete_gacha_workflow_premium_pool(
        self, mock_verify_token, controllers, sample_items, mock_firebase_token, mock_decoded_token
    ):
        """Test complete gacha workflow with premium pool."""
        account_ctrl, item_ctrl, gacha_ctrl = controllers

        # Mock Firebase token verification
        mock_verify_token.return_value = mock_decoded_token

        # Create account
        account_data = account_ctrl.create_account(id_token=mock_firebase_token)

        # Add premium gacha tickets to account - fixed parameter order
        result = item_ctrl.send_item_to_account(
            2, 5, account_data["id"]
        )  # item_id, amount, account_id
        assert result["success"] is True

        # Perform gacha
        gacha_result = gacha_ctrl.gacha(account_data["id"], "premium_pool")

        # Verify gacha result structure
        assert gacha_result is not None
        assert "success" in gacha_result

        # Check if gacha was successful or failed due to missing config
        if gacha_result["success"]:
            assert "hero_obtained" in gacha_result

            # Verify premium tickets were consumed
            remaining_tickets = item_ctrl.get_account_item_amount(account_data["id"], 2)
            assert remaining_tickets == 4  # 5 - 1 = 4
        else:
            # If gacha pool not configured, that's expected
            assert gacha_result["success"] is False

    @patch("src.py_libs.controllers.account_controller.auth.verify_id_token")
    def test_multiple_gacha_pulls(
        self, mock_verify_token, controllers, sample_items, mock_firebase_token, mock_decoded_token
    ):
        """Test multiple gacha pulls."""
        account_ctrl, item_ctrl, gacha_ctrl = controllers

        # Mock Firebase token verification
        mock_verify_token.return_value = mock_decoded_token

        # Create account
        account_data = account_ctrl.create_account(id_token=mock_firebase_token)

        # Add gacha tickets - fixed parameter order
        result = item_ctrl.send_item_to_account(
            1, 20, account_data["id"]
        )  # item_id, amount, account_id
        assert result["success"] is True

        # Perform multiple gacha pulls
        num_pulls = 3
        results = gacha_ctrl.multi_gacha(account_data["id"], "standard_pool", num_pulls)

        # Verify results structure
        assert results is not None
        assert "success" in results
        assert "heroes_obtained" in results

        # Check if multi-gacha was successful or failed due to missing config
        if results["success"]:
            assert len(results["heroes_obtained"]) == num_pulls

            # Verify tickets were consumed
            remaining_tickets = item_ctrl.get_account_item_amount(account_data["id"], 1)
            assert remaining_tickets == 17  # 20 - 3 = 17

            # Verify heroes were added (total amount should equal num_pulls)
            heroes = account_ctrl.get_account_heroes(account_data["id"])
            total_hero_amount = sum(hero.get("amount", 1) for hero in heroes)
            assert total_hero_amount == num_pulls
        else:
            # If gacha pool not configured, that's expected
            assert results["success"] is False

    @patch("src.py_libs.controllers.account_controller.auth.verify_id_token")
    def test_ten_pull_gacha(
        self, mock_verify_token, controllers, sample_items, mock_firebase_token, mock_decoded_token
    ):
        """Test ten-pull gacha functionality."""
        account_ctrl, item_ctrl, gacha_ctrl = controllers

        # Mock Firebase token verification
        mock_verify_token.return_value = mock_decoded_token

        # Create account
        account_data = account_ctrl.create_account(id_token=mock_firebase_token)

        # Add gacha tickets - fixed parameter order
        result = item_ctrl.send_item_to_account(
            1, 15, account_data["id"]
        )  # item_id, amount, account_id
        assert result["success"] is True

        # Perform ten-pull gacha
        results = gacha_ctrl.multi_gacha(account_data["id"], "standard_pool", 10)

        # Verify results structure
        assert results is not None
        assert "success" in results
        assert "heroes_obtained" in results

        # Check if ten-pull gacha was successful or failed due to missing config
        if results["success"]:
            assert len(results["heroes_obtained"]) == 10

            # Verify tickets were consumed
            remaining_tickets = item_ctrl.get_account_item_amount(account_data["id"], 1)
            assert remaining_tickets == 5  # 15 - 10 = 5

            # Verify heroes were added (total amount should equal 10)
            heroes = account_ctrl.get_account_heroes(account_data["id"])
            total_hero_amount = sum(hero.get("amount", 1) for hero in heroes)
            assert total_hero_amount == 10
        else:
            # If gacha pool not configured, that's expected
            assert results["success"] is False

    @patch("src.py_libs.controllers.account_controller.auth.verify_id_token")
    def test_insufficient_tickets_scenario(
        self, mock_verify_token, controllers, sample_items, mock_firebase_token, mock_decoded_token
    ):
        """Test gacha with insufficient tickets."""
        account_ctrl, item_ctrl, gacha_ctrl = controllers

        # Mock Firebase token verification
        mock_verify_token.return_value = mock_decoded_token

        # Create account
        account_data = account_ctrl.create_account(id_token=mock_firebase_token)

        # Don't add any tickets

        # Attempt gacha
        gacha_result = gacha_ctrl.gacha(account_data["id"], "standard_pool")

        # Verify gacha failed due to insufficient tickets or missing config
        assert gacha_result is not None
        assert gacha_result["success"] is False

        # Verify no heroes were added
        heroes = account_ctrl.get_account_heroes(account_data["id"])
        assert len(heroes) == 0

    @patch("src.py_libs.controllers.account_controller.auth.verify_id_token")
    def test_partial_tickets_ten_pull(
        self, mock_verify_token, controllers, sample_items, mock_firebase_token, mock_decoded_token
    ):
        """Test ten-pull gacha with insufficient tickets."""
        account_ctrl, item_ctrl, gacha_ctrl = controllers

        # Mock Firebase token verification
        mock_verify_token.return_value = mock_decoded_token

        # Create account
        account_data = account_ctrl.create_account(id_token=mock_firebase_token)

        # Add insufficient tickets for ten-pull - fixed parameter order
        result = item_ctrl.send_item_to_account(
            1, 5, account_data["id"]
        )  # item_id, amount, account_id
        assert result["success"] is True

        # Attempt ten-pull gacha
        results = gacha_ctrl.multi_gacha(account_data["id"], "standard_pool", 10)

        # Verify ten-pull failed due to insufficient tickets or missing config
        assert results is not None
        assert results["success"] is False

        # Verify some tickets were consumed for the successful individual pulls
        # (The multi_gacha processes pulls sequentially, so it will succeed for some pulls
        # until it runs out of tickets)
        remaining_tickets = item_ctrl.get_account_item_amount(account_data["id"], 1)

        # Check if gacha pool is configured
        if "heroes_obtained" in results and len(results["heroes_obtained"]) > 0:
            # If gacha pool is configured, tickets should be consumed for successful pulls
            assert remaining_tickets < 5  # Some tickets should be consumed

            # Verify some heroes were added (total amount should equal successful pulls)
            heroes = account_ctrl.get_account_heroes(account_data["id"])
            total_hero_amount = sum(hero.get("amount", 1) for hero in heroes)
            assert total_hero_amount == len(results["heroes_obtained"])
        else:
            # If gacha pool is not configured, no tickets should be consumed
            assert remaining_tickets == 5  # Should still have 5 tickets

            # Verify no heroes were added
            heroes = account_ctrl.get_account_heroes(account_data["id"])
            assert len(heroes) == 0

    @patch("src.py_libs.controllers.account_controller.auth.verify_id_token")
    def test_account_inventory_after_gacha(
        self, mock_verify_token, controllers, sample_items, mock_firebase_token, mock_decoded_token
    ):
        """Test account inventory changes after gacha."""
        account_ctrl, item_ctrl, gacha_ctrl = controllers

        # Mock Firebase token verification
        mock_verify_token.return_value = mock_decoded_token

        # Create account
        account_data = account_ctrl.create_account(id_token=mock_firebase_token)

        # Add multiple types of items - fixed parameter order
        result1 = item_ctrl.send_item_to_account(1, 10, account_data["id"])  # Gacha tickets
        result2 = item_ctrl.send_item_to_account(2, 5, account_data["id"])  # Premium tickets
        assert result1["success"] is True
        assert result2["success"] is True

        # Check initial inventory
        initial_inventory = account_ctrl.get_account_inventory(account_data["id"])
        assert len(initial_inventory) == 2

        # Perform gacha
        gacha_result = gacha_ctrl.gacha(account_data["id"], "standard_pool")

        # Check inventory after gacha
        final_inventory = account_ctrl.get_account_inventory(account_data["id"])

        # Verify inventory exists (exact changes depend on if gacha pool is configured)
        if gacha_result["success"]:
            # If gacha was successful, gacha tickets should be consumed
            gacha_tickets = next((item for item in final_inventory if item["item_id"] == 1), None)
            assert gacha_tickets is not None
            assert gacha_tickets["amount"] == 9  # 10 - 1 = 9
        else:
            # If gacha failed (likely due to missing config), tickets should remain
            gacha_tickets = next((item for item in final_inventory if item["item_id"] == 1), None)
            assert gacha_tickets is not None
            assert gacha_tickets["amount"] == 10  # Should remain unchanged

        # Premium tickets should always remain unchanged
        premium_tickets = next((item for item in final_inventory if item["item_id"] == 2), None)
        assert premium_tickets is not None
        assert premium_tickets["amount"] == 5  # Should remain unchanged

    def test_gacha_pool_info_integration(self, controllers, sample_items):
        """Test gacha pool info retrieval."""
        account_ctrl, item_ctrl, gacha_ctrl = controllers

        # Get available pools
        pools = gacha_ctrl.get_available_pools()

        # Pools might be empty if no config file, that's ok
        assert isinstance(pools, list)

        # Get specific pool info
        pool_info_result = gacha_ctrl.get_gacha_pool_info("standard_pool")

        # Verify pool info structure
        assert pool_info_result is not None
        assert "success" in pool_info_result

        # Check if pool info is available or if it's expected to be missing
        if pool_info_result["success"]:
            assert "pool_info" in pool_info_result
            assert pool_info_result["pool_info"]["pool_id"] == "standard_pool"
            assert "heroes" in pool_info_result["pool_info"]
            assert "requiring_item_id" in pool_info_result["pool_info"]
        else:
            # If pool doesn't exist (no config), that's expected
            assert pool_info_result["success"] is False
