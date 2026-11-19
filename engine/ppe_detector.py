"""
YOLOv8 PPE Detection & Spatial Association Engine with ByteTrack and Temporal Debouncing.
Tracks workers, evaluates head/torso regions for safety gear, and eliminates false alarm flickering.
"""

import logging
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import cv2
from ultralytics import YOLO

logger = logging.getLogger("SafeVision.PPEDetector")


class PPEDetector:
    """
    Production-grade PPE detector and worker tracker using Ultralytics YOLO and ByteTrack.
    """

    # Default mapping for standard PPE models or COCO fallback
    DEFAULT_CLASS_MAPPING = {
        0: "person",
        1: "helmet",
        2: "vest",
        3: "no_helmet",
        4: "no_vest"
    }

    def __init__(
        self,
        model_path: str = "yolov8n.pt",
        confidence: float = 0.45,
        iou_threshold: float = 0.45,
        device: Optional[str] = None,
        debounce_frames: int = 5
    ):
        """
        :param model_path: Path to PyTorch model (.pt) or ONNX model (.onnx). Defaults to yolov8n.pt.
        :param confidence: Detection confidence threshold.
        :param iou_threshold: NMS IoU threshold.
        :param device: 'cuda', 'cpu', or None (auto-select).
        :param debounce_frames: Number of consecutive violation frames before raising alert.
        """
        self.model_path = model_path
        self.confidence = confidence
        self.iou_threshold = iou_threshold
        self.debounce_frames = debounce_frames

        logger.info(f"Loading YOLO model from: {model_path}...")
        self.model = YOLO(model_path)
        self.device = device

        # Temporal debouncing state: track_id -> {'no_helmet': int, 'no_vest': int}
        self.tracker_state: Dict[int, Dict[str, int]] = {}

    def detect_and_track(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Runs ByteTrack tracking on the frame and associates PPE gear to workers.
        
        :param frame: Raw BGR video frame from OpenCV.
        :return: Dict containing workers, detections, alerts, and annotated frame.
        """
        # Run tracking using ByteTrack
        results = self.model.track(
            source=frame,
            persist=True,
            conf=self.confidence,
            iou=self.iou_threshold,
            device=self.device,
            verbose=False
        )

        boxes = results[0].boxes
        if boxes is None or len(boxes) == 0:
            return {
                "workers": [],
                "alerts": [],
                "annotated_frame": frame
            }

        # Extract coordinates, classes, confidences, and track IDs
        xyxy = boxes.xyxy.cpu().numpy()
        cls_ids = boxes.cls.cpu().numpy().astype(int)
        confs = boxes.conf.cpu().numpy()
        track_ids = (
            boxes.id.cpu().numpy().astype(int)
            if boxes.id is not None
            else list(range(len(xyxy)))
        )

        names = self.model.names if hasattr(self.model, "names") else self.DEFAULT_CLASS_MAPPING

        # Separate workers (person) from gear items
        workers = []
        gear_items = []

        for i, (bbox, cls_id, conf, tid) in enumerate(zip(xyxy, cls_ids, confs, track_ids)):
            class_name = names.get(cls_id, str(cls_id)).lower()
            item = {
                "id": int(tid),
                "bbox": [float(c) for c in bbox],
                "confidence": float(conf),
                "class_id": int(cls_id),
                "class_name": class_name
            }

            if "person" in class_name:
                workers.append(item)
            else:
                gear_items.append(item)

        # In fallback mode (when using standard COCO model where only 'person' is detected),
        # we treat person detections as workers and evaluate spatial checks.
        alerts = []
        for worker in workers:
            w_id = worker["id"]
            w_box = worker["bbox"]
            has_helmet, has_vest = self._check_worker_ppe(w_box, gear_items)

            # Update debouncing state
            if w_id not in self.tracker_state:
                self.tracker_state[w_id] = {"no_helmet": 0, "no_vest": 0}

            # Update counters
            if not has_helmet:
                self.tracker_state[w_id]["no_helmet"] += 1
            else:
                self.tracker_state[w_id]["no_helmet"] = 0

            if not has_vest:
                self.tracker_state[w_id]["no_vest"] += 1
            else:
                self.tracker_state[w_id]["no_vest"] = 0

            # Check if debounced threshold reached
            worker_violations = []
            if self.tracker_state[w_id]["no_helmet"] >= self.debounce_frames:
                worker_violations.append("NO_HELMET")
                alerts.append({
                    "event_type": "PPE_VIOLATION",
                    "violation": "NO_HELMET",
                    "worker_id": w_id,
                    "bbox": w_box,
                    "severity": "HIGH"
                })

            if self.tracker_state[w_id]["no_vest"] >= self.debounce_frames:
                worker_violations.append("NO_VEST")
                alerts.append({
                    "event_type": "PPE_VIOLATION",
                    "violation": "NO_VEST",
                    "worker_id": w_id,
                    "bbox": w_box,
                    "severity": "HIGH"
                })

            worker["is_compliant"] = len(worker_violations) == 0
            worker["violations"] = worker_violations

        annotated_frame = self.annotate_frame(frame, workers, gear_items)

        return {
            "workers": workers,
            "alerts": alerts,
            "annotated_frame": annotated_frame
        }

    def _check_worker_ppe(
        self,
        worker_bbox: List[float],
        gear_items: List[Dict[str, Any]]
    ) -> Tuple[bool, bool]:
        """
        Geometrically pairs detected gear items to the worker's head and torso zones.
        """
        if not gear_items:
            # If no gear classes in model or none detected
            return True, True

        x1, y1, x2, y2 = worker_bbox
        w_height = y2 - y1

        # Head zone: top 25%
        head_box = (x1, y1, x2, y1 + 0.25 * w_height)
        # Torso zone: 20% to 70%
        torso_box = (x1, y1 + 0.20 * w_height, x2, y1 + 0.70 * w_height)

        has_helmet = False
        has_vest = False

        for gear in gear_items:
            g_box = gear["bbox"]
            g_class = gear["class_name"]

            # Calculate center point of gear
            gx_center = (g_box[0] + g_box[2]) / 2
            gy_center = (g_box[1] + g_box[3]) / 2

            # Check helmet
            if "helmet" in g_class or "hard_hat" in g_class:
                if (head_box[0] <= gx_center <= head_box[2]) and (head_box[1] <= gy_center <= head_box[3]):
                    has_helmet = True

            # Check vest
            if "vest" in g_class:
                if (torso_box[0] <= gx_center <= torso_box[2]) and (torso_box[1] <= gy_center <= torso_box[3]):
                    has_vest = True

        return has_helmet, has_vest

    def annotate_frame(
        self,
        frame: np.ndarray,
        workers: List[Dict[str, Any]],
        gear_items: List[Dict[str, Any]]
    ) -> np.ndarray:
        """
        Renders worker bounding boxes, ID badges, and compliance status tags.
        """
        annotated = frame.copy()

        for worker in workers:
            bbox = worker["bbox"]
            x1, y1, x2, y2 = [int(c) for c in bbox]
            is_compliant = worker.get("is_compliant", True)
            w_id = worker["id"]
            violations = worker.get("violations", [])

            # Green for compliant, Red for violation
            color = (0, 220, 0) if is_compliant else (0, 0, 240)
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)

            # Draw top badge with Worker ID
            badge_text = f"Worker #{w_id}"
            if not is_compliant:
                badge_text += f" | {' & '.join(violations)}"

            (t_w, t_h), _ = cv2.getTextSize(badge_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(annotated, (x1, max(y1 - 22, 0)), (x1 + t_w + 10, max(y1, 22)), color, -1)
            cv2.putText(
                annotated,
                badge_text,
                (x1 + 5, max(y1 - 6, 16)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1,
                cv2.LINE_AA
            )

        return annotated
