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

# SAM3 檢查點設定
# 可以透過環境變數 SAM3_CHECKPOINT_PATH 進行覆寫，例如：
# SAM3_CHECKPOINT_PATH=/path/to/sam3.pt
# 默認檢查點位置（按優先順序）
DEFAULT_SAM3_CHECKPOINT_PATHS = [
    "/root/joey/sam3_model/sam3.pt",  # 實際模型位置
    "/root/joey/sam3_model/model.safetensors",  # 備選格式
    str(BASE_DIR / "checkpoints" / "sam3_hiera_base.pt"),  # 本地備份位置
    str(BASE_DIR / "checkpoints" / "sam3.pt"),  # 本地備份位置
]

# 從環境變數獲取或使用第一個存在的默認路徑
SAM3_CHECKPOINT_PATH = os.getenv("SAM3_CHECKPOINT_PATH")
if not SAM3_CHECKPOINT_PATH:
    for path in DEFAULT_SAM3_CHECKPOINT_PATHS:
        if os.path.exists(path):
            SAM3_CHECKPOINT_PATH = path
            break
    else:
        # 如果都不存在，使用第一個默認路徑（會在運行時報錯）
        SAM3_CHECKPOINT_PATH = DEFAULT_SAM3_CHECKPOINT_PATHS[0]

# 確保檢查點目錄存在（用於可能的備份）
SAM3_CHECKPOINT_DIR = BASE_DIR / "checkpoints"
SAM3_CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

# 環境變數
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

