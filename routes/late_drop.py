"""
routes/late_drop.py — OFF26-10: a URNA do late drop (22/08).

Segunda mini-janela selada, e a **única porta de declaração do Manager em 2026**: os
cortes de 20/08 acontecem direto no Sleeper (públicos e graduais) e o Manager só
fotografa por sync — ver a aposentadoria da porta antiga em `routes/cuts.py`.

Cada owner deposita UM bilhete: **um jogador do próprio roster OU "não vou dropar
ninguém"**. Sigilo mais estrito que o da janela grande (U1): nem o conteúdo, nem a
EXISTÊNCIA da declaração são visíveis a terceiros — **não há contagem agregada**. O
admin abre por horário (U3), pode suprir time silencioso (nunca sobrescrever declaração
pessoal — hierarquia owner > admin) e dispara o lock + revelação simultânea (U5), que
congela o snapshot no molde M8 e **produz a lista de drops a executar**.

⛔ A execução do drop é MANUAL, no Sleeper (U7). Este módulo não muta roster, não escreve
no Sleeper e não cria/destrói contrato. Se um revelado não executar, a auditoria do
OFF26-4 acusa — e é assim que tem de ser.

⛔ FLAG DE ESTADO PRÓPRIA (`late_drop_opens_at`/`late_drop_closes_at`): reusar
`cuts_window_open` reabriria `POST /api/cuts/declaration` e a porta única viraria
promessa de UI.
"""

import json as _json
from datetime import datetime, timezone

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user

from models import (
    db, Team, Player, LateDropDeclaration, LateDropAudit,
    compute_cut_snapshot_hash, is_first_round_rookie,
    get_config, set_config, get_current_season,
)
from timeutil import utc_iso
from routes.auth import admin_required

late_drop_bp = Blueprint("late_drop", __name__)

OPENS_KEY = "late_drop_opens_at"      # ISO-8601 'Z' (UTC) — horário definido pelo admin
CLOSES_KEY = "late_drop_closes_at"
BLOCK_R1_KEY = "late_drop_block_r1_rookie"   # nasce OFF (regra em disputa na liga)


# ── Tempo / estado da janela (U3) ─────────────────────────────────────────────

def _parse_iso_utc(value):
    """ISO-8601 (com 'Z' ou offset) → datetime naive-UTC. None se vazio/inválido.

    O armazenamento do app é naive UTC (contrato do `timeutil`); o cliente manda o
    instante já convertido a partir do `datetime-local` do navegador."""
    if not value:
        return None
    txt = str(value).strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(txt)
    except ValueError:
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def _schedule():
    return _parse_iso_utc(get_config(OPENS_KEY)), _parse_iso_utc(get_config(CLOSES_KEY))


def _urn_locked(season: int) -> bool:
    """True se já existe snapshot canônico (urna revelada)."""
    return LateDropAudit.query.filter_by(
        season=season, is_canonical=True).first() is not None


def _urn_state(season: int) -> dict:
    """closed | open | locked — com o MOTIVO, que é o que o owner precisa ler no celular.

    U3: abre e fecha por horário do admin. Sem encadeamento com a janela extinta."""
    if _urn_locked(season):
        return {"state": "locked", "reason": "revelada"}
    opens, closes = _schedule()
    now = datetime.utcnow()
    if not opens:
        return {"state": "closed", "reason": "nao_agendada"}
    if now < opens:
        return {"state": "closed", "reason": "ainda_nao_abriu"}
    if closes and now >= closes:
        return {"state": "closed", "reason": "encerrada"}
    return {"state": "open", "reason": "aberta"}


def _block_r1() -> bool:
    return get_config(BLOCK_R1_KEY, "false") == "true"


# ── Bloqueio mútuo urna × rollover (MAN-OFF26-10-AJUSTES, 07/08/2026) ─────────
#
# Os bilhetes e o snapshot são escopados por `current_season`. Virar a season no meio da
# urna deixa os bilhetes ÓRFÃOS na season antiga e a revelação sai vazia — silenciosamente.
# Isso estava só no runbook; runbook é promessa, código é garantia (decisão do owner).
# A ordem do calendário é **rollover (18/08) → urna (20/08)**, e o bloqueio vale nos dois
# sentidos.

