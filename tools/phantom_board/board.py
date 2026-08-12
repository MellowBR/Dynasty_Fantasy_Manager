"""
board.py — o driver Playwright do board (OFF26-24, F2a). IO de browser; decisões no core.

Arquitetura definida pelo ensaio de 11/08: **comando via DOM, verdade via API** — o
cliente do Sleeper dessincroniza (pós-SET PLAYER o board pode não atualizar; o toast
vermelho "This pick could not be processed" pode aparecer COM o pick gravado). O
assentamento é confirmado em `/v1/draft/<id>/picks`, nunca pelo board nem pelo toast.
O servidor rejeita pick duplicado → re-comando é seguro.

Regras de interação (spec do ensaio):
- busca e preço por EVENTOS REAIS de teclado (press_sequentially/press) — setar
  `.value` programaticamente NÃO dispara o filtro;
- cliques ancorados em seletor/texto, nunca pixel (viewport oscila 1197↔1496, DPR 0.8;
  o board reescala);
- anti-homônimo pelo DOM (`.position`/`.team` da linha de resultado), nunca pelo pixel.

⚠️ NÃO exercido em navegador nesta sessão (sem browser logado na máquina do Code) —
o primeiro run real é do owner, e o `probe` anota o único seletor que a spec resumida
não fixou (a célula do board).
"""

import time
from pathlib import Path

from . import config
from .core import (ALREADY, ASSENTADO_LOCAL, BLOQUEADO_TETO, SETTLED,
                   choose_menu_item, is_budget_block, league_guard,
                   modal_header_check, parse_price_value, parse_result_row,
                   post_teto_decision, price_readback_decision,
                   search_filter_check, select_candidate_rows_named,
                   split_settled, url_guard)
from .sleeper_api import fetch_draft, fetch_draft_id, fetch_picks


class BoardAbort(RuntimeError):
    """Falha real → parar BARULHENTO. Quem captura anexa screenshot/trace/relatório."""


class EmptySearchResult(BoardAbort):
    """F2b — busca sem resultado utilizável (0 linhas pós-filtro ou 0 candidatos).
    NÃO é abort imediato: o `designate` re-checa a API antes ("designado entre a
    checagem e o modal?" — o desync corre; a lição da busca vazia misteriosa da
    F2a). Só vira abort de verdade se a API confirmar que o sid não está lá."""


def assert_allowed_click(label_text: str):
    """⛔ Lista de proibições: START/RESET/JOIN DRAFT nunca são clicados."""
    up = (label_text or "").strip().upper()
    for forbidden in config.FORBIDDEN_CLICK_LABELS:
        if forbidden in up:
            raise BoardAbort(f"Clique PROIBIDO recusado: '{label_text}'.")


def open_board(headless: bool = False, profile_dir: Path | None = None):
    """Abre o board com as guardas de nascença conferidas ANTES de qualquer clique.

    Retorna (playwright, context, page, draft_id). Perfil persistente DEDICADO:
    o owner loga manualmente 1× nessa janela; zero credencial no código."""
    from playwright.sync_api import sync_playwright   # lazy: só o designate precisa

    # 1) guarda de liga — ANTES de abrir browser: deriva o draft e confere a posse
    draft_id = fetch_draft_id(config.LEAGUE_ID)
    if not draft_id:
        raise BoardAbort("A liga fantasma não tem draft ativo — nada a abrir.")
    draft = fetch_draft(draft_id)
    err = league_guard(draft, config.LEAGUE_ID)
    if err:
        raise BoardAbort(err)

    profile = profile_dir or (Path(__file__).parent / config.PROFILE_DIR_NAME)
    pw = sync_playwright().start()
    # FIX2: CHROME REAL via channel — o hCaptcha do Sleeper recusa verificar no
    # Chromium de teste (anti-bot). As duas flags abaixo são as mitigações PADRÃO do
    # Playwright para o widget renderizar o desafio ao HUMANO (⛔ nada aqui resolve
    # ou burla captcha — o owner resolve na janela). Mesmo perfil dedicado.
    try:
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=str(profile), channel=config.CHROME_CHANNEL,
            headless=headless, viewport=None,
            args=["--start-maximized",
                  "--disable-blink-features=AutomationControlled"],
            ignore_default_args=["--enable-automation"],
        )
    except Exception as e:
        pw.stop()
        raise BoardAbort(
            f"Não consegui abrir o Chrome instalado (channel="
            f"'{config.CHROME_CHANNEL}'): {e}. Instale o Google Chrome ou ajuste "
            f"CHROME_CHANNEL no config (ex.: 'chrome-beta', 'msedge'). ⛔ Sem "
            f"fallback silencioso para o Chromium de teste — o captcha do login "
            f"não verifica nele.")
    ctx.tracing.start(screenshots=True, snapshots=True)
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto(config.DRAFT_URL_TMPL.format(draft_id=draft_id), wait_until="load")

    # 2) IDENTIDADE POR CONSTRUÇÃO (fix do 1º probe, 11/08): derivação → navegação →
    #    a URL contém o draft_id derivado. Texto de título NÃO é gate — a página do
    #    draft não exibe o nome da liga ("MellowBR's Draft" etc.); ele vira log.
    page.wait_for_timeout(1_500)          # deixa qualquer redirect acontecer
    err = url_guard(page.url, draft_id)
    if err:
        raise BoardAbort(err)
    try:
        title = page.title()
    except Exception:
        title = "?"
    print(f"Identidade do board confirmada pela URL (draft {draft_id}). "
          f"Título da página (informativo): {title!r}")

    # 3) 1ª vida do perfil: janela DESLOGADA renderiza o board como espectador, com
    #    "JOIN DRAFT" visível. Espera o login manual do owner — nunca clica nada.
    _wait_for_login_if_needed(page)
    return pw, ctx, page, draft_id


