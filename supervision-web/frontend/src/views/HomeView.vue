<template>
  <v-container>
    <!-- 歡迎區域 -->
    <v-row class="mb-8">
      <v-col cols="12">
        <div class="text-center">
          <h1 class="text-h3 font-weight-bold mb-4">
            Supervision Web
          </h1>
          <p class="text-h6 text-grey mb-6">
            完整的電腦視覺工具平台 - 檢測、分割、追蹤、標註一站式解決方案
          </p>
          <v-btn
            color="primary"
            size="large"
            rounded="pill"
            class="mr-4"
            to="/detect"
          >
            <v-icon left>mdi-play</v-icon>
            開始使用
          </v-btn>
          <v-btn
            variant="outlined"
            size="large"
            rounded="pill"
            href="https://supervision.roboflow.com/"
            target="_blank"
          >
            <v-icon left>mdi-book-open-variant</v-icon>
            文檔
          </v-btn>
        </div>
      </v-col>
    </v-row>

    <!-- 功能卡片 -->
    <v-row>
      <v-col
        v-for="feature in features"
        :key="feature.route"
        cols="12"
        sm="6"
        md="4"
      >
        <v-card
          :to="feature.route"
          class="feature-card h-100"
          elevation="2"
          hover
        >
          <v-card-item>
            <template v-slot:prepend>
              <v-avatar :color="feature.color" size="48">
                <v-icon color="white">{{ feature.icon }}</v-icon>
              </v-avatar>
            </template>
            <v-card-title>{{ feature.title }}</v-card-title>
            <v-card-subtitle>{{ feature.subtitle }}</v-card-subtitle>
          </v-card-item>
          <v-card-text>
            {{ feature.description }}
          </v-card-text>
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn variant="text" :color="feature.color">
              開始使用
              <v-icon right>mdi-arrow-right</v-icon>
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <!-- 統計資訊 -->
    <v-row class="mt-8">
      <v-col cols="12">
        <v-card>
          <v-card-title class="text-center">
            <v-icon left>mdi-chart-bar</v-icon>
            平台統計
          </v-card-title>
          <v-card-text>
            <v-row>
              <v-col
                v-for="stat in stats"
                :key="stat.label"
                cols="6"
                md="3"
              >
                <div class="stat-card">
                  <div class="stat-value" :style="{ color: stat.color }">
                    {{ stat.value }}
                  </div>
                  <div class="stat-label">{{ stat.label }}</div>
                </div>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 支援的模型 -->
    <v-row class="mt-8">
      <v-col cols="12">
        <v-card>
          <v-card-title>
            <v-icon left>mdi-cube-outline</v-icon>
            支援的模型
          </v-card-title>
          <v-card-text>
            <v-chip-group>
              <v-chip
                v-for="model in supportedModels"
                :key="model"
                variant="outlined"
                color="primary"
              >
                {{ model }}
              </v-chip>
            </v-chip-group>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 快速開始 -->
    <v-row class="mt-8">
      <v-col cols="12">
        <v-card>
          <v-card-title>
            <v-icon left>mdi-rocket-launch</v-icon>
            快速開始
          </v-card-title>
          <v-card-text>
            <v-timeline side="end" density="compact">
              <v-timeline-item
                v-for="(step, index) in quickStartSteps"
                :key="index"
                :dot-color="step.color"
                size="small"
              >
                <template v-slot:opposite>
                  <span class="text-caption text-grey">步驟 {{ index + 1 }}</span>
                </template>
                <div>
                  <strong>{{ step.title }}</strong>
                  <p class="text-body-2 text-grey mb-0">{{ step.description }}</p>
                </div>
              </v-timeline-item>
            </v-timeline>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAppStore } from '../stores/app'

const appStore = useAppStore()

const features = [
  {
    title: '物件檢測',
    subtitle: 'Object Detection',
    description: '使用 YOLO、Transformers 等模型進行即時物件檢測，支援多種標註風格',
    icon: 'mdi-target',
    color: '#FF6B6B',
    route: '/detect'
  },
  {
    title: '圖像分割',
    subtitle: 'SAM3 Segmentation',
    description: '使用 Segment Anything Model 3 進行精確的圖像分割，支援概念提示',
    icon: 'mdi-shape',
    color: '#4ECDC4',
    route: '/segment'
  },
  {
    title: '物件追蹤',
    subtitle: 'Object Tracking',
    description: '使用 ByteTrack 等演算法進行多物件追蹤，生成追蹤軌跡',
    icon: 'mdi-map-marker-path',
    color: '#45B7D1',
    route: '/track'
  },
  {
    title: '標註工具',
    subtitle: 'Annotation Tools',
    description: '20+ 種標註器，包括邊界框、遮罩、熱力圖、模糊效果等',
    icon: 'mdi-brush',
    color: '#96CEB4',
    route: '/annotate'
  },
  {
    title: '資料集管理',
    subtitle: 'Dataset Management',
    description: '資料集格式轉換、分割、合併，支援 COCO、YOLO、Pascal VOC',
    icon: 'mdi-database',
    color: '#FFEAA7',
    route: '/dataset'
  },
  {
    title: '評估指標',
    subtitle: 'Metrics Evaluation',
    description: '計算 mAP、Precision、Recall、F1 等評估指標',
    icon: 'mdi-chart-line',
    color: '#DDA0DD',
    route: '/metrics'
  },
  {
    title: '區域分析',
    subtitle: 'Zone Analytics',
    description: '創建多邊形區域和線區域進行物件計數和分析',
    icon: 'mdi-shape-polygon-plus',
    color: '#98D8C8',
    route: '/geometry'
  },
  {
    title: '影片處理',
    subtitle: 'Video Processing',
    description: '影片資訊獲取、幀提取、批量處理',
    icon: 'mdi-video',
    color: '#F7DC6F',
    route: '/video'
  }
]

const stats = ref([
  { label: '支援模型', value: '10+', color: '#1976D2' },
  { label: '標註器', value: '20+', color: '#4CAF50' },
  { label: '資料格式', value: '3', color: '#FF9800' },
  { label: '評估指標', value: '4', color: '#9C27B0' }
])

const supportedModels = [
  'YOLOv5',
  'YOLOv8',
  'YOLO-World',
  'RT-DETR',
  'SAM',
  'SAM2',
  'SAM3',
  'Transformers',
  'Inference',
  'DETR'
]

const quickStartSteps = [
  {
    title: '選擇功能',
    description: '選擇需要的功能：檢測、分割、追蹤或標註',
    color: 'primary'
  },
  {
    title: '上傳圖片或影片',
    description: '上傳要處理的圖片或影片檔案',
    color: 'secondary'
  },
  {
    title: '配置參數',
    description: '選擇模型、調整閾值等參數',
    color: 'success'
  },
  {
    title: '查看結果',
    description: '查看處理結果並下載標註後的檔案',
    color: 'warning'
  }
]

onMounted(() => {
  appStore.fetchModels()
})
</script>

<style scoped>
.feature-card {
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-4px);
}

.h-100 {
  height: 100%;
}
</style>
