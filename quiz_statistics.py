import json
from pathlib import Path
from datetime import datetime


def show_statistics():
    results_dir = Path("results")
    files = sorted(results_dir.glob("result_*.json"))

    if not files:
        print("\nІсторія тестувань порожня.")
        return

    history = []

    for file_path in files:
        with open(file_path, "r", encoding="utf-8") as file:
            result = json.load(file)

        history.append(result)

    print("\n" + "=" * 40)
    print("         ІСТОРІЯ ТЕСТУВАНЬ")
    print("=" * 40)

    print(f"{'Дата':<22} {'Результат':>10}")
    print("-" * 40)

    for result in history:
        date = datetime.fromisoformat(result["date"])
        percentage = result["percentage"]

        print(
            f"{date.strftime('%d.%m.%Y %H:%M'):<22}"
            f"{percentage:>9.2f}%"
        )

    percentages = [
        result["percentage"] for result in history
    ]

    average = sum(percentages) / len(percentages)
    best = max(percentages)

    print("\n" + "-" * 40)
    print(f"Кількість тестувань: {len(history)}")
    print(f"Середній результат: {average:.2f}%")
    print(f"Найкращий результат: {best:.2f}%")