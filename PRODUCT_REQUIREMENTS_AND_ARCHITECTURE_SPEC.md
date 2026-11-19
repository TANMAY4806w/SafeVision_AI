# SafeVision AI — Product Requirements Document (PRD) & Engineering Plan
**Project Name:** SafeVision AI (Real-Time Industrial Safety & Edge Video Analytics Platform)  
**Target Domain:** Manufacturing Plants, Industrial Construction, Heavy Warehouses & Refineries  
**Architecture Standard:** Edge-Deployed Computer Vision + Multi-Threaded RTSP Streaming + GenAI Audit Logging  
**Document Status:** Approved Engineering Specification  

---

## 1. Real-Life Problem Statement & Industry Context

### 1.1 The Real-World Crisis in Industrial Workplaces
In heavy industrial environments (cement plants, steel manufacturing, automotive assembly lines, chemical refineries, and high-rise construction sites):
1. **Fatal Workplace Injuries:** Every year, thousands of severe injuries and fatalities occur due to missing **Personal Protective Equipment (PPE)**—specifically head trauma from falling objects (missing hard hats) and vehicular/machinery collisions (missing high-visibility reflective vests).
2. **The "Surveillance Fatigue" Bottleneck:** Industrial plants have 50 to 500+ CCTV cameras streaming into a security room. Research proves that after just **20 minutes of continuous monitoring**, a human security guard misses **up to 95% of safety breaches**. Manual surveillance does not scale.
3. **Hazardous Machinery Incursion:** High-risk zones (robotic arm perimeters, overhead crane drop zones, conveyor belts, high-voltage switchyards) require strict physical isolation. When a worker inadvertently enters a blind spot, catastrophic accidents occur in fractions of a second.
4. **Cloud Latency & High Bandwidth Costs:** Streaming hundreds of 1080p CCTV camera feeds to cloud servers costs lakhs of rupees per month in bandwidth and introduces 500ms–2000ms latency. A worker walking into a danger zone needs an alert within **milliseconds**, not seconds. Inference **must run locally on edge hardware**.
5. **Regulatory Fines & Audit Penalties:** Regulatory bodies (OSHA, DGFASLI) impose heavy financial penalties and shutdown notices for safety violations. Companies lack automated, tamper-proof audit trails with verifiable image citations.

---

### 1.2 What `SafeVision AI` Solves
`SafeVision AI` turns passive, dumb CCTV cameras into an **active, autonomous, 24/7 edge safety supervisor**:
* **Autonomous PPE Compliance:** Continuously detects whether workers are wearing required safety helmets and high-visibility vests in real time.
* **Zero-Lag Video Processing:** Ingests live IP camera RTSP streams using a multi-threaded queue that automatically drops stale frames, guaranteeing real-time latency (<30ms).
* **Virtual Geofencing (Polygon Intrusion):** Allows plant managers to draw custom danger zones on camera feeds; immediately triggers an alarm if a worker crosses the virtual boundary.
* **Edge-Optimized Footprint:** Quantizes models from PyTorch into **ONNX Runtime (FP16/INT8)**, enabling 30+ FPS inference on low-cost edge GPUs or industrial PCs.
* **Automated GenAI Incident Reporting:** Translates raw detection bounding boxes into formal, structured safety incident reports formatted for factory safety officers.

---

## 2. High-Level Architecture & Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                1. VIDEO INGESTION LAYER                                 │
│      RTSP IP Camera Streams / Local MP4 Video / USB Webcams                             │
│      • Multi-threaded OpenCV VideoCapture worker                                        │
│      • Non-blocking frame queue (drops stale frames to prevent stream lag)             │
└────────────────────────────────────────────┬────────────────────────────────────────────┘
                                             │ Clean Frame (1080p / 720p)
                                             ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                           2. EDGE VISION INFERENCE ENGINE                               │
│      YOLOv8 Detection Model (PyTorch & ONNX Runtime FP16)                               │
│      • Detects: [Person], [Hard Hat / Helmet], [Safety Vest], [No-Helmet], [No-Vest]    │
│      • Outputs: Bounding Box Coordinates [x1, y1, x2, y2], Class ID, Confidence Score   │
└────────────────────────────────────────────┬────────────────────────────────────────────┘
                                             │ Detections Array
                                             ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                       3. SPATIAL GEOFENCING & LOGIC ENGINE                              │
