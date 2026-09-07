"""
modules/telegram_uploader.py
=============================
Telethon client wrapper for uploading a single file to the configured
target channel.

- Video files: uploaded with DocumentAttributeVideo (duration, w, h,
  supports_streaming=True) + a thumbnail, so Telegram renders it as a
  playable video with a streaming button instead of a plain document.
- Everything else: uploaded as a plain document.

Both paths report live progress via a callback.
"""

import time

from telethon import TelegramClient
from telethon.sync import TelegramClient as SyncTelegramClient  # noqa: F401 (kept for clarity if extended)
from telethon.sessions import StringSession
from telethon.tl.types import DocumentAttributeVideo

import config


def get_client() -> TelegramClient:
    """Build a Telethon client from the hardcoded session string."""
    if not config.TG_SESSION_STRING:
        raise RuntimeError(
            "TG_SESSION_STRING is empty in config.py. "
            "Run generate_session.py once and paste the result into config.py."
        )
    return TelegramClient(
        StringSession(config.TG_SESSION_STRING),
        config.TG_API_ID,
        config.TG_API_HASH,
    )


def _make_progress_callback(label: str, on_progress=None):
    """
    Wraps a user-supplied on_progress(percent, sent_bytes, total_bytes)
    callback with rate-limiting, so we don't spam output on every chunk.
    """
    state = {"last_report": 0.0}

    def callback(sent_bytes, total_bytes):
        now = time.time()
        if now - state["last_report"] < config.PROGRESS_UPDATE_INTERVAL:
            return
        state["last_report"] = now
        percent = int(sent_bytes / total_bytes * 100) if total_bytes else 0
        if on_progress:
            on_progress(percent, sent_bytes, total_bytes)
        else:
            print(f"[{label}] upload progress: {percent}%")

    return callback


async def upload_video(
    client: TelegramClient,
    local_path: str,
    duration: int,
    width: int,
    height: int,
    thumbnail_path: str,
    caption: str = "",
    on_progress=None,
):
    """Upload a file as a streamable video with thumbnail."""
    attributes = [
        DocumentAttributeVideo(
            duration=duration,
            w=width,
            h=height,
            supports_streaming=True,
        )
    ]

    await client.send_file(
        config.TG_TARGET_CHANNEL,
        local_path,
        caption=caption,
        attributes=attributes,
        thumb=thumbnail_path,
        supports_streaming=True,
        progress_callback=_make_progress_callback(local_path, on_progress),
    )


async def upload_document(
    client: TelegramClient,
    local_path: str,
    caption: str = "",
    on_progress=None,
):
    """Upload a file as a plain document (non-video files)."""
    await client.send_file(
        config.TG_TARGET_CHANNEL,
        local_path,
        caption=caption,
        force_document=True,
        progress_callback=_make_progress_callback(local_path, on_progress),
    )
