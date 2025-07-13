"""Unit tests for the gacha router endpoints."""

from unittest.mock import Mock, patch

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport

from src.routers.gacha_router import router

# Create a test app
app = FastAPI()
app.include_router(router)


@pytest.fixture
def mock_gacha_controller():
    """Mock GachaController for testing."""
    return Mock()


@pytest.fixture
def mock_account_controller():
    """Mock AccountController for testing."""
    return Mock()


@pytest.fixture
def mock_firebase_token():
    """Mock Firebase ID token for testing."""
    return "mock_firebase_token"


@pytest.fixture
def mock_decoded_token():
    """Mock decoded Firebase token data."""
    return {"uid": "firebase_uid_123", "email": "test@example.com"}


@pytest.fixture
def sample_account_data():
    """Sample account data for testing."""
    return {
        "id": 1,
        "name": "Test User",
        "firebaseUID": "firebase_uid_123",
        "email": "test@example.com",
    }


@pytest.fixture
def sample_gacha_result():
    """Sample gacha result data."""
    return {
        "success": True,
        "message": "Successfully obtained Common Hero from Test Pool!",
        "account_id": 1,
        "gacha_pool_id": "test_pool",
        "hero_name": "Common Hero",
        "hero_level": 1,
        "hero_obtained": {
            "hero_id": 1,
            "name": "Common Hero",
            "probability": 0.6,
            "database_hero_id": 123,
        },
        "items_consumed": {
            "item_id": 1,
            "item_name": "Basic Ticket",
            "amount_consumed": 1,
        },
    }


@pytest.fixture
def sample_multi_gacha_result():
    """Sample multi gacha result data."""
    return {
        "success": True,
        "message": "Successfully completed 3 gacha pulls",
        "account_id": 1,
        "gacha_pool_id": "test_pool",
        "heroes_obtained": [
            {"hero_id": 1, "name": "Common Hero", "probability": 0.6, "database_hero_id": 123},
            {"hero_id": 2, "name": "Rare Hero", "probability": 0.3, "database_hero_id": 124},
            {"hero_id": 1, "name": "Common Hero", "probability": 0.6, "database_hero_id": 125},
        ],
        "items_consumed": {1: {"item_id": 1, "item_name": "Basic Ticket", "amount_consumed": 3}},
        "num_pulls": 3,
    }


@pytest.fixture
def sample_pools_data():
    """Sample gacha pools data."""
    return [
        {
            "pool_id": "test_pool",
            "name": "Test Pool",
            "description": "A test gacha pool",
            "requiring_item_id": 1,
            "num_requiring_item": 1,
            "heroes": ["Common Hero", "Rare Hero", "Legendary Hero"],
        },
        {
            "pool_id": "premium_pool",
            "name": "Premium Pool",
            "description": "A premium gacha pool",
            "requiring_item_id": 2,
            "num_requiring_item": 1,
            "heroes": ["Epic Hero", "Mythic Hero"],
        },
    ]


@pytest.fixture
def sample_pool_info():
    """Sample pool info data."""
    return {
        "success": True,
        "message": "Gacha pool 'test_pool' information retrieved",
        "pool_info": {
            "pool_id": "test_pool",
            "name": "Test Pool",
            "description": "A test gacha pool",
            "requiring_item_id": 1,
            "num_requiring_item": 1,
            "heroes": [
                {
                    "hero_id": 1,
                    "name": "Common Hero",
                    "description": "",
                    "rarity": "unknown",
                    "element": "unknown",
                    "class": "unknown",
                    "stats": {},
                    "skills": [],
                    "probability": 0.6,
                },
                {
                    "hero_id": 2,
                    "name": "Rare Hero",
                    "description": "",
                    "rarity": "unknown",
                    "element": "unknown",
                    "class": "unknown",
                    "stats": {},
                    "skills": [],
                    "probability": 0.3,
                },
                {
                    "hero_id": 3,
                    "name": "Legendary Hero",
                    "description": "",
                    "rarity": "unknown",
                    "element": "unknown",
                    "class": "unknown",
                    "stats": {},
                    "skills": [],
                    "probability": 0.1,
                },
            ],
        },
    }


