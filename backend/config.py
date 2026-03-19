import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Model configuration
MODEL_PATH = os.getenv('MODEL_PATH', BASE_DIR / 'models' / 'model.pth')

# Upload configuration
UPLOAD_DIR = BASE_DIR / 'uploads'
UPLOAD_DIR.mkdir(exist_ok=True)

# File validation
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'bmp', 'tiff'}

# Model configuration
DEVICE = os.getenv('DEVICE', 'cpu')  # 'cuda' or 'cpu'

# Image processing configuration
IMAGE_SIZE = (512, 512)  # Default size, adjust based on your model
NORMALIZE_MEAN = [0.485, 0.456, 0.406]  # ImageNet defaults
NORMALIZE_STD = [0.229, 0.224, 0.225]   # ImageNet defaults

# API configuration
API_PREFIX = '/api'
CORS_ORIGINS = ['http://localhost:3000', 'http://localhost:3001']

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
