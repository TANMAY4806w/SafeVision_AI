"""
Tests for SafeVision AI Dashboard — /dashboard route.
Verifies: HTTP status, content-type, required HTML landmarks,
Chart.js CDN inclusion, MJPEG stream embed, and API data integrity.
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestDashboardRoute:
    """Core route availability and content checks."""

    def test_dashboard_returns_200(self):
        """GET /dashboard must return HTTP 200."""
        resp = client.get("/dashboard")
        assert resp.status_code == 200

    def test_dashboard_content_type_html(self):
        """Response must be text/html."""
        resp = client.get("/dashboard")
        assert "text/html" in resp.headers["content-type"]

    def test_dashboard_contains_brand_name(self):
        """Page must contain product name."""
        resp = client.get("/dashboard")
        assert "SafeVision" in resp.text

    def test_dashboard_contains_live_badge(self):
        """Live indicator element must be present."""
        resp = client.get("/dashboard")
        assert "live-dot" in resp.text or "LIVE" in resp.text.upper()


class TestDashboardAssets:
    """Check required CDN references and assets."""

    def test_chartjs_cdn_included(self):
        """Chart.js CDN script tag must be present."""
        resp = client.get("/dashboard")
        assert "chart.js" in resp.text.lower() or "Chart.js" in resp.text

    def test_inter_font_included(self):
        """Google Fonts Inter must be linked."""
        resp = client.get("/dashboard")
        assert "fonts.googleapis.com" in resp.text

    def test_jetbrains_mono_font(self):
        """JetBrains Mono monospace font must be referenced."""
        resp = client.get("/dashboard")
        assert "JetBrains" in resp.text


class TestDashboardStructure:
    """Verify required HTML structural elements."""

    def test_mjpeg_stream_img_present(self):
        """Live stream <img> must point to /api/v1/video/stream."""
        resp = client.get("/dashboard")
        assert "/api/v1/video/stream" in resp.text

    def test_kpi_fps_element(self):
        """FPS KPI element must be present."""
        resp = client.get("/dashboard")
        assert "kpi-fps" in resp.text

    def test_kpi_workers_element(self):
        """Workers KPI element must be present."""
        resp = client.get("/dashboard")
        assert "kpi-workers" in resp.text

    def test_kpi_violations_element(self):
        """Violations KPI element must be present."""
        resp = client.get("/dashboard")
        assert "kpi-violations" in resp.text

    def test_kpi_compliance_element(self):
        """Compliance rate KPI element must be present."""
        resp = client.get("/dashboard")
        assert "kpi-compliance" in resp.text

    def test_alert_list_present(self):
        """Alert ticker list must be present."""
        resp = client.get("/dashboard")
        assert "alert-list" in resp.text

    def test_zone_list_present(self):
        """Geofence zone list must be present."""
        resp = client.get("/dashboard")
        assert "zone-list" in resp.text

    def test_fps_chart_canvas(self):
        """FPS Chart.js canvas element must be present."""
        resp = client.get("/dashboard")
        assert "fps-chart" in resp.text

    def test_github_link_in_footer(self):
        """Footer must link to GitHub repo."""
        resp = client.get("/dashboard")
        assert "TANMAY4806w/SafeVision_AI" in resp.text

    def test_api_docs_link_in_footer(self):
        """Footer must link to API docs."""
        resp = client.get("/dashboard")
        assert "/docs" in resp.text


class TestHealthEndpointForDashboard:
    """Test the /health endpoint that powers dashboard JS polling."""

    def test_health_200(self):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_has_status_field(self):
        resp = client.get("/health")
        data = resp.json()
        assert "status" in data
        assert data["status"] in ("HEALTHY", "DEGRADED")

    def test_health_has_hardware_section(self):
        resp = client.get("/health")
        data = resp.json()
        assert "hardware" in data
        assert "cuda_available" in data["hardware"]
        assert "device_name" in data["hardware"]

    def test_health_has_engine_section(self):
        resp = client.get("/health")
        data = resp.json()
        assert "engine" in data
        assert "active_zones" in data["engine"]

    def test_health_timestamp_present(self):
        resp = client.get("/health")
        data = resp.json()
        assert "timestamp" in data


class TestRootRedirect:
    """Root / must redirect to /docs (not break dashboard)."""

    def test_root_redirects(self):
        resp = client.get("/", follow_redirects=False)
        assert resp.status_code in (301, 302, 307, 308)
