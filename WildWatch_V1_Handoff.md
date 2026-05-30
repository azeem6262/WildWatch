# WildWatch v1 — Complete Agent Handoff Document
### Everything needed to build this from scratch, no questions asked

---

## 0. Read This First

This document is written for an agent or developer picking up this project cold. Every decision has been made. Every open variable has a fallback. You do not need to ask the client anything to start. Read this top to bottom once, then go to Section 8 and start building.

**Key architecture decision**: The entire pipeline runs **fully offline**. No API keys. No internet dependency. No approval waitlists. Detection uses MegaDetector v5a. Species identification uses SpeciesNet — the same model that powers Wildlife Insights, now open-sourced by Google, trained on 65 million camera trap images, 94.5% species accuracy. Both models run locally on the user's laptop.

---

## 1. What We Are Building

A **Windows desktop app** called **WildWatch** for a wildlife conservation field team in India.

### The One Problem We Are Solving
Field associates collect up to **3,000 photos and videos** per session from a **GRDE PRO camera trap**. Every file is either a false trigger (wind, leaves, empty path) or an animal sighting. Right now a person watches every single file manually. WildWatch runs AI on the whole folder and produces a **CSV** that imports directly into their existing software (Timelapse+).

### What v1 Delivers
- Scan a folder of up to 3,000 photos/videos
- Detect whether an animal is present — MegaDetector v5a (offline)
- Identify the species — SpeciesNet (offline, same model as Wildlife Insights)
- Count the maximum number of individuals visible in any single frame
- Export a CSV with: `camera_id`, `result`, `count`, `date`
- SpeciesNet output converts natively to Timelapse+ format via built-in script

### What v1 Is NOT
- Not a video player or manual review UI (Timelapse+ handles that)
- Not a web app or mobile app
- Not multi-camera per session (one camera = one territory = one session)
- Not individual animal re-identification across sessions

---

## 2. Client Context

| Field | Detail |
|---|---|
| End users | Field associates — non-technical, Windows laptops |
| Camera brand | GRDE PRO (Indian brand) |
| Video filename format | `dscf0073.mp4` (lowercase, sequential, no timestamp in name) |
| Photo filename format | `dscf0073.jpeg` |
| Files per session | Up to 3,000 (mix of photos and videos) |
| Target animals | Any mammal — species name required in output |
| Camera IDs | Format: `C1`, `C11`, `C15` etc. — user types it in at session start |
| Existing software | **Timelapse+** — they import CSVs into it |
| Required CSV columns | `camera_id`, `result`, `count`, `date` |
| Internet required | **No** — entire pipeline runs offline |

---

## 3. Why SpeciesNet Instead of an API or Custom-Trained Model

### Option Comparison

| | Train on Kaggle data | Wildlife Insights API | SpeciesNet (chosen) |
|---|---|---|---|
| Internet needed | No | Yes | **No** |
| Approval wait | No | 1–3 days | **No** |
| Indian species coverage | Poor | Good | **Good (65M global images)** |
| Accuracy | Unpredictable | ~85–90% | **94.5%** |
| Cost | Your compute time | Free tier | **Completely free** |
| Runs locally | Yes | No | **Yes** |
| Timelapse+ compatible output | Manual work needed | No | **Built-in conversion script** |
| Maintenance | You own it | Google maintains | **Google maintains** |

### Why not train a custom model on Kaggle
Kaggle wildlife datasets are mostly zoo photos, daytime nature photography, and Western/African species. A model trained on them would confidently misidentify a civet as a raccoon. That is worse than writing `Unknown Animal`. The data problem is harder than the training problem.

### Why SpeciesNet is the right call
- It is the exact model powering Wildlife Insights — same weights, same accuracy, now open-source
- Trained on 65 million camera trap images globally including Asian fauna
- Classifies 2,498 species including Indian forest mammals
- Ships with `speciesnet_to_md.py` — a conversion script that outputs in Timelapse+ format
- Runs entirely on the local machine, no network call needed
- Maintained by Google, not by you

---

## 4. CSV Output Format

Every file gets a row. Empty frames are data — absence of animal is a valid observation.