@pytest_asyncio.fixture
async def client():
    """Create async HTTP client for testing."""
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestGachaPull:
    """Test cases for POST /gacha/pull endpoint."""

    @patch("src.routers.gacha_router.auth.verify_id_token")
    @patch("src.routers.gacha_router.AccountController")
    @patch("src.routers.gacha_router.gacha_controller")
    @pytest.mark.asyncio
    async def test_gacha_pull_success(
        self,
        mock_gacha_controller,
        mock_controller_class,
        mock_verify_token,
        mock_decoded_token,
        sample_account_data,
        sample_gacha_result,
        client,
    ):
        """Test successful gacha pull."""
        # Setup mocks
        mock_verify_token.return_value = mock_decoded_token
        mock_account_controller = Mock()
        mock_controller_class.return_value = mock_account_controller
        mock_account_controller.get_account_by_firebase_uid.return_value = sample_account_data
        mock_gacha_controller.gacha.return_value = sample_gacha_result

        # Make request
        request_data = {"id_token": "mock_firebase_token", "gacha_pool_id": "test_pool"}
        response = await client.post("/gacha/pull", json=request_data)

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["hero_name"] == "Common Hero"
        assert data["account_id"] == 1
        assert data["gacha_pool_id"] == "test_pool"

        # Verify controller was called correctly
        mock_gacha_controller.gacha.assert_called_once_with(account_id=1, gacha_pool_id="test_pool")

    @patch("src.routers.gacha_router.auth.verify_id_token")
    @pytest.mark.asyncio
    async def test_gacha_pull_invalid_token(self, mock_verify_token, client):
        """Test gacha pull with invalid Firebase token."""
        # Setup mock to raise exception
        mock_verify_token.side_effect = Exception("Invalid token")

        # Make request
        request_data = {"id_token": "invalid_token", "gacha_pool_id": "test_pool"}
        response = await client.post("/gacha/pull", json=request_data)

        # Assertions
        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Invalid Firebase ID token"

    @patch("src.routers.gacha_router.auth.verify_id_token")
    @patch("src.routers.gacha_router.AccountController")
    @pytest.mark.asyncio
    async def test_gacha_pull_account_not_found(
        self, mock_controller_class, mock_verify_token, mock_decoded_token, client
    ):
        """Test gacha pull when account is not found."""
        # Setup mocks
        mock_verify_token.return_value = mock_decoded_token
        mock_account_controller = Mock()
        mock_controller_class.return_value = mock_account_controller
        mock_account_controller.get_account_by_firebase_uid.return_value = None

        # Make request
        request_data = {"id_token": "mock_firebase_token", "gacha_pool_id": "test_pool"}
        response = await client.post("/gacha/pull", json=request_data)

        # Assertions
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Account not found"

    @patch("src.routers.gacha_router.auth.verify_id_token")
    @patch("src.routers.gacha_router.AccountController")
    @patch("src.routers.gacha_router.gacha_controller")
    @pytest.mark.asyncio
    async def test_gacha_pull_insufficient_items(
        self,
        mock_gacha_controller,
        mock_controller_class,
        mock_verify_token,
        mock_decoded_token,
        sample_account_data,
        client,
    ):
        """Test gacha pull with insufficient items."""
        # Setup mocks
        mock_verify_token.return_value = mock_decoded_token
        mock_account_controller = Mock()
        mock_controller_class.return_value = mock_account_controller
        mock_account_controller.get_account_by_firebase_uid.return_value = sample_account_data

        # Mock gacha failure
        gacha_failure_result = {
            "success": False,
            "message": "Insufficient Basic Ticket. Required: 1, Have: 0",
            "account_id": 1,
            "gacha_pool_id": "test_pool",
            "hero_obtained": None,
            "items_consumed": {},
        }
        mock_gacha_controller.gacha.return_value = gacha_failure_result

        # Make request
        request_data = {"id_token": "mock_firebase_token", "gacha_pool_id": "test_pool"}
        response = await client.post("/gacha/pull", json=request_data)

        # Assertions
        assert response.status_code == 400
        data = response.json()
        assert "Insufficient Basic Ticket" in data["detail"]

    @pytest.mark.asyncio
    async def test_gacha_pull_missing_fields(self, client):
        """Test gacha pull with missing required fields."""
        # Request without required 'gacha_pool_id' field
        invalid_request = {"id_token": "mock_firebase_token"}

        response = await client.post("/gacha/pull", json=invalid_request)

        # Assertions
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data


