# Supervision Web Application Architecture

本文檔描述 Supervision 網頁應用程式的架構設計，使用 Vue.js 作為前端框架。

## 專案結構

```
supervision-web/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI 應用程式入口
│   │   ├── config.py               # 配置設定
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── routes/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── detect.py       # 檢測端點
│   │   │   │   ├── segment.py     # 分割端點 (SAM3)
│   │   │   │   ├── track.py        # 追蹤端點
│   │   │   │   ├── annotate.py     # 標註端點
│   │   │   │   └── models.py       # 模型管理端點
│   │   │   └── dependencies.py    # API 依賴項
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── detection_service.py    # 檢測服務
│   │   │   ├── segmentation_service.py # 分割服務 (SAM3)
│   │   │   ├── tracking_service.py     # 追蹤服務
│   │   │   └── supervision_service.py  # Supervision 整合服務
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── schemas.py          # Pydantic 模型
│   │   │   └── responses.py        # 回應模型
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── file_handler.py     # 檔案處理工具
│   │       └── image_processor.py  # 影像處理工具
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── main.js                 # Vue 應用程式入口
│   │   ├── App.vue                 # 根組件
│   │   ├── router/
│   │   │   └── index.js            # Vue Router 配置
│   │   ├── stores/
│   │   │   ├── index.js            # Pinia store 入口
│   │   │   ├── detection.js        # 檢測狀態管理
│   │   │   └── ui.js               # UI 狀態管理
│   │   ├── services/
│   │   │   └── api.js              # API 服務層
│   │   ├── views/
│   │   │   ├── HomeView.vue        # 首頁
│   │   │   ├── DetectionView.vue   # 檢測頁面
│   │   │   ├── SegmentationView.vue # 分割頁面 (SAM3)
│   │   │   ├── TrackingView.vue    # 追蹤頁面
│   │   │   └── ResultsView.vue     # 結果展示頁面
│   │   ├── components/
│   │   │   ├── common/
│   │   │   │   ├── ImageUploader.vue    # 圖片上傳組件
│   │   │   │   ├── VideoUploader.vue    # 影片上傳組件
│   │   │   │   ├── ModelSelector.vue    # 模型選擇組件
│   │   │   │   └── LoadingSpinner.vue   # 載入動畫
│   │   │   ├── detection/
│   │   │   │   ├── DetectionCanvas.vue  # 檢測結果畫布
│   │   │   │   ├── BoundingBox.vue      # 邊界框組件
│   │   │   │   └── DetectionList.vue    # 檢測列表
│   │   │   ├── segmentation/
│   │   │   │   ├── SegmentationCanvas.vue # 分割結果畫布
│   │   │   │   ├── MaskOverlay.vue      # 遮罩疊加組件
│   │   │   │   └── PromptInput.vue      # SAM3 提示輸入
│   │   │   └── tracking/
│   │   │       ├── VideoPlayer.vue      # 影片播放器
│   │   │       ├── TrackingTimeline.vue  # 追蹤時間軸
│   │   │       └── TrackVisualization.vue # 追蹤視覺化
│   │   └── styles/
│   │       ├── main.css
│   │       └── variables.css
│   ├── package.json
│   ├── vite.config.js
│   ├── .env.example
│   └── Dockerfile
├── docker-compose.yml
├── README.md
└── .gitignore
```

## 後端 API 設計

### 技術棧

- **框架**: FastAPI
- **異步處理**: asyncio, BackgroundTasks
- **檔案處理**: python-multipart
- **影像處理**: OpenCV, PIL
- **模型整合**: Supervision, Ultralytics, SAM3

### API 端點規格

#### 1. 檢測端點

**POST /api/v1/detect**

上傳圖片進行物件檢測。

**請求:**
- Content-Type: multipart/form-data
- Body:
  - `image`: 圖片檔案 (required)
  - `model_type`: 模型類型 (optional, default: "yolov8")
  - `model_id`: 模型 ID (optional)
  - `confidence_threshold`: 信心閾值 (optional, default: 0.25)
  - `iou_threshold`: IoU 閾值 (optional, default: 0.45)

**回應:**
```json
{
  "success": true,
  "detections": {
    "xyxy": [[x1, y1, x2, y2], ...],
    "confidence": [0.95, 0.87, ...],
    "class_id": [0, 1, ...],
    "class_names": ["person", "car", ...]
  },
  "image_url": "/api/v1/files/processed_image_123.jpg",
  "processing_time": 0.234
}
```

#### 2. 分割端點 (SAM3)

**POST /api/v1/segment**

使用 SAM3 進行圖像分割。

