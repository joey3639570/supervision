<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <h1 class="text-h4 mb-2">影片處理</h1>
        <p class="text-body-2 text-grey mb-4">影片資訊獲取和處理工具</p>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" md="4">
        <v-card>
          <v-card-title>影片上傳</v-card-title>
          <v-card-text>
            <VideoUploader
              v-model="videoFile"
              label="選擇影片"
              @metadata="handleMetadata"
            />

            <v-btn
              color="primary"
              block
              class="mt-4"
              :loading="infoLoading"
              :disabled="!videoFile"
              @click="getVideoInfo"
            >
              獲取影片資訊
            </v-btn>
          </v-card-text>
        </v-card>

        <!-- 影片資訊 -->
        <v-card v-if="videoInfo" class="mt-4">
          <v-card-title>
            <v-icon left>mdi-information</v-icon>
            影片資訊
          </v-card-title>
          <v-card-text>
            <v-list density="compact">
              <v-list-item>
                <v-list-item-title>解析度</v-list-item-title>
                <v-list-item-subtitle>
                  {{ videoInfo.width }} x {{ videoInfo.height }}
                </v-list-item-subtitle>
              </v-list-item>
              <v-list-item>
                <v-list-item-title>幀率</v-list-item-title>
                <v-list-item-subtitle>
                  {{ videoInfo.fps?.toFixed(2) }} FPS
                </v-list-item-subtitle>
              </v-list-item>
              <v-list-item>
                <v-list-item-title>總幀數</v-list-item-title>
                <v-list-item-subtitle>
                  {{ videoInfo.total_frames?.toLocaleString() }}
                </v-list-item-subtitle>
              </v-list-item>
              <v-list-item>
                <v-list-item-title>時長</v-list-item-title>
                <v-list-item-subtitle>
                  {{ formatDuration(videoInfo.duration_seconds) }}
                </v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>

        <!-- 處理選項 -->
        <v-card class="mt-4">
          <v-card-title>
            <v-icon left>mdi-cog</v-icon>
            處理選項
          </v-card-title>
          <v-card-text>
            <v-select
              v-model="processType"
              :items="processTypes"
              label="處理類型"
              item-title="name"
              item-value="id"
            ></v-select>

            <v-slider
              v-model="frameStride"
              label="幀步長"
              min="1"
              max="10"
              step="1"
              thumb-label
              class="mt-4"
            ></v-slider>

            <v-range-slider
              v-model="frameRange"
              label="幀範圍"
              :max="videoInfo?.total_frames || 1000"
              step="1"
              thumb-label
              class="mt-4"
            ></v-range-slider>

            <v-btn
              color="primary"
              block
              class="mt-4"
              :loading="processLoading"
              :disabled="!videoFile"
              @click="processVideo"
            >
              開始處理
            </v-btn>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="8">
        <!-- 處理進度 -->
        <v-card v-if="processProgress > 0">
          <v-card-title>處理進度</v-card-title>
          <v-card-text>
            <v-progress-linear
              :model-value="processProgress"
              :color="processProgress === 100 ? 'success' : 'primary'"
              height="25"
              striped
            >
              <template v-slot:default>{{ processProgress }}%</template>
            </v-progress-linear>
            
            <div class="mt-2 text-center">
              <span v-if="processProgress < 100">處理中...</span>
              <span v-else class="text-success">處理完成!</span>
            </div>
          </v-card-text>
        </v-card>

        <!-- 幀提取預覽 -->
        <v-card class="mt-4">
          <v-card-title>
            幀提取預覽
            <v-spacer></v-spacer>
            <v-btn-toggle v-model="previewMode" mandatory density="compact">
              <v-btn value="single" size="small">單幀</v-btn>
              <v-btn value="grid" size="small">網格</v-btn>
            </v-btn-toggle>
          </v-card-title>
          <v-card-text>
            <div v-if="extractedFrames.length > 0">
              <div v-if="previewMode === 'single'" class="single-frame-view">
                <img :src="extractedFrames[currentFrameIndex]" alt="Frame" class="preview-frame" />
                <v-slider
                  v-model="currentFrameIndex"
                  :max="extractedFrames.length - 1"
                  step="1"
                  class="mt-4"
                ></v-slider>
                <p class="text-center text-grey">
                  幀 {{ currentFrameIndex + 1 }} / {{ extractedFrames.length }}
                </p>
              </div>
              <div v-else class="grid-view">
                <v-row>
                  <v-col
                    v-for="(frame, index) in extractedFrames.slice(0, 9)"
                    :key="index"
                    cols="4"
                  >
                    <img :src="frame" alt="Frame" class="grid-frame" />
                    <p class="text-center text-caption">幀 {{ index + 1 }}</p>
                  </v-col>
                </v-row>
              </div>
            </div>
            <div v-else class="text-center text-grey py-12">
              處理影片後將顯示提取的幀
            </div>
          </v-card-text>
        </v-card>

        <!-- FPS 監控器 -->
        <v-card class="mt-4">
          <v-card-title>
            <v-icon left>mdi-speedometer</v-icon>
            效能監控
          </v-card-title>
          <v-card-text>
            <v-row>
              <v-col cols="4">
                <v-card variant="outlined" class="text-center pa-4">
                  <div class="text-h4 text-primary">{{ currentFps }}</div>
                  <div class="text-caption">當前 FPS</div>
                </v-card>
              </v-col>
              <v-col cols="4">
                <v-card variant="outlined" class="text-center pa-4">
                  <div class="text-h4 text-success">{{ avgFps }}</div>
                  <div class="text-caption">平均 FPS</div>
                </v-card>
              </v-col>
              <v-col cols="4">
                <v-card variant="outlined" class="text-center pa-4">
                  <div class="text-h4 text-warning">{{ processedFrames }}</div>
                  <div class="text-caption">已處理幀數</div>
                </v-card>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref } from 'vue'
