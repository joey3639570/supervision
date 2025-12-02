# Supervision Web Application

完整的 Supervision 電腦視覺工具庫網頁應用程式，提供所有 Supervision 功能的 Web 接口。

## 專案結構

```
supervision-web/
├── backend/          # FastAPI 後端
├── frontend/         # Vue.js 前端
└── README.md
```

## 功能模組

### 後端 API

- **檢測** (`/api/v1/detect`) - 物件檢測
- **分割** (`/api/v1/segment`) - SAM3 圖像分割
- **追蹤** (`/api/v1/track`) - 物件追蹤
- **標註** (`/api/v1/annotate`) - 標註工具
- **模型管理** (`/api/v1/models`) - 模型列表
- **資料集** (`/api/v1/dataset`) - 資料集管理
- **評估指標** (`/api/v1/metrics`) - 指標計算
- **幾何工具** (`/api/v1/geometry`) - 區域分析
- **影片處理** (`/api/v1/video`) - 影片處理
- **工具** (`/api/v1/utils`) - 實用工具

### 前端頁面

- **首頁** - 功能總覽
- **物件檢測** - 檢測頁面
- **圖像分割** - SAM3 分割頁面
- **物件追蹤** - 追蹤頁面
- **標註工具** - 標註頁面
- **資料集管理** - 資料集頁面
- **評估指標** - 指標頁面
- **區域分析** - 區域分析頁面
- **影片處理** - 影片處理頁面

## 安裝與運行

### 後端

```bash
cd backend
pip install -r requirements.txt

# 使用啟動腳本（推薦，自動設置 SAM3 路徑）
./start.sh

# 或手動啟動（需要設置 PYTHONPATH）
export PYTHONPATH="../sam3:$PYTHONPATH"
uvicorn app.main:app --reload --port 8001
```

**注意**: SAM3 功能需要：
1. 確保 `/root/joey/supervision/sam3` 目錄存在（或設置正確的 SAM3 路徑）
2. 確保檢查點文件存在於 `/root/joey/sam3_model/sam3.pt`（或通過環境變數 `SAM3_CHECKPOINT_PATH` 指定）
3. 所有依賴已安裝（見 `requirements.txt`）
4. 使用 `start.sh` 腳本啟動以自動設置 Python 路徑

**檢查點配置**: 系統會自動查找檢查點文件。如果使用不同的位置，設置環境變數：
```bash
export SAM3_CHECKPOINT_PATH=/path/to/sam3.pt
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

## 開發狀態

- ✅ 後端 API 架構完成
- ✅ 前端基礎結構完成
- ✅ 檢測功能基本實作
- 🚧 其他功能開發中

## 技術棧

- **後端**: FastAPI, Supervision, OpenCV
- **前端**: Vue.js 3, Vuetify, Pinia, Axios
- **構建工具**: Vite



