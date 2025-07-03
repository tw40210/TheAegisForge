"""Integration tests for gacha functionality.

This module tests the complete gacha workflow:
1. Create an account
2. Send gacha tickets to the account
3. Perform gacha pulls using the tickets
4. Verify results
"""

from __future__ import annotations

import os
import tempfile
from unittest.mock import Mock, patch

import pytest
import yaml
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
def gacha_pools_config():
    """Real gacha pool configuration for integration testing."""
    return {
        "gacha_pools": {
            "standard_pool": {
                "name": "Standard Hero Pool",
                "description": "Basic gacha pool with common and rare heroes",
                "requiring_item_id": 1,  # Standard gacha ticket
                "num_requiring_item": 1,
                "heroes": [
                    {"hero_id": 1, "probability": 0.4},  # Knight
                    {"hero_id": 2, "probability": 0.3},  # Archer
                    {"hero_id": 3, "probability": 0.2},  # Mage
                    {"hero_id": 13, "probability": 0.1},  # Legendary Dragon
                ],
            },
            "premium_pool": {
                "name": "Premium Hero Pool",
                "description": "Premium gacha pool with rare and legendary heroes",
                "requiring_item_id": 2,  # Premium gacha ticket
                "num_requiring_item": 1,
                "heroes": [
                    {"hero_id": 4, "probability": 0.25},  # Dark Knight
                    {"hero_id": 5, "probability": 0.25},  # Fire Mage
                    {"hero_id": 6, "probability": 0.25},  # Ice Queen
                    {"hero_id": 14, "probability": 0.15},  # Ancient Dragon
                    {"hero_id": 16, "probability": 0.1},  # God of War
                ],
            },
            "rare_pool": {
                "name": "Rare Hero Pool",
                "description": "Special gacha pool with only rare and legendary heroes",
                "requiring_item_id": 3,  # Rare gacha ticket
                "num_requiring_item": 1,
                "heroes": [
                    {"hero_id": 7, "probability": 0.3},  # Shadow Assassin
                    {"hero_id": 8, "probability": 0.3},  # Holy Paladin
                    {"hero_id": 9, "probability": 0.25},  # Void Sorcerer
                    {"hero_id": 15, "probability": 0.15},  # Divine Phoenix
                ],
            },
            "ten_pull_pool": {
                "name": "Ten Pull Premium Pool",
                "description": "Premium ten-pull gacha with guaranteed rare hero",
                "requiring_item_id": 2,  # Premium gacha ticket
                "num_requiring_item": 10,
                "heroes": [
                    {"hero_id": 4, "probability": 0.2},  # Dark Knight
                    {"hero_id": 5, "probability": 0.2},  # Fire Mage
                    {"hero_id": 6, "probability": 0.2},  # Ice Queen
                    {"hero_id": 14, "probability": 0.2},  # Ancient Dragon
                    {"hero_id": 16, "probability": 0.1},  # God of War
                    {"hero_id": 15, "probability": 0.1},  # Divine Phoenix
                ],
            },
        }
    }


@pytest.fixture
def heroes_config():
    """Heroes configuration for testing."""
    return {
        "heroes": {
            "1": {"id": 1, "name": "Knight", "rarity": "Common"},
            "2": {"id": 2, "name": "Archer", "rarity": "Common"},
            "3": {"id": 3, "name": "Mage", "rarity": "Common"},
            "4": {"id": 4, "name": "Dark Knight", "rarity": "Rare"},
            "5": {"id": 5, "name": "Fire Mage", "rarity": "Rare"},
            "6": {"id": 6, "name": "Ice Queen", "rarity": "Rare"},
            "7": {"id": 7, "name": "Shadow Assassin", "rarity": "Rare"},
            "8": {"id": 8, "name": "Holy Paladin", "rarity": "Rare"},
            "9": {"id": 9, "name": "Void Sorcerer", "rarity": "Rare"},
            "13": {"id": 13, "name": "Legendary Dragon", "rarity": "Legendary"},
            "14": {"id": 14, "name": "Ancient Dragon", "rarity": "Legendary"},
            "15": {"id": 15, "name": "Divine Phoenix", "rarity": "Legendary"},
            "16": {"id": 16, "name": "God of War", "rarity": "Legendary"},
        }
    }


