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


# ── Anti-homônimo: parser do DOM real da linha de resultado (FIX5) ─────────────

_ROW_POSITIONS = {"QB", "RB", "WR", "TE", "K", "DEF", "DST", "D/ST", "FLEX"}


def _is_multi_position_label(token_upper):
    """FIX11 — token compound tipo "DB,WR" (caso Travis Hunter, probe de 12/08):
    é rótulo de posição se tiver 2+ partes nos separadores (,/) e ao menos UMA
    parte pertencer ao vocabulário — "DB" não precisa estar no vocabulário para
    o rótulo inteiro ser reconhecido e preservado ÍNTEGRO. Puro."""
    parts = [p for p in token_upper.replace("/", ",").split(",") if p]
    return len(parts) > 1 and any(p in _ROW_POSITIONS for p in parts)


def parse_result_row(position_text, team_text=""):
    """FIX5 — extrai (posição, sigla NFL) do DOM REAL da linha de resultado.

    O formato do abort de 11/08 (fixture nos testes): o nó `.position` vem
    EMPILHADO por newlines ('QB
TEN', 'RB
DET
QUES' — posição, sigla e status
    de injury no mesmo innerText) e o `.team` pode DUPLICAR a sigla no conjunto
    ('QB
TEN TEN'). Tokeniza por whitespace: posição = 1º token do vocabulário
    de posições; sigla = 1º token de 2-3 letras maiúsculas fora do vocabulário
    (o que exclui QUES/DOUB/OUT etc. por tamanho ou por não serem siglas).

    FIX11 — rótulo MULTI-POSIÇÃO ("DB,WR", caso Travis Hunter) é devolvido
    ÍNTEGRO como a posição da linha, nunca quebrado em posição+sigla (a vírgula
    não é separador de tokens; o pertencimento é julgado na eleição,
    `position_matches`). Puro."""
    tokens = f"{position_text or ''} {team_text or ''}".split()
    pos = ""
    for t in tokens:
        up = t.upper()
        if up in _ROW_POSITIONS or _is_multi_position_label(up):
            pos = up
            break
    sigla = next((t.upper() for t in tokens
                  if t.upper() not in _ROW_POSITIONS
                  and 2 <= len(t) <= 3 and t.isalpha() and t.upper() == t), "")
    return pos, sigla


def modal_header_check(modal_text: str, team_slot: int,
                       prefix: str = "Make Manual Pick for Team "):
    """FIX7 — o header do #modal é a prova de que o dialog aberto é o manual pick
    DO TIME CERTO. Retorna: "ok" · "wrong_team" (header presente, N de outro time
    — fronteira: 'Team 1' não casa slot 10) · "unexpected" (dialog sem o header —
    residual/aviso; quem chama fecha via Esc e aborta nomeando o conteúdo)."""
    import re as _re
    t = modal_text or ""
    if _re.search(_re.escape(f"{prefix}{team_slot}") + r"(?!\d)", t):
        return "ok"
    if prefix in t:
        return "wrong_team"
    return "unexpected"


def search_filter_check(row_count: int, max_expected: int = 8):
    """FIX6 — a digitação tem de FILTRAR antes de qualquer matching: dezenas de
    linhas visíveis = lista de FUNDO/ranking (o caso real: 57 linhas, todas as
    posições, 5 QBs) ou busca que não foi aplicada — nunca parsear isso. Retorna
    None (ok) ou a mensagem do abort."""
    if row_count > max_expected:
        return (f"busca não filtrou: {row_count} linhas visíveis — é a lista de "
                f"fundo/ranking, não o resultado do modal. Nada parseado, nada "
                f"designado.")
    return None


def position_matches(row_label, sheet_position):
    """FIX11 — caso Travis Hunter (probe do owner, 12/08): o rótulo da linha
    pode ser MULTI-POSIÇÃO ("DB,WR" — espelho de `fantasy_positions` da API, DB
    primeiro; único caso entre os 237 keepers da sheet). A posição da sheet
    casa por PERTENCIMENTO ao conjunto do rótulo (separadores `,` e `/`), com a
    igualdade cobrindo o caso comum ANTES do split (preserva "D/ST" como rótulo
    único). Pertencimento NÃO é afrouxamento: "QB" segue não casando "DB,WR".
    Puro."""
    lbl = (row_label or "").upper()
    want = (sheet_position or "").upper()
    if not lbl or not want:
        return False
    if lbl == want:
        return True
    return want in [p for p in lbl.replace("/", ",").split(",") if p]


