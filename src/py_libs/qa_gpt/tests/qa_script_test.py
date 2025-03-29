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
    file_meta.summaries = []
    file_meta.__getitem__.return_value = str(test_pdf_folder / "test.pdf")
    mock_material_controller.get_material_table.return_value = {"test_id": file_meta}

    def append_summary_side_effect(file_id, summary):
        file_meta.summaries.append(summary)

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
        technical_details={"detail1": "value1"},
        implementation_steps=["step1", "step2"],
        requirements={"req1": "value1"},
        limitations=["limit1"],
    )

    # Setup mock to return summaries in sequence (need 2 summaries for 1 iteration)
    mock_qa_controller.get_summary.side_effect = [
        standard_summary,
        technical_summary,
    ]

    # Run the function
    with patch("src.py_libs.qa_gpt.script.QA_simple_script.Path") as mock_path:
        mock_path.return_value = test_pdf_folder
        fetch_material_add_summary()

    # Verify the function calls
    mock_material_controller.fetch_material_folder.assert_called_once_with(test_pdf_folder)
    assert len(file_meta.summaries) == 2  # Should have 2 summaries after 1 iteration
    assert mock_qa_controller.get_summary.call_count == 2  # Should be called twice


def test_fetch_material_add_sets_flow(
    test_pdf_folder, mock_qa_controller, mock_material_controller, mock_db_controller
):
    # Setup mock returns
    file_meta = MagicMock()
    file_meta.mc_question_sets = []
    file_meta.__getitem__.return_value = str(test_pdf_folder / "test.pdf")

    def append_mc_question_set_side_effect(file_id, question_set):
        file_meta.mc_question_sets.append(question_set)

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

    # Setup mock to return the question set
    mock_qa_controller.get_questions.return_value = question_set

    # Run the function
    fetch_material_add_sets()

    # Verify the flow
    mock_material_controller.fetch_material_folder.assert_called_once_with(Path("./pdf_data"))
    assert mock_qa_controller.get_questions.call_count == 2
    assert mock_material_controller.append_mc_question_set.call_count == 2
    assert len(file_meta.mc_question_sets) == 2


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
    file_meta.summaries = []
    file_meta.mc_question_sets = []
    file_meta.__getitem__.return_value = str(test_pdf_folder / "test.pdf")

    def append_mc_question_set_side_effect(file_id, question_set):
        file_meta.mc_question_sets.append(question_set)

    def append_summary_side_effect(file_id, summary):
        file_meta.summaries.append(summary)

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
        technical_details={"detail1": "value1"},
        implementation_steps=["step1", "step2"],
        requirements={"req1": "value1"},
        limitations=["limit1"],
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
    ]
    mock_qa_controller.get_questions.return_value = question_set

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
    assert len(file_meta.summaries) == 2  # Should have 2 summaries after 1 iteration
    assert mock_qa_controller.get_summary.call_count == 2  # Should be called twice
    assert len(file_meta.mc_question_sets) == 2  # Should have 2 question sets
    assert mock_qa_controller.get_questions.call_count == 2  # Should be called twice
    mock_material_controller.output_material_as_folder.assert_called_once()
