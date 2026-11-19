# SafeVision AI — Enterprise Edge Deployment & Multi-Camera Setup Guide

This document specifies the exact industrial architecture, hardware topologies, camera integration procedures, and deployment models used by Computer Vision and Edge AI teams (such as Orbit Techsol / Augmented Transformations / VEDA implementations).

---

## 1. Industry Standard Deployment Architecture

In edge computer vision, deploying everything to the public cloud is usually non-viable due to RTSP bandwidth consumption (e.g., 8–16 cameras pushing 4–8 Mbps each = ~64 Mbps continuous upstream load) and security constraints (factory footage cannot leave local networks).

```mermaid
flowchart TD
    subgraph OnPremiseEdge["🏭 Client On-Premise Facility (Edge Local Network)"]
        direction TB
        subgraph IP_Cameras["📹 Factory Floor CCTV / IP Cameras"]
            CAM1["Camera 01: Welding Bay<br/>(RTSP H.264)"]
            CAM2["Camera 02: Loading Dock<br/>(RTSP H.264)"]
            CAM3["Camera 03: Assembly Line<br/>(RTSP H.264)"]
            CAM4["Camera 04: Chemical Storage<br/>(RTSP H.264)"]
        end

        subgraph LocalSwitch["🔀 Managed PoE Network Switch (VLAN 20)"]
            SWITCH["PoE+ L2/L3 Industrial Switch<br/>(1 Gbps Isolated Network)"]
        end

        subgraph EdgeServer["🖥️ Edge AI Appliance / On-Prem Server"]
            NVR["NVR / RTSP Gateway / SafeVision RTSP Ingestion"]
            GPU["NVIDIA GPU (RTX 4000 / Jetson AGX / T4 Edge)"]
            DOCKER["Docker Engine + NVIDIA Container Toolkit"]
            BACKEND["SafeVision AI Microservice (Port 8000)"]
        end

        CAM1 --> SWITCH
        CAM2 --> SWITCH
        CAM3 --> SWITCH
        CAM4 --> SWITCH
        SWITCH --> NVR
        NVR --> BACKEND
        GPU --> BACKEND
    end

    subgraph MonitoringClients["💻 Operations & Control Room"]
        LOCAL_DASH["Local Control Room Monitor<br/>(http://192.168.1.50:8000/dashboard)"]
        CLOUD_WEB["Optional Central Web App<br/>(Vercel / Cloud Portal via Reverse Proxy)"]
    end

    BACKEND --> LOCAL_DASH
    BACKEND -. Secure VPN / Wireguard .-> CLOUD_WEB
```

---

## 2. Backend vs Frontend Deployment Strategy

### A. The Backend (Inference Engine) — Must Run at the Edge
* **Where:** On-site Edge Server (e.g., Dell PowerEdge, Advantech Industrial PC, or NVIDIA Jetson AGX) physically connected to the same Local Area Network (LAN/VLAN) as the cameras.
* **Why:**
  1. **Low Latency:** Inference runs at `<15ms` per frame without internet latency.
  2. **Bandwidth Preservation:** 10 HD cameras ingest ~50 GB of raw video per hour. Processing locally eliminates massive outbound data bills.
  3. **Data Privacy & Compliance:** Plant footage remains inside the factory firewall.
* **How It Runs:** Packaged via `docker-compose.yml` with systemd auto-restart on boot:
  ```bash
  docker compose up -d --build
  ```

### B. The Frontend (Control Room & Operations Dashboard)
* **Option 1 (Air-Gapped / Standard Factory):** Served directly by the local Edge Server at `http://<edge-ip>:8000/dashboard`. Control room screens, tablets, and supervisor PCs access it via local IP.
* **Option 2 (Central Multi-Plant Corporate Portal):** A Next.js/React frontend hosted on Vercel/AWS. It connects to the on-prem edge microservices through a secure reverse proxy (e.g., Cloudflare Tunnel, Tailscale, or corporate WireGuard VPN).

---

## 3. Multi-Camera Configuration Specification

In a multi-camera factory, cameras are defined in a clean JSON configuration file (`config/cameras.json`). Each stream runs in its own decoupled ingestion thread to prevent cross-stream blocking.

