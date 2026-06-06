from speciesnet import SpeciesNet as _SpeciesNet
from speciesnet import DEFAULT_MODEL
from backend.config import MODEL_PATH
import os
import json
import base64
from transformers import CLIPProcessor, CLIPModel
import torch
from PIL import Image
from pathlib import Path

import sys

SPECIES_CONFIDENCE_THRESHOLD = 0.60  # below this → call Gemini fallback

class SpeciesNetService:

    def __init__(self):
        self.model = None
        self.clip_model = None
        self.clip_processor = None
        
        self.indian_species = [
            "a photo of a Nilgai (blue bull)",
            "a photo of a Chital (spotted deer)",
            "a photo of a Sambar Deer",
            "a photo of an Indian Leopard",
            "a photo of a Bengal Tiger",
            "a photo of a Wild Boar",
            "a photo of a Sloth Bear",
            "a photo of an Indian Peafowl",
            "a photo of a Blackbuck",
            "a photo of an Indian Elephant",
            "a photo of a Gaur (Indian Bison)",
            "a photo of a Dhole (Asiatic wild dog)",
            "a photo of a Gray Langur",
            "a photo of a Macaque",
            "a photo of a Mongoose",
            "a photo of a Porcupine",
            "a photo of a Hyena",
            "a photo of a Jackal",
            "a photo of a Fox",
            "a photo of a Civet",
            "a photo of a Hare",
            "a photo of a Pangolin",
            "a photo of a Monitor Lizard",
            "a photo of an empty forest with no animals",
            "a photo of a human or person"
        ]

    def load(self):
        """Load SpeciesNet into memory. Call once at app startup."""
        if self.model is None:
            # Downloads weights on first call if not cached
            self.model = _SpeciesNet(DEFAULT_MODEL)
            
        if self.clip_model is None:
            try:
                print("Loading offline CLIP fallback model...")
                if getattr(sys, 'frozen', False):
                    # PyInstaller path
                    clip_dir = Path(sys._MEIPASS) / "models" / "clip-vit-base-patch32"
                else:
                    # Dev path
                    clip_dir = Path("models") / "clip-vit-base-patch32"
                    
                if not clip_dir.exists():
                    print(f"Warning: Offline CLIP weights not found at {clip_dir}. Please run download_models.py.")
                else:
                    self.clip_model = CLIPModel.from_pretrained(str(clip_dir))
                    self.clip_processor = CLIPProcessor.from_pretrained(str(clip_dir))
            except Exception as e:
                print(f"Failed to load CLIP fallback model: {e}")

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
            print(f"Running SpeciesNet predict on {frame_path}")
            # SpeciesNet requires ISO-3166 alpha-3 codes.
            predictions_dict = self.model.predict(filepaths=[frame_path], country="IND")
            print(f"SpeciesNet predict finished for {frame_path}")

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

            generic_terms = {"Animal", "Mammal", "Bird", "Reptile", "Unknown Animal", "Blank", "Canine", "Feline", "Bovid", "Cervid"}
            needs_review = (
                common_name in generic_terms or 
                "Family" in common_name or 
                "Order" in common_name
            )

            if confidence < SPECIES_CONFIDENCE_THRESHOLD or needs_review:
                clip_result = self._call_clip_fallback(frame_path)
                if clip_result:
                    return clip_result
                    
                # If Gemini fails, default to SpeciesNet's animal prediction
                source = "speciesnet"
            else:
                source = "speciesnet"
                
                common_name = "Unknown Animal"
                scientific_name = ""
                if len(parts) >= 7:
                    common_name = parts[-1].title()
                    scientific_name = f"{parts[-3].capitalize()} {parts[-2].lower()}"

                generic_terms = {"Animal", "Mammal", "Bird", "Reptile", "Unknown Animal", "Blank", "Canine", "Feline", "Bovid", "Cervid"}
                needs_review = (
                    common_name in generic_terms or 
                    "Family" in common_name or 
                    "Order" in common_name
                )

            return {
                "species": common_name,
                "scientific_name": scientific_name,
                "confidence": confidence,
                "needs_review": needs_review,
                "source": "speciesnet"
            }

        except Exception as e:
            return self._unknown(f"error:{str(e)}")

    def _call_clip_fallback(self, filepath: str):
        if not self.clip_model or not self.clip_processor:
            return None
            
        try:
            print(f"Calling CLIP offline fallback for {filepath}")
            image = Image.open(filepath)
            
            inputs = self.clip_processor(
                text=self.indian_species, 
                images=image, 
                return_tensors="pt", 
                padding=True
            )
            
            with torch.no_grad():
                outputs = self.clip_model(**inputs)
                
            logits_per_image = outputs.logits_per_image
            probs = logits_per_image.softmax(dim=1)
            
            top_prob, top_idx = probs[0].max(dim=0)
            best_match_text = self.indian_species[top_idx.item()]
            confidence = top_prob.item()
            
            # If the best match is empty forest or human, return unknown or those specifically
            if "empty forest" in best_match_text.lower():
                return {
                    "species": "Blank",
                    "scientific_name": "",
                    "confidence": confidence,
                    "needs_review": False,
                    "source": "clip"
                }
            elif "human" in best_match_text.lower():
                return {
                    "species": "Human",
                    "scientific_name": "Homo sapiens",
                    "confidence": confidence,
                    "needs_review": False,
                    "source": "clip"
                }
                
            # Parse species name from "a photo of a [Species] ([Optional])"
            # Remove "a photo of a " or "a photo of an "
            species_part = best_match_text.replace("a photo of a ", "").replace("a photo of an ", "")
            
            # If there's a parenthesis (e.g. "Nilgai (blue bull)"), extract just the main part
            if "(" in species_part:
                species = species_part.split("(")[0].strip()
            else:
                species = species_part.strip()
                
            if confidence >= 0.2: # CLIP confidence threshold can be lower because it's softmax over N classes
                return {
                    "species": species,
                    "scientific_name": "",
                    "confidence": round(confidence, 3),
                    "needs_review": False,
                    "source": "clip"
                }
            else:
                return None
                
        except Exception as e:
            print(f"CLIP fallback error: {e}")
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
