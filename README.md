# 🐾 WildWatch

WildWatch is a fully offline, local Windows desktop application designed for wildlife conservation field teams. It processes thousands of camera trap photos and videos, automatically detecting animals and identifying species using state-of-the-art AI models, without requiring any internet connection.

## 🌟 Key Features

*   **Fully Offline AI Pipeline:** No API keys, no internet dependency, no cloud computing costs.
*   **MegaDetector v5a Integration:** Detects animal presence, draws bounding boxes, and counts individuals per frame.
*   **SpeciesNet Integration:** Powered by the same open-source model behind Wildlife Insights (trained on 65M images, 94.5% accuracy), it identifies over 2,400 species including Indian forest mammals.
*   **Timelapse+ Compatibility:** Automatically exports a CSV structured exactly for Timelapse+ integration (`camera_id`, `result`, `count`, `date`).
*   **High Performance:** Processes large folders of up to 3,000 files efficiently. Videos are sampled for optimal speed, and early exits are utilized for high-confidence detections.

## 🛠️ Tech Stack

*   **Frontend / Desktop Shell:** Tauri v2, HTML, Vanilla JS, CSS
*   **Backend API:** Python 3.11, FastAPI, Uvicorn
*   **Machine Learning:** PyTorch, MegaDetector v5a, Google SpeciesNet
*   **Database:** SQLite via SQLAlchemy
*   **Packaging:** PyInstaller (Backend), Tauri (Frontend)

## 🚀 Getting Started (Development Setup)

### Prerequisites

*   Windows 10/11 (64-bit)
*   Node.js & npm (for Tauri)
*   Rust (for Tauri)
*   Python 3.11

### 1. Backend Setup

```bash
# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate

# Install requirements
pip install -r requirements.txt

# Download AI Models (MegaDetector & SpeciesNet)
python scripts/download_models.py

# Run the FastAPI server locally
uvicorn backend.main:app --host 127.0.0.1 --port 8765 --reload
```

### 2. Frontend Setup

In a new terminal window:

```bash
cd app
npm install
npm run tauri dev
```

## 📦 Building for Production

To build a standalone Windows installer `.exe` that bundles the Python backend and the Tauri frontend:

1. Bundle the Python backend using PyInstaller:
```bash
pyinstaller backend/main.py --name wildwatch_backend --onefile --add-data "models:models" --hidden-import=torch --hidden-import=torchvision --hidden-import=speciesnet
```

2. Build the Tauri installer:
```bash
cd app
npm run tauri build
```
*(The final `.exe` will be located in `app/src-tauri/target/release/bundle/nsis/`)*

## 📂 Data & Privacy

WildWatch is designed to operate completely offline to protect sensitive wildlife location data and ensure reliability in remote field conditions. All photos, videos, and generated databases stay strictly on your local machine.

---
*Built for Wildlife Conservation.*
