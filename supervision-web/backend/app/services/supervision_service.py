"""
Supervision 整合服務
提供統一的 Supervision 功能接口
"""
import supervision as sv
import numpy as np
from typing import List, Dict, Any, Optional
import cv2


class SupervisionService:
    """Supervision 服務類別"""
    
    @staticmethod
    def create_detections_from_model(
        model_type: str,
        model_result: Any,
        model_names: Optional[Dict[int, str]] = None
    ) -> sv.Detections:
        """
        從不同模型結果創建 Detections 物件
        
        Args:
            model_type: 模型類型
            model_result: 模型推理結果
            model_names: 類別名稱映射
            
        Returns:
            Detections 物件
        """
        if model_type in ["yolov8", "yolov9", "yolov10"]:
            detections = sv.Detections.from_ultralytics(model_result)
        elif model_type == "yolov5":
            detections = sv.Detections.from_yolov5(model_result)
        elif model_type == "yolonas":
            detections = sv.Detections.from_yolo_nas(model_result)
        elif model_type == "sam":
            detections = sv.Detections.from_sam(model_result)
        elif model_type == "sam3":
            detections = sv.Detections.from_sam3(model_result)
        elif model_type == "transformers":
            detections = sv.Detections.from_transformers(
                model_result, 
                id2label=model_names
            )
        elif model_type == "mmdetection":
            detections = sv.Detections.from_mmdetection(model_result)
        elif model_type == "detectron2":
            detections = sv.Detections.from_detectron2(model_result)
        else:
            raise ValueError(f"不支援的模型類型: {model_type}")
        
        return detections
    
    @staticmethod
    def apply_nms(
        detections: sv.Detections,
        threshold: float = 0.5,
        class_agnostic: bool = False
    ) -> sv.Detections:
        """應用非極大值抑制"""
        return detections.with_nms(
            threshold=threshold,
            class_agnostic=class_agnostic
        )
    
    @staticmethod
    def apply_nmm(
        detections: sv.Detections,
        threshold: float = 0.5,
        class_agnostic: bool = False
    ) -> sv.Detections:
        """應用非極大值合併"""
        return detections.with_nmm(
            threshold=threshold,
            class_agnostic=class_agnostic
        )
    
    @staticmethod
    def filter_by_confidence(
        detections: sv.Detections,
        threshold: float
    ) -> sv.Detections:
        """按信心分數過濾"""
        if detections.confidence is None:
            return detections
        mask = detections.confidence >= threshold
        return detections[mask]
    
    @staticmethod
    def filter_by_class(
        detections: sv.Detections,
        class_ids: List[int]
    ) -> sv.Detections:
        """按類別過濾"""
        if detections.class_id is None:
            return detections
        mask = np.isin(detections.class_id, class_ids)
        return detections[mask]
    
    @staticmethod
    def create_annotator(annotator_type: str, **kwargs) -> Any:
        """
        創建標註器
        
        Args:
            annotator_type: 標註器類型
            **kwargs: 標註器參數
            
        Returns:
            標註器實例
        """
        annotator_map = {
            "box": sv.BoxAnnotator,
            "round_box": sv.RoundBoxAnnotator,
            "box_corner": sv.BoxCornerAnnotator,
            "oriented_box": sv.OrientedBoxAnnotator,
            "mask": sv.MaskAnnotator,
            "polygon": sv.PolygonAnnotator,
            "label": sv.LabelAnnotator,
            "rich_label": sv.RichLabelAnnotator,
            "color": sv.ColorAnnotator,
            "blur": sv.BlurAnnotator,
            "pixelate": sv.PixelateAnnotator,
            "circle": sv.CircleAnnotator,
            "ellipse": sv.EllipseAnnotator,
            "dot": sv.DotAnnotator,
            "heatmap": sv.HeatMapAnnotator,
            "trace": sv.TraceAnnotator,
        }
        
        if annotator_type not in annotator_map:
            raise ValueError(f"不支援的標註器類型: {annotator_type}")
        
        annotator_class = annotator_map[annotator_type]
        return annotator_class(**kwargs)
    
    @staticmethod
    def annotate_image(
        image: np.ndarray,
        detections: sv.Detections,
        annotator_type: str = "box",
        labels: Optional[List[str]] = None,
        **annotator_kwargs
    ) -> np.ndarray:
        """
        標註圖片
        
        Args:
            image: 輸入圖片
            detections: 檢測結果
            annotator_type: 標註器類型
            labels: 標籤列表
            **annotator_kwargs: 標註器參數
            
        Returns:
            標註後的圖片
        """
        annotator = SupervisionService.create_annotator(
            annotator_type,
            **annotator_kwargs
        )
        
        annotated = annotator.annotate(
            scene=image.copy(),
            detections=detections
        )
        
        # 如果有標籤，添加標籤標註器
        if labels and annotator_type != "label" and annotator_type != "rich_label":
            label_annotator = sv.LabelAnnotator()
            annotated = label_annotator.annotate(
                scene=annotated,
                detections=detections,
                labels=labels
            )
        
        return annotated
    
    @staticmethod
    def create_polygon_zone(
        polygon: np.ndarray,
        triggering_position: sv.Position = sv.Position.CENTER
    ) -> sv.PolygonZone:
        """創建多邊形區域"""
        return sv.PolygonZone(
            polygon=polygon,
            triggering_position=triggering_position
        )
    
    @staticmethod
    def create_line_zone(
        start: sv.Point,
        end: sv.Point
    ) -> sv.LineZone:
        """創建線區域"""
        return sv.LineZone(start=start, end=end)
    
    @staticmethod
    def create_tracker(
        tracker_type: str = "bytetrack",
        **kwargs
    ) -> Any:
        """創建追蹤器"""
        if tracker_type == "bytetrack":
            return sv.ByteTrack(**kwargs)
        else:
            raise ValueError(f"不支援的追蹤器類型: {tracker_type}")


