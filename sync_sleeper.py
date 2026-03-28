"""
sync_sleeper.py — Sleeper API sync for Dynasty SB.

Sleeper is the SOURCE OF TRUTH for who is on each team.
Local DB is the SOURCE OF TRUTH for salaries and contracts.

Flow:
  1. Fetch Sleeper player DB (cached weekly, ~5MB)
  2. Fetch league users → team display names
  3. Fetch rosters → authoritative player→team mapping
  4. Create/update teams from Sleeper roster data
  5. For each player on a Sleeper roster:
     - Match to existing DB player by sleeper_player_id or normalized name
     - Assign to correct team (Sleeper is authoritative)
     - Update name/position/nfl_team from Sleeper
     - NEVER overwrite salary/contract/acquisition_type
  6. Players on a team but NOT in that team's Sleeper roster → is_dropped=True
  7. Sync traded draft picks
"""

import json
import os
import re
import time
import requests
from datetime import datetime
from models import (db, Team, Player, Pick, SyncLog,
                    LEAGUE_ID, MY_TEAM_NAME, MY_OWNER_ID, CURRENT_SEASON)

BASE_URL = "https://api.sleeper.app/v1"
PLAYER_CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".sleeper_players_cache.json")
PLAYER_CACHE_TTL_HOURS = 168  # 1 week


def _get(url: str, timeout: int = 15) -> dict | list | None:
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        print(f"[sync] HTTP error {url}: {e}")
        return None


