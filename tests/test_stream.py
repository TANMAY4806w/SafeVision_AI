"""
Unit tests for Threaded RTSP Stream Ingestion & Zero-Lag Frame Buffering.
"""

import os
import sys
import time
import pytest

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine.video_stream import ThreadedRTSPStream


@pytest.fixture
def sample_video_path():
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "sample_feed.mp4"))
    if not os.path.exists(path):
        # Generate on the fly if needed
        from data.generate_sample import generate_synthetic_video
        generate_synthetic_video(path)
    return path


def test_stream_reading_and_frame_shape(sample_video_path):
    stream = ThreadedRTSPStream(src=sample_video_path)
    stream.start()

    time.sleep(0.2)  # Allow worker thread to read initial frames
    success, frame = stream.read(timeout=2.0)

    assert success is True
    assert frame is not None
    assert len(frame.shape) == 3
    assert frame.shape[0] == 480
    assert frame.shape[1] == 640

    stream.stop()
    assert stream.stopped.is_set()


def test_stream_context_manager(sample_video_path):
    with ThreadedRTSPStream(src=sample_video_path) as stream:
        time.sleep(0.1)
        success, frame = stream.read(timeout=1.0)
        assert success is True
        assert frame is not None
    assert stream.stopped.is_set()
