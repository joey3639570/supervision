"""
Example: Count objects inside polygon zones using SAM3 and Supervision

This example demonstrates how to:
1. Load SAM3 model from checkpoint
2. Process video frames with text prompts
3. Count objects inside predefined polygon zones
4. Visualize results with Supervision annotators
"""

import argparse
import json
import os
from pathlib import Path
from typing import Dict, List

import cv2
import numpy as np
import torch
from PIL import Image
from tqdm import tqdm

import supervision as sv
from sam3 import build_sam3_image_model
from sam3.model.sam3_image_processor import Sam3Processor

COLORS = sv.ColorPalette.DEFAULT


def load_sam3_model(checkpoint_path: str, device: str = "cuda"):
    """
    Load SAM3 model from checkpoint.
    
    Args:
        checkpoint_path: Path to SAM3 checkpoint file or directory
        device: Device to run inference on ('cuda' or 'cpu')
    
    Returns:
        SAM3 model instance
    """
    checkpoint_file = Path(checkpoint_path)
    
    # If it's a directory, look for common checkpoint file names
    if checkpoint_file.is_dir():
        possible_files = [
            checkpoint_file / "sam3.pt",
            checkpoint_file / "model.safetensors",
            checkpoint_file / "checkpoint.pt",
            checkpoint_file / "model.pt",
        ]
        checkpoint_file = None
        for possible_file in possible_files:
            if possible_file.exists():
                checkpoint_file = possible_file
                break
        
        if checkpoint_file is None:
            raise ValueError(
                f"Could not find checkpoint file in directory {checkpoint_path}. "
                f"Looking for: sam3.pt, model.safetensors, checkpoint.pt, or model.pt"
            )
    
    checkpoint_path_str = str(checkpoint_file)
    print(f"Loading SAM3 model from {checkpoint_path_str}...")
    
    # Build SAM3 model
    model = build_sam3_image_model(
        checkpoint_path=checkpoint_path_str,
        device=device,
        load_from_HF=False,
    )
    model.eval()
    
    return model


def load_zones_config(file_path: str) -> List[np.ndarray]:
    """
    Load polygon zone configurations from a JSON file.
    
    Args:
        file_path: Path to JSON configuration file
    
    Returns:
        List of polygons, each as a NumPy array
    """
    with open(file_path) as file:
        data = json.load(file)
        return [np.array(polygon, np.int32) for polygon in data["polygons"]]


def initiate_zones_and_annotators(
    polygons: List[np.ndarray], resolution_wh: tuple[int, int]
) -> tuple[List[sv.PolygonZone], List[sv.PolygonZoneAnnotator], List[sv.BoxAnnotator]]:
    """
    Initialize polygon zones and annotators.
    
    Args:
        polygons: List of polygon coordinates
        resolution_wh: Video resolution (width, height)
    
    Returns:
        Tuple of (zones, zone_annotators, box_annotators)
    """
    line_thickness = sv.calculate_optimal_line_thickness(resolution_wh=resolution_wh)
    text_scale = sv.calculate_optimal_text_scale(resolution_wh=resolution_wh)
    
    zones = []
    zone_annotators = []
    box_annotators = []
    
    for index, polygon in enumerate(polygons):
        zone = sv.PolygonZone(polygon=polygon)
        zone_annotator = sv.PolygonZoneAnnotator(
            zone=zone,
            color=COLORS.by_idx(index),
            thickness=line_thickness,
            text_thickness=line_thickness * 2,
            text_scale=text_scale * 2,
        )
        box_annotator = sv.BoxAnnotator(
            color=COLORS.by_idx(index),
            thickness=line_thickness,
        )
        zones.append(zone)
        zone_annotators.append(zone_annotator)
        box_annotators.append(box_annotator)
    
    return zones, zone_annotators, box_annotators