def urn_blocks_rollover(season: int) -> str | None:
    """Motivo pelo qual a urna impede o rollover agora — ou None se não impede.

    Bloqueia enquanto a urna estiver **viva e não revelada**: agendada (mesmo que ainda
    não tenha aberto) ou já com bilhetes depositados. Depois da revelação, o snapshot está
    congelado e o rollover é seguro."""
    if _urn_locked(season):
        return None
    opens, closes = _schedule()
    tem_bilhete = LateDropDeclaration.query.filter_by(season=season).count() > 0
    if not (opens or closes or tem_bilhete):
        return None
    estado = _urn_state(season)["state"]
    como = ("A urna está ABERTA" if estado == "open"
            else "A urna está agendada e ainda não foi revelada")
    return (f"{como} na season {season}. O rollover vira a season e deixaria os bilhetes "
            "órfãos — a revelação sairia VAZIA. Faça o lock + revelação da urna primeiro "
            "(ou limpe a agenda em /late_drop, se a urna ainda não foi usada) e rode o "
            "rollover depois.")


def rollover_blocks_urn() -> str | None:
    """Motivo pelo qual o rollover pendente impede abrir/agendar a urna — ou None.

    `rollover_done` é flag de AppConfig do ciclo de offseason corrente, então "rollover
    pendente" **é** estado detectável — o gap que o prompt admitia não existe.

    ⚠️ ESCAPE DECLARADO: com o **banner de ensaio ligado** (`cuts_ensaio_banner`, que o
    `ensaio_janela_selada.py --banner on` acende e o `--reset` apaga), o bloqueio é
    liberado. Sem isso, o gate impediria o próprio SMOKE da urna, que precisa rodar antes
    de 20/08 e pode cair antes do rollover de 18/08. O escape é explícito do operador,
    visível na tela para todos e some no reset."""
    if get_config("rollover_done", "false") == "true":
        return None
    if get_config("cuts_ensaio_banner", "false") == "true":
        return None      # ensaio declarado — o operador sabe que é teste
    return ("O Season Rollover ainda não foi executado neste ciclo. A ordem do calendário é "
            "**rollover → urna**: abrir a urna antes deixaria os bilhetes numa season que "
            "vai virar, e a revelação sairia vazia. Rode o passo 4 do /offseason primeiro. "
            "(Para ENSAIAR a urna antes do rollover, ligue o banner de ensaio: "
            "`python ensaio_janela_selada.py --banner on`.)")


# ── Elegibilidade (U6) ────────────────────────────────────────────────────────

def _eligible(team_id: int, season: int) -> list:
    """Roster ativo do time. Com a flag de admin LIGADA, o rookie de 1ª rodada desta
    season aparece **bloqueado** (visível e explicado — esconder confunde mais do que
    ajuda). Com a flag OFF (default), todo mundo é elegível."""
    block = _block_r1()
    players = Player.query.filter_by(team_id=team_id, is_dropped=False).all()
    out = []
    for p in sorted(players, key=lambda x: (-x.salary, x.name)):
        blocked = bool(block and is_first_round_rookie(p.id, season))
        out.append({
            "id": p.id, "name": p.name, "position": p.position,
            "salary": int(p.salary), "is_on_ir": p.is_on_ir,
            "blocked": blocked,
            "blocked_reason": "Rookie de 1ª rodada — protegido por decisão do admin"
                              if blocked else None,
        })
    return out


def _validate_choice(player_id, team_id: int, season: int):
    """(player_id_ok, erro). `None` = passo explícito, sempre válido."""
    if player_id in (None, "", "pass", "passo"):
        return None, None
    try:
        pid = int(player_id)
    except (TypeError, ValueError):
        return None, "Escolha inválida."
    p = db.session.get(Player, pid)
    if not p or p.team_id != team_id or p.is_dropped:
        return None, "Esse jogador não está no roster deste time."
    if _block_r1() and is_first_round_rookie(pid, season):
        return None, (f"{p.name} é rookie de 1ª rodada e o admin bloqueou o late drop "
                      "de rookies de 1ª rodada nesta temporada.")
    return pid, None


