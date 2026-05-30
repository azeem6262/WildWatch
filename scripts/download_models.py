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

    def progress(count, block_size, total_size):
        pct = count * block_size * 100 / total_size
        if pct > 100: pct = 100
        filled = int(pct / 2)
        bar = '#' * filled + '-' * (50 - filled)
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
