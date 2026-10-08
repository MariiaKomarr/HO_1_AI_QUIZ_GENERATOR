def run_quiz(questions: list) -> dict:
    correct_count = 0
    mistakes = []

    print("\n" + "=" * 40)
    print("          ПОЧАТОК ТЕСТУ")
    print("=" * 40)

    for index, question in enumerate(questions, start=1):
        print(f"\nПитання {index}/{len(questions)}")
        print(question["question"])

        for letter, option in question["options"].items():
            print(f"{letter}) {option}")

        while True:
            answer = input("\nВаша відповідь (A/B/C/D): ").strip().upper()

            if answer in ["A", "B", "C", "D"]:
                break

            print("Введіть A, B, C або D.")

        correct_answer = question["correct_answer"]

        if answer == correct_answer:
            correct_count += 1
        else:
            mistakes.append({
                "question": question["question"],
                "user_answer": answer,
                "correct_answer": correct_answer,
                "correct_text": question["options"][correct_answer],
                "explanation": question["explanation"],
            })

    total = len(questions)
    percentage = round(correct_count / total * 100, 2)

    print("\n" + "=" * 40)
    print("          РЕЗУЛЬТАТ ТЕСТУ")
    print("=" * 40)

    print(f"Кількість питань: {total}")
    print(f"Правильних відповідей: {correct_count}")
    print(f"Помилок: {len(mistakes)}")
    print(f"Результат: {percentage}%")

    if mistakes:
        print("\nВаші помилки:")

        for index, mistake in enumerate(mistakes, start=1):
            print(f"\n{index}. {mistake['question']}")
            print(f"Ваша відповідь: {mistake['user_answer']}")
            print(
                f"Правильна відповідь: "
                f"{mistake['correct_answer']}) "
                f"{mistake['correct_text']}"
            )
            print(f"Пояснення: {mistake['explanation']}")
    else:
        print("\nВідмінно! Усі відповіді правильні!")

    return {
        "total_questions": total,
        "correct_answers": correct_count,
        "incorrect_answers": len(mistakes),
        "percentage": percentage,
        "mistakes": mistakes,
    }