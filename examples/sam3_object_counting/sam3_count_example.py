"""
Example: Count objects by prompt using SAM3 and Supervision

This example demonstrates how to:
1. Load SAM3 model from checkpoint
2. Process images with text prompts
3. Count objects matching each prompt
4. Visualize results with Supervision annotators
"""

import argparse
import os
from pathlib import Path
from typing import List, Dict

import cv2
import numpy as np
import torch
from PIL import Image

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
        load_from_HF=False,  # We're providing our own checkpoint
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


def count_objects_by_prompt(
    image_path: str,
    model,
    prompts: List[str],
    device: str = "cuda",
    confidence_threshold: float = 0.5,
) -> Dict[str, int]:
    """
    Count objects in an image matching each prompt.
    
    Args:
        image_path: Path to input image
        model: SAM3 model instance
        prompts: List of text prompts to search for
        device: Device to run inference on
        confidence_threshold: Confidence threshold for detections
    
    Returns:
        Dictionary mapping prompts to object counts
    """
    # Load image
    image = Image.open(image_path).convert("RGB")
    image_np = np.array(image)
    
    # Initialize processor
    processor = Sam3Processor(
        model=model,
        device=device,
        confidence_threshold=confidence_threshold,
    )
    
    # Set image
    state = processor.set_image(image, state={})
    
    all_detections = []
    prompt_counts = {}
    
    # Process each prompt
    for prompt in prompts:
        print(f"Processing prompt: '{prompt}'...")
        
        # Set text prompt and get results
        state = processor.set_text_prompt(prompt, state)
        
        # Convert to supervision format
        sam3_results = sam3_result_to_supervision_format(state, prompt)
        all_detections.extend(sam3_results)
        
        # Count objects for this prompt
        count = len(sam3_results)
        prompt_counts[prompt] = count
        print(f"  Found {count} objects matching '{prompt}'")
        
        # Reset prompts for next iteration (keep image features in backbone_out)
        # Save backbone_out before resetting
        backbone_out = state["backbone_out"]
        processor.reset_all_prompts(state)
        # Restore backbone_out after reset
        state["backbone_out"] = backbone_out
    
    return prompt_counts, all_detections, image_np


def visualize_results(
    image: np.ndarray,
    all_detections: List[Dict],
    output_path: str = None,
):
    """
    Visualize detection results using Supervision annotators.
    
    Args:
        image: Input image as numpy array
        all_detections: List of detection dictionaries
        output_path: Optional path to save annotated image
    """
    if not all_detections:
        print("No detections to visualize.")
        return
    
    # Convert to supervision Detections format
    sam3_results = [
        {
            "bbox": det["bbox"],
            "segmentation": det["segmentation"],
            "area": det["area"],
        }
        for det in all_detections
    ]
    
    detections = sv.Detections.from_sam3(sam3_results)
    
    # Create annotators
    mask_annotator = sv.MaskAnnotator()
    box_annotator = sv.BoxAnnotator()
    label_annotator = sv.LabelAnnotator()
    
    # Group detections by prompt for different colors
    prompt_to_detections = {}
    for i, det in enumerate(all_detections):
        prompt = det.get("prompt", "unknown")
        if prompt not in prompt_to_detections:
            prompt_to_detections[prompt] = []
        prompt_to_detections[prompt].append(i)
    
    # Annotate image
    annotated_image = image.copy()
    
    # Use different colors for different prompts
    colors = sv.ColorPalette.DEFAULT
    for idx, (prompt, det_indices) in enumerate(prompt_to_detections.items()):
        color = colors.by_idx(idx)
        
        # Filter detections for this prompt
        prompt_detections = detections[det_indices]
        
        # Annotate masks
        mask_annotator.color = color
        annotated_image = mask_annotator.annotate(
            scene=annotated_image,
            detections=prompt_detections,
        )
        
        # Annotate boxes
        box_annotator.color = color
        annotated_image = box_annotator.annotate(
            scene=annotated_image,
            detections=prompt_detections,
        )
        
        # Annotate labels with prompt and count
        labels = [
            f"{prompt} ({len(det_indices)})"
            for _ in range(len(prompt_detections))
        ]
        label_annotator.color = color
        annotated_image = label_annotator.annotate(
            scene=annotated_image,
            detections=prompt_detections,
            labels=labels,
        )
    
    # Display or save
    if output_path:
        cv2.imwrite(output_path, cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR))
        print(f"Annotated image saved to {output_path}")
    else:
        # Display image
        cv2.imshow("SAM3 Object Counting", cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR))
        print("Press any key to close the window...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(
        description="Count objects by prompt using SAM3 and Supervision"
    )
    
    parser.add_argument(
        "--checkpoint_path",
        type=str,
        default="sam3_model",
        help="Path to SAM3 checkpoint directory (default: sam3_model)",
    )
    parser.add_argument(
        "--image_path",
        type=str,
        required=True,
        help="Path to input image",
    )
    parser.add_argument(
        "--prompts",
        type=str,
        nargs="+",
        required=True,
        help="Text prompts to search for (e.g., 'person' 'car' 'dog')",
    )
    parser.add_argument(
        "--output_path",
        type=str,
        default=None,
        help="Path to save annotated output image (optional)",
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
    
    # Validate image path
    if not os.path.exists(args.image_path):
        raise ValueError(f"Image path does not exist: {args.image_path}")
    
    # Load model
    model = load_sam3_model(str(checkpoint_path), device=args.device)
    
    # Count objects
    print(f"\nProcessing image: {args.image_path}")
    print(f"Prompts: {args.prompts}\n")
    
    prompt_counts, all_detections, image = count_objects_by_prompt(
        image_path=args.image_path,
        model=model,
        prompts=args.prompts,
        device=args.device,
        confidence_threshold=args.confidence_threshold,
    )
    
    # Print summary
    print("\n" + "=" * 50)
    print("OBJECT COUNT SUMMARY")
    print("=" * 50)
    total_count = sum(prompt_counts.values())
    for prompt, count in prompt_counts.items():
        print(f"  {prompt}: {count}")
    print(f"\n  Total objects detected: {total_count}")
    print("=" * 50 + "\n")
    
    # Visualize results
    if all_detections:
        visualize_results(
            image=image,
            all_detections=all_detections,
            output_path=args.output_path,
        )
    else:
        print("No objects detected. Try adjusting the confidence threshold or prompts.")


if __name__ == "__main__":
    main()
