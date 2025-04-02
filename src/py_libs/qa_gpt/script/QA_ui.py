import json
import os

import streamlit as st

from src.py_libs.qa_gpt.core.utils.display_utils import (
    display_question,
    display_summary_beautifully,
    get_parsed_question,
)


def load_json_from_file(file_path):
    with open(file_path) as file:
        return json.load(file)


# Set wide mode
st.set_page_config(layout="wide")
_, col1, _, col2, _ = st.columns([1, 4, 1, 6, 1])

with col1:
    st.header("Material selection")
    folder_path = "output_question_data"

    search_query = st.text_input("Search material", "")
    material_folders = list(os.listdir(folder_path))

    fileted_material_folders = [
        material_folder
        for material_folder in material_folders
        if search_query.lower() in material_folder.lower()
    ]
    selected_material = st.selectbox("Select a material folder", fileted_material_folders)

    selected_file = None
    if selected_material:
        material_folder_path = os.path.join(folder_path, selected_material)
        files = [
            f
            for f in os.listdir(material_folder_path)
            if f.endswith(".json") and not f.startswith("meta_data") and not f.startswith("summary")
        ]

        selected_file = st.selectbox("Select a file", files)

    st.header("Question set")
    st.write("---")
    if selected_file is not None:
        file_path = os.path.join(material_folder_path, selected_file)
        questions = load_json_from_file(file_path)

        user_selections = []

        for question_key, question_set in questions.items():
            parsed_question = get_parsed_question(question_set)
            selected_options = display_question(
                parsed_question["question_description"], parsed_question["options"], question_key
            )
            user_selections.append(
                (
                    parsed_question["question_description"],
                    selected_options,
                    parsed_question["answers"],
                    parsed_question["explanation"],
                )
            )
            st.write("---")

        if st.button("Submit"):
            for question, selected, answers, explanations in user_selections:
                st.write(f"**{question}**")
                st.write(f"Your selection : {selected}")
                st.write(f"Correct answers : {answers}")
                st.write("Explanation : \n")
                for i in range(len(explanations)):
                    st.write(f"Option {i} is {i in answers}. {explanations[i]}\n")

                if set(selected) == set(answers):
                    st.success("All correct!")
                else:
                    st.error("Some options wrong.")
                st.write("---")


with col2:
    st.header("Material summary")
    if selected_material:
        material_folder_path = os.path.join(folder_path, selected_material)
        summary_files = [f for f in os.listdir(material_folder_path) if f.startswith("summary")]

        if summary_files:
            selected_summary = st.selectbox("Select summary type", summary_files)
            if selected_summary:
                summary_path = os.path.join(material_folder_path, selected_summary)
                summary = load_json_from_file(summary_path)
                display_summary_beautifully(summary, "Material Summary")
        else:
            st.write("No summary files found for this material.")
    else:
        st.write("No material selected.")
