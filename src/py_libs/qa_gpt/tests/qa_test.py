from pathlib import Path

from src.py_libs.qa_gpt.core.controller.qa_controller import QAController


def test_get_summary():
    test_file_path = Path("./test_data/test_input_2.pdf")

    qa_cotroller = QAController()
    _ = qa_cotroller.preprocess_controller.preprocess(test_file_path)
    _ = qa_cotroller.get_summary(test_file_path)
    print()


def test_get_questions():
    test_file_path = Path("./test_data/test_input_2.pdf")

    qa_cotroller = QAController()
    _ = qa_cotroller.preprocess_controller.preprocess(test_file_path)
    _ = qa_cotroller.get_questions(test_file_path)
    print()


if __name__ == "__main__":
    test_get_questions()
