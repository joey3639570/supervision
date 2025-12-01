<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <h1 class="text-h4 mb-4">物件檢測</h1>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" md="4">
        <v-card>
          <v-card-title>上傳圖片</v-card-title>
          <v-card-text>
            <v-file-input
              v-model="imageFile"
              label="選擇圖片"
              accept="image/*"
              prepend-icon="mdi-image"
              @change="handleFileChange"
            ></v-file-input>

            <v-select
              v-model="selectedModel"
              :items="models"
              label="選擇模型"
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
              @click="detect"
            >
              開始檢測
            </v-btn>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="8">
        <v-card>
          <v-card-title>檢測結果</v-card-title>
          <v-card-text>
            <div v-if="resultImage" class="result-container">
              <img :src="resultImage" alt="檢測結果" class="result-image" />
            </div>
            <div v-else class="text-center text-grey py-12">
              請上傳圖片並點擊「開始檢測」
            </div>

            <v-list v-if="detections.length > 0" class="mt-4">
              <v-list-item
                v-for="(det, index) in detections"
                :key="index"
              >
                <v-list-item-title>
                  檢測 #{{ index + 1 }}
                </v-list-item-title>
                <v-list-item-subtitle>
                  位置: [{{ det.xyxy.join(', ') }}]
                  <span v-if="det.confidence">
                    | 信心: {{ (det.confidence * 100).toFixed(1) }}%
                  </span>
                  <span v-if="det.class_name">
                    | 類別: {{ det.class_name }}
                  </span>
                </v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../services/api'

const imageFile = ref(null)
const selectedModel = ref('yolov8n')
const confidence = ref(0.25)
const iou = ref(0.45)
const loading = ref(false)
const resultImage = ref(null)
const detections = ref([])
const models = ref([])

onMounted(async () => {
  try {
    const response = await api.getModels()
    models.value = response.models
  } catch (error) {
    console.error('Failed to load models:', error)
  }
})

const handleFileChange = (file) => {
  if (file) {
    const reader = new FileReader()
    reader.onload = (e) => {
      resultImage.value = e.target.result
    }
    reader.readAsDataURL(file)
  }
}

const detect = async () => {
  if (!imageFile.value) {
    alert('請先選擇圖片')
    return
  }

  loading.value = true
  try {
    const response = await api.detect(imageFile.value, {
      modelType: selectedModel.value,
      confidence: confidence.value,
      iou: iou.value
    })

    detections.value = response.detections
    if (response.image_url) {
      resultImage.value = response.image_url
    }
  } catch (error) {
    console.error('Detection failed:', error)
    alert('檢測失敗: ' + error.message)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.result-container {
  text-align: center;
}

.result-image {
  max-width: 100%;
  height: auto;
  border: 1px solid #ddd;
  border-radius: 4px;
}
</style>



