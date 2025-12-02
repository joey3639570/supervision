"""
SAM3 服務
提供 SAM3 模型載入和推理功能
"""
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING
import torch
import numpy as np
import cv2
from PIL import Image
import supervision as sv

# Try to import SAM3
# First try to add the project root to the path to find local sam3 installation
import sys
import os
from pathlib import Path

# Add project root and parent directory to path for local sam3 installation
project_root = Path(__file__).parent.parent.parent.parent
sam3_paths = [
    "/root/joey/supervision/sam3",  # Absolute path (most reliable)
    str(project_root.parent / "sam3"),  # /root/joey/supervision/sam3 -> /root/joey/sam3
    str(project_root / "sam3"),  # Local sam3 directory
]

# Add SAM3 paths to sys.path and PYTHONPATH
for sam3_path in sam3_paths:
    sam3_path = str(sam3_path)
    if os.path.exists(sam3_path) and sam3_path not in sys.path:
        sys.path.insert(0, sam3_path)
        # Also update PYTHONPATH environment variable
        current_pythonpath = os.environ.get("PYTHONPATH", "")
        if sam3_path not in current_pythonpath:
            os.environ["PYTHONPATH"] = f"{sam3_path}:{current_pythonpath}" if current_pythonpath else sam3_path

# Check if required dependencies are available before importing SAM3
try:
    import einops
except ImportError:
    einops = None
    print("Warning: einops not found. SAM3 may not work correctly.")

try:
    from sam3 import build_sam3_image_model
    from sam3.model.sam3_image_processor import Sam3Processor
    SAM3_AVAILABLE = True
except ImportError as e:
    SAM3_AVAILABLE = False
    Sam3Processor = None  # Set to None when not available
    import traceback
    print(f"Warning: SAM3 not available. Import error: {e}")
    print(f"Python path: {sys.path[:3]}")
    print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
    print("Please ensure sam3 package is installed or available in the project directory.")
    print("Make sure to use ./start.sh to launch the server with correct PYTHONPATH.")

if TYPE_CHECKING:
    try:
        from sam3.model.sam3_image_processor import Sam3Processor
    except ImportError:
        pass  # Type checker will handle this


