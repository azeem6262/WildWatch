from fastapi import APIRouter
from pydantic import BaseModel
import os
import dotenv

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
            
    # 2. Persist to .env file
    env_file = ".env"
    if not os.path.exists(env_file):
        # Create it if it doesn't exist
        with open(env_file, "w") as f:
            pass
            
    if key:
        dotenv.set_key(env_file, "GEMINI_API_KEY", key)
    else:
        dotenv.unset_key(env_file, "GEMINI_API_KEY")
        
    return {"status": "success", "message": "Gemini API key saved."}
