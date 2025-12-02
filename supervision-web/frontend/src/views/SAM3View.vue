<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <h1 class="text-h4 mb-2">SAM3 演示</h1>
        <p class="text-body-2 text-grey mb-4">使用 Segment Anything Model 3 進行對象檢測、計數和追蹤</p>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12">
        <v-tabs v-model="activeTab" bg-color="primary">
          <v-tab value="count">對象計數</v-tab>
          <v-tab value="multi">多提示詞檢測</v-tab>
          <v-tab value="line">線計數</v-tab>
          <v-tab value="zone">區域計數</v-tab>
          <v-tab value="track">對象追蹤</v-tab>
          <v-tab value="batch">批量處理</v-tab>
          <v-tab value="compare">對比視圖</v-tab>
        </v-tabs>

        <v-window v-model="activeTab">
          <!-- 對象計數 -->
          <v-window-item value="count">
            <v-card class="mt-4">
              <v-card-title>
                對象計數
                <v-spacer></v-spacer>
                <v-btn
                  v-if="countResult"
                  icon="mdi-download"
                  variant="text"
                  size="small"
                  @click="exportCountResults"
                ></v-btn>
              </v-card-title>
              <v-card-text>
                <v-row>
                  <v-col cols="12" md="4">
                    <v-file-input
                      v-model="countImageFile"
                      label="選擇圖片"
                      accept="image/*"
                      prepend-icon="mdi-image"
                      @change="handleCountImageChange"
                    ></v-file-input>

                    <v-text-field
                      v-model="countPrompt"
                      label="提示詞"
                      hint="例如: person, car, dog"
                      persistent-hint
                      class="mt-4"
                    ></v-text-field>

                    <v-slider
                      v-model="countConfidence"
                      label="信心閾值"
                      min="0"
                      max="1"
                      step="0.05"
                      thumb-label
                      class="mt-4"
                    ></v-slider>

                    <v-checkbox
                      v-model="showBoundingBoxes"
                      label="顯示邊界框"
                      class="mt-2"
                    ></v-checkbox>

                    <v-checkbox
                      v-model="showMasks"
                      label="顯示遮罩"
                      class="mt-2"
                    ></v-checkbox>

                    <v-checkbox
                      v-model="showLabels"
                      label="顯示標籤"
                      class="mt-2"
                    ></v-checkbox>

                    <v-btn
                      color="primary"
                      block
                      class="mt-4"
                      :loading="countLoading"
                      :disabled="!countImageFile || !countPrompt"
                      @click="handleCount"
                    >
                      開始計數
                    </v-btn>
                  </v-col>

                  <v-col cols="12" md="8">
                    <div class="image-preview-container">
                      <canvas
                        ref="countCanvas"
                        :style="{
                          'max-width': '100%',
                          'border': '1px solid #ddd',
                          'display': countImagePreview ? 'block' : 'none'
                        }"
                      ></canvas>
                      <div v-if="countImagePreview && countResult" class="result-overlay">
                        <v-alert type="success" density="compact">
                          <div>檢測到 {{ countResult.masks.length }} 個對象</div>
                          <div v-if="countResult.masks.length > 0">
                            平均信心: {{ (countResult.masks.reduce((sum, m) => sum + (m.confidence || 0), 0) / countResult.masks.length * 100).toFixed(1) }}%
                          </div>
                        </v-alert>
                      </div>
                      <div v-if="!countImagePreview" class="text-center text-grey py-12">
                        <v-icon size="64" color="grey-lighten-1">mdi-image-outline</v-icon>
                        <p class="mt-4">請上傳圖片開始計數</p>
                        <p class="text-caption text-grey">上傳圖片後，您可以在執行計數前預覽圖片</p>
                      </div>
                    </div>
                  </v-col>
                </v-row>
              </v-card-text>
            </v-card>
          </v-window-item>

          <!-- 多提示詞檢測 -->
          <v-window-item value="multi">
            <v-card class="mt-4">
              <v-card-title>
                多提示詞檢測
                <v-spacer></v-spacer>
                <v-btn
                  v-if="multiResult"
                  icon="mdi-download"
                  variant="text"
                  size="small"
                  @click="exportMultiResults"
                ></v-btn>
              </v-card-title>
              <v-card-text>
                <v-row>
                  <v-col cols="12" md="4">
                    <v-file-input
                      v-model="multiImageFile"
                      label="選擇圖片"
                      accept="image/*"
                      prepend-icon="mdi-image"
                      @change="handleMultiImageChange"
                    ></v-file-input>

                    <v-combobox
                      v-model="multiPrompts"
                      label="提示詞列表"
                      hint="輸入多個提示詞，用逗號分隔或按 Enter 添加"
                      persistent-hint
                      multiple
                      chips
                      closable-chips
                      class="mt-4"
                    ></v-combobox>

                    <v-slider
                      v-model="multiConfidence"
                      label="信心閾值"
                      min="0"
                      max="1"
                      step="0.05"
                      thumb-label
                      class="mt-4"
                    ></v-slider>

                    <v-btn
                      color="primary"
                      block
                      class="mt-4"
                      :loading="multiLoading"
                      :disabled="!multiImageFile || !multiPrompts || multiPrompts.length === 0"
                      @click="handleMultiPrompt"
                    >
                      開始檢測
                    </v-btn>

                    <v-card v-if="multiResult" class="mt-4">
                      <v-card-title>檢測結果</v-card-title>
                      <v-card-text>
                        <v-list density="compact">
                          <v-list-item
                            v-for="(count, prompt) in multiResult.prompt_counts"
                            :key="prompt"
                          >
                            <v-list-item-title>{{ prompt }}</v-list-item-title>
                            <v-list-item-subtitle>{{ count }} 個對象</v-list-item-subtitle>
                          </v-list-item>
                        </v-list>
                      </v-card-text>
                    </v-card>
                  </v-col>

                  <v-col cols="12" md="8">
                    <div v-if="multiImagePreview" class="image-preview-container">
                      <canvas
                        ref="multiCanvas"
                        :width="canvasWidth"
                        :height="canvasHeight"
                        style="max-width: 100%; border: 1px solid #ddd;"
                      ></canvas>
                    </div>
                  </v-col>
                </v-row>
              </v-card-text>
            </v-card>
          </v-window-item>

          <!-- 線計數 -->
          <v-window-item value="line">
            <v-card class="mt-4">
              <v-card-title>線計數</v-card-title>
              <v-card-text>
                <v-row>
                  <v-col cols="12" md="4">
                    <v-file-input
                      v-model="lineVideoFile"
                      label="選擇視頻"
                      accept="video/*"
                      prepend-icon="mdi-video"
                      @change="handleLineVideoChange"
                    ></v-file-input>

                    <v-text-field
                      v-model="linePrompt"
                      label="提示詞"
                      hint="例如: person, car"
                      persistent-hint
                      class="mt-4"
                    ></v-text-field>

                    <v-radio-group v-model="lineInputMode" label="線設置方式" class="mt-2">
                      <v-radio label="手動輸入座標" value="manual"></v-radio>
                      <v-radio label="畫布繪製" value="canvas"></v-radio>
                    </v-radio-group>

                    <template v-if="lineInputMode === 'manual'">
                      <v-row class="mt-2">
                        <v-col cols="6">
                          <v-text-field
                            v-model.number="lineStartX"
                            label="起點 X"
                            type="number"
                          ></v-text-field>
                        </v-col>
                        <v-col cols="6">
                          <v-text-field
                            v-model.number="lineStartY"
                            label="起點 Y"
                            type="number"
                          ></v-text-field>
                        </v-col>
                      </v-row>

                      <v-row>
                        <v-col cols="6">
                          <v-text-field
                            v-model.number="lineEndX"
                            label="終點 X"
                            type="number"
                          ></v-text-field>
                        </v-col>
                        <v-col cols="6">
                          <v-text-field
                            v-model.number="lineEndY"
                            label="終點 Y"
                            type="number"
                          ></v-text-field>
                        </v-col>
                      </v-row>
                    </template>

                    <template v-else>
                      <v-alert type="info" density="compact" class="mt-2">
                        在視頻預覽上點擊兩次來設置線的起點和終點
                      </v-alert>
                    </template>

                    <v-slider
                      v-model="lineConfidence"
                      label="信心閾值"
                      min="0"
                      max="1"
                      step="0.05"
                      thumb-label
                      class="mt-4"
                    ></v-slider>

                    <v-btn
                      color="primary"
                      block
                      class="mt-4"
                      :loading="lineLoading"
                      :disabled="!lineVideoFile || !linePrompt"
                      @click="handleLineCount"
                    >
                      開始處理
                    </v-btn>

                    <v-progress-linear
                      v-if="lineTaskId && lineProgress < 100"
                      :model-value="lineProgress"
                      color="primary"
                      class="mt-4"
                    ></v-progress-linear>

                    <div v-if="lineResult" class="mt-4">
                      <v-alert type="success" density="compact">
                        <div>穿過線的對象 (IN): {{ lineResult.in_count }}</div>
                        <div>穿過線的對象 (OUT): {{ lineResult.out_count }}</div>
                      </v-alert>
                      <v-btn
                        icon="mdi-download"
                        variant="text"
                        size="small"
                        @click="exportLineResults"
                      ></v-btn>
                      <video
                        v-if="lineResult.video_url"
                        :src="lineResult.video_url"
                        controls
                        preload="metadata"
                        style="width: 100%; margin-top: 16px;"
                        @error="handleVideoError('line', $event)"
                        @loadedmetadata="handleVideoLoaded('line')"
                      >
                        您的瀏覽器不支持視頻播放。
                      </video>
                    </div>
                  </v-col>

                  <v-col cols="12" md="8">
                    <div v-if="lineVideoPreview" class="video-preview">
                      <canvas
                        v-if="lineInputMode === 'canvas'"
                        ref="lineCanvas"
                        :width="lineCanvasWidth"
                        :height="lineCanvasHeight"
                        @click="handleLineCanvasClick"
                        style="max-width: 100%; border: 1px solid #ddd; cursor: crosshair;"
                      ></canvas>
                      <video
                        v-else
                        :src="lineVideoPreview"
                        controls
                        style="max-width: 100%;"
                      ></video>
                    </div>
                  </v-col>
                </v-row>
              </v-card-text>
            </v-card>
          </v-window-item>

          <!-- 區域計數 -->
          <v-window-item value="zone">
            <v-card class="mt-4">
              <v-card-title>區域計數</v-card-title>
              <v-card-text>
                <v-row>
                  <v-col cols="12" md="4">
                    <v-file-input
                      v-model="zoneVideoFile"
                      label="選擇視頻"
                      accept="video/*"
                      prepend-icon="mdi-video"
                      @change="handleZoneVideoChange"
                    ></v-file-input>

                    <v-text-field
                      v-model="zonePrompt"
                      label="提示詞"
                      hint="例如: person, car"
                      persistent-hint
                      class="mt-4"
                    ></v-text-field>

                    <v-radio-group v-model="zoneInputMode" label="區域設置方式" class="mt-2">
                      <v-radio label="JSON 配置" value="json"></v-radio>
                      <v-radio label="畫布繪製" value="canvas"></v-radio>
                    </v-radio-group>

                    <v-textarea
                      v-if="zoneInputMode === 'json'"
                      v-model="zoneConfig"
                      label="區域配置 (JSON)"
                      hint='格式: {"polygons": [[[x1,y1], [x2,y2], ...], ...]}'
                      persistent-hint
                      rows="5"
                      class="mt-4"
                    ></v-textarea>

                    <template v-else>
                      <v-alert type="info" density="compact" class="mt-2">
                        在視頻預覽上點擊多個點來繪製多邊形區域，雙擊完成
                      </v-alert>
                      <v-btn
                        variant="outlined"
                        size="small"
                        class="mt-2"
                        @click="clearZoneDrawing"
                      >
                        清除當前區域
                      </v-btn>
                    </template>

                    <v-slider
                      v-model="zoneConfidence"
                      label="信心閾值"
                      min="0"
                      max="1"
                      step="0.05"
                      thumb-label
                      class="mt-4"
                    ></v-slider>

                    <v-btn
                      color="primary"
                      block
                      class="mt-4"
                      :loading="zoneLoading"
                      :disabled="!zoneVideoFile || !zonePrompt"
                      @click="handleZoneCount"
                    >
                      開始處理
                    </v-btn>

                    <v-progress-linear
                      v-if="zoneTaskId && zoneProgress < 100"
                      :model-value="zoneProgress"
                      color="primary"
                      class="mt-4"
                    ></v-progress-linear>

                    <div v-if="zoneResult" class="mt-4">
                      <v-alert type="success" density="compact">
                        <div v-for="(count, index) in zoneResult.zone_counts" :key="index">
                          區域 {{ index + 1 }}: {{ count }} 個對象
                        </div>
                      </v-alert>
                      <v-btn
                        icon="mdi-download"
                        variant="text"
                        size="small"
                        @click="exportZoneResults"
                      ></v-btn>
                      <video
                        v-if="zoneResult.video_url"
                        :src="zoneResult.video_url"
                        controls
                        preload="metadata"
                        style="width: 100%; margin-top: 16px;"
                        @error="handleVideoError('zone', $event)"
                        @loadedmetadata="handleVideoLoaded('zone')"
                      >
                        您的瀏覽器不支持視頻播放。
                      </video>
                    </div>
                  </v-col>

                  <v-col cols="12" md="8">
                    <div v-if="zoneVideoPreview" class="video-preview">
                      <canvas
                        v-if="zoneInputMode === 'canvas'"
                        ref="zoneCanvas"
                        :width="zoneCanvasWidth"
                        :height="zoneCanvasHeight"
                        @click="handleZoneCanvasClick"
                        @dblclick="finishZonePolygon"
                        style="max-width: 100%; border: 1px solid #ddd; cursor: crosshair;"
                      ></canvas>
                      <video
                        v-else
                        :src="zoneVideoPreview"
                        controls
                        style="max-width: 100%;"
                      ></video>
                    </div>
                  </v-col>
                </v-row>
              </v-card-text>
            </v-card>
          </v-window-item>

          <!-- 對象追蹤 -->
          <v-window-item value="track">
            <v-card class="mt-4">
              <v-card-title>對象追蹤</v-card-title>
              <v-card-text>
                <v-row>
                  <v-col cols="12" md="4">
                    <v-file-input
                      v-model="trackVideoFile"
                      label="選擇視頻"
                      accept="video/*"
                      prepend-icon="mdi-video"
                    ></v-file-input>

                    <v-text-field
                      v-model="trackPrompt"
                      label="提示詞"
                      hint="例如: person, car"
                      persistent-hint
                      class="mt-4"
                    ></v-text-field>

                    <v-slider
                      v-model="trackConfidence"
                      label="信心閾值"
                      min="0"
                      max="1"
                      step="0.05"
                      thumb-label
                      class="mt-4"
                    ></v-slider>

                    <v-slider
                      v-model="trackTraceLength"
                      label="追蹤軌跡長度"
                      min="10"
                      max="100"
                      step="5"
                      thumb-label
                      class="mt-4"
                    ></v-slider>

                    <v-btn
                      color="primary"
                      block
                      class="mt-4"
                      :loading="trackLoading"
                      :disabled="!trackVideoFile || !trackPrompt"
                      @click="handleTrack"
                    >
                      開始追蹤
                    </v-btn>

                    <v-progress-linear
                      v-if="trackTaskId && trackProgress < 100"
                      :model-value="trackProgress"
                      color="primary"
                      class="mt-4"
                    ></v-progress-linear>

                    <div v-if="trackResult" class="mt-4">
                      <v-alert type="success" density="compact">
                        追蹤到 {{ trackResult.tracked_objects }} 個唯一對象
                      </v-alert>
                      <video
                        v-if="trackResult.video_url"
                        :src="trackResult.video_url"
                        controls
                        preload="metadata"
                        style="width: 100%; margin-top: 16px;"
                        @error="handleVideoError('track', $event)"
                        @loadedmetadata="handleVideoLoaded('track')"
                      >
                        您的瀏覽器不支持視頻播放。
                      </video>
                    </div>
                  </v-col>

                  <v-col cols="12" md="8">
                    <div v-if="trackVideoPreview" class="video-preview">
                      <video
                        :src="trackVideoPreview"
                        controls
                        style="max-width: 100%;"
                      ></video>
                    </div>
                  </v-col>
                </v-row>
              </v-card-text>
            </v-card>
          </v-window-item>

          <!-- 批量處理 -->
          <v-window-item value="batch">
            <v-card class="mt-4">
              <v-card-title>批量處理</v-card-title>
              <v-card-text>
                <v-row>
                  <v-col cols="12" md="4">
                    <v-file-input
                      v-model="batchFiles"
                      label="選擇多個文件"
                      accept="image/*,video/*"
                      prepend-icon="mdi-file-multiple"
                      multiple
                      @change="handleBatchFilesChange"
                    ></v-file-input>

                    <v-text-field
                      v-model="batchPrompt"
                      label="提示詞"
                      hint="例如: person, car"
                      persistent-hint
                      class="mt-4"
                    ></v-text-field>

                    <v-select
                      v-model="batchMode"
                      label="處理模式"
                      :items="[
                        { title: '對象計數', value: 'count' },
                        { title: '對象追蹤', value: 'track' }
                      ]"
                      class="mt-4"
                    ></v-select>

                    <v-slider
                      v-model="batchConfidence"
                      label="信心閾值"
                      min="0"
                      max="1"
                      step="0.05"
                      thumb-label
                      class="mt-4"
                    ></v-slider>

                    <v-btn
                      color="primary"
                      block
                      class="mt-4"
                      :loading="batchLoading"
                      :disabled="!batchFiles || batchFiles.length === 0 || !batchPrompt"
                      @click="handleBatchProcess"
                    >
                      開始批量處理
                    </v-btn>

                    <v-progress-linear
                      v-if="batchProgress > 0 && batchProgress < 100"
                      :model-value="batchProgress"
                      color="primary"
                      class="mt-4"
                    ></v-progress-linear>
                  </v-col>

                  <v-col cols="12" md="8">
                    <v-card v-if="batchResults.length > 0">
                      <v-card-title>處理結果</v-card-title>
                      <v-card-text>
                        <v-list>
                          <v-list-item
                            v-for="(result, index) in batchResults"
                            :key="index"
                          >
                            <v-list-item-title>{{ result.filename }}</v-list-item-title>
                            <v-list-item-subtitle>
                              {{ result.count }} 個對象
                            </v-list-item-subtitle>
                            <template v-slot:append>
                              <v-btn
                                icon="mdi-download"
                                variant="text"
                                size="small"
                                @click="downloadBatchResult(result)"
                              ></v-btn>
                            </template>
                          </v-list-item>
                        </v-list>
                        <v-btn
                          color="primary"
                          block
                          class="mt-4"
                          @click="exportBatchResults"
                        >
                          導出所有結果
                        </v-btn>
                      </v-card-text>
                    </v-card>
                  </v-col>
                </v-row>
              </v-card-text>
            </v-card>
          </v-window-item>

          <!-- 對比視圖 -->
          <v-window-item value="compare">
            <v-card class="mt-4">
              <v-card-title>對比視圖</v-card-title>
              <v-card-text>
                <v-row>
                  <v-col cols="12" md="6">
                    <v-card>
                      <v-card-title>原始圖像</v-card-title>
                      <v-card-text>
                        <v-file-input
                          v-model="compareImageFile"
                          label="選擇圖片"
                          accept="image/*"
                          prepend-icon="mdi-image"
                          @change="handleCompareImageChange"
                        ></v-file-input>
                        <div class="image-preview-container">
                          <canvas
                            ref="compareCanvas"
                            :style="{
                              'max-width': '100%',
                              'border': '1px solid #ddd',
                              'display': compareImagePreview ? 'block' : 'none'
                            }"
                          ></canvas>
                          <div v-if="!compareImagePreview" class="text-center text-grey py-8">
                            <v-icon size="48" color="grey-lighten-1">mdi-image-outline</v-icon>
                            <p class="mt-2 text-caption">請上傳圖片預覽</p>
                          </div>
                        </div>
                      </v-card-text>
                    </v-card>
                  </v-col>

                  <v-col cols="12" md="6">
                    <v-card>
                      <v-card-title>檢測結果</v-card-title>
                      <v-card-text>
                        <v-text-field
                          v-model="comparePrompt"
                          label="提示詞"
                          class="mb-4"
                        ></v-text-field>
                        <v-btn
                          color="primary"
                          block
                          :loading="compareLoading"
                          :disabled="!compareImageFile || !comparePrompt"
                          @click="handleCompare"
                        >
                          開始檢測
                        </v-btn>
                        <div v-if="compareResult && compareImagePreview" class="mt-4">
                          <v-alert type="success" density="compact">
                            檢測到 {{ compareResult.masks.length }} 個對象
                          </v-alert>
                          <p class="text-caption text-grey mt-2">檢測結果已繪製在上方的圖片預覽中</p>
                        </div>
                        <div v-else-if="!compareImagePreview" class="text-center text-grey py-8">
                          <v-icon size="48" color="grey-lighten-1">mdi-image-outline</v-icon>
                          <p class="mt-2 text-caption">請上傳圖片開始檢測</p>
                        </div>
                      </v-card-text>
                    </v-card>
                  </v-col>
                </v-row>
              </v-card-text>
            </v-card>
          </v-window-item>
        </v-window>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import api from '../services/api'