class SAM3Service:
    """SAM3 服務類別"""
    
    _model_cache: Dict[str, torch.nn.Module] = {}
    _processor_cache: Dict[str, "Sam3Processor"] = {}
    
    @staticmethod
    def is_available() -> bool:
        """檢查 SAM3 是否可用"""
        return SAM3_AVAILABLE
    
    @staticmethod
    def _get_checkpoint_path(checkpoint_path: Optional[str] = None) -> str:
        """
        獲取檢查點路徑
        
        Args:
            checkpoint_path: 用戶提供的檢查點路徑
        
        Returns:
            檢查點文件路徑
        """
        if checkpoint_path:
            checkpoint_file = Path(checkpoint_path)
        else:
            # 使用默認路徑
            from app.config import SAM3_CHECKPOINT_PATH
            checkpoint_file = Path(SAM3_CHECKPOINT_PATH)
        
        # 如果是目錄，查找檢查點文件
        if checkpoint_file.is_dir():
            possible_files = [
                checkpoint_file / "sam3.pt",
                checkpoint_file / "model.safetensors",
                checkpoint_file / "checkpoint.pt",
                checkpoint_file / "model.pt",
            ]
            for possible_file in possible_files:
                if possible_file.exists():
                    return str(possible_file)
            raise ValueError(
                f"Could not find checkpoint file in directory {checkpoint_file}. "
                f"Expected one of: sam3.pt, model.safetensors, checkpoint.pt, model.pt"
            )
        
        if not checkpoint_file.exists():
            # 提供更友好的錯誤信息，包括可能的檢查點位置
            from app.config import DEFAULT_SAM3_CHECKPOINT_PATHS
            possible_locations = "\n".join([f"  - {p}" for p in DEFAULT_SAM3_CHECKPOINT_PATHS])
            raise ValueError(
                f"Checkpoint file does not exist: {checkpoint_file}\n"
                f"Please ensure the checkpoint file exists at one of these locations:\n{possible_locations}\n"
                f"Or set SAM3_CHECKPOINT_PATH environment variable to point to the correct file."
            )
        
        return str(checkpoint_file)
    
    @staticmethod
    def load_model(
        checkpoint_path: Optional[str] = None,
        device: str = "cuda"
    ) -> Tuple[torch.nn.Module, str]:
        """
        載入 SAM3 模型
        
        Args:
            checkpoint_path: 檢查點路徑
            device: 設備 ('cuda' 或 'cpu')
        
        Returns:
            (模型實例, 模型鍵)
        """
        if not SAM3_AVAILABLE:
            raise RuntimeError("SAM3 is not available. Please install the sam3 package.")
        
        checkpoint_file = SAM3Service._get_checkpoint_path(checkpoint_path)
        model_key = f"{checkpoint_file}_{device}"
        
        # 檢查緩存
        if model_key in SAM3Service._model_cache:
            return SAM3Service._model_cache[model_key], model_key
        
        # 載入模型
        print(f"Loading SAM3 model from {checkpoint_file}...")
        model = build_sam3_image_model(
            checkpoint_path=checkpoint_file,
            device=device,
            load_from_HF=False,
        )
        model.eval()
        
        # 緩存模型
        SAM3Service._model_cache[model_key] = model
        
        return model, model_key
    
    @staticmethod
    def get_processor(
        model_key: str,
        device: str = "cuda",
        confidence_threshold: float = 0.5
    ) -> "Sam3Processor":
        """
        獲取 SAM3 處理器
        
        Args:
            model_key: 模型鍵
            device: 設備
            confidence_threshold: 信心閾值
        
        Returns:
            SAM3 處理器實例
        """
        if not SAM3_AVAILABLE:
            raise RuntimeError("SAM3 is not available.")
        
        processor_key = f"{model_key}_{confidence_threshold}"
        
        # 檢查緩存
        if processor_key in SAM3Service._processor_cache:
            return SAM3Service._processor_cache[processor_key]
        
        # 獲取模型
        if model_key not in SAM3Service._model_cache:
            raise ValueError(f"Model {model_key} not found in cache")
        
        model = SAM3Service._model_cache[model_key]
        
        # 創建處理器
        processor = Sam3Processor(
            model=model,
            device=device,
            confidence_threshold=confidence_threshold,
        )
        
        # 緩存處理器
        SAM3Service._processor_cache[processor_key] = processor
        
        return processor
    
    @staticmethod
    def sam3_result_to_supervision_format(
        state: Dict,
        prompt: str
    ) -> List[Dict]:
        """
        將 SAM3 輸出轉換為 Supervision 格式
        
        Args:
            state: SAM3 處理器狀態
            prompt: 提示詞
        
        Returns:
            Supervision 格式的檢測結果列表
        """
        if "masks" not in state or state["masks"] is None:
            return []
        
        masks = state["masks"].cpu().numpy()
        boxes = state["boxes"].cpu().numpy()
        scores = state["scores"].cpu().numpy()
        
        results = []
        for i in range(len(masks)):
            # boxes 已經是 [x0, y0, x1, y1] 格式，直接使用
            x0, y0, x1, y1 = boxes[i]
            bbox_xyxy = [float(x0), float(y0), float(x1), float(y1)]
            
            # 獲取遮罩為布爾數組
            mask = masks[i].astype(bool)
            
            # 確保 mask 是 2D (H, W) 格式
            # SAM3 可能返回不同維度的 mask: (H, W), (1, H, W), (1, 1, H, W) 等
            # 使用 squeeze 移除所有大小為 1 的維度
            mask = np.squeeze(mask)
            
            # 確保 mask 是 2D
            if mask.ndim != 2:
                raise ValueError(
                    f"Mask must be 2D after processing, but got shape {mask.shape}. "
                    f"Original shape was {masks[i].shape}"
                )
            
            # 計算面積
            area = float(np.sum(mask))
            
            results.append({
                "bbox_xyxy": bbox_xyxy,  # 使用 xyxy 格式
                "bbox": [float(x0), float(y0), float(x1 - x0), float(y1 - y0)],  # 保留舊格式以兼容
                "segmentation": mask,  # 2D mask (H, W)
                "area": area,
                "score": float(scores[i]),
                "prompt": prompt,
            })
        
        return results
    
    @staticmethod
    def detect_objects_in_image(
        image: np.ndarray,
        prompt: str,
        model_key: str,
        device: str = "cuda",
        confidence_threshold: float = 0.5
    ) -> Tuple[sv.Detections, Dict]:
        """
        在圖像中檢測對象
        
        Args:
            image: 輸入圖像 (BGR 格式)
            prompt: 文本提示
            model_key: 模型鍵
            device: 設備
            confidence_threshold: 信心閾值
        
        Returns:
            (檢測結果, 處理器狀態)
        """
        if not SAM3_AVAILABLE:
            raise RuntimeError("SAM3 is not available.")
        
        # 獲取處理器
        processor = SAM3Service.get_processor(
            model_key=model_key,
            device=device,
            confidence_threshold=confidence_threshold
        )
        
        # 轉換圖像格式
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(image_rgb)
        
        # 設置圖像
        state = processor.set_image(pil_image, state={})
        
        # 設置文本提示並獲取結果
        state = processor.set_text_prompt(prompt, state)
        
        # 轉換為 Supervision 格式
        sam3_results = SAM3Service.sam3_result_to_supervision_format(state, prompt)
        
        if not sam3_results:
            return sv.Detections.empty(), state
        
        # 手動創建 Supervision Detections 對象
        # 因為 supervision 0.27.0 沒有 from_sam3 方法
        xyxy_list = []
        confidence_list = []
        mask_list = []
        
        for result in sam3_results:
            # 使用 bbox_xyxy 格式 [x1, y1, x2, y2]，如果不存在則從 bbox 轉換
            if "bbox_xyxy" in result:
                xyxy_list.append(result["bbox_xyxy"])
            else:
                # 從 [x, y, width, height] 轉換到 [x1, y1, x2, y2]
                x, y, w, h = result["bbox"]
                xyxy_list.append([x, y, x + w, y + h])
            confidence_list.append(result["score"])
            
            # 確保 mask 是 2D (H, W)
            mask = result["segmentation"]
            if mask.ndim > 2:
                # 如果 mask 是多維的，壓縮到 2D
                mask = np.squeeze(mask)
            if mask.ndim != 2:
                raise ValueError(f"Mask must be 2D, but got shape {mask.shape}")
            mask_list.append(mask)
        
        # 創建 Detections 對象
        # mask 應該是 3D 數組 (N, H, W)，其中 N 是檢測數量
        if mask_list:
            mask_array = np.array(mask_list, dtype=bool)  # Shape: (N, H, W)
        else:
            mask_array = None
        
        detections = sv.Detections(
            xyxy=np.array(xyxy_list, dtype=np.float32),
            confidence=np.array(confidence_list, dtype=np.float32),
            mask=mask_array
        )
        
        return detections, state
    
    @staticmethod
    def detect_objects_in_frame(
        frame: np.ndarray,
        prompt: str,
        model_key: str,
        state: Optional[Dict] = None,
        device: str = "cuda",
        confidence_threshold: float = 0.5
    ) -> Tuple[sv.Detections, Dict]:
        """
        在視頻幀中檢測對象（重用圖像特徵）
        
        Args:
            frame: 輸入幀 (BGR 格式)
            prompt: 文本提示
            model_key: 模型鍵
            state: 之前的處理器狀態（可選）
            device: 設備
            confidence_threshold: 信心閾值
        
        Returns:
            (檢測結果, 更新的處理器狀態)
        """
        if not SAM3_AVAILABLE:
            raise RuntimeError("SAM3 is not available.")
        
        # 獲取處理器
        processor = SAM3Service.get_processor(
            model_key=model_key,
            device=device,
            confidence_threshold=confidence_threshold
        )
        
        # 轉換圖像格式
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(image_rgb)
        
        # 設置圖像（如果狀態為空）
        if state is None or "backbone_out" not in state:
            state = processor.set_image(pil_image, state={})
        else:
            # 重用圖像特徵，只更新圖像尺寸
            state["original_height"] = pil_image.height
            state["original_width"] = pil_image.width
        
        # 設置文本提示並獲取結果
        state = processor.set_text_prompt(prompt, state)
        
        # 轉換為 Supervision 格式
        sam3_results = SAM3Service.sam3_result_to_supervision_format(state, prompt)
        
        if not sam3_results:
            # 重置提示但保留 backbone_out
            backbone_out = state.get("backbone_out")
            processor.reset_all_prompts(state)
            if backbone_out:
                state["backbone_out"] = backbone_out
            return sv.Detections.empty(), state
        
        # 手動創建 Supervision Detections 對象
        # 因為 supervision 0.27.0 沒有 from_sam3 方法
        xyxy_list = []
        confidence_list = []
        mask_list = []
        
        for result in sam3_results:
            # 使用 bbox_xyxy 格式 [x1, y1, x2, y2]，如果不存在則從 bbox 轉換
            if "bbox_xyxy" in result:
                xyxy_list.append(result["bbox_xyxy"])
            else:
                # 從 [x, y, width, height] 轉換到 [x1, y1, x2, y2]
                x, y, w, h = result["bbox"]
                xyxy_list.append([x, y, x + w, y + h])
            confidence_list.append(result["score"])
            
            # 確保 mask 是 2D (H, W)
            mask = result["segmentation"]
            if mask.ndim > 2:
                # 如果 mask 是多維的，壓縮到 2D
                mask = np.squeeze(mask)
            if mask.ndim != 2:
                raise ValueError(f"Mask must be 2D, but got shape {mask.shape}")
            mask_list.append(mask)
        
        # 創建 Detections 對象
        # mask 應該是 3D 數組 (N, H, W)，其中 N 是檢測數量
        if mask_list:
            mask_array = np.array(mask_list, dtype=bool)  # Shape: (N, H, W)
        else:
            mask_array = None
        
        detections = sv.Detections(
            xyxy=np.array(xyxy_list, dtype=np.float32),
            confidence=np.array(confidence_list, dtype=np.float32),
            mask=mask_array
        )
        
        # 重置提示但保留 backbone_out 供下一幀使用
        backbone_out = state.get("backbone_out")
        processor.reset_all_prompts(state)
        if backbone_out:
            state["backbone_out"] = backbone_out
        
        return detections, state
