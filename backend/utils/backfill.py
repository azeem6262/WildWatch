import threading
from sqlalchemy.orm import Session
from backend.models.database import SessionLocal
from backend.models.tables import File
from backend.utils.metadata import extract_datetime_and_relative_path

# Global state for backfill status
is_backfill_running = False

def run_datetime_backfill_background():
    global is_backfill_running
    is_backfill_running = True
    
    # Run in a separate thread so it doesn't block startup or event loop
    thread = threading.Thread(target=_run_backfill)
    thread.daemon = True
    thread.start()

def _run_backfill():
    global is_backfill_running
    db: Session = SessionLocal()
    try:
        # Find all files where datetime_full is NULL
        files = db.query(File).filter(File.datetime_full.is_(None)).all()
        
        batch = []
        for file in files:
            try:
                datetime_full, relative_path = extract_datetime_and_relative_path(file.filepath, file.file_type)
                
                # Update attributes
                if datetime_full:
                    file.datetime_full = datetime_full
                    file.file_date = datetime_full.date()
                if relative_path:
                    file.relative_path = relative_path
                    
                batch.append(file)
                
                if len(batch) >= 100:
                    db.commit()
                    batch = []
            except Exception:
                pass
                
        if batch:
            db.commit()
    finally:
        db.close()
        is_backfill_running = False