def _upsert(season, team_id, player_id, editor_id):
    decl = LateDropDeclaration.query.filter_by(season=season, team_id=team_id).first()
    if not decl:
        decl = LateDropDeclaration(season=season, team_id=team_id)
        db.session.add(decl)
    decl.player_id = player_id
    decl.declared = True
    decl.updated_by = editor_id
    db.session.commit()
    return decl


# ── Página ────────────────────────────────────────────────────────────────────

@late_drop_bp.route("/late_drop")
@login_required
def late_drop_page():
    season = get_current_season()
    my_team = current_user.team_rel
    return render_template(
        "late_drop.html",
        season=season,
        my_team=my_team,
        eligible=_eligible(my_team.id, season) if my_team else [],
        teams=Team.query.order_by(Team.name).all() if current_user.is_admin else [],
        is_admin=current_user.is_admin,
        # mesmo rótulo de ensaio da janela (fonte única da flag) — serve ao smoke da urna
        ensaio_banner=get_config("cuts_ensaio_banner", "false") == "true",
    )


# ── Estado (U1: sem contagem — a existência da declaração é secreta) ──────────

@late_drop_bp.route("/api/late_drop/state")
@login_required
def state():
    """Estado + CONTAGEM AGREGADA (U1-CONT, arbitragem do owner em 07/08/2026).

    O que é selado é **quem** e **o quê**. A contagem agregada não expõe nenhum dos dois:
    drops e passos contam **indistintamente**, então nem inclinação vaza (um time que
    aparece no N pode estar passando). Função operacional: andamento visível para todos e,
    para o admin, quantos faltam cutucar perto do lock.

    ⛔ Esta é a ÚNICA superfície de agregado, e ela devolve **números, não times**. Nenhuma
    rota da urna individualiza declarante antes do lock — nem por lista, nem por
    `team_id`, nem separando drop de passo."""
    season = get_current_season()
    st = _urn_state(season)
    opens, closes = _schedule()
    mine = None
    if current_user.team_id:
        mine = LateDropDeclaration.query.filter_by(
            season=season, team_id=current_user.team_id).first()
    return jsonify({
        "season": season,
        "state": st["state"],
        "reason": st["reason"],
        "opens_at": utc_iso(opens) or None,
        "closes_at": utc_iso(closes) or None,
        "block_r1_rookie": _block_r1(),
        "is_admin": current_user.is_admin,
        "my_team_id": current_user.team_id,
        "my_team_name": current_user.team_rel.name if current_user.team_rel else None,
        # agregado: quantos bilhetes existem (drop OU passo — sem distinção)
        "declared_count": LateDropDeclaration.query.filter_by(season=season).count(),
        "total_teams": Team.query.count(),
        # e o próprio time (só o dono lê o próprio)
        "i_declared": bool(mine),
    })


# ── Owner: a própria declaração (sigilo — escopo current_user) ────────────────

@late_drop_bp.route("/api/late_drop/declaration")
@login_required
def get_my_declaration():
    """U1: devolve SÓ a declaração do próprio time. Não existe param de team_id."""
    if not current_user.team_id:
        return jsonify({"error": "Usuário sem time vinculado"}), 400
    season = get_current_season()
    d = LateDropDeclaration.query.filter_by(
        season=season, team_id=current_user.team_id).first()
    return jsonify({
        "team_id": current_user.team_id,
        "declared": bool(d),
        "player_id": d.player_id if d else None,
        "passed": bool(d and d.is_pass()),
    })


@late_drop_bp.route("/api/late_drop/declaration", methods=["POST"])
@login_required
def save_my_declaration():
    """U1/U4: uma marcação (jogador OU passo), substituível até o lock."""
    if not current_user.team_id:
        return jsonify({"error": "Usuário sem time vinculado"}), 400
    season = get_current_season()
    st = _urn_state(season)
    if st["state"] != "open":
        return jsonify({"error": "A urna não está aberta.", "reason": st["reason"]}), 409

    data = request.get_json() or {}
    if "player_id" not in data and "pass" not in data:
        return jsonify({"error": "Escolha um jogador ou 'não vou dropar ninguém'."}), 400
    raw = None if data.get("pass") else data.get("player_id")
    pid, err = _validate_choice(raw, current_user.team_id, season)
    if err:
        return jsonify({"error": err}), 400

    _upsert(season, current_user.team_id, pid, current_user.id)
    return jsonify({"success": True, "declared": True, "player_id": pid,
                    "passed": pid is None})


