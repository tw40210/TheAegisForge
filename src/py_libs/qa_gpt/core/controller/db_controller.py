import logging
import pickle
from abc import ABC, abstractmethod
from pathlib import Path

from src.py_libs.qa_gpt.core.constant import LOCAL_DB_FOLDER, MATERIAL_FOLDER

logger = logging.getLogger(__name__)


class BasicDatabaseController(ABC):
    @abstractmethod
    def __init__(self, db_name: str):
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
    def __init__(self, db_name: str = "local_db") -> None:
        self.db_folder_path = Path(f"{LOCAL_DB_FOLDER}")
        self.db_path = Path(f"{LOCAL_DB_FOLDER}/{db_name}.pkl")
        self.db = {}
        self.db_folder_path.mkdir(exist_ok=True)

        self._init_local_df()

    def _init_local_df(self) -> None:
        if self.db_path.exists():
            with open(str(self.db_path), "rb") as db_file:
                self.db = pickle.load(db_file)

    def _commit(self) -> int:
        with open(str(self.db_path), "wb") as db_file:
            pickle.dump(self.db, db_file)

        return 0

    def _query_path(self, target_path: str, create_path: bool = False):
        prev = None
        leaf_key = None
        cur = self.db
        for key in target_path.split("."):
            if key not in cur:
                if create_path:
                    cur[key] = {}
                else:
                    return {}, None, leaf_key
            prev = cur
            leaf_key = key
            cur = cur[key]
        return prev, cur, leaf_key

    def get_data(self, target_path: str) -> any:
        prev, cur, leaf_key = self._query_path(target_path)

        if leaf_key in prev:
            logger.info(f"Got {target_path}.")
        else:
            logger.warning(f"{target_path} is not found. Nothing gotten.")

        return cur

    def save_data(self, data: dict, target_path: str) -> int:
        prev, _, leaf_key = self._query_path(target_path, create_path=True)
        prev[leaf_key] = data

        self._commit()
        logger.info(f"{target_path} is newly saved.")

        return 0

    def delete_data(self, target_path: str) -> int:
        prev, _, leaf_key = self._query_path(target_path)
        if leaf_key in prev:
            prev.pop(leaf_key)
            self._commit()
            logger.info(f"{target_path} is deleted.")
        else:
            logger.warning(f"{target_path} is not found. Nothing deleted.")

        return 0

    def update_data(self, data: str, target_path: str) -> int:
        self.delete_data(target_path)
        self.save_data(data, target_path)

        self._commit()
        logger.info(f"{target_path} is updated.")

        return 0


class MaterialController:
    def __init__(self, df_controller: BasicDatabaseController, archive_name: str) -> None:
        self.df_controller = df_controller
        self.material_folder_path = Path(MATERIAL_FOLDER)
        self.archive_path = Path(f"{MATERIAL_FOLDER}/{archive_name}")
        self.db_table_name = "material_table"
        self.db_mapping_table_name = "material_id_mapping_table"
        self.material_folder_path.mkdir(exist_ok=True)
        self.archive_path.mkdir(exist_ok=True)

    def _fetch_material_folder(self, source_folder_path: Path):

        print()
