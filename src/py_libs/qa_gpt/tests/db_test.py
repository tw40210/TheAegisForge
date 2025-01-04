import shutil
from pathlib import Path

from src.py_libs.qa_gpt.core.controller.db_controller import (
    LocalDatabaseController,
    MaterialController,
)


def test_local_db():
    test_db_name = "test_local_db"
    test_local_db_controller = LocalDatabaseController(db_name=test_db_name)
    save_path = "material_1.questionSet_0"
    save_data = {"q": "QQ", "a": "AA"}
    test_local_db_controller.save_data(save_data, save_path)

    assert save_data == test_local_db_controller.get_data(save_path)

    update_data = {"c": "QQ", "a": "AA", "q": "QAQ"}
    test_local_db_controller.update_data(update_data, save_path)

    assert update_data == test_local_db_controller.get_data(save_path)

    test_local_db_controller.delete_data(save_path)

    assert test_local_db_controller.get_data(save_path) is None

    test_local_db_controller.db_path.unlink()


def test_local_material_controller_input():
    test_db_name = "test_local_db"
    test_archive_name = "test_archive"
    test_source_folder_path = Path("./test_data")
    test_local_db_controller = LocalDatabaseController(db_name=test_db_name)
    test_material_controller = MaterialController(
        db_controller=test_local_db_controller, archive_name=test_archive_name
    )

    test_material_controller.fetch_material_folder(test_source_folder_path)
    assert len(
        test_material_controller.db_controller.get_data(test_material_controller.db_table_name)
    ) == len(list(test_source_folder_path.iterdir()))
    assert len(list(test_material_controller.archive_path.iterdir())) == len(
        list(test_source_folder_path.iterdir())
    )

    shutil.rmtree(test_material_controller.archive_path)
    test_local_db_controller.db_path.unlink()


def test_local_material_controller_output():
    test_db_name = "test_local_output_db"
    test_archive_name = "test_archive"
    test_output_folder_path = Path("./test_output_question_data")
    test_output_folder_path.mkdir(exist_ok=True)

    test_local_db_controller = LocalDatabaseController(db_name=test_db_name)
    test_material_controller = MaterialController(
        db_controller=test_local_db_controller, archive_name=test_archive_name
    )
    test_material_controller.output_material_as_folder(test_output_folder_path)

    assert len(test_material_controller.get_material_table()) == len(
        list(test_output_folder_path.iterdir())
    )

    shutil.rmtree(test_output_folder_path)


if __name__ == "__main__":
    test_local_db()
    test_local_material_controller_input()
    test_local_material_controller_output()
