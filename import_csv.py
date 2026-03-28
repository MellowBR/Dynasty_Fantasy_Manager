"""
import_csv.py — Import salary/contract data from dynasty_rosters_clean.csv.

Imports players WITHOUT team assignment — teams are assigned by Sleeper sync
immediately after (Sleeper is the authoritative source for who is on each team).
"""
import csv
import os
from models import db, Player, SalaryHistory, CURRENT_SEASON

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dynasty_rosters_clean.csv")


def _safe_float(val, default=0.0):
    try:
        s = str(val).strip()
        return float(s) if s else default
    except (ValueError, TypeError):
        return default


def _safe_int(val, default=None):
    try:
        s = str(val).strip()
        return int(float(s)) if s else default
    except (ValueError, TypeError):
        return default


def _norm_acq(raw: str) -> str:
    acq = (raw or "unknown").strip().lower()
    mapping = {
        "keeper": "keeper",
        "waiver": "waiver",
        "fa": "free_agent",
        "free_agent": "free_agent",
        "rookie_draft": "rookie_draft",
        "auction_draft": "auction_draft",
        "unknown": "unknown",
    }
    return mapping.get(acq, "unknown")


def run_import():
    """
    Import salary/contract data only. Players are left unassigned (no team).
    Returns True if new data was imported (meaning Sleeper sync should run).
    """
    if Player.query.first() is not None:
        print("[import_csv] DB already populated — skipping.")
        return False

    if not os.path.exists(CSV_PATH):
        print(f"[import_csv] WARNING: {CSV_PATH} not found. Skipping import.")
        return False

    print(f"[import_csv] Importing salary/contract data from {CSV_PATH} ...")
    players_added = 0

    with open(CSV_PATH, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            player_name = (row.get("name") or "").strip()
            if not player_name:
                continue

            acq_raw = row.get("acquisition_type", "unknown")
            salary = _safe_float(row.get("salary_2025"), 1.0)
            espn = _safe_float(row.get("espn_ref_value"), 0.0)
            cyr = _safe_int(row.get("contract_year_2025"), 1) or 1
            orig_season = _safe_int(row.get("orig_draft_season"), None)

            player = Player(
                name=player_name,
                position=(row.get("position") or "").strip(),
                nfl_team=(row.get("nfl_team") or "").strip(),
                # NO team_id / fantasy_team — Sleeper sync assigns teams
                salary=salary,
                contract_year=cyr,
                contract_start_season=(orig_season or CURRENT_SEASON - cyr + 1),
                acquisition_type=_norm_acq(acq_raw),
                espn_ref_value=espn,
                orig_draft_season=orig_season,
                orig_draft_type=(row.get("orig_draft_type") or "").strip(),
            )
            db.session.add(player)
            players_added += 1

            hist = SalaryHistory(
                player=player,
                season=CURRENT_SEASON,
                salary=salary,
                contract_year=cyr,
                rule_applied="import",
                espn_ref_value=espn,
            )
            db.session.add(hist)

    db.session.commit()
    print(f"[import_csv] {players_added} players imported (unassigned, awaiting Sleeper sync).")
    return True
