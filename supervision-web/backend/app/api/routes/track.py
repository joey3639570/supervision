"""追蹤 API 路由"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from typing import Optional
import uuid
import time

from app.models.schemas import TrackingTaskResponse, TrackingStatusResponse
from app.config import ALLOWED_VIDEO_EXTENSIONS

router = APIRouter()

# 簡單的任務狀態儲存（生產環境應使用 Redis 或資料庫）
tracking_tasks = {}


@router.post("/track", response_model=TrackingTaskResponse)
async def track_objects(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...),
    model_type: str = Form(default="yolov8"),
    tracker_type: str = Form(default="bytetrack"),
    confidence_threshold: float = Form(default=0.25),
    iou_threshold: float = Form(default=0.45)
):
    """
    上傳影片進行物件追蹤
    
    返回任務 ID，使用 GET /track/{task_id}/status 查詢進度
    """
    task_id = str(uuid.uuid4())
    
    # 初始化任務狀態
    tracking_tasks[task_id] = {
        "status": "processing",
        "progress": 0,
        "video_url": None,
        "tracks": None,
        "created_at": time.time()
    }
    
    # TODO: 在背景任務中處理影片
    # background_tasks.add_task(process_tracking_task, task_id, video, ...)
    
    return TrackingTaskResponse(
        success=True,
        task_id=task_id,
        status="processing",
        estimated_time=120  # 示例時間
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


