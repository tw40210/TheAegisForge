# Database Setup Scripts

This directory contains scripts for quickly setting up and testing a local database for offline development.

## Files

- `simple_db_create.py` - Creates the database schema and populates it with sample data
- `test_db_operations.py` - Demonstrates how to use the AccountController to interact with the database
- `cleanup_db.py` - Removes the database file for fresh starts

## Quick Start

1. **Create the database with sample data:**
   ```bash
   python src/scripts/simple_db_create.py
   ```

2. **Test database operations:**
   ```bash
   python src/scripts/test_db_operations.py
   ```

3. **Clean up (optional):**
   ```bash
   python src/scripts/cleanup_db.py
   ```

## What the Setup Script Does

The `simple_db_create.py` script:

1. **Creates the database schema** - Sets up all tables defined in `sql_db_controller.py`
2. **Populates sample data** including:
   - 3 sample accounts (Player1, Player2, TestUser)
   - 4 heroes (Aragorn, Gandalf, Legolas, Gimli)
   - 8 different items (Health Potion, Iron Sword, etc.)
   - Trait sets and traits for heroes
   - Inventory items for accounts
   - Equipment for heroes

3. **Verifies the setup** by running basic queries

## Database File

The script creates a `game.db` SQLite file in the current working directory.

## Sample Data Overview

### Accounts
- **Player1**: Active account with 2 heroes, multiple stories, and party sets
- **Player2**: Active account with 1 hero and some stories
- **TestUser**: Inactive account with no heroes

### Heroes
- **Aragorn** (Level 15): Has 2 trait sets with various traits
- **Gandalf** (Level 20): Has 1 trait set with magic-related traits
- **Legolas** (Level 12): Has 1 trait set with archery traits
- **Gimli** (Level 8): Basic hero

### Items
- Health Potion, Mana Potion, Iron Sword, Leather Armor
- Magic Ring, Gold Coin, Fire Scroll, Healing Crystal

## Using the AccountController

After running the setup script, you can use the `AccountController` class to:

```python
from py_libs.controllers.account_controller import AccountController

controller = AccountController()

# List all accounts
accounts = controller.list_accounts()

# Get account by name
account = controller.get_account_by_name("Player1")

# Get heroes for an account
heroes = controller.get_account_heroes(account_id)

# Get inventory for an account
inventory = controller.get_account_inventory(account_id)

# Create a new account
new_account = controller.create_account(name="NewPlayer", status="active")
```

## Troubleshooting

- If you get import errors, make sure you're running the script from the project root directory
- If the database already exists, the script will add sample data to the existing database
- The script uses SQLite, so no additional database server setup is required 