from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.py_libs.qa_gpt.core.controller.qa_controller import QAController
from src.py_libs.qa_gpt.core.objects.summaries import (
    BulletPoint,
    Conclusion,
    Motivation,
    StandardSummary,
    TechnicalSummary,
)


@pytest.fixture
def qa_controller():
    controller = QAController()
    # Mock the _pdf_to_text method to avoid file operations
    controller.preprocess_controller._pdf_to_text = MagicMock(return_value="Test PDF content")
    return controller


@pytest.fixture
def mock_standard_summary():
    return StandardSummary(
        motivation=Motivation(
            description="The motivation behind this material is to present information in a structured format that is easy to digest and analyze.",
            problem_to_solve="Test problem",
            how_to_solve="Test solution",
            why_can_be_solved="Test why",
        ),
        conclusion=Conclusion(
            description="Test conclusion",
            problem_to_solve="Test problem",
            how_much_is_solved="Test solution",
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


@pytest.fixture
def mock_technical_summary():
    return TechnicalSummary(
        overview="This technical document describes the implementation of a new machine learning algorithm",
        key_concepts=["Neural Networks", "Gradient Descent", "Backpropagation", "Loss Functions"],
        technical_details={
            "model_architecture": "Multi-layer perceptron with 3 hidden layers",
            "activation_function": "ReLU for hidden layers, Softmax for output",
            "optimization": "Adam optimizer with learning rate 0.001",
            "batch_size": "32 samples per batch",
        },
        implementation_steps=[
            "Data preprocessing and normalization",
            "Model architecture definition",
            "Training loop implementation",
            "Validation and testing procedures",
        ],
        requirements={
            "python": "3.8+",
            "tensorflow": "2.4+",
            "cuda": "11.0+",
            "ram": "16GB minimum",
        },
        limitations=[
            "High computational resource requirements",
            "Limited to supervised learning tasks",
            "Requires large labeled dataset",
        ],
    )


@patch("src.py_libs.qa_gpt.core.controller.qa_controller.get_chat_gpt_response_structure")
def test_get_standard_summary(mock_get_response, qa_controller, mock_standard_summary):
    # Set up the mock to return our mock_standard_summary
    mock_get_response.return_value = mock_standard_summary

    # Test getting a standard summary
    result = qa_controller.get_summary(Path("test.pdf"), StandardSummary)

    # Verify that the mock was called
    mock_get_response.assert_called_once()

    # Verify the result matches our mock
    assert result == mock_standard_summary
    assert isinstance(result, StandardSummary)
    assert isinstance(result.motivation, Motivation)
    assert isinstance(result.conclusion, Conclusion)
    assert len(result.bullet_points) == 1
    assert result.bullet_points[0].description == "Test description"
    assert result.bullet_points[0].technical_details == "Test details"
    assert result.bullet_points[0].importance == 1


@patch("src.py_libs.qa_gpt.core.controller.qa_controller.get_chat_gpt_response_structure")
def test_get_technical_summary(mock_get_response, qa_controller, mock_technical_summary):
    # Set up the mock
    mock_get_response.return_value = mock_technical_summary

    # Test getting a technical summary
    result = qa_controller.get_summary(Path("test.pdf"), TechnicalSummary)

    # Verify that the mock was called
    mock_get_response.assert_called_once()

    # Verify the result matches our mock
    assert result == mock_technical_summary
    assert isinstance(result, TechnicalSummary)
    assert result.overview.startswith("This technical document")
    assert "Neural Networks" in result.key_concepts
    assert "model_architecture" in result.technical_details
    assert len(result.implementation_steps) == 4
    assert "python" in result.requirements
    assert len(result.limitations) == 3


def test_summary_serialization(mock_standard_summary, mock_technical_summary):
    # Test standard summary serialization
    standard_dict = mock_standard_summary.model_dump()
    assert "summary_type" in standard_dict
    assert standard_dict["summary_type"] == "standard"
    assert "motivation" in standard_dict
    assert "conclusion" in standard_dict
    assert "bullet_points" in standard_dict
    assert len(standard_dict["bullet_points"]) == 1

    # Test technical summary serialization
    technical_dict = mock_technical_summary.model_dump()
    assert "overview" in technical_dict
    assert "key_concepts" in technical_dict
    assert "technical_details" in technical_dict
    assert "implementation_steps" in technical_dict
    assert "requirements" in technical_dict
    assert "limitations" in technical_dict
