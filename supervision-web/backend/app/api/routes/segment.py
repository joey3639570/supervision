"""
分割 API 路由 (SAM3)
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional, List
import cv2
import numpy as np
import time
import base64
import json
import torch
from pathlib import Path

from app.models.schemas import SegmentationResponse
from app.services.sam3_service import SAM3Service
from app.services.supervision_service import SupervisionService
from app.config import ALLOWED_IMAGE_EXTENSIONS

router = APIRouter()


@router.post("/segment", response_model=SegmentationResponse)
async def segment_image(
    image: UploadFile = File(...),
    prompts: Optional[str] = Form(default=None),
    prompt_type: str = Form(default="text"),
    auto_generate: str = Form(default="false"),
    confidence_threshold: str = Form(default="0.5"),
    checkpoint_path: Optional[str] = Form(default=None),
    device: str = Form(default="cuda"),
):
    """
    使用 SAM3 進行圖像分割
    
    - **image**: 圖片檔案
    - **prompts**: 提示詞列表 (JSON 字串或單個字符串)
    - **prompt_type**: 提示類型 (text, point, box)
    - **auto_generate**: 是否自動生成遮罩
    - **confidence_threshold**: 信心閾值
    - **checkpoint_path**: SAM3 檢查點路徑（可選）
    - **device**: 設備 ('cuda' 或 'cpu')
    """
    if not SAM3Service.is_available():
        raise HTTPException(
            status_code=503,
            detail="SAM3 服務不可用。請安裝 sam3 套件以使用 SAM3 功能。"
        )
    
    start_time = time.time()
    
    try:
        # 轉換參數類型
        auto_generate_bool = auto_generate.lower() in ("true", "1", "yes", "on")
        try:
            confidence_threshold_float = float(confidence_threshold)
        except (ValueError, TypeError):
            confidence_threshold_float = 0.5
        
        # 讀取圖片
        contents = await image.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(status_code=400, detail="無法讀取圖片")
        
        # 解析提示詞
        prompts_list = []
        if prompts:
            try:
                prompts_list = json.loads(prompts)
                if isinstance(prompts_list, str):
                    prompts_list = [prompts_list]
                elif not isinstance(prompts_list, list):
                    prompts_list = [prompts_list]
            except json.JSONDecodeError:
                # 如果不是 JSON，嘗試作為字符串處理
                prompts_list = [prompts]
            except Exception as e:
                print(f"Error parsing prompts: {e}")
                prompts_list = [prompts] if prompts else []
        
        # 如果沒有提示詞且不是自動生成模式，使用默認提示
        if not prompts_list and not auto_generate_bool:
            if prompt_type == "auto":
                # 自動模式：使用空列表，讓 SAM3 自動生成
                prompts_list = []
            else:
                # 其他模式：使用默認提示
                prompts_list = ["object"]
        
        print(f"Segmentation request - prompt_type: {prompt_type}, prompts: {prompts_list}, auto_generate: {auto_generate_bool}")
        
        # 載入模型
        model, model_key = SAM3Service.load_model(
            checkpoint_path=checkpoint_path,
            device=device if device == "cuda" and torch.cuda.is_available() else "cpu"
        )
        
        # 處理每個提示詞
        all_masks_list = []
        for prompt in prompts_list:
            # 檢測對象
            detections, _ = SAM3Service.detect_objects_in_image(
                image=img,
                prompt=prompt,
                model_key=model_key,
                device=device,
                confidence_threshold=confidence_threshold_float
            )
            
            # 轉換為回應格式
            for i in range(len(detections)):
                mask_dict = {
                    "bbox": detections.xyxy[i].tolist(),
                    "area": float(detections.area[i]) if detections.area is not None else 0.0,
                    "confidence": float(detections.confidence[i]) if detections.confidence is not None else 0.0,
                    "prompt": prompt,
                }
                if detections.mask is not None:
                    # 將遮罩編碼為 base64
                    mask_bool = detections.mask[i]
                    mask_uint8 = (mask_bool * 255).astype(np.uint8)
                    _, buffer = cv2.imencode('.png', mask_uint8)
                    mask_base64 = base64.b64encode(buffer).decode('utf-8')
                    mask_dict["segmentation"] = mask_base64
                all_masks_list.append(mask_dict)
        
        processing_time = time.time() - start_time
        
        return SegmentationResponse(
            success=True,
            masks=all_masks_list,
            image_url=None,
            processing_time=processing_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"處理錯誤: {str(e)}")

