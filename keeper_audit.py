"""
keeper_audit.py — OFF26-4 (F2): auditoria de keepers pré-leilão.

⛔ NÃO É CONFERÊNCIA DE CAP — É GATE DE INTEGRIDADE DO LEILÃO.
   Um keeper que não esteja designado no board da liga fantasma é, para o Sleeper,
   JOGADOR DISPONÍVEL: qualquer owner pode nomeá-lo e o lance é processado
   normalmente. Isso não é erro de contabilidade que se corrige depois — é transação
   inválida ao vivo, sem desfazer limpo. Por isso a classe "keeper ausente do board"
   é BLOQUEANTE DE ABERTURA, e não uma divergência qualquer.

Organização (mesmo princípio de `salary_engine`: o núcleo é puro):
  · `audit(board, sheet)`   — NÚCLEO PURO: sem DB, sem rede. É o que os testes exercem.
  · `fetch_board(league_id)` — leitura READ-ONLY da API (só GET) → formato do núcleo.
  · `build_sheet(season)`    — lado Manager: consome a keeper sheet do OFF26-2 e a
                               enriquece com `sleeper_player_id` por RE-QUERY (D3 —
                               o caminho que NÃO toca o OFF26-2, ainda sob smoke).

Invariantes carregadas do terreno (medidas, não supostas):
  · `draft_id` NUNCA é persistido — derivado do `league_id` a cada uso (D1).
  · Identidade de jogador SÓ por `sleeper_id`, nunca por nome (incidente "Brown").
  · Ponte de time SÓ por `sleeper_owner_id`, nunca por nome (D6): `metadata.team_name`
    veio nulo em 8/8 dos owners da fantasma, e há dois Rafas entre eles.
  · `player_id` de DEF é SIGLA ("LAR") — nunca coagir a inteiro.
  · `metadata.amount` é STRING — coagir na leitura.
  · Contagem de rodadas: a do DRAFT (`draft.settings.rounds`), não a da liga.
"""
from collections import defaultdict

from models import get_config, get_current_season
import sync_sleeper as ss

# Chave do AppConfig (D1) — persiste-se APENAS o league_id, que é estável.
PHANTOM_LEAGUE_KEY = "phantom_league_id"

# ── Classes de divergência (D5, ajustado) ────────────────────────────────────
# A classe "slot errado" NÃO existe: `pick_no`/`round` não indicam vaga e a
# atribuição é automática por posição. Não inventá-la.
CLS_MISSING = "keeper_ausente_do_board"
CLS_SALARY = "salario_divergente"
CLS_WRONG_TEAM = "time_errado"
CLS_EXTRA = "fora_da_sheet"

CLASS_LABEL = {
    CLS_MISSING: "Keeper ausente do board",
    CLS_SALARY: "Salário divergente",
    CLS_WRONG_TEAM: "Keeper no time errado",
    CLS_EXTRA: "No board, fora da sheet",
}

# Severidade: a da classe 1 NÃO é escolha de desenho (é bloqueante por natureza);
# as demais são relativas entre si.
SEVERITY = {
    CLS_MISSING: "bloqueante",
    CLS_WRONG_TEAM: "alta",
    CLS_SALARY: "alta",
    CLS_EXTRA: "media",
}

# ── Estados de time (D4) — estado NÃO é divergência ──────────────────────────
ST_OK = "ok"
ST_UNPOPULATED = "nao_populado"     # coluna existe e está vazia (pode ser OFF26-10)
ST_NO_COLUMN = "sem_coluna"         # nenhuma coluna da fantasma tem o owner do time

STATE_LABEL = {
    ST_OK: "Populado",
    ST_UNPOPULATED: "Não populado",
    ST_NO_COLUMN: "Sem coluna na fantasma",
}


def _to_int(v, default=0):
    """`metadata.amount` vem como STRING da API. Nunca coagir `player_id`."""
    try:
        return int(str(v).strip())
    except (TypeError, ValueError):
        return default


