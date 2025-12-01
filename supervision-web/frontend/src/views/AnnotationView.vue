<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <h1 class="text-h4 mb-2">標註工具</h1>
        <p class="text-body-2 text-grey mb-4">使用多種標註器視覺化檢測結果</p>
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

            <AnnotatorSelector
              v-model="annotatorType"
              label="標註器類型"
            />

            <v-switch
              v-model="showLabels"
              label="顯示標籤"
              color="primary"
              class="mt-4"
            ></v-switch>

            <v-color-picker
              v-model="annotatorColor"
              label="標註顏色"
              :modes="['hex']"
              hide-canvas
              hide-inputs
              show-swatches
              class="mt-4"
            ></v-color-picker>

            <v-slider
              v-model="lineWidth"
              label="線條粗細"
              min="1"
              max="10"
              step="1"
              thumb-label
              class="mt-4"
            ></v-slider>

            <v-divider class="my-4"></v-divider>

            <p class="text-subtitle-2 mb-2">手動添加檢測框</p>
            
            <v-text-field
              v-model="newDetection.x1"
              label="X1"
              type="number"
              density="compact"
            ></v-text-field>
            <v-text-field
              v-model="newDetection.y1"
              label="Y1"
              type="number"
              density="compact"
            ></v-text-field>
            <v-text-field
              v-model="newDetection.x2"
              label="X2"
              type="number"
              density="compact"
            ></v-text-field>
            <v-text-field
              v-model="newDetection.y2"
              label="Y2"
              type="number"
              density="compact"
            ></v-text-field>
            <v-text-field
              v-model="newDetection.label"
              label="標籤"
              density="compact"
            ></v-text-field>

            <v-btn
              variant="outlined"
              block
              class="mt-2"
              @click="addDetection"
            >
              添加檢測框
            </v-btn>

            <v-btn
              color="primary"
              block
              class="mt-4"
              :disabled="!previewUrl || detections.length === 0"
              @click="applyAnnotation"
            >
              應用標註
            </v-btn>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="8">
        <v-card>
          <v-card-title>
            標註結果
            <v-spacer></v-spacer>
            <v-btn
              v-if="annotatedImageUrl"
              variant="text"
              size="small"
              @click="downloadAnnotated"
            >
              <v-icon left>mdi-download</v-icon>
              下載
            </v-btn>
          </v-card-title>
          <v-card-text>
            <div v-if="previewUrl" class="canvas-container">
              <DetectionCanvas
                ref="canvasRef"
                :image-url="previewUrl"
                :detections="detections"
                :annotator-type="annotatorType"
                :show-labels="showLabels"
                :line-width="lineWidth"
                :colors="[annotatorColor]"
              />
            </div>
            <div v-else class="text-center text-grey py-12">
              請上傳圖片並添加檢測框
            </div>
          </v-card-text>
        </v-card>

        <!-- 檢測列表 -->
        <v-card v-if="detections.length > 0" class="mt-4">
          <v-card-title>檢測列表 ({{ detections.length }})</v-card-title>
          <v-card-text>
            <v-list density="compact">
              <v-list-item
                v-for="(det, index) in detections"
                :key="index"
              >
                <template v-slot:prepend>
                  <v-avatar :color="annotatorColor" size="24">
                    {{ index + 1 }}
                  </v-avatar>
                </template>
                <v-list-item-title>
                  {{ det.class_name || `檢測 #${index + 1}` }}
                </v-list-item-title>
                <v-list-item-subtitle>
                  [{{ det.xyxy.map(v => Math.round(v)).join(', ') }}]
                </v-list-item-subtitle>
                <template v-slot:append>
                  <v-btn
                    icon="mdi-delete"
                    size="small"
                    variant="text"
                    @click="removeDetection(index)"
                  ></v-btn>
                </template>
              </v-list-item>
            </v-list>

            <v-btn
              variant="text"
              color="error"
              block
              class="mt-2"
              @click="clearDetections"
            >
              清除所有檢測框
            </v-btn>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref } from 'vue'
import api from '../services/api'
import ImageUploader from '../components/common/ImageUploader.vue'
import DetectionCanvas from '../components/common/DetectionCanvas.vue'
import AnnotatorSelector from '../components/common/AnnotatorSelector.vue'

const imageFile = ref(null)
const previewUrl = ref(null)
const annotatorType = ref('box')
const showLabels = ref(true)
const annotatorColor = ref('#FF6B6B')
const lineWidth = ref(2)
const detections = ref([])
const annotatedImageUrl = ref(null)
const canvasRef = ref(null)

const newDetection = ref({
  x1: 100,
  y1: 100,
  x2: 200,
  y2: 200,
  label: ''
})

const handlePreview = (url) => {
  previewUrl.value = url
}

const addDetection = () => {
  const { x1, y1, x2, y2, label } = newDetection.value
  detections.value.push({
    xyxy: [Number(x1), Number(y1), Number(x2), Number(y2)],
    class_name: label || null,
    confidence: 1.0
  })
  
  // 重置表單
  newDetection.value = {
    x1: Number(x2) + 10,
    y1: 100,
    x2: Number(x2) + 110,
    y2: 200,
    label: ''
  }
}

const removeDetection = (index) => {
  detections.value.splice(index, 1)
}

const clearDetections = () => {
  detections.value = []
}

const applyAnnotation = async () => {
  try {
    const response = await api.annotate({
      image_url: previewUrl.value,
      detections: detections.value,
      annotator_type: annotatorType.value,
      options: {
        color: annotatorColor.value,
        thickness: lineWidth.value
      },
      labels: detections.value.map(d => d.class_name).filter(Boolean)
    })

    if (response.annotated_image_url) {
      annotatedImageUrl.value = response.annotated_image_url
    }
  } catch (error) {
    console.error('Annotation failed:', error)
    alert('標註失敗: ' + error.message)
  }
}

const downloadAnnotated = () => {
  // 從 canvas 下載圖片
  if (canvasRef.value) {
    const canvas = canvasRef.value.$el.querySelector('canvas')
    if (canvas) {
      const link = document.createElement('a')
      link.download = 'annotated_image.png'
      link.href = canvas.toDataURL()
      link.click()
    }
  }
}
</script>

<style scoped>
.canvas-container {
  text-align: center;
  overflow: auto;
}
</style>
