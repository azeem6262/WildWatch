import os
import json
import shutil
import subprocess
from datetime import datetime
from PIL import Image

def _to_local_datetime(value: datetime) -> datetime:
    if value.tzinfo is not None:
        return value.astimezone().replace(tzinfo=None)
    return value


def _parse_ffprobe_creation_time(filepath: str) -> datetime | None:
    ffprobe_path = shutil.which("ffprobe")
    if not ffprobe_path:
        return None

    result = subprocess.run(
        [
            ffprobe_path, "-v", "quiet", "-print_format", "json",
            "-show_format", str(filepath)
        ],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        return None

    data = json.loads(result.stdout)
    creation_time = data.get("format", {}).get("tags", {}).get("creation_time")
    if not creation_time:
        return None

    try:
        # Example: 2026-05-02T21:05:30.000000Z
        cleaned = creation_time.strip()
        if cleaned.endswith("Z"):
            cleaned = cleaned[:-1] + "+00:00"
        dt = datetime.fromisoformat(cleaned)
        return _to_local_datetime(dt)
    except ValueError:
        try:
            cleaned = creation_time.split(".")[0].replace("Z", "")
            return datetime.strptime(cleaned, "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            return None


def _parse_hachoir_creation_time(filepath: str) -> datetime | None:
    try:
        from hachoir.parser import createParser
        from hachoir.metadata import extractMetadata
    except Exception:
        return None

    parser = createParser(str(filepath))
    if not parser:
        return None
    try:
        metadata = extractMetadata(parser)
        if not metadata:
            return None

        creation_date = (
            metadata.get("creation_date") or
            metadata.get("creation_time") or
            metadata.get("date_time_original")
        )
        if isinstance(creation_date, datetime):
            return _to_local_datetime(creation_date)
    finally:
        parser.close()

    return None


def _extract_timestamp_with_gemini(filepath: str, file_type: str) -> datetime | None:
    import os
    import google.generativeai as genai
    import json
    import time
    from PIL import Image
    import cv2
    import io

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None

    try:
        genai.configure(api_key=api_key)
        if file_type == "video":
            cap = cv2.VideoCapture(str(filepath))
            ret, frame = cap.read()
            cap.release()
            if not ret:
                return None
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb)
        else:
            pil_image = Image.open(str(filepath)).convert("RGB")

        # Resize to save bandwidth
        pil_image.thumbnail((1280, 1280))
        img_byte_arr = io.BytesIO()
        pil_image.save(img_byte_arr, format='JPEG', quality=85)
        image_data = img_byte_arr.getvalue()

        model = genai.GenerativeModel("gemini-2.5-flash")
        
        prompt = (
            "Extract the date and time stamped on this image (usually at the bottom). "
            "Ignore any camera labels or temperature readings. "
            "Respond ONLY with a JSON object in exactly this format: "
            "{\"datetime\": \"YYYY:MM:DD HH:MM:SS\"} "
            "If no timestamp is visible on the image, respond with {\"datetime\": null}."
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
        text = text.replace("'", '"')
        
        data = json.loads(text.strip())
        dt_str = data.get("datetime")
        
        # 15 RPM limit -> sleep
        time.sleep(4.5)
        
        if dt_str:
            try:
                dt_str = dt_str.replace("-", ":")
                return datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")
            except ValueError:
                return None
    except Exception as e:
        print(f"Gemini timestamp extraction error: {e}")
        return None
    return None


def extract_datetime_and_relative_path(filepath: str, file_type: str) -> tuple[datetime | None, str]:
    """
    Extracts the full datetime and relative path (parent folder name) from a file.
    Returns: (datetime_full, relative_path)
    """
    path_obj = type(filepath) == str and __import__("pathlib").Path(filepath) or filepath
    relative_path = path_obj.parent.name
    datetime_full = None

    if file_type == "photo":
        try:
            with Image.open(str(filepath)) as img:
                exif = img.getexif()
                if exif:
                    # Check common EXIF datetime tags
                    # 36867 = DateTimeOriginal, 36868 = DateTimeDigitized, 306 = DateTime
                    dt_str = exif.get(36867) or exif.get(36868) or exif.get(306)
                    if dt_str:
                        # Format is usually "YYYY:MM:DD HH:MM:SS"
                        try:
                            datetime_full = datetime.strptime(dt_str.strip(), "%Y:%m:%d %H:%M:%S")
                        except ValueError:
                            pass
        except Exception:
            pass

    elif file_type == "video":
        # Always try Gemini first for videos since camera trap video metadata is notoriously wrong/missing,
        # and usually just reflects the time the file was copied to the computer.
        datetime_full = _extract_timestamp_with_gemini(filepath, file_type)

        if datetime_full is None:
            try:
                datetime_full = _parse_ffprobe_creation_time(filepath)
            except Exception:
                datetime_full = None

        if datetime_full is None:
            try:
                datetime_full = _parse_hachoir_creation_time(filepath)
            except Exception:
                datetime_full = None

    # Fallback to mtime if all else fails
    if datetime_full is None:
        try:
            mtime = os.path.getmtime(str(filepath))
            datetime_full = datetime.fromtimestamp(mtime)
        except Exception:
            pass
            
    return datetime_full, relative_path