**請求:**
- Content-Type: multipart/form-data
- Body:
  - `image`: 圖片檔案 (required)
  - `prompts`: 提示詞列表 (optional, JSON string)
  - `prompt_type`: 提示類型 (optional, "text" | "point" | "box")
  - `auto_generate`: 是否自動生成遮罩 (optional, default: false)

**回應:**
```json
{
  "success": true,
  "masks": [
    {
      "bbox": [x, y, width, height],
      "segmentation": "base64_encoded_mask",
      "area": 12345
    },
    ...
  ],
  "image_url": "/api/v1/files/segmented_image_123.jpg",
  "processing_time": 1.567
}
```

#### 3. 追蹤端點

**POST /api/v1/track**

處理影片進行物件追蹤。

**請求:**
- Content-Type: multipart/form-data
- Body:
  - `video`: 影片檔案 (required)
  - `model_type`: 模型類型 (optional)
  - `tracker_type`: 追蹤器類型 (optional, default: "bytetrack")
  - `confidence_threshold`: 信心閾值 (optional)

**回應:**
```json
{
  "success": true,
  "task_id": "track_123456",
  "status": "processing",
  "estimated_time": 120
}
```

**GET /api/v1/track/{task_id}/status**

查詢追蹤任務狀態。

**回應:**
```json
{
  "success": true,
  "status": "completed",
  "progress": 100,
  "video_url": "/api/v1/files/tracked_video_123.mp4",
  "tracks": [
    {
      "track_id": 1,
      "frames": [0, 1, 2, ...],
      "xyxy": [[x1, y1, x2, y2], ...]
    },
    ...
  ]
}
```

#### 4. 標註端點

**POST /api/v1/annotate**

對檢測結果進行標註。

**請求:**
- Content-Type: application/json
- Body:
  - `image_url`: 圖片 URL (required)
  - `detections`: 檢測結果 (required)
  - `annotator_type`: 標註器類型 (optional, default: "box")
  - `options`: 標註選項 (optional)

**回應:**
```json
{
  "success": true,
  "annotated_image_url": "/api/v1/files/annotated_image_123.jpg"
}
```

#### 5. 模型管理端點

**GET /api/v1/models**

獲取可用模型列表。

**回應:**
```json
{
  "success": true,
  "models": [
    {
      "id": "yolov8n",
      "name": "YOLOv8 Nano",
      "type": "detection",
      "supported_formats": ["image", "video"]
    },
    {
      "id": "sam3",
      "name": "SAM3",
      "type": "segmentation",
      "supported_formats": ["image"]
    },
    ...
  ]
}
```

### 後端服務層設計

#### DetectionService

```python
class DetectionService:
    async def detect_image(
        self,
        image: bytes,
        model_type: str,
        confidence_threshold: float,
        iou_threshold: float
    ) -> Detections:
        """執行圖片檢測"""
        pass
```

#### SegmentationService (SAM3)

```python
class SegmentationService:
    async def segment_image(
        self,
        image: bytes,
        prompts: list[str] | None = None,
        auto_generate: bool = False
    ) -> list[dict]:
        """使用 SAM3 進行圖像分割"""
        pass
```

#### TrackingService

```python
class TrackingService:
    async def track_video(
        self,
        video_path: str,
        model_type: str,
        tracker_type: str
    ) -> str:
        """處理影片追蹤，返回任務 ID"""
        pass
```

## 前端設計

### 技術棧

- **框架**: Vue.js 3 (Composition API)
- **構建工具**: Vite
- **狀態管理**: Pinia
- **路由**: Vue Router
- **UI 庫**: Vuetify 或 Element Plus
- **HTTP 客戶端**: Axios
- **圖表**: Chart.js 或 ECharts

### 主要頁面設計

#### 1. 檢測頁面 (DetectionView.vue)

**功能:**
- 圖片上傳（拖放或點擊）
- 模型選擇
- 參數調整（信心閾值、IoU 閾值）
- 檢測結果展示
- 結果下載

**組件結構:**
```vue
<template>
  <div class="detection-view">
    <ImageUploader @uploaded="handleImageUpload" />
    <ModelSelector v-model="selectedModel" />
    <ParameterPanel v-model="parameters" />
    <DetectionCanvas 
      :image="image" 
      :detections="detections" 
    />
    <DetectionList :detections="detections" />
  </div>
</template>
```

#### 2. 分割頁面 (SegmentationView.vue)

**功能:**
- 圖片上傳
- SAM3 提示輸入（文字、點、框）
- 自動分割選項
- 分割結果展示
- 遮罩下載