def _load_players_db() -> dict:
    """Load Sleeper's player DB (cached locally for 1 week)."""
    if os.path.exists(PLAYER_CACHE_FILE):
        mtime = os.path.getmtime(PLAYER_CACHE_FILE)
        age_hours = (time.time() - mtime) / 3600
        if age_hours < PLAYER_CACHE_TTL_HOURS:
            try:
                with open(PLAYER_CACHE_FILE, encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

    print("[sync] Downloading Sleeper player DB (~5MB)...")
    data = _get(f"{BASE_URL}/players/nfl")
    if data:
        try:
            with open(PLAYER_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception:
            pass
        return data
    return {}


# ── Name normalization for matching ──────────────────────────────────────────

def _norm_name(name: str) -> str:
    """Normalize a player name for fuzzy matching."""
    n = name.lower().strip()
    n = re.sub(r"[''`]", "'", n)        # normalize apostrophes
    n = re.sub(r"[.\-]", "", n)          # remove dots and hyphens
    n = re.sub(r"\s+(jr|sr|ii|iii|iv|v)$", "", n)  # remove suffixes
    n = re.sub(r"\s+", " ", n)           # collapse whitespace
    return n.strip()


# ── Main sync ────────────────────────────────────────────────────────────────

def run_sync() -> dict:
    """
    Full Sleeper sync. Returns a summary dict.
    """
    summary = {
        "players_updated": 0,
        "players_added": 0,
        "teams_updated": 0,
        "picks_updated": 0,
        "new_unknown": [],
        "errors": [],
        "timestamp": datetime.utcnow().isoformat(),
    }

    # 1. Load player DB
    players_db = _load_players_db()

    # 2. Fetch league data
    league_data = _get(f"{BASE_URL}/league/{LEAGUE_ID}")
    if not league_data:
        summary["errors"].append("Could not fetch league info")
        _log_sync(summary, had_errors=True)
        return summary

    # 3. Fetch users (team names)
    users_data = _get(f"{BASE_URL}/league/{LEAGUE_ID}/users") or []
    user_map = {}  # owner_id → {display_name, team_name}
    for u in users_data:
        uid = u.get("user_id", "")
        meta = u.get("metadata", {}) or {}
        team_name = meta.get("team_name", "") or u.get("display_name", "")
        if uid == MY_OWNER_ID:
            team_name = MY_TEAM_NAME
        user_map[uid] = {
            "display_name": u.get("display_name", ""),
            "team_name": team_name or u.get("display_name", ""),
            "avatar": u.get("avatar", "") or "",
        }

    # 4. Fetch rosters
    rosters = _get(f"{BASE_URL}/league/{LEAGUE_ID}/rosters") or []
    if not rosters:
        summary["errors"].append("Could not fetch rosters")
        _log_sync(summary, had_errors=True)
        return summary

    # 5. Sync teams — create/update from Sleeper data
    teams_by_roster: dict[str, Team] = {
        t.sleeper_roster_id: t
        for t in Team.query.filter(Team.sleeper_roster_id.isnot(None)).all()
    }

    for roster in rosters:
        rid = str(roster.get("roster_id", ""))
        oid = str(roster.get("owner_id", "") or "")
        user_info = user_map.get(oid, {})
        team_name = user_info.get("team_name", "") or f"Team {rid}"
        if oid == MY_OWNER_ID:
            team_name = MY_TEAM_NAME

        owner_display = user_info.get("display_name", "")
        owner_avatar = user_info.get("avatar", "")

        team = teams_by_roster.get(rid)
        if team:
            if team.name != team_name and oid != MY_OWNER_ID:
                old_name = team.name
                team.name = team_name
                team.display_name = team_name
                # Cascade: update fantasy_team on all players of this team
                Player.query.filter_by(team_id=team.id).update(
                    {"fantasy_team": team_name}, synchronize_session="fetch")
                summary.setdefault("names_changed", []).append(
                    f"{old_name} -> {team_name}")
            team.sleeper_owner_id = oid
            team.owner_name = owner_display
            if owner_avatar:
                team.owner_avatar = owner_avatar
            team.is_my_team = (oid == MY_OWNER_ID)
        else:
            team = Team(
                name=team_name,
                display_name=team_name,
                sleeper_roster_id=rid,
                sleeper_owner_id=oid,
                owner_name=owner_display,
                owner_avatar=owner_avatar or None,
                is_my_team=(oid == MY_OWNER_ID),
            )
            db.session.add(team)
            db.session.flush()
            teams_by_roster[rid] = team

        summary["teams_updated"] += 1

    db.session.flush()

    # 6. Build player indexes for matching
    # Index by sleeper_player_id (for previously synced players)
    players_by_sid: dict[str, Player] = {}
    # Index by normalized name (for CSV-imported players without sleeper_player_id)
    players_by_norm_name: dict[str, Player] = {}

    for p in Player.query.all():
        if p.sleeper_player_id:
            players_by_sid[p.sleeper_player_id] = p
        else:
            nn = _norm_name(p.name)
            # If multiple players share same normalized name, keep first (avoid overwrite)
            if nn not in players_by_norm_name:
                players_by_norm_name[nn] = p

    # Track which sleeper IDs belong to each team (for drop logic)
    team_assigned_sids: dict[int, set] = {}

    # 7. Sync players per roster
    for roster in rosters:
        rid = str(roster.get("roster_id", ""))
        team = teams_by_roster.get(rid)
        if not team:
            continue

        player_ids = roster.get("players") or []
        ir_ids = set(str(x) for x in (roster.get("reserve") or []))

        if team.id not in team_assigned_sids:
            team_assigned_sids[team.id] = set()

        for sp_id in player_ids:
            sp_id_str = str(sp_id)
            sp_info = players_db.get(sp_id_str, {})
            full_name = (
                sp_info.get("full_name")
                or f"{sp_info.get('first_name', '')} {sp_info.get('last_name', '')}".strip()
                or str(sp_id)
            )
            position = sp_info.get("position", "")
            nfl_team = sp_info.get("team", "")

            # --- Find existing player ---
            p = players_by_sid.get(sp_id_str)

            if not p:
                # Try matching by normalized name (CSV imports)
                nn = _norm_name(full_name)
                p = players_by_norm_name.pop(nn, None)

                # NOTE: Last-name fallback was REMOVED here.
                # It caused the "3 Browns" bug where Marquise Brown,
                # A.J. Brown, and Amon-Ra St. Brown had their salaries
                # swapped because all matched on surname "Brown" + WR.
                # Now unmatched players are logged and added as new.

                if p:
                    # Link this CSV player to Sleeper ID
                    p.sleeper_player_id = sp_id_str
                    players_by_sid[sp_id_str] = p

            if p:
                # Update mutable fields (NEVER salary/contract/acquisition_type)
                if full_name and p.name != full_name:
                    p.name = full_name
                if position and p.position != position:
                    p.position = position
                if nfl_team and p.nfl_team != nfl_team:
                    p.nfl_team = nfl_team

                # Assign to correct team
                if p.team_id != team.id:
                    p.team_id = team.id
                    p.fantasy_team = team.name
                    p.is_my_team = team.is_my_team
                    summary["players_updated"] += 1

                p.is_on_ir = sp_id_str in ir_ids
                p.is_dropped = False  # back on a roster = not dropped

            else:
                # New player not in local DB — create with defaults
                p = Player(
                    sleeper_player_id=sp_id_str,
                    name=full_name,
                    position=position,
                    nfl_team=nfl_team,
                    team_id=team.id,
                    fantasy_team=team.name,
                    salary=1.0,
                    contract_year=1,
                    contract_start_season=CURRENT_SEASON,
                    acquisition_type="unknown",
                    espn_ref_value=0.0,
                    is_on_ir=(sp_id_str in ir_ids),
                    is_my_team=team.is_my_team,
                    needs_review=True,
                )
                db.session.add(p)
                db.session.flush()
                players_by_sid[sp_id_str] = p
                summary["players_added"] += 1
                summary["new_unknown"].append({"name": full_name, "team": team.name})

            team_assigned_sids[team.id].add(sp_id_str)

    # 8. Drop logic: players assigned to a team but NOT in that team's Sleeper roster
    for team_id, assigned_sids in team_assigned_sids.items():
        team_players = Player.query.filter_by(team_id=team_id, is_dropped=False).all()
        for p in team_players:
            if not p.sleeper_player_id or p.sleeper_player_id not in assigned_sids:
                p.is_dropped = True

    # 9. Fetch traded picks and derive active seasons
    traded_picks = _get(f"{BASE_URL}/league/{LEAGUE_ID}/traded_picks") or []
    traded_seasons = set(str(tp.get("season", "")) for tp in traded_picks)

    # 10. Ensure default picks exist (only for future seasons)
    _ensure_default_picks(list(teams_by_roster.values()), traded_seasons)

    # 11. Sync traded picks (overrides default ownership)
    summary["picks_updated"] = _sync_traded_picks(traded_picks, teams_by_roster)

    db.session.commit()
    _log_sync(summary, had_errors=bool(summary["errors"]))
    return summary


PICK_ROUNDS = [1, 2, 3]
MAX_FUTURE_YEARS = 3  # create picks up to 3 years ahead


def _ensure_default_picks(teams: list, traded_seasons: set):
    """
    Create default picks for seasons that Sleeper still tracks.
    Uses traded_seasons from the API as the source of truth for which seasons
    are active. Falls back to current_year .. current_year+MAX_FUTURE_YEARS.
    Also removes picks for past seasons no longer in Sleeper.
    """
    current_year = datetime.now().year

    if traded_seasons:
        active_seasons = sorted(int(s) for s in traded_seasons if s.isdigit())
    else:
        active_seasons = list(range(current_year, current_year + MAX_FUTURE_YEARS + 1))

    # Remove picks for past seasons (drafts already completed)
    past_deleted = Pick.query.filter(Pick.season < current_year).delete()
    if past_deleted:
        print(f"[sync] Removed {past_deleted} picks from past seasons")

    # Create missing picks for active seasons
    existing = set()
    for p in Pick.query.all():
        existing.add((p.season, p.round, p.original_team_name))

    added = 0
    for season in active_seasons:
        for rnd in PICK_ROUNDS:
            for team in teams:
                key = (season, rnd, team.name)
                if key not in existing:
                    pick = Pick(
                        season=season,
                        round=rnd,
                        original_team_id=team.id,
                        current_team_id=team.id,
                        original_team_name=team.name,
                        current_team_name=team.name,
                        traded_away=False,
                    )
                    db.session.add(pick)
                    added += 1
    if added:
        db.session.flush()
        print(f"[sync] Created {added} default picks for seasons {active_seasons}")


def _sync_traded_picks(traded_picks: list, teams_by_roster: dict) -> int:
    updated = 0
    for tp in traded_picks:
        season = tp.get("season")
        round_num = tp.get("round")
        owner_rid = str(tp.get("owner_id", "") or "")
        roster_id = str(tp.get("roster_id", "") or "")  # original owner

        orig_team = teams_by_roster.get(roster_id)
        cur_team = teams_by_roster.get(owner_rid)

        if not orig_team or not cur_team or not season or not round_num:
            continue

        pick = Pick.query.filter_by(
            season=season,
            round=round_num,
            original_team_name=orig_team.name,
        ).first()

        if pick:
            pick.current_team_id = cur_team.id
            pick.current_team_name = cur_team.name
            pick.traded_away = (cur_team.id != pick.original_team_id)
        else:
            pick = Pick(
                season=season,
                round=round_num,
                original_team_id=orig_team.id,
                current_team_id=cur_team.id,
                original_team_name=orig_team.name,
                current_team_name=cur_team.name,
                traded_away=(cur_team.id != orig_team.id),
            )
            db.session.add(pick)
        updated += 1

    return updated


def _log_sync(summary: dict, had_errors: bool = False):
    new_names = ", ".join(p["name"] for p in summary.get("new_unknown", [])[:5])
    more = len(summary.get("new_unknown", [])) - 5
    extra = f" (+{more} mais)" if more > 0 else ""
    desc_parts = [
        f"{summary['players_updated']} jogadores atualizados",
        f"{summary['players_added']} novos",
        f"{summary['teams_updated']} times",
        f"{summary['picks_updated']} picks",
    ]
    if new_names:
        desc_parts.append(f"Needs review: {new_names}{extra}")
    if summary.get("errors"):
        desc_parts.append(f"Erros: {'; '.join(summary['errors'][:3])}")

    log = SyncLog(
        players_updated=summary["players_updated"],
        players_added=summary["players_added"],
        teams_updated=summary["teams_updated"],
        picks_updated=summary["picks_updated"],
        summary=". ".join(desc_parts),
        had_errors=had_errors,
    )
    db.session.add(log)
    db.session.commit()
