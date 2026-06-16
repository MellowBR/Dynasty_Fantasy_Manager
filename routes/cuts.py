"""
routes/cuts.py — OFF26-1: janela de CORTES selada.

Cada owner declara EM SIGILO a lista de cortes do próprio roster (D1 — unidade é o
corte; keepers = complemento). Budget ao vivo via porta canônica em modo
NÃO-PROJETADO (D9, salário já rollado). O admin abre a janela (gate duro:
`needs_review` zerado — D3), supre/ajusta times pelo write-by-team (D5, nunca lê o
alheio — D6), e dispara o lock + revelação simultânea (D4) que congela um snapshot
auditável no molde do M8 (D7). A revelação só LÊ/congela — NÃO escreve no Sleeper
(OFF26-8) nem materializa cortes no estado oficial do Manager.

Sigilo (D6, requisito de segurança): NENHUMA rota devolve a declaração de outro time
antes do lock. A leitura de declaração é escopada a `current_user.team_id`; o admin
opera o time alheio só por ESCRITA. A contagem agregada ("X/Y declararam") não vaza
conteúdo.
"""

import csv as _csv
import io as _io
import json as _json
from types import SimpleNamespace
from flask import Blueprint, render_template, request, jsonify, Response
from flask_login import login_required, current_user
from models import (
    db, Team, Player, User,
    CutDeclaration, CutWindowAudit, compute_cut_snapshot_hash,
    get_config, set_config, get_current_season,
)
from salary_engine import draft_budget
from timeutil import utc_iso
from routes.auth import admin_required

