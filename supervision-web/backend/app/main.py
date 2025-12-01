"""
Supervision Web Application - FastAPI Backend
提供完整的 Supervision 功能 API
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.api.routes import (
    detect,
    segment,
    track,
    annotate,
    models,
    dataset,
    metrics,
    geometry,
    video,
    utils
)

app = FastAPI(
    title="Supervision Web API",
    description="完整的 Supervision 電腦視覺工具庫 Web API",
    version="0.1.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生產環境應限制特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 靜態檔案服務（用於儲存處理後的圖片和影片）
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# 註冊路由
app.include_router(detect.router, prefix="/api/v1", tags=["Detection"])
app.include_router(segment.router, prefix="/api/v1", tags=["Segmentation"])
app.include_router(track.router, prefix="/api/v1", tags=["Tracking"])
app.include_router(annotate.router, prefix="/api/v1", tags=["Annotation"])
app.include_router(models.router, prefix="/api/v1", tags=["Models"])
app.include_router(dataset.router, prefix="/api/v1", tags=["Dataset"])
app.include_router(metrics.router, prefix="/api/v1", tags=["Metrics"])
app.include_router(geometry.router, prefix="/api/v1", tags=["Geometry"])
app.include_router(video.router, prefix="/api/v1", tags=["Video"])
app.include_router(utils.router, prefix="/api/v1", tags=["Utils"])


@app.get("/")
async def root():
    """API 根端點"""
    return {
        "message": "Supervision Web API",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {"status": "healthy"}