@pytest.fixture
def temp_config_files(gacha_pools_config, heroes_config):
    """Create temporary config files for testing."""
    # Create temporary gacha pools config
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(gacha_pools_config, f)
        gacha_file = f.name

    # Create temporary heroes config
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(heroes_config, f)
        heroes_file = f.name

    yield {"gacha": gacha_file, "heroes": heroes_file}

    # Cleanup
    for file_path in [gacha_file, heroes_file]:
        if os.path.exists(file_path):
            os.unlink(file_path)


@pytest.fixture
def controllers(engine, temp_config_files):
    """Create controller instances with test database and config."""
    # Mock the config file paths
    with patch("src.py_libs.controllers.gacha_controller.Path") as mock_path:
        # Mock gacha pools config path
        mock_gacha_path = Mock()
        mock_gacha_path.exists.return_value = True
        mock_path.return_value.parent.parent.parent.__truediv__.return_value.__truediv__.return_value = temp_config_files[
            "gacha"
        ]

        # Create controllers
        account_controller = AccountController()
        item_controller = ItemController()
        gacha_controller = GachaController()

        # Set engines to use test database
        account_controller.engine = engine
        item_controller.engine = engine
        gacha_controller.engine = engine
        gacha_controller._ensure_engine_consistency()

        # Manually load config files
        with open(temp_config_files["gacha"]) as f:
            gacha_config = yaml.safe_load(f)
            gacha_controller.gacha_pools = gacha_config.get("gacha_pools", {})

        with open(temp_config_files["heroes"]) as f:
            heroes_config = yaml.safe_load(f)
            gacha_controller.heroes_config = heroes_config.get("heroes", {})

        return {
            "account": account_controller,
            "item": item_controller,
            "gacha": gacha_controller,
        }


@pytest.fixture
def gacha_items(controllers):
    """Create gacha ticket items in the database."""
    with Session(controllers["account"].engine) as session:
        items = [
            Item(id=1, name="Standard Gacha Ticket"),
            Item(id=2, name="Premium Gacha Ticket"),
            Item(id=3, name="Rare Gacha Ticket"),
        ]
        session.add_all(items)
        session.commit()

        return {
            "standard": {"id": 1, "name": "Standard Gacha Ticket"},
            "premium": {"id": 2, "name": "Premium Gacha Ticket"},
            "rare": {"id": 3, "name": "Rare Gacha Ticket"},
        }


