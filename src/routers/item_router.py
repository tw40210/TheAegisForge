"""Router for item related endpoints."""

import logging

from fastapi import APIRouter, HTTPException
from firebase_admin import auth
from pydantic import BaseModel

from src.py_libs.controllers.account_controller import AccountController
from src.py_libs.controllers.item_controller import ItemController

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


router = APIRouter(prefix="/item")
item_controller = ItemController()


class GachaSendRequest(BaseModel):
    """Request model for sending gacha items."""

    id_token: str


@router.post("/send-gacha-items", tags=["items"])
async def send_gacha_items(request: GachaSendRequest):
    """Send one of each gacha ticket to an account."""
    try:
        # Decode the Firebase ID token to get the UID
        try:
            decoded_token = auth.verify_id_token(request.id_token)
            firebase_uid = decoded_token["uid"]
        except Exception as e:
            logger.error(f"Invalid Firebase token: {e}")
            raise HTTPException(status_code=401, detail="Invalid Firebase ID token")

        # Get account_id from firebase_uid
        account_controller = AccountController()
        account = account_controller.get_account_by_firebase_uid(firebase_uid)
        if account is None:
            raise HTTPException(status_code=404, detail="Account not found")

        account_id = account["id"]

        # Send gacha items to the account
        result = item_controller.send_gacha_items_to_account(account_id=account_id)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))

        logger.info(f"Gacha items sent to account ID: {account_id}")
        return result

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error sending gacha items: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
