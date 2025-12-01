# Supervision Web 快速啟動指南

## 前置需求

- Python 3.9+
- Node.js 16+
- npm 或 yarn

## 快速開始

### 1. 後端設置

```bash
# 進入後端目錄
cd supervision-web/backend

# 安裝依賴
pip install -r requirements.txt

# 啟動服務器
uvicorn app.main:app --reload --port 8000
```

後端將在 `http://localhost:8000` 運行
- API 文檔: http://localhost:8000/docs
- 健康檢查: http://localhost:8000/health

### 2. 前端設置

```bash
# 進入前端目錄
cd supervision-web/frontend

# 安裝依賴
npm install

# 啟動開發服務器
npm run dev
```

前端將在 `http://localhost:3000` 運行

## 功能測試

### 檢測功能

1. 訪問 http://localhost:3000/detect
2. 上傳一張圖片
3. 選擇模型（預設: yolov8n）
4. 調整參數（信心閾值、IoU 閾值）
5. 點擊「開始檢測」
6. 查看檢測結果

### API 測試

使用 Swagger UI 測試 API：
1. 訪問 http://localhost:8000/docs
2. 選擇要測試的端點
3. 點擊 "Try it out"
4. 輸入參數並執行

## 環境變數配置

創建 `.env` 檔案（可選）：

```env
# 後端 .env
DEBUG=True
LOG_LEVEL=INFO
MAX_UPLOAD_SIZE=104857600  # 100MB

# 前端 .env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## 常見問題

### 後端無法啟動

- 檢查 Python 版本（需要 3.9+）
- 確認所有依賴已安裝
- 檢查端口 8000 是否被占用

### 前端無法連接後端

- 確認後端正在運行
- 檢查 `vite.config.js` 中的代理配置
- 確認 CORS 配置正確

### 模型載入錯誤

- 目前部分功能使用示例數據
- 需要實作實際的模型載入邏輯
- 參考 `app/services/supervision_service.py`

## 開發建議

1. **後端開發**
   - 在 `app/services/` 中添加業務邏輯
   - 在 `app/api/routes/` 中添加新端點
   - 使用 `app/models/schemas.py` 定義數據模型

2. **前端開發**
   - 在 `src/views/` 中完善頁面功能
   - 在 `src/components/` 中創建可重用組件
   - 使用 `src/services/api.js` 調用 API

3. **測試**
   - 後端: 使用 pytest
   - 前端: 使用 Vitest 或 Jest

## 下一步

查看 `IMPLEMENTATION_SUMMARY.md` 了解詳細的實作狀態和開發建議。



