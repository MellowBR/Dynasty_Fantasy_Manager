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

OFF26-11 (modo auction SOMENTE) — a keeper sheet congelada é LISTA DE EXCLUSÃO:
  · pick cujo jogador consta na lista PARA O MESMO TIME → keeper: não é ingerido,
    não gera contrato, não toca salário/contract_year/histórico;
  · pick cujo jogador consta para OUTRO time, sem id, ou sem time local → PENDÊNCIA
    que BLOQUEIA a confirmação (o importador não arbitra sozinho);
  · sem lista congelada utilizável → import BLOQUEADO (nunca "ingerir tudo").
Sem reconciliação: não se compara salário de keeper (isso é a auditoria OFF26-4, que
roda ANTES do leilão). O modo linear é intocado — ver `keeper_exclusion.py`.
"""
from types import SimpleNamespace
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import (db, Player, Team, get_current_season,
                    record_acquisition, acquisition_already_recorded,
                    rookie_espn_adjusted)
from player_lookup import find_player_by_sleeper_id
from salary_engine import year1_salary, draft_budget
from routes.auth import admin_required
import keeper_exclusion as kx
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


def _dropped_by_sid(sid):
    """Player DROPADO com este sleeper_id, se houver. `find_player_by_sleeper_id` filtra
    `is_dropped=False` — logo o CASO CANÔNICO do owner (jogador dropado na janela e
    recomprado no leilão pelo mesmo time) NUNCA cai em `matched`, e sem esta consulta a
    tela só ofereceria 'criar novo' (que duplicaria o Player e perderia o histórico)."""
    if not sid:
        return None
    return Player.query.filter_by(sleeper_player_id=str(sid), is_dropped=True).first()


def _classify_missing(sid, acquisition_type, dropped=None):
    """Causa do pick sem match (taxonomia observada em 2025)."""
    if sid and not str(sid).isdigit():
        return "DST/defesa (id não-numérico)"
    if dropped is not None:
        return "jogador dropado no banco"
    if acquisition_type == "rookie_draft":
        return "rookie ainda não cadastrado"
    return "não cadastrado no banco"


def _budget_alerts(matched):
    """Alertas de budget por time via draft_budget canônico (soft — não bloqueia).

    OFF26-11: `matched` já vem SEM keepers (foram excluídos antes). Isso conserta uma
    dupla contagem que existiria no caminho novo — o keeper já está no roster corrente
    (base da simulação) e, se também entrasse como pick adicionado, contaria duas vezes."""
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

    # ── OFF26-11: lista de exclusão (SÓ modo auction; linear intocado) ──────────
    exclusion_index, frozen, gate = None, None, None
    if not is_rookie:
        exclusion_index, frozen, gate = kx.exclusion_gate(season)
        if gate:
            # Sheet ausente/provisória/não congelada BLOQUEIA o import — jamais degradar
            # para "ingerir tudo" (cada keeper viraria contrato ano 1).
            return {"error": gate["error"], "exclusion_state": gate["state"],
                    "exclusion_source": _source_brief(gate.get("source")),
                    "draft_id": str(draft_id), "acquisition_type": acquisition_type}

    matched, unmatched, excluded, pendencies = [], [], [], []
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

        # Discriminador ANTES de qualquer resolução de identidade local: o keeper não é
        # "um pick que não casou" — é um pick que NÃO SE INGERE por definição.
        if exclusion_index is not None:
            kind = kx.classify_pick(sid, team.id if team else None, exclusion_index)
            if kind == kx.KIND_KEEPER:
                kp = exclusion_index[sid]
                excluded.append({**base, "keeper_name": kp["name"],
                                 "keeper_team": kp["team_name"],
                                 "keeper_position": kp.get("position"),
                                 "sheet_salary": kp["salary"]})
                continue
            if kind in kx.PENDING_KINDS:
                item = {**base, "kind": kind, "reason": kx.KIND_REASON[kind]}
                if kind == kx.KIND_KEEPER_OTHER:
                    kp = exclusion_index[sid]
                    item["sheet_team"] = kp["team_name"]
                    item["sheet_team_id"] = kp["team_id"]
                    item["sheet_salary"] = kp["salary"]
                pendencies.append(item)
                continue

        if team is None:
            unmatched.append({**base, "cause": "roster não mapeado a um time local"})
            continue
        player = find_player_by_sleeper_id(sid) if sid else None
        if player is None:
            # E2: rookie ainda não no DB — mostrar o salário projetado a partir do
            # store de valores ESPN (resolvido no import), se houver, p/ a decisão.
            dropped = _dropped_by_sid(sid)
            entry = {**base, "cause": _classify_missing(sid, acquisition_type, dropped)}
            if dropped is not None:
                # CASO CANÔNICO ($50): contrato antigo morreu, nasce contrato ANO 1 no
                # mesmo Player — resolver para o id existente, nunca 'criar novo'.
                entry["suggested_player_id"] = dropped.id
                entry["suggested_name"] = dropped.name
                entry["suggested_contract_year"] = dropped.contract_year
                entry["suggested_salary"] = dropped.salary
            store_espn = rookie_espn_adjusted(sid, season) if is_rookie else None
            if store_espn:
                entry["store_espn_adjusted"] = store_espn
                entry["projected_salary"] = year1_salary("rookie_draft", 0, store_espn)
            unmatched.append(entry)
            continue
        # E2: rookie já no DB mas sem espn (ex.: stub de sync) → fallback ao store
        espn_adj = player.espn_ref_value or 0.0
        if is_rookie and not espn_adj:
            espn_adj = rookie_espn_adjusted(sid, season) or 0.0
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
        # OFF26-11 — transparência SEM reconciliação: os keepers excluídos aparecem
        # separados dos arremates, e nada do salário do board é comparado com o Manager.
        "keepers_excluded": excluded, "n_keepers_excluded": len(excluded),
        "pendencies": pendencies, "n_pendencies": len(pendencies),
        "exclusion": _frozen_brief(frozen),
        # `matched` já exclui keepers → a soma é de ARREMATES apenas (ver _budget_alerts)
        "budget_alerts": _budget_alerts([m for m in matched if not m["already_imported"]]),
    }


def _frozen_brief(frozen):
    """Cabeçalho da lista congelada — sem despejar os keepers no payload do preview."""
    if not frozen:
        return None
    return {k: frozen.get(k) for k in (
        "season", "frozen_at", "source_stage", "sync_timestamp", "hash",
        "num_keepers", "num_teams", "late_drop_executed_at", "reason")}


def _source_brief(source):
    """Diagnóstico do estado da sheet quando o import está bloqueado."""
    if not source:
        return None
    return {k: source.get(k) for k in (
        "season", "available", "stage", "stage_label", "sync_timestamp", "num_teams")}


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
           skip_reasons: {sid: '...'}, exclusion_hash: '<hash do preview>'}
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

    # OFF26-11 — pendências BLOQUEIAM a confirmação e NÃO têm caminho de resolução: o
    # importador não arbitra keeper de outro time, nem classifica sem identidade.
    if prev.get("pendencies"):
        return jsonify({
            "error": (f"{len(prev['pendencies'])} pick(s) que o discriminador de keeper "
                      f"não pode classificar — confirmação bloqueada. Resolva no board / "
                      f"na sheet e recarregue o preview."),
            "pendencies": prev["pendencies"],
        }), 400

    # A lista congelada não pode trocar entre o preview que o admin leu e o confirm.
    sent_hash = (data.get("exclusion_hash") or "").strip()
    cur_hash = ((prev.get("exclusion") or {}).get("hash") or "")
    if sent_hash and cur_hash and sent_hash != cur_hash:
        return jsonify({"error": "A lista de exclusão foi re-congelada depois deste "
                                 "preview. Recarregue o preview e confira antes de "
                                 "confirmar."}), 409

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
        # E2: salário do rookie vem do store de valores ESPN (keyed por sleeper_id)
        # quando o player é criado agora ou está sem espn — o salary_engine deriva o
        # floor(ESPN×1.2) em record_acquisition (sem replicar o cálculo aqui).
        espn_adj = (player.espn_ref_value or 0.0) if player else 0.0
        if not espn_adj:
            espn_adj = rookie_espn_adjusted(sid, prev["season"]) or 0.0
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
        # keepers excluídos: contados, nunca escritos
        "keepers_excluded": prev.get("n_keepers_excluded", 0),
        "exclusion_hash": cur_hash or None,
    })


# ── OFF26-11: lista de exclusão (congelamento) ────────────────────────────────

@draft_import_bp.route("/api/draft_import/exclusion")
@admin_required
def exclusion_state():
    """Estado da lista congelada + diagnóstico da sheet ao vivo (read-only)."""
    season = get_current_season()
    frozen = kx.get_frozen_exclusion()
    src = kx.build_exclusion_source(season)
    return jsonify({
        "season": season,
        "frozen": _frozen_brief(frozen),
        "frozen_season_matches": bool(frozen and frozen.get("season") == season),
        "source": {
            "available": src["available"], "stage": src["stage"],
            "stage_label": src["stage_label"], "sync_timestamp": src["sync_timestamp"],
            "num_teams": src["num_teams"], "num_keepers": len(src["keepers"]),
            "late_drop": src["late_drop"],
            "keepers_sem_id": [{"name": k["name"], "team_name": k["team_name"]}
                               for k in src["keepers_sem_id"]],
        },
    })


@draft_import_bp.route("/api/draft_import/exclusion/freeze", methods=["POST"])
@admin_required
def exclusion_freeze():
    """Congela a keeper sheet DEFINITIVA como lista de exclusão do leilão de 24/08.

    Ato explícito de admin: é ele que fixa QUAL instante vale. Depois do leilão os owners
    adicionam os arremates na liga real, e uma lista derivada ao vivo passaria a chamá-los
    de keeper — excluindo da ingestão exatamente o que precisa entrar."""
    season = get_current_season()
    data = request.get_json() or {}
    res = kx.freeze_exclusion_list(
        season,
        executed_by=(current_user.id if current_user.is_authenticated else None),
        reason=(data.get("reason") or ""))
    if "error" in res:
        return jsonify({k: v for k, v in res.items() if k != "source"}), 409
    return jsonify({"success": True, "frozen": _frozen_brief(res["frozen"])})


@draft_import_bp.route("/api/draft_import/exclusion", methods=["DELETE"])
@admin_required
def exclusion_clear():
    """Descongela. O import volta a ficar bloqueado até novo congelamento."""
    kx.clear_frozen_exclusion()
    return jsonify({"success": True, "frozen": None})


def _as_float(amount):
    try:
        return float(amount) if amount not in (None, "") else 0.0
    except (TypeError, ValueError):
        return 0.0
