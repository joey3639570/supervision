<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <h1 class="text-h4 mb-2">區域分析</h1>
        <p class="text-body-2 text-grey mb-4">創建多邊形區域和線區域進行物件計數和分析</p>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" md="4">
        <v-card>
          <v-card-title>區域設定</v-card-title>
          <v-card-text>
            <ImageUploader
              v-model="imageFile"
              label="選擇背景圖片"
              @preview="handlePreview"
            />

            <v-divider class="my-4"></v-divider>

            <v-radio-group v-model="zoneType" label="區域類型">
              <v-radio label="多邊形區域" value="polygon"></v-radio>
              <v-radio label="線區域" value="line"></v-radio>
            </v-radio-group>

            <v-select
              v-if="zoneType === 'polygon'"
              v-model="triggerPosition"
              :items="positions"
              label="觸發位置"
              item-title="name"
              item-value="id"
              class="mt-4"
            ></v-select>

            <v-alert type="info" density="compact" class="mt-4">
              {{ zoneType === 'polygon' 
                ? '點擊畫布繪製多邊形頂點，雙擊完成繪製' 
                : '點擊畫布設定線的起點和終點' 
              }}
            </v-alert>

            <v-btn
              color="primary"
              block
              class="mt-4"
              :disabled="!canCreateZone"
              @click="createZone"
            >
              創建區域
            </v-btn>

            <v-btn
              variant="outlined"
              block
              class="mt-2"
              @click="clearPoints"
            >
              清除點
            </v-btn>
          </v-card-text>
        </v-card>

        <!-- 區域列表 -->
        <v-card v-if="zones.length > 0" class="mt-4">
          <v-card-title>區域列表 ({{ zones.length }})</v-card-title>
          <v-card-text>
            <v-list density="compact">
              <v-list-item
                v-for="(zone, index) in zones"
                :key="zone.id"
              >
                <template v-slot:prepend>
                  <v-icon :color="zone.color">
                    {{ zone.type === 'polygon' ? 'mdi-shape-polygon-plus' : 'mdi-minus' }}
                  </v-icon>
                </template>
                <v-list-item-title>
                  {{ zone.type === 'polygon' ? '多邊形' : '線' }} #{{ index + 1 }}
                </v-list-item-title>
                <v-list-item-subtitle>
                  進入: {{ zone.in_count }} | 離開: {{ zone.out_count }}
                </v-list-item-subtitle>
                <template v-slot:append>
                  <v-btn
                    icon="mdi-delete"
                    size="small"
                    variant="text"
                    @click="removeZone(index)"
                  ></v-btn>
                </template>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="8">
        <v-card>
          <v-card-title>
            區域繪製
            <v-spacer></v-spacer>
            <v-chip v-if="drawingPoints.length > 0" size="small">
              {{ drawingPoints.length }} 個點
            </v-chip>
          </v-card-title>
          <v-card-text>
            <div class="canvas-wrapper">
              <canvas
                ref="canvas"
                :width="canvasWidth"
                :height="canvasHeight"
                @click="handleCanvasClick"
                @dblclick="handleCanvasDoubleClick"
                @mousemove="handleMouseMove"
              ></canvas>
            </div>
            <div v-if="!previewUrl" class="text-center text-grey py-12">
              請上傳背景圖片
            </div>
          </v-card-text>
        </v-card>

        <!-- 座標轉換工具 -->
        <v-card class="mt-4">
          <v-card-title>座標轉換工具</v-card-title>
          <v-card-text>
            <v-row>
              <v-col cols="4">
                <v-select
                  v-model="convertFrom"
                  :items="coordFormats"
                  label="來源格式"
                ></v-select>
              </v-col>
              <v-col cols="4">
                <v-select
                  v-model="convertTo"
                  :items="coordFormats"
                  label="目標格式"
                ></v-select>
              </v-col>
              <v-col cols="4">
                <v-btn
                  color="primary"
                  block
                  class="mt-2"
                  @click="convertCoordinates"
                >
                  轉換
                </v-btn>
              </v-col>
            </v-row>
            <v-textarea
              v-model="coordInput"
              label="輸入座標"
              rows="2"
              class="mt-4"
            ></v-textarea>
            <v-textarea
              v-model="coordOutput"
              label="輸出座標"
              rows="2"
              readonly
              class="mt-2"
            ></v-textarea>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import api from '../services/api'
import ImageUploader from '../components/common/ImageUploader.vue'

const imageFile = ref(null)
const previewUrl = ref(null)
const zoneType = ref('polygon')
const triggerPosition = ref('center')
const drawingPoints = ref([])
const zones = ref([])
const canvas = ref(null)
const ctx = ref(null)
const canvasWidth = ref(800)
const canvasHeight = ref(600)
const image = ref(null)
const currentMousePos = ref(null)

// 座標轉換
const convertFrom = ref('xyxy')
const convertTo = ref('xywh')
const coordInput = ref('')
const coordOutput = ref('')

const positions = [
  { id: 'center', name: '中心' },
  { id: 'bottom_center', name: '底部中心' },
  { id: 'top_center', name: '頂部中心' },
]

const coordFormats = ['xyxy', 'xywh', 'xcycwh']

