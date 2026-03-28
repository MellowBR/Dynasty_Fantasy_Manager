"""
migration_add_season_flags.py — Add rookie_draft_done, auction_done,
playoffs_started flags to app_config.

Idempotent — safe to run multiple times.
Run: python migration_add_season_flags.py
"""

import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dynasty.db")

FLAGS = {
    "rookie_draft_done": "false",
    "auction_done": "false",
    "playoffs_started": "false",
}


def migrate():
    if not os.path.exists(DB_PATH):
        print(f"[migrate] DB not found: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    for key, default in FLAGS.items():
        cur.execute("SELECT value FROM app_config WHERE key = ?", (key,))
        row = cur.fetchone()
        if row:
            print(f"  {key}: already exists (value={row[0]})")
        else:
            cur.execute("INSERT INTO app_config (key, value) VALUES (?, ?)", (key, default))
            print(f"  {key}: inserted (value={default})")

    conn.commit()
    conn.close()
    print("[migrate] Done.")


if __name__ == "__main__":
    migrate()