### Camera Configuration Schema (`config/cameras.json`)
```json
{
  "facility": "Pune Plant - Bay 04",
  "cameras": [
    {
      "camera_id": "CAM-01-WELDING",
      "name": "Welding Bay East",
      "rtsp_url": "rtsp://admin:SafePass2026@192.168.1.101:554/Streaming/Channels/101",
      "zone_profile": "welding_zone_a",
      "enabled": true,
      "target_fps": 15
    },
    {
      "camera_id": "CAM-02-LOADING",
      "name": "Loading Dock North",
      "rtsp_url": "rtsp://admin:SafePass2026@192.168.1.102:554/Streaming/Channels/101",
      "zone_profile": "dock_zone_b",
      "enabled": true,
      "target_fps": 15
    },
    {
      "camera_id": "CAM-03-ASSEMBLY",
      "name": "Assembly Conveyor #2",
      "rtsp_url": "rtsp://admin:SafePass2026@192.168.1.103:554/live/ch0",
      "zone_profile": "assembly_general",
      "enabled": true,
      "target_fps": 10
    }
  ]
}
```

---

## 4. Client Camera Setup & Commissioning Checklist (For Engineers & Integrators)

When integrating client cameras on-site, provide this exact step-by-step checklist to field engineers:

```mermaid
flowchart TD
    S1["1. Network Isolation<br/>Assign Static IP on Camera VLAN"] 
    ➡️ S2["2. Camera Stream Config<br/>Enable RTSP, H.264 Main, Sub-stream 1080p@15fps"] 
    ➡️ S3["3. Security & Credentials<br/>Create read-only operator account"] 
    ➡️ S4["4. Stream Verification<br/>Validate via ffprobe / VLC"] 
    ➡️ S5["5. Geofence Calibration<br/>Map pixel coordinates for polygons"]
```

### Step 1: Network & Subnet Allocation
1. Verify the Edge Server and cameras share an isolated CCTV VLAN (e.g., `192.168.20.0/24`).
2. Ensure each camera has a **Static IP address** assigned (e.g., `192.168.20.101` to `192.168.20.116`) or DHCP reservations bound to their MAC addresses.
3. Test connectivity from edge terminal:
   ```bash
   ping -c 3 192.168.20.101
   ```

### Step 2: Camera Firmware & Stream Settings (Hikvision / Dahua / Axis / Hanwha)
* **Codec:** Use **H.264** (Baseline or Main Profile). Avoid H.265 if edge CPU decoding overhead is tight; avoid MJPEG on IP cameras due to excessive network saturation.
* **Resolution:** 1080p (`1920x1080`) or 720p (`1280x720`).
* **Frame Rate (FPS):** Set the camera output to **15 FPS** or **20 FPS** (30 FPS is redundant for PPE safety audits and burns extra edge memory).
* **Bitrate Control:** **CBR (Constant Bitrate)** at ~2048 to 4096 kbps.
* **GOP / I-Frame Interval:** Set equal to frame rate (e.g., GOP = 15 or 30) for fast stream synchronization.

### Step 3: Standard RTSP URL Formats by Vendor
* **Hikvision:** `rtsp://<user>:<pass>@<ip>:554/Streaming/Channels/101` (Main) or `/102` (Sub-stream)
* **Dahua:** `rtsp://<user>:<pass>@<ip>:554/cam/realmonitor?channel=1&subtype=0`
* **Axis:** `rtsp://<user>:<pass>@<ip>:554/axis-media/media.amp`
* **Generic ONVIF:** `rtsp://<user>:<pass>@<ip>:554/live/ch0`

### Step 4: Stream Validation with `ffprobe`
Before starting the SafeVision AI engine, test stream integrity directly on the edge box:
```bash
ffprobe -v error -show_entries stream=width,height,codec_name,r_frame_rate "rtsp://admin:password@192.168.20.101:554/Streaming/Channels/101"
```

---

## 5. Industrial Edge Sizing Rules of Thumb

| Concurrent Cameras | Recommended Edge GPU | CPU & RAM | Expected Latency |
| :--- | :--- | :--- | :--- |
| **1 – 2 Streams** | NVIDIA RTX 2050 / GTX 1660 / Jetson Orin Nano | 4 Cores, 8 GB RAM | ~13 ms / frame |
| **4 – 8 Streams** | NVIDIA RTX 4060 Ti (16GB) / RTX A2000 | 8 Cores, 32 GB RAM | ~18 ms / frame |
| **16+ Streams** | NVIDIA L4 (24GB) / RTX 4090 / Jetson AGX Orin | 16 Cores, 64 GB RAM | Batch inference (~25 ms) |
