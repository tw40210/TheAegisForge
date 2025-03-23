import json
import shutil
from pathlib import Path

import pytest

from src.py_libs.qa_gpt.core.controller.db_controller import (
    LocalDatabaseController,
    MaterialController,
)
from src.py_libs.qa_gpt.core.objects.materials import FileMeta
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


@pytest.fixture
def test_db_controller():
    db_name = "test_material_db"
    controller = LocalDatabaseController(db_name=db_name)
    yield controller
    # Cleanup
    controller.db_path.unlink()


@pytest.fixture
def test_material_controller(test_db_controller):
    archive_name = "test_material_archive"
    controller = MaterialController(db_controller=test_db_controller, archive_name=archive_name)
    yield controller
    # Cleanup
    shutil.rmtree(controller.archive_path, ignore_errors=True)


@pytest.fixture
def sample_choice():
    return Choice(choice_description="Test choice", answer=True, explanation="Test explanation")


@pytest.fixture
def sample_question(sample_choice):
    return MultipleChoiceQuestion(
        question_description="Test question",
        choice_1=sample_choice,
        choice_2=sample_choice,
        choice_3=sample_choice,
        choice_4=sample_choice,
    )


@pytest.fixture
def sample_question_set(sample_question):
    return MultipleChoiceQuestionSet(
        question_1=sample_question,
        question_2=sample_question,
        question_3=sample_question,
        question_4=sample_question,
        question_5=sample_question,
    )


@pytest.fixture
def sample_summary():
    motivation = Motivation(
        description="Test motivation",
        problem_to_solve="Test problem",
        how_to_solve="Test solution",
        why_can_be_solved="Test why",
    )
    conclusion = Conclusion(
        description="Test conclusion",
        problem_to_solve="Test problem",
        how_much_is_solved="Test solution",
        contribution="Test contribution",
    )
    bullet_point = BulletPoint(
        subject="Test subject",
        description="Test description",
        technical_details="Test details",
        importance_explanation="Test importance",
        importance=1,
    )
    return StandardSummary(
        motivation=motivation, conclusion=conclusion, bullet_points=[bullet_point]
    )


@pytest.fixture
def sample_technical_summary():
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


def test_material_controller_initialization(test_material_controller):
    assert test_material_controller.db_table_name == "material_table"
    assert test_material_controller.db_mapping_table_name == "material_id_mapping_table"
    assert test_material_controller.archive_path.exists()
    assert (
        test_material_controller.db_controller.get_data(test_material_controller.db_table_name)
        is not None
    )
    assert (
        test_material_controller.db_controller.get_data(
            test_material_controller.db_mapping_table_name
        )
        is not None
    )


def test_remove_dot_from_file_name():
    test_path = Path("test.file.name.pdf")
    new_path = MaterialController.remove_dot_from_file_name(test_path)
    assert new_path.name == "test_file_name.pdf"


def test_append_mc_question_set(test_material_controller, sample_question_set):
    # First create a file meta
    file_meta = FileMeta(
        id=0,
        file_name="test_file",
        file_suffix=".pdf",
        file_path=Path("test_file.pdf"),
        mc_question_sets={},
        summary=None,
    )
    test_material_controller.db_controller.save_data(
        file_meta,
        test_material_controller.db_controller.get_target_path(
            [test_material_controller.db_table_name, "0"]
        ),
    )

    # Test appending question set
    result = test_material_controller.append_mc_question_set(0, sample_question_set)
    assert result == 0

    # Verify the question set was saved
    updated_meta = test_material_controller.db_controller.get_data(
        test_material_controller.db_controller.get_target_path(
            [test_material_controller.db_table_name, "0"]
        )
    )
    assert "0" in updated_meta["mc_question_sets"]
    assert updated_meta["mc_question_sets"]["0"] == sample_question_set


def test_append_summary(test_material_controller, sample_summary):
    # First create a file meta
    file_meta = FileMeta(
        id=0,
        file_name="test_file",
        file_suffix=".pdf",
        file_path=Path("test_file.pdf"),
        mc_question_sets={},
        summary=None,
    )
    test_material_controller.db_controller.save_data(
        file_meta,
        test_material_controller.db_controller.get_target_path(
            [test_material_controller.db_table_name, "0"]
        ),
    )

    # Test appending summary
    result = test_material_controller.append_summary(0, sample_summary)
    assert result == 0

    # Verify the summary was saved
    updated_meta = test_material_controller.db_controller.get_data(
        test_material_controller.db_controller.get_target_path(
            [test_material_controller.db_table_name, "0"]
        )
    )
    assert updated_meta["summary"] == sample_summary
    assert isinstance(updated_meta["summary"], StandardSummary)
    assert updated_meta["summary"].motivation.description == "Test motivation"
    assert updated_meta["summary"].conclusion.description == "Test conclusion"
    assert len(updated_meta["summary"].bullet_points) == 1
    assert updated_meta["summary"].bullet_points[0].description == "Test description"


