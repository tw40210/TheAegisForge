"""Item controller for managing item operations in the database."""

from __future__ import annotations

from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.py_libs.controllers.sql_db_controller import Account, AccountItem, Item, engine


class ItemController:
    """Controller for managing item operations in the database."""

    def __init__(self):
        """Initialize the item controller."""
        self.engine = engine

    def send_item_to_account(self, item_id: int, num_item: int, account_id: int) -> dict[str, Any]:
        """Send items to an account's inventory.

        Args:
            item_id: The ID of the item to send
            num_item: The number of items to send
            account_id: The ID of the account to send items to

        Returns:
            Dictionary with operation result
        """
        if num_item <= 0:
            return {
                "success": False,
                "message": f"Invalid number of items to send: {num_item}",
                "account_id": account_id,
                "item_id": item_id,
                "item_name": "Unknown",
                "amount_added": 0,
                "total_amount": 0,
            }

        try:
            with Session(self.engine) as session:
                # Check if account exists
                account = session.get(Account, account_id)
                if not account:
                    return {
                        "success": False,
                        "message": f"Account {account_id} does not exist",
                        "account_id": account_id,
                        "item_id": item_id,
                        "item_name": "Unknown",
                        "amount_added": 0,
                        "total_amount": 0,
                    }

                # Check if item exists
                item = session.get(Item, item_id)
                if not item:
                    return {
                        "success": False,
                        "message": f"Item {item_id} does not exist",
                        "account_id": account_id,
                        "item_id": item_id,
                        "item_name": "Unknown",
                        "amount_added": 0,
                        "total_amount": 0,
                    }

                # Check if account already has this item
                existing_item = (
                    session.query(AccountItem)
                    .filter_by(account_id=account_id, item_id=item_id)
                    .first()
                )

                if existing_item:
                    # Update existing item amount
                    existing_item.amount += num_item
                    session.commit()
                    return {
                        "success": True,
                        "message": f"Added {num_item} {item.name}(s) to {account.name}'s inventory",
                        "account_id": account_id,
                        "item_id": item_id,
                        "item_name": item.name,
                        "amount_added": num_item,
                        "total_amount": existing_item.amount,
                    }
                else:
                    # Create new inventory entry
                    new_item = AccountItem(account_id=account_id, item_id=item_id, amount=num_item)
                    session.add(new_item)
                    session.commit()
                    return {
                        "success": True,
                        "message": f"Added {num_item} {item.name}(s) to {account.name}'s inventory",
                        "account_id": account_id,
                        "item_id": item_id,
                        "item_name": item.name,
                        "amount_added": num_item,
                        "total_amount": num_item,
                    }

        except IntegrityError as e:
            return {
                "success": False,
                "message": f"Database integrity error occurred: {str(e)}",
                "account_id": account_id,
                "item_id": item_id,
                "item_name": "Unknown",
                "amount_added": 0,
                "total_amount": 0,
            }

    def send_gacha_items_to_account(self, account_id: int) -> dict[str, Any]:
        """Send one of each gacha ticket to an account.

        Args:
            account_id (int): The account ID.

        Returns:
            dict[str, Any]: Dictionary with operation result.
        """
        gacha_item_ids = [1, 2, 3]  # Standard, Premium, Rare gacha tickets.
        num_item_to_add = 1  # Send one of each

        try:
            with Session(self.engine) as session:
                account = session.get(Account, account_id)
                if not account:
                    return {
                        "success": False,
                        "message": f"Account with id {account_id} not found.",
                    }

                items = session.query(Item).filter(Item.id.in_(gacha_item_ids)).all()
                if len(items) != len(gacha_item_ids):
                    found_item_ids = {item.id for item in items}
                    missing_item_ids = set(gacha_item_ids) - found_item_ids
                    return {
                        "success": False,
                        "message": f"Following gacha items do not exist: {list(missing_item_ids)}",
                    }

                results = []
                for item in items:
                    existing_item = (
                        session.query(AccountItem)
                        .filter_by(account_id=account_id, item_id=item.id)
                        .first()
                    )

                    if existing_item:
                        existing_item.amount += num_item_to_add
                        total_amount = existing_item.amount
                    else:
                        new_item = AccountItem(
                            account_id=account_id, item_id=item.id, amount=num_item_to_add
                        )
                        session.add(new_item)
                        total_amount = num_item_to_add

                    results.append(
                        {
                            "success": True,
                            "message": f"Added {num_item_to_add} {item.name}(s) to {account.name}'s inventory",
                            "account_id": account_id,
                            "item_id": item.id,
                            "item_name": item.name,
                            "amount_added": num_item_to_add,
                            "total_amount": total_amount,
                        }
                    )
                session.commit()
                return {"success": True, "details": results}

        except IntegrityError as e:
            return {
                "success": False,
                "message": f"Database integrity error occurred: {str(e)}",
            }

    def get_item(self, item_id: int) -> dict[str, Any]:
        """Retrieve an item by its ID.

        Args:
            item_id: The ID of the item to retrieve

        Returns:
            Dictionary with item data or error information
        """
        with Session(self.engine) as session:
            item = session.get(Item, item_id)
            if not item:
                return {
                    "success": False,
                    "message": f"Item {item_id} does not exist",
                    "id": item_id,
                    "name": None,
                }
            return {
                "success": True,
                "message": f"Item {item_id} retrieved successfully",
                "id": item.id,
                "name": item.name,
            }

    def get_account_item_amount(self, account_id: int, item_id: int) -> int:
        """Get the amount of a specific item in an account's inventory.

        Args:
            account_id: The ID of the account
            item_id: The ID of the item

        Returns:
            The amount of the item in the account's inventory (0 if not found)
        """
        with Session(self.engine) as session:
            account_item = (
                session.query(AccountItem).filter_by(account_id=account_id, item_id=item_id).first()
            )
            return account_item.amount if account_item else 0

    def remove_item_from_account(
        self, item_id: int, num_item: int, account_id: int
    ) -> dict[str, Any]:
        """Remove items from an account's inventory.

        Args:
            item_id: The ID of the item to remove
            num_item: The number of items to remove
            account_id: The ID of the account to remove items from

        Returns:
            Dictionary with operation result
        """
        if num_item <= 0:
            return {
                "success": False,
                "message": f"Invalid number of items to remove: {num_item}",
                "account_id": account_id,
                "item_id": item_id,
                "item_name": "Unknown",
                "amount_removed": 0,
                "total_amount": 0,
            }

        try:
            with Session(self.engine) as session:
                # Check if account exists
                account = session.get(Account, account_id)
                if not account:
                    return {
                        "success": False,
                        "message": f"Account {account_id} does not exist",
                        "account_id": account_id,
                        "item_id": item_id,
                        "item_name": "Unknown",
                        "amount_removed": 0,
                        "total_amount": 0,
                    }

                # Check if item exists
                item = session.get(Item, item_id)
                if not item:
                    return {
                        "success": False,
                        "message": f"Item {item_id} does not exist",
                        "account_id": account_id,
                        "item_id": item_id,
                        "item_name": "Unknown",
                        "amount_removed": 0,
                        "total_amount": 0,
                    }

                # Check if account has this item
                existing_item = (
                    session.query(AccountItem)
                    .filter_by(account_id=account_id, item_id=item_id)
                    .first()
                )

                if not existing_item:
                    return {
                        "success": False,
                        "message": f"Account {account.name} does not have any {item.name}(s) to remove",
                        "account_id": account_id,
                        "item_id": item_id,
                        "item_name": item.name,
                        "amount_removed": 0,
                        "total_amount": 0,
                    }

                if existing_item.amount < num_item:
                    return {
                        "success": False,
                        "message": f"Not enough {item.name}(s) to remove from {account.name}'s inventory. Has {existing_item.amount}, need {num_item}",
                        "account_id": account_id,
                        "item_id": item_id,
                        "item_name": item.name,
                        "amount_removed": 0,
                        "total_amount": existing_item.amount,
                    }

                if existing_item.amount == num_item:
                    # Remove the item entry completely
                    session.delete(existing_item)
                    session.commit()
                    return {
                        "success": True,
                        "message": f"Removed {num_item} {item.name}(s) from {account.name}'s inventory",
                        "account_id": account_id,
                        "item_id": item_id,
                        "item_name": item.name,
                        "amount_removed": num_item,
                        "total_amount": 0,
                    }
                else:
                    # Reduce the amount
                    existing_item.amount -= num_item
                    session.commit()
                    return {
                        "success": True,
                        "message": f"Removed {num_item} {item.name}(s) from {account.name}'s inventory",
                        "account_id": account_id,
                        "item_id": item_id,
                        "item_name": item.name,
                        "amount_removed": num_item,
                        "total_amount": existing_item.amount,
                    }

        except IntegrityError as e:
            return {
                "success": False,
                "message": f"Database integrity error occurred: {str(e)}",
                "account_id": account_id,
                "item_id": item_id,
                "item_name": "Unknown",
                "amount_removed": 0,
                "total_amount": 0,
            }

    def list_items(self) -> list[dict[str, Any]]:
        """List all items in the catalog.

        Returns:
            List of item data dictionaries
        """
        with Session(self.engine) as session:
            items = session.query(Item).all()
            return [{"id": item.id, "name": item.name} for item in items]
