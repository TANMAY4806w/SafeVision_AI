"""
Unit tests for PPE Detection, Spatial Association & Temporal Debouncing.
"""

import os
import sys
import pytest

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine.ppe_detector import PPEDetector


@pytest.fixture
def detector():
    # Use yolov8n.pt (downloads nano weights if not cached)
    return PPEDetector(model_path="yolov8n.pt", debounce_frames=3)


def test_spatial_ppe_association_compliant(detector):
    # Worker at [100, 100, 200, 400] (Height = 300)
    # Head zone: top 25% -> [100, 100, 200, 175]
    # Torso zone: 20% to 70% -> [100, 160, 200, 310]
    worker_bbox = [100.0, 100.0, 200.0, 400.0]

    gear_items = [
        {"class_name": "helmet", "bbox": [120.0, 105.0, 180.0, 160.0]},
        {"class_name": "vest", "bbox": [110.0, 180.0, 190.0, 280.0]}
    ]

    has_helmet, has_vest = detector._check_worker_ppe(worker_bbox, gear_items)
    assert has_helmet is True
    assert has_vest is True


def test_spatial_ppe_association_violation(detector):
    worker_bbox = [100.0, 100.0, 200.0, 400.0]

    # Helmet is outside head zone (e.g. far away at [400, 400, 450, 450])
    gear_items = [
        {"class_name": "helmet", "bbox": [400.0, 400.0, 450.0, 450.0]}
    ]

    has_helmet, has_vest = detector._check_worker_ppe(worker_bbox, gear_items)
    assert has_helmet is False
    assert has_vest is False