def sam3_result_to_supervision_format(
    state: Dict, 
    prompt: str
) -> List[Dict]:
    """
    Convert SAM3 output to format expected by supervision Detections.from_sam3().
    
    Args:
        state: SAM3 processor state containing masks, boxes, scores
        prompt: The text prompt used for detection
    
    Returns:
        List of dictionaries with 'bbox', 'segmentation', and 'area' keys
    """
    if "masks" not in state or state["masks"] is None:
        return []
    
    masks = state["masks"].cpu().numpy()
    boxes = state["boxes"].cpu().numpy()
    scores = state["scores"].cpu().numpy()
    
    results = []
    for i in range(len(masks)):
        # Convert box from [x0, y0, x1, y1] to [x, y, width, height]
        x0, y0, x1, y1 = boxes[i]
        bbox = [float(x0), float(y0), float(x1 - x0), float(y1 - y0)]
        
        # Get mask as boolean array
        mask = masks[i].astype(bool)
        
        # Calculate area
        area = float(np.sum(mask))
        
        results.append({
            "bbox": bbox,
            "segmentation": mask,
            "area": area,
            "score": float(scores[i]),
            "prompt": prompt,
        })
    
    return results


def detect_objects_in_frame(
    frame: np.ndarray,
    model,
    processor: Sam3Processor,
    prompt: str,
    state: Dict,
    confidence_threshold: float = 0.5,
) -> sv.Detections:
    """
    Detect objects in a frame using SAM3.
    
    Args:
        frame: Input frame as numpy array
        model: SAM3 model instance
        processor: SAM3 processor instance
        prompt: Text prompt for detection
        state: Processor state (will be updated)
        confidence_threshold: Confidence threshold for detections
    
    Returns:
        Supervision Detections object
    """
    # Convert frame to PIL Image
    image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    
    # Set image if not already set
    if "backbone_out" not in state:
        state = processor.set_image(image, state={})
    
    # Set text prompt and get results
    state = processor.set_text_prompt(prompt, state)
    
    # Convert to supervision format
    sam3_results = sam3_result_to_supervision_format(state, prompt)
    
    if not sam3_results:
        # Reset prompts but keep backbone_out
        backbone_out = state.get("backbone_out")
        processor.reset_all_prompts(state)
        if backbone_out:
            state["backbone_out"] = backbone_out
        return sv.Detections.empty()
    
    # Convert to supervision Detections
    detections = sv.Detections.from_sam3(sam3_results)
    
    # Reset prompts but keep backbone_out for next frame
    backbone_out = state.get("backbone_out")
    processor.reset_all_prompts(state)
    if backbone_out:
        state["backbone_out"] = backbone_out
    
    return detections


def annotate_frame(
    frame: np.ndarray,
    zones: List[sv.PolygonZone],
    zone_annotators: List[sv.PolygonZoneAnnotator],
    box_annotators: List[sv.BoxAnnotator],
    detections: sv.Detections,
) -> np.ndarray:
    """
    Annotate frame with zones and detections.
    
    Args:
        frame: Input frame
        zones: List of polygon zones
        zone_annotators: List of zone annotators
        box_annotators: List of box annotators
        detections: Detections to annotate
    
    Returns:
        Annotated frame
    """
    annotated_frame = frame.copy()
    
    for zone, zone_annotator, box_annotator in zip(
        zones, zone_annotators, box_annotators
    ):
        detections_in_zone = detections[zone.trigger(detections=detections)]
        annotated_frame = zone_annotator.annotate(scene=annotated_frame)
        annotated_frame = box_annotator.annotate(
            scene=annotated_frame,
            detections=detections_in_zone,
        )
    
    return annotated_frame


