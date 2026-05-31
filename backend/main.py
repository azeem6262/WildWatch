from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.models.database import engine, run_migrations
from backend.models import tables

from backend.routers import sessions, files, detection, export

# Run database migrations
run_migrations(engine)

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

if __name__ == "__main__":
    import uvicorn
    import multiprocessing
    multiprocessing.freeze_support()
    uvicorn.run(app, host="127.0.0.1", port=8765)
