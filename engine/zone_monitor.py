"""
Virtual Polygon Danger Zone Geofencing & Spatial Intrusion Engine.
Evaluates ground-contact coordinates against hazardous plant perimeters.
"""

import json
import logging
from typing import List, Dict, Any, Tuple, Optional, Union
import numpy as np
import cv2

logger = logging.getLogger("SafeVision.ZoneMonitor")


class ZoneMonitor:
    """
    Manages virtual safety geofences and monitors worker intrusion into restricted plant machinery zones.
    """

    def __init__(self, zones_config: Union[str, List[Dict[str, Any]]]):
        """
        :param zones_config: Path to a JSON configuration file, or direct list of zone dictionaries:
            [
                {
                    "name": "Robotic Arm Area",
                    "polygon": [[100, 200], [400, 200], [400, 500], [100, 500]],
                    "severity": "CRITICAL"
                }
            ]
        """
        self.zones: List[Dict[str, Any]] = []
        if isinstance(zones_config, str):
            self.load_zones_from_file(zones_config)
        else:
            self.zones = self._format_zones(zones_config)

    def load_zones_from_file(self, file_path: str):
        """Loads and formats polygon definitions from a JSON file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                raw_zones = data.get("zones", data) if isinstance(data, dict) else data
                self.zones = self._format_zones(raw_zones)
                logger.info(f"Loaded {len(self.zones)} safety zones from {file_path}")
        except Exception as e:
            logger.error(f"Failed to load zones file '{file_path}': {e}")
            self.zones = []

    def _format_zones(self, raw_zones: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Pre-processes polygon vertices into NumPy contours for fast cv2 operations."""
        formatted = []
        for z in raw_zones:
            name = z.get("name", "Restricted_Zone")
            polygon_pts = z.get("polygon", [])
            if len(polygon_pts) < 3:
                logger.warning(f"Zone '{name}' has fewer than 3 vertices. Skipping.")
                continue
            contour = np.array(polygon_pts, dtype=np.int32).reshape((-1, 1, 2))
            formatted.append({
                "name": name,
                "contour": contour,
                "polygon": polygon_pts,
                "severity": z.get("severity", "CRITICAL"),
                "active_intruders": 0
            })
        return formatted

    @staticmethod
    def get_ground_contact_point(bbox: Tuple[float, float, float, float]) -> Tuple[int, int]:
        """
        Calculates the bottom-center foot coordinate of a worker bounding box.
        bbox: (x1, y1, x2, y2)
        """
        x1, y1, x2, y2 = bbox
        x_foot = int((x1 + x2) / 2)
        y_foot = int(y2)
        return x_foot, y_foot

    def check_intrusion(
        self,
        worker_bboxes: List[Tuple[float, float, float, float]],
        track_ids: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Tests whether any worker's feet fall inside any danger zone.
        
        :param worker_bboxes: List of (x1, y1, x2, y2) coordinates.
        :param track_ids: Optional list of ByteTrack worker IDs.
        :return: List of intrusion alert dicts.
        """
        alerts = []
        # Reset counters
        for zone in self.zones:
            zone["active_intruders"] = 0

        for idx, bbox in enumerate(worker_bboxes):
            foot_x, foot_y = self.get_ground_contact_point(bbox)
            worker_id = track_ids[idx] if track_ids and idx < len(track_ids) else idx

            for zone in self.zones:
                # cv2.pointPolygonTest: >0 inside, ==0 on edge, <0 outside
                is_inside = cv2.pointPolygonTest(zone["contour"], (foot_x, foot_y), measureDist=False)
                if is_inside >= 0:
                    zone["active_intruders"] += 1
                    alerts.append({
                        "event_type": "ZONE_INTRUSION",
                        "zone_name": zone["name"],
                        "severity": zone["severity"],
                        "worker_id": worker_id,
                        "foot_coords": (foot_x, foot_y),
                        "bbox": bbox
                    })
        return alerts

    def annotate(self, frame: np.ndarray, alerts: List[Dict[str, Any]]) -> np.ndarray:
        """
        Draws semi-transparent polygon zones onto the frame.
        Zones are green when empty, and red when an intrusion is detected.
        """
        overlay = frame.copy()
        intruded_zone_names = {a["zone_name"] for a in alerts}

        for zone in self.zones:
            name = zone["name"]
            contour = zone["contour"]
            is_intruded = name in intruded_zone_names

            # Red for intrusion, Green for safe
            color = (0, 0, 230) if is_intruded else (0, 200, 0)
            
            # Draw filled translucent polygon
            cv2.fillPoly(overlay, [contour], color)
            # Draw solid polygon border
            cv2.polylines(frame, [contour], isClosed=True, color=color, thickness=2)

            # Draw zone label
            pts = zone["polygon"]
            label_pos = (pts[0][0], max(pts[0][1] - 10, 20))
            label_text = f"🚨 {name} (INTRUSION!)" if is_intruded else f"🛡️ {name} (Safe)"
            cv2.putText(frame, label_text, label_pos, cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        # Blend overlay with 30% opacity
        cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)
        return frame
