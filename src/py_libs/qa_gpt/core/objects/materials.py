from dataclasses import dataclass
from pathlib import Path


@dataclass
class FileMeta:
    id: int
    file_name: str
    file_suffix: str
    file_path: Path
    question_sets: dict
