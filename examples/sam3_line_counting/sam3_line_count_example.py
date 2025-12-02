"""
Example: Count objects crossing a line using SAM3 and Supervision

This example demonstrates how to:
1. Load SAM3 model from checkpoint
2. Process video frames with text prompts
3. Track objects across frames
4. Count objects crossing a predefined line
5. Visualize results with Supervision annotators
"""

import argparse
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


def process_video(
    source_video_path: str,
    target_video_path: str,
    model,
    prompt: str,
    line_start: tuple[int, int],
    line_end: tuple[int, int],
    device: str = "cuda",
    confidence_threshold: float = 0.5,
):
    """
    Process video to count objects crossing a line.
    
    Args:
        source_video_path: Path to input video
        target_video_path: Path to output video
        model: SAM3 model instance
        prompt: Text prompt for object detection
        line_start: Start point of the line (x, y)
        line_end: End point of the line (x, y)
        device: Device to run inference on
        confidence_threshold: Confidence threshold for detections
    """
    # Initialize processor
    processor = Sam3Processor(
        model=model,
        device=device,
        confidence_threshold=confidence_threshold,
    )
    
    # Initialize tracker
    tracker = sv.ByteTrack()
    
    # Initialize line zone
    line_zone = sv.LineZone(
        start=sv.Point(x=line_start[0], y=line_start[1]),
        end=sv.Point(x=line_end[0], y=line_end[1]),
    )
    
    # Initialize annotators
    box_annotator = sv.BoxAnnotator()
    label_annotator = sv.LabelAnnotator()
    line_zone_annotator = sv.LineZoneAnnotator()
    trace_annotator = sv.TraceAnnotator()
    
    # Get video info
    video_info = sv.VideoInfo.from_video_path(source_video_path)
    frames_generator = sv.get_video_frames_generator(source_video_path)
    
    # Process state for SAM3 (reuse image features across frames)
    state = {}
    
    print(f"\nProcessing video: {source_video_path}")
    print(f"Prompt: '{prompt}'")
    print(f"Line: ({line_start[0]}, {line_start[1]}) -> ({line_end[0]}, {line_end[1]})")
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
            
            # Track objects
            detections = tracker.update_with_detections(detections)
            
            # Update line zone
            crossed_in, crossed_out = line_zone.trigger(detections)
            
            # Annotate frame
            annotated_frame = frame.copy()
            
            # Draw line
            annotated_frame = line_zone_annotator.annotate(
                scene=annotated_frame,
                line_counter=line_zone,
            )
            
            # Draw traces
            annotated_frame = trace_annotator.annotate(
                scene=annotated_frame,
                detections=detections,
            )
            
            # Draw boxes
            annotated_frame = box_annotator.annotate(
                scene=annotated_frame,
                detections=detections,
            )
            
            # Draw labels
            labels = [
                f"#{tracker_id}" if tracker_id is not None else ""
                for tracker_id in detections.tracker_id
            ]
            annotated_frame = label_annotator.annotate(
                scene=annotated_frame,
                detections=detections,
                labels=labels,
            )
            
            sink.write_frame(annotated_frame)
    
    # Print summary
    print("\n" + "=" * 50)
    print("LINE CROSSING SUMMARY")
    print("=" * 50)
    print(f"  Objects crossed IN:  {line_zone.in_count}")
    print(f"  Objects crossed OUT: {line_zone.out_count}")
    print(f"  Total crossings:     {line_zone.in_count + line_zone.out_count}")
    print("=" * 50 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Count objects crossing a line using SAM3 and Supervision"
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
        "--line_start",
        type=int,
        nargs=2,
        required=True,
        metavar=("X", "Y"),
        help="Start point of the line (x y)",
    )
    parser.add_argument(
        "--line_end",
        type=int,
        nargs=2,
        required=True,
        metavar=("X", "Y"),
        help="End point of the line (x y)",
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
    
    # Validate checkpoint path
    checkpoint_path = Path(args.checkpoint_path)
    if not checkpoint_path.exists():
        raise ValueError(
            f"Checkpoint path does not exist: {checkpoint_path}. "
            f"Please provide a valid path to SAM3 checkpoint directory."
        )
    
    # Validate video path
    if not os.path.exists(args.source_video_path):
        raise ValueError(f"Video path does not exist: {args.source_video_path}")
    
    # Load model
    model = load_sam3_model(str(checkpoint_path), device=args.device)
    
    # Process video
    process_video(
        source_video_path=args.source_video_path,
        target_video_path=args.target_video_path,
        model=model,
        prompt=args.prompt,
        line_start=tuple(args.line_start),
        line_end=tuple(args.line_end),
        device=args.device,
        confidence_threshold=args.confidence_threshold,
    )


if __name__ == "__main__":
    main()
