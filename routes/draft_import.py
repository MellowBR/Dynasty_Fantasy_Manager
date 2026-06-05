"""
routes/draft_import.py — OFF26-3: importador de drafts de liga fantasma.

Fluxo administrativo ÚNICO com 2 modos auto-detectados por draft.type:
  linear  → rookie_draft  (salário = floor(ESPN×1.2) via salary_engine.year1_salary)
  auction → fa_auction    (salário = valor do lance / metadata.amount)

Duas etapas OBRIGATÓRIAS:
  1) preview  — nenhuma escrita; lista picks com match (salário + budget) e
                picks sem match classificados por causa.
  2) confirm  — exige resolução explícita de cada pick sem match (resolver →
                player_id existente / 'create'; ou 'skip' com justificativa).
                Escreve EXCLUSIVAMENTE via models.record_acquisition.

Idempotente por sleeper_event_ref ('draft:<id>:<pick_no>') gravado em
AuctionLog.notes. Leitura da Sleeper API é read-only (reusa sync_sleeper._get).
Cap é soft: budget gera alerta, nunca bloqueia.
"""
from types import SimpleNamespace
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from models import (db, Player, Team, get_current_season,
                    record_acquisition, acquisition_already_recorded)
from player_lookup import find_player_by_sleeper_id
from salary_engine import year1_salary, draft_budget
from routes.auth import admin_required
import sync_sleeper as ss

draft_import_bp = Blueprint("draft_import", __name__)


# ── Leitura (read-only) ───────────────────────────────────────────────────────

def _read_draft(draft_id):
    draft = ss._get(f"{ss.BASE_URL}/draft/{draft_id}")
    if not draft:
        return None, None
    picks = ss._get(f"{ss.BASE_URL}/draft/{draft_id}/picks") or []
    return draft, picks


def _team_by_roster(league_id):
    rosters = ss._get(f"{ss.BASE_URL}/league/{league_id}/rosters") or []
    out = {}
    for r in rosters:
        oid = str(r.get("owner_id") or "")
        out[str(r.get("roster_id"))] = Team.query.filter_by(sleeper_owner_id=oid).first()
    return out


def _classify_missing(sid, acquisition_type):
    """Causa do pick sem match (taxonomia observada em 2025)."""
    if sid and not str(sid).isdigit():
        return "DST/defesa (id não-numérico)"
    dropped = Player.query.filter_by(sleeper_player_id=str(sid), is_dropped=True).first()
    if dropped:
        return "jogador dropado no banco"
    if acquisition_type == "rookie_draft":
        return "rookie ainda não cadastrado"
    return "não cadastrado no banco"


def _budget_alerts(matched):
    """Alertas de budget por time via draft_budget canônico (soft — não bloqueia)."""
    alerts = []
    by_team = {}
    for m in matched:
        by_team.setdefault(m["team_id"], []).append(m)
    for team_id, picks in by_team.items():
        team = Team.query.get(team_id)
        if not team:
            continue
        current = Player.query.filter_by(team_id=team_id, is_dropped=False).all()
        sim = ([SimpleNamespace(salary=p.salary or 0, is_dropped=False) for p in current]
               + [SimpleNamespace(salary=m["salary"], is_dropped=False) for m in picks])
        b = draft_budget(sim)
        if b["over_cap"] or b["insufficient_budget"]:
            alerts.append({
                "team": team.name, "over_cap": b["over_cap"],
                "insufficient_budget": b["insufficient_budget"],
                "usable_draft_budget": b["usable_draft_budget"],
                "added_picks": len(picks),
            })
    return alerts


# ── Preview (sem escrita) ─────────────────────────────────────────────────────

def build_preview(draft_id):
    draft, picks = _read_draft(draft_id)
    if draft is None:
        return {"error": f"Draft {draft_id} não encontrado na API do Sleeper."}
    if draft.get("status") != "complete":
        return {"error": f"Draft {draft_id} não está completo (status="
                         f"{draft.get('status')}). Importação indisponível."}

    dtype = draft.get("type")
    acquisition_type = "rookie_draft" if dtype == "linear" else "auction_draft"
    is_rookie = acquisition_type == "rookie_draft"
    league_id = draft.get("league_id")
    try:
        season = int(draft.get("season"))
    except (TypeError, ValueError):
        season = get_current_season()
    by_roster = _team_by_roster(league_id) if league_id else {}

    matched, unmatched = [], []
    for pk in picks:
        sid = str(pk.get("player_id") or "")
        pick_no = pk.get("pick_no")
        md = pk.get("metadata") or {}
        amount = md.get("amount")
        team = by_roster.get(str(pk.get("roster_id")))
        ev_ref = f"draft:{draft_id}:{pick_no}"
        already = acquisition_already_recorded(ev_ref)
        pname = (md.get("first_name", "") + " " + md.get("last_name", "")).strip() or sid
        base = {
            "sleeper_player_id": sid, "pick_no": pick_no, "round": pk.get("round"),
            "player_name": pname, "team": team.name if team else None,
            "team_id": team.id if team else None, "amount": amount,
            "event_ref": ev_ref, "already_imported": already,
        }
        if team is None:
            unmatched.append({**base, "cause": "roster não mapeado a um time local"})
            continue
        player = find_player_by_sleeper_id(sid) if sid else None
        if player is None:
            unmatched.append({**base, "cause": _classify_missing(sid, acquisition_type)})
            continue
        espn_adj = player.espn_ref_value or 0.0
        if is_rookie:
            salary = year1_salary("rookie_draft", 0, espn_adj)
        else:
            try:
                bid = float(amount) if amount not in (None, "") else 1.0
            except (TypeError, ValueError):
                bid = 1.0
            salary = year1_salary(acquisition_type, bid, espn_adj)
        matched.append({**base, "player_id": player.id, "matched_name": player.name,
                        "salary": salary, "espn_adjusted": espn_adj})

    return {
        "draft_id": str(draft_id), "type": dtype, "acquisition_type": acquisition_type,
        "season": season, "status": draft.get("status"),
        "matched": matched, "unmatched": unmatched,
        "n_matched": len(matched), "n_unmatched": len(unmatched),
        "n_already": sum(1 for m in matched if m["already_imported"]),
        "budget_alerts": _budget_alerts([m for m in matched if not m["already_imported"]]),
    }


