# services/detection.py
import tempfile
import numpy as np
from ultralytics import YOLO
import config
import os


def load_model():
    """
    Loads the YOLO detection model.
    """
    try:
        abs_path = os.path.abspath(config.YOLO_MODEL_PATH)
        print(f"📦 Loading YOLO model from: {abs_path}")
        assert os.path.isfile(abs_path), "Model file does not exist at resolved path"
        model = YOLO(config.YOLO_MODEL_PATH).to(config.DEVICE)
        return model
    except Exception as e:
        raise RuntimeError("Failed to load YOLO detection model") from e


def detect_potholes(model, image):
    """
    Runs pothole detection on the given image.

    Returns:
        annotated_img: Image annotated with detection boxes (in BGR format)
        pothole_areas: List of pothole bounding box areas (in pixels)
        avg_area: Average area of detected potholes (or 0 if none)
        severity: Severity level ("Low", "Medium", "High")
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        image.save(tmp.name)
        image_path = tmp.name
        results = model(image_path)

    result = results[0]
    boxes = result.boxes
    annotated_img = result.plot()
    pothole_areas = []

    for box in boxes:
        xyxy = box.xyxy[0].cpu().numpy()
        width = xyxy[2] - xyxy[0]
        height = xyxy[3] - xyxy[1]
        area = width * height
        pothole_areas.append(area)

    # Determine severity based on average pothole area.
    severity = "Low"
    if pothole_areas:
        avg_area = np.mean(pothole_areas)
        if avg_area > 50000:
            severity = "High"
        elif avg_area > 20000:
            severity = "Medium"
    else:
        avg_area = 0

    return annotated_img, pothole_areas, avg_area, severity
