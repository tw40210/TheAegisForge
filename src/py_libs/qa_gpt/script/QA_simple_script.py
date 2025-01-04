from pathlib import Path

from src.py_libs.qa_gpt.core.controller.db_controller import (
    LocalDatabaseController,
    MaterialController,
)
from src.py_libs.qa_gpt.core.controller.qa_controller import QAController


def fetch_material_add_to_3_sets():
    db_name = "my_local_db"
    archive_name = "my_archive"
    source_folder_path = Path("./pdf_data")
    local_db_controller = LocalDatabaseController(db_name=db_name)
    material_controller = MaterialController(
        db_controller=local_db_controller, archive_name=archive_name
    )
    qa_cotroller = QAController()

    material_controller.fetch_material_folder(source_folder_path)

    for file_id, file_meta in material_controller.get_material_table().items():
        print(
            f"Material {file_id} originally have {len(file_meta.mc_question_sets)} mc_questions sets."
        )
        while len(file_meta.mc_question_sets) < 3:

            mc_question_set = qa_cotroller.get_questions(file_meta["file_path"])
            material_controller.append_mc_question_set(file_id, mc_question_set)
            print(f"Material {file_id} have {len(file_meta.mc_question_sets)} questions now.")


def output_question_data():
    db_name = "my_local_db"
    archive_name = "my_archive"
    local_db_controller = LocalDatabaseController(db_name=db_name)
    material_controller = MaterialController(
        db_controller=local_db_controller, archive_name=archive_name
    )
    output_folder_path = Path("./output_question_data")
    output_folder_path.mkdir(exist_ok=True)

    material_controller.output_material_as_folder(output_folder_path)


if __name__ == "__main__":
    fetch_material_add_to_3_sets()
    output_question_data()
