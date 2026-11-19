"""
FastAPI Routes for SafeVision AI Microservice.
Exposes Health Check, Real-Time MJPEG Streaming, Single-Frame Detection, and GenAI OSHA Incident Reports.
"""

import os
import cv2
import datetime
import logging
from typing import Generator, Optional
import numpy as np
import torch
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import StreamingResponse, JSONResponse

from engine.video_stream import ThreadedRTSPStream
from engine.ppe_detector import PPEDetector
from engine.zone_monitor import ZoneMonitor
from .schemas import DetectionResponse, DetectionItem, ViolationAlert, IncidentReportRequest, IncidentReportResponse
from .reporter import IncidentReporter

logger = logging.getLogger("SafeVision.API")

router = APIRouter()

# Global engine instances (Initialized at startup)
_stream: Optional[ThreadedRTSPStream] = None
_detector: Optional[PPEDetector] = None
_zone_monitor: Optional[ZoneMonitor] = None
_reporter: IncidentReporter = IncidentReporter()


def get_detector() -> PPEDetector:
    global _detector
    if _detector is None:
        model_path = os.getenv("MODEL_PATH", "models/best.pt")
        if not os.path.exists(model_path):
            model_path = "yolov8n.pt"
        logger.info(f"Initializing PPEDetector with: {model_path}")
        _detector = PPEDetector(model_path=model_path)
    return _detector


def get_zone_monitor() -> ZoneMonitor:
    global _zone_monitor
    if _zone_monitor is None:
        zones_file = os.path.join(os.path.dirname(__file__), "..", "data", "zones.json")
        _zone_monitor = ZoneMonitor(zones_file)
    return _zone_monitor


def get_stream() -> ThreadedRTSPStream:
    global _stream
    if _stream is None:
        video_src = os.path.join(os.path.dirname(__file__), "..", "data", "sample_feed.mp4")
        if not os.path.exists(video_src):
            video_src = 0  # Fallback to webcam
        logger.info(f"Initializing ThreadedRTSPStream with source: {video_src}")
        _stream = ThreadedRTSPStream(src=video_src).start()
    return _stream


@router.get("/health", summary="System & GPU Health Status")
def health_check():
    """Returns edge system health, GPU acceleration status, and active engine components."""
    cuda_available = torch.cuda.is_available()
    device_name = torch.cuda.get_device_name(0) if cuda_available else "CPU (Host)"
    vram_mb = torch.cuda.get_device_properties(0).total_memory / (1024 * 1024) if cuda_available else 0

    return {
        "status": "HEALTHY",
        "service": "SafeVision AI Production Microservice",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "hardware": {
            "cuda_available": cuda_available,
            "device_name": device_name,
            "total_vram_mb": round(vram_mb, 1),
        },
        "engine": {
            "model_path": os.getenv("MODEL_PATH", "models/best.pt"),
            "rtsp_streaming": _stream is not None and not _stream.stopped.is_set(),
            "active_zones": len(get_zone_monitor().zones)
        }
    }


@router.post("/api/v1/video/detect-frame", response_model=DetectionResponse, summary="Analyze Single Image Frame")
async def detect_frame(file: UploadFile = File(...)):
    """Ingests a single uploaded frame, runs PPE detection & polygon intrusion check, and returns structured alerts."""
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if frame is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image payload.")

    detector = get_detector()
    zone_monitor = get_zone_monitor()

    # 1. PPE Detection & Worker Tracking
    results = detector.detect_and_track(frame)
    workers = results["workers"]
    ppe_alerts = results["alerts"]

    # 2. Polygon Danger Zone Check
    worker_bboxes = [w["bbox"] for w in workers]
    worker_ids = [w["id"] for w in workers]
    zone_alerts = zone_monitor.check_intrusion(worker_bboxes, track_ids=worker_ids)

    # 3. Aggregate all alerts
    combined_alerts = []
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    for pa in ppe_alerts:
        combined_alerts.append(ViolationAlert(
            event_type=pa["event_type"],
            severity=pa["severity"],
            worker_id=pa["worker_id"],
            violation=pa["violation"],
            timestamp=now_iso
        ))

    for za in zone_alerts:
        combined_alerts.append(ViolationAlert(
            event_type=za["event_type"],
            severity=za["severity"],
            worker_id=za["worker_id"],
            zone_name=za["zone_name"],
            timestamp=now_iso
        ))

    detection_items = [
        DetectionItem(
            id=w["id"],
            class_id=w["class_id"],
            class_name=w["class_name"],
            confidence=w["confidence"],
            bbox=tuple(w["bbox"]),
            is_compliant=w.get("is_compliant", True),
            violations=w.get("violations", [])
        )
        for w in workers
    ]

    compliant_count = sum(1 for w in workers if w.get("is_compliant", True))

    return DetectionResponse(
        camera_id="CAM-01-EDGE",
        timestamp=now_iso,
        total_workers=len(workers),
        compliant_workers=compliant_count,
        active_violations=len(combined_alerts),
        detections=detection_items,
        alerts=combined_alerts
    )


def _generate_mjpeg_stream() -> Generator[bytes, None, None]:
    """Continuous generator yielding MJPEG multipart frames to web browsers."""
    stream = get_stream()
    detector = get_detector()
    zone_monitor = get_zone_monitor()

    while not stream.stopped.is_set():
        success, frame = stream.read(timeout=1.0)
        if not success or frame is None:
            continue

        # Run AI detection & tracking
        results = detector.detect_and_track(frame)
        workers = results["workers"]
        annotated = results["annotated_frame"]

        # Run polygon danger zone evaluation
        worker_bboxes = [w["bbox"] for w in workers]
        worker_ids = [w["id"] for w in workers]
        zone_alerts = zone_monitor.check_intrusion(worker_bboxes, track_ids=worker_ids)

        # Draw danger zone overlays
        annotated = zone_monitor.annotate(annotated, zone_alerts)

        # Draw live FPS overlay
        fps_text = f"FPS: {stream.fps:.1f} | Workers: {len(workers)} | Alerts: {len(zone_alerts) + len(results['alerts'])}"
        cv2.putText(annotated, fps_text, (20, annotated.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        # Encode frame as JPEG
        ret, buffer = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if not ret:
            continue

        frame_bytes = buffer.tobytes()
        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")


@router.get("/api/v1/video/stream", summary="Live Annotated MJPEG Video Stream")
def live_video_stream():
    """Streams real-time annotated video frames with bounding boxes, worker IDs, and geofence overlays."""
    return StreamingResponse(
        _generate_mjpeg_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@router.post("/api/v1/incident/generate-report", response_model=IncidentReportResponse, summary="Synthesize OSHA Incident Card")
def generate_incident_report(request: IncidentReportRequest):
    """Translates a raw safety detection event into a formal OSHA compliance incident report card."""
    return _reporter.generate_report(request)
