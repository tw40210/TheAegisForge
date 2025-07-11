"""Router for gacha related endpoints."""

import logging

from fastapi import APIRouter, HTTPException
from firebase_admin import auth
from pydantic import BaseModel

from src.py_libs.controllers.account_controller import AccountController
from src.py_libs.controllers.gacha_controller import GachaController

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


router = APIRouter(prefix="/gacha")
gacha_controller = GachaController()


class GachaRequest(BaseModel):
    """Request model for gacha operations."""

    id_token: str
    gacha_pool_id: str


class MultiGachaRequest(BaseModel):
    """Request model for multi-gacha operations."""

    id_token: str
    gacha_pool_id: str
    num_pulls: int


class GetPoolsRequest(BaseModel):
    """Request model for getting available gacha pools."""

    id_token: str


class PoolInfoRequest(BaseModel):
    """Request model for getting gacha pool information."""

    gacha_pool_id: str


@router.post("/pull", tags=["gacha"])
async def gacha_pull(request: GachaRequest):
    """Perform a single gacha pull."""
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

        # Perform gacha pull
        result = gacha_controller.gacha(account_id=account_id, gacha_pool_id=request.gacha_pool_id)

        if not result.get("success"):
            logger.warning(f"Gacha pull failed for account {account_id}: {result.get('message')}")
            raise HTTPException(status_code=400, detail=result.get("message"))

        logger.info(
            f"Gacha pull successful for account ID: {account_id}, pool: {request.gacha_pool_id}"
        )
        return result

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error performing gacha pull: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/multi-pull", tags=["gacha"])
async def multi_gacha_pull(request: MultiGachaRequest):
    """Perform multiple gacha pulls."""
    try:
        # Validate num_pulls
        if request.num_pulls <= 0:
            raise HTTPException(status_code=400, detail="Number of pulls must be greater than 0")
        if request.num_pulls > 100:  # Reasonable limit
            raise HTTPException(status_code=400, detail="Number of pulls cannot exceed 100")

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

        # Perform multi gacha pull
        result = gacha_controller.multi_gacha(
            account_id=account_id, gacha_pool_id=request.gacha_pool_id, num_pulls=request.num_pulls
        )

        if not result.get("success"):
            logger.warning(
                f"Multi gacha pull failed for account {account_id}: {result.get('message')}"
            )
            raise HTTPException(status_code=400, detail=result.get("message"))

        logger.info(
            f"Multi gacha pull successful for account ID: {account_id}, pool: {request.gacha_pool_id}, pulls: {request.num_pulls}"
        )
        return result

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error performing multi gacha pull: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/pools", tags=["gacha"])
async def get_available_pools():
    """Get all available gacha pools."""
    try:
        # Get available pools
        pools = gacha_controller.get_available_pools()

        return {
            "success": True,
            "message": "Available gacha pools retrieved successfully",
            "pools": pools,
        }

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error getting available pools: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/pool-info", tags=["gacha"])
async def get_pool_info(request: PoolInfoRequest):
    """Get detailed information about a specific gacha pool."""
    try:
        # Get pool information (no authentication needed for public pool data)
        result = gacha_controller.get_gacha_pool_info(request.gacha_pool_id)

        if not result.get("success"):
            logger.warning(f"Pool info request failed: {result.get('message')}")
            raise HTTPException(status_code=404, detail=result.get("message"))

        logger.info(f"Pool info retrieved for pool: {request.gacha_pool_id}")
        return result

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error getting pool info: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