```
camera_id,  result,           count,  date
C1,         Small Indian Civet, 1,    2024-03-12
C1,         Empty,              0,    2024-03-12
C1,         Sambar Deer,        3,    2024-03-13
C1,         Empty,              0,    2024-03-13
C1,         Unknown Animal,     1,    2024-03-14
C1,         Empty,              0,    2024-03-14
```

### Result column rules

| Situation | Result value | Count |
|---|---|---|
| Animal detected, species ID confident | Species common name e.g. `Small Indian Civet` | Max individuals in any frame |
| Animal detected, species confidence low | `Unknown Animal` | Max individuals in any frame |
| No animal detected | `Empty` | `0` |
| File could not be read | `Error` | `0` |

### Count column rules
- **Photos**: number of bounding boxes MegaDetector draws (one box = one individual)
- **Videos**: highest individual count seen across all sampled frames
- Example: frame 1 shows 1 deer, frame 2 shows 3 deer → count = `3`
- Count is a best estimate — partially obscured animals may not be detected. Client is aware.

### Date column
- Source: file system modification/creation date (GRDE PRO filenames have no embedded timestamp)
- Format: `YYYY-MM-DD`

---

## 5. The Two Pending Configs — Handled as Session Inputs

### Config 1 — Camera ID
- **UI**: Text input labelled "Camera ID"
- **Validation**: Required, max 20 characters
- **Examples**: `C1`, `C11`, `C15`
- **Goes into**: Every row of the `camera_id` CSV column

### Config 2 — Result Format
Client has not confirmed exact wording. Handle as a dropdown until confirmed.

| Option | Animal value | Empty value | Default? |
|---|---|---|---|
| Species Name / Empty | `<species name>` | `Empty` | ✅ |
| Species Name / 0 | `<species name>` | `0` | |
| Species Name / Blank | `<species name>` | `` | |

Once client confirms, remove the dropdown and hardcode the value.

---

## 6. Tech Stack — Exact Versions

| Layer | Choice | Notes |
|---|---|---|
| Desktop shell | **Tauri v2** | Wraps app into `.exe`. ~10MB shell. |
| Frontend | **HTML + Vanilla JS + CSS** | No framework. Simple and maintainable. |
| Backend | **Python 3.11 + FastAPI 0.111.0** | Served on `localhost:8765` |
| ASGI server | **Uvicorn 0.29.0** | |
| Animal detection | **MegaDetector v5a** | Detects animal presence + bounding boxes + individual count |
| Species identification | **SpeciesNet** (Google, open-source) | Identifies species from detected animal crops. Fully offline. |
| ML framework | **PyTorch ≥ 2.0.0** | CPU build for distribution |
| Image/video | **OpenCV 4.9.0.80** | Frame extraction from video |
| Image handling | **Pillow 10.3.0** | |
| Database | **SQLite via SQLAlchemy 2.0.30** | Local, no server needed |
| CSV export | **Python stdlib `csv`** | No extra dependency |
| Packaging | **PyInstaller 6.6.0** | Bundles Python backend into `.exe` |

### `requirements.txt`
```
fastapi==0.111.0
uvicorn==0.29.0
opencv-python==4.9.0.80
torch>=2.0.0
torchvision>=0.15.0
Pillow==10.3.0
SQLAlchemy==2.0.30
aiofiles==23.2.1
python-multipart==0.0.9
humanize==4.9.0
python-dotenv==1.0.1
pyinstaller==6.6.0
# SpeciesNet — install from Google's repo
# pip install git+https://github.com/google/cameratrapai.git
```

---

## 7. Model Files

Two models are needed. Both are downloaded on first run via `scripts/download_models.py`.

| Model | File | Size | Purpose |
|---|---|---|---|
| MegaDetector v5a | `md_v5a.0.0.pt` | ~165 MB | Detects animals + draws bounding boxes + counts individuals |
| SpeciesNet | downloaded via pip install | ~500 MB | Identifies species from animal crops |

### Download URLs
```
MegaDetector:
https://github.com/agentmorris/MegaDetector/releases/download/v5.0/md_v5a.0.0.pt

SpeciesNet:
pip install git+https://github.com/google/cameratrapai.git
```

---

