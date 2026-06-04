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
    safe_cam = "".join(c if c.isalnum() or c in "-_" else "_" for c in session.camera_id)
    csv_path = os.path.join(output_dir, f"WildWatch_{safe_name}_{safe_cam}_{timestamp}.csv")

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["File", "RelativePath", "DateTime", "DeleteFlag", "Species", "Individuals", "Behaviour"])

        for file in files:
            date_value = file.datetime_full.strftime("%Y-%m-%d %H:%M:%S") if file.datetime_full else ""
            
            relative_path = file.relative_path or ""
            behaviour = file.behaviour or ""

            if not file.animal_detected:
                species_value = ""
                count_value = 0
            else:
                if file.csv_result == "Unknown Animal":
                    species_value = "animal"
                else:
                    species_value = str(file.csv_result).strip().lower()
                count_value = file.max_count or 1

            writer.writerow([
                file.filename,
                relative_path,
                date_value,
                "false",
                species_value,
                count_value,
                behaviour
            ])

    return csv_path
