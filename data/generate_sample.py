"""
Generates synthetic video feed with moving simulated workers for testing
without requiring physical RTSP CCTV hardware.
"""

import os
import cv2
import numpy as np


def generate_synthetic_video(output_path: str = "data/sample_feed.mp4", duration_sec: int = 5, fps: int = 30):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    width, height = 640, 480
    total_frames = duration_sec * fps
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    print(f"Generating synthetic industrial video: {output_path} ({total_frames} frames)...")

    # Worker 1: walks from left to right (enters danger zone)
    # Worker 2: stays in safe zone on the right
    for i in range(total_frames):
        # Dark industrial floor background
        frame = np.full((height, width, 3), 40, dtype=np.uint8)

        # Draw grid lines on factory floor
        for y in range(0, height, 40):
            cv2.line(frame, (0, y), (width, y), (55, 55, 55), 1)
        for x in range(0, width, 40):
            cv2.line(frame, (x, 0), (x, height), (55, 55, 55), 1)

        # Worker 1 moving horizontally across the floor
        w1_x = int(30 + (i / total_frames) * 450)
        w1_y = 220
        # Draw worker body (torso)
        cv2.rectangle(frame, (w1_x, w1_y), (w1_x + 50, w1_y + 120), (180, 100, 50), -1)
        # Draw worker head
        cv2.circle(frame, (w1_x + 25, w1_y - 15), 18, (200, 180, 160), -1)
        # Worker 1 has hard hat (yellow helmet)
        cv2.ellipse(frame, (w1_x + 25, w1_y - 22), (20, 10), 0, 180, 360, (0, 220, 255), -1)

        # Worker 2 static in safe zone
        w2_x, w2_y = 520, 260
        # Draw worker 2 body
        cv2.rectangle(frame, (w2_x, w2_y), (w2_x + 50, w2_y + 120), (100, 150, 60), -1)
        # Draw worker 2 head (no helmet!)
        cv2.circle(frame, (w2_x + 25, w2_y - 15), 18, (190, 160, 140), -1)

        # Timestamp watermark
        cv2.putText(frame, f"CAM-01 INDUSTRIAL [FRAME {i:04d}]", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

        out.write(frame)

    out.release()
    print(f"Synthetic video successfully written to: {output_path}")


if __name__ == "__main__":
    generate_synthetic_video()