│      OpenCV Geometric Analysis                                                          │
│      • Virtual Polygon Danger Zone definition: [(x1,y1), (x2,y2), ...]                  │
│      • Point-in-Polygon test (`cv2.pointPolygonTest`) for bottom-center person coords   │
│      • Violation Classification: [PPE_VIOLATION], [ZONE_INTRUSION], [COMBINED_CRITICAL] │
└────────────────────────────────────────────┬────────────────────────────────────────────┘
                                             │ Filtered Violation Event
                                             ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                       4. DISPATCH, API & GENAI AUDIT LAYER                              │
│      FastAPI Microservice (Port 8000)                                                   │
│      • Real-time MJPEG annotated stream endpoint (`/api/v1/stream/feed`)                │
│      • Redis / In-memory Alert Queue                                                    │
│      • GenAI Incident Synthesizer: Generates formal OSHA Compliance Report              │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Product Functional Requirements (FR)

### FR-1: Real-Time RTSP Stream Ingestion with Zero Frame Lag
* Must ingest live RTSP camera feeds (`rtsp://username:password@ip:port/h264`) or local test video files.
* Must implement a dedicated background reader thread using `threading.Thread` that constantly reads frames and overwrites a single-element buffer.
* The processing engine must always pull the *latest* frame, completely eliminating the 5-to-10 second frame buffer lag common in naive `cv2.VideoCapture.read()` implementations.

### FR-2: Real-Time PPE Detection Engine
* Must detect workers and their safety gear with high precision ($\ge 85\%$ precision).
* Classes:
  1. `Person`
  2. `Helmet` (or `Hard Hat`)
  3. `Safety_Vest`
  4. `No_Helmet` (Flagged as Violation)
  5. `No_Vest` (Flagged as Violation)
* Must pair the detected gear to the specific person bounding box using geometric overlap (IoU / centroid inclusion).

### FR-3: Virtual Polygon Zone Intrusion (Danger Zone Geofencing)
* Plant managers must be able to specify a list of $(x, y)$ coordinate points representing a dangerous perimeter (e.g., robotic arm zone, chemical vat area).
* The system computes the worker's bottom-center coordinate:
  $$x_{\text{foot}} = \frac{x_1 + x_2}{2}, \quad y_{\text{foot}} = y_2$$
* Uses `cv2.pointPolygonTest` to evaluate if $(x_{\text{foot}}, y_{\text{foot}})$ is inside the virtual polygon.
* If inside: Draws a pulsing red border around the zone and flags a `CRITICAL_INTRUSION_ALERT`.

### FR-4: Model Optimization & Latency Benchmarking (ONNX Runtime)
* Must include a dedicated export script converting the PyTorch `.pt` model into an `.onnx` model.
* Supports FP16 (Half Precision) execution via ONNX Runtime Execution Providers (`CUDAExecutionProvider` or optimized `CPUExecutionProvider`).
* Includes an automated benchmark script comparing:
  * PyTorch standard inference time (ms).
  * ONNX Runtime inference time (ms).
  * Percentage latency reduction and FPS throughput.

### FR-5: FastAPI Microservice & Automated GenAI Incident Reporting
* Exposes clean REST API endpoints:
  * `GET /health`: System & GPU status.
  * `POST /api/v1/video/detect-frame`: Ingests a single image frame, returns structured JSON detections and violation status.
  * `GET /api/v1/video/stream`: Real-time streaming response of annotated video frames with visual bounding boxes.
  * `POST /api/v1/incident/generate-report`: Takes a detected violation payload and uses an LLM (Gemini / local LLaMA) to generate a structured, formal Industrial Safety Violation Notice with severity level, timestamp, camera ID, and mandated corrective action.

---

## 4. Product Non-Functional Requirements (NFR)

* **NFR-1 (Inference Latency):** Full end-to-end processing (capture + inference + polygon test + annotation) must execute under **35ms per frame** on a modern GPU, enabling $\ge 25$ real-time frames per second (FPS).
* **NFR-2 (Modular Codebase):** Clean Python OOP principles with strict Pydantic data schemas, type hinting, and docstrings.
* **NFR-3 (Edge Compatibility):** Must run self-contained without mandatory cloud internet access (model inference and polygon logic must function completely offline).
* **NFR-4 (Portability):** Packaged with a clean `requirements.txt` and `Dockerfile` for single-command deployment.

---

## 5. Modular Project Directory Structure

