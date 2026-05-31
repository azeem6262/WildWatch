import asyncio
import json
import datetime
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.models.database import get_db
from backend.models.tables import File
from backend.services.detector import MegaDetectorService
from backend.services.species import SpeciesNetService
from backend.config import MODEL_PATH

router = APIRouter()
detector = MegaDetectorService(model_path=MODEL_PATH)
species_svc = SpeciesNetService()

@router.get("/detect/{session_id}")
async def run_detection(session_id: int, db: Session = Depends(get_db)):
    return StreamingResponse(
        _detection_stream(session_id, db),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )

async def _detection_stream(session_id: int, db: Session):
    def emit(data: dict) -> str:
        return f"data: {json.dumps(data)}\n\n"

    # Load both models once
    detector.load()
    species_svc.load()

    files = (
        db.query(File)
        .filter(File.session_id == session_id, File.status == "pending")
        .order_by(File.id)
        .all()
    )

    total = len(files)
    animal_count = 0
    empty_count = 0
    error_count = 0

    for i, file in enumerate(files):
        file.status = "detecting"
        db.commit()

        yield emit({
            "type": "progress",
            "done": i,
            "total": total,
            "current_file": file.filename,
            "stage": "Detecting...",
            "percent": round((i / total) * 100, 1) if total > 0 else 0
        })

        try:
            # Stage 1 — MegaDetector (offline)
            detection = detector.process_file(
                filepath=file.filepath,
                file_type=file.file_type,
                sensitivity="medium"
            )

            if "error" in detection:
                raise Exception(detection["error"])

            file.animal_detected = detection["animal_detected"]
            file.detection_confidence = detection["confidence"]
            file.max_count = detection["max_count"]
            if "best_frame_path" in detection:
                file.best_frame_path = detection["best_frame_path"]

            # Stage 2 — SpeciesNet (offline)
            if detection["animal_detected"]:
                file.status = "identifying"
                db.commit()

                yield emit({
                    "type": "progress",
                    "done": i,
                    "total": total,
                    "current_file": file.filename,
                    "stage": "Identifying species...",
                    "percent": round((i / total) * 100, 1)
                })

                species_result = species_svc.identify(detection["best_frame_path"])
                file.species = species_result["species"]
                file.scientific_name = species_result["scientific_name"]
                file.species_confidence = species_result["confidence"]
                file.species_source = species_result["source"]
                file.csv_result = file.species or "Unknown Animal"
                file.csv_count = file.max_count
                file.needs_review = species_result.get("needs_review", False)
                animal_count += 1

            else:
                file.csv_result = "Absent"
                file.csv_count = 0
                file.needs_review = False
                empty_count += 1

            file.status = "done"
            file.processed_at = datetime.datetime.utcnow()
            db.commit()

            yield emit({
                "type": "result",
                "file_id": file.id,
                "filename": file.filename,
                "result": file.csv_result,
                "count": file.csv_count,
                "confidence": file.detection_confidence,
                "needs_review": file.needs_review,
                "manually_verified": file.manually_verified,
                "filepath": file.filepath,
                "best_frame_path": file.best_frame_path if hasattr(file, "best_frame_path") else None
            })

        except Exception as e:
            file.status = "error"
            file.error_message = str(e)
            file.csv_result = "Error"
            file.csv_count = 0
            db.commit()
            error_count += 1
            yield emit({
                "type": "error",
                "file_id": file.id,
                "filename": file.filename,
                "message": str(e)
            })

        await asyncio.sleep(0)

    yield emit({
        "type": "complete",
        "summary": {
            "total": total,
            "animal": animal_count,
            "empty": empty_count,
            "error": error_count
        }
    })

class OverrideRequest(BaseModel):
    species: str

@router.put("/files/{file_id}/override")
def override_species(file_id: int, req: OverrideRequest, db: Session = Depends(get_db)):
    file = db.query(File).filter(File.id == file_id).first()
    if not file:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="File not found")
    
    file.csv_result = req.species
    file.needs_review = False
    file.manually_verified = True
    file.species_source = "manual"
    db.commit()
    
    return {"status": "success", "file_id": file.id, "new_species": file.csv_result}