## 8. Project Folder Structure

```
wildwatch/
│
├── app/                              # Tauri frontend shell
│   ├── src/
│   │   ├── index.html
│   │   ├── styles/
│   │   │   └── main.css
│   │   └── js/
│   │       ├── main.js               # App boot, screen router
│   │       ├── session.js            # New session form
│   │       ├── queue.js              # File queue display
│   │       ├── progress.js           # Live progress during detection
│   │       ├── results.js            # Results table + export button
│   │       └── api.js                # All fetch() calls to backend
│   ├── src-tauri/
│   │   ├── tauri.conf.json
│   │   ├── Cargo.toml
│   │   └── src/
│   │       └── main.rs               # Spawns Python backend on app start
│   └── package.json
│
├── backend/
│   ├── main.py                       # FastAPI app entry point
│   ├── config.py                     # Paths, constants
│   │
│   ├── services/
│   │   ├── ingest.py                 # Folder scan, file metadata extraction
│   │   ├── detector.py               # MegaDetector: animal detection + count
│   │   ├── species.py                # SpeciesNet: offline species identification
│   │   └── exporter.py               # Build and write CSV
│   │
│   ├── models/
│   │   ├── database.py               # SQLAlchemy engine + session factory
│   │   └── tables.py                 # ORM table definitions
│   │
│   ├── routers/
│   │   ├── sessions.py               # /sessions endpoints
│   │   ├── files.py                  # /files/ingest
│   │   ├── detection.py              # /detect SSE stream
│   │   └── export.py                 # /export/csv
│   │
│   └── utils/
│       └── frame_extractor.py        # OpenCV frame extraction helpers
│
├── models/                           # Gitignored — downloaded on first run
│   └── md_v5a.0.0.pt                 # MegaDetector weights (~165 MB)
│   # SpeciesNet weights stored in pip package cache
│
├── data/                             # Gitignored — runtime data
│   ├── wildwatch.db                  # SQLite database
│   ├── temp_frames/                  # Temp JPEG crops for species ID, cleared after each session
│   └── exports/                      # Generated CSVs
│
├── scripts/
│   └── download_models.py            # Downloads MegaDetector + installs SpeciesNet
│
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 9. Database Schema

```sql
CREATE TABLE sessions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    camera_id       TEXT NOT NULL,          -- e.g. "C1", "C11", "C15"
    result_format   TEXT NOT NULL DEFAULT 'Species/Empty',
    location        TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE files (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id              INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    filename                TEXT NOT NULL,
    filepath                TEXT NOT NULL,
    file_type               TEXT NOT NULL,      -- 'photo' or 'video'
    file_date               DATE,               -- from file system metadata
    file_size_bytes         INTEGER,
    duration_sec            REAL,               -- NULL for photos
    status                  TEXT DEFAULT 'pending',
    -- status: pending | detecting | identified | done | error

    -- Stage 1: MegaDetector results
    animal_detected         BOOLEAN,
    detection_confidence    REAL,               -- highest confidence across all frames
    max_count               INTEGER DEFAULT 0,  -- max individuals in any single frame

    -- Stage 2: SpeciesNet results
    species                 TEXT,               -- common name or "Unknown Animal"
    scientific_name         TEXT,
    species_confidence      REAL,
    species_source          TEXT,               -- speciesnet | unknown

    -- Pre-computed CSV values
    csv_result              TEXT,               -- exactly what goes in result column
    csv_count               INTEGER,            -- exactly what goes in count column

    error_message           TEXT,
    processed_at            DATETIME
);

CREATE INDEX idx_files_session ON files(session_id);
CREATE INDEX idx_files_status  ON files(status);
CREATE INDEX idx_files_result  ON files(csv_result);
```

---

## 10. Core Service Implementation

### 10.1 File Ingest (`backend/services/ingest.py`)

```python
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
```

---

### 10.2 MegaDetector Service (`backend/services/detector.py`)

Stage 1 of the pipeline. Runs offline. Detects animal presence, draws bounding boxes, counts individuals per frame.

```python
import torch
import cv2
from PIL import Image

CONFIDENCE_THRESHOLDS = {
    "low":    0.10,
    "medium": 0.50,
    "high":   0.80
}

