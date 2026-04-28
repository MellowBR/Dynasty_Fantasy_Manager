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
    return render_template("admin.html",
                           last_sync=last_sync,
                           player_count=player_count,
                           teams_count=teams_count,
                           current_season=get_current_season(),
                           playoffs_started=playoffs,
                           f8_rebuilt=f8_rebuilt,
                           f8_snapshot=_snapshot_info())


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


@admin_bp.route("/api/admin/rollover/apply", methods=["POST"])
@admin_required
def rollover_apply():
    """Apply season rollover: increment year, recalc salaries, log history."""
    next_season = get_current_season() + 1
    players = Player.query.filter_by(is_dropped=False).all()
    applied = 0
    renewals = 0

    for p in players:
        old_salary = p.salary
        old_year   = p.contract_year
        new_sal, new_yr, rule = apply_season_rollover(p)

        p.salary = new_sal
        p.contract_year = new_yr
        if new_yr == 1:
            p.contract_start_season = next_season
            renewals += 1

        hist = SalaryHistory(
            player_id=p.id,
            season=next_season,
            salary=new_sal,
            contract_year=new_yr,
            rule_applied=rule,
            espn_ref_value=p.espn_ref_value or 0.0,
        )
        db.session.add(hist)
        applied += 1

    db.session.commit()

    # NOTE: CURRENT_SEASON in models is a constant — in production you'd persist
    # this in a Settings table. For now, document the rollover in SyncLog.
    from models import SyncLog
    log = SyncLog(
        players_updated=applied,
        summary=f"Season rollover {get_current_season()}→{next_season}: {applied} jogadores, {renewals} renovações.",
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({
        "success": True,
        "applied": applied,
        "renewals": renewals,
        "next_season": next_season,
    })


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
        player = find_player_by_name(name)
        if player:
            player.espn_ref_value = espn_raw * 1.2
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
    dt = _datetime.fromtimestamp(mtime)
    return {
        "exists": True,
        "path": path,
        "filename": _os.path.basename(path),
        "timestamp": dt.strftime("%d/%m/%Y %H:%M"),
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

ESPN_DEFAULT_URL = "https://g.espncdn.com/s/ffldraftkit/25/NFL25_CS_PPR300.pdf?adddata=2025CS_PPR300"


@admin_bp.route("/admin/espn_import", methods=["GET", "POST"])
@admin_required
def espn_import_page():
    """Form to fetch ESPN PDF and parse it."""
    last_import = ESPNImportLog.query.order_by(ESPNImportLog.imported_at.desc()).first()

    if request.method == "GET":
        return render_template("espn_import.html",
                               default_url=ESPN_DEFAULT_URL,
                               default_season=get_current_season() + 1,
                               last_import=last_import)

    # POST: fetch PDF, parse, store in session for review
    url = request.form.get("url", ESPN_DEFAULT_URL).strip()
    season = int(request.form.get("season", get_current_season() + 1) or get_current_season() + 1)
    is_final = request.form.get("is_final") == "on"

    import requests as req
    try:
        r = req.get(url, timeout=30)
        r.raise_for_status()
        pdf_bytes = r.content
    except Exception as e:
        flash(f"Erro ao baixar PDF: {e}", "error")
        return redirect(url_for("admin.espn_import_page"))

    from espn_pdf_parser import parse_pdf_bytes, match_players

    parsed = parse_pdf_bytes(pdf_bytes)
    if not parsed:
        flash("Nenhum jogador encontrado no PDF. Verifique o formato.", "error")
        return redirect(url_for("admin.espn_import_page"))

    db_players = Player.query.filter_by(is_dropped=False).all()
    results = match_players(parsed, db_players)

    # Store review data in a temp file (too large for session cookie)
    import json, os, tempfile
    review_data = {
        "url": url,
        "season": season,
        "is_final": is_final,
        "matched": results["matched"],
        "approximate": results["approximate"],
        "not_found": results["not_found"],
        "absent": [a for a in results["absent"]],
        "total_parsed": len(parsed),
    }
    review_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                               ".espn_review_pending.json")
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

    # Not found + absent → $1
    total_notfound += len(review_data["not_found"])

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
    })


def _save_espn_value(player_id: int, season: int, espn_raw: float, espn_adjusted: float, is_final: bool):
    """Save ESPN value for a player and update Player.espn_ref_value."""
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
        player.espn_ref_value = espn_adjusted


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
