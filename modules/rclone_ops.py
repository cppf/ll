"""
modules/rclone_ops.py
======================
Wraps `rclone` for two operations:
  1. Listing files in the remote Drive folder (rclone lsjson).
  2. Downloading a single file with live progress (rclone copy -P).

rclone is invoked as a subprocess — no rclone Python bindings needed.
"""

import json
import re
import subprocess
import time
from pathlib import Path

import config


def list_remote_files():
    """
    Return a list of dicts describing files in config.RCLONE_REMOTE,
    each shaped like: {"name": str, "path": str, "size": int}

    Uses `rclone lsjson` which returns structured JSON — far more
    reliable to parse than `rclone ls` plain text output.
    """
    cmd = [
        config.RCLONE_BINARY,
        "lsjson",
        config.RCLONE_REMOTE,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(
            f"rclone lsjson failed (exit {result.returncode}):\n{result.stderr}"
        )

    entries = json.loads(result.stdout)

    files = [
        {
            "name": e["Name"],
            "path": e["Path"],
            "size": e.get("Size", 0),
        }
        for e in entries
        if not e.get("IsDir", False)
    ]
    return files


# Matches rclone -P transfer lines, e.g.:
# Transferred:       12.345 MiB / 100.000 MiB, 12%, 1.234 MiB/s, ETA 1m5s
_PROGRESS_RE = re.compile(
    r"Transferred:\s+([\d.]+\s*\w+)\s*/\s*([\d.]+\s*\w+),\s*(\d+)%,\s*([\d.]+\s*\w+/s),\s*ETA\s*(\S+)"
)


def download_file(remote_file_path: str, local_dir: str, on_progress=None):
    """
    Download a single file from the remote using `rclone copy -P`,
    streaming progress to `on_progress(percent, speed, eta)` as it goes.

    remote_file_path: the "Path" field from list_remote_files(), relative
                       to config.RCLONE_REMOTE's root.
    local_dir: local directory to copy the file into.

    Returns the local filesystem path of the downloaded file.
    """
    Path(local_dir).mkdir(parents=True, exist_ok=True)

    remote_source = f"{config.RCLONE_REMOTE}/{remote_file_path}"
    cmd = [
        config.RCLONE_BINARY,
        "copy",
        "-P",
        remote_source,
        local_dir,
    ]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    last_report = 0.0
    for line in process.stdout:
        match = _PROGRESS_RE.search(line)
        if match and on_progress:
            now = time.time()
            if now - last_report >= config.PROGRESS_UPDATE_INTERVAL:
                transferred, total, percent, speed, eta = match.groups()
                on_progress(int(percent), speed.strip(), eta.strip())
                last_report = now

    process.wait()

    if process.returncode != 0:
        raise RuntimeError(
            f"rclone copy failed (exit {process.returncode}) for {remote_file_path}"
        )

    local_path = str(Path(local_dir) / Path(remote_file_path).name)
    if not Path(local_path).exists():
        raise RuntimeError(
            f"rclone reported success but file not found at {local_path}"
        )
    return local_path
