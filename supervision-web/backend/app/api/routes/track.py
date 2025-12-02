"""追蹤 API 路由"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from typing import Optional
import uuid
import time
import asyncio
from pathlib import Path

from app.models.schemas import TrackingTaskResponse, TrackingStatusResponse
from app.config import ALLOWED_VIDEO_EXTENSIONS, UPLOAD_DIR, PROCESSED_DIR
from app.services.tracking_service import TrackingService
from app.utils.file_handler import save_uploaded_file, validate_file_size

router = APIRouter()

# 簡單的任務狀態儲存（生產環境應使用 Redis 或資料庫）
tracking_tasks = {}


def validate_video_file(file: UploadFile) -> bool:
    """驗證影片檔案"""
    from pathlib import Path
    ext = Path(file.filename).suffix.lower()
    return ext in ALLOWED_VIDEO_EXTENSIONS


async def process_tracking_task(
    task_id: str,
    video_path: Path,
    model_type: str,
    model_id: Optional[str],
    tracker_type: str,
    confidence_threshold: float,
    iou_threshold: float
):
    """背景任務：處理影片追蹤"""
    try:
        # 更新狀態為處理中
        tracking_tasks[task_id]["status"] = "processing"
        tracking_tasks[task_id]["progress"] = 0
        
        # 準備輸出路徑
        output_path = PROCESSED_DIR / f"tracked_{task_id}.mp4"
        
        # 進度回調
        def update_progress(progress: int):
            tracking_tasks[task_id]["progress"] = progress
        
        # 在執行器線程中運行同步的追蹤處理
        loop = asyncio.get_event_loop()
        # 在執行器線程中運行同步的追蹤處理
        result = await loop.run_in_executor(
            None,
            lambda: TrackingService.process_video_tracking(
                video_path,
                output_path,
                model_type,
                model_id,
                tracker_type,
                confidence_threshold,
                iou_threshold,
                update_progress
            )
        )
        
        # 生成影片 URL
        video_url = f"/static/processed/{output_path.name}"
        
        # 更新任務狀態
        tracking_tasks[task_id]["status"] = "completed"
        tracking_tasks[task_id]["progress"] = 100
        tracking_tasks[task_id]["video_url"] = video_url
        tracking_tasks[task_id]["tracks"] = result["tracks"]
        
    except Exception as e:
        tracking_tasks[task_id]["status"] = "failed"
        tracking_tasks[task_id]["error"] = str(e)
        print(f"追蹤任務失敗 {task_id}: {e}")


@router.post("/track", response_model=TrackingTaskResponse)
async def track_objects(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...),
    model_type: str = Form(default="yolov8"),
    tracker_type: str = Form(default="bytetrack"),
    confidence_threshold: float = Form(default=0.25),
    iou_threshold: float = Form(default=0.45),
    model_id: Optional[str] = Form(default=None)
):
    """
    上傳影片進行物件追蹤
    
    返回任務 ID，使用 GET /track/{task_id}/status 查詢進度
    """
    # 驗證檔案
    if not validate_video_file(video):
        raise HTTPException(
            status_code=400,
            detail=f"不支援的影片格式。支援的格式: {ALLOWED_VIDEO_EXTENSIONS}"
        )
    
    # 讀取並儲存影片
    contents = await video.read()
    
    # 驗證檔案大小
    if not validate_file_size(len(contents), 500 * 1024 * 1024):  # 500MB
        raise HTTPException(status_code=400, detail="檔案大小超過限制 (500MB)")
    
    # 儲存上傳的影片
    video_path, _ = save_uploaded_file(
        contents,
        UPLOAD_DIR,
        prefix="tracking"
    )
    
    task_id = str(uuid.uuid4())
    
    # 初始化任務狀態
    tracking_tasks[task_id] = {
        "status": "queued",
        "progress": 0,
        "video_url": None,
        "tracks": None,
        "created_at": time.time()
    }
    
    # 在背景任務中處理影片
    background_tasks.add_task(
        process_tracking_task,
        task_id,
        video_path,
        model_type,
        model_id,
        tracker_type,
        confidence_threshold,
        iou_threshold
    )
    
    # 估算處理時間（根據影片大小粗略估算）
    estimated_time = 120  # 預設 2 分鐘
    
    return TrackingTaskResponse(
        success=True,
        task_id=task_id,
        status="queued",
        estimated_time=estimated_time
    )


@router.get("/track/{task_id}/status", response_model=TrackingStatusResponse)
async def get_tracking_status(task_id: str):
    """查詢追蹤任務狀態"""
    if task_id not in tracking_tasks:
        raise HTTPException(status_code=404, detail="任務不存在")
    
    task = tracking_tasks[task_id]
    return TrackingStatusResponse(
        success=True,
        status=task["status"],
        progress=task["progress"],
        video_url=task["video_url"],
        tracks=task["tracks"]
    )



