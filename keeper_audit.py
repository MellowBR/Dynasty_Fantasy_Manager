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
  · `qualify(report, meta)`  — OFF26-22: decide se ESTA execução vale como GATE. Roda
                               DEPOIS do núcleo, sobre o relatório pronto — sheet
                               PROVISÓRIA não pode produzir "ABERTURA LIBERADA".

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

# ── OFF26-22: estágio da sheet — METADADO do relatório, NUNCA insumo do diff ──
#
# A sheet nasce do SYNC (U7) e tem dois estágios: PROVISÓRIA e DEFINITIVA. A auditoria
# é o GATE DE ABERTURA do leilão — e um veredito "liberada" sobre sheet provisória é
# liberação sobre dado que ainda vai mudar (o caso perigoso: drops revelados na urna e
# ainda não executados/sincronizados). Decisão do owner (08/08/2026): **rodar e
# DESQUALIFICAR o veredito** — a execução antecipada tem valor (as divergências
# continuam listadas), o que ela não pode é dizer "pode abrir".
#
# ⛔ A decisão "provisória × definitiva" NÃO é tomada aqui. Ela é calculada uma única
#    vez, em `routes.cuts._build_keeper_sheet`, e este módulo apenas a CONSOME. Não
#    replicar a regra (revelação da urna + sync posterior) em lugar nenhum.
# ⛔ O estágio viaja POR FORA da estrutura que o núcleo puro lê: `build_sheet` o entrega
#    na chave `stage_meta`, e `run_audit` a REMOVE antes de chamar `audit()`. O núcleo
#    nunca o vê, as fixtures congeladas seguem válidas e os 34 testes não mudam.
STAGE_DEFINITIVA = "definitiva"

VERDICT_LIBERADA = "liberada"
VERDICT_BLOQUEADA = "bloqueada"
VERDICT_NAO_QUALIFICADA = "nao_qualificada"   # rodou, vale como conferência, NÃO é gate

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

        # UX18: inviabilidade de completar o elenco, herdada da flag canônica do
        # `draft_budget` (via sheet). ⛔ É AVISO, no canal que já existe — **não** uma 5ª
        # classe de divergência (o D2 fixa quatro, e há teste que falha se alguém criar
        # outra). Ausente da sheet → `.get()` devolve None → nada acontece: as fixtures
        # congeladas seguem válidas sem edição.
        if team.get("cannot_fill_roster"):
            warnings.append(
                "Teto de lance não cobre as vagas abertas a $1 cada — com este elenco o "
                "time não consegue completar o roster no leilão (flag "
                "`cannot_fill_roster`).")

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
    """Estado da liga fantasma — INDEPENDENTE da existência da keeper sheet.

    Sem sheet não há diff, mas há o que mostrar: é a única prova de que o serviço
    ALCANÇA a API do Sleeper e de que a derivação do `draft_id` funciona **de onde
    ele roda**. Esses modos de falha são de AMBIENTE (egress, DNS, timeout do plano)
    e não aparecem em localhost — sem este bloco só seriam descobertos no dia em que
    a auditoria precisa funcionar. Serve também ao operador: com `league_id` errado
    no `AppConfig`, o erro fica silencioso até a sheet existir.

    `error` e `available` são estado PRÓPRIO deste bloco — não se confundem com o
    bloqueio por falta de insumo, que é do veredito.
    """
    b = board or {}
    cols = b.get("columns") or []
    com_owner = sum(1 for c in cols if _sid(c.get("owner_id")))
    meta = {k: b.get(k) for k in ("league_id", "league_name", "draft_id",
                                  "draft_status", "draft_type", "rounds", "budget")}
    meta.update({
        "num_designations": len(b.get("designations") or []),
        "columns_total": len(cols),
        "columns_with_owner": com_owner,
        "columns_without_owner": len(cols) - com_owner,
        "error": b.get("error"),
        # A contagem de owners MUDA entre leituras (três leituras num dia deram três
        # números) — é campo de relatório, nunca constante.
        "available": bool(b.get("league_id")) and not b.get("error"),
    })
    return meta


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


def _stage_meta(raw: dict) -> dict:
    """OFF26-22 — carimbo de estágio, CONSUMIDO da fonte (nunca recalculado aqui).

    `available` é a condição de insumo utilizável: a chave homônima da fonte E pelo
    menos um time. É o que revive o ramo "sem insumo" — o gate antigo
    (`if not raw.get("revealed")`) virou CÓDIGO MORTO no U7, porque a sheet passou a
    devolver `revealed: True` incondicionalmente. Código morto que aparenta proteger é
    pior que ausência de proteção.
    """
    stage = raw.get("stage")
    late_drop = raw.get("late_drop") or {}
    meta = {
        "stage": stage,
        "stage_label": raw.get("stage_label"),
        "sync_timestamp": raw.get("sync_timestamp"),
        "source": raw.get("source"),
        "late_drop": late_drop,
        "available": bool(raw.get("available")) and bool(raw.get("teams")),
        "is_definitiva": stage == STAGE_DEFINITIVA,
    }
    # O que falta para virar DEFINITIVA — dito com o carimbo, não em abstrato.
    if meta["is_definitiva"]:
        meta["missing"] = None
    elif not late_drop.get("revealed"):
        meta["missing"] = ("A urna do late drop ainda não foi revelada. Até 22/08 os "
                           "keepers podem mudar em até um jogador por time.")
    else:
        meta["missing"] = (
            f"A urna revelou {late_drop.get('num_drops', 0)} drop(s) em "
            f"{late_drop.get('executed_at') or '—'}, mas o último sync é de "
            f"{meta['sync_timestamp'] or 'nenhum'} — não houve sync DEPOIS da revelação. "
            f"Execute os drops no Sleeper e rode o sync final.")
    return meta


