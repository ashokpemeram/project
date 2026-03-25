import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

# Load backend/.env if present (so DATA_BACKEND=MONGO works without shell exports)
load_dotenv(BASE_DIR / ".env")


def _resolve_path(value: str | Path, base: Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (base / path).resolve()


# Model configuration
MODEL_PATH = _resolve_path(
    os.getenv("MODEL_PATH", PROJECT_ROOT / "model" / "weights" / "model.pth"),
    PROJECT_ROOT,
)
MODEL_CLASS_PATH = os.getenv("MODEL_CLASS_PATH", "model.generator:MitsGanGenerator")
MODEL_STRICT = os.getenv("MODEL_STRICT", "1").lower() in {"1", "true", "yes"}
ALLOW_PLACEHOLDER_MODEL = os.getenv("ALLOW_PLACEHOLDER_MODEL", "0").lower() in {"1", "true", "yes"}
DEVICE = os.getenv("DEVICE", "cpu")

# Storage configuration
DATA_DIR = _resolve_path(os.getenv("DATA_DIR", BASE_DIR / "data"), BASE_DIR)
STORE_PATH = DATA_DIR / "store.json"
PROTECTED_DIR = _resolve_path(os.getenv("PROTECTED_DIR", BASE_DIR / "storage" / "protected"), BASE_DIR)
DATA_DIR.mkdir(parents=True, exist_ok=True)
PROTECTED_DIR.mkdir(parents=True, exist_ok=True)

# Legacy upload configuration (kept for backward compatibility)
UPLOAD_DIR = _resolve_path(os.getenv("UPLOAD_DIR", BASE_DIR / "uploads"), BASE_DIR)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# File validation
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 10 * 1024 * 1024))
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "bmp", "tiff"}

# Image processing configuration
IMAGE_SIZE = (512, 512)
NORMALIZE_MEAN = [0.485, 0.456, 0.406]
NORMALIZE_STD = [0.229, 0.224, 0.225]


# Model input configuration
MODEL_INPUT_CHANNELS = int(os.getenv("MODEL_INPUT_CHANNELS", "1"))
MODEL_INPUT_RANGE = os.getenv("MODEL_INPUT_RANGE", "tanh").lower()

# API configuration
API_PREFIX = "/api"
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]

# Simple auth configuration
PASSWORD_SALT = os.getenv("PASSWORD_SALT", "dev-salt")

# Data backend
DATA_BACKEND = os.getenv("DATA_BACKEND", "json")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "secure_hospital")

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
