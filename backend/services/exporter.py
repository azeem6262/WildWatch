import csv
import os
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from backend.models.tables import File, SessionModel

def build_csv(session_id: int, db: Session, output_dir: str) -> str:
    """
    Build Timelapse+-compatible CSV.
    Every file gets a row — empty frames included.
    Returns full path to the created file.
    """
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise ValueError(f"Session {session_id} not found")

    files = (
        db.query(File)
        .filter(File.session_id == session_id, File.status == "done")
        .order_by(File.file_date, File.filename)
        .all()
    )

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in session.name)
    csv_path = os.path.join(output_dir, f"WildWatch_{safe_name}_{timestamp}.csv")

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["camera_id", "result", "count", "date"])

        for file in files:
            date_value = file.file_date.strftime("%Y-%m-%d") if file.file_date else ""

            if not file.animal_detected:
                result_value = "Absent"
                count_value = 0
            else:
                result_value = file.species or "Unknown Animal"
                count_value = file.max_count or 1

            writer.writerow([
                session.camera_id,
                result_value,
                count_value,
                date_value
            ])

    return csv_path
