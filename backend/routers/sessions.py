from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.models.database import get_db
from backend.models.tables import SessionModel, File

router = APIRouter(prefix="/sessions", tags=["sessions"])

class SessionCreate(BaseModel):
    name: str
    camera_id: str
    location: str = ""

@router.post("/")
def create_session(session_in: SessionCreate, db: Session = Depends(get_db)):
    new_session = SessionModel(
        name=session_in.name,
        camera_id=session_in.camera_id,
        location=session_in.location
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return {"id": new_session.id}

@router.get("/")
def list_sessions(db: Session = Depends(get_db)):
    sessions = db.query(SessionModel).order_by(SessionModel.created_at.desc()).all()
    return sessions

@router.get("/{session_id}")
def get_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    total_files = db.query(File).filter(File.session_id == session_id).count()
    return {
        "id": session.id,
        "name": session.name,
        "camera_id": session.camera_id,
        "location": session.location,
        "created_at": session.created_at,
        "total_files": total_files
    }

@router.delete("/{session_id}")
def delete_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(session)
    db.commit()
    return {"status": "ok"}
