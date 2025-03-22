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
    Summary,
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
        why_can_be_solved="Test reasoning",
    )
    conclusion = Conclusion(
        description="Test conclusion",
        problem_to_solve="Test problem",
        how_much_is_solved="Test progress",
        contribution="Test contribution",
    )
    bullet_point = BulletPoint(
        subject="Test subject",
        description="Test description",
        technical_details="Test details",
        importance_explanation="Test importance",
        importance=1,
    )
    return Summary(
        motivation=motivation, conclusion=conclusion, content_bullet_points=[bullet_point]
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
