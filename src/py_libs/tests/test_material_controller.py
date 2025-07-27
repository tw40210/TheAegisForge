"""Unit tests for the MaterialController class."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.py_libs.controllers.material_controller import MaterialController
from src.py_libs.controllers.sql_db_controller import Base, Question, Summary

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
def material_controller(engine):
    """Create a MaterialController instance with test database."""
    controller = MaterialController()
    controller.engine = engine
    return controller


@pytest.fixture
def sample_questions(engine):
    """Create sample questions in the test database."""
    with Session(engine) as session:
        questions = [
            Question(
                question_type="mc_question",
                summary_type="InnovationSummary",
                content_type="innovation_points",
                index_number=0,
                material_name="test_material_1",
                content={"question": "What is innovation?", "options": ["A", "B", "C", "D"]},
            ),
            Question(
                question_type="essay_question",
                summary_type="InnovationSummary",
                content_type="innovation_theory",
                index_number=1,
                material_name="test_material_1",
                content={"question": "Explain innovation theory", "max_words": 500},
            ),
            Question(
                question_type="mc_question",
                summary_type="TechSummary",
                content_type="tech_basics",
                index_number=0,
                material_name="test_material_2",
                content={"question": "What is technology?", "options": ["A", "B", "C", "D"]},
            ),
        ]
        session.add_all(questions)
        session.commit()
        return questions


@pytest.fixture
def sample_summaries(engine):
    """Create sample summaries in the test database."""
    with Session(engine) as session:
        summaries = [
            Summary(
                summary_type="InnovationSummary",
                content_type="innovation_points",
                index_number=0,
                material_name="test_material_1",
                content={"key_points": ["Point 1", "Point 2"], "conclusion": "Summary text"},
            ),
            Summary(
                summary_type="InnovationSummary",
                content_type="innovation_theory",
                index_number=1,
                material_name="test_material_1",
                content={"theory": "Innovation theory explanation", "examples": ["Ex1", "Ex2"]},
            ),
            Summary(
                summary_type="TechSummary",
                content_type="tech_basics",
                index_number=0,
                material_name="test_material_2",
                content={"basics": "Technology basics", "applications": ["App1", "App2"]},
            ),
        ]
        session.add_all(summaries)
        session.commit()
        return summaries


class TestGetQuestionsByMaterialName:
    """Test cases for get_questions_by_material_name method."""

    def test_get_questions_existing_material(self, material_controller, sample_questions):
        """Test retrieving questions for an existing material."""
        questions = material_controller.get_questions_by_material_name("test_material_1")

        assert len(questions) == 2
        assert all(q["material_name"] == "test_material_1" for q in questions)

        # Check first question
        assert questions[0]["question_type"] == "mc_question"
        assert questions[0]["summary_type"] == "InnovationSummary"
        assert questions[0]["content_type"] == "innovation_points"
        assert questions[0]["index_number"] == 0
        assert "question" in questions[0]["content"]

        # Check second question
        assert questions[1]["question_type"] == "essay_question"
        assert questions[1]["content_type"] == "innovation_theory"
        assert questions[1]["index_number"] == 1

    def test_get_questions_nonexistent_material(self, material_controller, sample_questions):
        """Test retrieving questions for a non-existent material."""
        questions = material_controller.get_questions_by_material_name("nonexistent_material")

        assert questions == []

    def test_get_questions_empty_database(self, material_controller):
        """Test retrieving questions from empty database."""
        questions = material_controller.get_questions_by_material_name("any_material")

        assert questions == []

    def test_get_questions_single_material(self, material_controller, sample_questions):
        """Test retrieving questions for material with single question."""
        questions = material_controller.get_questions_by_material_name("test_material_2")

        assert len(questions) == 1
        assert questions[0]["material_name"] == "test_material_2"
        assert questions[0]["question_type"] == "mc_question"


class TestGetSummariesByMaterialName:
    """Test cases for get_summaries_by_material_name method."""

    def test_get_summaries_existing_material(self, material_controller, sample_summaries):
        """Test retrieving summaries for an existing material."""
        summaries = material_controller.get_summaries_by_material_name("test_material_1")

        assert len(summaries) == 2
        assert all(s["material_name"] == "test_material_1" for s in summaries)

        # Check first summary
        assert summaries[0]["summary_type"] == "InnovationSummary"
        assert summaries[0]["content_type"] == "innovation_points"
        assert summaries[0]["index_number"] == 0
        assert "key_points" in summaries[0]["content"]

        # Check second summary
        assert summaries[1]["summary_type"] == "InnovationSummary"
        assert summaries[1]["content_type"] == "innovation_theory"
        assert summaries[1]["index_number"] == 1

    def test_get_summaries_nonexistent_material(self, material_controller, sample_summaries):
        """Test retrieving summaries for a non-existent material."""
        summaries = material_controller.get_summaries_by_material_name("nonexistent_material")

        assert summaries == []

    def test_get_summaries_empty_database(self, material_controller):
        """Test retrieving summaries from empty database."""
        summaries = material_controller.get_summaries_by_material_name("any_material")

        assert summaries == []

    def test_get_summaries_single_material(self, material_controller, sample_summaries):
        """Test retrieving summaries for material with single summary."""
        summaries = material_controller.get_summaries_by_material_name("test_material_2")

        assert len(summaries) == 1
        assert summaries[0]["material_name"] == "test_material_2"
        assert summaries[0]["summary_type"] == "TechSummary"


class TestGetMaterialData:
    """Test cases for get_material_data method."""

    def test_get_material_data_with_both_questions_and_summaries(
        self, material_controller, sample_questions, sample_summaries
    ):
        """Test retrieving both questions and summaries for a material."""
        data = material_controller.get_material_data("test_material_1")

        assert data["material_name"] == "test_material_1"
        assert data["question_count"] == 2
        assert data["summary_count"] == 2
        assert len(data["questions"]) == 2
        assert len(data["summaries"]) == 2

        # Verify questions structure
        assert all(q["material_name"] == "test_material_1" for q in data["questions"])

        # Verify summaries structure
        assert all(s["material_name"] == "test_material_1" for s in data["summaries"])

    def test_get_material_data_questions_only(self, material_controller, sample_questions):
        """Test retrieving data for material with only questions."""
        data = material_controller.get_material_data("test_material_2")

        assert data["material_name"] == "test_material_2"
        assert data["question_count"] == 1
        assert data["summary_count"] == 0
        assert len(data["questions"]) == 1
        assert len(data["summaries"]) == 0

    def test_get_material_data_summaries_only(self, material_controller, sample_summaries):
        """Test retrieving data for material with only summaries."""
        data = material_controller.get_material_data("test_material_2")

        assert data["material_name"] == "test_material_2"
        assert data["question_count"] == 0
        assert data["summary_count"] == 1
        assert len(data["questions"]) == 0
        assert len(data["summaries"]) == 1

    def test_get_material_data_nonexistent(
        self, material_controller, sample_questions, sample_summaries
    ):
        """Test retrieving data for non-existent material."""
        data = material_controller.get_material_data("nonexistent_material")

        assert data["material_name"] == "nonexistent_material"
        assert data["question_count"] == 0
        assert data["summary_count"] == 0
        assert len(data["questions"]) == 0
        assert len(data["summaries"]) == 0


class TestListAvailableMaterials:
    """Test cases for list_available_materials method."""

    def test_list_materials_with_data(
        self, material_controller, sample_questions, sample_summaries
    ):
        """Test listing materials when data exists."""
        result = material_controller.list_available_materials()

        assert result["total_materials"] == 2
        assert len(result["materials"]) == 2

        # Check materials are sorted
        material_names = [m["material_name"] for m in result["materials"]]
        assert material_names == sorted(material_names)

        # Check material counts
        test_material_1 = next(
            m for m in result["materials"] if m["material_name"] == "test_material_1"
        )
        assert test_material_1["question_count"] == 2
        assert test_material_1["summary_count"] == 2
        assert test_material_1["total_count"] == 4

        test_material_2 = next(
            m for m in result["materials"] if m["material_name"] == "test_material_2"
        )
        assert test_material_2["question_count"] == 1
        assert test_material_2["summary_count"] == 1
        assert test_material_2["total_count"] == 2

    def test_list_materials_questions_only(self, material_controller, sample_questions):
        """Test listing materials with only questions."""
        result = material_controller.list_available_materials()

        assert result["total_materials"] == 2

        test_material_1 = next(
            m for m in result["materials"] if m["material_name"] == "test_material_1"
        )
        assert test_material_1["question_count"] == 2
        assert test_material_1["summary_count"] == 0

        test_material_2 = next(
            m for m in result["materials"] if m["material_name"] == "test_material_2"
        )
        assert test_material_2["question_count"] == 1
        assert test_material_2["summary_count"] == 0

    def test_list_materials_summaries_only(self, material_controller, sample_summaries):
        """Test listing materials with only summaries."""
        result = material_controller.list_available_materials()

        assert result["total_materials"] == 2

        test_material_1 = next(
            m for m in result["materials"] if m["material_name"] == "test_material_1"
        )
        assert test_material_1["question_count"] == 0
        assert test_material_1["summary_count"] == 2

        test_material_2 = next(
            m for m in result["materials"] if m["material_name"] == "test_material_2"
        )
        assert test_material_2["question_count"] == 0
        assert test_material_2["summary_count"] == 1

    def test_list_materials_empty_database(self, material_controller):
        """Test listing materials from empty database."""
        result = material_controller.list_available_materials()

        assert result["total_materials"] == 0
        assert result["materials"] == []
