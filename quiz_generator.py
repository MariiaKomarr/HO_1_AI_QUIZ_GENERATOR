import json

from google import genai
from google.genai import types

from config import GEMINI_API_KEY


MODEL_NAME = "gemini-3.5-flash-lite"


def generate_quiz(text: str, question_count: int = 10) -> list:
    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = f"""
Ти — викладач, який створює тестові завдання.

На основі наведеного конспекту створи
{question_count} тестових питань українською мовою.

Правила:
1. Використовуй лише інформацію з конспекту.
2. Кожне питання має 4 варіанти відповіді.
3. Лише одна відповідь правильна.
4. Не повторюй питання.
5. Додай коротке пояснення правильної відповіді.
6. Якщо матеріалу недостатньо для якісних питань,
   створи менше питань.

Поверни JSON-масив у форматі:

[
  {{
    "question": "Текст питання",
    "options": {{
      "A": "Варіант A",
      "B": "Варіант B",
      "C": "Варіант C",
      "D": "Варіант D"
    }},
    "correct_answer": "B",
    "explanation": "Пояснення"
  }}
]

КОНСПЕКТ:
{text}
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.3,
        ),
    )

    if not response.text:
        raise ValueError("Gemini повернув порожню відповідь.")

    questions = json.loads(response.text)

    if not isinstance(questions, list) or not questions:
        raise ValueError("Gemini не повернув список питань.")

    for question in questions:
        if not isinstance(question, dict):
            raise ValueError("Некоректний формат питання.")

        options = question.get("options")

        if not isinstance(options, dict) or set(options) != {
            "A", "B", "C", "D"
        }:
            raise ValueError("Некоректні варіанти відповідей.")

        if question.get("correct_answer") not in options:
            raise ValueError("Некоректна правильна відповідь.")

        if not question.get("question") or not question.get("explanation"):
            raise ValueError("Відсутній текст питання або пояснення.")

    return questions