def test_append_technical_summary(test_material_controller, sample_technical_summary):
    # First create a file meta
    file_meta = FileMeta(
        id=0,
        file_name="test_file",
        file_suffix=".pdf",
        file_path=Path("test_file.pdf"),
        mc_question_sets={},
        summary=None,
    )
    test_material_controller.db_controller.save_data(
        file_meta,
        test_material_controller.db_controller.get_target_path(
            [test_material_controller.db_table_name, "0"]
        ),
    )

    # Test appending technical summary
    result = test_material_controller.append_summary(0, sample_technical_summary)
    assert result == 0

    # Verify the technical summary was saved
    updated_meta = test_material_controller.db_controller.get_data(
        test_material_controller.db_controller.get_target_path(
            [test_material_controller.db_table_name, "0"]
        )
    )
    assert updated_meta["summary"] == sample_technical_summary
    assert isinstance(updated_meta["summary"], TechnicalSummary)
    assert (
        updated_meta["summary"].overview
        == "This technical document describes the implementation of a new machine learning algorithm"
    )
    assert "Neural Networks" in updated_meta["summary"].key_concepts
    assert "model_architecture" in updated_meta["summary"].technical_details


def test_get_material_table(test_material_controller):
    # Create some test data
    file_meta = FileMeta(
        id=0,
        file_name="test_file",
        file_suffix=".pdf",
        file_path=Path("test_file.pdf"),
        mc_question_sets={},
        summary=None,
    )
    test_material_controller.db_controller.save_data(
        file_meta,
        test_material_controller.db_controller.get_target_path(
            [test_material_controller.db_table_name, "0"]
        ),
    )

    # Test getting material table
    material_table = test_material_controller.get_material_table()
    assert "0" in material_table
    assert material_table["0"] == file_meta


def test_get_material_mapping_table(test_material_controller):
    # Create some test data
    test_material_controller.db_controller.save_data(
        0,
        test_material_controller.db_controller.get_target_path(
            [test_material_controller.db_mapping_table_name, "test_file"]
        ),
    )

    # Test getting mapping table
    mapping_table = test_material_controller.get_material_mapping_table()
    assert "test_file" in mapping_table
    assert mapping_table["test_file"] == 0


def test_output_material_as_folder(test_material_controller, sample_question_set, sample_summary):
    # Create test data
    file_meta = FileMeta(
        id=0,
        file_name="test_file",
        file_suffix=".pdf",
        file_path=Path("test_file.pdf"),
        mc_question_sets={"0": sample_question_set},
        summary=sample_summary,
    )
    test_material_controller.db_controller.save_data(
        file_meta,
        test_material_controller.db_controller.get_target_path(
            [test_material_controller.db_table_name, "0"]
        ),
    )

    # Create output directory
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)

    # Test output
    result = test_material_controller.output_material_as_folder(output_dir)
    assert result == 0

    # Verify output files
    material_dir = output_dir / "test_file"
    assert material_dir.exists()
    assert (material_dir / "meta_data.json").exists()
    assert (material_dir / "summary.json").exists()
    assert (material_dir / "mc_question_0.json").exists()

    # Verify summary.json contains standard summary data
    with open(material_dir / "summary.json") as f:
        summary_data = json.load(f)
        assert "summary_type" in summary_data
        assert summary_data["summary_type"] == "standard"
        assert "motivation" in summary_data
        assert "conclusion" in summary_data
        assert "bullet_points" in summary_data
        assert len(summary_data["bullet_points"]) == 1
        assert summary_data["motivation"]["description"] == "Test motivation"
        assert summary_data["conclusion"]["description"] == "Test conclusion"

    # Cleanup
    shutil.rmtree(output_dir)


def test_output_material_with_technical_summary(test_material_controller, sample_technical_summary):
    # Create test data with technical summary
    file_meta = FileMeta(
        id=0,
        file_name="test_file",
        file_suffix=".pdf",
        file_path=Path("test_file.pdf"),
        mc_question_sets={},
        summary=sample_technical_summary,
    )
    test_material_controller.db_controller.save_data(
        file_meta,
        test_material_controller.db_controller.get_target_path(
            [test_material_controller.db_table_name, "0"]
        ),
    )

    # Create output directory
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)

    # Test output
    result = test_material_controller.output_material_as_folder(output_dir)
    assert result == 0

    # Verify output files
    material_dir = output_dir / "test_file"
    assert material_dir.exists()
    assert (material_dir / "meta_data.json").exists()
    assert (material_dir / "summary.json").exists()

    # Verify summary.json contains technical summary data
    with open(material_dir / "summary.json") as f:
        summary_data = json.load(f)
        assert "overview" in summary_data
        assert "key_concepts" in summary_data
        assert "technical_details" in summary_data
        assert "implementation_steps" in summary_data
        assert "requirements" in summary_data
        assert "limitations" in summary_data
        assert (
            summary_data["overview"]
            == "This technical document describes the implementation of a new machine learning algorithm"
        )
        assert "Neural Networks" in summary_data["key_concepts"]
        assert "model_architecture" in summary_data["technical_details"]

    # Cleanup
    shutil.rmtree(output_dir)


