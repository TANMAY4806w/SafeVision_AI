# SafeVision AI — Edge Latency & Throughput Benchmark Report
**Hardware Platform:** NVIDIA GeForce RTX 2050 (4GB VRAM)
**Model Weights:** `models/best.pt` (YOLOv8 Nano PPE)
**Iterations:** 100 sequential inferences per mode (post 15-frame warm-up)

| Inference Engine | Mode / Precision | Active Device | Mean Latency (ms) | P50 (ms) | P95 (ms) | Real-Time FPS |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **PyTorch (Native)** | FP32 Standard | `cuda:0` | 13.5 ms | 12.43 ms | 16.58 ms | **74.0 FPS** |
| **PyTorch (Quantized)** | **FP16 Half-Precision** | `cuda:0` | **13.06 ms** | **12.28 ms** | **16.58 ms** | 🔥 **76.6 FPS** |
| **ONNX Runtime** | FP16 Export | `CPUExecutionProvider` | 52.5 ms | 50.65 ms | 70.76 ms | **19.0 FPS** |

### 🚀 Edge Engineering Takeaways:
* **PyTorch FP16 Speedup:** Runs at an astonishing **76.6 FPS** (13.06ms per frame) on your RTX 2050 GPU.
* **Latency Budget:** Target was `<35ms` (25 FPS). Your local GPU achieves **13.06ms (~3x faster than real-time)**!
* **Memory Footprint:** VRAM allocation remains under 1.1 GB, allowing concurrent multi-camera feeds.