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
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'

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
  showImage: {
    type: Boolean,
    default: true
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

const handleResize = () => {
  // 如果圖片已加載，重新計算尺寸
  if (image.value && image.value.complete) {
    const container = canvas.value?.parentElement
    let maxWidth = 1200
    let maxHeight = 800
    
    if (container) {
      const containerRect = container.getBoundingClientRect()
      if (containerRect.width > 0) {
        maxWidth = containerRect.width - 40
      }
      if (containerRect.height > 0) {
        maxHeight = Math.min(containerRect.height - 40, window.innerHeight - 200)
      }
    }
    
    // 計算最大縮放比例（允許放大以適應容器）
    const maxScale = Math.min(maxWidth / image.value.width, maxHeight / image.value.height)
    
    // 計算最小縮放比例，確保圖片至少 480x480
    const minWidth = 480
    const minHeight = 480
    const minScaleWidth = image.value.width < minWidth ? minWidth / image.value.width : 1
    const minScaleHeight = image.value.height < minHeight ? minHeight / image.value.height : 1
    const minScale = Math.max(minScaleWidth, minScaleHeight)
    
    // 使用最小和最大縮放比例中的較大值，確保圖片至少 480x480
    scale.value = Math.max(minScale, maxScale)
    
    canvasWidth.value = image.value.width * scale.value
    canvasHeight.value = image.value.height * scale.value
    
    // 重新繪製
    setTimeout(() => {
      draw()
    }, 100)  // 延遲一點以確保容器尺寸已更新
  }
}

onMounted(() => {
  ctx.value = canvas.value.getContext('2d')
  if (props.imageUrl) {
    loadImage(props.imageUrl)
  }
  
  // 監聽窗口大小變化，重新計算圖片尺寸
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})

watch(() => props.imageUrl, (newUrl) => {
  if (newUrl) {
    loadImage(newUrl)
  }
})

watch(() => props.detections, () => {
  draw()
}, { deep: true })

watch(() => props.masks, (newMasks, oldMasks) => {
  console.log(`[DetectionCanvas] Masks changed: ${newMasks?.length || 0} masks`)
  if (newMasks && newMasks.length > 0) {
    console.log(`[DetectionCanvas] First mask:`, newMasks[0])
  }
  draw()
}, { deep: true })

watch(() => props.showImage, () => {
  console.log(`[DetectionCanvas] showImage changed: ${props.showImage}`)
  draw()
})

const loadImage = (url) => {
  image.value = new Image()
  image.value.onload = () => {
    // 計算縮放比例 - 使用容器大小而不是固定值
    // 獲取容器元素
    const container = canvas.value?.parentElement
    let maxWidth = 1200  // 默认最大宽度
    let maxHeight = 800  // 默认最大高度
    
    if (container) {
      // 使用容器的实际可用空间
      const containerRect = container.getBoundingClientRect()
      if (containerRect.width > 0) {
        maxWidth = containerRect.width - 40  // 留出一些边距
      }
      if (containerRect.height > 0) {
        maxHeight = Math.min(containerRect.height - 40, window.innerHeight - 200)  // 留出一些边距，但不超过视口高度
      }
    }
    
    // 計算最大縮放比例，確保圖片完整顯示（允許放大以適應容器）
    const maxScale = Math.min(maxWidth / image.value.width, maxHeight / image.value.height)
    
    // 計算最小縮放比例，確保圖片至少 480x480
    const minWidth = 480
    const minHeight = 480
    const minScaleWidth = image.value.width < minWidth ? minWidth / image.value.width : 1
    const minScaleHeight = image.value.height < minHeight ? minHeight / image.value.height : 1
    const minScale = Math.max(minScaleWidth, minScaleHeight)
    
    // 使用最小和最大縮放比例中的較大值，確保圖片至少 480x480
    scale.value = Math.max(minScale, maxScale)
    
    canvasWidth.value = image.value.width * scale.value
    canvasHeight.value = image.value.height * scale.value
    
    console.log(`[DetectionCanvas] Image loaded: ${image.value.width}x${image.value.height}, scaled to: ${canvasWidth.value}x${canvasHeight.value}, scale: ${scale.value}`)
    
    // 等待 canvas 尺寸更新後再繪製
    setTimeout(() => {
      draw()
    }, 0)
  }
  image.value.src = url
}

const draw = async () => {
  if (!ctx.value || !image.value) return
  
  // 清除畫布
  ctx.value.clearRect(0, 0, canvasWidth.value, canvasHeight.value)
  
  // 繪製圖片（如果啟用）
  if (props.showImage) {
    ctx.value.drawImage(image.value, 0, 0, canvasWidth.value, canvasHeight.value)
  } else {
    // 如果不顯示原圖，填充黑色背景以便 mask 更明顯
    ctx.value.fillStyle = '#000000'
    ctx.value.fillRect(0, 0, canvasWidth.value, canvasHeight.value)
  }
  
  // 繪製遮罩（異步加載所有 mask 圖像後繪製）
  if (props.masks.length > 0) {
    await drawMasks()
  }
  
  // 繪製檢測框（在遮罩上方）
  if (props.detections.length > 0) {
    drawDetections()
  }
}

const drawMasks = async () => {
  if (!props.masks || props.masks.length === 0) {
    return
  }
  
  console.log(`[DetectionCanvas] Drawing ${props.masks.length} masks, showImage: ${props.showImage}`)
  
  // 加載所有 mask 圖像
  const maskData = await Promise.all(
    props.masks.map((mask, index) => {
      if (mask && mask.segmentation) {
        console.log(`[DetectionCanvas] Loading mask ${index}, has segmentation data`)
        return loadMaskImageData(mask.segmentation).catch(err => {
          console.warn(`[DetectionCanvas] Failed to load mask ${index}:`, err)
          return null
        })
      } else {
        console.log(`[DetectionCanvas] Mask ${index} has no segmentation data`)
      }
      return Promise.resolve(null)
    })
  )
  
  console.log(`[DetectionCanvas] Loaded ${maskData.filter(d => d !== null).length} mask images`)
  
  // 繪製所有遮罩
  maskData.forEach((data, index) => {
    if (!data) {
      // 如果沒有 segmentation，繪製邊界框區域的半透明填充
      const mask = props.masks[index]
      if (mask && mask.bbox) {
        console.log(`[DetectionCanvas] Drawing bbox fallback for mask ${index}`)
        const color = props.colors[index % props.colors.length]
        const [x1, y1, x2, y2] = mask.bbox.map((v, i) => v * scale.value)
        ctx.value.save()
        ctx.value.fillStyle = hexToRgba(color, 0.2)
        ctx.value.fillRect(x1, y1, x2 - x1, y2 - y1)
        ctx.value.restore()
      }
      return
    }
    
    const { imageData, width, height } = data
    const color = props.colors[index % props.colors.length]
    // 如果不顯示原圖（只顯示 mask），使用更高的不透明度
    const opacity = props.showImage ? 0.4 : 0.8
    
    console.log(`[DetectionCanvas] Drawing mask ${index}, size: ${width}x${height}, color: ${color}, opacity: ${opacity}`)
    
    // 保存當前 canvas 狀態
    ctx.value.save()
    
    // 創建臨時 canvas，使用原圖尺寸
    const tempCanvas = document.createElement('canvas')
    tempCanvas.width = image.value.width
    tempCanvas.height = image.value.height
    const tempCtx = tempCanvas.getContext('2d')
    
    // 創建一個臨時 canvas 來縮放 mask
    const maskCanvas = document.createElement('canvas')
    maskCanvas.width = width
    maskCanvas.height = height
    const maskCtx = maskCanvas.getContext('2d')
    maskCtx.putImageData(imageData, 0, 0)
    
    // 將 mask 縮放到原圖尺寸
    tempCtx.drawImage(maskCanvas, 0, 0, image.value.width, image.value.height)
    
    // 獲取縮放後的 ImageData
    const scaledImageData = tempCtx.getImageData(0, 0, image.value.width, image.value.height)
    const pixels = scaledImageData.data
    
    // 解析顏色
    const colorMatch = color.match(/^#([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i)
    if (!colorMatch) {
      console.error(`[DetectionCanvas] Invalid color format: ${color}`)
      ctx.value.restore()
      return
    }
    
    const r = parseInt(colorMatch[1], 16)
    const g = parseInt(colorMatch[2], 16)
    const b = parseInt(colorMatch[3], 16)
    const a = Math.floor(255 * opacity) // 0-255 範圍
    
    let maskPixelCount = 0
    
    // 直接操作像素：將白色/非黑色像素替換為指定顏色
    for (let i = 0; i < pixels.length; i += 4) {
      // 檢查是否是 mask 區域（非黑色像素）
      // mask 是灰度圖，白色(255)表示 mask 區域
      const gray = pixels[i] // R channel (grayscale)
      if (gray > 10) { // 使用閾值 10 而不是 0，避免抗鋸齒邊緣被忽略
        maskPixelCount++
        // 設置顏色和透明度
        pixels[i] = r     // R
        pixels[i + 1] = g // G
        pixels[i + 2] = b // B
        pixels[i + 3] = a // A (固定透明度)
      } else {
        // 黑色區域設為透明
        pixels[i + 3] = 0
      }
    }
    
    console.log(`[DetectionCanvas] Mask ${index} has ${maskPixelCount} mask pixels`)
    
    // 將處理後的 ImageData 放回 canvas
    tempCtx.putImageData(scaledImageData, 0, 0)
    
    // 繪製到主 canvas（縮放到顯示尺寸）
    ctx.value.globalCompositeOperation = 'source-over'
    ctx.value.globalAlpha = 1.0 // 確保不透明度
    ctx.value.drawImage(
      tempCanvas,
      0,
      0,
      canvasWidth.value,
      canvasHeight.value
    )
    
    // 恢復 canvas 狀態
    ctx.value.restore()
  })
  
  console.log(`[DetectionCanvas] Finished drawing masks`)
}

const loadMaskImageData = (base64Data) => {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => {
      // 創建臨時 canvas 來讀取 ImageData
      const tempCanvas = document.createElement('canvas')
      tempCanvas.width = img.width
      tempCanvas.height = img.height
      const tempCtx = tempCanvas.getContext('2d')
      tempCtx.drawImage(img, 0, 0)
      
      // 獲取 ImageData
      const imageData = tempCtx.getImageData(0, 0, img.width, img.height)
      
      resolve({
        imageData,
        width: img.width,
        height: img.height
      })
    }
    img.onerror = reject
    img.src = `data:image/png;base64,${base64Data}`
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
  display: flex;
  justify-content: center;
  align-items: flex-start;
  width: 100%;
  min-height: 200px;
}

canvas {
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: crosshair;
  max-width: 100%;
  height: auto;
  display: block;
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


