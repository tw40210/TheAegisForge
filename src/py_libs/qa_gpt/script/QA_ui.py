import json
import os

import streamlit as st


def load_questions_from_file(file_path):
    with open(file_path) as file:
        return json.load(file)


def get_parsed_question(question_object) -> dict:
    parsed_question = {}
    choices = ["choice_1", "choice_2", "choice_3", "choice_4"]
    parsed_question["question_description"] = question_object["question_description"]
    parsed_question["options"] = [
        question_object[choice]["choice_description"] for choice in choices
    ]
    parsed_question["answers"] = [
        idx for idx, choice in enumerate(choices) if question_object[choice]["answer"]
    ]
    parsed_question["explanation"] = [question_object[choice]["explanation"] for choice in choices]

    return parsed_question


def display_question(question, options, question_key):
    st.write(question)
    selected_options = []

    for idx, option in enumerate(options):
        if st.checkbox(option, key=f"{question_key}_{option}"):
            selected_options.append(idx)

    return selected_options


# Set wide mode
st.set_page_config(layout="wide")
_, col1, _, col2, _ = st.columns([1, 4, 1, 6, 1])

with col1:
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
            if f.endswith(".json") and not f.startswith("meta_data")
        ]

        selected_file = st.selectbox("Select a file", files)

    if selected_file:
        file_path = os.path.join(material_folder_path, selected_file)
        questions = load_questions_from_file(file_path)

        user_selections = []

        st.write("---")

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
    st.write("This is col2")
