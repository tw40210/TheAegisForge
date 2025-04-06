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


async def fetch_material_add_sets():
    """Fetch material and add question sets to each material."""
    db_name = "my_local_db"
    archive_name = "my_archive"
    local_db_controller = LocalDatabaseController(db_name=db_name)
    material_controller = MaterialController(
        db_controller=local_db_controller, archive_name=archive_name
    )
    qa_controller = QAController()

    # Fetch material folder first
    material_controller.fetch_material_folder(Path("./pdf_data"))
    material_table = material_controller.get_material_table()

    total_materials = len(material_table)
    for material_idx, (file_id, file_meta) in enumerate(material_table.items(), 1):
        print(f"\nProcessing material {material_idx}/{total_materials} (ID: {file_id})")
        print(
            f"Material {file_id} originally have {len(file_meta.mc_question_sets)} mc_questions sets."
        )

        # Prepare batch processing data
        file_paths = []
        field_names = []
        field_values = []
        prefixes = []

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

                file_paths.append(file_meta["file_path"])
                field_names.append(field_name)
                field_values.append(field_value)
                prefixes.append(prefix)

        # Process all questions in batch
        if file_paths:
            question_sets = await qa_controller.get_questions_batch(
                file_paths, field_names, field_values
            )
            for prefix, question_set in zip(prefixes, question_sets):
                material_controller.append_mc_question_set(file_id, question_set, prefix)
                print(f"Added question set for {prefix}")

        print(f"\nCompleted processing material {material_idx}/{total_materials} (ID: {file_id})")


async def fetch_material_add_summary():
    """Fetch material and add summary to each material."""
    db_name = "my_local_db"
    archive_name = "my_archive"
    local_db_controller = LocalDatabaseController(db_name=db_name)
    material_controller = MaterialController(
        db_controller=local_db_controller, archive_name=archive_name
    )
    qa_controller = QAController()

    # Fetch material folder first
    material_controller.fetch_material_folder(Path("./pdf_data"))
    material_table = material_controller.get_material_table()

    total_materials = len(material_table)
    for material_idx, (file_id, file_meta) in enumerate(material_table.items(), 1):
        print(f"\nProcessing material {material_idx}/{total_materials} (ID: {file_id})")

        # Prepare batch processing data
        file_paths = []
        summary_classes = []
        summary_types = []

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
            file_paths.append(file_meta["file_path"])
            summary_classes.append(summary_object)
            summary_types.append(summary_type)

        # Process all summaries in batch
        if file_paths:
            summaries = await qa_controller.get_summaries_batch(file_paths, summary_classes)
            for summary_type, summary in zip(summary_types, summaries):
                material_controller.append_summary(file_id, summary)
                print(f"Added summary for {summary_type}")

        print(f"\nCompleted processing material {material_idx}/{total_materials} (ID: {file_id})")


def output_question_data():
    """Output question data to a folder."""
    db_name = "my_local_db"
    archive_name = "my_archive"
    local_db_controller = LocalDatabaseController(db_name=db_name)
    material_controller = MaterialController(
        db_controller=local_db_controller, archive_name=archive_name
    )
    output_folder_path = Path("./output_question_data")
    output_folder_path.mkdir(exist_ok=True)

    material_controller.output_material_as_folder(output_folder_path)
