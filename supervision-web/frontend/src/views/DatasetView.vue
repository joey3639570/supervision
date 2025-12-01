<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <h1 class="text-h4 mb-2">資料集管理</h1>
        <p class="text-body-2 text-grey mb-4">資料集格式轉換、分割、合併</p>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>
            <v-icon left>mdi-swap-horizontal</v-icon>
            格式轉換
          </v-card-title>
          <v-card-text>
            <v-select
              v-model="convertSource"
              :items="formats"
              label="來源格式"
              item-title="name"
              item-value="id"
            ></v-select>

            <v-icon class="my-2">mdi-arrow-down</v-icon>

            <v-select
              v-model="convertTarget"
              :items="formats"
              label="目標格式"
              item-title="name"
              item-value="id"
            ></v-select>

            <v-file-input
              v-model="convertFiles"
              label="選擇資料集檔案"
              multiple
              chips
              class="mt-4"
            ></v-file-input>

            <v-btn
              color="primary"
              block
              class="mt-4"
              :loading="convertLoading"
              :disabled="!convertFiles || convertFiles.length === 0"
              @click="convertDataset"
            >
              開始轉換
            </v-btn>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>
            <v-icon left>mdi-content-cut</v-icon>
            資料集分割
          </v-card-title>
          <v-card-text>
            <v-slider
              v-model="trainRatio"
              label="訓練集比例"
              min="0"
              max="1"
              step="0.05"
              thumb-label
            ></v-slider>

            <v-slider
              v-model="testRatio"
              label="測試集比例"
              min="0"
              max="1"
              step="0.05"
              thumb-label
            ></v-slider>

            <v-alert
              v-if="validRatio < 0"
              type="error"
              density="compact"
              class="mb-4"
            >
              訓練集和測試集比例總和不能超過 1
            </v-alert>

            <v-alert
              v-else
              type="info"
              density="compact"
              class="mb-4"
            >
              驗證集比例: {{ (validRatio * 100).toFixed(0) }}%
            </v-alert>

            <v-file-input
              v-model="splitFiles"
              label="選擇資料集檔案"
              multiple
              chips
            ></v-file-input>

            <v-btn
              color="primary"
              block
              class="mt-4"
              :loading="splitLoading"
              :disabled="!splitFiles || splitFiles.length === 0 || validRatio < 0"
              @click="splitDataset"
            >
              開始分割
            </v-btn>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 結果區域 -->
    <v-row v-if="result">
      <v-col cols="12">
        <v-card>
          <v-card-title>
            <v-icon left color="success">mdi-check-circle</v-icon>
            處理結果
          </v-card-title>
          <v-card-text>
            <v-alert type="success">
              {{ result.message }}
            </v-alert>
            <v-btn
              v-if="result.downloadUrl"
              color="primary"
              variant="outlined"
              class="mt-4"
              @click="downloadResult"
            >
              <v-icon left>mdi-download</v-icon>
              下載結果
            </v-btn>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 格式說明 -->
    <v-row class="mt-4">
      <v-col cols="12">
        <v-card>
          <v-card-title>
            <v-icon left>mdi-information</v-icon>
            支援的格式
          </v-card-title>
          <v-card-text>
            <v-table>
              <thead>
                <tr>
                  <th>格式</th>
                  <th>說明</th>
                  <th>檔案類型</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="format in formats" :key="format.id">
                  <td>{{ format.name }}</td>
                  <td>{{ format.description }}</td>
                  <td>{{ format.fileTypes }}</td>
                </tr>
              </tbody>
            </v-table>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import api from '../services/api'

const formats = [
  { id: 'coco', name: 'COCO', description: 'MS COCO 格式', fileTypes: '.json' },
  { id: 'yolo', name: 'YOLO', description: 'YOLO 格式', fileTypes: '.txt, .yaml' },
  { id: 'pascal_voc', name: 'Pascal VOC', description: 'Pascal VOC XML 格式', fileTypes: '.xml' },
]

// 格式轉換
const convertSource = ref('coco')
const convertTarget = ref('yolo')
const convertFiles = ref(null)
const convertLoading = ref(false)

// 資料集分割
const trainRatio = ref(0.7)
const testRatio = ref(0.2)
const splitFiles = ref(null)
const splitLoading = ref(false)

// 結果
const result = ref(null)

const validRatio = computed(() => {
  return 1 - trainRatio.value - testRatio.value
})

const convertDataset = async () => {
  if (!convertFiles.value || convertFiles.value.length === 0) return

  convertLoading.value = true
  try {
    const response = await api.convertDataset(
      convertSource.value,
      convertTarget.value,
      convertFiles.value
    )
    result.value = response
  } catch (error) {
    console.error('Convert failed:', error)
    alert('轉換失敗: ' + error.message)
  } finally {
    convertLoading.value = false
  }
}

const splitDataset = async () => {
  if (!splitFiles.value || splitFiles.value.length === 0) return

  splitLoading.value = true
  try {
    const response = await api.splitDataset(
      trainRatio.value,
      testRatio.value,
      splitFiles.value
    )
    result.value = response
  } catch (error) {
    console.error('Split failed:', error)
    alert('分割失敗: ' + error.message)
  } finally {
    splitLoading.value = false
  }
}

const downloadResult = () => {
  if (result.value?.downloadUrl) {
    window.open(result.value.downloadUrl, '_blank')
  }
}
</script>
