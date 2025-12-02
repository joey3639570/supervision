"""
模型服務
統一管理模型載入、快取和推理
"""
import os
from typing import Dict, Optional, Any, Tuple
from pathlib import Path
import torch

# 嘗試導入不同的模型框架
try:
    from ultralytics import YOLO
    ULTRALYTICS_AVAILABLE = True
except ImportError:
    ULTRALYTICS_AVAILABLE = False
    YOLO = None

try:
    import ultralytics
    YOLOV5_AVAILABLE = hasattr(ultralytics, 'YOLOv5')
except:
    YOLOV5_AVAILABLE = False

try:
    from super_gradients.training import models as sg_models
    YOLONAS_AVAILABLE = True
except ImportError:
    YOLONAS_AVAILABLE = False
    sg_models = None


class ModelService:
    """模型服務類別 - 統一管理模型載入和快取"""
    
    _model_cache: Dict[str, Any] = {}
    _device_cache: Optional[str] = None
    
    @staticmethod
    def get_device() -> str:
        """獲取可用設備"""
        if ModelService._device_cache is not None:
            return ModelService._device_cache
        
        if torch.cuda.is_available():
            device = "cuda"
        else:
            device = "cpu"
        
        ModelService._device_cache = device
        return device
    
    @staticmethod
    def _get_model_key(model_type: str, model_id: Optional[str] = None) -> str:
        """生成模型快取鍵"""
        if model_id:
            return f"{model_type}_{model_id}"
        return model_type
    
    @staticmethod
    def load_yolo_model(
        model_type: str,
        model_id: Optional[str] = None,
        device: Optional[str] = None
    ) -> Tuple[Any, str]:
        """
        載入 YOLO 模型
        
        Args:
            model_type: 模型類型 (yolov8, yolov5, yolonas)
            model_id: 模型 ID 或路徑（可選）
            device: 設備（可選）
        
        Returns:
            (模型實例, 模型鍵)
        """
        if not ULTRALYTICS_AVAILABLE:
            raise RuntimeError(
                "Ultralytics YOLO 未安裝。請執行: pip install ultralytics"
            )
        
        if device is None:
            device = ModelService.get_device()
        
        # 根據模型類型確定預設模型 ID
        if model_id is None:
            if model_type == "yolov8":
                model_id = "yolov8n.pt"  # 預設使用 nano 版本
            elif model_type == "yolov9":
                model_id = "yolov9t.pt"
            elif model_type == "yolov10":
                model_id = "yolov10n.pt"
            else:
                model_id = "yolov8n.pt"
        
        model_key = ModelService._get_model_key(model_type, model_id)
        
        # 檢查快取
        if model_key in ModelService._model_cache:
            return ModelService._model_cache[model_key], model_key
        
        # 載入模型
        print(f"載入 {model_type} 模型: {model_id} (設備: {device})")
        try:
            model = YOLO(model_id)
            model.to(device)
            ModelService._model_cache[model_key] = model
            return model, model_key
        except Exception as e:
            raise RuntimeError(f"載入模型失敗 {model_id}: {str(e)}")
    
    @staticmethod
    def load_yolo_nas_model(
        model_id: Optional[str] = None,
        device: Optional[str] = None
    ) -> Tuple[Any, str]:
        """
        載入 YOLO-NAS 模型
        
        Args:
            model_id: 模型 ID（可選，預設: yolo_nas_s）
            device: 設備（可選）
        
        Returns:
            (模型實例, 模型鍵)
        """
        if not YOLONAS_AVAILABLE:
            raise RuntimeError(
                "YOLO-NAS 未安裝。請執行: pip install super-gradients"
            )
        
        if device is None:
            device = ModelService.get_device()
        
        if model_id is None:
            model_id = "yolo_nas_s"
        
        model_key = ModelService._get_model_key("yolonas", model_id)
        
        # 檢查快取
        if model_key in ModelService._model_cache:
            return ModelService._model_cache[model_key], model_key
        
        # 載入模型
        print(f"載入 YOLO-NAS 模型: {model_id} (設備: {device})")
        try:
            model = sg_models.get(model_id, pretrained_weights="coco")
            model.to(device)
            ModelService._model_cache[model_key] = model
            return model, model_key
        except Exception as e:
            raise RuntimeError(f"載入 YOLO-NAS 模型失敗 {model_id}: {str(e)}")
    
    @staticmethod
    def load_model(
        model_type: str,
        model_id: Optional[str] = None,
        device: Optional[str] = None
    ) -> Tuple[Any, str]:
        """
        載入模型（統一接口）
        
        Args:
            model_type: 模型類型
            model_id: 模型 ID 或路徑（可選）
            device: 設備（可選）
        
        Returns:
            (模型實例, 模型鍵)
        """
        if model_type in ["yolov8", "yolov9", "yolov10"]:
            return ModelService.load_yolo_model(model_type, model_id, device)
        elif model_type == "yolonas":
            return ModelService.load_yolo_nas_model(model_id, device)
        else:
            raise ValueError(f"不支援的模型類型: {model_type}")
    
    @staticmethod
    def clear_cache():
        """清除模型快取"""
        ModelService._model_cache.clear()
        print("模型快取已清除")
    
    @staticmethod
    def get_cached_models() -> Dict[str, Any]:
        """獲取快取的模型列表"""
        return {
            key: type(model).__name__ 
            for key, model in ModelService._model_cache.items()
        }