def build_sheet(season: int | None = None) -> dict:
    """Lado Manager. Consome a keeper sheet canônica do OFF26-2 (fonte única) e a
    enriquece com `sleeper_player_id` por RE-QUERY — D3: entre incluir o campo no
    payload da sheet e re-consultar, vence quem NÃO mexe em item pendente de smoke.

    OFF26-22: entrega também `stage_meta` — metadado do relatório que `run_audit`
    REMOVE antes de chamar o núcleo puro. O núcleo continua vendo exatamente o mesmo
    formato de sempre."""
    from models import Player, Team
    from routes.cuts import _build_keeper_sheet

    season = season or get_current_season()
    raw = _build_keeper_sheet(season)
    meta = _stage_meta(raw)
    if not meta["available"]:
        return {"revealed": False, "season": season, "stage_meta": meta}

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
            # UX18: repasse da flag canônica (o produtor é `routes/cuts`). `.get()` para
            # a sheet legada/congelada sem a chave seguir funcionando.
            "cannot_fill_roster": t.get("cannot_fill_roster"),
        })
    return {"revealed": True, "season": season,
            "lock_timestamp": raw.get("lock_timestamp"), "teams": teams,
            "stage_meta": meta}


def qualify(report: dict, meta: dict | None) -> dict:
    """OFF26-22 — decide se ESTA execução vale como GATE de abertura do leilão.

    Roda DEPOIS do núcleo puro, sobre o relatório pronto: o diff é o mesmo, o que muda
    é a autoridade do veredito. Três saídas:

      · sheet **DEFINITIVA**  → nada muda (o veredito do núcleo vale como gate);
      · sheet **PROVISÓRIA**  → `verdict = nao_qualificada`. A auditoria rodou, o
        relatório está completo e as divergências continuam listadas (é o valor da
        conferência antecipada) — mas "ABERTURA LIBERADA" fica **impossível**, porque
        a sheet ainda vai mudar. O motivo do estágio entra em PRIMEIRO nos
        `blocking_reasons`, à frente do que o diff achou;
      · sheet **indisponível** → o bloqueio por falta de insumo do núcleo é preservado,
        com a causa real prefixada (a frase do núcleo fala da "janela de cortes", que o
        U7 aposentou; corrigi-la exigiria mexer no núcleo — ver resíduo no OFF26-22).

    `gate_qualified` é o campo booleano: é o que um consumidor deve ler, não a string.
    """
    meta = dict(meta or {})
    report["sheet_stage"] = meta

    if not meta:                                    # sem carimbo (chamada sem meta)
        report["gate_qualified"] = report.get("verdict") == VERDICT_LIBERADA
        return report

    if not meta.get("available"):
        report["gate_qualified"] = False
        report["blocking_reasons"] = [
            "Keeper sheet indisponível (nenhum time na sheet) — sem os dois lados não "
            "há diff, e esta execução não vale como gate."
        ] + list(report.get("blocking_reasons") or [])
        return report

    if meta.get("is_definitiva"):
        report["gate_qualified"] = report.get("verdict") == VERDICT_LIBERADA
        return report

    report["gate_qualified"] = False
    report["verdict"] = VERDICT_NAO_QUALIFICADA
    report["blocking_reasons"] = [
        f"Keeper sheet {meta.get('stage_label') or 'PROVISÓRIA'} — esta execução é "
        f"CONFERÊNCIA ANTECIPADA e NÃO vale como gate de abertura. {meta.get('missing')}"
    ] + list(report.get("blocking_reasons") or [])
    return report


def run_audit(season: int | None = None) -> dict:
    """Porta única de execução: lê os dois lados e roda o núcleo. Read-only ponta a
    ponta — nenhuma escrita, nem no Sleeper nem no banco.

    Os dois lados são lidos SEMPRE, e um não depende do outro: sem sheet não há diff,
    mas o estado da liga continua sendo lido e exibido. Falha na leitura da liga vira
    `error` no bloco de meta — nunca 500, nunca página pendurada."""
    sheet = build_sheet(season)
    # ⛔ OFF26-22: o carimbo SAI da sheet antes do núcleo. O núcleo puro recebe
    #    exatamente o formato de sempre — é o que mantém as fixtures congeladas válidas.
    stage_meta = sheet.pop("stage_meta", None)
    league_id = get_phantom_league_id()
    if not league_id:
        board = {"error": "Liga fantasma não configurada — informe o `league_id` "
                          "no admin."}
    else:
        try:
            board = fetch_board(league_id)
        except Exception as e:      # rede/parse fora do que `_get` já absorve
            board = {"error": f"Falha ao ler a liga {league_id}: {e}"}
    return qualify(audit(board, sheet), stage_meta)