def _sid(v):
    """Id de jogador é STRING sempre — DEF vem como sigla ('LAR')."""
    s = str(v or "").strip()
    return s or None


# ══════════════════════════════════════════════════════════════════════════════
# NÚCLEO PURO — sem DB, sem rede. Entra dado, sai relatório.
# ══════════════════════════════════════════════════════════════════════════════

def audit(board: dict, sheet: dict) -> dict:
    """Compara o board da liga fantasma com a keeper sheet e devolve o relatório
    dos 12 times de uma vez (D4). Função pura: os testes a exercem com fixtures.

    board: {league_id, league_name, draft_id, draft_status, draft_type, rounds,
            budget, columns:[{roster_id, owner_id}], designations:[{roster_id,
            sleeper_player_id, name, position, amount}]}
    sheet: {revealed, season, lock_timestamp, teams:[{team_id, team_name,
            sleeper_owner_id, fa_budget, keepers:[(sid, nome, pos, salario)]}]}
    """
    if not sheet or not sheet.get("revealed"):
        # Sem insumo NÃO se acusa 12 times de keeper ausente — diz-se o que falta.
        return _no_input(
            "A janela de cortes ainda não foi revelada — a keeper sheet não existe. "
            "Sem os dois lados não há o que comparar (a auditoria não acusa ausência "
            "por falta de insumo).", board, sheet)
    if not board or board.get("error"):
        return _no_input(
            (board or {}).get("error") or "Board da liga fantasma indisponível.",
            board, sheet)

    columns = board.get("columns") or []
    column_by_owner = {}
    for col in columns:
        oid = _sid(col.get("owner_id"))
        if oid:
            column_by_owner[oid] = str(col.get("roster_id"))

    # ── lado board, por roster e por jogador ────────────────────────────────
    board_by_roster = defaultdict(list)
    board_by_sid = {}
    for des in board.get("designations") or []:
        sid = _sid(des.get("sleeper_player_id"))
        rid = str(des.get("roster_id"))
        item = {
            "sleeper_player_id": sid, "roster_id": rid,
            "name": des.get("name"), "position": des.get("position"),
            "amount": _to_int(des.get("amount")),
        }
        board_by_roster[rid].append(item)
        if sid:
            board_by_sid[sid] = item

    # ── lado sheet, por jogador ─────────────────────────────────────────────
    sheet_by_sid = {}
    for team in sheet.get("teams") or []:
        for kp in team.get("keepers") or []:
            sid = _sid(kp[0])
            if sid:
                sheet_by_sid[sid] = {
                    "team_id": team["team_id"], "team_name": team["team_name"],
                    "name": kp[1], "position": kp[2], "salary": _to_int(kp[3]),
                }

    rounds = board.get("rounds")
    teams_out, claimed_rosters = [], set()

    for team in sheet.get("teams") or []:
        oid = _sid(team.get("sleeper_owner_id"))
        rid = column_by_owner.get(oid) if oid else None
        if rid:
            claimed_rosters.add(rid)
        designations = board_by_roster.get(rid, []) if rid else []
        populated = bool(designations)
        keepers = team.get("keepers") or []

        if rid is None:
            state = ST_NO_COLUMN
        elif not populated:
            state = ST_UNPOPULATED
        else:
            state = ST_OK

        findings, warnings = [], []
        unresolved = 0

        for kp in keepers:
            sid = _sid(kp[0])
            if not sid:
                # Identidade não resolvível: NÃO é divergência — é limite de insumo.
                # Nunca cair para nome (incidente "Brown").
                unresolved += 1
                warnings.append(
                    f"{kp[1]}: sem `sleeper_player_id` no Manager — presença no board "
                    f"não verificável (identidade só por sleeper_id).")
                continue
            on_board = board_by_sid.get(sid)
            if on_board is None:
                # Só acusa ausência onde HÁ board: num time não populado a ausência
                # já está dita pelo estado (D4) e repeti-la por keeper é alarme falso.
                if populated:
                    findings.append(_finding(
                        CLS_MISSING, sid, kp[1], kp[2], sheet_salary=_to_int(kp[3]),
                        detail="Na sheet, ausente do board: EXPOSTO AO LEILÃO — "
                               "qualquer owner pode arrematá-lo."))
                continue
            if on_board["roster_id"] != rid:
                # Cross-team: UMA divergência, não duas (senão o mesmo erro apareceria
                # como 'ausente' aqui e 'fora da sheet' lá).
                findings.append(_finding(
                    CLS_WRONG_TEAM, sid, kp[1], kp[2],
                    sheet_salary=_to_int(kp[3]), board_amount=on_board["amount"],
                    board_roster_id=on_board["roster_id"],
                    detail=f"Sheet diz {team['team_name']}; board designou na coluna "
                           f"{on_board['roster_id']}."))
                continue
            if on_board["amount"] != _to_int(kp[3]):
                findings.append(_finding(
                    CLS_SALARY, sid, kp[1], kp[2], sheet_salary=_to_int(kp[3]),
                    board_amount=on_board["amount"],
                    detail=f"Sheet ${_to_int(kp[3])} × board ${on_board['amount']}."))

        for item in designations:
            sid = item["sleeper_player_id"]
            if sid and sid not in sheet_by_sid:
                findings.append(_finding(
                    CLS_EXTRA, sid, item["name"], item["position"],
                    board_amount=item["amount"],
                    detail="Designado no board e ausente da keeper sheet."))

        if rounds and len(keepers) > rounds:
            warnings.append(
                f"{len(keepers)} keepers para {rounds} vagas na sala — não cabem "
                f"(ressalva aritmética do D2).")

        board_total = sum(i["amount"] for i in designations)
        sheet_total = sum(_to_int(k[3]) for k in keepers)
        teams_out.append({
            "team_id": team["team_id"], "team_name": team["team_name"],
            "sleeper_owner_id": oid, "roster_id": rid,
            "state": state, "state_label": STATE_LABEL[state],
            "num_keepers_sheet": len(keepers), "num_designations": len(designations),
            "sheet_total": sheet_total, "board_total": board_total,
            "fa_budget": team.get("fa_budget"),          # usable_draft_budget (D2)
            "unresolved_keepers": unresolved,
            "findings": findings, "warnings": warnings,
        })

    # ── colunas sem dono: NÃO atribuíveis a time nenhum ─────────────────────
    orphan_columns = []
    for col in columns:
        rid = str(col.get("roster_id"))
        if _sid(col.get("owner_id")):
            continue
        des = board_by_roster.get(rid, [])
        orphan_columns.append({
            "roster_id": rid, "num_designations": len(des),
            "board_total": sum(i["amount"] for i in des),
        })

    # Coluna com dono que não bate com nenhum time da sheet (owner fora do Manager).
    for col in columns:
        rid = str(col.get("roster_id"))
        oid = _sid(col.get("owner_id"))
        if oid and rid not in claimed_rosters:
            des = board_by_roster.get(rid, [])
            orphan_columns.append({
                "roster_id": rid, "owner_id": oid, "num_designations": len(des),
                "board_total": sum(i["amount"] for i in des),
                "note": "owner sem time correspondente no Manager",
            })

    return _finish(board, sheet, teams_out, orphan_columns)


