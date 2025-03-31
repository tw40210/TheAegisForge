from pathlib import Path

from src.py_libs.qa_gpt.core.controller.db_controller import (
    LocalDatabaseController,
    MaterialController,
)
from src.py_libs.qa_gpt.core.controller.qa_controller import QAController
from src.py_libs.qa_gpt.core.objects.summaries import (
    InnovationSummary,
    StandardSummary,
    TechnicalSummary,
)

summary_objects = [
    StandardSummary,
    TechnicalSummary,
    InnovationSummary,
]


def fetch_material_add_sets():
    """Fetch material and add question sets to each material."""
    db_name = "my_local_db"
    archive_name = "my_archive"
    local_db_controller = LocalDatabaseController(db_name=db_name)
    material_controller = MaterialController(
        db_controller=local_db_controller, archive_name=archive_name
    )
    qa_cotroller = QAController()
    material_table = material_controller.get_material_table()

    total_materials = len(material_table)
    for material_idx, (file_id, file_meta) in enumerate(material_table.items(), 1):
        print(f"\nProcessing material {material_idx}/{total_materials} (ID: {file_id})")
        print(
            f"Material {file_id} originally have {len(file_meta.mc_question_sets)} mc_questions sets."
        )

        for summary_idx, summary_object in enumerate(summary_objects, 1):
            # Skip if summary type doesn't exist
            summary_type = summary_object.__name__
            if summary_type not in file_meta.summaries or file_meta.summaries[summary_type] is None:
                print(f"Skipping {summary_type} as it doesn't exist.")
                continue

            print(f"\nProcessing summary {summary_idx}/{len(summary_objects)}: {summary_type}")
            # Get the summary object
            summary = file_meta.summaries[summary_type]
            summary_dict = summary.model_dump()

            # Get questions for each top-level attribute
            total_fields = len(summary_dict)
            for field_idx, (field_name, field_value) in enumerate(summary_dict.items(), 1):
                print(f"Processing field {field_idx}/{total_fields}: {field_name}")
                # Create prefix for the question set
                prefix = f"{summary_type}_{field_name}"

                # Count existing question sets with this prefix
                existing_count = sum(
                    1 for key in file_meta.mc_question_sets.keys() if key.startswith(prefix)
                )
                if existing_count > 0:
                    print(
                        f"Skipping {prefix} as {existing_count} question set(s) already exist(s)."
                    )
                    continue

                # Get questions for this specific field
                question_set = qa_cotroller.get_questions(
                    file_meta["file_path"], field_name, field_value
                )
                material_controller.append_mc_question_set(file_id, question_set, prefix)
                print(f"Added question set for {prefix}")

        print(f"\nCompleted processing material {material_idx}/{total_materials} (ID: {file_id})")


def fetch_material_add_summary():
    """Fetch material and add summary to each material."""
    db_name = "my_local_db"
    archive_name = "my_archive"
    local_db_controller = LocalDatabaseController(db_name=db_name)
    material_controller = MaterialController(
        db_controller=local_db_controller, archive_name=archive_name
    )
    qa_cotroller = QAController()
    material_table = material_controller.get_material_table()

    total_materials = len(material_table)
    for material_idx, (file_id, file_meta) in enumerate(material_table.items(), 1):
        print(f"\nProcessing material {material_idx}/{total_materials} (ID: {file_id})")

        for summary_idx, summary_object in enumerate(summary_objects, 1):
            # Skip if summary type already exists
            summary_type = summary_object.__name__
            if (
                summary_type in file_meta.summaries
                and file_meta.summaries[summary_type] is not None
            ):
                print(f"Skipping {summary_type} as it already exists.")
                continue

            print(f"Processing summary {summary_idx}/{len(summary_objects)}: {summary_type}")
            summary = qa_cotroller.get_summary(file_meta["file_path"], summary_object)
            material_controller.append_summary(file_id, summary)
            print(f"Added summary for {summary_type}")

        print(f"\nCompleted processing material {material_idx}/{total_materials} (ID: {file_id})")


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