def _wait_for_login_if_needed(page):
    """Se "JOIN DRAFT" (sinal de sessão deslogada/espectador) estiver visível, pausa
    e espera o owner logar NA PRÓPRIA JANELA — Enter no terminal ou o sinal sumir
    (timeout generoso). ⛔ O script nunca clica em JOIN DRAFT (lista de proibições)."""
    join = page.get_by_text("JOIN DRAFT", exact=False)
    try:
        visible = join.first.is_visible(timeout=3_000)
    except Exception:
        visible = False
    if not visible:
        return
    print('\n⚠️ A janela parece DESLOGADA ("JOIN DRAFT" visível — modo espectador).')
    print("   Logue no Sleeper NESSA janela (a sessão fica no perfil dedicado).")
    try:
        input(f"   Pressione Enter quando terminar (ou aguarde até "
              f"{config.LOGIN_WAIT_SECONDS}s)... ")
    except EOFError:
        # sem stdin interativo: espera o sinal sumir, com timeout generoso
        deadline = time.monotonic() + config.LOGIN_WAIT_SECONDS
        while time.monotonic() < deadline:
            try:
                if not join.first.is_visible(timeout=1_000):
                    break
            except Exception:
                break
            time.sleep(2)
    print("   Seguindo.")


def probe(page):
    """Abre o Playwright Inspector para inspeção do DOM real (FIX4: a navegação é
    por coluna — `.team-column` → `.cell` sem `.drafted`; o probe serve para
    conferir esses seletores se apodrecerem). Nenhum clique automatizado."""
    page.pause()


