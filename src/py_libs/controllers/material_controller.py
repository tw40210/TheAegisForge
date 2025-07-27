"""Material controller for managing Question and Summary data by material name."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from src.py_libs.controllers.sql_db_controller import Question, Summary, engine


class MaterialController:
    """Controller for managing material-based operations for Questions and Summaries."""

    def __init__(self):
        """Initialize the material controller."""
        self.engine = engine

    def get_questions_by_material_name(self, material_name: str) -> list[dict[str, Any]]:
        """Retrieve all questions associated with a specific material name.

        Args:
            material_name: The name of the material to retrieve questions for

        Returns:
            List of question data dictionaries
        """
        with Session(self.engine) as session:
            questions = (
                session.query(Question).filter(Question.material_name == material_name).all()
            )

            return [
                {
                    "id": question.id,
                    "question_type": question.question_type,
                    "summary_type": question.summary_type,
                    "content_type": question.content_type,
                    "index_number": question.index_number,
                    "material_name": question.material_name,
                    "content": question.content,
                }
                for question in questions
            ]

    def get_summaries_by_material_name(self, material_name: str) -> list[dict[str, Any]]:
        """Retrieve all summaries associated with a specific material name.

        Args:
            material_name: The name of the material to retrieve summaries for

        Returns:
            List of summary data dictionaries
        """
        with Session(self.engine) as session:
            summaries = session.query(Summary).filter(Summary.material_name == material_name).all()

            return [
                {
                    "id": summary.id,
                    "summary_type": summary.summary_type,
                    "content_type": summary.content_type,
                    "index_number": summary.index_number,
                    "material_name": summary.material_name,
                    "content": summary.content,
                }
                for summary in summaries
            ]

    def get_material_data(self, material_name: str) -> dict[str, Any]:
        """Retrieve both questions and summaries for a specific material name.

        Args:
            material_name: The name of the material to retrieve data for

        Returns:
            Dictionary containing both questions and summaries for the material
        """
        questions = self.get_questions_by_material_name(material_name)
        summaries = self.get_summaries_by_material_name(material_name)

        return {
            "material_name": material_name,
            "questions": questions,
            "summaries": summaries,
            "question_count": len(questions),
            "summary_count": len(summaries),
        }

    def list_available_materials(self) -> dict[str, Any]:
        """List all available material names from both Questions and Summaries tables.

        Returns:
            Dictionary containing unique material names and their counts
        """
        with Session(self.engine) as session:
            # Get unique material names from both tables
            question_materials = session.query(Question.material_name).distinct().all()
            summary_materials = session.query(Summary.material_name).distinct().all()

            # Extract material names from tuples and combine
            question_names = {result[0] for result in question_materials}
            summary_names = {result[0] for result in summary_materials}
            all_materials = question_names.union(summary_names)

            # Get counts for each material
            material_info = []
            for material in sorted(all_materials):
                question_count = (
                    session.query(Question).filter(Question.material_name == material).count()
                )
                summary_count = (
                    session.query(Summary).filter(Summary.material_name == material).count()
                )

                material_info.append(
                    {
                        "material_name": material,
                        "question_count": question_count,
                        "summary_count": summary_count,
                        "total_count": question_count + summary_count,
                    }
                )

            return {
                "materials": material_info,
                "total_materials": len(all_materials),
            }
