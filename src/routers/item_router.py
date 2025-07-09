"""Router for item related endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel

from src.py_libs.controllers.item_controller import ItemController

router = APIRouter()
item_controller = ItemController()


class GachaSendRequest(BaseModel):
    """Request model for sending gacha items."""

    account_id: int


@router.post("/send-gacha-items", tags=["items"])
async def send_gacha_items(request: GachaSendRequest):
    """Send one of each gacha ticket to an account."""
    return item_controller.send_gacha_items_to_account(account_id=request.account_id)
