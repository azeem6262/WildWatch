from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.models.database import get_db
from backend.services.ingest import scan_folder
from backend.models.tables import File

router = APIRouter(prefix="/files", tags=["files"])

class IngestRequest(BaseModel):
    session_id: int
    folder_path: str

@router.post("/ingest")
def ingest_files(req: IngestRequest, db: Session = Depends(get_db)):
    try:
        stats = scan_folder(req.folder_path, req.session_id, db)
        return {"status": "ok", "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{session_id}")
def list_files(session_id: int, db: Session = Depends(get_db)):
    files = db.query(File).filter(File.session_id == session_id).order_by(File.id).all()
    return files
