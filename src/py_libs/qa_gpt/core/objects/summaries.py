from pydantic import BaseModel


class Motivation(BaseModel):
    description: str
    problem_to_solve: str
    how_to_solve: str
    why_can_be_solved: str

    def __str__(self):
        split_line = "*" * 20 + "\n"
        return f"""
        {split_line}
        description:{self.description}
        problem_to_solve:{self.problem_to_solve}
        how_to_solve:{self.how_to_solve}
        why_can_be_solved:{self.why_can_be_solved}
        {split_line}
        """


class Conclusion(BaseModel):
    description: str
    problem_to_solve: str
    how_much_is_solved: str
    contribution: str

    def __str__(self):
        split_line = "*" * 20 + "\n"
        return f"""
        {split_line}
        description:{self.description}
        problem_to_solve:{self.problem_to_solve}
        how_much_is_solved:{self.how_much_is_solved}
        contribution:{self.contribution}
        {split_line}
        """


class BulletPoint(BaseModel):
    subject: str
    description: str
    technical_details: str
    importance_explanation: str
    importance: int

    def __str__(self):
        split_line = "*" * 20 + "\n"
        return f"""
        {split_line}
        subject:{self.subject}
        description:{self.description}
        importance_explanation:{self.importance_explanation}
        technical_details:{self.technical_details}
        importance:{self.importance}
        {split_line}
        """

    @classmethod
    def model_json_schema(cls):
        return {
            "type": "object",
            "properties": {
                "subject": {"type": "string"},
                "description": {"type": "string"},
                "technical_details": {"type": "string"},
                "importance_explanation": {"type": "string"},
                "importance": {"type": "integer"},
            },
            "required": [
                "subject",
                "description",
                "technical_details",
                "importance_explanation",
                "importance",
            ],
        }


class BaseSummary(BaseModel):
    """Base summary class with motivation and bullet points"""

    motivation: Motivation
    bullet_points: list[BulletPoint]

    def __str__(self):
        split_line = "=" * 20 + "\n"
        return f"""
        {split_line}
        motivation:{self.motivation}
        bullet_points:{self.bullet_points}
        {split_line}
        """

    @classmethod
    def model_json_schema(cls):
        schema = super().model_json_schema()
        schema["required"] = list(schema["properties"].keys())
        return schema


class StandardSummary(BaseSummary):
    """Standard summary type with motivation, conclusion and bullet points"""

    motivation: Motivation
    conclusion: Conclusion
    bullet_points: list[BulletPoint]

    def __str__(self):
        split_line = "=" * 20 + "\n"
        return f"""
        {split_line}
        motivation:{self.motivation}
        conclusion:{self.conclusion}
        bullet_points:{self.bullet_points}
        {split_line}
        """

    def model_dump(self):
        return {
            "summary_type": "standard",
            "motivation": self.motivation.model_dump(),
            "conclusion": self.conclusion.model_dump(),
            "bullet_points": [bp.model_dump() for bp in self.bullet_points],
        }


class TechnicalSummary(BaseModel):
    """Summary specifically for technical documentation"""

    overview: str
    key_concepts: list[str]
    technical_details: dict[str, str]
    implementation_steps: list[str]
    requirements: dict[str, str]
    limitations: list[str]

    def __str__(self):
        split_line = "=" * 20 + "\n"
        return f"""
        {split_line}
        overview:{self.overview}
        key_concepts:{self.key_concepts}
        technical_details:{self.technical_details}
        implementation_steps:{self.implementation_steps}
        requirements:{self.requirements}
        limitations:{self.limitations}
        {split_line}
        """

    def model_dump(self):
        return {
            "overview": self.overview,
            "key_concepts": self.key_concepts,
            "technical_details": self.technical_details,
            "implementation_steps": self.implementation_steps,
            "requirements": self.requirements,
            "limitations": self.limitations,
        }

    @classmethod
    def model_json_schema(cls):
        return {
            "type": "object",
            "title": "TechnicalSummary",
            "description": "Summary specifically for technical documentation",
            "properties": {
                "overview": {
                    "type": "string",
                    "description": "A high-level overview of the technical content",
                },
                "key_concepts": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of key technical concepts",
                },
                "technical_details": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                    "description": "Technical details as key-value pairs",
                },
                "implementation_steps": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of implementation steps",
                },
                "requirements": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                    "description": "Requirements as key-value pairs",
                },
                "limitations": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of limitations",
                },
            },
            "required": [
                "overview",
                "key_concepts",
                "technical_details",
                "implementation_steps",
                "requirements",
                "limitations",
            ],
        }
