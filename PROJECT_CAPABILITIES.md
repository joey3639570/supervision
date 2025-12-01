# Supervision 專案功能整理

本文檔整理 Supervision 專案的所有核心功能和能力。

## 📋 目錄

1. [模型整合](#模型整合)
2. [檢測與追蹤](#檢測與追蹤)
3. [標註工具](#標註工具)
4. [資料集管理](#資料集管理)
5. [影片處理](#影片處理)
6. [幾何工具](#幾何工具)
7. [評估指標](#評估指標)
8. [工具與實用程式](#工具與實用程式)
9. [範例應用](#範例應用)

---

## 1. 模型整合

Supervision 支援多種電腦視覺模型的整合，提供統一的 `Detections` 介面。

### 1.1 支援的模型框架

- **Ultralytics (YOLO)**: `Detections.from_ultralytics()` - 支援 YOLOv5, YOLOv8, YOLOv9, YOLOv10, YOLO-NAS, SAM
- **Transformers (Hugging Face)**: `Detections.from_transformers()` - 支援 DETR, Mask2Former 等
- **MMDetection**: `Detections.from_mmdetection()` - 支援 MMDetection 和 MMYOLO
- **Detectron2**: `Detections.from_detectron2()`
- **TensorFlow Hub**: `Detections.from_tensorflow()`
- **DeepSparse**: `Detections.from_deepsparse()`
- **YOLO-NAS**: `Detections.from_yolo_nas()`
- **PaddleDetection**: `Detections.from_paddledet()`
- **Roboflow Inference**: `Detections.from_inference()`
- **SAM (Segment Anything Model)**: `Detections.from_sam()` - 支援 SAM 和 SAM2
- **Azure Image Analysis**: `Detections.from_azure_analyze_image()`
- **EasyOCR**: `Detections.from_easyocr()`
- **NCNN**: `Detections.from_ncnn()`
- **YOLOv5**: `Detections.from_yolov5()`

### 1.2 視覺語言模型 (VLM) 支援

- **PaliGemma**: `Detections.from_vlm(VLM.PALIGEMMA)`
- **Qwen2.5-VL**: `Detections.from_vlm(VLM.QWEN_2_5_VL)`
- **Qwen3-VL**: `Detections.from_vlm(VLM.QWEN_3_VL)`
- **Google Gemini 2.0**: `Detections.from_vlm(VLM.GOOGLE_GEMINI_2_0)`
- **Google Gemini 2.5**: `Detections.from_vlm(VLM.GOOGLE_GEMINI_2_5)` - 支援檢測和分割
- **Moondream**: `Detections.from_vlm(VLM.MOONDREAM)`
- **DeepSeek-VL2**: `Detections.from_vlm(VLM.DEEPSEEK_VL_2)`
- **Florence-2**: `Detections.from_vlm(VLM.FLORENCE_2)`

---

## 2. 檢測與追蹤

### 2.1 Detections 類別

核心資料結構，統一處理檢測結果：

**主要屬性：**
- `xyxy`: 邊界框座標 (x1, y1, x2, y2)
- `mask`: 分割遮罩 (可選)
- `confidence`: 信心分數 (可選)
- `class_id`: 類別 ID (可選)
- `tracker_id`: 追蹤 ID (可選)
- `data`: 額外資料字典
- `metadata`: 集合級別的中繼資料

**核心功能：**
- `from_*()`: 從各種模型格式轉換
- `merge()`: 合併多個 Detections 物件
- `with_nms()`: 非極大值抑制
- `with_nmm()`: 非極大值合併
- `is_empty()`: 檢查是否為空
- `get_anchors_coordinates()`: 獲取錨點座標
- 索引和切片操作

### 2.2 物件追蹤

- **ByteTrack**: `ByteTrack` - 多物件追蹤演算法
  - 支援跨幀追蹤
  - 處理遮擋和重新識別
  - 可與檢測結果整合

### 2.3 檢測工具

- **InferenceSlicer**: 將大圖像切片進行推理，適合小物件檢測
- **DetectionsSmoother**: 平滑檢測結果，減少抖動

---

## 3. 標註工具 (Annotators)

提供豐富的視覺化標註工具，可自訂樣式。

### 3.1 邊界框標註

- **BoxAnnotator**: 標準矩形邊界框
- **RoundBoxAnnotator**: 圓角矩形邊界框
- **BoxCornerAnnotator**: 只顯示邊界框的四個角
- **OrientedBoxAnnotator**: 定向邊界框（旋轉框）

### 3.2 遮罩標註

- **MaskAnnotator**: 分割遮罩標註
- **PolygonAnnotator**: 多邊形標註

### 3.3 標籤標註

- **LabelAnnotator**: 基本文字標籤
- **RichLabelAnnotator**: 豐富格式標籤（支援多行、背景等）
- **VertexLabelAnnotator**: 關鍵點標籤

### 3.4 特殊效果標註

- **ColorAnnotator**: 顏色填充
- **BlurAnnotator**: 模糊效果
- **PixelateAnnotator**: 像素化效果
- **CropAnnotator**: 裁剪標註
- **BackgroundOverlayAnnotator**: 背景疊加

### 3.5 形狀標註

- **CircleAnnotator**: 圓形標註
- **EllipseAnnotator**: 橢圓形標註
- **DotAnnotator**: 點標註
- **TriangleAnnotator**: 三角形標註
- **HaloAnnotator**: 光暈效果

### 3.6 其他標註

- **HeatMapAnnotator**: 熱力圖標註
- **IconAnnotator**: 圖示標註
- **PercentageBarAnnotator**: 百分比條
- **TraceAnnotator**: 追蹤軌跡
- **ComparisonAnnotator**: 比較標註

### 3.7 關鍵點標註

- **VertexAnnotator**: 頂點標註
- **EdgeAnnotator**: 邊緣標註

---

## 4. 資料集管理

### 4.1 資料集類別

- **DetectionDataset**: 檢測資料集
- **ClassificationDataset**: 分類資料集
- **BaseDataset**: 基礎資料集類別

### 4.2 支援的格式

**讀取格式：**
- COCO: `DetectionDataset.from_coco()`
- YOLO: `DetectionDataset.from_yolo()`
- Pascal VOC: `DetectionDataset.from_pascal_voc()`

**儲存格式：**
- `dataset.as_coco()`: 儲存為 COCO 格式
- `dataset.as_yolo()`: 儲存為 YOLO 格式
- `dataset.as_pascal_voc()`: 儲存為 Pascal VOC 格式

### 4.3 資料集操作

- **分割**: `dataset.split(split_ratio=0.7)` - 將資料集分割為訓練集和測試集
- **合併**: `DetectionDataset.merge([ds1, ds2])` - 合併多個資料集
- **轉換**: 在不同格式間轉換

### 4.4 工具函數

- `mask_to_rle()`: 遮罩轉 RLE 格式
- `rle_to_mask()`: RLE 轉遮罩格式
- `get_coco_class_index_mapping()`: 獲取 COCO 類別索引映射

---

## 5. 影片處理

### 5.1 影片讀取

- **get_video_frames_generator()**: 生成器方式讀取影片幀
  - 支援 stride（步長）
  - 支援 start/end 範圍
  - 支援迭代式搜尋

### 5.2 影片寫入

- **VideoSink**: 影片寫入器
  - 自動處理編碼
  - 支援多種格式

### 5.3 影片資訊

- **VideoInfo**: 影片資訊類別
  - 從影片路徑獲取資訊: `VideoInfo.from_video_path()`
  - 包含解析度、FPS、總幀數等

### 5.4 影片處理工具

- **process_video()**: 處理整個影片
- **FPSMonitor**: FPS 監控器

---

## 6. 幾何工具

### 6.1 幾何物件

- **Point**: 點座標
- **Rect**: 矩形
- **Position**: 位置枚舉（CENTER, TOP_LEFT, BOTTOM_RIGHT 等）

### 6.2 區域工具

- **PolygonZone**: 多邊形區域
  - 檢測物件是否在區域內
  - 計算進入/離開的物件數量

- **LineZone**: 線區域
  - 檢測物件是否跨越線
  - 計算跨越線的物件數量
  - 支援多類別: `LineZoneAnnotatorMulticlass`

### 6.3 幾何工具函數

- `get_polygon_center()`: 獲取多邊形中心
- `approximate_polygon()`: 近似多邊形
- `filter_polygons_by_area()`: 按面積過濾多邊形

---

## 7. 評估指標

### 7.1 檢測指標

- **MeanAveragePrecision (mAP)**: 平均精度均值
- **ConfusionMatrix**: 混淆矩陣
- **Precision**: 精確率
- **Recall**: 召回率
- **F1 Score**: F1 分數
- **MeanAverageRecall (mAR)**: 平均召回率均值

### 7.2 重疊度量

- **OverlapMetric**: 重疊度量枚舉（IOU, IOS 等）
- **box_iou()**: 邊界框 IoU
- **box_iou_batch()**: 批次邊界框 IoU
- **mask_iou_batch()**: 批次遮罩 IoU
- **oriented_box_iou_batch()**: 批次定向框 IoU

---

## 8. 工具與實用程式

### 8.1 邊界框工具

- `clip_boxes()`: 裁剪邊界框
- `denormalize_boxes()`: 反標準化邊界框
- `move_boxes()`: 移動邊界框
- `pad_boxes()`: 填充邊界框
- `scale_boxes()`: 縮放邊界框

### 8.2 座標轉換

- `xywh_to_xyxy()`: (x, y, w, h) → (x1, y1, x2, y2)
- `xyxy_to_xywh()`: (x1, y1, x2, y2) → (x, y, w, h)
- `xcycwh_to_xyxy()`: 中心點格式轉換
- `xyxy_to_xcycarh()`: 轉換為定向框格式
- `polygon_to_xyxy()`: 多邊形轉邊界框
- `polygon_to_mask()`: 多邊形轉遮罩
- `mask_to_xyxy()`: 遮罩轉邊界框
- `mask_to_polygons()`: 遮罩轉多邊形
- `xyxy_to_mask()`: 邊界框轉遮罩
- `xyxy_to_polygons()`: 邊界框轉多邊形

### 8.3 遮罩工具

- `calculate_masks_centroids()`: 計算遮罩質心
- `contains_holes()`: 檢查是否包含洞
- `contains_multiple_segments()`: 檢查是否包含多個片段
- `filter_segments_by_distance()`: 按距離過濾片段
- `move_masks()`: 移動遮罩

### 8.4 非極大值抑制/合併

- `box_non_max_suppression()`: 邊界框 NMS
- `box_non_max_merge()`: 邊界框 NMM
- `mask_non_max_suppression()`: 遮罩 NMS
- `mask_non_max_merge()`: 遮罩 NMM

### 8.5 過濾工具

- **OverlapFilter**: 重疊過濾器

### 8.6 影像工具

- `crop_image()`: 裁剪影像
- `resize_image()`: 調整影像大小
- `scale_image()`: 縮放影像
- `letterbox_image()`: Letterbox 處理
- `grayscale_image()`: 轉灰階
- `tint_image()`: 著色
- `overlay_image()`: 疊加影像
- `get_image_resolution_wh()`: 獲取影像解析度
- **ImageSink**: 影像儲存器

### 8.7 繪圖工具

- `draw_rectangle()`: 繪製矩形
- `draw_filled_rectangle()`: 繪製填充矩形
- `draw_polygon()`: 繪製多邊形
- `draw_filled_polygon()`: 繪製填充多邊形
- `draw_line()`: 繪製線條
- `draw_text()`: 繪製文字
- `draw_image()`: 繪製影像
- `calculate_optimal_line_thickness()`: 計算最佳線條粗細
- `calculate_optimal_text_scale()`: 計算最佳文字大小

### 8.8 顏色工具

- **Color**: 顏色類別
- **ColorPalette**: 調色板
- **ColorLookup**: 顏色查找表

### 8.9 檔案工具

- `list_files_with_extensions()`: 列出指定擴展名的檔案

### 8.10 格式轉換

- `cv2_to_pillow()`: OpenCV 轉 PIL
- `pillow_to_cv2()`: PIL 轉 OpenCV

### 8.11 Notebook 工具

- `plot_image()`: 繪製單張影像
- `plot_images_grid()`: 繪製影像網格

### 8.12 資料儲存

- **CSVSink**: CSV 格式儲存檢測結果
- **JSONSink**: JSON 格式儲存檢測結果

### 8.13 VLM 工具

- `edit_distance()`: 編輯距離
- `fuzzy_match_index()`: 模糊匹配索引

---

## 9. 範例應用

專案包含多個完整的應用範例：

### 9.1 物件追蹤 (tracking)
- 使用 YOLO 進行檢測
- 使用 ByteTrack 進行追蹤
- 標註追蹤結果

### 9.2 區域計數 (count_people_in_zone)
- 使用 PolygonZone 定義區域
- 計算區域內物件數量
- 視覺化結果

### 9.3 交通分析 (traffic_analysis)
- 車輛檢測和追蹤
- 交通流量分析
- 速度估算

### 9.4 速度估算 (speed_estimation)
- 車輛追蹤
- 透視變換
- 速度計算

### 9.5 停留時間分析 (time_in_zone)
- 計算物件在區域內的停留時間
- 支援即時串流和檔案處理

### 9.6 熱力圖與追蹤 (heatmap_and_track)
- 生成熱力圖
- 結合物件追蹤
- 視覺化分析

---

## 10. 分類功能

### 10.1 Classifications 類別

- 處理影像分類結果
- 支援多種分類模型整合

---

## 11. 關鍵點功能

### 11.1 KeyPoints 類別

- 處理關鍵點檢測結果
- 支援關鍵點標註和視覺化

---

## 總結

Supervision 是一個功能完整的電腦視覺工具庫，提供：

✅ **模型無關設計** - 可與任何檢測/分割模型整合  
✅ **豐富的標註工具** - 20+ 種標註樣式  
✅ **完整的資料集管理** - 支援多種格式的讀取、轉換、分割、合併  
✅ **強大的影片處理** - 讀取、處理、寫入影片  
✅ **物件追蹤** - ByteTrack 整合  
✅ **區域分析** - 多邊形區域、線區域、計數功能  
✅ **評估指標** - mAP, Precision, Recall, F1 等  
✅ **實用工具** - 座標轉換、影像處理、幾何運算等  
✅ **完整範例** - 多個端到端應用範例  

這使得 Supervision 成為構建電腦視覺應用的強大基礎工具庫。


