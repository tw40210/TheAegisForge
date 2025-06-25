#!/usr/bin/env python3
"""
Simple script to clean up the database file.

Usage:
    python src/scripts/cleanup_db.py
"""

import os
from pathlib import Path


def main():
    """Remove the database file."""
    db_file = Path("game.db")

    if db_file.exists():
        os.remove(db_file)
        print("✓ Database file 'game.db' removed successfully!")
    else:
        print("ℹ Database file 'game.db' not found.")


if __name__ == "__main__":
    main()
