"""
generate_session.py
====================
Run this ONCE, interactively, to log in to your Telegram account and
produce a session string. Paste the printed string into config.py as
TG_SESSION_STRING. After that, main.py never needs to log in again.

Usage:
    python generate_session.py

You'll be asked for:
  - API ID / API hash (only if not already filled in config.py)
  - Your phone number (with country code, e.g. +15551234567)
  - The login code Telegram sends you
  - Your 2FA password, if you have one enabled

Nothing here is uploaded anywhere except directly to Telegram's own
servers as part of a normal login — this is the same login flow the
official Telegram app uses.
"""

from telethon.sync import TelegramClient
from telethon.sessions import StringSession

import config


def main():
    api_id = config.TG_API_ID
    api_hash = config.TG_API_HASH

    if not api_id or not api_hash:
        print("TG_API_ID / TG_API_HASH are not set in config.py yet.")
        api_id = int(input("Enter your API ID: ").strip())
        api_hash = input("Enter your API hash: ").strip()

    print("\nStarting login flow. A code will be sent to your Telegram app.\n")

    with TelegramClient(StringSession(), api_id, api_hash) as client:
        session_string = client.session.save()

    print("\n" + "=" * 70)
    print("SUCCESS. Paste this into config.py as TG_SESSION_STRING:")
    print("=" * 70)
    print(session_string)
    print("=" * 70)
    print("\nKeep this string private — it grants full access to your account.\n")


if __name__ == "__main__":
    main()