def _finding(cls, sid, name, position, sheet_salary=None, board_amount=None,
             board_roster_id=None, detail=""):
    return {
        "class": cls, "class_label": CLASS_LABEL[cls], "severity": SEVERITY[cls],
        "blocking": SEVERITY[cls] == "bloqueante",
        "sleeper_player_id": sid, "player": name, "position": position,
        "sheet_salary": sheet_salary, "board_amount": board_amount,
        "board_roster_id": board_roster_id, "detail": detail,
    }


def _no_input(reason, board, sheet):
    """Insumo faltando: o relatório DIZ isso — não vira 12 falsos positivos."""
    return {
        "ok": False, "reason": reason, "verdict": "bloqueada",
        "blocking_reasons": [reason],
        "league": _league_meta(board), "season": (sheet or {}).get("season"),
        "lock_timestamp": (sheet or {}).get("lock_timestamp"),
        "summary": {"teams": 0, "populated": 0, "unpopulated": 0, "no_column": 0,
                    "divergences": 0, "blocking_findings": 0, "orphan_columns": 0,
                    "unresolved_keepers": 0},
        "teams": [], "orphan_columns": [],
    }


def _league_meta(board):
    b = board or {}
    return {k: b.get(k) for k in ("league_id", "league_name", "draft_id",
                                 "draft_status", "draft_type", "rounds", "budget")}


