import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../services/api'

export const useDetectionStore = defineStore('detection', () => {
  // State
  const currentImage = ref(null)
  const currentImageUrl = ref(null)
  const detections = ref([])
  const loading = ref(false)
  const error = ref(null)
  const history = ref([])
  
  // Settings
  const settings = ref({
    model: 'yolov8n',
    confidence: 0.25,
    iou: 0.45,
    classes: [],
    annotator: 'box',
    showLabels: true,
    color: '#FF6B6B'
  })

  // Getters
  const detectionCount = computed(() => detections.value.length)
  
  const detectionsByClass = computed(() => {
    const grouped = {}
    detections.value.forEach(det => {
      const cls = det.class_name || 'unknown'
      if (!grouped[cls]) {
        grouped[cls] = []
      }
      grouped[cls].push(det)
    })
    return grouped
  })

  const classNames = computed(() => {
    return [...new Set(detections.value.map(d => d.class_name).filter(Boolean))]
  })

  // Actions
  async function detect(imageFile) {
    loading.value = true
    error.value = null
    
    try {
      currentImage.value = imageFile
      currentImageUrl.value = URL.createObjectURL(imageFile)
      
      const response = await api.detect(imageFile, {
        modelType: settings.value.model,
        confidence: settings.value.confidence,
        iou: settings.value.iou,
        classes: settings.value.classes
      })
      
      detections.value = response.detections || []
      
      // 添加到歷史記錄
      history.value.unshift({
        id: Date.now(),
        image: currentImageUrl.value,
        detections: detections.value.length,
        timestamp: new Date().toISOString(),
        model: settings.value.model
      })
      
      // 保留最近 10 條記錄
      if (history.value.length > 10) {
        history.value = history.value.slice(0, 10)
      }
      
      return response
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  function setImage(file, url) {
    currentImage.value = file
    currentImageUrl.value = url
  }

  function clearDetections() {
    detections.value = []
  }

  function updateSettings(newSettings) {
    settings.value = { ...settings.value, ...newSettings }
  }

  function removeDetection(index) {
    detections.value.splice(index, 1)
  }

  function addDetection(detection) {
    detections.value.push(detection)
  }

  function reset() {
    currentImage.value = null
    currentImageUrl.value = null
    detections.value = []
    error.value = null
  }

  return {
    // State
    currentImage,
    currentImageUrl,
    detections,
    loading,
    error,
    history,
    settings,
    
    // Getters
    detectionCount,
    detectionsByClass,
    classNames,
    
    // Actions
    detect,
    setImage,
    clearDetections,
    updateSettings,
    removeDetection,
    addDetection,
    reset
  }
})

