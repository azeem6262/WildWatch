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
        return FileResponse(
            path=csv_path,
            filename=os.path.basename(csv_path),
            media_type="text/csv"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
