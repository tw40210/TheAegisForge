"""Unit tests for the material router endpoints."""

from unittest.mock import Mock, patch

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport

from src.routers.material_router import router

# Create a test app
app = FastAPI()
app.include_router(router)


@pytest.fixture
def mock_material_controller():
    """Mock MaterialController for testing."""
    return Mock()


@pytest.fixture
def sample_questions():
    """Sample questions data for testing."""
    return [
        {
            "id": 1,
            "question_type": "mc_question",
            "summary_type": "InnovationSummary",
            "content_type": "innovation_points",
            "index_number": 0,
            "material_name": "test_material",
            "content": {"question": "What is innovation?", "options": ["A", "B", "C", "D"]},
        },
        {
            "id": 2,
            "question_type": "essay_question",
            "summary_type": "InnovationSummary",
            "content_type": "innovation_theory",
            "index_number": 1,
            "material_name": "test_material",
            "content": {"question": "Explain innovation theory", "max_words": 500},
        },
    ]


@pytest.fixture
def sample_summaries():
    """Sample summaries data for testing."""
    return [
        {
            "id": 1,
            "summary_type": "InnovationSummary",
            "content_type": "innovation_points",
            "index_number": 0,
            "material_name": "test_material",
            "content": {"key_points": ["Point 1", "Point 2"], "conclusion": "Summary text"},
        },
        {
            "id": 2,
            "summary_type": "InnovationSummary",
            "content_type": "innovation_theory",
            "index_number": 1,
            "material_name": "test_material",
            "content": {"theory": "Innovation theory explanation", "examples": ["Ex1", "Ex2"]},
        },
    ]


@pytest.fixture
def sample_material_data(sample_questions, sample_summaries):
    """Sample combined material data for testing."""
    return {
        "material_name": "test_material",
        "questions": sample_questions,
        "summaries": sample_summaries,
        "question_count": len(sample_questions),
        "summary_count": len(sample_summaries),
    }


@pytest.fixture
def sample_materials_list():
    """Sample materials list for testing."""
    return {
        "materials": [
            {
                "material_name": "test_material_1",
                "question_count": 2,
                "summary_count": 2,
                "total_count": 4,
            },
            {
                "material_name": "test_material_2",
                "question_count": 1,
                "summary_count": 1,
                "total_count": 2,
            },
        ],
        "total_materials": 2,
    }


@pytest.fixture
def material_request():
    """Sample material request data."""
    return {"material_name": "test_material"}


@pytest_asyncio.fixture
async def client():
    """Create async HTTP client for testing."""
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestGetQuestionsByMaterialNameGET:
    """Test cases for GET /material/questions/{material_name} endpoint."""

    @patch("src.routers.material_router.material_controller")
    @pytest.mark.asyncio
    async def test_get_questions_success(self, mock_controller, sample_questions, client):
        """Test successful retrieval of questions."""
        mock_controller.get_questions_by_material_name.return_value = sample_questions

        response = await client.get("/material/questions/test_material")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["material_name"] == "test_material"
        assert data["question_count"] == 2
        assert len(data["data"]) == 2
        assert data["data"][0]["question_type"] == "mc_question"

        mock_controller.get_questions_by_material_name.assert_called_once_with("test_material")

    @patch("src.routers.material_router.material_controller")
    @pytest.mark.asyncio
    async def test_get_questions_empty_result(self, mock_controller, client):
        """Test retrieval of questions for non-existent material."""
        mock_controller.get_questions_by_material_name.return_value = []

        response = await client.get("/material/questions/nonexistent_material")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["material_name"] == "nonexistent_material"
        assert data["question_count"] == 0
        assert data["data"] == []

    @patch("src.routers.material_router.material_controller")
    @pytest.mark.asyncio
    async def test_get_questions_controller_error(self, mock_controller, client):
        """Test handling of controller errors."""
        mock_controller.get_questions_by_material_name.side_effect = Exception("Database error")

        response = await client.get("/material/questions/test_material")

        assert response.status_code == 500
        data = response.json()
        assert data["detail"] == "Internal server error"


