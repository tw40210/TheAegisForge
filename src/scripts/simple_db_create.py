import sys
from pathlib import Path

import yaml
from sqlalchemy.orm import Session

from src.py_libs.controllers.account_controller import AccountController
from src.py_libs.controllers.sql_db_controller import (
    Account,
    AccountItem,
    Base,
    Hero,
    HeroItem,
    HeroTrait,
    HeroTraitSet,
    Item,
    engine,
)


def load_config_file(config_path: str) -> dict:
    """Load a YAML configuration file."""
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_file, encoding="utf-8") as file:
        return yaml.safe_load(file)


def create_database():
    """Create the database schema."""
    print("Creating database schema...")
    Base.metadata.create_all(engine)
    print("✓ Database schema created successfully!")


def populate_items_from_config():
    """Populate items table from items.yaml configuration."""
    print("\nLoading items from configuration...")

    try:
        items_config = load_config_file("src/config/items.yaml")

        with Session(engine) as session:
            items_data = items_config.get("items", {})
            items_to_add = []

            for item_data in items_data.values():
                item = Item(id=item_data["id"], name=item_data["name"])
                items_to_add.append(item)

            session.add_all(items_to_add)
            session.commit()

            print(f"✓ Added {len(items_to_add)} items from configuration")

    except Exception as e:
        print(f"⚠️  Warning: Could not load items config: {e}")
        print("   Creating basic sample items instead...")

        # Fallback to basic items if config loading fails
        with Session(engine) as session:
            items = [
                Item(id=1, name="Standard Gacha Ticket"),
                Item(id=2, name="Premium Gacha Ticket"),
                Item(id=3, name="Rare Gacha Ticket"),
                Item(id=4, name="Gold Coins"),
                Item(id=5, name="Gems"),
                Item(id=11, name="Iron Sword"),
                Item(id=31, name="Leather Armor"),
                Item(id=51, name="Health Potion"),
            ]
            session.add_all(items)
            session.commit()
            print("✓ Created basic sample items")


