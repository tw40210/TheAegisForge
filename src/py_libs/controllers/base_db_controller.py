from abc import ABC, abstractmethod


class BaseDatabaseController(ABC):
    @abstractmethod
    def __init__(self, db_name: str):
        pass

    @abstractmethod
    def get_data(self, target_path: str) -> any:
        pass

    @abstractmethod
    def save_data(self, data: dict, target_path: str) -> int:
        pass

    @abstractmethod
    def delete_data(self, target_path: str) -> int:
        pass

    @abstractmethod
    def update_data(self, data: str, target_path: str) -> int:
        pass
