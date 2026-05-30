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
