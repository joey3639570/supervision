<template>
  <div class="detection-canvas-container">
    <canvas
      ref="canvas"
      :width="canvasWidth"
      :height="canvasHeight"
      @click="handleCanvasClick"
      @mousemove="handleMouseMove"
    ></canvas>
    
    <div v-if="showTooltip && hoveredDetection" class="detection-tooltip" :style="tooltipStyle">
      <div v-if="hoveredDetection.class_name">類別: {{ hoveredDetection.class_name }}</div>
      <div v-if="hoveredDetection.confidence">信心: {{ (hoveredDetection.confidence * 100).toFixed(1) }}%</div>
      <div v-if="hoveredDetection.tracker_id">追蹤 ID: {{ hoveredDetection.tracker_id }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue'

const props = defineProps({
  imageUrl: {
    type: String,
    default: null
  },
  detections: {
    type: Array,
    default: () => []
  },
  masks: {
    type: Array,
    default: () => []
  },
  annotatorType: {
    type: String,
    default: 'box'
  },
  colors: {
    type: Array,
    default: () => ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F']
  },
  showLabels: {
    type: Boolean,
    default: true
  },
  showTooltip: {
    type: Boolean,
    default: true
  },
  lineWidth: {
    type: Number,
    default: 2
  }
})

const emit = defineEmits(['click', 'detection-click'])

const canvas = ref(null)
const ctx = ref(null)
const image = ref(null)
const canvasWidth = ref(800)
const canvasHeight = ref(600)
const scale = ref(1)
const hoveredDetection = ref(null)
const tooltipPosition = ref({ x: 0, y: 0 })

const tooltipStyle = computed(() => ({
  left: `${tooltipPosition.value.x + 10}px`,
  top: `${tooltipPosition.value.y + 10}px`
}))

onMounted(() => {
  ctx.value = canvas.value.getContext('2d')
  if (props.imageUrl) {
    loadImage(props.imageUrl)
  }
})

watch(() => props.imageUrl, (newUrl) => {
  if (newUrl) {
    loadImage(newUrl)
  }
})

watch(() => props.detections, () => {
  draw()
}, { deep: true })

watch(() => props.masks, () => {
  draw()
}, { deep: true })

const loadImage = (url) => {
  image.value = new Image()
  image.value.onload = () => {
    // 計算縮放比例
    const maxWidth = 800
    const maxHeight = 600
    scale.value = Math.min(maxWidth / image.value.width, maxHeight / image.value.height, 1)
    
    canvasWidth.value = image.value.width * scale.value
    canvasHeight.value = image.value.height * scale.value
    
    // 等待 canvas 尺寸更新後再繪製
    setTimeout(() => {
      draw()
    }, 0)
  }
  image.value.src = url
}

const draw = () => {
  if (!ctx.value || !image.value) return
  
  // 清除畫布
  ctx.value.clearRect(0, 0, canvasWidth.value, canvasHeight.value)
  
  // 繪製圖片
  ctx.value.drawImage(image.value, 0, 0, canvasWidth.value, canvasHeight.value)
  
  // 繪製遮罩
  if (props.masks.length > 0) {
    drawMasks()
  }
  
  // 繪製檢測框
  if (props.detections.length > 0) {
    drawDetections()
  }
}

const drawMasks = () => {
  props.masks.forEach((mask, index) => {
    const color = props.colors[index % props.colors.length]
    ctx.value.fillStyle = hexToRgba(color, 0.3)
    
    // 如果有 segmentation 數據，繪製遮罩
    if (mask.segmentation) {
      // TODO: 解碼並繪製遮罩
    }
  })
}

const drawDetections = () => {
  props.detections.forEach((det, index) => {
    const color = props.colors[index % props.colors.length]
    const [x1, y1, x2, y2] = det.xyxy.map((v, i) => v * scale.value)
    
    ctx.value.strokeStyle = color
    ctx.value.lineWidth = props.lineWidth
    
    switch (props.annotatorType) {
      case 'box':
        drawBox(x1, y1, x2, y2)
        break
      case 'round_box':
        drawRoundBox(x1, y1, x2, y2, 8)
        break
      case 'box_corner':
        drawBoxCorner(x1, y1, x2, y2, 15)
        break
      case 'circle':
        drawCircle(x1, y1, x2, y2)
        break
      case 'ellipse':
        drawEllipse(x1, y1, x2, y2)
        break
      default:
        drawBox(x1, y1, x2, y2)
    }
    
    // 繪製標籤
    if (props.showLabels) {
      drawLabel(det, x1, y1, color)
    }
  })
}

const drawBox = (x1, y1, x2, y2) => {
  ctx.value.strokeRect(x1, y1, x2 - x1, y2 - y1)
}

const drawRoundBox = (x1, y1, x2, y2, radius) => {
  ctx.value.beginPath()
  ctx.value.roundRect(x1, y1, x2 - x1, y2 - y1, radius)
  ctx.value.stroke()
}

const drawBoxCorner = (x1, y1, x2, y2, cornerLength) => {
  ctx.value.beginPath()
  // 左上角
  ctx.value.moveTo(x1, y1 + cornerLength)
  ctx.value.lineTo(x1, y1)
  ctx.value.lineTo(x1 + cornerLength, y1)
  // 右上角
  ctx.value.moveTo(x2 - cornerLength, y1)
  ctx.value.lineTo(x2, y1)
  ctx.value.lineTo(x2, y1 + cornerLength)
  // 右下角
  ctx.value.moveTo(x2, y2 - cornerLength)
  ctx.value.lineTo(x2, y2)
  ctx.value.lineTo(x2 - cornerLength, y2)
  // 左下角
  ctx.value.moveTo(x1 + cornerLength, y2)
  ctx.value.lineTo(x1, y2)
  ctx.value.lineTo(x1, y2 - cornerLength)
  ctx.value.stroke()
}

const drawCircle = (x1, y1, x2, y2) => {
  const centerX = (x1 + x2) / 2
  const centerY = (y1 + y2) / 2
  const radius = Math.min(x2 - x1, y2 - y1) / 2
  ctx.value.beginPath()
  ctx.value.arc(centerX, centerY, radius, 0, Math.PI * 2)
  ctx.value.stroke()
}

const drawEllipse = (x1, y1, x2, y2) => {
  const centerX = (x1 + x2) / 2
  const centerY = (y1 + y2) / 2
  const radiusX = (x2 - x1) / 2
  const radiusY = (y2 - y1) / 2
  ctx.value.beginPath()
  ctx.value.ellipse(centerX, centerY, radiusX, radiusY, 0, 0, Math.PI * 2)
  ctx.value.stroke()
}

const drawLabel = (det, x, y, color) => {
  let label = ''
  if (det.class_name) {
    label = det.class_name
  } else if (det.class_id !== undefined) {
    label = `Class ${det.class_id}`
  }
  if (det.confidence) {
    label += ` ${(det.confidence * 100).toFixed(0)}%`
  }
  
  if (!label) return
  
  ctx.value.font = '12px Arial'
  const textWidth = ctx.value.measureText(label).width
  
  // 背景
  ctx.value.fillStyle = color
  ctx.value.fillRect(x, y - 18, textWidth + 8, 18)
  
  // 文字
  ctx.value.fillStyle = '#fff'
  ctx.value.fillText(label, x + 4, y - 5)
}

const handleCanvasClick = (e) => {
  const rect = canvas.value.getBoundingClientRect()
  const x = (e.clientX - rect.left) / scale.value
  const y = (e.clientY - rect.top) / scale.value
  
  emit('click', { x, y })
  
  // 檢查是否點擊了某個檢測框
  const clickedDet = props.detections.find(det => {
    const [x1, y1, x2, y2] = det.xyxy
    return x >= x1 && x <= x2 && y >= y1 && y <= y2
  })
  
  if (clickedDet) {
    emit('detection-click', clickedDet)
  }
}

const handleMouseMove = (e) => {
  if (!props.showTooltip) return
  
  const rect = canvas.value.getBoundingClientRect()
  const x = (e.clientX - rect.left) / scale.value
  const y = (e.clientY - rect.top) / scale.value
  
  tooltipPosition.value = { x: e.clientX - rect.left, y: e.clientY - rect.top }
  
  // 檢查是否懸停在某個檢測框上
  hoveredDetection.value = props.detections.find(det => {
    const [x1, y1, x2, y2] = det.xyxy
    return x >= x1 && x <= x2 && y >= y1 && y <= y2
  })
}

const hexToRgba = (hex, alpha) => {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}

// 暴露方法供父組件調用
defineExpose({
  draw,
  loadImage
})
</script>

<style scoped>
.detection-canvas-container {
  position: relative;
  display: inline-block;
}

canvas {
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: crosshair;
}

.detection-tooltip {
  position: absolute;
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 12px;
  pointer-events: none;
  z-index: 100;
}
</style>

