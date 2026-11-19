"""
SafeVision AI - Core Engine Package
Provides real-time RTSP stream ingestion, YOLOv8 PPE detection with ByteTrack,
and virtual polygon geofencing intrusion monitoring.
"""

from .video_stream import ThreadedRTSPStream
from .zone_monitor import ZoneMonitor
from .ppe_detector import PPEDetector

__all__ = ["ThreadedRTSPStream", "ZoneMonitor", "PPEDetector"]