```
03_Projects/SafeVision_AI/
│
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
│   ├── schemas.py                        # Pydantic request/response models
│   ├── routes.py                         # Stream & Detection REST endpoints
│   └── reporter.py                       # GenAI OSHA Incident Report Synthesizer
│
├── demo/                                 # Enterprise Operations Dashboard
│   ├── __init__.py
│   └── app.py                            # Production HTML5 monitoring console (/dashboard)
│
├── data/                                 # Sample media & test assets
│   ├── sample_feed.mp4                   # Sample industrial video clip
│   ├── zones.json                        # Pre-configured polygon zone coordinates
│   └── cameras.json                      # Multi-camera RTSP topology specification
│
├── tests/                                # Automated Test Suite (33 tests)
│   ├── test_stream.py
│   ├── test_polygon.py
│   ├── test_detector.py
│   ├── test_api.py
│   └── test_dashboard.py
│
├── Dockerfile                            # Production Container Definition
├── requirements.txt                      # Frozen Python dependencies
├── main.py                               # CLI & Service Entry Point
└── README.md                             # Production Documentation & Resume Bullets
```

---

## 6. Step-by-Step Implementation Plan

### Phase 1: Environment & Dependency Setup
* Initialize virtual environment with Python 3.10+.
* Install core dependencies: `ultralytics`, `opencv-python-headless`, `onnxruntime`, `fastapi`, `uvicorn`, `pydantic`, `numpy`.

### Phase 2: Build Multi-Threaded RTSP Stream Buffer (`video_stream.py`)
* Implement class `ThreadedRTSPStream`:
  * Spawns a daemon thread executing `cv2.VideoCapture`.
  * Maintains an atomic queue of size 1 (`queue.Queue(maxsize=1)`).
  * Automatically discards old frames when new frames arrive so processing never falls behind real-time.

### Phase 3: Build PPE Detection & Pairing Pipeline (`ppe_detector.py`)
* Implement class `PPEDetector`:
  * Loads YOLOv8 model (PyTorch or ONNX).
  * Filters detections for workers and safety gear.
  * Associates gear with workers based on bounding box geometry.
  * Outputs list of identified violations: `NO_HARD_HAT`, `NO_SAFETY_VEST`.

### Phase 4: Build Polygon Intrusion Geofencing (`zone_monitor.py`)
* Implement class `ZoneMonitor`:
  * Ingests arbitrary polygon vertices from `zones.json`.
  * Computes person ground-contact coordinates $(x_{\text{foot}}, y_{\text{foot}})$.
  * Executes `cv2.pointPolygonTest(polygon, (x_foot, y_foot), measureDist=False)`.
  * Overlays danger zone overlay on the video frame (Green = Safe, Red = Intrusion Detected).

### Phase 5: ONNX Optimization & Benchmark Script (`optimization/`)
* Export YOLOv8 to ONNX format with dynamic axes:
  `yolo export model=yolov8n.pt format=onnx dynamic=True half=True`
* Run side-by-side benchmark measuring 100 sequential inferences:
  * Measures PyTorch average latency (ms).
  * Measures ONNX Runtime average latency (ms).
  * Calculates exact percentage latency reduction and FPS gains.

### Phase 6: FastAPI Service & GenAI Compliance Reporter (`api/`)
* Build asynchronous endpoints streaming MJPEG video to any web browser.
* Build `/api/v1/incident/generate-report` taking detection events and generating formal OSHA incident cards via LLM.

---

## 7. Product Deliverables & Outputs

1. **Annotated Video Stream:** Live video feed displaying:
   * Green bounding boxes for compliant workers with hard hats and vests.
   * Red bounding boxes and warning banners for non-compliant workers.
   * Highlighted virtual polygon zones with real-time occupancy counts.
2. **Benchmark Report:** Reproducible latency metrics showing **40%+ latency reduction** using ONNX Runtime.
3. **Structured Alert JSON:** Real-time event payloads sent to message queues.
4. **Automated Incident Report:** Publication-ready compliance logs for safety managers.

---

## 8. Interview Talking Points (How to Pitch This in 60 Seconds)

When the interview panel at Augmented Transformations asks about your experience:
> *"I noticed your flagship platform VEDA focuses heavily on industrial video analytics, so I engineered **SafeVision AI**—a real-time edge safety monitoring system.  
> The core challenge in industrial CCTV is stream latency and camera buffer lag. I solved this by building a dedicated multi-threaded RTSP ingestion pipeline that drops stale frames and processes live feeds under 30ms.  
> For inference, I built a YOLOv8 PPE detector that tracks hard hats and safety vests while monitoring restricted machinery zones via OpenCV polygon geofencing.  
> To ensure it runs on edge hardware, I quantized the model into **ONNX Runtime FP16**, achieving a **40%+ latency reduction**, and connected it to a FastAPI service that auto-generates OSHA safety violation reports."*
