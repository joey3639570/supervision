import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../services/api'

export const useAppStore = defineStore('app', () => {
  // State
  const models = ref([])
  const loadingModels = ref(false)
  const theme = ref('light')
  const sidebarOpen = ref(true)
  const notifications = ref([])

  // Getters
  const detectionModels = computed(() => {
    return models.value.filter(m => m.type === 'detection')
  })

  const segmentationModels = computed(() => {
    return models.value.filter(m => m.type === 'segmentation')
  })

  const hasModels = computed(() => models.value.length > 0)

  // Actions
  async function fetchModels() {
    loadingModels.value = true
    try {
      const response = await api.getModels()
      models.value = response.models || []
      return models.value
    } catch (error) {
      console.error('Failed to fetch models:', error)
      addNotification({
        type: 'error',
        message: '無法載入模型列表'
      })
      return []
    } finally {
      loadingModels.value = false
    }
  }

  function toggleTheme() {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
    localStorage.setItem('theme', theme.value)
  }

  function toggleSidebar() {
    sidebarOpen.value = !sidebarOpen.value
  }

  function addNotification(notification) {
    const id = Date.now()
    notifications.value.push({ ...notification, id })
    
    // 5 秒後自動移除
    setTimeout(() => {
      removeNotification(id)
    }, 5000)
  }

  function removeNotification(id) {
    const index = notifications.value.findIndex(n => n.id === id)
    if (index !== -1) {
      notifications.value.splice(index, 1)
    }
  }

  function initTheme() {
    const savedTheme = localStorage.getItem('theme')
    if (savedTheme) {
      theme.value = savedTheme
    } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
      theme.value = 'dark'
    }
  }

  return {
    // State
    models,
    loadingModels,
    theme,
    sidebarOpen,
    notifications,
    
    // Getters
    detectionModels,
    segmentationModels,
    hasModels,
    
    // Actions
    fetchModels,
    toggleTheme,
    toggleSidebar,
    addNotification,
    removeNotification,
    initTheme
  }
})


