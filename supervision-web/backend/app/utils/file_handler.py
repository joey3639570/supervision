"""
檔案處理工具
處理檔案上傳、儲存和管理
"""
import os
import uuid
import shutil
from pathlib import Path
from typing import Optional, Tuple
import cv2
import numpy as np
from datetime import datetime, timedelta


def generate_unique_filename(original_filename: str, prefix: str = "") -> str:
    """生成唯一的檔案名稱"""
    ext = Path(original_filename).suffix
    unique_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if prefix:
        filename = f"{prefix}_{timestamp}_{unique_id}{ext}"
    else:
        filename = f"{timestamp}_{unique_id}{ext}"
    
    return filename


def save_image(
    image: np.ndarray,
    upload_dir: Path,
    filename: Optional[str] = None,
    prefix: str = "processed"
) -> Tuple[Path, str]:
    """
    儲存圖片
    
    Args:
        image: OpenCV 圖片 (numpy array)
        upload_dir: 上傳目錄
        filename: 檔案名稱（可選）
        prefix: 檔案前綴
    
    Returns:
        (檔案路徑, URL 路徑)
    """
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    if filename is None:
        filename = generate_unique_filename("image.jpg", prefix)
    
    file_path = upload_dir / filename
    cv2.imwrite(str(file_path), image)
    
    # 生成 URL 路徑
    url_path = f"/static/uploads/{filename}"
    
    return file_path, url_path


def save_video(
    video_path: Path,
    upload_dir: Path,
    filename: Optional[str] = None,
    prefix: str = "video"
) -> Tuple[Path, str]:
    """
    儲存影片檔案
    
    Args:
        video_path: 原始影片路徑
        upload_dir: 上傳目錄
        filename: 檔案名稱（可選）
        prefix: 檔案前綴
    
    Returns:
        (檔案路徑, URL 路徑)
    """
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    if filename is None:
        filename = generate_unique_filename(video_path.name, prefix)
    
    file_path = upload_dir / filename
    shutil.copy2(video_path, file_path)
    
    # 生成 URL 路徑
    url_path = f"/static/uploads/{filename}"
    
    return file_path, url_path


def get_file_url(file_path: Path, base_dir: Path) -> str:
    """
    生成檔案 URL
    
    Args:
        file_path: 檔案路徑
        base_dir: 基礎目錄
    
    Returns:
        URL 路徑
    """
    try:
        relative_path = file_path.relative_to(base_dir)
        return f"/static/{relative_path.as_posix()}"
    except ValueError:
        # 如果檔案不在基礎目錄中，返回檔名
        return f"/static/{file_path.name}"


def cleanup_old_files(directory: Path, days: int = 7):
    """
    清理舊檔案
    
    Args:
        directory: 要清理的目錄
        days: 保留天數
    """
    if not directory.exists():
        return
    
    cutoff_time = datetime.now() - timedelta(days=days)
    
    for file_path in directory.iterdir():
        if file_path.is_file():
            file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            if file_time < cutoff_time:
                try:
                    file_path.unlink()
                    print(f"已刪除舊檔案: {file_path}")
                except Exception as e:
                    print(f"刪除檔案失敗 {file_path}: {e}")


def validate_file_size(file_size: int, max_size: int) -> bool:
    """驗證檔案大小"""
    return file_size <= max_size


def save_uploaded_file(
    contents: bytes,
    upload_dir: Path,
    filename: Optional[str] = None,
    prefix: str = "upload"
) -> Tuple[Path, str]:
    """
    儲存上傳的檔案
    
    Args:
        contents: 檔案內容 (bytes)
        upload_dir: 上傳目錄
        filename: 檔案名稱（可選）
        prefix: 檔案前綴
    
    Returns:
        (檔案路徑, URL 路徑)
    """
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    if filename is None:
        filename = generate_unique_filename("file", prefix)
    
    file_path = upload_dir / filename
    file_path.write_bytes(contents)
    
    # 生成 URL 路徑
    url_path = f"/static/uploads/{filename}"
    
    return file_path, url_path

