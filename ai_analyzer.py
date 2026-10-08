import json

from google import genai
from config import GEMINI_API_KEY


MODEL_NAME = "gemini-3.5-flash-lite"


def analyze_results(results: dict, source_text: str) -> str:
    if not results["mistakes"]:
        return (
            "Вітаємо! Усі відповіді правильні.\n"
            "Рекомендуємо переходити до складніших питань."
        )

    client = genai.Client(api_key=GEMINI_API_KEY)

    mistakes_json = json.dumps(
        results["mistakes"],
        ensure_ascii=False,
        indent=2
    )

    prompt = f"""
Ти — AI-помічник викладача.

Проаналізуй результати тестування студента.

Результат: {results["percentage"]}%
Правильних відповідей: {results["correct_answers"]}
Усього питань: {results["total_questions"]}

ПОМИЛКИ СТУДЕНТА:
{mistakes_json}

НАВЧАЛЬНИЙ МАТЕРІАЛ:
{source_text}

Сформуй відповідь українською мовою.

Структура відповіді:

1. Загальна оцінка знань
2. Теми, які студент засвоїв недостатньо
3. Пояснення допущених помилок
4. Рекомендації щодо повторення матеріалу
5. Короткий підсумок

Правила:
- Спирайся лише на наданий конспект.
- Не вигадуй інформацію, якої немає в матеріалі.
- Не роби висновків про знання тем, які не перевірялися.
- Надавай конкретні та зрозумілі рекомендації.
- Пиши доброзичливо й конструктивно.
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    if not response.text:
        raise ValueError("Gemini не повернув аналіз.")

    return response.text