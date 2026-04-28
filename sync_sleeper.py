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

    # 12. Sync trades (S1) — completed trades from the current league
    try:
        trades_result = _sync_trades(LEAGUE_ID)
        summary["trades_imported"] = trades_result["imported"]
        summary["trades_skipped"] = trades_result["skipped"]
        if trades_result.get("warnings"):
            summary["trade_warnings"] = trades_result["warnings"]
        # M1: propagate soft-cap alerts for teams affected by trade movement
        if trades_result.get("cap_alerts"):
            summary["cap_alerts"] = trades_result["cap_alerts"]
    except Exception as e:
        summary["errors"].append(f"trade sync: {e}")
        summary["trades_imported"] = 0
        summary["trades_skipped"] = 0

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
    if "trades_imported" in summary:
        desc_parts.append(f"{summary['trades_imported']} trades novas, {summary['trades_skipped']} já sincronizadas")
    if summary.get("trade_warnings"):
        desc_parts.append(f"⚠️ {len(summary['trade_warnings'])} warning(s) em trades")
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


# ── S1: Sleeper Trade Sync ───────────────────────────────────────────────────

def _build_team_map_for_league(league_id: str) -> dict:
    """
    Build roster_id (str) → Team mapping for a given league (current or previous).
    Owners (sleeper_owner_id) are constant across seasons, so we join via owner_id.
    """
    rosters = _get(f"{BASE_URL}/league/{league_id}/rosters") or []
    teams_by_owner = {
        t.sleeper_owner_id: t
        for t in Team.query.filter(Team.sleeper_owner_id.isnot(None)).all()
    }
    team_by_roster = {}
    for r in rosters:
        rid = str(r.get("roster_id", ""))
        oid = str(r.get("owner_id", "") or "")
        team = teams_by_owner.get(oid)
        if team:
            team_by_roster[rid] = team
    return team_by_roster


def _compute_cap_alerts(affected_team_ids: set) -> list[dict]:
    """M1 — soft-cap alerts for teams affected by a trade leg.

    Computes Team.active_salary() post-movement (within current session, sees
    pending writes via autoflush). Reports any team strictly above SALARY_CAP.

    Soft-cap semantics: hard enforcement only at FA auction entry. M1 alerts,
    never blocks. Caller wraps in try/except so a failure here logs but does
    not abort the sync (Sleeper is source of truth for asset movement).

    Returns list of {"team": str, "active_salary": float, "over_by": float}.
    """
    from salary_engine import SALARY_CAP
    alerts = []
    for tid in affected_team_ids:
        team = db.session.get(Team, tid)
        if not team:
            continue
        active = team.active_salary()
        if active > SALARY_CAP:
            alerts.append({
                "team": team.name,
                "active_salary": round(active, 2),
                "over_by": round(active - SALARY_CAP, 2),
            })
    return alerts


