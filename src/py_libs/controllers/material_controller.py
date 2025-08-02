"""Material controller for managing Question and Summary data by material name."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from firebase_admin import auth
from sqlalchemy.orm import Session

from src.py_libs.controllers.sql_db_controller import (
    Account,
    MaterialStory,
    Question,
    QuestionSetResponse,
    Summary,
    engine,
)


class InvalidTokenError(Exception):
    """Raised when an invalid ID token is provided."""

    pass


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

    def submit_question_set_response(
        self,
        id_token: str,
        answer: dict[str, str],
        question_set_id: str,
        material_name: str,
    ) -> dict[str, Any]:
        """Submit user's response to a question set and calculate correct rate.

        Args:
            id_token: Firebase ID token for user authentication
            answer: Dictionary mapping question IDs to user's choice (e.g., {"question_1": "choice_1"})
            question_set_id: Identifier for the question set
            material_name: Name of the material

        Returns:
            Dictionary containing response data and calculated correct rate

        Raises:
            InvalidTokenError: If the provided ID token is invalid
            ValueError: If no questions found for the given question_set_id and material_name
        """
        # Verify Firebase token and get user account
        try:
            decoded = auth.verify_id_token(id_token)
            firebase_uid = decoded["uid"]
        except Exception as e:
            raise InvalidTokenError("Invalid ID token") from e

        with Session(self.engine) as session:
            # Find account by Firebase UID
            account = session.query(Account).filter(Account.firebaseUID == firebase_uid).first()
            if not account:
                raise ValueError("Account not found for this Firebase user")

            # Find or create MaterialStory
            material_story = (
                session.query(MaterialStory)
                .filter(
                    MaterialStory.account_id == account.id,
                    MaterialStory.material_name == material_name,
                )
                .first()
            )

            if not material_story:
                material_story = MaterialStory(
                    account_id=account.id,
                    material_name=material_name,
                )
                session.add(material_story)
                session.flush()  # Get the ID

            # Find questions for this question set and material
            # For now, we'll use a simple mapping where question_set_id maps to questions
            # This could be improved with a more sophisticated mapping strategy
            questions = (
                session.query(Question).filter(Question.material_name == material_name).all()
            )

            if not questions:
                raise ValueError(f"No questions found for material: {material_name}")

            # Calculate correct rate
            correct_count = 0
            total_count = len(answer)

            # For each answer provided by the user
            for question_key, user_choice in answer.items():
                # Find corresponding question in database
                # This is a simplified approach - in practice, you might need a more sophisticated mapping
                for question in questions:
                    question_content = question.content
                    if isinstance(question_content, dict):
                        # Check if this question matches the question_key
                        # This is where you'd implement your specific question matching logic
                        # For now, we'll assume the question content structure supports this
                        if self._check_user_answer(question_content, question_key, user_choice):
                            correct_count += 1
                            break

            correct_rate = correct_count / total_count if total_count > 0 else 0.0

            # Get current timestamp
            current_time = datetime.now().isoformat()

            # Find or create QuestionSetResponse
            question_set_response = (
                session.query(QuestionSetResponse)
                .filter(
                    QuestionSetResponse.material_story_id == material_story.id,
                    QuestionSetResponse.question_set_id == question_set_id,
                )
                .first()
            )

            if question_set_response:
                # Update existing response
                existing_times = question_set_response.finish_times or []
                existing_rates = question_set_response.correct_rates or []
                existing_answers = question_set_response.answers_list or []

                # Append new data
                existing_times.append(current_time)
                existing_rates.append(correct_rate)
                existing_answers.append(answer)

                # Update the record
                question_set_response.finish_times = existing_times
                question_set_response.correct_rates = existing_rates
                question_set_response.answers_list = existing_answers
            else:
                # Create new response
                question_set_response = QuestionSetResponse(
                    material_story_id=material_story.id,
                    question_set_id=question_set_id,
                    finish_times=[current_time],
                    correct_rates=[correct_rate],
                    answers_list=[answer],
                )
                session.add(question_set_response)

            session.commit()

            return {
                "success": True,
                "material_name": material_name,
                "question_set_id": question_set_id,
                "correct_rate": correct_rate,
                "correct_count": correct_count,
                "total_count": total_count,
                "finish_time": current_time,
                "account_id": account.id,
            }

    def _check_user_answer(
        self, question_content: dict, question_key: str, user_choice: str
    ) -> bool:
        """Check if user's answer is correct for a given question.

        Args:
            question_content: The JSON content of the question from database
            question_key: The question identifier (e.g., "question_1")
            user_choice: The user's choice (e.g., "choice_1")

        Returns:
            Boolean indicating if the answer is correct
        """
        try:
            # Navigate to the specific question in the content
            if question_key in question_content:
                question = question_content[question_key]
                if user_choice in question:
                    choice = question[user_choice]
                    # Check if this choice has an 'answer' field that is True
                    return choice.get("answer", False) is True
            return False
        except (KeyError, TypeError, AttributeError):
            return False
