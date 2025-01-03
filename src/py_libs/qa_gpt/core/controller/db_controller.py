import logging
import pickle
import shutil
from abc import ABC, abstractmethod
from pathlib import Path

from src.py_libs.qa_gpt.core.constant import LOCAL_DB_FOLDER, MATERIAL_FOLDER
from src.py_libs.qa_gpt.core.objects.materials import FileMeta
from src.py_libs.qa_gpt.core.objects.questions import MultipleChoiceQuestionSet

logger = logging.getLogger(__name__)


class BasicDatabaseController(ABC):
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
        logger.debug(f"Try to get `{target_path}`.")

        prev, cur, leaf_key = self._query_path(target_path)

        return cur

    def save_data(self, data: dict, target_path: str) -> int:
        prev, _, leaf_key = self._query_path(target_path, create_path=True)
        prev[leaf_key] = data

        self._commit()
        logger.debug(f"`{target_path}` is newly saved.")

        return 0

    def delete_data(self, target_path: str) -> int:
        prev, _, leaf_key = self._query_path(target_path)
        if leaf_key in prev:
            prev.pop(leaf_key)
            self._commit()
            logger.debug(f"`{target_path}` is deleted.")
        else:
            logger.warning(f"`{target_path}` is not found. Nothing deleted.")

        return 0

    def update_data(self, data: str, target_path: str) -> int:
        self.delete_data(target_path)
        self.save_data(data, target_path)

        self._commit()
        logger.debug(f"`{target_path}` is updated.")

        return 0

    @staticmethod
    def get_target_path(path_list: list[str]) -> str:
        return ".".join(path_list)


class MaterialController:
    def __init__(self, db_controller: BasicDatabaseController, archive_name: str) -> None:
        self.db_controller = db_controller
        self.material_folder_path = Path(MATERIAL_FOLDER)
        self.archive_path = Path(f"{MATERIAL_FOLDER}/{archive_name}")
        self.db_table_name = "material_table"
        self.db_mapping_table_name = "material_id_mapping_table"
        self.material_folder_path.mkdir(exist_ok=True)
        self.archive_path.mkdir(exist_ok=True)

        # init in db
        if self.db_controller.get_data(self.db_table_name) is None:
            self.db_controller.save_data({}, self.db_table_name)
        if self.db_controller.get_data(self.db_mapping_table_name) is None:
            self.db_controller.save_data({}, self.db_mapping_table_name)

    @staticmethod
    def remove_dot_from_file_name(file_path: Path) -> Path:
        # We don't allow "." in file names since it's used in db query
        new_file_name = file_path.stem.replace(".", "_") + file_path.suffix
        new_file_path = file_path.parent / Path(new_file_name)

        return new_file_path

    def fetch_material_folder(self, source_folder_path: Path):
        archive_file_id = len(self.db_controller.get_data(self.db_mapping_table_name))

        for file_path in sorted(source_folder_path.iterdir()):
            if (
                not str(file_path).endswith(".pdf")
                or self.db_controller.get_data(
                    LocalDatabaseController.get_target_path(
                        [self.db_mapping_table_name, file_path.stem]
                    )
                )
                is not None
            ):
                continue

            # Rename the file in case there is an illegal name.
            new_file_path = MaterialController.remove_dot_from_file_name(file_path)
            file_path.rename(new_file_path)
            file_path = new_file_path

            file_meta = {}
            file_meta["id"] = archive_file_id
            file_meta["file_name"] = file_path.stem
            file_meta["file_suffix"] = file_path.suffix
            file_meta["file_path"] = self.archive_path / Path(
                f"archived_file_{archive_file_id}{file_path.suffix}"
            )
            file_meta["mc_question_sets"] = {}

            db_path = LocalDatabaseController.get_target_path(
                [self.db_table_name, str(archive_file_id)]
            )
            db_mapping_path = LocalDatabaseController.get_target_path(
                [self.db_mapping_table_name, file_meta["file_name"]]
            )

            self.db_controller.save_data(file_meta, db_path)
            self.db_controller.save_data(archive_file_id, db_mapping_path)

            shutil.copy(file_path, file_meta["file_path"])

            logger.info(f"{file_path.stem} is archived with id:{archive_file_id}.")

            archive_file_id += 1

    def append_mc_question_set(self, file_id: int, question_set: MultipleChoiceQuestionSet) -> int:
        target_path = LocalDatabaseController.get_target_path([self.db_table_name, str(file_id)])
        file_meta = self.db_controller.get_data(target_path)
        mc_question_sets = file_meta["mc_question_sets"]
        question_set_id = len(mc_question_sets)

        file_meta["mc_question_sets"][str(question_set_id)] = question_set

        self.db_controller.save_data(file_meta, target_path)
        return 0

    def get_material_table(self) -> dict[str, FileMeta]:
        return self.db_controller.get_data(self.db_table_name)

    def get_material_mapping_table(self) -> dict:
        return self.db_controller.get_data(self.db_mapping_table_name)
