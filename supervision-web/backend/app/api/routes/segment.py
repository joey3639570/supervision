"""
分割 API 路由 (SAM3)
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional, List
import cv2
import numpy as np
import time
import base64
from pathlib import Path

from app.models.schemas import SegmentationResponse
from app.services.supervision_service import SupervisionService
from app.config import ALLOWED_IMAGE_EXTENSIONS

router = APIRouter()


@router.post("/segment", response_model=SegmentationResponse)
async def segment_image(
    image: UploadFile = File(...),
    prompts: Optional[str] = Form(default=None),
    prompt_type: str = Form(default="text"),
    auto_generate: bool = Form(default=False)
):
    """
    使用 SAM3 進行圖像分割
    
    - **image**: 圖片檔案
    - **prompts**: 提示詞列表 (JSON 字串)
    - **prompt_type**: 提示類型 (text, point, box)
    - **auto_generate**: 是否自動生成遮罩
    """
    start_time = time.time()
    
    try:
        # 讀取圖片
        contents = await image.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(status_code=400, detail="無法讀取圖片")
        
        # TODO: 實際的 SAM3 推理
        # 這裡需要載入 SAM3 模型並進行推理
        # 目前返回示例數據
        
        # 示例：創建空的 SAM3 結果
        sam3_result = []
        
        # 轉換為 Detections
        import supervision as sv
        detections = sv.Detections.from_sam3(sam3_result)
        
        # 轉換為回應格式
        masks_list = []
        for i in range(len(detections)):
            mask_dict = {
                "bbox": detections.xyxy[i].tolist(),
                "area": float(detections.area[i]) if hasattr(detections, 'area') else 0.0
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

