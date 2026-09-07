"""
config.py
=========
ALL credentials and settings live here, hardcoded, on purpose.
Nothing is read from environment variables or prompted at runtime —
fill this file in once and `python main.py` just works.

⚠️  SECURITY NOTE
This file will contain your Telegram API ID/hash and a session string.
That session string is equivalent to your Telegram login — anyone who
has it can act as your account (read chats, send messages, etc).
Keep this repo private. Do not paste this file into public issues,
public repos, or share it with anyone.

Fill in every value marked  <<< FILL ME IN >>>  before running main.py.
"""

# ─────────────────────────────────────────────────────────────────
# TELEGRAM API CREDENTIALS
# Get these from https://my.telegram.org -> API Development Tools
# ─────────────────────────────────────────────────────────────────
TG_API_ID = 0                       # <<< FILL ME IN >>>  e.g. 12345678  (int, no quotes)
TG_API_HASH = ""                    # <<< FILL ME IN >>>  e.g. "abcd1234abcd1234abcd1234abcd1234"

# Session string produced by running generate_session.py once.
# See README.md -> "One-time session setup".
TG_SESSION_STRING = ""              # <<< FILL ME IN >>>  long string from generate_session.py

# ─────────────────────────────────────────────────────────────────
# TARGET TELEGRAM CHANNEL
# The account tied to TG_SESSION_STRING must already be a member/
# admin of this channel. Use the numeric ID (recommended, starts
# with -100 for channels) or an @username string.
# ─────────────────────────────────────────────────────────────────
TG_TARGET_CHANNEL = 0               # <<< FILL ME IN >>>  e.g. -1001234567890  OR  "@my_private_channel"

# ─────────────────────────────────────────────────────────────────
# RCLONE SETTINGS
# TG_RCLONE_REMOTE must already be configured on this machine
# (`rclone config`) and point at the Google Drive folder to pull from.
# Run `rclone listremotes` to see what's configured.
# ─────────────────────────────────────────────────────────────────
RCLONE_REMOTE = "gdrive:SomeFolder"  # <<< FILL ME IN >>>  e.g. "gdrive:Movies/ToUpload"
RCLONE_BINARY = "rclone"             # path to rclone binary, "rclone" if it's on PATH

# ─────────────────────────────────────────────────────────────────
# LOCAL PATHS
# ─────────────────────────────────────────────────────────────────
DOWNLOAD_DIR = "./downloads"         # temp holding dir for one file at a time
THUMBNAIL_DIR = "./thumbnails"       # temp thumbnails, cleaned up after each upload
LOG_DIR = "./logs"                   # run logs land here

# ─────────────────────────────────────────────────────────────────
# BEHAVIOR
# ─────────────────────────────────────────────────────────────────
# Video file extensions -> uploaded with video attributes (duration,
# width, height, thumbnail, streaming enabled). Anything else is
# uploaded as a plain document.
VIDEO_EXTENSIONS = {
    ".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v", ".flv", ".ts", ".wmv",
}

# Delete the local file (and its thumbnail) only after Telegram confirms
# the upload finished. Keep this True unless you're debugging.
DELETE_AFTER_UPLOAD = True

# If a file fails to download or upload, log it and move to the next
# file instead of stopping the whole run.
CONTINUE_ON_ERROR = True

# Progress print interval in seconds (avoid spamming console/logs on
# every single callback tick).
PROGRESS_UPDATE_INTERVAL = 2
