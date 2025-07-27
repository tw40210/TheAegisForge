"""Router for material related endpoints."""

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.py_libs.controllers.material_controller import MaterialController

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/story_material")
material_controller = MaterialController()


class MaterialRequest(BaseModel):
    """Request model for material operations."""

    material_name: str


@router.get("/questions/{material_name}", tags=["materials"])
async def get_questions_by_material_name(material_name: str):
    """Get all questions for a specific material name.

    Args:
        material_name: The name of the material to retrieve questions for

    Returns:
        Dictionary with success status and list of questions

    Raises:
        HTTPException: If an error occurs during retrieval
    """
    try:
        questions = material_controller.get_questions_by_material_name(material_name)

        logger.info(f"Retrieved {len(questions)} questions for material: {material_name}")
        return {
            "success": True,
            "material_name": material_name,
            "question_count": len(questions),
            "data": questions,
        }

    except Exception as e:
        logger.error(f"Error retrieving questions for material {material_name}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/summaries/{material_name}", tags=["materials"])
async def get_summaries_by_material_name(material_name: str):
    """Get all summaries for a specific material name.

    Args:
        material_name: The name of the material to retrieve summaries for

    Returns:
        Dictionary with success status and list of summaries

    Raises:
        HTTPException: If an error occurs during retrieval
    """
    try:
        summaries = material_controller.get_summaries_by_material_name(material_name)

        logger.info(f"Retrieved {len(summaries)} summaries for material: {material_name}")
        return {
            "success": True,
            "material_name": material_name,
            "summary_count": len(summaries),
            "data": summaries,
        }

    except Exception as e:
        logger.error(f"Error retrieving summaries for material {material_name}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/data/{material_name}", tags=["materials"])
async def get_material_data(material_name: str):
    """Get both questions and summaries for a specific material name.

    Args:
        material_name: The name of the material to retrieve data for

    Returns:
        Dictionary with success status and both questions and summaries

    Raises:
        HTTPException: If an error occurs during retrieval
    """
    try:
        material_data = material_controller.get_material_data(material_name)

        logger.info(
            f"Retrieved material data for {material_name}: "
            f"{material_data['question_count']} questions, {material_data['summary_count']} summaries"
        )
        return {"success": True, "data": material_data}

    except Exception as e:
        logger.error(f"Error retrieving material data for {material_name}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/list", tags=["materials"])
async def list_available_materials():
    """List all available material names with their question and summary counts.

    Returns:
        Dictionary with success status and list of available materials

    Raises:
        HTTPException: If an error occurs during retrieval
    """
    try:
        materials_info = material_controller.list_available_materials()

        logger.info(f"Retrieved {materials_info['total_materials']} available materials")
        return {"success": True, "data": materials_info}

    except Exception as e:
        logger.error(f"Error retrieving available materials: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/questions", tags=["materials"])
async def get_questions_by_material_name_post(request: MaterialRequest):
    """Get all questions for a specific material name (POST version).

    Args:
        request: MaterialRequest containing material_name

    Returns:
        Dictionary with success status and list of questions

    Raises:
        HTTPException: If an error occurs during retrieval
    """
    try:
        questions = material_controller.get_questions_by_material_name(request.material_name)

        logger.info(f"Retrieved {len(questions)} questions for material: {request.material_name}")
        return {
            "success": True,
            "material_name": request.material_name,
            "question_count": len(questions),
            "data": questions,
        }

    except Exception as e:
        logger.error(f"Error retrieving questions for material {request.material_name}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/summaries", tags=["materials"])
async def get_summaries_by_material_name_post(request: MaterialRequest):
    """Get all summaries for a specific material name (POST version).

    Args:
        request: MaterialRequest containing material_name

    Returns:
        Dictionary with success status and list of summaries

    Raises:
        HTTPException: If an error occurs during retrieval
    """
    try:
        summaries = material_controller.get_summaries_by_material_name(request.material_name)

        logger.info(f"Retrieved {len(summaries)} summaries for material: {request.material_name}")
        return {
            "success": True,
            "material_name": request.material_name,
            "summary_count": len(summaries),
            "data": summaries,
        }

    except Exception as e:
        logger.error(f"Error retrieving summaries for material {request.material_name}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/data", tags=["materials"])
async def get_material_data_post(request: MaterialRequest):
    """Get both questions and summaries for a specific material name (POST version).

    Args:
        request: MaterialRequest containing material_name

    Returns:
        Dictionary with success status and both questions and summaries

    Raises:
        HTTPException: If an error occurs during retrieval
    """
    try:
        material_data = material_controller.get_material_data(request.material_name)

        logger.info(
            f"Retrieved material data for {request.material_name}: "
            f"{material_data['question_count']} questions, {material_data['summary_count']} summaries"
        )
        return {"success": True, "data": material_data}

    except Exception as e:
        logger.error(f"Error retrieving material data for {request.material_name}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
