
from google.cloud import firestore

PROJECT_ID = "ai-quiz-generator-511621"

db = firestore.Client(
    project=PROJECT_ID,
    database="(default)"
)


def test_connection():
    doc_ref = db.collection("connection_tests").document("test_1")

    doc_ref.set({
        "message": "AI Quiz Generator connected successfully",
        "status": "success",
        "created_at": firestore.SERVER_TIMESTAMP
    })

    print("Успішно записано документ у Firestore!")


if __name__ == "__main__":
    test_connection()



def save_result_to_firestore(results: dict, document_name: str):
    record = {
        "document": document_name,
        "percentage": results["percentage"],
        "correct_answers": results["correct_answers"],
        "total_questions": results["total_questions"],
        "mistakes": results["mistakes"],
        "created_at": firestore.SERVER_TIMESTAMP,
    }

    document_ref = db.collection("quiz_results").document()
    document_ref.set(record)

    print("Результат тесту збережено у Firestore!")
    return document_ref.id
