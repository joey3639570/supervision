"""應用程式配置"""
import os
from pathlib import Path

# 基礎路徑
BASE_DIR = Path(__file__).parent.parent
STATIC_DIR = BASE_DIR / "static"
UPLOAD_DIR = STATIC_DIR / "uploads"
PROCESSED_DIR = STATIC_DIR / "processed"

# 創建必要的目錄
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# API 配置
API_V1_PREFIX = "/api/v1"

# 檔案上傳限制
MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}

# 模型配置
DEFAULT_MODEL_TYPE = "yolov8n"
DEFAULT_CONFIDENCE_THRESHOLD = 0.25
DEFAULT_IOU_THRESHOLD = 0.45

# 環境變數
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


