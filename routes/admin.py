from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, session
from flask_login import login_required
from models import (
    db, Player, Team, User, SalaryHistory, PlayerHistory, SyncLog, ESPNValue, ESPNImportLog,
    CURRENT_SEASON, get_current_season, correct_player_salary, get_config,
)
from salary_engine import apply_season_rollover, CONTRACT_LENGTH
from routes.auth import admin_required

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin")
@login_required
def admin_page():
    last_sync = SyncLog.query.order_by(SyncLog.synced_at.desc()).first()
    player_count = Player.query.filter_by(is_dropped=False).count()
    teams_count  = Team.query.count()
    playoffs = get_config("playoffs_started", "false") == "true"
    f8_rebuilt = get_config("f8_rebuilt", "false") == "true"
    from board_mirror import get_mirrored_season, build_permutation
    mirrored = get_mirrored_season()
    draft_season = get_current_season() + 1
    return render_template("admin.html",
                           last_sync=last_sync,
                           player_count=player_count,
                           teams_count=teams_count,
                           current_season=get_current_season(),
                           playoffs_started=playoffs,
                           f8_rebuilt=f8_rebuilt,
                           f8_snapshot=_snapshot_info(),
                           draft_season=draft_season,
                           board_mirrored_season=mirrored,
                           board_perm_size=len(build_permutation(draft_season)))


# ── S2-F2: espelhamento do board do Sleeper ──────────────────────────────────

@admin_bp.route("/api/admin/board_mirror", methods=["POST"])
@admin_required
def toggle_board_mirror():
    """
    Arma/desarma o desconto da permutação administrativa do board (S2).

    Armar declara: "o board do rookie draft desta draft season JÁ foi montado no
    Sleeper". Enquanto armado, o sync interpreta as picks de R1 dessa season
    descontando a permutação (ver `board_mirror.py`). O rollover desarma sozinho —
    a season guardada deixa de casar com `current_season + 1`.
    """
    from board_mirror import set_mirrored_season, build_permutation, get_mirrored_season
    data = request.get_json() or {}
    armed = bool(data.get("armed"))
    draft_season = get_current_season() + 1
    if armed:
        perm = build_permutation(draft_season)
        if not perm:
            return jsonify({
                "success": False,
                "error": f"Permutação indisponível para {draft_season}: exige lottery "
                         f"canônico e standings da season anterior, e precisa ser bijetiva."
            }), 400
        set_mirrored_season(draft_season)
    else:
        set_mirrored_season(None)
    return jsonify({"success": True,
                    "board_mirrored_season": get_mirrored_season(),
                    "draft_season": draft_season})


# ── OFF26-4 (F2): auditoria de keepers pré-leilão ────────────────────────────
#
# Gate de integridade do leilão, não conferência de cap: keeper fora do board é
# jogador leiloável. Tudo aqui é READ-ONLY ponta a ponta — a única escrita da
# seção é o `league_id` da fantasma no AppConfig (D1), feita pelo admin.

@admin_bp.route("/admin/keeper_audit")
@login_required
def keeper_audit_page():
    """Roda a auditoria e renderiza. Reexecutar = recarregar a página (o gate roda
    3× ou mais na janela de 48 h e o `draft_id` é derivado a cada execução)."""
    from keeper_audit import run_audit, get_phantom_league_id
    return render_template("keeper_audit.html",
                           report=run_audit(),
                           phantom_league_id=get_phantom_league_id())


@admin_bp.route("/api/admin/keeper_audit")
@login_required
def keeper_audit_json():
    from keeper_audit import run_audit
    return jsonify(run_audit())


@admin_bp.route("/api/admin/phantom_league", methods=["POST"])
@admin_required
def set_phantom_league():
    """D1: persiste APENAS o `league_id` (estável). O `draft_id` muda a cada RESET
    DRAFT e é derivado a cada uso — nenhuma forma de persistência é aceitável."""
    from models import set_config
    from keeper_audit import PHANTOM_LEAGUE_KEY
    data = request.get_json() or request.form or {}
    league_id = str(data.get("league_id", "")).strip()
    if league_id and not league_id.isdigit():
        return jsonify({"success": False,
                        "error": "O `league_id` do Sleeper é numérico."}), 400
    set_config(PHANTOM_LEAGUE_KEY, league_id)
    if request.is_json:
        return jsonify({"success": True, "league_id": league_id})
    flash(f"Liga fantasma: {league_id or '(vazio)'}", "success")
    return redirect(url_for("admin.keeper_audit_page"))


# ── Sleeper Sync ──────────────────────────────────────────────────────────────

