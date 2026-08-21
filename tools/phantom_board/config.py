"""
config.py — constantes e guardas de nascença do script de população (OFF26-24).

⛔ A GUARDA DE LEAGUE_ID É REQUISITO DE NASCENÇA, NÃO MELHORIA: o script se recusa a
operar em qualquer liga que não seja a fantasma. Nada aqui roda contra a liga real
em hipótese alguma.
"""

# A liga fantasma (estável — sobrevive a RESET DRAFT). ⛔ Hardcoded de propósito.
LEAGUE_ID = "1389725099556372481"

# Nome da liga — conferência SECUNDÁRIA informativa (logada no relatório). ⛔ NÃO é
# gate: a página do draft não exibe o nome da liga (exibe "MellowBR's Draft" etc. —
# achado do 1º probe, 11/08). A identidade do board é provada POR CONSTRUÇÃO:
# derivação do draft_id pela API → navegação → URL contém o draft_id (core.url_guard).
LEAGUE_NAME = "Dynasty SB FA Auction"

# ⛔ O draft_id MUDA a cada RESET DRAFT — derivado da API pública a cada uso, NUNCA
# constante. O id do ensaio de 11/08 (1392654933580353536) é fixture de LEITURA nos
# testes, não configuração.
SLEEPER_API = "https://api.sleeper.app/v1"
DRAFT_URL_TMPL = "https://sleeper.com/draft/nfl/{draft_id}"

# ⛔ Lista de proibições: estes rótulos NUNCA são clicados. `board.assert_allowed_click`
# recusa qualquer alvo cujo texto case com eles — e há teste estático de que a lista
# existe e o driver a consulta.
FORBIDDEN_CLICK_LABELS = ("START DRAFT", "RESET DRAFT", "JOIN DRAFT",
                          "CHANGE PLAYER")

# Seletores da spec do ensaio de 11/08 (classes BEM legíveis; board no documento
# principal, sem iframe; 264 células no DOM, sem virtualização).
SEL_MENU_ITEM = "div.item"                      # menu de contexto da célula
MENU_TITLE_SET_PLAYER = "Set Player"
# FIX12 (21/08): o rótulo da coluna tem DOIS formatos e a liga alternou sem aviso —
# o genérico "Team {N}" e o NOME DO OWNER ("...for rafadgil"), que é o que a fantasma
# exibe desde que o metadata do draft ganhou `show_team_names: "0"` (12/12 times;
# screenshots runs/abort_slot1..5.png). O prefixo abaixo é COMUM aos dois; o rótulo
# esperado (handle do owner OU "Team N") é julgado no núcleo puro, com casamento
# EXATO — ⛔ nunca "contém".
MENU_DESC_PREFIX = "Manually set a player for "
# ⛔ O item de RESET DE NOMINAÇÃO carrega o MESMO nome de owner ("Reset Nomination /
# Change nominator to rafadgil") — marcador próprio para que jamais seja lido como
# item de designação.
MENU_TITLE_RESET = "Reset Nomination"
MENU_DESC_RESET_PREFIX = "Change nominator to"
# FIX12: o menu de contexto do Sleeper NÃO fecha com Escape (evidência: os 5
# screenshots de abort de 21/08 mostram o MESMO menu do slot 1 aberto durante os
# slots 2-5). Quem fecha é o clique no próprio underlay — o elemento que aparece
# no erro do Playwright interceptando os cliques dos times seguintes.
SEL_MENU_UNDERLAY = ".context-menu-underlay"
SEL_SEARCH_INPUT = 'input[placeholder="Find player Ctrl + U"]'  # há 3 — usar o do modal
SEL_RESULT_ROW = ".player-rank-item2"           # linha de resultado da busca
SEL_ROW_POSITION = ".position"                  # anti-homônimo: pelo DOM, nunca pixel
SEL_ROW_TEAM = ".team"
SEL_PLUS_BUTTON = ".draft-button"               # habilitado quando NÃO tem .disable
PLUS_DISABLED_CLASS = "disable"
SEL_CONFIRM_BUTTON = ".linear_gradient"         # nasce "Assign a player" → "SET PLAYER"
CONFIRM_READY_TEXT = "SET PLAYER"
# FIX6: busca aplicada tem POUCAS linhas; dezenas = lista de fundo vazando no
# matching (o caso real: 57 linhas do ranking geral) → abort, nunca parsear.
SEARCH_MAX_RESULTS = 8
# FIX7 (screenshot do abort): o manual pick vive num `<div id="modal"
# role="alertdialog">` com o header "Make Manual Pick for Team {N}" — e a página
# de FUNDO duplica input/lista/botão (a heurística de ancestral do FIX6 achou o
# trio do fundo). A âncora é o #modal; a heurística vira FALLBACK logado.
SEL_MODAL = '#modal, [role="alertdialog"]'
# FIX12: o header nomeia a coluna com o MESMO rótulo do menu (handle do owner ou
# "Team N") — prefixo comum aos dois, rótulo julgado no núcleo puro.
MODAL_HEADER_PREFIX = "Make Manual Pick for "