class TestGetSummariesByMaterialNameGET:
    """Test cases for GET /material/summaries/{material_name} endpoint."""

    @patch("src.routers.material_router.material_controller")
    @pytest.mark.asyncio
    async def test_get_summaries_success(self, mock_controller, sample_summaries, client):
        """Test successful retrieval of summaries."""
        mock_controller.get_summaries_by_material_name.return_value = sample_summaries

        response = await client.get("/material/summaries/test_material")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["material_name"] == "test_material"
        assert data["summary_count"] == 2
        assert len(data["data"]) == 2
        assert data["data"][0]["summary_type"] == "InnovationSummary"

        mock_controller.get_summaries_by_material_name.assert_called_once_with("test_material")

    @patch("src.routers.material_router.material_controller")
    @pytest.mark.asyncio
    async def test_get_summaries_empty_result(self, mock_controller, client):
        """Test retrieval of summaries for non-existent material."""
        mock_controller.get_summaries_by_material_name.return_value = []

        response = await client.get("/material/summaries/nonexistent_material")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["material_name"] == "nonexistent_material"
        assert data["summary_count"] == 0
        assert data["data"] == []

    @patch("src.routers.material_router.material_controller")
    @pytest.mark.asyncio
    async def test_get_summaries_controller_error(self, mock_controller, client):
        """Test handling of controller errors."""
        mock_controller.get_summaries_by_material_name.side_effect = Exception("Database error")

        response = await client.get("/material/summaries/test_material")

        assert response.status_code == 500
        data = response.json()
        assert data["detail"] == "Internal server error"


class TestGetMaterialDataGET:
    """Test cases for GET /material/data/{material_name} endpoint."""

    @patch("src.routers.material_router.material_controller")
    @pytest.mark.asyncio
    async def test_get_material_data_success(self, mock_controller, sample_material_data, client):
        """Test successful retrieval of material data."""
        mock_controller.get_material_data.return_value = sample_material_data

        response = await client.get("/material/data/test_material")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["material_name"] == "test_material"
        assert data["data"]["question_count"] == 2
        assert data["data"]["summary_count"] == 2

        mock_controller.get_material_data.assert_called_once_with("test_material")

    @patch("src.routers.material_router.material_controller")
    @pytest.mark.asyncio
    async def test_get_material_data_controller_error(self, mock_controller, client):
        """Test handling of controller errors."""
        mock_controller.get_material_data.side_effect = Exception("Database error")

        response = await client.get("/material/data/test_material")

        assert response.status_code == 500
        data = response.json()
        assert data["detail"] == "Internal server error"


class TestListAvailableMaterials:
    """Test cases for GET /material/list endpoint."""

    @patch("src.routers.material_router.material_controller")
    @pytest.mark.asyncio
    async def test_list_materials_success(self, mock_controller, sample_materials_list, client):
        """Test successful listing of materials."""
        mock_controller.list_available_materials.return_value = sample_materials_list

        response = await client.get("/material/list")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total_materials"] == 2
        assert len(data["data"]["materials"]) == 2

        mock_controller.list_available_materials.assert_called_once()

    @patch("src.routers.material_router.material_controller")
    @pytest.mark.asyncio
    async def test_list_materials_empty_result(self, mock_controller, client):
        """Test listing when no materials exist."""
        mock_controller.list_available_materials.return_value = {
            "materials": [],
            "total_materials": 0,
        }

        response = await client.get("/material/list")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total_materials"] == 0
        assert data["data"]["materials"] == []

    @patch("src.routers.material_router.material_controller")
    @pytest.mark.asyncio
    async def test_list_materials_controller_error(self, mock_controller, client):
        """Test handling of controller errors."""
        mock_controller.list_available_materials.side_effect = Exception("Database error")

        response = await client.get("/material/list")

        assert response.status_code == 500
        data = response.json()
        assert data["detail"] == "Internal server error"


