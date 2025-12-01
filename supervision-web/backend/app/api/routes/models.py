"""模型管理 API 路由"""
from fastapi import APIRouter
from app.models.schemas import ModelsResponse, ModelInfo

router = APIRouter()


@router.get("/models", response_model=ModelsResponse)
async def get_models():
    """獲取可用模型列表"""
    models = [
        ModelInfo(
            id="yolov8n",
            name="YOLOv8 Nano",
            type="detection",
            supported_formats=["image", "video"],
            description="輕量級檢測模型，速度快"
        ),
        ModelInfo(
            id="yolov8s",
            name="YOLOv8 Small",
            type="detection",
            supported_formats=["image", "video"],
            description="小型檢測模型，平衡速度和精度"
        ),
        ModelInfo(
            id="yolov8m",
            name="YOLOv8 Medium",
            type="detection",
            supported_formats=["image", "video"],
            description="中型檢測模型，高精度"
        ),
        ModelInfo(
            id="sam3",
            name="Segment Anything Model 3",
            type="segmentation",
            supported_formats=["image"],
            description="最新的分割模型，支援概念提示"
        ),
        ModelInfo(
            id="sam",
            name="Segment Anything Model",
            type="segmentation",
            supported_formats=["image"],
            description="Meta 的分割模型"
        ),
    ]
    
    return ModelsResponse(success=True, models=models)