class MegaDetectorService:

    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    def load(self):
        """Load model into memory. Call once at app startup."""
        if self.model is None:
            self.model = torch.hub.load(
                'ultralytics/yolov5', 'custom',
                path=self.model_path,
                force_reload=False,
                verbose=False
            )
            self.model.to(self.device)
            self.model.eval()

    def process_file(self, filepath: str, file_type: str, sensitivity: str = "medium") -> dict:
        """
        Returns:
        {
            "animal_detected": True,
            "confidence": 0.91,
            "max_count": 3,           # max individuals seen in any single frame
            "best_frame_path": "/tmp/xyz.jpg"  # saved crop for SpeciesNet
        }
        """
        threshold = CONFIDENCE_THRESHOLDS[sensitivity]
        if file_type == "photo":
            return self._process_photo(filepath, threshold)
        else:
            return self._process_video(filepath, threshold)

    def _process_photo(self, filepath: str, threshold: float) -> dict:
        try:
            image = Image.open(filepath).convert("RGB")
            result = self._run_detection(image, threshold)
            if result["animal_detected"]:
                result["best_frame_path"] = filepath  # use original for species ID
            return result
        except Exception as e:
            return {"animal_detected": False, "confidence": 0.0,
                    "max_count": 0, "best_frame_path": None, "error": str(e)}

    def _process_video(self, filepath: str, threshold: float,
                       fps_sample: float = 1.0) -> dict:
        """
        Sample video at fps_sample frames per second.
        Track highest confidence + max individual count across all frames.
        Save the best frame as a JPEG for SpeciesNet.
        """
        try:
            cap = cv2.VideoCapture(filepath)
            video_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
            frame_interval = max(1, int(video_fps / fps_sample))

            best_confidence = 0.0
            max_count = 0
            animal_detected = False
            best_frame_img = None
            frame_idx = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_idx % frame_interval == 0:
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_image = Image.fromarray(rgb)
                    result = self._run_detection(pil_image, threshold)

                    if result["animal_detected"]:
                        animal_detected = True
                        if result["confidence"] > best_confidence:
                            best_confidence = result["confidence"]
                            best_frame_img = pil_image  # save this frame for species ID
                        if result["max_count"] > max_count:
                            max_count = result["max_count"]

                    # Early exit — high-confidence detection found
                    if best_confidence >= 0.90:
                        break

                frame_idx += 1

            cap.release()

            # Save best frame as temp JPEG for SpeciesNet
            best_frame_path = None
            if best_frame_img is not None:
                import tempfile, os
                tmp = tempfile.NamedTemporaryFile(
                    delete=False, suffix=".jpg",
                    dir="data/temp_frames"
                )
                best_frame_img.save(tmp.name, "JPEG", quality=90)
                best_frame_path = tmp.name

            return {
                "animal_detected": animal_detected,
                "confidence": best_confidence,
                "max_count": max_count,
                "best_frame_path": best_frame_path
            }

        except Exception as e:
            return {"animal_detected": False, "confidence": 0.0,
                    "max_count": 0, "best_frame_path": None, "error": str(e)}

    def _run_detection(self, image: Image.Image, threshold: float) -> dict:
        """
        Run MegaDetector on a single PIL image.
        Count all animal bounding boxes — each box = one individual.
        """
        with torch.no_grad():
            results = self.model(image)

        detections = results.pandas().xyxyn[0]

        # Class 0 in MegaDetector = animal
        animals = detections[
            (detections["confidence"] >= threshold) &
            (detections["class"] == 0)
        ]

        if animals.empty:
            return {"animal_detected": False, "confidence": 0.0, "max_count": 0}

        return {
            "animal_detected": True,
            "confidence": round(float(animals["confidence"].max()), 4),
            "max_count": len(animals)   # number of boxes = number of individuals
        }
```

---

### 10.3 SpeciesNet Service (`backend/services/species.py`)

Stage 2 of the pipeline. Runs fully offline using Google's open-source SpeciesNet model. Only called when MegaDetector finds an animal.

```python
from speciesnet import SpeciesNet as _SpeciesNet
from pathlib import Path

