import json
import os

import streamlit as st


def load_questions_from_file(file_path):
    with open(file_path) as file:
        return json.load(file)


def display_question(question, options, question_index):
    st.write(question)
    selected_options = []

    for option in options:
        if st.checkbox(option, key=f"{question_index}_{option}"):
            selected_options.append(option)

    return selected_options


folder_path = "qa_data"

files = [f for f in os.listdir(folder_path) if f.endswith(".json")]
search_query = st.text_input("Search file", "")
fileted_files = [f for f in files if search_query.lower() in f.lower()]
selected_file = st.selectbox("Select a file", fileted_files)

if selected_file:
    file_path = os.path.join(folder_path, selected_file)
    questions = load_questions_from_file(file_path)

    user_selections = []

    for i, q in enumerate(questions):
        selected_options = display_question(q["question"], q["options"], i)
        user_selections.append((q["question"], selected_options, q["correct_answers"]))
        st.write("---")

    if st.button("Submit"):
        for question, selected, correct in user_selections:
            st.write(f"**{question}**")
            st.write(f"Your selection : {selected}")
            st.write(f"Correct answers : {correct}")

            if set(selected) == set(correct):
                st.success("All correct!")
            else:
                st.error("Some options wrong.")
            st.write("---")
