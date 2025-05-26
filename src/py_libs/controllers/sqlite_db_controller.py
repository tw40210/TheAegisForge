import json
import logging
import sqlite3
from pathlib import Path
from typing import Any

from src.py_libs.controllers.base_db_controller import BaseDatabaseController

logger = logging.getLogger(__name__)


class SQLiteDatabaseController(BaseDatabaseController):
    def __init__(self, db_name: str = "local_db") -> None:
        super().__init__(db_name)
        self.db_path = Path(f"{db_name}.db")
        self.conn = sqlite3.connect(str(self.db_path))
        self.cursor = self.conn.cursor()
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the database with required tables."""
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS data_store (
                path TEXT PRIMARY KEY,
                data TEXT NOT NULL
            )
        """
        )
        self.conn.commit()

    def _query_path(self, target_path: str) -> dict | None:
        """Query data for a given path."""
        self.cursor.execute("SELECT data FROM data_store WHERE path = ?", (target_path,))
        result = self.cursor.fetchone()
        if result:
            return json.loads(result[0])
        return None

    def get_data(self, target_path: str) -> Any:
        """Get data for a given path."""
        logger.debug(f"Try to get `{target_path}`.")
        return self._query_path(target_path)

    def save_data(self, data: dict, target_path: str) -> int:
        """Save data for a given path."""
        data_json = json.dumps(data)
        self.cursor.execute(
            "INSERT OR REPLACE INTO data_store (path, data) VALUES (?, ?)", (target_path, data_json)
        )
        self.conn.commit()
        logger.debug(f"`{target_path}` is newly saved.")
        return 0

    def delete_data(self, target_path: str) -> int:
        """Delete data for a given path."""
        self.cursor.execute("DELETE FROM data_store WHERE path = ?", (target_path,))
        self.conn.commit()
        if self.cursor.rowcount > 0:
            logger.debug(f"`{target_path}` is deleted.")
        else:
            logger.warning(f"`{target_path}` is not found. Nothing deleted.")
        return 0

    def update_data(self, data: str, target_path: str) -> int:
        """Update data for a given path."""
        return self.save_data(data, target_path)

    def __del__(self):
        """Cleanup database connection."""
        if hasattr(self, "conn"):
            self.conn.close()

    @staticmethod
    def get_target_path(path_list: list[str]) -> str:
        """Convert a list of path components to a dot-separated path."""
        return ".".join(path_list)
