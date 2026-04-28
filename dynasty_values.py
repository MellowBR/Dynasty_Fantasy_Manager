"""
dynasty_values.py — FantasyCalc values integration (T2 dynasty + T3 redraft).

Fetcher com cache JSON em data/.dynasty_values_cache.json. TTL 24h.
Matching com players do DB via sleeper_player_id (100% preciso — testado).
Matching com picks via formato DP_<year_offset>_<pick_index>.

T3 (27/04/2026): payload do FantasyCalc `isDynasty=true` já retorna `redraftValue`
ao lado de `value` em cada entry — sem fetch separado. Map enriquecido com ambos
os campos; helpers `resolve_asset_value` (dynasty) e `resolve_asset_redraft_value`
(redraft) acessam cada dimensão. Picks têm `redraft_value=0` por construção (puro
futuro, sem expressão na temporada vigente).

Degradação elegante: se API cair, retorna dict vazio e UI mostra '—'.
"""

import json
import os
import re
import time
import requests
from datetime import datetime

FC_URL = "https://api.fantasycalc.com/values/current?isDynasty=true&numQbs=1&numTeams=12&ppr=1"
CACHE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", ".dynasty_values_cache.json")
CACHE_TTL_HOURS = 24
ROSTER_SIZE = 12  # trade league size — matches DP_ indexing in FantasyCalc

# Parser para nomes como "2026 Pick 1.04" usados nos entries DP_*.
_DP_NAME_RE = re.compile(r"^(\d{4})\s+Pick\s+\d+\.\d+", re.IGNORECASE)


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
    Build {sleeper_id: {value, redraft_value, name, position, overall_rank, position_rank, is_pick}}
    from raw FantasyCalc response.

    T3: `redraft_value` extraído do campo `redraftValue` (já presente no payload do
    isDynasty=true). Picks têm redraftValue=0 por convenção da API.
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
            "redraft_value": entry.get("redraftValue") or 0,
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
      {values: {sid: {value, redraft_value, name, position, overall_rank, position_rank, is_pick}},
       fetched_at: ISO,
       count: int}

    Returns FantasyCalc values map with dynasty (`value`) + redraft (`redraft_value`)
    per entry. Single fetch, single cache file — both calculadores no mesmo payload.
    Nome do helper preservado por retro-compat com T2/T2-FIX/T2-FIX-2/M1.

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


def _detect_dp_year(values_map: dict) -> int | None:
    """Identify the year covered by DP_*_* entries (the next draft).

    Scans for any DP_0_* entry and parses the year from its 'name'
    (format "YYYY Pick X.YY"). Returns None if no DP entries found or
    if names are in unexpected format — caller should fall back to FP_.
    """
    for key, entry in values_map.items():
        if not key.startswith("DP_0_"):
            continue
        name = (entry or {}).get("name") or ""
        m = _DP_NAME_RE.match(name)
        if m:
            try:
                return int(m.group(1))
            except (ValueError, TypeError):
                continue
    return None


def pick_sleeper_id(pick, current_season: int, values_map: dict | None = None) -> str | None:
    """Map a Pick object to the best-matching FantasyCalc key.

    Lookup em 3 camadas, em ordem de especificidade:
      1. DP_<round-1>_<projected_pick-1> — pick específica do draft mais
         próximo (DP). Só se pick.season == ano do DP E projected_pick > 0.
      2. FP_<season>_<round> — agregado por ano+round (formato usado para
         picks futuras e fallback quando projected_pick é desconhecido).
      3. None — nenhuma das duas keys existe no cache.

    Args:
      pick: objeto Pick com .season e .round (e opcionalmente .projected_pick).
      current_season: ano corrente do Manager (de get_current_season()).
      values_map: opcional. Se None, carrega via get_dynasty_values().

    Returns:
      String com a key (DP_* ou FP_*) que existe no values_map, ou None.
    """
    season = getattr(pick, "season", None)
    rnd = getattr(pick, "round", None)
    if season is None or rnd is None:
        return None
    if int(season) < int(current_season):
        return None  # past seasons not in FC

    if values_map is None:
        values_map = get_dynasty_values().get("values", {})
    if not values_map:
        return None

    # Tier 1: DP_<round-1>_<pp-1> quando season é do draft próximo e pp conhecido.
    pp = getattr(pick, "projected_pick", None) or 0
    if pp > 0:
        dp_year = _detect_dp_year(values_map)
        if dp_year is not None and int(season) == dp_year:
            dp_key = f"DP_{int(rnd) - 1}_{int(pp) - 1}"
            if dp_key in values_map:
                return dp_key

    # Tier 2: FP_<year>_<round> agregado.
    fp_key = f"FP_{int(season)}_{int(rnd)}"
    if fp_key in values_map:
        return fp_key

    # Tier 3: nenhuma key disponível.
    return None


def resolve_asset_value(values_map: dict, sid: str | None) -> int | None:
    """Look up dynasty value for a single sleeper_id. Returns None if not found."""
    if not sid or sid not in values_map:
        return None
    entry = values_map[sid]
    return entry.get("value")


def resolve_asset_redraft_value(values_map: dict, sid: str | None) -> int | None:
    """T3 — Look up redraft value for a single sleeper_id. Returns None if not found.

    Picks naturalmente retornam 0 (campo `redraft_value` é 0 nos PICK entries do
    FantasyCalc). Players sem cobertura redraft (raros) também retornam 0.
    Caller decide se 0 vira '—' visual ou contribui zero pra agregação.
    """
    if not sid or sid not in values_map:
        return None
    entry = values_map[sid]
    return entry.get("redraft_value", 0)
