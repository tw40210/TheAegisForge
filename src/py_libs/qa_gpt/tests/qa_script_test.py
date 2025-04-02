from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.py_libs.qa_gpt.core.objects.questions import (
    Choice,
    MultipleChoiceQuestion,
    MultipleChoiceQuestionSet,
)
from src.py_libs.qa_gpt.core.objects.summaries import (
    BulletPoint,
    Conclusion,
    InnovationSummary,
    Motivation,
    StandardSummary,
    TechnicalSummary,
)
from src.py_libs.qa_gpt.core.utils.fetch_utils import (
    fetch_material_add_sets,
    fetch_material_add_summary,
    output_question_data,
)


@pytest.fixture
def test_pdf_folder(tmp_path):
    # Create a test PDF folder with a sample PDF
    pdf_folder = tmp_path / "pdf_data"
    pdf_folder.mkdir()
    (pdf_folder / "test.pdf").touch()
    return pdf_folder


@pytest.fixture
def mock_qa_controller():
    controller = MagicMock()
    with patch("src.py_libs.qa_gpt.core.utils.fetch_utils.QAController") as mock:
        mock.return_value = controller
        yield controller


@pytest.fixture
def mock_material_controller():
    controller = MagicMock()
    with patch("src.py_libs.qa_gpt.core.utils.fetch_utils.MaterialController") as mock:
        mock.return_value = controller
        yield controller


@pytest.fixture
def mock_db_controller():
    controller = MagicMock()
    with patch("src.py_libs.qa_gpt.core.utils.fetch_utils.LocalDatabaseController") as mock:
        mock.return_value = controller
        yield controller


def test_fetch_material_add_summary_flow(
    test_pdf_folder, mock_qa_controller, mock_material_controller, mock_db_controller
):
    # Setup mock returns
    file_meta = MagicMock()
    file_meta.summaries = {
        "StandardSummary": MagicMock(),  # Already exists
        "TechnicalSummary": None,  # Will be added
        "InnovationSummary": None,  # Will be added
    }
    file_meta.__getitem__.return_value = str(test_pdf_folder / "test.pdf")

    def append_summary_side_effect(file_id, summary):
        summary_type = summary.__class__.__name__
        file_meta.summaries[summary_type] = summary

    mock_material_controller.get_material_table.return_value = {"test_id": file_meta}
    mock_material_controller.append_summary.side_effect = append_summary_side_effect

    # Create test summaries
    technical_summary = TechnicalSummary(
        overview="Test overview",
        key_concepts=["concept1", "concept2"],
        technical_details=["Detail 1: value1"],
        implementation_steps=["step1", "step2"],
        requirements=["Requirement 1: value1"],
        limitations=["limit1"],
    )

    innovation_summary = InnovationSummary(
        overview="Test overview",
        key_concepts=["concept1", "concept2"],
        innovation_points=[],
        references=["ref1", "ref2"],
    )

    # Setup mock to return only new summaries
    mock_qa_controller.get_summary.side_effect = [
        technical_summary,
        innovation_summary,
    ]

    # Run the function
    with patch("src.py_libs.qa_gpt.core.utils.fetch_utils.Path") as mock_path:
        mock_path.return_value = test_pdf_folder
        fetch_material_add_summary()

    # Verify the function calls
    mock_material_controller.fetch_material_folder.assert_called_once_with(test_pdf_folder)
    assert len(file_meta.summaries) == 3  # Should have all 3 summaries
    assert mock_qa_controller.get_summary.call_count == 2  # Should only be called for new summaries


