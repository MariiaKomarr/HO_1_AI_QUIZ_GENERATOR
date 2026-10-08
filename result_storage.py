import json
from datetime import datetime
from pathlib import Path


def save_results(results: dict, document_path: str) -> Path:
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    record = {
        "date": datetime.now().isoformat(timespec="seconds"),
        "document": Path(document_path).name,
        **results,
    }

    output_path = results_dir / f"result_{timestamp}.json"

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(record, file, ensure_ascii=False, indent=4)

    return output_path