class TestMultiGachaPull:
    """Test cases for POST /gacha/multi-pull endpoint."""

    @patch("src.routers.gacha_router.auth.verify_id_token")
    @patch("src.routers.gacha_router.AccountController")
    @patch("src.routers.gacha_router.gacha_controller")
    @pytest.mark.asyncio
    async def test_multi_gacha_pull_success(
        self,
        mock_gacha_controller,
        mock_controller_class,
        mock_verify_token,
        mock_decoded_token,
        sample_account_data,
        sample_multi_gacha_result,
        client,
    ):
        """Test successful multi gacha pull."""
        # Setup mocks
        mock_verify_token.return_value = mock_decoded_token
        mock_account_controller = Mock()
        mock_controller_class.return_value = mock_account_controller
        mock_account_controller.get_account_by_firebase_uid.return_value = sample_account_data
        mock_gacha_controller.multi_gacha.return_value = sample_multi_gacha_result

        # Make request
        request_data = {
            "id_token": "mock_firebase_token",
            "gacha_pool_id": "test_pool",
            "num_pulls": 3,
        }
        response = await client.post("/gacha/multi-pull", json=request_data)

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["num_pulls"] == 3
        assert len(data["heroes_obtained"]) == 3

        # Verify controller was called correctly
        mock_gacha_controller.multi_gacha.assert_called_once_with(
            account_id=1, gacha_pool_id="test_pool", num_pulls=3
        )

    @pytest.mark.asyncio
    async def test_multi_gacha_pull_invalid_num_pulls(self, client):
        """Test multi gacha pull with invalid number of pulls."""
        # Test with zero pulls
        request_data = {
            "id_token": "mock_firebase_token",
            "gacha_pool_id": "test_pool",
            "num_pulls": 0,
        }
        response = await client.post("/gacha/multi-pull", json=request_data)
        assert response.status_code == 400
        assert "greater than 0" in response.json()["detail"]

        # Test with too many pulls
        request_data["num_pulls"] = 101
        response = await client.post("/gacha/multi-pull", json=request_data)
        assert response.status_code == 400
        assert "cannot exceed 100" in response.json()["detail"]

    @patch("src.routers.gacha_router.auth.verify_id_token")
    @patch("src.routers.gacha_router.AccountController")
    @patch("src.routers.gacha_router.gacha_controller")
    @pytest.mark.asyncio
    async def test_multi_gacha_pull_partial_failure(
        self,
        mock_gacha_controller,
        mock_controller_class,
        mock_verify_token,
        mock_decoded_token,
        sample_account_data,
        client,
    ):
        """Test multi gacha pull with partial failure."""
        # Setup mocks
        mock_verify_token.return_value = mock_decoded_token
        mock_account_controller = Mock()
        mock_controller_class.return_value = mock_account_controller
        mock_account_controller.get_account_by_firebase_uid.return_value = sample_account_data

        # Mock multi gacha partial failure
        partial_failure_result = {
            "success": False,
            "message": "Failed after 1 successful pulls: Insufficient Basic Ticket. Required: 1, Have: 0",
            "account_id": 1,
            "gacha_pool_id": "test_pool",
            "heroes_obtained": [
                {"hero_id": 1, "name": "Common Hero", "probability": 0.6, "database_hero_id": 123}
            ],
            "items_consumed": {
                1: {"item_id": 1, "item_name": "Basic Ticket", "amount_consumed": 1}
            },
            "num_pulls": 1,
        }
        mock_gacha_controller.multi_gacha.return_value = partial_failure_result

        # Make request
        request_data = {
            "id_token": "mock_firebase_token",
            "gacha_pool_id": "test_pool",
            "num_pulls": 5,
        }
        response = await client.post("/gacha/multi-pull", json=request_data)

        # Assertions
        assert response.status_code == 400
        data = response.json()
        assert "Failed after 1 successful pulls" in data["detail"]


class TestGetAvailablePools:
    """Test cases for GET /gacha/pools endpoint."""

    @patch("src.routers.gacha_router.gacha_controller")
    @pytest.mark.asyncio
    async def test_get_available_pools_success(
        self, mock_gacha_controller, sample_pools_data, client
    ):
        """Test successful retrieval of available pools."""
        # Setup mock
        mock_gacha_controller.get_available_pools.return_value = sample_pools_data

        # Make request
        response = await client.get("/gacha/pools")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["pools"]) == 2
        assert data["pools"][0]["pool_id"] == "test_pool"
        assert data["pools"][1]["pool_id"] == "premium_pool"

        # Verify controller was called correctly
        mock_gacha_controller.get_available_pools.assert_called_once()

    @patch("src.routers.gacha_router.gacha_controller")
    @pytest.mark.asyncio
    async def test_get_available_pools_internal_error(self, mock_gacha_controller, client):
        """Test get available pools with internal server error."""
        # Setup mock to raise exception
        mock_gacha_controller.get_available_pools.side_effect = Exception("Database error")

        # Make request
        response = await client.get("/gacha/pools")

        # Assertions
        assert response.status_code == 500
        data = response.json()
        assert data["detail"] == "Internal server error"