def process_video(
    source_video_path: str,
    target_video_path: str,
    model,
    prompt: str,
    zone_config_path: str,
    device: str = "cuda",
    confidence_threshold: float = 0.5,
):
    """
    Process video to count objects in zones.
    
    Args:
        source_video_path: Path to input video
        target_video_path: Path to output video
        model: SAM3 model instance
        prompt: Text prompt for object detection
        zone_config_path: Path to zone configuration JSON file
        device: Device to run inference on
        confidence_threshold: Confidence threshold for detections
    """
    # Initialize processor
    processor = Sam3Processor(
        model=model,
        device=device,
        confidence_threshold=confidence_threshold,
    )
    
    # Get video info
    video_info = sv.VideoInfo.from_video_path(source_video_path)
    
    # Load zones
    polygons = load_zones_config(zone_config_path)
    zones, zone_annotators, box_annotators = initiate_zones_and_annotators(
        polygons=polygons,
        resolution_wh=video_info.resolution_wh,
    )
    
    # Process state for SAM3
    state = {}
    
    frames_generator = sv.get_video_frames_generator(source_video_path)
    
    print(f"\nProcessing video: {source_video_path}")
    print(f"Prompt: '{prompt}'")
    print(f"Number of zones: {len(zones)}")
    print(f"Total frames: {video_info.total_frames}\n")
    
    with sv.VideoSink(target_path=target_video_path, video_info=video_info) as sink:
        for frame in tqdm(frames_generator, total=video_info.total_frames):
            # Detect objects
            detections = detect_objects_in_frame(
                frame=frame,
                model=model,
                processor=processor,
                prompt=prompt,
                state=state,
                confidence_threshold=confidence_threshold,
            )
            
            # Annotate frame
            annotated_frame = annotate_frame(
                frame=frame,
                zones=zones,
                zone_annotators=zone_annotators,
                box_annotators=box_annotators,
                detections=detections,
            )
            
            sink.write_frame(annotated_frame)
    
    # Print summary
    print("\n" + "=" * 50)
    print("ZONE COUNTING SUMMARY")
    print("=" * 50)
    for i, zone in enumerate(zones):
        print(f"  Zone {i + 1}: {zone.current_count} objects")
    print("=" * 50 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Count objects in polygon zones using SAM3 and Supervision"
    )
    
    parser.add_argument(
        "--checkpoint_path",
        type=str,
        default="sam3_model",
        help="Path to SAM3 checkpoint directory (default: sam3_model)",
    )
    parser.add_argument(
        "--source_video_path",
        type=str,
        required=True,
        help="Path to input video file",
    )
    parser.add_argument(
        "--target_video_path",
        type=str,
        required=True,
        help="Path to output video file",
    )
    parser.add_argument(
        "--prompt",
        type=str,
        required=True,
        help="Text prompt for object detection (e.g., 'person', 'car')",
    )
    parser.add_argument(
        "--zone_config_path",
        type=str,
        required=True,
        help="Path to zone configuration JSON file",
    )
    parser.add_argument(
        "--confidence_threshold",
        type=float,
        default=0.5,
        help="Confidence threshold for detections (default: 0.5)",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cuda" if torch.cuda.is_available() else "cpu",
        help="Device to run inference on (default: cuda if available, else cpu)",
    )
    
    args = parser.parse_args()
    
    # Validate paths
    checkpoint_path = Path(args.checkpoint_path)
    if not checkpoint_path.exists():
        raise ValueError(
            f"Checkpoint path does not exist: {checkpoint_path}. "
            f"Please provide a valid path to SAM3 checkpoint directory."
        )
    
    if not os.path.exists(args.source_video_path):
        raise ValueError(f"Video path does not exist: {args.source_video_path}")
    
    if not os.path.exists(args.zone_config_path):
        raise ValueError(f"Zone config path does not exist: {args.zone_config_path}")
    
    # Load model
    model = load_sam3_model(str(checkpoint_path), device=args.device)
    
    # Process video
    process_video(
        source_video_path=args.source_video_path,
        target_video_path=args.target_video_path,
        model=model,
        prompt=args.prompt,
        zone_config_path=args.zone_config_path,
        device=args.device,
        confidence_threshold=args.confidence_threshold,
    )


if __name__ == "__main__":
    main()