def _open_set_player_menu(page, team_slot: int):
    """FIX4 — navega POR COLUNA, nunca por índice global de célula (o call log real:
    nth(1) de células caiu numa célula PREENCHIDA do MellowBR e o menu "Change
    Player" interceptou tudo). A coluna do slot N é a N-ésima `.team-column`;
    dentro dela, a primeira célula VAZIA (sem `.drafted`). A ordem é CANDIDATA —
    quem decide é o menu: "Manually set a player for Team {N}" com o N esperado,
    julgado pelo núcleo puro (`choose_menu_item`). Qualquer outra coisa → Escape e
    aborto barulhento. Nada de varrer células tentando."""
    # FIX9 — verificação defensiva: um #modal residual de abort anterior intercepta
    # QUALQUER clique (o crash real de 12/08: a célula do time seguinte ficou 30s
    # inatingível sob o SET PLAYER aberto do abort do Malik Willis). Estado sujo
    # detectado → Escape até limpar; não limpou → abort barulhento, NUNCA clicar
    # através.
    if _is_modal_open(page) and not _dismiss_modal(page):
        raise BoardAbort(f"Slot {team_slot}: estado SUJO — #modal residual aberto "
                         f"e o Escape não o fechou. Nada clicado.")
    cols = page.locator(config.SEL_TEAM_COLUMN)
    ncols = cols.count()
    if ncols == 0:
        raise BoardAbort(f"Nenhuma coluna casa com '{config.SEL_TEAM_COLUMN}' — "
                         f"seletor apodreceu? Rode `probe` e confira o DOM.")
    if team_slot < 1 or team_slot > ncols:
        raise BoardAbort(f"Slot {team_slot} fora do board ({ncols} colunas).")
    col = cols.nth(team_slot - 1)
    empty = col.locator(
        f"{config.SEL_CELL}:not(.{config.CELL_DRAFTED_CLASS})")
    if empty.count() == 0:
        raise BoardAbort(f"Coluna do slot {team_slot} sem célula VAZIA — time "
                         f"cheio? Nada foi clicado além da inspeção.")
    empty.first.click()

    menu = page.locator(config.SEL_MENU_ITEM)
    try:
        menu.first.wait_for(timeout=4_000)
    except Exception:
        raise BoardAbort(f"A célula vazia do slot {team_slot} não abriu menu de "
                         f"contexto — DOM mudou? Nada designado.")
    texts = [menu.nth(i).inner_text() for i in range(menu.count())]
    action, detail = choose_menu_item(
        texts, team_slot, set_title=config.MENU_TITLE_SET_PLAYER,
        change_title=config.MENU_TITLE_CHANGE,
        desc_prefix=config.MENU_DESC_PREFIX)
    if action == "click":
        assert_allowed_click(texts[detail])
        menu.nth(detail).click()
        return
    page.keyboard.press("Escape")         # fecha o menu ANTES de abortar
    page.wait_for_timeout(300)
    motivo = {
        "change_player": (f"menu 'Change Player' — a célula está PREENCHIDA "
                          f"(célula errada; a lista de proibições cobre o rótulo)"),
        "wrong_team": (f"o menu é de OUTRO time — a correspondência coluna↔slot "
                       f"quebrou (esperado 'for Team {team_slot}')"),
        "no_menu": "nenhum item reconhecível no menu",
    }[detail]
    raise BoardAbort(f"Slot {team_slot}: {motivo}. Itens vistos: {texts}. "
                     f"Nada designado — parando barulhento.")


def _modal(page, team_slot=None, wait_open=False, log=None):
    """FIX7 — o container REAL do manual pick é `#modal[role=alertdialog]`
    (screenshot do abort: header "Make Manual Pick for Team N" dentro dele; a
    página de FUNDO duplica input/lista/botão — a heurística de ancestral do FIX6
    achou o trio do fundo). Âncora: o #modal quando presente; a heurística vira
    FALLBACK, logada como tal, só se #modal não existir no DOM.

    Com `team_slot`, o header é verificado (núcleo puro `modal_header_check`):
    time errado → abort; dialog sem o header (residual/aviso) → Esc + abort
    nomeando o conteúdo. `wait_open` espera ESTADO (não sleep) após o Set Player."""
    modal = page.locator(config.SEL_MODAL)
    if wait_open:
        try:
            modal.first.wait_for(state="visible", timeout=8_000)
        except Exception:
            raise BoardAbort("O modal do manual pick NÃO abriu após o 'Set Player' "
                             "(#modal ausente/invisível). Nada designado.")
    try:
        has_modal = modal.count() > 0 and modal.first.is_visible()
    except Exception:
        has_modal = False

    if has_modal:
        m = modal.first
        if team_slot is not None:
            texto = (m.inner_text() or "")
            veredito = modal_header_check(texto, team_slot,
                                          config.MODAL_HEADER_PREFIX)
            if veredito == "wrong_team":
                page.keyboard.press("Escape")
                raise BoardAbort(f"O modal aberto é de OUTRO time (esperado "
                                 f"'{config.MODAL_HEADER_PREFIX}{team_slot}'). "
                                 f"Nada designado.")
            if veredito == "unexpected":
                page.keyboard.press("Escape")
                page.wait_for_timeout(300)
                raise BoardAbort(f"Dialog inesperado aberto (sem o header do manual "
                                 f"pick): '{texto[:160]}'. Fechado via Esc; nada "
                                 f"designado — reabra o fluxo.")
        if log is not None:
            log.append({"event": "modal_ancorado", "ancora": "#modal"})
        return m

    # FALLBACK (DOM sem #modal) — a heurística estrutural do FIX6, logada como tal
    confirm = page.locator(config.SEL_CONFIRM_BUTTON).first
    try:
        confirm.wait_for(timeout=5_000)
    except Exception:
        raise BoardAbort("Nem #modal nem botão de confirmação visíveis — o fluxo "
                         "do manual pick não está aberto. Nada designado.")
    anc = confirm.locator(
        f'xpath=ancestor::*[.//input[@placeholder="Find player Ctrl + U"]][1]')
    if anc.count() == 0:
        raise BoardAbort("Sem #modal no DOM e a heurística de ancestral não achou "
                         "container — DOM mudou? Rode `probe` (README).")
    if log is not None:
        log.append({"event": "modal_ancorado", "ancora": "ancestral_fallback"})
    return anc.first


