"""
core.py — núcleo PURO do script de população (OFF26-24). Sem rede, sem browser, sem FS.

Mesma separação do salary_engine/keeper_audit: tudo que decide vive aqui e é testável
(`phantom_board_test.py`); IO fica em `sleeper_api.py` (rede) e `board.py` (browser).

Armadilhas herdadas do OFF26-4 (medidas lá, respeitadas aqui):
- `player_id` de DEF é SIGLA ("LAR") — nunca coagir a inteiro;
- `metadata.amount` é STRING;
- identidade de jogador por sid e de time por owner_id — nunca por nome.
"""


def league_guard(draft_obj: dict, expected_league_id: str):
    """⛔ Guarda de nascença: o draft derivado tem de pertencer à liga fantasma.
    Retorna None se ok; string de erro (para abort barulhento) se não."""
    if not draft_obj:
        return "Draft não encontrado — nada a fazer."
    got = str(draft_obj.get("league_id") or "")
    if got != str(expected_league_id):
        return (f"GUARDA DE LIGA: o draft pertence à liga {got or '?'}, não à fantasma "
                f"{expected_league_id}. Recusando QUALQUER interação.")
    return None


def url_guard(page_url: str, derived_draft_id: str):
    """⛔ Identidade do board POR CONSTRUÇÃO (fix do 1º probe, 11/08): a prova de que
    o board aberto é o certo é a URL conter o draft_id que o script DERIVOU da
    LEAGUE_ID pela API — derivação → navegação → conferência. Texto de título não é
    gate (a página do draft não exibe o nome da liga). Retorna None ou erro."""
    if not derived_draft_id:
        return "Sem draft_id derivado — nada a conferir."
    if derived_draft_id not in str(page_url or ""):
        return (f"GUARDA DE IDENTIDADE: a URL do board ({page_url or '?'}) não contém "
                f"o draft_id derivado da liga fantasma ({derived_draft_id}) — houve "
                f"redirect ou a página não é o board esperado. Nenhum clique será "
                f"feito.")
    return None


def parse_pick(pick: dict) -> dict:
    """Normaliza um pick da API `/v1/draft/<id>/picks` para o que o casamento usa.
    sid SEMPRE string (DEF é sigla); amount int quando presente (vem string)."""
    meta = pick.get("metadata") or {}
    amount = meta.get("amount")
    try:
        amount = int(amount) if amount not in (None, "") else None
    except (TypeError, ValueError):
        amount = None
    return {
        "sid": str(pick.get("player_id") or ""),
        "slot": pick.get("draft_slot"),
        "roster_id": pick.get("roster_id"),
        "picked_by": str(pick.get("picked_by") or ""),
        "amount": amount,
        "name": f"{meta.get('first_name', '')} {meta.get('last_name', '')}".strip(),
        "position": meta.get("position") or "",
    }


def build_slot_map(draft_obj: dict, users: list) -> dict:
    """Mapa Team N (slot) ↔ owner, derivado SEMPRE da API (`draft_order` inverte
    user_id→slot; `users` dá o handle). O mapa do ensaio de 11/08 é fixture de
    conferência nos testes, nunca fonte."""
    handles = {str(u.get("user_id")): (u.get("display_name") or "")
               for u in (users or [])}
    slot_map = {}
    for user_id, slot in (draft_obj.get("draft_order") or {}).items():
        slot_map[int(slot)] = {"user_id": str(user_id),
                               "handle": handles.get(str(user_id), "")}
    return slot_map


def slot_map_from_rosters(draft_obj: dict, rosters: list, users: list) -> dict:
    """FIX3 (11/08): fallback (b) — `slot_to_roster_id` (presente MESMO em pre_draft
    com `draft_order` null, medido no draft real) × rosters da liga (roster→owner) ×
    users (handle). Composição 100% API, sem ambiguidade."""
    handles = {str(u.get("user_id")): (u.get("display_name") or "")
               for u in (users or [])}
    owner_by_roster = {r.get("roster_id"): str(r.get("owner_id") or "")
                       for r in (rosters or [])}
    out = {}
    for slot, roster_id in (draft_obj.get("slot_to_roster_id") or {}).items():
        owner = owner_by_roster.get(roster_id, "")
        if owner:
            out[int(slot)] = {"user_id": owner, "handle": handles.get(owner, "")}
    return out


def slot_map_from_picks(picks: list, users: list) -> dict:
    """FIX3 — fallback (c): slots OBSERVADOS nos picks existentes (`draft_slot` ×
    `picked_by`). Parcial por natureza (só times que já têm pick) — entra por último."""
    handles = {str(u.get("user_id")): (u.get("display_name") or "")
               for u in (users or [])}
    out = {}
    for raw in picks or []:
        p = parse_pick(raw)
        if p["slot"] and p["picked_by"]:
            out[int(p["slot"])] = {"user_id": p["picked_by"],
                                   "handle": handles.get(p["picked_by"], "")}
    return out


def resolve_slot_map(draft_obj: dict, users: list, rosters: list = None,
                     picks: list = None):
    """FIX3 — cadeia em ordem de confiança: (a) `draft_order` quando presente;
    (b) `slot_to_roster_id` × rosters; (c) slots observados nos picks. Retorna
    (mapa, fonte) — a fonte vai ao relatório JSON (rastreabilidade). Mapa vazio =
    nenhuma fonte serviu; quem chama aborta nomeando o que faltou. A confirmação
    final continua sendo o DOM no fluxo ("for Team {N}"), nunca fonte primária."""
    m = build_slot_map(draft_obj, users)
    if m:
        return m, "draft_order"
    m = slot_map_from_rosters(draft_obj, rosters or [], users)
    if m:
        return m, "slot_to_roster_id×rosters"
    m = slot_map_from_picks(picks or [], users)
    if m:
        return m, "picks_observados"
    return {}, "nenhuma"


