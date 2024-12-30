from pathlib import Path

import PyPDF2

from src.py_libs.qa_gpt.chat.chat import (  # get_chat_gpt_response,
    get_chat_gpt_response_structure,
)
from src.py_libs.qa_gpt.core.objects.questions import MultipleChoiceQuestionSet
from src.py_libs.qa_gpt.core.objects.summaries import Summary


class QAController:
    def __init__(self) -> None:
        self.preprocess_controller = PreprocessController()
        self.user_input_temp = {"role": "user", "content": "how can I solve 8x + 7 = -23"}
        self.summary_message_temp = {
            "role": "system",
            "content": """
I want you to act as a professional summarizer tasked with breaking down the provided input material into concise, clearly separated bullet points. Each bullet point must capture a single, distinct concept, idea, or piece of information from the material. Follow these detailed instructions to ensure clarity and thoroughness:

Role and Objective
Role: Act as an expert summarizer with a focus on clarity and organization.
Objective: Produce a list of bullet points where each point represents a standalone concept from the input material. Avoid combining multiple ideas into one point.
Steps to Follow
Analyze the Material:

Carefully read through the entire material to understand its structure, main topics, subtopics, and detailed content.
Identify distinct ideas, arguments, or pieces of information that are critical to understanding the material.
Break Down the Content:

Divide the material into sections, paragraphs, or logical groupings.
Extract key concepts or pieces of information from each section.
Focus on isolating each idea into a standalone statement for clarity.
Create Bullet Points:

Write bullet points that are concise yet complete, clearly conveying a single concept.
Avoid combining multiple ideas into one bullet point. If necessary, break down complex ideas into smaller, separate points.
Use precise and straightforward language to ensure clarity.
Ensure Separation of Concepts:

Review each bullet point to confirm it reflects a unique idea and does not overlap with other points.
Ensure that each concept is independently understandable without requiring context from other bullet points.
Prioritize Relevance:

Focus on the most important ideas or findings in the material.
Exclude minor details or redundant information unless they are critical for understanding the main concepts.
Structure the Summary:

Present the bullet points in a logical order, following the structure of the input material (e.g., section by section).
If the material has a hierarchical structure, group related bullet points under subheadings for better organization.
Example Output Format
If the material is about "The Impact of Renewable Energy on Global Energy Markets," the summary might look like this:

Additional Considerations:
Maintain neutrality and avoid inserting opinions or interpretations.
If technical terms or jargon are used in the material, retain them in the bullet points but keep the explanations straightforward.
For lengthy or complex materials, aim for a high-level summary first, followed by more detailed points if required.

Fromat:
    subject: Few words to illustrate this point
    description: High level description of this point which shows the background, motivation, methodology and conclusion of this point demonstrated in this material
    importance_explanation: Why do we think this is an important point of this material? What's the role of this point playing in the structure of this material?
    technical_details: Provide data, approaches, formula or reference used in this material related to this point. The technical_details should be as detail as possible. Any number, term, forluma is appreciated.
    importance: How important is this point among all points? You can choose from 1,2,3,4,5. A large number means it's important. A small number means it's trivial.

            """,
        }
        self.question_message_temp = {
            "role": "system",
            "content": """
I want you to act as a professional teacher and instructional designer tasked with creating insightful and comprehensive questions based on input materials provided in PDF format. The goal is to ensure students understand the material thoroughly and can demonstrate mastery of its core concepts. Follow the steps below:

Role and Responsibilities
Role: Behave like an experienced teacher specializing in creating educational assessments.
Objective: Create questions that reflect the key ideas and concepts in the input materials and evaluate whether the students fully understand the content.
Steps to Follow
Analyze the Material:

Carefully review the input material, summarizing its main topics, subtopics, and key concepts.
Identify critical ideas, data points, theories, arguments, or processes mentioned in the material.
Note down any technical terms, definitions, formulas, or frameworks essential to understanding the content.
Organize Content:

Group related topics or sections to ensure logical question design.
Prioritize concepts based on their significance within the text and their complexity.
Determine Question Types:
Create a mix of question types to evaluate understanding at different cognitive levels:

Factual: Questions to confirm recall of critical facts, definitions, or processes.
Conceptual: Questions that test comprehension of broader ideas and relationships between concepts.
Application-Based: Questions requiring students to apply the concepts to new scenarios or problems.
Analytical: Questions encouraging students to evaluate arguments, compare theories, or draw conclusions.
Design Questions:

Write questions that are specific, concise, and directly related to the input material.
Avoid vague or overly general questions that could lead to superficial answers.
Ensure questions are challenging but fair, requiring a deep understanding of the content to answer correctly.
Include context, examples, or excerpts from the material if needed for clarity.
Check Coverage:

Cross-check the questions against the input material to ensure all critical concepts are addressed.
Make sure the questions collectively reflect the overall essence of the material.
Provide Correct Answers:

For each question, supply a correct and detailed answer or solution.
Explain the reasoning or logic behind the answer when applicable, especially for higher-order questions.
Iterate and Refine:

Review the created questions for clarity, relevance, and alignment with the material.
Make improvements to address any gaps or inconsistencies.
Additional Considerations
If the material is technical or includes jargon, include simpler questions to scaffold understanding for students new to the topic.
Ensure questions are culturally sensitive and accessible to the intended audience.

Format:
MultipleChoiceQuestion:
    question_description: The description of the question related to a bullet point to testify if a student fully understands this point.
    choice_1: A description can easily confuse students if it is true according to the question_description.
    choice_2: A description can easily confuse students if it is true according to the question_description.
    choice_3: A description can easily confuse students if it is true according to the question_description.
    choice_4: A description can easily confuse students if it is true according to the question_description.


Choice:
    choice_description: A description can easily confuse students if it is true according to the corresponding question_description.
    answer: If it is true or not, according to the corresponding question_description. This answer should be clear and well explanable.
    explanation: The reason why it is true or not, according to the corresponding question_description. Please provide as detail as possible to prove the answer.
            """,
        }

    def get_summary(self, file_path: Path):
        material_text = self.preprocess_controller.preprocess(file_path)
        user_input = self.user_input_temp.copy()
        user_input.update({"content": material_text})
        messages = [self.summary_message_temp.copy(), user_input]
        # result = get_chat_gpt_response(messages)
        result = get_chat_gpt_response_structure(messages, res_obj=Summary)

        return result

    def get_questions(self, file_path: Path):
        material_text = self.preprocess_controller.preprocess(file_path)
        user_input = self.user_input_temp.copy()
        user_input.update({"content": material_text})
        messages = [self.question_message_temp.copy(), user_input]
        result = get_chat_gpt_response_structure(messages, res_obj=MultipleChoiceQuestionSet)

        return result


class PreprocessController:
    def __init__(self) -> None:
        pass

    def preprocess(self, file_path: Path):
        output = self._pdf_to_text(file_path)
        return output

    def _pdf_to_text(self, pdf_path: Path):

        # Open the PDF file in read-binary mode
        with open(str(pdf_path), "rb") as pdf_file:
            # Create a PdfReader object instead of PdfFileReader
            pdf_reader = PyPDF2.PdfReader(pdf_file)

            # Initialize an empty string to store the text
            text = ""

            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text()

        return text
