from pathlib import Path

from src.py_libs.qa_gpt.core.controller.db_controller import (
    LocalDatabaseController,
    MaterialController,
)
from src.py_libs.qa_gpt.core.controller.qa_controller import QAController
from src.py_libs.qa_gpt.core.objects.materials import FileMeta


def main():
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

        file_meta: FileMeta
        question_set = qa_cotroller.get_questions(file_meta.file_path)
        material_controller.append_question_set(file_id, question_set)


if __name__ == "__main__":
    main()
