"""Unit tests for the simple_db_create.py script."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.py_libs.controllers.sql_db_controller import (
    Account,
    Base,
    Hero,
    Item,
    Question,
    Summary,
)
from src.scripts.simple_db_create import (
    load_config_file,
    populate_items_from_config,
    populate_questions_from_data,
    populate_sample_data,
    populate_summaries_from_data,
)

# Test database URL
TEST_DB_URL = "sqlite:///:memory:"


@pytest.fixture
def engine():
    """Create a test database engine."""
    engine = create_engine(TEST_DB_URL)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def sample_items_config():
    """Sample items configuration for testing."""
    return {
        "items": {
            "1": {"id": 1, "name": "Standard Gacha Ticket"},
            "2": {"id": 2, "name": "Premium Gacha Ticket"},
            "3": {"id": 3, "name": "Gold Coins"},
        }
    }


@pytest.fixture
def sample_heroes_config():
    """Sample heroes configuration for testing."""
    return {
        "heroes": {
            "1": {"name": "Test Hero 1", "rarity": "Common"},
            "2": {"name": "Test Hero 2", "rarity": "Rare"},
            "3": {"name": "Test Hero 3", "rarity": "Epic"},
        }
    }


@pytest.fixture
def sample_herotraits_config():
    """Sample hero traits configuration for testing."""
    return {
        "hero_traits": {
            "1": {"name": "Strength", "description": "Increases attack power"},
            "2": {"name": "Defense", "description": "Increases defense"},
            "3": {"name": "Speed", "description": "Increases speed"},
        }
    }


@pytest.fixture
def sample_question_data():
    """Sample question data for testing."""
    return {
        "question_1": {
            "question_description": "What is the main challenge in marketing mix models?",
            "choice_1": {
                "choice_description": "Linear models work perfectly",
                "answer": False,
                "explanation": "Linear models have limitations",
            },
            "choice_2": {
                "choice_description": "Nonlinear effects are hard to identify",
                "answer": True,
                "explanation": "This is the main challenge discussed",
            },
        }
    }


@pytest.fixture
def sample_summary_data():
    """Sample summary data for testing."""
    return {
        "summary_type": "innovation",
        "overview": "This paper investigates marketing mix model challenges.",
        "key_concepts": ["Marketing Mix Models", "Nonlinear Effects"],
        "innovation_points": [
            {
                "subject": "Model Identification",
                "description": "New approach to identifying model parameters",
                "technical_details": "Uses advanced statistical methods",
                "why_is_innovative": "First to address this specific problem",
            }
        ],
    }


@pytest.fixture
def temp_output_dir(sample_question_data, sample_summary_data):
    """Create a temporary output_question_data directory structure."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create the main output directory
        output_dir = Path(temp_dir) / "output_question_data"
        output_dir.mkdir()

        # Create a sample subdirectory
        paper_dir = output_dir / "Test Paper_1"
        paper_dir.mkdir()

        # Create sample question files
        question_file = paper_dir / "mc_question_InnovationSummary_innovation_points_0.json"
        with open(question_file, "w") as f:
            json.dump(sample_question_data, f)

        question_file2 = paper_dir / "mc_question_TechnicalSummary_overview_0.json"
        with open(question_file2, "w") as f:
            json.dump(sample_question_data, f)

        # Create sample summary files
        summary_file = paper_dir / "summary_InnovationSummary.json"
        with open(summary_file, "w") as f:
            json.dump(sample_summary_data, f)

        summary_file2 = paper_dir / "summary_TechnicalSummary.json"
        with open(summary_file2, "w") as f:
            json.dump(sample_summary_data, f)

        # Create metadata file
        meta_file = paper_dir / "meta_data.json"
        with open(meta_file, "w") as f:
            json.dump(
                {
                    "id": 1,
                    "file_name": "Test Paper",
                    "file_suffix": ".pdf",
                    "file_path": "test/path.pdf",
                },
                f,
            )

        yield temp_dir


def test_load_config_file_success(tmp_path):
    """Test successfully loading a YAML configuration file."""
    config_data = {"test": "data", "items": {"1": {"id": 1, "name": "Test Item"}}}
    config_file = tmp_path / "test_config.yaml"

    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    result = load_config_file(str(config_file))
    assert result == config_data


def test_load_config_file_not_found():
    """Test loading a non-existent configuration file."""
    with pytest.raises(FileNotFoundError):
        load_config_file("non_existent_file.yaml")


def test_create_database(engine):
    """Test database schema creation."""
    # Use the engine fixture which already creates tables
    # Just verify that tables exist by trying to query them
    with Session(engine) as session:
        # These should not raise exceptions if tables exist
        session.query(Account).count()
        session.query(Item).count()
        session.query(Question).count()
        session.query(Summary).count()


