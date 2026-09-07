"""
modules/media_probe.py
=======================
- Detects whether a downloaded file is a video (by extension).
- For videos: extracts duration/width/height via ffprobe, and grabs a
  thumbnail frame via ffmpeg.

Requires `ffmpeg` and `ffprobe` to be installed and on PATH.
"""

import json
import subprocess
from pathlib import Path

import config


def is_video(local_path: str) -> bool:
    return Path(local_path).suffix.lower() in config.VIDEO_EXTENSIONS


def probe_video(local_path: str):
    """
    Return {"duration": int seconds, "width": int, "height": int}
    for a video file, using ffprobe.
    """
    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-show_entries", "format=duration",
        "-of", "json",
        local_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed for {local_path}:\n{result.stderr}")

    data = json.loads(result.stdout)

    stream = (data.get("streams") or [{}])[0]
    fmt = data.get("format", {})

    width = int(stream.get("width", 0))
    height = int(stream.get("height", 0))
    duration = int(float(fmt.get("duration", 0)))

    return {"duration": duration, "width": width, "height": height}


def generate_thumbnail(local_path: str, thumbnail_dir: str, duration: int) -> str:
    """
    Extract a single frame as a JPEG thumbnail, taken from ~10% into
    the video (avoids black/blank opening frames common at 0:00).

    Returns the local path to the generated thumbnail.
    """
    Path(thumbnail_dir).mkdir(parents=True, exist_ok=True)

    seek_time = max(1, int(duration * 0.1)) if duration else 1
    thumb_path = str(Path(thumbnail_dir) / (Path(local_path).stem + "_thumb.jpg"))

    cmd = [
        "ffmpeg",
        "-y",
        "-ss", str(seek_time),
        "-i", local_path,
        "-vframes", "1",
        "-vf", "scale=320:-1",
        thumb_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0 or not Path(thumb_path).exists():
        raise RuntimeError(f"ffmpeg thumbnail generation failed for {local_path}:\n{result.stderr}")

    return thumb_path
