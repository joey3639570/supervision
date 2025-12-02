# SAM3 Object Counting

This example demonstrates how to count objects in images using SAM3 (Segment Anything Model 3) with text prompts and Supervision for visualization.

## 👋 Overview

SAM3 is the latest version of the Segment Anything Model, which supports concept-based prompting (e.g., phrases, image examples) for detecting, segmenting, and tracking objects in images and videos. This example shows how to:

1. Load SAM3 model from checkpoint
2. Process images with multiple text prompts
3. Count objects matching each prompt
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
    cd supervision/examples/sam3_object_counting
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
    # If SAM3 is not installed, install it from the sam3 directory
    # Option 1: If sam3 is symlinked in the supervision directory:
    pip install -e ../sam3
    
    # Option 2: If you have sam3 in a different location:
    pip install -e /path/to/sam3
    
    # Option 3: Install from the SAM3 repository directly:
    # git clone https://github.com/facebookresearch/sam3.git
    # cd sam3
    # pip install -e .
    ```
    
    **Note**: Make sure SAM3 is properly installed and importable before running the example.

## 🛠️ Usage

### Basic Usage

Count objects matching specific prompts in an image:

```bash
python sam3_count_example.py \
    --image_path /path/to/image.jpg \
    --prompts "person" "car" "dog" \
    --checkpoint_path sam3_model \
    --confidence_threshold 0.5
```

### Arguments

- `--checkpoint_path` (optional): Path to SAM3 checkpoint directory. Default: `sam3_model`
- `--image_path` (required): Path to input image file
- `--prompts` (required): One or more text prompts to search for (e.g., `"person" "car" "dog"`)
- `--output_path` (optional): Path to save annotated output image. If not provided, displays the image
- `--confidence_threshold` (optional): Confidence threshold for detections. Default: `0.5`
- `--device` (optional): Device to run inference on (`cuda` or `cpu`). Default: `cuda` if available, else `cpu`

### Examples

#### Count people and cars:

```bash
python sam3_count_example.py \
    --image_path street_scene.jpg \
    --prompts "person" "car" \
    --output_path result.jpg
```

#### Count multiple object types with custom confidence:

```bash
python sam3_count_example.py \
    --image_path park.jpg \
    --prompts "person" "dog" "bicycle" "bench" \
    --confidence_threshold 0.3 \
    --output_path park_counted.jpg
```

#### Run on CPU:

```bash
python sam3_count_example.py \
    --image_path image.jpg \
    --prompts "cat" "dog" \
    --device cpu
```

## 📊 Output

The script will:

1. Process each prompt and detect matching objects
2. Print a summary showing the count for each prompt:
   ```
   ==================================================
   OBJECT COUNT SUMMARY
   ==================================================
     person: 5
     car: 3
   
     Total objects detected: 8
   ==================================================
   ```
3. Visualize results with:
   - Colored masks for each detected object
   - Bounding boxes around each object
   - Labels showing the prompt and count

## 🔧 Troubleshooting

### Checkpoint Not Found

If you get an error about checkpoint path:

```bash
# Make sure sam3_model directory exists or specify the correct path
python sam3_count_example.py \
    --checkpoint_path /path/to/sam3_model \
    --image_path image.jpg \
    --prompts "person"
```

### CUDA Out of Memory

If you run out of GPU memory:

1. Use a smaller image or resize it before processing
2. Process prompts one at a time (modify the script)
3. Use CPU instead: `--device cpu` (slower but uses less memory)

### No Detections Found

If no objects are detected:

1. Lower the confidence threshold: `--confidence_threshold 0.3`
2. Try different prompt wording
3. Check that the image contains the objects you're searching for

## 📝 Notes

- SAM3 supports natural language prompts, so you can use descriptive phrases
- The model processes each prompt independently
- Results are visualized with different colors for each prompt type
- The script converts SAM3 output format to Supervision's Detections format for easy visualization

## 🔗 Related

- [SAM3 Repository](https://github.com/facebookresearch/sam3)
- [Supervision Documentation](https://roboflow.github.io/supervision/)
- Other examples in the `examples/` directory

## © License

This demo integrates two main components:

- **SAM3**: The Segment Anything Model 3, licensed by Meta Platforms, Inc.
- **Supervision**: Licensed under the [MIT license](https://github.com/roboflow/supervision/blob/develop/LICENSE.md)
