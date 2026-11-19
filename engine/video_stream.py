"""
Threaded RTSP Stream Ingestion Engine with Zero-Lag Frame Buffering.
Decouples frame capture from AI inference, eliminating buffer lag in naive OpenCV.
"""

import time
import logging
import threading
import queue
from typing import Optional, Tuple, Union
import numpy as np
import cv2

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SafeVision.VideoStream")


class ThreadedRTSPStream:
    """
    Multi-threaded VideoCapture reader that continuously pulls frames in a background thread
    and keeps only the latest 1 frame in an atomic queue of size 1.
    
    Includes auto-reconnect watchdog for industrial camera stream drops.
    """

    def __init__(
        self,
        src: Union[str, int] = 0,
        reconnect_timeout_sec: float = 2.0,
        max_reconnect_attempts: int = 10,
    ):
        """
        :param src: RTSP URL (e.g. 'rtsp://user:pass@ip:554/feed'), video file path, or webcam int (0).
        :param reconnect_timeout_sec: Time to wait before attempting reconnection when feed drops.
        :param max_reconnect_attempts: Maximum retries before raising a persistent error.
        """
        self.src = src
        self.reconnect_timeout_sec = reconnect_timeout_sec
        self.max_reconnect_attempts = max_reconnect_attempts

        self.cap: Optional[cv2.VideoCapture] = None
        self.frame_queue: queue.Queue = queue.Queue(maxsize=1)
        self.stopped = threading.Event()
        self.thread: Optional[threading.Thread] = None

        self.total_frames_read = 0
        self.dropped_frames = 0
        self.fps = 0.0
        self._fps_time = time.time()
        self._fps_count = 0

    def start(self) -> "ThreadedRTSPStream":
        """Opens capture source and spawns background worker thread."""
        self._open_capture()
        self.stopped.clear()
        self.thread = threading.Thread(target=self._capture_worker, daemon=True, name="RTSPReader")
        self.thread.start()
        logger.info(f"ThreadedRTSPStream worker started on source: {self.src}")
        return self

    def _open_capture(self) -> bool:
        """Initializes or resets the OpenCV VideoCapture object."""
        if self.cap is not None:
            self.cap.release()

        # On Windows/Linux, cv2.CAP_FFMPEG works best for RTSP
        if isinstance(self.src, str) and (self.src.startswith("rtsp://") or self.src.startswith("http://")):
            self.cap = cv2.VideoCapture(self.src, cv2.CAP_FFMPEG)
        else:
            self.cap = cv2.VideoCapture(self.src)

        if not self.cap.isOpened():
            logger.warning(f"Unable to open video stream at: {self.src}")
            return False
        return True

    def _capture_worker(self):
        """Continuous background loop reading frames and overwriting the queue."""
        consecutive_failures = 0

        while not self.stopped.is_set():
            if self.cap is None or not self.cap.isOpened():
                if not self._handle_reconnect():
                    break
                continue

            grabbed, frame = self.cap.read()

            if not grabbed or frame is None:
                consecutive_failures += 1
                if consecutive_failures > 15:
                    logger.warning("Stream read failed for 15 consecutive frames. Triggering reconnect watchdog...")
                    if not self._handle_reconnect():
                        break
                    consecutive_failures = 0
                time.sleep(0.01)
                continue

            consecutive_failures = 0
            self.total_frames_read += 1
            self._update_fps()

            # Zero-Lag Buffer Logic:
            # If queue is full, discard the old frame and insert the newest one
            if self.frame_queue.full():
                try:
                    self.frame_queue.get_nowait()
                    self.dropped_frames += 1
                except queue.Empty:
                    pass

            try:
                self.frame_queue.put_nowait(frame)
            except queue.Full:
                pass

        logger.info("RTSPReader background worker loop terminated.")

    def _handle_reconnect(self) -> bool:
        """Attempts reconnecting to the stream with backoff."""
        attempt = 0
        while not self.stopped.is_set() and attempt < self.max_reconnect_attempts:
            attempt += 1
            logger.info(f"Reconnecting to stream (Attempt {attempt}/{self.max_reconnect_attempts})...")
            if self._open_capture():
                logger.info("Successfully reconnected to video stream!")
                return True
            time.sleep(self.reconnect_timeout_sec)
        logger.error(f"Failed to reconnect after {self.max_reconnect_attempts} attempts.")
        return False

    def _update_fps(self):
        """Calculates instantaneous ingestion FPS."""
        self._fps_count += 1
        elapsed = time.time() - self._fps_time
        if elapsed >= 1.0:
            self.fps = self._fps_count / elapsed
            self._fps_count = 0
            self._fps_time = time.time()

    def read(self, timeout: float = 1.0) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Retrieves the latest available frame from the zero-lag queue.
        Blocks for up to timeout seconds.
        """
        try:
            frame = self.frame_queue.get(timeout=timeout)
            return True, frame
        except queue.Empty:
            return False, None

    def stop(self):
        """Stops the reader thread and releases hardware resources."""
        self.stopped.set()
        if self.thread is not None and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        logger.info(f"ThreadedRTSPStream stopped. Total read: {self.total_frames_read}, Discarded: {self.dropped_frames}")

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
