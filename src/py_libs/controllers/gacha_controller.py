"""Gacha controller for managing gacha events and hero summoning."""

from __future__ import annotations

import random
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy.orm import Session

from src.py_libs.controllers.account_controller import AccountController
from src.py_libs.controllers.item_controller import ItemController
from src.py_libs.controllers.sql_db_controller import Hero, engine


class GachaController:
    """Controller for managing gacha operations and hero summoning."""

    def __init__(self):
        """Initialize the gacha controller."""
        self.engine = engine
        self.account_controller = AccountController()
        self.item_controller = ItemController()
        self.gacha_pools = self._load_gacha_pools()
        self.heroes_config = self._load_heroes_config()

    def _ensure_engine_consistency(self):
        """Ensure all sub-controllers use the same engine as this controller."""
        self.account_controller.engine = self.engine
        self.item_controller.engine = self.engine

    def _load_gacha_pools(self) -> dict[str, Any]:
        """Load gacha pool configurations from YAML file.

        Returns:
            Dictionary containing gacha pool configurations
        """
        config_path = Path(__file__).parent.parent.parent / "config" / "gacha_pools.yaml"
        try:
            with open(config_path) as file:
                config = yaml.safe_load(file)
                return config.get("gacha_pools", {})
        except FileNotFoundError:
            return {}

    def _load_heroes_config(self) -> dict[str, Any]:
        """Load heroes configuration from YAML file."""
        try:
            config_path = Path("src/config/heroes.yaml")
            if config_path.exists():
                with open(config_path, encoding="utf-8") as file:
                    config = yaml.safe_load(file)
                    return config.get("heroes", {})
        except Exception as e:
            print(f"Warning: Could not load heroes config: {e}")

        # Return empty dict if loading fails
        return {}

    def _get_hero_name_by_id(self, hero_id: int) -> str:
        """Get hero name by hero ID from configuration."""
        hero_data = self.heroes_config.get(str(hero_id))
        if hero_data:
            return hero_data.get("name", f"Hero {hero_id}")
        return f"Hero {hero_id}"

    def get_available_pools(self) -> list[dict[str, Any]]:
        """Get all available gacha pools.

        Returns:
            List of gacha pool information
        """
        pools = []
        for pool_id, pool_data in self.gacha_pools.items():
            hero_names = []
            for hero in pool_data.get("heroes", []):
                hero_id = hero.get("hero_id")
                if hero_id:
                    hero_names.append(self._get_hero_name_by_id(hero_id))

            pools.append(
                {
                    "pool_id": pool_id,
                    "name": pool_data.get("name", pool_id),
                    "description": pool_data.get("description", ""),
                    "requiring_item_id": pool_data.get("requiring_item_id"),
                    "num_requiring_item": pool_data.get("num_requiring_item"),
                    "heroes": hero_names,
                }
            )
        return pools

    def gacha(self, account_id: int, gacha_pool_id: str) -> dict[str, Any]:
        """Perform a gacha summon to randomly pick a hero from the pool.

        Args:
            account_id: The ID of the account performing the gacha
            gacha_pool_id: The ID of the gacha pool to draw from

        Returns:
            Dictionary with gacha result information
        """
        # Ensure engine consistency
        self._ensure_engine_consistency()

        # Validate account exists
        account = self.account_controller.get_account(account_id)
        if not account:
            return {
                "success": False,
                "message": f"Account {account_id} does not exist",
                "account_id": account_id,
                "gacha_pool_id": gacha_pool_id,
                "hero_obtained": None,
                "items_consumed": {},
            }

        # Validate gacha pool exists
        if gacha_pool_id not in self.gacha_pools:
            return {
                "success": False,
                "message": f"Gacha pool '{gacha_pool_id}' does not exist",
                "account_id": account_id,
                "gacha_pool_id": gacha_pool_id,
                "hero_obtained": None,
                "items_consumed": {},
            }

        pool_config = self.gacha_pools[gacha_pool_id]

        # Validate heroes exist in pool BEFORE checking items
        heroes = pool_config.get("heroes", [])
        if not heroes:
            return {
                "success": False,
                "message": f"Gacha pool '{gacha_pool_id}' has no heroes configured",
                "account_id": account_id,
                "gacha_pool_id": gacha_pool_id,
                "hero_obtained": None,
                "items_consumed": {},
            }

        requiring_item_id = pool_config.get("requiring_item_id")
        num_requiring_item = pool_config.get("num_requiring_item", 1)

        # Check if account has required items
        if requiring_item_id:
            current_amount = self.item_controller.get_account_item_amount(
                account_id, requiring_item_id
            )
            if current_amount < num_requiring_item:
                item_info = self.item_controller.get_item(requiring_item_id)
                item_name = item_info.get("name", f"Item {requiring_item_id}")
                return {
                    "success": False,
                    "message": f"Insufficient {item_name}. Required: {num_requiring_item}, Have: {current_amount}",
                    "account_id": account_id,
                    "gacha_pool_id": gacha_pool_id,
                    "hero_obtained": None,
                    "items_consumed": {},
                }

        # Randomly select hero from pool based on probabilities
        selected_hero = self._select_random_hero(heroes)
        if not selected_hero:
            return {
                "success": False,
                "message": "Failed to select hero from pool",
                "account_id": account_id,
                "gacha_pool_id": gacha_pool_id,
                "hero_obtained": None,
                "items_consumed": {},
            }

        # Get hero name from ID
        hero_id = selected_hero["hero_id"]
        hero_name = self._get_hero_name_by_id(hero_id)

        # Add hero to account
        hero_result = self._add_hero_to_account(account_id, hero_name)
        if not hero_result["success"]:
            return {
                "success": False,
                "message": f"Failed to add hero to account: {hero_result['message']}",
                "account_id": account_id,
                "gacha_pool_id": gacha_pool_id,
                "hero_obtained": selected_hero,
                "items_consumed": {},
            }

        # Consume required items
        items_consumed = {}
        if requiring_item_id and num_requiring_item > 0:
            remove_result = self.item_controller.remove_item_from_account(
                requiring_item_id, num_requiring_item, account_id
            )
            if remove_result["success"]:
                items_consumed = {
                    "item_id": requiring_item_id,
                    "item_name": remove_result["item_name"],
                    "amount_consumed": num_requiring_item,
                }

        return {
            "success": True,
            "message": f"Successfully obtained {hero_name} from {pool_config.get('name', gacha_pool_id)}!",
            "account_id": account_id,
            "gacha_pool_id": gacha_pool_id,
            "hero_name": hero_name,
            "hero_level": 1,
            "hero_obtained": {
                "hero_id": hero_id,
                "name": hero_name,
                "probability": selected_hero["probability"],
                "database_hero_id": hero_result["hero_id"],
            },
            "items_consumed": items_consumed,
        }

    def _select_random_hero(self, heroes: list[dict[str, Any]]) -> dict[str, Any] | None:
        """Randomly select a hero from the list based on their probabilities.

        Args:
            heroes: List of hero dictionaries with hero_id and probability

        Returns:
            Selected hero dictionary or None if selection fails
        """
        if not heroes:
            return None

        # Normalize probabilities to ensure they sum to 1.0
        total_probability = sum(hero.get("probability", 0) for hero in heroes)
        if total_probability <= 0:
            return None

        # Generate random number and select hero
        random_value = random.random() * total_probability
        cumulative_probability = 0

        for hero in heroes:
            probability = hero.get("probability", 0)
            cumulative_probability += probability
            if random_value <= cumulative_probability:
                return hero

        # Fallback to last hero if floating point errors occur
        return heroes[-1] if heroes else None

    def _add_hero_to_account(self, account_id: int, hero_name: str) -> dict[str, Any]:
        """Add a new hero to the specified account.

        Args:
            account_id: The ID of the account
            hero_name: The name of the hero to add

        Returns:
            Dictionary with operation result
        """
        try:
            with Session(self.engine) as session:
                hero = Hero(
                    account_id=account_id, name=hero_name, level=1  # New heroes start at level 1
                )
                session.add(hero)
                session.commit()

                return {
                    "success": True,
                    "message": f"Hero {hero_name} added to account {account_id}",
                    "hero_id": hero.id,
                }
        except Exception as e:
            return {"success": False, "message": f"Database error: {str(e)}", "hero_id": None}

    def get_gacha_pool_info(self, gacha_pool_id: str) -> dict[str, Any]:
        """Get detailed information about a specific gacha pool.

        Args:
            gacha_pool_id: The ID of the gacha pool

        Returns:
            Dictionary with gacha pool information
        """
        if gacha_pool_id not in self.gacha_pools:
            return {
                "success": False,
                "message": f"Gacha pool '{gacha_pool_id}' does not exist",
                "pool_info": None,
            }

        pool_config = self.gacha_pools[gacha_pool_id]

        return {
            "success": True,
            "message": f"Gacha pool '{gacha_pool_id}' information retrieved",
            "pool_info": {
                "pool_id": gacha_pool_id,
                "name": pool_config.get("name", gacha_pool_id),
                "description": pool_config.get("description", ""),
                "requiring_item_id": pool_config.get("requiring_item_id"),
                "num_requiring_item": pool_config.get("num_requiring_item"),
                "heroes": pool_config.get("heroes", []),
            },
        }

    def multi_gacha(self, account_id: int, gacha_pool_id: str, num_pulls: int) -> dict[str, Any]:
        """Perform multiple gacha pulls at once.

        Args:
            account_id: The ID of the account performing the gacha
            gacha_pool_id: The ID of the gacha pool to draw from
            num_pulls: Number of gacha pulls to perform

        Returns:
            Dictionary with results of all gacha pulls
        """
        if num_pulls <= 0:
            return {
                "success": False,
                "message": "Number of pulls must be greater than 0",
                "account_id": account_id,
                "gacha_pool_id": gacha_pool_id,
                "heroes_obtained": [],
                "items_consumed": {},
                "num_pulls": num_pulls,
            }

        results = []
        total_items_consumed = {}
        failed_pulls = 0

        for _ in range(num_pulls):
            result = self.gacha(account_id, gacha_pool_id)
            if result["success"]:
                results.append(result["hero_obtained"])
                # Accumulate consumed items
                if result["items_consumed"]:
                    item_id = result["items_consumed"]["item_id"]
                    amount = result["items_consumed"]["amount_consumed"]
                    if item_id in total_items_consumed:
                        total_items_consumed[item_id]["amount_consumed"] += amount
                    else:
                        total_items_consumed[item_id] = result["items_consumed"].copy()
            else:
                failed_pulls += 1
                # If we fail once, we'll likely fail all subsequent pulls
                # Return early to avoid unnecessary attempts
                break

        if failed_pulls > 0:
            return {
                "success": False,
                "message": f"Failed after {len(results)} successful pulls: {result['message']}",
                "account_id": account_id,
                "gacha_pool_id": gacha_pool_id,
                "heroes_obtained": results,
                "items_consumed": total_items_consumed,
                "num_pulls": len(results),
            }

        return {
            "success": True,
            "message": f"Successfully completed {num_pulls} gacha pulls",
            "account_id": account_id,
            "gacha_pool_id": gacha_pool_id,
            "heroes_obtained": results,
            "items_consumed": total_items_consumed,
            "num_pulls": num_pulls,
        }