export default {
  name: 'SAM3View',
  data() {
    return {
      activeTab: 'count',
      canvasWidth: 800,
      canvasHeight: 600,
      // 保存原始图片尺寸和缩放比例
      originalImageWidth: null,
      originalImageHeight: null,
      imageScale: 1,
      
      // 對象計數
      countImageFile: null,
      countImagePreview: null,
      countPrompt: 'person',
      countConfidence: 0.5,
      countLoading: false,
      countResult: null,
      showBoundingBoxes: true,
      showMasks: true,
      showLabels: true,
      
      // 多提示詞檢測
      multiImageFile: null,
      multiImagePreview: null,
      multiPrompts: ['person', 'car'],
      multiConfidence: 0.5,
      multiLoading: false,
      multiResult: null,
      
      // 線計數
      lineVideoFile: null,
      lineVideoPreview: null,
      linePrompt: 'person',
      lineStartX: 0,
      lineStartY: 540,
      lineEndX: 1920,
      lineEndY: 540,
      lineConfidence: 0.5,
      lineLoading: false,
      lineTaskId: null,
      lineProgress: 0,
      lineResult: null,
      linePollInterval: null,
      lineInputMode: 'manual',
      lineDrawingPoints: [],
      lineVideoFrame: null, // 保存視頻第一幀的 Image 對象
      lineCanvasWidth: 800,
      lineCanvasHeight: 600,
      
      // 區域計數
      zoneVideoFile: null,
      zoneVideoPreview: null,
      zonePrompt: 'person',
      zoneConfig: JSON.stringify({
        polygons: [
          [[100, 100], [500, 100], [500, 400], [100, 400]]
        ]
      }, null, 2),
      zoneConfidence: 0.5,
      zoneLoading: false,
      zoneTaskId: null,
      zoneProgress: 0,
      zoneResult: null,
      zonePollInterval: null,
      zoneInputMode: 'json',
      zoneDrawingPolygons: [],
      currentZonePoints: [],
      zoneVideoFrame: null, // 保存視頻第一幀的 Image 對象
      zoneCanvasWidth: 800,
      zoneCanvasHeight: 600,
      
      // 對象追蹤
      trackVideoFile: null,
      trackVideoPreview: null,
      trackPrompt: 'person',
      trackConfidence: 0.5,
      trackTraceLength: 30,
      trackLoading: false,
      trackTaskId: null,
      trackProgress: 0,
      trackResult: null,
      trackPollInterval: null,
      
      // 批量處理
      batchFiles: null,
      batchPrompt: 'person',
      batchMode: 'count',
      batchConfidence: 0.5,
      batchLoading: false,
      batchProgress: 0,
      batchResults: [],
      
      // 對比視圖
      compareImageFile: null,
      compareImagePreview: null,
      comparePrompt: 'person',
      compareLoading: false,
      compareResult: null,
    }
  },
  watch: {
    lineInputMode(newMode) {
      // 當切換到 canvas 模式時，如果視頻已上傳，自動加載第一幀
      if (newMode === 'canvas' && this.lineVideoPreview) {
        // 等待 DOM 更新，確保 canvas 已經渲染
        this.$nextTick(() => {
          // 使用 setTimeout 確保 canvas ref 已經準備好
          setTimeout(() => {
            if (this.$refs.lineCanvas) {
              console.log('[SAM3View] Loading video frame to line canvas')
              this.loadVideoFrameToCanvas(this.$refs.lineCanvas, this.lineVideoPreview)
            } else {
              console.warn('[SAM3View] Line canvas ref not available, retrying...')
              // 如果 ref 還沒準備好，再試一次
              setTimeout(() => {
                if (this.$refs.lineCanvas && this.lineVideoPreview) {
                  this.loadVideoFrameToCanvas(this.$refs.lineCanvas, this.lineVideoPreview)
                }
              }, 200)
            }
          }, 100)
        })
      }
    },
    zoneInputMode(newMode) {
      // 當切換到 canvas 模式時，如果視頻已上傳，自動加載第一幀
      if (newMode === 'canvas' && this.zoneVideoPreview) {
        // 等待 DOM 更新，確保 canvas 已經渲染
        this.$nextTick(() => {
          // 使用 setTimeout 確保 canvas ref 已經準備好
          setTimeout(() => {
            if (this.$refs.zoneCanvas) {
              console.log('[SAM3View] Loading video frame to zone canvas')
              this.loadVideoFrameToCanvas(this.$refs.zoneCanvas, this.zoneVideoPreview)
            } else {
              console.warn('[SAM3View] Zone canvas ref not available, retrying...')
              // 如果 ref 還沒準備好，再試一次
              setTimeout(() => {
                if (this.$refs.zoneCanvas && this.zoneVideoPreview) {
                  this.loadVideoFrameToCanvas(this.$refs.zoneCanvas, this.zoneVideoPreview)
                }
              }, 200)
            }
          }, 100)
        })
      }
    }
  },
  mounted() {
    this.setupCanvas()
  },
  beforeUnmount() {
    this.clearPollIntervals()
    // 清理所有 blob URL，避免內存洩漏
    if (this.lineVideoPreview && this.lineVideoPreview.startsWith('blob:')) {
      URL.revokeObjectURL(this.lineVideoPreview)
    }
    if (this.zoneVideoPreview && this.zoneVideoPreview.startsWith('blob:')) {
      URL.revokeObjectURL(this.zoneVideoPreview)
    }
    if (this.trackVideoPreview && this.trackVideoPreview.startsWith('blob:')) {
      URL.revokeObjectURL(this.trackVideoPreview)
    }
    if (this.countImagePreview && this.countImagePreview.startsWith('blob:')) {
      URL.revokeObjectURL(this.countImagePreview)
    }
    if (this.multiImagePreview && this.multiImagePreview.startsWith('blob:')) {
      URL.revokeObjectURL(this.multiImagePreview)
    }
    if (this.compareImagePreview && this.compareImagePreview.startsWith('blob:')) {
      URL.revokeObjectURL(this.compareImagePreview)
    }
  },
  methods: {
    setupCanvas() {
      // Setup canvas contexts when components mount
      this.$nextTick(() => {
        if (this.$refs.countCanvas) {
          this.drawCountResults()
        }
        if (this.$refs.multiCanvas) {
          this.drawMultiResults()
        }
        if (this.$refs.compareCanvas) {
          this.drawCompareResults()
        }
      })
    },
    
    handleCountImageChange(event) {
      // v-file-input 的 @change 事件可能传递 Event 对象或 File 对象
      let file = null
      if (event instanceof File) {
        file = event
      } else if (event && event.target && event.target.files && event.target.files.length > 0) {
        file = event.target.files[0]
      } else if (this.countImageFile instanceof File) {
        // 如果事件对象无效，使用 v-model 绑定的值
        file = this.countImageFile
      }
      
      if (file && file instanceof File) {
        console.log('[SAM3View] File selected for count:', file.name)
        const reader = new FileReader()
        reader.onload = (e) => {
          console.log('[SAM3View] File read, setting preview URL')
          this.countImagePreview = e.target.result
          // 使用 $nextTick 确保 DOM 已更新
          this.$nextTick(() => {
            console.log('[SAM3View] NextTick, checking canvas ref:', !!this.$refs.countCanvas)
            if (this.$refs.countCanvas) {
              this.loadImageToCanvas(this.$refs.countCanvas, e.target.result)
            } else {
              // 如果 ref 还没准备好，延迟一下
              console.log('[SAM3View] Canvas ref not ready, retrying in 200ms')
              setTimeout(() => {
                if (this.$refs.countCanvas) {
                  console.log('[SAM3View] Canvas ref ready, loading image')
                  this.loadImageToCanvas(this.$refs.countCanvas, e.target.result)
                } else {
                  console.error('[SAM3View] Canvas ref still not available after delay')
                }
              }, 200)
            }
          })
        }
        reader.onerror = (err) => {
          console.error('[SAM3View] FileReader error:', err)
        }
        reader.readAsDataURL(file)
      } else {
        // 如果文件被清除，清除预览
        console.log('[SAM3View] File cleared')
        this.countImagePreview = null
        this.countResult = null
      }
    },
    
    handleMultiImageChange(event) {
      // v-file-input 的 @change 事件可能传递 Event 对象或 File 对象
      let file = null
      if (event instanceof File) {
        file = event
      } else if (event && event.target && event.target.files && event.target.files.length > 0) {
        file = event.target.files[0]
      } else if (this.multiImageFile instanceof File) {
        // 如果事件对象无效，使用 v-model 绑定的值
        file = this.multiImageFile
      }
      
      if (file && file instanceof File) {
        const reader = new FileReader()
        reader.onload = (e) => {
          this.multiImagePreview = e.target.result
          // 使用 $nextTick 确保 DOM 已更新
          this.$nextTick(() => {
            if (this.$refs.multiCanvas) {
              this.loadImageToCanvas(this.$refs.multiCanvas, e.target.result)
            } else {
              // 如果 ref 还没准备好，延迟一下
              setTimeout(() => {
                if (this.$refs.multiCanvas) {
                  this.loadImageToCanvas(this.$refs.multiCanvas, e.target.result)
                }
              }, 200)
            }
          })
        }
        reader.readAsDataURL(file)
      } else {
        // 如果文件被清除，清除预览
        this.multiImagePreview = null
        this.multiResult = null
      }
    },
    
    handleCompareImageChange(event) {
      // v-file-input 的 @change 事件可能传递 Event 对象或 File 对象
      let file = null
      if (event instanceof File) {
        file = event
      } else if (event && event.target && event.target.files && event.target.files.length > 0) {
        file = event.target.files[0]
      } else if (this.compareImageFile instanceof File) {
        // 如果事件对象无效，使用 v-model 绑定的值
        file = this.compareImageFile
      }
      
      if (file && file instanceof File) {
        const reader = new FileReader()
        reader.onload = (e) => {
          this.compareImagePreview = e.target.result
          // 使用 $nextTick 确保 DOM 已更新
          this.$nextTick(() => {
            if (this.$refs.compareCanvas) {
              this.loadImageToCanvas(this.$refs.compareCanvas, e.target.result)
            } else {
              // 如果 ref 还没准备好，延迟一下
              setTimeout(() => {
                if (this.$refs.compareCanvas) {
                  this.loadImageToCanvas(this.$refs.compareCanvas, e.target.result)
                }
              }, 200)
            }
          })
        }
        reader.readAsDataURL(file)
      } else {
        // 如果文件被清除，清除预览
        this.compareImagePreview = null
        this.compareResult = null
      }
    },
    
    handleLineVideoChange(event) {
      // v-file-input 的 @change 事件可能传递 Event 对象或 File 对象
      let file = null
      if (event instanceof File) {
        file = event
      } else if (event && event.target && event.target.files && event.target.files.length > 0) {
        file = event.target.files[0]
      } else if (this.lineVideoFile instanceof File) {
        // 如果事件对象无效，使用 v-model 绑定的值
        file = this.lineVideoFile
      }
      
      if (file && file instanceof File) {
        // 清理舊的 blob URL
        if (this.lineVideoPreview && this.lineVideoPreview.startsWith('blob:')) {
          URL.revokeObjectURL(this.lineVideoPreview)
        }
        
        // 重置繪製狀態
        this.lineDrawingPoints = []
        this.lineVideoFrame = null
        
        this.lineVideoPreview = URL.createObjectURL(file)
        if (this.lineInputMode === 'canvas') {
          // 等待 DOM 更新，確保 canvas 已經渲染
          this.$nextTick(() => {
            setTimeout(() => {
              if (this.$refs.lineCanvas) {
                console.log('[SAM3View] Loading video frame to line canvas after file change')
                this.loadVideoFrameToCanvas(this.$refs.lineCanvas, this.lineVideoPreview)
              }
            }, 100)
          })
        }
      }
    },
    
    handleZoneVideoChange(event) {
      // v-file-input 的 @change 事件可能传递 Event 对象或 File 对象
      let file = null
      if (event instanceof File) {
        file = event
      } else if (event && event.target && event.target.files && event.target.files.length > 0) {
        file = event.target.files[0]
      } else if (this.zoneVideoFile instanceof File) {
        // 如果事件对象无效，使用 v-model 绑定的值
        file = this.zoneVideoFile
      }
      
      if (file && file instanceof File) {
        // 清理舊的 blob URL
        if (this.zoneVideoPreview && this.zoneVideoPreview.startsWith('blob:')) {
          URL.revokeObjectURL(this.zoneVideoPreview)
        }
        
        // 重置繪製狀態
        this.zoneDrawingPolygons = []
        this.currentZonePoints = []
        this.zoneVideoFrame = null
        
        this.zoneVideoPreview = URL.createObjectURL(file)
        if (this.zoneInputMode === 'canvas') {
          // 等待 DOM 更新，確保 canvas 已經渲染
          this.$nextTick(() => {
            setTimeout(() => {
              if (this.$refs.zoneCanvas) {
                console.log('[SAM3View] Loading video frame to zone canvas after file change')
                this.loadVideoFrameToCanvas(this.$refs.zoneCanvas, this.zoneVideoPreview)
              }
            }, 100)
          })
        }
      }
    },
    
    loadImageToCanvas(canvas, imageSrc) {
      if (!canvas) {
        console.warn('[SAM3View] Canvas ref not available')
        return
      }
      console.log('[SAM3View] Loading image to canvas:', imageSrc.substring(0, 50) + '...')
      const ctx = canvas.getContext('2d')
      if (!ctx) {
        console.error('[SAM3View] Failed to get canvas context')
        return
      }
      const img = new Image()
      img.onload = () => {
        console.log('[SAM3View] Image loaded:', img.width, 'x', img.height)
        // 保存原始尺寸
        this.originalImageWidth = img.width
        this.originalImageHeight = img.height
        
        // 計算縮放比例的函數
        const calculateScale = () => {
          const container = canvas.parentElement
          let maxWidth = 1200  // 默认最大宽度
          let maxHeight = 800  // 默认最大高度
          
          if (container) {
            const containerRect = container.getBoundingClientRect()
            console.log('[SAM3View] Container rect:', containerRect.width, 'x', containerRect.height)
            if (containerRect.width > 0) {
              maxWidth = containerRect.width - 40  // 留出一些边距
            }
            if (containerRect.height > 0) {
              maxHeight = Math.min(containerRect.height - 40, window.innerHeight - 200)
            }
          }
          
          // 計算最大縮放比例，確保圖片完整顯示（允許放大以適應容器）
          const maxScale = Math.min(maxWidth / img.width, maxHeight / img.height)
          
          // 計算最小縮放比例，確保圖片至少 480x480
          const minWidth = 480
          const minHeight = 480
          const minScaleWidth = img.width < minWidth ? minWidth / img.width : 1
          const minScaleHeight = img.height < minHeight ? minHeight / img.height : 1
          const minScale = Math.max(minScaleWidth, minScaleHeight)
          
          // 使用最小和最大縮放比例中的較大值，確保圖片至少 480x480
          const scale = Math.max(minScale, maxScale)
          console.log('[SAM3View] Calculated scale:', scale, 'for image', img.width, 'x', img.height)
          return scale
        }
        
        // 繪製圖片的函數
        const drawImage = () => {
          const scale = calculateScale()
          this.imageScale = scale
          const displayWidth = img.width * scale
          const displayHeight = img.height * scale
          
          // 設置 canvas 的實際尺寸為圖片原始尺寸（用於高質量繪製）
          canvas.width = img.width
          canvas.height = img.height
          
          // 清除畫布
          ctx.clearRect(0, 0, canvas.width, canvas.height)
          
          // 繪製圖片到 canvas（使用原始尺寸）
          ctx.drawImage(img, 0, 0, img.width, img.height)
          
          // 設置顯示尺寸（CSS）
          canvas.style.width = `${displayWidth}px`
          canvas.style.height = `${displayHeight}px`
          
          // 更新響應式變量（用於模板綁定）
          this.canvasWidth = displayWidth
          this.canvasHeight = displayHeight
          
          console.log('[SAM3View] Image drawn to canvas:', {
            canvasSize: `${canvas.width}x${canvas.height}`,
            displaySize: `${displayWidth}x${displayHeight}`,
            scale: scale
          })
        }
        
        // 如果容器尺寸为0，延迟计算（等待DOM渲染）
        const container = canvas.parentElement
        const containerRect = container?.getBoundingClientRect()
        if (!containerRect || containerRect.width === 0 || containerRect.height === 0) {
          console.log('[SAM3View] Container not ready, delaying...')
          // 增加延迟时间，确保容器已渲染
          setTimeout(() => {
            drawImage()
          }, 300)
        } else {
          // 使用 $nextTick 確保 Vue 響應式更新完成
          this.$nextTick(() => {
            drawImage()
          })
        }
      }
      img.onerror = (err) => {
        console.error('[SAM3View] Failed to load image:', err)
      }
      img.src = imageSrc
    },
    
    loadVideoFrameToCanvas(canvas, videoSrc) {
      if (!canvas) {
        console.warn('[SAM3View] Canvas not available for loading video frame')
        return
      }
      
      console.log('[SAM3View] Loading video frame to canvas:', videoSrc.substring(0, 50) + '...')
      const video = document.createElement('video')
      video.preload = 'metadata'
      video.src = videoSrc
      
      video.onloadedmetadata = () => {
        console.log('[SAM3View] Video metadata loaded:', video.videoWidth, 'x', video.videoHeight)
        // 保存原始尺寸
        this.originalImageWidth = video.videoWidth
        this.originalImageHeight = video.videoHeight
        
        // 計算縮放比例的函數
        const calculateScale = () => {
          const container = canvas.parentElement
          let maxWidth = 1200  // 默认最大宽度
          let maxHeight = 800  // 默认最大高度
          
          if (container) {
            const containerRect = container.getBoundingClientRect()
            if (containerRect.width > 0) {
              maxWidth = containerRect.width - 40  // 留出一些边距
            }
            if (containerRect.height > 0) {
              maxHeight = Math.min(containerRect.height - 40, window.innerHeight - 200)
            }
          }
          
          // 計算最大縮放比例，確保視頻幀完整顯示（允許放大以適應容器）
          const maxScale = Math.min(maxWidth / video.videoWidth, maxHeight / video.videoHeight)
          
          // 計算最小縮放比例，確保視頻幀至少 480x480
          const minWidth = 480
          const minHeight = 480
          const minScaleWidth = video.videoWidth < minWidth ? minWidth / video.videoWidth : 1
          const minScaleHeight = video.videoHeight < minHeight ? minHeight / video.videoHeight : 1
          const minScale = Math.max(minScaleWidth, minScaleHeight)
          
          // 使用最小和最大縮放比例中的較大值，確保視頻幀至少 480x480
          return Math.max(minScale, maxScale)
        }
        
        // 繪製第一幀的函數
        const drawFrame = () => {
          console.log('[SAM3View] Drawing video frame to canvas')
          const ctx = canvas.getContext('2d')
          if (!ctx) {
            console.error('[SAM3View] Failed to get canvas context')
            return
          }
          
          // 確保 canvas 尺寸正確
          canvas.width = video.videoWidth
          canvas.height = video.videoHeight
          
          // 繪製視頻第一幀
          ctx.drawImage(video, 0, 0, video.videoWidth, video.videoHeight)
          
          // 保存第一幀為 Image 對象，以便後續重新繪製
          // 創建一個臨時 canvas 來保存第一幀
          const tempCanvas = document.createElement('canvas')
          tempCanvas.width = video.videoWidth
          tempCanvas.height = video.videoHeight
          const tempCtx = tempCanvas.getContext('2d')
          tempCtx.drawImage(video, 0, 0, video.videoWidth, video.videoHeight)
          
          const frameImage = new Image()
          frameImage.src = tempCanvas.toDataURL()
          frameImage.onload = () => {
            console.log('[SAM3View] Video frame image saved')
            // 根據 canvas 是哪一個，保存對應的 frame
            if (canvas === this.$refs.lineCanvas) {
              this.lineVideoFrame = frameImage
            } else if (canvas === this.$refs.zoneCanvas) {
              this.zoneVideoFrame = frameImage
            }
          }
          frameImage.onerror = (err) => {
            console.error('[SAM3View] Failed to save video frame image:', err)
          }
        }
        
        // 設置視頻時間到第一幀並繪製
        video.currentTime = 0.1
        video.onseeked = () => {
          console.log('[SAM3View] Video seeked to first frame')
          const scale = calculateScale()
          this.imageScale = scale
          
          // 根據 canvas 是哪一個，設置對應的尺寸
          if (canvas === this.$refs.lineCanvas) {
            this.lineCanvasWidth = video.videoWidth * scale
            this.lineCanvasHeight = video.videoHeight * scale
          } else if (canvas === this.$refs.zoneCanvas) {
            this.zoneCanvasWidth = video.videoWidth * scale
            this.zoneCanvasHeight = video.videoHeight * scale
          }
          
          drawFrame()
          
          // 設置顯示尺寸
          const displayWidth = video.videoWidth * scale
          const displayHeight = video.videoHeight * scale
          canvas.style.width = `${displayWidth}px`
          canvas.style.height = `${displayHeight}px`
          
          console.log('[SAM3View] Canvas size set to:', displayWidth, 'x', displayHeight)
        }
        
        video.onerror = (err) => {
          console.error('[SAM3View] Video loading error:', err)
        }
      }
      
      video.onerror = (err) => {
        console.error('[SAM3View] Video error:', err)
      }
    },
    
    async handleCount() {
      if (!this.countImageFile || !this.countPrompt) return
      
      this.countLoading = true
      this.countResult = null
      
      try {
        const result = await api.sam3Count(this.countImageFile, {
          prompt: this.countPrompt,
          confidence: this.countConfidence
        })
        
        this.countResult = result
        this.drawCountResults()
      } catch (error) {
        console.error('Count error:', error)
        alert('處理失敗: ' + (error.response?.data?.detail || error.message))
      } finally {
        this.countLoading = false
      }
    },
    
    async handleMultiPrompt() {
      if (!this.multiImageFile || !this.multiPrompts || this.multiPrompts.length === 0) return
      
      this.multiLoading = true
      this.multiResult = null
      
      try {
        const result = await api.sam3MultiPrompt(this.multiImageFile, {
          prompts: this.multiPrompts,
          confidence: this.multiConfidence
        })
        
        this.multiResult = result
        this.drawMultiResults()
      } catch (error) {
        console.error('Multi prompt error:', error)
        alert('處理失敗: ' + (error.response?.data?.detail || error.message))
      } finally {
        this.multiLoading = false
      }
    },
    
    // 加載 base64 mask 圖像數據
    loadMaskImageData(base64Data) {
      return new Promise((resolve, reject) => {
        const img = new Image()
        img.onload = () => {
          const tempCanvas = document.createElement('canvas')
          tempCanvas.width = img.width
          tempCanvas.height = img.height
          const tempCtx = tempCanvas.getContext('2d')
          tempCtx.drawImage(img, 0, 0)
          const imageData = tempCtx.getImageData(0, 0, img.width, img.height)
          resolve({ imageData, width: img.width, height: img.height })
        }
        img.onerror = reject
        img.src = `data:image/png;base64,${base64Data}`
      })
    },
    
    // 繪製 mask 到 canvas
    async drawMaskOnCanvas(ctx, maskData, color, opacity, canvasWidth, canvasHeight) {
      if (!maskData) return
      
      const { imageData, width, height } = maskData
      
      // 創建臨時 canvas 來處理 mask
      const tempCanvas = document.createElement('canvas')
      tempCanvas.width = canvasWidth
      tempCanvas.height = canvasHeight
      const tempCtx = tempCanvas.getContext('2d')
      
      // 創建一個臨時 canvas 來縮放 mask
      const maskCanvas = document.createElement('canvas')
      maskCanvas.width = width
      maskCanvas.height = height
      const maskCtx = maskCanvas.getContext('2d')
      maskCtx.putImageData(imageData, 0, 0)
      
      // 將 mask 縮放到原圖尺寸
      tempCtx.drawImage(maskCanvas, 0, 0, canvasWidth, canvasHeight)
      
      // 獲取縮放後的 ImageData
      const scaledImageData = tempCtx.getImageData(0, 0, canvasWidth, canvasHeight)
      const pixels = scaledImageData.data
      
      // 解析顏色
      const colorMatch = color.match(/^#([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i)
      if (!colorMatch) {
        console.error(`Invalid color format: ${color}`)
        return
      }
      
      const r = parseInt(colorMatch[1], 16)
      const g = parseInt(colorMatch[2], 16)
      const b = parseInt(colorMatch[3], 16)
      const a = Math.floor(255 * opacity)
      
      // 直接操作像素
      for (let i = 0; i < pixels.length; i += 4) {
        const gray = pixels[i] // R channel (grayscale mask)
        if (gray > 10) { // Threshold for mask pixels
          pixels[i] = r
          pixels[i + 1] = g
          pixels[i + 2] = b
          pixels[i + 3] = a
        } else {
          pixels[i + 3] = 0 // Make non-mask areas transparent
        }
      }
      
      tempCtx.putImageData(scaledImageData, 0, 0)
      
      // 繪製到主 canvas
      ctx.save()
      ctx.globalCompositeOperation = 'source-over'
      ctx.drawImage(tempCanvas, 0, 0)
      ctx.restore()
    },
    
    async drawCountResults() {
      if (!this.$refs.countCanvas || !this.countImagePreview || !this.countResult) return
      
      const canvas = this.$refs.countCanvas
      const ctx = canvas.getContext('2d')
      const img = new Image()
      
      img.onload = async () => {
        // 确保 canvas 尺寸正确（使用原始尺寸）
        if (canvas.width !== img.width || canvas.height !== img.height) {
          canvas.width = img.width
          canvas.height = img.height
          // 重新应用缩放后的显示尺寸
          if (this.imageScale && this.imageScale !== 1) {
            canvas.style.width = `${img.width * this.imageScale}px`
            canvas.style.height = `${img.height * this.imageScale}px`
          }
        }
        ctx.clearRect(0, 0, canvas.width, canvas.height)
        ctx.drawImage(img, 0, 0, img.width, img.height)
        
        if (this.countResult && this.countResult.masks) {
          // 先加載所有 mask 數據
          const maskDataPromises = this.countResult.masks.map(mask => {
            if (this.showMasks && mask.segmentation) {
              return this.loadMaskImageData(mask.segmentation).catch(err => {
                console.warn('Failed to load mask:', err)
                return null
              })
            }
            return Promise.resolve(null)
          })
          
          const maskDataList = await Promise.all(maskDataPromises)
          
          // 繪製 masks
          this.countResult.masks.forEach((mask, index) => {
            // bbox 格式是 [x1, y1, x2, y2]，需要轉換為 [x, y, w, h]
            const [x1, y1, x2, y2] = mask.bbox
            const x = x1
            const y = y1
            const w = x2 - x1
            const h = y2 - y1
            
            // 繪製 mask
            if (this.showMasks && maskDataList[index]) {
              this.drawMaskOnCanvas(ctx, maskDataList[index], '#FF6B6B', 0.4, canvas.width, canvas.height)
            }
            
            if (this.showBoundingBoxes) {
              ctx.strokeStyle = '#FF6B6B'
              ctx.lineWidth = 2
              ctx.strokeRect(x, y, w, h)
            }
            
            if (this.showLabels) {
              ctx.fillStyle = '#FF6B6B'
              ctx.font = '16px Arial'
              ctx.fillText(
                `${this.countPrompt} ${(mask.confidence * 100).toFixed(0)}%`,
                x,
                y - 5
              )
            }
          })
        }
      }
      
      img.src = this.countImagePreview
    },
    
    async drawMultiResults() {
      if (!this.$refs.multiCanvas || !this.multiImagePreview || !this.multiResult) return
      
      const canvas = this.$refs.multiCanvas
      const ctx = canvas.getContext('2d')
      const img = new Image()
      const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
      
      img.onload = async () => {
        // 确保 canvas 尺寸正确（使用原始尺寸）
        if (canvas.width !== img.width || canvas.height !== img.height) {
          canvas.width = img.width
          canvas.height = img.height
          // 重新应用缩放后的显示尺寸
          if (this.imageScale && this.imageScale !== 1) {
            canvas.style.width = `${img.width * this.imageScale}px`
            canvas.style.height = `${img.height * this.imageScale}px`
          }
        }
        ctx.clearRect(0, 0, canvas.width, canvas.height)
        ctx.drawImage(img, 0, 0, img.width, img.height)
        
        if (this.multiResult && this.multiResult.masks) {
          // 先加載所有 mask 數據
          const maskDataPromises = this.multiResult.masks.map(mask => {
            if (this.showMasks && mask.segmentation) {
              return this.loadMaskImageData(mask.segmentation).catch(err => {
                console.warn('Failed to load mask:', err)
                return null
              })
            }
            return Promise.resolve(null)
          })
          
          const maskDataList = await Promise.all(maskDataPromises)
          
          // 繪製 masks 和邊界框
          this.multiResult.masks.forEach((mask, index) => {
            // bbox 格式是 [x1, y1, x2, y2]，需要轉換為 [x, y, w, h]
            const [x1, y1, x2, y2] = mask.bbox
            const x = x1
            const y = y1
            const w = x2 - x1
            const h = y2 - y1
            const color = colors[index % colors.length]
            
            // 繪製 mask
            if (this.showMasks && maskDataList[index]) {
              this.drawMaskOnCanvas(ctx, maskDataList[index], color, 0.4, canvas.width, canvas.height)
            }
            
            if (this.showBoundingBoxes) {
              ctx.strokeStyle = color
              ctx.lineWidth = 2
              ctx.strokeRect(x, y, w, h)
            }
            
            if (this.showLabels) {
              ctx.fillStyle = color
              ctx.font = '14px Arial'
              ctx.fillText(
                `${mask.prompt || 'object'}`,
                x,
                y - 5
              )
            }
          })
        }
      }
      
      img.src = this.multiImagePreview
    },
    
    handleLineCanvasClick(e) {
      if (this.lineInputMode !== 'canvas') return
      
      const canvas = this.$refs.lineCanvas
      const rect = canvas.getBoundingClientRect()
      
      // 獲取顯示坐標
      const displayX = e.clientX - rect.left
      const displayY = e.clientY - rect.top
      
      // 轉換為原始坐標（canvas 實際尺寸）
      // 因為 canvas 可能被 CSS 縮放，需要將顯示坐標轉換為原始坐標
      const scaleX = canvas.width / rect.width
      const scaleY = canvas.height / rect.height
      const x = Math.round(displayX * scaleX)
      const y = Math.round(displayY * scaleY)
      
      this.lineDrawingPoints.push({ x, y })
      
      if (this.lineDrawingPoints.length === 1) {
        this.lineStartX = x
        this.lineStartY = y
      } else if (this.lineDrawingPoints.length === 2) {
        this.lineEndX = x
        this.lineEndY = y
        this.drawLineOnCanvas()
      }
    },
    
    drawLineOnCanvas() {
      if (!this.$refs.lineCanvas) return
      
      const ctx = this.$refs.lineCanvas.getContext('2d')
      
      // 如果視頻第一幀已加載，先重新繪製第一幀
      if (this.lineVideoFrame && this.lineVideoFrame.complete) {
        ctx.drawImage(this.lineVideoFrame, 0, 0, this.$refs.lineCanvas.width, this.$refs.lineCanvas.height)
      }
      
      // 如果有兩個點，繪製線
      if (this.lineDrawingPoints.length >= 2) {
        ctx.strokeStyle = '#FF6B6B'
        ctx.lineWidth = 3
        ctx.beginPath()
        ctx.moveTo(this.lineStartX, this.lineStartY)
        ctx.lineTo(this.lineEndX, this.lineEndY)
        ctx.stroke()
      }
      
      // 如果有第一個點，繪製一個標記點
      if (this.lineDrawingPoints.length >= 1) {
        ctx.fillStyle = '#FF6B6B'
        ctx.beginPath()
        ctx.arc(this.lineStartX, this.lineStartY, 5, 0, Math.PI * 2)
        ctx.fill()
      }
    },
    
    handleZoneCanvasClick(e) {
      if (this.zoneInputMode !== 'canvas') return
      
      const canvas = this.$refs.zoneCanvas
      const rect = canvas.getBoundingClientRect()
      
      // 獲取顯示坐標
      const displayX = e.clientX - rect.left
      const displayY = e.clientY - rect.top
      
      // 轉換為原始坐標（canvas 實際尺寸）
      // 因為 canvas 可能被 CSS 縮放，需要將顯示坐標轉換為原始坐標
      const scaleX = canvas.width / rect.width
      const scaleY = canvas.height / rect.height
      const x = Math.round(displayX * scaleX)
      const y = Math.round(displayY * scaleY)
      
      this.currentZonePoints.push([x, y])
      this.drawZoneOnCanvas()
    },
    
    finishZonePolygon() {
      if (this.currentZonePoints.length >= 3) {
        this.zoneDrawingPolygons.push([...this.currentZonePoints])
        this.currentZonePoints = []
        this.updateZoneConfig()
      }
    },
    
    clearZoneDrawing() {
      this.currentZonePoints = []
      if (this.$refs.zoneCanvas) {
        const ctx = this.$refs.zoneCanvas.getContext('2d')
        // 如果視頻第一幀已加載，重新繪製第一幀，否則清除畫布
        if (this.zoneVideoFrame && this.zoneVideoFrame.complete) {
          ctx.drawImage(this.zoneVideoFrame, 0, 0, this.$refs.zoneCanvas.width, this.$refs.zoneCanvas.height)
        } else {
          ctx.clearRect(0, 0, this.$refs.zoneCanvas.width, this.$refs.zoneCanvas.height)
        }
      }
    },
    
    drawZoneOnCanvas() {
      if (!this.$refs.zoneCanvas) return
      
      const ctx = this.$refs.zoneCanvas.getContext('2d')
      
      // 如果視頻第一幀已加載，先重新繪製第一幀，否則清除畫布
      if (this.zoneVideoFrame && this.zoneVideoFrame.complete) {
        ctx.drawImage(this.zoneVideoFrame, 0, 0, this.$refs.zoneCanvas.width, this.$refs.zoneCanvas.height)
      } else {
        ctx.clearRect(0, 0, this.$refs.zoneCanvas.width, this.$refs.zoneCanvas.height)
      }
      
      // Draw existing polygons
      this.zoneDrawingPolygons.forEach((polygon, index) => {
        const color = `hsl(${index * 60}, 70%, 50%)`
        ctx.strokeStyle = color
        ctx.fillStyle = color + '33'
        ctx.lineWidth = 2
        ctx.beginPath()
        ctx.moveTo(polygon[0][0], polygon[0][1])
        polygon.forEach(([x, y]) => ctx.lineTo(x, y))
        ctx.closePath()
        ctx.fill()
        ctx.stroke()
      })
      
      // Draw current polygon being drawn
      if (this.currentZonePoints.length > 0) {
        ctx.strokeStyle = '#FF6B6B'
        ctx.fillStyle = 'rgba(255, 107, 107, 0.2)'
        ctx.lineWidth = 2
        ctx.beginPath()
        ctx.moveTo(this.currentZonePoints[0][0], this.currentZonePoints[0][1])
        this.currentZonePoints.forEach(([x, y]) => ctx.lineTo(x, y))
        ctx.stroke()
      }
    },
    
    updateZoneConfig() {
      const polygons = [...this.zoneDrawingPolygons]
      if (this.currentZonePoints.length >= 3) {
        polygons.push([...this.currentZonePoints])
      }
      this.zoneConfig = JSON.stringify({ polygons }, null, 2)
    },
    
    async handleLineCount() {
      if (!this.lineVideoFile || !this.linePrompt) return
      
      if (this.lineInputMode === 'canvas') {
        this.updateZoneConfig()
      }
      
      this.lineLoading = true
      this.lineResult = null
      
      try {
        // 如果還沒有預覽 URL，創建一個
        if (this.lineVideoFile && !this.lineVideoPreview) {
          this.lineVideoPreview = URL.createObjectURL(this.lineVideoFile)
        }
        
        const result = await api.sam3LineCount(this.lineVideoFile, {
          prompt: this.linePrompt,
          lineStartX: this.lineStartX,
          lineStartY: this.lineStartY,
          lineEndX: this.lineEndX,
          lineEndY: this.lineEndY,
          confidence: this.lineConfidence
        })
        
        this.lineTaskId = result.task_id
        this.startPolling('line')
      } catch (error) {
        console.error('Line count error:', error)
        alert('處理失敗: ' + (error.response?.data?.detail || error.message))
        this.lineLoading = false
      }
    },
    
    async handleZoneCount() {
      if (!this.zoneVideoFile || !this.zonePrompt) return
      
      if (this.zoneInputMode === 'canvas') {
        this.updateZoneConfig()
      }
      
      this.zoneLoading = true
      this.zoneResult = null
      
      try {
        // 如果還沒有預覽 URL，創建一個
        if (this.zoneVideoFile && !this.zoneVideoPreview) {
          this.zoneVideoPreview = URL.createObjectURL(this.zoneVideoFile)
        }
        
        let zones
        try {
          zones = JSON.parse(this.zoneConfig)
        } catch (e) {
          alert('區域配置 JSON 格式錯誤')
          this.zoneLoading = false
          return
        }
        
        const result = await api.sam3ZoneCount(this.zoneVideoFile, {
          prompt: this.zonePrompt,
          zones: zones,
          confidence: this.zoneConfidence
        })
        
        this.zoneTaskId = result.task_id
        this.startPolling('zone')
      } catch (error) {
        console.error('Zone count error:', error)
        alert('處理失敗: ' + (error.response?.data?.detail || error.message))
        this.zoneLoading = false
      }
    },
    
    async handleTrack() {
      if (!this.trackVideoFile || !this.trackPrompt) return
      
      this.trackLoading = true
      this.trackResult = null
      
      try {
        // 如果還沒有預覽 URL，創建一個
        if (this.trackVideoFile && !this.trackVideoPreview) {
          this.trackVideoPreview = URL.createObjectURL(this.trackVideoFile)
        }
        
        const result = await api.sam3Track(this.trackVideoFile, {
          prompt: this.trackPrompt,
          confidence: this.trackConfidence,
          traceLength: this.trackTraceLength
        })
        
        this.trackTaskId = result.task_id
        this.startPolling('track')
      } catch (error) {
        console.error('Track error:', error)
        alert('處理失敗: ' + (error.response?.data?.detail || error.message))
        this.trackLoading = false
      }
    },
    
    async handleBatchProcess() {
      if (!this.batchFiles || this.batchFiles.length === 0 || !this.batchPrompt) return
      
      this.batchLoading = true
      this.batchResults = []
      this.batchProgress = 0
      
      try {
        for (let i = 0; i < this.batchFiles.length; i++) {
          const file = this.batchFiles[i]
          const isVideo = file.type.startsWith('video/')
          
          try {
            let result
            if (isVideo && this.batchMode === 'track') {
              // For videos, start tracking task
              const taskResult = await api.sam3Track(file, {
                prompt: this.batchPrompt,
                confidence: this.batchConfidence,
                traceLength: 30
              })
              
              // Poll for completion
              let status = await api.getSam3TaskStatus(taskResult.task_id)
              while (status.status === 'processing') {
                await new Promise(resolve => setTimeout(resolve, 2000))
                status = await api.getSam3TaskStatus(taskResult.task_id)
              }
              
              result = {
                filename: file.name,
                count: status.tracked_objects || 0,
                success: status.status === 'completed'
              }
            } else {
              // For images, count objects
              const countResult = await api.sam3Count(file, {
                prompt: this.batchPrompt,
                confidence: this.batchConfidence
              })
              
              result = {
                filename: file.name,
                count: countResult.masks.length,
                success: true,
                data: countResult
              }
            }
            
            this.batchResults.push(result)
          } catch (error) {
            this.batchResults.push({
              filename: file.name,
              count: 0,
              success: false,
              error: error.message
            })
          }
          
          this.batchProgress = ((i + 1) / this.batchFiles.length) * 100
        }
      } catch (error) {
        console.error('Batch process error:', error)
        alert('批量處理失敗: ' + error.message)
      } finally {
        this.batchLoading = false
      }
    },
    
    handleBatchFilesChange(files) {
      this.batchFiles = Array.isArray(files) ? files : [files]
    },
    
    async handleCompare() {
      if (!this.compareImageFile || !this.comparePrompt) return
      
      this.compareLoading = true
      this.compareResult = null
      
      try {
        const result = await api.sam3Count(this.compareImageFile, {
          prompt: this.comparePrompt,
          confidence: 0.5
        })
        
        this.compareResult = result
        this.drawCompareResults()
      } catch (error) {
        console.error('Compare error:', error)
        alert('處理失敗: ' + (error.response?.data?.detail || error.message))
      } finally {
        this.compareLoading = false
      }
    },
    
    async drawCompareResults() {
      if (!this.$refs.compareCanvas || !this.compareImagePreview) return
      
      const canvas = this.$refs.compareCanvas
      const ctx = canvas.getContext('2d')
      const img = new Image()
      
      img.onload = async () => {
        // 保存原始尺寸
        this.originalImageWidth = img.width
        this.originalImageHeight = img.height
        
        // 計算縮放比例 - 使用容器大小
        const container = canvas.parentElement
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
        const maxScale = Math.min(maxWidth / img.width, maxHeight / img.height)
        
        // 計算最小縮放比例，確保圖片至少 480x480
        const minWidth = 480
        const minHeight = 480
        const minScaleWidth = img.width < minWidth ? minWidth / img.width : 1
        const minScaleHeight = img.height < minHeight ? minHeight / img.height : 1
        const minScale = Math.max(minScaleWidth, minScaleHeight)
        
        // 使用最小和最大縮放比例中的較大值，確保圖片至少 480x480
        this.imageScale = Math.max(minScale, maxScale)
        
        // 設置 canvas 實際尺寸為原始尺寸
        canvas.width = img.width
        canvas.height = img.height
        
        // 設置 canvas 顯示尺寸（縮放後）
        this.canvasWidth = img.width * this.imageScale
        this.canvasHeight = img.height * this.imageScale
        canvas.style.width = `${this.canvasWidth}px`
        canvas.style.height = `${this.canvasHeight}px`
        
        ctx.drawImage(img, 0, 0, img.width, img.height)
        
        // 如果有結果，繪製檢測框和 mask
        if (this.compareResult && this.compareResult.masks) {
          // 加載所有 mask 數據
          const maskDataPromises = this.compareResult.masks.map(mask => {
            if (mask.segmentation) {
              return this.loadMaskImageData(mask.segmentation).catch(err => {
                console.warn('Failed to load mask:', err)
                return null
              })
            }
            return Promise.resolve(null)
          })
          
          const maskDataList = await Promise.all(maskDataPromises)
          
          this.compareResult.masks.forEach((mask, index) => {
            // bbox 格式是 [x1, y1, x2, y2]，需要轉換為 [x, y, w, h]
            const [x1, y1, x2, y2] = mask.bbox
            const x = x1
            const y = y1
            const w = x2 - x1
            const h = y2 - y1
            
            // 繪製 mask
            if (maskDataList[index]) {
              this.drawMaskOnCanvas(ctx, maskDataList[index], '#FF6B6B', 0.4, canvas.width, canvas.height)
            }
            
            // 繪製邊界框
            ctx.strokeStyle = '#FF6B6B'
            ctx.lineWidth = 3
            ctx.strokeRect(x, y, w, h)
            
            // 繪製標籤
            ctx.fillStyle = '#FF6B6B'
            ctx.font = '18px Arial'
            ctx.fillText(
              `${this.comparePrompt} ${(mask.confidence * 100).toFixed(0)}%`,
              x,
              y - 10
            )
          })
        }
      }
      
      img.src = this.compareImagePreview
    },
    
    exportCountResults() {
      if (!this.countResult) return
      this.exportToCSV([{
        prompt: this.countPrompt,
        count: this.countResult.masks.length,
        masks: this.countResult.masks
      }], 'count_results.csv')
    },
    
    exportMultiResults() {
      if (!this.multiResult) return
      const rows = Object.entries(this.multiResult.prompt_counts).map(([prompt, count]) => ({
        prompt,
        count
      }))
      this.exportToCSV(rows, 'multi_prompt_results.csv')
    },
    
    exportLineResults() {
      if (!this.lineResult) return
      this.exportToCSV([{
        in_count: this.lineResult.in_count,
        out_count: this.lineResult.out_count
      }], 'line_count_results.csv')
    },
    
    exportZoneResults() {
      if (!this.zoneResult) return
      const rows = this.zoneResult.zone_counts.map((count, index) => ({
        zone: index + 1,
        count
      }))
      this.exportToCSV(rows, 'zone_count_results.csv')
    },
    
    exportBatchResults() {
      if (this.batchResults.length === 0) return
      this.exportToCSV(this.batchResults, 'batch_results.csv')
    },
    
    exportToCSV(data, filename) {
      if (data.length === 0) return
      
      const headers = Object.keys(data[0])
      const csv = [
        headers.join(','),
        ...data.map(row => headers.map(header => {
          const value = row[header]
          if (Array.isArray(value)) return JSON.stringify(value)
          return value
        }).join(','))
      ].join('\n')
      
      const blob = new Blob([csv], { type: 'text/csv' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      a.click()
      URL.revokeObjectURL(url)
    },
    
    downloadBatchResult(result) {
      if (result.data) {
        const json = JSON.stringify(result.data, null, 2)
        const blob = new Blob([json], { type: 'application/json' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${result.filename}_result.json`
        a.click()
        URL.revokeObjectURL(url)
      }
    },
    
    startPolling(type) {
      const taskId = this[`${type}TaskId`]
      if (!taskId) return
      
      const poll = async () => {
        try {
          const status = await api.getSam3TaskStatus(taskId)
          
          console.log(`[SAM3View] Task status for ${type}:`, status)
          
          this[`${type}Progress`] = status.progress || 0
          
          if (status.status === 'completed') {
            this[`${type}Loading`] = false
            // 處理 video_url，如果是相對路徑則轉換為完整 URL
            if (status.video_url) {
              if (status.video_url.startsWith('http://') || status.video_url.startsWith('https://')) {
                // 已經是完整 URL，保持不變
                console.log(`[SAM3View] Video URL (absolute): ${status.video_url}`)
              } else {
                // 相對路徑，需要構建完整 URL
                // 後端返回的格式是 /static/processed/{filename}
                // 由於 vite 代理配置，可以直接使用相對路徑，瀏覽器會通過代理訪問
                // 或者構建完整 URL 使用 window.location.origin（通過代理）
                const videoPath = status.video_url.startsWith('/') ? status.video_url : '/' + status.video_url
                
                // 優先使用 API base URL 來確定後端地址
                const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1'
                let baseOrigin = window.location.origin // 默認使用前端地址（通過代理）
                
                if (baseURL.startsWith('http://') || baseURL.startsWith('https://')) {
                  try {
                    const url = new URL(baseURL)
                    baseOrigin = `${url.protocol}//${url.host}`
                    console.log(`[SAM3View] Using API base URL origin: ${baseOrigin}`)
                  } catch (e) {
                    console.warn('[SAM3View] Failed to parse baseURL, using window.location.origin:', e)
                  }
                } else {
                  // 如果 baseURL 是相對路徑，使用 window.location.origin
                  // vite 代理會將 /static 請求轉發到後端
                  console.log(`[SAM3View] Using window.location.origin (via proxy): ${baseOrigin}`)
                }
                
                // 構建完整的視頻 URL
                status.video_url = `${baseOrigin}${videoPath}`
                console.log(`[SAM3View] Video URL (constructed): ${status.video_url}`)
                console.log(`[SAM3View] Original video_url from backend: ${videoPath}`)
              }
            } else {
              console.warn(`[SAM3View] No video_url in status for ${type}`)
            }
            this[`${type}Result`] = status
            this.clearPollInterval(type)
          } else if (status.status === 'error') {
            this[`${type}Loading`] = false
            alert('處理錯誤: ' + (status.error || 'Unknown error'))
            this.clearPollInterval(type)
          } else {
            this[`${type}PollInterval`] = setTimeout(poll, 2000)
          }
        } catch (error) {
          console.error('Poll error:', error)
          this[`${type}Loading`] = false
          this.clearPollInterval(type)
        }
      }
      
      poll()
    },
    
    clearPollInterval(type) {
      if (this[`${type}PollInterval`]) {
        clearTimeout(this[`${type}PollInterval`])
        this[`${type}PollInterval`] = null
      }
    },
    
    clearPollIntervals() {
      this.clearPollInterval('line')
      this.clearPollInterval('zone')
      this.clearPollInterval('track')
    },
    
    handleVideoError(type, event) {
      console.error(`[SAM3View] Video error for ${type}:`, event)
      const videoUrl = this[`${type}Result`]?.video_url
      const videoElement = event.target
      console.error(`[SAM3View] Failed video URL: ${videoUrl}`)
      console.error(`[SAM3View] Video element error code:`, videoElement.error?.code)
      console.error(`[SAM3View] Video element error message:`, videoElement.error?.message)
      
      // 嘗試使用 fetch 檢查文件是否存在
      if (videoUrl) {
        fetch(videoUrl, { method: 'HEAD' })
          .then(response => {
            if (!response.ok) {
              console.error(`[SAM3View] Video file not found (${response.status}): ${videoUrl}`)
            } else {
              console.log(`[SAM3View] Video file exists but cannot be played: ${videoUrl}`)
            }
          })
          .catch(err => {
            console.error(`[SAM3View] Failed to check video file:`, err)
          })
      }
      
      alert(`無法加載${type === 'line' ? '線計數' : type === 'zone' ? '區域計數' : '追蹤'}結果視頻。\nURL: ${videoUrl}\n請檢查控制台獲取詳細信息。`)
    },
    
    handleVideoLoaded(type) {
      console.log(`[SAM3View] Video loaded successfully for ${type}:`, this[`${type}Result`]?.video_url)
    }
  },
  watch: {
    activeTab() {
      this.$nextTick(() => {
        this.setupCanvas()
      })
    },
    showBoundingBoxes() {
      this.drawCountResults()
    },
    showMasks() {
      this.drawCountResults()
    },
    showLabels() {
      this.drawCountResults()
    }
  }
}
</script>

<style scoped>
.image-preview-container, .video-preview {
  position: relative;
  width: 100%;
  text-align: center;
  overflow: auto;
  padding: 16px;
  display: flex;
  justify-content: center;
  align-items: flex-start;
}

.image-preview-container canvas,
.video-preview canvas {
  max-width: 100%;
  height: auto;
  display: block;
}

.result-overlay {
  position: absolute;
  top: 10px;
  left: 10px;
  z-index: 10;
}
</style>
