"""Account controller for managing user accounts in the database."""

from __future__ import annotations

from typing import Any

from firebase_admin import auth
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.py_libs.controllers.sql_db_controller import Account, engine


class InvalidTokenError(Exception):
    """Raised when an invalid ID token is provided."""

    pass


class AccountController:
    """Controller for managing account operations in the database."""

    def __init__(self):
        """Initialize the account controller."""
        self.engine = engine

    def create_account(
        self,
        id_token: str,
    ) -> dict[str, Any] | None:
        """Create a new account in the database.

        Args:
            id_token: Firebase ID token to decode for user information

        Returns:
            Dictionary with account data if successful, None if creation fails

        Raises:
            InvalidTokenError: If the provided ID token is invalid
        """
        # Decode the Firebase ID token
        try:
            decoded = auth.verify_id_token(id_token)
        except Exception as e:
            raise InvalidTokenError("Invalid ID token") from e

        uid = decoded["uid"]
        email = decoded.get("email")
        user_name = decoded.get("name")

        # Use user_name from Firebase token as the account name
        # If no name is available, fall back to email or UID
        account_name = user_name or email or uid

        try:
            with Session(self.engine) as session:
                account = Account(
                    name=account_name,
                    firebaseUID=uid,
                    email=email,
                    user_name=user_name,
                    stories=[],
                    status="active",
                    party_sets=[],
                )
                session.add(account)
                session.commit()
                return {
                    "id": account.id,
                    "name": account.name,
                    "firebaseUID": account.firebaseUID,
                    "email": account.email,
                    "user_name": account.user_name,
                    "stories": account.stories,
                    "status": account.status,
                    "party_sets": account.party_sets,
                }
        except IntegrityError:
            return None

    def get_account(self, account_id: int) -> dict[str, Any] | None:
        """Retrieve an account by its ID.

        Args:
            account_id: The ID of the account to retrieve

        Returns:
            Dictionary with account data if found, None otherwise
        """
        with Session(self.engine) as session:
            account = session.get(Account, account_id)
            if not account:
                return None
            return {
                "id": account.id,
                "name": account.name,
                "firebaseUID": account.firebaseUID,
                "email": account.email,
                "user_name": account.user_name,
                "stories": account.stories,
                "status": account.status,
                "party_sets": account.party_sets,
            }

    def get_account_by_name(self, name: str) -> dict[str, Any] | None:
        """Retrieve an account by its name.

        Args:
            name: The name of the account to retrieve

        Returns:
            Dictionary with account data if found, None otherwise
        """
        with Session(self.engine) as session:
            account = session.query(Account).filter(Account.name == name).first()
            if not account:
                return None
            return {
                "id": account.id,
                "name": account.name,
                "firebaseUID": account.firebaseUID,
                "email": account.email,
                "user_name": account.user_name,
                "stories": account.stories,
                "status": account.status,
                "party_sets": account.party_sets,
            }

    def get_account_by_firebase_uid(self, firebase_uid: str) -> dict[str, Any] | None:
        """Retrieve an account by its Firebase UID.

        Args:
            firebase_uid: The Firebase UID of the account to retrieve

        Returns:
            Dictionary with account data if found, None otherwise
        """
        with Session(self.engine) as session:
            account = session.query(Account).filter(Account.firebaseUID == firebase_uid).first()
            if not account:
                return None
            return {
                "id": account.id,
                "name": account.name,
                "firebaseUID": account.firebaseUID,
                "email": account.email,
                "user_name": account.user_name,
                "stories": account.stories,
                "status": account.status,
                "party_sets": account.party_sets,
            }

    def update_account(self, account_id: int, **kwargs) -> bool:
        """Update an existing account's attributes.

        Args:
            account_id: The ID of the account to update
            **kwargs: The attributes to update and their new values

        Returns:
            True if update was successful, False otherwise
        """
        try:
            with Session(self.engine) as session:
                account = session.get(Account, account_id)
                if not account:
                    return False

                for key, value in kwargs.items():
                    if hasattr(account, key):
                        setattr(account, key, value)

                session.commit()
                return True
        except IntegrityError:
            return False

    def delete_account(self, account_id: int) -> bool:
        """Delete an account from the database.

        Args:
            account_id: The ID of the account to delete

        Returns:
            True if deletion was successful, False otherwise
        """
        with Session(self.engine) as session:
            account = session.get(Account, account_id)
            if not account:
                return False

            session.delete(account)
            session.commit()
            return True

    def list_accounts(self) -> list[dict[str, Any]]:
        """List all accounts in the database.

        Returns:
            List of account data dictionaries
        """
        with Session(self.engine) as session:
            accounts = session.query(Account).all()
            return [
                {
                    "id": account.id,
                    "name": account.name,
                    "firebaseUID": account.firebaseUID,
                    "email": account.email,
                    "user_name": account.user_name,
                    "stories": account.stories,
                    "status": account.status,
                    "party_sets": account.party_sets,
                }
                for account in accounts
            ]

    def get_account_heroes(self, account_id: int) -> list[dict[str, Any]]:
        """Get all heroes associated with an account.

        Args:
            account_id: The ID of the account

        Returns:
            List of hero data dictionaries
        """
        with Session(self.engine) as session:
            account = session.get(Account, account_id)
            if not account:
                return []

            return [
                {
                    "id": hero.id,
                    "hero_index": hero.hero_index,
                    "name": hero.name,
                    "level": hero.level,
                    "rarity": hero.rarity,
                    "amount": hero.amount,
                    "trait_sets": [
                        {
                            "slot": trait_set.slot,
                            "traits": [
                                {
                                    "slot": trait.slot,
                                    "trait_id": trait.trait_id,
                                    "trait_level": trait.trait_level,
                                }
                                for trait in trait_set.traits
                            ],
                        }
                        for trait_set in hero.trait_sets
                    ],
                }
                for hero in account.heroes
            ]

    def get_account_inventory(self, account_id: int) -> list[dict[str, Any]]:
        """Get all items in an account's inventory.

        Args:
            account_id: The ID of the account

        Returns:
            List of inventory item data dictionaries
        """
        with Session(self.engine) as session:
            account = session.get(Account, account_id)
            if not account:
                return []

            return [
                {"item_id": item.item_id, "name": item.item.name, "amount": item.amount}
                for item in account.inventory
            ]