def _sync_trades(league_id: str, league_season: int | None = None) -> dict:
    """
    Sync completed trades from a Sleeper league. Idempotent via sleeper_transaction_id.
    2-way trades: normal Trade row.
    N-way trades (N>2): placeholder Trade row with team_b="N-way: <others>", description
    prefixed "[N-WAY]". Players/picks still move correctly via adds/drops/draft_picks.
    Returns {"imported": N, "skipped": M, "warnings": [str, ...], "cap_alerts": [dict, ...]}.

    MAN-S1-FIX (cross-season guard): se a liga sendo processada pertence a uma season
    anterior à `current_season` global (caso típico: backfill de previous_league_id ou
    F8a iterando pela chain), Trade row + PlayerHistory event continuam sendo criados
    (preserva histórico canônico), mas Player.team_id/fantasy_team NÃO são mutados
    (evita sobrescrever estado pós-trades da current league). PlayerHistory.season é
    sempre a season da liga sendo processada, não `get_current_season()`.

    `league_season` pode ser passada pelo caller para evitar I/O redundante; se None,
    é derivada uma única vez via /league/{league_id}.

    M1 — cap_alerts populated post-movement, pre-commit, in try/except (failure
    logs to warnings, sync continues — soft cap, alert never blocks).
    """
    from models import Trade, PlayerHistory, get_current_season

    result = {"imported": 0, "skipped": 0, "warnings": [], "cap_alerts": []}
    affected_team_ids: set = set()
    team_by_roster = _build_team_map_for_league(league_id)
    if not team_by_roster:
        result["warnings"].append(f"Nenhum roster mapeado para liga {league_id}")
        return result

    if league_season is None:
        league_data = _get(f"{BASE_URL}/league/{league_id}") or {}
        try:
            league_season = int(league_data.get("season")) if league_data.get("season") else None
        except (ValueError, TypeError):
            league_season = None
        if league_season is None:
            result["warnings"].append(
                f"Liga {league_id}: season indisponível — guard cross-season pulado, "
                f"comportamento legado (movimentação aplicada)"
            )

    current_season = get_current_season()
    is_previous_season = (
        league_season is not None and league_season < current_season
    )

    players_by_sid = {
        p.sleeper_player_id: p
        for p in Player.query.filter(Player.sleeper_player_id.isnot(None)).all()
    }

    for leg in range(1, 19):
        txs = _get(f"{BASE_URL}/league/{league_id}/transactions/{leg}") or []
        for tx in txs:
            if tx.get("type") != "trade" or tx.get("status") != "complete":
                continue
            tx_id = tx.get("transaction_id")
            if not tx_id:
                result["warnings"].append(f"Trade sem transaction_id (leg {leg})")
                continue

            # Idempotency
            if Trade.query.filter_by(sleeper_transaction_id=tx_id).first():
                result["skipped"] += 1
                continue

            roster_ids = tx.get("roster_ids") or []
            if len(roster_ids) < 2 or not all(team_by_roster.get(str(rid)) for rid in roster_ids):
                missing = [str(rid) for rid in roster_ids if not team_by_roster.get(str(rid))]
                result["warnings"].append(f"tx={tx_id}: roster_ids não mapeados: {missing}")
                continue

            is_n_way = len(roster_ids) > 2
            adds = tx.get("adds") or {}
            drops = tx.get("drops") or {}
            flow_info = []

            # Move players via adds/drops
            for pid_str, dst_rid in adds.items():
                src_rid = drops.get(pid_str)
                player = players_by_sid.get(str(pid_str))
                dst_team = team_by_roster.get(str(dst_rid))
                src_team = team_by_roster.get(str(src_rid)) if src_rid is not None else None
                if not dst_team:
                    continue
                if not player:
                    result["warnings"].append(
                        f"tx={tx_id}: player sleeper_id={pid_str} não existe no DB (dropado?)"
                    )
                    continue

                # MAN-S1-FIX: só muta asset live se a trade pertence à current
                # league. Trades de previous leagues (backfill, F8a chain walk) só
                # geram Trade row + PH event histórico, sem sobrescrever team_id.
                if not is_previous_season:
                    player.team_id = dst_team.id
                    player.fantasy_team = dst_team.name
                    player.is_my_team = dst_team.is_my_team
                    player.via_trade = True

                    # M1: track teams whose roster changed (cap recompute target).
                    # Só dentro do guard — trade cross-season não muda cap atual.
                    affected_team_ids.add(dst_team.id)
                    if src_team:
                        affected_team_ids.add(src_team.id)

                src_name = src_team.name if src_team else "?"
                notes_prefix = "N-way trade " if is_n_way else "Trade sleeper_sync "
                db.session.add(PlayerHistory(
                    player_id=player.id,
                    season=league_season,
                    team_name=dst_team.name,
                    event_type="trade",
                    salary=player.salary,
                    contract_year=player.contract_year,
                    notes=f"{notes_prefix}tx={tx_id} ({src_name}→{dst_team.name})",
                ))
                flow_info.append(f"{player.name} ({src_name}→{dst_team.name})")

            # Move picks via draft_picks
            for p_info in tx.get("draft_picks") or []:
                p_season_raw = p_info.get("season")
                p_round = p_info.get("round")
                orig_rid = p_info.get("roster_id")
                dst_rid = p_info.get("owner_id")
                src_rid = p_info.get("previous_owner_id")
                orig_team = team_by_roster.get(str(orig_rid))
                dst_team = team_by_roster.get(str(dst_rid))
                src_team = team_by_roster.get(str(src_rid))
                if not orig_team or not dst_team:
                    result["warnings"].append(
                        f"tx={tx_id}: pick {p_season_raw} R{p_round} com teams não mapeados"
                    )
                    continue
                try:
                    p_season_int = int(p_season_raw) if p_season_raw else None
                except (ValueError, TypeError):
                    p_season_int = None
                pick = Pick.query.filter_by(
                    season=p_season_int,
                    round=p_round,
                    original_team_id=orig_team.id,
                ).first()
                if pick:
                    pick.current_team_id = dst_team.id
                    pick.current_team_name = dst_team.name
                    pick.traded_away = (dst_team.id != pick.original_team_id)
                else:
                    result["warnings"].append(
                        f"tx={tx_id}: pick {p_season_raw} R{p_round} ({orig_team.name}) não encontrada (drafada?)"
                    )
                src_name = src_team.name if src_team else orig_team.name
                flow_info.append(f"Pick {p_season_raw} Rd{p_round} ({src_name}→{dst_team.name})")

            # Build Trade row
            desc_raw = "; ".join(flow_info) if flow_info else "(sem ativos rastreáveis)"
            created_ms = tx.get("created") or 0
            trade_dt = datetime.fromtimestamp(created_ms / 1000) if created_ms else datetime.utcnow()

            team_a_obj = team_by_roster[str(roster_ids[0])]
            if is_n_way:
                others = [team_by_roster[str(rid)].name for rid in roster_ids[1:]]
                trade = Trade(
                    team_a=team_a_obj.name,
                    team_b=f"N-way: {', '.join(others)}",
                    description=f"[N-WAY] {desc_raw}",
                    source="sleeper_sync",
                    sleeper_transaction_id=tx_id,
                    trade_date=trade_dt,
                )
                result["warnings"].append(
                    f"N-way tx={tx_id} (N={len(roster_ids)}) registrada como placeholder"
                )
            else:
                team_b_obj = team_by_roster[str(roster_ids[1])]
                trade = Trade(
                    team_a=team_a_obj.name,
                    team_b=team_b_obj.name,
                    description=desc_raw,
                    source="sleeper_sync",
                    sleeper_transaction_id=tx_id,
                    trade_date=trade_dt,
                )
            db.session.add(trade)
            result["imported"] += 1

    # M1: compute cap-overrun alerts for teams whose roster changed.
    # Wrapped in try/except — soft cap, alert never blocks sync. Asset
    # movement is committed regardless of alert computation outcome.
    try:
        result["cap_alerts"] = _compute_cap_alerts(affected_team_ids)
    except Exception as e:
        result["warnings"].append(f"cap_alerts computation failed: {e}")
        result["cap_alerts"] = []

    db.session.commit()
    return result


