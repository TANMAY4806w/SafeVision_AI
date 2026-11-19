"""
GenAI OSHA Incident Report Synthesizer.
Translates raw detection events and danger zone intrusions into formal, publication-ready
Industrial Safety Compliance Violation Cards.
"""

import uuid
import datetime
import logging
from typing import Dict, Any, Optional
from .schemas import IncidentReportRequest, IncidentReportResponse

logger = logging.getLogger("SafeVision.Reporter")

# Regulatory OSHA code mapping for industrial safety violations
OSHA_CODE_MAPPING = {
    "NO_HELMET": {
        "code": "OSHA 29 CFR 1910.135",
        "title": "Head Protection Standards",
        "hazard": "Risk of severe traumatic brain injury, skull fractures, and electrical shock from falling or overhead hazards.",
        "action": "Immediate suspension of worker from active floor. Inspect hard hat inventory and issue mandatory ANSI Z89.1 certified headgear before re-entry."
    },
    "NO_VEST": {
        "code": "OSHA 29 CFR 1926.201",
        "title": "High-Visibility Signaling Apparel",
        "hazard": "Worker camouflage in blind spots; critical risk of vehicular collision with industrial forklifts and moving machinery.",
        "action": "Issue ANSI/ISEA 107 Class 2 high-visibility fluorescent vest immediately. Conduct tool-box safety briefing on line-of-sight safety."
    },
    "ZONE_INTRUSION": {
        "code": "OSHA 29 CFR 1910.212",
        "title": "General Machine Guarding & Isolation",
        "hazard": "Uncontrolled entry into active robotic arm / crane drop zone perimeter. Imminent risk of crush injuries or amputation.",
        "action": "Trigger emergency stop (E-STOP) protocol. Evacuate zone immediately and verify interlock sensor integrity before resetting."
    }
}


class IncidentReporter:
    """
    Synthesizes real-time edge violation events into formal OSHA Incident Reports.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def generate_report(self, req: IncidentReportRequest) -> IncidentReportResponse:
        """Generates a formal OSHA Compliance Safety Violation Notice."""
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        incident_id = f"OSHA-INC-{uuid.uuid4().hex[:8].upper()}"

        v_type = req.violation_type.upper()
        meta = OSHA_CODE_MAPPING.get(v_type, {
            "code": "OSHA 29 CFR 1910.132",
            "title": "General Personal Protective Equipment Requirements",
            "hazard": "Unspecified industrial safety breach creating imminent workplace hazard.",
            "action": "Conduct on-site safety intervention and document root cause analysis."
        })

        summary = (
            f"On-site Vision AI automated surveillance detected Worker #{req.worker_id} committing a "
            f"{req.severity} severity safety violation ({v_type}) at camera location [{req.camera_id}]."
        )
        if req.zone_name:
            summary += f" The worker was concurrently identified within the restricted boundary '{req.zone_name}'."

        if req.additional_notes:
            summary += f" Field Note: {req.additional_notes}"

        logger.info(f"Generated formal incident card [{incident_id}] for Worker #{req.worker_id}")

        return IncidentReportResponse(
            incident_id=incident_id,
            generated_at=now_iso,
            camera_id=req.camera_id,
            worker_id=req.worker_id,
            severity=req.severity,
            osha_violation_code=meta["code"],
            summary=summary,
            immediate_hazard=meta["hazard"],
            mandated_corrective_action=meta["action"],
            supervisor_signoff_required=True
        )
