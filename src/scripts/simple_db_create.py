import sys

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


def create_database():
    """Create the database schema."""
    print("Creating database schema...")
    Base.metadata.create_all(engine)
    print("✓ Database schema created successfully!")


def populate_sample_data():
    """Populate the database with sample data."""
    print("\nPopulating database with sample data...")

    with Session(engine) as session:
        # Create sample items
        items = [
            Item(id=1, name="Health Potion"),
            Item(id=2, name="Mana Potion"),
            Item(id=3, name="Iron Sword"),
            Item(id=4, name="Leather Armor"),
            Item(id=5, name="Magic Ring"),
            Item(id=6, name="Gold Coin"),
            Item(id=7, name="Fire Scroll"),
            Item(id=8, name="Healing Crystal"),
        ]
        session.add_all(items)

        # Create sample accounts
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
            Account(name="TestUser", stories=[], status="inactive", party_sets=[]),
        ]
        session.add_all(accounts)
        session.commit()

        # Create sample heroes
        heroes = [
            Hero(account_id=1, name="Aragorn", level=15),
            Hero(account_id=1, name="Gandalf", level=20),
            Hero(account_id=2, name="Legolas", level=12),
            Hero(account_id=3, name="Gimli", level=8),
        ]
        session.add_all(heroes)
        session.commit()

        # Create sample trait sets and traits
        trait_sets = [
            HeroTraitSet(hero_id=1, slot=0),  # Aragorn's primary trait set
            HeroTraitSet(hero_id=1, slot=1),  # Aragorn's secondary trait set
            HeroTraitSet(hero_id=2, slot=0),  # Gandalf's trait set
            HeroTraitSet(hero_id=3, slot=0),  # Legolas's trait set
        ]
        session.add_all(trait_sets)
        session.commit()

        # Create sample traits
        traits = [
            # Aragorn's primary traits
            HeroTrait(trait_set_id=1, slot=0, trait_id=101, trait_level=3),  # Leadership
            HeroTrait(trait_set_id=1, slot=1, trait_id=102, trait_level=2),  # Sword Mastery
            HeroTrait(trait_set_id=1, slot=2, trait_id=103, trait_level=1),  # Endurance
            # Aragorn's secondary traits
            HeroTrait(trait_set_id=2, slot=0, trait_id=201, trait_level=2),  # Stealth
            HeroTrait(trait_set_id=2, slot=1, trait_id=202, trait_level=1),  # Tracking
            # Gandalf's traits
            HeroTrait(trait_set_id=3, slot=0, trait_id=301, trait_level=5),  # Magic Mastery
            HeroTrait(trait_set_id=3, slot=1, trait_id=302, trait_level=3),  # Wisdom
            HeroTrait(trait_set_id=3, slot=2, trait_id=303, trait_level=2),  # Fire Magic
            # Legolas's traits
            HeroTrait(trait_set_id=4, slot=0, trait_id=401, trait_level=4),  # Archery
            HeroTrait(trait_set_id=4, slot=1, trait_id=402, trait_level=2),  # Agility
        ]
        session.add_all(traits)

        # Create sample account inventory items
        account_items = [
            AccountItem(account_id=1, item_id=1, amount=10),  # Player1: 10 Health Potions
            AccountItem(account_id=1, item_id=2, amount=5),  # Player1: 5 Mana Potions
            AccountItem(account_id=1, item_id=6, amount=1000),  # Player1: 1000 Gold Coins
            AccountItem(account_id=2, item_id=1, amount=3),  # Player2: 3 Health Potions
            AccountItem(account_id=2, item_id=7, amount=2),  # Player2: 2 Fire Scrolls
            AccountItem(account_id=3, item_id=8, amount=1),  # TestUser: 1 Healing Crystal
        ]
        session.add_all(account_items)

        # Create sample hero equipment
        hero_items = [
            HeroItem(hero_id=1, item_id=3, amount=1),  # Aragorn: Iron Sword
            HeroItem(hero_id=1, item_id=4, amount=1),  # Aragorn: Leather Armor
            HeroItem(hero_id=2, item_id=5, amount=1),  # Gandalf: Magic Ring
            HeroItem(hero_id=3, item_id=3, amount=1),  # Legolas: Iron Sword
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


def main():
    """Main function to create and populate the database."""
    print("=== Local Database Setup Script ===\n")

    try:
        # Create database schema
        create_database()

        # Populate with sample data
        populate_sample_data()

        # Verify the setup
        verify_database()

        print("\n=== Database Setup Complete! ===")
        print("Database file: game.db")
        print("You can now use the AccountController for testing.")

    except Exception as e:
        print(f"\n❌ Error during database setup: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
