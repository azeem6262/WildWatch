from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse
from backend.models.database import get_db
from backend.services.exporter import build_csv
from backend.config import EXPORT_DIR
import os

router = APIRouter(prefix="/export", tags=["export"])

@router.get("/csv/{session_id}")
def export_csv(session_id: int, db: Session = Depends(get_db)):
    try:
        csv_path = build_csv(session_id, db, EXPORT_DIR)
        
        # Open the folder in Windows Explorer and select the file
        import subprocess, sys
        if sys.platform == "win32":
            subprocess.run(["explorer", "/select,", os.path.normpath(csv_path)])
            
        return {"status": "success", "file_saved_at": csv_path}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
