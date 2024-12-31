import pickle
from abc import ABC, abstractmethod
from pathlib import Path


class BasicDatabaseController(ABC):
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def get_data(self, target_id: str) -> dict:
        pass

    @abstractmethod
    def save_data(self, data: dict) -> int:
        pass

    @abstractmethod
    def delete_data(self, file_name: str, question_set_id: str) -> int:
        pass

    @abstractmethod
    def update_data(self, data: str, file_name: str, question_set_id: str) -> int:
        pass


class LocalDatabaseController(BasicDatabaseController):
    def __init__(self, db_path: str = "./local_db.pkl") -> None:
        db_path = Path(db_path)
        self.db_path = db_path
        self.db = {}
        self._init_local_df()

    def _init_local_df(self) -> None:
        if self.db_path.exists():
            with open(str(self.db_path), "rb") as db_file:
                self.db = pickle.load(db_file)

    def get_data(self, file_name: str, question_set_id: str) -> dict:
        question_sets = self.db.get(file_name, {})
        question_set = question_sets.get(question_set_id, {})

        return question_set

    def save_data(self, data: dict, file_name: str, question_set_id: str) -> int:
        if file_name not in self.db:
            self.db[file_name] = {}

        self.db[file_name][question_set_id] = data

        return 0

    def delete_data(self, file_name: str, question_set_id: str) -> int:
        if file_name in self.db and question_set_id in self.db[file_name]:
            self.db[file_name].pop(question_set_id)

        return 0

    def update_data(self, data: str, file_name: str, question_set_id: str) -> int:
        self.delete_data(file_name, question_set_id)
        self.save_data(data, file_name, question_set_id)

        return 0
