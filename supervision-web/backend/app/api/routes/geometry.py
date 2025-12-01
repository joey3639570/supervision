"""幾何工具 API 路由"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import supervision as sv
import numpy as np

router = APIRouter()


class ZoneRequest(BaseModel):
    """區域請求"""
    zone_type: str  # "polygon" or "line"
    coordinates: List[List[float]]
    triggering_position: str = "center"


class ZoneResponse(BaseModel):
    """區域回應"""
    success: bool
    zone_id: str
    in_count: int
    out_count: int
    current_objects: List[int]


@router.post("/geometry/zone", response_model=ZoneResponse)
async def create_zone(request: ZoneRequest):
    """
    創建區域（多邊形或線）
    
    - **zone_type**: 區域類型 (polygon, line)
    - **coordinates**: 座標列表
    - **triggering_position**: 觸發位置 (center, top_left, etc.)
    """
    try:
        if request.zone_type == "polygon":
            polygon = np.array(request.coordinates)
            position = getattr(sv.Position, request.triggering_position.upper(), sv.Position.CENTER)
            zone = sv.PolygonZone(polygon=polygon, triggering_position=position)
        elif request.zone_type == "line":
            if len(request.coordinates) != 2:
                raise HTTPException(status_code=400, detail="線區域需要兩個點")
            start = sv.Point(*request.coordinates[0])
            end = sv.Point(*request.coordinates[1])
            zone = sv.LineZone(start=start, end=end)
        else:
            raise HTTPException(status_code=400, detail=f"不支援的區域類型: {request.zone_type}")
        
        # TODO: 儲存區域並返回 ID
        zone_id = "zone_123"  # 示例 ID
        
        return ZoneResponse(
            success=True,
            zone_id=zone_id,
            in_count=0,
            out_count=0,
            current_objects=[]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"處理錯誤: {str(e)}")



