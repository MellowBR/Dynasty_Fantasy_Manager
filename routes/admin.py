from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, session
from models import db, Player, Team, SalaryHistory, SyncLog, ESPNValue, ESPNImportLog, CURRENT_SEASON, get_current_season
from salary_engine import apply_season_rollover, CONTRACT_LENGTH

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin")
def admin_page():
    last_sync = SyncLog.query.order_by(SyncLog.synced_at.desc()).first()
    player_count = Player.query.filter_by(is_dropped=False).count()
    review_count = Player.query.filter_by(needs_review=True, is_dropped=False).count()
    teams_count  = Team.query.count()
    from models import get_config
    playoffs = get_config("playoffs_started", "false") == "true"
    return render_template("admin.html",
                           last_sync=last_sync,
                           player_count=player_count,
                           review_count=review_count,
                           teams_count=teams_count,
                           current_season=get_current_season(),
                           playoffs_started=playoffs)


# ── Sleeper Sync ──────────────────────────────────────────────────────────────

@admin_bp.route("/api/admin/sync", methods=["POST"])
def trigger_sync():
    try:
        from sync_sleeper import run_sync
        result = run_sync()
        return jsonify({"success": True, **result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@admin_bp.route("/api/admin/last_sync")
def last_sync():
    log = SyncLog.query.order_by(SyncLog.synced_at.desc()).first()
    if log:
        return jsonify(log.to_dict())
    return jsonify({"synced_at": None, "summary": "Nenhum sync realizado"})


# ── Season Rollover ───────────────────────────────────────────────────────────

@admin_bp.route("/api/admin/rollover/preview", methods=["GET"])
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
def list_teams():
    teams = Team.query.order_by(Team.name).all()
    return jsonify([t.to_dict() for t in teams])


@admin_bp.route("/api/admin/teams/<int:team_id>/owner", methods=["PATCH"])
def update_team_owner(team_id):
    """Manually set or update a team's owner_name."""
    team = db.get_or_404(Team, team_id)
    data = request.get_json() or {}
    owner_name = data.get("owner_name", "").strip()
    team.owner_name = owner_name or None
    db.session.commit()
    return jsonify({"success": True, "team": team.to_dict()})


# ── ESPN PDF Import ──────────────────────────────────────────────────────────

ESPN_DEFAULT_URL = "https://g.espncdn.com/s/ffldraftkit/25/NFL25_CS_PPR300.pdf?adddata=2025CS_PPR300"


@admin_bp.route("/admin/espn_import", methods=["GET", "POST"])
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
def espn_import_status():
    """Return info about the most recent ESPN import."""
    last = ESPNImportLog.query.order_by(ESPNImportLog.imported_at.desc()).first()
    if last:
        return jsonify(last.to_dict())
    return jsonify({"status": None})


@admin_bp.route("/api/admin/review_players")
def review_players():
    players = Player.query.filter_by(needs_review=True, is_dropped=False).all()
    return jsonify([p.to_dict() for p in players])


@admin_bp.route("/api/admin/review_players/<int:pid>/clear", methods=["POST"])
def clear_review(pid):
    player = db.get_or_404(Player, pid)
    player.needs_review = False
    db.session.commit()
    return jsonify({"success": True})


# ── Playoffs Flag ────────────────────────────────────────────────────────────

@admin_bp.route("/api/admin/playoffs_started", methods=["POST"])
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

        # Entry 1: original acquisition
        origin_event = acq if acq in (
            "rookie_draft", "auction_draft", "fa_auction", "keeper"
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
