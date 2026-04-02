"""
init_data.py — Copy seed database to /data/ on first Render deploy.

Only copies if /data/ exists (Render environment) and the target file
doesn't already exist (preserves production data on redeploys).
"""
import os
import shutil

DATA_DIR = "/data"
SEED_DB = "dynasty.db"


def init_data():
    if not os.path.isdir(DATA_DIR):
        print("[init_data] /data/ not found — local environment, skipping.")
        return

    repo_root = os.path.dirname(os.path.abspath(__file__))
    destino = os.path.join(DATA_DIR, SEED_DB)
    origem = os.path.join(repo_root, SEED_DB)

    if os.path.isfile(destino):
        size_kb = os.path.getsize(destino) / 1024
        print(f"[init_data] {SEED_DB} already exists in /data/ ({size_kb:.0f} KB) — keeping.")
    elif os.path.isfile(origem):
        shutil.copy2(origem, destino)
        size_kb = os.path.getsize(destino) / 1024
        print(f"[init_data] Copied {SEED_DB} to /data/ ({size_kb:.0f} KB)")
    else:
        print(f"[init_data] WARNING: {SEED_DB} not found in repo at {origem}")


if __name__ == "__main__":
    init_data()
