"""資料集管理 API 路由"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Optional

router = APIRouter()


@router.post("/dataset/convert")
async def convert_dataset(
    source_format: str,
    target_format: str,
    files: list[UploadFile] = File(...)
):
    """
    轉換資料集格式
    
    - **source_format**: 來源格式 (coco, yolo, pascal_voc)
    - **target_format**: 目標格式 (coco, yolo, pascal_voc)
    - **files**: 資料集檔案
    """
    # TODO: 實作資料集轉換邏輯
    return {"success": True, "message": "資料集轉換功能開發中"}


@router.post("/dataset/split")
async def split_dataset(
    train_ratio: float,
    test_ratio: float,
    files: list[UploadFile] = File(...)
):
    """
    分割資料集
    
    - **train_ratio**: 訓練集比例
    - **test_ratio**: 測試集比例
    - **files**: 資料集檔案
    """
    # TODO: 實作資料集分割邏輯
    return {"success": True, "message": "資料集分割功能開發中"}


