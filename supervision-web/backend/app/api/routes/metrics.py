"""評估指標 API 路由"""
from fastapi import APIRouter, HTTPException
from app.models.schemas import MetricRequest, MetricResponse, Detection
import supervision as sv
import numpy as np
from typing import List

router = APIRouter()


def detections_list_to_supervision_detections(detections_list: List[Detection]) -> sv.Detections:
    """將檢測列表轉換為 Supervision Detections 物件"""
    if not detections_list:
        return sv.Detections.empty()
    
    xyxy_list = []
    confidence_list = []
    class_id_list = []
    
    for det in detections_list:
        xyxy_list.append(det.xyxy)
        if det.confidence is not None:
            confidence_list.append(det.confidence)
        if det.class_id is not None:
            class_id_list.append(det.class_id)
    
    detections_dict = {
        "xyxy": np.array(xyxy_list, dtype=np.float32),
    }
    
    if confidence_list:
        detections_dict["confidence"] = np.array(confidence_list, dtype=np.float32)
    
    if class_id_list:
        detections_dict["class_id"] = np.array(class_id_list, dtype=np.int64)
    
    return sv.Detections(**detections_dict)


@router.post("/metrics/calculate", response_model=MetricResponse)
async def calculate_metrics(request: MetricRequest):
    """
    計算評估指標
    
    - **metric_type**: 指標類型 (mAP, precision, recall, f1, confusion_matrix)
    - **ground_truth**: 真實標籤
    - **predictions**: 預測結果
    - **iou_threshold**: IoU 閾值
    """
    try:
        # 轉換為 Detections 格式
        ground_truth_detections = detections_list_to_supervision_detections(request.ground_truth)
        predictions_detections = detections_list_to_supervision_detections(request.predictions)
        
        value = 0.0
        details = None
        
        if request.metric_type == "mAP":
            # Mean Average Precision
            metric = sv.MeanAveragePrecision(
                iou_thresholds=np.arange(0.5, 1.0, 0.05)
            )
            metric.update(predictions_detections, ground_truth_detections)
            value = metric.compute()['map50']
            details = {
                "map50": metric.compute()['map50'],
                "map50_95": metric.compute()['map50_95'] if 'map50_95' in metric.compute() else None
            }
            
        elif request.metric_type == "precision":
            # Precision
            metric = sv.Precision()
            metric.update(predictions_detections, ground_truth_detections)
            value = float(metric.compute())
            
        elif request.metric_type == "recall":
            # Recall
            metric = sv.Recall()
            metric.update(predictions_detections, ground_truth_detections)
            value = float(metric.compute())
            
        elif request.metric_type == "f1":
            # F1 Score
            metric = sv.F1Score()
            metric.update(predictions_detections, ground_truth_detections)
            value = float(metric.compute())
            
        elif request.metric_type == "confusion_matrix":
            # Confusion Matrix
            metric = sv.ConfusionMatrix()
            metric.update(predictions_detections, ground_truth_detections)
            matrix = metric.compute()
            value = 0.0  # Confusion matrix 沒有單一數值
            details = {
                "matrix": matrix.tolist() if hasattr(matrix, 'tolist') else matrix,
                "classes": list(range(len(matrix))) if hasattr(matrix, '__len__') else []
            }
            
        else:
            raise HTTPException(status_code=400, detail=f"不支援的指標類型: {request.metric_type}")
        
        return MetricResponse(
            success=True,
            metric_type=request.metric_type,
            value=value,
            details=details
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"計算錯誤: {str(e)}")



