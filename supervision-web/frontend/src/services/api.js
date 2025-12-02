import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 請求攔截器
api.interceptors.request.use(
  (config) => {
    // 可以在這裡添加認證 token
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 回應攔截器
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export default {
  // 檢測
  async detect(imageFile, params) {
    const formData = new FormData()
    formData.append('image', imageFile)
    formData.append('model_type', params.modelType || 'yolov8')
    formData.append('confidence_threshold', params.confidence || 0.25)
    formData.append('iou_threshold', params.iou || 0.45)
    if (params.classes) {
      formData.append('classes', JSON.stringify(params.classes))
    }
    
    return api.post('/detect', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // 分割 (SAM3)
  async segment(imageFile, params = {}) {
    const formData = new FormData()
    formData.append('image', imageFile)
    
    // prompts 是可选的，但如果提供了就发送
    if (params.prompts && Array.isArray(params.prompts) && params.prompts.length > 0) {
      formData.append('prompts', JSON.stringify(params.prompts))
    }
    
    // 必需字段，使用默认值
    formData.append('prompt_type', params.promptType || 'text')
    formData.append('auto_generate', String(params.autoGenerate === true || params.autoGenerate === 'true'))
    formData.append('confidence_threshold', String(params.confidence || 0.5))
    formData.append('device', params.device || 'cuda')
    
    // 可选字段
    if (params.checkpointPath) {
      formData.append('checkpoint_path', params.checkpointPath)
    }
    
    return api.post('/segment', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // 追蹤
  async track(videoFile, params) {
    const formData = new FormData()
    formData.append('video', videoFile)
    formData.append('model_type', params.modelType || 'yolov8')
    formData.append('tracker_type', params.trackerType || 'bytetrack')
    formData.append('confidence_threshold', params.confidence || 0.25)
    formData.append('iou_threshold', params.iou || 0.45)
    
    return api.post('/track', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // 查詢追蹤狀態
  async getTrackStatus(taskId) {
    return api.get(`/track/${taskId}/status`)
  },

  // 標註
  async annotate(request) {
    return api.post('/annotate', request)
  },

  // 模型列表
  async getModels() {
    return api.get('/models')
  },

  // 資料集轉換
  async convertDataset(sourceFormat, targetFormat, files) {
    const formData = new FormData()
    files.forEach(file => formData.append('files', file))
    formData.append('source_format', sourceFormat)
    formData.append('target_format', targetFormat)
    
    return api.post('/dataset/convert', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // 資料集分割
  async splitDataset(trainRatio, testRatio, files) {
    const formData = new FormData()
    files.forEach(file => formData.append('files', file))
    formData.append('train_ratio', trainRatio)
    formData.append('test_ratio', testRatio)
    
    return api.post('/dataset/split', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // 計算指標
  async calculateMetrics(request) {
    return api.post('/metrics/calculate', request)
  },

  // 創建區域
  async createZone(request) {
    return api.post('/geometry/zone', request)
  },

  // 影片資訊
  async getVideoInfo(videoFile) {
    const formData = new FormData()
    formData.append('video', videoFile)
    
    return api.post('/video/info', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // 處理影片
  async processVideo(videoFile, callbackType) {
    const formData = new FormData()
    formData.append('video', videoFile)
    formData.append('callback_type', callbackType)
    
    return api.post('/video/process', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // 座標轉換
  async convertCoordinates(request) {
    return api.post('/utils/convert', request)
  },

  // SAM3 對象計數
  async sam3Count(imageFile, params) {
    const formData = new FormData()
    formData.append('image', imageFile)
    formData.append('prompt', params.prompt || 'object')
    formData.append('confidence_threshold', params.confidence || 0.5)
    if (params.checkpointPath) {
      formData.append('checkpoint_path', params.checkpointPath)
    }
    formData.append('device', params.device || 'cuda')
    
    return api.post('/sam3/count', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // SAM3 多提示詞檢測
  async sam3MultiPrompt(imageFile, params) {
    const formData = new FormData()
    formData.append('image', imageFile)
    formData.append('prompts', JSON.stringify(params.prompts || []))
    formData.append('confidence_threshold', params.confidence || 0.5)
    if (params.checkpointPath) {
      formData.append('checkpoint_path', params.checkpointPath)
    }
    formData.append('device', params.device || 'cuda')
    
    return api.post('/sam3/multi-prompt', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // SAM3 線計數
  async sam3LineCount(videoFile, params) {
    const formData = new FormData()
    formData.append('video', videoFile)
    formData.append('prompt', params.prompt || 'object')
    formData.append('line_start_x', params.lineStartX)
    formData.append('line_start_y', params.lineStartY)
    formData.append('line_end_x', params.lineEndX)
    formData.append('line_end_y', params.lineEndY)
    formData.append('confidence_threshold', params.confidence || 0.5)
    if (params.checkpointPath) {
      formData.append('checkpoint_path', params.checkpointPath)
    }
    formData.append('device', params.device || 'cuda')
    
    return api.post('/sam3/line-count', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // SAM3 區域計數
  async sam3ZoneCount(videoFile, params) {
    const formData = new FormData()
    formData.append('video', videoFile)
    formData.append('prompt', params.prompt || 'object')
    formData.append('zones', JSON.stringify(params.zones))
    formData.append('confidence_threshold', params.confidence || 0.5)
    if (params.checkpointPath) {
      formData.append('checkpoint_path', params.checkpointPath)
    }
    formData.append('device', params.device || 'cuda')
    
    return api.post('/sam3/zone-count', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // SAM3 追蹤
  async sam3Track(videoFile, params) {
    const formData = new FormData()
    formData.append('video', videoFile)
    formData.append('prompt', params.prompt || 'object')
    formData.append('confidence_threshold', params.confidence || 0.5)
    formData.append('trace_length', params.traceLength || 30)
    if (params.checkpointPath) {
      formData.append('checkpoint_path', params.checkpointPath)
    }
    formData.append('device', params.device || 'cuda')
    
    return api.post('/sam3/track', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // 獲取 SAM3 任務狀態
  async getSam3TaskStatus(taskId) {
    return api.get(`/sam3/task/${taskId}`)
  }
}