def test_fetch_material_add_sets_flow(
    test_pdf_folder, mock_qa_controller, mock_material_controller, mock_db_controller
):
    # Setup mock returns
    file_meta = MagicMock()
    file_meta.mc_question_sets = {
        "StandardSummary_motivation_0": MagicMock(),  # Already exists
        "StandardSummary_conclusion_0": MagicMock(),  # Already exists
        "StandardSummary_bullet_points_0": MagicMock(),  # Already exists
    }

    # Create mock summaries with model_dump
    standard_summary = MagicMock()
    standard_summary.model_dump.return_value = {
        "summary_type": "standard",
        "motivation": "test motivation",
        "conclusion": "test conclusion",
        "bullet_points": "test bullet points",
    }

    technical_summary = MagicMock()
    technical_summary.model_dump.return_value = {
        "summary_type": "technical",
        "overview": "test overview",
        "key_concepts": ["test concept"],
        "technical_details": ["test detail"],
        "implementation_steps": ["test step"],
        "requirements": ["test requirement"],
        "limitations": ["test limitation"],
    }

    file_meta.summaries = {
        "StandardSummary": standard_summary,
        "TechnicalSummary": technical_summary,
    }
    file_meta.__getitem__.return_value = str(test_pdf_folder / "test.pdf")

    def append_mc_question_set_side_effect(file_id, question_set, prefix=""):
        file_meta.mc_question_sets[prefix] = question_set

    mock_material_controller.get_material_table.return_value = {"test_id": file_meta}
    mock_material_controller.append_mc_question_set.side_effect = append_mc_question_set_side_effect

    # Create a test question set
    question = MultipleChoiceQuestion(
        question_description="Test question",
        choice_1=Choice(choice_description="Choice 1", answer=True, explanation="Explanation 1"),
        choice_2=Choice(choice_description="Choice 2", answer=False, explanation="Explanation 2"),
        choice_3=Choice(choice_description="Choice 3", answer=False, explanation="Explanation 3"),
        choice_4=Choice(choice_description="Choice 4", answer=False, explanation="Explanation 4"),
    )

    question_set = MultipleChoiceQuestionSet(
        question_1=question,
        question_2=question,
        question_3=question,
        question_4=question,
        question_5=question,
    )

    # Setup mock to return question sets for each summary's top-level attributes
    mock_qa_controller.get_questions.side_effect = [
        question_set,  # For each field in StandardSummary
        question_set,
        question_set,
        question_set,
        question_set,  # For each field in TechnicalSummary
        question_set,
        question_set,
        question_set,
        question_set,
        question_set,
        question_set,
    ]

    # Run the function
    fetch_material_add_sets()

    # Verify the flow
    mock_material_controller.fetch_material_folder.assert_called_once_with(Path("./pdf_data"))
    assert (
        mock_qa_controller.get_questions.call_count == 8
    )  # Called for all fields in both summaries, minus skipped ones
    assert (
        mock_material_controller.append_mc_question_set.call_count == 8
    )  # Called for each new question set
    assert len(file_meta.mc_question_sets) == 11  # 3 existing + 8 new

    # Verify question sets were saved with correct prefixes
    saved_prefixes = list(file_meta.mc_question_sets.keys())
    # Existing StandardSummary sets should remain
    assert "StandardSummary_motivation_0" in saved_prefixes
    assert "StandardSummary_conclusion_0" in saved_prefixes
    assert "StandardSummary_bullet_points_0" in saved_prefixes
    # New StandardSummary sets should be added
    assert "StandardSummary_summary_type" in saved_prefixes
    # TechnicalSummary sets should be added
    assert "TechnicalSummary_summary_type" in saved_prefixes
    assert "TechnicalSummary_overview" in saved_prefixes
    assert "TechnicalSummary_key_concepts" in saved_prefixes
    assert "TechnicalSummary_technical_details" in saved_prefixes
    assert "TechnicalSummary_implementation_steps" in saved_prefixes
    assert "TechnicalSummary_requirements" in saved_prefixes
    assert "TechnicalSummary_limitations" in saved_prefixes


def test_output_question_data_flow(
    test_pdf_folder, mock_qa_controller, mock_material_controller, mock_db_controller
):
    # Setup output folder
    output_folder = Path("./output_question_data")

    # Run the function
    output_question_data()

    # Verify the flow
    mock_material_controller.output_material_as_folder.assert_called_once_with(output_folder)


