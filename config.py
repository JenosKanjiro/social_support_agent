import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "models"
STORAGE_DIR = BASE_DIR / "storage"
LOGS_DIR = BASE_DIR / "logs"
ASSETS_DIR = STORAGE_DIR / "assets"

# Create directories if they don't exist
os.makedirs(LOGS_DIR, exist_ok=True)

# Model paths
MODEL_PATH = MODEL_DIR / "model.xgb"
LABEL_ENCODER_PATH = MODEL_DIR / "label_encoder.pkl"

# Vector store settings
VECTOR_STORE_DIR = STORAGE_DIR / "llama_index_storage"
EMBEDDING_MODEL = "nomic-embed-text:latest"
EMBEDDING_BASE_URL = "http://localhost:11434"

# Database settings
DB_CONFIG = {
    "database": "",
    "user": "postgres",
    "host": "localhost",
    "password": os.environ.get("DB_PASSWORD", ""),
}

# LLM settings
LLM_CONFIG = {
    "extraction_model": "llama3.2:1b",
    "validation_model": "qwen3:0.6b",
    "extraction_temperature": 0,
    "validation_temperature": 0,
}

# Cache settings
EXTRACTION_CACHE_PATH = STORAGE_DIR / "cached_extraction_data_file_path.pkl"