# ── Admin: agenda, flag do rookie, suprimento, lock/revelação ────────────────

@late_drop_bp.route("/api/late_drop/admin/schedule", methods=["POST"])
@admin_required
def admin_schedule():
    """U3: abre/fecha por horário definido pelo admin (instantes em UTC)."""
    season = get_current_season()
    if _urn_locked(season):
        return jsonify({"error": "Urna já revelada nesta season."}), 409
    data = request.get_json() or {}
    opens = _parse_iso_utc(data.get("opens_at"))
    closes = _parse_iso_utc(data.get("closes_at"))
    if data.get("opens_at") and not opens:
        return jsonify({"error": "Horário de abertura inválido."}), 400
    if data.get("closes_at") and not closes:
        return jsonify({"error": "Horário de fechamento inválido."}), 400
    if opens and closes and closes <= opens:
        return jsonify({"error": "O fechamento tem de ser depois da abertura."}), 400

    # Bloqueio mútuo: rollover pendente impede ABRIR/AGENDAR a urna. LIMPAR a agenda
    # (opens/closes vazios) é sempre permitido — é justamente o caminho de destravar.
    if opens or closes:
        motivo = rollover_blocks_urn()
        if motivo:
            return jsonify({"error": motivo, "blocked_by": "rollover_pendente"}), 409
    set_config(OPENS_KEY, utc_iso(opens) if opens else "")
    set_config(CLOSES_KEY, utc_iso(closes) if closes else "")
    st = _urn_state(season)
    return jsonify({"success": True, "state": st["state"], "reason": st["reason"],
                    "opens_at": utc_iso(opens) or None,
                    "closes_at": utc_iso(closes) or None})


@late_drop_bp.route("/api/late_drop/admin/config", methods=["POST"])
@admin_required
def admin_config():
    """U6: liga/desliga o bloqueio do rookie de 1ª rodada. Nasce OFF — o regulamento é
    silencioso e o código não arbitra regra em disputa."""
    data = request.get_json() or {}
    set_config(BLOCK_R1_KEY, "true" if data.get("block_r1_rookie") else "false")
    return jsonify({"success": True, "block_r1_rookie": _block_r1()})


@late_drop_bp.route("/api/late_drop/admin/declare", methods=["POST"])
@admin_required
def admin_declare_for_team():
    """Suprimento por time (escrita, nunca leitura do alheio).

    HIERARQUIA OWNER > ADMIN (herdada da janela, exercitada em produção no ensaio):
    time que JÁ DECLAROU PESSOALMENTE não é sobrescrito — recusa seca 409 expondo só
    **existência e autoria**, nunca o conteúdo. O owner sempre pode sobrescrever o
    suprimento do admin (o outro sentido da hierarquia)."""
    season = get_current_season()
    if _urn_locked(season):
        return jsonify({"error": "Urna já revelada."}), 409
    data = request.get_json() or {}
    try:
        team_id = int(data.get("team_id"))
    except (TypeError, ValueError):
        return jsonify({"error": "team_id inválido"}), 400
    if not db.session.get(Team, team_id):
        return jsonify({"error": "Time não encontrado"}), 404

    existing = LateDropDeclaration.query.filter_by(season=season, team_id=team_id).first()
    if (existing and existing.editor and existing.editor.team_id == team_id):
        return jsonify({"error": "Este time já declarou pessoalmente — a declaração do "
                                 "owner prevalece e o suprimento foi recusado. "
                                 "(O conteúdo permanece selado.)"}), 409

    raw = None if data.get("pass") else data.get("player_id")
    pid, err = _validate_choice(raw, team_id, season)
    if err:
        return jsonify({"error": err}), 400
    _upsert(season, team_id, pid, current_user.id)
    # Não devolve conteúdo — só confirma a escrita.
    return jsonify({"success": True, "team_id": team_id, "passed": pid is None})