SPECIES_CONFIDENCE_THRESHOLD = 0.60  # below this → "Unknown Animal"

class SpeciesNetService:

    def __init__(self):
        self.model = None

    def load(self):
        """Load SpeciesNet into memory. Call once at app startup."""
        if self.model is None:
            # Downloads weights on first call if not cached
            self.model = _SpeciesNet()

    def identify(self, frame_path: str) -> dict:
        """
        Run SpeciesNet on a single image frame.

        Args:
            frame_path: path to a JPEG frame saved by MegaDetector

        Returns:
        {
            "species": "Small Indian Civet",
            "scientific_name": "Viverricula indica",
            "confidence": 0.87,
            "source": "speciesnet"   # or "unknown"
        }
        """
        if not self.model:
            self.load()

        if not frame_path or not Path(frame_path).exists():
            return self._unknown("no_frame")

        try:
            # SpeciesNet accepts image path, returns predictions list
            predictions = self.model.predict(frame_path)

            if not predictions:
                return self._unknown("no_predictions")

            top = predictions[0]
            confidence = round(float(top.get("score", 0)), 3)

            if confidence < SPECIES_CONFIDENCE_THRESHOLD:
                return self._unknown("low_confidence")

            return {
                "species": top.get("common_name", "Unknown Animal"),
                "scientific_name": top.get("scientific_name", ""),
                "confidence": confidence,
                "source": "speciesnet"
            }

        except Exception as e:
            return self._unknown(f"error:{str(e)}")

    def _unknown(self, reason: str) -> dict:
        return {
            "species": "Unknown Animal",
            "scientific_name": "",
            "confidence": 0.0,
            "source": reason
        }
```

> **Note on SpeciesNet API**: The exact method names (`predict`, field names like `common_name`, `scientific_name`, `score`) should be verified against the latest `google/cameratrapai` repo README after install. The interface above matches the documented API as of May 2026 but confirm before wiring up.

---

### 10.4 CSV Exporter (`backend/services/exporter.py`)

```python
import csv
import os
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from backend.models.tables import File, SessionModel

RESULT_FORMAT_MAP = {
    "Species/Empty": {"empty_label": "Empty"},
    "Species/0":     {"empty_label": "0"},
    "Species/Blank": {"empty_label": ""},
}

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

    fmt = RESULT_FORMAT_MAP.get(session.result_format, RESULT_FORMAT_MAP["Species/Empty"])
    empty_label = fmt["empty_label"]

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
                result_value = empty_label if empty_label != "Empty" else "Empty"
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
```

---

### 10.5 Detection Router with SSE (`backend/routers/detection.py`)

Two-stage pipeline per file — both stages offline.

```python
import asyncio
import json
import datetime
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from backend.models.database import get_db
from backend.models.tables import File
from backend.services.detector import MegaDetectorService
from backend.services.species import SpeciesNetService
from backend.config import MODEL_PATH

router = APIRouter()
detector = MegaDetectorService(model_path=MODEL_PATH)
species_svc = SpeciesNetService()

@router.post("/detect/{session_id}")
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
                file.csv_result = file.species
                file.csv_count = file.max_count
                animal_count += 1

            else:
                file.csv_result = "Empty"
                file.csv_count = 0
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
                "confidence": file.detection_confidence
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
```

---

### 10.6 Model Downloader (`scripts/download_models.py`)

```python
import urllib.request
import subprocess
import sys
from pathlib import Path

MEGADETECTOR_URL = (
    "https://github.com/agentmorris/MegaDetector/releases/download/v5.0/md_v5a.0.0.pt"
)
MEGADETECTOR_PATH = Path(__file__).parent.parent / "models" / "md_v5a.0.0.pt"