cuts_bp = Blueprint("cuts", __name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _window_locked(season: int) -> bool:
    """True se já existe snapshot canônico (janela revelada/travada)."""
    return CutWindowAudit.query.filter_by(
        season=season, is_canonical=True).first() is not None


def _window_state(season: int) -> str:
    """closed | open | locked."""
    if _window_locked(season):
        return "locked"
    if get_config("cuts_window_open", "false") == "true":
        return "open"
    return "closed"


def _pending_review_count() -> int:
    """Gate duro de abertura (D3): jogadores em needs_review em qualquer roster."""
    return Player.query.filter_by(needs_review=True, is_dropped=False).count()


def _roster_player_ids(team_id: int) -> set:
    """IDs do roster ATIVO de um time (chave de declaração = Player.id)."""
    return {p.id for p in Player.query.filter_by(team_id=team_id, is_dropped=False).all()}


def _sanitize_cut_ids(raw, team_id: int):
    """Valida que cada cut_id ∈ roster ativo do time. Retorna (ids_ok, invalid)."""
    roster = _roster_player_ids(team_id)
    ids_ok, invalid = [], []
    seen = set()
    for x in (raw or []):
        try:
            pid = int(x)
        except (TypeError, ValueError):
            continue
        if pid in seen:
            continue
        seen.add(pid)
        (ids_ok if pid in roster else invalid).append(pid)
    return ids_ok, invalid


def _upsert_declaration(season, team_id, cut_ids, editor_id):
    """Cria/atualiza a declaração de cortes (declared=True). Não muta roster/Sleeper."""
    decl = CutDeclaration.query.filter_by(season=season, team_id=team_id).first()
    if not decl:
        decl = CutDeclaration(season=season, team_id=team_id)
        db.session.add(decl)
    decl.cut_ids_json = _json.dumps(sorted(cut_ids))
    decl.declared = True
    decl.updated_by = editor_id
    db.session.commit()
    return decl


# ── Page ──────────────────────────────────────────────────────────────────────

@cuts_bp.route("/cuts")
@login_required
def cuts_page():
    season = get_current_season()
    my_team = current_user.team_rel
    my_roster = []
    if my_team:
        players = Player.query.filter_by(team_id=my_team.id, is_dropped=False).all()
        my_roster = [{
            "id": p.id, "name": p.name, "position": p.position,
            "salary": p.salary, "contract_display": p.contract_display(),
            "is_on_ir": p.is_on_ir, "needs_review": p.needs_review,
        } for p in sorted(players, key=lambda p: (-p.salary, p.name))]
    teams = Team.query.order_by(Team.name).all() if current_user.is_admin else []
    return render_template(
        "cuts.html",
        season=season,
        my_team=my_team,
        my_roster=my_roster,
        teams=teams,
        state=_window_state(season),
        is_admin=current_user.is_admin,
    )


# ── State / aggregate count (sem vazar conteúdo) ──────────────────────────────

@cuts_bp.route("/api/cuts/state")
@login_required
def cuts_state():
    """Estado da janela + contagem AGREGADA (D6 — nunca conteúdo alheio)."""
    season = get_current_season()
    total = Team.query.count()
    declared = CutDeclaration.query.filter_by(season=season, declared=True).count()
    return jsonify({
        "season": season,
        "state": _window_state(season),
        "declared_count": declared,
        "total_teams": total,
        "pending_review": _pending_review_count(),
        "is_admin": current_user.is_admin,
        "my_team_id": current_user.team_id,
        "my_team_name": current_user.team_rel.name if current_user.team_rel else None,
        "i_declared": bool(current_user.team_id and CutDeclaration.query.filter_by(
            season=season, team_id=current_user.team_id, declared=True).first()),
    })


# ── Owner: ler/gravar a PRÓPRIA declaração (sigilo — escopo current_user) ──────

@cuts_bp.route("/api/cuts/declaration")
@login_required
def get_my_declaration():
    """D6: devolve SÓ a declaração do próprio time. Não há param de team_id —
    é impossível ler a alheia por esta rota antes (ou depois) do lock."""
    if not current_user.team_id:
        return jsonify({"error": "Usuário sem time vinculado"}), 400
    season = get_current_season()
    decl = CutDeclaration.query.filter_by(
        season=season, team_id=current_user.team_id).first()
    return jsonify({
        "team_id": current_user.team_id,
        "cut_ids": decl.cut_ids() if decl else [],
        "declared": bool(decl and decl.declared),
    })


@cuts_bp.route("/api/cuts/declaration", methods=["POST"])
@login_required
def save_my_declaration():
    """Owner grava a declaração do PRÓPRIO time (D1). Janela precisa estar aberta."""
    if not current_user.team_id:
        return jsonify({"error": "Usuário sem time vinculado"}), 400
    season = get_current_season()
    if _window_state(season) != "open":
        return jsonify({"error": "A janela de cortes não está aberta."}), 409

    data = request.get_json() or {}
    cut_ids, invalid = _sanitize_cut_ids(data.get("cut_ids"), current_user.team_id)
    if invalid:
        return jsonify({"error": f"IDs fora do seu roster: {invalid}"}), 400

    _upsert_declaration(season, current_user.team_id, cut_ids, current_user.id)
    return jsonify({"success": True, "cut_ids": cut_ids, "declared": True})


# ── Admin: abrir janela (gate duro needs_review) ──────────────────────────────

@cuts_bp.route("/api/cuts/admin/open", methods=["POST"])
@admin_required
def admin_open_window():
    """D3: bloqueio DURO — não abre enquanto houver needs_review pendente."""
    season = get_current_season()
    if _window_locked(season):
        return jsonify({"error": "Janela já revelada/travada nesta season."}), 409
    pending = _pending_review_count()
    if pending > 0:
        return jsonify({
            "error": f"Há {pending} jogador(es) em needs_review. Zere a fila antes de abrir a janela.",
            "pending_review": pending,
        }), 409
    set_config("cuts_window_open", "true")
    return jsonify({"success": True, "state": "open"})


@cuts_bp.route("/api/cuts/admin/close", methods=["POST"])
@admin_required
def admin_close_window():
    """Fecha a janela sem revelar (volta a 'closed'); não destrói declarações."""
    season = get_current_season()
    if _window_locked(season):
        return jsonify({"error": "Janela já travada."}), 409
    set_config("cuts_window_open", "false")
    return jsonify({"success": True, "state": "closed"})


# ── Admin: declarar/ajustar PELO time (write-by-team, nunca lê o alheio) ───────

@cuts_bp.route("/api/cuts/admin/declare", methods=["POST"])
@admin_required
def admin_declare_for_team():
    """D5: admin supre ausente / adequa, ESCREVENDO pelo time alvo. É escrita pelo
    time (não leitura do alheio — D6): valida cut_ids contra o roster PÚBLICO do alvo
    e grava; não devolve o conteúdo prévio da declaração."""
    season = get_current_season()
    if _window_locked(season):
        return jsonify({"error": "Janela já travada."}), 409
    data = request.get_json() or {}
    try:
        team_id = int(data.get("team_id"))
    except (TypeError, ValueError):
        return jsonify({"error": "team_id inválido"}), 400
    if not db.session.get(Team, team_id):
        return jsonify({"error": "Time não encontrado"}), 404

    cut_ids, invalid = _sanitize_cut_ids(data.get("cut_ids"), team_id)
    if invalid:
        return jsonify({"error": f"IDs fora do roster do time: {invalid}"}), 400

    _upsert_declaration(season, team_id, cut_ids, current_user.id)
    # D6: não retorna conteúdo — só confirma a escrita.
    return jsonify({"success": True, "team_id": team_id, "num_cuts": len(cut_ids)})


# ── Admin: lock + revelação (snapshot canônico, molde M8) ─────────────────────

def _build_snapshot(season: int) -> list:
    """Snapshot de TODOS os times: declarados usam seus cortes; ausentes = zero (D2)."""
    decls = {d.team_id: d for d in CutDeclaration.query.filter_by(season=season).all()}
    snapshot = []
    for team in Team.query.order_by(Team.id).all():
        decl = decls.get(team.id)
        cut_ids = decl.cut_ids() if decl else []
        names = {}
        if cut_ids:
            names = {p.id: p.name for p in Player.query.filter(Player.id.in_(cut_ids)).all()}
        snapshot.append({
            "team_id": team.id,
            "team_name": team.name,
            "cut_ids": cut_ids,
            "cut_names": [names.get(c, f"#{c}") for c in cut_ids],
            "num_cuts": len(cut_ids),
            "declared": bool(decl and decl.declared),
        })
    return snapshot


def _persist_audit(season, snapshot, previous_audit_id, reason):
    audit = CutWindowAudit(
        season=season,
        declarations_json=_json.dumps(snapshot, ensure_ascii=False),
        executed_by=current_user.id if current_user.is_authenticated else None,
        result_hash=compute_cut_snapshot_hash(snapshot),
        previous_audit_id=previous_audit_id,
        reason=reason,
        is_canonical=True,
    )
    db.session.add(audit)
    set_config("cuts_window_open", "false")  # janela revelada → fechada p/ edição
    db.session.commit()
    return audit


@cuts_bp.route("/api/cuts/admin/lock", methods=["POST"])
@admin_required
def admin_lock_reveal():
    """D4/D7: lock + revelação simultânea. Congela snapshot canônico. Bloqueia 2º
    lock sem reason (padrão M8 — use /replace)."""
    season = get_current_season()
    if _window_locked(season):
        return jsonify({
            "error": "Janela já revelada. Use /api/cuts/admin/replace com justificativa para re-executar."
        }), 409
    snapshot = _build_snapshot(season)
    audit = _persist_audit(season, snapshot, previous_audit_id=None, reason=None)
    return jsonify({"success": True, "audit": audit.to_dict()})


@cuts_bp.route("/api/cuts/admin/replace", methods=["POST"])
@admin_required
def admin_replace_reveal():
    """M8: re-executa a revelação depois da canônica. Exige reason; encadeia
    previous_audit_id; marca a anterior superseded."""
    season = get_current_season()
    data = request.get_json() or {}
    reason = (data.get("reason") or "").strip()
    if not reason:
        return jsonify({"error": "Campo 'reason' é obrigatório para re-execução"}), 400
    prev = CutWindowAudit.query.filter_by(season=season, is_canonical=True).first()
    if not prev:
        return jsonify({"error": "Nenhum snapshot canônico. Use /lock primeiro."}), 404

    prev.is_canonical = False
    db.session.add(prev)
    snapshot = _build_snapshot(season)
    audit = _persist_audit(season, snapshot, previous_audit_id=prev.id, reason=reason)
    return jsonify({
        "success": True,
        "audit": audit.to_dict(),
        "superseded_audit_id": prev.id,
    })


# ── Reveal + verify (pós-lock) ────────────────────────────────────────────────

@cuts_bp.route("/api/cuts/audit")
@login_required
def cuts_audit():
    """Pós-lock: revela o snapshot canônico (conteúdo de todos). Pré-lock: not revealed."""
    season = get_current_season()
    canonical = CutWindowAudit.query.filter_by(season=season, is_canonical=True).first()
    if not canonical:
        return jsonify({"revealed": False})
    superseded = CutWindowAudit.query.filter_by(
        season=season, is_canonical=False).order_by(CutWindowAudit.id.desc()).all()
    return jsonify({
        "revealed": True,
        "audit": canonical.to_dict(),
        "superseded": [a.to_dict() for a in superseded],
    })


@cuts_bp.route("/api/cuts/audit/verify")
@login_required
def cuts_audit_verify():
    """M8: re-deriva o hash do snapshot canônico e compara com o gravado."""
    season = get_current_season()
    canonical = CutWindowAudit.query.filter_by(season=season, is_canonical=True).first()
    if not canonical:
        return jsonify({"error": "Nenhum snapshot canônico nesta season."}), 404
    snapshot = _json.loads(canonical.declarations_json)
    recomputed = compute_cut_snapshot_hash(snapshot)
    return jsonify({
        "season": season,
        "stored_hash": canonical.result_hash,
        "recomputed_hash": recomputed,
        "hash_match": recomputed == canonical.result_hash,
    })


# ══════════════════════════════════════════════════════════════════════════════
# OFF26-2 — Keeper sheet exportável (consolidada; LEITORA — não muta nada)
# ══════════════════════════════════════════════════════════════════════════════
#
# Deriva por INVERSÃO do snapshot do OFF26-1: keepers = roster LIVE − cut_ids do
# snapshot canônico (D1). Salário = p.salary canônico (D3, não re-derivar). Budget de
# FA = `usable_draft_budget` via o MESMO `draft_budget` que a porta usa em
# `projected:false` (D4 — consome a fonte única, não recalcula; mesmo precedente de
# draft_import.py). Fonte mista deliberada (D2): cortes frozen, salário/budget ao vivo;
# a página exibe o timestamp do lock + aviso. Status `declared` por time (D6).

# Labels PT do status de declaração (D6) — chave estável p/ CSV/tabela.
_DECL_STATUS_LABEL = {
    "owner_declared": "Declarou",
    "default_zero": "Default (manteve todos)",
    "admin_supplied": "Admin supriu",
}


def _declared_status(snap_team: dict, season: int) -> str:
    """Status de declaração (D6). default-zero vs. declarou vem do SNAPSHOT (`declared`);
    owner-vs-admin é enriquecido pela CutDeclaration live (congelada pós-lock — sem edição
    possível com a janela travada). Leitura pura."""
    if not snap_team.get("declared"):
        return "default_zero"  # não declarou → manteve todos (D2 do OFF26-1)
    decl = CutDeclaration.query.filter_by(
        season=season, team_id=snap_team["team_id"]).first()
    if decl and decl.editor and decl.editor.team_id != snap_team["team_id"]:
        return "admin_supplied"  # escrito por quem não é dono daquele time (D5)
    return "owner_declared"


def _team_fa_budget(keepers: list) -> int:
    """Budget de FA do time = `usable_draft_budget` (D4). Consome o ÚNICO `draft_budget`
    com base salarial CORRENTE (`p.salary` — equivale a `projected:false` da porta).
    Nenhuma aritmética de cap nova (invariante F10)."""
    roster = [SimpleNamespace(salary=p.salary, is_dropped=False) for p in keepers]
    return int(draft_budget(roster)["usable_draft_budget"])


def _build_keeper_sheet(season: int) -> dict:
    """Monta a sheet consolidada (12 times). Leitora — não escreve nada.
    Retorna {revealed:False} se a janela não foi revelada (pré-condição D9)."""
    canonical = CutWindowAudit.query.filter_by(
        season=season, is_canonical=True).first()
    if not canonical:
        return {"revealed": False, "season": season}

    snapshot = _json.loads(canonical.declarations_json)
    teams = []
    for snap in sorted(snapshot, key=lambda d: d["team_name"].lower()):
        cut_ids = set(snap.get("cut_ids", []))
        # keepers = roster LIVE − cortes do snapshot (D1)
        roster = Player.query.filter_by(
            team_id=snap["team_id"], is_dropped=False).all()
        keepers = [p for p in roster if p.id not in cut_ids]
        keepers.sort(key=lambda p: (-p.salary, p.name))
        status = _declared_status(snap, season)
        teams.append({
            "team_id": snap["team_id"],
            "team_name": snap["team_name"],
            "declared_status": status,
            "declared_label": _DECL_STATUS_LABEL[status],
            "fa_budget": _team_fa_budget(keepers),  # usable_draft_budget (D4)
            "num_keepers": len(keepers),
            "keepers": [{
                "id": p.id, "name": p.name, "position": p.position,
                "salary": int(p.salary),
            } for p in keepers],
        })
    return {
        "revealed": True,
        "season": season,
        "lock_timestamp": utc_iso(canonical.executed_at) or None,
        "teams": teams,
    }


@cuts_bp.route("/cuts/keeper_sheet")
@login_required
def keeper_sheet_page():
    season = get_current_season()
    return render_template("keeper_sheet.html", season=season,
                           sheet=_build_keeper_sheet(season))


@cuts_bp.route("/api/cuts/keeper_sheet")
@login_required
def keeper_sheet_json():
    return jsonify(_build_keeper_sheet(get_current_season()))


@cuts_bp.route("/api/cuts/keeper_sheet.csv")
@login_required
def keeper_sheet_csv():
    """CSV com PARIDADE 1:1 com a tabela renderizada (mesma fonte _build_keeper_sheet).
    1 linha por keeper; budget de FA e status repetidos por time. Sem mutação."""
    season = get_current_season()
    sheet = _build_keeper_sheet(season)
    si = _io.StringIO()
    w = _csv.writer(si)
    w.writerow(["Time", "Keeper", "Posicao", "Salario", "Budget FA (time)", "Status"])
    if sheet.get("revealed"):
        for t in sheet["teams"]:
            for k in t["keepers"]:
                w.writerow([t["team_name"], k["name"], k["position"],
                            k["salary"], t["fa_budget"], t["declared_label"]])
    return Response(
        si.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition":
                 f'attachment; filename=keeper_sheet_{season}.csv'},
    )
