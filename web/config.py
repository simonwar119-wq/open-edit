"""Open Edit - Web Demo Configuration"""
import os

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
TAXONOMY_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "taxonomy", "03-styles"))

# Limits
MAX_UPLOAD_SIZE_MB = 30
MAX_DURATION_SECONDS = 60
ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi", ".webm", ".mkv"}

# Analysis
FRAME_INTERVAL = 5  # seconds between frames
SAMPLE_FRAMES = 12  # max frames to analyze

# Doubao ARK API (for video analysis - quality balance)
ARK_API_KEY = os.environ.get("ARK_API_KEY", "a67d5de9-aa45-423c-a326-c011d5692a4c")
VISION_MODEL = "doubao-seed-2-0-lite-260215"
VISION_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"

# Server
HOST = "0.0.0.0"
PORT = 5555
DEBUG = False

# Cleanup: delete uploaded files after analysis
DELETE_AFTER_ANALYSIS = True
