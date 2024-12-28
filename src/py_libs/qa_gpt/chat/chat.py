import os

import openai
from pydantic import BaseModel
from src.py_libs.qa_gpt.chat.private_keys import openapi_key

os.environ["OPENAI_API_KEY"] = openapi_key
client = openai.OpenAI()


def check_api():
    if len(os.environ["OPENAI_API_KEY"]) == 0:
        raise ValueError("OPENAI_API_KEY is not set properly, got empty")


def get_chat_gpt_response(messages):
    check_api()
    MODEL = "gpt-4o-mini"
    response = openai.ChatCompletion.create(model=MODEL, messages=messages, temperature=1)
    return response["choices"][0]["message"]["content"]


def get_chat_gpt_response_structure(messages: list, res_obj: BaseModel):
    check_api()
    MODEL = "gpt-4o-mini"

    response = client.beta.chat.completions.parse(
        model=MODEL,
        messages=messages,
        response_format=res_obj,
    )

    return response.choices[0].message.parsed