# ── F8a: Reconstruir PlayerHistory via Sleeper chain ─────────────────────────

_ACTIVE_ACQUISITION_TYPES = {
    "auction_draft", "rookie_draft", "fa_auction",
    "fa_waiver", "free_agent", "commissioner", "trade",
}


def _walk_league_chain(start_league_id: str) -> list[dict]:
    """
    Walk previous_league_id chain until None. Returns chronological list
    (startup → current) of league info dicts.
    """
    chain = []
    lid = start_league_id
    seen = set()
    while lid and lid not in seen:
        seen.add(lid)
        data = _get(f"{BASE_URL}/league/{lid}")
        if not data:
            break
        chain.append({
            "league_id": data.get("league_id"),
            "name": data.get("name"),
            "season": data.get("season"),
            "status": data.get("status"),
            "previous_league_id": data.get("previous_league_id"),
        })
        lid = data.get("previous_league_id")
    chain.reverse()  # startup first
    return chain


def _classify_draft(draft: dict, is_first_in_chain: bool) -> str | None:
    """
    Classify a Sleeper draft into a PlayerHistory event_type.
    Returns None to skip the draft (status != complete).
    """
    if draft.get("status") != "complete":
        return None
    dtype = draft.get("type")
    settings = draft.get("settings") or {}
    rounds = settings.get("rounds") or 0
    if dtype == "linear":
        return "rookie_draft"
    if dtype == "auction":
        if rounds >= 20 and is_first_in_chain:
            return "auction_draft"  # startup auction
        return "fa_auction"
    return None


