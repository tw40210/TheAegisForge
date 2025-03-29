from pathlib import Path

from src.py_libs.qa_gpt.core.controller.db_controller import (
    LocalDatabaseController,
    MaterialController,
)
from src.py_libs.qa_gpt.core.controller.qa_controller import QAController
from src.py_libs.qa_gpt.core.objects.summaries import StandardSummary, TechnicalSummary


def fetch_material_add_sets():
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
        current_num_sets = len(file_meta.mc_question_sets)
        while current_num_sets < 2:

            mc_question_set = qa_cotroller.get_questions(file_meta["file_path"])
            material_controller.append_mc_question_set(file_id, mc_question_set)
            updated_num_sets = len(file_meta.mc_question_sets)
            print(f"Material {file_id} have {updated_num_sets} questions now.")

            assert updated_num_sets == current_num_sets + 1
            current_num_sets = updated_num_sets


def fetch_material_add_summary():
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
        current_num_summaries = len(file_meta.summaries)
        adding_summary_objects = [StandardSummary, TechnicalSummary]
        while len(file_meta.summaries) < len(adding_summary_objects):
            print(f"Adding summary to material {file_id}.")
            for summary_object in adding_summary_objects:
                summary = qa_cotroller.get_summary(file_meta["file_path"], summary_object)
                material_controller.append_summary(file_id, summary)
            updated_num_summaries = len(file_meta.summaries)

            assert updated_num_summaries > current_num_summaries
            current_num_summaries = updated_num_summaries


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
    fetch_material_add_summary()
    fetch_material_add_sets()
    output_question_data()
