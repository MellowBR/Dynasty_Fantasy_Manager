import io
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required
from models import (db, Player, Team, AuctionLog, SalaryHistory, CURRENT_SEASON,
                    get_current_season, record_acquisition,
                    acquisition_already_recorded)
from salary_engine import year1_salary, _floor
from routes.auth import admin_required

auction_bp = Blueprint("auction", __name__)


@auction_bp.route("/auction")
@login_required
def auction_page():
    teams = Team.query.order_by(Team.name).all()
    recent = AuctionLog.query.order_by(AuctionLog.created_at.desc()).limit(50).all()
    return render_template("auction.html",
                           teams=[t.name for t in teams],
                           recent_entries=recent)


# ── FA Auction ────────────────────────────────────────────────────────────────

@auction_bp.route("/api/auction/fa", methods=["POST"])
@admin_required
def register_fa_auction():
    """
    Register a free agent auction result.
    Body: {player_name, team_name, value_paid, espn_ref_value, season?, notes?}
    """
    data = request.get_json() or {}
    player_name = data.get("player_name", "").strip()
    team_name   = data.get("team_name", "").strip()
    value_paid  = float(data.get("value_paid", 1) or 1)
    espn_raw    = float(data.get("espn_ref_value", 0) or 0)
    season      = int(data.get("season", get_current_season()) or get_current_season())
    notes       = data.get("notes", "")

    if not player_name or not team_name:
        return jsonify({"error": "player_name e team_name são obrigatórios"}), 400

    team = Team.query.filter_by(name=team_name).first()
    if not team:
        return jsonify({"error": f"Equipe não encontrada: {team_name}"}), 404

    espn_adjusted = espn_raw * 1.2

    # Find existing (by name + team); matching fica no chamador, escrita no helper.
    player = Player.query.filter(
        Player.name.ilike(player_name),
        Player.team_id == team.id,
    ).first()

    # OFF26-3: criação de contrato via helper atômico canônico (única porta).
    player, _salary = record_acquisition(
        player=player, player_name=player_name, team=team,
        acquisition_type="auction_draft", season=season,
        value_paid=value_paid, espn_adjusted=espn_adjusted, notes=notes,
    )
    db.session.commit()
    return jsonify({"success": True, "player": player.to_dict()})


# ── Rookie Draft ──────────────────────────────────────────────────────────────

@auction_bp.route("/api/auction/rookie", methods=["POST"])
@admin_required
def register_rookie():
    """
    Register a rookie draft pick.
    Body: {player_name, team_name, round, espn_ref_value, season?, notes?}
    """
    data = request.get_json() or {}
    player_name = data.get("player_name", "").strip()
    team_name   = data.get("team_name", "").strip()
    round_num   = int(data.get("round", 1) or 1)
    espn_raw    = float(data.get("espn_ref_value", 0) or 0)
    season      = int(data.get("season", get_current_season()) or get_current_season())
    notes       = data.get("notes", "")

    if not player_name or not team_name:
        return jsonify({"error": "player_name e team_name são obrigatórios"}), 400

    team = Team.query.filter_by(name=team_name).first()
    if not team:
        return jsonify({"error": f"Equipe não encontrada: {team_name}"}), 404

    espn_adjusted = espn_raw * 1.2

    player = Player.query.filter(
        Player.name.ilike(player_name),
        Player.team_id == team.id,
    ).first()

    # OFF26-3: criação de contrato via helper atômico canônico (única porta).
    player, _salary = record_acquisition(
        player=player, player_name=player_name, team=team,
        acquisition_type="rookie_draft", season=season,
        espn_adjusted=espn_adjusted, round_num=round_num, notes=notes,
    )
    db.session.commit()
    return jsonify({"success": True, "player": player.to_dict()})


