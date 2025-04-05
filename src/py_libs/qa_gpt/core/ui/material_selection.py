import os

import streamlit as st


def get_material_folders(folder_path: str, search_query: str) -> list[str]:
    """Get filtered material folders based on search query."""
    material_folders = list(os.listdir(folder_path))
    return [
        material_folder
        for material_folder in material_folders
        if search_query.lower() in material_folder.lower()
    ]


def get_question_files(material_folder_path: str) -> list[str]:
    """Get question files from a material folder."""
    return [
        f
        for f in os.listdir(material_folder_path)
        if f.endswith(".json") and not f.startswith("meta_data") and not f.startswith("summary")
    ]


def get_summary_files(material_folder_path: str) -> list[str]:
    """Get summary files from a material folder."""
    return [f for f in os.listdir(material_folder_path) if f.startswith("summary")]


def display_material_selection(folder_path: str) -> tuple[str | None, str | None]:
    """Display material selection UI and return selected material and file.

    Args:
        folder_path: Path to the folder containing materials

    Returns:
        Tuple containing:
        - Selected material folder path (or None if none selected)
        - Selected file name (or None if none selected)
    """
    st.header("Material selection")

    search_query = st.text_input("Search material", "")
    material_folders = get_material_folders(folder_path, search_query)
    selected_material = st.selectbox("Select a material folder", material_folders)

    selected_file = None
    material_folder_path = None

    if selected_material:
        material_folder_path = os.path.join(folder_path, selected_material)
        files = get_question_files(material_folder_path)
        selected_file = st.selectbox("Select a file", files)

    return material_folder_path, selected_file
