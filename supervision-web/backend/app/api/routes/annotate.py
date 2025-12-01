"""標註 API 路由"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import cv2
import numpy as np
import time

from app.models.schemas import AnnotationRequest
from app.services.supervision_service import SupervisionService

router = APIRouter()


class AnnotateRequest(BaseModel):
    """標註請求"""
    image_url: str
    detections: List[Dict[str, Any]]
    annotator_type: str = "box"
    options: Optional[Dict[str, Any]] = None
    labels: Optional[List[str]] = None


@router.post("/annotate")
async def annotate_image(request: AnnotateRequest):
    """
    對檢測結果進行標註
    
    - **image_url**: 圖片 URL 或 base64
    - **detections**: 檢測結果列表
    - **annotator_type**: 標註器類型
    - **options**: 標註選項
    - **labels**: 標籤列表
    """
    try:
        # TODO: 從 image_url 載入圖片
        # 這裡需要實作圖片載入邏輯
        
        # 轉換檢測結果為 Detections
        xyxy = np.array([d["xyxy"] for d in request.detections])
        confidence = None
        class_id = None
        
        if any("confidence" in d for d in request.detections):
            confidence = np.array([d.get("confidence", 0.0) for d in request.detections])
        
        if any("class_id" in d for d in request.detections):
            class_id = np.array([d.get("class_id", 0) for d in request.detections])
        
        import supervision as sv
        detections = sv.Detections(
            xyxy=xyxy,
            confidence=confidence,
            class_id=class_id
        )
        
        # 創建標註器並標註
        annotated_image = SupervisionService.annotate_image(
            image=np.zeros((100, 100, 3), dtype=np.uint8),  # 示例圖片
            detections=detections,
            annotator_type=request.annotator_type,
            labels=request.labels,
            **(request.options or {})
        )
        
        # TODO: 儲存標註後的圖片並返回 URL
        
        return {
            "success": True,
            "annotated_image_url": None  # 實際的圖片 URL
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"處理錯誤: {str(e)}")

