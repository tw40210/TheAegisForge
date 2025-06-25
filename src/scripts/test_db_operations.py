from src.py_libs.controllers.account_controller import AccountController


def main():
    """Test database operations."""
    print("=== Database Operations Test ===\n")

    controller = AccountController()

    # List all accounts
    accounts = controller.list_accounts()
    print(f"Found {len(accounts)} accounts:")
    for account in accounts:
        print(f"  - {account['name']} (ID: {account['id']})")

    # Test getting heroes for first account
    if accounts:
        heroes = controller.get_account_heroes(accounts[0]["id"])
        print(f"\nFound {len(heroes)} heroes for {accounts[0]['name']}:")
        for hero in heroes:
            print(f"  - {hero['name']} (Level {hero['level']})")

    # Test getting inventory for first account
    if accounts:
        inventory = controller.get_account_inventory(accounts[0]["id"])
        print(f"\nFound {len(inventory)} inventory items for {accounts[0]['name']}:")
        for item in inventory:
            print(f"  - {item['name']} (x{item['amount']})")


if __name__ == "__main__":
    main()