class TestGetPoolInfo:
    """Test cases for POST /gacha/pool-info endpoint."""

    @patch("src.routers.gacha_router.gacha_controller")
    @pytest.mark.asyncio
    async def test_get_pool_info_success(self, mock_gacha_controller, sample_pool_info, client):
        """Test successful retrieval of pool information."""
        # Setup mock
        mock_gacha_controller.get_gacha_pool_info.return_value = sample_pool_info

        # Make request
        request_data = {"gacha_pool_id": "test_pool"}
        response = await client.post("/gacha/pool-info", json=request_data)

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["pool_info"]["pool_id"] == "test_pool"
        assert data["pool_info"]["name"] == "Test Pool"

        # Verify controller was called correctly
        mock_gacha_controller.get_gacha_pool_info.assert_called_once_with("test_pool")

    @patch("src.routers.gacha_router.gacha_controller")
    @pytest.mark.asyncio
    async def test_get_pool_info_nonexistent_pool(self, mock_gacha_controller, client):
        """Test pool info request for nonexistent pool."""
        # Setup mock
        pool_not_found_result = {
            "success": False,
            "message": "Gacha pool 'nonexistent_pool' does not exist",
            "pool_info": None,
        }
        mock_gacha_controller.get_gacha_pool_info.return_value = pool_not_found_result

        # Make request
        request_data = {"gacha_pool_id": "nonexistent_pool"}
        response = await client.post("/gacha/pool-info", json=request_data)

        # Assertions
        assert response.status_code == 404
        data = response.json()
        assert "does not exist" in data["detail"]

    @pytest.mark.asyncio
    async def test_get_pool_info_missing_pool_id(self, client):
        """Test pool info request with missing pool ID."""
        # Request without required 'gacha_pool_id' field
        invalid_request = {}

        response = await client.post("/gacha/pool-info", json=invalid_request)

        # Assertions
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data

    @patch("src.routers.gacha_router.gacha_controller")
    @pytest.mark.asyncio
    async def test_get_pool_info_internal_error(self, mock_gacha_controller, client):
        """Test pool info request with internal server error."""
        # Setup mock to raise exception
        mock_gacha_controller.get_gacha_pool_info.side_effect = Exception("Database error")

        # Make request
        request_data = {"gacha_pool_id": "test_pool"}
        response = await client.post("/gacha/pool-info", json=request_data)

        # Assertions
        assert response.status_code == 500
        data = response.json()
        assert data["detail"] == "Internal server error"


class TestEndpointIntegration:
    """Integration tests combining multiple endpoints."""

    @patch("src.routers.gacha_router.auth.verify_id_token")
    @patch("src.routers.gacha_router.AccountController")
    @patch("src.routers.gacha_router.gacha_controller")
    @pytest.mark.asyncio
    async def test_get_pools_then_pull_gacha(
        self,
        mock_gacha_controller,
        mock_controller_class,
        mock_verify_token,
        mock_decoded_token,
        sample_account_data,
        sample_pools_data,
        sample_gacha_result,
        client,
    ):
        """Test getting pools then performing a gacha pull."""
        # Setup mocks for authentication
        mock_verify_token.return_value = mock_decoded_token
        mock_account_controller = Mock()
        mock_controller_class.return_value = mock_account_controller
        mock_account_controller.get_account_by_firebase_uid.return_value = sample_account_data

        # Setup gacha controller mocks
        mock_gacha_controller.get_available_pools.return_value = sample_pools_data
        mock_gacha_controller.gacha.return_value = sample_gacha_result

        # First, get available pools
        pools_response = await client.get("/gacha/pools")
        assert pools_response.status_code == 200
        pools_data = pools_response.json()
        available_pool_id = pools_data["pools"][0]["pool_id"]

        # Then, perform gacha pull on the first available pool
        gacha_request = {"id_token": "mock_firebase_token", "gacha_pool_id": available_pool_id}
        gacha_response = await client.post("/gacha/pull", json=gacha_request)

        # Assertions
        assert gacha_response.status_code == 200
        gacha_data = gacha_response.json()
        assert gacha_data["success"] is True
        assert gacha_data["gacha_pool_id"] == available_pool_id
