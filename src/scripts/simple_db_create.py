import json
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
    Question,
    Summary,
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
        heroes_config = load_config_file("src/config/heroes.yaml")
        hero_data = heroes_config.get("heroes", {})
        hero_names = [
            hero_info.get("name", f"Hero {hero_id}") for hero_id, hero_info in hero_data.items()
        ]

        # Extract rarity information for the first few heroes
        hero_rarities = []
        for _, hero_info in list(hero_data.items())[:4]:
            hero_rarities.append(hero_info.get("rarity", "Common"))

        heroes = [
            Hero(account_id=1, hero_index=1, name=hero_names[0], level=15, rarity=hero_rarities[0]),
            Hero(account_id=1, hero_index=2, name=hero_names[1], level=20, rarity=hero_rarities[1]),
            Hero(account_id=2, hero_index=3, name=hero_names[2], level=12, rarity=hero_rarities[2]),
            Hero(account_id=3, hero_index=4, name=hero_names[3], level=8, rarity=hero_rarities[3]),
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
        traits_config = load_config_file("src/config/herotraits.yaml")
        trait_ids = list(traits_config.get("hero_traits", {}).keys())
        trait_ids = [int(tid) for tid in trait_ids[:10]]  # Use first 10 trait IDs

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


def populate_questions_from_data():
    """Populate questions table from output_question_data directory."""
    print("\nLoading questions from output_question_data...")

    questions_dir = Path("output_question_data")
    if not questions_dir.exists():
        print("⚠️  output_question_data directory not found, skipping questions")
        return

    with Session(engine) as session:
        questions_to_add = []
        question_count = 0

        # Iterate through each subdirectory
        for subdir in questions_dir.iterdir():
            if not subdir.is_dir():
                continue

            # Extract subdirectory identifier (number after last underscore)
            subdir_parts = subdir.name.split("_")
            try:
                subdir_id = int(subdir_parts[-1])
            except (ValueError, IndexError):
                print(f"⚠️  Skipping directory with invalid name format: {subdir.name}")
                continue

            # Find all question files (mc_question_*.json)
            for question_file in subdir.glob("mc_question_*.json"):
                # Parse filename to extract components
                # Format: mc_question_{summary_type}_{content_type}_{index}.json
                filename_parts = question_file.stem.split("_")
                if len(filename_parts) < 4:
                    print(f"⚠️  Skipping malformed question file: {question_file}")
                    continue

                question_type = filename_parts[0] + "_" + filename_parts[1]  # "mc_question"
                summary_type = filename_parts[2]  # e.g., "InnovationSummary"
                content_type = "_".join(filename_parts[3:-1])  # e.g., "innovation_points"
                file_index = int(filename_parts[-1])  # e.g., 0

                # Create globally unique index: subdir_id * 1000 + file_index
                index_number = subdir_id * 1000 + file_index

                try:
                    with open(question_file, encoding="utf-8") as f:
                        question_data = json.load(f)

                    # Create Question record
                    question = Question(
                        question_type=question_type,
                        summary_type=summary_type,
                        content_type=content_type,
                        index_number=index_number,
                        content=question_data,
                    )
                    questions_to_add.append(question)
                    question_count += 1

                except (json.JSONDecodeError, ValueError) as e:
                    print(f"⚠️  Error processing {question_file}: {e}")
                    continue

        session.add_all(questions_to_add)
        session.commit()

        print(
            f"✓ Added {question_count} questions from {len(list(questions_dir.iterdir()))} directories"
        )


def populate_summaries_from_data():
    """Populate summaries table from output_question_data directory."""
    print("\nLoading summaries from output_question_data...")

    summaries_dir = Path("output_question_data")
    if not summaries_dir.exists():
        print("⚠️  output_question_data directory not found, skipping summaries")
        return

    with Session(engine) as session:
        summaries_to_add = []
        summary_count = 0

        # Iterate through each subdirectory
        for subdir in summaries_dir.iterdir():
            if not subdir.is_dir():
                continue

            # Extract subdirectory identifier (number after last underscore)
            subdir_parts = subdir.name.split("_")
            try:
                subdir_id = int(subdir_parts[-1])
            except (ValueError, IndexError):
                print(f"⚠️  Skipping directory with invalid name format: {subdir.name}")
                continue

            # Find all summary files (summary_*.json)
            for summary_file in subdir.glob("summary_*.json"):
                # Parse filename to extract components
                # Format: summary_{summary_type}.json
                filename_parts = summary_file.stem.split("_", 1)
                if len(filename_parts) < 2:
                    print(f"⚠️  Skipping malformed summary file: {summary_file}")
                    continue

                summary_type = filename_parts[1]  # e.g., "InnovationSummary"

                try:
                    with open(summary_file, encoding="utf-8") as f:
                        summary_data = json.load(f)

                    # Determine content_type and index based on summary_type
                    # For most summaries, we'll use the summary_type as content_type
                    # Create globally unique index using subdirectory ID
                    content_type = summary_type.lower()  # e.g., "innovationsummary"
                    index_number = subdir_id * 1000  # Use subdir_id to make unique

                    # Create Summary record
                    summary = Summary(
                        summary_type=summary_type,
                        content_type=content_type,
                        index_number=index_number,
                        content=summary_data,
                    )
                    summaries_to_add.append(summary)
                    summary_count += 1

                except (json.JSONDecodeError, ValueError) as e:
                    print(f"⚠️  Error processing {summary_file}: {e}")
                    continue

        session.add_all(summaries_to_add)
        session.commit()

        print(
            f"✓ Added {summary_count} summaries from {len(list(summaries_dir.iterdir()))} directories"
        )


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
        total_questions = session.query(Question).count()
        total_summaries = session.query(Summary).count()
        print(f"\n✓ Total items in database: {total_items}")
        print(f"✓ Total questions in database: {total_questions}")
        print(f"✓ Total summaries in database: {total_summaries}")


def main():
    """Main function to create and populate the database."""
    print("=== Enhanced Database Setup Script ===\n")
    print("This script will create a comprehensive game database using")
    print("configuration files for items, heroes, traits, and question/summary data.\n")

    try:
        # Create database schema
        create_database()

        # Populate items from configuration
        populate_items_from_config()

        # Populate with sample data
        populate_sample_data()

        # Populate questions and summaries from output_question_data
        populate_questions_from_data()
        populate_summaries_from_data()

        # Verify the setup
        verify_database()

        print("\n=== Database Setup Complete! ===")
        print("Database file: game.db")
        print("✓ All items loaded from configuration")
        print("✓ Sample accounts created with gacha tickets")
        print("✓ Sample heroes with traits and equipment")
        print("✓ Questions and summaries loaded from output_question_data")
        print("You can now use the GachaController and other controllers for testing.")

    except Exception as e:
        print(f"\n❌ Error during database setup: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
