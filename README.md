# SafeVision AI — Real-Time Industrial Safety & Edge Video Analytics Platform

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-00FFFF)](https://github.com/ultralytics/ultralytics)
[![ONNX Runtime](https://img.shields.io/badge/ONNX_Runtime-FP16-005CED?logo=onnx&logoColor=white)](https://onnxruntime.ai/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/TANMAY4806w/SafeVision_AI/blob/main/notebooks/train_colab.ipynb)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **SafeVision AI** transforms passive industrial CCTV cameras into an autonomous, 24/7 edge safety supervisor. It ingests live RTSP camera feeds with zero buffer lag, detects missing Personal Protective Equipment (Hard Hats & High-Visibility Vests), enforces virtual polygon danger zones, and generates automated GenAI OSHA compliance incident reports.

---

## 📌 1. Problem Statement: Why SafeVision AI?

In heavy manufacturing plants, construction sites, and chemical refineries:

```
[50+ Factory CCTV Cameras] ──> [Human Security Guards] ──> [Fatigue after 20 mins (95% breaches missed)]
                                                                       │
                                                                       ▼
[Catastrophic Incidents] <── [Severe Head Trauma / Danger Incursion] <──┘
```

1. **Surveillance Fatigue:** Studies show human operators miss up to **95% of safety breaches** after just 20 minutes of continuous CCTV monitoring.
2. **Missing PPE Hazards:** Lack of hard hats and high-visibility safety vests is the leading cause of preventable workplace fatalities.
3. **Hazardous Machinery Incursion:** Blind spots around robotic arms, overhead cranes, and conveyor belts lead to fatal crush injuries.
4. **Cloud Latency & High Bandwidth Costs:** Streaming hundreds of 1080p feeds to cloud servers costs thousands of dollars monthly and introduces 500ms–2000ms latency. Edge inference must execute locally in **under 35ms**.

---

## 🏗️ 2. End-to-End System Architecture

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               1. VIDEO INGESTION LAYER                                 │
│   RTSP IP Camera (rtsp://...) / USB Webcams / Local MP4 Video                          │
│   • Multi-threaded OpenCV VideoCapture worker                                          │
│   • Atomic Queue (maxsize=1) ➔ Discards stale frames (Zero-Lag Guaranteed)             │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ Fresh Frame (<1ms lag)
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                          2. EDGE VISION INFERENCE ENGINE                               │
│   YOLOv8 Object Detection (PyTorch & ONNX Runtime FP16)                                │
│   • Detected Classes: [Person], [Helmet], [Safety_Vest], [No_Helmet], [No_Vest]        │
│   • Outputs: Bounding Box Coordinates [x1, y1, x2, y2], Class ID, Confidence           │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ Detections Array
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                      3. SPATIAL PAIRING & GEOFENCING LOGIC                             │
│   OpenCV Geometric Analysis                                                            │
│   • Worker-to-Gear Pairing: Evaluates geometric overlap (Upper 25% for Head)           │
│   • Foot Coordinates: x_foot = (x1 + x2)/2, y_foot = y2                                │
│   • Point-in-Polygon Test: cv2.pointPolygonTest against zones.json                     │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ Violation Event
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                      4. DISPATCH, API & GENAI AUDITING LAYER                           │
│   FastAPI Microservice                                                                 │
│   • Live MJPEG Video Stream (/api/v1/video/stream)                                     │
│   • Detection REST Endpoint (/api/v1/video/detect-frame)                               │
│   • GenAI Incident Synthesizer: Translates raw alerts into formal OSHA Incident Cards  │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔍 3. Core Technical Innovations Explained Simply

### A. What is RTSP?
* **RTSP (Real-Time Streaming Protocol)** is the universal network protocol used by industrial IP cameras (Hikvision, Dahua, Axis, CP Plus) to stream continuous live video over local Ethernet or Wi-Fi (`rtsp://192.168.1.10:554/stream`).
* Unlike HTTP video streaming, RTSP provides a continuous frame-by-frame transmission pipeline optimized for security cameras.

---

### B. The Video Lag Problem & Zero-Lag Buffer Solution

#### The Problem:
* Standard OpenCV `cv2.VideoCapture.read()` queues incoming frames into a memory buffer.
* When AI processes frames at 20 FPS while the camera sends 30 FPS, frames accumulate in the queue.
* **Result:** After just 2 minutes, your AI is analyzing video from **10 seconds in the past**—unacceptable for workplace safety!

```
[Camera sends 30 FPS] ──> [OpenCV Internal Queue (100+ frames)] ──> [AI processes 20 FPS] ──> 10-Second Video Lag!
```

#### Our Zero-Lag Solution:
* We decouple frame reading from AI inference using a **dedicated background daemon thread** and an **atomic queue of size 1** (`queue.Queue(maxsize=1)`).
* The background thread constantly updates the buffer; old frames are instantly discarded when a new frame arrives.

```
[CCTV Camera] ──> [Background Thread] ──(Discards stale frames)──> [Buffer Size=1] ──> [AI Engine (<1ms lag)]
```

---

### C. Spatial Worker-to-Gear Association

Having a `Person` and a `Helmet` detected in the same room does not prove the worker is wearing it. We pair gear using geometric bounding box analysis:

```
┌────────────────────────────────────────┐
│ Person Bounding Box                    │
│ ┌────────────────────────────────────┐ │
│ │  Head Zone (Top 25% of Box)        │ │ ──> Helmet detected? ──> ✅ Compliant
│ │  [Helmet Check]                    │ │                      ──> ❌ Violation: NO_HELMET
│ ├────────────────────────────────────┤ │
│ │  Torso Zone (Middle 50% of Box)    │ │ ──> Vest detected?   ──> ✅ Compliant
│ │  [Safety Vest Check]               │ │                      ──> ❌ Violation: NO_VEST
│ └────────────────────────────────────┘ │
│                                        │
│  Feet Anchor: (x_center, y_bottom)     │ ──> Evaluated against Virtual Polygon Danger Zone
└────────────────────────────────────────┘
```

---

### D. Virtual Polygon Danger Zone Geofencing

Safety managers define hazardous perimeters (e.g. robotic arm zones) via polygon vertices in `data/zones.json`.
1. Calculate the worker's ground-contact coordinate:
   $$x_{\text{foot}} = \frac{x_1 + x_2}{2}, \quad y_{\text{foot}} = y_2$$
2. Execute OpenCV Point-in-Polygon test:
   $$\text{status} = \text{cv2.pointPolygonTest}(\text{polygon\_contour}, (x_{\text{foot}}, y_{\text{foot}}), \text{measureDist}=\text{False})$$
3. If inside ($\ge 0$): Instantly draw a flashing red perimeter and flag `CRITICAL_INTRUSION_ALERT`.

---

## 📁 4. Project Directory Structure

```
SafeVision_AI/
├── engine/                               # Core Computer Vision & Video Processing
│   ├── __init__.py
│   ├── video_stream.py                   # Multi-threaded RTSP frame buffer (zero lag)
│   ├── ppe_detector.py                   # YOLOv8 PPE detection & association logic
│   └── zone_monitor.py                   # Virtual polygon geofencing & intrusion math
│
├── optimization/                         # Model Optimization & Compression
│   ├── __init__.py
│   ├── export_onnx.py                    # PyTorch ➡️ ONNX FP16 conversion script
│   └── benchmark.py                      # Latency & FPS comparative benchmarking
│
├── api/                                  # Production FastAPI Microservice
│   ├── __init__.py
│   ├── schemas.py                        # Pydantic v2 request/response models
│   ├── routes.py                         # Stream & Detection REST endpoints
│   └── reporter.py                       # GenAI OSHA Incident Report Synthesizer
│
├── demo/                                 # Enterprise Operations Dashboard
│   ├── __init__.py
│   └── app.py                            # Production HTML5 monitoring console (/dashboard)
│
├── data/                                 # Media & configurations
│   ├── sample_feed.mp4                   # Sample industrial video clip
│   ├── zones.json                        # Pre-configured polygon zone coordinates
│   └── cameras.json                      # Multi-camera RTSP topology specification
│
├── tests/                                # Automated Pytest Suite (33 tests)
│   ├── test_stream.py                    # Stream buffer concurrency tests
│   ├── test_polygon.py                   # Point-in-polygon math accuracy tests
│   ├── test_detector.py                  # Spatial PPE pairing & tracking tests
│   ├── test_api.py                       # REST API & OSHA report tests
│   └── test_dashboard.py                 # Enterprise UI route & telemetry tests
│
├── docs/                                 # Enterprise Field Documentation
│   ├── CLIENT_CAMERA_SETUP_AND_DEPLOYMENT_GUIDE.md  # On-prem camera & network setup
│   └── INTERVIEW_TALKING_POINTS_AND_DECISIONS.md    # Senior engineering decisions log
│
├── Dockerfile                            # Production Container Definition
├── docker-compose.yml                    # Multi-container orchestration
├── requirements.txt                      # Production dependencies
├── main.py                               # CLI & Service Entry Point
└── README.md                             # Production Documentation
```

---

## ⚡ 5. Quickstart & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/TANMAY4806w/SafeVision_AI.git
cd SafeVision_AI
```

### 2. Set Up Virtual Environment
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Run the Microservice & Dashboard
```bash
python main.py
```
* **Operations Dashboard:** `http://localhost:8000/dashboard`
* **API Documentation:** `http://localhost:8000/docs`
* **Live Video Stream:** `http://localhost:8000/api/v1/video/stream`
* **Health Check:** `http://localhost:8000/health`

---

## 📊 6. Model Training & Evaluation Metrics

The custom YOLOv8 model was trained on the industrial **Construction-PPE** dataset (20 Epochs on Tesla T4 GPU).

### Key Class Accuracy & mAP@50:
| Class | Precision | Recall | mAP@50 | Operational Status |
| :--- | :--- | :--- | :--- | :--- |
| **`Person` (Workers)** | **91.1%** | **90.0%** | **94.5%** | 🔥 Production Grade |
| **`Safety_Vest`** | **91.4%** | **87.9%** | **91.7%** | 🔥 Production Grade |
| **`Helmet`** | **83.4%** | **80.3%** | **82.8%** | 🟢 Compliant |
| **`No_Vest` (Violation)** | **92.2%** | **61.5%** | **71.4%** | 🟢 High Precision Alert |
| **`No_Helmet` (Violation)** | **77.7%** | **53.6%** | **61.5%** | 🟢 High Precision Alert |
| **Overall Dataset** | **79.9%** | **69.4%** | **74.3%** | ✅ Exceeds 70% threshold |

* **Model Checkpoint Size:** `best.pt` (~6.2 MB) | `best.onnx` FP16 (~6.4 MB)
* **Raw Inference Latency:** **2.6 ms per image** (>380 FPS theoretical on Tesla T4)
* **Training Notebook:** [notebooks/train_colab.ipynb](notebooks/train_colab.ipynb) (Includes full outputs & loss curves)

---

## ⚡ 7. Edge Performance Benchmarks (Empirical Hardware Results)

Tested on **NVIDIA GeForce RTX 2050 (4GB VRAM)** using fine-tuned weights (`models/best.pt`) across 100 sequential inferences:

| Runtime Engine | Precision | Active Device | Mean Latency (ms) | P50 (ms) | P95 (ms) | Throughput (FPS) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **PyTorch (Native)** | FP32 Standard | `cuda:0` | 13.50 ms | 12.43 ms | 16.58 ms | **74.0 FPS** |
| **PyTorch (Quantized)**| **FP16 Half** | `cuda:0` | **13.06 ms** | **12.28 ms** | **16.58 ms** | 🔥 **76.6 FPS** |
| **ONNX Runtime** | FP16 Export | `CPU` (Fallback) | 52.50 ms | 50.65 ms | 70.76 ms | **19.0 FPS** |

*Note: On Windows edge systems without matching CUDA 13 DLLs, PyTorch native FP16 (`cuda:0`) delivers the best production throughput (76.6 FPS, ~3x faster than the 25 FPS production latency budget).*

---

## 👤 Author & Contributor
* **Tanmay Patil** ([@TANMAY4806w](https://github.com/TANMAY4806w))
* Email: [patiltanmay019@gmail.com](mailto:patiltanmay019@gmail.com)

---

## 📜 License
This project is licensed under the [MIT License](LICENSE).
