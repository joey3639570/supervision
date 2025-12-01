"""工具 API 路由"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import numpy as np

router = APIRouter()


class ConvertRequest(BaseModel):
    """轉換請求"""
    source_format: str
    target_format: str
    coordinates: List[float]
    image_width: Optional[int] = None
    image_height: Optional[int] = None


class ConvertResponse(BaseModel):
    """轉換回應"""
    success: bool
    coordinates: List[float]
    source_format: str
    target_format: str


def xywh_to_xyxy(xywh: np.ndarray) -> np.ndarray:
    """將 xywh 格式轉換為 xyxy 格式"""
    if len(xywh) == 4:
        x, y, w, h = xywh
        return np.array([x, y, x + w, y + h])
    return xywh


def xyxy_to_xywh(xyxy: np.ndarray) -> np.ndarray:
    """將 xyxy 格式轉換為 xywh 格式"""
    if len(xyxy) == 4:
        x1, y1, x2, y2 = xyxy
        return np.array([x1, y1, x2 - x1, y2 - y1])
    return xyxy


def xyxy_to_xcycwh(xyxy: np.ndarray) -> np.ndarray:
    """將 xyxy 格式轉換為 xcycwh (中心點) 格式"""
    if len(xyxy) == 4:
        x1, y1, x2, y2 = xyxy
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        w = x2 - x1
        h = y2 - y1
        return np.array([cx, cy, w, h])
    return xyxy


def xcycwh_to_xyxy(xcycwh: np.ndarray) -> np.ndarray:
    """將 xcycwh (中心點) 格式轉換為 xyxy 格式"""
    if len(xcycwh) == 4:
        cx, cy, w, h = xcycwh
        x1 = cx - w / 2
        y1 = cy - h / 2
        x2 = cx + w / 2
        y2 = cy + h / 2
        return np.array([x1, y1, x2, y2])
    return xcycwh


def normalize_coordinates(coords: np.ndarray, width: int, height: int) -> np.ndarray:
    """正規化座標到 [0, 1] 範圍"""
    if len(coords) == 4:
        return np.array([
            coords[0] / width,
            coords[1] / height,
            coords[2] / width,
            coords[3] / height
        ])
    return coords


def denormalize_coordinates(coords: np.ndarray, width: int, height: int) -> np.ndarray:
    """將正規化座標轉換回像素座標"""
    if len(coords) == 4:
        return np.array([
            coords[0] * width,
            coords[1] * height,
            coords[2] * width,
            coords[3] * height
        ])
    return coords


@router.post("/utils/convert", response_model=ConvertResponse)
async def convert_coordinates(request: ConvertRequest):
    """
    轉換座標格式
    
    支援的格式:
    - **xyxy**: [x1, y1, x2, y2] 左上角和右下角座標
    - **xywh**: [x, y, width, height] 左上角座標和寬高
    - **xcycwh**: [center_x, center_y, width, height] 中心點座標和寬高
    - **normalized**: 正規化座標 (需要提供 image_width 和 image_height)
    """
    try:
        coords = np.array(request.coordinates)
        source = request.source_format.lower()
        target = request.target_format.lower()
        
        # 首先轉換為 xyxy 格式（作為中間格式）
        if source == "xyxy":
            xyxy = coords
        elif source == "xywh":
            xyxy = xywh_to_xyxy(coords)
        elif source == "xcycwh":
            xyxy = xcycwh_to_xyxy(coords)
        elif source == "normalized":
            if not request.image_width or not request.image_height:
                raise HTTPException(
                    status_code=400, 
                    detail="正規化座標需要提供 image_width 和 image_height"
                )
            xyxy = denormalize_coordinates(coords, request.image_width, request.image_height)
        else:
            raise HTTPException(status_code=400, detail=f"不支援的來源格式: {source}")
        
        # 然後從 xyxy 轉換為目標格式
        if target == "xyxy":
            result = xyxy
        elif target == "xywh":
            result = xyxy_to_xywh(xyxy)
        elif target == "xcycwh":
            result = xyxy_to_xcycwh(xyxy)
        elif target == "normalized":
            if not request.image_width or not request.image_height:
                raise HTTPException(
                    status_code=400, 
                    detail="正規化座標需要提供 image_width 和 image_height"
                )
            result = normalize_coordinates(xyxy, request.image_width, request.image_height)
        else:
            raise HTTPException(status_code=400, detail=f"不支援的目標格式: {target}")
        
        return ConvertResponse(
            success=True,
            coordinates=result.tolist(),
            source_format=source,
            target_format=target
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"轉換錯誤: {str(e)}")


class IouRequest(BaseModel):
    """IoU 計算請求"""
    box1: List[float]
    box2: List[float]
    format: str = "xyxy"


@router.post("/utils/iou")
async def calculate_iou(request: IouRequest):
    """
    計算兩個邊界框的 IoU (Intersection over Union)
    """
    try:
        box1 = np.array(request.box1)
        box2 = np.array(request.box2)
        
        # 轉換為 xyxy 格式
        if request.format.lower() == "xywh":
            box1 = xywh_to_xyxy(box1)
            box2 = xywh_to_xyxy(box2)
        elif request.format.lower() == "xcycwh":
            box1 = xcycwh_to_xyxy(box1)
            box2 = xcycwh_to_xyxy(box2)
        
        # 計算交集
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])
        
        intersection = max(0, x2 - x1) * max(0, y2 - y1)
        
        # 計算並集
        area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
        area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
        union = area1 + area2 - intersection
        
        iou = intersection / union if union > 0 else 0
        
        return {
            "success": True,
            "iou": float(iou),
            "intersection": float(intersection),
            "union": float(union)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"計算錯誤: {str(e)}")


class AreaRequest(BaseModel):
    """面積計算請求"""
    coordinates: List[float]
    format: str = "xyxy"


@router.post("/utils/area")
async def calculate_area(request: AreaRequest):
    """
    計算邊界框面積
    """
    try:
        coords = np.array(request.coordinates)
        
        # 轉換為 xyxy 格式
        if request.format.lower() == "xywh":
            xyxy = xywh_to_xyxy(coords)
        elif request.format.lower() == "xcycwh":
            xyxy = xcycwh_to_xyxy(coords)
        else:
            xyxy = coords
        
        width = xyxy[2] - xyxy[0]
        height = xyxy[3] - xyxy[1]
        area = width * height
        
        return {
            "success": True,
            "area": float(area),
            "width": float(width),
            "height": float(height)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"計算錯誤: {str(e)}")
