"""
追蹤服務
處理影片物件追蹤
"""
import cv2
import numpy as np
import supervision as sv
from pathlib import Path
from typing import Dict, List, Optional
from tqdm import tqdm

from app.services.model_service import ModelService
from app.services.supervision_service import SupervisionService


class TrackingService:
    """追蹤服務類別"""
    
    @staticmethod
    def process_video_tracking(
        video_path: Path,
        output_path: Path,
        model_type: str = "yolov8",
        model_id: Optional[str] = None,
        tracker_type: str = "bytetrack",
        confidence_threshold: float = 0.25,
        iou_threshold: float = 0.45,
        progress_callback: Optional[callable] = None
    ) -> Dict:
        """
        處理影片追蹤
        
        Args:
            video_path: 輸入影片路徑
            output_path: 輸出影片路徑
            model_type: 模型類型
            model_id: 模型 ID
            tracker_type: 追蹤器類型
            confidence_threshold: 信心閾值
            iou_threshold: IoU 閾值
            progress_callback: 進度回調函數
        
        Returns:
            追蹤結果字典
        """
        # 載入模型
        model, _ = ModelService.load_model(
            model_type=model_type,
            model_id=model_id
        )
        
        # 創建追蹤器
        tracker = SupervisionService.create_tracker(tracker_type)
        
        # 創建標註器
        box_annotator = sv.BoxAnnotator()
        label_annotator = sv.LabelAnnotator()
        
        # 獲取影片資訊
        video_info = sv.VideoInfo.from_video_path(str(video_path))
        
        # 追蹤數據儲存
        tracks_data: Dict[int, List[Dict]] = {}
        
        # 處理影片
        frame_generator = sv.get_video_frames_generator(source_path=str(video_path))
        
        with sv.VideoSink(target_path=str(output_path), video_info=video_info) as sink:
            for frame_idx, frame in enumerate(tqdm(frame_generator, total=video_info.total_frames)):
                # 執行檢測
                if model_type in ["yolov8", "yolov9", "yolov10"]:
                    results = model(frame, verbose=False, conf=confidence_threshold, iou=iou_threshold)[0]
                    detections = sv.Detections.from_ultralytics(results)
                else:
                    raise ValueError(f"不支援的模型類型: {model_type}")
                
                # 更新追蹤器
                detections = tracker.update_with_detections(detections)
                
                # 記錄追蹤數據
                if detections.tracker_id is not None:
                    for i, tracker_id in enumerate(detections.tracker_id):
                        if tracker_id not in tracks_data:
                            tracks_data[tracker_id] = []
                        tracks_data[tracker_id].append({
                            "frame": frame_idx,
                            "xyxy": detections.xyxy[i].tolist(),
                            "confidence": float(detections.confidence[i]) if detections.confidence is not None else None,
                            "class_id": int(detections.class_id[i]) if detections.class_id is not None else None
                        })
                
                # 標註幀
                annotated_frame = box_annotator.annotate(
                    scene=frame.copy(),
                    detections=detections
                )
                
                # 添加標籤
                if detections.tracker_id is not None:
                    labels = [f"#{tracker_id}" for tracker_id in detections.tracker_id]
                    annotated_frame = label_annotator.annotate(
                        scene=annotated_frame,
                        detections=detections,
                        labels=labels
                    )
                
                sink.write_frame(frame=annotated_frame)
                
                # 更新進度
                if progress_callback:
                    progress = int((frame_idx + 1) / video_info.total_frames * 100)
                    progress_callback(progress)
        
        # 轉換追蹤數據格式
        tracks = []
        for tracker_id, frames_data in tracks_data.items():
            tracks.append({
                "track_id": int(tracker_id),
                "frames": [data["frame"] for data in frames_data],
                "xyxy": [data["xyxy"] for data in frames_data],
                "total_frames": len(frames_data)
            })
        
        return {
            "tracks": tracks,
            "total_tracks": len(tracks),
            "total_frames": video_info.total_frames
        }