# FIX4 (11/08, do call log do 1º designate): a navegação até a célula é POR COLUNA,
# nunca por índice global — a ordem do DOM das células não corresponde a colunas
# (`[id^='draft-cell']` nth(1) caiu numa célula PREENCHIDA do MellowBR e abriu
# "Change Player"). A coluna do slot N é a N-ésima `.team-column` (12 no DOM,
# ensaio + probe); dentro dela, a primeira célula VAZIA (`.cell` sem `.drafted`).
# A ordem é CANDIDATA — a confirmação obrigatória segue sendo o menu "for Team {N}".
SEL_TEAM_COLUMN = ".team-column"
SEL_CELL = ".cell"
CELL_DRAFTED_CLASS = "drafted"          # célula preenchida (ex.: "cell rb drafted")
MENU_TITLE_CHANGE = "Change Player"     # menu de célula PREENCHIDA — proibido

# Assentamento (o achado que define a arquitetura): comando via DOM, VERDADE via API.
# O board pode não atualizar e o toast vermelho pode MENTIR ("This pick could not be
# processed" com o pick gravado) — só a API decide. Lag observado ~3s.
# 1ª vida do perfil dedicado: a janela abre DESLOGADA (sinal: "JOIN DRAFT" de
# espectador — o board renderiza mesmo assim). O probe/designate esperam o login
# manual do owner em vez de estourar.
LOGIN_WAIT_SECONDS = 120

# F2b: recusa de teto do Sleeper (§B.3.2) — resultado esperado, não erro.
BUDGET_BLOCK_TEXT = "does not have enough budget"

SETTLE_POLL_SECONDS = 1.5
SETTLE_TIMEOUT_SECONDS = 15.0
COMMAND_RETRIES = 1        # servidor rejeita duplicata — re-comando é seguro

# FIX8: assentamento ASSÍNCRONO — o lag da API de leitura variou de ~3s (ensaio)
# a >5min (Josh Allen, medido); o poll bloqueante por keeper morreu. Reconciliação
# POR TIME com teto generoso; no MEIO do teto, um RELOAD do board (tarefa 7: a
# visita do próprio script como possível gatilho de refresh do cache preguiçoso —
# a telemetria distingue lag puro de rajada pós-reload).
RECONCILE_TETO_SECONDS = 300
RECONCILE_POLL_SECONDS = 5
RECOMMAND_RECONCILE_SECONDS = 60   # mini-reconciliação após um re-comando

# FIX2 (11/08): o hCaptcha do Sleeper RECUSA verificar no Chromium de teste do
# Playwright ("Failed to get captcha verification" — anti-bot detecta o navegador de
# automação; o desafio nem renderiza). O launch usa o CHROME REAL instalado
# (channel abaixo) — mesmo perfil dedicado, só muda o binário. Se o Chrome não
# estiver instalado, o script aborta com instrução (nunca cai para o Chromium em
# silêncio). Valores aceitos pelo Playwright: "chrome", "chrome-beta", "msedge"…
CHROME_CHANNEL = "chrome"

# Perfil de navegador DEDICADO e persistente (login manual 1×; zero credencial no
# código). ⛔ Nunca o perfil principal do Chrome — o CANAL usa o binário instalado,
# mas o user_data_dir continua sendo o diretório dedicado abaixo.
PROFILE_DIR_NAME = ".phantom_board_profile"
RUNS_DIR_NAME = "runs"