class TestGachaIntegration:
    """Integration tests for complete gacha workflow."""

    def test_complete_gacha_workflow_standard_pool(self, controllers, gacha_items):
        """Test complete workflow: create account, send tickets, do standard gacha."""
        account_ctrl = controllers["account"]
        item_ctrl = controllers["item"]
        gacha_ctrl = controllers["gacha"]

        # Step 1: Create a new account
        account_data = account_ctrl.create_account(
            name="test_player", stories=[], status="active", party_sets=[]
        )
        assert account_data is not None, "Account creation failed"
        account_id = account_data["id"]
        assert account_data["name"] == "test_player"

        # Step 2: Send standard gacha tickets to the account
        send_result = item_ctrl.send_item_to_account(
            item_id=1, num_item=5, account_id=account_id  # Standard Gacha Ticket
        )
        assert send_result["success"] is True
        assert send_result["amount_added"] == 5
        assert "Standard Gacha Ticket" in send_result["message"]

        # Step 3: Verify account has the tickets
        ticket_amount = item_ctrl.get_account_item_amount(account_id, 1)
        assert ticket_amount == 5

        # Step 4: Perform gacha pull
        gacha_result = gacha_ctrl.gacha(account_id, "standard_pool")
        assert gacha_result["success"] is True
        assert gacha_result["account_id"] == account_id
        assert gacha_result["gacha_pool_id"] == "standard_pool"
        assert "hero_name" in gacha_result
        assert "hero_obtained" in gacha_result
        assert gacha_result["hero_obtained"]["hero_id"] in [1, 2, 3, 13]

        # Step 5: Verify item consumption
        assert "items_consumed" in gacha_result
        consumed = gacha_result["items_consumed"]
        assert consumed["item_id"] == 1
        assert consumed["amount_consumed"] == 1
        assert "Standard Gacha Ticket" in consumed["item_name"]

        # Step 6: Verify tickets were deducted
        remaining_tickets = item_ctrl.get_account_item_amount(account_id, 1)
        assert remaining_tickets == 4

        # Step 7: Verify hero was added to account
        heroes = account_ctrl.get_account_heroes(account_id)
        assert len(heroes) == 1
        assert heroes[0]["name"] == gacha_result["hero_name"]
        assert heroes[0]["level"] == 1  # New heroes start at level 1

    def test_complete_gacha_workflow_premium_pool(self, controllers, gacha_items):
        """Test complete workflow with premium gacha pool."""
        account_ctrl = controllers["account"]
        item_ctrl = controllers["item"]
        gacha_ctrl = controllers["gacha"]

        # Create account
        account_data = account_ctrl.create_account(name="premium_player")
        account_id = account_data["id"]

        # Send premium tickets
        send_result = item_ctrl.send_item_to_account(
            item_id=2, num_item=3, account_id=account_id  # Premium Gacha Ticket
        )
        assert send_result["success"] is True

        # Perform premium gacha
        gacha_result = gacha_ctrl.gacha(account_id, "premium_pool")
        assert gacha_result["success"] is True
        assert gacha_result["hero_obtained"]["hero_id"] in [4, 5, 6, 14, 16]

        # Verify premium ticket consumption
        remaining_tickets = item_ctrl.get_account_item_amount(account_id, 2)
        assert remaining_tickets == 2

    def test_multiple_gacha_pulls(self, controllers, gacha_items):
        """Test multiple gacha pulls with multi_gacha method."""
        account_ctrl = controllers["account"]
        item_ctrl = controllers["item"]
        gacha_ctrl = controllers["gacha"]

        # Create account
        account_data = account_ctrl.create_account(name="multi_pull_player")
        account_id = account_data["id"]

        # Send enough tickets for multiple pulls
        item_ctrl.send_item_to_account(
            item_id=1, num_item=10, account_id=account_id  # Standard Gacha Ticket
        )

        # Perform 3 gacha pulls
        multi_result = gacha_ctrl.multi_gacha(account_id, "standard_pool", 3)
        assert multi_result["success"] is True
        assert multi_result["num_pulls"] == 3
        assert len(multi_result["heroes_obtained"]) == 3

        # Verify all heroes are valid
        for hero in multi_result["heroes_obtained"]:
            assert hero["hero_id"] in [1, 2, 3, 13]

        # Verify ticket consumption
        consumed = multi_result["items_consumed"]
        assert consumed[1]["amount_consumed"] == 3
        remaining_tickets = item_ctrl.get_account_item_amount(account_id, 1)
        assert remaining_tickets == 7

        # Verify heroes were added
        heroes = account_ctrl.get_account_heroes(account_id)
        assert len(heroes) == 3

    def test_ten_pull_gacha(self, controllers, gacha_items):
        """Test ten-pull gacha requiring 10 premium tickets."""
        account_ctrl = controllers["account"]
        item_ctrl = controllers["item"]
        gacha_ctrl = controllers["gacha"]

        # Create account
        account_data = account_ctrl.create_account(name="ten_pull_player")
        account_id = account_data["id"]

        # Send exactly 10 premium tickets
        item_ctrl.send_item_to_account(
            item_id=2, num_item=10, account_id=account_id  # Premium Gacha Ticket
        )

        # Perform ten-pull gacha
        gacha_result = gacha_ctrl.gacha(account_id, "ten_pull_pool")
        assert gacha_result["success"] is True
        assert gacha_result["items_consumed"]["amount_consumed"] == 10

        # Verify all tickets consumed
        remaining_tickets = item_ctrl.get_account_item_amount(account_id, 2)
        assert remaining_tickets == 0

    def test_insufficient_tickets_scenario(self, controllers, gacha_items):
        """Test gacha failure when account has insufficient tickets."""
        account_ctrl = controllers["account"]
        gacha_ctrl = controllers["gacha"]

        # Create account
        account_data = account_ctrl.create_account(name="poor_player")
        account_id = account_data["id"]

        # Don't send any tickets

        # Try to perform gacha without tickets
        gacha_result = gacha_ctrl.gacha(account_id, "standard_pool")
        assert gacha_result["success"] is False
        assert "Insufficient" in gacha_result["message"]
        assert gacha_result["hero_obtained"] is None

        # Verify no heroes were added
        heroes = account_ctrl.get_account_heroes(account_id)
        assert len(heroes) == 0

    def test_partial_tickets_ten_pull(self, controllers, gacha_items):
        """Test ten-pull failure when account has less than 10 tickets."""
        account_ctrl = controllers["account"]
        item_ctrl = controllers["item"]
        gacha_ctrl = controllers["gacha"]

        # Create account
        account_data = account_ctrl.create_account(name="partial_player")
        account_id = account_data["id"]

        # Send only 5 premium tickets (need 10 for ten-pull)
        item_ctrl.send_item_to_account(
            item_id=2, num_item=5, account_id=account_id  # Premium Gacha Ticket
        )

        # Try to perform ten-pull gacha
        gacha_result = gacha_ctrl.gacha(account_id, "ten_pull_pool")
        assert gacha_result["success"] is False
        assert "Required: 10, Have: 5" in gacha_result["message"]

        # Verify tickets weren't consumed
        remaining_tickets = item_ctrl.get_account_item_amount(account_id, 2)
        assert remaining_tickets == 5

    def test_account_inventory_after_gacha(self, controllers, gacha_items):
        """Test that account inventory is properly updated after gacha."""
        account_ctrl = controllers["account"]
        item_ctrl = controllers["item"]
        gacha_ctrl = controllers["gacha"]

        # Create account
        account_data = account_ctrl.create_account(name="inventory_player")
        account_id = account_data["id"]

        # Send multiple types of tickets
        item_ctrl.send_item_to_account(item_id=1, num_item=5, account_id=account_id)  # Standard
        item_ctrl.send_item_to_account(item_id=2, num_item=3, account_id=account_id)  # Premium
        item_ctrl.send_item_to_account(item_id=3, num_item=1, account_id=account_id)  # Rare

        # Check initial inventory
        inventory = account_ctrl.get_account_inventory(account_id)
        assert len(inventory) == 3
        ticket_amounts = {item["item_id"]: item["amount"] for item in inventory}
        assert ticket_amounts[1] == 5  # Standard tickets
        assert ticket_amounts[2] == 3  # Premium tickets
        assert ticket_amounts[3] == 1  # Rare tickets

        # Perform different gacha pulls
        gacha_ctrl.gacha(account_id, "standard_pool")  # Uses 1 standard ticket
        gacha_ctrl.gacha(account_id, "premium_pool")  # Uses 1 premium ticket
        gacha_ctrl.gacha(account_id, "rare_pool")  # Uses 1 rare ticket

        # Check final inventory
        final_inventory = account_ctrl.get_account_inventory(account_id)
        final_amounts = {item["item_id"]: item["amount"] for item in final_inventory}
        assert final_amounts[1] == 4  # Standard tickets decreased
        assert final_amounts[2] == 2  # Premium tickets decreased
        # Rare ticket should be completely removed from inventory
        assert 3 not in final_amounts

        # Verify heroes were added
        heroes = account_ctrl.get_account_heroes(account_id)
        assert len(heroes) == 3

    def test_gacha_pool_info_integration(self, controllers, gacha_items):
        """Test getting gacha pool information in integration context."""
        gacha_ctrl = controllers["gacha"]

        # Test getting available pools
        pools = gacha_ctrl.get_available_pools()
        assert len(pools) == 4
        pool_names = [pool["name"] for pool in pools]
        assert "Standard Hero Pool" in pool_names
        assert "Premium Hero Pool" in pool_names

        # Test getting specific pool info
        pool_info = gacha_ctrl.get_gacha_pool_info("standard_pool")
        assert pool_info["success"] is True
        assert pool_info["pool_info"]["requiring_item_id"] == 1
        assert len(pool_info["pool_info"]["heroes"]) == 4