def _finish(board, sheet, teams_out, orphan_columns):
    divergences = sum(len(t["findings"]) for t in teams_out)
    blocking = sum(1 for t in teams_out for f in t["findings"] if f["blocking"])
    unpopulated = [t for t in teams_out if t["state"] == ST_UNPOPULATED]
    no_column = [t for t in teams_out if t["state"] == ST_NO_COLUMN]
    unresolved = sum(t["unresolved_keepers"] for t in teams_out)

    reasons = []
    if blocking:
        reasons.append(
            f"{blocking} keeper(s) na sheet e ausente(s) do board — expostos ao leilão.")
    if unpopulated:
        reasons.append(
            f"{len(unpopulated)} time(s) não populado(s): "
            f"{', '.join(t['team_name'] for t in unpopulated)} — os keepers desses "
            f"times estão expostos pelo mesmo motivo, ainda que não seja divergência.")
    if no_column:
        reasons.append(
            f"{len(no_column)} time(s) sem coluna atribuída na fantasma: "
            f"{', '.join(t['team_name'] for t in no_column)} — convite não aceito "
            f"(cobertura do D6).")
    if orphan_columns:
        reasons.append(
            f"{len(orphan_columns)} coluna(s) não atribuível(is) a time do Manager.")
    if unresolved:
        reasons.append(
            f"{unresolved} keeper(s) sem `sleeper_player_id` — auditoria incompleta "
            f"para esses jogadores.")

    for t in teams_out:                     # pior primeiro: gate se lê de cima
        t["_rank"] = (
            0 if any(f["blocking"] for f in t["findings"]) else
            1 if t["findings"] else
            2 if t["state"] != ST_OK else 3)
    teams_out.sort(key=lambda t: (t["_rank"], t["team_name"].lower()))
    for t in teams_out:
        t.pop("_rank")

    return {
        "ok": True,
        "verdict": "bloqueada" if reasons else "liberada",
        "blocking_reasons": reasons,
        "reason": None,
        "league": _league_meta(board),
        "season": sheet.get("season"),
        "lock_timestamp": sheet.get("lock_timestamp"),
        "summary": {
            "teams": len(teams_out),
            "populated": sum(1 for t in teams_out if t["state"] == ST_OK),
            "unpopulated": len(unpopulated), "no_column": len(no_column),
            "divergences": divergences, "blocking_findings": blocking,
            "orphan_columns": len(orphan_columns), "unresolved_keepers": unresolved,
        },
        "teams": teams_out,
        "orphan_columns": orphan_columns,
    }


# ══════════════════════════════════════════════════════════════════════════════
# LEITURA (read-only) — só GET. Nada aqui escreve na plataforma.
# ══════════════════════════════════════════════════════════════════════════════

def get_phantom_league_id() -> str:
    """D1: o `league_id` (estável) mora no AppConfig; o `draft_id` NUNCA."""
    return (get_config(PHANTOM_LEAGUE_KEY, "") or "").strip()


