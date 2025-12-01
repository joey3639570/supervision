<template>
  <v-select
    v-model="selected"
    :items="annotators"
    :label="label"
    item-title="name"
    item-value="id"
    @update:model-value="handleChange"
  >
    <template v-slot:item="{ props, item }">
      <v-list-item v-bind="props">
        <template v-slot:prepend>
          <v-icon :icon="item.raw.icon"></v-icon>
        </template>
        <v-list-item-subtitle>{{ item.raw.description }}</v-list-item-subtitle>
      </v-list-item>
    </template>
  </v-select>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: 'box'
  },
  label: {
    type: String,
    default: '選擇標註器'
  }
})

const emit = defineEmits(['update:modelValue'])

const selected = ref(props.modelValue)

const annotators = [
  { id: 'box', name: '邊界框', icon: 'mdi-checkbox-blank-outline', description: '標準矩形邊界框' },
  { id: 'round_box', name: '圓角框', icon: 'mdi-checkbox-blank-outline', description: '圓角矩形邊界框' },
  { id: 'box_corner', name: '角框', icon: 'mdi-crop-square', description: '只顯示四個角' },
  { id: 'circle', name: '圓形', icon: 'mdi-circle-outline', description: '圓形標註' },
  { id: 'ellipse', name: '橢圓', icon: 'mdi-ellipse-outline', description: '橢圓形標註' },
  { id: 'mask', name: '遮罩', icon: 'mdi-texture-box', description: '分割遮罩' },
  { id: 'polygon', name: '多邊形', icon: 'mdi-shape-polygon-plus', description: '多邊形標註' },
  { id: 'blur', name: '模糊', icon: 'mdi-blur', description: '模糊效果' },
  { id: 'pixelate', name: '像素化', icon: 'mdi-grid', description: '像素化效果' },
  { id: 'heatmap', name: '熱力圖', icon: 'mdi-fire', description: '熱力圖視覺化' },
]

watch(() => props.modelValue, (newVal) => {
  selected.value = newVal
})

const handleChange = (value) => {
  emit('update:modelValue', value)
}
</script>