# ── Rotas ─────────────────────────────────────────────────────────────────────

@draft_import_bp.route("/draft_import")
@login_required
def draft_import_page():
    return render_template("draft_import.html")


@draft_import_bp.route("/api/draft_import/preview", methods=["POST"])
@admin_required
def preview():
    data = request.get_json() or {}
    draft_id = str(data.get("draft_id") or "").strip()
    if not draft_id:
        return jsonify({"error": "draft_id obrigatório"}), 400
    prev = build_preview(draft_id)
    return jsonify(prev), (400 if "error" in prev else 200)


@draft_import_bp.route("/api/draft_import/confirm", methods=["POST"])
@admin_required
def confirm():
    """
    Body: {draft_id, resolutions: {sid: <player_id> | 'create' | 'skip'},
           skip_reasons: {sid: '...'}}
    Toda pick sem match precisa de resolução; skip exige justificativa.
    Escreve via record_acquisition; idempotente por event_ref.
    """
    data = request.get_json() or {}
    draft_id = str(data.get("draft_id") or "").strip()
    resolutions = data.get("resolutions") or {}
    skip_reasons = data.get("skip_reasons") or {}
    if not draft_id:
        return jsonify({"error": "draft_id obrigatório"}), 400

    prev = build_preview(draft_id)
    if "error" in prev:
        return jsonify(prev), 400

    # Gate: nenhum pulo silencioso — cada unmatched precisa de ação explícita.
    unresolved = []
    for u in prev["unmatched"]:
        if u["already_imported"]:
            continue
        res = resolutions.get(u["sleeper_player_id"])
        if res in (None, ""):
            unresolved.append({**u, "reason": "sem resolução"})
        elif res == "skip" and not (skip_reasons.get(u["sleeper_player_id"]) or "").strip():
            unresolved.append({**u, "reason": "skip sem justificativa"})
    if unresolved:
        return jsonify({"error": "Picks sem match não resolvidos — confirmação bloqueada.",
                        "unresolved": unresolved}), 400

    created, skipped, already = [], [], 0

    # 1) Picks com match
    for m in prev["matched"]:
        if m["already_imported"]:
            already += 1
            continue
        team = Team.query.get(m["team_id"])
        player = Player.query.get(m["player_id"])
        record_acquisition(
            player=player, team=team, acquisition_type=prev["acquisition_type"],
            season=prev["season"], espn_adjusted=m["espn_adjusted"],
            value_paid=_as_float(m["amount"]), round_num=m["round"],
            event_ref=m["event_ref"], notes="draft import",
        )
        created.append(m["event_ref"])

    # 2) Picks sem match resolvidos
    for u in prev["unmatched"]:
        if u["already_imported"]:
            already += 1
            continue
        sid = u["sleeper_player_id"]
        res = resolutions.get(sid)
        if res == "skip":
            skipped.append({"sid": sid, "reason": skip_reasons.get(sid)})
            continue
        team = Team.query.get(u["team_id"]) if u["team_id"] else None
        if team is None:
            skipped.append({"sid": sid, "reason": "sem time mapeado"})
            continue
        if res == "create":
            player = None
        else:
            player = Player.query.get(int(res)) if str(res).isdigit() else None
            if player is None:
                skipped.append({"sid": sid, "reason": f"resolução inválida: {res}"})
                continue
        espn_adj = (player.espn_ref_value or 0.0) if player else 0.0
        record_acquisition(
            player=player, player_name=u["player_name"], team=team,
            acquisition_type=prev["acquisition_type"], season=prev["season"],
            espn_adjusted=espn_adj, value_paid=_as_float(u["amount"]),
            round_num=u["round"],
            sleeper_player_id=(sid if (player is None and str(sid).isdigit()) else None),
            event_ref=u["event_ref"], notes="draft import (resolvido)",
        )
        created.append(u["event_ref"])

    db.session.commit()
    return jsonify({
        "success": True, "created": len(created),
        "already_imported": already, "skipped": skipped,
    })


def _as_float(amount):
    try:
        return float(amount) if amount not in (None, "") else 0.0
    except (TypeError, ValueError):
        return 0.0
