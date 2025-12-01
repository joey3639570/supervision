<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <h1 class="text-h4 mb-2">物件追蹤</h1>
        <p class="text-body-2 text-grey mb-4">使用 ByteTrack 進行多物件追蹤</p>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" md="4">
        <v-card>
          <v-card-title>設定</v-card-title>
          <v-card-text>
            <VideoUploader
              v-model="videoFile"
              label="選擇影片"
              @metadata="handleMetadata"
            />

            <v-divider class="my-4"></v-divider>

            <v-select
              v-model="selectedModel"
              :items="models"
              label="檢測模型"
              item-title="name"
              item-value="id"
            ></v-select>

            <v-select
              v-model="trackerType"
              :items="trackers"
              label="追蹤器"
              item-title="name"
              item-value="id"
              class="mt-4"
            ></v-select>

            <v-slider
              v-model="confidence"
              label="信心閾值"
              min="0"
              max="1"
              step="0.01"
              thumb-label
              class="mt-4"
            ></v-slider>

            <v-slider
              v-model="iou"
              label="IoU 閾值"
              min="0"
              max="1"
              step="0.01"
              thumb-label
              class="mt-4"
            ></v-slider>

            <v-btn
              color="primary"
              block
              class="mt-4"
              :loading="loading"
              :disabled="!videoFile"
              @click="startTracking"
            >
              開始追蹤
            </v-btn>
          </v-card-text>
        </v-card>

        <!-- 追蹤任務狀態 -->
        <v-card v-if="taskId" class="mt-4">
          <v-card-title>任務狀態</v-card-title>
          <v-card-text>
            <v-progress-linear
              :model-value="progress"
              :color="taskStatus === 'completed' ? 'success' : 'primary'"
              height="20"
              striped
            >
              <template v-slot:default>{{ progress }}%</template>
            </v-progress-linear>
            
            <div class="mt-2 text-center">
              <v-chip :color="statusColor" size="small">
                {{ statusText }}
              </v-chip>
            </div>
          </v-card-text>
        </v-card>

        <!-- 追蹤統計 -->
        <v-card v-if="tracks.length > 0" class="mt-4">
          <v-card-title>追蹤統計</v-card-title>
          <v-card-text>
            <v-list density="compact">
              <v-list-item>
                <v-list-item-title>追蹤數量: {{ tracks.length }}</v-list-item-title>
              </v-list-item>
              <v-list-item v-for="track in tracks.slice(0, 10)" :key="track.track_id">
                <v-list-item-title>
                  ID #{{ track.track_id }}
                </v-list-item-title>
                <v-list-item-subtitle>
                  出現幀數: {{ track.frames?.length || 0 }}
                </v-list-item-subtitle>
              </v-list-item>
              <v-list-item v-if="tracks.length > 10">
                <v-list-item-title class="text-grey">
                  ... 還有 {{ tracks.length - 10 }} 個追蹤
                </v-list-item-title>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="8">
        <v-card>
          <v-card-title>
            追蹤結果
            <v-spacer></v-spacer>
            <v-btn
              v-if="resultVideoUrl"
              variant="text"
              size="small"
              @click="downloadResult"
            >
              <v-icon left>mdi-download</v-icon>
              下載
            </v-btn>
          </v-card-title>
          <v-card-text>
            <div v-if="resultVideoUrl" class="video-container">
              <video
                :src="resultVideoUrl"
                controls
                class="result-video"
              ></video>
            </div>
            <div v-else-if="videoFile" class="text-center py-12">
              <v-icon size="64" color="grey">mdi-video-outline</v-icon>
              <p class="mt-2 text-grey">點擊「開始追蹤」處理影片</p>
            </div>
            <div v-else class="text-center text-grey py-12">
              請上傳影片開始追蹤
            </div>
          </v-card-text>
        </v-card>

        <!-- 時間軸 -->
        <v-card v-if="tracks.length > 0" class="mt-4">
          <v-card-title>追蹤時間軸</v-card-title>
          <v-card-text>
            <div class="timeline-container">
              <div
                v-for="track in tracks.slice(0, 5)"
                :key="track.track_id"
                class="timeline-track"
              >
                <span class="track-label">ID #{{ track.track_id }}</span>
                <div class="track-bar">
                  <div
                    class="track-segment"
                    :style="getTrackStyle(track)"
                  ></div>
                </div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import api from '../services/api'
