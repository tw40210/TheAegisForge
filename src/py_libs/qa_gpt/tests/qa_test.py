from pathlib import Path

from src.py_libs.qa_gpt.core.controller.qa_controller import QAController
from src.py_libs.qa_gpt.core.objects.summaries import StandardSummary


def test_get_summary():
    test_file_path = Path("./test_data/test_input_2.pdf")

    qa_cotroller = QAController()
    _ = qa_cotroller.preprocess_controller.preprocess(test_file_path)
    _ = qa_cotroller.get_summary(test_file_path, StandardSummary)
    print()


def test_get_questions():
    test_file_path = Path("./test_data/test_input_2.pdf")

    qa_cotroller = QAController()
    preprocess_result = qa_cotroller.preprocess_controller.preprocess(test_file_path)
    assert preprocess_result is not None

    result = qa_cotroller.get_questions(test_file_path)
    assert result is not None


if __name__ == "__main__":
    test_get_questions()