def select_candidate_rows(parsed_rows, position):
    """FIX5 — índices das linhas cuja POSIÇÃO casa a da sheet. O critério segue
    estrito: 0 candidatos = não achou; 2+ = homônimo real → quem chama aborta.
    A sigla NÃO entra no critério (a sheet não a carrega) — é logada para
    conferência humana. FIX11: "casa" é PERTENCIMENTO (`position_matches`) —
    rótulo multi-posição "DB,WR" casa sheet "WR"; a regra 0/2+ não mudou."""
    return [i for i, (pos, _sigla) in enumerate(parsed_rows)
            if position_matches(pos, position)]


def _name_tokens(text):
    """FIX9 — tokens normalizados p/ casar nome: sem acentos, casefold, pontuação
    removida ('St.' → 'st', "Ja'Marr" → 'jamarr'); HÍFEN preservado de propósito —
    'Hajj-Malik' é UM token e não casa 'Malik'. Puro."""
    import unicodedata
    t = unicodedata.normalize("NFKD", text or "")
    t = "".join(c for c in t if not unicodedata.combining(c)).casefold()
    out = []
    for tok in t.split():
        tok = "".join(c for c in tok if c.isalnum() or c == "-")
        if tok:
            out.append(tok)
    return out


def row_matches_name(row_text, player_name):
    """FIX9 — o nome buscado aparece como SEQUÊNCIA de tokens no texto da linha?

    O abort da campanha de 12/08 provou que a busca do Sleeper é FUZZY: 'Malik
    Willis' devolveu também Malik Williams (WR e RB) e Hajj-Malik Williams (QB) —
    linhas REAIS de outros jogadores (FAs, sigla vazia), não artefato de DOM. O
    innerText da linha carrega rank/stats além do nome; casar por sequência de
    tokens ('malik'+'willis' consecutivos) elimina os não-candidatos sem depender
    de seletor novo. Puro."""
    name = _name_tokens(player_name)
    row = _name_tokens(row_text)
    if not name or not row:
        return False
    n = len(name)
    return any(row[i:i + n] == name for i in range(len(row) - n + 1))


def select_candidate_rows_named(parsed_rows, position, row_texts, player_name):
    """FIX9 — candidato REAL = posição exata (critério do FIX5, INTACTO) E o nome
    buscado presente na linha (a busca do Sleeper é fuzzy — devolve outros nomes).
    ⛔ Sigla vazia NÃO desqualifica: FA real é linha legítima (keeper cortado da
    NFL continuaria elegível). 0 ou 2+ candidatos REAIS seguem abortando no
    chamador — a regra do anti-homônimo não mudou, só o que conta como candidato."""
    texts = row_texts or []
    return [i for i in select_candidate_rows(parsed_rows, position)
            if i < len(texts) and row_matches_name(texts[i], player_name)]


# ── F2b: idempotência, plano por time, teto e agregação (núcleo puro) ──────────

DESIGNAR = "designar"
JA_ASSENTADO = "ja_assentado"
CONFLITO = "conflito"
BLOQUEADO_TETO = "bloqueado_teto"


def idempotency_decision(sid, expected_owner_id, expected_price, picks, slot_map):
    """F2b — A LIÇÃO DA F2a: idempotência é a PRIMEIRA verificação, não a última
    (o pick de Cam Ward gravou numa run que morreu antes do poll, e a run seguinte
    gastou um ciclo com "busca vazia misteriosa" — designado some do pool).

    Confere nos PICKS DA API (a verdade) antes de qualquer interação com o board:
    - ausente → ("designar", None);
    - presente no time certo, preço certo → ("ja_assentado", pick) — sucesso, zero
      cliques (preço None no pick = não conferível → aceita como assentado);
    - presente com time OU preço divergente → ("conflito", detalhe) — decisão
      humana, quem chama aborta nomeado. Puro."""
    for raw in picks or []:
        p = parse_pick(raw)
        if p["sid"] != str(sid):
            continue
        slot_owner = (slot_map.get(p["slot"]) or {}).get("user_id", "")
        if expected_owner_id and slot_owner and slot_owner != str(expected_owner_id):
            return (CONFLITO, {"motivo": "time divergente", "slot": p["slot"],
                               "owner_no_board": slot_owner,
                               "owner_esperado": str(expected_owner_id)})
        if (expected_price is not None and p["amount"] is not None
                and int(p["amount"]) != int(expected_price)):
            return (CONFLITO, {"motivo": "preço divergente",
                               "preco_no_board": p["amount"],
                               "preco_esperado": expected_price})
        return (JA_ASSENTADO, {"slot": p["slot"], "amount": p["amount"]})
    return (DESIGNAR, None)


def team_pending_keepers(sheet_rows, picks, owner_id):
    """F2b — os keepers do owner que AINDA não têm pick (retomabilidade por
    construção: o que já assentou sai do plano). Ordem da sheet preservada."""
    designados = {parse_pick(p)["sid"] for p in picks or []}
    return [r for r in sheet_rows
            if r["owner_id"] == str(owner_id) and r["sid"]
            and r["sid"] not in designados]


