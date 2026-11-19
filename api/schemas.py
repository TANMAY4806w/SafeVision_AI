"""
Pydantic v2 Data Schemas for SafeVision AI REST Microservice.
Defines strict validation for detection payloads, violation alerts, and OSHA compliance reports.
"""

from typing import List, Optional, Tuple, Dict, Any
from pydantic import BaseModel, Field


class DetectionItem(BaseModel):
    """Represents a single detected object or worker."""
    id: int = Field(..., description="Unique track ID assigned by ByteTrack")
    class_id: int = Field(..., description="YOLO class index")
    class_name: str = Field(..., description="Human-readable class label (e.g. 'person', 'helmet')")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence score")
    bbox: Tuple[float, float, float, float] = Field(..., description="Bounding box [x1, y1, x2, y2]")
    is_compliant: Optional[bool] = Field(None, description="True if wearing all required PPE")
    violations: List[str] = Field(default_factory=list, description="List of detected violations (e.g. ['NO_HELMET'])")


class ViolationAlert(BaseModel):
    """Represents a safety breach event."""
    event_type: str = Field(..., description="Type of violation: 'PPE_VIOLATION' or 'ZONE_INTRUSION'")
    severity: str = Field("CRITICAL", description="Severity level: 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'")
    worker_id: int = Field(..., description="Associated worker track ID")
    zone_name: Optional[str] = Field(None, description="Name of danger zone if intrusion event")
    violation: Optional[str] = Field(None, description="Specific gear violation (e.g. 'NO_HELMET')")
    timestamp: str = Field(..., description="ISO 8601 timestamp of occurrence")


class DetectionResponse(BaseModel):
    """Response returned for single-frame detection requests."""
    camera_id: str
    timestamp: str
    total_workers: int
    compliant_workers: int
    active_violations: int
    detections: List[DetectionItem]
    alerts: List[ViolationAlert]


class IncidentReportRequest(BaseModel):
    """Request payload to trigger GenAI OSHA incident report generation."""
    camera_id: str = "CAM-01-ROBOTIC-BAY"
    timestamp: Optional[str] = None
    worker_id: int
    violation_type: str = "NO_HELMET"
    zone_name: Optional[str] = "Robotic_Arm_Perimeter"
    severity: str = "HIGH"
    additional_notes: Optional[str] = None


class IncidentReportResponse(BaseModel):
    """Structured OSHA Compliance Safety Incident Card."""
    incident_id: str
    generated_at: str
    camera_id: str
    worker_id: int
    severity: str
    osha_violation_code: str
    summary: str
    immediate_hazard: str
    mandated_corrective_action: str
    supervisor_signoff_required: bool = True
