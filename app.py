
import os
import tempfile
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    abort,
)
from google.cloud import firestore
from werkzeug.exceptions import RequestEntityTooLarge

from document_reader import read_document
from quiz_generator import generate_quiz
from ai_analyzer import analyze_results
from result_storage import save_results
from firestore_service import db, save_result_to_firestore


load_dotenv()

app = Flask(__name__)

secret_key = os.environ.get("FLASK_SECRET_KEY")

if not secret_key:
    raise RuntimeError(
        "Не задано FLASK_SECRET_KEY. "
        "Додай його до .env або змінних середовища."
    )

app.config.update(
    SECRET_KEY=secret_key,
    MAX_CONTENT_LENGTH=10 * 1024 * 1024,
    SESSION_PERMANENT=False,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=bool(os.environ.get("K_SERVICE")),
)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_QUESTIONS = 30


# ==========================================
# ГОЛОВНА СТОРІНКА
# ==========================================

@app.route("/")
def home():
    return render_template("index.html")


# ==========================================
# ГЕНЕРАЦІЯ ТЕСТУ
# ==========================================

@app.route("/generate", methods=["POST"])
def generate():

    document = request.files.get("document")

    if not document or not document.filename:
        return "Будь ласка, вибери файл.", 400

    extension = Path(document.filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        return "Підтримуються лише PDF, DOCX і TXT.", 400

    try:
        question_count = int(
            request.form.get("num_questions", 5)
        )

        if not 1 <= question_count <= MAX_QUESTIONS:
            return "Кількість питань має бути від 1 до 30.", 400

        document_name = Path(
            document.filename.replace("\\", "/")
        ).name

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / f"document{extension}"
            document.save(file_path)
            source_text = read_document(str(file_path))

        questions = generate_quiz(
            source_text,
            question_count
        )

        # Створюємо унікальний ідентифікатор тесту
        quiz_id = uuid.uuid4().hex

        # Зберігаємо тест у Firestore
        db.collection("active_quizzes").document(
            quiz_id
        ).set({
            "questions": questions,
            "source_text": source_text,
            "document_name": document_name,
            "created_at": firestore.SERVER_TIMESTAMP,
            "expires_at": (
                datetime.now(timezone.utc)
                + timedelta(hours=2)
            ),
        })

        # У cookie зберігається лише ID
        session["quiz_id"] = quiz_id

        return render_template(
            "quiz.html",
            questions=questions
        )

    except ValueError as error:
        return f"Помилка: {error}", 400

    except Exception:
        app.logger.exception("Помилка генерації тесту")
        return "Не вдалося згенерувати тест.", 500


# ==========================================
# ПЕРЕВІРКА ТЕСТУ
# ==========================================

@app.route("/submit", methods=["POST"])
def submit_quiz():

    quiz_id = session.get("quiz_id")

    if not quiz_id:
        return redirect(url_for("home"))

    quiz_ref = db.collection(
        "active_quizzes"
    ).document(quiz_id)

    quiz_snapshot = quiz_ref.get()

    if not quiz_snapshot.exists:
        session.pop("quiz_id", None)
        return redirect(url_for("home"))

    quiz_data = quiz_snapshot.to_dict()

    expires_at = quiz_data.get("expires_at")

    if (
        expires_at
        and datetime.now(timezone.utc) > expires_at
    ):
        quiz_ref.delete()
        session.pop("quiz_id", None)
        return "Час проходження тесту закінчився.", 410

    questions = quiz_data["questions"]
    source_text = quiz_data["source_text"]
    document_name = quiz_data["document_name"]

    results = []
    mistakes = []
    correct_count = 0

    for index, question in enumerate(
        questions,
        start=1
    ):
        selected = request.form.get(
            f"question_{index}"
        )

        correct = question["correct_answer"]
        options = question["options"]

        is_correct = selected == correct

        if is_correct:
            correct_count += 1
        else:
            mistakes.append({
                "question": question["question"],
                "student_answer": options.get(
                    selected,
                    "Не обрано"
                ),
                "correct_answer": options[correct],
                "explanation": question["explanation"],
            })

        results.append({
            "number": index,
            "question": question["question"],
            "selected": selected,
            "correct": correct,
            "is_correct": is_correct,
            "options": options,
            "explanation": question["explanation"],
        })

    total = len(questions)

    percentage = round(
        correct_count / total * 100,
        2
    )

    analysis_data = {
        "percentage": percentage,
        "correct_answers": correct_count,
        "incorrect_answers": total - correct_count,
        "total_questions": total,
        "mistakes": mistakes,
    }

    # Аналіз через Gemini
    try:
        ai_analysis = analyze_results(
            analysis_data,
            source_text
        )
    except Exception:
        app.logger.exception("Помилка AI-аналізу")
        ai_analysis = (
            "AI-аналіз тимчасово недоступний."
        )

    # Запис результату у Firestore
    try:
        save_result_to_firestore(
            analysis_data,
            document_name
        )
    except Exception:
        app.logger.exception(
            "Помилка запису результату у Firestore"
        )

    # Локальний JSON для резервного збереження
    # У Cloud Run локальна файлова система тимчасова
    if not os.environ.get("K_SERVICE"):
        try:
            save_results(
                analysis_data,
                document_name
            )
        except Exception:
            app.logger.exception(
                "Помилка локального збереження"
            )

    # Видаляємо активний тест
    try:
        quiz_ref.delete()
    except Exception:
        app.logger.exception(
            "Не вдалося видалити активний тест"
        )

    session.pop("quiz_id", None)

    return render_template(
        "result.html",
        results=results,
        correct_count=correct_count,
        total=total,
        percentage=percentage,
        ai_analysis=ai_analysis,
    )


# ==========================================
# ХМАРНА ІСТОРІЯ ТЕСТУВАНЬ
# ==========================================

@app.route("/history")
def history():

    history_records = []

    try:
        documents = db.collection(
            "quiz_results"
        ).stream()

        for document in documents:
            record = document.to_dict()

            if not record:
                continue

            date = record.get("created_at")

            if date is None:
                continue

            history_records.append({
                "date": date,
                "document": record.get(
                    "document",
                    "Невідомий"
                ),
                "percentage": float(
                    record.get("percentage", 0)
                ),
                "correct": record.get(
                    "correct_answers",
                    0
                ),
                "total": record.get(
                    "total_questions",
                    0
                ),
            })

    except Exception:
        app.logger.exception(
            "Помилка отримання історії"
        )
        return "Не вдалося завантажити історію.", 503

    history_records.sort(
        key=lambda item: item["date"],
        reverse=True
    )

    percentages = [
        item["percentage"]
        for item in history_records
    ]

    total_tests = len(history_records)

    average = (
        round(
            sum(percentages) / total_tests,
            2
        )
        if total_tests else 0
    )

    best = max(percentages) if percentages else 0

    return render_template(
        "history.html",
        history=history_records,
        total_tests=total_tests,
        average=average,
        best=best,
    )


# ==========================================
# ОБРОБКА ПОМИЛОК
# ==========================================

@app.errorhandler(RequestEntityTooLarge)
def file_too_large(error):
    return "Максимальний розмір файлу — 10 МБ.", 413


# ==========================================
# ЛОКАЛЬНИЙ ЗАПУСК
# ==========================================

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=not bool(os.environ.get("K_SERVICE")),
    )
