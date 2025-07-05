import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from firebase_admin import auth
from pydantic import BaseModel

from src.py_libs.controllers.account_controller import (
    AccountController,
    InvalidTokenError,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/account")


class CreateAccountRequest(BaseModel):
    """Request model for creating an account."""

    name: str
    id_token: str
    stories: list[dict[str, Any]] | None = None
    status: str | None = None
    party_sets: list[dict[str, Any]] | None = None


@router.post("/create")
async def create_account(request: CreateAccountRequest):
    """Create a new account using Firebase ID token.

    Args:
        request: CreateAccountRequest containing name, id_token, and optional fields

    Returns:
        Dictionary with created account data

    Raises:
        HTTPException: If token is invalid or account creation fails
    """
    try:
        controller = AccountController()

        account_data = controller.create_account(
            name=request.name,
            id_token=request.id_token,
            stories=request.stories,
            status=request.status,
            party_sets=request.party_sets,
        )

        if account_data is None:
            raise HTTPException(
                status_code=400, detail="Account creation failed. Name might already exist."
            )

        logger.info(f"Account created successfully: {account_data['name']}")
        return {"success": True, "data": account_data}

    except InvalidTokenError as e:
        logger.error(f"Invalid Firebase token: {e}")
        raise HTTPException(status_code=401, detail="Invalid Firebase ID token")
    except Exception as e:
        logger.error(f"Error creating account: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/info")
async def get_account_info(authorization: str):
    """Get account information using Firebase ID token.

    Args:
        authorization: Firebase ID token in Authorization header

    Returns:
        Dictionary with account data

    Raises:
        HTTPException: If token is invalid or account not found
    """
    try:
        # Extract token from Authorization header (expecting "Bearer <token>")
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=401, detail="Authorization header must be in format: Bearer <token>"
            )

        id_token = authorization.split(" ")[1]

        # Decode the Firebase ID token to get the UID
        try:
            decoded = auth.verify_id_token(id_token)
            firebase_uid = decoded["uid"]
        except Exception as e:
            logger.error(f"Invalid Firebase token: {e}")
            raise HTTPException(status_code=401, detail="Invalid Firebase ID token")

        controller = AccountController()
        account_data = controller.get_account_by_firebase_uid(firebase_uid)

        if account_data is None:
            raise HTTPException(status_code=404, detail="Account not found for this Firebase user")

        logger.info(f"Account info retrieved for: {account_data['name']}")
        return {"success": True, "data": account_data}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving account info: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
