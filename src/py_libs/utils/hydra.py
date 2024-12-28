import os
from datetime import datetime
from pathlib import Path

import hydra
from omegaconf import DictConfig
from src import REPO


def setup_hydra() -> DictConfig:
    with hydra.initialize_config_dir(version_base=None, config_dir=str(REPO / "src/config")):
        config = hydra.compose(config_name="main")

    current = os.getcwd().partition("backend")
    today = datetime.now()
    dir_path = (
        Path(current[0] + current[1])
        / Path("logs")
        / config.env.name
        / today.strftime("%Y-%m-%d")
        / today.strftime("%H-%M-%S")
    )

    os.makedirs(dir_path, exist_ok=True)
    os.chdir(dir_path)
    return config

    return config