def flatten_sheet(sheet: dict) -> list:
    """Achata o pacote do build_sheet (endpoint `/api/admin/keeper_sheet_export`)
    em linhas {sid, name, position, salary, team_name, owner_id}.
    ⛔ A DEFINIÇÃO de keeper é a do build_sheet — nada é re-derivado aqui."""
    rows = []
    for t in sheet.get("teams", []):
        for k in t.get("keepers", []):
            rows.append({
                "sid": str(k.get("sleeper_player_id") or ""),
                "name": k.get("name", ""),
                "position": k.get("position", ""),
                "salary": int(k.get("salary") or 0),
                "team_name": t.get("team_name", ""),
                "owner_id": str(t.get("sleeper_owner_id") or ""),
            })
    return rows


def match_picks_to_sheet(picks: list, sheet_rows: list, slot_map: dict) -> dict:
    """Casa os picks vivos do board com a keeper sheet, POR SID.

    Devolve o relatório da validação read-only:
    - matched: sid nos dois lados, salário e owner conferem;
    - salary_divergent: sid casou mas o amount difere do salário da sheet;
    - owner_divergent: sid casou mas o pick está no slot de OUTRO owner;
    - picks_not_in_sheet: no board e fora da sheet (em ensaio: designação de teste);
    - sheet_missing: keepers da sheet ainda sem pick (esperado até a população).
    """
    by_sid = {r["sid"]: r for r in sheet_rows if r["sid"]}
    matched, salary_div, owner_div, extra = [], [], [], []
    seen = set()
    for raw in picks:
        p = parse_pick(raw)
        seen.add(p["sid"])
        row = by_sid.get(p["sid"])
        if row is None:
            extra.append(p)
            continue
        slot_owner = (slot_map.get(p["slot"]) or {}).get("user_id", "")
        entry = {"sid": p["sid"], "name": row["name"], "team_name": row["team_name"],
                 "sheet_salary": row["salary"], "pick_amount": p["amount"],
                 "slot": p["slot"]}
        if row["owner_id"] and slot_owner and row["owner_id"] != slot_owner:
            owner_div.append(entry)
        elif p["amount"] is not None and p["amount"] != row["salary"]:
            salary_div.append(entry)
        else:
            matched.append(entry)
    missing = [r for r in sheet_rows if r["sid"] and r["sid"] not in seen]
    return {"matched": matched, "salary_divergent": salary_div,
            "owner_divergent": owner_div, "picks_not_in_sheet": extra,
            "sheet_missing": missing}


def team_totals(report: dict, team_name: str) -> dict:
    """Contagem + soma dos picks casados de um time — a conferência da F2a
    (ensaio de 11/08: MellowBR, 18 picks, $176)."""
    rows = [m for m in report["matched"] if m["team_name"] == team_name]
    return {"team_name": team_name, "count": len(rows),
            "total": sum(m["sheet_salary"] for m in rows)}


def choose_menu_item(menu_texts: list, team_slot: int,
                     set_title: str = "Set Player",
                     change_title: str = "Change Player",
                     desc_prefix: str = "Manually set a player for Team "):
    """FIX4 — decisão PURA sobre o menu de contexto aberto. Retorna (ação, detalhe):
    - ("click", i): o item i é "Set Player ... for Team {N}" com o N esperado
      (o N casa por FRONTEIRA — "for Team 1" não casa slot 10 nem vice-versa);
    - ("abort", "change_player"): menu de célula PREENCHIDA — célula errada, NUNCA
      prosseguir (o call log real: "Change Player" interceptou 30s de retries);
    - ("abort", "wrong_team"): Set Player de OUTRO time — a correspondência
      coluna↔slot quebrou; fechar e abortar (nada de tentar a próxima);
    - ("abort", "no_menu"): nenhum item reconhecível."""
    import re as _re
    pat = _re.compile(_re.escape(f"{desc_prefix}{team_slot}") + r"(?!\d)")
    wrong_team = False
    for i, text in enumerate(menu_texts or []):
        t = text or ""
        if change_title.lower() in t.lower():
            return ("abort", "change_player")
        if pat.search(t):
            return ("click", i)
        if set_title.lower() in t.lower():
            wrong_team = True
    return ("abort", "wrong_team" if wrong_team else "no_menu")


# ── Assentamento: a decisão pós-comando (comando via DOM, verdade via API) ──────

SETTLED = "assentado"
ALREADY = "duplicata_ja_assentado"
PENDING = "pendente"
TIMEOUT = "timeout"


def settlement_decision(sid: str, present_before: bool, present_now: bool,
                        polls_exhausted: bool) -> str:
    """O toast NUNCA é veredito — a API decide.
    - presente agora e já estava antes do comando → duplicata (sucesso: o servidor
      rejeita pick duplicado, o estado é o desejado);
    - presente agora → assentado;
    - ausente com polls esgotados → timeout (candidato a re-comando; caso Caleb:
      staging revertido);
    - ausente ainda dentro da janela → pendente (continuar polling; lag ~3s)."""
    if present_now:
        return ALREADY if present_before else SETTLED
    return TIMEOUT if polls_exhausted else PENDING