**組件結構:**
```vue
<template>
  <div class="segmentation-view">
    <ImageUploader @uploaded="handleImageUpload" />
    <PromptInput 
      v-model="prompts" 
      :prompt-type="promptType" 
    />
    <SegmentationCanvas 
      :image="image" 
      :masks="masks" 
    />
    <MaskOverlay :masks="masks" />
  </div>
</template>
```

#### 3. 追蹤頁面 (TrackingView.vue)

**功能:**
- 影片上傳
- 追蹤參數設定
- 進度顯示
- 追蹤結果播放
- 追蹤數據下載

**組件結構:**
```vue
<template>
  <div class="tracking-view">
    <VideoUploader @uploaded="handleVideoUpload" />
    <TrackingParameters v-model="parameters" />
    <VideoPlayer 
      :video-url="videoUrl" 
      :tracks="tracks" 
    />
    <TrackingTimeline :tracks="tracks" />
  </div>
</template>
```

### 狀態管理 (Pinia Stores)

#### Detection Store

```javascript
import { defineStore } from 'pinia'

export const useDetectionStore = defineStore('detection', {
  state: () => ({
    image: null,
    detections: null,
    selectedModel: 'yolov8n',
    parameters: {
      confidence: 0.25,
      iou: 0.45
    },
    loading: false,
    error: null
  }),
  
  actions: {
    async detectImage(imageFile) {
      this.loading = true
      try {
        const response = await api.detect(imageFile, this.selectedModel, this.parameters)
        this.detections = response.detections
        this.image = response.image_url
      } catch (error) {
        this.error = error.message
      } finally {
        this.loading = false
      }
    }
  }
})
```

#### Segmentation Store (SAM3)

```javascript
export const useSegmentationStore = defineStore('segmentation', {
  state: () => ({
    image: null,
    masks: [],
    prompts: [],
    promptType: 'text',
    autoGenerate: false,
    loading: false
  }),
  
  actions: {
    async segmentImage(imageFile, prompts, autoGenerate) {
      this.loading = true
      try {
        const response = await api.segment(imageFile, prompts, autoGenerate)
        this.masks = response.masks
        this.image = response.image_url
      } finally {
        this.loading = false
      }
    }
  }
})
```

### API 服務層

```javascript
// services/api.js
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  timeout: 30000
})

export default {
  async detect(imageFile, modelType, parameters) {
    const formData = new FormData()
    formData.append('image', imageFile)
    formData.append('model_type', modelType)
    formData.append('confidence_threshold', parameters.confidence)
    formData.append('iou_threshold', parameters.iou)
    
    const response = await api.post('/detect', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  },
  
  async segment(imageFile, prompts, autoGenerate) {
    const formData = new FormData()
    formData.append('image', imageFile)
    if (prompts) {
      formData.append('prompts', JSON.stringify(prompts))
    }
    formData.append('auto_generate', autoGenerate)
    
    const response = await api.post('/segment', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  },
  
  async track(videoFile, parameters) {
    const formData = new FormData()
    formData.append('video', videoFile)
    // ... 其他參數
    
    const response = await api.post('/track', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  },
  
  async getTrackStatus(taskId) {
    const response = await api.get(`/track/${taskId}/status`)
    return response.data
  },
  
  async getModels() {
    const response = await api.get('/models')
    return response.data
  }
}
```

## 部署配置

### Docker Compose

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - PYTHONUNBUFFERED=1
    volumes:
      - ./backend:/app
      - model_cache:/app/models
    depends_on:
      - redis

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - VITE_API_BASE_URL=http://localhost:8000/api/v1
    depends_on:
      - backend

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"

volumes:
  model_cache:
```

## 安全性考量

1. **檔案上傳限制**: 限制檔案大小和類型
2. **API 認證**: 實作 JWT 或 API Key 認證
3. **速率限制**: 使用 Redis 實作 API 速率限制
4. **輸入驗證**: 使用 Pydantic 驗證所有輸入
5. **CORS 配置**: 正確配置 CORS 政策

## 效能優化

1. **非同步處理**: 使用 FastAPI 的異步功能
2. **背景任務**: 長時間任務使用 Celery 或 BackgroundTasks
3. **快取**: 使用 Redis 快取模型結果
4. **CDN**: 靜態資源使用 CDN
5. **圖片優化**: 壓縮和調整圖片大小

## 未來擴展

1. **即時串流**: 支援 WebSocket 即時處理
2. **批次處理**: 支援多檔案批次處理
3. **模型管理**: 動態載入和管理模型
4. **用戶系統**: 用戶註冊、登入、歷史記錄
5. **API 文檔**: 自動生成 Swagger/OpenAPI 文檔