def _build_snapshot(season: int) -> list:
    """Snapshot dos 12 times. Sem declaração = passo (U2). Jogador que saiu do roster
    entre o depósito e o lock = **passo com aviso** (U6) — a decisão não some da trilha,
    mas não vira drop.

    O `cut_ids` de cada entrada carrega 0 ou 1 id: é o que alimenta o hash canônico
    (mesma função da janela) e é, literalmente, **a lista de drops a executar**."""
    decls = {d.team_id: d for d in
             LateDropDeclaration.query.filter_by(season=season).all()}
    snapshot = []
    for team in Team.query.order_by(Team.id).all():
        d = decls.get(team.id)
        drop_id = drop_name = None
        invalidated, invalid_reason = False, None
        if d and d.player_id:
            p = db.session.get(Player, d.player_id)
            if p and p.team_id == team.id and not p.is_dropped:
                drop_id, drop_name = p.id, p.name
            else:
                invalidated = True
                drop_name = p.name if p else f"#{d.player_id}"
                invalid_reason = ("jogador não estava mais no roster do time no momento "
                                  "do lock — vale como passo")
        snapshot.append({
            "team_id": team.id,
            "team_name": team.name,
            "cut_ids": [drop_id] if drop_id else [],
            "drop_id": drop_id,
            "drop_name": drop_name,
            "declared": bool(d),
            "passed": bool(d and d.is_pass()),
            "invalidated": invalidated,
            "invalid_reason": invalid_reason,
        })
    return snapshot


def _persist(season, snapshot, previous_audit_id, reason):
    audit = LateDropAudit(
        season=season,
        declarations_json=_json.dumps(snapshot, ensure_ascii=False),
        executed_by=current_user.id if current_user.is_authenticated else None,
        result_hash=compute_cut_snapshot_hash(snapshot),
        previous_audit_id=previous_audit_id,
        reason=reason,
        is_canonical=True,
    )
    db.session.add(audit)
    db.session.commit()
    return audit


@late_drop_bp.route("/api/late_drop/admin/lock", methods=["POST"])
@admin_required
def admin_lock_reveal():
    """U5: lock + revelação simultânea. Congela o snapshot canônico."""
    season = get_current_season()
    if _urn_locked(season):
        return jsonify({
            "error": "Urna já revelada. Use /api/late_drop/admin/replace com justificativa."
        }), 409
    audit = _persist(season, _build_snapshot(season), None, None)
    return jsonify({"success": True, "audit": audit.to_dict()})


@late_drop_bp.route("/api/late_drop/admin/replace", methods=["POST"])
@admin_required
def admin_replace_reveal():
    """M8: re-executa a revelação. Exige reason; encadeia previous_audit_id."""
    season = get_current_season()
    data = request.get_json() or {}
    reason = (data.get("reason") or "").strip()
    if not reason:
        return jsonify({"error": "Campo 'reason' é obrigatório para re-execução"}), 400
    prev = LateDropAudit.query.filter_by(season=season, is_canonical=True).first()
    if not prev:
        return jsonify({"error": "Nenhum snapshot canônico. Use /lock primeiro."}), 404
    prev.is_canonical = False
    db.session.add(prev)
    audit = _persist(season, _build_snapshot(season), prev.id, reason)
    return jsonify({"success": True, "audit": audit.to_dict(),
                    "superseded_audit_id": prev.id})


# ── Revelação + verificação ───────────────────────────────────────────────────

@late_drop_bp.route("/api/late_drop/audit")
@login_required
def audit_read():
    """Pós-lock: a lista de drops a executar, visível a todos. Pré-lock: nada."""
    season = get_current_season()
    canonical = LateDropAudit.query.filter_by(season=season, is_canonical=True).first()
    if not canonical:
        return jsonify({"revealed": False})
    superseded = LateDropAudit.query.filter_by(
        season=season, is_canonical=False).order_by(LateDropAudit.id.desc()).all()
    data = canonical.to_dict()
    drops = [d for d in data["declarations"] if d["drop_id"]]
    return jsonify({
        "revealed": True,
        "audit": data,
        "drops_to_execute": drops,      # o produto da revelação (U7)
        "num_drops": len(drops),
        "superseded": [a.to_dict() for a in superseded],
    })


@late_drop_bp.route("/api/late_drop/audit/verify")
@login_required
def audit_verify():
    """M8: re-deriva o hash do snapshot canônico e compara com o gravado."""
    season = get_current_season()
    canonical = LateDropAudit.query.filter_by(season=season, is_canonical=True).first()
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
