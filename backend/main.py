from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.models.database import engine, run_migrations
from backend.models import tables
import os
from pathlib import Path
from dotenv import load_dotenv

# Load user config first before anything else initializes
config_file = Path.home() / ".wildwatch" / "config.env"
if config_file.exists():
    load_dotenv(dotenv_path=config_file)

from backend.routers import sessions, files, detection, export, settings
from backend.utils.backfill import run_datetime_backfill_background, is_backfill_running
import backend.utils.backfill as backfill_module

# Run database migrations
run_migrations(engine)

# Start backfill background task
run_datetime_backfill_background()

app = FastAPI(title="WildWatch Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions.router)
app.include_router(files.router)
app.include_router(detection.router)
app.include_router(export.router)
app.include_router(settings.router)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "WildWatch API is running"}

@app.get("/system/status")
def system_status():
    return {"is_backfill_running": backfill_module.is_backfill_running}

if __name__ == "__main__":
    import uvicorn
    import multiprocessing
    multiprocessing.freeze_support()
    uvicorn.run(app, host="127.0.0.1", port=8765)