def _is_modal_open(page) -> bool:
    """FIX9 — checagem instantânea (sem espera) de #modal/alertdialog visível."""
    try:
        m = page.locator(config.SEL_MODAL).first
        return m.count() > 0 and m.is_visible()
    except Exception:
        return False


def _dismiss_modal(page) -> bool:
    """FIX9 — higiene de estado: fecha menu/modal residual via Escape (melhor
    esforço, nunca levanta). Retorna True se a página ficou limpa. O abort do
    anti-homônimo de 12/08 deixou o SET PLAYER aberto e o clique do time seguinte
    foi interceptado até TimeoutError — nenhum caminho de abort pode mais sair
    daqui com dialog aberto."""
    for _ in range(3):
        if not _is_modal_open(page):
            return True
        try:
            page.keyboard.press("Escape")
            page.wait_for_timeout(300)
        except Exception:
            break
    return not _is_modal_open(page)


def _pick_search_result(page, team_slot: int, player_name: str, position: str,
                        nfl_team: str, log: list = None):
    """Digita a busca NO MODAL e elege a linha pelo DOM do MODAL (FIX6 — nenhum
    locator global sobrevive: a página de fundo tem a mesma lista). Antes de
    qualquer matching, a digitação tem de ter FILTRADO (núcleo:
    `search_filter_check` — 57 linhas = fundo, abort). Critério do anti-homônimo
    intacto: posição exata; 0 ou 2+ candidatos abortam; sigla logada. ⛔ O "+"
    clicado é o da linha ELEITA."""
    modal = _modal(page, team_slot=team_slot, wait_open=True, log=log)
    search = modal.locator(config.SEL_SEARCH_INPUT).first
    search.click()
    search.press("Control+a")
    search.press_sequentially(player_name, delay=40)
    page.wait_for_timeout(600)            # o filtro reage a teclas — deixa assentar

    rows = modal.locator(config.SEL_RESULT_ROW + ":visible")
    n = rows.count()
    if n == 0:
        page.keyboard.press("Escape")     # fecha o modal p/ o chamador re-checar
        raise EmptySearchResult(f"'{player_name}': lista VAZIA após o filtro — "
                                f"designado entre a checagem e o modal?")
    err = search_filter_check(n, config.SEARCH_MAX_RESULTS)
    if err:
        raise BoardAbort(f"'{player_name}': {err} (escopo: modal; se persistir, o "
                         f"wrapper do modal mudou — probe/README).")
    parsed, textos = [], []
    for i in range(n):
        row = rows.nth(i)
        pos_text = row.locator(config.SEL_ROW_POSITION).first.inner_text()
        team_text = row.locator(config.SEL_ROW_TEAM).first.inner_text()
        parsed.append(parse_result_row(pos_text, team_text))
        textos.append((row.inner_text() or "").replace("\n", " "))
    # FIX9 — a busca do Sleeper é FUZZY ("Malik Willis" devolveu também Malik
    # Williams ×2 e Hajj-Malik Williams, screenshot de 12/08): candidato REAL
    # exige o NOME buscado na linha, além da posição exata. Sigla vazia não
    # desqualifica (FA real é linha legítima). Critério 0/2+ → abort intacto.
    chosen = select_candidate_rows_named(parsed, position, textos, player_name)
    resumo = [t[:60] for t in textos]
    if len(chosen) == 0:
        page.keyboard.press("Escape")
        raise EmptySearchResult(f"'{player_name}': 0 candidatos {position} com o "
                                f"nome buscado (parseadas: {parsed}; linhas: "
                                f"{resumo}) — designado some do pool?")
    if len(chosen) > 1:
        raise BoardAbort(
            f"Anti-homônimo: {len(chosen)} candidato(s) {position} homônimos de "
            f"'{player_name}' (linhas parseadas: {parsed}; linhas: {resumo}). "
            f"Nada designado.")
    idx = chosen[0]
    pos, sigla = parsed[idx]
    if log is not None:
        log.append({"event": "linha_eleita", "player": player_name,
                    "position": pos, "nfl_team_no_board": sigla,
                    "linhas_no_modal": n})
    warn = None
    if nfl_team and sigla and sigla != nfl_team.upper():
        warn = (f"time NFL divergente: sheet={nfl_team} board={sigla} — pode ser "
                f"dado fresco do Sleeper (nota Diggs/D.Jones do ensaio)")
    row = rows.nth(idx)                   # ⛔ a linha ELEITA pelo matcher
    plus = row.locator(config.SEL_PLUS_BUTTON).first
    klass = plus.get_attribute("class") or ""
    if config.PLUS_DISABLED_CLASS in klass.split():
        raise BoardAbort(f"O '+' de '{player_name}' está desabilitado "
                         f"(já designado?). Nada feito.")
    plus.click()                          # ⛔ o "+", NUNCA o nome (nome cancela o fluxo)
    return warn


