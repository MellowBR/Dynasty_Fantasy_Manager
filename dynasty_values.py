"""
dynasty_values.py — FantasyCalc dynasty values integration (T2).

Fetcher com cache JSON em data/.dynasty_values_cache.json. TTL 24h.
Matching com players do DB via sleeper_player_id (100% preciso — testado).
Matching com picks via formato DP_<year_offset>_<pick_index>.

Degradação elegante: se API cair, retorna dict vazio e UI mostra '—'.
"""

import json
import os
import time
import requests
from datetime import datetime

FC_URL = "https://api.fantasycalc.com/values/current?isDynasty=true&numQbs=1&numTeams=12&ppr=1"
CACHE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", ".dynasty_values_cache.json")
CACHE_TTL_HOURS = 24
ROSTER_SIZE = 12  # trade league size — matches DP_ indexing in FantasyCalc


def _fetch_fantasycalc_values() -> dict | None:
    """
    Fetch raw JSON from FantasyCalc. Returns list of entries or None on failure.
    """
    try:
        r = requests.get(FC_URL, timeout=20)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"[dynasty_values] fetch failed: {e}")
        return None


def _build_map_from_raw(raw: list) -> dict:
    """
    Build {sleeper_id: {value, name, position, overall_rank, position_rank, is_pick}}
    from raw FantasyCalc response.
    """
    values = {}
    for entry in raw:
        player = entry.get("player") or {}
        sid = player.get("sleeperId")
        if not sid:
            continue
        # Se o mesmo sid aparece 2x (FC tem duplicatas em alguns picks), fica com o de maior rank.
        existing = values.get(sid)
        if existing and existing.get("overall_rank", 10**9) <= entry.get("overallRank", 10**9):
            continue
        values[sid] = {
            "value": entry.get("value") or 0,
            "name": player.get("name") or "",
            "position": player.get("position") or "",
            "overall_rank": entry.get("overallRank"),
            "position_rank": entry.get("positionRank"),
            "is_pick": player.get("position") == "PICK",
        }
    return values


def _load_cache() -> dict | None:
    if not os.path.exists(CACHE_PATH):
        return None
    try:
        with open(CACHE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _save_cache(payload: dict) -> None:
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)


def _cache_age_hours(cache: dict) -> float:
    ts = cache.get("fetched_at")
    if not ts:
        return float("inf")
    try:
        dt = datetime.fromisoformat(ts)
    except Exception:
        return float("inf")
    return (datetime.utcnow() - dt).total_seconds() / 3600


def get_dynasty_values(force_refresh: bool = False) -> dict:
    """
    Public accessor — returns cached payload dict:
      {values: {sid: {value, name, position, overall_rank, position_rank, is_pick}},
       fetched_at: ISO,
       count: int}

    If cache is stale (>24h) or missing, refetches. On fetch failure, returns
    stale cache (if any) or {values: {}, fetched_at: None, count: 0}.
    """
    cache = _load_cache()
    if not force_refresh and cache and _cache_age_hours(cache) < CACHE_TTL_HOURS:
        return cache

    raw = _fetch_fantasycalc_values()
    if raw is None:
        # Fall back to stale cache if we have one
        if cache:
            return cache
        return {"values": {}, "fetched_at": None, "count": 0}

    values = _build_map_from_raw(raw)
    payload = {
        "values": values,
        "fetched_at": datetime.utcnow().isoformat(),
        "count": len(values),
    }
    try:
        _save_cache(payload)
    except Exception as e:
        print(f"[dynasty_values] cache write failed: {e}")
    return payload


def pick_sleeper_id(pick, current_season: int) -> str | None:
    """
    Convert a Pick object into a FantasyCalc DP_<year_offset>_<pick_index> id.

    pick_index = (round - 1) * ROSTER_SIZE + (projected_pick - 1)
    If projected_pick is None/0: use middle of the round as conservative estimate
    (pick_index = (round - 1) * ROSTER_SIZE + 5).

    Returns None if pick.season or pick.round is missing.
    """
    season = getattr(pick, "season", None)
    rnd = getattr(pick, "round", None)
    if season is None or rnd is None:
        return None
    year_offset = int(season) - int(current_season)
    if year_offset < 0:
        return None  # past seasons not in FC

    pp = getattr(pick, "projected_pick", None) or 0
    if pp > 0:
        pick_index = (int(rnd) - 1) * ROSTER_SIZE + (int(pp) - 1)
    else:
        pick_index = (int(rnd) - 1) * ROSTER_SIZE + 5  # middle-of-round fallback
    return f"DP_{year_offset}_{pick_index}"


def resolve_asset_value(values_map: dict, sid: str | None) -> int | None:
    """Look up value for a single sleeper_id. Returns None if not found."""
    if not sid or sid not in values_map:
        return None
    entry = values_map[sid]
    return entry.get("value")
