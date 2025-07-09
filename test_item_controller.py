#!/usr/bin/env python3
"""Test script to demonstrate ItemController functionality."""

from src.py_libs.controllers.account_controller import AccountController
from src.py_libs.controllers.item_controller import ItemController


def main():
    """Test the ItemController send_item_to_account functionality."""
    print("=== Testing ItemController ===\n")

    # Initialize controllers
    item_controller = ItemController()
    account_controller = AccountController()

    # List available accounts
    accounts = account_controller.list_accounts()
    print("Available accounts:")
    for account in accounts:
        print(f"  - {account['name']} (ID: {account['id']})")

    # List available items
    items = item_controller.list_items()
    print("\nAvailable items:")
    for item in items:
        print(f"  - {item['name']} (ID: {item['id']})")

    if not accounts or not items:
        print("\nNo accounts or items found. Please run the database setup script first.")
        return

    # Test sending items to an account
    account_id = accounts[0]["id"]
    item_id = items[0]["id"]
    num_items = 5

    print(f"\n--- Testing: Send {num_items} {items[0]['name']}(s) to {accounts[0]['name']} ---")

    # Check current inventory before
    current_amount = item_controller.get_account_item_amount(account_id, item_id)
    print(f"Current amount: {current_amount}")

    # Send items
    result = item_controller.send_item_to_account(item_id, num_items, account_id)
    if result["success"]:
        print(f"✓ Success: {result['message']}")
        print(f"  Amount added: {result['amount_added']}")
        print(f"  Total amount now: {result['total_amount']}")
    else:
        print(f"✗ Failed to send items: {result['message']}")

    # Verify by checking inventory again
    new_amount = item_controller.get_account_item_amount(account_id, item_id)
    print(f"Verified new amount: {new_amount}")

    # Test sending more of the same item (should update existing entry)
    print(
        f"\n--- Testing: Send {num_items} more {items[0]['name']}(s) to {accounts[0]['name']} ---"
    )
    result2 = item_controller.send_item_to_account(item_id, num_items, account_id)
    if result2["success"]:
        print(f"✓ Success: {result2['message']}")
        print(f"  Amount added: {result2['amount_added']}")
        print(f"  Total amount now: {result2['total_amount']}")
    else:
        print(f"✗ Failed to send more items: {result2['message']}")

    # Test sending gacha items to an account
    print(f"\n--- Testing: Send gacha items to {accounts[0]['name']} ---")
    gacha_result = item_controller.send_gacha_items_to_account(account_id)
    if gacha_result and gacha_result.get("success"):
        print("✓ Success: Gacha items sent successfully.")
        for detail in gacha_result.get("details", []):
            print(f"  - {detail['message']}")
    else:
        print(f"✗ Failed to send gacha items: {gacha_result.get('message')}")

    # Test error cases
    print("\n--- Testing Error Cases ---")

    # Test invalid account ID
    result_error1 = item_controller.send_item_to_account(item_id, num_items, 99999)
    print(
        f"Invalid account ID: {'Failed as expected' if not result_error1['success'] else 'Unexpected success'}"
    )

    # Test invalid item ID
    result_error2 = item_controller.send_item_to_account(99999, num_items, account_id)
    print(
        f"Invalid item ID: {'Failed as expected' if not result_error2['success'] else 'Unexpected success'}"
    )

    # Test invalid number of items
    result_error3 = item_controller.send_item_to_account(item_id, -5, account_id)
    print(
        f"Negative items: {'Failed as expected' if not result_error3['success'] else 'Unexpected success'}"
    )

    # Show final inventory state
    print(f"\n--- Final Inventory for {accounts[0]['name']} ---")
    inventory = account_controller.get_account_inventory(account_id)
    for item in inventory:
        print(f"  - {item['name']}: {item['amount']}")


if __name__ == "__main__":
    main()