def _set_price_and_confirm(page, price: int, sid=None, log=None,
                           expected_max=None):
    """Preço nasce $1 SEMPRE (mesmo com $PROJ maior). >$1 → Ctrl+A + digitar.
    FIX6: o input de preço também é escopado ao MODAL (o único input do modal que
    não é o de busca).

    FIX10 — a SEGUNDA cara do teto: o input CLAMPA silenciosamente ao max bid
    (run de 12/08: digitou 6/4/3/2, gravou 5/1/1/1 sem aviso). Depois de digitar,
    o valor EFETIVO do input é lido de volta — a VERDADE OPERACIONAL
    (`expected_max` do modelo é só anotação de motivo). Clampou → NÃO aciona o
    SET PLAYER, fecha limpo e retorna bloqueado_teto (⛔ a sheet é canônica — o
    script nunca grava preço diferente dela). Read-back ilegível ou MAIOR que o
    comandado → abort barulhento, nada gravado. Retorna "ok" ou BLOQUEADO_TETO."""
    modal = _modal(page)
    confirm = modal.locator(config.SEL_CONFIRM_BUTTON,
                            has_text=config.CONFIRM_READY_TEXT).first
    confirm.wait_for(timeout=5_000)       # "Assign a player" já virou "SET PLAYER"
    if price and price > 1:
        price_input = modal.locator(
            f'input:not([placeholder="Find player Ctrl + U"])').first
        price_input.click()
        price_input.press("Control+a")
        price_input.press_sequentially(str(price), delay=40)
        page.wait_for_timeout(200)        # deixa o clamp do board assentar
        efetivo = parse_price_value(price_input.input_value())
        decisao = price_readback_decision(price, efetivo)
        if decisao == BLOQUEADO_TETO:
            if log is not None:
                log.append({"sid": sid, "event": BLOQUEADO_TETO,
                            "motivo": "clamp_do_input",
                            "preco_sheet": price, "preco_efetivo": efetivo,
                            "max_bid_modelo": expected_max})
            _dismiss_modal(page)          # NADA gravado — fecha e devolve o teto
            return BLOQUEADO_TETO
        if decisao == "abortar":
            raise BoardAbort(
                f"Read-back do preço indeterminado (comandado ${price}, input "
                f"{efetivo!r}) — digitação não aplicada/estado estranho. NADA "
                f"gravado (a sheet é canônica).")
    assert_allowed_click(config.CONFIRM_READY_TEXT)
    confirm.click()
    return "ok"


def _visible_toast_text(page) -> str:
    """Melhor esforço: texto visível de toasts/avisos p/ classificar a recusa de
    teto (o toast NÃO é veredito de sucesso — mas a RECUSA nomeada é dele)."""
    try:
        return page.locator("body").inner_text()[-500:]
    except Exception:
        return ""