def is_budget_block(text: str) -> bool:
    """F2b — o Sleeper RECUSA designação acima do teto de lance com a mensagem
    "does not have enough budget" (§B.3.2 do runbook). É resultado ESPERADO
    pré-late-drop (AlexTheDawg $203, Miller Time! $200), não erro."""
    return "does not have enough budget" in (text or "").lower()


# ── FIX10: a SEGUNDA cara do teto — o clamp silencioso do input de preço ───────
#
# A campanha de 12/08 (AlexTheDawg, sheet $203 > budget $200) provou que o teto
# tem DUAS manifestações: a recusa síncrona acima (§B.3.2) e um CLAMP silencioso
# do input ao max bid — o script digitou $6/$4/$3/$2, o input clampou para
# $5/$1/$1/$1 e o SET PLAYER gravou errado sem aviso (total $196, detectado só
# na conferência, tarde e sem apontar quais). Preço errado no board é divergência
# de severidade ALTA na doutrina OFF26-4 — pior que ausência, porque parece certo.


def parse_price_value(text):
    """FIX10 — valor efetivo do input de preço ('6', '$6', ' 6 ') → int; sem
    dígitos → None (read-back ilegível; quem chama aborta, nunca grava às cegas)."""
    digits = "".join(c for c in str(text or "") if c.isdigit())
    return int(digits) if digits else None


def price_readback_decision(commanded, effective):
    """FIX10 — decisão sobre o READ-BACK do input após digitar o preço:
    - igual ao comandado → "ok" (SET PLAYER liberado);
    - MENOR → bloqueado_teto (clamp = a 2ª cara do teto; ⛔ a sheet é canônica —
      o script NUNCA grava preço diferente dela; mesma classe do §B.3.2, sem
      semântica paralela);
    - None ou MAIOR → "abortar" (ilegível/digitação não aplicada — estado
      indeterminado, nunca gravar às cegas). Puro."""
    if effective is None or effective > commanded:
        return "abortar"
    if effective < commanded:
        return BLOQUEADO_TETO
    return "ok"


def max_bid(budget, gasto, picks_feitos, total_slots, min_bid=1):
    """FIX10 — modelo do teto VERIFICADO contra a run de 12/08 (fecha ao dólar
    nos 4 clamps do AlexTheDawg e no total $196): o Sleeper reserva min_bid por
    vaga vazia RESTANTE do board além da atual. Serve de ANOTAÇÃO de motivo no
    relatório — a verdade operacional é o read-back do input, não este cálculo.
    Puro."""
    return budget - gasto - (total_slots - picks_feitos - 1) * min_bid


def draft_budget_slots(draft_obj, default_budget=200, default_slots=22):
    """FIX10 — budget e slots do board saem do PRÓPRIO draft derivado
    (`settings.budget` / `settings.rounds` — a mesma fonte de rodadas do
    OFF26-4); ausentes/ilegíveis → defaults da fantasma ($200, board de 22).
    Puro."""
    s = (draft_obj or {}).get("settings") or {}

    def _int(v):
        try:
            return int(v)
        except (TypeError, ValueError):
            return 0

    return (_int(s.get("budget")) or default_budget,
            _int(s.get("rounds")) or default_slots)


def conference_report(picks, team_rows, excluidos=None):
    """FIX10 — conferência por time que APONTA os picks (a antiga só somava: o
    $196/$203 do AlexTheDawg denunciou QUE divergia, não QUAIS — os 4 clamps só
    apareceram no validate). Compara sheet × board POR SID: cada divergente vira
    {sid, name, sheet, board}; keeper esperado sem pick vira `faltantes`; keepers
    pulados por teto (`excluidos`) saem da expectativa e vão em campo próprio.
    Substitui a soma inline do CLI — ⛔ nenhuma segunda conferência fora daqui.
    Puro."""
    exc = {str(s) for s in (excluidos or [])}
    esperados = [r for r in team_rows if r["sid"] and r["sid"] not in exc]
    by_sid = {}
    for raw in picks or []:
        p = parse_pick(raw)
        by_sid[p["sid"]] = p
    achados, total_board = 0, 0
    divergentes, faltantes = [], []
    for r in esperados:
        p = by_sid.get(r["sid"])
        if p is None:
            faltantes.append({"sid": r["sid"], "name": r["name"]})
            continue
        achados += 1
        total_board += p["amount"] or 0
        if p["amount"] is not None and p["amount"] != r["salary"]:
            divergentes.append({"sid": r["sid"], "name": r["name"],
                                "sheet": r["salary"], "board": p["amount"]})
    return {"picks_no_board": achados,
            "keepers_na_sheet": len(esperados),
            "total_no_board": total_board,
            "total_na_sheet": sum(r["salary"] for r in esperados),
            "divergentes": divergentes, "faltantes": faltantes,
            "bloqueados_excluidos": sorted(exc)}


