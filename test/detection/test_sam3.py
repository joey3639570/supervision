from __future__ import annotations

import numpy as np
import pytest

from supervision.detection.core import Detections


def test_from_sam3_with_valid_input():
    """Test from_sam3 with valid SAM3 output format."""
    # Create mock SAM3 result with same format as SAM/SAM2
    sam3_result = [
        {
            "bbox": [10, 20, 100, 150],  # x, y, width, height
            "segmentation": np.zeros((200, 300), dtype=bool),
            "area": 15000,
        },
        {
            "bbox": [50, 60, 80, 90],
            "segmentation": np.ones((200, 300), dtype=bool),
            "area": 7200,
        },
    ]
    # Set some pixels in the masks
    sam3_result[0]["segmentation"][20:170, 10:110] = True
    sam3_result[1]["segmentation"][60:150, 50:130] = True

    detections = Detections.from_sam3(sam3_result)

    assert len(detections) == 2
    assert detections.xyxy.shape == (2, 4)
    assert detections.mask is not None
    assert detections.mask.shape == (2, 200, 300)
    # Check that masks are sorted by area (largest first)
    assert detections.xyxy[0, 0] == 10  # First mask (larger area)
    assert detections.xyxy[1, 0] == 50  # Second mask (smaller area)


def test_from_sam3_with_empty_result():
    """Test from_sam3 with empty result."""
    sam3_result = []
    detections = Detections.from_sam3(sam3_result)
    assert detections.is_empty()


def test_from_sam3_without_area_field():
    """Test from_sam3 when area field is missing."""
    sam3_result = [
        {
            "bbox": [10, 20, 100, 150],
            "segmentation": np.zeros((200, 300), dtype=bool),
        },
        {
            "bbox": [50, 60, 80, 90],
            "segmentation": np.ones((200, 300), dtype=bool),
        },
    ]
    sam3_result[0]["segmentation"][20:170, 10:110] = True
    sam3_result[1]["segmentation"][60:150, 50:130] = True

    detections = Detections.from_sam3(sam3_result)

    assert len(detections) == 2
    assert detections.xyxy.shape == (2, 4)
    assert detections.mask is not None


def test_from_sam3_bbox_conversion():
    """Test that bbox is correctly converted from xywh to xyxy."""
    sam3_result = [
        {
            "bbox": [10, 20, 100, 150],  # x, y, width, height
            "segmentation": np.zeros((200, 300), dtype=bool),
            "area": 15000,
        }
    ]
    sam3_result[0]["segmentation"][20:170, 10:110] = True

    detections = Detections.from_sam3(sam3_result)

    # xyxy should be [x, y, x+width, y+height] = [10, 20, 110, 170]
    assert detections.xyxy[0, 0] == 10
    assert detections.xyxy[0, 1] == 20
    assert detections.xyxy[0, 2] == 110
    assert detections.xyxy[0, 3] == 170


def test_from_sam3_mask_preservation():
    """Test that masks are correctly preserved."""
    mask1 = np.zeros((100, 100), dtype=bool)
    mask1[10:50, 20:60] = True

    mask2 = np.zeros((100, 100), dtype=bool)
    mask2[60:90, 70:95] = True

    sam3_result = [
        {
            "bbox": [20, 10, 40, 40],
            "segmentation": mask1,
            "area": 1600,
        },
        {
            "bbox": [70, 60, 25, 30],
            "segmentation": mask2,
            "area": 750,
        },
    ]

    detections = Detections.from_sam3(sam3_result)

    assert detections.mask is not None
    assert np.array_equal(detections.mask[0], mask1)
    assert np.array_equal(detections.mask[1], mask2)


def test_from_sam3_single_mask():
    """Test from_sam3 with a single mask."""
    sam3_result = [
        {
            "bbox": [0, 0, 50, 50],
            "segmentation": np.ones((100, 100), dtype=bool),
            "area": 2500,
        }
    ]

    detections = Detections.from_sam3(sam3_result)

    assert len(detections) == 1
    assert detections.xyxy.shape == (1, 4)
    assert detections.mask is not None
    assert detections.mask.shape == (1, 100, 100)



