"""SQLAlchemy ORM schema for the game objects described in the prompt.
Compatible with SQLite and SQLAlchemy ≥2.0.

To generate the database:
    >>> from game_schema import Base, engine
    >>> Base.metadata.create_all(engine)
"""

from __future__ import annotations

from sqlalchemy import (
    JSON,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship

# ---------------------------------------------------------------------------
# Database engine / Base
# ---------------------------------------------------------------------------

engine = create_engine("sqlite:///game.db", echo=False, future=True)
Base = declarative_base()

# ---------------------------------------------------------------------------
# Core domain tables
# ---------------------------------------------------------------------------


class Account(Base):
    """Player account."""

    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    firebaseUID: Mapped[str | None] = mapped_column(String(128), unique=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    user_name: Mapped[str | None] = mapped_column(String(64))
    stories: Mapped[list | None] = mapped_column(
        JSON, default=list
    )  # general story data, see material_stories for progress tracking
    status: Mapped[str | None] = mapped_column(String(32))
    party_sets: Mapped[list | None] = mapped_column(JSON, default=list)

    # --- Relationships ------------------------------------------------------

    heroes: Mapped[list[Hero]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )
    inventory: Mapped[list[AccountItem]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )
    material_stories: Mapped[list[MaterialStory]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )

    # --- Dunder methods -----------------------------------------------------

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Account id={self.id} name={self.name!r}>"


class Hero(Base):
    """A hero belonging to an account."""

    __tablename__ = "heroes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    hero_index: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    rarity: Mapped[str | None] = mapped_column(String(32), default="Common")
    amount: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # --- Relationships ------------------------------------------------------

    account: Mapped[Account] = relationship(back_populates="heroes")
    trait_sets: Mapped[list[HeroTraitSet]] = relationship(
        back_populates="hero", cascade="all, delete-orphan"
    )
    equipment: Mapped[list[HeroItem]] = relationship(
        back_populates="hero", cascade="all, delete-orphan"
    )

    # --- Dunder methods -----------------------------------------------------

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<Hero id={self.id} name={self.name!r} lvl={self.level} hero_index={self.hero_index} "
            f"rarity={self.rarity!r} amount={self.amount}>"
        )


class HeroTraitSet(Base):
    """One of up to 6 trait‑loadouts for a hero (slots 0‑5)."""

    __tablename__ = "hero_trait_sets"
    __table_args__ = (UniqueConstraint("hero_id", "slot", name="uq_hero_trait_set_slot"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hero_id: Mapped[int] = mapped_column(ForeignKey("heroes.id"), nullable=False)
    slot: Mapped[int] = mapped_column(Integer, nullable=False)  # 0‑5

    # --- Relationships ------------------------------------------------------

    hero: Mapped[Hero] = relationship(back_populates="trait_sets")
    traits: Mapped[list[HeroTrait]] = relationship(
        back_populates="trait_set", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<HeroTraitSet hero={self.hero_id} slot={self.slot}>"


class HeroTrait(Base):
    """A single trait within a trait set (slots 0‑4)."""

    __tablename__ = "hero_traits"
    __table_args__ = (UniqueConstraint("trait_set_id", "slot", name="uq_traitset_slot"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trait_set_id: Mapped[int] = mapped_column(ForeignKey("hero_trait_sets.id"), nullable=False)
    slot: Mapped[int] = mapped_column(Integer, nullable=False)  # 0‑4
    trait_id: Mapped[int] = mapped_column(Integer, nullable=False)
    trait_level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # --- Relationships ------------------------------------------------------

    trait_set: Mapped[HeroTraitSet] = relationship(back_populates="traits")

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<HeroTrait set={self.trait_set_id} slot={self.slot} "
            f"trait={self.trait_id} lvl={self.trait_level}>"
        )


# ---------------------------------------------------------------------------
# Inventory tables
# ---------------------------------------------------------------------------


class Item(Base):
    """Static item catalog (optional)."""

    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str | None] = mapped_column(String(64))

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Item id={self.id} name={self.name!r}>"


class AccountItem(Base):
    """Items held directly in an account's inventory."""

    __tablename__ = "account_items"
    __table_args__ = (UniqueConstraint("account_id", "item_id", name="uq_account_item"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # --- Relationships ------------------------------------------------------

    account: Mapped[Account] = relationship(back_populates="inventory")
    item: Mapped[Item] = relationship()

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AccountItem acc={self.account_id} item={self.item_id} qty={self.amount}>"


class HeroItem(Base):
    """Items equipped or carried by a hero."""

    __tablename__ = "hero_items"
    __table_args__ = (UniqueConstraint("hero_id", "item_id", name="uq_hero_item"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hero_id: Mapped[int] = mapped_column(ForeignKey("heroes.id"), nullable=False)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # --- Relationships ------------------------------------------------------

    hero: Mapped[Hero] = relationship(back_populates="equipment")
    item: Mapped[Item] = relationship()

    def __repr__(self) -> str:  # pragma: no cover
        return f"<HeroItem hero={self.hero_id} item={self.item_id} qty={self.amount}>"


# ---------------------------------------------------------------------------
# Question and Summary tables
# ---------------------------------------------------------------------------


class Question(Base):
    """Questions with type categorization and JSON content."""

    __tablename__ = "questions"
    __table_args__ = (
        UniqueConstraint(
            "question_type",
            "summary_type",
            "content_type",
            "index_number",
            "material_name",
            name="uq_question_identifier",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question_type: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g., "mc_question"
    summary_type: Mapped[str] = mapped_column(
        String(128), nullable=False
    )  # e.g., "InnovationSummary"
    content_type: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # e.g., "innovation_points"
    index_number: Mapped[int] = mapped_column(Integer, nullable=False)  # e.g., 0
    material_name: Mapped[str] = mapped_column(
        String(255), nullable=False
    )  # folder name from output_question_data
    content: Mapped[dict] = mapped_column(JSON, nullable=False)  # JSON question content

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<Question id={self.id} type={self.question_type} "
            f"summary={self.summary_type} content={self.content_type} idx={self.index_number} "
            f"material={self.material_name}>"
        )


class Summary(Base):
    """Summaries with type categorization and JSON content."""

    __tablename__ = "summaries"
    __table_args__ = (
        UniqueConstraint(
            "summary_type",
            "content_type",
            "index_number",
            "material_name",
            name="uq_summary_identifier",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    summary_type: Mapped[str] = mapped_column(
        String(128), nullable=False
    )  # e.g., "InnovationSummary"
    content_type: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # e.g., "innovation_points"
    index_number: Mapped[int] = mapped_column(Integer, nullable=False)  # e.g., 0
    material_name: Mapped[str] = mapped_column(
        String(255), nullable=False
    )  # folder name from output_question_data
    content: Mapped[dict] = mapped_column(JSON, nullable=False)  # JSON summary content

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<Summary id={self.id} type={self.summary_type} "
            f"content={self.content_type} idx={self.index_number} "
            f"material={self.material_name}>"
        )


class QuestionSetResponse(Base):
    """Response data for a specific question set within a material."""

    __tablename__ = "question_set_responses"
    __table_args__ = (
        UniqueConstraint("material_story_id", "question_set_id", name="uq_material_question_set"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    material_story_id: Mapped[int] = mapped_column(
        ForeignKey("material_stories.id"), nullable=False
    )
    question_set_id: Mapped[str] = mapped_column(String(128), nullable=False)
    finish_times: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list
    )  # list of timestamps
    correct_rates: Mapped[list] = mapped_column(JSON, nullable=False, default=list)  # list of rates
    answers_list: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list
    )  # list of answer data

    # --- Relationships ------------------------------------------------------

    material_story: Mapped[MaterialStory] = relationship(back_populates="question_set_responses")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<QuestionSetResponse id={self.id} material_story={self.material_story_id} question_set={self.question_set_id!r}>"


class MaterialStory(Base):
    """Material progress logging with question set tracking."""

    __tablename__ = "material_stories"
    __table_args__ = (UniqueConstraint("account_id", "material_name", name="uq_account_material"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    material_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # --- Relationships ------------------------------------------------------

    account: Mapped[Account] = relationship(back_populates="material_stories")
    question_set_responses: Mapped[list[QuestionSetResponse]] = relationship(
        back_populates="material_story", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<MaterialStory id={self.id} account={self.account_id} material={self.material_name!r}>"


# ---------------------------------------------------------------------------
# Utility: metadata creation helper
# ---------------------------------------------------------------------------


def create_schema(sqlite_url: str | None = None, echo: bool = False) -> None:
    """Convenience helper that creates all tables on the provided SQLite URL.

    Example:
        create_schema("sqlite:///my_game.db", echo=True)
    """

    eng = create_engine(sqlite_url or "sqlite:///game.db", echo=echo, future=True)
    Base.metadata.create_all(eng)
