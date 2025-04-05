import json
from pathlib import Path

import streamlit as st

from src.py_libs.qa_gpt.core.ui.material_selection import display_material_selection
from src.py_libs.qa_gpt.core.ui.question_display import (
    display_question_results,
    display_questions,
    load_questions,
)
from src.py_libs.qa_gpt.core.ui.summary_display import display_summary
from src.py_libs.qa_gpt.core.utils.fetch_utils import (
    fetch_material_add_sets,
    fetch_material_add_summary,
    output_question_data,
)


def load_json_from_file(file_path):
    with open(file_path) as file:
        return json.load(file)


def handle_file_upload():
    """Handle file upload with validation and process using fetch functions."""
    uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

    if uploaded_file is not None:
        # Check if file is PDF
        if not uploaded_file.name.lower().endswith(".pdf"):
            st.error("Please upload a PDF file")
            return

        # Create pdf_data directory if it doesn't exist
        pdf_data_path = Path("./pdf_data")
        pdf_data_path.mkdir(exist_ok=True)

        # Check for duplicate file names
        file_path = pdf_data_path / uploaded_file.name
        if file_path.exists():
            st.error(f"A file with name '{uploaded_file.name}' already exists")
            return

        # Save the file
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Show warning about processing time
        st.warning("⚠️ Processing the file might take several minutes. Please wait...")

        # Process the uploaded file using fetch functions
        with st.spinner("Processing the uploaded file..."):
            fetch_material_add_summary()
            fetch_material_add_sets()
            output_question_data()

        st.success(f"File '{uploaded_file.name}' uploaded and processed successfully")


# Set wide mode
st.set_page_config(layout="wide")
_, col1, _, col2, _ = st.columns([1, 4, 1, 6, 1])

# Constants
FOLDER_PATH = "output_question_data"

with col1:
    # Add file upload functionality
    handle_file_upload()

    # Display material selection and get selected material and file
    material_folder_path, selected_file = display_material_selection(FOLDER_PATH)

    # Display questions if a file is selected
    if selected_file:
        file_path = f"{material_folder_path}/{selected_file}"
        questions = load_questions(file_path)
        user_selections = display_questions(questions)
        display_question_results(user_selections)

with col2:
    # Display summary
    display_summary(material_folder_path)
