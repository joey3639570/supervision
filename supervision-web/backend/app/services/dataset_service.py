"""
資料集服務
處理資料集格式轉換和分割
"""
import supervision as sv
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import tempfile
import shutil
import zipfile


class DatasetService:
    """資料集服務類別"""
    
    @staticmethod
    def convert_dataset_format(
        source_format: str,
        target_format: str,
        source_path: Path,
        target_path: Path,
        images_dir: Optional[Path] = None,
        annotations_file: Optional[Path] = None
    ) -> Dict:
        """
        轉換資料集格式
        
        Args:
            source_format: 來源格式 (coco, yolo, pascal_voc)
            target_format: 目標格式 (coco, yolo, pascal_voc)
            source_path: 來源資料集路徑
            target_path: 目標資料集路徑
            images_dir: 圖片目錄（可選）
            annotations_file: 註釋檔案（可選）
        
        Returns:
            轉換結果字典
        """
        try:
            # 讀取來源資料集
            if source_format == "coco":
                dataset = sv.DetectionDataset.from_coco(
                    images_directory_path=str(source_path),
                    annotations_path=str(annotations_file) if annotations_file else None
                )
            elif source_format == "yolo":
                dataset = sv.DetectionDataset.from_yolo(
                    images_directory_path=str(source_path),
                    annotations_directory_path=str(annotations_file) if annotations_file else None
                )
            elif source_format == "pascal_voc":
                dataset = sv.DetectionDataset.from_pascal_voc(
                    images_directory_path=str(source_path),
                    annotations_directory_path=str(annotations_file) if annotations_file else None
                )
            else:
                raise ValueError(f"不支援的來源格式: {source_format}")
            
            # 創建目標目錄
            target_path.mkdir(parents=True, exist_ok=True)
            
            # 儲存為目標格式
            if target_format == "coco":
                dataset.as_coco(
                    images_directory_path=str(target_path / "images"),
                    annotations_path=str(target_path / "annotations.json")
                )
            elif target_format == "yolo":
                dataset.as_yolo(
                    images_directory_path=str(target_path / "images"),
                    annotations_directory_path=str(target_path / "labels")
                )
            elif target_format == "pascal_voc":
                dataset.as_pascal_voc(
                    images_directory_path=str(target_path / "images"),
                    annotations_directory_path=str(target_path / "annotations")
                )
            else:
                raise ValueError(f"不支援的目標格式: {target_format}")
            
            return {
                "success": True,
                "message": f"資料集已從 {source_format} 轉換為 {target_format}",
                "target_path": str(target_path),
                "num_images": len(dataset)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def split_dataset(
        dataset_path: Path,
        train_ratio: float,
        test_ratio: float,
        output_path: Path,
        dataset_format: str = "yolo"
    ) -> Dict:
        """
        分割資料集
        
        Args:
            dataset_path: 資料集路徑
            train_ratio: 訓練集比例
            test_ratio: 測試集比例
            output_path: 輸出路徑
            dataset_format: 資料集格式
        
        Returns:
            分割結果字典
        """
        try:
            # 讀取資料集
            if dataset_format == "coco":
                dataset = sv.DetectionDataset.from_coco(
                    images_directory_path=str(dataset_path),
                    annotations_path=str(dataset_path / "annotations.json")
                )
            elif dataset_format == "yolo":
                dataset = sv.DetectionDataset.from_yolo(
                    images_directory_path=str(dataset_path / "images"),
                    annotations_directory_path=str(dataset_path / "labels")
                )
            elif dataset_format == "pascal_voc":
                dataset = sv.DetectionDataset.from_pascal_voc(
                    images_directory_path=str(dataset_path / "images"),
                    annotations_directory_path=str(dataset_path / "annotations")
                )
            else:
                raise ValueError(f"不支援的資料集格式: {dataset_format}")
            
            # 分割資料集
            train_dataset, remaining_dataset = dataset.split(split_ratio=train_ratio)
            val_ratio = test_ratio / (1 - train_ratio)
            test_dataset, val_dataset = remaining_dataset.split(split_ratio=val_ratio)
            
            # 創建輸出目錄
            train_path = output_path / "train"
            val_path = output_path / "val"
            test_path = output_path / "test"
            
            # 儲存分割後的資料集
            if dataset_format == "coco":
                train_dataset.as_coco(
                    images_directory_path=str(train_path / "images"),
                    annotations_path=str(train_path / "annotations.json")
                )
                val_dataset.as_coco(
                    images_directory_path=str(val_path / "images"),
                    annotations_path=str(val_path / "annotations.json")
                )
                test_dataset.as_coco(
                    images_directory_path=str(test_path / "images"),
                    annotations_path=str(test_path / "annotations.json")
                )
            elif dataset_format == "yolo":
                train_dataset.as_yolo(
                    images_directory_path=str(train_path / "images"),
                    annotations_directory_path=str(train_path / "labels")
                )
                val_dataset.as_yolo(
                    images_directory_path=str(val_path / "images"),
                    annotations_directory_path=str(val_path / "labels")
                )
                test_dataset.as_yolo(
                    images_directory_path=str(test_path / "images"),
                    annotations_directory_path=str(test_path / "labels")
                )
            elif dataset_format == "pascal_voc":
                train_dataset.as_pascal_voc(
                    images_directory_path=str(train_path / "images"),
                    annotations_directory_path=str(train_path / "annotations")
                )
                val_dataset.as_pascal_voc(
                    images_directory_path=str(val_path / "images"),
                    annotations_directory_path=str(val_path / "annotations")
                )
                test_dataset.as_pascal_voc(
                    images_directory_path=str(test_path / "images"),
                    annotations_directory_path=str(test_path / "annotations")
                )
            
            return {
                "success": True,
                "message": "資料集分割完成",
                "train_size": len(train_dataset),
                "val_size": len(val_dataset),
                "test_size": len(test_dataset),
                "output_path": str(output_path)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

