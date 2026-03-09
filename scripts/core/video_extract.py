"""Video frame extraction using OpenCV (optional dependency)."""

import sys
from pathlib import Path
from typing import Generator

# Maximum frames to prevent runaway processing
MAX_FRAMES_DEFAULT = 3000  # 5 min at 10fps
WARN_DURATION_SECS = 60


def check_opencv():
    """Check if OpenCV is available."""
    try:
        import cv2  # noqa: F401
        return True
    except ImportError:
        return False


def extract_frames(
    video_path: str,
    target_fps: int = 10,
    max_frames: int = MAX_FRAMES_DEFAULT,
) -> Generator:
    """
    Extract frames from video at target FPS.

    Yields PIL Image objects one at a time (memory safe).

    Args:
        video_path: Path to video file (MP4, WebM, GIF)
        target_fps: Desired output frame rate
        max_frames: Safety limit on total frames
    """
    try:
        import cv2
    except ImportError:
        print(
            "Error: Video support requires opencv-python.\n"
            "Install with: pip install opencv-python-headless",
            file=sys.stderr,
        )
        return

    from PIL import Image

    path = Path(video_path)
    if not path.exists():
        print(f"Error: Video file not found: {video_path}", file=sys.stderr)
        return

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        print(f"Error: Could not open video: {video_path}", file=sys.stderr)
        return

    source_fps = cap.get(cv2.CAP_PROP_FPS) or 30
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration = total_frames / source_fps if source_fps > 0 else 0

    if duration > WARN_DURATION_SECS:
        print(
            f"Warning: Video is {duration:.0f}s long. "
            f"Processing at {target_fps}fps (max {max_frames} frames).",
            file=sys.stderr,
        )

    # Calculate frame skip interval
    frame_interval = max(1, int(source_fps / target_fps))
    frame_idx = 0
    yielded = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % frame_interval == 0:
            if yielded >= max_frames:
                print(
                    f"Warning: Reached max frame limit ({max_frames}). Stopping.",
                    file=sys.stderr,
                )
                break

            # Convert BGR (OpenCV) → RGB (PIL)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            yield img
            yielded += 1

            # Progress feedback every 100 frames
            if yielded % 100 == 0:
                print(f"  Processed {yielded} frames...", file=sys.stderr)

        frame_idx += 1

    cap.release()
    print(f"  Extracted {yielded} frames total.", file=sys.stderr)
