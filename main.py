import json
from pathlib import Path
from ai_analyzer import analyze_results
from result_storage import save_results

from document_reader import read_document
from quiz_generator import generate_quiz
from quiz_runner import run_quiz

from quiz_statistics import show_statistics


def main():
    print("=" * 40)
    print("           AI QUIZ GENERATOR")
    print("=" * 40)

    file_path = input(
        "\nВведіть шлях до конспекту "
        "(Enter — documents/test_notes.txt): "
    ).strip().strip('"')

    if not file_path:
        file_path = "documents/test_notes.txt"

    try:
        text = read_document(file_path)

        print("\nКонспект успішно завантажено!")
        print(f"Кількість символів: {len(text)}")

        print("\nGemini генерує тест. Зачекайте...")

        questions = generate_quiz(text, question_count=10)

        print(f"\nЗгенеровано {len(questions)} питань.")

        results_dir = Path("results")
        results_dir.mkdir(exist_ok=True)

        # Зберігаємо тест
        with open(
            results_dir / "quiz.json",
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                questions,
                file,
                ensure_ascii=False,
                indent=4,
            )

        # Запускаємо проходження тесту
        results = run_quiz(questions)

        print("\n" + "=" * 40)
        print("          AI-АНАЛІЗ ЗНАНЬ")
        print("=" * 40)

        print("\nGemini аналізує ваші відповіді...")

        try:
            analysis = analyze_results(results, text)

            print("\n" + analysis)

            results["ai_analysis"] = analysis

        except Exception as error:
            print(f"\nНе вдалося виконати AI-аналіз: {error}")
            results["ai_analysis"] = None

        # Зберігаємо результати
        output_path = save_results(results, file_path)

        print(f"\nРезультати збережено: {output_path}")

        show_statistics()

    except Exception as error:
        print(f"\nПомилка: {error}")


if __name__ == "__main__":
    main()