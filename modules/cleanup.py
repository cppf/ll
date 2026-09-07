"""
modules/cleanup.py
===================
Deletes local files after a confirmed successful upload. Kept as its
own tiny module so main.py never calls os.remove directly — makes it
obvious where "delete the user's file" happens, and easy to disable
via config.DELETE_AFTER_UPLOAD for debugging.
"""

from pathlib import Path

import config


def remove_local_file(*paths: str):
    """
    Delete one or more local files if they exist. Silently skips paths
    that don't exist (e.g. a video with no thumbnail generated) and
    respects config.DELETE_AFTER_UPLOAD as a global safety switch.
    """
    if not config.DELETE_AFTER_UPLOAD:
        print("  (DELETE_AFTER_UPLOAD is False — leaving local files in place)")
        return

    for path in paths:
        if not path:
            continue
        p = Path(path)
        if p.exists():
            p.unlink()
            print(f"  deleted local: {path}")
