from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.models.database import engine
from backend.models import tables

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

@app.get("/")
def read_root():
    return {"status": "ok", "message": "WildWatch API is running"}