@patch("src.scripts.simple_db_create.engine")
@patch("src.scripts.simple_db_create.load_config_file")
def test_populate_items_from_config_success(
    mock_load_config, mock_engine, engine, sample_items_config
):
    """Test successfully populating items from configuration."""
    mock_engine.return_value = engine
    mock_load_config.return_value = sample_items_config

    # Set up the mock engine to use our test engine
    with patch("src.scripts.simple_db_create.engine", engine):
        populate_items_from_config()

    # Verify items were added
    with Session(engine) as session:
        items = session.query(Item).all()
        assert len(items) == 3
        assert items[0].name == "Standard Gacha Ticket"


@patch("src.scripts.simple_db_create.engine")
def test_populate_questions_from_data_success(mock_engine, engine, temp_output_dir):
    """Test successfully populating questions from output_question_data."""
    mock_engine.return_value = engine

    # Change to temp directory and run the function
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_output_dir)
        with patch("src.scripts.simple_db_create.engine", engine):
            populate_questions_from_data()

        # Verify questions were added
        with Session(engine) as session:
            questions = session.query(Question).all()
            assert len(questions) == 2  # Two question files

            # Check first question
            q1 = questions[0]
            assert q1.question_type == "mc_question"
            assert q1.summary_type == "InnovationSummary"
            assert q1.content_type == "innovation_points"
            assert q1.index_number == 0
            assert "question_1" in q1.content

    finally:
        os.chdir(original_cwd)


@patch("src.scripts.simple_db_create.engine")
def test_populate_summaries_from_data_success(mock_engine, engine, temp_output_dir):
    """Test successfully populating summaries from output_question_data."""
    mock_engine.return_value = engine

    # Change to temp directory and run the function
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_output_dir)
        with patch("src.scripts.simple_db_create.engine", engine):
            populate_summaries_from_data()

        # Verify summaries were added
        with Session(engine) as session:
            summaries = session.query(Summary).all()
            assert len(summaries) == 2  # Two summary files

            # Check first summary
            s1 = summaries[0]
            assert s1.summary_type == "InnovationSummary"
            assert s1.content_type == "innovationsummary"
            assert s1.index_number == 0
            assert "summary_type" in s1.content

    finally:
        os.chdir(original_cwd)


def test_populate_questions_missing_directory():
    """Test populating questions when output_question_data directory doesn't exist."""
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            # Should not raise an exception, just print warning
            populate_questions_from_data()
        finally:
            os.chdir(original_cwd)


def test_populate_summaries_missing_directory():
    """Test populating summaries when output_question_data directory doesn't exist."""
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            # Should not raise an exception, just print warning
            populate_summaries_from_data()
        finally:
            os.chdir(original_cwd)


@patch("src.scripts.simple_db_create.engine")
def test_populate_questions_malformed_filename(mock_engine, engine, tmp_path):
    """Test populating questions with malformed filenames."""
    mock_engine.return_value = engine

    # Create directory structure with malformed filename
    output_dir = tmp_path / "output_question_data"
    output_dir.mkdir()
    paper_dir = output_dir / "Test Paper_1"
    paper_dir.mkdir()

    # Create malformed question file (too few parts)
    bad_file = paper_dir / "mc_question_bad.json"
    with open(bad_file, "w") as f:
        json.dump({"test": "data"}, f)

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        with patch("src.scripts.simple_db_create.engine", engine):
            populate_questions_from_data()

        # Should not crash, and no questions should be added
        with Session(engine) as session:
            questions = session.query(Question).all()
            assert len(questions) == 0

    finally:
        os.chdir(original_cwd)


@patch("src.scripts.simple_db_create.engine")
def test_populate_questions_invalid_json(mock_engine, engine, tmp_path):
    """Test populating questions with invalid JSON."""
    mock_engine.return_value = engine

    # Create directory structure with invalid JSON
    output_dir = tmp_path / "output_question_data"
    output_dir.mkdir()
    paper_dir = output_dir / "Test Paper_1"
    paper_dir.mkdir()

    # Create question file with invalid JSON
    bad_file = paper_dir / "mc_question_InnovationSummary_overview_0.json"
    with open(bad_file, "w") as f:
        f.write("{ invalid json }")

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        with patch("src.scripts.simple_db_create.engine", engine):
            populate_questions_from_data()

        # Should not crash, and no questions should be added
        with Session(engine) as session:
            questions = session.query(Question).all()
            assert len(questions) == 0

    finally:
        os.chdir(original_cwd)