def command_pick(page, team_slot: int, player_name: str, position: str,
                 nfl_team: str, price: int, sid: str, log: list,
                 expected_max: int = None) -> str:
    """FIX8 — envia UM comando (menu→busca→+→preço→SET PLAYER) e retorna SEM
    poll: o assentamento é ASSÍNCRONO (lag real medido: 3s a >5min — o board
    local preenchendo a célula é feedback suficiente para seguir). O TETO tem
    DUAS caras (FIX10): o clamp silencioso do input, detectado por read-back
    ANTES do SET PLAYER (nada gravado), e a recusa síncrona (§B.3.2), cujo aviso
    aparece na hora. Ambas → `bloqueado_teto`. Retorna "comandado" ou
    BLOQUEADO_TETO. EmptySearchResult propaga — o chamador decide (recheck da
    API / board local / estado da própria run)."""
    try:
        _open_set_player_menu(page, team_slot)
        warn = _pick_search_result(page, team_slot, player_name, position,
                                   nfl_team, log)
        if warn:
            log.append({"sid": sid, "warning": warn})
        r = _set_price_and_confirm(page, price, sid=sid, log=log,
                                   expected_max=expected_max)
    except Exception:
        # FIX9 — NENHUM caminho de erro sai do comando com menu/modal aberto:
        # o abort do anti-homônimo (12/08) deixou o SET PLAYER aberto e o time
        # seguinte clicou através dele (TimeoutError cru de 30s). Melhor esforço;
        # o próximo _open_set_player_menu re-confere de qualquer jeito.
        _dismiss_modal(page)
        raise
    if r == BLOQUEADO_TETO:               # FIX10: clamp detectado — nada gravado
        return BLOQUEADO_TETO
    page.wait_for_timeout(1_500)          # a recusa de teto é imediata, se houver
    try:
        teto = page.get_by_text(config.BUDGET_BLOCK_TEXT,
                                exact=False).first.is_visible()
    except Exception:
        teto = False
    if teto or is_budget_block(_visible_toast_text(page)):
        _dismiss_modal(page)
        log.append({"sid": sid, "event": BLOQUEADO_TETO,
                    "motivo": "recusa_sincrona"})
        return BLOQUEADO_TETO
    log.append({"sid": sid, "event": "comandado"})
    return "comandado"


def board_shows_designated(page, team_slot: int, player_name: str) -> bool:
    """FIX8 — o board LOCAL mostra o jogador designado na coluna do slot? (célula
    `.cell.drafted` da coluna contendo o SOBRENOME — as células abreviam o
    primeiro nome: "J. Allen"). Usado só para REBAIXAR pendente a
    `assentado_local_api_atrasada` — nunca como verdade de campanha."""
    try:
        col = page.locator(config.SEL_TEAM_COLUMN).nth(team_slot - 1)
        last = (player_name or "").split()[-1]
        return col.locator(f"{config.SEL_CELL}.{config.CELL_DRAFTED_CLASS}",
                           has_text=last).count() > 0
    except Exception:
        return False


def reconcile_team(page, draft_id: str, pendentes: list, log: list,
                   teto: float = None, poll: float = None) -> list:
    """FIX8 — reconciliação POR TIME: varre a API com paciência (teto generoso)
    até os pendentes assentarem. No MEIO do teto com pendência viva, um RELOAD
    do board — tarefa 7: a visita do próprio script como possível gatilho do
    cache preguiçoso; a telemetria (`segundos_apos_comando` + `apos_reload`)
    distingue lag puro (fila contínua) de cache por visita (rajada pós-reload).

    `pendentes`: [{sid, name, slot, price, cmd_at}]. Retorna os AINDA pendentes
    no teto (decisão pós-teto é do chamador via post_teto_decision)."""
    teto = teto or config.RECONCILE_TETO_SECONDS
    poll = poll or config.RECONCILE_POLL_SECONDS
    start = time.monotonic()
    reloaded = False
    pend = {p["sid"]: p for p in pendentes}
    while pend and time.monotonic() - start < teto:
        time.sleep(poll)
        api_sids = {str(x.get("player_id")) for x in fetch_picks(draft_id)}
        settled, _rest = split_settled(list(pend), api_sids)
        for sid in settled:
            item = pend.pop(sid)
            log.append({"sid": sid, "event": "assentado",
                        "segundos_apos_comando":
                            round(time.monotonic() - item["cmd_at"], 1),
                        "apos_reload": reloaded})
        if pend and not reloaded and (time.monotonic() - start) >= teto / 2:
            log.append({"event": "reload_do_board",
                        "segundos": round(time.monotonic() - start, 1),
                        "pendentes": sorted(pend)})
            try:
                page.reload(wait_until="load")
                page.wait_for_timeout(1_500)
            except Exception:
                pass
            reloaded = True
    return list(pend.values())


