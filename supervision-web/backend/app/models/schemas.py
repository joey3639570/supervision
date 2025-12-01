"""Pydantic 模型定義"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class ModelType(str, Enum):
    """模型類型枚舉"""
    YOLOV8 = "yolov8"
    YOLOV5 = "yolov5"
    YOLONAS = "yolonas"
    SAM = "sam"
    SAM2 = "sam2"
    SAM3 = "sam3"
    TRANSFORMERS = "transformers"
    MMDETECTION = "mmdetection"
    DETECTRON2 = "detectron2"


class AnnotatorType(str, Enum):
    """標註器類型枚舉"""
    BOX = "box"
    ROUND_BOX = "round_box"
    BOX_CORNER = "box_corner"
    ORIENTED_BOX = "oriented_box"
    MASK = "mask"
    POLYGON = "polygon"
    LABEL = "label"
    RICH_LABEL = "rich_label"
    COLOR = "color"
    BLUR = "blur"
    PIXELATE = "pixelate"
    CIRCLE = "circle"
    ELLIPSE = "ellipse"
    DOT = "dot"
    HEATMAP = "heatmap"
    TRACE = "trace"


class DetectionRequest(BaseModel):
    """檢測請求模型"""
    model_type: ModelType = Field(default=ModelType.YOLOV8, description="模型類型")
    model_id: Optional[str] = Field(default=None, description="特定模型 ID")
    confidence_threshold: float = Field(default=0.25, ge=0.0, le=1.0, description="信心閾值")
    iou_threshold: float = Field(default=0.45, ge=0.0, le=1.0, description="IoU 閾值")
    classes: Optional[List[int]] = Field(default=None, description="要檢測的類別 ID 列表")


class SegmentationRequest(BaseModel):
    """分割請求模型"""
    prompts: Optional[List[str]] = Field(default=None, description="SAM3 提示詞列表")
    prompt_type: str = Field(default="text", description="提示類型: text, point, box")
    auto_generate: bool = Field(default=False, description="是否自動生成遮罩")


class TrackingRequest(BaseModel):
    """追蹤請求模型"""
    model_type: ModelType = Field(default=ModelType.YOLOV8, description="模型類型")
    tracker_type: str = Field(default="bytetrack", description="追蹤器類型")
    confidence_threshold: float = Field(default=0.25, ge=0.0, le=1.0)
    iou_threshold: float = Field(default=0.45, ge=0.0, le=1.0)


class AnnotationRequest(BaseModel):
    """標註請求模型"""
    annotator_type: AnnotatorType = Field(default=AnnotatorType.BOX, description="標註器類型")
    options: Optional[Dict[str, Any]] = Field(default=None, description="標註選項")


class BoundingBox(BaseModel):
    """邊界框模型"""
    x1: float
    y1: float
    x2: float
    y2: float


class Detection(BaseModel):
    """檢測結果模型"""
    xyxy: List[float]  # [x1, y1, x2, y2]
    confidence: Optional[float] = None
    class_id: Optional[int] = None
    class_name: Optional[str] = None
    tracker_id: Optional[int] = None


class DetectionResponse(BaseModel):
    """檢測回應模型"""
    success: bool
    detections: List[Detection]
    image_url: Optional[str] = None
    processing_time: float


class SegmentationResponse(BaseModel):
    """分割回應模型"""
    success: bool
    masks: List[Dict[str, Any]]
    image_url: Optional[str] = None
    processing_time: float


class TrackingTaskResponse(BaseModel):
    """追蹤任務回應模型"""
    success: bool
    task_id: str
    status: str
    estimated_time: Optional[int] = None


class TrackingStatusResponse(BaseModel):
    """追蹤狀態回應模型"""
    success: bool
    status: str
    progress: int
    video_url: Optional[str] = None
    tracks: Optional[List[Dict[str, Any]]] = None


class ModelInfo(BaseModel):
    """模型資訊模型"""
    id: str
    name: str
    type: str
    supported_formats: List[str]
    description: Optional[str] = None


class ModelsResponse(BaseModel):
    """模型列表回應模型"""
    success: bool
    models: List[ModelInfo]


class ZoneRequest(BaseModel):
    """區域請求模型"""
    zone_type: str = Field(description="區域類型: polygon, line")
    coordinates: List[List[float]] = Field(description="區域座標")
    trigger_condition: Optional[str] = Field(default="enter", description="觸發條件: enter, exit, both")


class ZoneResponse(BaseModel):
    """區域回應模型"""
    success: bool
    zone_id: str
    in_count: int
    out_count: int
    current_objects: List[int]


class MetricRequest(BaseModel):
    """評估指標請求模型"""
    metric_type: str = Field(description="指標類型: mAP, precision, recall, f1, confusion_matrix")
    ground_truth: List[Detection]
    predictions: List[Detection]
    iou_threshold: float = Field(default=0.5, ge=0.0, le=1.0)


class MetricResponse(BaseModel):
    """評估指標回應模型"""
    success: bool
    metric_type: str
    value: float
    details: Optional[Dict[str, Any]] = None