@patch("src.scripts.simple_db_create.engine")
@patch("src.scripts.simple_db_create.load_config_file")
def test_populate_sample_data_success(
    mock_load_config, mock_engine, engine, sample_heroes_config, sample_herotraits_config
):
    """Test successfully populating sample data."""
    mock_engine.return_value = engine
    mock_load_config.side_effect = [sample_heroes_config, sample_herotraits_config]

    with patch("src.scripts.simple_db_create.engine", engine):
        populate_sample_data()

    # Verify data was added
    with Session(engine) as session:
        accounts = session.query(Account).all()
        heroes = session.query(Hero).all()
        assert len(accounts) == 3
        assert len(heroes) == 4


def test_question_content_structure(temp_output_dir, engine):
    """Test that question content is properly structured when loaded."""
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_output_dir)
        with patch("src.scripts.simple_db_create.engine", engine):
            populate_questions_from_data()

        with Session(engine) as session:
            question = session.query(Question).first()
            assert question is not None

            # Verify the content structure
            content = question.content
            assert "question_1" in content
            assert "question_description" in content["question_1"]
            assert "choice_1" in content["question_1"]
            assert "answer" in content["question_1"]["choice_1"]

    finally:
        os.chdir(original_cwd)


def test_summary_content_structure(temp_output_dir, engine):
    """Test that summary content is properly structured when loaded."""
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_output_dir)
        with patch("src.scripts.simple_db_create.engine", engine):
            populate_summaries_from_data()

        with Session(engine) as session:
            summary = session.query(Summary).first()
            assert summary is not None

            # Verify the content structure
            content = summary.content
            assert "summary_type" in content
            assert "overview" in content
            assert "key_concepts" in content
            assert "innovation_points" in content

    finally:
        os.chdir(original_cwd)


@patch("src.scripts.simple_db_create.engine")
def test_unique_constraint_enforcement(mock_engine, engine, temp_output_dir):
    """Test that unique constraints are properly enforced."""
    mock_engine.return_value = engine

    original_cwd = os.getcwd()
    try:
        os.chdir(temp_output_dir)
        with patch("src.scripts.simple_db_create.engine", engine):
            # Load questions twice - should not create duplicates due to unique constraint
            populate_questions_from_data()

    finally:
        os.chdir(original_cwd)


def test_empty_output_directory(engine, tmp_path):
    """Test behavior with empty output_question_data directory."""
    # Create empty directory structure
    output_dir = tmp_path / "output_question_data"
    output_dir.mkdir()

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        with patch("src.scripts.simple_db_create.engine", engine):
            populate_questions_from_data()
            populate_summaries_from_data()

        # Should complete without errors
        with Session(engine) as session:
            questions = session.query(Question).all()
            summaries = session.query(Summary).all()
            assert len(questions) == 0
            assert len(summaries) == 0

    finally:
        os.chdir(original_cwd)


@patch("src.scripts.simple_db_create.verify_database")
@patch("src.scripts.simple_db_create.populate_summaries_from_data")
@patch("src.scripts.simple_db_create.populate_questions_from_data")
@patch("src.scripts.simple_db_create.populate_sample_data")
@patch("src.scripts.simple_db_create.populate_items_from_config")
@patch("src.scripts.simple_db_create.create_database")
def test_main_integration_success(
    mock_create_db,
    mock_populate_items,
    mock_populate_sample,
    mock_populate_questions,
    mock_populate_summaries,
    mock_verify,
):
    """Test that main() function calls all required functions in correct order."""
    from src.scripts.simple_db_create import main

    # Mock all functions to avoid actual database operations
    mock_create_db.return_value = None
    mock_populate_items.return_value = None
    mock_populate_sample.return_value = None
    mock_populate_questions.return_value = None
    mock_populate_summaries.return_value = None
    mock_verify.return_value = None

    # Run main function
    main()

    # Verify all functions were called in correct order
    assert mock_create_db.called
    assert mock_populate_items.called
    assert mock_populate_sample.called
    assert mock_populate_questions.called
    assert mock_populate_summaries.called
    assert mock_verify.called

    # Verify call order
    calls = [
        mock_create_db.call_args_list,
        mock_populate_items.call_args_list,
        mock_populate_sample.call_args_list,
        mock_populate_questions.call_args_list,
        mock_populate_summaries.call_args_list,
        mock_verify.call_args_list,
    ]

    # All should have been called exactly once
    for call_list in calls:
        assert len(call_list) == 1


@patch("src.scripts.simple_db_create.populate_items_from_config")
def test_main_handles_exceptions(mock_populate_items, capsys):
    """Test that main() function properly handles and reports exceptions."""
    from src.scripts.simple_db_create import main

    # Make one of the functions raise an exception
    mock_populate_items.side_effect = Exception("Test error")

    # Main should exit with code 1 and print error
    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1

    # Check that error was printed
    captured = capsys.readouterr()
    assert "❌ Error during database setup: Test error" in captured.out