import VideoUploader from '../components/common/VideoUploader.vue'

const videoFile = ref(null)
const videoInfo = ref(null)
const selectedModel = ref('yolov8n')
const trackerType = ref('bytetrack')
const confidence = ref(0.25)
const iou = ref(0.45)
const loading = ref(false)
const taskId = ref(null)
const taskStatus = ref(null)
const progress = ref(0)
const resultVideoUrl = ref(null)
const tracks = ref([])
let pollInterval = null

const models = ref([
  { id: 'yolov8n', name: 'YOLOv8 Nano' },
  { id: 'yolov8s', name: 'YOLOv8 Small' },
  { id: 'yolov8m', name: 'YOLOv8 Medium' },
])

const trackers = [
  { id: 'bytetrack', name: 'ByteTrack' },
]

const statusColor = computed(() => {
  switch (taskStatus.value) {
    case 'processing': return 'primary'
    case 'completed': return 'success'
    case 'failed': return 'error'
    default: return 'grey'
  }
})

const statusText = computed(() => {
  switch (taskStatus.value) {
    case 'processing': return '處理中'
    case 'completed': return '已完成'
    case 'failed': return '失敗'
    default: return '未知'
  }
})

onMounted(async () => {
  try {
    const response = await api.getModels()
    models.value = response.models.filter(m => m.type === 'detection')
  } catch (error) {
    console.error('Failed to load models:', error)
  }
})

onUnmounted(() => {
  if (pollInterval) {
    clearInterval(pollInterval)
  }
})

const handleMetadata = (info) => {
  videoInfo.value = info
}

const startTracking = async () => {
  if (!videoFile.value) return

  loading.value = true
  taskStatus.value = 'processing'
  progress.value = 0

  try {
    const response = await api.track(videoFile.value, {
      modelType: selectedModel.value,
      trackerType: trackerType.value,
      confidence: confidence.value,
      iou: iou.value
    })

    taskId.value = response.task_id
    
    // 開始輪詢狀態
    pollInterval = setInterval(pollStatus, 2000)
  } catch (error) {
    console.error('Tracking failed:', error)
    taskStatus.value = 'failed'
    alert('追蹤失敗: ' + error.message)
  } finally {
    loading.value = false
  }
}

const pollStatus = async () => {
  if (!taskId.value) return

  try {
    const response = await api.getTrackStatus(taskId.value)
    
    taskStatus.value = response.status
    progress.value = response.progress || 0
    
    if (response.status === 'completed') {
      clearInterval(pollInterval)
      resultVideoUrl.value = response.video_url
      tracks.value = response.tracks || []
    } else if (response.status === 'failed') {
      clearInterval(pollInterval)
    }
  } catch (error) {
    console.error('Poll status failed:', error)
  }
}

const getTrackStyle = (track) => {
  if (!track.frames || !videoInfo.value) return {}
  
  const totalFrames = videoInfo.value.duration * 30 // 假設 30fps
  const startFrame = Math.min(...track.frames)
  const endFrame = Math.max(...track.frames)
  
  return {
    left: `${(startFrame / totalFrames) * 100}%`,
    width: `${((endFrame - startFrame) / totalFrames) * 100}%`
  }
}

const downloadResult = () => {
  if (resultVideoUrl.value) {
    window.open(resultVideoUrl.value, '_blank')
  }
}
</script>

<style scoped>
.video-container {
  text-align: center;
}

.result-video {
  max-width: 100%;
  max-height: 500px;
  border-radius: 4px;
}

.timeline-container {
  padding: 10px 0;
}

.timeline-track {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.track-label {
  width: 60px;
  font-size: 12px;
}

.track-bar {
  flex: 1;
  height: 20px;
  background: #eee;
  border-radius: 4px;
  position: relative;
}

.track-segment {
  position: absolute;
  height: 100%;
  background: #1976D2;
  border-radius: 4px;
  min-width: 4px;
}
</style>