import api from '../services/api'
import VideoUploader from '../components/common/VideoUploader.vue'

const videoFile = ref(null)
const videoInfo = ref(null)
const infoLoading = ref(false)
const processLoading = ref(false)
const processProgress = ref(0)
const processType = ref('detect')
const frameStride = ref(1)
const frameRange = ref([0, 1000])
const extractedFrames = ref([])
const currentFrameIndex = ref(0)
const previewMode = ref('single')
const currentFps = ref(0)
const avgFps = ref(0)
const processedFrames = ref(0)

const processTypes = [
  { id: 'detect', name: '物件檢測' },
  { id: 'track', name: '物件追蹤' },
  { id: 'segment', name: '圖像分割' },
  { id: 'extract', name: '幀提取' },
]

const handleMetadata = (info) => {
  videoInfo.value = info
  frameRange.value = [0, Math.min(info.duration * 30, 1000)]
}

const getVideoInfo = async () => {
  if (!videoFile.value) return

  infoLoading.value = true
  try {
    const response = await api.getVideoInfo(videoFile.value)
    videoInfo.value = response
  } catch (error) {
    console.error('Get video info failed:', error)
    alert('獲取影片資訊失敗: ' + error.message)
  } finally {
    infoLoading.value = false
  }
}

const processVideo = async () => {
  if (!videoFile.value) return

  processLoading.value = true
  processProgress.value = 0
  processedFrames.value = 0

  try {
    // 模擬處理進度
    const interval = setInterval(() => {
      if (processProgress.value < 100) {
        processProgress.value += 10
        processedFrames.value += 100
        currentFps.value = Math.random() * 10 + 20
        avgFps.value = (avgFps.value + currentFps.value) / 2
      } else {
        clearInterval(interval)
      }
    }, 500)

    const response = await api.processVideo(videoFile.value, processType.value)
    
    // 處理完成
    processProgress.value = 100
    clearInterval(interval)
    
    // TODO: 載入提取的幀
    // extractedFrames.value = response.frames
  } catch (error) {
    console.error('Process video failed:', error)
    alert('處理失敗: ' + error.message)
  } finally {
    processLoading.value = false
  }
}

const formatDuration = (seconds) => {
  if (!seconds) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}
</script>

<style scoped>
.single-frame-view {
  text-align: center;
}

.preview-frame {
  max-width: 100%;
  max-height: 400px;
  border-radius: 4px;
}

.grid-frame {
  width: 100%;
  height: auto;
  border-radius: 4px;
}
</style>
