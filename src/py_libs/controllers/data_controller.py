from pathlib import Path

import pandas as pd
from src.py_libs.data_process.load_utils import (
    get_historical_metadata,
    load_historical_data,
)


class DataController:
    def __init__(self, data_dir: Path) -> None:
        self.prices_dataframes = {}
        self.prices_meta_data = {}
        self.prices_dict = {}
        self.data_dir = data_dir
        self.fetch_data()

    def fetch_data(self) -> None:
        self.prices_dict = load_historical_data(self.data_dir)
        self.prices_meta_data = get_historical_metadata(self.data_dir)
        self.prices_dataframes = pd.DataFrame.from_dict(
            {k: v.adjclose for k, v in self.prices_dict.items()}
        ).dropna()

    def get_price_data(self):
        return self.prices_dataframes

    def get_meta_data(self):
        return self.prices_meta_data
