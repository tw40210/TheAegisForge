"""Unit tests for the SQLite database controller."""

import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.py_libs.controllers.sql_db_controller import (
    Account,
    AccountItem,
    Base,
    Hero,
    HeroItem,
    HeroTrait,
    HeroTraitSet,
    Item,
)

# Test database URL
TEST_DB_URL = "sqlite:///test_game.db"


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test."""
    # Create test database
    engine = create_engine(TEST_DB_URL, echo=False)
    Base.metadata.create_all(engine)

    # Create session
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()
        # Clean up test database
        Base.metadata.drop_all(engine)
        if os.path.exists("test_game.db"):
            os.remove("test_game.db")


def test_create_account(db_session):
    """Test creating a new account."""
    account = Account(
        name="test_player",
        stories=["story1", "story2"],
        status="active",
        party_sets=["party1", "party2"],
    )
    db_session.add(account)
    db_session.commit()

    # Verify account was created
    saved_account = db_session.query(Account).filter_by(name="test_player").first()
    assert saved_account is not None
    assert saved_account.name == "test_player"
    assert saved_account.stories == ["story1", "story2"]
    assert saved_account.status == "active"
    assert saved_account.party_sets == ["party1", "party2"]


def test_create_hero(db_session):
    """Test creating a hero for an account."""
    # Create account first
    account = Account(name="test_player")
    db_session.add(account)
    db_session.commit()

    # Create hero
    hero = Hero(account_id=account.id, name="test_hero", level=5)
    db_session.add(hero)
    db_session.commit()

    # Verify hero was created
    saved_hero = db_session.query(Hero).filter_by(name="test_hero").first()
    assert saved_hero is not None
    assert saved_hero.name == "test_hero"
    assert saved_hero.level == 5
    assert saved_hero.account_id == account.id


def test_hero_trait_sets(db_session):
    """Test creating and managing hero trait sets."""
    # Create account and hero
    account = Account(name="test_player")
    db_session.add(account)
    db_session.commit()

    hero = Hero(account_id=account.id, name="test_hero")
    db_session.add(hero)
    db_session.commit()

    # Create trait set
    trait_set = HeroTraitSet(hero_id=hero.id, slot=0)
    db_session.add(trait_set)
    db_session.commit()

    # Add traits to the set
    trait1 = HeroTrait(trait_set_id=trait_set.id, slot=0, trait_id=1, trait_level=2)
    trait2 = HeroTrait(trait_set_id=trait_set.id, slot=1, trait_id=2, trait_level=3)
    db_session.add_all([trait1, trait2])
    db_session.commit()

    # Verify trait set and traits
    saved_trait_set = db_session.query(HeroTraitSet).filter_by(hero_id=hero.id).first()
    assert saved_trait_set is not None
    assert len(saved_trait_set.traits) == 2
    assert saved_trait_set.traits[0].trait_id == 1
    assert saved_trait_set.traits[1].trait_id == 2


def test_inventory_management(db_session):
    """Test managing account and hero inventory."""
    # Create account and hero
    account = Account(name="test_player")
    db_session.add(account)
    db_session.commit()

    hero = Hero(account_id=account.id, name="test_hero")
    db_session.add(hero)
    db_session.commit()

    # Create items
    item1 = Item(id=1, name="Sword")
    item2 = Item(id=2, name="Shield")
    db_session.add_all([item1, item2])
    db_session.commit()

    # Add items to account inventory
    account_item = AccountItem(account_id=account.id, item_id=1, amount=5)
    db_session.add(account_item)
    db_session.commit()

    # Add items to hero inventory
    hero_item = HeroItem(hero_id=hero.id, item_id=2, amount=1)
    db_session.add(hero_item)
    db_session.commit()

    # Verify inventories
    saved_account_item = db_session.query(AccountItem).filter_by(account_id=account.id).first()
    assert saved_account_item is not None
    assert saved_account_item.amount == 5
    assert saved_account_item.item.name == "Sword"

    saved_hero_item = db_session.query(HeroItem).filter_by(hero_id=hero.id).first()
    assert saved_hero_item is not None
    assert saved_hero_item.amount == 1
    assert saved_hero_item.item.name == "Shield"


def test_cascade_deletion(db_session):
    """Test cascade deletion of related records."""
    # Create account with hero and inventory
    account = Account(name="test_player")
    db_session.add(account)
    db_session.commit()

    hero = Hero(account_id=account.id, name="test_hero")
    db_session.add(hero)
    db_session.commit()

    item = Item(id=1, name="Test Item")
    db_session.add(item)
    db_session.commit()

    account_item = AccountItem(account_id=account.id, item_id=1)
    hero_item = HeroItem(hero_id=hero.id, item_id=1)
    db_session.add_all([account_item, hero_item])
    db_session.commit()

    # Delete account and verify cascade
    db_session.delete(account)
    db_session.commit()

    # Verify all related records are deleted
    assert db_session.query(Hero).filter_by(account_id=account.id).first() is None
    assert db_session.query(AccountItem).filter_by(account_id=account.id).first() is None
    assert db_session.query(HeroItem).filter_by(hero_id=hero.id).first() is None


def test_unique_constraints(db_session):
    """Test unique constraints on tables."""
    # Test account name uniqueness
    account1 = Account(name="test_player")
    db_session.add(account1)
    db_session.commit()

    account2 = Account(name="test_player")
    db_session.add(account2)
    with pytest.raises(IntegrityError, match="UNIQUE constraint failed: accounts.name"):
        db_session.commit()
    db_session.rollback()

    # Test hero trait set slot uniqueness
    hero = Hero(account_id=account1.id, name="test_hero")
    db_session.add(hero)
    db_session.commit()

    trait_set1 = HeroTraitSet(hero_id=hero.id, slot=0)
    db_session.add(trait_set1)
    db_session.commit()

    trait_set2 = HeroTraitSet(hero_id=hero.id, slot=0)
    db_session.add(trait_set2)
    with pytest.raises(
        IntegrityError,
        match="UNIQUE constraint failed: hero_trait_sets.hero_id, hero_trait_sets.slot",
    ):
        db_session.commit()
