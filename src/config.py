import os
import torch

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# === API URLs & Parameters ===
NOMINATIM_SEARCH_URL = "https://nominatim.openstreetmap.org/search"
NOMINATIM_REVERSE_URL = "https://nominatim.openstreetmap.org/reverse"
NOMINATIM_USER_AGENT = "pothole-ai"
NOMINATIM_SEARCH_LIMIT = 1

OVERPASS_API_URL = "https://overpass-api.de/api/interpreter"

# === Model Configuration ===
YOLO_MODEL_PATH = os.path.join(BASE_DIR, "../models/Baseline_YOLOv8Small_Filtered.pt")

BLIP_MODEL_NAME = "Salesforce/blip-image-captioning-base"
LLAMA_MODEL_DEFAULT = "llama3.2:3b"
LLAMA_VISION_MODEL = "llama3.2-vision"

# === Radii & Thresholds ===
AMENITY_RADIUS = 500  # Radius for querying amenities (meters)
FACILITY_THRESHOLD_M = 200  # Critical distance in meters for facility risk
TRAFFIC_RADIUS = 300  # Radius for querying traffic data (meters)

# === Severity Colors ===
SEVERITY_COLORS = {
    "Low": "#5cb85c",
    "Medium": "#f0ad4e",
    "High": "#d9534f",
}

# === Folium Map Settings ===
FOLIUM_TILE_TYPE = "CartoDB positron"
FOLIUM_DEFAULT_ZOOM_START = 16
FOLIUM_MAP_WIDTH = 700
FOLIUM_MAP_HEIGHT = 450

# === Folium Marker & Circle Defaults ===
POTHOLE_MARKER_COLOR = "red"
POTHOLE_MARKER_ICON = "exclamation-triangle"

FACILITY_MARKER_COLOR = "green"
FACILITY_MARKER_ICON = "plus-sign"

RADIUS_CIRCLE_COLOR = "blue"
RADIUS_CIRCLE_FILL_OPACITY = 0.08

# === GPU Configuration ===
USE_GPU = True

DEVICE = (
    "cuda"
    if torch.cuda.is_available()
    else "mps" if torch.backends.mps.is_available() else "cpu"
)