def populate_sample_data():
    """Populate the database with sample accounts and heroes."""
    print("\nPopulating database with sample data...")

    with Session(engine) as session:
        # Create sample accounts with gacha tickets and starter items
        accounts = [
            Account(
                name="Player1",
                stories=[{"chapter": 1, "completed": True}, {"chapter": 2, "completed": False}],
                status="active",
                party_sets=[{"name": "Main Party", "heroes": [1, 2]}],
            ),
            Account(
                name="Player2",
                stories=[{"chapter": 1, "completed": True}],
                status="active",
                party_sets=[{"name": "Adventure Party", "heroes": [3]}],
            ),
            Account(
                name="NewPlayer",
                stories=[],
                status="active",
                party_sets=[],
            ),
        ]
        session.add_all(accounts)
        session.commit()

        # Create sample heroes using names from the hero config
        try:
            heroes_config = load_config_file("src/config/heroes.yaml")
            hero_data = heroes_config.get("heroes", {})
            hero_names = [
                hero_info.get("name", f"Hero {hero_id}") for hero_id, hero_info in hero_data.items()
            ]
        except Exception:
            hero_names = ["Knight", "Archer", "Mage", "Fire Mage"]

        heroes = [
            Hero(account_id=1, name=hero_names[0] if len(hero_names) > 0 else "Knight", level=15),
            Hero(account_id=1, name=hero_names[1] if len(hero_names) > 1 else "Archer", level=20),
            Hero(account_id=2, name=hero_names[2] if len(hero_names) > 2 else "Mage", level=12),
            Hero(account_id=3, name=hero_names[3] if len(hero_names) > 3 else "Fire Mage", level=8),
        ]
        session.add_all(heroes)
        session.commit()

        # Create sample trait sets and traits
        trait_sets = [
            HeroTraitSet(hero_id=1, slot=0),  # First hero's primary trait set
            HeroTraitSet(hero_id=1, slot=1),  # First hero's secondary trait set
            HeroTraitSet(hero_id=2, slot=0),  # Second hero's trait set
            HeroTraitSet(hero_id=3, slot=0),  # Third hero's trait set
        ]
        session.add_all(trait_sets)
        session.commit()

        # Create sample traits using trait IDs from config
        try:
            traits_config = load_config_file("src/config/herotraits.yaml")
            trait_ids = list(traits_config.get("hero_traits", {}).keys())
            trait_ids = [int(tid) for tid in trait_ids[:10]]  # Use first 10 trait IDs
        except Exception:
            trait_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]  # Fallback trait IDs

        traits = [
            # First hero's primary traits
            HeroTrait(trait_set_id=1, slot=0, trait_id=trait_ids[0], trait_level=3),
            HeroTrait(trait_set_id=1, slot=1, trait_id=trait_ids[1], trait_level=2),
            HeroTrait(trait_set_id=1, slot=2, trait_id=trait_ids[2], trait_level=1),
            # First hero's secondary traits
            HeroTrait(trait_set_id=2, slot=0, trait_id=trait_ids[3], trait_level=2),
            HeroTrait(trait_set_id=2, slot=1, trait_id=trait_ids[4], trait_level=1),
            # Second hero's traits
            HeroTrait(trait_set_id=3, slot=0, trait_id=trait_ids[5], trait_level=5),
            HeroTrait(trait_set_id=3, slot=1, trait_id=trait_ids[6], trait_level=3),
            HeroTrait(trait_set_id=3, slot=2, trait_id=trait_ids[7], trait_level=2),
            # Third hero's traits
            HeroTrait(trait_set_id=4, slot=0, trait_id=trait_ids[8], trait_level=4),
            HeroTrait(trait_set_id=4, slot=1, trait_id=trait_ids[9], trait_level=2),
        ]
        session.add_all(traits)

        # Create sample account inventory items with gacha tickets and resources
        account_items = [
            # Player1: Well-established player with resources
            AccountItem(account_id=1, item_id=1, amount=20),  # Standard Gacha Tickets
            AccountItem(account_id=1, item_id=2, amount=5),  # Premium Gacha Tickets
            AccountItem(account_id=1, item_id=3, amount=1),  # Rare Gacha Ticket
            AccountItem(account_id=1, item_id=4, amount=50000),  # Gold Coins
            AccountItem(account_id=1, item_id=5, amount=1000),  # Gems
            AccountItem(account_id=1, item_id=51, amount=25),  # Health Potions
            # Player2: Moderate player
            AccountItem(account_id=2, item_id=1, amount=10),  # Standard Gacha Tickets
            AccountItem(account_id=2, item_id=2, amount=2),  # Premium Gacha Tickets
            AccountItem(account_id=2, item_id=4, amount=15000),  # Gold Coins
            AccountItem(account_id=2, item_id=5, amount=250),  # Gems
            AccountItem(account_id=2, item_id=51, amount=10),  # Health Potions
            # NewPlayer: Starting resources
            AccountItem(account_id=3, item_id=1, amount=5),  # Standard Gacha Tickets
            AccountItem(account_id=3, item_id=4, amount=1000),  # Gold Coins
            AccountItem(account_id=3, item_id=5, amount=100),  # Gems
            AccountItem(account_id=3, item_id=51, amount=5),  # Health Potions
        ]
        session.add_all(account_items)

        # Create sample hero equipment
        hero_items = [
            HeroItem(hero_id=1, item_id=11, amount=1),  # First hero: Iron Sword
            HeroItem(hero_id=1, item_id=31, amount=1),  # First hero: Leather Armor
            HeroItem(hero_id=2, item_id=11, amount=1),  # Second hero: Iron Sword
            HeroItem(hero_id=3, item_id=11, amount=1),  # Third hero: Iron Sword
        ]
        session.add_all(hero_items)

        session.commit()

    print("✓ Sample data populated successfully!")


def verify_database():
    """Verify the database was created correctly."""
    print("\nVerifying database contents...")

    controller = AccountController()

    # List all accounts
    accounts = controller.list_accounts()
    print(f"✓ Found {len(accounts)} accounts:")
    for account in accounts:
        print(f"  - {account['name']} (ID: {account['id']}, Status: {account['status']})")

    # Get heroes for first account
    if accounts:
        heroes = controller.get_account_heroes(accounts[0]["id"])
        print(f"\n✓ Found {len(heroes)} heroes for {accounts[0]['name']}:")
        for hero in heroes:
            print(f"  - {hero['name']} (Level {hero['level']})")
            print(f"    Trait sets: {len(hero['trait_sets'])}")

    # Get inventory for first account
    if accounts:
        inventory = controller.get_account_inventory(accounts[0]["id"])
        print(f"\n✓ Found {len(inventory)} inventory items for {accounts[0]['name']}:")
        for item in inventory:
            print(f"  - {item['name']} (x{item['amount']})")

    # Show total items in database
    with Session(engine) as session:
        total_items = session.query(Item).count()
        print(f"\n✓ Total items in database: {total_items}")


def main():
    """Main function to create and populate the database."""
    print("=== Enhanced Database Setup Script ===\n")
    print("This script will create a comprehensive game database using")
    print("configuration files for items, heroes, and traits.\n")

    try:
        # Create database schema
        create_database()

        # Populate items from configuration
        populate_items_from_config()

        # Populate with sample data
        populate_sample_data()

        # Verify the setup
        verify_database()

        print("\n=== Database Setup Complete! ===")
        print("Database file: game.db")
        print("✓ All items loaded from configuration")
        print("✓ Sample accounts created with gacha tickets")
        print("✓ Sample heroes with traits and equipment")
        print("You can now use the GachaController and other controllers for testing.")

    except Exception as e:
        print(f"\n❌ Error during database setup: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
