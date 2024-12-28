import logging
from pathlib import Path

from fastapi import APIRouter
from src.py_libs.controllers.data_controller import DataController

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/data")
data_path = Path("output/historical_data")
data_path.mkdir(exist_ok=True, parents=True)
data_controller = DataController(data_path)


@router.get("/getMetaData")
def get_metadata():
    meta_data = data_controller.prices_meta_data
    result = []
    for name, data in meta_data.items():
        result.append(
            {
                "name": name,
                "start_date": data.start_date,
                "end_date": data.end_date,
                "type": data.type.value,
            }
        )

    return {"MetaDataList": result}