@auction_bp.route("/api/auction/bulk", methods=["POST"])
@admin_required
def bulk_register():
    """
    Bulk register: list of FA auction or rookie entries.
    Body: {entries: [{type, player_name, team_name, value_paid or espn_ref_value, ...}]}
    """
    data = request.get_json() or {}
    entries = data.get("entries", [])
    results = []
    errors = []

    for entry in entries:
        entry_type = entry.get("type", "fa_auction")
        try:
            if entry_type != "fa_auction":
                errors.append(f"Tipo desconhecido: {entry_type}")
                continue

            player_name = entry.get("player_name", "").strip()
            team_name = entry.get("team_name", "").strip()
            team = Team.query.filter_by(name=team_name).first()
            if not team:
                errors.append(f"{player_name}: equipe '{team_name}' não encontrada")
                continue

            value_paid = float(entry.get("value_paid", 1) or 1)
            espn_adj = float(entry.get("espn_ref_value", 0) or 0) * 1.2
            season = int(entry.get("season", get_current_season()) or get_current_season())

            # Idempotência por referência de evento (mesmo padrão do importador OFF26-3).
            ev_ref = f"bulk:{season}:{team_name}:{player_name}"
            if acquisition_already_recorded(ev_ref):
                continue

            player = Player.query.filter(
                Player.name.ilike(player_name), Player.team_id == team.id
            ).first()

            # F9: criação de contrato via helper atômico canônico (única porta) —
            # Player + SalaryHistory + AuctionLog. Sem cálculo de salário local.
            player, salary = record_acquisition(
                player=player, player_name=player_name, team=team,
                acquisition_type="auction_draft", season=season,
                value_paid=value_paid, espn_adjusted=espn_adj, event_ref=ev_ref,
            )
            results.append({"name": player_name, "salary": salary})
        except Exception as e:
            errors.append(f"{entry.get('player_name', '?')}: {e}")

    db.session.commit()
    return jsonify({"registered": len(results), "results": results, "errors": errors})


# ── Excel Upload ─────────────────────────────────────────────────────────────

@auction_bp.route("/auction/upload_excel", methods=["POST"])
@admin_required
def upload_excel():
    """
    Import FA auction entries from an Excel file (.xlsx/.xls).
    Required columns: player_name, team_name, value_paid, season
    """
    file = request.files.get("file")
    if not file or not file.filename:
        flash("Nenhum arquivo selecionado.", "error")
        return redirect(url_for("auction.auction_page"))

    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ("xlsx", "xls"):
        flash("Formato inválido. Use .xlsx ou .xls.", "error")
        return redirect(url_for("auction.auction_page"))

    try:
        import pandas as pd
        df = pd.read_excel(io.BytesIO(file.read()), engine="openpyxl" if ext == "xlsx" else None)
    except Exception as e:
        flash(f"Erro ao ler arquivo: {e}", "error")
        return redirect(url_for("auction.auction_page"))

    required = {"player_name", "team_name", "value_paid", "season"}
    missing = required - set(df.columns)
    if missing:
        flash(f"Colunas faltando: {', '.join(sorted(missing))}", "error")
        return redirect(url_for("auction.auction_page"))

    imported = 0
    skipped = 0
    errors = []

    for _, row in df.iterrows():
        player_name = str(row.get("player_name", "")).strip()
        team_name = str(row.get("team_name", "")).strip()
        if not player_name or not team_name:
            skipped += 1
            continue

        try:
            value_paid = float(row.get("value_paid", 1) or 1)
            season = int(row.get("season", get_current_season()) or get_current_season())
        except (ValueError, TypeError):
            skipped += 1
            continue

        from player_lookup import find_player_by_name
        player = find_player_by_name(player_name)
        team = Team.query.filter(Team.name.ilike(f"%{team_name}%")).first()

        if not player or not team:
            skipped += 1
            reason = []
            if not player:
                reason.append(f"jogador '{player_name}' nao encontrado")
            if not team:
                reason.append(f"time '{team_name}' nao encontrado")
            errors.append("; ".join(reason))
            continue

        espn_at_time = player.espn_ref_value or 0.0

        # OFF26-3: criação de contrato via helper atômico canônico (única porta).
        record_acquisition(
            player=player, team=team, acquisition_type="auction_draft",
            season=season, value_paid=value_paid, espn_adjusted=espn_at_time,
            notes="Importado via Excel",
        )
        player.fantasy_team = team.name  # excel pode mover o time
        imported += 1

    db.session.commit()

    msg = f"{imported} registro(s) importado(s)"
    if skipped:
        msg += f", {skipped} pulado(s)"
    if errors:
        msg += ". Detalhes: " + "; ".join(errors[:5])
        if len(errors) > 5:
            msg += f" (+{len(errors) - 5} mais)"

    flash(msg, "ok" if not skipped else "warn")
    return redirect(url_for("auction.auction_page"))
