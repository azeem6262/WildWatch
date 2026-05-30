from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.models.database import engine
from backend.models import tables

from backend.routers import sessions, files, detection, export

# Create tables
tables.Base.metadata.create_all(bind=engine)

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

@app.get("/")
def read_root():
    return {"status": "ok", "message": "WildWatch API is running"}
