"""
SAM3 API 路由
提供 SAM3 相關功能：對象計數、線計數、區域計數、追蹤
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from typing import Optional, List
import cv2
import numpy as np
import time
import base64
import json
import os
import uuid
import torch
from pathlib import Path
from tqdm import tqdm

from app.models.schemas import SegmentationResponse
from app.services.sam3_service import SAM3Service
from app.services.supervision_service import SupervisionService
from app.config import ALLOWED_IMAGE_EXTENSIONS, ALLOWED_VIDEO_EXTENSIONS, STATIC_DIR, PROCESSED_DIR
import supervision as sv

router = APIRouter()

# 任務狀態存儲（生產環境應使用 Redis 或數據庫）
task_status = {}


@router.post("/sam3/count", response_model=SegmentationResponse)
async def count_objects(
    image: UploadFile = File(...),
    prompt: str = Form(...),
    confidence_threshold: float = Form(default=0.5),
    checkpoint_path: Optional[str] = Form(default=None),
    device: str = Form(default="cuda"),
):
    """
    使用 SAM3 計算圖像中的對象數量
    
    - **image**: 圖片檔案
    - **prompt**: 文本提示（例如："person", "car"）
    - **confidence_threshold**: 信心閾值
    - **checkpoint_path**: SAM3 檢查點路徑（可選）
    - **device**: 設備 ('cuda' 或 'cpu')
    """
    if not SAM3Service.is_available():
        raise HTTPException(
            status_code=503,
            detail="SAM3 is not available. Please install the sam3 package."
        )
    
    start_time = time.time()
    
    try:
        # 讀取圖片
        contents = await image.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(status_code=400, detail="無法讀取圖片")
        
        # 載入模型
        model, model_key = SAM3Service.load_model(
            checkpoint_path=checkpoint_path,
            device=device if device == "cuda" and torch.cuda.is_available() else "cpu"
        )
        
        # 檢測對象
        detections, _ = SAM3Service.detect_objects_in_image(
            image=img,
            prompt=prompt,
            model_key=model_key,
            device=device,
            confidence_threshold=confidence_threshold
        )
        
        # 轉換為回應格式
        masks_list = []
        for i in range(len(detections)):
            mask_dict = {
                "bbox": detections.xyxy[i].tolist(),
                "area": float(detections.area[i]) if detections.area is not None else 0.0,
                "confidence": float(detections.confidence[i]) if detections.confidence is not None else 0.0,
            }
            if detections.mask is not None:
                # 將遮罩編碼為 base64
                mask_bool = detections.mask[i]
                mask_uint8 = (mask_bool * 255).astype(np.uint8)
                _, buffer = cv2.imencode('.png', mask_uint8)
                mask_base64 = base64.b64encode(buffer).decode('utf-8')
                mask_dict["segmentation"] = mask_base64
            masks_list.append(mask_dict)
        
        processing_time = time.time() - start_time
        
        return SegmentationResponse(
            success=True,
            masks=masks_list,
            image_url=None,
            processing_time=processing_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"處理錯誤: {str(e)}")


@router.post("/sam3/multi-prompt")
async def multi_prompt_detection(
    image: UploadFile = File(...),
    prompts: str = Form(...),  # JSON array string
    confidence_threshold: float = Form(default=0.5),
    checkpoint_path: Optional[str] = Form(default=None),
    device: str = Form(default="cuda"),
):
    """
    使用多個提示詞檢測對象
    
    - **image**: 圖片檔案
    - **prompts**: 提示詞列表 JSON 字符串 (例如: ["person", "car"])
    - **confidence_threshold**: 信心閾值
    """
    if not SAM3Service.is_available():
        raise HTTPException(
            status_code=503,
            detail="SAM3 is not available. Please install the sam3 package."
        )
    
    start_time = time.time()
    
    try:
        # 解析提示詞
        prompts_list = json.loads(prompts)
        if not isinstance(prompts_list, list):
            raise HTTPException(status_code=400, detail="prompts must be a JSON array")
        
        # 讀取圖片
        contents = await image.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(status_code=400, detail="無法讀取圖片")
        
        # 載入模型
        model, model_key = SAM3Service.load_model(
            checkpoint_path=checkpoint_path,
            device=device if device == "cuda" and torch.cuda.is_available() else "cpu"
        )
        
        # 處理每個提示詞
        prompt_counts = {}
        all_masks = []
        
        for prompt in prompts_list:
            detections, _ = SAM3Service.detect_objects_in_image(
                image=img,
                prompt=prompt,
                model_key=model_key,
                device=device,
                confidence_threshold=confidence_threshold
            )
            
            count = len(detections)
            prompt_counts[prompt] = count
            
            # 轉換為回應格式
            for i in range(len(detections)):
                mask_dict = {
                    "bbox": detections.xyxy[i].tolist(),
                    "area": float(detections.area[i]) if detections.area is not None else 0.0,
                    "confidence": float(detections.confidence[i]) if detections.confidence is not None else 0.0,
                    "prompt": prompt,
                }
                if detections.mask is not None:
                    mask_bool = detections.mask[i]
                    mask_uint8 = (mask_bool * 255).astype(np.uint8)
                    _, buffer = cv2.imencode('.png', mask_uint8)
                    mask_base64 = base64.b64encode(buffer).decode('utf-8')
                    mask_dict["segmentation"] = mask_base64
                all_masks.append(mask_dict)
        
        processing_time = time.time() - start_time
        
        return {
            "success": True,
            "prompt_counts": prompt_counts,
            "masks": all_masks,
            "processing_time": processing_time
        }
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format for prompts")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"處理錯誤: {str(e)}")


@router.post("/sam3/line-count")
async def count_line_crossings(
    video: UploadFile = File(...),
    prompt: str = Form(...),
    line_start_x: int = Form(...),
    line_start_y: int = Form(...),
    line_end_x: int = Form(...),
    line_end_y: int = Form(...),
    confidence_threshold: float = Form(default=0.5),
    checkpoint_path: Optional[str] = Form(default=None),
    device: str = Form(default="cuda"),
    background_tasks: BackgroundTasks = None,
):
    """
    計算視頻中穿過線的對象數量
    
    - **video**: 視頻檔案
    - **prompt**: 文本提示
    - **line_start_x**, **line_start_y**: 線的起點座標
    - **line_end_x**, **line_end_y**: 線的終點座標
    - **confidence_threshold**: 信心閾值
    """
    if not SAM3Service.is_available():
        raise HTTPException(
            status_code=503,
            detail="SAM3 is not available. Please install the sam3 package."
        )
    
    task_id = str(uuid.uuid4())
    task_status[task_id] = {
        "status": "processing",
        "progress": 0,
        "in_count": 0,
        "out_count": 0,
    }
    
    try:
        # 保存視頻文件
        video_path = PROCESSED_DIR / f"upload_{task_id}_{video.filename}"
        with open(video_path, "wb") as f:
            content = await video.read()
            f.write(content)
        
        # 在後台處理視頻
        background_tasks.add_task(
            process_line_counting_video,
            str(video_path),
            prompt,
            (line_start_x, line_start_y),
            (line_end_x, line_end_y),
            confidence_threshold,
            checkpoint_path,
            device,
            task_id
        )
        
        return {
            "success": True,
            "task_id": task_id,
            "status": "processing",
            "message": "Video processing started"
        }
        
    except Exception as e:
        task_status[task_id]["status"] = "error"
        raise HTTPException(status_code=500, detail=f"處理錯誤: {str(e)}")


@router.post("/sam3/zone-count")
async def count_zone_objects(
    video: UploadFile = File(...),
    prompt: str = Form(...),
    zones: str = Form(...),  # JSON string of zones
    confidence_threshold: float = Form(default=0.5),
    checkpoint_path: Optional[str] = Form(default=None),
    device: str = Form(default="cuda"),
    background_tasks: BackgroundTasks = None,
):
    """
    計算視頻中區域內的對象數量
    
    - **video**: 視頻檔案
    - **prompt**: 文本提示
    - **zones**: 區域配置 JSON 字符串，格式: {"polygons": [[[x1,y1], [x2,y2], ...], ...]}
    - **confidence_threshold**: 信心閾值
    """
    if not SAM3Service.is_available():
        raise HTTPException(
            status_code=503,
            detail="SAM3 is not available. Please install the sam3 package."
        )
    
    task_id = str(uuid.uuid4())
    task_status[task_id] = {
        "status": "processing",
        "progress": 0,
        "zone_counts": [],
    }
    
    try:
        # 解析區域配置
        zones_data = json.loads(zones)
        polygons = [np.array(polygon, np.int32) for polygon in zones_data["polygons"]]
        
        # 保存視頻文件
        video_path = PROCESSED_DIR / f"upload_{task_id}_{video.filename}"
        with open(video_path, "wb") as f:
            content = await video.read()
            f.write(content)
        
        # 在後台處理視頻
        background_tasks.add_task(
            process_zone_counting_video,
            str(video_path),
            prompt,
            polygons,
            confidence_threshold,
            checkpoint_path,
            device,
            task_id
        )
        
        return {
            "success": True,
            "task_id": task_id,
            "status": "processing",
            "message": "Video processing started"
        }
        
    except Exception as e:
        task_status[task_id]["status"] = "error"
        raise HTTPException(status_code=500, detail=f"處理錯誤: {str(e)}")


@router.post("/sam3/track")
async def track_objects(
    video: UploadFile = File(...),
    prompt: str = Form(...),
    confidence_threshold: float = Form(default=0.5),
    trace_length: int = Form(default=30),
    checkpoint_path: Optional[str] = Form(default=None),
    device: str = Form(default="cuda"),
    background_tasks: BackgroundTasks = None,
):
    """
    追蹤視頻中的對象
    
    - **video**: 視頻檔案
    - **prompt**: 文本提示
    - **confidence_threshold**: 信心閾值
    - **trace_length**: 追蹤軌跡長度
    """
    if not SAM3Service.is_available():
        raise HTTPException(
            status_code=503,
            detail="SAM3 is not available. Please install the sam3 package."
        )
    
    task_id = str(uuid.uuid4())
    task_status[task_id] = {
        "status": "processing",
        "progress": 0,
        "tracked_objects": 0,
    }
    
    try:
        # 保存視頻文件
        video_path = PROCESSED_DIR / f"upload_{task_id}_{video.filename}"
        with open(video_path, "wb") as f:
            content = await video.read()
            f.write(content)
        
        # 在後台處理視頻
        background_tasks.add_task(
            process_tracking_video,
            str(video_path),
            prompt,
            confidence_threshold,
            trace_length,
            checkpoint_path,
            device,
            task_id
        )
        
        return {
            "success": True,
            "task_id": task_id,
            "status": "processing",
            "message": "Video processing started"
        }
        
    except Exception as e:
        task_status[task_id]["status"] = "error"
        raise HTTPException(status_code=500, detail=f"處理錯誤: {str(e)}")


@router.get("/sam3/task/{task_id}")
async def get_task_status(task_id: str):
    """獲取任務狀態"""
    if task_id not in task_status:
        raise HTTPException(status_code=404, detail="Task not found")
    
    status = task_status[task_id]
    
    response = {
        "success": True,
        "task_id": task_id,
        "status": status["status"],
        "progress": status.get("progress", 0),
    }
    
    if status["status"] == "completed":
        response["video_url"] = status.get("video_url")
        response["in_count"] = status.get("in_count", 0)
        response["out_count"] = status.get("out_count", 0)
        response["zone_counts"] = status.get("zone_counts", [])
        response["tracked_objects"] = status.get("tracked_objects", 0)
    
    return response


# 後台處理函數
def process_line_counting_video(
    video_path: str,
    prompt: str,
    line_start: tuple,
    line_end: tuple,
    confidence_threshold: float,
    checkpoint_path: Optional[str],
    device: str,
    task_id: str
):
    """處理線計數視頻"""
    try:
        import torch
        
        # 載入模型
        model, model_key = SAM3Service.load_model(
            checkpoint_path=checkpoint_path,
            device=device if device == "cuda" and torch.cuda.is_available() else "cpu"
        )
        
        # 初始化追蹤器
        tracker = sv.ByteTrack()
        
        # 初始化線區域
        line_zone = sv.LineZone(
            start=sv.Point(x=line_start[0], y=line_start[1]),
            end=sv.Point(x=line_end[0], y=line_end[1]),
        )
        
        # 初始化標註器
        box_annotator = sv.BoxAnnotator()
        label_annotator = sv.LabelAnnotator()
        line_zone_annotator = sv.LineZoneAnnotator()
        trace_annotator = sv.TraceAnnotator()
        
        # 獲取視頻信息
        video_info = sv.VideoInfo.from_video_path(video_path)
        frames_generator = sv.get_video_frames_generator(video_path)
        
        # 處理狀態
        state = {}
        output_path = PROCESSED_DIR / f"output_{task_id}.mp4"
        
        # 使用 cv2.VideoWriter 直接控制編碼，確保使用 H.264
        # 嘗試使用 'H264'，如果不支持則使用 'avc1'
        fourcc = cv2.VideoWriter_fourcc(*'H264')
        if fourcc == -1:
            fourcc = cv2.VideoWriter_fourcc(*'avc1')
        
        video_writer = cv2.VideoWriter(
            str(output_path),
            fourcc,
            video_info.fps,
            (video_info.width, video_info.height)
        )
        
        if not video_writer.isOpened():
            raise RuntimeError(f"無法創建視頻寫入器，編碼器可能不支持")
        
        try:
            for frame_idx, frame in enumerate(tqdm(frames_generator, total=video_info.total_frames)):
                # 檢測對象
                detections, state = SAM3Service.detect_objects_in_frame(
                    frame=frame,
                    prompt=prompt,
                    model_key=model_key,
                    state=state,
                    device=device,
                    confidence_threshold=confidence_threshold
                )
                
                # 追蹤對象
                detections = tracker.update_with_detections(detections)
                
                # 更新線區域
                crossed_in, crossed_out = line_zone.trigger(detections)
                
                # 標註幀
                annotated_frame = frame.copy()
                annotated_frame = line_zone_annotator.annotate(scene=annotated_frame, line_counter=line_zone)
                annotated_frame = trace_annotator.annotate(scene=annotated_frame, detections=detections)
                annotated_frame = box_annotator.annotate(scene=annotated_frame, detections=detections)
                
                labels = [f"#{tracker_id}" if tracker_id is not None else "" for tracker_id in detections.tracker_id]
                annotated_frame = label_annotator.annotate(scene=annotated_frame, detections=detections, labels=labels)
                
                # supervision 基於 OpenCV，返回的幀已經是 BGR 格式，直接寫入
                video_writer.write(annotated_frame)
                
                # 更新進度
                progress = int((frame_idx + 1) / video_info.total_frames * 100)
                task_status[task_id]["progress"] = progress
                task_status[task_id]["in_count"] = line_zone.in_count
                task_status[task_id]["out_count"] = line_zone.out_count
        finally:
            video_writer.release()
        
        task_status[task_id]["status"] = "completed"
        task_status[task_id]["video_url"] = f"/static/processed/{output_path.name}"
        
    except Exception as e:
        task_status[task_id]["status"] = "error"
        task_status[task_id]["error"] = str(e)


def process_zone_counting_video(
    video_path: str,
    prompt: str,
    polygons: List[np.ndarray],
    confidence_threshold: float,
    checkpoint_path: Optional[str],
    device: str,
    task_id: str
):
    """處理區域計數視頻"""
    try:
        import torch
        
        # 載入模型
        model, model_key = SAM3Service.load_model(
            checkpoint_path=checkpoint_path,
            device=device if device == "cuda" and torch.cuda.is_available() else "cpu"
        )
        
        # 獲取視頻信息
        video_info = sv.VideoInfo.from_video_path(video_path)
        
        # 初始化區域
        zones = []
        zone_annotators = []
        box_annotators = []
        colors = sv.ColorPalette.DEFAULT
        
        for index, polygon in enumerate(polygons):
            zone = sv.PolygonZone(polygon=polygon)
            zone_annotator = sv.PolygonZoneAnnotator(
                zone=zone,
                color=colors.by_idx(index),
            )
            box_annotator = sv.BoxAnnotator(color=colors.by_idx(index))
            zones.append(zone)
            zone_annotators.append(zone_annotator)
            box_annotators.append(box_annotator)
        
        frames_generator = sv.get_video_frames_generator(video_path)
        state = {}
        output_path = PROCESSED_DIR / f"output_{task_id}.mp4"
        
        # 使用 cv2.VideoWriter 直接控制編碼，確保使用 H.264
        # 嘗試使用 'H264'，如果不支持則使用 'avc1'
        fourcc = cv2.VideoWriter_fourcc(*'H264')
        if fourcc == -1:
            fourcc = cv2.VideoWriter_fourcc(*'avc1')
        
        video_writer = cv2.VideoWriter(
            str(output_path),
            fourcc,
            video_info.fps,
            (video_info.width, video_info.height)
        )
        
        if not video_writer.isOpened():
            raise RuntimeError(f"無法創建視頻寫入器，編碼器可能不支持")
        
        try:
            for frame_idx, frame in enumerate(tqdm(frames_generator, total=video_info.total_frames)):
                # 檢測對象
                detections, state = SAM3Service.detect_objects_in_frame(
                    frame=frame,
                    prompt=prompt,
                    model_key=model_key,
                    state=state,
                    device=device,
                    confidence_threshold=confidence_threshold
                )
                
                # 標註幀
                annotated_frame = frame.copy()
                for zone, zone_annotator, box_annotator in zip(zones, zone_annotators, box_annotators):
                    detections_in_zone = detections[zone.trigger(detections=detections)]
                    annotated_frame = zone_annotator.annotate(scene=annotated_frame)
                    annotated_frame = box_annotator.annotate(scene=annotated_frame, detections=detections_in_zone)
                
                # supervision 基於 OpenCV，返回的幀已經是 BGR 格式，直接寫入
                video_writer.write(annotated_frame)
                
                # 更新進度
                progress = int((frame_idx + 1) / video_info.total_frames * 100)
                task_status[task_id]["progress"] = progress
                task_status[task_id]["zone_counts"] = [zone.current_count for zone in zones]
        finally:
            video_writer.release()
        
        task_status[task_id]["status"] = "completed"
        task_status[task_id]["video_url"] = f"/static/processed/{output_path.name}"
        
    except Exception as e:
        task_status[task_id]["status"] = "error"
        task_status[task_id]["error"] = str(e)


def process_tracking_video(
    video_path: str,
    prompt: str,
    confidence_threshold: float,
    trace_length: int,
    checkpoint_path: Optional[str],
    device: str,
    task_id: str
):
    """處理追蹤視頻"""
    try:
        import torch
        
        # 載入模型
        model, model_key = SAM3Service.load_model(
            checkpoint_path=checkpoint_path,
            device=device if device == "cuda" and torch.cuda.is_available() else "cpu"
        )
        
        # 初始化追蹤器
        tracker = sv.ByteTrack()
        
        # 初始化標註器
        mask_annotator = sv.MaskAnnotator()
        box_annotator = sv.BoxAnnotator()
        label_annotator = sv.LabelAnnotator()
        trace_annotator = sv.TraceAnnotator(trace_length=trace_length)
        
        # 獲取視頻信息
        video_info = sv.VideoInfo.from_video_path(video_path)
        frames_generator = sv.get_video_frames_generator(video_path)
        
        state = {}
        tracked_objects = set()
        output_path = PROCESSED_DIR / f"output_{task_id}.mp4"
        
        # 使用 cv2.VideoWriter 直接控制編碼，確保使用 H.264
        # 嘗試使用 'H264'，如果不支持則使用 'avc1'
        fourcc = cv2.VideoWriter_fourcc(*'H264')
        if fourcc == -1:
            fourcc = cv2.VideoWriter_fourcc(*'avc1')
        
        video_writer = cv2.VideoWriter(
            str(output_path),
            fourcc,
            video_info.fps,
            (video_info.width, video_info.height)
        )
        
        if not video_writer.isOpened():
            raise RuntimeError(f"無法創建視頻寫入器，編碼器可能不支持")
        
        try:
            for frame_idx, frame in enumerate(tqdm(frames_generator, total=video_info.total_frames)):
                # 檢測對象
                detections, state = SAM3Service.detect_objects_in_frame(
                    frame=frame,
                    prompt=prompt,
                    model_key=model_key,
                    state=state,
                    device=device,
                    confidence_threshold=confidence_threshold
                )
                
                # 追蹤對象
                detections = tracker.update_with_detections(detections)
                
                if detections.tracker_id is not None:
                    tracked_objects.update(detections.tracker_id.tolist())
                
                # 標註幀
                annotated_frame = frame.copy()
                annotated_frame = mask_annotator.annotate(scene=annotated_frame, detections=detections)
                annotated_frame = trace_annotator.annotate(scene=annotated_frame, detections=detections)
                annotated_frame = box_annotator.annotate(scene=annotated_frame, detections=detections)
                
                labels = []
                if detections.tracker_id is not None:
                    for tracker_id, score in zip(detections.tracker_id, detections.confidence):
                        labels.append(f"#{tracker_id} ({score:.2f})")
                else:
                    labels = [f"{score:.2f}" for score in detections.confidence]
                
                annotated_frame = label_annotator.annotate(scene=annotated_frame, detections=detections, labels=labels)
                
                # supervision 基於 OpenCV，返回的幀已經是 BGR 格式，直接寫入
                video_writer.write(annotated_frame)
                
                # 更新進度
                progress = int((frame_idx + 1) / video_info.total_frames * 100)
                task_status[task_id]["progress"] = progress
                task_status[task_id]["tracked_objects"] = len(tracked_objects)
        finally:
            video_writer.release()
        
        task_status[task_id]["status"] = "completed"
        task_status[task_id]["video_url"] = f"/static/processed/{output_path.name}"
        
    except Exception as e:
        task_status[task_id]["status"] = "error"
        task_status[task_id]["error"] = str(e)