def download_megadetector():
    MEGADETECTOR_PATH.parent.mkdir(parents=True, exist_ok=True)
    if MEGADETECTOR_PATH.exists():
        print(f"[MegaDetector] Already downloaded at {MEGADETECTOR_PATH}")
        return

    print("[MegaDetector] Downloading v5a (~165 MB)...")

    def progress(block, block_size, total):
        pct = min(100, block * block_size * 100 / total) if total > 0 else 0
        bar = "█" * int(pct // 2) + "░" * (50 - int(pct // 2))
        print(f"\r  [{bar}] {pct:.1f}%", end="", flush=True)

    urllib.request.urlretrieve(MEGADETECTOR_URL, MEGADETECTOR_PATH, progress)
    print(f"\n[MegaDetector] Saved to {MEGADETECTOR_PATH}")

def install_speciesnet():
    print("[SpeciesNet] Installing from Google's cameratrapai repo...")
    subprocess.check_call([
        sys.executable, "-m", "pip", "install",
        "git+https://github.com/google/cameratrapai.git",
        "--quiet"
    ])
    print("[SpeciesNet] Installed. Weights will download on first inference call.")

if __name__ == "__main__":
    download_megadetector()
    install_speciesnet()
    print("\nAll models ready. You can now run the app.")
```

---

### 10.7 Config (`backend/config.py`)

```python
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR     = Path(__file__).parent.parent
MODEL_PATH   = str(BASE_DIR / "models" / "md_v5a.0.0.pt")
DATABASE_URL = f"sqlite:///{BASE_DIR / 'data' / 'wildwatch.db'}"
EXPORT_DIR   = str(BASE_DIR / "data" / "exports")
TEMP_DIR     = str(BASE_DIR / "data" / "temp_frames")

BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8765

DEFAULT_SENSITIVITY   = "medium"
VIDEO_FPS_SAMPLE_RATE = 1.0     # frames per second sampled from video
EARLY_EXIT_CONFIDENCE = 0.90    # stop sampling if confidence reaches this

SUPPORTED_VIDEO = {".mp4", ".avi", ".mov", ".mkv"}
SUPPORTED_PHOTO = {".jpg", ".jpeg", ".png"}
```

---

## 11. Frontend UI Specification

### Screen 1 — New Session

| Field | Type | Required | Notes |
|---|---|---|---|
| Session name | Text input | Yes | e.g. "March Survey" |
| Camera ID | Text input | Yes | e.g. "C1", "C11", "C15" |
| Location notes | Text input | No | Free text |
| Result format | Dropdown | Yes | Default: Species/Empty |

### Screen 2 — File Queue
- Large drag-and-drop zone: "Drop SD card folder here" or "Browse folder"
- Once loaded: file count, photo count, video count, total size
- Sensitivity selector: Low / **Medium** (default) / High with one-line explanation
- **"Start Processing"** button — prominent

### Screen 3 — Live Progress
- Overall bar: `Processing 1,247 of 3,000 (41.6%)`
- Per-file stage label: `Detecting...` or `Identifying species...`
- Running tally: `Animals: 42 | Empty: 1,205 | Errors: 0`
- Cancel button (marks remaining as pending — resumable)

### Screen 4 — Results
- Summary cards: Total | Animals | Empty | Errors
- Table: `Filename | Type | Date | Species | Count | Confidence`
- Filter: All | Animals only | Empty only | Errors
- **"Export CSV"** button
- **"New session"** button

### Persistent Sidebar
- List of past sessions — click to reopen any session's results

---

## 12. API Endpoints

Base: `http://localhost:8765`

```
POST   /sessions                  Create session
GET    /sessions                  List all sessions
GET    /sessions/{id}             Get session + file stats
DELETE /sessions/{id}             Delete session and files

POST   /files/ingest              Scan folder, register files
                                  Body: { session_id, folder_path }
GET    /files/{session_id}        List files for a session

POST   /detect/{session_id}       Run full pipeline — SSE stream
                                  Events: progress | result | error | complete

GET    /export/csv/{session_id}   Generate + return CSV
```

---

## 13. Build & Distribution

### Development Setup
```bash
# Python backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
python scripts/download_models.py    # one-time setup, ~700 MB total

# Start backend
uvicorn backend.main:app --host 127.0.0.1 --port 8765 --reload

# Tauri frontend (separate terminal)
cd app && npm install && npm run tauri dev
```

### Production Build
```bash
# Bundle Python into standalone exe
pyinstaller backend/main.py \
  --name wildwatch_backend \
  --onefile \
  --add-data "models:models" \
  --hidden-import=torch \
  --hidden-import=torchvision \
  --hidden-import=speciesnet

# Build Tauri installer
cd app && npm run tauri build
# Output: app/src-tauri/target/release/bundle/nsis/WildWatch_1.0.0_x64-setup.exe
```

### Installer Size
| Component | Size |
|---|---|
| Python + FastAPI | ~80 MB |
| PyTorch CPU | ~750 MB |
| OpenCV | ~60 MB |
| MegaDetector model | ~165 MB |
| SpeciesNet model | ~500 MB |
| Tauri shell | ~10 MB |
| **Total** | **~1.6 GB** |

> Distribute via USB or shared drive with the full installer. Models can alternatively be downloaded on first run to keep the installer itself smaller.

### System Requirements
| | Minimum | Recommended |
|---|---|---|
| OS | Windows 10 64-bit | Windows 11 |
| RAM | 8 GB | 16 GB |
| Storage | 5 GB free | 15 GB free |
| GPU | Not required | NVIDIA (10–20× faster) |
| Internet | **Not required** | Not required |

---

## 14. Performance on 3,000 Files

| File type | CPU time per file | 3,000 files estimate |
|---|---|---|
| Photo | 1–2 sec (detect + identify) | 50–100 min |
| Video (30s clip, 1fps) | 8–15 sec | varies |
| Either with NVIDIA GPU | 10–20× faster | 5–10 min |

- Files committed to SQLite in batches of 500 — prevents memory pressure
- Videos exit early if confidence ≥ 0.90 (saves significant time on clear sightings)
- Both models loaded into memory once at startup — no repeated load cost per file
- SSE stream keeps UI live throughout — progress always visible

---

## 15. Error Handling

| Scenario | Behaviour |
|---|---|
| Corrupt or unreadable file | Mark `error`, log message, continue batch |
| MegaDetector model missing | Show "Download models" screen before anything else |
| SpeciesNet not installed | Show "Setup required" screen, run installer script |
| No supported files found | Show message with list of supported formats |
| User cancels mid-run | Mark remaining as `pending` — resumable on next open |
| All files already processed | Jump to results screen directly, no reprocessing |
| SQLite write error | Toast error, stop, preserve everything already saved |
| SpeciesNet low confidence | Write `Unknown Animal` — never blank, batch continues |
| Temp frame cleanup | Delete all files in `data/temp_frames/` after export |

---

## 16. What Comes After v1

Do not build these now.

| Version | Feature |
|---|---|
| v1.1 | Confirm result format with client, hardcode, remove the dropdown |
| v1.2 | Thumbnail of best animal frame shown in results table |
| v2.0 | Activity heatmap — hour-of-day sighting chart per session |
| v2.1 | Annotated video export — bounding box + label burned into clip |
| v3.0 | Cross-session comparison across camera IDs |

---

## 17. Handoff Checklist

Before calling this done, verify every item:

- [ ] Installs on a fresh Windows 10 machine with no Python
- [ ] First run prompts model download and completes successfully
- [ ] Drag-and-drop folder of 10 test files (mix of photos + videos)
- [ ] Detection completes without crashing
- [ ] Species name appears correctly for animal files
- [ ] `Unknown Animal` appears when confidence is low — not blank, not `Empty`
- [ ] Count column shows correct individual count (test with a photo of multiple animals)
- [ ] CSV columns are exactly: `camera_id`, `result`, `count`, `date`
- [ ] Empty files appear in CSV with result = `Empty` and count = `0`
- [ ] Past sessions visible in sidebar after app restart
- [ ] Entire pipeline works with Wi-Fi turned off
- [ ] Corrupt file is handled gracefully, batch continues
- [ ] Temp frames folder is cleaned up after export

---

## 18. .gitignore

```
venv/
__pycache__/
*.pyc
dist/
build/
*.spec
models/
data/
app/src-tauri/target/
.env
```

## 19. .env.example

```
# No secrets required — entire pipeline is offline
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8765
```

---

*WildWatch v1 — Agent Handoff Document*
*Version: 3.0 — SpeciesNet replaces Wildlife Insights API, fully offline pipeline*
*Date: May 2026 | Status: Ready to build — start at Section 10*
