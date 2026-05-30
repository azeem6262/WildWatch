from speciesnet import SpeciesNet as _SpeciesNet
from speciesnet import DEFAULT_MODEL
from pathlib import Path

SPECIES_CONFIDENCE_THRESHOLD = 0.60  # below this → "Unknown Animal"

class SpeciesNetService:

    def __init__(self):
        self.model = None

    def load(self):
        """Load SpeciesNet into memory. Call once at app startup."""
        if self.model is None:
            # Downloads weights on first call if not cached
            self.model = _SpeciesNet(DEFAULT_MODEL)

    def identify(self, frame_path: str) -> dict:
        """
        Run SpeciesNet on a single image frame.

        Args:
            frame_path: path to a JPEG frame saved by MegaDetector

        Returns:
        {
            "species": "Small Indian Civet",
            "scientific_name": "Viverricula indica",
            "confidence": 0.87,
            "source": "speciesnet"   # or "unknown"
        }
        """
        if not self.model:
            self.load()

        if not frame_path or not Path(frame_path).exists():
            return self._unknown("no_frame")

        try:
            # SpeciesNet accepts image path, returns predictions list
            predictions = self.model.predict(frame_path)

            if not predictions:
                return self._unknown("no_predictions")

            top = predictions[0]
            confidence = round(float(top.get("score", 0)), 3)

            if confidence < SPECIES_CONFIDENCE_THRESHOLD:
                return self._unknown("low_confidence")

            return {
                "species": top.get("common_name", "Unknown Animal"),
                "scientific_name": top.get("scientific_name", ""),
                "confidence": confidence,
                "source": "speciesnet"
            }

        except Exception as e:
            return self._unknown(f"error:{str(e)}")

    def _unknown(self, reason: str) -> dict:
        return {
            "species": "Unknown Animal",
            "scientific_name": "",
            "confidence": 0.0,
            "source": reason
        }