@admin_bp.route("/api/admin/sync", methods=["POST"])
@login_required
def trigger_sync():
    try:
        from sync_sleeper import run_sync
        result = run_sync()
        return jsonify({"success": True, **result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@admin_bp.route("/api/admin/last_sync")
@login_required
def last_sync():
    log = SyncLog.query.order_by(SyncLog.synced_at.desc()).first()
    if log:
        return jsonify(log.to_dict())
    return jsonify({"synced_at": None, "summary": "Nenhum sync realizado"})


# ── Season Rollover ───────────────────────────────────────────────────────────

@admin_bp.route("/api/admin/rollover/preview", methods=["GET"])
@login_required
def rollover_preview():
    """Preview what season rollover will do — no DB changes."""
    next_season = get_current_season() + 1
    players = Player.query.filter_by(is_dropped=False).all()
    preview = []
    for p in players:
        new_sal, new_yr, rule = apply_season_rollover(p)
        preview.append({
            "id": p.id,
            "name": p.name,
            "position": p.position,
            "fantasy_team": p.fantasy_team_name,
            "current_salary": p.salary,
            "current_year": p.contract_year,
            "new_salary": new_sal,
            "new_year": new_yr,
            "rule": rule,
            "is_renewal": p.contract_year >= CONTRACT_LENGTH,
            "salary_delta": new_sal - p.salary,
        })
    total_current = sum(p.salary for p in players if not p.is_on_ir)
    total_next = sum(r["new_salary"] for r in preview if not Player.query.get(r["id"]).is_on_ir)
    return jsonify({
        "next_season": next_season,
        "player_count": len(preview),
        "total_current": total_current,
        "total_next": total_next,
        "renewals": len([r for r in preview if r["is_renewal"]]),
        "players": preview,
    })


# F11: a aplicação do rollover vive SOMENTE no workflow do offseason
# (POST /api/offseason/rollover, Step 4 — gated por etapas 2+3 e rollover_done,
# avança current_season na AppConfig). O admin mantém apenas o preview acima.


# ── ESPN Value Bulk Upload ────────────────────────────────────────────────────

@admin_bp.route("/api/admin/espn_bulk", methods=["POST"])
@admin_required
def espn_bulk_upload():
    """
    CSV paste or JSON list of ESPN value updates.
    Body: {csv_text: "name,espn_value\n..."} or {players: [{name, espn_value}]}
    """
    data = request.get_json() or {}
    entries = []

    if "csv_text" in data:
        import io, csv as csv_mod
        reader = csv_mod.DictReader(io.StringIO(data["csv_text"]))
        for row in reader:
            entries.append({
                "name": row.get("name", "").strip(),
                "espn_value": float(row.get("espn_value", 0) or 0),
            })
    else:
        entries = data.get("players", [])

    updated, not_found = 0, []
    for entry in entries:
        name = (entry.get("name") or "").strip()
        espn_raw = float(entry.get("espn_value", 0) or 0)
        if not name:
            continue
        from player_lookup import find_player_by_name
        from models import set_espn_value, get_current_season
        player = find_player_by_name(name)
        if player:
            set_espn_value(player, get_current_season() + 1, espn_raw * 1.2, raw=espn_raw)
            updated += 1
        else:
            not_found.append(name)

    db.session.commit()
    return jsonify({
        "updated": updated,
        "not_found": not_found[:20],
        "not_found_count": len(not_found),
    })


# ── Players needing review ────────────────────────────────────────────────────

# ── Team owner management ────────────────────────────────────────────────────

@admin_bp.route("/api/admin/teams")
@login_required
def list_teams():
    teams = Team.query.order_by(Team.name).all()
    return jsonify([t.to_dict() for t in teams])


@admin_bp.route("/api/admin/teams/<int:team_id>/owner", methods=["PATCH"])
@admin_required
def update_team_owner(team_id):
    """Manually set or update a team's owner_name."""
    team = db.get_or_404(Team, team_id)
    data = request.get_json() or {}
    owner_name = data.get("owner_name", "").strip()
    team.owner_name = owner_name or None
    db.session.commit()
    return jsonify({"success": True, "team": team.to_dict()})


# ── M12: Owner ↔ User Management ─────────────────────────────────────────────

@admin_bp.route("/admin/users")
@login_required
def admin_users_page():
    """Page for linking Google OAuth users to teams."""
    return render_template("admin_users.html")


@admin_bp.route("/api/admin/users")
@login_required
def admin_users_list():
    """Return teams with their linked user + orphan users (no team_id)."""
    teams = Team.query.order_by(Team.name).all()
    users_by_team = {}
    unlinked = []
    for u in User.query.order_by(User.id).all():
        if u.team_id:
            users_by_team[u.team_id] = u
        else:
            unlinked.append(u)

    teams_data = [{
        "team_id": t.id,
        "team_name": t.name,
        "sleeper_display_name": t.display_name,
        "sleeper_owner_name": t.owner_name,
        "sleeper_owner_avatar": t.owner_avatar,
        "sleeper_owner_id": t.sleeper_owner_id,
        "user": users_by_team[t.id].to_dict() if t.id in users_by_team else None,
    } for t in teams]

    return jsonify({
        "teams": teams_data,
        "unlinked_users": [u.to_dict() for u in unlinked],
    })


@admin_bp.route("/api/admin/users", methods=["POST"])
@admin_required
def admin_users_create():
    """Create a new user linked to a team."""
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    name = (data.get("name") or "").strip() or None
    team_id = data.get("team_id")
    is_admin = bool(data.get("is_admin", False))

    if not email:
        return jsonify({"error": "email obrigatório"}), 400

    existing = User.query.filter_by(email=email).first()
    if existing:
        return jsonify({"error": f"email já existe (id={existing.id}, team_id={existing.team_id})"}), 409

    user = User(
        email=email,
        name=name,
        team_id=int(team_id) if team_id else None,
        is_admin=is_admin,
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({"success": True, "user": user.to_dict()}), 201


@admin_bp.route("/api/admin/users/<int:user_id>", methods=["PATCH"])
@admin_required
def admin_users_update(user_id):
    """Update name, is_admin, and/or team_id of an existing user. Email is immutable."""
    user = db.get_or_404(User, user_id)
    data = request.get_json() or {}

    if "name" in data:
        user.name = (data.get("name") or "").strip() or None
    if "is_admin" in data:
        user.is_admin = bool(data["is_admin"])
    if "team_id" in data:
        user.team_id = int(data["team_id"]) if data["team_id"] else None

    db.session.commit()
    return jsonify({"success": True, "user": user.to_dict()})


@admin_bp.route("/api/admin/users/<int:user_id>", methods=["DELETE"])
@admin_required
def admin_users_delete(user_id):
    """Delete a user (unlink). The email will no longer be able to log in."""
    user = db.get_or_404(User, user_id)
    email = user.email
    db.session.delete(user)
    db.session.commit()
    return jsonify({"success": True, "deleted_email": email})


# ── S1: Trade Backfill (previous_league_id) ──────────────────────────────────

@admin_bp.route("/api/admin/sync_trades/backfill", methods=["POST"])
@admin_required
def sync_trades_backfill():
    """
    Backfill trades from the previous_league_id (last season).
    Idempotent via sleeper_transaction_id — re-calls are no-op.
    """
    from sync_sleeper import _sync_trades, _get, BASE_URL
    from models import LEAGUE_ID

    league_data = _get(f"{BASE_URL}/league/{LEAGUE_ID}")
    if not league_data:
        return jsonify({"error": "Não foi possível buscar dados da liga atual"}), 500

    prev_id = league_data.get("previous_league_id")
    if not prev_id or prev_id == "0":
        return jsonify({"error": "Liga atual não tem previous_league_id"}), 400

    prev_data = _get(f"{BASE_URL}/league/{prev_id}") or {}
    prev_season = prev_data.get("season", "?")
    try:
        prev_season_int = int(prev_data.get("season")) if prev_data.get("season") else None
    except (ValueError, TypeError):
        prev_season_int = None

    result = _sync_trades(prev_id, league_season=prev_season_int)
    result["previous_league_id"] = prev_id
    result["previous_season"] = prev_season
    return jsonify(result)


# ── F8c: PlayerHistory canonical rebuild ─────────────────────────────────────

import os as _os
import json as _json
import glob as _glob
from datetime import datetime as _datetime

_SNAPSHOT_DIR = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), "data")
_SNAPSHOT_GLOB = _os.path.join(_SNAPSHOT_DIR, ".player_history_snapshot_*.json")


def _latest_snapshot_path():
    files = sorted(_glob.glob(_SNAPSHOT_GLOB))
    return files[-1] if files else None


def _snapshot_info():
    path = _latest_snapshot_path()
    if not path:
        return {"exists": False}
    mtime = _os.path.getmtime(path)
    # M18: UTC não-ambíguo (utcfromtimestamp); template formata via macro local_dt
    # no fuso do cliente. Era fromtimestamp (hora local do servidor) + strftime.
    return {
        "exists": True,
        "path": path,
        "filename": _os.path.basename(path),
        "dt": _datetime.utcfromtimestamp(mtime),
    }


@admin_bp.route("/api/admin/player_history/rebuild", methods=["POST"])
@admin_required
def player_history_rebuild():
    """
    F8 — Rebuild PlayerHistory canonicamente via Sleeper chain.
    ?dry_run=1 → apenas simula, não grava. Idempotente via UNIQUE.
    """
    try:
        from sync_sleeper import _rebuild_player_history
        dry_run = request.args.get("dry_run") in ("1", "true", "yes")
        result = _rebuild_player_history(dry_run=dry_run)
        result["dry_run"] = dry_run
        return jsonify(result)
    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500


@admin_bp.route("/api/admin/player_history/backfill_trades", methods=["POST"])
@admin_required
def player_history_backfill_trades():
    """
    F8-GAP — Cria PlayerHistory rows para trades que existem em Trade table
    mas não têm events. Idempotente via UNIQUE.
    """
    try:
        from sync_sleeper import _backfill_missing_trade_history
        result = _backfill_missing_trade_history()
        return jsonify(result)
    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500


@admin_bp.route("/api/admin/cleanup_orphan_players", methods=["POST"])
@admin_required
def cleanup_orphan_players():
    """
    E4-b — Remove Players órfãos-duplicata do estado VIVO (prod): sem sleeper_id,
    não-rosterados (team_id NULL), não-dropados e SEM SalaryHistory/AuctionLog (sem
    valor a preservar). Remove também PlayerHistory/ESPNValue stray do órfão. Os
    canônicos (que têm sid) NUNCA entram no filtro — preservados intactos.
    Idempotente (re-rodar não acha mais candidatos). Auditável: reporta cada remoção.
    Caso conhecido (E4-b-F1): id 279 'Hollywood Brown' (dup de Marquise Brown) +
    id 280 'Cameron Ward' (dup de Cam Ward).
    """
    from models import Player, SalaryHistory, AuctionLog, PlayerHistory, ESPNValue
    candidates = Player.query.filter(
        ((Player.sleeper_player_id == None) | (Player.sleeper_player_id == "")),  # noqa: E711
        Player.team_id == None,  # noqa: E711
        Player.is_dropped == False,  # noqa: E712
    ).all()

    removed = []
    skipped = []
    for p in candidates:
        sh = SalaryHistory.query.filter_by(player_id=p.id).count()
        al = AuctionLog.query.filter_by(player_id=p.id).count()
        if sh > 0 or al > 0:
            # tem valor/histórico de contrato → NÃO é órfão descartável; não toca.
            skipped.append({"id": p.id, "name": p.name,
                            "salary_history": sh, "auction_log": al})
            continue
        ph = PlayerHistory.query.filter_by(player_id=p.id).count()
        ev = ESPNValue.query.filter_by(player_id=p.id).count()
        removed.append({"id": p.id, "name": p.name, "position": p.position,
                        "player_history_removed": ph, "espn_value_removed": ev})
        PlayerHistory.query.filter_by(player_id=p.id).delete()
        ESPNValue.query.filter_by(player_id=p.id).delete()
        db.session.delete(p)   # salary_history (vazio) cai por cascade

    db.session.commit()
    return jsonify({"removed_count": len(removed), "removed": removed,
                    "skipped_with_history": skipped})


@admin_bp.route("/api/admin/player_history/restore", methods=["POST"])
@admin_required
def player_history_restore():
    """
    F8 — Restaura o snapshot mais recente de player_history e reverte as
    correções de Player.contract_start_season + acquisition_type via
    f8_player_backup. Remove a flag f8_rebuilt.
    """
    from models import PlayerHistory, F8PlayerBackup, Player, AppConfig
    from sqlalchemy import text

    path = _latest_snapshot_path()
    if not path:
        return jsonify({"error": "Nenhum snapshot encontrado em data/"}), 404

    try:
        with open(path, encoding="utf-8") as f:
            rows = _json.load(f)

        # 1. Replace player_history
        db.session.execute(text("DELETE FROM player_history"))
        db.session.commit()
        for r in rows:
            db.session.add(PlayerHistory(
                id=r.get("id"),
                player_id=r["player_id"],
                season=r.get("season"),
                team_name=r.get("team_name") or "",
                event_type=r["event_type"],
                salary=r.get("salary") or 0.0,
                contract_year=r.get("contract_year") or 0,
                notes=r.get("notes") or "",
                sleeper_event_ref=r.get("sleeper_event_ref"),
            ))
        db.session.commit()

        # 2. Revert Player fields via f8_player_backup
        reverted = 0
        backups = F8PlayerBackup.query.all()
        for bk in backups:
            player = db.session.get(Player, bk.player_id)
            if not player:
                continue
            player.contract_start_season = bk.old_contract_start_season
            player.acquisition_type = bk.old_acquisition_type or "unknown"
            reverted += 1
        db.session.commit()

        # 3. Clear backup + flag
        db.session.execute(text("DELETE FROM f8_player_backup"))
        ac = db.session.get(AppConfig, "f8_rebuilt")
        if ac:
            db.session.delete(ac)
        db.session.commit()

        # 4. F8-RESTORE-GAP: o restore preserva Trade rows criadas após o snapshot,
        # mas o DELETE em player_history acima apaga os events correspondentes.
        # Executar backfill automaticamente para recriar os events faltantes via
        # Sleeper chain. Falha aqui NÃO reverte o restore (já foi aplicado) —
        # só reporta warning no payload.
        backfill_result = None
        backfill_error = None
        try:
            from sync_sleeper import _backfill_missing_trade_history
            backfill_result = _backfill_missing_trade_history()
        except Exception as bf_exc:
            import traceback as _tb
            backfill_error = {
                "error": str(bf_exc),
                "traceback": _tb.format_exc(),
            }

        return jsonify({
            "success": True,
            "restored_rows": len(rows),
            "players_reverted": reverted,
            "snapshot": _os.path.basename(path),
            "backfill_result": backfill_result,
            "backfill_error": backfill_error,
        })
    except Exception as e:
        db.session.rollback()
        import traceback
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500


# ── ESPN PDF Import ──────────────────────────────────────────────────────────
# E3: import é upload-only. A constante ESPN_DEFAULT_URL e o caminho de download foram
# removidos — a ESPN bloqueia o download automatizado do datacenter do Render (E1).


def _espn_review_path():
    """Caminho do estado transitório de review em diretório GRAVÁVEL.
    Usa o diretório do dynasty.db (volume persistente /data no Render), nunca a
    raiz do app (read-only em produção — E1)."""
    import os
    app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.environ.get("DYNASTY_DB", os.path.join(app_root, "dynasty.db"))
    review_dir = os.path.dirname(os.path.abspath(db_path))
    return os.path.join(review_dir, ".espn_review_pending.json")


def _build_pool_index():
    """Índice normalizado do POOL GLOBAL do Sleeper: norm_name -> [(sid, team, pos), ...].
    Fonte única da resolução por id (E2 store + E4-a matcher). Ignora DST/defesas
    (id não-numérico)."""
    from sync_sleeper import _load_players_db, _norm_name
    pool = _load_players_db() or {}
    idx = {}
    for sid, info in pool.items():
        if not str(sid).isdigit():
            continue
        fn = (info or {}).get("full_name") or \
            f"{(info or {}).get('first_name','')} {(info or {}).get('last_name','')}".strip()
        if not fn:
            continue
        idx.setdefault(_norm_name(fn), []).append(
            (str(sid), ((info or {}).get("team") or "").upper(),
             ((info or {}).get("position") or "").upper()))
    return idx


def _resolve_entry_sid(entry, idx):
    """Resolve uma entrada ESPN → sleeper_id contra o índice do pool, Brown-safe:
    nome+team como desambiguador, SEM substring/sobrenome isolado. Retorna o sid (str)
    ou None quando ambíguo (0 ou >1 candidatos sem team único). Fonte única usada pelo
    matcher (E4-a) e pelo store de rookie (E2)."""
    from sync_sleeper import _norm_name
    cands = idx.get(_norm_name(entry.get("name", "")), [])
    team = (entry.get("nfl_team") or "").upper()
    exact = [c for c in cands if c[1] == team]   # desambigua por team
    if len(exact) == 1:
        return exact[0][0]
    if len(cands) == 1:                          # nome único no pool → seguro (sem Brown)
        return cands[0][0]
    return None                                  # ambíguo → não chuta


def _classify_not_found_entry(entry, idx):
    """E5 — classifica UMA entrada not_found no seu destino REAL do confirm, read-only
    (sem escrita). Fonte ÚNICA da decisão: usada tanto pela escrita do store
    (_resolve_not_found_to_store) quanto pelo split do render (espn_review_page), para o
    texto da tela não poder divergir do que o confirm de fato faz.
    Retorna (dest, detail): dest ∈ {'store','excluded'}. Para 'store', detail = sid (str).
    Para 'excluded', detail = motivo ('kdst' | 'zero' | 'ambiguous')."""
    pos = (entry.get("position") or "").upper()
    if pos in ("K", "DST"):                       # fora do foco (REFINE) — $1
        return ("excluded", "kdst")
    if float(entry.get("espn_raw") or 0) <= 0:    # $0 inócuo → $1
        return ("excluded", "zero")
    sid = _resolve_entry_sid(entry, idx)
    if not sid:                                   # ambíguo no pool → não chuta → $1
        return ("excluded", "ambiguous")
    return ("store", sid)


def _resolve_not_found_to_store(not_found_entries, season):
    """
    E2 — resolve cada entrada not_found (skill, valor>0) para um sleeper_player_id
    contra o POOL GLOBAL do Sleeper (nome+team Brown-safe) e faz upsert no store
    RookieEspnValue. Idempotente (upsert por sleeper_id+season). NÃO cria Player; NÃO
    calcula salário. Adiciona à sessão; o chamador faz commit.
    E5: a decisão store×$1 sai do classificador único `_classify_not_found_entry`.
    Retorna {resolved, ambiguous, skipped}.
    """
    from models import upsert_rookie_espn

    idx = _build_pool_index()
    resolved = ambiguous = skipped = 0
    for e in not_found_entries:
        dest, detail = _classify_not_found_entry(e, idx)
        if dest == "excluded":
            if detail == "ambiguous":
                ambiguous += 1
            else:                                 # 'kdst' | 'zero'
                skipped += 1
            continue
        sid = detail
        team = (e.get("nfl_team") or "").upper()
        upsert_rookie_espn(season, sid, e.get("name", ""), e.get("position", ""),
                           team, float(e.get("espn_raw") or 0),
                           float(e.get("espn_adjusted") or 0))
        resolved += 1
    return {"resolved": resolved, "ambiguous": ambiguous, "skipped": skipped}


@admin_bp.route("/api/admin/capture_rookie_class", methods=["POST"])
@admin_required
def capture_rookie_class():
    """
    DP3 — CAPTURA da classe entrante (snapshot materializado, postura P3 da REFINE).
    Varre o pool global do Sleeper, aplica o critério único `is_entering_class_member`
    (D1: years_exp==0; D3: active+status 'Active'; skill) e materializa a membership
    em RookieEspnValue via upsert idempotente por (sid, season) — SEM tocar valores
    ESPN (o import ESPN é o dono desses campos; captura passa None → preservados).
    Re-executável a qualquer momento: linhas que saíram do critério desde a captura
    anterior são desmarcadas (in_class=False), não deletadas (preserva valor ESPN).
    Única superfície de escrita nova do DP3; nada de salário/contrato/roster é tocado.
    Pool indisponível → erro gracioso (sem 500). Retorna {added, updated, removed,
    total_in_class, season}.
    """
    from sync_sleeper import _load_players_db
    from models import RookieEspnValue, is_entering_class_member, upsert_rookie_espn

    data = request.get_json(silent=True) or {}
    try:
        season = int(data.get("season") or (get_current_season() + 1))
    except (TypeError, ValueError):
        season = get_current_season() + 1

    try:
        pool = _load_players_db() or {}
    except Exception:
        pool = {}
    if not pool:
        return jsonify({"error": "Pool global do Sleeper indisponível — "
                                 "tente novamente mais tarde."}), 503

    # Classe entrante do pool (sids numéricos; DST tem sid de texto e já cai fora)
    members = {}
    for sid, info in pool.items():
        if not str(sid).isdigit():
            continue
        if is_entering_class_member(info):
            members[str(sid)] = info

    existing = {r.sleeper_player_id: r for r in
                RookieEspnValue.query.filter_by(season=season).all()}

    added = updated = removed = 0
    for sid, info in members.items():
        name = (info.get("full_name") or
                f"{info.get('first_name', '')} {info.get('last_name', '')}".strip())
        pos = (info.get("position") or "").upper()
        team = (info.get("team") or "").upper()
        row = existing.get(sid)
        if row is None:
            upsert_rookie_espn(season, sid, name, pos, team, in_class=True)
            added += 1
        else:
            if not row.in_class:
                added += 1      # linha de valor pré-existente entrando na classe agora
            else:
                updated += 1    # já era membro — refresh de identidade (nome/pos/team)
            upsert_rookie_espn(season, sid, name, pos, team, in_class=True)

    # Saíram do critério desde a captura anterior (ex.: cortado + recaptura, D3)
    for sid, row in existing.items():
        if row.in_class and sid not in members:
            row.in_class = False
            removed += 1

    db.session.commit()
    total = RookieEspnValue.query.filter_by(season=season, in_class=True).count()
    return jsonify({"season": season, "added": added, "updated": updated,
                    "removed": removed, "total_in_class": total})


@admin_bp.route("/admin/espn_import", methods=["GET", "POST"])
@admin_required
def espn_import_page():
    """Form to fetch ESPN PDF and parse it."""
    last_import = ESPNImportLog.query.order_by(ESPNImportLog.imported_at.desc()).first()

    if request.method == "GET":
        return render_template("espn_import.html",
                               default_season=get_current_season() + 1,
                               last_import=last_import)

    # POST: obter PDF por upload manual, parsear, guardar p/ review.
    # E3: import é UPLOAD-ONLY. O download por URL foi removido — a ESPN bloqueia o
    # acesso automatizado a partir do datacenter do Render (E1), então em prod a URL
    # era sempre falha/ruído; o único caminho real é o upload do PDF baixado no navegador.
    season = int(request.form.get("season", get_current_season() + 1) or get_current_season() + 1)
    is_final = request.form.get("is_final") == "on"

    uploaded = request.files.get("pdf_file")
    if not (uploaded and uploaded.filename):
        flash("Forneça um arquivo PDF (upload). Baixe o PDF da ESPN no navegador e suba aqui.", "error")
        return redirect(url_for("admin.espn_import_page"))
    pdf_bytes = uploaded.read()
    source = f"upload:{uploaded.filename}"

    # Guarda anti-500 (E1): exigir um PDF de verdade. Protege o upload de arquivo
    # inválido/corrompido — sem isso, o parser não guardado estouraria PDFSyntaxError.
    if not pdf_bytes or pdf_bytes[:4] != b"%PDF":
        flash("O arquivo enviado não é um PDF válido. Baixe o PDF da ESPN no navegador "
              "e faça o upload novamente.", "error")
        return redirect(url_for("admin.espn_import_page"))

    from espn_pdf_parser import parse_pdf_bytes, match_players
    try:
        parsed = parse_pdf_bytes(pdf_bytes)
    except Exception as e:
        flash(f"Erro ao processar o PDF: {type(e).__name__}: {e}", "error")
        return redirect(url_for("admin.espn_import_page"))
    if not parsed:
        flash("Nenhum jogador encontrado no PDF. Verifique o formato.", "error")
        return redirect(url_for("admin.espn_import_page"))

    db_players = Player.query.filter_by(is_dropped=False).all()
    # E4-a: identidade resolvida por sleeper_id contra o pool global (Brown-safe), em vez
    # de fuzzy contra o roster local. Pool indisponível → idx vazio → resolver retorna
    # None p/ tudo → fallback (igualdade exata / review), degradação graciosa sem 500.
    try:
        _pool_idx = _build_pool_index()
    except Exception:
        _pool_idx = {}
    _sid_resolver = (lambda e: _resolve_entry_sid(e, _pool_idx)) if _pool_idx else None
    try:
        results = match_players(parsed, db_players, sid_resolver=_sid_resolver)
    except Exception as e:
        flash(f"Erro no matching de jogadores: {type(e).__name__}: {e}", "error")
        return redirect(url_for("admin.espn_import_page"))

    # Persistir o estado de review em diretório GRAVÁVEL (dir do dynasty.db = volume
    # persistente no Render), nunca na raiz do app (read-only em produção — E1).
    import json
    review_data = {
        "url": source,
        "season": season,
        "is_final": is_final,
        "matched": results["matched"],
        "approximate": results["approximate"],
        "not_found": results["not_found"],
        "absent": [a for a in results["absent"]],
        "total_parsed": len(parsed),
    }
    review_path = _espn_review_path()
    with open(review_path, "w", encoding="utf-8") as f:
        json.dump(review_data, f, ensure_ascii=False)
    session["espn_review_path"] = review_path

    return redirect(url_for("admin.espn_review_page"))


@admin_bp.route("/admin/espn_import/review", methods=["GET"])
@admin_required
def espn_review_page():
    """Review page showing matched, approximate, and not-found players."""
    import json, os
    review_path = session.get("espn_review_path")
    if not review_path or not os.path.exists(review_path):
        flash("Nenhuma importacao pendente. Faca o upload primeiro.", "warn")
        return redirect(url_for("admin.espn_import_page"))

    with open(review_path, encoding="utf-8") as f:
        data = json.load(f)

    # E5: split de "Não Encontrados" pelo destino REAL, computado no servidor (read-only,
    # sem escrita) reusando o classificador único do confirm. Entrantes que resolvem a sid
    # vão ao store e recebem salário projetado floor(ESPN×1.2) no draft; os demais → $1. O
    # salário projetado vem da fonte única (salary_engine.year1_salary), sem replicar a
    # conta no template/JS. Pool indisponível → tudo cai em 'excluded' (degradação igual à
    # do confirm).
    from salary_engine import year1_salary
    try:
        _idx = _build_pool_index()
    except Exception:
        _idx = {}
    nf_store, nf_excluded = [], []
    for e in data.get("not_found", []):
        dest, detail = _classify_not_found_entry(e, _idx)
        if dest == "store":
            proj = year1_salary("rookie_draft", 0, float(e.get("espn_adjusted") or 0))
            nf_store.append({**e, "projected_salary": proj})
        else:
            nf_excluded.append({**e, "excluded_reason": detail})
    data["nf_store"] = nf_store
    data["nf_excluded"] = nf_excluded
    return render_template("espn_review.html", data=data)


@admin_bp.route("/api/admin/espn_import/confirm", methods=["POST"])
@admin_required
def espn_import_confirm():
    """Confirm and save ESPN import after review."""
    import json, os
    review_path = session.get("espn_review_path")
    if not review_path or not os.path.exists(review_path):
        return jsonify({"error": "No pending import"}), 400

    with open(review_path, encoding="utf-8") as f:
        review_data = json.load(f)
    payload = request.get_json() or {}
    season = review_data["season"]
    is_final = review_data["is_final"]
    url = review_data["url"]

    # Resolved approximate matches from user: {espn_name: player_id or null}
    approx_resolved = payload.get("approximate_resolutions", {})

    total_matched = 0
    total_approx = 0
    total_notfound = 0

    # Process matched entries
    excluded = set(payload.get("excluded_ids", []))
    for entry in review_data["matched"]:
        pid = entry["player_id"]
        if pid in excluded:
            continue
        _save_espn_value(pid, season, entry["espn_raw"], entry["espn_adjusted"], is_final)
        total_matched += 1

    # Process resolved approximate matches
    for entry in review_data["approximate"]:
        espn_name = entry["name"]
        resolved_pid = approx_resolved.get(espn_name)
        if resolved_pid and resolved_pid != "skip":
            resolved_pid = int(resolved_pid)
            _save_espn_value(resolved_pid, season, entry["espn_raw"], entry["espn_adjusted"], is_final)
            total_approx += 1
        else:
            total_notfound += 1

    # E5: `total_notfound` é contador de EXIBIÇÃO ("não-encontrados"), não uma escrita de
    # $1. O destino real de cada not_found (store de rookie via floor(ESPN×1.2) vs. $1) é
    # decidido logo abaixo por _resolve_not_found_to_store; os `absent` (Players do DB fora
    # do Top-300) recebem referência $1 mais adiante, por regra de liga.
    total_notfound += len(review_data["not_found"])

    # E2: store = not_found + approximate NÃO resolvidos a um player do DB. Um rookie
    # pode cair em approximate por falso-positivo de fuzzy (ex.: "Carnell Tate" ~
    # "Darnell Mooney" sim 0.665); se o admin não confirma esse match, o valor ESPN do
    # rookie deve ir para o store (keyed por sleeper_id) em vez de se perder. Consumido
    # pelo rookie draft (OFF26-3) + board DP1. Additive/idempotente — não derruba o
    # confirm dos matched se falhar (ex.: pool indisponível).
    store_candidates = list(review_data["not_found"])
    for _a in review_data["approximate"]:
        _rp = approx_resolved.get(_a["name"])
        if not _rp or _rp == "skip":
            store_candidates.append(_a)
    try:
        store_stats = _resolve_not_found_to_store(store_candidates, season)
    except Exception:
        store_stats = {"resolved": 0, "ambiguous": 0, "skipped": 0}

    # Absent DB players → set to $1 if they have no ESPN value for this season
    for absent in review_data["absent"]:
        pid = absent["player_id"]
        _save_espn_value(pid, season, 0.0, 1.0, is_final)

    # Log the import
    log = ESPNImportLog(
        season=season,
        url_used=url,
        status="final" if is_final else "provisional",
        total_matched=total_matched,
        total_approximate=total_approx,
        total_notfound=total_notfound,
    )
    db.session.add(log)
    db.session.commit()

    # Clean up
    session.pop("espn_review_path", None)
    try:
        os.remove(review_path)
    except OSError:
        pass

    return jsonify({
        "success": True,
        "total_matched": total_matched,
        "total_approximate": total_approx,
        "total_notfound": total_notfound,
        "rookie_store": store_stats,  # E2: resolvidos p/ o store de valores de rookie
    })


def _save_espn_value(player_id: int, season: int, espn_raw: float, espn_adjusted: float, is_final: bool):
    """Save ESPN value for a player. E4-c-1: valor via fonte única set_espn_value
    (store canônico + materializa a coluna). Mantém o upsert legado em ESPNValue por ora
    (sem leitor após o repontamento da badge; removido no E4-c-2)."""
    from models import set_espn_value
    ev = ESPNValue.query.filter_by(player_id=player_id, season=season).first()
    if ev:
        ev.espn_raw = espn_raw
        ev.espn_adjusted = espn_adjusted
        ev.is_final = is_final
    else:
        ev = ESPNValue(player_id=player_id, season=season,
                       espn_raw=espn_raw, espn_adjusted=espn_adjusted, is_final=is_final)
        db.session.add(ev)

    player = Player.query.get(player_id)
    if player:
        set_espn_value(player, season, espn_adjusted, raw=espn_raw, is_final=is_final)


@admin_bp.route("/api/admin/espn_import/status")
@login_required
def espn_import_status():
    """Return info about the most recent ESPN import."""
    last = ESPNImportLog.query.order_by(ESPNImportLog.imported_at.desc()).first()
    if last:
        return jsonify(last.to_dict())
    return jsonify({"status": None})


def _categorize_review_player(player):
    """M2 — runtime categorization, no schema column.

    Cat A — Sync Sleeper unmatched: salary=$1, acquisition_type='unknown',
    espn_ref_value=0. Action: apply defaults (unknown -> free_agent) + approve.
    Cat B — everything else (auction registered manually, manual flag, etc.).
    Action: confirm or edit-then-approve.
    """
    if (player.acquisition_type == "unknown"
            and player.salary == 1.0
            and (player.espn_ref_value or 0.0) == 0.0):
        return "A"
    return "B"


@admin_bp.route("/api/admin/review_players")
@login_required
def review_players():
    players = Player.query.filter_by(needs_review=True, is_dropped=False).all()
    out = []
    for p in players:
        d = p.to_dict()
        d["category"] = _categorize_review_player(p)
        out.append(d)
    return jsonify(out)


# ── M2: Auditable review approval ─────────────────────────────────────────────
# Legacy endpoint POST /api/admin/review_players/<pid>/clear removido em M1
# (housekeeping). Único consumidor era o JS antigo de admin.html, deletado em M2.
# Caminho atual: POST /api/admin/review_players/<pid>/approve (auditável).

_REVIEW_ALLOWED_EDITS = {"salary", "acquisition_type", "contract_year"}


@admin_bp.route("/api/admin/review_players/<int:pid>/approve", methods=["POST"])
@admin_required
def approve_review(pid):
    """M2 — approve a single needs_review player with full audit trail.

    Body (all optional): {salary, acquisition_type, contract_year}
    Behavior:
      * No edits + Cat A: apply defaults (acquisition_type unknown -> free_agent)
      * No edits + Cat B: confirm without changes
      * With edits: apply each (salary via correct_player_salary helper to keep
        SalaryHistory + PlayerHistory consistent; other fields direct)
    Always: clear needs_review flag + create PlayerHistory(event_type='review_approved').
    All in one transaction.
    """
    player = db.get_or_404(Player, pid)
    if not player.needs_review:
        return jsonify({"error": "Player não está em revisão"}), 400

    data = request.get_json(silent=True) or {}
    edits = {k: v for k, v in data.items() if k in _REVIEW_ALLOWED_EDITS and v is not None}
    category = _categorize_review_player(player)
    season = int(get_config("current_season", CURRENT_SEASON))
    team_name = player.team_rel.name if player.team_rel else ""

    notes_parts = [f"Cat {category}"]

    # 1. Apply explicit edits (if any).
    if edits:
        applied = []
        if "salary" in edits:
            new_salary = float(edits["salary"])
            if new_salary != player.salary:
                # Helper updates Player.salary, latest SalaryHistory in-place,
                # and emits its own PlayerHistory(event_type='salary_correction').
                result = correct_player_salary(
                    player.id, new_salary, reason="Aprovação de revisão (M2)"
                )
                if "error" in result:
                    db.session.rollback()
                    return jsonify({"error": result["error"]}), 400
                applied.append(f"salary ${result['old_salary']:.0f}→${new_salary:.0f}")
        if "acquisition_type" in edits and edits["acquisition_type"] != player.acquisition_type:
            old = player.acquisition_type
            player.acquisition_type = edits["acquisition_type"]
            applied.append(f"acquisition_type {old}→{edits['acquisition_type']}")
        if "contract_year" in edits:
            new_yr = int(edits["contract_year"])
            if new_yr != player.contract_year:
                old = player.contract_year
                player.contract_year = new_yr
                applied.append(f"contract_year {old}→{new_yr}")
        if applied:
            notes_parts.append("edited: " + ", ".join(applied))
        else:
            notes_parts.append("confirmed without changes")
    else:
        # No explicit edits — Cat A applies defaults, Cat B confirms.
        if category == "A":
            old_type = player.acquisition_type
            player.acquisition_type = "free_agent"
            notes_parts.append(f"applied defaults (acquisition_type {old_type}→free_agent)")
        else:
            notes_parts.append("confirmed without changes")

    # 2. Clear the flag.
    player.needs_review = False

    # 3. Audit trail — always.
    db.session.add(PlayerHistory(
        player_id=player.id,
        season=season,
        team_name=team_name,
        event_type="review_approved",
        salary=player.salary,
        contract_year=player.contract_year,
        notes="; ".join(notes_parts),
    ))

    db.session.commit()
    out = player.to_dict()
    out["category"] = _categorize_review_player(player)  # post-approval (defaults applied)
    return jsonify({"success": True, "player": out, "notes": "; ".join(notes_parts)})


@admin_bp.route("/api/admin/review_players/bulk_approve_cat_a", methods=["POST"])
@admin_required
def bulk_approve_cat_a():
    """M2 — bulk approval of Cat A players with race-condition guard.

    Body: {player_ids: [int, ...]}
    Server re-validates each ID against current state. If any ID is no longer
    Cat A (or no longer needs_review), rejects the entire transaction — admin
    must reload and retry. Avoids partial application that diverges from what
    the modal showed.
    """
    data = request.get_json(silent=True) or {}
    ids = data.get("player_ids", [])
    if not isinstance(ids, list) or not ids:
        return jsonify({"error": "player_ids deve ser uma lista não-vazia"}), 400

    players = Player.query.filter(Player.id.in_(ids)).all()
    found_ids = {p.id for p in players}
    missing = [i for i in ids if i not in found_ids]
    if missing:
        return jsonify({
            "error": "Estado mudou desde a abertura do modal — recarregue a tela e tente de novo.",
            "details": f"Players não encontrados: {missing}",
        }), 409

    not_cat_a = []
    for p in players:
        if not p.needs_review or p.is_dropped or _categorize_review_player(p) != "A":
            not_cat_a.append(p.id)
    if not_cat_a:
        return jsonify({
            "error": "Estado mudou desde a abertura do modal — recarregue a tela e tente de novo.",
            "details": f"Players não são mais Cat A ou já foram aprovados: {not_cat_a}",
        }), 409

    season = int(get_config("current_season", CURRENT_SEASON))
    approved_count = 0
    for p in players:
        old_type = p.acquisition_type
        p.acquisition_type = "free_agent"
        p.needs_review = False
        team_name = p.team_rel.name if p.team_rel else ""
        db.session.add(PlayerHistory(
            player_id=p.id,
            season=season,
            team_name=team_name,
            event_type="review_approved",
            salary=p.salary,
            contract_year=p.contract_year,
            notes=f"Cat A: bulk approval, applied defaults (acquisition_type {old_type}→free_agent)",
        ))
        approved_count += 1

    db.session.commit()
    return jsonify({"success": True, "approved": approved_count})


@admin_bp.route("/admin/review")
@admin_required
def review_page():
    """M2 — dedicated review screen with Cat A / Cat B sectioning."""
    players = (Player.query
               .filter_by(needs_review=True, is_dropped=False)
               .order_by(Player.fantasy_team, Player.name)
               .all())
    cat_a = [p for p in players if _categorize_review_player(p) == "A"]
    cat_b = [p for p in players if _categorize_review_player(p) == "B"]
    return render_template("admin_review.html", cat_a=cat_a, cat_b=cat_b,
                           total=len(players))


# ── Playoffs Flag ────────────────────────────────────────────────────────────

@admin_bp.route("/api/admin/playoffs_started", methods=["POST"])
@admin_required
def toggle_playoffs():
    from models import set_config, get_config
    data = request.get_json() or {}
    undo = data.get("undo", False)
    val = "false" if undo else "true"
    set_config("playoffs_started", val)
    msg = "Playoffs revertido para temporada regular" if undo else "Playoffs iniciados"
    return jsonify({"ok": True, "key": "playoffs_started", "value": val, "message": msg})


# ── Player History Backfill ──────────────────────────────────────────────────

@admin_bp.route("/api/admin/backfill_history", methods=["POST"])
@admin_required
def backfill_history():
    """Generate initial history entries from existing player data."""
    from models import PlayerHistory
    count = _backfill_player_history()
    return jsonify({"success": True, "entries_created": count})


def _backfill_player_history():
    """
    Create history entries for players that have none.
    Reconstructs timeline from: contract_start_season, acquisition_type,
    via_trade, salary, contract_year.
    """
    from models import PlayerHistory

    players = Player.query.filter_by(is_dropped=False).all()
    created = 0

    for p in players:
        # Skip if already has history
        if PlayerHistory.query.filter_by(player_id=p.id).first():
            continue

        season = p.contract_start_season or get_current_season()
        acq = p.acquisition_type or "unknown"

        # Entry 1: original acquisition (F6: "keeper" removido do vocabulário)
        origin_event = acq if acq in (
            "rookie_draft", "auction_draft", "fa_auction"
        ) else "fa_waiver" if acq in ("waiver", "free_agent", "fa") else "unknown"

        # Calculate original salary (year 1)
        # For multi-year contracts, the current salary has been through valorization
        # We approximate year 1 salary from salary_history if available
        from models import SalaryHistory
        first_hist = SalaryHistory.query.filter_by(
            player_id=p.id, contract_year=1
        ).order_by(SalaryHistory.season).first()
        year1_salary = first_hist.salary if first_hist else p.salary

        db.session.add(PlayerHistory(
            player_id=p.id,
            season=season,
            team_name=p.fantasy_team or "",
            event_type=origin_event,
            salary=year1_salary,
            contract_year=1,
            notes=f"Contrato iniciado em {season}",
        ))
        created += 1

        # Entry 2: if via_trade, add trade event
        if p.via_trade:
            db.session.add(PlayerHistory(
                player_id=p.id,
                season=get_current_season(),
                team_name=p.fantasy_team or "",
                event_type="trade",
                salary=p.salary,
                contract_year=p.contract_year,
                notes="Trade registrada (retroativa)",
            ))
            created += 1

        # Entry 3: if contract_year > 1, add intermediate season entries
        for yr in range(2, p.contract_year + 1):
            hist = SalaryHistory.query.filter_by(
                player_id=p.id, contract_year=yr
            ).first()
            if hist:
                db.session.add(PlayerHistory(
                    player_id=p.id,
                    season=season + yr - 1,
                    team_name=p.fantasy_team or "",
                    event_type="renewal" if yr == 1 else "rollover",
                    salary=hist.salary,
                    contract_year=yr,
                    notes=hist.rule_applied or f"Ano {yr}",
                ))
                created += 1

    db.session.commit()
    return created