class TestGetQuestionsByMaterialNamePOST:
    """Test cases for POST /material/questions endpoint."""

    @patch("src.routers.material_router.material_controller")
    @pytest.mark.asyncio
    async def test_post_questions_success(
        self, mock_controller, sample_questions, material_request, client
    ):
        """Test successful retrieval of questions via POST."""
        mock_controller.get_questions_by_material_name.return_value = sample_questions

        response = await client.post("/material/questions", json=material_request)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["material_name"] == "test_material"
        assert data["question_count"] == 2
        assert len(data["data"]) == 2

        mock_controller.get_questions_by_material_name.assert_called_once_with("test_material")

    @patch("src.routers.material_router.material_controller")
    @pytest.mark.asyncio
    async def test_post_questions_empty_result(self, mock_controller, material_request, client):
        """Test POST questions for non-existent material."""
        mock_controller.get_questions_by_material_name.return_value = []

        response = await client.post("/material/questions", json=material_request)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["question_count"] == 0
        assert data["data"] == []

    @pytest.mark.asyncio
    async def test_post_questions_invalid_request(self, client):
        """Test POST questions with invalid request body."""
        response = await client.post("/material/questions", json={})

        assert response.status_code == 422  # Validation error


class TestGetSummariesByMaterialNamePOST:
    """Test cases for POST /material/summaries endpoint."""

    @patch("src.routers.material_router.material_controller")
    @pytest.mark.asyncio
    async def test_post_summaries_success(
        self, mock_controller, sample_summaries, material_request, client
    ):
        """Test successful retrieval of summaries via POST."""
        mock_controller.get_summaries_by_material_name.return_value = sample_summaries

        response = await client.post("/material/summaries", json=material_request)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["material_name"] == "test_material"
        assert data["summary_count"] == 2
        assert len(data["data"]) == 2

        mock_controller.get_summaries_by_material_name.assert_called_once_with("test_material")

    @patch("src.routers.material_router.material_controller")
    @pytest.mark.asyncio
    async def test_post_summaries_empty_result(self, mock_controller, material_request, client):
        """Test POST summaries for non-existent material."""
        mock_controller.get_summaries_by_material_name.return_value = []

        response = await client.post("/material/summaries", json=material_request)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["summary_count"] == 0
        assert data["data"] == []

    @pytest.mark.asyncio
    async def test_post_summaries_invalid_request(self, client):
        """Test POST summaries with invalid request body."""
        response = await client.post("/material/summaries", json={})

        assert response.status_code == 422  # Validation error


class TestGetMaterialDataPOST:
    """Test cases for POST /material/data endpoint."""

    @patch("src.routers.material_router.material_controller")
    @pytest.mark.asyncio
    async def test_post_material_data_success(
        self, mock_controller, sample_material_data, material_request, client
    ):
        """Test successful retrieval of material data via POST."""
        mock_controller.get_material_data.return_value = sample_material_data

        response = await client.post("/material/data", json=material_request)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["material_name"] == "test_material"
        assert data["data"]["question_count"] == 2
        assert data["data"]["summary_count"] == 2

        mock_controller.get_material_data.assert_called_once_with("test_material")

    @patch("src.routers.material_router.material_controller")
    @pytest.mark.asyncio
    async def test_post_material_data_empty_result(self, mock_controller, material_request, client):
        """Test POST material data for non-existent material."""
        empty_data = {
            "material_name": "test_material",
            "questions": [],
            "summaries": [],
            "question_count": 0,
            "summary_count": 0,
        }
        mock_controller.get_material_data.return_value = empty_data

        response = await client.post("/material/data", json=material_request)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["question_count"] == 0
        assert data["data"]["summary_count"] == 0

    @pytest.mark.asyncio
    async def test_post_material_data_invalid_request(self, client):
        """Test POST material data with invalid request body."""
        response = await client.post("/material/data", json={})

        assert response.status_code == 422  # Validation error
