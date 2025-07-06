import logging

from fastapi import APIRouter, Header, HTTPException
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

    id_token: str


@router.post("/create")
async def create_account(request: CreateAccountRequest):
    """Create a new account using Firebase ID token.

    Args:
        request: CreateAccountRequest containing id_token

    Returns:
        Dictionary with created account data

    Raises:
        HTTPException: If token is invalid or account creation fails
    """
    try:
        controller = AccountController()
        print("received id_token: ", request.id_token)

        account_data = controller.create_account(
            id_token=request.id_token,
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating account: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/info")
async def get_account_info(authorization: str = None):
    """Get account information using Firebase ID token.

    Args:
        authorization: Firebase ID token in Authorization header

    Returns:
        Dictionary with account data

    Raises:
        HTTPException: If token is invalid or account not found
    """

    if authorization is None:
        authorization = Header(None)
    try:
        # Check if authorization header is present
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header is required")

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
