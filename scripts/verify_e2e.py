import os
import time
import requests
import json
import sqlite3
import cv2
import numpy as np
from pathlib import Path

BASE_URL = "http://127.0.0.1:8765"
DB_PATH = "wildwatch.db"
TEST_DIR = "test_sd_card"

def create_test_images():
    print("Creating test images...")
    os.makedirs(TEST_DIR, exist_ok=True)
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    # Add a white box in the middle to simulate an object so MegaDetector doesn't crash on completely black images.
    cv2.rectangle(img, (200, 150), (440, 330), (255, 255, 255), -1)
    cv2.imwrite(os.path.join(TEST_DIR, "IMG_0001.JPG"), img)
    cv2.imwrite(os.path.join(TEST_DIR, "IMG_0002.JPG"), img)
    print(f"Created 2 images in {TEST_DIR}/")

def test_api():
    print("1. Testing Session Creation...")
    res = requests.post(f"{BASE_URL}/sessions/", json={
        "name": "E2E Test Session",
        "camera_id": "TEST-CAM-1",
        "location": "Virtual Test Area"
    })
    res.raise_for_status()
    session_id = res.json()["id"]
    print(f"Created Session ID: {session_id}")

    print("2. Testing File Ingestion...")
    # Use absolute path
    folder_path = os.path.abspath(TEST_DIR)
    res = requests.post(f"{BASE_URL}/files/ingest", json={
        "session_id": session_id,
        "folder_path": folder_path
    })
    res.raise_for_status()
    print("Ingestion Stats:", res.json())

    print("3. Testing SSE Detection Stream...")
    # Using raw streaming response
    response = requests.post(f"{BASE_URL}/detect/{session_id}", stream=True)
    response.raise_for_status()
    for line in response.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            if decoded_line.startswith('data: '):
                data = json.loads(decoded_line[6:])
                if data["type"] == "progress":
                    print(f"Progress: {data['percent']}% - {data['stage']}")
                elif data["type"] == "result":
                    print(f"Result for {data['filename']}: {data['result']} (Count: {data['count']}, Confidence: {data['confidence']})")
                elif data["type"] == "complete":
                    print("Detection Complete! Summary:", data["summary"])
                elif data["type"] == "error":
                    print(f"Error on {data['filename']}: {data['message']}")

    print("4. Testing CSV Export...")
    res = requests.get(f"{BASE_URL}/export/csv/{session_id}")
    res.raise_for_status()
    print("CSV Content:")
    print(res.text)

if __name__ == "__main__":
    create_test_images()
    test_api()
