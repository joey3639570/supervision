<template>
  <div class="video-uploader">
    <v-file-input
      v-model="file"
      :label="label"
      accept="video/*"
      prepend-icon="mdi-video"
      @change="handleFileChange"
      :disabled="disabled"
    ></v-file-input>
    
    <div v-if="showPreview && previewUrl" class="preview-container mt-4">
      <video
        ref="videoElement"
        :src="previewUrl"
        controls
        class="preview-video"
        @loadedmetadata="handleMetadataLoaded"
      ></video>
      
      <div v-if="videoInfo" class="video-info mt-2">
        <v-chip size="small" class="mr-2">
          {{ videoInfo.width }}x{{ videoInfo.height }}
        </v-chip>
        <v-chip size="small" class="mr-2">
          {{ videoInfo.duration.toFixed(1) }}s
        </v-chip>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  label: {
    type: String,
    default: '選擇影片'
  },
  showPreview: {
    type: Boolean,
    default: true
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

const emit = defineEmits(['update:modelValue', 'change', 'metadata'])

const file = ref(props.modelValue)
const previewUrl = ref(null)
const videoElement = ref(null)
const videoInfo = ref(null)

watch(() => props.modelValue, (newVal) => {
  file.value = newVal
})

const handleFileChange = (newFile) => {
  if (newFile) {
    emit('update:modelValue', newFile)
    emit('change', newFile)
    previewUrl.value = URL.createObjectURL(newFile)
  } else {
    previewUrl.value = null
    videoInfo.value = null
    emit('update:modelValue', null)
  }
}

const handleMetadataLoaded = () => {
  if (videoElement.value) {
    videoInfo.value = {
      width: videoElement.value.videoWidth,
      height: videoElement.value.videoHeight,
      duration: videoElement.value.duration
    }
    emit('metadata', videoInfo.value)
  }
}
</script>

<style scoped>
.preview-container {
  text-align: center;
}

.preview-video {
  max-width: 100%;
  max-height: 400px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.video-info {
  text-align: center;
}
</style>


