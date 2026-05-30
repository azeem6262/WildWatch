import torch
import cv2
from PIL import Image
from pathlib import Path

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
        threshold = CONFIDENCE_THRESHOLDS.get(sensitivity, 0.50)
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
                from backend.config import TEMP_DIR
                Path(TEMP_DIR).mkdir(parents=True, exist_ok=True)
                tmp = tempfile.NamedTemporaryFile(
                    delete=False, suffix=".jpg",
                    dir=TEMP_DIR
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
