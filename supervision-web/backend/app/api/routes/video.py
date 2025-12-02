"""影片處理 API 路由"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
import tempfile
import supervision as sv
import cv2
from app.config import ALLOWED_VIDEO_EXTENSIONS, UPLOAD_DIR
from app.utils.file_handler import save_video, validate_file_size

router = APIRouter()


def validate_video_file(file: UploadFile) -> bool:
    """驗證影片檔案"""
    ext = Path(file.filename).suffix.lower()
    return ext in ALLOWED_VIDEO_EXTENSIONS


@router.post("/video/info")
async def get_video_info(video: UploadFile = File(...)):
    """
    獲取影片資訊
    
    - **video**: 影片檔案
    """
    if not validate_video_file(video):
        raise HTTPException(
            status_code=400,
            detail=f"不支援的影片格式。支援的格式: {ALLOWED_VIDEO_EXTENSIONS}"
        )
    
    # 驗證檔案大小
    contents = await video.read()
    await video.seek(0)  # 重置檔案指針
    
    if not validate_file_size(len(contents), 500 * 1024 * 1024):  # 500MB
        raise HTTPException(status_code=400, detail="檔案大小超過限制 (500MB)")
    
    try:
        # 將上傳的檔案儲存到臨時位置
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(video.filename).suffix) as tmp_file:
            tmp_file.write(contents)
            tmp_path = Path(tmp_file.name)
        
        try:
            # 使用 Supervision 獲取影片資訊
            video_info = sv.VideoInfo.from_video_path(str(tmp_path))
            
            return {
                "success": True,
                "width": video_info.width,
                "height": video_info.height,
                "fps": video_info.fps,
                "total_frames": video_info.total_frames,
                "duration_seconds": video_info.duration_seconds
            }
        finally:
            # 清理臨時檔案
            if tmp_path.exists():
                tmp_path.unlink()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"處理錯誤: {str(e)}")


@router.post("/video/process")
async def process_video(
    video: UploadFile = File(...),
    callback_type: str = "detect",
    model_type: str = "yolov8",
    confidence_threshold: float = 0.25
):
    """
    處理影片
    
    - **video**: 影片檔案
    - **callback_type**: 處理類型 (detect, track, segment)
    - **model_type**: 模型類型
    - **confidence_threshold**: 信心閾值
    """
    if not validate_video_file(video):
        raise HTTPException(
            status_code=400,
            detail=f"不支援的影片格式。支援的格式: {ALLOWED_VIDEO_EXTENSIONS}"
        )
    
    try:
        # 儲存上傳的影片
        contents = await video.read()
        video_path, video_url = save_video(
            Path(video.filename),
            UPLOAD_DIR,
            prefix="video"
        )
        video_path.write_bytes(contents)
        
        # 根據處理類型執行不同的邏輯
        if callback_type == "detect":
            # 這裡可以實作檢測邏輯
            # 目前返回基本資訊
            video_info = sv.VideoInfo.from_video_path(str(video_path))
            return {
                "success": True,
                "message": "影片處理完成",
                "video_url": video_url,
                "video_info": {
                    "width": video_info.width,
                    "height": video_info.height,
                    "fps": video_info.fps,
                    "total_frames": video_info.total_frames,
                    "duration_seconds": video_info.duration_seconds
                }
            }
        else:
            return {
                "success": True,
                "message": f"{callback_type} 處理功能開發中",
                "video_url": video_url
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"處理錯誤: {str(e)}")



