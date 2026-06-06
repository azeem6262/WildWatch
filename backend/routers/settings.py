from fastapi import APIRouter
from pydantic import BaseModel
import os
import dotenv
from pathlib import Path

router = APIRouter(prefix="/settings", tags=["settings"])

class GeminiKeyModel(BaseModel):
    api_key: str

@router.get("/gemini")
def get_gemini_key():
    # Only return whether the key is set, and partially mask it for safety,
    # or just return the full key since it's a local desktop app.
    # Returning the key so the frontend can populate the input field if they want to edit it.
    key = os.environ.get("GEMINI_API_KEY", "")
    return {"api_key": key, "is_set": bool(key)}

@router.post("/gemini")
def set_gemini_key(payload: GeminiKeyModel):
    key = payload.api_key.strip()
    
    # 1. Update the running process environment so metadata.py picks it up immediately
    if key:
        os.environ["GEMINI_API_KEY"] = key
    else:
        # If they send an empty string, maybe they want to clear it?
        if "GEMINI_API_KEY" in os.environ:
            del os.environ["GEMINI_API_KEY"]
            
    # 2. Persist to ~/.wildwatch/config.env
    config_dir = Path.home() / ".wildwatch"
    config_dir.mkdir(parents=True, exist_ok=True)
    env_file = config_dir / "config.env"
    
    if not env_file.exists():
        # Create it if it doesn't exist
        with open(env_file, "w") as f:
            pass
            
    if key:
        dotenv.set_key(str(env_file), "GEMINI_API_KEY", key)
    else:
        dotenv.unset_key(str(env_file), "GEMINI_API_KEY")
        
    return {"status": "success", "message": "Gemini API key saved."}
