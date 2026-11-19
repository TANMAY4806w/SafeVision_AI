"""
Unit tests for Virtual Polygon Danger Zone Geofencing & Spatial Intrusion Logic.
"""

import os
import sys
import numpy as np
import pytest

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine.zone_monitor import ZoneMonitor


@pytest.fixture
def sample_zones():
    return [
        {
            "name": "Test_Machinery_Zone",
            "severity": "CRITICAL",
            "polygon": [
                [100, 100],
                [300, 100],
                [300, 300],
                [100, 300]
            ]
        }
    ]


def test_ground_contact_point():
    bbox = (100.0, 50.0, 200.0, 250.0)
    x_foot, y_foot = ZoneMonitor.get_ground_contact_point(bbox)
    assert x_foot == 150
    assert y_foot == 250


def test_intrusion_detection_inside(sample_zones):
    monitor = ZoneMonitor(sample_zones)
    # Worker whose feet are at (200, 200), strictly inside the [100,100] to [300,300] zone
    worker_inside = (150, 100, 250, 200)
    alerts = monitor.check_intrusion([worker_inside], track_ids=[101])

    assert len(alerts) == 1
    assert alerts[0]["event_type"] == "ZONE_INTRUSION"
    assert alerts[0]["worker_id"] == 101
    assert alerts[0]["zone_name"] == "Test_Machinery_Zone"


def test_intrusion_detection_outside(sample_zones):
    monitor = ZoneMonitor(sample_zones)
    # Worker whose feet are at (500, 500), outside the zone
    worker_outside = (450, 400, 550, 500)
    alerts = monitor.check_intrusion([worker_outside], track_ids=[102])

    assert len(alerts) == 0


def test_annotation_rendering(sample_zones):
    monitor = ZoneMonitor(sample_zones)
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    alerts = [{"zone_name": "Test_Machinery_Zone"}]
    annotated = monitor.annotate(frame, alerts)

    assert annotated.shape == (480, 640, 3)
    # Pixels should be modified by overlay
    assert np.any(annotated > 0)
