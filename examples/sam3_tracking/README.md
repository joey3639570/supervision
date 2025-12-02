# SAM3 Object Tracking

This example demonstrates how to track objects across video frames using SAM3 (Segment Anything Model 3) for detection and Supervision's ByteTrack for tracking.

## 👋 Overview

This example shows how to:
1. Load SAM3 model from checkpoint
2. Process video frames with text prompts to detect objects
3. Track objects across frames using ByteTrack
4. Visualize tracking results with masks, boxes, traces, and labels

## 💻 Installation

### Prerequisites

- Python 3.8+
- CUDA-capable GPU (recommended) or CPU
- SAM3 checkpoint in `sam3_model` directory (or specify path)

### Setup

1. Clone repository and navigate to example directory:

    ```bash
    git clone --depth 1 -b develop https://github.com/roboflow/supervision.git
    cd supervision/examples/sam3_tracking
    ```

2. Setup python environment and activate it [optional]:

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3. Install required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4. Install SAM3:

    ```bash
    # If sam3 is symlinked in the supervision directory:
    pip install -e ../sam3
    
    # Or if you have sam3 in a different location:
    pip install -e /path/to/sam3
    ```

## 🛠️ Usage

### Basic Usage

Track objects in a video:

```bash
python sam3_tracking_example.py \
    --source_video_path /path/to/video.mp4 \
    --target_video_path output.mp4 \
    --prompt "person" \
    --checkpoint_path sam3_model
```

### Arguments

- `--checkpoint_path` (optional): Path to SAM3 checkpoint directory. Default: `sam3_model`
- `--source_video_path` (required): Path to input video file
- `--target_video_path` (required): Path to output video file
- `--prompt` (required): Text prompt for object detection (e.g., `"person"`, `"car"`)
- `--confidence_threshold` (optional): Confidence threshold for detections. Default: `0.5`
- `--trace_length` (optional): Number of frames to show in trace. Default: `30`
- `--device` (optional): Device to run inference on (`cuda` or `cpu`). Default: `cuda` if available

### Examples

#### Track people with default settings:

```bash
python sam3_tracking_example.py \
    --source_video_path street_scene.mp4 \
    --target_video_path result.mp4 \
    --prompt "person"
```

#### Track cars with longer traces:

```bash
python sam3_tracking_example.py \
    --source_video_path traffic.mp4 \
    --target_video_path traffic_tracked.mp4 \
    --prompt "car" \
    --trace_length 60 \
    --confidence_threshold 0.3
```

#### Track multiple object types (run multiple times):

```bash
# Track people
python sam3_tracking_example.py \
    --source_video_path scene.mp4 \
    --target_video_path people_tracked.mp4 \
    --prompt "person"

# Track cars
python sam3_tracking_example.py \
    --source_video_path scene.mp4 \
    --target_video_path cars_tracked.mp4 \
    --prompt "car"
```

## 📊 Output

The script will:
1. Process each frame of the video
2. Detect objects matching the prompt
3. Track objects across frames using ByteTrack
4. Generate an annotated video with:
   - Segmentation masks for each object
   - Bounding boxes around tracked objects
   - Traces showing object movement paths
   - Labels with tracker IDs and confidence scores

At the end, it prints a summary:
```
==================================================
TRACKING SUMMARY
==================================================
  Total unique objects tracked: 15
  Average track length: 45.3 frames
  Longest track: 120 frames
  Shortest track: 5 frames
==================================================
```

## 🔧 Troubleshooting

### No Objects Tracked

- Lower the confidence threshold: `--confidence_threshold 0.3`
- Try different prompt wording
- Check that the video contains the objects you're searching for
- Ensure objects are visible for multiple frames (tracking needs continuity)

### Tracking Issues

- **Objects losing IDs**: This can happen with occlusions or fast movement. Try adjusting confidence threshold
- **Multiple IDs for same object**: Usually happens with detection failures. Lower confidence threshold
- **Short tracks**: Objects may be leaving frame quickly or detection is inconsistent

### Performance

- Use GPU for faster processing: `--device cuda`
- Reduce trace length for better performance: `--trace_length 15`
- For long videos, consider processing in chunks
- Reduce video resolution if needed

### Trace Length

The trace length determines how many previous positions are shown:
- Longer traces (60+) show more history but may clutter the display
- Shorter traces (15-30) are cleaner but show less history
- Adjust based on your needs

## 📝 Notes

- Each tracked object gets a unique ID that persists across frames
- Traces show the recent path of each object
- Masks provide pixel-level segmentation
- The tracker uses ByteTrack algorithm for robust tracking
- Objects are tracked even through temporary occlusions

## 🔗 Related

- [SAM3 Object Counting Example](../sam3_object_counting/) - Count objects in images
- [SAM3 Line Counting Example](../sam3_line_counting/) - Count objects crossing a line
- [SAM3 Zone Counting Example](../sam3_zone_counting/) - Count objects in zones
- [Supervision Tracking Documentation](https://roboflow.github.io/supervision/latest/trackers/)
- [ByteTrack Paper](https://arxiv.org/abs/2110.06864)

## © License

This demo integrates:
- **SAM3**: Licensed by Meta Platforms, Inc.
- **Supervision**: Licensed under the [MIT license](https://github.com/roboflow/supervision/blob/develop/LICENSE.md)