def _collect_draft_events(league_info: dict, is_first: bool,
                          team_by_roster: dict, warnings: list) -> list[dict]:
    """
    Fetch drafts + picks for a league. Returns list of event dicts.
    Each event: {sleeper_player_id, season, event_type, team_name, salary,
                 timestamp, sleeper_event_ref, notes, contract_year}.
    """
    events = []
    lid = league_info["league_id"]
    season_raw = league_info.get("season")
    try:
        season = int(season_raw) if season_raw else None
    except (ValueError, TypeError):
        season = None

    drafts = _get(f"{BASE_URL}/league/{lid}/drafts") or []
    for d in drafts:
        event_type = _classify_draft(d, is_first)
        if not event_type:
            continue
        did = d.get("draft_id")
        start_time = d.get("start_time") or 0
        picks = _get(f"{BASE_URL}/draft/{did}/picks") or []
        for pk in picks:
            sid = pk.get("player_id")
            if not sid:
                continue
            roster_id = str(pk.get("roster_id", ""))
            team = team_by_roster.get(roster_id)
            if not team:
                warnings.append(
                    f"draft {did} season {season}: roster {roster_id} não mapeado "
                    f"(player sid={sid} pick={pk.get('pick_no')})"
                )
                continue
            md = pk.get("metadata") or {}
            amount_raw = md.get("amount")
            try:
                salary = int(amount_raw) if amount_raw not in (None, "") else None
            except (ValueError, TypeError):
                salary = None
            events.append({
                "sleeper_player_id": str(sid),
                "season": season,
                "event_type": event_type,
                "team_name": team.name,
                "salary": salary,
                "timestamp": start_time,
                "sleeper_event_ref": f"draft:{did}:{pk.get('pick_no')}",
                "notes": f"{event_type} r{pk.get('round')}p{pk.get('pick_no')} (draft {did})",
            })
    return events


def _collect_transaction_events(league_id: str, season: int | None,
                                team_by_roster: dict, warnings: list) -> list[dict]:
    """
    Iterate transactions/<leg> for waiver/free_agent/commissioner events.
    Skips type=trade (delegated to _sync_trades via S1). Returns list of event dicts.
    """
    events = []
    type_map = {
        "waiver": "fa_waiver",
        "free_agent": "free_agent",
        "commissioner": "commissioner",
    }
    for leg in range(1, 19):
        txs = _get(f"{BASE_URL}/league/{league_id}/transactions/{leg}") or []
        for tx in txs:
            if tx.get("status") != "complete":
                continue
            ttype = tx.get("type")
            if ttype == "trade":
                continue  # S1 handles trades
            event_type = type_map.get(ttype)
            if not event_type:
                continue
            tx_id = tx.get("transaction_id")
            if not tx_id:
                warnings.append(f"{ttype} sem transaction_id (leg {leg})")
                continue
            created = tx.get("created") or 0
            adds = tx.get("adds") or {}
            drops = tx.get("drops") or {}
            add_sids = set(adds.keys())

            # Add events (acquisition)
            for sid, dst_rid in adds.items():
                team = team_by_roster.get(str(dst_rid))
                if not team:
                    warnings.append(
                        f"tx={tx_id} leg {leg}: roster destino {dst_rid} não mapeado (sid={sid})"
                    )
                    continue
                events.append({
                    "sleeper_player_id": str(sid),
                    "season": season,
                    "event_type": event_type,
                    "team_name": team.name,
                    "salary": None,
                    "timestamp": created,
                    "sleeper_event_ref": f"tx:{tx_id}",
                    "notes": f"{event_type} (leg {leg}, tx {tx_id})",
                })

            # Drop events (só emitimos drop se o player não está em adds
            # dentro da mesma tx — move intra-tx já é coberto pelo add)
            for sid, src_rid in drops.items():
                if sid in add_sids:
                    continue
                team = team_by_roster.get(str(src_rid))
                if not team:
                    warnings.append(
                        f"tx={tx_id} leg {leg}: roster origem {src_rid} não mapeado (sid={sid})"
                    )
                    continue
                events.append({
                    "sleeper_player_id": str(sid),
                    "season": season,
                    "event_type": "drop",
                    "team_name": team.name,
                    "salary": None,
                    "timestamp": created,
                    "sleeper_event_ref": f"tx:{tx_id}",
                    "notes": f"drop (leg {leg}, tx {tx_id})",
                })
    return events


