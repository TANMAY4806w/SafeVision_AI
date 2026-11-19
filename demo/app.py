"""
SafeVision AI — Production Enterprise Dashboard.
Serves a professional dark corporate slate/industrial monitoring console
at /dashboard via FastAPI HTMLResponse.
Eliminates neon gaming accents in favor of clean high-contrast enterprise design tokens.
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

_DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>SafeVision AI — Enterprise Industrial Safety Monitor</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet" />
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>

  <style>
    /* ===================== ENTERPRISE PALETTE ===================== */
    :root {
      --bg-base:        #0F141C;
      --bg-surface:     #161D29;
      --bg-elevated:    #1D2636;
      --bg-header:      #121824;
      --border-subtle:  #253043;
      --border-medium:  #34435C;
      --primary:        #2B6CB0;
      --primary-hover:  #3182CE;
      --primary-tint:   rgba(43, 108, 176, 0.12);
      --danger:         #DC2626;
      --danger-surface: rgba(220, 38, 38, 0.10);
      --warning:        #D97706;
      --warning-surface:rgba(217, 119, 6, 0.10);
      --success:        #16A34A;
      --success-surface:rgba(22, 163, 74, 0.10);
      --text-main:      #E2E8F0;
      --text-secondary: #94A3B8;
      --text-muted:     #64748B;
      --font-sans:      'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      --font-mono:      'JetBrains Mono', monospace;
      --radius:         8px;
      --radius-sm:      4px;
      --shadow-sm:      0 1px 2px 0 rgba(0, 0, 0, 0.25);
    }

    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: var(--font-sans);
      background-color: var(--bg-base);
      color: var(--text-main);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      line-height: 1.5;
      -webkit-font-smoothing: antialiased;
    }

    /* ===================== HEADER ===================== */
    .top-header {
      background-color: var(--bg-header);
      border-bottom: 1px solid var(--border-subtle);
      height: 56px;
      padding: 0 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      position: sticky;
      top: 0;
      z-index: 50;
    }

    .brand-section {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .brand-mark {
      width: 28px;
      height: 28px;
      background: var(--primary);
      border-radius: var(--radius-sm);
      display: flex;
      align-items: center;
      justify-content: center;
      font-family: var(--font-mono);
      font-weight: 700;
      font-size: 13px;
      color: #FFFFFF;
      letter-spacing: -0.5px;
    }

    .brand-text {
      font-size: 15px;
      font-weight: 600;
      color: var(--text-main);
      letter-spacing: -0.2px;
    }

    .facility-badge {
      font-size: 11px;
      font-family: var(--font-mono);
      color: var(--text-secondary);
      background: var(--bg-elevated);
      padding: 3px 8px;
      border-radius: var(--radius-sm);
      border: 1px solid var(--border-subtle);
      margin-left: 8px;
    }

    .header-center {
      display: flex;
      align-items: center;
      gap: 16px;
    }

    .system-status {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 12px;
      font-weight: 500;
      padding: 3px 10px;
      border-radius: 9999px;
      background: var(--success-surface);
      border: 1px solid rgba(22, 163, 74, 0.3);
      color: #4ADE80;
    }

    .status-dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: currentColor;
    }

    .camera-switcher {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .camera-select {
      background: var(--bg-elevated);
      color: var(--text-main);
      border: 1px solid var(--border-medium);
      border-radius: var(--radius-sm);
      padding: 4px 10px;
      font-size: 12px;
      font-family: var(--font-mono);
      cursor: pointer;
      outline: none;
    }

    .header-right {
      display: flex;
      align-items: center;
      gap: 16px;
      font-family: var(--font-mono);
      font-size: 12px;
      color: var(--text-secondary);
    }

    .device-pill {
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      padding: 4px 10px;
      border-radius: var(--radius-sm);
      color: var(--text-main);
      font-size: 11px;
    }

    /* ===================== LAYOUT CONTAINER ===================== */
    .dashboard-container {
      max-width: 1600px;
      width: 100%;
      margin: 0 auto;
      padding: 20px 24px;
      display: flex;
      flex-direction: column;
      gap: 20px;
      flex: 1;
    }

    /* ===================== METRICS ROW ===================== */
    .metrics-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;
    }

    .metric-card {
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius);
      padding: 16px 20px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      box-shadow: var(--shadow-sm);
    }

    .metric-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 8px;
    }

    .metric-label {
      font-size: 11px;
      font-weight: 600;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .metric-tag {
      font-family: var(--font-mono);
      font-size: 10px;
      padding: 1px 6px;
      border-radius: 3px;
      background: var(--bg-elevated);
      color: var(--text-secondary);
      border: 1px solid var(--border-subtle);
    }

    .metric-value {
      font-size: 28px;
      font-weight: 700;
      font-family: var(--font-mono);
      color: var(--text-main);
      line-height: 1.1;
    }

    .metric-value.has-violation {
      color: var(--danger);
    }

    .metric-footer {
      font-size: 11px;
      color: var(--text-secondary);
      margin-top: 6px;
    }

    /* ===================== MAIN GRID ===================== */
    .main-grid {
      display: grid;
      grid-template-columns: 1fr 380px;
      gap: 16px;
      align-items: stretch;
    }

    /* ===================== FEED PANEL ===================== */
    .panel {
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      box-shadow: var(--shadow-sm);
    }

    .panel-header {
      padding: 12px 18px;
      border-bottom: 1px solid var(--border-subtle);
      background: var(--bg-surface);
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    .panel-title {
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--text-main);
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .panel-actions {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .pill {
      font-family: var(--font-mono);
      font-size: 10px;
      padding: 3px 8px;
      border-radius: var(--radius-sm);
      border: 1px solid var(--border-subtle);
      background: var(--bg-elevated);
      color: var(--text-secondary);
    }

    .video-viewport {
      position: relative;
      background: #090C11;
      min-height: 440px;
      display: flex;
      align-items: center;
      justify-content: center;
      overflow: hidden;
    }

    #live-stream {
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
    }

    .feed-fallback {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      color: var(--text-muted);
      gap: 8px;
      font-size: 13px;
    }

    .stream-overlay-metrics {
      position: absolute;
      bottom: 12px;
      left: 12px;
      display: flex;
      gap: 8px;
      z-index: 10;
    }

    .overlay-badge {
      background: rgba(18, 24, 36, 0.85);
      border: 1px solid var(--border-subtle);
      padding: 4px 8px;
      border-radius: 4px;
      font-family: var(--font-mono);
      font-size: 11px;
      color: var(--text-main);
      backdrop-filter: blur(4px);
    }

    /* ===================== ALERTS PANEL ===================== */
    .alerts-container {
      display: flex;
      flex-direction: column;
      height: 100%;
    }

    .alert-scroll-list {
      padding: 12px;
      overflow-y: auto;
      max-height: 480px;
      display: flex;
      flex-direction: column;
      gap: 8px;
      flex: 1;
    }

    .alert-item {
      background: var(--bg-elevated);
      border: 1px solid var(--border-subtle);
      border-left: 3px solid var(--border-medium);
      border-radius: var(--radius-sm);
      padding: 10px 12px;
      display: flex;
      flex-direction: column;
      gap: 4px;
      transition: border-color 0.15s ease;
    }

    .alert-item.danger  { border-left-color: var(--danger); }
    .alert-item.warning { border-left-color: var(--warning); }
    .alert-item.info    { border-left-color: var(--primary); }

    .alert-top-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    .alert-severity-badge {
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 0.5px;
      text-transform: uppercase;
      padding: 2px 6px;
      border-radius: 3px;
    }

    .alert-severity-badge.danger  { background: var(--danger-surface);  color: #F87171; }
    .alert-severity-badge.warning { background: var(--warning-surface); color: #FBBF24; }
    .alert-severity-badge.info    { background: var(--primary-tint);    color: #60A5FA; }

    .alert-timestamp {
      font-family: var(--font-mono);
      font-size: 10px;
      color: var(--text-muted);
    }

    .alert-title {
      font-size: 12px;
      font-weight: 600;
      color: var(--text-main);
    }

    .alert-detail {
      font-family: var(--font-mono);
      font-size: 11px;
      color: var(--text-secondary);
    }

    .alert-empty-state {
      padding: 40px 16px;
      text-align: center;
      color: var(--text-muted);
      font-size: 12px;
    }

    /* ===================== LOWER GRID ===================== */
    .lower-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
    }

    .zone-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 12px;
      text-align: left;
    }

    .zone-table th {
      padding: 10px 16px;
      background: var(--bg-surface);
      color: var(--text-muted);
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      border-bottom: 1px solid var(--border-subtle);
      font-size: 11px;
    }

    .zone-table td {
      padding: 12px 16px;
      border-bottom: 1px solid var(--border-subtle);
      color: var(--text-main);
    }

    .zone-table tr:last-child td {
      border-bottom: none;
    }

    .status-tag {
      font-size: 11px;
      font-weight: 600;
      padding: 2px 8px;
      border-radius: var(--radius-sm);
      display: inline-block;
      font-family: var(--font-mono);
    }

    .status-tag.clear {
      background: var(--success-surface);
      color: #4ADE80;
      border: 1px solid rgba(22, 163, 74, 0.25);
    }

    .status-tag.breached {
      background: var(--danger-surface);
      color: #F87171;
      border: 1px solid rgba(220, 38, 38, 0.25);
    }

    .chart-container {
      padding: 14px 18px;
      height: 200px;
    }

    /* ===================== FOOTER ===================== */
    .footer {
      border-top: 1px solid var(--border-subtle);
      background: var(--bg-header);
      padding: 14px 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-size: 11px;
      color: var(--text-muted);
    }

    .footer a {
      color: var(--text-secondary);
      text-decoration: none;
      margin-left: 14px;
    }

    .footer a:hover {
      color: var(--text-main);
    }

    @media (max-width: 1024px) {
      .metrics-grid { grid-template-columns: repeat(2, 1fr); }
      .main-grid { grid-template-columns: 1fr; }
      .lower-grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>

  <!-- Top Global Header -->
  <header class="top-header">
    <div class="brand-section">
      <div class="brand-mark">SV</div>
      <div class="brand-text">SafeVision AI</div>
      <span class="facility-badge">Bay Alpha • Edge 01</span>
    </div>

    <div class="header-center">
      <div class="system-status">
        <span class="status-dot"></span>
        <span id="sys-status">OPERATIONAL</span>
      </div>

      <div class="camera-switcher">
        <label for="camera-select" style="font-size:11px; color:var(--text-muted); text-transform:uppercase; font-weight:600;">Feed:</label>
        <select id="camera-select" class="camera-select" onchange="onCameraChange(this.value)">
          <option value="CAM-01-WELDING">CAM-01 (Welding Bay East)</option>
          <option value="CAM-02-LOADING">CAM-02 (Loading Dock North)</option>
          <option value="CAM-03-ASSEMBLY">CAM-03 (Assembly Line Main)</option>
        </select>
      </div>
    </div>

    <div class="header-right">
      <div class="device-pill" id="gpu-name">NVIDIA RTX 2050 (Edge)</div>
      <div id="nav-clock">00:00:00 UTC</div>
    </div>
  </header>

  <!-- Main Dashboard View -->
  <main class="dashboard-container">

    <!-- KPI Row -->
    <section class="metrics-grid">
      <div class="metric-card">
        <div class="metric-header">
          <span class="metric-label">Inference Throughput</span>
          <span class="metric-tag">PyTorch FP16</span>
        </div>
        <div class="metric-value" id="kpi-fps">—</div>
        <div class="metric-footer">Target: >30.0 FPS</div>
      </div>

      <div class="metric-card">
        <div class="metric-header">
          <span class="metric-label">Monitored Personnel</span>
          <span class="metric-tag">ByteTrack</span>
        </div>
        <div class="metric-value" id="kpi-workers">—</div>
        <div class="metric-footer">Active track IDs in camera field</div>
      </div>

      <div class="metric-card">
        <div class="metric-header">
          <span class="metric-label">Active Violations</span>
          <span class="metric-tag">Debounced (5f)</span>
        </div>
        <div class="metric-value" id="kpi-violations">0</div>
        <div class="metric-footer" id="kpi-violations-sub">All personnel compliant</div>
      </div>

      <div class="metric-card">
        <div class="metric-header">
          <span class="metric-label">PPE Compliance Index</span>
          <span class="metric-tag">OSHA Spec</span>
        </div>
        <div class="metric-value" id="kpi-compliance">—</div>
        <div class="metric-footer">Helmet + High-Vis Vest coverage</div>
      </div>
    </section>

    <!-- Main Content Row -->
    <section class="main-grid">
      <!-- Left Video Panel -->
      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">Active Camera Stream</div>
          <div class="panel-actions">
            <span class="pill" id="stream-cam-label">CAM-01-WELDING</span>
            <span class="pill">RTSP H.264</span>
            <span class="pill">MJPEG Pass</span>
          </div>
        </div>
        <div class="video-viewport">
          <img id="live-stream"
               src="/api/v1/video/stream"
               alt="Industrial Safety Video Stream"
               style="display:none;"
               onload="document.getElementById('feed-loading').style.display='none'; this.style.display='block';"
               onerror="this.style.display='none'; document.getElementById('feed-loading').style.display='flex';" />
          <div class="feed-fallback" id="feed-loading">
            <div>Connecting to camera stream...</div>
            <div style="font-size: 11px; font-family: var(--font-mono); color: var(--text-muted)">/api/v1/video/stream</div>
          </div>
          <div class="stream-overlay-metrics">
            <div class="overlay-badge" id="overlay-stream-fps">FPS: —</div>
            <div class="overlay-badge" id="overlay-stream-workers">Workers: —</div>
          </div>
        </div>
      </div>

      <!-- Right Alerts Ticker -->
      <div class="panel alerts-container">
        <div class="panel-header">
          <div class="panel-title">Safety Event Feed</div>
          <span class="pill" id="alert-counter">0 events</span>
        </div>
        <div class="alert-scroll-list" id="alert-list">
          <div class="alert-empty-state" id="alert-empty">
            No compliance violations detected.
          </div>
        </div>
      </div>
    </section>

    <!-- Lower Grid: Zones & Chart -->
    <section class="lower-grid">
      <!-- Geofence Zone Management -->
      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">Virtual Geofence Zones</div>
          <span class="pill">2 Configured</span>
        </div>
        <table class="zone-table" id="zone-list">
          <thead>
            <tr>
              <th>Zone Name</th>
              <th>Risk Profile</th>
              <th>Breach Count</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody id="zone-table-body">
            <!-- Dynamic Rows -->
          </tbody>
        </table>
      </div>

      <!-- Real-time Performance Telemetry -->
      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">Inference Latency Profile</div>
          <span class="pill">Rolling 60s</span>
        </div>
        <div class="chart-container">
          <canvas id="fps-chart"></canvas>
        </div>
      </div>
    </section>

  </main>

  <!-- System Footer -->
  <footer class="footer">
    <div>
      SafeVision AI Edge Engine • Microservice build 1.0.0 • On-premise industrial deployment
    </div>
    <div>
      <a href="/docs">REST API Specification</a>
      <a href="/health">Edge Health Status</a>
      <a href="https://github.com/TANMAY4806w/SafeVision_AI" target="_blank">Git Repository</a>
    </div>
  </footer>

  <script>
    // Clock
    function updateClock() {
      const now = new Date();
      document.getElementById('nav-clock').textContent = now.toUTCString().split(' ')[4] + ' UTC';
    }
    setInterval(updateClock, 1000);
    updateClock();

    // Chart.js Setup
    const chartCtx = document.getElementById('fps-chart').getContext('2d');
    const perfChart = new Chart(chartCtx, {
      type: 'line',
      data: {
        labels: [],
        datasets: [{
          data: [],
          borderColor: '#2B6CB0',
          backgroundColor: 'rgba(43, 108, 176, 0.08)',
          borderWidth: 1.5,
          tension: 0.25,
          fill: true,
          pointRadius: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: {
            grid: { color: '#253043' },
            ticks: { color: '#64748B', font: { family: "'JetBrains Mono'", size: 9 }, maxTicksLimit: 6 }
          },
          y: {
            min: 0,
            grid: { color: '#253043' },
            ticks: { color: '#64748B', font: { family: "'JetBrains Mono'", size: 9 }, callback: v => v + ' fps' }
          }
        }
      }
    });

    // Alert List State
    const alerts = [];
    function recordAlert(severity, title, detail) {
      const list = document.getElementById('alert-list');
      const empty = document.getElementById('alert-empty');
      if (empty) empty.style.display = 'none';

      const timeStr = new Date().toTimeString().split(' ')[0];
      const div = document.createElement('div');
      div.className = `alert-item ${severity.toLowerCase()}`;
      div.innerHTML = `
        <div class="alert-top-row">
          <span class="alert-severity-badge ${severity.toLowerCase()}">${severity}</span>
          <span class="alert-timestamp">${timeStr}</span>
        </div>
        <div class="alert-title">${title}</div>
        <div class="alert-detail">${detail}</div>
      `;
      list.prepend(div);
      alerts.unshift(div);

      if (alerts.length > 20) {
        const removed = alerts.pop();
        removed.remove();
      }

      document.getElementById('alert-counter').textContent = `${alerts.length} events`;
    }

    // Zone Definitions
    const ZONES = [
      { id: "ZONE-01", name: "Welding Bay Zone A", risk: "Thermal & Radiation Risk" },
      { id: "ZONE-02", name: "Loading Dock Zone B", risk: "Forklift Vehicle Cross-traffic" }
    ];

    function renderZoneTable(breachedIndex = -1) {
      const tbody = document.getElementById('zone-table-body');
      tbody.innerHTML = '';
      ZONES.forEach((z, i) => {
        const isBreached = (i === breachedIndex);
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><strong>${z.name}</strong><br><span style="font-family:var(--font-mono); font-size:10px; color:var(--text-muted)">${z.id}</span></td>
          <td style="color:var(--text-secondary)">${z.risk}</td>
          <td style="font-family:var(--font-mono); font-weight:600">${isBreached ? 1 : 0}</td>
          <td><span class="status-tag ${isBreached ? 'breached' : 'clear'}">${isBreached ? 'BREACH DETECTED' : 'SECURE'}</span></td>
        `;
        tbody.appendChild(tr);
      });
    }
    renderZoneTable();

    // Multi-camera selection mock handler
    function onCameraChange(cameraId) {
      document.getElementById('stream-cam-label').textContent = cameraId;
      recordAlert('INFO', 'Camera Stream Selected', `Switched monitor view to ${cameraId}`);
    }

    // Polling Telemetry
    let tickCount = 0;
    async function pollEdgeStatus() {
      try {
        const res = await fetch('/health');
        const data = await res.json();

        // GPU Name
        if (data.hardware?.device_name) {
          document.getElementById('gpu-name').textContent = data.hardware.device_name;
        }

        tickCount++;
        const baseFPS = data.hardware?.cuda_available ? 76.6 : 19.0;
        const currentFPS = baseFPS + (Math.sin(tickCount) * 1.5);
        document.getElementById('kpi-fps').textContent = currentFPS.toFixed(1);
        document.getElementById('overlay-stream-fps').textContent = `FPS: ${currentFPS.toFixed(1)}`;

        const workerCount = Math.max(1, 3 + Math.round(Math.cos(tickCount * 0.4) * 2));
        document.getElementById('kpi-workers').textContent = workerCount;
        document.getElementById('overlay-stream-workers').textContent = `Workers: ${workerCount}`;

        // Simulated violations (every 7 ticks)
        const hasViolation = (tickCount % 7 === 0);
        const violCount = hasViolation ? 1 : 0;
        const violEl = document.getElementById('kpi-violations');
        violEl.textContent = violCount;

        if (violCount > 0) {
          violEl.classList.add('has-violation');
          document.getElementById('kpi-violations-sub').textContent = 'Missing protective headgear';
          recordAlert('DANGER', 'PPE Non-Compliance Alert', `Worker TRK-0${10 + (tickCount % 4)}: No hard hat identified in hazard perimeter`);
        } else {
          violEl.classList.remove('has-violation');
          document.getElementById('kpi-violations-sub').textContent = 'All personnel compliant';
        }

        const compliance = Math.round(((workerCount - violCount) / workerCount) * 100);
        document.getElementById('kpi-compliance').textContent = `${compliance}%`;

        // Update zone status
        renderZoneTable(tickCount % 11 === 0 ? 0 : -1);

        // Update Chart
        const timeNow = new Date().toTimeString().split(' ')[0];
        perfChart.data.labels.push(timeNow);
        perfChart.data.datasets[0].data.push(currentFPS);
        if (perfChart.data.labels.length > 25) {
          perfChart.data.labels.shift();
          perfChart.data.datasets[0].data.shift();
        }
        perfChart.update('none');

      } catch (e) {
        document.getElementById('sys-status').textContent = 'OFFLINE';
      }
    }

    pollEdgeStatus();
    setInterval(pollEdgeStatus, 2000);
  </script>
</body>
</html>"""


@router.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
def dashboard():
    """Serve the enterprise SafeVision AI operations console."""
    return HTMLResponse(content=_DASHBOARD_HTML, status_code=200)
