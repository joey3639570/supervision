# SAM3 Line Counting

This example demonstrates how to count objects crossing a predefined line in a video using SAM3 (Segment Anything Model 3) for detection and Supervision for tracking and visualization.

## 👋 Overview

This example shows how to:
1. Load SAM3 model from checkpoint
2. Process video frames with text prompts to detect objects
3. Track objects across frames using ByteTrack
4. Count objects crossing a predefined line
5. Visualize results with Supervision annotators

## 💻 Installation

### Prerequisites

- Python 3.8+
- CUDA-capable GPU (recommended) or CPU
- SAM3 checkpoint in `sam3_model` directory (or specify path)

### Setup

1. Clone repository and navigate to example directory:

    ```bash
    git clone --depth 1 -b develop https://github.com/roboflow/supervision.git
    cd supervision/examples/sam3_line_counting
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

Count objects crossing a line in a video:

```bash
python sam3_line_count_example.py \
    --source_video_path /path/to/video.mp4 \
    --target_video_path output.mp4 \
    --prompt "person" \
    --line_start 0 540 \
    --line_end 1920 540 \
    --checkpoint_path sam3_model
```

### Arguments

- `--checkpoint_path` (optional): Path to SAM3 checkpoint directory. Default: `sam3_model`
- `--source_video_path` (required): Path to input video file
- `--target_video_path` (required): Path to output video file
- `--prompt` (required): Text prompt for object detection (e.g., `"person"`, `"car"`)
- `--line_start` (required): Start point of the line as two integers (x y)
- `--line_end` (required): End point of the line as two integers (x y)
- `--confidence_threshold` (optional): Confidence threshold for detections. Default: `0.5`
- `--device` (optional): Device to run inference on (`cuda` or `cpu`). Default: `cuda` if available

### Examples

#### Count people crossing a horizontal line:

```bash
python sam3_line_count_example.py \
    --source_video_path street_scene.mp4 \
    --target_video_path result.mp4 \
    --prompt "person" \
    --line_start 0 540 \
    --line_end 1920 540
```

#### Count cars crossing a diagonal line:

```bash
python sam3_line_count_example.py \
    --source_video_path traffic.mp4 \
    --target_video_path traffic_counted.mp4 \
    --prompt "car" \
    --line_start 0 1080 \
    --line_end 1920 0 \
    --confidence_threshold 0.3
```

## 📊 Output

The script will:
1. Process each frame of the video
2. Detect objects matching the prompt
3. Track objects across frames
4. Count objects crossing the line (in and out directions)
5. Generate an annotated video with:
   - The counting line
   - Object bounding boxes
   - Object tracking traces
   - Tracker IDs
   - In/out counts displayed on the line

At the end, it prints a summary:
```
==================================================
LINE CROSSING SUMMARY
==================================================
  Objects crossed IN:  15
  Objects crossed OUT:  12
  Total crossings:     27
==================================================
```

## 🔧 Troubleshooting

### No Objects Detected

- Lower the confidence threshold: `--confidence_threshold 0.3`
- Try different prompt wording
- Check that the video contains the objects you're searching for

### Line Position

The line coordinates are in pixels:
- Origin (0, 0) is at the top-left corner
- X increases from left to right
- Y increases from top to bottom

To find the right line position, you can:
1. Use a video player to check frame dimensions
2. Use image editing software to find coordinates
3. Start with a simple horizontal or vertical line

### Performance

- Use GPU for faster processing: `--device cuda`
- For long videos, consider processing in chunks
- Reduce video resolution if needed

## 📝 Notes

- LineZone requires tracking, so objects must be tracked across frames
- The line crossing detection uses the object's bounding box anchors
- Objects are counted when they cross the line in either direction
- The trace shows the recent path of each tracked object

## 🔗 Related

- [SAM3 Object Counting Example](../sam3_object_counting/) - Count objects in images
- [SAM3 Zone Counting Example](../sam3_zone_counting/) - Count objects in zones
- [SAM3 Tracking Example](../sam3_tracking/) - Track object movement
- [Supervision LineZone Documentation](https://roboflow.github.io/supervision/latest/detection/tools/line_zone/)

## © License

This demo integrates:
- **SAM3**: Licensed by Meta Platforms, Inc.
- **Supervision**: Licensed under the [MIT license](https://github.com/roboflow/supervision/blob/develop/LICENSE.md)
