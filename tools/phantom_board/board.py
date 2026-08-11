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
from .core import (PENDING, SETTLED, ALREADY, TIMEOUT, league_guard,
                   settlement_decision, url_guard)
from .sleeper_api import fetch_draft, fetch_draft_id, fetch_picks


class BoardAbort(RuntimeError):
    """Falha real → parar BARULHENTO. Quem captura anexa screenshot/trace/relatório."""


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
    ctx = pw.chromium.launch_persistent_context(
        user_data_dir=str(profile), headless=headless, viewport=None,
        args=["--start-maximized"],
    )
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
    """Abre o Playwright Inspector para o owner anotar o seletor da CÉLULA do board
    (o único que a spec resumida do ensaio não fixou) → vai para
    `config.BOARD_CELL_SELECTOR`. Nenhum clique automatizado acontece aqui."""
    page.pause()


def _open_set_player_menu(page, team_slot: int):
    """Clica células candidatas da coluna até o menu confirmar o time PELO TEXTO —
    'Manually set a player for Team {N}' (a verificação canônica do runbook §B.2b).
    Mismatch de N → Escape e próxima célula; esgotou → aborta."""
    if not config.BOARD_CELL_SELECTOR:
        raise BoardAbort(
            "BOARD_CELL_SELECTOR vazio — rode `probe` primeiro e anote a classe real "
            "da célula no config (o único seletor que o ensaio resumido não fixou).")
    cells = page.locator(config.BOARD_CELL_SELECTOR)
    n = cells.count()
    if n == 0:
        raise BoardAbort(f"Nenhuma célula casa com '{config.BOARD_CELL_SELECTOR}' — "
                         f"seletor apodreceu? Rode `probe` de novo.")
    expected = f"{config.MENU_DESC_PREFIX}{team_slot}"
    for i in range(n):
        cells.nth(i).click()
        menu = page.locator(config.SEL_MENU_ITEM,
                            has_text=config.MENU_TITLE_SET_PLAYER)
        try:
            menu.first.wait_for(timeout=3_000)
        except Exception:
            continue                      # célula sem menu (ocupada?) — próxima
        desc = menu.first.inner_text()
        if expected in desc:
            assert_allowed_click(desc)
            menu.first.click()
            return
        page.keyboard.press("Escape")     # time errado — fecha e segue a varredura
    raise BoardAbort(f"Nenhuma célula abriu o menu de '{expected}' — coluna do time "
                     f"{team_slot} não encontrada. Nada foi designado.")


def _pick_search_result(page, player_name: str, position: str, nfl_team: str):
    """Digita a busca com teclas REAIS e escolhe a linha por DOM (anti-homônimo:
    posição obrigatória; time NFL divergente vira AVISO — pode ser dado fresco do
    Sleeper (caso Diggs/D.Jones do ensaio) — mas 0 ou 2+ candidatos abortam."""
    search = page.locator(config.SEL_SEARCH_INPUT + ":visible").last  # o do modal
    search.click()
    search.press("Control+a")
    search.press_sequentially(player_name, delay=40)
    page.wait_for_timeout(600)            # o filtro reage a teclas — deixa assentar

    rows = page.locator(config.SEL_RESULT_ROW + ":visible")
    candidates, infos = [], []
    for i in range(rows.count()):
        row = rows.nth(i)
        pos = row.locator(config.SEL_ROW_POSITION).first.inner_text().strip()
        team = row.locator(config.SEL_ROW_TEAM).first.inner_text().strip()
        infos.append(f"{pos} {team}")
        if pos.upper() == (position or "").upper():
            candidates.append((row, pos, team))
    if len(candidates) != 1:
        raise BoardAbort(
            f"Anti-homônimo: {len(candidates)} candidato(s) {position} para "
            f"'{player_name}' (linhas visíveis: {infos or 'nenhuma'}). Nada designado.")
    row, pos, team = candidates[0]
    warn = None
    if nfl_team and team.upper() != nfl_team.upper():
        warn = (f"time NFL divergente: sheet={nfl_team} board={team} — pode ser dado "
                f"fresco do Sleeper (nota Diggs/D.Jones do ensaio)")
    plus = row.locator(config.SEL_PLUS_BUTTON).first
    klass = plus.get_attribute("class") or ""
    if config.PLUS_DISABLED_CLASS in klass.split():
        raise BoardAbort(f"O '+' de '{player_name}' está desabilitado "
                         f"(já designado?). Nada feito.")
    plus.click()                          # ⛔ o "+", NUNCA o nome (nome cancela o fluxo)
    return warn


def _set_price_and_confirm(page, price: int):
    """Preço nasce $1 SEMPRE (mesmo com $PROJ maior). >$1 → Ctrl+A + digitar."""
    confirm = page.locator(config.SEL_CONFIRM_BUTTON,
                           has_text=config.CONFIRM_READY_TEXT).first
    confirm.wait_for(timeout=5_000)       # "Assign a player" já virou "SET PLAYER"
    if price and price > 1:
        bar = confirm.locator("xpath=..")
        price_input = bar.locator("input").first
        price_input.click()
        price_input.press("Control+a")
        price_input.press_sequentially(str(price), delay=40)
    assert_allowed_click(config.CONFIRM_READY_TEXT)
    confirm.click()


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
        warn = _pick_search_result(page, player_name, position, nfl_team)
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
        # TIMEOUT: caso Caleb (staging revertido) → re-comando, uma vez
        log.append({"sid": sid, "event": "timeout_sem_assentar"})
        if attempts > config.COMMAND_RETRIES:
            raise BoardAbort(
                f"'{player_name}' NÃO assentou na API após {attempts} comando(s) — "
                f"parando barulhento. O board pode estar dessincronizado; confira "
                f"os picks pela API antes de qualquer novo comando.")
