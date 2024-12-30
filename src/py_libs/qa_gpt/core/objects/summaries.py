from pydantic import BaseModel


class Motivation(BaseModel):
    description: str
    problem_to_solve: str
    how_to_solve: str
    why_can_be_solved: str

    def __str__(self):
        split_line = "=" * 20 + "\n"
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
        split_line = "=" * 20 + "\n"
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
        split_line = "=" * 20 + "\n"
        return f"""
        {split_line}
        subject:{self.subject}
        description:{self.description}
        importance_explanation:{self.importance_explanation}
        technical_details:{self.technical_details}
        importance:{self.importance}
        {split_line}
        """


class Summary(BaseModel):
    motivation: Motivation
    conclusion: Conclusion
    content_bullet_points: list[BulletPoint]
