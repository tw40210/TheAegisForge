# Installation
1. add `./src/py_libs/qa_gpt/chat/private_keys.py`
2. put pdf materials in a folder
3. python3.12 -m venv py_env
4. source py_env/bin/activate
5. python3.12 -m pip install -r requirements/requirments.txt

# Run
1. `streamlit run ./src/py_libs/qa_gpt/script/QA_ui.py`

# Object design
1. DatabaseController
    * Interact with static storage.
    * Like `.pkl` file as simple local db
2. MaterialController
    * Depend on `DatabaseController`
    * Fetch materials like `pdf` files.
    * Generate materials like `output json` files.

3. PreprocessController
    * Preprocess input text
4. QAController
    * Depend on `PreprocessController`
    * Interact with GPT api