def test_remove_material_by_filename(test_material_controller):
    # Create test data
    file_name = "test_file"
    file_meta = FileMeta(
        id=0,
        file_name=file_name,
        file_suffix=".pdf",
        file_path=test_material_controller.archive_path / f"{file_name}_0.pdf",
        mc_question_sets={},
        summary=None,
    )

    # Save file meta to material table
    test_material_controller.db_controller.save_data(
        file_meta,
        test_material_controller.db_controller.get_target_path(
            [test_material_controller.db_table_name, "0"]
        ),
    )

    # Save mapping
    test_material_controller.db_controller.save_data(
        0,
        test_material_controller.db_controller.get_target_path(
            [test_material_controller.db_mapping_table_name, file_name]
        ),
    )

    # Create a dummy file
    file_meta["file_path"].touch()

    # Test removing the material
    result = test_material_controller.remove_material_by_filename(file_name)
    assert result == 0

    # Verify the file is deleted
    assert not file_meta["file_path"].exists()

    # Verify material table entry is deleted
    material_table = test_material_controller.get_material_table()
    assert "0" not in material_table

    # Verify mapping table entry is deleted
    mapping_table = test_material_controller.get_material_mapping_table()
    assert file_name not in mapping_table


def test_remove_material_by_filename_not_found(test_material_controller):
    # Test removing non-existent material
    result = test_material_controller.remove_material_by_filename("nonexistent_file")
    assert result == -1

    # Verify no changes were made to the tables
    material_table = test_material_controller.get_material_table()
    mapping_table = test_material_controller.get_material_mapping_table()
    assert material_table == {}
    assert mapping_table == {}


def test_remove_material_by_filename_with_associated_data(
    test_material_controller, sample_question_set, sample_summary
):
    # Create test data with associated question set and summary
    file_name = "test_file"
    file_meta = FileMeta(
        id=0,
        file_name=file_name,
        file_suffix=".pdf",
        file_path=test_material_controller.archive_path / f"{file_name}_0.pdf",
        mc_question_sets={"0": sample_question_set},
        summary=sample_summary,
    )

    # Save file meta to material table
    test_material_controller.db_controller.save_data(
        file_meta,
        test_material_controller.db_controller.get_target_path(
            [test_material_controller.db_table_name, "0"]
        ),
    )

    # Save mapping
    test_material_controller.db_controller.save_data(
        0,
        test_material_controller.db_controller.get_target_path(
            [test_material_controller.db_mapping_table_name, file_name]
        ),
    )

    # Create a dummy file
    file_meta["file_path"].touch()

    # Test removing the material
    result = test_material_controller.remove_material_by_filename(file_name)
    assert result == 0

    # Verify the file is deleted
    assert not file_meta["file_path"].exists()

    # Verify material table entry is deleted
    material_table = test_material_controller.get_material_table()
    assert "0" not in material_table

    # Verify mapping table entry is deleted
    mapping_table = test_material_controller.get_material_mapping_table()
    assert file_name not in mapping_table


def test_remove_material_with_technical_summary(test_material_controller, sample_technical_summary):
    # Create test data with technical summary
    file_name = "test_file"
    file_meta = FileMeta(
        id=0,
        file_name=file_name,
        file_suffix=".pdf",
        file_path=test_material_controller.archive_path / f"{file_name}_0.pdf",
        mc_question_sets={},
        summary=sample_technical_summary,
    )

    # Save file meta to material table
    test_material_controller.db_controller.save_data(
        file_meta,
        test_material_controller.db_controller.get_target_path(
            [test_material_controller.db_table_name, "0"]
        ),
    )

    # Save mapping
    test_material_controller.db_controller.save_data(
        0,
        test_material_controller.db_controller.get_target_path(
            [test_material_controller.db_mapping_table_name, file_name]
        ),
    )

    # Create a dummy file
    file_meta["file_path"].touch()

    # Test removing the material
    result = test_material_controller.remove_material_by_filename(file_name)
    assert result == 0

    # Verify the file is deleted
    assert not file_meta["file_path"].exists()

    # Verify material table entry is deleted
    material_table = test_material_controller.get_material_table()
    assert "0" not in material_table

    # Verify mapping table entry is deleted
    mapping_table = test_material_controller.get_material_mapping_table()
    assert file_name not in mapping_table