def _snapshot_player_history(path: str) -> int:
    """Dump all PlayerHistory rows as JSON for rollback. Returns row count."""
    from models import PlayerHistory
    rows = PlayerHistory.query.all()
    data = []
    for r in rows:
        data.append({
            "id": r.id,
            "player_id": r.player_id,
            "season": r.season,
            "team_name": r.team_name,
            "event_type": r.event_type,
            "salary": r.salary,
            "contract_year": r.contract_year,
            "notes": r.notes,
            "sleeper_event_ref": r.sleeper_event_ref,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return len(data)


def _rebuild_player_history(dry_run: bool = False) -> dict:
    """
    F8a — Rebuild PlayerHistory canonicamente a partir da Sleeper chain.
    Preserva rows S1 (sleeper_event_ref LIKE 'tx:%') e rollover (LIKE 'rollover:%').
    DELETE apenas rows com sleeper_event_ref IS NULL (legacy _backfill_player_history).
    Emite eventos de drafts + transactions (exceto trade — delegado ao S1 via _sync_trades).
    Idempotente via UNIQUE uq_player_history_event.
    """
    from models import PlayerHistory, Player, F8PlayerBackup, get_current_season

    result = {
        "events_written": 0,
        "events_skipped": 0,
        "warnings": [],
        "players_corrected": 0,
        "ligas_visitadas": [],
        "snapshot_path": None,
        "deleted_legacy": 0,
    }

    chain = _walk_league_chain(LEAGUE_ID)
    if not chain:
        result["warnings"].append("Walk chain retornou vazio — abortando")
        return result
    result["ligas_visitadas"] = [c["season"] for c in chain]

    # Step 1: collect all events from chain (chronological)
    all_events = []
    for idx, league in enumerate(chain):
        is_first = (idx == 0)
        lid = league["league_id"]
        team_by_roster = _build_team_map_for_league(lid)
        if not team_by_roster:
            result["warnings"].append(
                f"Liga {league.get('name')} {league.get('season')}: nenhum roster mapeado"
            )
            continue

        # Trades via S1 (idempotente). Só executa se not dry_run.
        # MAN-S1-FIX: passar league_season para o guard cross-season de _sync_trades.
        if not dry_run:
            try:
                lid_season = int(league.get("season")) if league.get("season") else None
            except (ValueError, TypeError):
                lid_season = None
            trade_result = _sync_trades(lid, league_season=lid_season)
            result["warnings"].extend(
                f"[{league.get('season')}] {w}" for w in trade_result.get("warnings", [])
            )

        try:
            season_int = int(league.get("season")) if league.get("season") else None
        except (ValueError, TypeError):
            season_int = None

        all_events.extend(
            _collect_draft_events(league, is_first, team_by_roster, result["warnings"])
        )
        all_events.extend(
            _collect_transaction_events(lid, season_int, team_by_roster, result["warnings"])
        )

    # Step 2: resolve sid → player_id
    players_by_sid = {
        p.sleeper_player_id: p
        for p in Player.query.filter(Player.sleeper_player_id.isnot(None)).all()
    }
    players_without_sid = [
        p for p in Player.query.filter(
            (Player.sleeper_player_id.is_(None)) | (Player.sleeper_player_id == "")
        ).all()
    ]
    for p in players_without_sid:
        result["warnings"].append(
            f"Player pid={p.id} name={p.name!r}: sem sleeper_player_id — pulado"
        )

    resolved_events = []
    unresolved_sids = set()
    for ev in all_events:
        player = players_by_sid.get(ev["sleeper_player_id"])
        if not player:
            unresolved_sids.add(ev["sleeper_player_id"])
            continue
        resolved_events.append({**ev, "player_id": player.id})
    if unresolved_sids:
        sample = list(sorted(unresolved_sids))[:10]
        result["warnings"].append(
            f"{len(unresolved_sids)} sleeper_player_ids sem match no DB. "
            f"Amostra: {sample}"
        )

    # Sort chronologically for determinism
    resolved_events.sort(key=lambda e: (e["season"] or 0, e["timestamp"] or 0))

    if dry_run:
        # Count what WOULD be written without touching DB
        existing_refs = {
            (r.player_id, r.season, r.event_type, r.team_name, r.sleeper_event_ref)
            for r in PlayerHistory.query.filter(
                PlayerHistory.sleeper_event_ref.isnot(None)
            ).all()
        }
        legacy_count = db.session.execute(
            db.text("SELECT COUNT(*) FROM player_history WHERE sleeper_event_ref IS NULL")
        ).scalar()
        result["deleted_legacy"] = legacy_count
        for ev in resolved_events:
            key = (ev["player_id"], ev["season"], ev["event_type"],
                   ev["team_name"], ev["sleeper_event_ref"])
            if key in existing_refs:
                result["events_skipped"] += 1
            else:
                result["events_written"] += 1
        # Count players that would be corrected
        result["players_corrected"] = _count_players_to_correct(resolved_events, players_by_sid)
        return result

    # Step 3: snapshot before destructive ops
    snapshot_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "data",
        f".player_history_snapshot_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    )
    _snapshot_player_history(snapshot_path)
    result["snapshot_path"] = snapshot_path

    # Step 4: DELETE legacy rows (sleeper_event_ref IS NULL)
    legacy_deleted = db.session.execute(
        db.text("DELETE FROM player_history WHERE sleeper_event_ref IS NULL")
    ).rowcount
    result["deleted_legacy"] = legacy_deleted
    db.session.commit()

    # Step 5: bulk INSERT new events (idempotent via UNIQUE)
    existing_refs = {
        (r.player_id, r.season, r.event_type, r.team_name, r.sleeper_event_ref)
        for r in PlayerHistory.query.filter(
            PlayerHistory.sleeper_event_ref.isnot(None)
        ).all()
    }
    for ev in resolved_events:
        key = (ev["player_id"], ev["season"], ev["event_type"],
               ev["team_name"], ev["sleeper_event_ref"])
        if key in existing_refs:
            result["events_skipped"] += 1
            continue
        db.session.add(PlayerHistory(
            player_id=ev["player_id"],
            season=ev["season"],
            team_name=ev["team_name"],
            event_type=ev["event_type"],
            salary=ev["salary"] if ev["salary"] is not None else 0.0,
            contract_year=0,  # F8 não sabe contract_year histórico
            notes=ev["notes"],
            sleeper_event_ref=ev["sleeper_event_ref"],
        ))
        existing_refs.add(key)
        result["events_written"] += 1
    db.session.commit()

    # Step 6: reconcile Player.contract_start_season and acquisition_type
    current_season = get_current_season()
    players_corrected = 0
    by_player = {}
    for ev in resolved_events:
        if ev["event_type"] not in _ACTIVE_ACQUISITION_TYPES:
            continue
        if ev["season"] is None or ev["season"] > current_season:
            continue
        # Keep the most recent active acquisition <= current_season
        existing = by_player.get(ev["player_id"])
        if existing is None or (ev["season"], ev["timestamp"] or 0) > (existing["season"], existing["timestamp"] or 0):
            by_player[ev["player_id"]] = ev

    # Add trades from DB (S1 rows) to the candidate pool for reconciliation.
    # S1 rows live in PlayerHistory with sleeper_event_ref='tx:<id>' and event_type='trade'.
    # Use Trade.trade_date (ms epoch from Sleeper) as real timestamp for ordering.
    from models import Trade
    trade_date_by_tx = {
        t.sleeper_transaction_id: t.trade_date
        for t in Trade.query.filter(Trade.sleeper_transaction_id.isnot(None)).all()
    }
    trade_rows = PlayerHistory.query.filter(
        PlayerHistory.event_type == "trade",
        PlayerHistory.sleeper_event_ref.like("tx:%"),
    ).all()
    for tr in trade_rows:
        if tr.season is None or tr.season > current_season:
            continue
        tx_id = tr.sleeper_event_ref.split(":", 1)[1]
        trade_dt = trade_date_by_tx.get(tx_id)
        trade_ts = int(trade_dt.timestamp() * 1000) if trade_dt else 0
        candidate = {
            "player_id": tr.player_id,
            "season": tr.season,
            "event_type": "trade",
            "timestamp": trade_ts,
        }
        existing = by_player.get(tr.player_id)
        if existing is None:
            by_player[tr.player_id] = candidate
        elif (candidate["season"], candidate["timestamp"]) > (existing["season"], existing["timestamp"] or 0):
            by_player[tr.player_id] = candidate

    for player_id, ev in by_player.items():
        player = db.session.get(Player, player_id)
        if not player:
            continue
        old_css = player.contract_start_season
        old_acq = player.acquisition_type
        new_css = ev["season"]
        # Only update acquisition_type if last event is >= 2025
        # (protege year-1 rules do salary_engine para contratos vigentes).
        if ev["season"] >= 2025:
            new_acq = ev["event_type"]
        else:
            new_acq = old_acq

        if old_css == new_css and old_acq == new_acq:
            continue

        # Snapshot for rollback (only first time per player)
        if not F8PlayerBackup.query.filter_by(player_id=player_id).first():
            db.session.add(F8PlayerBackup(
                player_id=player_id,
                old_contract_start_season=old_css,
                old_acquisition_type=old_acq,
            ))
        player.contract_start_season = new_css
        player.acquisition_type = new_acq
        players_corrected += 1
    db.session.commit()
    result["players_corrected"] = players_corrected

    # F8b — mark DB as post-rebuild so run_import() stops overwriting
    # acquisition_type and contract_start_season on next boots.
    from models import set_config
    set_config("f8_rebuilt", "true")

    return result


def _backfill_missing_trade_history() -> dict:
    """
    F8-GAP — cria rows de PlayerHistory para Trade rows que existem no banco
    mas não têm eventos correspondentes.

    Situação ocorre quando, durante testes do F8c, o endpoint /restore apagou
    PlayerHistory (via snapshot pré-rebuild) mas não as Trade rows criadas pelo
    run anterior. Re-runs do _sync_trades skipam via idempotência de Trade,
    então nunca recriam os PlayerHistory events. Esta função preenche o gap.

    Percorre a Sleeper chain para localizar cada transação órfã, resolve adds
    via team map da liga correta, e cria PlayerHistory com season real (da liga
    da transação), não get_current_season().

    Idempotente via UNIQUE uq_player_history_event.
    NÃO atualiza Player.team_id/fantasy_team/via_trade — backfill retroativo
    só cria rastro histórico.

    Returns {processed, events_created, warnings, txs_not_found}.
    """
    from models import Trade, PlayerHistory, Player

    result = {
        "processed": 0,
        "events_created": 0,
        "warnings": [],
        "txs_not_found": [],
    }

    # 1. Find Trade rows without any PlayerHistory
    orphan_rows = db.session.execute(db.text("""
        SELECT t.sleeper_transaction_id
        FROM trades t
        LEFT JOIN player_history ph ON ph.sleeper_event_ref = 'tx:' || t.sleeper_transaction_id
        WHERE t.sleeper_transaction_id IS NOT NULL
        GROUP BY t.id, t.sleeper_transaction_id
        HAVING COUNT(ph.id) = 0
    """)).fetchall()
    orphan_tx_ids = {row[0] for row in orphan_rows}

    if not orphan_tx_ids:
        return result

    # 2. Walk chain and try to locate each orphan tx
    chain = _walk_league_chain(LEAGUE_ID)
    players_by_sid = {
        p.sleeper_player_id: p
        for p in Player.query.filter(Player.sleeper_player_id.isnot(None)).all()
    }

    for league in chain:
        if not orphan_tx_ids:
            break
        lid = league["league_id"]
        team_by_roster = _build_team_map_for_league(lid)
        if not team_by_roster:
            continue
        try:
            season = int(league.get("season")) if league.get("season") else None
        except (ValueError, TypeError):
            season = None

        for leg in range(1, 19):
            if not orphan_tx_ids:
                break
            txs = _get(f"{BASE_URL}/league/{lid}/transactions/{leg}") or []
            for tx in txs:
                tx_id = tx.get("transaction_id")
                if tx_id not in orphan_tx_ids:
                    continue
                if tx.get("type") != "trade" or tx.get("status") != "complete":
                    continue

                adds = tx.get("adds") or {}
                drops = tx.get("drops") or {}

                for sid, dst_rid in adds.items():
                    player = players_by_sid.get(str(sid))
                    if not player:
                        result["warnings"].append(
                            f"tx={tx_id} season={season}: sid {sid} não existe no DB"
                        )
                        continue
                    dst_team = team_by_roster.get(str(dst_rid))
                    if not dst_team:
                        continue
                    src_rid = drops.get(sid)
                    src_team = team_by_roster.get(str(src_rid)) if src_rid is not None else None
                    src_name = src_team.name if src_team else "?"

                    # Idempotency: UNIQUE (player_id, season, event_type, team_name, sleeper_event_ref)
                    existing = PlayerHistory.query.filter_by(
                        player_id=player.id,
                        season=season,
                        event_type="trade",
                        team_name=dst_team.name,
                        sleeper_event_ref=f"tx:{tx_id}",
                    ).first()
                    if existing:
                        continue

                    db.session.add(PlayerHistory(
                        player_id=player.id,
                        season=season,
                        team_name=dst_team.name,
                        event_type="trade",
                        salary=player.salary,
                        contract_year=player.contract_year,
                        notes=f"Trade sleeper_sync tx={tx_id} ({src_name}→{dst_team.name})",
                        sleeper_event_ref=f"tx:{tx_id}",
                    ))
                    result["events_created"] += 1

                result["processed"] += 1
                orphan_tx_ids.discard(tx_id)

    # Trades not located in any league of the chain (shouldn't happen, but log)
    result["txs_not_found"] = sorted(orphan_tx_ids)
    if orphan_tx_ids:
        result["warnings"].append(
            f"{len(orphan_tx_ids)} tx_ids não localizados na chain Sleeper: "
            f"{sorted(orphan_tx_ids)[:5]}"
        )

    db.session.commit()
    return result


def _count_players_to_correct(resolved_events: list, players_by_sid: dict) -> int:
    """Dry-run helper: count how many players would be corrected."""
    from models import Player, get_current_season
    current_season = get_current_season()
    by_player = {}
    for ev in resolved_events:
        if ev["event_type"] not in _ACTIVE_ACQUISITION_TYPES:
            continue
        if ev["season"] is None or ev["season"] > current_season:
            continue
        existing = by_player.get(ev["player_id"])
        if existing is None or (ev["season"], ev["timestamp"] or 0) > (existing["season"], existing["timestamp"] or 0):
            by_player[ev["player_id"]] = ev

    count = 0
    for pid, ev in by_player.items():
        p = db.session.get(Player, pid)
        if not p:
            continue
        new_css = ev["season"]
        new_acq = ev["event_type"] if ev["season"] >= 2025 else p.acquisition_type
        if p.contract_start_season != new_css or p.acquisition_type != new_acq:
            count += 1
    return count
