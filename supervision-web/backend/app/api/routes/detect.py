"""
檢測 API 路由
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import cv2
import numpy as np
import time
import os
from pathlib import Path

from app.models.schemas import (
    DetectionRequest,
    DetectionResponse,
    Detection,
    ModelType
)
from app.services.supervision_service import SupervisionService
from app.config import UPLOAD_DIR, PROCESSED_DIR, ALLOWED_IMAGE_EXTENSIONS

router = APIRouter()


def validate_image_file(file: UploadFile) -> bool:
    """驗證圖片檔案"""
    ext = Path(file.filename).suffix.lower()
    return ext in ALLOWED_IMAGE_EXTENSIONS


@router.post("/detect", response_model=DetectionResponse)
async def detect_objects(
    image: UploadFile = File(...),
    model_type: str = Form(default="yolov8"),
    model_id: Optional[str] = Form(default=None),
    confidence_threshold: float = Form(default=0.25),
    iou_threshold: float = Form(default=0.45),
    classes: Optional[str] = Form(default=None)
):
    """
    上傳圖片進行物件檢測
    
    - **image**: 圖片檔案
    - **model_type**: 模型類型 (yolov8, yolov5, yolonas, etc.)
    - **confidence_threshold**: 信心閾值 (0.0-1.0)
    - **iou_threshold**: IoU 閾值 (0.0-1.0)
    - **classes**: 要檢測的類別 ID 列表 (JSON 字串)
    """
    start_time = time.time()
    
    # 驗證檔案
    if not validate_image_file(image):
        raise HTTPException(
            status_code=400,
            detail=f"不支援的圖片格式。支援的格式: {ALLOWED_IMAGE_EXTENSIONS}"
        )
    
    try:
        # 讀取圖片
        contents = await image.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(status_code=400, detail="無法讀取圖片")
        
        # TODO: 實際的模型推理
        # 這裡需要根據 model_type 載入對應的模型並進行推理
        # 目前返回示例數據
        
        # 示例：創建空的檢測結果
        import supervision as sv
        detections = sv.Detections.empty()
        
        # 應用過濾
        if detections.confidence is not None:
            detections = SupervisionService.filter_by_confidence(
                detections,
                confidence_threshold
            )
        
        if classes:
            import json
            class_ids = json.loads(classes)
            detections = SupervisionService.filter_by_class(
                detections,
                class_ids
            )
        
        # 應用 NMS
        detections = SupervisionService.apply_nms(
            detections,
            threshold=iou_threshold
        )
        
        # 轉換為回應格式
        detection_list = []
        for i in range(len(detections)):
            detection_dict = {
                "xyxy": detections.xyxy[i].tolist(),
            }
            if detections.confidence is not None:
                detection_dict["confidence"] = float(detections.confidence[i])
            if detections.class_id is not None:
                detection_dict["class_id"] = int(detections.class_id[i])
            if detections.tracker_id is not None:
                detection_dict["tracker_id"] = int(detections.tracker_id[i])
            detection_list.append(Detection(**detection_dict))
        
        # 儲存處理後的圖片（可選）
        # processed_path = PROCESSED_DIR / f"detected_{int(time.time())}.jpg"
        # cv2.imwrite(str(processed_path), img)
        # image_url = f"/static/processed/{processed_path.name}"
        
        processing_time = time.time() - start_time
        
        return DetectionResponse(
            success=True,
            detections=detection_list,
            image_url=None,  # image_url,
            processing_time=processing_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"處理錯誤: {str(e)}")

