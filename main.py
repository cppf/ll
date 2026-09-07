"""
main.py
=======
Orchestrator. Run this to process every file currently in the
configured Google Drive remote folder:

    for each file in the remote folder:
        1. download it locally via `rclone copy -P`   (live progress)
        2. if it's a video: probe duration/resolution, make a thumbnail
        3. upload it to the target Telegram channel     (live progress)
           - video -> streamable video with thumbnail
           - anything else -> plain document
        4. delete the local copy (+ thumbnail)
        5. move to the next file

Runs once through the current file list, then exits. Failures on
individual files are logged and skipped (see config.CONTINUE_ON_ERROR)
rather than crashing the whole run.

Usage:
    python main.py
"""

import asyncio
import sys
import time
from datetime import datetime
from pathlib import Path

import config
from modules import cleanup, media_probe, rclone_ops, telegram_uploader


def log_path():
    Path(config.LOG_DIR).mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path(config.LOG_DIR) / f"run_{stamp}.log"


class RunLogger:
    def __init__(self, path):
        self.path = path
        self._fh = open(path, "a", encoding="utf-8")

    def log(self, message: str):
        line = f"[{datetime.now().isoformat(timespec='seconds')}] {message}"
        print(line)
        self._fh.write(line + "\n")
        self._fh.flush()

    def close(self):
        self._fh.close()


def download_progress_printer(logger, filename):
    def _cb(percent, speed, eta):
        logger.log(f"  downloading {filename}: {percent}% @ {speed} ETA {eta}")
    return _cb


def upload_progress_printer(logger, filename):
    def _cb(percent, sent, total):
        logger.log(f"  uploading {filename}: {percent}% ({sent}/{total} bytes)")
    return _cb


async def process_file(client, file_info, logger):
    name = file_info["name"]
    remote_path = file_info["path"]
    local_path = None
    thumb_path = None

    try:
        logger.log(f"=== Starting: {name} ({file_info['size']} bytes) ===")

        # 1. Download
        local_path = rclone_ops.download_file(
            remote_path,
            config.DOWNLOAD_DIR,
            on_progress=download_progress_printer(logger, name),
        )
        logger.log(f"  downloaded -> {local_path}")

        # 2. Probe + thumbnail (video only)
        if media_probe.is_video(local_path):
            meta = media_probe.probe_video(local_path)
            logger.log(
                f"  video meta: duration={meta['duration']}s "
                f"{meta['width']}x{meta['height']}"
            )
            thumb_path = media_probe.generate_thumbnail(
                local_path, config.THUMBNAIL_DIR, meta["duration"]
            )
            logger.log(f"  thumbnail -> {thumb_path}")

            # 3a. Upload as streamable video
            await telegram_uploader.upload_video(
                client,
                local_path,
                duration=meta["duration"],
                width=meta["width"],
                height=meta["height"],
                thumbnail_path=thumb_path,
                caption=name,
                on_progress=upload_progress_printer(logger, name),
            )
        else:
            # 3b. Upload as plain document
            await telegram_uploader.upload_document(
                client,
                local_path,
                caption=name,
                on_progress=upload_progress_printer(logger, name),
            )

        logger.log(f"  uploaded to Telegram OK: {name}")

        # 4. Cleanup
        cleanup.remove_local_file(local_path, thumb_path)

        logger.log(f"=== Done: {name} ===\n")
        return True

    except Exception as e:
        logger.log(f"!!! FAILED: {name} -> {e}")
        # Best-effort cleanup of partial download even on failure, so
        # failed files don't pile up in DOWNLOAD_DIR.
        cleanup.remove_local_file(local_path, thumb_path)
        if not config.CONTINUE_ON_ERROR:
            raise
        return False


async def run():
    logger = RunLogger(log_path())
    logger.log("Listing files in remote folder...")

    try:
        files = rclone_ops.list_remote_files()
    except Exception as e:
        logger.log(f"Failed to list remote files: {e}")
        logger.close()
        sys.exit(1)

    if not files:
        logger.log("No files found in remote folder. Nothing to do.")
        logger.close()
        return

    logger.log(f"Found {len(files)} file(s) to process.\n")

    client = telegram_uploader.get_client()
    await client.start()

    succeeded = 0
    failed = 0
    start_time = time.time()

    async with client:
        for file_info in files:
            ok = await process_file(client, file_info, logger)
            if ok:
                succeeded += 1
            else:
                failed += 1

    elapsed = int(time.time() - start_time)
    logger.log(
        f"\nRun complete in {elapsed}s. "
        f"{succeeded} succeeded, {failed} failed, {len(files)} total."
    )
    logger.close()


if __name__ == "__main__":
    asyncio.run(run())
