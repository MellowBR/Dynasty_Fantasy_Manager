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
FORBIDDEN_CLICK_LABELS = ("START DRAFT", "RESET DRAFT", "JOIN DRAFT")

# Seletores da spec do ensaio de 11/08 (classes BEM legíveis; board no documento
# principal, sem iframe; 264 células no DOM, sem virtualização).
SEL_MENU_ITEM = "div.item"                      # menu de contexto da célula
MENU_TITLE_SET_PLAYER = "Set Player"
MENU_DESC_PREFIX = "Manually set a player for Team "   # o N confirma o time
SEL_SEARCH_INPUT = 'input[placeholder="Find player Ctrl + U"]'  # há 3 — usar o do modal
SEL_RESULT_ROW = ".player-rank-item2"           # linha de resultado da busca
SEL_ROW_POSITION = ".position"                  # anti-homônimo: pelo DOM, nunca pixel
SEL_ROW_TEAM = ".team"
SEL_PLUS_BUTTON = ".draft-button"               # habilitado quando NÃO tem .disable
PLUS_DISABLED_CLASS = "disable"
SEL_CONFIRM_BUTTON = ".linear_gradient"         # nasce "Assign a player" → "SET PLAYER"
CONFIRM_READY_TEXT = "SET PLAYER"

# ⚠️ Único seletor que o relatório resumido do ensaio NÃO fixou: a CÉLULA do board.
# O comando `probe` abre o board com o Playwright Inspector para o owner anotar a
# classe real; até lá, `designate` aborta barulhento se isto estiver vazio.
BOARD_CELL_SELECTOR = ""

# Assentamento (o achado que define a arquitetura): comando via DOM, VERDADE via API.
# O board pode não atualizar e o toast vermelho pode MENTIR ("This pick could not be
# processed" com o pick gravado) — só a API decide. Lag observado ~3s.
# 1ª vida do perfil dedicado: a janela abre DESLOGADA (sinal: "JOIN DRAFT" de
# espectador — o board renderiza mesmo assim). O probe/designate esperam o login
# manual do owner em vez de estourar.
LOGIN_WAIT_SECONDS = 120

SETTLE_POLL_SECONDS = 1.5
SETTLE_TIMEOUT_SECONDS = 15.0
COMMAND_RETRIES = 1        # servidor rejeita duplicata — re-comando é seguro

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