const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']

const canCreateZone = computed(() => {
  if (zoneType.value === 'polygon') {
    return drawingPoints.value.length >= 3
  } else {
    return drawingPoints.value.length === 2
  }
})

onMounted(() => {
  if (canvas.value) {
    ctx.value = canvas.value.getContext('2d')
  }
})

watch(previewUrl, (url) => {
  if (url) {
    loadImage(url)
  }
})

const handlePreview = (url) => {
  previewUrl.value = url
}

const loadImage = (url) => {
  image.value = new Image()
  image.value.onload = () => {
    const maxWidth = 800
    const maxHeight = 600
    const scale = Math.min(maxWidth / image.value.width, maxHeight / image.value.height, 1)
    
    canvasWidth.value = image.value.width * scale
    canvasHeight.value = image.value.height * scale
    
    setTimeout(() => {
      draw()
    }, 0)
  }
  image.value.src = url
}

const draw = () => {
  if (!ctx.value) return
  
  ctx.value.clearRect(0, 0, canvasWidth.value, canvasHeight.value)
  
  // 繪製圖片
  if (image.value) {
    ctx.value.drawImage(image.value, 0, 0, canvasWidth.value, canvasHeight.value)
  }
  
  // 繪製已創建的區域
  zones.value.forEach((zone, index) => {
    ctx.value.strokeStyle = zone.color
    ctx.value.lineWidth = 2
    
    if (zone.type === 'polygon') {
      ctx.value.beginPath()
      ctx.value.moveTo(zone.points[0][0], zone.points[0][1])
      zone.points.forEach(([x, y]) => ctx.value.lineTo(x, y))
      ctx.value.closePath()
      ctx.value.stroke()
      ctx.value.fillStyle = zone.color + '33'
      ctx.value.fill()
    } else {
      ctx.value.beginPath()
      ctx.value.moveTo(zone.points[0][0], zone.points[0][1])
      ctx.value.lineTo(zone.points[1][0], zone.points[1][1])
      ctx.value.stroke()
    }
  })
  
  // 繪製正在繪製的點
  if (drawingPoints.value.length > 0) {
    ctx.value.strokeStyle = '#FF6B6B'
    ctx.value.fillStyle = '#FF6B6B'
    ctx.value.lineWidth = 2
    
    // 繪製點
    drawingPoints.value.forEach(([x, y]) => {
      ctx.value.beginPath()
      ctx.value.arc(x, y, 5, 0, Math.PI * 2)
      ctx.value.fill()
    })
    
    // 繪製線
    if (drawingPoints.value.length > 1) {
      ctx.value.beginPath()
      ctx.value.moveTo(drawingPoints.value[0][0], drawingPoints.value[0][1])
      drawingPoints.value.forEach(([x, y]) => ctx.value.lineTo(x, y))
      
      // 如果是多邊形且有滑鼠位置，連接到滑鼠
      if (zoneType.value === 'polygon' && currentMousePos.value) {
        ctx.value.lineTo(currentMousePos.value.x, currentMousePos.value.y)
      }
      
      ctx.value.stroke()
    }
  }
}

const handleCanvasClick = (e) => {
  const rect = canvas.value.getBoundingClientRect()
  const x = e.clientX - rect.left
  const y = e.clientY - rect.top
  
  if (zoneType.value === 'line' && drawingPoints.value.length >= 2) {
    return // 線區域只需要兩個點
  }
  
  drawingPoints.value.push([x, y])
  draw()
}

const handleCanvasDoubleClick = () => {
  if (zoneType.value === 'polygon' && drawingPoints.value.length >= 3) {
    createZone()
  }
}

const handleMouseMove = (e) => {
  const rect = canvas.value.getBoundingClientRect()
  currentMousePos.value = {
    x: e.clientX - rect.left,
    y: e.clientY - rect.top
  }
  draw()
}

const createZone = async () => {
  if (!canCreateZone.value) return
  
  try {
    const response = await api.createZone({
      zone_type: zoneType.value,
      coordinates: drawingPoints.value,
      triggering_position: triggerPosition.value
    })
    
    zones.value.push({
      id: response.zone_id,
      type: zoneType.value,
      points: [...drawingPoints.value],
      color: colors[zones.value.length % colors.length],
      in_count: response.in_count,
      out_count: response.out_count
    })
    
    clearPoints()
  } catch (error) {
    console.error('Create zone failed:', error)
    alert('創建區域失敗: ' + error.message)
  }
}

const clearPoints = () => {
  drawingPoints.value = []
  draw()
}

const removeZone = (index) => {
  zones.value.splice(index, 1)
  draw()
}

const convertCoordinates = async () => {
  try {
    const coords = coordInput.value.split(',').map(Number)
    const response = await api.convertCoordinates({
      source_format: convertFrom.value,
      target_format: convertTo.value,
      coordinates: coords
    })
    coordOutput.value = response.coordinates.join(', ')
  } catch (error) {
    console.error('Convert failed:', error)
    alert('轉換失敗: ' + error.message)
  }
}
</script>

<style scoped>
.canvas-wrapper {
  text-align: center;
  overflow: auto;
}

canvas {
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: crosshair;
}
</style>