def campaign_summary(team_results: list) -> dict:
    """F2b — resumo da campanha por status; o VEREDITO é da auditoria OFF26-4
    sobre o board (o juiz independente), nunca desta contagem."""
    tally = {"times_processados": len(team_results), "designados": 0,
             "ja_assentados": 0, "bloqueados_teto": 0, "conflitos": 0,
             "falhas": 0, "times_ok": 0, "times_bloqueados": 0,
             "times_com_falha": 0}
    for t in team_results:
        tally["designados"] += t.get("designados", 0)
        tally["ja_assentados"] += t.get("ja_assentados", 0)
        tally["conflitos"] += t.get("conflitos", 0)
        # FIX10: bloqueados contados POR KEEPER (o teto pula o keeper, não o time)
        tally["bloqueados_teto"] += t.get("bloqueados_teto", 0)
        st = t.get("status")
        if st == "ok":
            tally["times_ok"] += 1
        elif st == BLOQUEADO_TETO:
            tally["times_bloqueados"] += 1
        else:
            tally["times_com_falha"] += 1
            tally["falhas"] += 1
    return tally


# ── FIX8: assentamento ASSÍNCRONO — reconciliação por time (núcleo puro) ───────
#
# O lag real medido matou o poll bloqueante: o pick do Josh Allen GRAVOU na hora
# (board local certo) e a API pública levou >5 MINUTOS para refleti-lo — o poll de
# 15s desistiu de um sucesso lento e o retry viu "busca vazia" (o board escondia o
# designado). No ensaio o lag fora ~3s: A VARIÂNCIA É O FATO CENTRAL. Hipótese do
# owner (tarefa 7, em teste): a propagação pode depender de VISITA de cliente
# (cache preguiçoso) — o validate que enfim viu 20 rodou logo após abrir o board
# num navegador. Bloquear 5min por keeper × 218 é inviável → assíncrono:
# comanda → pendente_confirmacao → segue; reconcilia POR TIME com teto generoso.

PENDENTE_CONFIRMACAO = "pendente_confirmacao"
ASSENTADO_LOCAL = "assentado_local_api_atrasada"


def split_settled(pending_sids, api_sids):
    """Reconciliação de uma varredura: quais pendentes JÁ aparecem na API.
    Retorna (assentados_agora, ainda_pendentes) — ordem preservada. Puro."""
    api = {str(x) for x in api_sids or []}
    settled = [s for s in pending_sids if str(s) in api]
    remaining = [s for s in pending_sids if str(s) not in api]
    return settled, remaining


def post_teto_decision(board_mostra_designado: bool, recomandos_feitos: int,
                       max_recomandos: int = 1) -> str:
    """Pendente que NÃO apareceu na API após o teto:
    - o board LOCAL o mostra designado no slot → `assentado_local_api_atrasada`
      (com aviso; ⛔ NUNCA re-comandar — o pick existe, a API que está atrás);
    - board o mostra disponível e ainda há re-comando no orçamento → "recomandar"
      (máx 1 — duplicata é rejeitada pelo servidor, a rede de segurança);
    - esgotou → "abort" (do KEEPER, preservando o resto do time). Puro."""
    if board_mostra_designado:
        return ASSENTADO_LOCAL
    if recomandos_feitos < max_recomandos:
        return "recomandar"
    return "abort"


def classify_team_keepers(team_rows, picks, slot_map):
    """FIX8 (tarefa 4) — idempotência EM LOTE: classifica todos os keepers do time
    numa passada única sobre os picks, ANTES do primeiro clique (pendência de run
    anterior entra como ja_assentado aqui). Retorna {sid: (decisão, detalhe)}."""
    return {r["sid"]: idempotency_decision(r["sid"], r["owner_id"], r["salary"],
                                           picks, slot_map)
            for r in team_rows if r["sid"]}


def simulate_reconciliation(pending_sids, arrival_times, teto, poll):
    """Simulador PURO da reconciliação (para testes com lags de 3s/40s/6min, sem
    sleep): `arrival_times` = {sid: segundos até aparecer na API}. Devolve
    (assentados_com_tempo, ainda_pendentes_no_teto)."""
    settled, pending = [], list(pending_sids)
    t = 0.0
    while pending and t < teto:
        t += poll
        api_now = {s for s, at in arrival_times.items() if at <= t}
        just, pending = split_settled(pending, api_now)
        settled.extend((s, t) for s in just)
    return settled, pending


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
