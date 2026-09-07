# gdrive-to-telegram

Downloads every file in a Google Drive folder (via `rclone`) one at a
time, uploads each to a private Telegram channel (via Telethon — user
account API, not a bot), and deletes the local copy after a confirmed
upload. Videos are uploaded as streamable videos with a thumbnail;
everything else is uploaded as a plain document. Runs once through the
current file list, then exits.

All credentials are hardcoded in `config.py` — no environment
variables, no runtime prompts. Fill it in once, then `python main.py`
just works.

⚠️ **This repo contains real Telegram API credentials and a session
string once configured.** That session string is equivalent to your
Telegram login. Keep this repo **private**. Never share `config.py` or
push it anywhere public.

---

## Prerequisites

- Python 3.11+
- [`rclone`](https://rclone.org/downloads/) installed and on `PATH`
- `ffmpeg` + `ffprobe` installed and on `PATH`
  (`sudo apt install ffmpeg` / `brew install ffmpeg`)
- An `rclone` remote already configured for your Google Drive folder
  (`rclone config` — see [rclone's Google Drive docs](https://rclone.org/drive/)).
  Run `rclone listremotes` to confirm the remote name.
- A Telegram account that is already a member/admin of the target
  private channel.
- API ID + API hash from **https://my.telegram.org** → API Development Tools.

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Fill in `config.py`

Open `config.py` and fill in every value marked `<<< FILL ME IN >>>`:

- `TG_API_ID`, `TG_API_HASH` — from my.telegram.org
- `TG_TARGET_CHANNEL` — numeric channel ID (e.g. `-1001234567890`) or `@username`
- `RCLONE_REMOTE` — your configured rclone remote + folder, e.g. `gdrive:Movies/ToUpload`

Leave `TG_SESSION_STRING` empty for now — the next step generates it.

### 3. One-time session setup

Run this once, interactively:

```bash
python generate_session.py
```

You'll be prompted for your phone number, the login code Telegram
sends you, and your 2FA password if you have one. At the end it
prints a long session string — copy it into `config.py` as
`TG_SESSION_STRING`.

After this step, `main.py` never needs to log in interactively again.

### 4. Run

```bash
python main.py
```

It will:
1. List every file in `RCLONE_REMOTE`.
2. For each file, in order: download with live progress → probe/thumbnail
   if it's a video → upload with live progress → delete the local copy.
3. Print a summary at the end and write a timestamped log to `logs/`.

---

## Configuration reference (`config.py`)

| Setting | Meaning |
|---|---|
| `TG_API_ID` / `TG_API_HASH` | Telegram API credentials from my.telegram.org |
| `TG_SESSION_STRING` | Produced by `generate_session.py` |
| `TG_TARGET_CHANNEL` | Where files get uploaded |
| `RCLONE_REMOTE` | Source Drive folder, e.g. `gdrive:Folder` |
| `RCLONE_BINARY` | Path to rclone binary, default `"rclone"` |
| `DOWNLOAD_DIR` | Temp dir for the file currently being processed |
| `THUMBNAIL_DIR` | Temp dir for generated video thumbnails |
| `LOG_DIR` | Where run logs are written |
| `VIDEO_EXTENSIONS` | Extensions treated as video (streaming upload) vs document |
| `DELETE_AFTER_UPLOAD` | Set `False` to keep local files for debugging |
| `CONTINUE_ON_ERROR` | Set `False` to stop the whole run on first failure |
| `PROGRESS_UPDATE_INTERVAL` | Seconds between progress log lines |

## Repo structure

```
gdrive-to-telegram/
├── config.py                # all credentials + settings (fill in once)
├── generate_session.py      # one-time interactive login -> session string
├── requirements.txt
├── main.py                  # orchestrator: list -> download -> probe -> upload -> delete, per file
├── modules/
│   ├── rclone_ops.py         # rclone lsjson + rclone copy -P with progress parsing
│   ├── media_probe.py        # ffprobe duration/resolution + ffmpeg thumbnail
│   ├── telegram_uploader.py  # Telethon send_file: video (streaming+thumb) vs document, with progress
│   └── cleanup.py            # deletes local file/thumbnail after confirmed upload
├── logs/                     # one timestamped log file per run
└── README.md
```

## Notes / caveats

- **User account, not a bot.** This uses your personal Telegram
  account via the API (not `@BotFather`). This is required for
  reliable large-file uploads (bots are capped at 50MB; user accounts
  support up to ~2-4GB depending on your account). It means the
  script posts to the channel *as you*.
- **One file at a time, sequential.** By design — matches "download,
  upload, delete, repeat" rather than parallel transfers.
- **Non-video files** (pdf, zip, images, etc.) are uploaded as plain
  Telegram documents — no thumbnail/streaming attributes apply to them.
- **Re-running** the script will re-download and re-upload every file
  currently in the remote folder — it does not track what's already
  been uploaded in a previous run. If you need "only new files since
  last run," that's a straightforward addition (e.g. a local
  `uploaded.json` manifest) — not included here since you asked for
  "run once and exit" over "continuous watch."
