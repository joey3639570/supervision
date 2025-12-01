<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <h1 class="text-h4 mb-2">評估指標</h1>
        <p class="text-body-2 text-grey mb-4">計算 mAP、Precision、Recall、F1 等評估指標</p>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" md="4">
        <v-card>
          <v-card-title>設定</v-card-title>
          <v-card-text>
            <v-select
              v-model="selectedMetric"
              :items="metrics"
              label="選擇指標"
              item-title="name"
              item-value="id"
            ></v-select>

            <v-slider
              v-model="iouThreshold"
              label="IoU 閾值"
              min="0.1"
              max="0.95"
              step="0.05"
              thumb-label
              class="mt-4"
            ></v-slider>

            <v-divider class="my-4"></v-divider>

            <v-file-input
              v-model="groundTruthFile"
              label="真實標籤檔案"
              accept=".json,.txt"
              prepend-icon="mdi-target"
            ></v-file-input>

            <v-file-input
              v-model="predictionsFile"
              label="預測結果檔案"
              accept=".json,.txt"
              prepend-icon="mdi-robot"
              class="mt-4"
            ></v-file-input>

            <v-btn
              color="primary"
              block
              class="mt-4"
              :loading="loading"
              :disabled="!groundTruthFile || !predictionsFile"
              @click="calculateMetrics"
            >
              計算指標
            </v-btn>
          </v-card-text>
        </v-card>

        <!-- 指標說明 -->
        <v-card class="mt-4">
          <v-card-title>指標說明</v-card-title>
          <v-card-text>
            <v-expansion-panels>
              <v-expansion-panel
                v-for="metric in metrics"
                :key="metric.id"
              >
                <v-expansion-panel-title>
                  {{ metric.name }}
                </v-expansion-panel-title>
                <v-expansion-panel-text>
                  {{ metric.description }}
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="8">
        <!-- 結果顯示 -->
        <v-card v-if="result">
          <v-card-title>
            計算結果
            <v-spacer></v-spacer>
            <v-chip :color="getScoreColor(result.value)" size="large">
              {{ (result.value * 100).toFixed(2) }}%
            </v-chip>
          </v-card-title>
          <v-card-text>
            <v-progress-linear
              :model-value="result.value * 100"
              :color="getScoreColor(result.value)"
              height="30"
              striped
            >
              <template v-slot:default>
                {{ result.metric_type }}: {{ (result.value * 100).toFixed(2) }}%
              </template>
            </v-progress-linear>

            <!-- 詳細結果 -->
            <div v-if="result.details" class="mt-4">
              <h3 class="text-subtitle-1 mb-2">詳細結果</h3>
              <v-table density="compact">
                <thead>
                  <tr>
                    <th>項目</th>
                    <th>值</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(value, key) in result.details" :key="key">
                    <td>{{ key }}</td>
                    <td>{{ typeof value === 'number' ? value.toFixed(4) : value }}</td>
                  </tr>
                </tbody>
              </v-table>
            </div>
          </v-card-text>
        </v-card>

        <!-- 使用說明 -->
        <v-card v-else>
          <v-card-title>使用說明</v-card-title>
          <v-card-text>
            <v-timeline side="end" density="compact">
              <v-timeline-item dot-color="primary" size="small">
                <div class="text-body-2">
                  <strong>步驟 1:</strong> 選擇要計算的評估指標
                </div>
              </v-timeline-item>
              <v-timeline-item dot-color="primary" size="small">
                <div class="text-body-2">
                  <strong>步驟 2:</strong> 設定 IoU 閾值
                </div>
              </v-timeline-item>
              <v-timeline-item dot-color="primary" size="small">
                <div class="text-body-2">
                  <strong>步驟 3:</strong> 上傳真實標籤檔案 (ground truth)
                </div>
              </v-timeline-item>
              <v-timeline-item dot-color="primary" size="small">
                <div class="text-body-2">
                  <strong>步驟 4:</strong> 上傳預測結果檔案 (predictions)
                </div>
              </v-timeline-item>
              <v-timeline-item dot-color="success" size="small">
                <div class="text-body-2">
                  <strong>步驟 5:</strong> 點擊「計算指標」查看結果
                </div>
              </v-timeline-item>
            </v-timeline>

            <v-alert type="info" class="mt-4">
              <strong>檔案格式:</strong> JSON 或 TXT 格式，包含檢測框座標和類別資訊
            </v-alert>
          </v-card-text>
        </v-card>

        <!-- 歷史記錄 -->
        <v-card v-if="history.length > 0" class="mt-4">
          <v-card-title>計算歷史</v-card-title>
          <v-card-text>
            <v-table density="compact">
              <thead>
                <tr>
                  <th>指標</th>
                  <th>IoU 閾值</th>
                  <th>結果</th>
                  <th>時間</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, index) in history" :key="index">
                  <td>{{ item.metric }}</td>
                  <td>{{ item.iou }}</td>
                  <td>
                    <v-chip :color="getScoreColor(item.value)" size="small">
                      {{ (item.value * 100).toFixed(2) }}%
                    </v-chip>
                  </td>
                  <td>{{ item.time }}</td>
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
import { ref } from 'vue'
import api from '../services/api'

const metrics = [
  { id: 'mAP', name: 'mAP (Mean Average Precision)', description: '平均精度均值，綜合評估檢測器在不同召回率下的精度表現' },
  { id: 'precision', name: 'Precision (精確率)', description: '正確預測的正樣本數量 / 預測為正樣本的總數量' },
  { id: 'recall', name: 'Recall (召回率)', description: '正確預測的正樣本數量 / 實際正樣本的總數量' },
  { id: 'f1', name: 'F1 Score', description: 'Precision 和 Recall 的調和平均數' },
]

const selectedMetric = ref('mAP')
const iouThreshold = ref(0.5)
const groundTruthFile = ref(null)
const predictionsFile = ref(null)
const loading = ref(false)
const result = ref(null)
const history = ref([])

const calculateMetrics = async () => {
  if (!groundTruthFile.value || !predictionsFile.value) return

  loading.value = true
  try {
    // TODO: 解析檔案內容並發送到 API
    const response = await api.calculateMetrics({
      metric_type: selectedMetric.value,
      ground_truth: [], // 從檔案解析
      predictions: [], // 從檔案解析
      iou_threshold: iouThreshold.value
    })

    result.value = response
    
    // 添加到歷史記錄
    history.value.unshift({
      metric: selectedMetric.value,
      iou: iouThreshold.value,
      value: response.value,
      time: new Date().toLocaleTimeString()
    })
  } catch (error) {
    console.error('Calculation failed:', error)
    alert('計算失敗: ' + error.message)
  } finally {
    loading.value = false
  }
}

const getScoreColor = (score) => {
  if (score >= 0.8) return 'success'
  if (score >= 0.6) return 'primary'
  if (score >= 0.4) return 'warning'
  return 'error'
}
</script>
