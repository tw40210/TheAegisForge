
from src.py_libs.qa_gpt.core.utils.parsing_utils import pdf_to_text


def test_pdf_to_text():
    print(pdf_to_text("./test_data/test_input.pdf"))

if __name__ == "__main__":
    test_pdf_to_text()