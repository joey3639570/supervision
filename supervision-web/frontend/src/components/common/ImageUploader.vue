<template>
  <div class="image-uploader">
    <v-file-input
      v-model="file"
      :label="label"
      accept="image/*"
      prepend-icon="mdi-image"
      :disabled="disabled"
    ></v-file-input>
    
    <div
      v-if="showPreview && previewUrl"
      class="preview-container mt-4"
    >
      <img :src="previewUrl" alt="預覽" class="preview-image" />
    </div>

    <div
      v-if="showDropzone && !file"
      class="dropzone"
      :class="{ 'dragover': isDragOver }"
      @drop.prevent="handleDrop"
      @dragover.prevent="isDragOver = true"
      @dragleave="isDragOver = false"
      @click="triggerFileInput"
    >
      <v-icon size="48" color="grey">mdi-cloud-upload</v-icon>
      <p class="mt-2">拖放圖片到此處或點擊上傳</p>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  label: {
    type: String,
    default: '選擇圖片'
  },
  showPreview: {
    type: Boolean,
    default: true
  },
  showDropzone: {
    type: Boolean,
    default: false
  },
  disabled: {
    type: Boolean,
    default: false
  },
  modelValue: {
    type: [File, null],
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'change', 'preview'])

const file = ref(props.modelValue)
const previewUrl = ref(null)
const isDragOver = ref(false)

watch(() => props.modelValue, (newVal) => {
  if (newVal !== file.value) {
    file.value = newVal
  }
})

// 监听 file 的变化（v-file-input 的 v-model 会直接更新 file）
watch(file, (newFile, oldFile) => {
  // 只在文件实际变化时处理，避免初始化时的重复处理
  if (newFile !== oldFile) {
    handleFileChange(newFile)
  }
})

const handleFileChange = (newFile) => {
  // v-file-input 的 v-model 可能返回 File 对象或 File 数组
  let actualFile = null
  if (newFile instanceof File) {
    actualFile = newFile
  } else if (Array.isArray(newFile) && newFile.length > 0) {
    actualFile = newFile[0]
  } else if (newFile instanceof FileList && newFile.length > 0) {
    actualFile = newFile[0]
  }
  
  if (actualFile && actualFile instanceof File) {
    emit('update:modelValue', actualFile)
    emit('change', actualFile)
    
    // 生成預覽 URL
    const reader = new FileReader()
    reader.onload = (e) => {
      previewUrl.value = e.target.result
      emit('preview', e.target.result)
    }
    reader.readAsDataURL(actualFile)
  } else {
    previewUrl.value = null
    emit('update:modelValue', null)
  }
}

const handleDrop = (e) => {
  isDragOver.value = false
  const droppedFiles = e.dataTransfer.files
  if (droppedFiles.length > 0) {
    file.value = droppedFiles[0]
    // watch 会自动触发 handleFileChange，不需要手动调用
  }
}

const triggerFileInput = () => {
  document.querySelector('.v-file-input input').click()
}
</script>

<style scoped>
.preview-container {
  text-align: center;
}

.preview-image {
  max-width: 100%;
  max-height: 300px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.dropzone {
  border: 2px dashed #ccc;
  border-radius: 8px;
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
}

.dropzone:hover,
.dropzone.dragover {
  border-color: #1976D2;
  background-color: rgba(25, 118, 210, 0.05);
}
</style>


