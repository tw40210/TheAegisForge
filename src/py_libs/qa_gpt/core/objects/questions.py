from pydantic import BaseModel


class Choice(BaseModel):
    choice_description: str
    answer: bool
    explanation: str

    def __str__(self):
        return f"""
        choice_description:{self.choice_description}
        answer:{self.answer}
        explanation:{self.explanation}
        """


class MultipleChoiceQuestion(BaseModel):
    question_description: str
    choice_1: Choice
    choice_2: Choice
    choice_3: Choice
    choice_4: Choice

    def __str__(self):
        split_line = "=" * 20 + "\n"
        return f"""
        {split_line}
        question_description:{self.descriquestion_descriptionption}
        choice_1:{self.choice_1}
        choice_2:{self.choice_2}
        choice_3:{self.choice_3}
        choice_4:{self.choice_4}
        {split_line}
        """


class MultipleChoiceQuestionSet(BaseModel):
    question_1: MultipleChoiceQuestion
    question_2: MultipleChoiceQuestion
    question_3: MultipleChoiceQuestion
    question_4: MultipleChoiceQuestion
    question_5: MultipleChoiceQuestion
