# SAM3 Zone Counting

This example demonstrates how to count objects inside polygon zones in a video using SAM3 (Segment Anything Model 3) for detection and Supervision for zone visualization.

## 👋 Overview

This example shows how to:
1. Load SAM3 model from checkpoint
2. Process video frames with text prompts to detect objects
3. Count objects inside predefined polygon zones
4. Visualize results with Supervision annotators

## 💻 Installation

### Prerequisites

- Python 3.8+
- CUDA-capable GPU (recommended) or CPU
- SAM3 checkpoint in `sam3_model` directory (or specify path)

### Setup

1. Clone repository and navigate to example directory:

    ```bash
    git clone --depth 1 -b develop https://github.com/roboflow/supervision.git
    cd supervision/examples/sam3_zone_counting
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

Count objects in polygon zones:

```bash
python sam3_zone_count_example.py \
    --source_video_path /path/to/video.mp4 \
    --target_video_path output.mp4 \
    --prompt "person" \
    --zone_config_path zones.json \
    --checkpoint_path sam3_model
```

### Arguments

- `--checkpoint_path` (optional): Path to SAM3 checkpoint directory. Default: `sam3_model`
- `--source_video_path` (required): Path to input video file
- `--target_video_path` (required): Path to output video file
- `--prompt` (required): Text prompt for object detection (e.g., `"person"`, `"car"`)
- `--zone_config_path` (required): Path to zone configuration JSON file
- `--confidence_threshold` (optional): Confidence threshold for detections. Default: `0.5`
- `--device` (optional): Device to run inference on (`cuda` or `cpu`). Default: `cuda` if available

### Zone Configuration Format

The zone configuration file should be a JSON file with the following format:

```json
{
  "polygons": [
    [[x1, y1], [x2, y2], [x3, y3], [x4, y4]],
    [[x1, y1], [x2, y2], [x3, y3]]
  ]
}
```

Each polygon is defined as a list of `[x, y]` coordinate pairs. You can have multiple polygons.

### Examples

#### Count people in multiple zones:

```bash
python sam3_zone_count_example.py \
    --source_video_path street_scene.mp4 \
    --target_video_path result.mp4 \
    --prompt "person" \
    --zone_config_path zones.json
```

#### Count cars in zones with lower confidence:

```bash
python sam3_zone_count_example.py \
    --source_video_path traffic.mp4 \
    --target_video_path traffic_counted.mp4 \
    --prompt "car" \
    --zone_config_path traffic_zones.json \
    --confidence_threshold 0.3
```

### Example Zone Configuration

Create a file `zones.json`:

```json
{
  "polygons": [
    [[100, 100], [500, 100], [500, 400], [100, 400]],
    [[600, 200], [1000, 200], [1000, 600], [600, 600]]
  ]
}
```

This defines two rectangular zones. You can use any polygon shape with 3 or more points.

## 📊 Output

The script will:
1. Process each frame of the video
2. Detect objects matching the prompt
3. Count objects in each zone
4. Generate an annotated video with:
   - Zone boundaries highlighted
   - Object bounding boxes colored by zone
   - Zone counts displayed

At the end, it prints a summary:
```
==================================================
ZONE COUNTING SUMMARY
==================================================
  Zone 1: 5 objects
  Zone 2: 3 objects
==================================================
```

## 🔧 Troubleshooting

### Creating Zone Configurations

You can create zone configurations manually or use tools:

1. **Manual creation**: Edit a JSON file with polygon coordinates
2. **Use image editor**: Open a frame in an image editor, note coordinates
3. **Use supervision tools**: Check the `count_people_in_zone` example for zone drawing utilities

### Zone Coordinates

- Origin (0, 0) is at the top-left corner
- X increases from left to right
- Y increases from top to bottom
- Coordinates are in pixels

### No Objects Detected

- Lower the confidence threshold: `--confidence_threshold 0.3`
- Try different prompt wording
- Check that zones are positioned correctly

### Performance

- Use GPU for faster processing: `--device cuda`
- For long videos, consider processing in chunks
- Reduce video resolution if needed

## 📝 Notes

- Each zone is displayed in a different color
- Objects are counted if their center point is inside the zone
- The count updates in real-time as objects enter/leave zones
- You can define any number of zones

## 🔗 Related

- [SAM3 Object Counting Example](../sam3_object_counting/) - Count objects in images
- [SAM3 Line Counting Example](../sam3_line_counting/) - Count objects crossing a line
- [SAM3 Tracking Example](../sam3_tracking/) - Track object movement
- [Supervision PolygonZone Documentation](https://roboflow.github.io/supervision/latest/detection/tools/polygon_zone/)

## © License

This demo integrates:
- **SAM3**: Licensed by Meta Platforms, Inc.
- **Supervision**: Licensed under the [MIT license](https://github.com/roboflow/supervision/blob/develop/LICENSE.md)
