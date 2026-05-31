from speciesnet import SpeciesNet as _SpeciesNet
from speciesnet import DEFAULT_MODEL
from backend.config import MODEL_PATH
import os
import json
import base64
import google.generativeai as genai
from dotenv import load_dotenv
from pathlib import Path

import sys

if getattr(sys, 'frozen', False):
    env_path = Path(sys._MEIPASS) / ".env"
else:
    env_path = Path(".env")

load_dotenv(dotenv_path=env_path)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

SPECIES_CONFIDENCE_THRESHOLD = 0.60  # below this → call Gemini fallback

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
            # SpeciesNet requires ISO-3166 alpha-3 codes.
            predictions_dict = self.model.predict(filepaths=[frame_path], country="IND")

            if not predictions_dict or "predictions" not in predictions_dict:
                return self._unknown("no_predictions")

            preds = predictions_dict["predictions"]
            if not preds:
                return self._unknown("empty_predictions")
                
            top = preds[0]
            confidence = round(float(top.get("prediction_score", 0)), 3)
            pred_string = top.get("prediction", "")
            parts = pred_string.split(";")
            
            common_name = "Unknown Animal"
            scientific_name = ""
            if len(parts) >= 7:
                common_name = parts[-1].title()
                scientific_name = f"{parts[-3].capitalize()} {parts[-2].lower()}"

            generic_terms = {"Animal", "Mammal", "Bird", "Reptile", "Unknown Animal", "Blank"}
            needs_review = (common_name in generic_terms)

            if confidence < SPECIES_CONFIDENCE_THRESHOLD or needs_review:
                gemini_result = self._call_gemini_fallback(frame_path)
                if gemini_result:
                    return gemini_result
                    
                # If Gemini fails, default to SpeciesNet's animal prediction
                source = "speciesnet"
            else:
                source = "speciesnet"
                
                common_name = "Unknown Animal"
                scientific_name = ""
                if len(parts) >= 7:
                    common_name = parts[-1].title()
                    scientific_name = f"{parts[-3].capitalize()} {parts[-2].lower()}"

                generic_terms = {"Animal", "Mammal", "Bird", "Reptile", "Unknown Animal", "Blank"}
                needs_review = (common_name in generic_terms)

            return {
                "species": common_name,
                "scientific_name": scientific_name,
                "confidence": confidence,
                "needs_review": needs_review,
                "source": "speciesnet"
            }

        except Exception as e:
            return self._unknown(f"error:{str(e)}")

    def _call_gemini_fallback(self, filepath: str):
        if not GEMINI_API_KEY:
            return None
        
        try:
            model = genai.GenerativeModel("gemini-2.5-flash")
            
            with open(filepath, "rb") as f:
                image_data = f.read()
                
            prompt = (
                "This is a camera trap image from a forest in India. Look at the animal "
                "in this image carefully. Identify the exact species using its common name "
                "as used in India (for example: Nilgai, Blackbuck, Three-striped Palm "
                "Squirrel, Indian Leopard). Respond in this exact JSON format only, no "
                "other text:\n"
                "{\n"
                "  'species': 'common name here',\n"
                "  'scientific_name': 'scientific name here',\n"
                "  'confidence': 0.0 to 1.0,\n"
                "  'reasoning': 'one sentence explaining key identifying features'\n"
                "}"
            )
            
            response = model.generate_content([
                {"mime_type": "image/jpeg", "data": image_data},
                prompt
            ])
            
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
                
            # Replace single quotes with double quotes for valid JSON
            text = text.replace("'", '"')
                
            data = json.loads(text.strip())
            conf = float(data.get("confidence", 0.0))
            
            if conf >= 0.5:
                return {
                    "species": data.get("species", "Animal"),
                    "scientific_name": data.get("scientific_name", ""),
                    "confidence": conf,
                    "needs_review": False,
                    "source": "gemini"
                }
            else:
                return None
                
        except Exception as e:
            print(f"Gemini fallback error: {e}")
            return None

        except Exception as e:
            return self._unknown(f"error:{str(e)}")

    def _unknown(self, reason: str) -> dict:
        return {
            "species": "Unknown Animal",
            "scientific_name": "",
            "confidence": 0.0,
            "needs_review": True,
            "source": reason
        }