def fetch_board(league_id: str, timeout: int = 15) -> dict:
    """Lê o board da liga fantasma. `draft_id` DERIVADO do `league_id` a cada uso —
    ele muda a cada RESET DRAFT e nenhuma forma de persistência é aceitável (D1).
    Draft morto responde 404 limpo (~0,2 s); o timeout explícito é boa prática,
    não mitigação — o travamento em LOADING é do app web, não desta porta."""
    if not league_id:
        return {"error": "Liga fantasma não configurada — informe o `league_id` no admin."}

    league = ss._get(f"{ss.BASE_URL}/league/{league_id}", timeout=timeout)
    if not league:
        return {"error": f"Liga {league_id} não respondeu na API do Sleeper "
                         f"(id errado, liga apagada ou API fora)."}

    draft_id = league.get("draft_id")       # vem no próprio objeto da liga (1 request)
    if not draft_id:
        return {"error": f"A liga {league_id} não tem draft associado."}

    draft = ss._get(f"{ss.BASE_URL}/draft/{draft_id}", timeout=timeout)
    if not draft:
        return {"error": f"Draft {draft_id} não respondeu (provável RESET DRAFT: o id "
                         f"muda e o anterior morre). Recarregue a auditoria."}

    picks = ss._get(f"{ss.BASE_URL}/draft/{draft_id}/picks", timeout=timeout) or []
    rosters = ss._get(f"{ss.BASE_URL}/league/{league_id}/rosters", timeout=timeout) or []
    settings = draft.get("settings") or {}

    designations = []
    for pk in picks:
        md = pk.get("metadata") or {}
        designations.append({
            "roster_id": str(pk.get("roster_id")),
            "sleeper_player_id": _sid(pk.get("player_id")),   # DEF vem como sigla
            "name": (f"{md.get('first_name', '')} {md.get('last_name', '')}".strip()
                     or _sid(pk.get("player_id"))),
            "position": md.get("position"),
            "amount": md.get("amount"),                       # string — coagido depois
        })

    return {
        "league_id": str(league_id),
        "league_name": league.get("name"),
        "draft_id": str(draft_id),
        "draft_status": draft.get("status"),
        "draft_type": draft.get("type"),
        "rounds": settings.get("rounds"),        # do DRAFT, não `league.settings`
        "budget": settings.get("budget"),
        "columns": [{"roster_id": str(r.get("roster_id")),
                     "owner_id": _sid(r.get("owner_id"))} for r in rosters],
        "designations": designations,
    }


def build_sheet(season: int | None = None) -> dict:
    """Lado Manager. Consome a keeper sheet canônica do OFF26-2 (fonte única) e a
    enriquece com `sleeper_player_id` por RE-QUERY — D3: entre incluir o campo no
    payload da sheet e re-consultar, vence quem NÃO mexe em item pendente de smoke."""
    from models import Player, Team
    from routes.cuts import _build_keeper_sheet

    season = season or get_current_season()
    raw = _build_keeper_sheet(season)
    if not raw.get("revealed"):
        return {"revealed": False, "season": season}

    teams = []
    for t in raw["teams"]:
        db_team = Team.query.get(t["team_id"])
        ids = [k["id"] for k in t["keepers"]]
        players = ({p.id: p for p in Player.query.filter(Player.id.in_(ids)).all()}
                   if ids else {})
        keepers = []
        for k in t["keepers"]:
            p = players.get(k["id"])
            keepers.append((_sid(p.sleeper_player_id) if p else None,
                            k["name"], k["position"], int(k["salary"])))
        teams.append({
            "team_id": t["team_id"], "team_name": t["team_name"],
            "sleeper_owner_id": _sid(db_team.sleeper_owner_id) if db_team else None,
            "fa_budget": t["fa_budget"], "keepers": keepers,
        })
    return {"revealed": True, "season": season,
            "lock_timestamp": raw.get("lock_timestamp"), "teams": teams}


def run_audit(season: int | None = None) -> dict:
    """Porta única de execução: lê os dois lados e roda o núcleo. Read-only ponta a
    ponta — nenhuma escrita, nem no Sleeper nem no banco."""
    sheet = build_sheet(season)
    league_id = get_phantom_league_id()
    board = fetch_board(league_id) if league_id else {
        "error": "Liga fantasma não configurada — informe o `league_id` no admin."}
    return audit(board, sheet)