def test_full_script_flow(
    test_pdf_folder, mock_qa_controller, mock_material_controller, mock_db_controller
):
    # Setup mock returns
    file_meta = MagicMock()
    file_meta.summaries = {}
    file_meta.mc_question_sets = {}
    file_meta.__getitem__.return_value = str(test_pdf_folder / "test.pdf")

    def append_mc_question_set_side_effect(file_id, question_set, prefix=""):
        file_meta.mc_question_sets[prefix] = question_set

    def append_summary_side_effect(file_id, summary):
        summary_type = summary.__class__.__name__
        file_meta.summaries[summary_type] = summary

    mock_material_controller.get_material_table.return_value = {"test_id": file_meta}
    mock_material_controller.append_mc_question_set.side_effect = append_mc_question_set_side_effect
    mock_material_controller.append_summary.side_effect = append_summary_side_effect

    # Create test summaries
    standard_summary = StandardSummary(
        motivation=Motivation(
            description="Test description",
            problem_to_solve="Test problem",
            how_to_solve="Test solution",
            why_can_be_solved="Test reason",
        ),
        conclusion=Conclusion(
            description="Test description",
            problem_to_solve="Test problem",
            how_much_is_solved="Test progress",
            contribution="Test contribution",
        ),
        bullet_points=[
            BulletPoint(
                subject="Test subject",
                description="Test description",
                technical_details="Test details",
                importance_explanation="Test importance",
                importance=1,
            )
        ],
    )

    technical_summary = TechnicalSummary(
        overview="Test overview",
        key_concepts=["concept1", "concept2"],
        technical_details=["Detail 1: value1"],
        implementation_steps=["step1", "step2"],
        requirements=["Requirement 1: value1"],
        limitations=["limit1"],
    )

    innovation_summary = InnovationSummary(
        overview="Test overview",
        key_concepts=["concept1", "concept2"],
        innovation_points=[],
        references=["ref1", "ref2"],
    )

    # Create a test question set
    question = MultipleChoiceQuestion(
        question_description="Test question",
        choice_1=Choice(choice_description="Choice 1", answer=True, explanation="Explanation 1"),
        choice_2=Choice(choice_description="Choice 2", answer=False, explanation="Explanation 2"),
        choice_3=Choice(choice_description="Choice 3", answer=False, explanation="Explanation 3"),
        choice_4=Choice(choice_description="Choice 4", answer=False, explanation="Explanation 4"),
    )

    question_set = MultipleChoiceQuestionSet(
        question_1=question,
        question_2=question,
        question_3=question,
        question_4=question,
        question_5=question,
    )

    # Setup mocks to return summaries and questions
    mock_qa_controller.get_summary.side_effect = [
        standard_summary,
        technical_summary,
        innovation_summary,
    ]

    # Setup mock to return question sets for each field
    mock_qa_controller.get_questions.side_effect = [
        question_set,  # For each field in StandardSummary (4 fields)
        question_set,
        question_set,
        question_set,
        question_set,  # For each field in TechnicalSummary (6 fields)
        question_set,
        question_set,
        question_set,
        question_set,
        question_set,
        question_set,  # For each field in InnovationSummary (4 fields)
        question_set,
        question_set,
        question_set,
    ]

    # Run all functions in sequence
    with patch("src.py_libs.qa_gpt.core.utils.fetch_utils.Path") as mock_path:
        mock_path.return_value = test_pdf_folder
        fetch_material_add_summary()
        fetch_material_add_sets()
        output_question_data()

    # Verify the function calls
    assert (
        mock_material_controller.fetch_material_folder.call_count == 2
    )  # Called by both fetch_material functions
    assert len(file_meta.summaries) == 3  # Should have all 3 summaries
    assert mock_qa_controller.get_summary.call_count == 3  # Should be called for each summary type
    assert (
        len(file_meta.mc_question_sets) == 14
    )  # 4 for StandardSummary + 6 for TechnicalSummary + 4 for InnovationSummary
    assert mock_qa_controller.get_questions.call_count == 14  # Should be called for each field
    mock_material_controller.output_material_as_folder.assert_called_once()
