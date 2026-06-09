"""
import_csv.py — Import salary/contract data from dynasty_rosters_clean.csv.

Imports players WITHOUT team assignment — teams are assigned by Sleeper sync
immediately after (Sleeper is the authoritative source for who is on each team).
"""
import csv
import os
from models import db, Player, CURRENT_SEASON, get_config, set_espn_value

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "dynasty_rosters_clean.csv")


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
        # F6: "keeper" deprecated — normaliza para auction_draft no import.
        # Defesa para CSVs legacy; DBs já migrados não dependem disso
        # (guard f8_rebuilt em run_import() ignora acquisition_type).
        "keeper": "auction_draft",
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
    Import/update salary/contract data from CSV (upsert).
    - Existing players: update salary & contract fields (preserves team_id from Sleeper)
    - New players: create without team assignment
    Returns True if new players were created (meaning Sleeper sync should run).
    """
    if not os.path.exists(CSV_PATH):
        print(f"[import_csv] WARNING: {CSV_PATH} not found. Skipping import.")
        return False

    print(f"[import_csv] Importing salary/contract data from {CSV_PATH} ...")
    # F8b — post-rebuild, preserve canonical acquisition_type + contract_start_season
    # from PlayerHistory Sleeper chain. Flag set by _rebuild_player_history().
    f8_rebuilt = get_config("f8_rebuilt", "false") == "true"
    if f8_rebuilt:
        print("[import_csv] F8b guard active — skipping acquisition_type and contract_start_season on existing players")
    created = 0
    updated = 0

    # E4-b — guard contra órfãos-duplicata. Resolve nome+team → sid (Brown-safe, reusa
    # o resolver do E4-a) só no 1º create (lazy: steady-state sem creates não carrega o
    # pool de ~15MB). Falha do pool → degrada p/ needs_review.
    _resolver_cache = {}
    def _resolve_sid(name, team):
        if "fn" not in _resolver_cache:
            try:
                from routes.admin import _build_pool_index, _resolve_entry_sid
                _idx = _build_pool_index()
                _resolver_cache["fn"] = (
                    lambda nm, tm: _resolve_entry_sid({"name": nm, "nfl_team": tm}, _idx))
            except Exception:
                _resolver_cache["fn"] = lambda nm, tm: None
        return _resolver_cache["fn"](name, team)

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
            start_season = orig_season or CURRENT_SEASON - cyr + 1

            nfl_team = (row.get("nfl_team") or "").strip()
            player = Player.query.filter_by(name=player_name).first()

            # E4-b dedup: nome não casou, mas o nome+team resolve por sid p/ um Player
            # que JÁ existe (apelido/grafia divergente do Sleeper) → atualiza o canônico
            # em vez de inserir um órfão-duplicata. resolved_sid também semeia o sid de
            # um Player genuinamente novo.
            resolved_sid = None
            if player is None:
                resolved_sid = _resolve_sid(player_name, nfl_team)
                if resolved_sid:
                    from player_lookup import find_player_by_sleeper_id
                    player = find_player_by_sleeper_id(resolved_sid)

            if player:
                player.salary = salary
                player.contract_year = cyr
                if not f8_rebuilt:
                    player.contract_start_season = start_season
                    player.acquisition_type = _norm_acq(acq_raw)
                # E4-c-1: valor ESPN via fonte única (store canônico + materializa coluna)
                set_espn_value(player, CURRENT_SEASON + 1, espn)
                player.orig_draft_season = orig_season
                player.orig_draft_type = (row.get("orig_draft_type") or "").strip()
                if not player.position:
                    player.position = (row.get("position") or "").strip()
                if not player.nfl_team:
                    player.nfl_team = nfl_team
                updated += 1
            else:
                player = Player(
                    name=player_name,
                    position=(row.get("position") or "").strip(),
                    nfl_team=nfl_team,
                    salary=salary,
                    contract_year=cyr,
                    contract_start_season=start_season,
                    acquisition_type=_norm_acq(acq_raw),
                    orig_draft_season=orig_season,
                    orig_draft_type=(row.get("orig_draft_type") or "").strip(),
                    # E4-b: sid resolvido limpo → nasce com sid; senão → needs_review p/
                    # surgir no review M2 (fecha o gap: import_csv não marcava review,
                    # gerando órfão invisível quando o nome diverge do Sleeper).
                    sleeper_player_id=resolved_sid,
                    needs_review=(resolved_sid is None),
                )
                db.session.add(player)
                # E4-c-1: valor ESPN via fonte única (store + materializa coluna)
                set_espn_value(player, CURRENT_SEASON + 1, espn)
                created += 1

    db.session.commit()
    print(f"[import_csv] created={created}, updated={updated}")
    return created > 0
