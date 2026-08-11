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
from .core import (ALREADY, BLOQUEADO_TETO, PENDING, SETTLED, TIMEOUT,
                   choose_menu_item, is_budget_block, league_guard,
                   modal_header_check, parse_result_row, search_filter_check,
                   select_candidate_rows, settlement_decision, url_guard)
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
    parsed = []
    for i in range(n):
        row = rows.nth(i)
        pos_text = row.locator(config.SEL_ROW_POSITION).first.inner_text()
        team_text = row.locator(config.SEL_ROW_TEAM).first.inner_text()
        parsed.append(parse_result_row(pos_text, team_text))
    chosen = select_candidate_rows(parsed, position)
    if len(chosen) == 0:
        page.keyboard.press("Escape")
        raise EmptySearchResult(f"'{player_name}': 0 candidatos {position} "
                                f"(parseadas: {parsed}) — designado some do pool?")
    if len(chosen) > 1:
        raise BoardAbort(
            f"Anti-homônimo: {len(chosen)} candidato(s) {position} para "
            f"'{player_name}' (linhas parseadas: {parsed}). Nada designado.")
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


def _set_price_and_confirm(page, price: int):
    """Preço nasce $1 SEMPRE (mesmo com $PROJ maior). >$1 → Ctrl+A + digitar.
    FIX6: o input de preço também é escopado ao MODAL (o único input do modal que
    não é o de busca)."""
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
    assert_allowed_click(config.CONFIRM_READY_TEXT)
    confirm.click()


def _visible_toast_text(page) -> str:
    """Melhor esforço: texto visível de toasts/avisos p/ classificar a recusa de
    teto (o toast NÃO é veredito de sucesso — mas a RECUSA nomeada é dele)."""
    try:
        return page.locator("body").inner_text()[-500:]
    except Exception:
        return ""


def designate(page, draft_id: str, team_slot: int, player_name: str, position: str,
              nfl_team: str, price: int, sid: str, log: list) -> str:
    """Uma designação ponta a ponta. Comando via DOM; ASSENTAMENTO via API (poll).

    Retorna o veredito do core (assentado/duplicata/…) ou levanta BoardAbort."""
    before = {str(p.get("player_id")) for p in fetch_picks(draft_id)}
    present_before = sid in before
    if present_before:
        log.append({"sid": sid, "event": "ja_assentado_antes_do_comando"})
        return ALREADY

    attempts = 0
    while True:
        attempts += 1
        _open_set_player_menu(page, team_slot)
        try:
            warn = _pick_search_result(page, team_slot, player_name, position,
                                       nfl_team, log)
        except EmptySearchResult as e:
            # F2b: a lição da F2a — re-checa a API ANTES de abortar (o desync
            # pode ter assentado o pick entre a checagem inicial e o modal)
            now = {str(p.get("player_id")) for p in fetch_picks(draft_id)}
            if sid in now:
                log.append({"sid": sid, "event": "ja_assentado_no_recheck"})
                return ALREADY
            raise BoardAbort(str(e))
        if warn:
            log.append({"sid": sid, "warning": warn})
        _set_price_and_confirm(page, price)
        log.append({"sid": sid, "event": f"comando_enviado (tentativa {attempts})"})

        # o toast NÃO é veredito — poll na API até o timeout
        deadline = time.monotonic() + config.SETTLE_TIMEOUT_SECONDS
        verdict = PENDING
        while verdict == PENDING:
            time.sleep(config.SETTLE_POLL_SECONDS)
            now = {str(p.get("player_id")) for p in fetch_picks(draft_id)}
            verdict = settlement_decision(sid, present_before, sid in now,
                                          time.monotonic() >= deadline)
        if verdict in (SETTLED, ALREADY):
            log.append({"sid": sid, "event": verdict})
            return verdict
        # TIMEOUT com recusa de TETO visível → resultado esperado, não erro
        # (§B.3.2: o Sleeper recusa acima do bid máximo — pré-late-drop é normal)
        try:
            teto = page.get_by_text(config.BUDGET_BLOCK_TEXT,
                                    exact=False).first.is_visible()
        except Exception:
            teto = False
        if teto or is_budget_block(_visible_toast_text(page)):
            page.keyboard.press("Escape")
            log.append({"sid": sid, "event": BLOQUEADO_TETO})
            return BLOQUEADO_TETO
        # TIMEOUT: caso Caleb (staging revertido) → re-comando, uma vez
        log.append({"sid": sid, "event": "timeout_sem_assentar"})
        if attempts > config.COMMAND_RETRIES:
            raise BoardAbort(
                f"'{player_name}' NÃO assentou na API após {attempts} comando(s) — "
                f"parando barulhento. O board pode estar dessincronizado; confira "
                f"os picks pela API antes de qualquer novo comando.")
