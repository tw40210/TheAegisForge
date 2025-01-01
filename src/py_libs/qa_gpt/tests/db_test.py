from src.py_libs.qa_gpt.core.controller.db_controller import LocalDatabaseController


def test_local_db():
    test_db_name = "test_local_db"
    test_local_db_controller = LocalDatabaseController(name=test_db_name)
    save_path = "material_1.questionSet_0"
    save_data = {"q": "QQ", "a": "AA"}
    test_local_db_controller.save_data(save_data, save_path)

    assert save_data == test_local_db_controller.get_data(save_path)

    update_data = {"c": "QQ", "a": "AA", "q": "QAQ"}
    test_local_db_controller.update_data(update_data, save_path)

    assert update_data == test_local_db_controller.get_data(save_path)

    test_local_db_controller.delete_data(save_path)

    assert test_local_db_controller.get_data(save_path) is None

    test_local_db_controller.db_path.unlink()


if __name__ == "__main__":
    test_local_db()
