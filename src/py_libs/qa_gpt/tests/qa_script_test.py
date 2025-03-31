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
from src.py_libs.qa_gpt.script.QA_simple_script import (
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
    with patch("src.py_libs.qa_gpt.script.QA_simple_script.QAController") as mock:
        mock.return_value = controller
        yield controller


@pytest.fixture
def mock_material_controller():
    controller = MagicMock()
    with patch("src.py_libs.qa_gpt.script.QA_simple_script.MaterialController") as mock:
        mock.return_value = controller
        yield controller


@pytest.fixture
def mock_db_controller():
    controller = MagicMock()
    with patch("src.py_libs.qa_gpt.script.QA_simple_script.LocalDatabaseController") as mock:
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
    with patch("src.py_libs.qa_gpt.script.QA_simple_script.Path") as mock_path:
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
    file_meta.summaries = {
        "StandardSummary": MagicMock(),
        "TechnicalSummary": MagicMock(),
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
        # First call with StandardSummary model_dump (should be skipped)
        {
            "motivation": question_set,
            "conclusion": question_set,
            "bullet_points": question_set,
        },
        # Second call with TechnicalSummary model_dump (should be added)
        {
            "overview": question_set,
            "key_concepts": question_set,
            "technical_details": question_set,
            "implementation_steps": question_set,
            "requirements": question_set,
            "limitations": question_set,
        },
    ]

    # Run the function
    fetch_material_add_sets()

    # Verify the flow
    mock_material_controller.fetch_material_folder.assert_called_once_with(Path("./pdf_data"))
    assert mock_qa_controller.get_questions.call_count == 2  # Called for both summaries
    assert (
        mock_material_controller.append_mc_question_set.call_count == 6
    )  # Only for TechnicalSummary fields

    # Verify question sets were saved with correct prefixes
    saved_prefixes = list(file_meta.mc_question_sets.keys())
    # Existing StandardSummary sets should remain
    assert "StandardSummary_motivation_0" in saved_prefixes
    assert "StandardSummary_conclusion_0" in saved_prefixes
    assert "StandardSummary_bullet_points_0" in saved_prefixes
    # New TechnicalSummary sets should be added
    assert "TechnicalSummary_overview_0" in saved_prefixes
    assert "TechnicalSummary_key_concepts_0" in saved_prefixes
    assert "TechnicalSummary_technical_details_0" in saved_prefixes
    assert "TechnicalSummary_implementation_steps_0" in saved_prefixes
    assert "TechnicalSummary_requirements_0" in saved_prefixes
    assert "TechnicalSummary_limitations_0" in saved_prefixes


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
    file_meta.mc_question_sets = []
    file_meta.__getitem__.return_value = str(test_pdf_folder / "test.pdf")

    def append_mc_question_set_side_effect(file_id, question_set, prefix=""):
        file_meta.mc_question_sets.append((prefix, question_set))

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

    # Setup mock to return question sets for each summary type
    mock_qa_controller.get_questions.side_effect = [
        # StandardSummary fields
        {
            "motivation": question_set,
            "conclusion": question_set,
            "bullet_points": question_set,
        },
        # TechnicalSummary fields
        {
            "overview": question_set,
            "key_concepts": question_set,
            "technical_details": question_set,
            "implementation_steps": question_set,
            "requirements": question_set,
            "limitations": question_set,
        },
        # InnovationSummary fields
        {
            "overview": question_set,
            "key_concepts": question_set,
            "innovation_points": question_set,
            "references": question_set,
        },
    ]

    # Run all functions in sequence
    with patch("src.py_libs.qa_gpt.script.QA_simple_script.Path") as mock_path:
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
        len(file_meta.mc_question_sets) == 13
    )  # 3 for StandardSummary + 6 for TechnicalSummary + 4 for InnovationSummary
    assert (
        mock_qa_controller.get_questions.call_count == 3
    )  # Should be called for each summary type
    mock_material_controller.output_material_as_folder.assert_called_once()
