"""startup_check.py — Verify database files exist before app starts."""
import os
import sys


def check_databases():
    db_path = os.environ.get("DYNASTY_DB", os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "dynasty.db"))

    if not os.path.exists(db_path):
        print(f"[startup_check] WARNING: dynasty.db not found at {db_path}")
        print("[startup_check] The app will create an empty database on first run.")
        return False

    size_kb = os.path.getsize(db_path) / 1024
    print(f"[startup_check] dynasty.db OK ({size_kb:.0f} KB) at {db_path}")
    return True


if __name__ == "__main__":
    ok = check_databases()
    sys.exit(0 if ok else 1)
