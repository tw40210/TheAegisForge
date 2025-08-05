"""Unit tests for the MaterialController class."""

from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.py_libs.controllers.material_controller import MaterialController
from src.py_libs.controllers.sql_db_controller import (
    Account,
    Base,
    Item,
    Question,
    Summary,
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

    @patch("firebase_admin.auth.verify_id_token")
    def test_submit_question_set_response(self, mock_verify_token, material_controller, engine):
        """Test submitting a question set response."""

        # Mock Firebase token verification
        mock_verify_token.return_value = {"uid": "test_firebase_uid"}

        with Session(engine) as session:
            # Create test account
            account = Account(
                name="Test User", firebaseUID="test_firebase_uid", email="test@example.com"
            )
            session.add(account)
            session.commit()

            # Create test questions with proper structure
            question_content = {
                "question_1": {
                    "question_description": "Test question 1?",
                    "choice_1": {
                        "choice_description": "Correct answer",
                        "answer": True,
                        "explanation": "This is correct",
                    },
                    "choice_2": {
                        "choice_description": "Wrong answer",
                        "answer": False,
                        "explanation": "This is wrong",
                    },
                    "choice_3": {
                        "choice_description": "Another wrong",
                        "answer": False,
                        "explanation": "Also wrong",
                    },
                    "choice_4": {
                        "choice_description": "Last wrong",
                        "answer": False,
                        "explanation": "Still wrong",
                    },
                },
                "question_2": {
                    "question_description": "Test question 2?",
                    "choice_1": {
                        "choice_description": "Wrong answer",
                        "answer": False,
                        "explanation": "This is wrong",
                    },
                    "choice_2": {
                        "choice_description": "Correct answer",
                        "answer": True,
                        "explanation": "This is correct",
                    },
                    "choice_3": {
                        "choice_description": "Another wrong",
                        "answer": False,
                        "explanation": "Also wrong",
                    },
                    "choice_4": {
                        "choice_description": "Last wrong",
                        "answer": False,
                        "explanation": "Still wrong",
                    },
                },
            }

            question = Question(
                question_type="mc_question",
                summary_type="TestSummary",
                content_type="test_content",
                index_number=1,
                material_name="test_material",
                content=question_content,
            )
            session.add(question)
            session.commit()

        # Test submitting responses
        user_answers = {
            "question_1": "choice_1",  # Correct
            "question_2": "choice_1",  # Wrong (correct is choice_2)
        }

        result = material_controller.submit_question_set_response(
            id_token="mock_token",
            answer=user_answers,
            question_set_id="TestSummary-test_content",
            material_name="test_material",
        )

        # Verify response
        assert result["success"] is True
        assert result["material_name"] == "test_material"
        assert result["question_set_id"] == "TestSummary-test_content"
        assert result["correct_rate"] == 0.5  # 1 out of 2 correct
        assert result["correct_count"] == 1
        assert result["total_count"] == 2
        assert "finish_time" in result
        assert "account_id" in result

        # Verify rewards are included
        assert "rewards" in result
        rewards = result["rewards"]
        assert "rewards_sent" in rewards
        assert "total_items" in rewards
        assert "message" in rewards
        assert "correct_rate_tier" in rewards
        assert rewards["correct_rate_tier"] == "Basic"  # 50% correct rate

        mock_verify_token.assert_called_once_with("mock_token")

    @patch("firebase_admin.auth.verify_id_token")
    def test_submit_question_set_response_invalid_token(
        self, mock_verify_token, material_controller
    ):
        """Test submitting response with invalid token."""
        from src.py_libs.controllers.material_controller import InvalidTokenError

        mock_verify_token.side_effect = Exception("Invalid token")

        with pytest.raises(InvalidTokenError):
            material_controller.submit_question_set_response(
                id_token="invalid_token",
                answer={"question_1": "choice_1"},
                question_set_id="test_set",
                material_name="test_material",
            )

    @patch("firebase_admin.auth.verify_id_token")
    def test_submit_question_set_response_account_not_found(
        self, mock_verify_token, material_controller
    ):
        """Test submitting response when account doesn't exist."""
        mock_verify_token.return_value = {"uid": "nonexistent_uid"}

        with pytest.raises(ValueError, match="Account not found for this Firebase user"):
            material_controller.submit_question_set_response(
                id_token="valid_token",
                answer={"question_1": "choice_1"},
                question_set_id="test_set",
                material_name="test_material",
            )


class TestRewardSystem:
    """Test cases for the reward system functionality."""

    def test_get_performance_tier_excellent(self, material_controller):
        """Test performance tier calculation for excellent performance."""
        assert material_controller._get_performance_tier(0.95) == "Excellent"
        assert material_controller._get_performance_tier(0.90) == "Excellent"

    def test_get_performance_tier_great(self, material_controller):
        """Test performance tier calculation for great performance."""
        assert material_controller._get_performance_tier(0.85) == "Great"
        assert material_controller._get_performance_tier(0.80) == "Great"

    def test_get_performance_tier_good(self, material_controller):
        """Test performance tier calculation for good performance."""
        assert material_controller._get_performance_tier(0.75) == "Good"
        assert material_controller._get_performance_tier(0.70) == "Good"

    def test_get_performance_tier_decent(self, material_controller):
        """Test performance tier calculation for decent performance."""
        assert material_controller._get_performance_tier(0.65) == "Decent"
        assert material_controller._get_performance_tier(0.60) == "Decent"

    def test_get_performance_tier_basic(self, material_controller):
        """Test performance tier calculation for basic performance."""
        assert material_controller._get_performance_tier(0.55) == "Basic"
        assert material_controller._get_performance_tier(0.40) == "Basic"

    def test_get_performance_tier_participation(self, material_controller):
        """Test performance tier calculation for participation level."""
        assert material_controller._get_performance_tier(0.35) == "Participation"
        assert material_controller._get_performance_tier(0.0) == "Participation"

    def test_calculate_and_send_rewards_no_items_available(self, material_controller):
        """Test reward calculation when no items are available."""
        # Mock the item_controller's list_items method
        material_controller.item_controller.list_items = lambda: []

        result = material_controller._calculate_and_send_rewards(1, 0.85)

        assert result["rewards_sent"] == []
        assert result["total_items"] == 0
        assert result["message"] == "No gacha tickets available for rewards"

    def test_calculate_and_send_rewards_no_gacha_tickets(self, material_controller):
        """Test reward calculation when no gacha tickets are available."""
        # Mock the item_controller's list_items method to return non-gacha items
        material_controller.item_controller.list_items = lambda: [
            {"id": 1, "name": "Health Potion"},
            {"id": 2, "name": "Energy Crystal"},
        ]

        result = material_controller._calculate_and_send_rewards(1, 0.85)

        assert result["rewards_sent"] == []
        assert result["total_items"] == 0
        assert result["message"] == "No gacha tickets available for rewards"

    @patch("random.randint")
    @patch("random.choice")
    def test_calculate_and_send_rewards_excellent_performance(
        self, mock_choice, mock_randint, material_controller
    ):
        """Test reward calculation for excellent performance (90%+)."""
        # Mock available gacha tickets
        gacha_tickets = [
            {"id": 1, "name": "Standard Gacha Ticket"},
            {"id": 2, "name": "Premium Gacha Ticket"},
            {"id": 3, "name": "Rare Gacha Ticket"},
        ]
        material_controller.item_controller.list_items = lambda: gacha_tickets

        # Mock random choices
        mock_randint.side_effect = [4, 2, 1, 3, 1]  # item_count=4, then quantities 2,1,3,1
        mock_choice.side_effect = [
            gacha_tickets[0],  # Standard Gacha Ticket
            gacha_tickets[1],  # Premium Gacha Ticket
            gacha_tickets[2],  # Rare Gacha Ticket
            gacha_tickets[0],  # Standard Gacha Ticket (4th item)
        ]

        # Mock item controller responses
        send_responses = [
            {"success": True, "item_name": "Standard Gacha Ticket", "total_amount": 5},
            {"success": True, "item_name": "Premium Gacha Ticket", "total_amount": 2},
            {"success": True, "item_name": "Rare Gacha Ticket", "total_amount": 4},
            {"success": True, "item_name": "Standard Gacha Ticket", "total_amount": 6},
        ]
        call_count = 0

        def mock_send_item(item_id, quantity, account_id):
            nonlocal call_count
            response = send_responses[call_count % len(send_responses)]
            call_count += 1
            return response

        material_controller.item_controller.send_item_to_account = mock_send_item

        result = material_controller._calculate_and_send_rewards(42, 0.95)

        assert len(result["rewards_sent"]) == 4
        assert result["total_items"] == 7  # 2+1+3+1
        assert result["message"] == "Excellent performance! Outstanding rewards!"
        assert result["correct_rate_tier"] == "Excellent"

        # Verify item controller was called correctly
        assert call_count == 4

    @patch("random.randint")
    @patch("random.choice")
    def test_calculate_and_send_rewards_good_performance(
        self, mock_choice, mock_randint, material_controller
    ):
        """Test reward calculation for good performance (70-79%)."""
        gacha_tickets = [
            {"id": 1, "name": "Standard Gacha Ticket"},
            {"id": 2, "name": "Premium Gacha Ticket"},
        ]
        material_controller.item_controller.list_items = lambda: gacha_tickets

        mock_randint.side_effect = [2, 1, 2]  # item_count=2, quantities 1,2
        mock_choice.side_effect = [gacha_tickets[0], gacha_tickets[1]]

        send_responses = [
            {"success": True, "item_name": "Standard Gacha Ticket", "total_amount": 3},
            {"success": True, "item_name": "Premium Gacha Ticket", "total_amount": 2},
        ]
        call_count = 0

        def mock_send_item(item_id, quantity, account_id):
            nonlocal call_count
            response = send_responses[call_count % len(send_responses)]
            call_count += 1
            return response

        material_controller.item_controller.send_item_to_account = mock_send_item

        result = material_controller._calculate_and_send_rewards(42, 0.75)

        assert len(result["rewards_sent"]) == 2
        assert result["total_items"] == 3  # 1+2
        assert result["message"] == "Good work! Here are your rewards!"
        assert result["correct_rate_tier"] == "Good"

    @patch("random.randint")
    @patch("random.choice")
    def test_calculate_and_send_rewards_participation_level(
        self, mock_choice, mock_randint, material_controller
    ):
        """Test reward calculation for participation level (<40%)."""
        gacha_tickets = [{"id": 1, "name": "Standard Gacha Ticket"}]
        material_controller.item_controller.list_items = lambda: gacha_tickets

        mock_randint.return_value = 1  # quantity=1
        mock_choice.return_value = gacha_tickets[0]

        material_controller.item_controller.send_item_to_account = (
            lambda item_id, quantity, account_id: {
                "success": True,
                "item_name": "Standard Gacha Ticket",
                "total_amount": 1,
            }
        )

        result = material_controller._calculate_and_send_rewards(42, 0.30)

        assert len(result["rewards_sent"]) == 1
        assert result["total_items"] == 1
        assert result["message"] == "Don't give up! Participation reward!"
        assert result["correct_rate_tier"] == "Participation"

    @patch("random.randint")
    @patch("random.choice")
    def test_calculate_and_send_rewards_item_send_failure(
        self, mock_choice, mock_randint, material_controller
    ):
        """Test reward calculation when item sending fails."""
        gacha_tickets = [{"id": 1, "name": "Standard Gacha Ticket"}]
        material_controller.item_controller.list_items = lambda: gacha_tickets

        mock_randint.return_value = 1
        mock_choice.return_value = gacha_tickets[0]

        # Mock failed item sending
        material_controller.item_controller.send_item_to_account = (
            lambda item_id, quantity, account_id: {
                "success": False,
                "message": "Failed to send item",
            }
        )

        result = material_controller._calculate_and_send_rewards(42, 0.85)

        assert result["rewards_sent"] == []
        assert result["total_items"] == 0
        assert result["message"] == "Great job! Well-deserved rewards!"
        assert result["correct_rate_tier"] == "Great"

    @patch("firebase_admin.auth.verify_id_token")
    def test_submit_question_set_response_with_rewards(
        self, mock_verify_token, material_controller, engine
    ):
        """Test submitting response includes reward information."""

        # Setup test data
        mock_verify_token.return_value = {"uid": "test_uid"}

        with Session(engine) as session:
            # Create account
            account = Account(name="test_user", firebaseUID="test_uid")
            session.add(account)
            session.flush()

            # Create gacha ticket items
            items = [
                Item(id=1, name="Standard Gacha Ticket"),
                Item(id=2, name="Premium Gacha Ticket"),
            ]
            session.add_all(items)

            # Create question
            question = Question(
                question_type="mc_question",
                summary_type="test",
                content_type="multiple_choice",
                index_number=0,
                material_name="test_material",
                content={
                    "question_1": {
                        "choice_1": {"text": "Option A", "answer": True},
                        "choice_2": {"text": "Option B", "answer": False},
                    }
                },
            )
            session.add(question)
            session.commit()

        # Submit response
        result = material_controller.submit_question_set_response(
            id_token="mock_token",
            answer={"question_1": "choice_1"},  # Correct answer
            question_set_id="test-multiple_choice",
            material_name="test_material",
        )

        # Verify response includes rewards
        assert result["success"] is True
        assert result["correct_rate"] == 1.0  # 100% correct
        assert "rewards" in result

        rewards = result["rewards"]
        assert "rewards_sent" in rewards
        assert "total_items" in rewards
        assert "message" in rewards
        assert "correct_rate_tier" in rewards
        assert rewards["correct_rate_tier"] == "Excellent"

    @patch("firebase_admin.auth.verify_id_token")
    def test_submit_question_set_response_with_rewards_no_gacha_tickets(
        self, mock_verify_token, material_controller, engine
    ):
        """Test submitting response when no gacha tickets are available."""
        from src.py_libs.controllers.sql_db_controller import Account, Item, Question

        mock_verify_token.return_value = {"uid": "test_uid"}

        with Session(engine) as session:
            # Create account
            account = Account(name="test_user", firebaseUID="test_uid")
            session.add(account)
            session.flush()

            # Create non-gacha items only
            items = [
                Item(id=1, name="Health Potion"),
                Item(id=2, name="Energy Crystal"),
            ]
            session.add_all(items)

            # Create question
            question = Question(
                question_type="mc_question",
                summary_type="test",
                content_type="multiple_choice",
                index_number=0,
                material_name="test_material",
                content={
                    "question_1": {
                        "choice_1": {"text": "Option A", "answer": True},
                    }
                },
            )
            session.add(question)
            session.commit()

        # Mock the item_controller to return only non-gacha items
        original_list_items = material_controller.item_controller.list_items
        material_controller.item_controller.list_items = lambda: [
            {"id": 1, "name": "Health Potion"},
            {"id": 2, "name": "Energy Crystal"},
        ]

        try:
            result = material_controller.submit_question_set_response(
                id_token="mock_token",
                answer={"question_1": "choice_1"},
                question_set_id="test-multiple_choice",
                material_name="test_material",
            )

            # Verify response includes empty rewards
            assert result["success"] is True
            rewards = result["rewards"]
            assert rewards["rewards_sent"] == []
            assert rewards["total_items"] == 0
            assert rewards["message"] == "No gacha tickets available for rewards"
        finally:
            # Restore original method
            material_controller.item_controller.list_items = original_list_items