def settle_pendentes(page, draft_id: str, pendentes: list, log: list) -> dict:
    """FIX8 — fecha os pendentes de um time: reconciliação paciente → decisão
    pós-teto por pendente (board local → `assentado_local_api_atrasada` com
    aviso, NUNCA re-comando; disponível → 1 re-comando + mini-reconciliação;
    esgotou → falha DO KEEPER, preservando o resto). Retorna o placar."""
    placar = {"assentados": 0, "locais": 0, "falhas": []}
    sobras = reconcile_team(page, draft_id, pendentes, log)
    placar["assentados"] = len(pendentes) - len(sobras)
    for item in sobras:
        recomandos = 0
        while True:
            decisao = post_teto_decision(
                board_shows_designated(page, item["slot"], item["name"]),
                recomandos, config.COMMAND_RETRIES)
            if decisao == ASSENTADO_LOCAL:
                log.append({"sid": item["sid"], "event": ASSENTADO_LOCAL,
                            "aviso": "board local designado; API atrasada — "
                                     "conferir na auditoria"})
                placar["locais"] += 1
                break
            if decisao == "recomandar":
                recomandos += 1
                log.append({"sid": item["sid"], "event": "recomando"})
                try:
                    r = command_pick(page, item["slot"], item["name"],
                                     item.get("position", ""), "",
                                     item["price"], item["sid"], log)
                except EmptySearchResult:
                    # sumiu da busca logo após o próprio comando desta run →
                    # sinal de sucesso LOCAL (tarefa 5), não mistério
                    log.append({"sid": item["sid"],
                                "event": "sumiu_da_busca_pos_comando"})
                    r = "comandado"
                except Exception as e:
                    # FIX9: exceção CRUA (Timeout etc.) tem o mesmo destino do
                    # BoardAbort — falha DO KEEPER, preservando o resto do time
                    # (o command_pick já saiu com a página limpa).
                    placar["falhas"].append(
                        {"keeper": item["name"],
                         "falha": f"{type(e).__name__}: {str(e)[:200]}"})
                    break
                if r == BLOQUEADO_TETO:
                    placar["falhas"].append({"keeper": item["name"],
                                             "falha": BLOQUEADO_TETO})
                    break
                item["cmd_at"] = time.monotonic()
                ainda = reconcile_team(page, draft_id, [item], log,
                                       teto=config.RECOMMAND_RECONCILE_SECONDS)
                if not ainda:
                    placar["assentados"] += 1
                    break
                continue          # volta ao post_teto_decision (board check)
            placar["falhas"].append({"keeper": item["name"],
                                     "falha": "não assentou nem no board local "
                                              "após re-comando"})
            break
    return placar


def designate(page, draft_id: str, team_slot: int, player_name: str,
              position: str, nfl_team: str, price: int, sid: str,
              log: list) -> str:
    """Uma designação (o comando único do CLI): comando assíncrono + os MESMOS
    fecho e decisão pós-teto da campanha. Verdade continua sendo a API."""
    before = {str(p.get("player_id")) for p in fetch_picks(draft_id)}
    if sid in before:
        log.append({"sid": sid, "event": "ja_assentado_antes_do_comando"})
        return ALREADY
    try:
        r = command_pick(page, team_slot, player_name, position, nfl_team,
                         price, sid, log)
    except EmptySearchResult as e:
        now = {str(p.get("player_id")) for p in fetch_picks(draft_id)}
        if sid in now:
            log.append({"sid": sid, "event": "ja_assentado_no_recheck"})
            return ALREADY
        if board_shows_designated(page, team_slot, player_name):
            log.append({"sid": sid, "event": ASSENTADO_LOCAL})
            return ASSENTADO_LOCAL
        raise BoardAbort(str(e))
    if r == BLOQUEADO_TETO:
        return BLOQUEADO_TETO
    pend = [{"sid": sid, "name": player_name, "slot": team_slot,
             "price": price, "position": position, "cmd_at": time.monotonic()}]
    placar = settle_pendentes(page, draft_id, pend, log)
    if placar["falhas"]:
        raise BoardAbort(f"'{player_name}' não assentou: {placar['falhas']}")
    return SETTLED if placar["assentados"] else ASSENTADO_LOCAL
