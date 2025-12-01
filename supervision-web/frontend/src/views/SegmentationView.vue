<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <h1 class="text-h4 mb-2">圖像分割 (SAM3)</h1>
        <p class="text-body-2 text-grey mb-4">使用 Segment Anything Model 3 進行圖像分割，支援概念提示</p>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" md="4">
        <v-card>
          <v-card-title>設定</v-card-title>
          <v-card-text>
            <ImageUploader
              v-model="imageFile"
              label="選擇圖片"
              @preview="handlePreview"
            />

            <v-divider class="my-4"></v-divider>

            <v-radio-group v-model="promptType" label="提示類型">
              <v-radio label="自動分割" value="auto"></v-radio>
              <v-radio label="文字提示" value="text"></v-radio>
              <v-radio label="點擊選擇" value="point"></v-radio>
              <v-radio label="框選區域" value="box"></v-radio>
            </v-radio-group>

            <v-text-field
              v-if="promptType === 'text'"
              v-model="textPrompt"
              label="輸入提示詞"
              hint="例如: person, car, dog"
              persistent-hint
              class="mt-4"
            ></v-text-field>

            <v-chip-group
              v-if="promptType === 'text'"
              v-model="selectedPrompts"
              column
              multiple
              class="mt-2"
            >
              <v-chip
                v-for="prompt in promptHistory"
                :key="prompt"
                :value="prompt"
                filter
              >
                {{ prompt }}
              </v-chip>
            </v-chip-group>

            <v-btn
              v-if="promptType === 'text' && textPrompt"
              variant="text"
              size="small"
              @click="addPrompt"
            >
              添加提示詞
            </v-btn>

            <v-alert
              v-if="promptType === 'point'"
              type="info"
              density="compact"
              class="mt-4"
            >
              點擊圖片上的物件進行分割
            </v-alert>

            <v-alert
              v-if="promptType === 'box'"
              type="info"
              density="compact"
              class="mt-4"
            >
              在圖片上拖動繪製框選區域
            </v-alert>

            <v-btn
              color="primary"
              block
              class="mt-4"
              :loading="loading"
              :disabled="!imageFile"
              @click="segment"
            >
              開始分割
            </v-btn>
          </v-card-text>
        </v-card>

        <!-- 分割結果統計 -->
        <v-card v-if="masks.length > 0" class="mt-4">
          <v-card-title>分割結果</v-card-title>
          <v-card-text>
            <v-list density="compact">
              <v-list-item>
                <v-list-item-title>遮罩數量: {{ masks.length }}</v-list-item-title>
              </v-list-item>
              <v-list-item v-for="(mask, index) in masks" :key="index">
                <v-list-item-title>
                  遮罩 #{{ index + 1 }}
                </v-list-item-title>
                <v-list-item-subtitle>
                  面積: {{ mask.area ? mask.area.toLocaleString() : 'N/A' }} px²
                </v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="8">
        <v-card>
          <v-card-title>
            分割結果
            <v-spacer></v-spacer>
            <v-btn-toggle v-model="viewMode" mandatory density="compact">
              <v-btn value="overlay" size="small">疊加</v-btn>
              <v-btn value="masks" size="small">遮罩</v-btn>
              <v-btn value="original" size="small">原圖</v-btn>
            </v-btn-toggle>
          </v-card-title>
          <v-card-text>
            <div v-if="previewUrl" class="canvas-container">
              <DetectionCanvas
                ref="canvasRef"
                :image-url="previewUrl"
                :masks="viewMode === 'overlay' ? masks : []"
                :detections="viewMode === 'overlay' ? maskBoxes : []"
                annotator-type="box"
                @click="handleCanvasClick"
              />
            </div>
            <div v-else class="text-center text-grey py-12">
              請上傳圖片開始分割
            </div>
          </v-card-text>
          <v-card-actions v-if="masks.length > 0">
            <v-btn variant="text" @click="downloadMasks">
              <v-icon left>mdi-download</v-icon>
              下載遮罩
            </v-btn>
            <v-btn variant="text" @click="clearMasks">
              <v-icon left>mdi-delete</v-icon>
              清除結果
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import api from '../services/api'
import ImageUploader from '../components/common/ImageUploader.vue'
import DetectionCanvas from '../components/common/DetectionCanvas.vue'

const imageFile = ref(null)
const previewUrl = ref(null)
const promptType = ref('auto')
const textPrompt = ref('')
const selectedPrompts = ref([])
const promptHistory = ref(['person', 'car', 'dog', 'cat', 'building'])
const loading = ref(false)
const masks = ref([])
const viewMode = ref('overlay')
const canvasRef = ref(null)

// 將遮罩轉換為邊界框格式供 Canvas 繪製
const maskBoxes = computed(() => {
  return masks.value.map(mask => ({
    xyxy: mask.bbox || [0, 0, 0, 0]
  }))
})

const handlePreview = (url) => {
  previewUrl.value = url
  masks.value = []
}

const addPrompt = () => {
  if (textPrompt.value && !promptHistory.value.includes(textPrompt.value)) {
    promptHistory.value.push(textPrompt.value)
  }
  if (!selectedPrompts.value.includes(textPrompt.value)) {
    selectedPrompts.value.push(textPrompt.value)
  }
  textPrompt.value = ''
}

const segment = async () => {
  if (!imageFile.value) return

  loading.value = true
  try {
    const prompts = promptType.value === 'text' ? selectedPrompts.value : null
    const response = await api.segment(imageFile.value, {
      prompts,
      promptType: promptType.value,
      autoGenerate: promptType.value === 'auto'
    })

    masks.value = response.masks || []
  } catch (error) {
    console.error('Segmentation failed:', error)
    alert('分割失敗: ' + error.message)
  } finally {
    loading.value = false
  }
}

const handleCanvasClick = ({ x, y }) => {
  if (promptType.value === 'point') {
    // TODO: 處理點擊分割
    console.log('Point click:', x, y)
  }
}

const downloadMasks = () => {
  // TODO: 實作遮罩下載
  alert('下載功能開發中')
}

const clearMasks = () => {
  masks.value = []
}
</script>

<style scoped>
.canvas-container {
  text-align: center;
  overflow: auto;
}
</style>
