import cv2
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from backend.models.tables import File

SUPPORTED_VIDEO = {'.mp4', '.avi', '.mov', '.mkv'}
SUPPORTED_PHOTO = {'.jpg', '.jpeg', '.png'}

def scan_folder(folder_path: str, session_id: int, db: Session) -> dict:
    """
    Walk folder recursively, register all valid files in DB.
    Returns: { "total": 3000, "photos": 1200, "videos": 1800, "skipped": 12 }
    """
    folder = Path(folder_path)
    if not folder.exists():
        raise ValueError(f"Folder not found: {folder_path}")

    stats = {"total": 0, "photos": 0, "videos": 0, "skipped": 0}
    batch = []

    for filepath in sorted(folder.rglob("*")):
        if not filepath.is_file():
            continue

        ext = filepath.suffix.lower()

        if ext in SUPPORTED_VIDEO:
            file_type = "video"
        elif ext in SUPPORTED_PHOTO:
            file_type = "photo"
        else:
            stats["skipped"] += 1
            continue

        # Date from file system — GRDE PRO has no timestamp in filename
        try:
            file_date = datetime.fromtimestamp(filepath.stat().st_mtime).date()
        except Exception:
            file_date = None

        # Video duration
        duration_sec = None
        if file_type == "video":
            try:
                cap = cv2.VideoCapture(str(filepath))
                fps = cap.get(cv2.CAP_PROP_FPS)
                frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                if fps > 0:
                    duration_sec = round(frames / fps, 2)
                cap.release()
            except Exception:
                pass

        batch.append(File(
            session_id=session_id,
            filename=filepath.name,
            filepath=str(filepath.resolve()),
            file_type=file_type,
            file_date=file_date,
            file_size_bytes=filepath.stat().st_size,
            duration_sec=duration_sec,
            status="pending"
        ))

        stats["total"] += 1
        stats[file_type + "s"] += 1

        # Commit in batches of 500 to avoid memory pressure on 3,000 files
        if len(batch) >= 500:
            db.bulk_save_objects(batch)
            db.commit()
            batch = []

    if batch:
        db.bulk_save_objects(batch)
        db.commit()

    return stats
