"""
Automated Integration Tests for FastAPI Microservice & OSHA Incident Synthesizer.
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app

client = TestClient(app)


def test_health_check_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert "hardware" in data
    assert "cuda_available" in data["hardware"]


def test_osha_incident_report_generation():
    payload = {
        "camera_id": "CAM-02-PRESS-SHOP",
        "worker_id": 104,
        "violation_type": "NO_HELMET",
        "zone_name": "Robotic_Arm_Perimeter",
        "severity": "CRITICAL",
        "additional_notes": "Worker entered perimeter during robot welding cycle."
    }
    response = client.post("/api/v1/incident/generate-report", json=payload)
    assert response.status_code == 200
    report = response.json()
    assert "incident_id" in report
    assert "OSHA-INC-" in report["incident_id"]
    assert report["worker_id"] == 104
    assert "OSHA 29 CFR 1910.135" in report["osha_violation_code"]
    assert report["supervisor_signoff_required"] is True
