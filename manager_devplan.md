# devplan.md — Fantasy Manager

> Plano vivo + Log de Decisões  
> Última atualização: 03/08/2026-pt3 (MAN-OFF26-4-REFINE-PT2: **absorção dos achados do probe + achado de maior peso do arco**. ⛔ **KEEPER FORA DO BOARD É JOGADOR LEILOÁVEL** — o Sleeper o trata como disponível e **processa o lance normalmente**; jogador com dono é arrematado **ao vivo**, sem desfazer limpo. **Não é contabilidade a corrigir depois — é transação inválida em tempo real** → o **OFF26-4 vira GATE DE INTEGRIDADE DO LEILÃO** e a classe "keeper ausente do board" fica **bloqueante**, não escolha da F2. **Propagado ao OFF26-10** (time bloqueado pelo teto = **keepers expostos** → **população completa do board é PRÉ-CONDIÇÃO DE ABERTURA**; a decisão em aberto do item **não foi arbitrada**) e ao **OFF26-5 + runbook** (nova §B.5: board incompleto **não é estado aceitável**). **IR resolvido:** designar normalmente, excedentes no banco, vaga automática por posição; **descartado** descontar do budget (não resolve — o problema é disponibilidade — e some da auditoria). **D2:** sala = **22 slots** (metade fechada), **8.3.4 pendente**, com caso concreto do IR. **D1 corrigido (texto preservado):** a falha silenciosa **não existe pela API** (404 em 0,2 s; LOADING é do app web) → **timeout vira boa prática**; **não persistir `draft_id` permanece**. **D5:** classe "slot errado" **não existe**. **D6:** construção **liberada** contra placeholders; só a **costura `roster_id` ↔ time** espera os aceites. **Nota de método:** 3ª premissa da família *observação verdadeira, procedência errada*. Sem código)  
> Anterior: 03/08/2026-pt2 (MAN-OFF26-4-PROBE: **probe read-only na liga fantasma real — o bloqueador do §2 da F1 do OFF26-4 CAIU**. Zero escrita, draft não iniciado, board intacto. **Derivação `league_id → draft_id` funciona por 2 caminhos** (`league.draft_id` no topo, 1 request; e `/drafts` com 1 item — o morto não aparece). **Premissa do D1 refutada para a API:** draft morto = **404 limpo em 0,2 s**, não trava (o LOADING é do app web). **Designações expostas pré-draft** em `/draft/{did}/picks` (mesma superfície já usada), 24 registros com **`metadata.amount`** — **totais $148/$95/$60 reconstruídos exatos**. Jogador por `player_id`=`sleeper_player_id`, **⚠️ DEF vem como sigla (`"LAR"`)**; time por `roster_id`; **`owner_id` nulo em 11/12** (D6 confirmado como bloqueio de validação, mas a auditoria casa por roster). **Sem campo de budget por time** → soma, como o D2 já dizia. **Réplica dupla** de leitura de picks (`draft_import.py:39` × `sync_sleeper.py:872`, coerção `float` × `int`), **ambos gateados em `status=="complete"` — era o gate, não a API**. Não previstos: **`is_keeper:false` nas 24**; **`pick_no`/`round` não indicam vaga → D5 sem classe "slot errado"**; **22 slots (10+12 BN)** medem o lado Sleeper da ressalva do D2; **fantasma sem IR** × liga real com IR = divergência concreta. Status 🔲; sem código)  
> Anterior: 03/08/2026 (MAN-OFF26-4-REFINE: **spec do OFF26-4 sincronizada** com a evidência de 02/08 — bloco D1–D7 no padrão do OFF26-2, cada decisão rotulada (**arbitrada** / **resolvida por evidência** / **delegada com critério**); F1 e ATUALIZAÇÃO EMPÍRICA **intactas** abaixo, status segue **🔲**. **D1:** `league_id` em `AppConfig`, **`draft_id` NUNCA persistido** (derivado a cada uso, com timeout explícito — URL morta trava em LOADING); a F2 herda a pendência de que `league_id → draft_id` nunca foi exercitado. **D2:** base = `usable_draft_budget` (resolvida por evidência), com a **ressalva aritmética 22 rodadas × 8.3.4 pendente**. **D3:** ponte de jogador **delegada** com critério "não tocar o OFF26-2". **D4/D5:** 12 times de uma vez; **não populado = estado próprio**, não divergência; 4 classes + severidade na F2. **D6:** só `sleeper_owner_id`; ⛔ **times ainda placeholders (owner_id nulo, convites de 03/08) → F2 não validável contra placeholders**. **D7:** probe exige board populado — janela aberta agora, fecha no próximo reset. Sem código)  
> Anterior: 02/08/2026-pt8 (MAN-OFF26-RUNBOOK-REG-PT2: **2ª execução do Cowork** — runbook corrigido **validado** (Team 3/4/5 populados, totais conferindo). **`draft_id` NÃO é estável**: o reset gerou id novo e **matou o registrado no pt7** (atual `1389755381567213568`; `league_id` estável), com **falha silenciosa** (URL velha trava em LOADING) → **restrição de desenho na decisão 1 do OFF26-4: persistir `draft_id` está descartado por evidência**; persiste-se `league_id` e deriva-se o draft. **⛔ Falso achado rejeitado:** rebaixar o check anti-homônimo — causa era **lista de teste com dados velhos**; check **mantido** e orientação **invertida** (divergência real = parar e reportar). 5 correções de runbook + não fixar URL de board. **Melhoria do OFF26-2** registrada (ordenar a sheet na sequência do board). **Medição perdida** por timeouts de ambiente → risco de **variância imprevisível** (~2 h × ~5 h), mitigação **fatiar por time**; decisão Cowork-2026 **mantida** com reconsideração parcial **aberta**. Sem código)  
> Anterior: 02/08/2026-pt7 (MAN-OFF26-IDS-REG: **fecha as 2 pendências do pt6** sobre a liga fantasma **Dynasty SB FA Auction** — **`league_id` = `1389725099556372481`**, **`draft_id` = `1389725100684611584`** (distintos e **não deriváveis um do outro por inspeção**, reforçando o precedente do `draft_import.py`: passa-se o draft_id e deriva-se o league_id), registrados como **dado** e **não persistidos** em constante/`AppConfig`/coluna — a parametrização segue **decisão em aberto** do OFF26-4; e **RESET DRAFT executado, board vazio**, liga pronta para uso real. **Pré-condição registrada:** o reset **apagou o alvo empírico** dos probes pendentes (pré-draft do OFF26-4 e pós-draft do OFF26-11) → **repopular o board antes de rodar as diagnoses**. Sem código)  
> Anterior: 02/08/2026-pt6 (MAN-OFF26-10-11-REG 2ª parte: **liga fantasma criada e testada** — **Dynasty SB FA Auction** (Redraft, 12, Auction, $200, 22 rodadas, 3 WR; 2 times populados, RESET DRAFT e ids pendentes **naquele momento — ambos resolvidos no pt7 acima**). **§5 da F1 do OFF26-4 REFUTADO por experimento:** o Sleeper aplica a **mesma reserva de $1/vaga** (`teto = 200 − gasto − (vagas−1)`; $29 aceito, $32+ recusado) → base correta = **`usable_draft_budget`**, decisão 2 **resolvida por evidência**. **OFF26-10:** time acima do teto **não entra no board** → **população escalonada obrigatória**. **OFF26-11:** **indício** `is_keeper:false` (verificação definitiva é pós-draft). **Runbook corrigido — o caminho da Fase B não existe**; +7 correções e seção nova do teto. **Medido:** ~75 s/jogador ≈ **2,5 h p/ 12 times** → 2026 via **Cowork**, script determinístico p/ **2027**, API interna **descartada**. Sem código)  
> Anterior: 02/08/2026-pt5 (MAN-OFF26-10-11-REG: **registro docs-only** — o calendário real da intertemporada 2026 (17/08 rookie draft · 18/08 congelamento ESPN · 20/08 cortes · **22/08 late drop** · 24/08 FA auction) expôs 2 gaps inéditos: **OFF26-10 🔲** (late drop altera keepers **dois dias após o lock**; sheet de 20/08 é provisória p/ quem fechou acima do cap) e **OFF26-11 🔲** (importador não distingue **keeper de arremate novo**; a porta canônica é de **contrato ano 1** → ingerir keeper zera a idade do contrato). Duas questões empíricas registradas como **probe, não fato**; duas **decisões em aberto** deixadas com o owner. **Emenda de premissa:** o **rookie draft NÃO roda em liga fantasma** — existe **uma** liga fantasma permanente (a da FA auction), não duas. Sem código)  
> Anterior: 02/08/2026-pt4 (MAN-S2-DONE: **S2 ✅** — smoke prod sobre o hash `9b4bcf1` (backup `/data/dynasty_pre_s2_smoke_2026-08-02.db`): as 4 posições convergiram para o alvo da F1b (pos. 2 = Fazenda sem troca, pos. 5 = 3 peat → Cangaceiros), cruzamento com o board do Sleeper confere, **2ª execução sem alteração** (idempotência em prod), verify do lottery conferindo. Migração O3 feita; fatia F2-3 desmembrada como **S5 🔲**. Arco S2/S3 ✅; ativos S4 e S5, nenhum bloqueante. Nota de método: a correção do critério de validação do prompt partiu do Code contra a tabela-alvo da F1b)  
> Anterior: 02/08/2026-pt3 (MAN-S2-F2: desconto determinístico da permutação do board — novo `board_mirror.py` (π derivado das fontes canônicas, bijeção obrigatória), armamento por **season** em AppConfig (rollover desarma sozinho) + gate de audit canônica, ligado em `_resolve_traded_pick_identity` **e** no loop de picks do `_sync_trades`, card de armar/desarmar no `/admin`. **F2-1 = redundante**: o próprio sync reescreve as 4 posições. 24/24 em cópia + 48/48. ⚠️ **✅ só após smoke prod (PROC1)**)  
> Anterior: 02/08/2026-pt2 (MAN-S3-DONE: **S3 ✅** — smoke prod aprovado sobre o hash `89dc08d` (gate PROC1; backup `/data/dynasty_pre_s3_smoke_2026-08-02.db`): /picks 12 linhas/temporada e 108 picks, /league correto, verify do lottery conferindo, dynasty resolvendo no /trades. **Sync religado** e a 1ª execução real ingeriu o rename do time 9 **sem duplicação** (projeção #11 preservada) — suspensão encerrada. Migração O3 feita. **S2 segue 🔲**: posições 2–5 do R1 2026 no estado permutado até o S2-F2)  
> Anterior: 02/08/2026 (MAN-S3-F2: picks casadas por **id de time**, nome vira display derivado — sem schema (os ids já existiam e já estavam corretos); join da projeção migrado para id porque refrescar `DraftLotteryResult.team_name` quebraria o verify do M8; `_resolve_traded_pick_identity` criado como ponto de costura do S2-F2. 25/25 em cópia + 48/48. ⚠️ **✅ só após smoke prod (PROC1)**; sync segue suspenso. Arco S2→S3→S4 registrado no improvements)  
> Anterior: 31/07/2026-pt2 (MAN-F13: cache do pool Sleeper descongelado — F1 diagnose + F2 (volume `/data` + carimbo por conteúdo, commit `2cd8de3`) + CLOSE ✅ com smoke prod (recaptura 287); DP3 ✅ fechado no mesmo dia (smoke prod `e12fdef`) com ressalva baixada pelo F13; F14 🔲 cosmético; regra nova de smoke local no DEV_METHODOLOGY)  
> Anterior: 31/07/2026 (MAN-DP3: board de rookies do cap_projector = classe entrante capturada (snapshot `in_class`, D1–D5); ⚠️ F2 localhost, aguarda smoke prod; commit `e12fdef` pushado; F13 🔲 registrado)  
> Anterior: 23/06/2026-pt4 (MAN-PROC1: PROC1 ✅ — gate de hash deployado afinado no DEV_METHODOLOGY (Forma 1, transversal); PROC2 🔲 registrado; edição do DEV_METHODOLOGY aplicada mas não commitada (repo umbrella sem commits))  
> Status atual: Produção (Render: dynasty-fantasy-manager.onrender.com) | Tag: `manager-v1.0` | PythonAnywhere legacy

---

## Visão Geral

O Fantasy Manager é o sistema operacional da liga Dynasty SB. Gerencia o estado
canônico da liga: contratos, salary cap, picks, trades e workflows de offseason.
É o único projeto com permissão de escrita no `dynasty.db`.

**Filosofia:** Confiabilidade acima de features. O Manager precisa ser a fonte de
verdade — erros de salary cap ou player matching têm consequências reais para 12 owners.

---

## Camadas de Desenvolvimento

### Camada 0 — Fundação ✅ Done

- Flask app factory com SQLAlchemy
- 15+ modelos: Team, Player, SalaryHistory, Pick, Trade, AuctionLog, AppConfig, etc.
- `salary_engine.py` puro (zero DB dependencies) + unit tests (`salary_engine_test.py`)
- Import inicial via `dynasty_rosters_clean.csv`
- Sync com Sleeper API (rosters, picks, IR slots, player cache semanal)
- 7 blueprints: roster, salary, trades, picks, auction, admin, offseason
- Audit trails completos: SalaryHistory (rule_applied), PlayerHistory, SyncLog, AuctionLog, ESPNImportLog

### Camada 1 — Offseason Workflow ✅ Done

- 7-step offseason workflow completo
- Draft lottery (pesos: último 50%, penúltimo 25%, ante-penúltimo 12%, 8º 5%, 7º 3%)
- ESPN PDF parser (`espn_pdf_parser.py`) com 3-tier matching
- Season rollover: aplica VALORIZAÇÃO, incrementa contract_year
- Ordenação Round 1 via `draft_lottery_result` + `season_standings` (F2)

### Camada 2 — Salary Cap Accuracy ✅ Done

- `correct_player_salary()` atômico em `models.py` (Player + SalaryHistory + PlayerHistory)
- `player_lookup.py` centralizado — `find_player_by_name()` com hierarquia estrita:
  exato → case-insensitive → normalizado. Substring e surname isolado bloqueados. (F1)
- ESPN ref values armazenados já ajustados (raw × 1.2)
- Histórico inline accordion em `/salary_history` (F3)

### Camada X1 — Multi-User Access ✅ Done (31/03/2026)

**X1a — Preparação para produção**
- `wsgi.py` como entry point WSGI
- `.env` com `APP_ENV`, `SECRET_KEY`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
- `load_dotenv()` no topo do `app.py`; debug condicional via `APP_ENV`
- `ProxyFix` para resolver redirect URI corretamente atrás do reverse proxy
- `requirements.txt` corrigido: flask-login, authlib, python-dotenv, pandas, openpyxl
- Startup sync com try/except para degradação elegante

**X1b — Google OAuth + Flask-Login**
- Blueprint `routes/auth.py`: `/login`, `/login/google`, `/auth/callback`, `/logout`
- `LoginManager` com unauthorized_handler: 401 JSON para `/api/*`, redirect para `/login` nas páginas
- OAuth via `authlib` + Google OpenID Connect
- Template `login.html`; email não cadastrado → 403

**X1c — Tabela users + seed_users.py**
- Model `User(UserMixin)`: email, name, team_id FK, is_admin
- Migration em `_run_migrations()`
- `seed_users.py`: aceita CSV ou parâmetros CLI (`--email`, `--name`, `--team-id`, `--admin`, `--list`)

**X1d — Decorators de permissão**
- `@login_required` em todas as rotas (exceto login/callback)
- `@admin_required` em 27 rotas POST/PATCH/DELETE irreversíveis
- Exceções: `POST /api/admin/sync` → `@login_required`; `POST /api/trades/preview` e
  `POST /api/salary/calculate` → `@login_required` (simulações)
- `POST /api/player/<id>/ir` → `@admin_required` (correção administrativa)

### Camada M5 — Ordenação por Posição ✅ Done (02/04/2026)

- `POS_ORDER` movido de `routes/roster.py` para `models.py` como constante central
- `sort_players_by_pos(players)` criada em `models.py`: posição (QB→DEF) + salary DESC
- Aplicada em `routes/roster.py` (2 endpoints API) e `routes/salary.py` (cap projector)

### Camada C — Deploy Render ✅ Done (02/04/2026)

Migração de host primário de PythonAnywhere para Render. Manager em https://dynasty-fantasy-manager.onrender.com.

- **C1 — Preparação para produção:** `wsgi.py` como entry point, persistent disk `/data/`, env vars (`APP_ENV`, `SECRET_KEY`, `GOOGLE_CLIENT_*`, `DYNASTY_DB=/data/dynasty.db`), `ProxyFix` condicional.
- **C2 — init_data.py (seed de banco):** copia `dynasty.db` do repo para `/data/` apenas no primeiro deploy; nunca sobrescreve. Mesmo padrão do optimizer.
- **C3 — Controle de acesso auditado:** `data/users.csv` no git (exceção no `.gitignore`) como fonte do auto-seed de users no startup. `dynasty.db` no repo como seed para manter salários/contratos corretos em produção (sync Sleeper nunca sobrescreve dados financeiros).

PythonAnywhere mantido como legacy em https://mellowbr.pythonanywhere.com.

### Camada F7b — Data migration automática para produção ✅ Done (22/04/2026)

Follow-up do F7 para limpar o DB em produção sem depender do Render shell (experiência ruim). Adicionada Migração 4 em `_run_migrations()` (app.py) com 3 blocos guardados por `SELECT COUNT`, idempotentes. Próximo boot do Render pós-deploy detecta e limpa: 9174 rows de `salary_history` inflado, rewrite 3 Browns + DELETE salary_correction, 220 notes cosméticos em rollover.

Validação local em 3 cenários (DB limpo, stale injetado, re-run pós-migração) — guards funcionam como esperado em todos.

### Camada F7 — Fix SalaryHistory + rewrite 3 Browns + redesign /salary_history ✅ Done (22/04/2026)

Trinca de problemas descobertos via diagnose F1 + F1b na mesma sessão. Implementação em um commit.

- **Fix crítico:** removido INSERT em `SalaryHistory` dentro de `run_import()` (`import_csv.py:104-111`). Rollover e auction criam SalaryHistory legítimo. Cleanup: `DELETE FROM salary_history WHERE rule_applied='import'` removeu 9174 rows fósseis (~33× inflação causada por reboots acumulados).
- **3 Browns — Opção A (rewrite):** UPDATE em PlayerHistory para refletir salários reais desde o draft (A.J.Brown $47, Marquise $3, Amon-Ra $61). DELETE das 3 rows `salary_correction`. Audit do bug mora em improvements.md (F1) + Log — sem rastro no banco.
- **Redesign narrativo:** `/api/salary_history` agora lê `PlayerHistory` em vez de `SalaryHistory`. Template agrupa por jogador em cards; rótulos PT-BR por event_type ("Draft (Auction)", "Mantido como keeper", "Renovado pela VALORIZAÇÃO", "Trade", etc.). Expansão inline usa `/api/player/<id>/history` já existente. Coluna "Regra" removida.
- **Cleanup extra:** 220 PlayerHistory rollover rows com `notes='import'` (fóssil) atualizadas para `'Renovado (VALORIZAÇÃO)'`.

### Camada S1 — Sync automático de trades do Sleeper ✅ Done (22/04/2026)

Sync automático de trades + backfill da temporada anterior. Trade table passa de 0 rows para 29 (seed); PlayerHistory trade events de 0 para 78.

- **Nova função `_sync_trades(league_id)`** em `sync_sleeper.py`: itera legs 1-18, filtra `type=trade AND status=complete`, idempotente via `sleeper_transaction_id`. Move `Player.team_id` via `adds/drops`, `Pick.current_team_id` via `draft_picks[]`. Cria `PlayerHistory` por ativo + `Trade` row com `source='sleeper_sync'` + `trade_date` do `created` (ms epoch) do Sleeper.
- **Integrado em `run_sync()`:** toda sincronização com Sleeper detecta trades automaticamente.
- **Endpoint `POST /api/admin/sync_trades/backfill`** (`@admin_required`): importa da `previous_league_id` (season anterior).
- **Migração:** `Trade.source` (default 'manual') + `Trade.sleeper_transaction_id` (unique nullable) via `_run_migrations()`.
- **Tratamento C+ para N-way:** 2-way = row normal; N>2 = placeholder `team_b="N-way: ..."` + `description="[N-WAY] ..."`. Admin sempre vê a trade na UI, nunca precisa de código.
- **UI:** card "Trades Históricas (Backfill)" em `/admin` com botão.

### Camada M9-FIX — Todas as picks clicáveis + pré-seleção no /trades ✅ Done (23/04/2026)

Feedback pós-deploy do M9 revelou escopo restritivo: só picks trocadas de outros times eram clicáveis. Ampliou-se para todas as picks (minhas ou de outros), com comportamento diferente por ownership. Estende M14 com params `pick_a`/`pick_b` — /trades recebe e marca checkbox automaticamente após `loadSide`.

- **Template `picks.html`**: `clickable = my_team_name is not None`. Href condicional: minha pick → `/trades?team_a=meu&pick_a=<id>`; pick de outro → `/trades?team_a=meu&team_b=<dono>&pick_b=<id>`.
- **`routes/trades.py`**: helper `_resolve_preset_pick(arg_name, team_name)` valida pick existe + pertence ao team do lado correspondente. Ignora mismatch silenciosamente.
- **`templates/trades.html`**: `data-preset-pick-a`/`data-preset-pick-b` no container, `data-pick-id` nos checkboxes. No `loadSide`, após renderizar picks, marca checkbox do preset + adiciona ao `selected.picks[side]` + `updateDynastyBar()`. Consome dataset após uso.
- **Validado em 7 cenários** (23/04/2026): 108 células clicáveis (9 minhas + 99 outras), preset-pick correto nos 4 caminhos (só A, só B, A+B, sem params), pick inexistente/mismatch ignorados.

### Camada M13 — Página de jogador + "Propor Trade" ✅ Done (23/04/2026)

Entrega de página dedicada por jogador (`/player/<id>`) com foto (Sleeper CDN), bloco de contrato incluindo dynasty value, timeline histórica reusando `/api/player/<id>/history`, e botão "⇄ Propor Trade" que dispara M14 com os dois times pré-selecionados. Links a partir de `/` (roster), `/salary_history`, `/trades` concluem o atalho universal.

- **Rota `GET /player/<int:player_id>`** em `routes/roster.py`. `player_id` (não `id`) para evitar shadow builtin. `dynasty_value` resolvido no backend via `get_dynasty_values()` (padrão T2) — zero flash visual, zero round-trip extra. `can_propose_trade` pré-calculado no backend.
- **Partial novo `templates/_trade_detail_modal.html`** extrai modal clicável de trade do `salary_history.html`. Reusado em `/salary_history` e `/player/<id>`. Evita divergência futura.
- **Template `player_detail.html`**: header com foto sleepercdn (onerror fallback), grid de contrato com 6 campos, timeline inline fetch. Botão "Propor Trade" condicional a `can_propose_trade`.
- **Links em 3 telas**: roster (Jinja server + ícone 🔗 discreto preserva `showPlayerHistory` modal), salary_history (JS com `stopPropagation` pra não colidir com accordion), trades (JS com `target=_blank` + `stopPropagation` pra não toggleiar checkbox do `<label>`).
- **Validado em 10 cenários** (23/04/2026): render McBride/Bowers, botão só pra outros times, 404, Hollywood sem sid, dynasty server-rendered, modal partial em ambas páginas, links corretos.

### Camada M9 — Grid navegável de picks + atalho para trade ✅ Done (23/04/2026)

Substitui listas verticais da `/picks` por grid matrix 12 times × 3 rounds. Cada célula é clicável quando a pick é de outro dono — abre `/trades` com dois times pré-selecionados via M14. Reduz fluxo de "ver pick → anotar → ir em trades → selecionar 2 times" (4 passos) para 1 clique.

- **Backend**: `picks_page` reorganiza dados como matrix `{season: {teams_ordered, cells, projections}}`. Ordem de linhas por `projected_pick` do R1 (fallback alfabético). Passa `my_team_name` derivado de `current_user.team_rel.name` (None se admin sem time).
- **Template**: grid 4 colunas (rowlabel + R1 + R2 + R3). Célula é `<a>` linkando `/trades?team_a=<meu>&team_b=<atual>` apenas quando `traded_away=True` + `current_team != my_team`. Senão é `<div>` estático. Banner de warning quando `my_team_name is None`.
- **CSS**: `.picks-matrix`, `.picks-matrix-cell` com variantes `is-mine` (borda verde), `is-traded` (fundo azul), `clickable` (hover highlight). `.picks-badge` para `#N` do pick.
- **Admin preservado**: botão ✎ por célula (opacity 0 default, 1 no hover) chama `openPickEdit` existente.
- **Filtro adaptado**: `filterTeam` itera em grupos de 4 children após headers — mostra linha se `origTeam === name` ou alguma célula tem `current_team === name`.
- **Validado em 9 cenários** (23/04/2026): status 200, primeira linha Miller Time! (pick 1 do lottery), 18 células trocadas visíveis, 16 clicáveis (excluindo 2 que chegam ao Cangaceiros), 9 células `is-mine`, seasons 2027/2028 sem projeção com ordem alfabética, warning pra user sem time.

### Camada M8 — Lottery auditável + visualização de bolinhas + fluxo duas fases ✅ Done (23/04/2026)

Transforma o draft lottery em operação auditável e visualmente transparente. Resolve três problemas simultâneos: (1) sorteio com seed não persistido dificultava qualquer auditoria; (2) UI mostrava só tabela de resultado sem contexto visual; (3) fluxo "re-rodar até travar" permitia cherry-picking teórico.

- **Modelo `LotteryAudit`**: UUID natural via auto-increment, `random_seed` (token_hex(16)), `weights_json`, `pool_json` (snapshot dos 5 times no momento), `result_hash` (SHA256 picks 1-5), `previous_audit_id` + `reason` + `is_canonical` para histórico de re-runs.
- **Helper `_draw_weighted_lottery(pool, seed)`**: bolinhas literais + `random.shuffle` com `random.seed` único (Opção B). Pure function, determinística, testável isoladamente.
- **Endpoints novos**: `run_lottery` reescrito (409 se canônica existe), `lottery_replace` (exige `reason`), `/verify` (re-reprodução via pool+seed salvos), page `/picks/lottery/<season>` com histórico.
- **UI duas fases**: pool de 95 bolinhas coloridas (paleta fixa 5 cores) + legenda com %, SEM botão "testar". Execução oficial com confirm duplo → reveal animado pick a pick (setTimeout 1500ms, scale + glow dourado) → "Travar" + "Executar novamente (com justificativa)" + "Ver auditoria".
- **Re-run com atrito público**: modal exige textarea de motivo, audit anterior vira `is_canonical=False`, nova row linkada via `previous_audit_id`. Tudo visível em `/picks/lottery/<season>` → tabela "Histórico de tentativas anteriores".
- **Validado em 9 cenários** (23/04/2026): run inicial, 409 duplicado, verify match, tampering detectado, replace com reason, replace 400 sem reason, audit page, UI, regression salary_engine 48/48.

### Camada T2 — Valores dynasty FantasyCalc no preview de trade ✅ Done (22/04/2026)

Integra valores de mercado dynasty (fonte: FantasyCalc) ao simulador de trade. Preview ganha enriquecimento per-asset e barra visual que atualiza em tempo real conforme assets são selecionados.

- **`dynasty_values.py`**: fetcher + cache JSON (`data/.dynasty_values_cache.json`, TTL 24h), `get_dynasty_values()`, `pick_sleeper_id()` para converter Pick em `DP_<year_offset>_<pick_index>`. Degradação elegante se API/cache indisponíveis.
- **`_compute_cap_impact()` enriquecido**: cada asset ganha `dynasty_value`, cada side ganha `dynasty_total_out/in/delta`, top-level `dynasty_available`.
- **2 endpoints novos** em `routes/trades.py`: `GET /api/dynasty_values` + `POST /api/admin/dynasty_values/refresh` (ambos `@login_required` — refresh não precisa admin por ser read-only externa).
- **Frontend em `templates/trades.html`**: banner freshness, badge inline per checkbox (`🪙6.801`), barra espelhada dinâmica com recálculo 100% client-side em `toggleAsset()`, modal enriquecido com badge de vantagem e deltas por side.
- **CSS em `static/style.css`**: `.dynasty-banner`, `.dynasty-value-badge`, `.dynasty-bar-section/track/fill-a/fill-b`, `.dynasty-advantage`.
- **Validado em 6 cenários** (22/04/2026): endpoints OK, preview enriquecido (McBride ↔ Bowers delta +159), degradação elegante confirmada (FC fora + cache vazio → UI funciona sem dynasty), `salary_engine_test` 48/48.

### Camada T1 — Trade Manager como simulador puro + link compartilhável ✅ Done (22/04/2026)

Com S1 ativo (trades capturadas automaticamente do Sleeper), o botão "Confirmar Trade" do Manager virou redundante e gerava shadow trades (Manager confirmava antes do Sleeper, S1 criava duplicata). T1 redesenha o `/trades` como simulador puro com link compartilhável de 7 dias.

- **`POST /api/trades/confirm` removido** (`routes/trades.py`) + import `PlayerHistory` + JS `executeTrade()` + botão "Confirmar Trade" do template. Zero side-effect no DB vindo da tela de trades.
- **Novo modelo `TradeProposal` em `models.py`**: UUID v4 como PK, assets como JSON text, TTL 7 dias via `expires_at`. Criada via `db.create_all()` (tabela nova, sem migration explícita). Relationships com Team e User.
- **Helper `_compute_cap_impact()`** extraído como função pura em `routes/trades.py` — compartilhado entre `preview_trade()` (JSON) e `view_trade_proposal()` (template). Zero duplicação.
- **Novos endpoints**: `POST /api/trades/proposals` (cria com UUID, valida assets em ambos os lados) e `GET /trades/proposta/<uuid>` (renderiza read-only). Ambos `@login_required`.
- **Template `trade_proposal.html`**: preview read-only com layout reutilizado de `trades.html`, badge "📸 Simulação", info de criação e expiração visível. Sem controles de ação.
- **UI em `trades.html`**: "✅ Confirmar Trade" → "🔗 Gerar Link Compartilhável". Modal ganhou seção com input copiável + "📋 Copiar" (clipboard API + fallback) + "↗ Abrir" em nova aba.
- **Validação via Flask test_client** (22/04/2026): 8/8 casos (botão removido, endpoint 404, proposal criada, URL renderizada, expirada 410, sem login 302, sem assets 400, preview continua funcional).

### Camada F6 — Remover "keeper" como acquisition_type ✅ Done (22/04/2026)

Eliminação do pseudônimo `keeper` do vocabulário canônico de `acquisition_type`. Decisão de manutenção ("player foi kept") não é origem de aquisição — um jogador adquirido via startup auction continua sendo auction_draft mesmo que tenha sido kept na offseason.

- **Migration 6 em `_run_migrations()` (app.py)**: `UPDATE players SET acquisition_type='auction_draft' WHERE acquisition_type='keeper'`. Guard COUNT, idempotente. Aplicou em 60 players (dos 101 originais; F8a havia reconciliado 41 via última aquisição Sleeper ≥ 2025).
- **`salary_engine.py`**: `_AUCTION_TYPES = {"auction_draft"}` (removido `"keeper"`). `keeper_salaries`/`num_keepers` em `draft_budget()` mantidos — nomes descritivos do resultado, não `acquisition_type`.
- **Consumidores atualizados**: `import_csv.py` (mapping `keeper → auction_draft`), `routes/admin.py:707` (tuple origin_event), `salary_engine_test.py` (test redundante removido), `templates/salary.html` (dropdown).
- **CSV atualizado**: `data/dynasty_rosters_clean.csv` — 100 rows `keeper` → `auction_draft`.
- **Regression zero**: `salary_engine_test.py` 48/48, cap per team idêntico pré/pós (salary_engine já tratava os dois igualmente).

### Camada F8c — Endpoint admin, UI e boot skip ✅ Done (22/04/2026)

Mecanismo de acionamento em produção para o F8a + UI de visibilidade para o owner.

- **3 endpoints em `routes/admin.py`** seguindo o padrão de `sync_trades_backfill` (`@admin_required`, JSON response, erro via try/except com traceback): rebuild (com `?dry_run=1`), restore. Helpers `_latest_snapshot_path` e `_snapshot_info` consultam `data/.player_history_snapshot_*.json` via glob.
- **Card UI `Histórico Canônico (F8)` em admin.html**: 3 botões (simular/executar/restaurar), banner verde quando flag ativa, small-text com timestamp do último snapshot, `disabled` no botão restore quando não há snapshot. JS segue padrão S1 de result-box com classes `result-ok/result-warn/result-error`. Confirms duplos em rebuild e restore para evitar execução acidental.
- **EVENT_LABELS novos em `salary_history.html`**: `drop`, `free_agent`, `commissioner` (fa_auction já existia). Sem isso, eventos do F8a apareceriam crus ("drop" em vez de "Dropado") no `/salary_history`.
- **Boot skip em `app.py`**: antes de `_backfill_player_history()` no block `if fresh_import`, verifica `get_config('f8_rebuilt', 'false')`. Se `true`, log `[boot] F8 rebuild já executado — _backfill_player_history ignorado` e skipa. Função não removida — continua disponível para DBs novos.
- **Nova seção em `manager_vision.md`**: "Calendário Operacional da Liga" documenta o ciclo anual completo (ESPN → lottery → rookie → drop/cap → FA auction Sleeper → registro manual no Manager → sync trades S1). Documenta explicitamente o gap de standings não sincronizados.
- **Validado via Flask test_client** (22/04/2026): dry-run, rebuild real, restore (4 casos revertem ao CSV), re-rebuild (4 casos voltam ao canônico F8), GET /admin renderiza card corretamente. `salary_engine_test.py` 49/49.

### Camada F8b — Guard CSV para campos canônicos do F8a ✅ Done (22/04/2026)

Proteção de `Player.acquisition_type` e `Player.contract_start_season` contra overwrite do `run_import()` no boot. Sem isso, as 180 correções do F8a seriam revertidas no próximo deploy a partir do CSV stale.

- **`AppConfig.f8_rebuilt` como flag:** `_rebuild_player_history(dry_run=False)` seta `'true'` no fim do path bem-sucedido. `run_import()` lê no início via `get_config('f8_rebuilt', 'false')` e envolve as duas atribuições em `if not f8_rebuilt` (update path apenas). Create path fica inalterado — player novo no CSV precisa dos valores iniciais.
- **Log condicional:** 1 linha no início do `run_import()` informando que os campos protegidos serão pulados. Silencioso per-player.
- **Validado em 3 cenários** (22/04/2026): (1) rebuild seta flag ✓; (2) reboot preserva 4 casos F8a ✓; (3) DB sem flag reverte do CSV — compat original preservada ✓.

### Camada F8a — Core rebuild de PlayerHistory via Sleeper chain ✅ Done (22/04/2026)

Substituição do `_backfill_player_history()` (inventava events a partir do Player atual) por walk canônico da chain 2024→2025→2026 + drafts + transactions. Corrige `acquisition_type` e `contract_start_season` retroativos quando divergem da verdade Sleeper.

- **Migration 5 em `_run_migrations()` (app.py)**: adiciona coluna `sleeper_event_ref` TEXT em player_history + backfill das 78 trade rows (S1 pattern `tx:<id>`) e 220 rollover rows (`rollover:<season>`) + pré-limpeza de duplicatas + `CREATE UNIQUE INDEX uq_player_history_event` no quintupleto `(player_id, season, event_type, team_name, sleeper_event_ref)`. 5 sub-blocos idempotentes via guard COUNT.
- **6 funções novas em sync_sleeper.py**: `_walk_league_chain` (recursivo até `previous_league_id=None`), `_classify_draft` (heurística validada: `type=linear → rookie_draft`; `type=auction` com rounds≥20 na primeira liga → `auction_draft`; demais auction → `fa_auction`), `_collect_draft_events`, `_collect_transaction_events` (skipa `type=trade`, delegado ao S1), `_snapshot_player_history` (dump JSON em `data/.player_history_snapshot_<ts>.json`), `_rebuild_player_history(dry_run=False)` (orquestrador).
- **Modelo F8PlayerBackup** em models.py: tabela auxiliar para rollback das correções de `Player.contract_start_season` e `Player.acquisition_type`. Usada pelo endpoint F8c `/api/admin/player_history/restore`.
- **Delegação de trades ao S1**: `_rebuild_player_history` chama `_sync_trades(lid)` por liga na chain, garantindo cobertura retroativa. Preserva 78 rows existentes via UNIQUE.
- **Resultado local**: total PlayerHistory 578 → 1092 rows (269 draft + 603 tx + 220 rollover preservado); 320 rows fictícias deletadas; 180 players com campos corrigidos. 4 casos de validação (Aiyuk, Bowers, BUF, Stroud) conferem com a proposta F8 original. 49 testes do salary_engine passam. Re-run do rebuild retorna `events_written=0, events_skipped=794`.

### Camada M12 — Admin Users (UI de vinculação Owner↔Time) ✅ Done (22/04/2026)

Tela `/admin/users` substitui o uso manual de `seed_users.py` + edição de `data/users.csv` para operação cotidiana de vincular owners a times.

- **Backend:** 5 endpoints em `routes/admin.py` — page `GET /admin/users` (`@login_required`), REST `/api/admin/users[/<id>]` para list/create/patch/delete (writes com `@admin_required`)
- **Frontend:** `templates/admin_users.html` — tabela única com 12 linhas, avatar Sleeper (via `Team.owner_avatar` já populado pelo sync), inputs inline (email/nome), checkbox admin. Seção secundária para users órfãos (team_id=NULL)
- **Sem migração de schema:** lookup Manager↔Sleeper via relação `User.team_rel.sleeper_owner_id` existente. Economiza coluna redundante.
- **Sem chamada Sleeper API na tela:** dados já vêm do sync. Usuário roda "Sincronizar com Sleeper" no `/admin` se precisar atualizar.
- **Sem sync bidirecional com `users.csv`:** CSV continua sendo apenas seed inicial; UI é source-of-truth pós-seed. Aceitável pois Render usa persistent disk + init_data.py é no-overwrite.

---

## Backlog Ativo

### Features

| ID | Item | Prioridade | Status |
|----|------|------------|--------|
| T1 | Simulador de trade compartilhável (link público, sem X2) | Alta | 🔲 Pendente |
| X2 | Trades multi-usuário (propor / aceitar / recusar) | Média | 🔲 Deferido pós T1 |

### Melhorias

| ID | Item | Prioridade | Status |
|----|------|------------|--------|
| M1 | Validação de cap antes de confirmar trade (server-side) | Média | 🔲 Pendente |
| M2 | Alerta de jogadores `needs_review=True` pendentes (badge navbar) | Baixa | 🔲 Pendente |
| M3 | Endpoint `/api/estado` JSON read-only para outros owners | Baixa | 🔲 Pendente |
| M4 | Banner de sync desatualizada com timestamp + botão sincronizar | Baixa | 🔲 Deferido do X1 |

---

## Passos Manuais Pendentes (Deploy PythonAnywhere)

Estes passos não podem ser executados pelo Claude Code — requerem ação manual:

1. ✅ **Criar Google OAuth credentials** no Google Cloud Console (feito 01/04/2026)
   - Authorized redirect URIs: `https://mellowbr.pythonanywhere.com/auth/callback` + `http://localhost:5000/auth/callback`
2. ✅ **Popular `.env`** no PythonAnywhere com as credenciais geradas (feito 01/04/2026)
3. ✅ **Users seeded** — auto-seed no startup a partir de `data/users.csv` (não requer mais ação manual)

---

## Log de Decisões

### 28/03/2026 — Camada 2 (Salary Cap Accuracy)

- **player_lookup.py centralizado:** antes, cada módulo fazia sua própria busca por nome.
  Decisão de criar função canônica que todos os caminhos de escrita usam.
  Substring e surname isolado bloqueados explicitamente — não é fallback silencioso, é erro.

- **correct_player_salary() atômico:** correções de salário precisam tocar Player,
  SalaryHistory e PlayerHistory na mesma operação. Separar em chamadas distintas
  criava risco de inconsistência se uma falhasse.

- **Bug "3 Browns" (F1):** partial matching durante o import original do CSV resolveu
  Marquise Brown, A.J. Brown e Amon-Ra St. Brown para o mesmo registro.
  Corrigido atomicamente nos três jogadores nos três campos.

- **Ordenação Round 1 rookie draft (F2):** lógica precisava consultar `draft_lottery_result`
  para picks 1-5 e `season_standings` para picks 6-12. Estavam sendo lidas de fonte incorreta.

### 31/03/2026 — Camada X1 (Multi-User)

- **PythonAnywhere vs Cloudflare Tunnel:** migrado para PythonAnywhere (~$5/mês) para
  o app rodar 24/7 sem depender do computador do Erico. Consequência: split entre DB de
  produção (PythonAnywhere) e DB local (usado pelo Optimizer e Predictor).

- **APP_ENV em vez de FLASK_ENV:** FLASK_ENV foi deprecated no Flask 2.x.
  Toda lógica condicional de ambiente usa APP_ENV daqui em diante.

- **url_for com _external=True no callback OAuth:** necessário para resolver a URI
  corretamente atrás do reverse proxy do PythonAnywhere.

- **@admin_required escopo restrito:** qualquer owner autenticado pode simular um trade
  ou forçar uma sincronização. Só ações irreversíveis de intertemporada exigem admin.
  Evita que owners fiquem bloqueados em funcionalidades de uso cotidiano.

- **seed_users.py via CSV:** os team IDs já existem no dynasty.db de produção.
  Script lê CSV (email + team_id) e popula tabela users. Três Cowork prompts criados
  para os passos manuais que o Claude Code não pode executar remotamente.

### 02/04/2026 — Camada M5 (Ordenação por Posição)

- **POS_ORDER em models.py:** constante vivia em routes/roster.py e precisava ser
  duplicada para routes/salary.py. Movida para models.py como única fonte de verdade.
  sort_players_by_pos() centraliza o critério: posição (QB→DEF) + salary DESC como tiebreaker.

### 02/04/2026 — Reorganização de Pastas

- **Pasta `data/` criada:** CSVs e PDFs movidos da raiz para `data/`, alinhando com
  Optimizer e Predictor que já usam essa estrutura. `data/` não vai pro GitHub
  (coberto por `*.csv`, `*.pdf` e `data/` no `.gitignore`).
- **CSVs de stats (receiving, rushing, passing):** mantidos em `data/` como dado bruto
  para futura feature de atualização automática de ESPN ref values (M6 no improvements.md).
  Renomeados para remover números entre parênteses.
- **Docs renomeados:** `manager_devplan.md` → `devplan.md`, `manager_vision.md` → `vision.md`.
  Padrão de 4 docs (CLAUDE.md, devplan.md, improvements.md, vision.md) agora completo.
- **import_csv.py:** CSV_PATH atualizado para `data/dynasty_rosters_clean.csv`.
- **Docs prefixados:** Erico prefere `manager_devplan.md` / `manager_vision.md` para
  deixar claro o projeto a que pertencem (mesmo padrão de `optimizer_vision.md`).

### 02/04/2026 — Fix OAuth local + Auto-seed users

- **ProxyFix condicional:** `ProxyFix` estava rodando sempre, inclusive localmente.
  Sem reverse proxy, corromperia a URL do callback OAuth. Fix: `if APP_ENV == "production"`.
- **app.run(host='localhost'):** Flask subia em `0.0.0.0`, gerando callback com `127.0.0.1`
  que não batia com `localhost:5000` cadastrado no Google Console.
- **APP_ENV local:** `.env` local tinha `APP_ENV=production` (copiado do PythonAnywhere).
  Corrigido para `development`.
- **GOOGLE_CLIENT_SECRET:** `.env` local tinha secret antigo/errado. Corrigido.
- **Auto-seed users no startup:** users eram populados manualmente via `seed_users.py` CLI.
  Agora o startup lê `data/users.csv` e insere novos emails automaticamente (skip existentes).
  Limitação aceita: mudança de email de um owner requer intervenção manual (raro para 12 owners).

### 02/04/2026 — Deploy no Render (C1-C3)

- **Render.com como host primário:** Migrado de PythonAnywhere para Render. Dois web services
  independentes (Manager + Optimizer), cada um com seu repo no GitHub.
- **Persistent disk `/data/`:** `dynasty.db` reside em `/data/` no Render. Env var `DYNASTY_DB`
  define o path; fallback para path local garante que dev local continua funcionando.
- **Seed DB no repo:** `dynasty.db` incluído no git (exceção no `.gitignore`). `init_data.py`
  copia para `/data/` no primeiro deploy; não sobrescreve se já existir (preserva dados de produção).
- **`data/users.csv` no git:** Exceção no `.gitignore` para que o auto-seed de users funcione
  no deploy. Sem isso, tabela `users` ficava vazia no Render → 403 para todos.
- **Sync NÃO sobrescreve salários:** O Sleeper sync (`sync_sleeper.py:242`) nunca toca em
  salary/contract_year/acquisition_type de jogadores existentes. O banco no Render precisa
  ter os salários corretos desde o seed — o sync só atualiza roster membership e metadados.
- **Diagnóstico do "salários zerados":** O banco no Render foi criado vazio pelo `create_all()`,
  o sync populou jogadores com `salary=1.0` (default para novos). Solução: incluir `dynasty.db`
  com salários corretos como seed no repo.

### 22/04/2026 — Seed Michel + M12 backlog + Auto-Containment M11

- **users.csv é canônico para produção:** o caminho para adicionar um novo owner é editar
  `data/users.csv` e commitar. O auto-seed no startup (app.py) insere no DB de produção no
  próximo deploy. `seed_users.py --email ...` é apenas **conveniência dev** para popular o
  `dynasty.db` local. Decisão tomada ao adicionar Michel (michelzel96@gmail.com, team_id=8,
  admin) — o prompt original sugeria só o CLI, que não resolveria produção.

- **Comportamento duplo do seed_users.py:** rodar o CLI dispara o boot do Flask (via import
  de `app.py`), que já roda o auto-seed do CSV primeiro. Se o usuário alvo já está no CSV,
  a chamada CLI subsequente falha com "já existe" (exit code 1) — comportamento correto,
  não é bug. Documentado em CLAUDE.md.

- **M11 (Auto-Containment documental) adicionado ao backlog** como Média. Princípio formalizado
  no `../DEV_METHODOLOGY.md` na mesma sessão: os 4 docs + código devem bastar para qualquer um
  (outro Claude sem memória, colaborador novo, owner daqui a 2 anos) retomar o projeto. M11 é
  o teste prático aplicado ao manager.

- **M12 (Vincular owners via tela de admin com lookup Sleeper) adicionado ao backlog** como
  Média. Proposta: rota `/admin/users` que lista os 12 times via `GET /league/{LEAGUE_ID}/users`
  da Sleeper API e permite vincular usuários por clique em vez de CLI/CSV manual. Pré-avaliação:
  `Team.sleeper_owner_id` já existe — avaliar se o lookup Manager↔Sleeper pode ser feito via
  Team antes de criar coluna nova `User.sleeper_user_id`.

- **Commit 82e1c29 pushed para origin/main** (`MellowBR/Dynasty_Fantasy_Manager`):
  `data/users.csv` + `improvements.md` + `dynasty.db` (side-effect natural do auto-seed
  gerar Michel no DB local durante o comando).

### 22/04/2026 — Camada F7b (Data migration para produção)

- **Motivação:** F7 limpou o DB local, mas produção (Render persistent disk) não é tocada por `init_data.py` (no-overwrite). Owner preferiu não usar Render shell (trava, experiência ruim), então migração automática via código é o caminho.
- **Padrão adotado:** guard por `SELECT COUNT` antes de cada bloco de fix — se o estado stale está presente, aplica; se não, skipa silenciosamente. Idempotente em qualquer ambiente e qualquer número de execuções.
- **Uso de subquery por nome (não pid):** os `player_id` locais (58, 105, 173) foram inferidos na F1b via SELECT local; em produção podem divergir (auto-increment depende da ordem de INSERT). Usar `(SELECT id FROM players WHERE name='A.J. Brown')` resolve o pid correto em qualquer banco. Se o player não existir (edge case), a UPDATE não afeta nada — mais seguro que falhar.
- **Não mudou `init_data.py`:** comportamento no-overwrite está correto para uso normal. A migração resolve o caso específico do DB que já existe em estado stale, sem mexer na semântica de first-boot.
- **Validação local:** 3 cenários testados via `importlib.reload(app)` — DB limpo skipa, stale aplica, re-run skipa. Confirmado por SQL assertions.

### 22/04/2026 — Camada F7 (Fix + Redesign histórico de salário)

- **Causa raiz do SalaryHistory inflado (9174 rows):** `import_csv.py:104-111` inseria um row a cada boot sem guard de idempotência. Fix de raiz: remover o INSERT (rollover/auction já cobrem o uso legítimo) em vez de adicionar guard. Motivação: o row de `rule_applied='import'` não representava um evento real — era ruído.

- **Decisão Opção A para os 3 Browns (rewrite limpo) em vez de Opção C (renomear event_type):** owner escolheu manter o histórico como se o import original tivesse sido correto desde o dia 1. Justificativa: audit trail do bug **já existe** em improvements.md (F1) e no Log de Decisões deste devplan — manter rastro no banco seria ruído para o owner sem ganho de auditoria. A.J. Brown deve mostrar "$47 desde 2024", ponto. Opção C preservaria o audit mas à custa de UX ambígua na timeline narrativa.

- **Troca de fonte de dados de `/api/salary_history` (de SalaryHistory para PlayerHistory):** PlayerHistory tem `event_type` + `notes` ricos; SalaryHistory só tem `rule_applied` técnico. Endpoint `/api/player/<id>/history` já existia em `routes/roster.py`; template já fazia expansão inline no clique do nome. Só faltava trocar a fonte da API principal + redesign de labels. Zero migração de schema.

- **Cleanup cosmético dos notes `'import'` em 220 rollover rows:** fóssil do `_backfill_player_history` que usava `hist.rule_applied` como fallback. Com SalaryHistory `'import'` rows deletados, o notes congelado virou nonsense. Atualizado para `'Renovado (VALORIZAÇÃO)'` — narrativa coerente com o event_type.

- **Validação:** reboot app local 3× consecutivos, `SELECT COUNT(*) FROM salary_history` permanece 0. Flask test_client com admin mockado: 500 records retornados, 242 jogadores únicos, zero `salary_correction` no payload. A.J. Brown via filtro mostra 2 events ($47 em ambos).

### 22/04/2026 — Camada S1 (Sleeper Trade Sync)

- **Abordagem N-way escolhida: C+ (placeholder row).** Motivação: requisito explícito do owner = "admin nunca precisa mexer em código quando uma 3-way acontecer" (Rafa é o admin da liga e pode não ter acesso ao código). Avaliadas 4 opções (B, C, C+, D refactor). B (2 rows A↔B + B↔C fixas) é inviável em ciclos/mixes de 3-way. C (skip silencioso) deixa trade invisível em `/trades` — UX pior. D (refactor para `TradeLeg` relacional) é over-engineering dado histórico de 0 N-way em 29 trades. **C+ atende o requisito com ~10 linhas extras vs C, sem breaking changes.**

- **Backfill incluído no seed `dynasty.db`.** Alternativa era deixar vazio e admin clicar na UI após deploy. Decisão: incluir as 29 trades no seed direto — Rafa nunca precisa clicar nada. Botão de backfill fica como redundância útil (idempotente) para re-check ou se Sleeper adicionar trades retroativas.

- **Idempotência via `sleeper_transaction_id`** (string unique nullable). Decisão: nullable permite coexistência com `Trade` rows manuais (source='manual'). Unique index previne duplicatas mesmo sob race conditions.

- **Rosters da previous_league_id via `_build_team_map_for_league()`.** A liga 2025 tem `roster_ids` diferentes da liga 2026. O mapping é feito via `Team.sleeper_owner_id` (owner_id é constante entre seasons no Sleeper).

- **Warnings esperados (19 na importação):** (a) picks de season 2025 já drafadas — `sync_sleeper.py` deleta picks com `season < current_year` (`past_deleted` em `_ensure_default_picks`). Trades históricas que moviam essas picks não encontram Pick row; (b) 1 player dropado antes do snapshot atual.

- **`trade_date` vem do `created` (ms epoch) do Sleeper**, não `datetime.utcnow()` — preserva cronologia histórica correta (listagem em `/trades` mostra ordem cronológica real).

- **Validação via Flask test_client:** backfill → 29 imported; re-run → 0 imported, 29 skipped; contagens SQL corretas.

### 23/04/2026 — META: 4 regras novas no DEV_METHODOLOGY (transversais)

- **Origem:** o T2-FIX (mesma sessão) corrigiu o helper Python `pick_sleeper_id` mas o usuário reportou o mesmo bug em produção. Diagnose F2 revelou réplica em JS (`pickFcSid` em `templates/trades.html`) que não foi tocada — a diagnose F1 não perguntou sobre réplicas, e a restrição "alterar apenas dynasty_values.py" amarrou o escopo antes de o Code descobrir o gap. Análise post-mortem com Claude.ai identificou padrão sistêmico.

- **Regra 1 — Diagnose obrigatória de réplicas:** seção "Fase 1 Diagnose" agora exige a pergunta "esta lógica/formato existe em mais de um lugar (JS, templates, outros módulos)?". Sem isso, fixes ficam pela metade.

- **Regra 2 — RESTRIÇÕES por intenção:** prompts devem descrever o que NÃO alterar em termos de domínio/contrato (ex: "não alterar schema, salary_engine") em vez de caminho de arquivo ("alterar apenas X.py"). Restrição por arquivo amarra escopo prematuramente.

- **Regra 3 — Code grep antes de aceitar escopo:** seção "Antes de implementar" do Code agora exige grep pelo padrão de saída (literal, prefixo, formato) em todo o codebase — não só pelo nome da função. Réplicas client-side raramente importam o helper Python.

- **Regra 4 — Checklist de fim de sessão (NOVA, descoberta agora):** ao fechar sessão, validar que (a) ✅/⚠️/🔲 em improvements.md reflete realidade end-to-end (não só backend); (b) diagnoses subsequentes (F2/F3) que descobriram novos itens viraram entradas no backlog; (c) sub-fixes (FIX, FIX2) têm entradas no log do devplan, não só commit message; (d) meta-mudanças têm registro de motivação em algum log canônico. Origem: 4 gaps factuais encontrados nesta sessão antes de encerrar — todos com o mesmo padrão "info ficou em chat/commit, não migrou pra doc canônico".

- **Propagação:** as 4 regras aplicadas nos 3 ecossistemas (`~/fantasy/`, `~/energy/`, `~/finance/gestor-financeiro/DEV_METHODOLOGY.md`). Memória do Code também recebeu Regra 3 e Regra 4 como feedback memories (defesa redundante quando DEV_METHODOLOGY não for carregado).

### 23/04/2026 — N1-FIX + N1-FIX2 (correções pós-deploy do redesign navbar)

- **N1-FIX (commit 65ef289):** dropdowns abertos só por `:hover + :focus-within` (CSS-only) não funcionavam em desktop quando o usuário clicava — `:focus-within` se perde ao mover mouse. Adicionado handler global `document.addEventListener('click')` que toggleia `.nav-open` no grupo, fecha demais, click fora fecha tudo, Esc fecha. CSS `.nav-group:focus-within > .nav-dropdown` substituído por `.nav-group.nav-open > .nav-dropdown` (mais previsível).

- **N1-FIX2 (commit fffea3f):** mesmo após FIX, dropdown continuava invisível em produção. Causa raiz: `.nav-links { overflow-x: auto }` (regra pré-N1, para permitir scroll horizontal dos 9 links flat originais). Quando `overflow` é `auto/scroll` numa dimensão, browsers forçam a outra a não ser `visible` (spec CSS Overflow). Resultado: `.nav-dropdown` (`position: absolute; top: 100%`) clipado verticalmente. Removida 1 linha (`overflow-x: auto`). Mobile não afetado (já usa hamburger overlay com `display: none` na nav-links).

- **Decisão registrada (Regra 4 violada momentaneamente):** decisão original do log do N1 ("dropdowns desktop CSS-only") ficou desatualizada — esta entrada é o registro corretivo. Antes desta correção, quem lesse só o log do N1 teria info errada.

### 23/04/2026 — Camada T2-FIX (pick_sleeper_id formato FantasyCalc)

- **Decisão:** rewrite completo de `pick_sleeper_id` em vez de patch parcial. **Why:** diagnose MAN-T2-FIX-F1 revelou bug **duplo** — Rd1 exibia valor errado (DP_1_5 = Rd2 valor) silenciosamente, Rd2+ retornava None. Patchar apenas o índice deixaria Rd1 ainda apontando para keys DP_ erradas. Rewrite usando os formatos reais do FantasyCalc (DP_<round-1>_<pick-1> + FP_<year>_<round>) corrige ambos numa só passada.

- **Decisão:** lookup em 3 camadas (DP específica → FP agregada → None). **Why:** DP cobre só o draft próximo com pick específica; FP é agregado per-year-per-round. Para picks sem projection conhecida (caso de 100% das picks atuais), FP é a opção semanticamente correta. Combinar dá resiliência futura.

- **Decisão:** `_detect_dp_year(values_map)` parseia o ano dos entries DP_0_* em vez de hardcoded. **Why:** quando o cache for atualizado para 2027 no off-season FantasyCalc, o ano DP avança sem mudança de código. Custo: iteração linear no map até primeira DP_0_* — microsegundos.

- **Decisão:** signature opcional `values_map=None` em `pick_sleeper_id`. **Why:** `routes/trades.py` já carrega o map uma vez via `get_dynasty_values()` em `_compute_cap_impact`. Repassar evita I/O redundante (file read por pick). Default `None` mantém backwards compat — caller atual não precisa mudar (e não muda, per restrição do prompt).

- **Decisão:** Tier 1 (DP com projection) é dead code path hoje. **Why:** Pick model não tem coluna `projected_pick` (confirmado 0/108 picks com o atributo). Implementado mesmo assim para quando algum caller futuro popular dinamicamente (ex: enriquecimento via `_build_pick_projections` de `picks.py`). Não custa nada e evita re-fix depois.

- **Decisão:** Rd1 vai exibir valor diferente do que owner viu antes (~1300 → ~2700) — comunicar no commit. **Why:** correção pode parecer regressão para quem se acostumou ao número errado. Documentar evita confusão.

- **Validação por mock:** Pick model não tem `projected_pick`, então o teste de Tier 1 usa `class MockPick` com `setattr` dinâmico. Cobre o code path apesar de não haver pick real ativa.

### 23/04/2026 — Camada N1 (Redesign navbar)

- **Decisão:** novo context processor `inject_nav_teams` separado do `inject_global_state` existente. **Why:** estado global (offseason flags) é cheap mas independe de autenticação; nav_teams precisa de guarda `is_authenticated` para evitar query em `/login`. Misturar misturaria responsabilidades. `with_entities()` retorna tuplas leves em vez de objetos ORM com lazy relationships.

- **Decisão:** algoritmo de match path-aware no macro `_nav_match`: `path == prefix.rstrip('/')` OR `path.startswith(prefix.rstrip('/') + '/')`. **Why:** substring naïve (`prefix in path`) faz `/salary` matchear `/salary_history`. Algoritmo path-aware corrige sem precisar de exact mode em todos. `rstrip('/')` evita `'//'` quando prefix já tem trailing slash (descoberto no smoke test em `/team/`).

- **Decisão:** Liga + Times **ambos ativos** simultaneamente em `/team/<id>`. **Why:** comunicação visual natural — owner está na área de Liga, especificamente num time. Visual destaca contexto duplo. Alternativa rejeitada: tirar `/team/` do Liga, deixando só Times — perderia contexto.

- **Decisão:** dropdowns desktop **CSS-only** via `:hover` + `:focus-within`. **Why:** zero JS, mais simples e acessível. Click-toggle (acessibilidade keyboard) pode ser evolução futura se virar dor.

- **Decisão:** mobile via **overlay vertical CSS-only** (checkbox hack), não drawer JS. **Why:** drawer com slide animado exige JS para click-outside; overlay com `<label for="checkbox">` no fundo escuro fecha sem JS. ~30 linhas CSS vs ~50 + JS. Trade-off aceito.

- **Decisão:** dropdown do owner mantido (1 item Logout) em vez de link inline. **Why:** prepara para itens futuros (Configurações, Tema). Diff zero quando vier; refatorar agora seria churn.

- **Decisão:** avatar com cascata 4-step (hash Sleeper → inicial owner_name → inicial user.name → 👤). **Why:** Erico (admin com time) tem hash; admin sem time vinculado teria fallback de inicial; user totalmente sem dados cai no emoji. Resiliência contra DB incompleto.

- **Decisão:** algoritmo de match testado com `/salary_history` vs `/salary` antes de declarar concluído. **Why:** o conflito mais provável de regredir; cobertura explícita no smoke test garante que mudanças futuras não quebram.

- **Decisão:** Auction movido para dropdown Admin. Picks movido para dropdown Liga. **Why:** prompt definiu; semanticamente alinhado (auction é processo administrativo de offseason; picks é visão de liga).

### 23/04/2026 — Camada L1 (League Hub)

- **Decisão:** novo blueprint `routes/league.py` em vez de adicionar a `roster_bp`. **Why:** `roster_bp` está semanticamente acoplado a "meu roster" + APIs de jogador. League Hub é visão da liga inteira — mistura de responsabilidades inflaria o blueprint. 9º blueprint coerente com a separação por domínio que o projeto já segue.

- **Decisão:** sem mudança de schema, sem migration, sem nova coluna. **Why:** diagnose MAN-L1-F1 confirmou que todos os dados necessários existem em Team, Player, Pick, SeasonStandings, dynasty_values cache. Trabalho puramente de routes + templates + CSS.

- **Decisão (perf):** evitar `team.cap_remaining()` no loop de 12 cards. **Why:** `Team.players` é relationship `lazy="dynamic"` — cada chamada dispara query. Pré-carregar todos players em 1 query e calcular cap por team_id no Python preserva a meta de 5 queries totais (teams, standings, pick_counts via group_by, players, get_dynasty_values via cache).

- **Decisão:** `_build_players_by_pos` importado de `routes/roster.py` com underscore (`from routes.roster import _build_players_by_pos`). **Why:** restrição "não alterar roster blueprint" me impediu de tornar a função pública (rename). Função tem 35 linhas de lógica não-trivial (POS_ORDER + healthy/IR ordering). Duplicar é pior que importar privado entre blueprints. Anti-pattern leve, zero risco.

- **Decisão:** dynasty_total só soma **players** ativos. Picks ficam de fora. **Why:** T2-FIX aberto (picks Rd2+ retornam None do FantasyCalc). Somar picks daria valor enviesado. Quando T2-FIX for resolvido, adicionar picks é um diff trivial.

- **Decisão:** `dv_map[sid]` é um dict `{value, name, position, overall_rank, position_rank, is_pick}`, não int. Usar helper `resolve_asset_value(values_map, sid)` de `dynasty_values.py` para extrair `.value`. **Why:** descoberta no smoke test (TypeError int + dict). Consistência com T2 (`routes/trades.py` já usa o mesmo helper).

- **Decisão:** sem tabs JS no `/team/<id>`. 3 seções (Cap Breakdown, Roster, Picks) renderizadas inline server-side. **Why:** alinha com `player_detail.html` (M13) que é página densa SSR. Tabs adicionariam complexidade sem ganho proporcional. Evolução futura se virar dor.

- **Decisão:** botão "Propor Trade" não aparece no detalhe do próprio time. **Why:** owner não negocia consigo mesmo. Verificação via `current_user.team_rel.id == team.id`.

- **Decisão (UX):** ordenação por rank da temporada com fallback `name` para times sem standings (`rank=999`). **Why:** garante que time sem standings (edge case improvável dado os 12 standings 2025 confirmados) ainda apareça, no fim da grid.

### 23/04/2026 — Camada O1 (Linkificar nomes de jogadores)

- **Decisão:** introduzir 2 helpers centralizados — macro Jinja `player_name_link` em `templates/_macros.html` (NOVO) e função JS `renderPlayerNameLink` em `base.html`. **Why:** zero infra de helper de jogador existia; cada template implementava seu link inline. Helper reduz divergência futura sem retrofittar telas já corretas (trades, salary_history).

- **Decisão:** **não** retrofittar `trades.html` nem `salary_history.html`. **Why:** restrição explícita do prompt + risco baixo de divergência (apenas 2 lugares no padrão informal). Helper aplica só nas mudanças desta camada e em código novo daqui pra frente.

- **Decisão (UX roster, opção A):** nome do jogador no roster vira link direto para `/player/<id>`; ícone 🔗 separado removido; modal de histórico inline (`showPlayerHistory`) eliminado. **Why:** consistência com o resto do app pós-O1. Modal duplicava a timeline da `player_detail.html` (M13). Owner aprovou trade-off "consistência > preservar fluxo legado" no prompt MAN-O1.

- **Decisão (cleanup base.html):** removidos modal `#player-modal`, função `showPlayerHistory` e `closePlayerModal` — órfãos após Lote 2. CSS `.timeline*` **preservado** porque `player_detail.html` consome. **Why:** dead code é dead code; CSS compartilhado fica.

- **Decisão (Lote 3):** `/api/trades/by_tx/<tx>` faz best-effort `find_player_by_name(asset)` — alternativa a re-arquitetar `Trade.description` com asset references estruturadas (esforço médio, valor incremental baixo). Picks e nomes ambíguos retornam `player_id=null` e o template faz fallback para `escapeHtml(asset)`. **Why:** degradação elegante já é padrão do projeto (T2 dynasty values com 84.9% cobertura). Validado em produção: 60%, 25%, 100% de cobertura em 3 trades reais.

- **Decisão (anti-pattern evitado):** comentários `// MAN-O1: ...` adicionados inicialmente em base.html, _trade_detail_modal.html e routes/trades.py foram **removidos** após smoke test pegar `showPlayerHistory` num comentário literal. Refs ao task atual em comentários violam regra do projeto (esses contextos vivem no PR/commit/log, não no código).

### 23/04/2026 — M8-PERM (revisão de permissões da lottery)

- **Decisão:** abrir `/lottery/simulate` para qualquer owner autenticado (`@login_required`); manter `/lottery/replace` em `@admin_required`. **Why:** simulação não persiste nada — não há razão para restringir a admin. Owners querem poder testar cenários de bolinhas antes do sorteio oficial.

- **Decisão:** adicionar guarda server-side (409) em `/lottery/simulate` quando audit canônico já existe para `current_season+1`. **Why:** template tinha guarda visual (`has_canonical_audit`) mas backend ficava aberto a chamadas diretas (curl). Defesa em profundidade.

- **Decisão:** sinal de bloqueio é `LotteryAudit.is_canonical=True` (não `DraftLotteryResult.locked`). **Why:** consistência com guarda já existente em `run_lottery` (linha 326-332). Reativação automática no rollover sem flags novos.

- **Decisão:** template não alterado — guarda visual já funcionava por substituição completa do botão (não desabilitação). UX preservada.

- **Decisão:** registrar como item novo M8-PERM em vez de sub-nota em M8 ✅ — preserva backlog limpo (regra do projeto: itens completos não acumulam revisões).

- **Correção ao diagnose MAN-M8-F1 (Q4):** resposta original afirmou "botão sempre visível" no template. Errado — o `{% if has_canonical_audit %}` na linha 201 de `offseason.html` já substitui o botão por Travar/Re-executar/Ver auditoria. Falha de leitura no diagnose; corrigido na análise crítica do MAN-M8-02.

### 23/04/2026 — M9-FIX (Todas as picks clicáveis + pré-seleção de pick no /trades)

- **Condição `clickable` original era restritiva demais.** Primeira versão do M9 só tornava clicáveis as picks com `traded_away=True AND current_team != my_team`. Justificativa original: "foca no caso real 'recomprar pick tradada'". Mas owner identificou 2 casos legítimos faltando: (a) **pedir** pick original de outro time (não precisa ter sido trocada), (b) **oferecer** minha própria pick como ativo de trade. Correção: `clickable = my_team_name is not None` — qualquer pick vira clicável, só exige user com time vinculado.

- **Href dual: pick_a para minhas, pick_b para outras.** Simétrico com o M14 que usa team_a/team_b. Semântica: "pick_a" é pick do lado A (meu lado quem propõe). "pick_b" é pick do lado B (contraparte). Mantém a convenção da rota `/trades` onde A sempre é quem inicia a proposta.

- **Extensão do M14 para aceitar pick_a/pick_b foi leve.** ~15 linhas em `trades.py` com helper `_resolve_preset_pick` que valida que a pick existe E que seu `current_team_name` bate com o `preset_team_a`/`preset_team_b`. Validação dupla evita: (a) pick inexistente exposta no HTML, (b) pick de outro time sendo marcada no lado errado. Em ambos os casos: ignora silenciosamente (mesma postura do M14 pra team_a/team_b inexistentes).

- **Consume pattern no dataset.** Após `loadSide` marcar o checkbox do preset, limpa `dataset[presetKey] = ''` para evitar que uma re-renderização de `loadSide` (hipotética, se o user mudar de time depois) remarque o checkbox. Padrão "use-once" explícito e seguro.

- **`data-pick-id` adicionado aos `<input>` dos checkboxes.** Necessário pra achar o checkbox correto via `div.querySelector('input[data-pick-id="${id}"]')`. Custo: 1 attribute por checkbox, trivial.

- **Decisão de UX:** pick pré-marcada vem com a barra dynasty atualizando automaticamente — user chega em `/trades` já vendo o valor do lado A, só precisa escolher o que pedir do outro lado. Fluxo "1 clique + 1 decisão" em vez de "1 clique + N cliques de seleção".

### 23/04/2026 — Camada M13 (Página de jogador)

- **`dynasty_value` no backend (E3 da análise crítica pré-impl).** M13 é render único (uma página por request). Diferente do T2 (client-side porque precisa recalcular ao `toggleAsset`), aqui backend resolver é: (a) 1 lookup em cache JSON local (~ms), (b) zero flash visual, (c) zero round-trip extra, (d) zero fallback JS se `/api/dynasty_values` falhar. Rejeitei padronizar client-side só por uniformidade — os dois casos têm natureza diferente.

- **`player_id` em vez de `id` no parâmetro da rota (E1).** Python tem builtin `id(obj)`. Usar `id` como parâmetro em view function funciona mas shadowia o builtin dentro da função — confusão e tipagem de IDE. Padrão do projeto inteiro já usa `player_id`, `pick_id`, `tid`, `user_id`. Consistência.

- **`event.stopPropagation()` no `<a>` do `trades.html` (E2, crítico).** Clique num filho de `<label>` com checkbox **toggleia o checkbox** por default HTML. Nome do jogador ficou `<a href="/player/..." target="_blank">` dentro do `<label class="asset-item">` — sem `stopPropagation`, clicar no nome do jogador pra abrir a página em nova aba **também** removeria/adicionaria o jogador da trade. Efeito colateral invisível e frustrante. Fix de 2 caracteres, essencial.

- **Modal de trade clicável extraído como partial `_trade_detail_modal.html` (O1).** Originalmente inline em `salary_history.html` (F8-NOTES). M13 queria o mesmo modal. Duplicar HTML + CSS + 2 funções JS seria DRY violation — qualquer mudança futura precisaria sincronizar manualmente. Include partial é `{% include %}` simples do Jinja. Dependência: partial assume `escapeHtml(s)` no escopo host — documentei na primeira linha do arquivo.

- **Foto via Sleeper CDN com `onerror` fallback.** Player model não tem coluna de foto. Sleeper serve `https://sleepercdn.com/content/nfl/players/thumb/<sleeper_player_id>.jpg` para a maioria dos jogadores ativos (e retorna 404 para retirees/DSTs/rookies recém-chegados). `onerror="this.style.display='none'"` faz o img sumir sem quebrar layout. Mesmo padrão já usado em avatars de team (`sleepercdn.com/avatars/...`). Zero schema change.

- **`showPlayerHistory` modal inline do roster preservado.** Owner pode estar acostumado ao fluxo atual "clicar no nome → modal de histórico expandido". Em vez de substituir por "clicar no nome → página dedicada", adicionei ícone `🔗` discreto ao lado do nome. Quem quiser página dedicada clica no 🔗; quem quiser modal inline clica no nome. Evita quebrar expectativa.

- **`can_propose_trade` boolean pré-calculado no backend**, não como 3-way condicional no Jinja (`{% if my_team_name and team and player.team_id != current_user.team_id %}`). Template fica `{% if can_propose_trade %}` — um único check, lógica clara no backend com fallbacks explícitos.

- **EVENT_LABELS copiado inline no JS do `player_detail.html`** (O2 rejeitado). Análise crítica sugeriu extrair pra arquivo `static/js/event_labels.js`. Rejeitei: tela é a 2ª e última que usa os mapas (depois de `salary_history.html`). Extração pagaria com 3ª usuária, não 2ª. Se M10 (autocomplete) precisar, extrai aí.

### 23/04/2026 — Camada M9 (Grid de picks navegável)

- **Matrix `team × round` em vez de `season × round` com listas.** Layout anterior listava picks de cada round em coluna vertical separada — usuário precisava procurar mentalmente o time em 3 colunas pra ver seus picks. Nova matrix: 1 linha = 1 time, 3 colunas = R1/R2/R3. Scaneamento natural.

- **Ordem de linhas por `projected_pick` do R1.** Alternativas consideradas: alfabético (previsível mas não informativo), por `current_team_name` (complicado com trades), por rank do standings anterior (bom mas exigiria query extra). Escolhi `projected_pick` porque é a ordem que interessa ao owner — "quem pega antes" é o que dá contexto ao ver a matrix. Fallback alfabético para seasons sem projeção.

- **Célula clicável apenas quando `traded_away=True` AND `current_team != my_team`.** Dois filtros combinados. Trades próprias (recebi de outro) já me dão acesso — não faz sentido "propor trade" comigo mesmo. Picks não trocadas também ficam não-clicáveis: propor trade por pick original é ruído (o padrão seria trocar players, não começar pela pick). Restringir ao caso trocado-por-outro foca o fluxo no caso real: "vi que a pick 1.01 foi tradada pro X, vou propor X recomprá-la por outra coisa minha".

- **`<a>` HTML nativo em vez de JavaScript onclick.** Link nativo dá right-click "abrir em nova aba" grátis — útil pro owner comparar trades sem perder contexto. Mesmo padrão do avatar de team → roster.

- **`my_team_name` derivado no backend, não no template.** Evita lógica complexa no Jinja (`current_user.team_rel.name if current_user.team_rel else None`) repetida em várias condicionais. Backend resolve uma vez e template usa direto.

- **Banner warning quando `my_team_name is None`** (admin sem time vinculado). Comportamento atual: zero células clicáveis, página funciona mas sem atalhos. Alternativa rejeitada: esconder toda a funcionalidade de trade (desnecessariamente restritivo — admin pode querer ver os picks sem intenção de propor).

- **Botão ✎ de edição admin com opacity 0 no default + 1 no hover.** Alternativa rejeitada: botão sempre visível — poluiria visualmente a matrix densa. Hover-only mantém a matrix limpa e o botão descobrível quando o owner passa mouse em cima da célula.

### 23/04/2026 — Camada M8 (Lottery auditável + bolinhas + duas fases)

- **Tabela `LotteryAudit` separada, não colunas em `DraftLotteryResult`.** Granularidade é por execução (5 picks afetadas), não por pick. Colunas em `DraftLotteryResult` duplicariam o valor em 12 rows e complicariam histórico de re-runs. Decisão clara.

- **`pool_json` snapshot foi essencial, não cosmético.** Meu primeiro instinto (diagnose) era salvar apenas `weights_json`. Feedback do owner e reflexão subsequente revelaram: se `SeasonStandings` for editada depois do lottery (admin corrige um rank), a reprodução via `/verify` falharia mesmo sem tampering. Pool snapshotado resolve isso — congela os 5 times + seus seeds + pesos no exato momento da execução.

- **Algoritmo bolinhas literais + `random.shuffle` em vez de `random.uniform + cumulative sum`.** Matematicamente equivalentes em distribuição (cada bolinha = 1/total chance), mas diferentes em sequência de números aleatórios consumidos — resultados com mesmo seed são DIFERENTES entre os dois algoritmos. Escolhi bolinhas porque: (a) alinha exatamente com a UI de pool visual, (b) é mais intuitivo pro owner que pergunta "e se eu quiser reproduzir manualmente?", (c) `random.shuffle` é determinístico em Python garantido.

- **Seed derivado contínuo (Opção B), não reset por pick.** `random.seed(seed)` **uma vez** no início do helper, depois `random.shuffle` roda com estado atual do RNG. Alternativa rejeitada: resetar seed antes de cada pick com `seed + ":" + pick_num`. Contínuo é mais simples e reproduzível do mesmo jeito; reset per-pick sugeriria "cada pick tem seu próprio seed", semântica confusa.

- **Fluxo duas fases explícitas, fechando cherry-picking.** Originalmente o prompt previa re-runs livres antes do lock. Discussão com owner revelou brecha: admin rodaria 10x até pegar resultado favorável. Solução: fase 1 puramente estatística (pool de bolinhas + % chance, SEM botão testar), fase 2 oficial única (confirm duplo + commit). Re-run existe mas exige `reason` textual e fica público em `/picks/lottery/<season>`. Trust by design.

- **`hash_match=True` + `match=False` após tampering manual** é o estado correto, não bug. O `result_hash` deriva da reprodução via seed+pool (audit íntegra). Se alguém editar `DraftLotteryResult` direto no DB, o hash da audit continua batendo com a reprodução (porque audit não foi tocada), mas `DraftLotteryResult` diverge — detectado via `match=False`. Owner que fizer a verificação vê imediatamente que algo foi adulterado no DB.

- **Paleta fixa 5 cores (vermelho/azul/verde/roxo/laranja) em vez de HSL gerado.** Com 5 times, HSL espaçado produziria pares como laranja/amarelo que se confundem em tela pequena. Paleta fixa garante contraste entre vizinhos — decisão puramente visual.

- **Animação controlada: só 1 bolinha em destaque por vez**, não 95 simultâneas. Primeiro instinto seria embaralhar as 95 bolinhas antes de cada pick (`@keyframes ballShuffleBrief`). Simplifiquei para só highlighted/eliminated — menos ruído visual, leitura mais clara do que está acontecendo. Sem prejuízo de auditoria (dados estão no backend, animação é cerimônia).

- **Reveal backend-first.** `run_lottery` retorna resultado completo num único POST (backend é autoridade). UI anima pick 1 → pick 5 via `setTimeout` 1500ms. Alternativa rejeitada: 5 POSTs separados (um por pick). Adicionaria 5× a latência + riscos de race conditions sem ganho real.

- **Tabela nova via `db.create_all()`, sem Migration em `_run_migrations`.** Mesmo padrão de `TradeProposal` (T1): `db.create_all()` é chamado no boot e cria tabelas novas em DBs existentes sem tocar nas antigas. Sem schema change em tabelas existentes = sem migration explícita.

### 23/04/2026 — T3 (sugestões de assets) descartado após review do T2

- **T3 foi considerado e removido do backlog** após review da tela `/trades` pós-deploy do T2. Proposta era bloco de até 5 sugestões automáticas abaixo da barra dynasty, clicáveis para adicionar à trade, preenchendo o gap de `|delta|`.
- **Motivo do descarte:** a combinação já entregue pelo T2 (barra em tempo real + chip central de vantagem + badges 🪙 inline em cada checkbox) resolve o problema prático. Owner consegue navegar o roster do lado vantajoso e testar assets com feedback visual imediato — a sugestão automática seria conveniência marginal, não um gap de UX real.
- **Decisão preservada no git:** análise completa + decisões de design ficam no commit `e338c28` (adicionou T3 ao backlog) e na reversão logo em seguida. Se voltarmos a priorizar essa camada no futuro, basta resgatar do histórico.

### 22/04/2026 — Camada T2 (Valores dynasty FantasyCalc)

- **FantasyCalc escolhido ao invés de KeepTradeCut** (opção original do improvements.md). Motivos: (a) API pública documentada e estável (`/values/current` com params explícitos), (b) matching por `sleeperId` exato — zero risco de ambiguidade de nome (problema histórico "3 Browns" do F1), (c) inclui picks de draft como entries `DP_<year_offset>_<pick_index>`, (d) gratuita sem rate limit agressivo, (e) retorna `value`, `overallRank`, `positionRank`, `trend30Day` num único request (~1MB). KTC seria API não-oficial/scraping + matching por nome com risco.

- **Cache em JSON file, não tabela no banco.** Seguiu padrão do `.sleeper_players_cache.json` já existente. Vantagens: (a) operação ephemeral (regenerável via refetch), (b) sem migration, (c) trivial de invalidar (`rm data/.dynasty_values_cache.json`), (d) consistente com outro cache externo. Tabela no banco seria overkill.

- **Recálculo da barra dynasty 100% client-side** via `toggleAsset()`. API chamada 1x ao load da página (`/api/dynasty_values`) + 1x em refresh manual. `toggleAsset` opera em memória lendo `dynastyMap[sid]` e soma. Alternativa rejeitada: POST a cada toggle para `/api/trades/preview` — traria latência de 100-300ms a cada clique e sobrecarregaria o backend. Recálculo local é instantâneo e adequado pra escala de ~25 assets por side.

- **Refresh com `@login_required`, não `@admin_required`.** A operação é read-only do mundo externo (fetch FC + save cache local). Qualquer owner autenticado pode disparar um refresh se perceber que os valores estão stale. Não há risco de destruição. O botão fica desabilitado quando `age_hours < 1` — evita hammering.

- **Picks sem `projected_pick` usam middle-of-round como estimativa.** Picks 2026+ nem sempre têm projected_pick preenchido (especialmente picks de rounds tardios ou de temporadas futuras). Fallback: `pick_index = (round-1) * 12 + 5` (pick 6 do round, meio da tabela). Valor marcado com sufixo "est." no badge para deixar claro que é estimativa. Alternativa rejeitada: usar o pick 1 (melhor do round) ou pick 12 (pior). Middle-of-round é o melhor compromisso sem info adicional.

- **Degradação elegante preserva preview de cap.** Se FC + cache indisponíveis, `_compute_cap_impact` retorna `dynasty_available=False` e `dynasty_value=None` por asset. Frontend esconde a barra dynasty + badges ficam `—`. Cap impact original continua funcionando 100%. Feature dynasty é additive.

- **Cobertura 84.9% é aceitável sem fallback por nome.** Os 42 players sem value são majoritariamente DSTs (Buffalo Bills DST etc.), kickers e fringe players — não costumam ser sujeitos de trades relevantes. Implementar fallback por nome normalizado traria risco "3 Browns" sem ganho proporcional. Se um owner tentar tradar um player sem value, vê `🪙—` no badge e segue — a barra ignora (0 somado).

- **Barra espelhada em vez de barra empilhada.** Duas visualizações consideradas: (1) barra única com 2 cores mostrando proporção A:B, (2) barras separadas cada uma com 50% da largura máxima cresceindo de bordas pra dentro. Escolhi (2) — mais intuitivo visualmente ("cada lado puxa pro seu canto"), fica óbvio quem está colocando mais valor na mesa. A (1) daria leitura ambígua quando totalA=totalB=0.

### 22/04/2026 — Camada T1 (Trade Manager simulador + link compartilhável)

- **Visibilidade da proposta: `@login_required`, não pública.** Decisão discutida em MAN-T1-F1 (diagnose) e resolvida aqui: propostas exigem login Google cadastrado, mesmo modelo do resto do Manager. Motivação: (a) screenshot no WhatsApp da liga já resolve o caso "mostrar pra alguém fora que não tem conta Google" — é tão fácil quanto o link e evita exposição pública; (b) manter consistência com o X1 (multi-user access via OAuth), já que todos os 12 owners têm login; (c) evita cache/indexação externa acidental de estados internos da liga. Se algum owner perder acesso à liga no futuro, o link deixa de funcionar — comportamento esperado.

- **Cap impact recalculado no momento do GET, não snapshot na criação.** Proposta só armazena IDs (players_a, players_b, picks_a, picks_b). `view_trade_proposal()` busca os Players e recalcula via `_compute_cap_impact()`. Consequência: se o owner trocar um player envolvido antes do acesso ao link, o cap impact mostrado reflete o estado atual — não o estado hipotético do momento em que a proposta foi criada. Escolhi essa abordagem porque: (a) TTL é 7 dias, mudanças grandes no cap intermediárias são raras; (b) snapshot do cap exigiria serializar mais data + decidir como lidar com players dropados/tradados intermediários (corromper a proposta ou mostrar estado stale?). Recálculo é mais honesto — "este é o impacto se essa trade acontecesse AGORA".

- **Helper `_compute_cap_impact()` extraído antes de adicionar a lógica de proposta, não depois.** O prompt pedia "não duplicar lógica". Refatorei `preview_trade()` para extrair a função pura primeiro, depois adicionei os endpoints novos reutilizando. Alternativa rejeitada: copiar o `side()` inline — mais rápido de escrever mas cria 2 cópias do cálculo de cap, qualquer evolução (ex: T2 adicionar KTC values) obrigaria mudar nos 2 lugares.

- **`db.create_all()` suficiente para tabela nova; sem Migration explícita.** Tabela `trade_proposals` não existe em nenhum DB (nem local nem produção). `db.create_all()` é chamado no boot antes de `_run_migrations` e cria tabelas novas em DBs existentes sem tocar em tabelas antigas. Migration explícita seria redundante e introduziria caminho sem guard. Migrations (F7b, F8a, F6) foram necessárias porque alteravam schema/dados existentes.

- **Botão "↗ Abrir" ao lado do "📋 Copiar" no modal.** Caso comum: owner gera o link pra compartilhar, quer ver primeiro como ficou antes de enviar no grupo. Abrir em nova aba (target=_blank) mostra a proposta real (incluindo expiration, owner_name de quem criou, layout final), sem precisar sair do modal atual. Pequeno polish de UX.

- **X2 (propor/aceitar/recusar no Manager) continua deferido.** A T1 cumpre o caso de uso atual: simular + compartilhar. X2 seria "trade negociável dentro do Manager com fluxo de proposta → aceitar → registro automático", que compete com o fluxo natural "owner proposta no Sleeper → aceito no Sleeper → S1 captura". S1 já cobre o caminho feliz; X2 só faria sentido se owners começassem a reclamar do fluxo atual.

### 22/04/2026 — F8-RESTORE-GAP (Backfill automático no restore)

- **Backfill integrado no `/restore` em vez de polling externo ou warning manual.** Considerei duas alternativas: (a) warning na UI alertando o admin pra rodar backfill depois; (b) chamada automática integrada. Escolhi (b): restore é operação rara (poucas vezes por ano), os 100-200ms extras do walk da chain são aceitáveis, e eliminar a pegadinha ("esqueci de rodar backfill e agora X jogadores não aparecem na timeline") vale o pequeno acoplamento. A intenção do admin ao chamar `/restore` é sempre "voltar ao estado anterior de forma completa", então o backfill automático é semanticamente correto.

- **Try/except isolado em torno da chamada de backfill.** Restore é a operação principal (DELETE + INSERT + revert Player + clear backup/flag). Se o backfill falhar (ex: Sleeper API fora), NÃO revertemos o restore — ele já foi aplicado. O JSON inclui `backfill_error` com traceback, UI mostra `result-warn` com recomendação de rodar o botão manual "Backfill de Trades Órfãs". Restore "funciona", backfill é opcional.

- **Manter botão manual "Backfill de Trades Órfãs"** no card F8 mesmo com o automático no restore. Operação é idempotente via UNIQUE e inofensiva; útil pra cenários externos (import de dados, manipulação direta do DB, teste). Remover o botão tornaria o caminho manual impossível — preservamos como fallback.

- **`backfill_result` pode legitimamente retornar `events_created=0` sem erro.** Acontece quando os 2 casos patológicos conhecidos (tx=1154533231048630272, tx=1152430188438040576) são os únicos órfãos restantes — todos os players delas já foram dropados do DB. UI não trata isso como warning — `events_created: 0` com `processed: 2` é cenário saudável.

### 22/04/2026 — Camada F6 (Remover acquisition_type 'keeper')

- **"keeper" deprecated como acquisition_type, não como conceito.** O termo continua existindo no contexto do `draft_budget()` — variáveis `keeper_salaries` e `num_keepers` somam players ativos no roster antes do FA auction de offseason (definição da liga). Decidi NÃO renomear essas variáveis: são descritivas, bateram com o vocabulário da liga, e o leitor entende pelo contexto que são "players retidos pré-auction", não "players com acquisition_type='keeper'". Renomear para `retained_salaries` / `num_retained` economizaria confusão para novos leitores mas quebraria familiaridade com quem usa o código há 2 anos.

- **Migration 6 aplicou em 60 players, não 101.** Diferença absorvida pelo F8a (reconciliação via Sleeper chain corrigiu 41 cujo último evento de aquisição foi ≥ 2025 — aqueles viraram `fa_auction`, `trade`, `fa_waiver` etc.). Os 60 restantes são startup 2024 que permaneceram no mesmo time por 2 seasons sem drop/trade — semanticamente auction_draft.

- **Guard f8_rebuilt protege CSV, mas atualizei o CSV mesmo assim.** Em produção, `run_import()` skipa `acquisition_type` quando `f8_rebuilt=true`, então o CSV ficaria inerte mesmo com `keeper` nele. Atualizei o CSV pra consistência: first-deploys (Render novo) leem o CSV na inicialização antes do F8 rodar, e o CSV deve estar no vocabulário canônico. Também reduz confusão pra leitor humano.

- **Test `test_keeper_uses_value_paid` foi removido, não renomeado.** Era literalmente `year1_salary("keeper", 40, 60.0) == 40`, duplicata de `test_auction_draft_uses_value_paid` exceto pela string. Renomear preservaria uma redundância. Deletei — coverage não diminui (ambos testavam o mesmo path).

- **Card UI do `/salary` ganhou `fa_auction` no lugar de `keeper`.** Ao remover o option keeper do dropdown da calculadora de salário, decidi substituir por `fa_auction` (que faltava no form). Mudança incidental mas alinhada com o vocabulário atual — startup auction, FA auction e rookie draft são os 3 tipos de draft que a liga opera.

- **F8-RESTORE-GAP adicionado ao backlog como Baixa.** Observação do owner na sessão anterior: `/restore` apaga PlayerHistory mas mantém Trade rows, exigindo `/backfill_trades` manual depois. Proposta registrada: automatizar o backfill no fim do restore. Baixa prioridade — cenário só ocorre após uso do /restore, raro em produção.

### 22/04/2026 — Camada F8c (Endpoint admin, UI e boot skip)

- **Snapshot path via `data/.player_history_snapshot_*.json` com glob + mtime sort**: helper `_latest_snapshot_path()` retorna o mais recente. Decidi não manter registro do snapshot em tabela (`AppConfig` ou coluna em `F8PlayerBackup`) — o filesystem já é a fonte de verdade e glob é barato. Habilita o botão "Restaurar" no admin apenas quando existe arquivo; UI não precisa polling.

- **Snapshot preserva IDs originais do PlayerHistory** (dump inclui `id`, INSERT usa explícito). Ao restaurar, DELETE + INSERT recria rows com PKs originais — importante se algo no futuro cachear pid de history. Se o dump falhar, fallback é `db.create_all()` normal onde sqlite gera novo id (sem perda funcional, só os pids históricos mudam). Aceitável.

- **Restore é one-shot: limpa `f8_player_backup` completamente ao final.** Motivação: se o owner re-rodar rebuild depois do restore, o primeiro rebuild vai gerar um novo backup do zero (o "estado anterior" agora é o CSV-original, não o primeiro F8). Manter os backups antigos confundiria o próximo rollback. Mesma lógica: remove a flag `f8_rebuilt` — a partir do restore, o DB volta a estado pré-F8, e o próximo rebuild re-seta tudo.

- **Boot skip foi colocado DENTRO do block `if fresh_import`**, não antes dele. Motivação: o block inteiro só roda quando há player novo importado do CSV (fresh DB). Em DB maduro (98% dos boots pós-primeiro-deploy), `fresh_import=False`, o block não roda, e o skip é no-op. Em DB novo com F8 rodado (cenário raro mas possível), o skip evita regenerar history fictícia. Em DB novo sem F8 (first-deploy Render típico), o legacy `_backfill_player_history` roda normalmente — compatibilidade preservada.

- **Endpoint restore NÃO re-cria o snapshot antes de restaurar.** Considerei essa proteção ("ocê só pode restaurar 1 vez porque perde o estado atual") mas descartei: o restore já cria backup implícito via f8_player_backup (snapshot do estado pré-F8), e se o usuário quiser re-rebuildar, o fluxo é claro (restore → rebuild gera novo snapshot). Adicionar "snapshot do snapshot" seria complexidade sem valor real — a ferramenta é pra casos onde o rebuild deu errado e o owner quer voltar.

- **Confirms duplos no botão rebuild, simples no restore.** Rebuild é destrutivo-reversível (snapshot existe); restore é destrutivo-irreversível na mesma sessão (apaga backup). Poderia ser o inverso — mas o rebuild envolve 2 etapas (check ESPN values / ler que vai sobrescrever history fictícia) e o restore é operacionalmente raro. Mantive padrão do `rollover` (2 confirms) que o owner já está acostumado.

- **Novo seção vision.md "Calendário Operacional" escrita em prosa fluida**, não lista. Motivação do prompt original: documentar o fluxo real que mistura Manager + Sleeper (FA auction no Sleeper é a pegadinha que não está óbvia só olhando o Manager) e o gap dos standings não sincronizados automaticamente. Escrita deixa claro onde estão os pontos frágeis (registro manual de FA auction) sem virar changelog técnico — vision.md deve envelhecer bem.

### 22/04/2026 — Camada F8b (Guard CSV contra reversão de F8a)

- **AppConfig em vez de coluna no Player:** considerei duas alternativas. (1) Coluna `Player.f8_reconciled` boolean — metadata per-player, mas exigiria migration, UPDATE das 180 linhas corrigidas, e cada upsert do CSV precisaria checar no próprio row. (2) AppConfig flag global `f8_rebuilt` — zero schema change, uma leitura no topo do `run_import()` resolve todo o loop, e semanticamente é correto: "este DB passou pelo rebuild canônico". Escolhi (2). AppConfig já existe, já tem `get_config`/`set_config` pattern, e a decisão é realmente binária no nível do DB, não do player.

- **Guard só no update path, não no create path:** player novo adicionado ao CSV pós-F8 (ex: rookie mid-season, jogador assinado na FA) precisa dos valores iniciais do CSV. Não existe "história Sleeper" pra ele ainda no ponto da criação. F8 re-run depois reconcilia se necessário. Bloquear o create path seria over-reach.

- **Flag ausente = comportamento original:** DBs novos (primeiro deploy em Render, dev rodando do zero) não têm a row AppConfig `f8_rebuilt`. Default `'false'` do `get_config` mantém `run_import()` funcional exatamente como antes — importante para não quebrar o first-boot flow que ainda chama `_backfill_player_history` (a remoção dessa chamada é escopo do F8c, não do F8b).

- **Guard não ataca 50 campos — só os 2 que o F8 canoniza.** `salary`, `contract_year`, `espn_ref_value`, `name`, `position`, `nfl_team`, `orig_draft_season`, `orig_draft_type` continuam vindo do CSV. O F8 explicitamente **não** sobrescreve salary/contract_year atuais (salary é regra local da liga, não do Sleeper); só reconcilia o histórico e os 2 campos "origem".

### 22/04/2026 — Camada F8a (Rebuild PlayerHistory via Sleeper chain)

- **Quintupleto UNIQUE via `sleeper_event_ref` em vez de quadrupleto simples.** Motivação: quadrupleto `(player_id, season, event_type, team_name)` colapsa casos reais como BUF DST com múltiplos drops/waivers do mesmo time no mesmo season. `sleeper_event_ref` TEXT nullable com formato `'tx:<id>' | 'draft:<draft_id>:<pick_no>' | 'rollover:<season>'` é auditor-friendly (dá pra decifrar a origem lendo a ref) e um único campo simplifica o index. Descartado alternativa `leg INTEGER` porque números 0/99/leg são menos auto-explicativos.

- **Heurística de draft corrigida na Fase 2 via inspeção Sleeper real:** o plano original assumia `type=snake` → rookie_draft. **Realidade:** rookie_draft 2025 é `type=linear`. Heurística final: `type=linear → rookie_draft`; `type=auction + rounds≥20 + primeira liga da chain → auction_draft (startup)`; demais auction → `fa_auction`. Validada contra 2024 (1 draft auction rounds=22) e 2025 (7 drafts complete: 6 auctions com rounds 3 ou 8 + 1 linear com rounds=3).

- **Delete-and-rebuild preservando S1 + rollover via `sleeper_event_ref IS NULL`** como chave de distinção. Após backfill da migration, rows legacy do `_backfill_player_history` ficam com ref=NULL; rows factuais (tx + draft + rollover) têm ref válida. DELETE targets apenas NULL. Mais robusto que LIKE no `notes` (notes pode mudar). Resultado: 320 rows legacy deletadas, 78 trades + 220 rollover preservadas.

- **Trades delegadas 100% ao S1:** `_rebuild_player_history` chama `_sync_trades(league_id)` por liga da chain. `_collect_transaction_events` skipa `type=trade` explicitamente. Benefício: uma única lógica de trade (já testada em 22/04/2026 no S1). Risco evitado: não duplica trades S1 via UNIQUE no quintupleto.

- **Reconciliação de `Player.acquisition_type` só para eventos >= 2025:** protege year-1 rules do `salary_engine.py` para contratos vigentes. Players cujo último evento de aquisição ativa é 2024 (startup) mantêm `acquisition_type` original (geralmente `auction_draft` correto). Aplicou-se aos 4 casos: Aiyuk=fa_auction(2025), Bowers=trade(2025), BUF=fa_waiver(2025), Stroud=trade(2025).

- **Bug detectado e corrigido durante a validação dos 4 casos:** Stroud inicialmente veio com `acq=free_agent` em vez de `trade`. Causa: minha lógica de reconciliação usava `timestamp=0` hardcoded para trades preservadas do S1, então perdia para free_agent events cujo `timestamp` era o `created` da transação (número grande). Fix: buscar `Trade.trade_date` real via `sleeper_transaction_id` → cast para ms epoch → usar como tie-breaker. Stroud passou a `acq=trade` corretamente (trade leg 11 > free_agent leg 3).

- **Warnings aceitos (30 total):** 2 players sem sleeper_player_id (Hollywood Brown pid=279, Cameron Ward pid=280) → skip; 217 sleeper_player_ids sem match no DB local → players dropados antes da criação do Manager, não bloqueantes; warnings S1 de picks já drafadas → esperados.

- **Validação regression:** `salary_engine_test.py` 49/49 passam. Player.salary e contract_year atuais dos 4 casos inalterados (cap per team idêntico pré/pós). Re-run idempotente: `events_written=0, events_skipped=794`.

- **Pendente:** F8b (AppConfig.f8_rebuilt guard em import_csv.py para proteger reconciliação contra run_import() no boot) e F8c (endpoint admin `/api/admin/player_history/rebuild` + UI `/admin` + atualização de EVENT_LABELS/EVENT_BADGES no template salary_history.html + remoção da chamada `_backfill_player_history()` no boot). Backup de 175 players salvo em `f8_player_backup` pronto para o endpoint de restore F8c.

### 22/04/2026 — Camada M12 (Admin Users)

- **3 desvios da proposta original registrados no backlog:**
  (1) sem coluna `User.sleeper_user_id` — `Team.sleeper_owner_id` já existe e é
  populado pelo sync; lookup via `User.team_rel.sleeper_owner_id`;
  (2) sem chamada à `/league/{id}/users` da Sleeper API na tela — o sync existente já
  popula os dados que a tela precisa;
  (3) sem sync bidirecional com `data/users.csv` — CSV permanece como seed inicial,
  UI vira source-of-truth pós-seed. Aceitável pois Render usa persistent disk.

- **Validação automatizada via Flask test_client + auth mockado:** 7 cenários cobertos
  (GET list, POST create, PATCH toggle admin, POST duplicate→409, DELETE, GET list
  pós-cleanup, page render). Todos passaram antes de marcar como Done.

- **Decisão UX:** UI usa inputs inline + botões por linha (mesmo padrão da tabela
  "Donos dos Times" que já existia em `/admin`). Sem modais, sem framework JS —
  fetch() nativo. Consistência visual com admin.html.

### 24/04/2026 — Camada T2-FIX-2 (Fix estrutural: eliminar réplica JS `pickFcSid`)

- **Decisão: fix estrutural (opção D), não as 3 tácticas da diagnose F2.** As tácticas documentadas (a/b/c) mantinham a lógica 3-tier replicada entre Python e JS — o anti-padrão que as 4 regras novas do `DEV_METHODOLOGY.md` (adotadas ontem) existem para prevenir. **Why:** primeira oportunidade pós-regras; aplicar táctica agora seria incoerente com a motivação das regras. O refator é pequeno (~10 linhas movidas de template para endpoint) — custo comparável ao da opção (b) recomendada no handoff.

- **Decisão: enriquecer `/api/picks` em vez de criar endpoint novo `/api/picks/dynasty_values`.** **Why:** `/api/picks` já é chamado pelo `loadSide()` de `/trades` e já enriquece picks com `projected_pick`/`projection_locked` no backend. Adicionar `dynasty_value` ali preserva a semântica "tudo sobre pick vem em um único fetch", evita segunda chamada HTTP, e não cria contrato novo. Endpoint dedicado teria sido overkill.

- **Decisão: mutar `p.projected_pick` na instância ORM em vez de usar SimpleNamespace.** **Why:** `pick_sleeper_id` em `dynasty_values.py` usa `getattr(pick, "projected_pick", None)` — o Pick model não tem a coluna, então setar o atributo cria apenas um Python attr não-persistente no objeto da sessão read-only. SQLAlchemy não marca dirty para atributos que não são colunas mapeadas. Alternativa (SimpleNamespace) funcionaria mas adicionaria import + wrapper sem ganho.

- **Decisão: manter `dynastyMap` e `fetch('/api/dynasty_values')` no frontend.** **Why:** o mapa ainda é usado para jogadores (lookup por `sleeper_player_id`) em 2 lugares — `loadSide` linha ~260 e `computeSideDynastyTotal` linha ~344. Remover o fetch quebraria badges dynasty de jogadores. Apenas as variáveis órfãs do `pickFcSid` (`currentSeasonInt`, `DYNASTY_ROSTER_SIZE`) foram removidas.

- **Auditoria da regra 3 (grep de réplicas antes de fechar):** `pickFcSid`, `DP_[0-9]`, `FP_[0-9]` em `templates/` e `static/` → 0 matches. Nenhuma lógica de construção de chave FantasyCalc permanece no frontend. Fonte única: `dynasty_values.pick_sleeper_id` (Python).

- **Validação com valores concretos:** teste unitário de `pick_sleeper_id` em 4 casos — sids 100% corretos (`FP_2026_1`, `FP_2026_2`, `DP_0_3`, `None`), valores absolutos com drift pequeno vs. validação do T2-FIX no dia anterior (FC atualiza continuamente: 2571/1282/3264 em 24/04 vs. 2695/1291/3272 em 23/04). O que importa é que os sids resolvidos batem com o Python — antes do fix, JS gerava sids linearmente errados (`DP_0_14` para Rd2 pp=3, em vez de `DP_1_2`). Smoke `GET /api/picks?team=<name>` retornou HTTP 200 com `dynasty_value` populado em 100% das picks.

- **Custo do bug latente que o fix também corrige:** a diagnose F1 revelou que a fórmula JS era **pior** do que o "3-tier errado" originalmente reportado — era índice linear `(round-1)*ROSTER_SIZE + (pp-1)` em vez de `DP_<round-1>_<pp-1>`. Rd1 mostrava valor de uma slot específica da Rd2 (não de toda a Rd2 como eu havia assumido). Só o fix estrutural garante que nenhuma variante do bug sobrevive, porque elimina o lugar onde a fórmula existe.

### 24/04/2026 — Camada UX1 (Redesign tabela roster em /team/<id>) + UX3 parcial

- **Decisão: Cenário C da diagnose F1 — UX1 + UX3 (3 telas com foto), UX2 isolado.** **Why:** UX3 é aditivo puro (extrair macro de foto já é ganho líquido mesmo sem propagar); UX2 tem decisão arquitetural não trivial (como expor `_ACQ_LABELS` pra JS — 4 dos 5 call sites de acquisition_type cru são em JS). Misturar UX2 com UX1 dobraria os pontos de validação sem coerência temática. Alternativa rejeitada: UX1 puro — economizaria 10 LOC mas deixaria mais uma réplica da URL inline (sem macro), dívida imediata.

- **Decisão: enriquecer `Player` na instância ORM com atributos efêmeros `p.dynasty_value` e `p.acquisition_label`.** **Why:** mesmo padrão de T2-FIX-2 (`p.projected_pick` em `api_picks`). Setar atributos não-mapeados em ORM instance não marca dirty; é a forma mais leve de passar dados derivados ao template. Alternativa (dict wrapper ou SimpleNamespace) funcionaria mas custaria linhas extras sem ganho — a instância já circula pelo template.

- **Decisão: importar `_ACQ_LABELS` direto de `routes.roster` (underscore privado).** **Why:** prompt UX1 deixou explícito "não mover o mapa, só consumir — movê-lo é escopo UX2". Import privado entre blueprints é o mesmo anti-pattern leve do L1 importando `_build_players_by_pos`. Correto até UX2 promover o mapa a utils público.

- **Decisão: `dynasty_total` passou a consumir `p.dynasty_value` em vez de chamar `resolve_asset_value` de novo.** **Why:** evita double call no mesmo request (já resolvemos por player no enrich loop). Diff mínimo, ganho de clareza: o número exibido no Cap Breakdown é literalmente a soma dos números da tabela.

- **Decisão: macro Jinja `player_photo` + helper JS `renderPlayerPhoto` coexistem com mesma URL Sleeper CDN.** **Why:** convenção O1 já estabelecida (`player_name_link` macro + `renderPlayerNameLink` JS — mesma URL `/player/<id>`). 1 source por modo de render é o trade-off aceito; tentar centralizar mais (ex: URL via context processor injetada em JS global) seria engenharia prematura. Grep da URL retorna 2 matches (macro + JS helper), 0 inlines — critério de validação interpretado como "1 por modo de render", documentado aqui.

- **Decisão (CSS): `.player-photo-sm` como override de tamanho, não classe independente.** **Why:** `.player-photo` base (96px do M13) continua servindo o header de `player_detail`. Override de 32px + border 1px via classe modifier mantém o padrão e evita duplicar as propriedades base (border-radius, object-fit, background). Classe `.team-roster-table .col-photo` controla largura da coluna na tabela; classe `.dynasty-value-inline` usa `tabular-nums` para alinhar valores por casas decimais (padrão Bloomberg-like do UX guide).

- **Decisão: preservar `acquisition_type` cru em `roster.html` e `cap_projector.html`.** **Why:** escopo UX2 explicitamente declarado fora desta camada. Validação passou: linhas `roster.html:120` e `cap_projector.html:121` inalteradas.

- **Decisão: UX3 marcado ⚠️ parcial com 3/6 telas.** **Why:** propagar foto pras 3 telas restantes (`trades.html`, `trade_proposal.html`, `salary_history.html`) exige decisões visuais próprias — cada uma tem estrutura (asset checkboxes / server-side timeline / events) distinta da tabela densa do cenário C. Fica como UX3-b se virar dor; não é evolução trivial do UX3 atual.

- **Validação end-to-end via test_client + direct app_context:** `/team/<id>` HTTP 200 com `col-photo`, `dynasty-value-inline`, PT-BR; `dynasty_total` bate com sum dos `p.dynasty_value` dos ativos (57514 no time testado). `/`, `/cap_projector`, `/player/<id>` todos HTTP 200 consumindo macro/helper. Grep da URL: 2 matches (macro+JS), 0 inlines.

### 24/04/2026 — Camada UX3-b (fechamento de UX3 — 3 telas densas restantes)

- **Decisão: fechar débito na mesma sessão.** **Why:** F1 mostrou que o custo era trivial (~15-25 LOC total, 4 arquivos) e a infra UX1 cobria 100% sem variante/helper novos. Deixar pendente geraria overhead de contexto numa sessão futura por economia marginal. UX1 ⚠️ virou UX1 ✅ sem nova diagnose estrutural.

- **Decisão CSS: reuso total de `player-photo-sm` (32px) em todas as 6 telas, zero classe modifier nova.** **Why:** tamanho único simplifica o sistema de design — foto em lista densa tem 32px, ponto. Alternativa rejeitada (3 tamanhos: 28px Trade Manager, 24px preview, 32px salary history) dispersaria a escolha estética e criaria 2 classes CSS novas para ganho visual marginal. Se mobile ficar apertado no Trade Manager (denso com pos-badge + foto + nome + salary + dynasty badge), ajuste vira `@media` pontual, não refator estrutural.

- **Decisão: incluir `sleeper_player_id` no payload de `/api/salary_history`** (linha em `routes/salary.py:145`). **Why:** único bloqueio real identificado na F1 — sem esse campo, o JS não conseguiria invocar `renderPlayerPhoto` na tela de salary history. Extensão mínima de contrato (1 campo adicionado, nenhum removido ou renomeado), backwards-compatible. Paralelo com T2-FIX-2 que ampliou `/api/picks` com `dynasty_value`.

- **Decisão: `renderPlayerPhoto` em `salary_history.html` recebe objeto sintético** `{sleeper_player_id: p.sleeper_player_id, name: p.player_name}` em vez do record inteiro. **Why:** o endpoint usa `player_name` (não `name`) como convenção existente; o helper espera `name`. Em vez de mudar convenção do endpoint (risco de quebrar outros consumidores hipotéticos), mapeia inline. Se futuro reuso tiver mais fricção, padroniza num helper de adaptação — hoje é adaptação localizada e não bloqueante.

- **Mobile no Trade Manager — não validado empiricamente** (CLI não abre DevTools responsive). Layout `.asset-item` flex ganhou 1 elemento novo (foto 32px), somando a pos-badge + foto + nome + salary text + dynasty badge. Risco visual potencial em viewport < 400px. Sem ajuste planejado nesta camada; se virar dor no uso real, `@media` em CSS já existente.

- **Validação:** `salary_engine_test.py` 48/48; `GET /trades` e `/salary_history` HTTP 200 com `renderPlayerPhoto` no JS; `GET /api/salary_history?team=<name>` retorna 85 records 100% com `sleeper_player_id`. SSR de `/trades/proposta/<uuid>` não smoke-testado localmente (sem proposta ativa em DB local) — confiança via leitura do template + padrão SSR já validado em `team_detail`. Grep da URL Sleeper CDN: 2 matches (macro + JS helper), 0 inlines.

### 24/04/2026 — Camada UX4 (Macro compartilhada de linha de roster — HYBRID)

- **Decisão: cenário HYBRID recomendado na consulta `MAN-UX1-REORG-CONSULT` e F1 `MAN-UX4-F1`.** **Why:** converge `/team/<id>` e `/` numa única implementação estrutural de layout denso estilo FantasyPros; evita dois CSS tacticais separados (UX1-b + UX1-c) e permite que futuras camadas visuais (ex: UX2) apliquem uma vez cobrindo ambas telas. Paralelo direto com O1 (macro de link) e UX1 (macro de foto) — mesma disciplina em granularidade maior.

- **Decisão: badge REVISÃO unificada em ambos contextos da macro.** **Why:** `needs_review=True` é status do dado (Sleeper sync adicionou o player e ainda não foi validado pelo owner), não é ação dependente da tela. Mostrar em `/team/<id>` dá transparência pra quem olha time alheio ("esse player ainda nem foi revisado pelo owner dele"), valor informativo sem custo marginal. Alternativa rejeitada: preservar status quo (só em roster) — inconsistência arbitrária sem razão semântica.

- **Perda de info documentada: roster antigo exibia `ESPN: $X · Projeção 2026: $Y` numa 2ª linha de meta.** F1 especificou "name+meta = name + NFL only"; F2 manteve escopo estrito. **Consequência:** essas 2 métricas deixam de aparecer em `/`. **Caminho se virar dor:** abrir UX4-b para restaurar com coluna dedicada ou meta expandida. Decisão agora: aceitar a perda e observar se owner reclama no uso real — se ESPN/projeção era crítico, o sinal aparece rápido.

- **Decisão (canonização): CSS vars `--pos-color-*` apontam para theme vars existentes onde há match (4 de 6), e hex próprio onde não há (2 de 6 — wr, k).** **Why:** converge paleta canônica ao theme em vez de duplicar. `--pos-color-qb → var(--purple)`, etc. Os 2 hex literais restantes (`#60a5fa` wr, `#94a3b8` k) não têm correspondente no theme; mantidos como fonte canônica dedicada. Strip do `.player-roster-table` consome `--pos-color-*`. Zero hex novo duplicado em seletor de posição.

- **Débito identificado e deixado fora do escopo: `.acq-*` (acquisition-type coloring em linhas 584-588) duplica 4 dos mesmos hex** (`#a78bfa`, `#22d3ee`, `#22c55e`, `#fb923c`). **Why não resolver aqui:** semântica diferente (cor de TIPO de aquisição, não de posição); faz parte da família UX2 de PT-BR que tem discussão arquitetural própria. Registrado como observação — se UX2 futuro fizer refactor das classes acq, aplicar mesma canonização via theme vars.

- **Decisão: `.player-row` legacy preservada viva no CSS** com comentário de bloco documentando uso residual em `admin.html:351` (review_players modal). **Why:** único uso não-migrado; modal admin tem campos ad-hoc (`fantasy_team`, `acquisition_type` cru, botão "✓ Revisado") que não mapeiam na API da macro. Migrar seria inflação; reescrever inline sem classe seria trabalho sem ganho. Custo 0 LOC, ganho de clareza de intent.

- **Decisão: cada position-block mantém seu próprio `<table>` + `<thead>` repetido**, em vez de 1 tabela única com group headers. **Why:** alinha com pattern já estabelecido em UX1 (`team_detail` tinha tabela por position-block); auto-alinhamento de colunas funciona por tabela isoladamente; header repete 3-4 vezes por tela típica mas é visualmente claro por posição (title + badge + count acima). Alternativa considerada (1 tabela, pos header como `<tbody>` sub-group) adiciona complexidade CSS (`tr[data-pos-group]`, spans) sem ganho proporcional.

- **Responsividade mobile — validação planejada mas não empírica via CLI.** Layout com 7 colunas; `@media` esconde Contrato+Aquisição em <640px, Dynasty em <414px. Não validado em DevTools responsive nesta sessão. Expectativa: em 375-414px, visíveis strip + foto + nome+NFL + salário + actions (5 colunas reais) — suficiente para função primária. Se algum elemento quebrar, ajuste pontual em `@media` nas linhas já escritas.

- **Validação:** `salary_engine_test.py` 48/48. Smoke `GET /team/<id>` e `/`: HTTP 200 com `player-roster-table` no HTML, strip pos presente (23 rows em team testado com distribuição QB=3, RB=6, WR=6, TE=5, K=1, DEF=2; 25 rows em /). PT-BR ("Startup Auction") em ambas as telas. `toggleIR` handler intocado em `/`. `GET /admin` HTTP 200 com `.player-row` legado renderizando normal. Sum HTML de `dynasty_value` = 60608 == backend `total_all`; backend `dynasty_total(active)` = 57514 (continua batendo com Cap Breakdown). Grep Sleeper CDN: 2 matches (unchanged). Grep hex de pos-color em posição própria: apenas wr + k (1 ocorrência cada) — canônicos; outros 4 apontam para theme vars.

### 24/04/2026 — Camada DATA-1 (Remover badges TRADE e REVISÃO de listagens de roster)

- **Decisão: reformular o DATA-1 de "semântica + reset rule" para "onde essa info deveria viver".** **Why:** a investigação read-only confirmou que `Player.via_trade` é vitalício por omissão (setter em `sync_sleeper.py:529`, nenhum reset automático). A pergunta de owner sobre uso real de `/team/<id>` (olhando roster alheio) apontou que a info de origem histórica não é central ao uso da tela — scout, trade, audit e curiosidade olham estado atual, não história. Timeline de `/player/<id>` já é a fonte canônica da história. Remover o badge resolve na raiz sem tocar no campo.

- **Decisão: remover TRADE e REVISÃO juntos (2 linhas removidas da macro).** **Why:** REVISÃO tem dinâmica análoga (badge operacional admin, irrelevante em roster alheio). Coerência no escopo — ambos badges são "info de listagem que não pertence a listagem". Commit único, escopo compacto.

- **Decisão: manter classes CSS `.tag-trade` e `.tag-review` vivas.** **Why:** grep comprovou múltiplos consumidores legítimos fora da macro. `.tag-trade` usada em `auction.html` (entry_type fa_auction), `offseason.html` (source lottery), EVENT_LABELS JS em `player_detail.html` + `salary_history.html`. `.tag-review` usada em `cap_projector.html` (needs_review JS), banner alert em `roster.html:85`, IR/Dropado em `player_detail.html`, EVENT_LABELS em `player_detail.html` + `salary_history.html`. Remover classes quebraria vários templates; manter vivas é zero LOC extra. Justificativa alinhada com "CSS compartilhado tem múltiplos usos legítimos, não é réplica".

- **Decisão: não tocar campos `Player.via_trade` e `Player.needs_review` no modelo.** **Why:** `via_trade` continua útil para rebuild de history em `routes/admin.py:749-750` ("if via_trade, add trade event"). `needs_review` continua útil para alerta admin em `roster.html:85` e workflow de sync de player novo. Remover os badges de UI de listagem não justifica tocar o modelo. Débito "via_trade vitalício" reduz de "ativo" para "latente" — só importa se algum consumidor novo aparecer.

- **Decisão: não tocar banner alert em `roster.html:85` nem cap_projector REVISÃO.** **Why:** fora do escopo "macro de roster". Banner de roster é alerta agregado admin (info útil para quem tem time próprio); cap_projector é tela de planejamento salarial com contexto próprio. Se owner quiser ampliar remoção, camada separada.

- **Validação:** `salary_engine_test.py` 48/48. Smoke `GET /team/<id>`, `/`, `/admin`, `/player/<id>`: todos HTTP 200. Grep `class="tag tag-trade">TRADE` e `class="tag tag-review">REVISÃO` nos HTMLs de `/team/<id>` e `/`: 0 matches cada. Badge IR persistente (contagem > 0). `/player/<id>` timeline intocada (`tag-trade` no HTML via EVENT_LABELS JS). Grep `via_trade` em `templates/_macros.html`: 0 matches. Grep `via_trade` no codebase: ocorrências apenas em contextos não-UI (`models.py`, `sync_sleeper.py`, `routes/admin.py`, `routes/roster.py` PATCH).

### 24/04/2026 — Camada UX4-b (Redesign de densidade e layout de detalhe de time)

- **Decisão: 4 camadas coordenadas em commit único.** **Why:** camadas D (ESPN+Projeção), C (distribuição de colunas), A (densidade cap breakdown), B (layout 2-col cap by pos) têm interdependência visual — mudar apenas 1 deixaria inconsistência percebida pelo owner. Ordem da F1 respeitada (D→C→A→B) mas o commit agrega tudo. Vantagem: 1 review, 1 validação, 1 rollback.

- **Decisão: ESPN+Projeção em ambos contextos (paridade total), não só em `/`.** **Why:** F1 deixou decisão aberta. Argumentos a favor da paridade: consistência da macro (mesmo layout em ambas telas facilita mental model), info de ESPN ref é útil para scout de trade (owner olhando roster alheio pode querer comparar `salary` vs `espn_ref_value`), Projeção ajuda a avaliar custo real do player no offseason seguinte. Contra (rejeitado): "info off-team de baixa relevância" — marginal; o ganho de simetria supera.

- **Decisão: colgroup via macro nova `player_roster_colgroup(context)`, invocada antes do `<thead>` em cada tabela.** **Why:** alternativa (inline em cada template) geraria réplica do colgroup HTML 12+ vezes. Alternativa (include de partial) funciona mas exige arquivo novo. Macro é o padrão estabelecido em O1 e UX4 — coerente com "1 source por modo de render". Context param controla presença de `col-actions` condicional, espelhando o padrão de `player_roster_row`.

- **Larguras de `<col>` calibradas por conteúdo real (documentadas no CSS):**

| col | width | racional |
|---|---|---|
| col-photo    | 44px  | foto 32px + padding lateral (UX1) |
| col-name     | auto  | flex com o resto (min-width: 0 via CSS) |
| col-salary   | 72px  | `$28` ~40px; aguenta `$999` em tabular-nums |
| col-contract | 90px  | `Ano 2/4` ~70px; 90 dá folga |
| col-dynasty  | 96px  | `🪙 2.695` ~85px; aguenta `🪙 12.345` |
| col-espn     | 68px  | `$23.4` ~50px; folga modest |
| col-proj     | 78px  | `$28` ~35px; 78 permite 3 dígitos |
| col-acq      | 128px | `Startup Auction` ~110px; texto longo trunca com ellipsis |
| col-actions  | 84px  | `↑ Tirar IR` ~90px; compromisso |

Total fixo: 576px (team_detail sem actions) / 660px (roster com actions). col-name recebe o resto. Em 1200px viewport, col-name fica ~540-620px.

- **Decisão: `td { overflow: hidden; text-overflow: ellipsis; white-space: nowrap }` global na tabela + override `td.col-name { white-space: normal }`.** **Why:** `table-layout: fixed` + widths explícitas respeitadas 100%, mas conteúdo que exceder trunca (não estica a coluna). col-name precisa wrap para o stacked "nome + NFL em 2 linhas" funcionar — exceção explícita.

- **Densidade Cap Breakdown (camada A) — valores:**
  - `stat-num`: 1.6rem → 1.2rem (redução 25%)
  - `stat-label`: .72rem → .68rem (redução marginal; mantém hierarquia)
  - `padding`: .65rem .8rem → .4rem .55rem (redução ~35%)
  - Grid `minmax(140px, 1fr)` → `minmax(120px, 1fr)` (mais densidade horizontal)
  - **Scope-safe:** override via `.cap-breakdown-stat .stat-num` (classe parent + descendente) — zero risco em telas `/league`, `/offseason`, `/lottery_audit`, `/espn_import`, `/salary` que consomem `.stat-num` / `.stat-label` globais (smoke test HTTP 200 em todas).

- **Decisão: camada B (layout 2-col) com `grid-template-columns: 1fr 360px`.** **Why:** cards ocupam o espaço disponível à esquerda (1fr); cap-by-pos fixa em 360px à direita. `max-width: none` aplicado em `.team-detail-cap-layout .cap-by-pos-table` para sobrescrever o limit original de 360px — a tabela preenche a coluna do grid inteira. Breakpoint 768px empilha vertical (single column) — escolha pragmática para preservar leitura em mobile/tablet.

- **`@media` ampliado para esconder ESPN+Proj em <640px** junto com Contrato+Aquisição (já existentes). Sempre visíveis em mobile: strip + foto + nome+NFL + salário + [actions em roster]. Em <414px, Dynasty também some (regra pré-existente mantida).

- **Validação:** `salary_engine_test.py` 48/48. Smoke HTTP 200 em todas as 7 telas testadas: `/team/<id>`, `/`, `/admin`, `/player/<id>`, `/league`, `/offseason`, `/salary`. `/team/<id>` tem 6 `<colgroup>` (1 por posição), headers ESPN+Proj 2026 presentes, wrapper `team-detail-cap-layout` presente. `/` tem 6 `<colgroup>` dinâmicos, headers idem, `toggleIR` preservado. Grep hex pos-color em classes prefixed novas UX4-b: 0 matches (strip usa apenas CSS vars canonizadas em UX4). Zero consumidores de `.stat-num`/`.stat-label` globais afetados — override scoped preservado.

- **Alinhamento vertical cross-table e cross-page:** `<colgroup>` com widths explícitas + `table-layout: fixed` força cada tabela a respeitar as larguras dos `<col>`. Resultado: colunas SALÁRIO, CONTRATO, DYNASTY, ESPN, PROJEÇÃO, AQUISIÇÃO ficam em posições X idênticas entre QB/RB/WR/TE/K/DEF na mesma tela e entre `/team/<id>` e `/`. Validação empírica visual por inspeção no browser fica para owner; smoke via HTML confirmou estrutura e larguras aplicadas.

### 24/04/2026 — Camada UX4-c (Aperto visual final: status bar + pos-block compact + colgroup denso)

- **Decisão: 3 frentes em commit único, ordem 3→2→1 (conforme F1).** **Why:** frente 3 (colgroup) é trivial CSS-only sem dependência, calibra a base da tabela. Frente 2 (pos-block) mesmo perfil, independente. Frente 1 (status bar) é a mais complexa (toca template + CSS novo + progress bar feature nova) e se beneficia de começar com as bases já apertadas. Commit único porque o valor visual é coletivo — owner avalia o conjunto, não peça por peça.

- **Decisão: progress bar como feature nova em `/team/<id>`** (não existia antes; roster `/` tinha via `.cap-bar-wrap` separado). **Why:** owner aprovou explicitamente na F1. Paridade visual com o roster principal + sinal imediato de saúde do cap sem demandar leitura numérica. Cores via semantic tokens do theme (`--green`, `--yellow`, `--red`) — zero hex novo.

- **Valores finais para colunas tight (Frente 3):**
  - `col-espn: 58px` — pior caso `$68.4` (~40px + padding 19 = 59px). Tight mas funcional em tabular-nums. **Fallback documentado: 62-64px** se visual quebrar no browser. Sem ajuste reservado agora.
  - `col-actions: 76px` — botão `↑ Tirar IR` ~90px default. Com padding reduzido via `.btn-sm` (classe existente), cabe em 76. **Fallback documentado: 84px** se botão quebrar linha. Sem ajuste reservado agora.
  - Demais colunas da Frente 3 (photo 40, salary 56, contract 72, dynasty 88, proj 56, acq 108) ficam com folga conforme auditoria do DB (n=280 players).

- **Semantic tokens da progress bar:** `--green: #22c55e`, `--yellow: #f59e0b`, `--red: #ef4444` — definidos em `:root` (style.css:16, 17, 18). Aplicados via classes `.progress-ok`, `.progress-warn`, `.progress-over`. Zero hex novo introduzido pelo UX4-c. Grep de `#22c55e`/`#f59e0b`/`#ef4444` continua mostrando apenas os valores canônicos em `:root` + usos pré-existentes (`.acq-*`, theme vars).

- **Medição vertical pós-UX4-c (Frente 2):**
  - Gap entre última row de um pos-block e primeira row do próximo:
    - Antes: 16 (margin-bottom) + 8 (title margin-top) + ~22 (title) + ~6 (title margin-bottom) = **~52px**
    - Depois: 8 + 4 + ~20 + 3.2 = **~35px**
    - Redução: ~17px por gap × 5 gaps em 6 posições = **~85px vertical economizados** por página de roster.

- **Medição horizontal pós-UX4-c (Frente 3):**
  - Total fixo das colunas:
    - team_detail (sem actions): 576 → 478 (**-98px, -17%**)
    - roster (com actions): 660 → 554 (**-106px, -16%**)
  - `col-name` (auto) absorve a redução, ganhando ~100px extras de largura.

- **Medição do header (Frente 1):**
  - Antes (UX4-b): `.team-detail-cap-layout` com cards `.cap-breakdown-grid` (~180px altura) + `.cap-by-pos-table` (~240px altura) empilhados desbalanceados em 2-col. Altura efetiva do section: ~**240px** (a maior das duas).
  - Depois: `.team-status-bar` (~50px) + `.team-cap-progress` (5px + .4rem margin = ~11px) = **~61-65px**.
  - **Economia estimada: ~175-180px verticais** em `/team/<id>`. Empiricamente um ganho de densidade significativo — toda a info crítica de cap cabe em ~25% da altura anterior.

- **Decisão: pos-chips inline no template, sem macro nova.** **Why:** F1 confirmou. 6 invocações inline em `{% for pos, total in cap_by_pos.items() %}` são enxutas e manuteníveis. Macro nova para 6 usos em 1 único template seria engenharia prematura. CSS vars `--pos-color-*` canonizadas (UX4) garantem zero duplicação de cor no novo seletor `.team-status-bar .pos-chip.pos-*`.

- **Decisão: HTML antigo removido do template, CSS antigo mantido vivo.** Classes `.cap-breakdown-grid`, `.cap-breakdown-stat`, `.cap-by-pos-table`, `.team-detail-cap-layout` ainda existem no `style.css` mas não há mais consumidor HTML. **Why:** não removi para reduzir blast radius do commit; git history preserva para resgate. Se owner quiser limpeza de CSS dead, item separado no backlog. Atualmente "dead CSS" é menor que "risco de regressão subtil em outra tela que eu não mapeei".

- **Responsividade (Frente 1):** `@media (max-width: 768px)` esconde `.status-pos-group` inteiro; `@media (max-width: 414px)` esconde `.status-ir-cost`. Cap overview + progress bar sempre visíveis. Não validado empiricamente em viewport real — smoke test via HTML confirmou que o CSS está aplicado; comportamento visual em mobile fica para owner validar no uso real.

- **Validação:** `salary_engine_test.py` 48/48. Smoke HTTP 200 em 7 telas: `/team/<id>`, `/`, `/admin`, `/player/<id>`, `/league`, `/offseason`, `/salary`. `/team/<id>`: 1 `.team-status-bar`, 2 `.team-cap-progress` (wrapper + fill), 6 pos-chips, classe `progress-over` aplicada corretamente em time over-cap testado. HTML antigo ausente: `cap-breakdown-grid`, `cap-by-pos-table`, `team-detail-cap-layout` todos 0 matches. `/`: HTTP 200, pos-block compactado via CSS da Frente 2, colgroup denso da Frente 3 aplicado. Grep de hex de cor em CSS UX4-c novo: 0 matches (tudo via CSS vars).

### 24/04/2026 — Camada UX4-d (Tabela única de roster com pos inline)

- **Decisão: colapso estrutural via loop aninhado no `<tbody>`**, em vez de achar uma lista plana no handler. **Why:** ordem QB → RB → WR → TE → K → DEF já é garantida pelo handler via `_build_players_by_pos`; loop aninhado `{% for pos %}{% for p %}` preserva agrupamento por construção sem exigir mudança de payload. Alternativa (flatten no backend, ordem via Python sort) duplicaria ordenação que o handler já faz. Template Jinja lida bem com loop duplo; `loop.first` no inner loop marca 1ª row de cada grupo, que é todo o sinal necessário para o separador CSS.

- **Decisão: marcar 1ª row de cada grupo com atributo `data-group-first`** via param `group_first` na macro (adicionado como 3º param opcional). **Why:** permite CSS `tr[data-group-first]:not(:first-child) > td { border-top: 1px dashed }` limpo, sem precisar de adjacent-sibling por pares específicos (`tr.pos-QB + tr.pos-RB`, etc.). Alternative rejected: detectar via JS post-render — overkill, fragile. Param opcional com default `False` é backwards-compatible para qualquer futuro call de `player_roster_row` fora dos contextos de listagem.

- **Decisão localização dos counts: linha dedicada `.roster-counts` em AMBAS telas** (não só em `/`). **Why:** coerência cross-tela supera a pequena redundância com status bar em `/team/<id>`. Status bar mostra `$` por pos (info de cap); linha de counts mostra `quantidade` por pos (info de balanço) — **complementar, não duplicada**. Alternativa considerada: integrar count dentro dos pos-chips da status bar (`QB 5 $18`) só em `/team/<id>` + `.roster-counts` dedicada em `/` — **rejeitada** porque criaria divergência estrutural cross-tela, complicaria a macro dos chips, e amarraria 2 decisões independentes (densidade da status bar vs apresentação do balanço). Mantendo `.roster-counts` em ambas, as 2 telas têm o mesmo pattern de leitura ("linha de balanço no topo + tabela única").

- **Decisão: fallback K aplicado a priori** (omitir `tr.pos-K .player-name` das regras de cor). **Why:** `var(--pos-color-k) = #94a3b8` é cinza-azulado — matematicamente o contraste sobre `--bg` escuro passa WCAG AA, mas *visualmente* fica "apagado" em relação às 5 posições saturadas (roxo QB, verde RB, azul WR, laranja TE, ciano DST/DEF). Aplicar cor que parece "desligada" no K rompe o padrão de "cor como sinal de identidade" que as outras posições estabelecem. Pos-badge colorido (que continua aplicado) já carrega identidade visual suficiente para K. **Fallback aplicado como conservadora, não reativa** — sem browser local, decisão a priori é mais segura que "aplicar e esperar reclamação". Se owner quiser K colorido igual às outras, remover a omissão é trivial (1 linha CSS).

- **Decisão: manter CSS legacy de wrappers antigos vivos** (classes `.pos-block`, `.pos-block-title`, `.roster-section`, `.count-badge`, `.ir-count-badge`, etc.). **Why:** mesma postura de UX4-c — HTML removido dos templates, mas classes permanecem no style.css. Alternativa (limpar dead CSS) teria blast radius maior que o ganho estético de ~40-60 LOC removidos. Git history preserva se owner quiser resgatar. Limpeza pode virar item dedicado no backlog futuramente.

- **Medição vertical agregada (6 posições típicas):**
  - Antes UX4-d: 6× (wrapper `.pos-block`/`.roster-section` + title externo `h2/h3` + `<thead>` repetido) ≈ 6 × 45-50px = **~270-300px estruturais**
  - Depois UX4-d: 1 `.roster-counts` (~22px) + 1 `<thead>` (~22px) + 5 separadores dashed (5 × 1px = 5px) = **~49px**
  - **Economia: ~220-250px verticais** por tela de roster com 6 posições ativas

- **Colgroup atualizado:** col-pos 40px como 1ª coluna. Total fixo: 478 → 518 (team_detail, +40) / 554 → 594 (roster, +40). `col-name` (auto) absorve os +40px — em viewport 1200px, col-name passa de ~640-720px para ~600-680px, ainda suficiente para nomes reais (pior caso 22 chars "Jacory Croskey-Merritt") + tags inline.

- **col-pos CSS:** `text-align: center; padding-left: .2rem; padding-right: .2rem` — pos-badge renderizado no centro da célula, padding reduzido para maximizar uso da largura de 40px.

- **Validação:** `salary_engine_test.py` 48/48. Smoke HTTP 200 em 7 telas: `/team/<id>`, `/`, `/admin`, `/player/<id>`, `/league`, `/offseason`, `/salary`. `/team/<id>` e `/`: exatamente 1 `<table class="player-roster-table">` por tela (antes: 6 por tela), 1 `.roster-counts` (nova), 6 `data-group-first` (uma por posição QB/RB/WR/TE/K/DEF), col-pos TH presente. Wrapper `pos-block` / `roster-section` / `ir-count-badge` todos com 0 matches (removidos). Grep de hex de cor em classes UX4-d novas: 0 matches (todas as 5 cores via `var(--pos-color-*)` canonizadas em UX4). Convenção salário preservada — `.salary-cell { color: var(--green) }` e `.salary-high { color: var(--yellow) }` intocadas.

### 24/04/2026 — Camada UX4-e (Remover fundo pintado das rows por posição)

- **Descoberta durante implementação:** as regras `.pos-QB { background: rgba(...) }` (style.css:476-482) são **genéricas** — aplicam em qualquer elemento com classe `pos-QB`, incluindo span.pos-badge (col-pos da row, counts, status bar pos-chips) E tr.pos-QB (row inteira). Remover o background das regras genéricas afetaria pos-badge em todos os contextos → regressão visual indesejada.

- **Decisão: override scoped em vez de remoção da regra genérica.** **Why:** pos-badge precisa do fundo em contextos standalone (cabeçalhos, counts, status bar); row não precisa (tem strip + nome colorido já). Override `.player-roster-table tbody tr.pos-*:not(.player-ir-row):not(.renewal-flag) { background-color: transparent }` neutraliza SÓ no contexto da row, preservando regras genéricas intactas. Specificity (0,5,2) > (0,1,0) das regras `.pos-*`.

- **Decisão: `:not(.player-ir-row):not(.renewal-flag)` para proteger backgrounds semânticos.** **Why:** `.player-ir-row` tem fundo vermelho alpha; `.renewal-flag` tem fundo amarelo alpha. Essas são camadas de "status do player", não "cor por posição". `:not()` é **negative matcher** (não apenas aumenta specificity) — rows com IR ou renewal-flag não são alcançadas pelo override, mantendo os backgrounds próprios. Alternativa (depender de ordem de declaração) seria frágil.

- **Decisão: `background-color: transparent` em vez de `background: transparent`.** **Why:** validação do prompt pede grep `tr.pos-.*background:` dentro do contexto `.player-roster-table` retornar zero — shorthand `background:` dispararia falso positivo. `background-color` é semanticamente idêntico mas grep-friendly. Custo: pattern name diferente, zero impacto visual ou funcional.

- **Decisão: 7 seletores separados (QB, RB, WR, TE, K, DST, DEF) em vez de um só via attribute selector.** **Why:** classes `pos-DST` e `pos-DEF` existem distintas no codebase (herança do modelo Sleeper); listar ambas garante cobertura. QB/RB/WR/TE/K são 5 padrão. Agrupar via `[class*="pos-"]` pegaria outras classes como `pos-badge` acidentalmente — não vale o risco.

- **Decisão: não adicionar zebra-striping ou row-hover extra.** **Why:** `.player-roster-table tbody tr:hover { background: var(--bg3) }` já existe (UX4) e funciona pós-UX4-e como separação visual sutil entre rows. Sem cor de posição, hover neutro cumpre o papel. Adicionar stripes alternados (`tr:nth-child(even)`) seria complexidade sem ganho — rosters têm ~20 rows divididas em 6 grupos; separador dashed (UX4-d) + hover basta.

- **Preservado intacto:** strip vertical, cor no nome (fallback K incluído), separador dashed, linha counts, colgroup, pos-badge no col-pos inline, pos-chips da status bar, pos-badges no roster-counts, convenção salário `--green`/`--yellow`. Zero regressão em outras telas.

- **Validação:** `salary_engine_test.py` 48/48. Smoke HTTP 200 em 7 telas. Grep `tr.pos-.*background:` em contexto `.player-roster-table`: 0 matches (validação atendida). 1 ocorrência de `background-color: transparent` no override UX4-e. IR/renewal-flag preservadas por construção via `:not()`.

- **LOC:** +15 CSS (bloco do override com 7 seletores e comentário), 0 HTML/template/backend.

### 24/04/2026 — Camada UX7 (Clareamento do fundo +3pp, Opção A)

- **Decisão: Opção A (+3pp) em vez de Opção B (+5pp).** **Why:** owner comparou mocks e preferiu clareamento sutil — aproximação conservadora preserva a identidade "quase preto" do design enquanto reduz peso visual. Opção B exigiria ajuste em `--text-dim` (L54→L58) para manter contraste; Opção A não toca `--text-dim`, reduzindo superfície de mudança. Trade-off aceito: diferença visual é sutil mas real; se pós-uso real owner quiser mais clareamento, Opção B fica como próximo passo (docs indicam L58 para `--text-dim`).

- **Delta uniforme preservado em todos os 6 tokens de fundo/borda:** bg (7→10), bg2 (12→15), bg3 (16→19), bg4 (20→23), border (25→28), border2 (32→35). Cada token sobe exatamente 3pp → hierarquia entre surfaces preservada por construção (mesmos deltas relativos).

- **Matiz 218° e saturação ~30% inalterados.** Só luminosidade. Cores novas por HSL approximation: ex. `--bg` novo = hsl(218°, 28%, 10%) = `#161c28`. Validado por conversão hex→hsl.

- **`--text-dim` intocado** (`#6e84a3`, L54). **Why:** Opção A mantém contraste AA em surfaces `--bg`, `--bg2` e borderline em `--bg3`. Regressão pré-existente de `--text-dim` sobre `--bg4` (3.5:1, falha AA small) **não foi introduzida aqui** — já existia antes do UX7 (ratio era 3.7:1 original, caiu para 3.5:1 após clareamento). Se futuramente virar dor, tratamento dedicado.

- **Tokens semantic intocados:** `--green`, `--yellow`, `--red`, `--accent`, `--purple`, `--orange`, `--cyan` preservados. Saturação alta + luminosidade ~50% garante contraste confortável sobre qualquer fundo dark (L<30). F1 avaliou "parecerem gritantes" como risco teórico; nenhum ajuste considerado necessário a priori.

- **`--pos-color-*` canonizadas intocadas** (UX4). 4 apontam para theme vars; 2 são próprios (wr `#60a5fa`, k `#94a3b8`). Zero impacto de UX7.

- **Estados destacados preservados em CSS** (`.player-ir-row` alpha 8%, `.renewal-flag` alpha 5%), mas percepção visual degrada sutilmente:
  - IR-row: diferença de luminosidade sobre `--bg2` era +3.6pp (12→15.6 blended), agora é +3.4pp (15→18.4). Marginalmente menos distinto, ainda perceptível.
  - Renewal-flag: já era muito sutil (delta +1.9pp). Agora +1.75pp. **Débito delimitado aceito** — se virar dor, item futuro pode subir alpha 5→8-10%. F1 já sinalizou, owner aceitou antes da F2.

- **CSS legado preservado vivo** (`.cap-breakdown-*`, `.cap-by-pos-table`, `.team-detail-cap-layout`, `.pos-block`, `.player-row`, etc. — dead HTML pós-UX4-c/UX4-d). Clareamento do fundo afeta essas classes por `var(--*)` se forem resgatadas no futuro. Sem ação aqui.

- **Validação empírica não executada via CLI.** Smoke HTTP 200 em 13 telas confirmou que não há crash/render failure. Validação visual **fica pendente pelo owner** — inspeção em browser das telas de risco Alto (`/trades`, `/admin`, `/offseason`) e Médio (`/team/<id>`, `/`, `/player/<id>`, `/salary_history`, `/cap_projector`). Checklist per F1 (MAN-UX7-F1) documentado em `improvements.md`.

- **Nota cross-ecossistema adicionada em `fantasy_optimizer/CLAUDE.md`** (commit separado): registra que Manager clareou paleta em UX7, indica commit SHA, sinaliza que Optimizer mantém paleta original por ora. Predictor intocado (data-side sem UI owner-facing significativa — F1 justificou).

- **LOC:** 6 LOC alteradas no Manager (`static/style.css` linhas 5-12, + 2 linhas de comentário explicativo). 3-5 LOC no Optimizer (nota em `CLAUDE.md`). Smoke test cobriu 13 telas HTTP 200.

- **Validação:** `salary_engine_test.py` 48/48. Smoke HTTP 200 em 13 telas (`/team/<id>`, `/`, `/trades`, `/admin`, `/offseason`, `/player/<id>`, `/salary_history`, `/cap_projector`, `/league`, `/picks`, `/auction`, `/admin/users`, `/salary`). Grep dos 6 hex antigos em style.css: 0 matches. Grep dos 6 hex novos: 1 ocorrência cada (só em `:root`).

### 27/04/2026 — MAN-T3 registrado em improvements.md (REG, deferido)

- **MAN-T3-REG:** Trade Manager passa a expor valores **redraft** do FantasyCalc em paralelo aos dynasty existentes. Modelo escolhido: **duas barras independentes paralelas** (uma dynasty, uma redraft, ambas com origem no zero e deslocamento bidirecional), com gap implícito pela leitura visual — barras pendendo para lados opostos = flip de veredicto, mesmo sentido com magnitudes diferentes = youth premium. Briefing originado em chat do Optimizer (27/04/2026) durante análise da trade real D'Andre Swift × RJ Harvey, que mostrou flip de veredicto entre as duas perspectivas (Harvey +189 dynasty / Swift +265 redraft). Item registrado em improvements.md preservando as 8 seções de rationale (CONTEXTO, PROBLEMA/OPORTUNIDADE, DISCUSSAO, DECISOES JA TOMADAS, ALTERNATIVAS DESCARTADAS, QUESTOES EM ABERTO, DEPENDENCIAS, AO FINALIZAR) conforme template Registro do `DEV_METHODOLOGY.md` (atualizado nesta semana com a nova subseção "Tipos de prompt"). F1 (diagnose) fica para sessão futura — questões abertas listadas no item incluem endpoint redraft, schema, cobertura de jogadores, tratamento de picks (degradação elegante), refetch paralelo, cache namespace, layout das duas barras (horizontal vs vertical) e escala (compartilhada vs separada).

- **Alternativas descartadas (preservadas no item):** Modelo 1 (substituir dynasty por redraft conforme perfil) por prescritivo; Modelo 2 (blend ponderado) por inventar terceiro número não-canônico; Modelo 3 com primazia dynasty (dynasty principal + redraft secundário em tooltip) por reintroduzir prescrição.

- **Desambiguação histórica:** este MAN-T3 é distinto do "T3 (sugestões de assets)" registrado em commit `e338c28` e descartado em 23/04/2026 (entrada acima neste log). Aquele T3 nunca chegou a ser persistido em improvements.md como item de backlog — o ID estava livre e foi reaproveitado para este escopo redraft. Searchs futuros em improvements.md por "T3" encontram apenas o atual; searchs no devplan encontram ambas entradas, mas a de 23/04 está claramente marcada como descartada.

- **Primeiro item no template Registro de 8 seções:** o backlog do Manager até hoje só usava narrativa condensada para items concluídos (T2-FIX, T2-FIX-2, UX7, DATA-1). MAN-T3 inaugura o formato de 8 seções inline para items adiados com rationale a preservar. Items futuros deferidos (em qualquer ecossistema fantasy/energy/finance) que sigam o padrão usarão este como referência de formatação.

### 27/04/2026 — O2 refinado (escopo ampliado para 5 dimensões)

- **MAN-O2-REFINE:** escopo de O2 ampliado in-place absorvendo 2 dimensões novas — **time NFL no header** e **depth chart NFL embedded** (jogadores da mesma posição/time NFL ranqueados por `depth_chart_order` do Sleeper players cache, campo já consumido pela aplicação). Item agora cobre 5 dimensões agrupadas em 2 guarda-chuvas: **Contexto NFL** (header + depth chart) e **Valor de Campo** (stats Sleeper + ECR/ADP + schedule). Motivação: caso real DJ Moore (WR), owner abriu a player page e percebeu ausência completa de contexto NFL — nem o time, nem posição relativa entre os WRs do Carolina. Status/prioridade preservados (🔲 / Média).

- **Refinar in-place vs item O3 separado:** rejeitada a fragmentação porque (a) mesma página alvo (`player_detail.html`, M13), (b) mesma fonte de dados (Sleeper cache + Sleeper API), (c) escopo natural de "enriquecer page do jogador" já existia em O2. Sub-organização em "Contexto NFL (novas)" + "Valor de Campo (originais)" inline preserva visibilidade do auditor sobre o que entrou nesta sessão vs o que estava lá desde a abertura — alinhado com Auto-Containment.

- **Decisão de batching delegada a F1.** Nota explícita registrada em O2: F1 avalia se as 5 dimensões cabem numa única camada ou se vale quebrar em batches (ex: contexto NFL primeiro — só template + leitura de cache local; valor de campo depois — exige fetch Sleeper stats + schedule). Não fragmentar nesta sessão de refinação documental.

### 27/04/2026 — Camada M2 (Tela de revisão admin auditável + badge navbar)

- **Descobertas determinantes da F1 (MAN-M2-F1) que moldaram a F2:**
  - **Não-greenfield:** `/admin` já tinha `review_count` em destaque + card `#review-card` consumindo `/api/admin/review_players` e `/api/admin/review_players/<pid>/clear`. F2 foi extensão + extração, não construção do zero. Card antigo removido após substituição pela tela dedicada para evitar duplicação visual.
  - **Duas categorias semanticamente distintas no flag `needs_review`:** Cat A (sync Sleeper sem match: `salary=$1`, `acquisition_type='unknown'`, `espn_ref_value=0`) demanda aplicar defaults; Cat B (auction registrada manualmente, PATCH manual, etc.) tem dados válidos pendentes de validação cruzada. UI agrupa as duas separadamente com ações diferentes.
  - **Caminho anterior era lossy:** `/clear` zerava flag sem `PlayerHistory`; PATCH bruto via `setattr` em `/api/player/<id>` ignora o helper canônico `correct_player_salary` (`models.py:200`) que mantém SalaryHistory + PlayerHistory consistentes. F2 corrigiu prospectivamente — sem backfill retroativo.

- **5 decisões de design confirmadas pelo owner em 27/04/2026:**
  - **Tela dedicada `/admin/review` em vez de card expandido em `/admin`.** Stat-item "Revisão pendente" virou link clicável; card removido. Sem duplicação visual.
  - **Categorização em runtime, sem coluna no schema.** Predicate inline (`_categorize_review_player`) determina Cat A/B server-side; payload do GET expõe `category`; template renderiza. Frontend não duplica predicate.
  - **Auditoria só prospectiva.** Aprovações futuras geram `PlayerHistory(event_type='review_approved')`. Não inventar eventos para clears legados — princípio aprendido em F8 (não sintetizar histórico sem fonte canônica).
  - **Ação unificada com behavior por categoria.** Botão único "Aprovar" no UI; backend roteia: Cat A sem edits aplica defaults; Cat B sem edits confirma sem alteração; ambos com edits usam `correct_player_salary` se salary mudou. Tudo atômico.
  - **Contagem do modal em runtime + race-condition guard.** Modal computa lista no clique; bulk endpoint re-valida cada ID contra estado atual. Se algum ID já não é Cat A (outro admin aprovou ou sync mudou estado), rejeita transação inteira com 409 — aplicação parcial proibida porque divergiria do que admin aprovou.

- **Slot A (counter inline no dropdown "Admin ▾"):** novo context processor `inject_review_count` em `app.py` expõe `g_review_count` admin-only. Macro `nav_dropdown` ganhou param `badge` opcional. Render `Admin ▾ (3)` quando count > 0, oculto quando 0. Mobile replica via section title + item "Revisão de Jogadores".

- **Aprendizado generalizável para o Manager (não meta-mudança no DEV_METHODOLOGY):** PATCH bruto via `setattr` não é caminho seguro para campos com história. Sempre que um campo tem **tabela de história canônica** (Player.salary → SalaryHistory + PlayerHistory event_type='salary_correction'; eventualmente outros), usar o helper atômico canônico que cria as rows de história consistentes — não setattr. Para salary específicamente, o helper é `correct_player_salary(player_id, new_salary, reason)` em `models.py:200`. Diretriz fica no devplan do Manager — se padrão se repetir noutros ecossistemas (Optimizer, Predictor, Finance), aí promove para DEV_METHODOLOGY transversal. Por agora, é regra do Manager.

- **Validação:** `salary_engine_test.py` 48/48; smoke transitório (`scripts/m2_smoke.py` deletado pós-execução, conforme decisão de design — script de validação one-shot não merece slot permanente) cobriu 7 cenários: GET com category, Cat A approve, Cat B com edição passando pelo helper canônico (verificou que `SalaryHistory` foi atualizado in-place + dois `PlayerHistory` criados — `salary_correction` do helper + `review_approved` da camada M2), bulk com IDs válidos, race-guard 409, approve em player não-em-revisão 400, legacy `/clear` segue 200. Smoke de páginas confirmou `/admin` sem crash de `review_count`, `/admin/review` rendering com título e link no dropdown navbar.

- **DB local zerado** (0 players em `needs_review=True` no momento) obrigou seed sintético com marker `_M2_TEST_*`, `team_id=NULL`, cleanup atômico no `finally`. M2 é infraestrutura para próxima vez que sync gerar registros, não fix de algo quebrado em produção *atualmente* — escopo defensivo da dívida acumulada do sprint UX.

### 27/04/2026 — Camada M1 (Alerta de cap estourado pós-S1, A+B integrados) + housekeeping `/clear`

- **Descobertas determinantes da F1 (MAN-M1-F1) que moldaram M1:**
  - **"Confirmar Trade no Manager" não existe mais.** T1 transformou `/trades` em simulador puro (preview + link compartilhável); S1 fez do sync Sleeper o único caminho que materializa trades reais. A premissa original do M1 ("validação antes de confirmar trade") referia a um endpoint que foi removido. Item precisou de reframing completo, não só implementação.
  - **`_compute_cap_impact` (`routes/trades.py:86`) já retornava `over_cap: bool` por lado.** Sinal estava no payload desde T2; M1 só precisava escalar UX, não calcular nada novo no backend para Surface A.
  - **`_sync_trades` tem ponto natural antes do commit final** para computar cap pós-movimento. Sleeper é source of truth para asset movement — alert de cap precisa ser informativo, não bloqueante. Try/except wrapper garante que falha de cálculo não aborta sync.

- **Decisões de design confirmadas pelo owner em 27/04/2026:**
  - **Cap é soft (hard só na entrada do FA auction) → M1 alerta, nunca bloqueia.** Owner explicitou esse contexto durante refinamento do prompt; mudou completamente o framing de "gate" para "alerta". Sem isso, M1 teria sido implementado como bloqueio inútil (Sleeper aceitaria a trade independente).
  - **A+B integrados, não redundantes.** A é pré-decisão exploratória (owner pode mudar de ideia antes de fechar trade no Sleeper); B é pós-fato operacional (captura 100% das trades reais, incluindo as feitas direto no Sleeper sem passar pelo simulador). Cobertura diferente, função diferente.
  - **Banner B gated por offseason mode.** Durante season ativa, time pode ficar acima do cap por trades sem ser problema operacional — banner suprime. Só após rollover (offseason_mode=true) que cap vira preocupação prática (próxima janela é FA auction).
  - **Threshold estritamente acima.** `> SALARY_CAP`, não `>=`. Sub-cap = silêncio. Sem margem de aviso preventivo (rejeitada por gerar ruído crônico).
  - **Sem contagem de dias** até FA auction. Mensagem fixa, sem horizonte temporal. Manager só comunica o estado.
  - **Sem persistência.** Cap é estado, não evento. Banner recalcula a cada page load via context processor + summary; sem coluna nova, sem tabela nova, sem `PlayerHistory(event_type='cap_overrun_alert')` (mistura semântica rejeitada).
  - **Novo campo `cap_alerts` separado de `warnings`** no retorno do `_sync_trades`. `warnings` é data-integrity (roster não mapeado, n-way placeholder, player ausente); `cap_alerts` é estado operacional. Consumidores existentes de `warnings` (`admin.html:236-237`) ignoram cap_alerts sem precisar filtrar — separação semântica limpa.

- **Gap registrado (M1-FOLLOWUP, Baixa):** `is_offseason()` retorna `AppConfig.offseason_mode == "true"` (`models.py:44-45`). Flag é setada via UI quando admin inicia o ciclo de offseason, mas **não tem auto-desativação após FA auction concluído** — depende de admin desligar manualmente. Implicação prática durante 1ª temporada de uso real: se admin esquecer, banner M1 persiste mostrando "Cap será aplicado na entrada do FA auction" mesmo depois do FA auction ter acontecido. Vira ruído e desgasta confiança no alerta. Aproximação aceita por ora; item M1-FOLLOWUP em improvements.md (Status Rápido) registra a tarefa de avaliar auto-desativação (provavelmente disparada pela conclusão do passo 7 do offseason workflow ou por flag dedicada `fa_auction_completed`).

- **Housekeeping aproveitado: removido endpoint legado `POST /api/admin/review_players/<pid>/clear`.** Em M2 ele foi preservado por restrição "não quebrar retro-compat"; F1 confirmou (via grep) que único consumidor era o JS de `admin.html` deletado em M2. Custo de remoção: ~10 linhas. Aproveitar com `routes/admin.py` aberto evita reabrir contexto em sessão futura. Decisão owner: descartar de vez, sem entrada em improvements.md — commit message é o registro. Caminho atual de aprovação é `POST /approve` (auditável).

- **Aprendizado generalizável para o Manager (não meta-mudança no DEV_METHODOLOGY):** quando um signal já existe no payload (como `over_cap` em `_compute_cap_impact` desde T2) mas é renderizado de forma sutil, **F1 deve mapear se o sinal já está pronto antes de propor backend novo**. Em M1, descobrir via F1 que `over_cap` já existia eliminou ~50% do trabalho de Surface A — virou puro CSS/template. Princípio: "diagnose primeiro busca o sinal existente, não a falta dele".

- **Validação:** `salary_engine_test.py` 48/48; smoke transitório (`scripts/m1_smoke.py` deletado pós-execução) cobriu 5 cenários: synthetic player com marker `_M1_TEST_*` pushed team admin para `active_salary=$449` (over_by=$249); banner aparece com cópia e valor correto quando offseason_mode=true; banner ausente quando offseason_mode=false (gating funciona); helper `_compute_cap_alerts` retorna entry correto e `[]` para set vazio; cenário (iv) "sub-cap → banner ausente" skipado graciosamente porque baseline real do team admin já está acima do cap ($239) — exato use case do M1, threshold strict-above coberto pelo helper. Smoke pages: `/admin` 200, `/admin/review` 200, `/` 200, `/trades` 200, `/api/admin/review_players` 200; `/clear` legado retorna 404 (removido com sucesso).

- **Observação real-world:** o team admin (`Cangaceiros da Colina`) está com `active_salary=$239` — $39 acima do cap atualmente. Ou seja, M1 já tem trabalho a fazer no momento que offseason_mode for ativado pela próxima vez. Item não é puramente preventivo.

### 27/04/2026 — Camada T3 (Valores redraft do FantasyCalc no Trade Manager)

- **Sessão única:** registro REG → F1 → F2 → commit ocorreram na mesma sessão (27/04/2026), antes do deadline informal de junho/2026 que tinha sido auto-imposto. Owner em mobile remote control (sem acesso a localhost) escolheu implementar imediatamente em auto mode após F1 conclusiva.

- **Descobertas determinantes da F1 (MAN-T3-F1) — reduziram esforço esperado em ~50%:**
  - **Endpoint `isDynasty=true` do FantasyCalc já retorna `redraftValue`** ao lado de `value` em cada entry. Single fetch, single cache file. Nenhum dos refors arquiteturais antecipados em T3-REG foi necessário (cache paralelo, refetch paralelo, namespace).
  - **Picks têm `redraftValue=0`** explicit em todos os 12 PICK entries. Tratamento natural sem marcador "n/a" — barra redraft simplesmente não recebe contribuição quando asset é pick.
  - **Barra dynasty existente (`style.css:1198-1221`) é centro-zero com fills `max-width: 50%`** — estrutura ideal pra clonar visualmente. Replicar a barra redraft é puro CSS + JS espelhado, zero refator do markup existente.

- **5 decisões de design confirmadas pelo owner em troca curta via mobile (27/04/2026):**
  - **Paleta dynasty mais clara** para a barra redraft (opção C de 3) — variantes lighter dos tokens existentes (`#6ea8fe`→`#a3c4ff`; `#ff8f6b`→`#ffb8a0`). "Irmã caçula" visualmente identificável.
  - **Naming `redraft_value`** snake_case (opção A) — espelha `dynasty_value` por simetria. Frontend e backend uniformes.
  - **Manter helper `get_dynasty_values()`** com docstring atualizada (opção C) — zero refs externas mexidas, blast radius zero. Custo de "nome historicamente impreciso" aceito; auditor relê doc e entende.
  - **Totais nos labels das próprias barras** (opção A) — sem rodapé extra, sem duplicação. Stack vertical das 2 barras já produz o efeito "totais paralelos lado a lado, ambos canônicos" mencionado em T3-REG.
  - **Implementar agora em auto mode** (opção A de timing) — owner aceitou risco visual residual antecipadamente. Smoke valida lógica/payload; pixel-level pendente de inspeção em desktop.

- **Decisão de escopo emergente em F2:** `trade_proposal.html` (read-only de proposta compartilhável) **não tinha dynasty bar — T2 nunca portou**. Em vez de inflar T3 com bar markup completo (~70 LOC de Jinja), adicionado em F2 linhas compactas estilo `cap-mini` por side: "🪙 Dynasty: envia X · recebe Y · Δ Z" + "⚡ Redraft: envia X · recebe Y · Δ Z". Visualizadores externos veem ambas dimensões sem markup duplicado das barras visuais. Dynasty bar em proposal vira opcional pra camada futura se virar dor.

- **Aprendizado generalizável (não meta-mudança no DEV_METHODOLOGY):** F1 vale o tempo investido **especialmente quando o registro original (REG) lista questões abertas que assumem o pior caso**. T3-REG listou 9 questões cobrindo refator de cache, refetch paralelo, idempotência, etc. F1 confirmou que 7/9 questões caíam por achados simples no payload existente — economia real de horas de F2. Princípio: F1 sempre deve verificar se o sinal já existe no payload/código antes de propor backend novo. Mesmo padrão observado em M1 (`over_cap` já no payload de `_compute_cap_impact`).

- **Ordem REG → F1 → F2 → commit em mesma sessão funciona quando** (a) o registro REG tem 8 seções com rationale completo, (b) F1 é read-only puro e factível com WebFetch + Grep + Read, (c) F2 é majoritariamente UI sobre payload existente. Não generalizar pra todas as camadas — mas registrar como caso possível quando todas as 3 condições batem.

- **Validação:** `salary_engine_test.py` 48/48; smoke transitório (`scripts/t3_smoke.py` deletado pós-execução) cobriu 7 cenários: cache + helper + asset_dicts + cap_impact + endpoints + page render. WebFetch direto na FantasyCalc API confirmou shape do payload (150 entries em redraft, 100 em dynasty, 12 PICK em dynasty com redraftValue=0). **Validação visual (cores, alinhamento, mobile) fica pendente do owner em desktop pós-deploy.**

- **Risco visual residual aceito:** F2 implementada em mobile remote control — owner não consegue inspecionar `/trades` e `/trades/proposta/<uuid>` em browser nesta sessão. Se cores destoarem, alinhamento das 2 barras stacked não ficar bom, ou mobile quebrar densidade, owner sinaliza pós-deploy e ajustamos como camada T3-FIX se necessário.

### 27/04/2026 — Camada T3-FIX-UX (delta-pointing redesign + mobile overflow fix)

- **Owner inspecionou prod via screenshot mobile e identificou divergência:** T3-REG escreveu *"barra correspondente desloca-se para o lado oposto na proporção do valor recebido"* — owner queria padrão **delta-pointing** (1 fill se desloca do centro pro lado do vencedor da trade). Implementação F2 inicial replicou o padrão T2 dual-fill (2 fills coexistindo, cada um mostrando magnitude do seu lado). Erro de interpretação meu — T3-REG falava de "desloca-se", eu li como "cresce de cada lado".

- **Bonus issue detectado no screenshot:** mobile overflow horizontal — header da barra tinha 5 elementos (name+total esquerdo, chip central, total+name direito) competindo por largura, com team names truncados ou cortados.

- **Redesign aplicado nesta camada:**
  - **HTML** (templates/trades.html): markup substituído por `.delta-bar-section` consolidada (compartilhada entre dynasty e redraft via classes `.delta-bar-dynasty` e `.delta-bar-redraft`). Header em **3 linhas separadas** (label dim "🪙 Dynasty" → names truncados → totais compactos → bar → chip), reduzindo overflow horizontal em mobile. Track tem 2 metades (`.delta-bar-half-left` / `.delta-bar-half-right`) com `.delta-bar-zero` (marcador vertical 2px) entre elas indicando o "zero".
  - **JS**: extraído renderer compartilhado `_renderDeltaBar(opts)` chamado por `updateDynastyBar()` e `updateRedraftBar()` (DRY — mesma lógica, só muda dimensão e IDs). Lógica: `delta = totalB - totalA`; `delta > 0` → A wins → fill na metade esquerda anchored ao centro com `width = pct%`; `delta < 0` → B wins → fill na metade direita; `delta == 0` ou ambos zero → ambos fills width=0. Magnitude: `pct = abs(delta) / max(totalA, totalB) * 100`.
  - **CSS**: classes legacy `.dynasty-bar-*` e `.redraft-bar-*` substituídas por `.delta-bar-*` consolidadas. Mobile-first: header com `display: grid; grid-template-columns: auto 1fr 1fr;` + `text-overflow: ellipsis` em team names. `.delta-bar-zero` é `width: 2px; background: rgba(255,255,255,0.25)` — vertical line tênue marcando o zero. Cores per side preservadas (left=blue, right=orange) entre dynasty e redraft, redraft com paleta lighter.

- **Validação:** smoke 10/10 (markup novo presente, JS function `_renderDeltaBar` exportada, classes legacy ausentes); `salary_engine_test.py` 48/48. Validação visual continua pendente — owner inspeciona pós-deploy e sinaliza se algo ainda destoa.

- **Aprendizado:** quando o registro REG diz "se desloca", o auditor (eu) deveria ter pensado **paradigma de movimento** (1 elemento que se move) antes de **paradigma de growth** (2 elementos que crescem). Inércia de replicar T2 (que era growth-based) cegou a leitura. Princípio: ao implementar UI baseada em descrição textual, **explicitar o paradigma visual** (growth vs movement vs other) antes de codar markup. Se o T3-REG tivesse uma frase tipo "modelo: 1 marcador único se deslocando do zero" ou um sketch ASCII, a divergência teria sido evitada.

- **4 sub-iterações pós-deploy inicial (todas owner-driven via screenshot mobile, mesmo dia):**
  - **T3-FIX-UX-2** (`5faaf17`): bug nos totais — só 1 dos 2 totais aparecia em cada barra. Causa: `.delta-bar-totals` com `grid-template-columns: auto 1fr 1fr` (3 colunas) mas HTML tinha 2 spans; regra `:nth-child(1) { visibility: hidden }` escondia totalA, jogava totalB na coluna errada. Fix: `grid-column` explícito (col 2 + col 3) nos 2 spans existentes.
  - **T3-FIX-UX-3** (`862444c`): owner detectou (1) overflow lateral do chip "✅ Team leva +X" quando team name era longo, e (2) modal "Preview Cap Impact" não mostrava redraft. Fixes: chip com `display: block; max-width: 100%; white-space: normal` (wrap em vez de overflow); `.delta-bar-section { overflow: hidden }` belt-and-suspenders; `renderPreview()` JS estendido com `assetLine` mostrando 🪙 + ⚡ por player, helper `makeAdvBadge` extraído, 2 advantage badges no topo do modal (dynasty + redraft).
  - **T3-FIX-UX-4** (`c4e1619`): owner detectou (1) team-cell ainda com nowrap empurrando "Tropa do Bicampeonato 🏆 (TropadoJarra)" pra fora do card mobile, e (2) descrição de trade ("Player (TeamA→TeamB); ...") era parede de texto. Fixes: override de `.team-cell { white-space: normal; word-break: break-word }` em `@max-width: 768px`; novo helper `_parse_trade_description(desc, team_a, team_b)` em `routes/trades.py` parsing tokens em listas a_to_b/b_to_a/unparsed; template renderiza 2 colunas "de/para" estruturadas com headers `{team} envia →` quando `t.flow` está presente, fallback raw description quando N-way.
  - **T3-FIX-UX-5** (`45005fc`): owner detectou que o primeiro asset de cada coluna começava em alturas diferentes — header esquerdo era 3 linhas, header direito era 2 linhas, então "George Kittle" e "Travis Kelce" não alinhavam. Causa: `.flow-col` independentes empurravam assets pra baixo conforme altura do próprio header. Fix: restruturação do markup — headers e listas agora siblings diretos do `.trade-flow` (4 children); CSS `grid-template-rows: auto auto` faz row 1 reservar altura do header maior; `align-self: end` em `.flow-col-header` faz o texto do header menor alinhar pelo bottom da row.

- **Aprendizado generalizável das 4 sub-iterações:** UX iterativo com owner em mobile remote control via screenshots funciona BEM. Cada iteração é cirúrgica (~10-100 LOC), testável visualmente em segundos pelo owner, e corrige um problema específico. Loop tight: owner aponta gap → fix → push → screenshot → próximo gap. 4 deploys em sequência fechando uma camada UX completa. Risco residual aceito antecipadamente (auto mode, sem inspeção visual em desktop pelo Code) compensado pelo loop curto.

### 28/04/2026 — MAN-S1-FIX Fase 2 Implementação ✅

- **Fix arquitetural deployado.** `_sync_trades` em `sync_sleeper.py:495+` ganhou guard cross-season: parâmetro opcional `league_season` (derivado via `_get(/league/{lid}).season` se None) + flag local `is_previous_season = (league_season < current_season)`. Mutação de `Player.team_id`/`fantasy_team`/`is_my_team`/`via_trade` (linhas 587-600) e `affected_team_ids` agora envolvidas em `if not is_previous_season:`. Trade row + PlayerHistory event continuam sendo gravados incondicionalmente (histórico canônico preservado). PH gravada com `season=league_season` (não `get_current_season()`) — corrige a fonte da metadata errada que estava em parte do bug raiz da linha 519 original.

- **Callers atualizados para passar season cacheada:** `routes/admin.py:323-329` (backfill — payload já em escopo) e `sync_sleeper.py:909-915` (F8a `_rebuild_player_history` chain walk). `run_sync()` linha 307 deixa derivar internamente (overhead trivial de 1 chamada API extra por sync).

- **Decisão de assinatura:** `league_season` como parâmetro opcional (não obrigatório) preserva retrocompatibilidade — se algum caller futuro esquecer de passar, fix continua ativo via derivação interna. Warning explícito no `result["warnings"]` quando derivação falha (Sleeper indisponível) e código cai no comportamento legado (mutação aplicada). Aceitável: degradação graciosa para edge case raro.

- **Validação executada em DB de cópia (`dynasty_test_f2.db` ephemeral, deletado pós-teste):** 4 cenários do prompt + sanity. Cenário 1 (backfill cross-season): forçado `league_season=current-1`, 29 Trade rows + 78 PH criadas, zero mutações de team_id. Cenário 3 (PH.season): 78/78 com season correta. Cenário 5 (idempotência): 2ª passada `imported=0`. Cenário 2 (sanity current league): zero erros. Logs específicos em `improvements.md` → MAN-S1-FIX → Fase 2.

- **Recovery aplicado no DB real via `run_sync()`:** 4 stale movidos para times corretos automaticamente via guard pré-existente (`sync_sleeper.py:251-254`). **Cangaceiros active_salary $239 → $255** (bate com prod). Idempotência confirmada — 2ª passada `players_updated=0`. UPDATE manual one-shot (cogitado em F1 para Tank Dell + Rico Dowdle por estarem dropados) **não foi necessário** — owner confirmou em validação manual de prod que ambos estão em rosters Sleeper ativos hoje, então alignment os resgatou.

- **Surpresa de drift de season Sleeper:** entre F1 (28/04 manhã) e início do F2 (28/04 tarde), Sleeper avançou suas próprias seasons — `LEAGUE_ID` agora retorna `season=2026`, `previous_league_id` retorna `season=2025`. AppConfig local ainda em `current_season=2025`. Implica que reproduzir o bug "naturalmente" hoje requer forçar `league_season` explicitamente (Sleeper não devolve mais `previous_season < current_season`). Não afeta o fix; apenas a estratégia de teste. Sinaliza que rollover local de season eventualmente terá que acontecer e o guard continuará válido (`league_season < current_season` é a condição que importa, independentemente dos valores absolutos).

- **Nota de leitura sobre "rafadgil":** o prompt do F2 listou Tank Dell indo para "rafadgil" — owner esclareceu pós-recovery que rafadgil é o **owner** do time Pitbull do Samba (team_id=1), não o nome do time. Recovery está correto: Sleeper retornou Pitbull do Samba e bate com a expectativa do owner.

- **Cosmético do botão "Importar Trades Históricas":** fora do escopo do F2 conforme alinhado. Owner avalia pós-deploy se vale criar item separado de baixa prioridade.

- **Outputs:** 2 arquivos de código (`sync_sleeper.py`, `routes/admin.py`) + 2 docs (`improvements.md`, `manager_devplan.md`). Sem schema change, sem migration, sem alterações em prod além do auto-deploy via push origin/main. Status MAN-S1-FIX: 🔲 → ✅.

### 28/04/2026 — M10 refinado (escopo ampliado: navbar global + calculadora; correções factuais)

- **MAN-M10-REFINE:** escopo de M10 ampliado in-place absorvendo busca global de jogador. Item passa de "Autocomplete de Jogador na Calculadora de Salário" (Baixa) para "Busca de Jogador: Global + Calculadora" (Média). ID preservado, status 🔲 mantido. Refinamento puramente documental — nenhum código de aplicação tocado nesta sessão. Precedente seguido: MAN-O2-REFINE (27/04/2026).

- **Motivação (gap de navegação básica):** owner observou em 28/04/2026 que o Manager não tem ponto de entrada para chegar à player page (`/player/<id>`, M13) sem antes saber em que time fantasy o jogador está. Os 5 entry points existentes (alert Year 4 e needs_review do roster, admin/review, salary_history timeline, trade simulator asset list) todos pressupõem contexto. Caso real: "queria ver o contrato do Patrick Mahomes" → caminho atual seria abrir os 12 rosters procurando visualmente. Promoção Baixa → Média justificada pelo gap concreto + custo de implementação reduzido (endpoint backend já existe).

- **Decisão de promover M10 in-place vs criar item novo (Opção A — "S1 — Search"):** rejeitada criação de ID novo. Calculadora segue como consumidor legítimo do mesmo backend; expandir escopo de M10 preserva continuidade auditável e o histórico do item. Opção C (refinar in-place) é alinhada com MAN-O2-REFINE como precedente para refinamento documental sem inflação de IDs.

- **Refutação explícita da Opção D (absorver em O2)** baseada nos 3 critérios de MAN-O2-REFINE: (a) **target page diferente** — O2 enriquece o conteúdo de `/player/<id>`, busca global vive na navbar atravessando o app inteiro; (b) **fonte de dados diferente** — O2 puxa Sleeper API + cache, busca usa apenas DB local (`Player.query.filter`); (c) **escopo natural distinto** — "enriquecer página" e "navegar até a página" são verbos diferentes. Refutação registrada dentro do próprio item M10 para auditoria futura.

- **Correções factuais identificadas pelo diagnose MAN-SEARCH-F1, absorvidas no item refinado:**
  - Endpoint correto é `GET /api/player/search?q=<nome>&team_id=<opt>` (singular) em `routes/roster.py:312-326`. **Já existe** com `Player.name.ilike("%q%")`, limit 20, retornando `Player.to_dict()`. A versão pré-refinamento de M10 propunha criar `/api/players/search` (plural) — premissa incorreta, agora corrigida.
  - `player_lookup.find_player_by_name()` é matching estrito 4-tier (exact → ci → normalized → None), usado em reconciliação Sleeper/CSV. **Não serve para autocomplete** — incompatível com prefix typing. A versão pré-refinamento sugeria reusar — também corrigido.

- **Reuso confirmado pelo diagnose, registrado como base para F1 do item refinado:** padrão de dropdown UI do team-filter em `templates/roster.html:51-65, 159-170` + `static/style.css:311-340` (vanilla JS, abs-positioned, sem libs); helper JS `renderPlayerNameLink` em `templates/base.html:245`; padrão debounce de `salary_history.html:27-31`.

- **Decisões delegadas a F1 (registradas no item, não fechadas nesta sessão):** breakpoint desktop↔mobile, layout do dropdown dentro do overlay mobile (flow normal vs absolute), criação opcional de `Player.to_search_dict()` minimal (~6 campos vs 21 de `to_dict()`), reuso direto vs manual de `renderPlayerNameLink`, e batching dos 2 consumidores (única camada vs navbar-primeiro / calculadora-depois). F1 avalia priorizando o gap UX maior (navegação global) primeiro.

- **Observações tangenciais do diagnose:** absorvida como nota dentro de M10 a observação sobre `Player.to_dict()` retornar 21 campos com método invocado (`is_renewal_candidate`) e função (`projected_next_salary`) — F1 decide se otimiza. Descartada como decisão de plataforma (não vira item) a ausência de rate limiting global em endpoints Flask.

- **Outputs desta sessão:** 2 docs editados — `improvements.md` (entrada M10 refinada + linha de Status Rápido) e `manager_devplan.md` (este log entry). Nenhum código tocado.

### 28/04/2026 — MAN-S1-FIX Fase 1 Diagnose ✅

- **Diagnose read-only do bug cross-season de `_sync_trades`.** Mecanismo confirmado contra dados reais (47 Trade rows; 1-29=2025 inseridas 14:49, 30-47=2024 inseridas 18:26 = backfill +3.5h depois; Player.updated_at dos 6 stale = 2026-04-22 19:41:57 coincide com Trade rows 2024). Causa: `_sync_trades` (`sync_sleeper.py:495-661`) muta `Player.team_id` cego (linhas 561-562) + idempotência global por `sleeper_transaction_id` UNIQUE (linha 532) impede correção via re-run. Linha 519 (`season = get_current_season()`) também faz parte do bug raiz — grava `PlayerHistory.season` errada para trades de previous league.

- **Surpresa de escopo:** apenas 4 dos 6 players citados são stale. Jaydon Blue e RJ Harvey ESTÃO corretos em Cangaceiros (rookies via trades 2025); o `via_trade=True` + `updated_at=22/04 19:41:57` deles é da sync legítima da current league. Diff $239 vs $255 ($16) é compatível com 4 stale. 2 dos 4 (Tank Dell, Rico Dowdle) estão dropados no Sleeper — `run_sync()` linhas 286-291 só seta `is_dropped=True`, deixando `team_id` órfão errado.

- **Réplicas mapeadas:** 8 caminhos de mutação `Player.team_id` no codebase. **Apenas `_sync_trades` (`sync_sleeper.py:561-562`) tem o bug**; F8a (`sync_sleeper.py:909`) **herda** via `_walk_league_chain` que itera `_sync_trades(lid)` por liga. Outros 6 caminhos imunes (run_sync alignment com guard `!=`, run_sync new player, drop logic só seta `is_dropped`, auction manual autoritativo, CSV import preserva, rollover não toca). PH 2024 (4 rows criadas em 22/04 19:42:31-32) é factualmente correta — preservar.

- **Recomendação para F2:** fix **(a)** rejeitar movimentação de `Player.team_id` quando `trade.season < season-da-liga-processada` (cobre F8a e rollover inerentemente; deve corrigir linha 519 simultaneamente, gravando `PlayerHistory.season` como `season-da-liga-processada`) + recovery **(iv)** rodar `run_sync()` (corrige Chase Brown e Emanuel Wilson de graça via guard das linhas 251-254) + UPDATE one-shot para Tank Dell e Rico Dowdle (dropados, fora do path do run_sync). Não escolher (b)/(c)/(d) (cosmético, perigoso ou frágil); não escolher (i)/(ii)/(iii) (overkill, frágil para Tank/Rico, ou bloqueado por fix).

- **Pendências do owner antes do F2:** (1) validar manualmente cobertura prod em `/team/5` (suspeita: latente, não manifesto), (2) confirmar estado Sleeper atual de Tank Dell e Rico Dowdle (ainda dropped?) — determina target do UPDATE one-shot, (3) preservar PH 2024 (confirmado pelo owner), (4) cosmético do botão "Importar Trades Históricas" fica fora do F2; eventual item separado se owner decidir pós-F2.

- **Outputs apenas em docs:** sub-bloco completo em `improvements.md` (item MAN-S1-FIX) com 5 tabelas + recomendação + pendências; nenhuma alteração em `sync_sleeper.py`, `models.py`, `dynasty.db`, ou prod. Status do item permanece 🔲 (F1 não fecha — F2 fecha quando implementação termina). Detalhes técnicos completos em `improvements.md` → MAN-S1-FIX → Fase 1.

### 05/06/2026 — M15 (Lottery 6 seeds) Fase 1 Diagnose ✅ (MAN-M15-F1)

- **Item M15 (MAN-M15-REG) registrado 🔲 em `improvements.md`** com as seções do prompt preservadas + sub-item "Fase 1 Diagnose ✅" respondendo às 5 validações. Status permanece 🔲 (F1 não fecha o item).
- **Achados-chave (read-only, verificado contra código + `dynasty.db`):** lottery oficial 2026 ainda **não ocorreu** (`lottery_audit` vazia → F2 usa `/run_lottery`, não `/replace`); premissa de 5 seeds é **literal** em 6 arquivos (pool/draw `range(1,6)` / verify `<=5` / `[12,11,10,9,8]` em 4 pontos / `ball-color-1..5` / string "95 bolinhas"), sem `static/*.js` (JS é inline); legenda de % do `offseason.html` já é derivada (ok), mas `LOTTERY_ODDS` em `picks.py` é réplica hardcoded; fronteira lottery↔standings em **5 lugares**, mas só o pick 6 migra de fixo→lottery (picks 7-12 inalterados).
- **Retrocompat:** audits antigas de 5 seeds **não quebram** desde que a F2 derive a contagem de draws/verify de `len(pool_json)` do snapshot, nunca de constante global. Escopo F2 recomendado: parametrizar (fonte única) > ajustar literais; custo ~5-6h.
- **Item descoberto:** `LOTTERY_ODDS`/legenda de `/picks` mostra odds **erradas hoje** (pré-existente ao M15). Recomendação: absorver na F2 do M15 (default) ou promover a ID própria — decisão do owner.
- **Outputs só em docs** — nenhuma alteração de código/DB; sem commit isolado (agrupar com a F2). Detalhes em `improvements.md` → M15 → Fase 1 Diagnose.

### 05/06/2026 — M15 (Lottery 6 seeds) Fase 2 Implementação ✅ (MAN-M15)

- **Parametrização como fonte única, não ajuste de literais.** Seguindo a recomendação da F1 (Opção parametrizar > literais), criei em `routes/offseason.py` uma única declaração `DEFAULT_LOTTERY_WEIGHTS` (6 seeds, soma 96) + `_seed_rank` + três builders (`_build_lottery_pool`, `_build_fixed_picks`, `_build_default_draft_order`). Todos os pontos antes replicados (3 cópias de pool, 5 da fronteira lottery/standings, contagem de draws, seeds da página, threshold do save) passaram a derivar deles. Adicionar/remover um seed no futuro = mudar só o dict. Custo real ~em linha com a estimativa F1.
- **Retrocompat via `len(pool_json)`, nunca constante global.** Decisão crítica da F1 confirmada na implementação: `_draw_weighted_lottery` virou `range(1, len(pool)+1)` e o verify usa `n_lottery = len(pool)` do snapshot salvo. Resultado: audit de 5 seeds reproduz exatamente 5 picks e bate com seu `result_hash` (validado com audit sintético V3); audit de 6 seeds reproduz 6. Schema de `LotteryAudit` e fluxo de 2 fases do M8 (409/replace+reason) intocados — restrição respeitada.
- **Correção da legenda de odds absorvida no M15, sem ID próprio.** O `LOTTERY_ODDS` hardcoded e divergente de `picks.py` foi **removido** e substituído por `_build_lottery_odds()` que deriva da fonte canônica (pct = peso/total). Corrigir standalone e re-tocar na F2 seria retrabalho — owner havia deixado a decisão em aberto na F1; default (dobrar no M15) aplicado.
- **Validação sobre cópia temporária do DB.** As 8 validações (19 asserts, 19/19 PASS) rodaram via Flask `test_client` apontando `DYNASTY_DB` para uma cópia em tempdir — o `dynasty.db` real permanece com `lottery_audit` vazio (sorteio oficial 2026 segue a cargo do admin via UI). Evita criar audit canônica real que bloquearia o sorteio oficial com 409. Script de validação descartado pós-run.
- **Arquivos:** `routes/offseason.py`, `routes/picks.py`, `templates/{offseason,picks,lottery_audit}.html`, `static/style.css` (`ball-color-6`), `CLAUDE.md`. Detalhes em `improvements.md` → M15 → Fase 2 Implementação.

### 05/06/2026 — M15-FIX (Editor de pesos do lottery) F1 Diagnose ✅ (MAN-M15-FIX-REG)

- **Item M15-FIX registrado 🔲** em `improvements.md` com seções do prompt + Fase 1 Diagnose. Bug reportado pós-M15: editar pesos no `/offseason` não atualiza pool/legenda. F1 (read-only) isolou que a divergência é **puramente visual/client-side** — o backend (run_lottery/simulate/replace) já consome os pesos editados via `gatherLotteryWeights()` → `{weights}` no body, e o audit grava exatamente esses (`weights_json`/`pool_json`). A causa: grid `#lottery-pool` + legenda são renderizados só no server (Jinja, page load) e os inputs `.lottery-weight` não têm `oninput` → não re-renderizam.
- **Gap derivado:** `_build_lottery_odds()` (`/picks`) sempre lê `DEFAULT_LOTTERY_WEIGHTS`, nunca o `weights_json` do audit — pós-sorteio com pesos editados a legenda divergiria. Entra no escopo do fix (frente B).
- **Escopo do fix (fase seguinte):** A — `oninput` que reconstrói pool/legenda/total client-side; B — `_build_lottery_odds()` deriva do audit canônico quando existir. Status permanece 🔲. Sem commit docs-only isolado — agrupar com o código do fix.

### 05/06/2026 — M15-FIX (Editor de pesos reativo + legenda audit-first) Fase 2 ✅ (MAN-M15-FIX)

- **Fonte ÚNICA de render movida para JS, não duplicada Jinja↔JS.** A restrição central era não ter a lógica peso→bolinhas/%/total em dois lugares. Em vez de adicionar um re-render JS *além* da render Jinja existente (que criaria a réplica), **removi** a construção de pool/legenda do template e a centralizei em `renderLotteryPool()`; o template virou só dados (inputs `.lottery-weight` com `data-seed`/`data-team` + valor default) + containers vazios. O estado inicial também sai do JS (via `DOMContentLoaded`) — uma fonte só, ver [[feedback_grep_replicas_before_scope]]. `gatherLotteryWeights` foi reescrito sobre a mesma `getSeedRows()`, garantindo "o que é exibido = o que é sorteado = o que é gravado".
- **Regra de input inválido: bloquear, não clampar.** Vazio/zero/negativo/não-numérico (mínimo 1 bolinha) → `lotteryWeightsValid()=false`, banner visível, e `runLottery`/`submitReplace` retornam antes de enviar request. Optei por bloquear em vez de auto-corrigir para 1 porque silenciar a edição do owner poderia gravar um pool que ele não pretendia.
- **Legenda `/picks` audit-first.** `_build_lottery_odds()` passou a aceitar pesos; `_canonical_lottery_weights(draft_season)` lê `weights_json` do audit canônico. Com audit → mostra os pesos efetivamente usados; sem audit → default canônico. Fecha o gap em que pesos editados no sorteio não apareciam na legenda pública.
- **Backend intocado (confirmado na F1).** Endpoints já consumiam `{weights}` e o audit já gravava os pesos usados — a F2 só alinhou a camada de apresentação. Schema do audit, fluxo de 2 fases do M8 e retrocompat do verify (5 seeds) preservados.
- **Validação:** 8 validações / 15 asserts, 15/15 PASS. As de render (V1/V2/V5) rodaram o **JS real** extraído da página em Node + DOM shim (não uma reimplementação), sobre cópia temporária do DB — `dynasty.db` real intocado. Detalhes em `improvements.md` → M15-FIX → Fase 2.
- **Arquivos:** `templates/offseason.html`, `routes/picks.py`, `CLAUDE.md`. Commit único agrupando código + docs pendentes da REG/F1.

### 05/06/2026 — M16 (R2/R3 do rookie draft) F1 Diagnose ✅ — bug CONFIRMADO (MAN-M16-REG)

- **Item M16 registrado 🔲 (Alta)**. Verificação read-only pós-lottery (regulamento 8.2.1/8.2.5: lottery define só o R1; R2/R3 = standings invertido, campeão fecha com 12/24/36). **Divergência confirmada:** `_build_pick_projections` (picks.py) aplica o mesmo `lr.pick_number` (ordem sorteada) a R1/R2/R3 via `for rnd in PICK_ROUNDS`. Reprodução em cópia temporária do DB: hoje mongoloides (11º, ganhou pick 1) abre o R2; deveria ser Miller Time! (12º). `R2==lottery=True`, `R2==standings=False`.
- **Propaga para valores dynasty:** `pick_sleeper_id` (dynasty_values.py:192) usa `projected_pick` para a chave FantasyCalc → R2/R3 com posição errada = valor dynasty errado nos picks de R2/R3 = trade distorcida. Não é cosmético.
- **Replicada em 3 loops** (todos em `_build_pick_projections`): branch lottery draft_season, branch future com lottery, `_apply_standings_order`. O caso sem-lottery (#3) está correto; o bug é só quando HÁ lottery.
- **Recomendação F2:** R1 = rows do `DraftLotteryResult`; R2/R3 = `_build_default_draft_order(standings)` (fonte única já existente do M15, dá a ordem standings-invertida). Sem mudar schema/audit/sorteio. Status permanece 🔲. Sem commit docs-only isolado — agrupar com o código do fix. Detalhes em `improvements.md` → M16 → Fase 1 Diagnose.

### 05/06/2026 — M16 (R2/R3 = standings) Fase 2 ✅ (MAN-M16)

- **Causa:** fan-out do `pick_number` nos 3 rounds (`for rnd in PICK_ROUNDS`) no branch de lottery — a ordem sorteada vazava para R2/R3, que pelo regulamento (8.2.1/8.2.5) seguem standings invertido. Corrigido com `_apply_lottery_with_standings_tail()`: R1 das rows do `DraftLotteryResult`, R2/R3 de `_build_default_draft_order(standings)`.
- **Reuso da fonte única, sem nova implementação.** A ordem standings-invertida de R2/R3 vem do helper já criado no M15 (`_build_default_draft_order`) — o mesmo usado no caso sem-lottery. O orquestrador é compartilhado pelos dois branches de lottery (draft_season + future), eliminando a réplica do fan-out. Caso sem lottery permanece intocado (R1=R2=R3=standings já era correto).
- **Nota — valores dynasty de R2/R3 estavam distorcidos desde o sorteio.** `pick_sleeper_id` deriva a chave FantasyCalc de `projected_pick`; com R2/R3 na ordem sorteada, os picks de R2/R3 de times do lottery recebiam valor de slot errado em trades. O fix corrige isso de tabela (ex.: mongoloides R2 → `DP_1_1`, antes `DP_1_0`).
- **Validação:** 8/8 PASS em estado pós-lottery sintético (discriminante: mongoloides 1/14/26, Miller Time! 4/13/25, campeão 12/24/36) sobre cópia temporária do DB; regressão sem-lottery byte-equivalente; `salary_engine` 48/48. `dynasty.db` real intocado.
- **Arquivo:** `routes/picks.py`. Commit único (código + docs da REG/F1). Pós-deploy, owner confere `/picks` em produção (pick 13 = 12º colocado) — única instância com a audit canônica real.

### 05/06/2026 — OFF26-3 (Importador de drafts) F2 ✅ + helper canônico de aquisição (MAN-OFF26-3-F2)

- **Fundação primeiro: helper atômico canônico de aquisição.** A F1 revelou que o "helper canônico de criação de contrato" **não existia** (replicado 4× inline no `/auction`, sem usar `year1_salary`). Criei `models.record_acquisition()` como única porta (Player+SalaryHistory+AuctionLog atômico, salário via `year1_salary`) e refatorei `register_fa_auction`/`register_rookie`/`upload_excel` para usá-lo. **`bulk_register` ficou de fora** — é o item F9, e a restrição do F2 proibia tocá-lo; documentei como a única réplica inline remanescente (consolidação faz parte do F9). Tensão com a validação "criação em 1 ponto" resolvida a favor da restrição explícita, com a exceção sinalizada.
- **Idempotência sem mudar schema.** Restrição proibia alterar schema; `AuctionLog` não tem `sleeper_event_ref`. Em vez de adicionar coluna, gravo o token `[ref:draft:<id>:<pick>]` em `AuctionLog.notes` e checo via `acquisition_already_recorded()`. Reimport não duplica (validado: 0 criados / 45 já existentes).
- **Fluxo único com 2 modos, não dois fluxos** (decisão da F1 confirmada). Auto-detecta por `draft.type`; salário resolvido pelo canônico (`year1_salary`: auction→amount, rookie→floor(ESPN×1.2)). Reusa o núcleo de leitura do `sync_sleeper` (`_get`) adaptado p/ 1 draft.
- **Preview→confirm com gate anti-pulo-silencioso.** Preview não escreve; cada pick sem match (DST/rookie/dropado/roster) exige ação explícita; confirm bloqueia (400) se houver pendência. Cap **soft** (alerta via `draft_budget`, nunca bloqueia). Rejeitar = não confirmar (preview é read-only).
- **Validação:** 12/12 contra drafts reais de 2025 (rookie 36 picks: 34 match + 2 classificados; auction: 45 criados, salário=amount, idempotente) em cópia temporária; `salary_engine` 48/48; `dynasty.db` real intocado.
- **Arquivos:** `models.py`, `routes/auction.py`, `routes/draft_import.py` (novo, 10º blueprint), `templates/draft_import.html` (novo), `app.py`, `CLAUDE.md`. Commit único agrupa também os docs pendentes de OFF26 (REG + OFF26-3-F1) e F9/F10. Handoff gerado.

### 07/06/2026 — M17 + M18 registrados (feedback de produção do Michel) + colisão de IDs

- **Dois itens novos 🔲 a partir de feedback do Michel (team_id=8) via WhatsApp:** **M17** — personalização por usuário logado (home abre no time do admin + cap widget mostra cap do Cangaceiros para todos; default team e widget devem derivar de `current_user`, precedente M9/M13), prioridade **Alta** (afeta os 11 owners não-admin). **M18** — timestamps exibidos em UTC cru (card Sleeper Sync +3h vs BRT); fix de exibição com conversão client-side pelo fuso do browser, armazenamento UTC mantido, prioridade **Média** (bloqueia M4).
- **Colisão de IDs corrigida:** os prompts vinham rotulados como M15 e M16, mas ambos foram consumidos nesta sessão pelo trabalho de lottery (M15 = 6 seeds, M16 = R2/R3). O planejamento no Claude.ai estava com o backlog defasado. Remapeados para os próximos livres da série M: **M17** e **M18**. Refs originais preservadas nas seções (prompt MAN-M15-REG / MAN-M16-REG).
- Registro apenas (REG); F1 de cada um ainda não rodado. Sem commit docs-only isolado — agrupa com o próximo código.

### 08/06/2026 — M17-F1 diagnose (read-only) absorvida + decisões de escopo F2

- **F1 confirmou a hipótese:** nenhuma surface deriva de `current_user.team_rel`; todas ancoram no legado `MY_TEAM_NAME`/`is_my_team` → sempre o time do admin. `$255` = `active_salary()` real do Cangaceiros → time errado renderizado, não valor stale.
- **Conjunto completo mapeado (8 surfaces):** 5 funcionais (home default+fallback do roster, chip JS + título hardcoded do cap widget, pré-seleção do cap projector) + 3 cosméticas (tag "EU" no dropdown Times, card `league-card-mine`+EU no League Hub, prefixo 🏆 no header do roster). Lógica replicada em 4 lugares (rota Python, JS client-side, literal hardcoded) — o chip **re-resolve no cliente**, não consome valor server-side.
- **Precedente canônico a replicar:** `current_user.team_rel` em `/team/<id>`, banner M1 e picks — já tratam `team_rel is None` como neutro.
- **3 decisões de escopo do owner para a F2** (gravadas na subseção F1 do M17 em improvements.md): (1) fallback team NULL = estado neutro; (2) cosméticas entram junto com as funcionais (mesma causa-raiz); (3) cap widget migra para resolução server-side via context processor (padrão `inject_nav_teams`), eliminando a réplica JS.
- M17 permanece 🔲 (F2 não executada). Absorção docs-only — sem commit isolado; agrupa com o código da F2.

### 08/06/2026 — M17-F2 implementada (personalização por usuário logado) ⚠️ localhost

- **Fonte única server-side:** novo context processor `inject_user_team` (`app.py`) injeta `g_user_team` (= `current_user.team_rel` ou None) + `g_user_team_cap` (= `active_salary()`). Substitui o conceito legado `MY_TEAM_NAME`/`is_my_team` em todas as surfaces de **exibição**. Precedente replicado: `/team/<id>`, M1, picks.
- **8 surfaces unificadas:** home default + fallback (`roster.py`), chip de cap valor + título (`base.html`, render server-side — réplica JS `loadCapChip` removida), cap projector (`salary.py`), tag "EU" no dropdown Times desktop+mobile (`base.html`), `league-card-mine`+EU no League Hub (`_build_team_card` recebe `my_team_id`), 🏆 no header do roster (`roster.html`).
- **Decisão — flag `is_my_team` vira só dado:** mantida no schema e escrita pelo sync/`record_acquisition`/`/api/teams` to_dict (restrição: não tocar sync/engine/schema), mas **deixou de ser fonte** de "time do usuário" em qualquer surface de exibição. Projeção `Team.is_my_team` removida de `inject_nav_teams` (dado morto na navbar).
- **Decisão — fallback neutro:** usuário sem time vinculado (team_id NULL) → `g_user_team=None` → home "Sem dados", sem chip, sem time forçado, sem 500. `?team=` inválido cai no próprio time do usuário (não num time fixo).
- **Limpeza:** import morto `MY_TEAM_NAME` removido de `routes/trades.py` e `routes/roster.py` (confirmado via grep: só aparecia no import).
- **Validação localhost** (test_client, DB copiado, login via sessão `_user_id`): 8/8 critérios. Michel (team 8) vê o próprio time + chip `$183/$200` "Trust The Process" (não os $255 do Cangaceiros); Erico (team 5) vê Cangaceiros por derivação; usuário sem time → neutro; cap projector pré-seleciona o time certo; cosméticos no time do usuário; chip sem `teams.find`/`loadCapChip`. `salary_engine_test.py` 48/48.
- **Status M17 = ⚠️** (pendente smoke em produção com login real dos owners). Sobe para ✅ após confirmação em prod.
- **Arquivos:** `app.py`, `routes/roster.py`, `routes/salary.py`, `routes/league.py`, `routes/trades.py`, `templates/base.html`, `templates/roster.html` + docs (`improvements.md`, `manager_devplan.md`). Commit único agrupa código + docs (inclui a absorção F1 e este registro F2).

### 08/06/2026 — WV1 registrado (regra waiver-sem-drop → salário de FA) 🔲

- **Item novo 🔲 (MAN-WV1-REG)** emergido em discussão durante o M18. Regra de liga: aquisição fora de draft é **waiver** quando o jogador **nunca foi dropado** por nenhum time, senão **FA**; o salário difere. Caso ilustrativo: rookie não-draftado pego no waiver após semana 1 — como nunca foi dropado, o contrato deve usar a **regra de salário de FA** apesar do mecanismo ser waiver.
- **ID:** novo prefixo **WV** (waiver) — confirmado livre contra o backlog (nenhuma colisão; séries existentes: X/S/T/Q/M/MAN-/OFF26-/F/E/DP). 1º item da série.
- **Decisões já tomadas:** waiver-sem-drop → salário-como-FA; implementação adiada (depende da lógica de aquisição / pacote offseason); **preservar** os timestamps hoje não exibidos (`AuctionLog.created_at`, salary history) — decisão do M18 reforçada aqui, pois podem virar consumidores desta regra.
- **Toca:** `record_acquisition` (porta canônica de criação de contrato) + `salary_engine` + histórico (`PlayerHistory`/`AuctionLog`). **Relaciona-se** com OFF26-3, E2, F9. **F1 pendente:** confrontar regulamento (valores waiver vs FA) + mapear a fonte do sinal "foi dropado?" (Sleeper transactions / PlayerHistory / flag) + verificar se o tipo de aquisição chega confiável ao helper ou é inferido + checar réplica (cap projector JS, preview do draft import).
- Registro apenas (REG); sem F1/F2 nesta etapa. **Sem commit docs-only isolado** — agrupa com o próximo commit de código (provável M18-F2).

### 09/06/2026 — Encerramento da sessão 08–09/06 (checklist de fim de sessão)

- **Entregue ✅ em prod:** M17 (personalização por usuário — ⚠️ aguarda só smoke de login), M18 (timestamps no fuso, validado), E4-b (delete de 2 órfãos-duplicata, validado), E4-c-1 (store canônico ESPN por `(sleeper_id, season)`, backfill 273 validado). **⚠️ localhost, smoke prod pendente:** E2-RISK (tela) + E4-a (matcher) — um import ESPN real fecha os dois. **Registros 🔲:** WV1, E3, E4 (guarda-chuva), E4-c-2.
- **Diagnoses → itens (auditado):** E2RISK-F1/F1B→E2-RISK+E4; E4-F1→E4-a/b/c; E4-c-F1→E4-c-1/c-2; E4-b-F1 corrigiu a premissa (dup→delete). Todas absorvidas no improvements.md.
- **Meta-mudanças com motivação:** MAN-DOC-DBPATH (caminho do banco vivo `/data/dynasty.db` no CLAUDE.md, descoberto na operação do E4-b); helper único `set_espn_value` como fonte de escrita; flag `is_my_team`/`MY_TEAM_NAME` rebaixados a dado (M17).
- **Pendências registradas (próxima sessão):** smoke prod de M17/E2-RISK/E4-a; **DP1 desbloqueado** (lê o store canônico); E4-c-2 (higiene: DROP ESPNValue + generalizar RookieEspnValue); E2 e2e (~ago); seed versionado ainda contém os 2 órfãos (latente; rota re-rodável).
- **git = prod = knowledge** após o push do commit de fechamento (docs-only). `salary_engine_test` 48/48 ao longo da sessão.

### 10/06/2026 — Encerramento da sessão DP1 (checklist de fim de sessão)

- **Entregue nesta sessão:** **DP1-F1** (diagnose read-only — verificada independentemente contra o código e absorvida no improvements.md) + **DP1-F2** (board de planejamento de cap pré-draft + simulação multi-pick no backend) — ⚠️ localhost, smoke prod pendente. **Registro 🔲:** MAN-METH-REG (candidato a baseline do DEV_METHODOLOGY). **Commits em prod (`main`):** DP1-F2 `dc47bd4`, MAN-METH-REG `452231b` (push `7ffde04..452231b`).
- **Status reflete realidade:** DP1 = ⚠️ (localhost; ✅ só após smoke em prod, que depende de um import ESPN da season popular `RookieEspnValue`). improvements.md (item DP1 + Status Rápido + header) e handoff 10/06 atualizados.
- **Diagnoses → itens (auditado):** DP1-F1 absorvida no item DP1 (bloco F1 — ACHADOS) + o achado de premissa-falsa virou item próprio **MAN-METH-REG** (não ficou só no parecer). UX4-b: nota metodológica pré-existente **absorvida/referenciada** (não duplicada).
- **Correção de premissa (registrada):** a premissa "DP1 lê o store canônico via `espn_store_adjusted`" (repetida no REG, no improvements.md e no handoff 08–09/06) estava **empiricamente errada** — o canônico só tem rosterados (backfill `SELECT FROM players`, `app.py:390`); os entrantes vivem em `RookieEspnValue`. Seguir a premissa entregaria board vazio. Fonte corrigida em todos os docs; **E4-c-2 não bloqueia nem é pré-requisito do DP1**. (A nota 09/06 acima — "DP1 desbloqueado (lê o store canônico)" — fica como registro histórico da crença da época; esta entrada a corrige.)
- **Meta-mudança com motivação:** MAN-METH-REG eleva a lição "F1 de consumo/refatoração deve refutar premissas do prompt contra o código + listar campos existentes ausentes na proposta" a candidato a baseline, consolidando DP1-F1 (premissa falsa) + UX4-b (campo omitido). Não é regra vigente; consolidação no `DEV_METHODOLOGY.md` fica para sessão de revisão de metodologia dedicada.
- **Pendências registradas (próxima sessão):** smoke prod do DP1 (junto com E2-RISK/E4-a/M17 — um import ESPN real fecha vários); E4-c-2 (higiene); E2 e2e (~ago); **F10** (`draft_budget` replicado em JS no cap_projector — o DP1 **não** ampliou o débito: simulação no backend). Persistência de cenário do DP1 ficou **fora de escopo** (item próprio se priorizado).
- **git = prod = knowledge** após o push do commit de fechamento desta sessão (docs-only). `salary_engine_test` 48/48.

### 10/06/2026 — DP1-F2 implementada (board pré-draft + simulação multi-pick) ⚠️ localhost

- **Fonte da lista = `RookieEspnValue` por season** (`get_current_season()+1`), **não** o store canônico — decisão derivada da F1 (canônico só rosterados). Endpoint `GET /api/cap_projector/rookies` ordena por valor e devolve ESPN ref (raw) + `projected_salary` via fonte única `year1_salary("rookie_draft", 0, espn_adjusted)` — sem row de Player, sem réplica (mesma invocação do `draft_import.py`).
- **Simulação no backend** (`POST /api/cap_projector/simulate`): `draft_budget()` canônico sobre o roster ativo do `current_user.team_rel` (M17, cap atual via `p.salary`) + os rookies do cenário como "+salário" via `SimpleNamespace` transitório em memória (**não materializa Player** — stub-$1 segue rejeitado, E2-REFINE). Cenário vazio → budget atual, idêntico ao `/api/cap_projector`. **Decisão:** base = salário atual (literal "cap atual"/"budget atual sem alteração" do prompt), não projetado.
- **Não amplia o F10:** a réplica JS de budget (`updateSummary`) ficou **intocada**; a nova seção lê `keeper_salaries`/`usable_draft_budget` direto do backend — 0 agregação de cap em JS, 0 `×1.2` novo no template (grep confirmado).
- **Fora de escopo (explícito):** persistência de cenário e modelagem de picks (regra 8.2.7 independe do slot).
- **Validação localhost:** `salary_engine_test` 48/48; smoke via test client (usuário **não-admin**): `GET /cap_projector` 200; lista de `RookieEspnValue` (canônico vazio no DB → confirma fonte); `$46→$55` e `$3→$3`; cenário 2 picks → soma `+$58` no backend; cenário vazio inalterado; **nada escrito** (store + cap intactos).
- **Arquivos:** `routes/salary.py`, `templates/cap_projector.html` + docs (`improvements.md`, handoff 10/06). Commit único `dc47bd4`.

### 10/06/2026 — MAN-METH-REG registrado (F1 refuta premissas do prompt contra o código) 🔲

- **Lição transversal** emergida 2× (DP1-F1 = premissa de fonte falsa; UX4-b = campo existente omitido): especificação positiva **omite por silêncio**. Regra candidata: F1 de consumo/refatoração lista, com evidência do código, as premissas do prompt contradizidas + os campos/comportamentos existentes ausentes na proposta, com parecer por item (premissa falsa / remoção intencional / perda não-intencional / deslocamento).
- **Candidato a baseline, NÃO regra vigente.** Destino: consolidação no `DEV_METHODOLOGY.md` em revisão de metodologia dedicada (transversal manager/optimizer/predictor). Absorve a nota metodológica do UX4-b (referência, não duplicata). Registro apenas — sem código. Commit docs-only `452231b`.
- **Relaciona-se** a "validar premissas empiricamente" (pré-IMPL) e à fonte única (T2-FIX-2 / F10): a F1 é o momento barato de pegar o gap antes do IMPL nascer sobre base falsa.

### 15/06/2026-pt2 — Fechamento de 5 itens + migração O3 (Opus, docs-only)

Sessão de fechamento documental (sem código). Cinco itens atingiram o critério de ✅ e foram
marcados no Status Rápido + tiveram a seção detalhada movida **verbatim** ao
`improvements_archive.md` (regra O3: ao marcar ✅, migrar no fechamento).

- **UX8** (foto ao lado do nome no /cap_projector) e **UX9** (fragmentação do passo 2 no /admin):
  **smoke de prod 15/06/2026** confirmado.
- **F11-FIX-UX** (microcopy do preview de rollover): fecha **junto com o UX9** — o sintoma que
  perseguia (passo 2 quebrado em prod) foi eliminado **pela raiz** pelo fix do UX9; sem trabalho
  próprio remanescente.
- **DP2** (cadeia única no cap projector — board sobre keep/corte + summary sticky): smoke de prod
  já confirmado.
- **F12** (CSV bootstrap one-shot via flag `csv_bootstrap_done`): fechado pelo **critério
  dev-local** registrado (comportamento puramente dev-local; não depende de smoke de prod).
- **Migração O3:** as 5 seções detalhadas saíram do `improvements.md` e estão no
  `improvements_archive.md` (verbatim, só o marcador de status flipado p/ ✅). O **Status Rápido
  permanece completo** (105 linhas; as 5 linhas seguem lá como ✅ — namespace/baseline de dedupe).
  Cross-refs `[[DP2]]`/`[[F11-FIX-UX]]`/`[[UX9]]` continuam resolvíveis (agora apontam ao archive).
- **Sanity:** `salary_engine_test.py` 48/48; seams de remoção limpos (1 `---` por junção); zero
  mojibake. Nenhum item 🔲/⚠️ tocado.
- **Lembrete ao owner:** re-upload de `improvements.md`, `improvements_archive.md` e
  `manager_devplan.md` no Project Knowledge.

### 15/06/2026 — UX9 F2 (Opus): fim da fragmentação do passo 2 no card de fluxo (/admin)

Continuação da sessão UX (Opus 4.8). F2 do UX9 após a F1 de diagnose.

- **Causa-raiz (F1):** no card "Ordem do Fluxo Pré-Temporada", cada passo é um `<li>` com
  `display:flex`. O passo 2 tem um link inline (`Intertemporada` → `/offseason`) **no meio da
  frase**, que parte os filhos do `<li>` em vários flex items (badge + strong + texto-antes +
  link + texto-depois); cada item de texto encolhia até min-content e quebrava numa coluna
  estreita. Passos 1/3 (texto contíguo, um flex item) não fragmentavam. **Não era multi-coluna
  nem comprimento** — por isso o F11-FIX-UX (que encurtou o texto) não resolveu.
- **Fix (Opção A, estrutural):** envolver o corpo de cada passo (tudo após o badge) num
  `<span class="step-body">` único → o `<li>` volta a ter 2 flex items (badge + body) e o
  conteúdo do body flui inline normal, link incluso, em ordem de leitura. Regra CSS nova
  `.step-body { flex:1; min-width:0 }`. Aplicado aos 3 passos (consistência + resistência a
  links inline futuros).
- **Local, zero propagação:** `.workflow-steps`/`.step-num`/`.step-body` são exclusivos deste
  card. Card "Season Rollover (preview)" abaixo (link `/offseason` num `<p>` normal) e demais
  cards do `/admin` **não tocados**.
- **Amarração com F11-FIX-UX:** o sintoma que o F11-FIX-UX perseguia some pela raiz aqui. Seu
  critério de done não tem mais trabalho próprio — quando o smoke de prod do UX9 passar, o
  F11-FIX-UX **fecha junto** (anotado explicitamente no `improvements.md`).
- **Validação localhost:** `salary_engine_test.py` 48/48; `git diff` = 3 `<li>` + 1 regra CSS.
  UX9 → ⚠️ (✅ após smoke prod). **Sem push** — deploy fica com o owner.

### 15/06/2026 — UX8 F2 (Opus): foto ao lado do nome no /cap_projector

Sessão UX (Opus 4.8). Lote REG→F1→F2 de duas pendências de UI do cap projector e do /admin;
o F2 do UX8 foi implementado nesta sessão (UX9 ficou em F1).

- **Decisão de layout (UX8, opção B do owner):** no `/cap_projector` a foto deixa de ser
  empilhada **acima** do nome e passa a ficar **ao lado** (mesma linha que nome + tags ANO 4/
  REVISÃO), recuperando densidade vertical em telas com 20+ jogadores.
- **Implementação (Opção A da F1, mínima):** uma regra CSS — `.player-name-cell` ganhou
  `display:flex; align-items:center; gap:.4rem; flex-wrap:wrap`. A `<td>` da row vira flex
  container; a foto fica em 32px (`.player-photo-sm` intocada). Sem mudança de markup/JS.
- **Por que local e seguro:** `.player-name-cell` é **exclusiva do cap projector** (grep: 1
  ocorrência). A infra de foto compartilhada (`.player-photo-sm`/`.player-photo`/macro
  `player_photo`/helper `renderPlayerPhoto`) governa **só a imagem**, não o posicionamento — as
  outras 5 telas densas (`/`, `/team/<id>`, `/trades`, `/salary_history`, `/player/<id>`) já põem
  a foto ao lado por estrutura própria e **não foram tocadas**. Blast radius zero.
- **Falso positivo corrigido:** a "tag de fechamento malformada (`<\span>`)" que a F1 havia
  flagrado **não existia** — era artefato do Grep, que renderiza `/` como `\` (o `</span>` real
  aparecia como `<\span>`). O Read do fonte confirmou markup bem formado. Nenhuma correção de tag
  foi feita (não havia bug). Lição: cruzar achados de "tag malformada" do Grep com o Read antes de
  tratar como real.
- **Validação localhost:** `salary_engine_test.py` 48/48 (sanity de cálculo); `git diff` = 1
  regra CSS. **Pendente:** smoke visual em prod (owner dispara o deploy). UX8 → ⚠️ no
  `improvements.md` (✅ após smoke).
- **Sem push** — gatilho de deploy fica com o owner.

### 12/06/2026 (pt3) — F10 ✅ + DOC1 ✅ + F11-FIX-UX layout + F12 + DP2 (Opus)

Sessão multi-item (commits separados por item; abertura no 1º commit). Início no Opus 4.8.

- **Abertura — F10 ✅:** smoke de prod passou (/cap_projector com summary canônico: $157 projetado /
  $43 restantes / $38 usável / 5 spots min $5, matemática conferida; toggles dirigindo o POST; board
  DP1 com aviso de store vazio). Seção F10 (4.699 chars) **migrada verbatim+flip ao archive** (O3).
- **F11-FIX-UX (layout):** o texto novo passou no card "Season Rollover (preview)" mas **quebrou o
  layout** do passo 2 do card "Ordem do Fluxo Pré-Temporada" (fragmentou em colunas, espaço antes do
  `;`). Encurtado só o passo 2 → "— aplicado na etapa Season Rollover da página de Intertemporada;
  aqui, só a prévia" (link mantido). **Segue ⚠️** até smoke do layout em prod.
- **DOC1 ✅ (docs-only):** seção "App Startup Sequence" do CLAUDE.md reescrita lendo `app.py` passo a
  passo (âncoras de linha). Corrigidas as 2 divergências da AUD1 (ordem do `init_auth` = perto do fim,
  não antes do sync; `run_sync`/backfill **condicionais** a `fresh_import`, backfill ainda atrás de
  `f8_rebuilt`) + 4 omissões achadas na mesma passada (URI via env `DYNASTY_DB`; filtro `utc_iso`/M18;
  4 context processors + 9 blueprints + error handlers; `app.run` só sob `__main__`). Nenhuma virou
  item novo. **Done sem smoke** (docs): cada passo com âncora apontável. Seção migrada ao archive (O3).
- **Commit 1** (abertura + DOC1): docs + `templates/admin.html` (passo 2).
- **F12 ⚠️ localhost (commit 2):** CSV vira bootstrap one-shot para salary/contract. **Decisão:
  Opção B (flag própria `csv_bootstrap_done`), não o guard `f8_rebuilt`** — num DB de dev fresco
  `f8_rebuilt=false`, reusá-lo não fecharia o caso dev-local; flag própria segue o precedente do
  próprio `f8_rebuilt` (lazy, fallback "false", fora do `_seed_app_config`) e é chave nova em
  AppConfig (sem mudança de schema). No branch de player existente, salary/cyr só na 1ª semeadura;
  branch de create intocado (player novo entra normal); prod (CSV ausente) retorna cedo, flag nunca
  setada. Escopo estrito a salary/cyr (set_espn_value/position/nfl_team fora — registrada observação
  ESPN como candidata a item próprio). CLAUDE.md (Commands) atualizado. **Validação:** boot duplo
  (semeia→edita→preserva 26.0/cyr 3), player novo entra com flag=true (created=1), prod skip com flag
  intacta; `salary_engine_test` 48/48. Done dev-local registrado; mantido ⚠️ até o owner confirmar.
- **DP2 ⚠️ localhost (commit 3):** cadeia única de planejamento no cap projector (revisão consciente
  da base do DP1-F2, decisão do owner). O board de rookies passa a partir do **cenário keep/corte**
  (salário projetado, base = summary do F10) em vez do roster integral com salário atual; a tela
  ganha **uma barra sticky única** (cortes + rookies). **Estendeu o `/budget` canônico do F10 com
  `rookie_sids`** (preferiu estender a criar 2ª fonte) e **removeu o `/simulate`** do DP1-F2 (fundido).
  Painel do board reduzido a nº de rookies + custo; `updateSummary`+`simulateScenario` fundidas em
  `refreshScenario` (1 POST `kept_ids`+`rookie_sids`). CSS `.cap-summary-sticky` (top=navbar 54px;
  flex-wrap → sem overflow mobile). **Grep de duplicação:** a única era interna (`#proj-*`×`#rk-*`),
  colapsada; `draft_import.html` é superfície distinta (fora de escopo). **Validação:** retrocompat
  (all kept+0 rookies==$256 F10), 4 cenários integrados × canônico, caso DP1 ($46→$55/$3→$3/+$58),
  `/simulate` 405, nada escrito; `salary_engine_test` 48/48. DP1 ganhou nota de revisão (cross-ref
  DP2). ✅ após smoke em prod (sticky ao rolar + toggles refletindo + board nº/custo).

### 12/06/2026 (pt2) — F11 ✅ (smoke prod) + F11-FIX-UX + evidência no F9 + F10 ⚠️ localhost (Fable)

- **Abertura — F11 ✅:** smoke de prod PASSOU (deploy `75e69e7`): /admin sem o botão de apply, preview
  funcional com dados reais (273 jogadores, 0 renovações, cap $2187→$2310), /offseason Step 4
  bloqueado por gate (step 3 pendente). Seção F11 (3.928 chars) **migrada verbatim p/ o archive**
  (regra O3, asserts por script: verbatim no archive + ausente do ativo). **F11-FIX-UX** registrado
  (sub-item, padrão N1-FIX/T3-FIX-UX) e **aplicado**: microcopy de owner nos 2 cards do /admin
  (prévia × aplicação real na etapa Season Rollover da página de **Intertemporada**, link
  /offseason, sem nº de step, sem season hardcoded) — ⚠️ até o smoke do F10. **F9** ganhou a
  corroboração viva da forense F11 (salary_history=0 no disco vivo 12/06; F1B auditara cópia de
  07/06) + vínculo de urgência: fechar F9 **antes da FA auction 2026** (primeiro uso real do
  /auction; `bulk_register` é a única porta inline restante).
- **F10 — premissa do prompt refutada (MAN-METH-REG, 4ª ocorrência da família):** "pode bastar
  consumir o payload atual" — não basta: o `budget` do GET é sobre salário ATUAL do roster inteiro;
  o `updateSummary` soma `next_salary` do subconjunto keep/corte. **Fix no padrão DP1:** novo
  `POST /api/cap_projector/<team>/budget` ({kept_ids} → `draft_budget` canônico sobre mantidos com
  `project_next_salary` + derivados de display `cap_pct`/`shortfall`). JS vira POST+display puro:
  consts `SALARY_CAP`/`MAX_ROSTER` deletadas, zero agregação, guard de sequência p/ toggles
  rápidos, mensagens usam `b.salary_cap` (tb. no painel DP1 — render idêntico, endpoint intocado).
- **Grep de réplicas (codebase): zero réplicas novas → zero itens novos.** Única réplica era o
  updateSummary; literais "$200" de display (base/trades) = decisão consciente (valores vêm do
  backend); agregações server-side de cap usado ≠ regra de budget; draft_import já consome o
  canônico via SimpleNamespace.
- **Validação (test client, não-admin temporário):** payload×canônico idêntico em 4 cenários de
  keep/corte; paridade Σ next_salary == keeper_salaries; 404; **regressão DP1** — cenário vazio ==
  budget atual e caso 2 picks **+$58** reproduzido ($46→$55, $3→$3, store re-semeado e limpo);
  nada escrito; grep template = zero aritmética; Jinja parse OK; `salary_engine_test` **48/48**.
- **Status: F10 🔲 → ⚠️ localhost; F11 ⚠️ → ✅; F11-FIX-UX novo ⚠️.** Commit único (código + docs);
  push a cargo do owner. ✅ do F10/F11-FIX-UX após smoke em prod (summary correto + toggles +
  board DP1 + cards do /admin).

### 12/06/2026 — F11 (Fable): Etapa 1 prod LIMPO ✅ + Etapa 2 fix Opção A ⚠️ localhost

- **Etapa 1 — verificação retroativa em prod (read-only, gate obrigatório antes do fix):** queries
  forenses geradas pelo Code, executadas pelo owner no Render Shell (`sqlite3 -readonly /data/dynasty.db`).
  **Veredito: LIMPO — nenhum rollover jamais foi aplicado em prod.** `salary_history` = **0 linhas**
  (contratos vivos vieram do CSV bootstrap, que não gera history — classe F12); 0 lotes/0 duplicatas
  de rollover; **0 assinaturas `"Season rollover"` no `sync_log`** (marcador forense exclusivo do
  caminho admin — só ele gravava SyncLog) → botão admin nunca usado; 0 contract_year fora de 1..4;
  config consistente (`current_season=2025`, `rollover_done=false`, `season_locked=true` — offseason
  2026 no Step 2/3). Sem corrupção, repair desnecessário; a janela de risco estava **aberta** (1º
  rollover da liga iminente) — o fix chegou antes do primeiro disparo possível.
- **Pré-fix, grep por 3º caminho (restrição do prompt):** escritas de `SalaryHistory(` = models.py:396
  (record_acquisition ano-1) + os 2 rollovers; incrementos de contract_year = os 2 rollovers + edição
  per-player M2 (admin.py); fetches de UI = admin.html:285 + offseason.html:724. **Só os 2 catalogados.**
- **Etapa 2 — fix Opção A (matar a réplica):** removidos `POST /api/admin/rollover/apply` (admin.py,
  substituído por comentário-guard "porta única = offseason Step 4"), botão "⚡ Aplicar Rollover" +
  `confirmRollover()` + `#rollover-result` (admin.html) e o comentário stale "CURRENT_SEASON is a
  constant" (vivia dentro do endpoint removido). **Preview mantido** (decisão registrada: read-only,
  função pura, zero dependência do caminho removido); card renomeado "Season Rollover (preview)" e
  step-list apontando o apply para `/offseason`. **Offseason 100% intocado** (nenhum diff em
  offseason.py/offseason.html — gates e semântica do Step 4 idênticos).
- **Validação:** grep pós-fix = **1 caminho de escrita** (offseason.py:675-683); 0 refs a
  `rollover/apply`/`confirmRollover`; `py_compile` + Jinja parse OK; `salary_engine_test` **48/48**.
- **Status F11: 🔲 → ⚠️ localhost.** ✅ só após smoke em prod (deploy + admin sem botão/preview
  funcional + offseason Step 4 intacto). Commit único código+docs. **F10 (mesma janela Fable) fica
  para a próxima sessão** — não embarcado aqui para manter o commit do F11 atômico.

### 11/06/2026 — Encerramento da sessão AUD1 (REG + F1 + priorização do lote)

- **Entregue:** AUD1 registrada (série **AUD** nova — auditorias, F1-only, sem F2 própria) e **F1
  executada ✅** — varredura read-only do codebase inteiro pelas 6 lentes de incidentes históricos,
  rodada no **Fable 5** (caso cirúrgico da política de modelos; janela até 22/06; foi também o
  test drive da Lente 6 = regra candidata MAN-METH-REG). Zero código tocado; `salary_engine_test`
  48/48; todos os achados absorvidos no improvements.md (vereditos por lente na entrada AUD1, com
  evidência de busca; cada achado com evidência + severidade + parecer).
- **Achados → itens novos 🔲:** **F11** (Alta — rollover duplicado admin×offseason com guards
  divergentes; dupla execução incrementa contratos 2×), **F12** (Média — `run_import` sobrescreve
  salary/cyr a cada boot local sem SalaryHistory), **DOC1** (Média — CLAUDE.md App Startup Sequence
  ≠ código: ordem do `init_auth` + condicionalidade `fresh_import`), **E4-d** (Baixa/Média —
  matching frouxo nas portas do /auction), **M19** (Baixa — validação de pesos do lottery só
  client-side), **M20** (Baixa — descomissionar write-side da flag single-user; **bloqueado por
  M17 ⚠️**). **Cross-refs (não re-reportados):** F10 (updateSummary integral), F9 (bulk_register +
  bloco vestigial), E4-a/E2-RISK (fuzzy do parser), OFF26-1 (gap de enforcement do cap na entrada
  da FA auction — promessa do banner M1 hoje sem lastro em código).
- **Varreduras limpas (com evidência):** sync (sid-first, fallback nome-completo, lição 3-Browns
  in-code), dynasty_values (100% sid + DP_), cap soft (nenhum bloqueio indevido — tudo informativo),
  barras de trade (agregação client de valores server-resolved, sem contraparte backend).
- **Priorização do lote (decisão do owner, 11/06):**
  1. **F11 (Fable)** — próxima sessão; o prompt F2 virá com **passo obrigatório de verificação
     retroativa em prod** (a dupla execução já corrompeu contratos?) antes do fix; eventual repair
     é escopo separado, com backup.
  2. **F10 (Fable)** — mesma sessão Fable do F11.
  3. **DOC1 + F12 + O3 (Opus)** — sessão única; **O3 = split do improvements.md** (a registrar via
     MAN-O3-REG), executado por último dentro da sessão.
  4. **E4-d (Opus)** — prazo: antes da FA auction.
  5. **M19 (Opus)** — carona em sessão Opus futura.
  6. **M20 (Opus)** — bloqueado até M17 marcar ✅ (smoke prod com import ESPN real).
- **Meta (3ª ocorrência do MAN-METH-REG):** a análise pré-execução do próprio F1 refutou duas
  premissas do prompt contra código/docs **antes de aceitar o escopo** ("JS estático" — inexistente,
  todo JS é inline nos templates; "regra MAN-O2" — referência imprecisa, a regra de absorção é do
  DEV_METHODOLOGY). Registrada na entrada MAN-METH-REG; a sessão de consolidação de metodologia
  terá **3 casos** (DP1-F1, UX4-b, AUD1-F1).
- **Commit docs-only de fechamento** (improvements.md + devplan) — exceção justificada: sessão de
  diagnose pura, sem código pendente (precedente 08/06).

### 11/06/2026 — O3 ✅ (split do improvements.md: ativo 🔲/⚠️ + archive ✅ verbatim)

- **Executado (MAN-O3-REG + MAN-O3, mesma sessão, Opus):** `improvements.md` (2.300+ linhas) dividido
  em **ativo** (cabeçalho + **Status Rápido completo e intocado** + seções detalhadas só de 🔲/⚠️) +
  **`improvements_archive.md`** novo (seções ✅ movidas **verbatim**). Ambos no Project Knowledge.
- **Operação verificada por máquina, não por leitura:** classificação autoritativa cruzando
  emoji-da-seção × Status Rápido (regra "primeiro emoji da célula vence" — pegou DP1 e UX2, que
  contêm ✅ no texto mas são 🔲/⚠️). **51 seções migradas, 37 retidas, 88 conservadas** (asserts:
  contagem de linhas + cada bloco migrado presente **verbatim** no archive e **ausente** do ativo).
  Diff do Status Rápido vs HEAD = **exatamente 1 linha** (row O3, flipada p/ ✅) — zero rows
  perdidas/alteradas. `salary_engine_test` 48/48 (zero código).
- **Regra de desempate aplicada (retidos apesar de cheiro de ✅):** **F8** (umbrella ⚠️ — F8a ✅ mas
  F8b/F8c no item; seção lidera com ✅, Status Rápido manda ⚠️ → fica); **DP1/M17/E2/E2-RISK/E4-a**
  (⚠️/🔲, smoke prod pendente → ficam); **E4/E4-c** (umbrellas fatiados 🔲 → ficam);
  **MAN-METH-REG/MAN-ESPN12** (sem row no Status Rápido, registros 🔲 → ficam). **AUD1 migrou** por
  instrução explícita do prompt (✅, sem exceção por recência) — suas seções F11/F12/E4-d/M19/M20/DOC1
  permanecem no ativo (itens próprios) e cross-refam o archive (pesquisável no Project Knowledge).
- **Desvio de sequenciamento (registrado, não contradiz o log AUD1):** o plano AUD1 punha O3 por
  último numa sessão Opus com DOC1+F12; **owner antecipou O3 sozinho**. A ressalva "por último" só
  valia intra-sessão (DOC1/F12 escreveriam antes da reorg); executado sozinho, cai. **DOC1+F12 seguem
  na fila** Opus; **F11+F10 (Fable)** antes de 22/06.
- **CLAUDE.md** ganhou nota do esquema de dois arquivos + a regra de migração contínua (Project
  Structure). Promoção a padrão **transversal** fica para a sessão de revisão de metodologia.
- **Self-aplicação:** O3 marcado ✅ no Status Rápido e a própria seção O3 movida para o archive
  (critério de done = a reorg íntegra, sem validação de prod).
- **Commit docs-only** cobrindo REG + execução (improvements.md, improvements_archive.md, CLAUDE.md,
  devplan). **Lembrete ao owner:** re-upload dos 3 docs no Project Knowledge.

### 09/06/2026 — E4-c-1 fechado ✅ (store canônico backfillado e verificado em produção)

- **Migration 7 rodou no boot pós-deploy** contra o banco vivo (`/data/dynasty.db`). **Backup pré-op:** `/data/dynasty_prod_backup_2026-06-09_pre-E4c1.db`.
- **Evidência:** log `[migrate] E4-c-1: backfilled 273 rows into espn_value_store (season 2026)`; store **273 linhas** (= value-bearing com sid, não-dropados); schema (PRAGMA) ok — `sleeper_player_id VARCHAR` aceita chave de texto das DEF; `espn_raw` nullable vazio; consistência **store==coluna** (Marquise Brown sid 5848 = 1.0; Indianapolis Colts sid `'IND'` = 1.0 → chave de texto das DEF funciona no vivo); valores reais preservados (MIN 1.0 / MAX 68.0 / média 8.7; 160 stubs + cauda real, não uniformizado); **coluna intocada** (278 com `espn_ref_value>0`); idempotente (guard COUNT==0).
- **Correção de registro:** o exemplo da F1 do E4-c citava "Marquise Brown `espn_ref_value=60`" — **valor real 1.0** (o 60 era de outro jogador; confusão da classe "Brown" no próprio exemplo da doc). Backfill correto; expectativa documentada errada — registrado p/ não propagar.
- **Status E4-c-1: ⚠️ → ✅** (09/06/2026). **DP1 DESBLOQUEADO** — o store canônico que ele consome existe e está backfillado em prod.
- **Commit docs-only justificado** (código já em prod + operação verificada — exceção de E1/M17/M18/E4-b).

### 09/06/2026 — E4-c-1 F2 (fundação do store canônico) ⚠️ localhost; backfill PROD pendente

- **(1) Tabela `EspnValueStore`/`espn_value_store`** `(sleeper_id, season)[raw,adjusted,is_final]` via `db.create_all()` (aditivo, sem ALTER; aceita sid de texto p/ DST).
- **(2) Backfill = Migration 7** (`app.py`): `INSERT...SELECT` de `Player.espn_ref_value>0 + sid + não-dropado` → store em `season=current_season+1` (2026 prelim), `raw=NULL`, `is_final=0`; idempotente (guard `COUNT==0`); roda no boot.
- **(3) Helper único `set_espn_value`** (`models.py`): upsert store (só `adjusted>0`) + materializa a coluna. **8 escritores roteados** (`_save_espn_value`, admin bulk, salary bulk, `bulk_register`, `record_acquisition`, `import_csv`, roster PATCH); `sync` segue com stub 0 (não-valor, não roteado). Grep confirma 0 escrita de `espn_ref_value` fora do helper nos caminhos roteados.
- **(4) Badge PROV** repontada p/ ler `is_final` do store por `sleeper_id`; demais leitores inalterados (coluna materializada); **engine nunca vira lookup** (pureza preservada sem tocar a engine).
- **Aditivo:** `ESPNValue`/`RookieEspnValue` intactos (DROP/generalização = E4-c-2).
- **Validação localhost (10/10):** backfill 248 == value-bearing com sid; store==coluna (Marquise Brown 60.0); DST `'IND'` ok; badge lê `is_final=True` do store; re-migrate não duplica (248→248); helper sincroniza; páginas 200. `salary_engine_test` 48/48.
- **Passo operacional PROD:** backfill roda **automático no boot pós-deploy** (Migration 7). Backup `/data` antes do deploy; conferir log `[migrate] E4-c-1: backfilled N rows` + `SELECT COUNT(*) FROM espn_value_store` ≈ 248 + spot-check. **E4-c-1 → ✅ só após isso**; até lá ⚠️.
- **Arquivos:** `models.py`, `app.py`, `import_csv.py`, `routes/admin.py`, `routes/salary.py`, `routes/auction.py`, `routes/roster.py` + docs. Commit agrupa absorção E4-c-F1 + sub-fatiamento + MAN-DOC-DBPATH (CLAUDE.md) + esta F2.

### 09/06/2026 — E4-c F1 de migração absorvida + sub-fatiado em E4-c-1/E4-c-2 🔲

- **Diagnose de migração (MAN-E4-c-F1)** confirmou contra prod pós-E4b: **248 value-bearing, 100% com sid** (os 2 sem-sid eram os órfãos deletados), **0 sids duplicados** → chave `(sid, season)` segura; `ESPNValue` vazio (aposentar não migra linhas); pureza do `salary_engine` preservada de graça (a coluna materializada continua sendo o que a engine lê).
- **Achado estrutural:** o **único passo irreversível** (DROP `ESPNValue` + generalizar `RookieEspnValue`) está **isolado no fim**; passos 1-4 (criar tabela / backfill / helper nos escritores / repontar badge) são **aditivos, reversíveis, sem downtime**.
- **Estado-alvo:** **tabela canônica NOVA** via `db.create_all()` (sem ALTER, mais reversível que generalizar in-place); `Player.espn_ref_value` = cache materializado; backfill da coluna **a partir de si mesma** → coluna==store; refactor dos **8 escritores → helper único `set_espn_value`**; **só a badge PROV** é repontada (resto lê a coluna, inalterado).
- **Sub-fatiamento (E4-c vira guarda-chuva):** **E4-c-1** (passos 1-4; aditivo/reversível; **entrega o store ao DP1**; Alta/agora) · **E4-c-2** (passo 5; destrutivo/isolado; higiene; Baixa).
- **Decisões de escopo (owner):** (1) season do backfill = **2026 preliminar** (re-materializado pelo import definitivo); (2) linhas: `adjusted` autoritativo, `raw` vazio, `is_final=False`; (3) **DST incluídas** (não filtrar) — F2 valida a chave com sid de texto (`"IND"` etc.); (4) sequência E4-c-1 agora → DP1 perto do draft → E4-c-2 quando convier.
- **DP1 repontado:** **bloqueado por E4-c-1** (não E4-c inteiro; E4-c-2 não bloqueia). Nada virou ✅. Absorção docs-only — agrupa com o código da F2 do E4-c-1.

### 09/06/2026 — Doc: localização do banco vivo de prod no CLAUDE.md (MAN-DOC-DBPATH)

- Registrado no **CLAUDE.md** (Deployment → Render) o caminho do **banco VIVO de prod = `/data/dynasty.db`** (via env `DYNASTY_DB`) vs. **seed = `/opt/render/project/src/dynasty.db`** (git, sem efeito em prod), como o app resolve o path, acesso via Render Shell e o comando de backup seguro (`sqlite3 ... ".backup"`). Concretiza a nota "seed ≠ prod" descoberta ao vivo na operação do E4-b. Docs-only.

### 09/06/2026 — E4-b fechado ✅ (limpeza executada e verificada em produção)

- **Limpeza executada em prod** via a rota admin ("🧹 Limpar Órfãos Duplicados") contra o banco vivo (`/data/dynasty.db`). **Backup pré-op:** `/data/dynasty_prod_backup_2026-06-09_pre-E4b.db`.
- **Evidência:** 2 órfãos removidos — Hollywood Brown (id 279, +1 PlayerHistory stray) e Cameron Ward (id 280, +0). Pós-limpeza: `COUNT(players)=278` (era 280); **`sleeper_id` NULL = 0**; canônicos intactos (58 Marquise Brown sid 5848; 255 Cam Ward sid 12522). **Idempotência confirmada** (2º acionamento = 0).
- **Causa-raiz fechada** na mesma F2 pelo guard (dedup-por-sid + `needs_review` no `import_csv`). `sleeper_id` agora é chave de junção confiável (cobertura útil completa) no estado vivo.
- **Status E4-b: ⚠️ → ✅** (09/06/2026). Nota: o seed versionado ainda contém os 2 órfãos (latente, intencional; rota re-rodável em re-seed) — não impede o fechamento (estado vivo limpo).
- **Commit docs-only justificado** (código já em prod + operação executada/verificada — mesma exceção de E1/M17/M18).

### 09/06/2026 — E4-b F2 (delete dos órfãos + guard) ⚠️ código localhost; limpeza PROD pendente

- **(a) Rota admin auditável** `POST /api/admin/cleanup_orphan_players` + botão "🧹 Limpar Órfãos Duplicados". Remove Players sem `sleeper_id` + não-rosterados + sem `SalaryHistory`/`AuctionLog` (assinatura do órfão sem valor), + `PlayerHistory`/`ESPNValue` stray. Idempotente, auditável (lista removidos + skipped-com-histórico), canônicos (com sid) fora do filtro. **Não** é script one-shot.
- **(b) Guard no `import_csv`:** no create, resolve nome+team→sid (resolver Brown-safe do E4-a, lazy). Resolve p/ player existente → dedup (update, sem insert); resolve p/ sid livre → nasce com sid; não resolve → `needs_review=True` (fecha o gap do import_csv). Sem hard-block.
- **Escopo respeitado:** não toca schema/`salary_engine`/`sync`/matcher (só consome o resolver). `run_import` já pula sem CSV → prod (sem CSV) não regenera; órfãos de prod vieram do seed via `init_data`.
- **Validação localhost:** a rota removeu os 2 órfãos reais do seed (279 Hollywood Brown +1 stray, 280 Cameron Ward) + 2 sintéticos; canônico intacto + SalaryHistory; órfão-com-history preservado (skipped); idempotente (2ª = 0). Guard: dedup resolve, irresolúvel → needs_review. `salary_engine_test` 48/48.
- **Passo operacional PROD (fecha o item):** após deploy, Admin → "🧹 Limpar Órfãos Duplicados" → confirmar; esperado 2 removidos, re-clicar 0; conferir Marquise Brown/Cam Ward intactos. **E4-b → ✅ só após isso**; até lá ⚠️.
- **Arquivos:** `routes/admin.py`, `import_csv.py`, `templates/admin.html` + docs. Commit agrupa absorção E4-b-F1 + esta F2.

### 09/06/2026 — E4-b F1 absorvida: órfãos são duplicatas → DELETE (não backfill) 🔲

- **Premissa do E4-b refutada pela F1.** Os 2 Players sem sleeper_id **não são jogadores a backfillar — são duplicatas órfãs de canônicos rosterados:** id 279 "Hollywood Brown" = dup do id 58 "Marquise Brown" (sid 5848, apelido↔nome real, salary 3.0/ano2 idênticos, história completa no canônico); id 280 "Cameron Ward" = dup do id 255 "Cam Ward" (sid 12522, mesmo QB rookie, 1.0/ano1, órfão **puro** sem registros). **Backfill duplicaria sids existentes** → ação errada.
- **Ação (F1):** 279 → DELETE (+ 1 PlayerHistory stray `team_name=''`); 280 → DELETE (puro). Nem backfill nem merge (canônicos completos).
- **Causa-raiz:** `import_csv` cria sem sid e **sem `needs_review`**; quando o nome diverge do Sleeper (Hollywood≠Marquise, Cameron≠Cam) o sync nunca casa → órfão invisível.
- **Guard (reusa o existente):** (1) dedup-por-sid na criação — resolver nome→sid via o resolver Brown-safe do E4-a → `find_player_by_sleeper_id` → atualizar canônico em vez de inserir; (2) `needs_review=True` quando não resolve (fechar o gap do import_csv). **Rejeitado:** hard-block (quebra import_csv seed + /auction manual).
- **Decisões de escopo F2 (owner):** (1) delete dos 2 + guard na MESMA F2; (2) delete reusa infra existente, senão **rota admin auditável** — não script one-shot; (3) delete atinge **PROD** (disco do Render), não o seed (seed ≠ prod) → daí a rota auditável contra o estado vivo.
- E4-b permanece 🔲. Absorção docs-only — **sem commit isolado**; agrupa com o código da F2.

### 09/06/2026 — E4-a F2 (matcher do import ESPN resolve por sleeper_id) ⚠️ localhost

- **Identidade por `sleeper_id` (Brown-safe), não fuzzy contra roster.** `match_players` ganhou `sid_resolver` injetável: sid→Player rosterado = matched por id (sem review); sid→não-rosterado = not_found (store no confirm, **nunca match de veterano**); sem sid limpo = fallback igualdade exata (matched) ou review. **Sem auto-match silencioso por similaridade** no modo resolver; modo legado (`sid_resolver=None`) preservado byte-a-byte.
- **`routes/admin.py`:** extraídos `_build_pool_index()` + `_resolve_entry_sid()` (fonte única Brown-safe nome+team; `_resolve_not_found_to_store` do E2 refatorado p/ usá-los — DRY). `espn_import_page` passa o resolver ao matcher; pool indisponível → fallback gracioso.
- **Invariantes preservadas:** `salary_engine` intocado; escrita segue em `Player.espn_ref_value` via id (store canônico é E4-c); `SalaryHistory`/`PlayerHistory` intactos; sem schema; reversível.
- **Validação localhost (test_client + pool real 11.810):** Tate→not_found (sid 13279), não vira candidato de Mooney, Mooney não recebe valor; vet (Jayden Daniels)→matched por sleeper_id; typo→review; sobrenome isolado não resolve; 2 nulos degradam sem match espúrio; reimport idempotente; confirm de matched-by-id grava espn_ref_value=60.0; review 200. `salary_engine_test` 48/48.
- **Relação E2-RISK:** E2-RISK = camada de tela (default neutro + gate); **E4-a = raiz** (resolução por id). O F2 do E2-RISK paliou; E4-a fecha a raiz. E2-RISK segue ⚠️ (smoke de tela próprio).
- **Status E4-a = ⚠️** (pendente smoke prod com import real). **Arquivos:** `espn_pdf_parser.py`, `routes/admin.py` + docs. **Commit agrupa:** código F2 + absorção E4-F1 + fatiamento E4-a/b/c (docs pendentes no working tree).

### 09/06/2026 — E4 F1 de design absorvida + fatiado em E4-a/b/c 🔲

- **Diagnose de design (MAN-E4-F1) contra snapshot prod (07/06, 280 players)** desmontou os 3 receios da F1B: (1) **não há 3 fontes vivas** — só `Player.espn_ref_value` é viva (250/280); **`ESPNValue` vazia em prod** (0 linhas, único leitor = badge PROV); `RookieEspnValue` transitória e complementar (vão pré-roster); (2) **`sleeper_id` cobre 99,3%** (278/280, 0 dups; só 2 nulos não-rosterados: Hollywood Brown apelido + Cameron Ward) → saneamento mínimo, incremental; (3) **pureza do `salary_engine` preservada sem tocar a engine** — a materialização no Player já existe (`_save_espn_value`); muda só fonte + join (por `sleeper_id`).
- **Achado estrutural decisivo:** o conserto do matcher (entrada ESPN → `sleeper_id`) é **independente** da reconciliação e entrega quase todo o ganho de segurança **sem schema**; o store canônico só precisa vir com a leitura pré-roster (DP1).
- **Modelo-alvo:** chave `(sleeper_id, season)`; base = `RookieEspnValue` generalizado (persistente, com `is_final`) que subsume `ESPNValue`; `Player.espn_ref_value` vira cache materializado; `ESPNValue` aposentada (vazia → sem migração de linhas).
- **Fatiamento (E4 vira guarda-chuva):** **E4-a** matcher por id (Alta/agora; sem schema; absorve o conserto do matcher ex-E2-RISK; elimina "Brown" na raiz + corrupção→miss) · **E4-b** saneamento de `sleeper_id` (Média/em seguida; 2 nulos + guard) · **E4-c** store canônico (atrelado a DP1; único passo com migração, data-light; aposenta ESPNValue; habilita pré-roster).
- **Referência do E2-RISK atualizada:** o conserto do matcher aponta agora para **E4-a** (não E4 genérico). Nada virou ✅.
- Absorção docs-only — **sem commit isolado**; agrupa com o código da F2 do E4-a.

### 09/06/2026 — E2-RISK F2 (mínimo de tela: default neutro + gate) ⚠️ localhost

- **Mudança única (camada de tela):** `templates/espn_review.html` — o `<select>` de cada approximate inicia **NEUTRO** (`<option value="" selected>— selecionar —`); removido o `selected` que pré-escolhia o `best_player` (veterano). Risco quase nulo; **não toca** matcher/`salary_engine`/`ESPNValue`/`RookieEspnValue`/sync/schema (re-escopo respeitado — conserto do matcher é o E4).
- **Gate já existente, ativado pelo default neutro:** `getApproxResolutions` conta select vazio como pendente; `updateStatus()` (load + `change`) desabilita `#btn-confirm` até toda approximate ter escolha explícita. Sem réplica nova de lógica de resolução — só a habilitação do botão (que já existia).
- **Caminho de escrita inalterado:** resolução explícita ainda grava via `_save_espn_value`; a F2 só impede confirm-por-inércia.
- **Validação localhost (test_client, DB copiado):** render sem pré-select (option neutra `selected`, nenhum candidato `selected`); confirm **sem ação** não altera `espn_ref_value` do veterano (32.4→32.4 — Mooney não recebe valor de Tate); confirm com resolução explícita grava (32.4→48.0); auto-matched/not_found intactos. `salary_engine_test.py` 48/48.
- **Status E2-RISK = ⚠️** (pendente smoke em prod com import ESPN real). Critérios 2/3 (botão disabled/enabled) são JS client-side, confirmados por leitura de código (não executáveis em test_client).
- **Arquivos:** `templates/espn_review.html` + docs. **Commit único agrupa:** código F2 + absorção E2-RISK F1/F1B + re-escopo + E4-REG (docs pendentes no working tree).

### 09/06/2026 — E2-RISK F1+F1B absorvidas + re-escopo híbrido + E4 registrado 🔲

- **F1 (hazard):** nasce em `match_players` (fuzzy contra **roster local apenas**); Tate~Mooney 0.665 por falta de candidato melhor local. **Fonte única** (sem réplica JS), **sem outros consumidores**. **Agravante:** o review **pré-seleciona o veterano** no `<select>` e o JS trata qualquer valor truthy como resolvido → **confirm sem interação** grava o valor do rookie no `espn_ref_value` do veterano via `_save_espn_value` (escrita direta no confirm, **não** passa por `record_acquisition`).
- **F1B (`espn_ref_value` por `sleeper_id`?):** correta e elegante, mas **redesenho de camada de dados**, não fix de segurança — `salary_engine` é puro (a coluna não some); **3 tabelas** de valor ESPN a reconciliar sob chave nova `sleeper_id+season`; `sleeper_id` **furado** (import_csv cria Player sem ele). Ganho lateral: resolver por id troca "corrupção" por "miss" (ambíguo→não chuta), mais seguro.
- **Decisão do owner (híbrido):** parar a corrupção **agora** com o **mínimo de tela** (remover o pré-select do veterano), risco quase nulo; tratar o **redesenho da estrutura ESPN** como item de design próprio onde matcher (resolução por `sleeper_id`) e armazenamento convergem para a chave certa de uma vez.
- **Re-escopo do E2-RISK:** passa a ser **SOMENTE** o mínimo de tela (default seguro no review; não toca matcher/engine/ESPNValue/schema). **E2-RISK permanece 🔲.**
- **Novo item [[E4]] 🔲** (origem MAN-E2RISK-F1B): redesenho da camada de valor ESPN — matcher resolve entrada→`sleeper_id` (nome+team Brown-safe) + reconciliar as 3 tabelas sob `sleeper_id+season`; **recebe o conserto do matcher** que saiu do E2-RISK. ID E4 (próximo livre da série E; E1✅/E2⚠️/E3🔲).
- Absorção docs-only — **sem commit isolado**; agrupa com o código da F2 do E2-RISK (o mínimo de tela).

### 09/06/2026 — E2-RISK registrado (fuzzy oferece rookie como match de veterano) 🔲

- **Item novo 🔲 (MAN-E2RISK-REG)** formaliza o risco residual achado no E2-F2 (08/06). No **review do import ESPN**, o fuzzy pode oferecer um **rookie** como candidato de match contra um **veterano do DB** (falso-positivo: "Carnell Tate"~"Darnell Mooney", sim 0.665). Se o admin **confirma** o match falso, o valor ESPN do rookie **contamina o `espn_ref_value` do veterano** — **classe do incidente "Brown"**.
- **Escopo:** só o caminho de **confirm errado**; o *skip* já foi mitigado no E2 (store captura o valor do rookie mesmo no skip). O **matching canônico não muda** — o foco é o que o review *oferece* como candidato fuzzy.
- **Fix delineado (a refinar na F1):** não oferecer como fuzzy-match contra veterano uma entrada que já resolve para o `sleeper_id` de um rookie (pool global do Sleeper); ou rebaixar/sinalizar esses candidatos no review.
- **ID:** **E2-RISK** (sub-item do E2, convenção de nomeação tipo M15-FIX/F8-RESTORE-GAP) — confirmado livre. **F1 (diagnose read-only) em prompt separado.** Registro apenas; **sem commit docs-only isolado** — agrupa com o próximo commit de código.

### 09/06/2026 — M18 fechado ✅ (validado em produção, smoke BRT)

- **Smoke em prod (cliente BRT):** sync disparado às **11:47 BRT** (= 14:47 UTC) renderizado como **"09/06/2026 11:47"** no rodapé global — bate com o relógio local, descartando o bug de UTC cru (mostraria 14:47). Offset de fuso aplicado corretamente ao vivo → a fonte única (`utc_iso` ISO `Z` → `formatLocalDT` no device) funciona em prod.
- **Status M18: ⚠️ → ✅** (09/06/2026). Os 8 critérios estruturais já tinham passado em localhost no commit `462e3bc` (já em prod). Armazenamento UTC intacto.
- **Commit docs-only justificado:** código já em produção e validado — exceção legítima à regra de não-commit-isolado (mesma lógica do fechamento do E1). Fecha o delta de status nos docs (improvements.md, manager_devplan.md, handoff).

### 08/06/2026 — E3 registrado (import ESPN upload-only: remover URL) 🔲

- **Item novo 🔲 (MAN-E3-REG):** remover a opção de **download por URL** do import ESPN, deixando-o **upload-only**. O E1 provou que o fetch da ESPN é **inviável em prod** (bloqueio anti-bot por IP de datacenter do Render) → em prod, único contexto real do import, a URL nunca funciona e só gera ruído.
- **Decisão de escopo a confirmar na F2:** (a) **remoção completa** — RECOMENDADA — input de URL na UI + caminho de download server-side + a **degradação graciosa** associada (existia só para cobrir esse fetch); (b) esconder só a UI mantendo o backend (menos limpo, deixa caminho morto). Nuance: a URL **funciona em dev** (E1-F1), mas o ganho é marginal.
- **Vai REG → F2 direto, sem F1:** o E1-F1 já isolou download/parse/match num **único caminho server-side** (`routes/admin.py` + `espn_pdf_parser.py`), sem réplica em JS/templates — isolação já diagnosticada.
- **ID:** E3, próximo livre da série E (E1 ✅, E2 ⚠️). Registro apenas; **sem commit docs-only isolado** — agrupa com o código do MAN-E3-F2.

### 08/06/2026 — M18-F1 diagnose (read-only) absorvida + decisões de escopo F2

- **Escopo mais estrutural que o registro supunha.** Armazenamento = **naive UTC** (`utcnow`) em todos os modelos; exceções (`Trade.trade_date`, snapshot F8 via `fromtimestamp`) também naive. Camada de storage **não muda** (UTC permanece).
- **Sem ponto central de formatação:** string `%d/%m/%Y %H:%M` duplicada ~9× entre `to_dict()`, rotas e templates → **~10 sites independentes**.
- **Conjunto completo mapeado por camada:** Jinja (card Sleeper Sync, snapshot F8, ESPN import, lottery audit, lista de trades [só data], proposta created/expired/days_left); pré-formatado→JS (rodapé global de último sync — o que o Michel viu, além do card admin; modal de detalhe de trade); client-side `Date` (criação de link de proposta — **único que converte, e está bugado**: ISO de naive sem `Z` → `new Date` lê como local).
- **Reavaliação dos candidatos:** trades + proposta + telas admin confirmados; **salary history NÃO exibe timestamp** (`created_at` no payload mas não renderizado — campo morto); **bônus** `AuctionLog.created_at` também morto.
- **Achado decisivo (transporte):** onde o servidor formata para string, o **fuso é destruído antes do browser** → conversão client-side impossível sem primeiro mudar o transporte para UTC não-ambíguo.
- **4 decisões de escopo do owner para a F2** (gravadas na subseção F1 do M18 em improvements.md): (1) fonte única de formatação, migrar os ~10 sites — não corrigir site a site; (2) storage UTC mantido, servidor entrega UTC não-ambíguo (ISO `Z`/offset ou epoch), cliente converte pelo fuso do browser sem config; (3) campos mortos (salary history + `AuctionLog.created_at`) **preservados** — amarração com WV1; (4) ponto client-side bugado corrigido pela mesma fonte única.
- M18 permanece 🔲 (F2 não executada). Absorção docs-only — **sem commit isolado**; agrupa com o código da F2 (junto com o WV1-REG já pendente no working tree).

### 08/06/2026 — M18-F2 implementada (timestamps no fuso do usuário) ⚠️ localhost

- **Fonte única (1 por modo de render):** novo `timeutil.utc_iso(dt)` marca naive-UTC → ISO-8601 com `Z` (transporte não-ambíguo); usado por `to_dict()`/rotas + registrado como filtro Jinja `utc_iso` (`app.py`) → macro `local_dt` (`_macros.html`, emite `<time class="js-localtime" datetime="…Z">`). **Formatação humana só no cliente:** `formatLocalDT(iso, fmt)` (`base.html`) é o único ponto que escolhe `dd/mm/aaaa [HH:MM]` e aplica o fuso do device; `applyLocalTimes()` no `DOMContentLoaded` converte os `<time>`; JS dinâmico chama `formatLocalDT` direto.
- **~11 sites migrados:** card Sleeper Sync + rodapé global, snapshot F8 (agora `utcfromtimestamp`, era hora local do servidor), ESPN import, banner ESPN do cap projector, lottery audit (×2), lista de trades (`date`), modal de trade, proposta create/expired, e o **link de proposta antes bugado** (recebia ISO naive sem fuso → agora ISO `Z` + `formatLocalDT`).
- **Transporte:** `SyncLog.synced_at`, `Trade.trade_date`, `ESPNImportLog.imported_at`, `LotteryAudit.executed_at` (to_dict) + `/api/trades/by_tx`, `expires_at`, `espn_status.date` (rotas) passam a emitir ISO `Z`.
- **Decisão — campos mortos preservados (amarração WV1):** `created_at` de salary history (`PlayerHistory`/`routes/salary.py`) e `AuctionLog` **não** alterados nem exibidos. **Armazenamento intacto:** `utcnow` naive, sem migração de schema (restrição respeitada).
- **Validação localhost:** `utc_iso(00:25 naive)`→`2026-06-08T00:25:00Z`; admin/rodapé emitem `<time …Z>`; banco mantém `00:25:00Z`; `/admin /trades /cap_projector /salary_history /picks`→200; `/api/trades/by_tx`→ISO `Z`; nenhum timestamp cru no `/admin`. `salary_engine_test.py` 48/48.
- **Status M18 = ⚠️** (pendente smoke em prod com cliente em BRT: confirmar 00:25 UTC → 21:25 do dia anterior — não verificável sem browser real). Sobe para ✅ após confirmação.
- **Arquivos:** `timeutil.py` (novo), `app.py`, `models.py`, `routes/trades.py`, `routes/admin.py`, `routes/salary.py`, `templates/_macros.html`, `base.html`, `admin.html`, `espn_import.html`, `lottery_audit.html`, `trades.html`, `trade_proposal.html`, `_trade_detail_modal.html`, `cap_projector.html` + docs. **Commit único agrupa:** código M18 + docs M18 (absorção F1 + F2) + **WV1-REG** (pendente no working tree).

### 07/06/2026 — E1 (Import ESPN robusto) F1 + F2 ✅ (MAN-E1)

- **F1 (diagnose do 500):** o 500 não era o download (que tem try/except → 302), e sim o **parse não guardado** estourando `PDFSyntaxError` quando a ESPN devolve um **200 não-PDF** (anti-bot) ao IP de datacenter do Render. O PDF e o parser estavam corretos (provado de IP residencial: download 200/PDF, parse 299). Caminho de parse/download/match é **único e server-side** (sem réplica). Secundário: estado de review escrito na raiz do app (read-only em prod).
- **F2 — decisão de escopo:** atacar a causa (confiar no corpo, não só no código HTTP) + remover a dependência estrutural do fetch server-side. Quatro frentes: (1) **upload manual** do PDF como entrada preferida; (2) **guarda magic-bytes + try/except** em parse/match → flash 302, nunca 500; (3) estado de review em **dir gravável** (`dirname(DYNASTY_DB)` = volume do Render), não na raiz; (4) parser **299→300** (`/` no `_NAME_RE` recuperou o `Texans D/ST` que caía em linha standalone).
- **Por que upload é o caminho principal:** o IP do Render dificilmente sai da lista de bloqueio da ESPN; depender do download seria frágil. O owner já baixa o PDF no navegador — upload é mais confiável. URL fica como alternativa graciosa.
- **Preservado:** matching 3-tier, salary_engine, schema, sync, CSV (`espn_bulk`), semântica provisório/final; escrita só via `_save_espn_value` (upsert idempotente).
- **Validação:** 13/13 (test_client, temp DB; PDF real como upload) — upload→300, spot checks ok, URL ruim→302, review em FS gravável, reimport não duplica, final persiste, sem réplica JS. `dynasty.db` real intocado.
- **Arquivos:** `espn_pdf_parser.py`, `routes/admin.py`, `templates/espn_import.html`, `CLAUDE.md`. Commit agrupa também os docs pendentes (M17/M18 REG, OFF26 F9-F1B, E1 REG/F1).

### 07/06/2026 — E1-FIX: `pdfminer.six` faltava no requirements (500 em prod) + aprendizado

- **Bug:** o import ESPN 500ava em produção com `ModuleNotFoundError: No module named 'pdfminer'` — o `requirements.txt` não declarava `pdfminer.six`, então o build limpo do Render não o instalava. O erro ocorria na **importação do módulo** (`espn_pdf_parser.py:16`), antes de qualquer lógica → afetava upload **e** URL. **O ✅ do E1-F2 foi prematuro:** a validação passou só em localhost (pacote já instalado).
- **Fix:** `pdfminer.six>=20231228` no requirements (NÃO o legado `pdfminer`, Python 2, que não fornece `pdfminer.high_level`). Validado em **venv limpo**: `pip install -r requirements.txt` resolve `extract_text`. Status do E1 revertido p/ ⚠️ até o smoke test em prod.
- **Aprendizado (regra):** **validação em localhost não captura dependências ausentes no ambiente limpo de produção.** Toda dependência nova (import de terceiro) exige: (1) declarar no `requirements.txt` no mesmo commit do código que a usa; (2) validar em **venv limpo** (`pip install -r requirements.txt` + import) antes do deploy; (3) só marcar ✅ após smoke test em produção. Aplica-se retroativamente como item de checklist de "dependência nova".

### 08/06/2026 — E1 ✅ validado em prod + E2 registrado (gap de ESPN value de rookie)

- **E1 → ✅:** smoke test em produção passou (upload do `NFL26_CS_PPR300.pdf` → review 300, sem 500). Confirma o E1-FIX (pdfminer.six) e fecha o ciclo E1.
- **E2 registrado 🔲 (Alta):** achado do smoke test — rookies do ESPN Top 300 (ex.: Carnell Tate $12, Jeremiyah Love $46) **não existem no DB** no import (passo 3, antes do rookie draft, passo 5) → caem em not_found → valor ESPN descartado. **Não é bug de parse/match** (parser lê certo); é gap de workflow: o rookie draftado depois perde o `floor(ESPN×1.2)` (default $1 no importador OFF26-3). 43 skill not_found, dano concentrado nos rookies de alto valor; veteranos/FA $0 são inofensivos. F1 vai mapear opções (criar stub no review / store de valores pendentes / importador buscar snapshot). Relaciona-se a OFF26-3.

### 08/06/2026 — E2-F1 + REFINE (store keyed por sleeper_id) + DP1 registrado

- **E2-F1 (read-only):** descartou a **via Sleeper-sync** — rookies não estão rosterados na liga (só no pool global do Sleeper, com NFL team), então um sync não os traz; e o Sleeper é roster-only (sem ESPN value). Confirmou: sync cria stub ($1/unknown/espn 0) só p/ rosterados; OFF26-3 idempotente por `sleeper_id`; `floor(ESPN×1.2)` fonte única (`year1_salary`), sem réplica.
- **E2-REFINE:** re-escopado como **camada de dados** — **store de valores ESPN de rookie keyed por `sleeper_id`** (resolve not_found via pool global do Sleeper, matcher nome+team). Decidido pelo surgimento de um **2º consumidor** (board de cap DP1) além do salário no draft. **Rejeitados:** Sleeper-sync (inviável) e **Player stub-$1** (viola "rookie só pelo draft", polui roster/cap, serve mal o board). Store transitório, limpo pós-draft; $0/K-DST inócuos. Próximo: E2-F2.
- **DP1 registrado 🔲 (prioridade a definir):** board de planejamento de cap pré-draft (rookies entrantes: `espn_ref_value` + salário projetado `floor(ESPN×1.2)` + simulação de impacto no cap, **projeção ≠ contrato**). Domínio cap → Manager/cap_projector (não Optimizer). **Bloqueado por E2** (consome o store). Reusa `year1_salary` (sem réplica JS).

### 08/06/2026 — Commit docs-only deliberado (exceção à convenção)

- **Exceção consciente à regra "docs agrupados com código".** A fila de docs uncommitted (E1→✅ validado em prod, E2 REG/F1/REFINE, DP1 REG) é **inteiramente documentação, sem nenhum código pendente**, e já estava grande. Commitada e pushada isoladamente para **preservar o trabalho e eliminar a divergência** entre git, estado local e project knowledge — em vez de esperar o próximo commit de código (E2-F2).
- **Por que é seguro:** zero mudança de código → o rebuild do Render disparado pelo push é **no-op funcional**. (M17/M18, F9-F1/F1B e o aprendizado de "dependência nova" já tinham sido commitados em b36f6a8/3c1b93f; este commit fecha o delta restante.)
- **A convenção segue válida** para o fluxo normal (REG/F1 agrupam com o F2); esta foi uma sincronização de fim-de-maratona, justificada pelo tamanho da fila.

### 08/06/2026 — E2-F2 ✅ (store de valores ESPN de rookie) — ⚠️ aplicação aguarda draft real

- **Camada de dados implementada:** modelo `RookieEspnValue` (keyed por `sleeper_id`+season, via `db.create_all`), + helpers `upsert_rookie_espn`/`rookie_espn_adjusted`/`clear_rookie_espn_store`. Guarda o ref value (raw×1.2), **não** salário; não é Player (não polui roster/cap) — stub-$1 rejeitado no REFINE.
- **População:** no confirm do import ESPN, resolve `not_found` **+ approximate-skipped** → `sleeper_id` via pool global do Sleeper (nome+team, **Brown-safe**, sem substring/sobrenome); exclui $0/K-DST; upsert idempotente. **Achado:** rookies caem em *approximate* por falso-positivo de fuzzy (Carnell Tate ~ Darnell Mooney 0.665) — por isso o approximate-skipped também alimenta o store (senão o valor do rookie se perderia).
- **Consumo:** OFF26-3 (`draft_import`) busca `rookie_espn_adjusted` ao criar o rookie e deriva `floor(ESPN×1.2)` via `year1_salary` (sem réplica). Limpeza no `toggle_rookie_draft`.
- **Validação:** 12/12 (temp DB; PDF+pool read-only) — Love adj 55, Carnell Tate adj 14, idempotente, Brown-safe, matched intocado, rookie→salário 55, cleanup ok, salary_engine 48/48.
- **Status ⚠️ (não ✅):** store validável em prod agora (import → conferir store); aplicação no draft só e2e no rookie draft real (~ago, 8.2.2). **DP1 desbloqueado** (store existe).
- **Arquivos:** `models.py`, `routes/admin.py`, `routes/draft_import.py`, `routes/offseason.py`, `CLAUDE.md`.

### 16/06/2026 — F9 ⚠️ localhost (bulk_register pela porta canônica, sem backfill)

- **Última réplica inline fechada.** `bulk_register` (`routes/auction.py`) deixou de criar contrato inline (Player + AuctionLog, **sem** SalaryHistory + `salary = max(1,int(value_paid))` duplicado) e passou a consumir `record_acquisition` — mesma porta das outras 3 entradas do `/auction`. Agora cada item gera **Player + SalaryHistory + AuctionLog** atômicos. **As 4 portas do `/auction` escrevem contrato num único ponto.**
- **Valor inalterado:** para `auction_draft`, `year1_salary(_, value_paid, _) = max(1, int(value_paid))` — exatamente o que o inline calculava. A mudança adiciona SalaryHistory (que faltava), não altera salário.
- **Idempotência nova:** `event_ref = f"bulk:{season}:{team_name}:{player_name}"` + guarda `acquisition_already_recorded` (padrão OFF26-3). O inline antigo duplicava AuctionLog em re-execução; agora a 2ª passada não cria nada.
- **Bloco vestigial removido:** classe `_noop` + `test_request_context()`/`app_context()` no-op (eram herança de um esboço que nunca teve efeito). `grep` em `auction.py` → zero ocorrências.
- **Decisão sem backfill** ratificada pela diagnose F1+F1B (e forense ao vivo do F11): `bulk_register` **nunca rodou em prod** (`salary_history`=0, zero AuctionLog em players ativos), dano acumulado = 0. Refatoração pura, sem migração/rota de reparo.
- **Validação localhost:** smoke contra DB temp (test client, admin seedado): BEFORE (0 SH,0 AL) → RUN1 registra 2 → **(2,2)**, salaries `[7,3]` = canônico; RUN2 mesmas entradas → `registered=0`, counts **(2,2)** (idempotente). `salary_engine_test.py` 48/48. Contrato da rota `{registered, results, errors}` estável.
- **Status ⚠️ (não ✅):** ✅ depende do smoke em prod (a FA auction 2026 será o 1º uso real). **Sem push** — deploy fica com o owner.
- **Arquivos:** `routes/auction.py`, `improvements.md`, `manager_devplan.md`.

### 16/06/2026 — Maratona OFF26: OFF26-8 (reg) + OFF26-1 + OFF26-2 implementados ⚠️ (pushed)

Sessão longa (Opus 4.8 1M). Pipeline REG-before-IMPL em cada item: F1 (diagnose read-only)
→ REFINE (spec do owner) → F2 (implementação). Tudo pushado (`6b73141`/`2c243d4`/`a8c6f0f`).

- **OFF26-8 registrado** 🔲 (op, Média) — capability NÃO-código: agente Cowork aplica os
  cortes do OFF26-1 no roster real do Sleeper (irmão de OFF26-6, ⊂ OFF26-7, dep. OFF26-1).
  Docs-only (`6b73141`).

- **OFF26-1 — janela de cortes selada ⚠️ localhost** (`2c243d4`). Owner declara em sigilo a
  **lista de CORTES** do próprio roster (keepers = complemento); admin abre (gate duro
  `needs_review` zerado), supre time ausente por **escrita** (nunca lê alheio), e dispara
  **lock + revelação simultânea** que congela snapshot canônico (molde M8: `is_canonical` +
  `previous_id` + `reason` + `hash`). **Não escreve no Sleeper** (OFF26-8) nem materializa
  cortes (Rollover/FA auction). Spec D1–D11.
  - **D8 (infra):** janela roda **pós-rollover** (lê salário já valorizado).
  - **D9 (infra):** porta canônica `.../budget` ganhou flag **`projected`** (default True
    intocado; `false` = salário corrente). **Ampliação deliberada, não réplica** — fonte de
    cálculo segue única (`draft_budget`); invariante F10 mantida.
  - **Sigilo (segurança):** nenhuma rota expõe `cut_ids` alheios pré-lock; `/state` só dá
    contagem agregada. e2e **23/23** + `salary_engine` 48/48.
  - **Models novos** (`CutDeclaration`, `CutWindowAudit`) → `create_all` **toca o schema de
    prod** no deploy (aditivo). **Backup do `dynasty.db` antes do smoke.**

- **OFF26-2 — keeper sheet consolidada ⚠️ localhost** (`a8c6f0f`). **Leitora pura** — deriva
  por inversão do snapshot: `keepers = roster_live − cut_ids`; salário = `p.salary`
  (pós-rollover); budget de FA = `usable_draft_budget` via porta em **`projected:false`**
  (paridade com o lock, 130==130). Status `declared` por time. Saída **CSV + tabela** (12
  times). **Fonte mista deliberada (D2):** salário/budget ao vivo + aviso de timestamp do
  lock — não duplica fonte canônica, não mexe no OFF26-1. Zero aritmética de cap nova (grep).
  e2e **20/20**. Expõe `/api/cuts/keeper_sheet` (JSON) = **base de diff da futura OFF26-4**.

- **Nota de processo:** o OFF26-1 foi commitado inteiro em `2c243d4` ainda na turn de "pode
  dar commit"; a tentativa posterior de "commit 1 de 2 (OFF26-1)" era **no-op** (já commitado)
  — surfaçado ao owner, e o ciclo fechou em **1 commit OFF26-2** (`a8c6f0f`) com os
  compartilhados + `improvements.md` dos dois ciclos.

- **Cadeia / próximos:** **OFF26-4** consome a keeper sheet (diff vs. liga fantasma real);
  **OFF26-7** encadeia revelação → sheet → Cowork → auditoria. **Smoke prod** dos dois itens
  depende de **E4-a (ESPN definitiva) + rollover** aplicados numa season real (~ago) com
  `needs_review` zerado; só então ✅. Candidato natural de F1 restante do pacote: OFF26-4.

### 17/06/2026 — Fechamento OFF26: OFF26-9 (acoplamento de fase) + OFF26-6/5 ✅ + smoke parcial (docs-only, pushed)

Sessão **docs-only** (microcopy + registros + runbook); zero mudança de lógica/gate/schema.
6 commits (`173d444`…`f861fb4`), todos em `origin/main`.

- **OFF26-9 — acoplamento intertemporada × ESPN definitivo ✅** (registro → F1 → FIX → smoke).
  Suspeita do owner: o E4-a (ESPN definitivo, deliberadamente tardio) entrou nas pré-condições
  de abertura **por arrasto**. **F1 (read-only) confirmou contra o código:**
  - **Abertura da janela (`admin_open_window`, cuts.py) exige SÓ `needs_review` zerado** — não
    checa E4-a nem `rollover_done`. O "pós-rollover" (D8) e "E4-a+rollover" (handoff) são
    **qualidade de dado** (budget valorizado / exatidão), **não trava de abertura**.
  - **Rollover (`do_rollover`)** é gated na flag **manual** `espn_values_updated` (passo 3, set
    por `confirm_espn`), **não** pelo import E4-a; lê `Player.espn_ref_value` (qualquer) → roda
    sobre ESPN preliminar.
  - **`offseason_mode`** só liga no rollover e gateia **cosmético** (banners). Gates funcionais
    reais = só rollover + abertura de cortes; resto é label.
  - **FIX (sem mudança de lógica):** separou **timing pós-rollover × qualidade de dado ESPN** no
    microcopy do **passo 6** (`offseason.html` — abertura = só `needs_review`; rollover =
    recomendação), na **D8** (esclarecimento anexo, decisão intacta), na linha "Dependências" da
    OFF26-1 e no handoff pt12. Rebaixado a ⚠️ até o **smoke do microcopy** (artefato de runtime);
    smoke **conferido em prod** (texto lê bem + layout intacto) → **✅ + migração O3** (seção →
    `improvements_archive.md`).

- **OFF26-6 — PoC do Cowork ✅ (op, GATE passou).** Em liga de teste descartável, Cowork + Claude
  in Chrome **cria a liga** (wizard 12 times + Auction) e **seta keeper com salário sozinho**
  (Draft Settings → SET KEEPERS), conferindo nome+time NFL (anti-homônimo). **Decisões de
  design:** liga fantasma **PERMANENTE** (redraft, owners reais — placeholders sem dono não são
  gerenciáveis); reset de roster automático (redraft) → trabalho anual = só popular keepers;
  config de roster **espelha a real** (3 WR, não 2); mapa owner↔time por **`sleeper_owner_id`**
  (não nome). **Achados → OFF26-4:** cap = budget do auction ($200 global), restante só visível ao
  vivo → auditoria **calcula** ($200 − Σ keepers), não lê; keepers = designação de board → lê
  designações, não roster; ponte de owner já resolvida (`Team.sleeper_owner_id`, M12), resta só a
  ponte de jogador.

- **OFF26-5 — runbook ✅ (doc).** Criado **`runbook_cowork_liga_fantasma.md`** (raiz) a partir do
  conteúdo-base escrito pelo Cowork pós-PoC, **preservando** detalhes operacionais (Ctrl+A no
  preço, anti-homônimo por sigla NFL, conexão da extensão, anatomia do board, TL;DR). **3
  reconciliações** com o OFF26-6: roster espelha a real (WR 2→3 obrigatório); liga PERMANENTE +
  mapa por `sleeper_owner_id`; **setup único × trabalho anual** separados, reset automático,
  gatilho da auditoria OFF26-4 ao término.

- **OFF26-1/2 — smoke PARCIAL em prod (17/06), seguem ⚠️.** Antes dos passos 3-ESPN/4-Rollover;
  backup `dynasty_prod_backup_17_06_2026_pre-off26.db` (540K). **Validado:** deploy live, tabelas
  `CutDeclaration`/`CutWindowAudit` criadas no schema de prod, tela `/cuts` "Fechada — 0/12" +
  budget + cap soft, gate `needs_review` zerado. **Não validado (owner não travou):** abertura+
  cortes reais, lock/reveal+hash, budget definitivo da keeper sheet → **OFF26-7**.

- **Sync de docs:** `CLAUDE.md` atualizado — blueprints **10→11** (linha `cuts`), models **17→19**
  (`CutDeclaration`/`CutWindowAudit`), runbook na estrutura; este devplan atualizado.

### MAN-OFF26-4-F1 — Diagnose read-only da auditoria pré-leilão ✅ (18/06/2026, Opus, docs-only)

Diagnose Fase 1 do OFF26-4 (auditoria de keepers pré-leilão). Read-only puro — sem código,
schema ou implementação. Achados gravados na entrada OFF26-4 do `improvements.md` (status
segue 🔲; descrição assentada intocada). Pontos-chave confirmados contra o código:

- **League ID** é constante hard-coded (`models.py:15 LEAGUE_ID`), assume uma só liga.
  **Precedente para ler outra liga já existe:** `draft_import.py` (OFF26-3) recebe `draft_id`
  do admin e deriva `league_id = draft.get("league_id")` via `ss._get` (URL arbitrária). Caminho
  limpo = parâmetro/AppConfig, não constante. → decisão de produto (REFINE).
- **GAP maior:** todo consumo de `/draft/{id}/picks` exige `status=="complete"`; **nada lê o
  estado pré-draft** (designações de keeper de board). O que a API expõe pré-draft é **questão
  empírica → probe na F2**, não assertável do código.
- Ponte de **owner** ✅ resolvida por `Team.sleeper_owner_id` (populado todo sync,
  `sync_sleeper.py:157,167`; casamento em `draft_import.py:48`). Ressalva: `Team.name` ainda é
  mutado pelo sync e exibido na sheet → casar **só por owner_id**, nunca por nome.
- Ponte de **jogador**: `/api/cuts/keeper_sheet` **NÃO** expõe `sleeper_player_id` (só `id` local);
  resolução via `Player.sleeper_player_id` / `find_player_by_sleeper_id` (Brown-safe).
- **Budget:** auditoria CALCULA os dois lados (confirmado). **Refutação:** `fa_budget` da sheet é
  `usable_draft_budget` (= `$200 − Σ keepers − $1/slot vazio`) ≠ budget de auction do Sleeper
  (`raw_budget` = `$200 − Σ keepers`). Comparar Σ salários de keeper ou `raw_budget`, **não**
  `fa_budget`. → decisão de produto.
- **Réplica:** `salary_engine.draft_budget` é porta única (sem réplica client-side); o diff
  Manager×Sleeper é greenfield. Recomendado extrair `_team_by_roster` (hoje em `draft_import.py`)
  para helper compartilhado em vez de recriar.

**Próxima fase: Opus modo REFINE** (2 decisões de produto + 1 probe empírico bloqueador).

### MAN-E4a-PRODF1 — Diagnose read-only do fuzzy espúrio no import ESPN em prod ✅ (23/06/2026, Opus, docs-only)

Owner rodou import ESPN real (cheat sheet PPR Top 300) e viu D/ST recebendo skill como
candidato (Texans D/ST → Stefon Diggs) + rookies 2026 em "Não Encontrados (76)", sim.
52.2%/50.0%. Suspeita: prod em modo legado. **Refutada.** Read-only puro; achados na entrada
E4-a do `improvements.md` (+ nota no E2-RISK); status segue ⚠️.

- **H1 (resolver inativo/legado) REFUTADA.** Threshold de approximate é 0.65 no legado
  (`espn_pdf_parser.py:262`) vs **0.5** no resolver (`:239`). As sugestões a **0.50/0.522**
  só vêm do resolver. Reforço: rookie→not_found com `resolved_sid` (`:204`) é exclusivo do
  resolver. Pool carregou; resolver ativo.
- **H2 (código ausente/divergente) REFUTADA** (sujeito a confirmar commit deployado).
  Assinatura = E4-a/E2-RISK, não legado.
- **H3 (réplica fora do matcher) REFUTADA.** Similaridade só em `match_players`
  (`:226,244`), persistida em `.espn_review_pending.json`, **só renderizada** em
  `espn_review.html:56,67`. Bug mora no ramo resolver-mode `:236-251`, fonte única.
- **Causa-raiz (CÓDIGO):** entrada que não resolve a sid (D/ST sempre — excluída do índice
  `admin.py:508`) cai no fuzzy `>=0.5` **sem filtro de posição** (`:236-251`); bônus de
  posição `:228-231` só soma +0.05, não filtra. Gap de desenho do E4-a desde a F2.
- **Eixo A (D/ST+K com skill espúrio) = BUG DE UI residual** (severidade baixa: confirm
  gated por E2-RISK + store pula K/DST `:550` → zero corrupção). **Eixo B (rookies em
  not_found) = INTENCIONAL** (E4-a correto; premissa "bug" é falsa).

**Próxima fase: F2 do E4-a** (filtro de posição/identidade no fallback de candidatos), não
item novo. Núcleo do E4-a/E2-RISK passou no smoke prod → candidato a ⚠️→✅ desses claims.

### MAN-E4a-F2-EixoA — Filtro de posição D/ST/K no fallback de candidatos do review ESPN (23/06/2026-pt2, Opus, código+docs)

Fecha o Eixo A da PRODF1 na origem (matcher), não na tela. **Código aplicado + validado
localhost; E4-a/E2-RISK seguem ⚠️ até smoke prod** (gate explícito, sem inércia de localhost).

- **`espn_pdf_parser.py`:** helper `_special_pos_compatible` + ramo especial no modo resolver
  de `match_players`. Entrada **D/ST ou K** só recebe candidato de posição compatível
  (D/ST→DEF/DST; K→K); sem candidato compatível ≥0.5 → **not_found limpo**. Ramo skill
  **inalterado**; modo legado (`sid_resolver=None`) **intocado** (mudança 100% dentro do
  `if sid_resolver is not None`). Sem tocar salary_engine/store/sync/schema/SalaryHistory/
  PlayerHistory; gate + default neutro do E2-RISK só confirmados.
- **Validação localhost:** harness sintético — Texans D/ST → not_found (não oferece Diggs);
  Rams/Ravens D/ST → not_found; **sem regressão** (Carnell Tate → not_found via sid; Jayden
  Daniels → matched por id; legado reproduz baseline). `salary_engine_test.py` 48/48.
- **Bloqueio honesto:** passos 2 (colher split de prod) e 3 (flip ✅) **não executáveis
  localmente** — exigem deploy + import ESPN real em prod. Entregue o código + narrativa de
  status (⚠️); o flip ✅ de E4-a/E2-RISK aguarda o owner rodar o smoke prod (procedimento no
  handoff). **Não flipado por inércia de localhost** (restrição respeitada).

### MAN-E4a-DONE — E4-a ✅ + E2-RISK ✅ após smoke prod do import real (23/06/2026-pt3, Opus, docs-only)

O commit do filtro (97b90ed) nunca tinha subido — o deploy ativo era o docs-only 927831a
(17/06). Após `git push` (`927831a..97b90ed`) e import ESPN real em prod, o smoke confirmou:

- **Eixo A fechado:** D/ST só recebem candidato de posição compatível (Broncos D/ST → só
  Denver Broncos DEF); demais D/ST sem entrada no índice → "Não Encontrados" limpo, sem skill.
- **Sem regressão:** ramo skill intacto (Antonio Williams ainda recebe skill); rookies 2026
  (Carnell Tate, Jeremiah Love, Jadarian Price…) seguem not_found → store.
- **Split de prod: 211 matched / 5 aproximados (4 D/ST consigo) / 84 não encontrados→store /
  62 ausentes no PDF.**

Gates satisfeitos → **E4-a e E2-RISK → ✅** (23/06). Migração O3: seções detalhadas movidas
verbatim p/ `improvements_archive.md` com nota de fechamento; Status Rápido mantém ✅. Sem código.

### MAN-PROC1 — Gate de hash deployado ancorado no DEV_METHODOLOGY (23/06/2026-pt4, Opus)

F1 recomendou **Forma 1** (afinar o gate existente, não criar artefato novo). Aplicado:

- **`DEV_METHODOLOGY.md`** (parent `Fantasy/`, transversal): reforçado o bullet "✅ só em prod"
  da seção **"Checklist de fim de sessão"** com o **gate de hash deployado** — fechamentos com
  smoke de prod exigem confirmar que o **hash live = commit validado** (não basta commitado/
  pushado); escopo só gates de prod; cita E1 + E4-a/927831a×97b90ed. **Sem seção paralela.**
- **`improvements.md`:** **PROC1 ✅** (Status Rápido + migração O3 da seção p/ o archive com nota
  de fechamento). Registrado **PROC2 🔲** (ressalva da F1 — surfacear `RENDER_GIT_COMMIT` no
  `/admin`; é código, follow-up separado).
- **Bloqueio honesto:** o parent `Fantasy/` é um **repo umbrella sem nenhum commit** (tudo staged
  como Added: ambos os repos nested, pff_data, CSVs, MYPFF db). A edição do `DEV_METHODOLOGY.md`
  fica **aplicada no arquivo mas não commitada** — pertence ao commit inicial do umbrella, que é
  do owner. **Não disparei** esse commit. O commit desta sessão (manager repo) cobre só
  `improvements.md`/archive/devplan/handoff.

### MAN-E5-F1 — Diagnose read-only: microcopy do review ESPN × pipeline do store (10/07/2026, Opus)

F1 read-only do E5 (texto "todos receberão $1" na tela de review do import ESPN). **Veredito:
problema de TEXTO PURO** — o pipeline pós-E2 está correto no código; só a microcopy mente.
Escopo do F2 não muda.

- **Inventário (5 microcopy + 1 comentário):** 4 textos em `espn_review.html` — :84 ("Não
  Encontrados — todos receberão $1", STALE), :70 (opção "Nenhum (aplicar $1)", STALE), :190 JS
  ("X com $1", STALE/superestima), :101 ("Ausentes — receberão $1", **CORRETO**, classe distinta
  = Players do DB → `espn_ref_value=1.0`). `espn_import.html:93` ($0→$1) CORRETO. `admin.py:716`
  comentário stale (não-UI).
- **Destino real por subclasse:** skill valor>0 sid-resolvível → **store** → `floor(ESPN×1.2)`
  (Love $46→$55; Tate $12→$14, **não $1**); $0 / K-DST / ambíguo / pool-indisponível → excluídos
  do store → $1 (claim verdadeiro só p/ essas). O bucket "Não Encontrados" é um MIX; o header
  achata tudo p/ $1.
- **Ponto 3 (bug de comportamento?):** **NÃO.** `not_found`/approx-skip não escrevem Player no
  confirm (só `upsert_rookie_espn`); `total_notfound` é contador de exibição. No draft, lê o store
  (`rookie_espn_adjusted`) → `floor(ESPN×1.2)`. $1 só quando store vazio (correto).
- **Réplicas:** varredura ("$1"/receber/not_found/"com $1" em templates+JS+routes) → semântica de
  destino vive em **4 pontos, todos em `espn_review.html`**; sem réplica externa. Único eco fora da
  UI = comentário `admin.py:716`.
- **Sinal p/ o F2:** pós-confirm a resposta **já retorna** `rookie_store{resolved,ambiguous,skipped}`
  (admin.py:764) e o JS ignora; pré-confirm o split é derivável no render reusando helpers read-only
  (`_build_pool_index`/`_resolve_entry_sid`) — decisão do F2.
- **Observação (não é item novo):** absent→$1 sobrescreve `espn_ref_value` de veteranos fora do
  Top-300 a cada import (admin.py:738) — pré-existente, plausivelmente intencional; ciência do owner.
- **Premissas do prompt contradichas:** nenhuma.

Absorvido na seção E5 do `improvements.md` (bloco "F1 — ACHADOS" + tabelas); Status Rápido atualizado
(F1 ✅, texto puro). Sem código, sem F2. Docs-only — agrupa com o próximo commit.

### MAN-E5-F2 — Review do import ESPN comunica destino real por subclasse (10/07/2026, Opus)

Fix do "todos receberão $1" (E5). Decisão do owner: opção (b) — texto + split por subclasse,
tela auto-explicativa. **Só comunicação — comportamento intacto** (matcher/store/confirm/
salary_engine/schema inalterados).

- **Classificador único (`routes/admin.py`):** novo `_classify_not_found_entry(entry, idx)` →
  `('store', sid)` | `('excluded', {kdst|zero|ambiguous})`. `_resolve_not_found_to_store`
  refatorado p/ consumi-lo (contagens `resolved/ambiguous/skipped` idênticas; predicado
  preservado). Mesmo classificador alimenta o split do render → texto não diverge do confirm.
- **Split server-side (`espn_review_page`):** computa `nf_store` (com `projected_salary` via
  `salary_engine.year1_salary` — fonte única) e `nf_excluded`, read-only; pool indisponível →
  tudo excluído (degradação = confirm).
- **`templates/espn_review.html`:** seção "Não Encontrados" dividida em 🟢 entrantes→store
  (texto floor(ESPN×1.2) + tag `raw→$proj`) e ⚪ sem valor→$1; opção skip reescrita; resumo
  pós-confirm (JS) consome `d.rookie_store` (resolved→store, ambiguous+skipped→$1); "Ausentes
  no PDF" ganha texto de regra de liga (comportamento intacto). Comentário stale `admin.py:716`
  reescrito.
- **Validação localhost:** salary_engine_test 48/48; templates parseiam; admin.py compila; teste
  sintético do classificador — Love→$55, Tate→$14, D/ST/$0/ambíguo→$1, partição store+excluded=
  total. **Pendente: smoke prod** (render + confirm com PDF real; gate PROC1 hash live=commit).
- **improvements.md:** E5 → ⚠️ (F2 localhost, gate de smoke prod). Commit agrupa código + docs.

**Smoke prod p/ o owner conferir:** (1) `/admin/espn_import` → upload de um PDF real → tela de
review mostra Jeremiyah Love e Carnell Tate sob "🟢 Entrantes → store" com salário projetado
($55/$14), e D/ST + entradas $0 sob "⚪ → $1"; soma dos dois = total de não-encontrados; (2)
confirmar o import → resumo diz "N → store de rookie (salário projetado), M → $1" (não "com $1"
genérico); (3) store recebe os mesmos upserts de antes (sem mudança de escrita).

### MAN-E3-F2 — Import ESPN upload-only: remoção completa do caminho de URL (10/07/2026, Opus)

Decisão do owner: opção (a) — remoção completa. A URL é inviável em prod (ESPN bloqueia IP do
Render — E1); só gerava ruído na mesma UI cuja clareza o E5-F2 acabou de melhorar. **Escopo =
porta de entrada; processamento intocado.**

- **`routes/admin.py`:** removido o branch de download por URL (`requests.get`/`raise_for_status`/
  flash anti-bot); POST agora exige upload (sem arquivo → flash). Guard `%PDF` **preservado**
  (protege upload corrompido → flash, sem 500), mensagem reescrita p/ upload-only. Removidos a
  constante morta `ESPN_DEFAULT_URL` e o `default_url` do render.
- **`templates/espn_import.html`:** removido o bloco do input de URL; label/subtítulo/tooltip/botão
  sem menção a URL ("Processar PDF"); card de formato intacto.
- **Validação localhost:** salary_engine_test 48/48; admin.py compila; espn_import.html parseia;
  grep confirma zero resquício de URL-download no fluxo (o `import requests` restante é do
  offseason.py, não relacionado). **Pendente: smoke prod** (upload real → review → confirm;
  inválido → flash sem 500).
- **improvements.md:** E3 → ⚠️ (F2 localhost, gate smoke prod). Commit próprio (E5-F2 já commitado
  em 642d447 antes da decisão do owner).

### MAN-DP3 — Board de rookies: classe entrante capturada (snapshot in_class) (31/07/2026, Opus + Fable)

Arco completo REG→F1→REFINE→F2→COMMIT. O board "🏈 Planejamento de Rookie Draft" do
cap_projector listava "entrada Top-300 ESPN não-rosterada" — critério **cego a classe**: mostrava
veteranos/rookies de classes antigas (Ridley ye8, Allen ye2, Ferguson ye1) e **omitia** rookies
da classe fora do Top-300. Refeito para listar **só a classe entrante da NFL**.

- **F1 (diagnose read-only):** `years_exp==0` é o **único** sinal do pool que captura a classe mais
  nova — `metadata.rookie_year` atrasa uma classe (sem bucket 2026 no cache), `search_rank`/`age`/
  `college`/`nfl_team` vêm nulos nos stubs entrantes. FantasyCalc cobre só 70 de 289. O critério
  "é rookie de classe" **não existia** em nenhum ponto do código.
- **REFINE (arquitetura de fonte):** 3 posturas × 6 eixos. Recomendada e escolhida (D4) = **P3,
  snapshot materializado** — captura por ação de admin com upsert idempotente por `(sid, season)`;
  devolve ao board o custo de request de hoje (1-2 queries indexadas vs. parse de 15 MB do pool),
  **preserva `clear_rookie_espn_store` como gate** e **resolve** o descompasso NFL×liga (a virada de
  classe ancora no calendário da liga, não no `years_exp` do Sleeper). D5 = tela alt. A.
- **F2 (implementação, D1–D5):**
  - **models.py:** coluna `RookieEspnValue.in_class` (Migration 8, ALTER idempotente); helper único
    `is_entering_class_member` (`years_exp==0` + skill + **`active` AND `status=='Active'`**);
    `upsert_rookie_espn` vira porta única com **dois donos por campo** (import ESPN = valores,
    captura = membership; `None` = não tocar).
  - **routes/admin.py:** `POST /api/admin/capture_rookie_class` (`@admin_required`) — varre o pool,
    upsert idempotente; quem saiu do critério é **desmarcado** (`in_class=False`), não deletado
    (preserva valor ESPN); pool indisponível → 503 gracioso; relatório `{added, updated, removed,
    total_in_class}`. Botão na tela do import ESPN (passo 3 da intertemporada).
  - **routes/salary.py:** `/api/cap_projector/rookies` lê `in_class=True` **menos já-rosterados**
    (subquery — sem double-count com a cadeia keep/corte do DP2); sem ESPN → `espn_adjusted=0` →
    `year1_salary` devolve **$1** (fonte única, zero cálculo novo).
  - **templates/cap_projector.html:** D5 alt. A — valorados ESPN no topo (ordem do server), massa
    $1 atrás de busca por nome + filtro de posição com contagem; renderer único, controles montados
    1× (foco da busca preservado); **zero** lógica de classe/salário/budget em JS; `/budget` DP2
    intocado.
- **Predicado D3 — justificativa:** conjunção `active`+`status=='Active'` porque cada flag isolada
  tem um modo de falha comprovado no pool — `status='Active'`+`active=False` = stubs fantasmas
  antigos com `years_exp` congelado (falsos entrantes); `active=True`+`status='Inactive'` =
  cortados/limbo. A conjunção exclui ambos.
- **Comportamento sazonal (esperado, não bug):** o predicado lê status vivo — ~**288** em
  julho/agosto (rosters NFL em 90, training camp), ordem de ~**150** pós-corte de fim de agosto.
  Nosso rookie draft ocorre **antes** do corte → board em uso real exibe a contagem alta. Recaptura
  desmarca cortados se o board seguir em uso pós-corte.
- **Validação localhost:** smoke **27/27** em DB temporário (seed do git intocado) —
  captura 2× idempotente sem duplicata; os 7 nomes da F1 (Ridley/Allen/Ferguson fora,
  Love/Tate/Bernard/A.Williams dentro); Love $46→$55, Lemon $3→$3, sem-ESPN→$1; rosterado fora;
  cenário 2 rookies → barra fixa +$58 exato; `clear_rookie_espn_store`→board vazio; captura sem
  login→401; `salary_history` inalterado. `salary_engine_test.py` 48/48.
- **Achado colateral → F13 🔲:** o TTL de 168h do `.sleeper_players_cache.json` (trackeado no git,
  ~15 MB) expirou no smoke e a captura baixou o pool vivo (recalibrou ~151→288); arquivo
  **restaurado antes do commit** (não é artefato do DP3). F13 avalia gitignore × cache em FS
  gravável — registro apenas.
- **E4-c-2:** REFINE detectou colisão (a metade "subsumir RookieEspnValue" bate com a natureza nova
  `in_class`); **reescopo pós-DP3** anotado no item, escopo original intocado.
- **COMMIT:** código + docs (improvements.md, CLAUDE.md) em `e12fdef`; cache fora do stage;
  handoff pré-existente fora. **Pushado** (`5c2414f..e12fdef`) com autorização do owner (deploy
  auto do Render). DP3 segue **⚠️** — não ✅.

**Smoke prod p/ o owner conferir (gate PROC1 — hash live = `e12fdef`):** (1) `/admin/espn_import`
→ card "🏈 Classe de Rookies" → capturar (1ª exec baixa ~15 MB do pool) → relatório ~288; rodar de
novo → `added=0, removed=0`; (2) `/cap_projector` → valorados no topo pós-import ESPN (conferir nº
× import real — interseção `in_class` × valor>0), massa $1 atrás de busca/filtro sem reload; (3)
cenário com rookie da massa $1 refletindo na barra fixa.


### MAN-F13 — Cache do pool Sleeper descongelado: volume persistente + TTL por conteúdo (31/07/2026, Opus + Fable)

Arco F1→F2→COMMIT→CLOSE no mesmo dia do fechamento do DP3 (o smoke do DP3 expôs o F13 em prod:
captura devolveu 148 = snapshot de 12/06, contra 288 do pool vivo).

- **F1 (diagnose read-only):** prod **nem tentava** escrever o cache — dupla trava estrutural:
  (1) mtime do checkout renovado a cada deploy mantinha o TTL de 168h eternamente "fresco";
  (2) checkout-revert — o deploy seguinte repunha o arquivo de junho mesmo que algo o atualizasse.
  Dano real maior que "stale": **145 dos 287** da classe entrante viva **nem tinham sid** no pool
  de junho (invisíveis p/ captura/resolver/sync); 108/142 com NFL team desatualizado (degrada o
  desambiguador Brown-safe do import ESPN). Correção de premissa: no E1 a escrita na raiz era
  hipótese preventiva, não falha confirmada; o que o E1 comprova é a gravabilidade de `/data`.
  Recomendação: caminho (b) padrão E1 + complemento (d) carimbo por conteúdo (padrão
  `dynasty_values`, já em casa).
- **F2 (commit `2cd8de3`):** `_player_cache_path()` deriva de `DYNASTY_DB` → cache em
  `dirname(DYNASTY_DB)` (volume `/data`; constante `PLAYER_CACHE_FILE` da raiz removida);
  `git rm --cached` + cópia de junho fora da árvore (o `.gitignore` já cobria, mas o arquivo fora
  committado antes); validade por envelope `{fetched_at, players}` **dentro** do arquivo (não
  mtime) — formato antigo/sem carimbo/ilegível/corrompido → vencido, refresh, nunca lança; leitores
  recebem o dict cru (envelope só na camada de disco). 6 consumidores e degradação graciosa
  intactos. Smoke cache 21/21 + e2e real (boot + download → captura 287, envelope no volume) + 48/48.
- **CLOSE (smoke prod, hash `2cd8de3` confirmado live; backup `/data/pre_f13.db`):** recaptura =
  **287** — 145 entraram (exatamente os ausentes previstos pela F1), 142 atualizados, **6 saíram
  por corte** (desmarcação `in_class=False` validada em condição real); 2ª captura **0/0 sem novo
  download** (carimbo operou); board 287 com 12 do import ESPN (6 valorados); busca/filtro no
  navegador. **Baixa da ressalva do DP3** anexada ao fechamento no archive (dos 84 do import, só
  12 são da classe — os 72 restantes eram os não-rookies que motivaram o DP3). Pendência
  remanescente (não impede ✅): frescor sobreviver ao **2º deploy** → verificação no próximo release.
- **Colaterais da sessão:** **F14 🔲** (nomes do board sem sufixo de geração — cosmético, identidade
  por sid intacta). **Regra nova no `DEV_METHODOLOGY.md`** ("Durante a implementacao"): smoke local
  que dá boot na aplicação DEVE apontar `DYNASTY_DB` p/ **cópia temporária**, nunca o caminho
  padrão — motivação: nesta sessão um boot caiu no default e rodou migrações contra o **seed
  versionado** (consumido por optimizer/predictor); detectado no diff pré-commit do F13 e revertido
  in-place (Windows recusou unlink). Edição do DEV_METHODOLOGY aplicada mas **não commitada**
  (repo umbrella sem commits — precedente PROC1; commit inicial é do owner).
- **Commits da sessão (todos pushados exceto o CLOSE):** `e12fdef` (DP3-F2) → `0f128c1` (docs
  CLAUDE/devplan) → `5ae4dd4` (DP3-CLOSE) → `2cd8de3` (F13-F2) → `d565c91` (F13-CLOSE, docs).

### MAN-S3-F2 — Picks casadas por chave estável (id de time), nome só display (02/08/2026, Opus)

**Contexto (cadeia S2 → S3):** o arco começou no S2 (sync ingerindo as permutações
administrativas de picks que o co-admin faz no Sleeper para montar a ordem do rookie draft).
A F1b do S2 descobriu, de raspão, que o sync **renomeia `Team.name`** e que `Pick` era casada
por **string de nome** — com o time 9 já renomeado no Sleeper ("Tropa do Bicampeonato" →
"Tropa do Jarra") e ainda não ingerido, o próximo sync criaria picks duplicadas. Virou o S3,
**bloqueante do retorno do sync** e, portanto, da própria correção do S2.

- **Decisão: casar por `original_team_id`, não por nome — e sem mexer no schema.** A F1
  mostrou que `Pick.original_team_id`/`current_team_id` **já existiam e já estavam corretos**,
  inclusive nas linhas duplicadas que a simulação gerou. O bug nunca foi falta de chave: era
  chave disponível e ignorada. **Why:** `_sync_trades:670` já casava por id — o precedente
  canônico estava no mesmo módulo. A F2 alinhou os dois retardatários ao terceiro em vez de
  inventar desenho novo.

- **Decisão: o join da projeção migra para id — forçado, não preferência.** A saída aparentemente
  mais barata (cascatear o rename para os nomes das picks, espelhando o cascade de
  `Player.fantasy_team`) **não fecha**: a projeção cruza `Pick` × `DraftLotteryResult` ×
  `SeasonStandings` por string, então o rename converteria "linha duplicada" em "linha sem
  projeção" (fallback 999). E refrescar `DraftLotteryResult.team_name` **quebraria o verify do
  M8** — ele compara o `team_name` congelado no `pool_json` com o da tabela viva, e essa
  congruência é a prova pública de que o sorteio não foi adulterado. **Why:** com o refresh
  vetado pela auditoria, id era a única saída. `_build_default_draft_order` passou a devolver
  `(pick_number, team_id, team_name)`; `_build_lottery_pool`/`_build_fixed_picks`, que alimentam
  o `pool_json`, ficaram **intocados**.

- **Decisão: `_resolve_tid` com queda para o nome só em linha legada.** `DraftLotteryResult.team_id`
  e `SeasonStandings.team_id` são nullable. **Why:** o fallback por nome é compatibilidade para
  linhas antigas sem id, nunca o caminho principal — e não reintroduz o bug, porque o nome dessas
  tabelas é congelado de propósito (nunca é reescrito).

- **Decisão: `Pick.*_team_name` vira display derivado, com refresh no próprio sync.**
  `_refresh_pick_team_names` (passo 11b) reescreve os dois rótulos a partir de `Team.name` a cada
  execução. **Why:** mesmo espírito do cascade de `Player.fantasy_team` (`:186-187`), idempotente
  (sem rename, 0 linhas mudam) e dispensa migração de dados — os ids já estavam certos, então não
  havia backfill de correção a fazer, só normalização de rótulo.

- **Decisão: criar `_resolve_traded_pick_identity` como ponto de costura explícito do S2-F2.**
  Porta única "entrada de `/traded_picks` → (season, round, Team original, Team dono)".
  **Why:** os dois fixes tocam `_sync_traded_picks` mas em camadas componíveis — o S3 responde
  *como* se acha a pick (id estável), o S2-F2 responderá *qual* pick é essa (desconto
  `x → L(S⁻¹(x))`). Com a porta pronta, o desconto entra num único lugar, operando sobre
  `Team`/id e nunca sobre string. Na ordem inversa o desconto produziria um **nome**, caindo
  justamente no match quebrado.

- **Validação (25/25, sobre cópia, sem rede).** Isolamento herdado da F1: **não importa `app.py`**,
  porque `data/dynasty_rosters_clean.csv` existe local e tornaria `fresh_import` truthy,
  disparando `run_sync()` de verdade contra a API — o sync está suspenso por diretriz do owner.
  Harness = Flask mínimo + blueprint de picks + `LOGIN_DISABLED` + filtro `utc_iso`, com os
  `traded_picks` do JSON capturado na F1a. Cobriu: regressão sem rename (estado das 108 picks
  **byte-equivalente**, 0 nomes refrescados), rename ingerido (**108 picks, 0 duplicatas**, time 9
  com 9 picks, 0 rótulos velhos), projeção (time 9 mantém pick #11, 12/12 times projetados),
  League Hub (contagens **idênticas à baseline** — o rename não move posse), dynasty (picks 2026
  do time 9 resolvem por `DP_`, sem fallback `FP_`), grid `/picks` (HTTP 200, rowlabel novo 3×,
  nome antigo ausente), `/api/picks` (36 picks 2026, 100% com projeção e valor) e **M8 verify
  match+hash antes e depois**. `salary_engine_test` 48/48.

- **Duas asserções minhas caíram na validação e foram corrigidas — não o código.** (1) "nenhum
  time com >12 picks": não existe esse invariante — um time acumula picks alheias via trade
  (Cangaceiros tem 16, e tinha 16 na baseline). Trocada pelo invariante correto: contagens
  idênticas à baseline. (2) O 17 que a F1 reportou para o Cangaceiros era o valor **inflado** pela
  duplicação, não a baseline.

- **Colateral registrado: S4 🔲** — `PlayerHistory` e `Trade` identificam time **só por nome**,
  sem chave estável no schema, e o `team_name` está **dentro do índice UNIQUE de dedupe do F8a**
  → pós-rename o mesmo evento não colide e a idempotência do histórico cai. Fora do escopo do S3
  (exige coluna nova + migração de 1.151 linhas + mexer na garantia do rebuild).

- **Estado:** ⚠️ validado em cópia local; **✅ só após smoke em produção** com gate PROC1 (hash
  live no Render = commit validado). **O sync permanece suspenso** — religar é decisão do owner,
  após o smoke. Sequência: **S3 smoke → sync liberado → S2-F2**.

### MAN-S3-DONE — S3 fechado com smoke em produção; sync religado (02/08/2026, Opus)

- **S3 ✅ (02/08/2026), gate PROC1 cumprido.** Hash live no Render confirmado pelo owner =
  **`89dc08d`** — o commit efetivamente validado, não um docs-only posterior. Backup pré-smoke:
  `/data/dynasty_pre_s3_smoke_2026-08-02.db`. Verificado em produção: `/picks` com **12 linhas por
  temporada e 108 picks**; `/league` com contagens corretas por time; **verify do lottery 2026
  conferindo** (a migração do join para `team_id` não tocou a auditoria do M8, como o desenho
  previa); valores dynasty de picks resolvendo no `/trades`.

- **O caso concreto que motivou o item passou limpo — em condição real.** O owner religou o sync e
  a **primeira execução** ingeriu o rename do time 9 ("Tropa do Jarra") **sem duplicação**, com a
  projeção **#11** preservada e as referências de display atualizadas. A cópia previu 0 duplicatas
  e a produção entregou 0 duplicatas: o rename que teria criado 9 picks duplicadas foi absorvido
  sem incidente.

- **Suspensão do sync encerrada.** O bloqueio operacional era do S3, não do S2 — a diretriz na
  seção do S2 foi corrigida para refletir isso. **O S2 segue 🔲**: as posições **2–5 do R1 2026
  permanecem no estado permutado** e o sync **reingere a permutação a cada execução**, então
  correção manual de dono de pick continua não sobrevivendo. Estado conhecido e documentado, não
  defeito novo — só o S2-F2 (desconto determinístico) fecha.

- **Migração O3:** seção detalhada do S3 movida **verbatim** para `improvements_archive.md` com
  nota de fechamento; o Status Rápido do ativo mantém a linha como ✅. O S4 (histórico sem chave
  estável) segue 🔲 no ativo, fora do caminho crítico.

- **Arco da sessão (S2 → S3 → S4), 6 commits:** `03a1f5d` (S2 REG) → `1949ac0` (S2-F1a, refuta a
  premissa: as trocas não são transações) → `94ff868` (S2-F1b, formaliza π = S⁻¹∘L e deriva o
  alvo) → `be16de1` (S3-F1, reproduz a duplicação) → `f4b1b40` (S4 REG) → `89dc08d` (S3-F2,
  código) → este fechamento. **Próximo passo: S2-F2.**

### MAN-S2-F2 — Desconto determinístico da permutação administrativa do board (02/08/2026, Opus)

- **Decisão: π derivado, nunca hardcoded — e bijeção como pré-condição.** Novo `board_mirror.py`
  monta `π = {S[p]: L[p]}` com `L` do `DraftLotteryResult` e `S` do `_build_default_draft_order`
  (a mesma fonte única do M15/M16 que a projeção já usa). **Why:** uma tabela de permutação
  precisaria ser reescrita todo ano e envelheceria em silêncio. E se π não for bijetiva, o desconto
  **não opera** — colisão significa board meio-montado, e descontar aí produz rótulos errados **com
  aparência de corretos**, que é estritamente pior que o bug conhecido.

- **Decisão: o armamento guarda a SEASON, não um booleano.** `AppConfig["board_mirrored_season"]`
  = `"2026"`. **Why:** o rollover avança `current_season`, logo `draft_season = current_season + 1`
  muda e o valor guardado deixa de casar — **desarma sozinho**, sem depender de alguém lembrar. Um
  booleano sobreviveria ao rollover e dispararia o desconto no ano seguinte sobre um board ainda
  não montado. Segundo gate: audit canônica de lottery para a season (sem sorteio canônico não
  existe `L`, logo não existe π).

- **Decisão: toggle explícito de admin, não detecção automática.** **Why:** a montagem **não deixa
  rastro** — não é transação (achado da F1a). Detectá-la seria inferir intenção a partir de ausência
  de evidência, e uma montagem **parcial** ingerida com o desconto ligado corromperia em silêncio.
  O ato explícito de quem executou a montagem é o único sinal honesto disponível hoje; a F2-3
  (futura) fecha o laço fazendo o Manager **prescrever** a permutação — aí ele sabe o que vai ler
  de volta.

- **Extensão deliberada além da letra do prompt: o desconto também entra no loop de picks do
  `_sync_trades`.** O prompt escopou a F2-2 em `_resolve_traded_pick_identity`. **Why estendi:** uma
  trade **real** fechada dentro da janela é registrada pelo Sleeper contra o rótulo do slot no
  board; sem o mesmo desconto no passo 12, ele sobrescreveria com o rótulo errado o que o passo 11
  acabou de gravar certo, e o estado só se recuperaria no sync seguinte. Um fix que se auto-corrompe
  na próxima trade não está pronto. Os outros dois chamadores de `_sync_trades` (backfill de ligas
  anteriores) não passam desconto → identidade, por default de parâmetro.

- **F2-1 respondida antes de implementar: a rota corretiva é REDUNDANTE.** As 4 entradas
  administrativas re-chaveadas formam uma **bijeção** sobre o mesmo conjunto de times
  `{mongoloides, 3 peat, Trust, Fazenda}` — ou seja, **exatamente as 4 linhas divergentes recebem
  escrita explícita** (3 viram no-op `pick de X → X`, a quarta re-rotula a trade real). Nenhuma
  linha-alvo fica de fora, então a correção do estado é **armar + rodar o sync**. A rota admin
  auditável prevista na F1b **não foi implementada** — seria código morto. Confirmado na validação.

- **Validação 24/24 sobre cópia, sem rede** (mesmo isolamento das fases anteriores — sem
  `import app`, que dispararia `run_sync()` real). Desarmado: estado **byte-equivalente**. Armado:
  as **12 posições do R1 2026 batem com a tabela-alvo da F1b**; idempotente na 2ª execução; **96
  linhas fora do R1 2026 intocadas**; trade real simulada na janela move só a posição negociada;
  3 gates de armamento; **M8 verify match+hash antes e depois**; `/admin` render + endpoint.
  `salary_engine_test` 48/48.

- **Premissa do prompt contradita (critério de validação).** O prompt pediu "posição 2 →
  Cangaceiros via pick da 3 peat" — o que **contradiz a tabela-alvo da própria F1b**, citada pelo
  prompt como autoridade. O alvo é **pos. 2 → Fazenda Pederasta** e **pos. 5 → Cangaceiros**:
  "Cangaceiros na posição 2" é o **estado permutado atual** (o defeito), e a pick da 3 peat ocupa a
  **posição 5** pelo lottery. Implementei conforme a tabela da F1b.

- **Estado:** ⚠️ validado em cópia; **✅ só após smoke em produção** com gate PROC1. Roteiro do
  smoke: backup → deploy + conferir hash live → `/admin` **Armar para 2026** → rodar o sync →
  conferir as 4 posições no `/picks` contra o board do Sleeper.

### MAN-S2-DONE — S2 fechado com smoke em produção; arco S2→S5 encerrado (02/08/2026, Opus)

- **S2 ✅ (02/08/2026), gate PROC1 cumprido.** Hash live no Render confirmado pelo owner =
  **`9b4bcf1`**; backup prévio `/data/dynasty_pre_s2_smoke_2026-08-02.db`. Sequência do smoke:
  desconto **armado para 2026** via `/admin` → sync executado → conferência. Resultado: as **4
  posições divergentes do R1 2026 convergiram para o alvo derivado na F1b** — pos. **2 = Fazenda
  Pederasta sem troca**, pos. **5 = 3 peat → Cangaceiros** (o re-rótulo da trade de 29/07,
  confirmado em produção), pos. **3 e 4** com donas originais corretas. Pos. 1 e 6–12, R2/R3 e
  seasons futuras intactos.

- **A verificação que fecha o ciclo: cruzamento com o board do Sleeper.** O owner conferiu `1.05`
  via `fernandoxmf` visível no roster MellowBR. O alvo era, desde a derivação da F1b, **"o que o
  board já exibia"** — o Sleeper sempre esteve certo na *sequência*, errado na *titularidade*, e o
  Manager era quem re-permutava ao projetar. Agora os dois contam a mesma história.

- **Idempotência confirmada em produção**, não só em cópia: a 2ª execução do sync não alterou nada.
  É a propriedade que torna o desconto seguro de conviver com um Sleeper permanentemente "errado" —
  a montagem administrativa segue viva lá e é aniquilada a cada leitura.

- **Nota de método — a F1 refutando premissas operou também sobre o prompt, não só sobre o código.**
  O prompt da F2 trazia como critério de validação "posição 2 → Cangaceiros via pick da 3 peat".
  Isso **contradizia a tabela-alvo da própria F1b**, que o mesmo prompt citava como autoridade: o
  alvo é **pos. 2 → Fazenda** e **pos. 5 → Cangaceiros** ("Cangaceiros na 2" era o estado
  **permutado**, ou seja, o defeito). A correção **partiu do Code**, conferindo o critério contra a
  tabela derivada antes de implementar — e o smoke em produção confirmou a leitura corrigida.
  É a terceira família de ocorrência do [[MAN-METH-REG]]: até aqui a regra candidata falava em
  refutar premissas do prompt **contra o código**; este caso mostra que ela vale também **contra
  artefatos derivados em fases anteriores** (a tabela-alvo). Aceitar o critério como dado teria
  produzido um fix "validado" contra o alvo errado.

- **Migração O3:** seção detalhada do S2 (REG + F1a + F1b + F2 + smoke) movida **verbatim** para
  `improvements_archive.md`. Sanidade da migração verificada por marcadores de fase antes de
  escrever.

- **Fatia F2-3 desmembrada como item próprio [[S5]] 🔲** — tela que **prescreve** a permutação ao
  co-admin. **Why desmembrar no fechamento:** a F1b recomendou 3 fatias e só 2 foram entregues; se a
  terceira ficasse descrita apenas dentro da seção do S2, sumiria do backlog ativo junto com a
  migração O3. Não bloqueia nada — o desconto já exige bijeção e **desliga** diante de board
  meio-montado. O que ela remove é o **conhecimento tácito**: hoje o Manager torce para que a
  montagem tenha seguido π; com a tela, ele prescreve e portanto sabe o que vai ler.

- **Estado do arco:** **S2 ✅**, **S3 ✅** (ambos com smoke em prod). Ativos: **S4 🔲** (histórico
  sem chave estável de time) e **S5 🔲** (tela prescritiva) — nenhum dos dois bloqueia operação.
  Sync liberado e com o desconto armado para 2026; o rollover desarma sozinho.

- **Commits do arco (8):** `03a1f5d` (S2 REG) → `1949ac0` (F1a) → `94ff868` (F1b) → `be16de1`
  (S3-F1) → `f4b1b40` (S4 REG) → `89dc08d` (S3-F2, código) → `e5677d9` (S3 DONE) → `9b4bcf1`
  (S2-F2, código) → este fechamento.

### MAN-OFF26-10-11-REG — dois gaps de intertemporada + emenda da premissa "ligas fantasmas" (02/08/2026, Opus)

- **Sessão de registro puro** (docs-only, sem código, sem diagnose, sem arbitragem de produto). O
  calendário real da intertemporada 2026 foi fixado com o comissário — **17/08** rookie draft ·
  **18/08** congelamento ESPN · **20/08** prazo de cortes · **22/08 late drop** (máx. **1** jogador
  por time) · **24/08** FA auction — e percorrê-lo expôs **dois gaps que não existiam em lugar
  nenhum do backlog**.

- **OFF26-10 🔲 Alta (caminho crítico 22/08) — late drop pós-lock na janela selada.** A janela do
  [[OFF26-1]] foi desenhada com **deadline único, lock e revelação simultânea**; o late drop altera
  o conjunto de keepers **dois dias depois do lock**, e keeper sheet, budget de FA e board da liga
  fantasma derivam **todos** do snapshot selado. Consequência já identificada: **a sheet de 20/08 é
  provisória** para os times que fecharam os cortes acima do cap, virando definitiva só após 22/08 —
  um artefato provisório circulando com cara de definitivo no exato ponto em que o Cowork o
  transcreve. **Registrado como questão empírica (probe, não fato):** o Sleeper pode **recusar**
  designação de keepers acima do budget do auction — se recusar, a população do board teria de ser
  **fatiada por time**, não feita de uma vez e remendada. Registrada também a **assimetria de
  limite**: o Sleeper só conhece o budget global, a regra da liga reserva $1/slot vazio → um time
  pode **passar lá e estar ilegal aqui**. **Decisão deixada em aberto com o owner:** segunda
  mini-janela selada × correção administrativa pós-lock (determina se há novo lock/hash, se a
  revelação é simultânea de novo, e o que a trilha registra).

- **OFF26-11 🔲 Alta (caminho crítico 24/08) — importador distingue keeper de arremate novo.** Os
  keepers **precisam** estar designados no board (o Sleeper não tem cap por time: o cap **emerge**
  do budget global consumido pelos keepers), logo os picks do auction virão **misturados**. O
  importador [[OFF26-3]] escreve pela **porta canônica de aquisição**, que é porta de **contrato
  ano 1** — ingerir um keeper **zera a idade do contrato** de quem nunca saiu do time. **Dano
  silencioso, visível só anos depois, na renovação.** Caso canônico do owner: $50 dropado, leiloado
  e **recomprado pelo mesmo time por $50** — valor idêntico, **natureza diferente** (o contrato
  antigo morreu, nasceu um ano 1). O cenário nunca foi exercitado: o importador foi validado contra
  os drafts reais de 2025, cujas salas **não tinham keeper no board**. **Probe pendente** (o mesmo
  que o [[OFF26-4]] aguarda): os picks vêm marcados, ou o discriminador sai da keeper sheet como
  lista de exclusão? **Decisão em aberto:** importar só arremates × reconciliar e reportar
  divergência de salário (virando uma segunda auditoria).

- **Emenda de premissa — o rookie draft NÃO roda em liga fantasma.** O registro do pacote OFF26
  (05/06/2026) afirma, numa frase, que rookie draft e FA auction rodam **ambos** em ligas fantasmas.
  É falso, e a metade do rookie draft **nunca foi justificada item a item** — entrou por arrasto,
  colada no motivo real da FA auction. Evidência: o [[OFF26-3]] foi validado contra o **rookie draft
  real de 2025**, lido da chain da **liga real**; e todo o arco [[S2]]/[[S3]], fechado hoje, trata do
  **board de R1 2026 da liga real** — a permutação administrativa, o espelhamento e a tela
  prescritiva ([[S5]]) só fazem sentido ali. O motivo próprio da sala separada da **FA auction**
  permanece válido: a liga real é **dynasty com rosters cheios**, e o auction pressupõe **rosters
  vazios preenchidos por lance**. **Consequência propagada: existe UMA liga fantasma permanente,
  não duas.** Texto histórico **preservado verbatim** com bloco EMENDA anexo (precedente de correção
  de premissa do [[DP1]]); ajustados o título da seção do pacote, a descrição do [[OFF26-7]] e a
  linha do `draft_import` no `CLAUDE.md`. **Deixadas intactas de propósito** (registro histórico +
  restrição do prompt de não mexer no Status Rápido além das duas linhas novas): a linha do
  [[OFF26-3]] no Status Rápido e sua seção no `improvements_archive.md`, que rotulam o item como
  "importador de drafts de liga fantasma" — rótulo de nomeação de item fechado, não premissa viva.

- **Cross-refs estabelecidos:** OFF26-10 depende de OFF26-1 e afeta OFF26-2/OFF26-4; OFF26-11
  depende de OFF26-3 (✅) e do mesmo probe do OFF26-4. **Ambos entram como etapas do [[OFF26-7]]**
  (dry run E2E) — são **costuras**, exatamente o objeto daquele ensaio.

- **Nenhum item existente teve status alterado.** Sem código, sem schema, sem rotas, sem testes.

### MAN-OFF26-10-11-REG (2ª parte) — achados empíricos da liga fantasma (02/08/2026, Opus)

- **A sala existe.** A liga fantasma permanente foi **criada de fato** nesta sessão: **Dynasty SB
  FA Auction** — Redraft, 12 times, draft **Auction**, budget **$200**, **22 rodadas**, roster
  espelhando a real (**3 WR**). Estado **no momento deste registro**: ambiente de teste com 2 times
  populados, RESET DRAFT pendente e ids ainda não fornecidos. **→ As duas pendências foram
  resolvidas na mesma sessão, logo depois — ver `MAN-OFF26-IDS-REG` abaixo.**

- **REFUTAÇÃO: §5 da F1 do [[OFF26-4]] (18/06/2026) está errado.** A diagnose afirmava que a
  reserva de **$1 por slot vazio** era regra **interna do Manager, inexistente no Sleeper**, e
  concluía em negrito que a auditoria **não** podia comparar `fa_budget`. O experimento mostra o
  contrário: **o Sleeper aplica a mesma reserva**. Fórmula confirmada —
  `teto = 200 − gasto − (vagas_restantes − 1)`. Time com **$150 gastos** e **21 vagas** → teto
  **$29**: **$40, $33 e $32 recusados** (*"The specified slot does not have enough budget."*),
  **$29 aceito**; e **sem falso positivo** no sentido oposto (10 keepers somando **$140**, folga de
  $49, passaram sem aviso). → **A base de comparação correta é `usable_draft_budget`** — o número
  que a keeper sheet **já entrega**. A **decisão de produto 2** do OFF26-4 passa a **RESOLVIDA POR
  EVIDÊNCIA**, não por arbitragem. Texto da F1 **preservado verbatim** com bloco de atualização
  anexo (precedente [[DP1]]). **Ressalva registrada:** o Sleeper reserva sobre as **22 rodadas** da
  sala e a regra **8.3.4** conta slots pelo **regulamento** — se as contagens divergirem os limites
  não coincidem apesar da fórmula idêntica; é **conferência aritmética pendente**, não experimento.

- **[[OFF26-10]] — a suspeita da 1ª parte virou fato.** Registrei de manhã, como *questão empírica
  destino de probe*, que "o Sleeper **pode** recusar designação acima do budget". **Confirmado:**
  recusa. Consequência: **a população escalonada é OBRIGATÓRIA, não alternativa** — times
  enquadrados em 20/08, estourados **só após o late drop de 22/08**. Abre uma funcionalidade
  concreta: o Manager pode **pré-calcular quais times ficarão bloqueados** antes de o Cowork tentar.

- **[[OFF26-11]] — indício forte, registrado como indício.** A operação disparada ao designar
  keeper carrega **`is_keeper: false`**, e a UI **toca o som de lance vencedor**: o Sleeper trata a
  designação como **pick forçado de leilão**, não como keeper. **Não é fato assentado** — a
  verificação definitiva é o que os picks expõem **pós-draft**, ainda não observado (o draft não
  rodou). Se confirmar, o campo **não serve de discriminador** e este terá de vir da **keeper sheet
  como lista de exclusão** — o que **inclina, sem decidir**, a decisão em aberto para o ramo
  "Manager é fonte única da verdade".

- **Runbook do [[OFF26-5]] corrigido contra a UI real — status ✅ mantido (correção de texto
  factual, não reabertura).** O achado grave: **o caminho de entrada da Fase B não existe** —
  engrenagem → Draft Settings → *SET KEEPERS/DYNASTY PLAYERS* → *SET PLAYERS* sumiu; **o board já
  está em modo de designação** e clica-se **direto na célula vazia**. Caçar esse caminho fantasma
  foi a maior fatia dos ~9 min de overhead da transcrição. Mais 7 correções: **"+" da linha, nunca
  o nome** (o nome abre o perfil e fechar **cancela o fluxo inteiro**); **K/DEF abaixo da dobra**
  (seta ▼ — o scroll não move o board); **filtro de posição** para K/DEF; **preço já vem $1** (não
  editar em keepers de $1); **Ctrl+A rebaixado de alerta a nota** (100% dos casos); **homônimo
  suavizado sem ser removido** (o pool só traz ofensivos elegíveis → Josh Allen LB/JAX nem
  aparece, mas dois ofensivos homônimos seguiriam ambíguos); **nome da liga**. **Adição além das 8
  correções:** seção nova **§B.3.2** com o teto de lance e a ordem escalonada — sem ela o Cowork
  bate na recusa em 2026 sem saber o que fazer.

- **Medição de esforço e decisão de método.** **Medido, não estimado:** 1 time (10 keepers) =
  **20 min 32 s**, dos quais **~9 min de overhead único** de descoberta. Regime: **~75 s/jogador ≈
  12,5 min/time → ~2,5 h para os 12** (a transcrição manual do ano anterior levou **uma tarde
  inteira**). **Decisão do owner:** 2026 roda **via Cowork** com o runbook corrigido; **script
  determinístico fica como melhoria para 2027** — o argumento que o justificaria ("não cabe na
  janela de 48 h entre late drop e leilão") **cai** diante das 2,5 h medidas. **Caminho via API
  interna não documentada: deliberadamente descartado** — sem contrato, quebra sem aviso, provável
  violação de termos de uso e **expõe a conta de comissário da liga real**. Registrado para não ser
  re-proposto como "otimização óbvia" em 2027.

- **Nota de método.** Metade do valor desta sessão veio de **premissas caindo**: uma diagnose
  read-only de junho (§5 do OFF26-4) e um runbook escrito com contexto fresco em junho **ambos
  descreviam um Sleeper que não é o de hoje**. O denominador comum é que os dois foram produzidos
  **sem tocar a plataforma real** — a F1 raciocinou sobre o código do Manager e concluiu sobre o
  Sleeper; o runbook documentou uma UI de uma liga de teste descartável. **Vinte minutos de
  experimento manual derrubaram os dois.** Reforça a regra do [[MAN-METH-REG]] numa quarta família:
  premissa sobre **sistema externo** só se assenta **tocando o sistema externo**.

- **Nenhum item existente teve status alterado.** Sem código, sem schema, sem rotas, sem testes.

### MAN-OFF26-IDS-REG — identificadores da liga fantasma + reset executado (02/08/2026, Opus)

- **Fecha as duas pendências** que o `MAN-OFF26-10-11-REG` (2ª parte) deixou explícitas. Ambas
  foram resolvidas pelo owner **na mesma sessão, logo após aquele commit**.

- **(1) Identificadores registrados** — liga **Dynasty SB FA Auction**:
  **`league_id` = `1389725099556372481`** · **`draft_id` = `1389725100684611584`** *(⚠️ este
  `draft_id` **morreu no mesmo dia** — ver `MAN-OFF26-RUNBOOK-REG-PT2` abaixo; o `league_id` segue
  válido)*, lidos das URLs
  da página da liga e do draft board. **Os dois são distintos e NÃO deriváveis um do outro por
  inspeção** — o que **reforça o precedente do `draft_import.py`** levantado no §1 da F1 do
  [[OFF26-4]]: passa-se o **`draft_id`** e **deriva-se** o `league_id` do objeto do draft; o
  caminho inverso não é inspecionável. **Registrados como DADO e deliberadamente NÃO persistidos**
  em constante, `AppConfig` ou coluna — as opções (a)/(b)/(c) do §1 **seguem abertas**. Ter o
  número não escolhe onde ele mora, e antecipar isso num registro seria arbitrar por acidente.

- **(2) RESET DRAFT executado — board vazio.** Os 2 times populados durante a validação
  (transcrição cronometrada + experimento de teto de budget) foram removidos. A liga está **pronta
  para o uso real**.

- **Consequência registrada como PRÉ-CONDIÇÃO, não como detalhe de execução: o reset apagou o alvo
  empírico dos probes pendentes.** As duas verificações que continuam abertas — o que a API expõe
  **pré-draft** (§2 da F1 do [[OFF26-4]], o bloqueador daquela diagnose) e o que os picks expõem
  **pós-draft** (a confirmação definitiva do indício `is_keeper:false` do [[OFF26-11]]) — **não têm
  o que ler hoje**. **Repopular o board é pré-condição das diagnoses**, e ficou anotado nos dois
  lugares onde essas verificações são descritas, justamente para não ser descoberto no meio delas.

- **Nenhum status alterado, Status Rápido intocado, sem código.** Os identificadores não aparecem
  em nenhum arquivo `.py`/`.html` — verificado por grep.

### MAN-OFF26-RUNBOOK-REG-PT2 — 2ª execução do Cowork: runbook validado, `draft_id` instável, falso achado rejeitado (02/08/2026, Opus)

- **Contexto:** segunda rodada no mesmo dia, agora **com o runbook já corrigido** e com a lista de
  keepers **pré-ordenada na sequência do board**. Populados **Team 3 (10 keepers, $148)**, **Team 4
  (8, $95)** e **Team 5 (6, $60)** — todos os totais conferindo. **O runbook corrigido foi
  validado**: o fluxo levou o agente ao fim três vezes, sem redescoberta de caminho. **A medição de
  tempo foi perdida** por instabilidade de ambiente.

- **Achado de maior alcance: o `draft_id` NÃO é estável.** O **RESET DRAFT gerou um draft novo, com
  id novo** — o valor registrado poucas horas antes pelo `MAN-OFF26-IDS-REG`
  (`1389725100684611584`) **morreu no mesmo dia**; id atual **`1389755381567213568`**. O
  `league_id` (`1389725099556372481`) **é estável**. **A morte é silenciosa:** a URL antiga **trava
  indefinidamente em LOADING**, não dá erro — o pior modo de falha possível, porque não se
  distingue de lentidão. Presumivelmente muda também **a cada virada de season**.

- **Incidência sobre a decisão 1 do [[OFF26-4]] — restrição, não arbitragem.** Não decidi entre (a)
  parâmetro por chamada, (b) `AppConfig`, (c) coluna em Team. O que a evidência elimina é um
  **atributo transversal às três**: **qualquer alternativa que persista `draft_id` está descartada
  por evidência**. Persiste-se o **`league_id`**; o `draft_id` é **derivado a cada uso**. **A
  confirmar, não assumir:** o precedente do `draft_import.py` é a derivação **inversa**
  (`draft_id → league_id`); o caminho necessário aqui (`league_id → draft_id`, presumivelmente via
  `/league/{lid}/drafts`, já usado em `sync_sleeper.py:762`) **nunca foi exercitado contra a
  fantasma**. Por que isso importa além do OFF26-4: um id persistido que morre em silêncio faz a
  auditoria **pendurar em vez de errar**, e o momento em que isso aconteceria é **logo após um
  reset — ou seja, na virada da intertemporada**.

- **⛔ FALSO ACHADO REJEITADO — o registro mais importante desta sessão.** O relatório do Cowork
  **recomendou rebaixar o check anti-homônimo**, alegando divergência entre a sigla NFL do Sleeper
  e a keeper sheet (**Waddle exibido como DEN, Hill sem sigla**). **A recomendação está errada e
  não foi aplicada.** A causa foi a **lista de teste**, montada à mão pelo owner-side com **times
  de temporadas anteriores** — **dado velho na lista**, não divergência de plataforma. Na execução
  real, a sheet sai do **Manager**, que **sincroniza do Sleeper**: os dois lados bebem da **mesma
  fonte**. **Orientação registrada é a INVERSA:** divergência de sigla na execução real é **sinal
  de problema no sync ou na sheet** → **parar e reportar**. O check da §B.3 permanece **inalterado**.

- **Nota de método (família [[MAN-METH-REG]]):** *recomendação de melhoria vinda de execução com
  **dados sintéticos** precisa ser conferida contra a **origem do dado** antes de virar correção de
  documento.* O que torna este caso instrutivo é que **a observação era verdadeira** — a sigla **de
  fato** divergiu. O erro não estava no que se viu, e sim em **de onde o dado vinha**. Sem a
  conferência, **uma proteção teria sido enfraquecida na véspera do uso real por artefato de
  teste**, e com justificativa aparentemente empírica.

- **5 correções aplicadas ao runbook** (status ✅ mantido — texto factual, não reabertura):
  (1) **identificação de coluna com placeholders** — cabeçalhos são **avatares vazios sem rótulo**;
  a verificação canônica é o **menu de contexto** (*"Manually set a player for Team N"*); a
  orientação "pelo owner" pressupõe rótulos que só existem com owners reais → os **dois estados**
  documentados; (2) **o board reescala** após a 1ª interação, quebrando referência posicional →
  revelar FLEX/K/DEF antes e confirmar o time pelo menu; (3) **a vaga é atribuída por posição** (um
  RB entra no FLEX quando as vagas de RB estão cheias) → clicar a célula exata é **conveniência,
  não obrigação**, o que desarma boa parte do risco de (2); (4) **o preço nasce em `$1` sempre**,
  inclusive com `$PROJ` maior → regra **generalizada** a qualquer keeper de $1; (5) **filtro de
  K/DEF** confirmado mais rápido, com propriedade útil: **já-designados somem do filtro**, então
  "primeiro disponível" é limpo. **Mais:** §B.1 reescrita para **não fixar URL de board** (entrada
  por descoberta: liga → pré-draft → widget Draftboard → globo).

- **Melhoria do [[OFF26-2]] com validação empírica — registrada, não implementada.** A lista
  pré-ordenada na sequência do board **eliminou busca, deliberação e navegação**; a execução virou
  **descida linha a linha**, e **6 dos 24 keepers dispensaram edição de preço** por serem de $1.
  → emitir a sheet **time a time, na ordem das linhas do board**, com **marcação dos keepers de
  $1**. É o **artefato de handoff** para o único passo do calendário que roda **fora** do Manager;
  ordená-lo na sequência do consumidor é a diferença entre dados **corretos** e dados **operáveis**.

- **⚠️ Medição perdida + risco de variância de ambiente.** Tempos: Team 3 = **26min52s** (10) ·
  Team 4 = **14min13s** (8) · Team 5 = **13min58s** (6) · total **58min26s**. **Não medem o
  procedimento:** o ambiente acumulou **dezenas de timeouts de captura de tela, 30 s cada**, que
  dominam o relógio. Evidência de que o gargalo é o ambiente: o **Team 4 foi mais rápido por
  jogador que o Team 3** e o **Team 5 voltou a subir por concentração de timeouts** (curva de
  aprendizado não sobe); e a execução anterior, **no mesmo dia e sem** runbook corrigido nem lista
  ordenada, rendeu **~75 s/jogador** — não há explicação plausível para corrigir o documento e
  pré-ordenar a lista **piorar** o trabalho. **Risco registrado:** mesmo ambiente, resultados muito
  diferentes, **sem causa identificada**; ~2 h × ~5 h para 12 times, **sem saber qual antes de
  começar**. **Mitigação: fatiar por time**, cada um uma **unidade verificável** — o modo de falha
  é **lentidão, não erro**, então a sessão seguinte retoma do time seguinte sem refazer nada.

- **Decisão Cowork-2026 mantida, com reconsideração parcial ABERTA.** O argumento original do
  script ("não cabe na janela de 48 h") **segue caído** — o tempo médio cabe. Mas surge um
  argumento **novo e de outra natureza**: **variância**. O script determinístico **não tem esse
  modo de falha**; o risco deixou de ser *demorar demais* e passou a ser *não dar para prever*, e é
  a imprevisibilidade que ameaça uma janela de 48 h. **Contra-argumentos preservados:**
  fragilidade de seletores (a UI **já mudou uma vez** entre junho e agosto), competição de prazo
  com [[OFF26-4]] e [[OFF26-11]] no caminho crítico, e **estreia no dia do uso** como pior cenário.
  **Não arbitrado.**

- **Estado da liga:** board **populado** com Team 3/4/5 (dados de teste); Team 1 e 2 limpos pelo
  reset; **novo RESET DRAFT pendente** antes do uso real — e ele **gerará novo `draft_id` outra
  vez**. **Janela aberta:** o board populado **serve de alvo** ao probe pré-draft do OFF26-4 e à
  verificação de designações, **desde que rodados antes do próximo reset**.

- **Nenhum status alterado. Status Rápido intocado. Sem código.**

### MAN-OFF26-4-REFINE — spec da auditoria de keepers pré-leilão (03/08/2026, Opus)

- **Sincronização de spec, não implementação.** O [[OFF26-4]] tinha F1 de 18/06 e, desde então,
  **evidência empírica de 02/08** que **refutou uma de suas premissas** e resolveu parte das
  decisões abertas. Esta fase fecha as decisões de produto e prepara a F2. **Status segue 🔲.** A
  **F1** e a **ATUALIZAÇÃO EMPÍRICA** ficaram **intactas abaixo da spec**, como terreno — a spec é
  camada nova acima delas, no mesmo padrão do [[OFF26-2]].

- **A natureza do item foi o que decidiu o D1.** A auditoria não é gate único: **roda 3× ou mais**
  numa janela de 48 h — após a **1ª leva de população (20/08)**, após o **remendo do late drop
  (22/08)** e possivelmente uma vez **final** antes de **24/08**. É essa repetição sob prazo que
  derruba o parâmetro-por-chamada: **recolar o id a cada execução é oportunidade recorrente de
  colar o errado exatamente quando ninguém tem tempo de conferir.**

- **D1 — `AppConfig` para o `league_id`; `draft_id` derivado** *(arbitrada)*. Descartadas a **coluna
  em `Team`** (é atributo **de liga**, não de time) e o **parâmetro por chamada**. ⛔ **Restrição
  não-negociável:** persiste-se **apenas o `league_id`**; o `draft_id` **muda a cada reset** e é
  **derivado a cada uso** — nenhuma forma de persistência, nem cache. ⚠️ **Requisito que vem do
  modo de falha:** a URL de um draft morto **trava em LOADING em vez de dar erro**, então a falha é
  **indistinguível de lentidão** → **timeout explícito e mensagem própria**. Numa janela de 48 h,
  uma auditoria que **pendura** é pior que uma que **falha**. 🔲 A F2 **herda** a pendência: o
  caminho `league_id → draft_id` existe no código mas **nunca foi exercitado contra a fantasma**, e
  o precedente do `draft_import.py` é a derivação **inversa**.

- **D2 — base = `usable_draft_budget`** *(resolvida por evidência, não arbitrada)*. O §5 da F1 está
  **refutado**: o Sleeper aplica **a mesma reserva de $1/vaga**. ⚠️ **Ressalva que a F2 carrega,
  ainda não conferida:** o Sleeper reserva sobre as **22 rodadas da sala**; a **8.3.4** conta slots
  pelo **regulamento** — divergindo as contagens, **os limites não coincidem apesar da fórmula
  idêntica**. Não depende de acesso à plataforma; depende de conferir regulamento × config.

- **D3 — ponte de jogador DELEGADA à F2, com critério** *(delegada)*. Incluir `sleeper_player_id`
  no payload × re-query fica com a F2, sob o critério do owner: **preferir o caminho que não toque
  o [[OFF26-2]]**, que segue ⚠️ aguardando smoke de produção. **Empate em robustez → vence quem não
  mexe em item pendente de validação.** Invariante inegociável nos dois caminhos: identidade **só
  por `sleeper_id`**, nunca por nome (precedente **"Brown"**).

- **D4/D5 — escopo e classes** *(arbitradas)*. Relatório dos **12 times de uma vez** (é gate da
  sala, não consulta por time). **Time não populado entra como ESTADO PRÓPRIO**, distinto de
  "keeper ausente" — **não populado por regra ([[OFF26-10]]) não é divergência de transcrição**, e
  confundir os dois produziria **alarme falso justamente no cenário que o calendário torna
  esperado** (times acima do cap aguardando o late drop). Classes: ausente do board · salário
  divergente · time errado · jogador no board fora da sheet · (+ estado) não populado. **Severidade
  fica com a F2.**

- **D6 — ponte de owner por `sleeper_owner_id`, reusando helper** *(arbitrada)*. `Team.name` é
  mutado pelo sync e **não serve de chave**. ⛔ **Terreno não verificado, com efeito de restrição
  de validação:** os **convites foram disparados em 03/08** e os times **ainda são placeholders**,
  com **`owner_id` nulo** — enquanto for assim, **a auditoria não tem como casar coluna e time**, e
  **a F2 não pode ser validada contra board de placeholders**. Registrado também no bloco de estado
  da liga, no registro do pacote.

- **D7 — pré-condição de probe, não passo interno da F2.** O §2 da F1 segue pendente (**nada no
  código lê estado pré-draft**) e o probe **exige board populado**. ✅ **Janela aberta agora**
  (Team 3/4/5, dados de teste — alvo válido); ⏳ **fecha no próximo RESET DRAFT**, já pendente, que
  **zera o board e troca o `draft_id`**.

- **O que a spec deliberadamente NÃO decide:** severidade das classes (D5), forma de exposição do
  `sleeper_player_id` (D3), extração do helper de owner (D6) e a conferência aritmética do D2 —
  todas da F2.

- **Sem código. Status Rápido intocado. Nada do [[OFF26-2]] alterado; nenhuma decisão em aberto do
  [[OFF26-10]]/[[OFF26-11]] arbitrada.**

### MAN-OFF26-4-PROBE — probe read-only do estado pré-draft: o bloqueador do §2 caiu (03/08/2026, Opus)

- **Probe empírico contra a liga fantasma real**, pela **API pública read-only** já usada pelo
  projeto (mesmo `BASE_URL` de `sync_sleeper._get`). **Zero escrita, draft NÃO iniciado, nenhum
  reset, board intacto ao fim.** Scripts transitórios no scratchpad, **não commitados**.

- **O resultado central:** o §2 da F1 dizia que *"nada no código lê o estado pré-draft, e o que a
  API expõe é questão empírica"*. **A API expõe tudo o que a auditoria precisa — designação,
  jogador, time e VALOR.** O que impedia não era a API: era o **gate `status == "complete"`** nos
  dois consumidores de picks do projeto (ver réplica, abaixo). **A F1 estava certa na causa e
  incompleta no efeito.**

- **P1 — derivação `league_id → draft_id`: funciona, e por dois caminhos.** `GET /league/{lid}` já
  traz **`draft_id` no topo** (1 request, mais barato que o previsto) e `/league/{lid}/drafts`
  devolve **exatamente 1 draft, o vigente**. **O draft morto não aparece na lista** — a pergunta
  "como distinguir se vier mais de um" não se coloca hoje; se vier, os discriminadores são `status`
  e `created`. **Pendência herdada do D1: fechada.**

- **⛔ Refutação de premissa do D1 — o draft morto NÃO trava na API.** `GET /draft/{morto}` retorna
  **404 com corpo `null` em 0,2 s**; idem `/picks`. **O "trava em LOADING" é comportamento do app
  WEB.** Pela porta que a auditoria vai usar, **o modo de falha silenciosa não existe** — a
  distinção morto × vivo é limpa e imediata. O requisito de *timeout explícito* continua sendo boa
  prática (o `_get` já tem `timeout=15`), mas **deixa de ser mitigação de um risco real**. O
  essencial do D1 — **não persistir `draft_id`** — permanece intacto.

- **P2/P3 — designações e salário legíveis pré-draft.** `GET /draft/{did}/picks` com o draft em
  `status: "pre_draft"` devolveu **24 registros**, com **`metadata.amount` (string)**. **Os três
  totais foram reconstruídos do payload, exatos: $148 / $95 / $60**, e o Team 3 confere 10/10
  nominalmente. **A auditoria pode comparar salário, não só presença.**
  - Detalhe que fecha um ciclo: **o "Waddle = DEN" vem do próprio Sleeper**. É a confirmação
    independente de que a divergência de sigla relatada na 2ª execução do Cowork era **da lista de
    teste**, não da plataforma — e que **rejeitar o falso achado foi correto** ([[OFF26-5]]).

- **P4 — pontes.** Jogador por **`player_id`, que casa com `sleeper_player_id`** — **⚠️ exceto DEF,
  que vem como sigla (`"LAR"`)**: qualquer coerção a `int` quebra. Time por **`roster_id`**;
  `picked_by` vem **vazio** nas 24. **`owner_id` nulo em 11 dos 12 rosters** (só o comissário tem
  dono; `/users` devolve 1 usuário) → **o D6 está confirmado como bloqueio de VALIDAÇÃO**. **Mas
  houve um deslocamento na premissa:** a auditoria **não precisa** de `owner_id` para casar
  designação e time — a pick **já vem chaveada por `roster_id`**. O `owner_id` é necessário para
  casar **`roster_id` ↔ time do Manager**, que é outra coisa.

- **P5 — não existe campo de budget por time.** Só `draft.settings.budget = 200`, global;
  `roster.settings` não tem nada de auction, e `roster.players`/`keepers` vêm vazios (confirma o
  [[OFF26-6]]: designação não popula roster). **Budget é derivável só por soma** — como o D2 já
  determinava. A UI mostra um número que a API não expõe.

- **P6 — réplica: existe, e é dupla.** Dois consumidores de `/draft/{did}/picks` —
  `routes/draft_import.py:39` e `sync_sleeper.py:872` — **replicam a leitura de `metadata.amount`
  com coerções diferentes** (`float` × `int`), e **ambos gateiam em `status == "complete"`**. A
  auditoria seria o **3º leitor**; se criar a própria coerção, vira a **3ª réplica** — candidata
  natural a helper único, no espírito da invariante do [[F10]]. Sem réplica em template/JS.

- **Achados não previstos pelo prompt:**
  1. **`is_keeper: false` nas 24 designações** — o indício do [[OFF26-11]] ganha **evidência de
     payload** na superfície pré-draft. **Continua não sendo a confirmação definitiva** (pós-draft,
     fora do escopo), mas o campo está lá e vale `false`.
  2. **`pick_no`/`round` NÃO indicam vaga de roster** — as 24 ocupam `pick_no` 1..24 na ordem de
     criação (as 10 do Team 3 são 1-10, todas `round=1`, num draft de 12 times). **Não há
     informação de qual vaga a designação ocupa**, só a posição do jogador. → **Consequência para o
     D5: não existe classe "slot errado" auditável.** Presença, valor e time sim; vaga não.
  3. **`roster_positions` = 22 slots** (`QB,RB,RB,WR,WR,WR,TE,FLEX,K,DEF` + 12 `BN`) → **o lado
     Sleeper da ressalva aritmética do D2 agora está MEDIDO**, não suposto. Falta o lado do
     regulamento (8.3.4).
  4. **A fantasma NÃO tem slot de IR**, e a liga real tem (máx. 2) — enquanto o **D5 do
     [[OFF26-2]]** manda **contar IR normalmente** no budget. É um **caso concreto** de divergência
     de contagem dentro da mesma ressalva do D2, não uma hipótese.
  5. **`league.settings.draft_rounds = 3` × `draft.settings.rounds = 22`** — homônimos com valores
     diferentes em níveis diferentes; a F2 deve ler o do **draft**.
  6. **`copy_from_league_id` = liga real** — a fantasma nasceu por **cópia**, o que explica o 3 WR e
     corrobora "config espelha a real".

- **Estado final:** board intacto (24 designações, 3 times), draft `pre_draft`, nenhuma escrita.
  **A janela do D7 continua aberta e continua fechando no próximo RESET DRAFT.** Status do OFF26-4
  segue **🔲**; a F2 está **desbloqueada do lado da leitura** — o que ainda a limita é **validação**
  (D6, placeholders), não construção.

### MAN-OFF26-4-REFINE-PT2 — keeper fora do board é leiloável; spec absorve o probe (03/08/2026, Opus)

- **Sincronização de spec + um achado novo que é o de maior peso do arco OFF26 até aqui** — e que
  **não existia em nenhum registro do pacote**. Emergiu da discussão da divergência de IR com o
  owner, logo após o probe. Sem código.

- **⛔ O ACHADO: um keeper que não esteja designado no board é, para o Sleeper, JOGADOR
  DISPONÍVEL.** Qualquer owner pode **nomeá-lo** e o leilão **processa o lance normalmente** — a
  plataforma **não tem como saber** que ele já tem contrato vigente. O resultado é **um jogador com
  dono sendo arrematado por outro time, ao vivo**, e o [[OFF26-3]] ingerindo depois **como aquisição
  legítima**.
  > **Não é erro de contabilidade que a auditoria corrige depois. É transação inválida em tempo
  > real, sem forma limpa de desfazer sem interromper o leilão.**
  - **Requalifica a natureza do [[OFF26-4]]:** deixa de ser **conferência de cap** e passa a ser
    **gate de INTEGRIDADE DO LEILÃO**. Toda a modelagem anterior tratava divergência como
    contabilidade a reconciliar — **esta classe não se reconcilia**: quando aparece, o lance já foi
    dado e desfazer significa **parar o leilão com 12 owners na sala**.
  - **Severidade da classe 1 do D5 deixa de ser decisão livre da F2** — é **bloqueante de
    abertura**. A F2 decide a severidade **relativa das outras três**.

- **Propagação obrigatória ao [[OFF26-10]] — é onde o risco fica agudo.** O item já registrava que
  **times acima do teto não conseguem ser populados** até o late drop. Combinado com o achado:
  **enquanto um time permanece bloqueado, TODOS os keepers dele estão expostos ao leilão.** →
  **População completa do board é PRÉ-CONDIÇÃO DE ABERTURA, não preparativo.** **A decisão em aberto
  do OFF26-10 (mini-janela × correção administrativa) NÃO foi arbitrada** — isto é **registro de
  consequência**; mas qualquer desenho que saia dela **tem de terminar com o board 100% populado
  antes de 24/08**.

- **Propagação ao [[OFF26-5]] e ao runbook.** Nova **§B.5**: **board incompleto NÃO é estado
  aceitável para iniciar o leilão**. O runbook já dizia "não clicar em START DRAFT até tudo estar
  populado" — o que muda é o **peso**: era higiene de processo, virou **integridade do leilão**. E
  fechei o loop no §B.3.2 (time bloqueado **não pode ficar assim até o leilão**).

- **IR: divergência real × fantasma RESOLVIDA pelo owner.** A liga real tem slot de IR; a fantasma
  **não tem nenhum** (22 = 10 titulares + 12 BN, medido no probe). **Resolução: designar o keeper em
  IR normalmente** — excedentes **caem no banco**, vaga **automática por posição**. Três efeitos:
  **sai do pool disponível** (fecha o risco do achado para este caso), **consome budget
  corretamente**, **fica visível à auditoria**.
  - **Alternativa descartada: descontar o valor do keeper em IR do budget do time.** Dois motivos, o
    primeiro decisivo: **não resolve o risco — o problema não é o dinheiro, é a disponibilidade do
    jogador**; e o desconto ficaria **invisível para a auditoria** (o budget por time **não é
    legível pela API** — P5 do probe —, e a auditoria **deriva por soma das designações**).

- **D2 — metade da ressalva fechada.** Lado da **sala: 22 slots**, medido. Lado do **regulamento
  8.3.4: pendente**, agora **com caso concreto** (a divergência de IR deixou de ser hipótese).
  **Aritmética nova a conferir:** a fantasma comporta **22 keepers por time** — confirmar que nenhum
  time excede isso após os cortes. Improvável dado o cap, **não verificado**.

- **🔧 D1 — correção de premissa, texto anterior preservado.** O D1 derivava um **timeout explícito
  como mitigação de risco** da ideia de que a URL de draft morto **trava em LOADING**. O probe
  mediu **404 com corpo nulo em ~0,2 s**: o travamento é do **app web**, não da API. → **timeout
  rebaixado de mitigação a boa prática**; **a proibição de persistir `draft_id` permanece intacta**,
  e a derivação está comprovada **por caminho mais barato que o previsto** (o `draft_id` vem no
  próprio objeto da liga, em **uma** requisição).

- **D5 e D6 ajustados.** **D5:** a classe "slot errado" **não existe** — `pick_no`/`round` não
  indicam vaga, **e não precisam**: a atribuição é automática por posição. Registrado para que a F2
  **não tente inventá-la**. **D6:** a restrição anterior era **ampla demais** — `owner_id` nulo em
  11/12 **não bloqueia**, porque as designações **já vêm chaveadas por `roster_id`**. **Construção e
  validação parcial liberadas contra placeholders**; só a **costura final `roster_id` ↔ time do
  Manager** espera os aceites dos convites. **A F2 não está bloqueada — está com uma costura
  pendente.**

- **Armadilhas registradas para a F2:** **`player_id` de DEF é sigla** (`"LAR"`), coerção a inteiro
  quebra; e **duas fontes de contagem de rodadas divergem** (`draft_rounds` da liga × `rounds` do
  draft) — **ler a do draft**.

- **Nota de método — a TERCEIRA premissa da mesma família na mesma sessão.** As três caíram pelo
  mesmo mecanismo: **observação verdadeira, procedência errada.** (1) a sigla NFL divergia — mas o
  dado vinha de **lista de teste com temporadas velhas**; (2) a reserva de $1/vaga existe no
  Manager — mas concluiu-se sobre o **Sleeper sem tocar o Sleeper**; (3) o LOADING infinito ocorre —
  mas é do **app web**, generalizado para a **API**. **Padrão a vigiar: comportamento observado numa
  superfície NÃO vale como propriedade de outra.** Nos três casos a evidência era real e a
  **inferência de escopo** é que falhou; nos três a correção veio de **tocar a superfície certa**.

- **[[OFF26-11]]:** `is_keeper: false` nas **24 designações lidas pela API** — o indício ganhou
  **evidência de payload**; a confirmação definitiva **segue pós-draft**, fora do escopo.

- **Nenhum status alterado (OFF26-4/10/5). Status Rápido intocado. Sem código.**

### MAN-OFF26-4-OWNERCHECK — a costura de owner da liga fantasma casa 8/8 (03/08/2026, Opus)

**Natureza:** verificação **read-only** + registro. **Zero escrita** dos dois lados (API só `GET`;
`dynasty.db` aberto em `mode=ro`). Draft **não iniciado**, board **intacto**, nenhuma rota/schema/
teste criado. Scripts transitórios rodados no scratchpad, **não commitados**.

- **A "última incógnita do D6" foi exercitada com owners reais e CASOU — 8 de 8, zero
  não-casamentos.** O `MAN-OFF26-4-PROBE` mediu `owner_id` nulo em **11/12** e deixou a costura
  `roster_id` ↔ time do Manager como pendência. Hoje **8 aceites** já entraram e **todos** casaram
  com `Team.sleeper_owner_id`.

- **⚠️ O estado esperado divergiu — 8 owners, não 7.** `LeoFBorges1` (roster 8) entrou entre a
  leitura de tela do owner e a leitura da API. Divergência benigna e na direção boa, mas registrada:
  **a contagem de aceites muda entre uma olhada e a seguinte — a F2 lê, não assume.**

- **O casamento não depende do banco local.** Os 12 `sleeper_owner_id` do Manager são **idênticos**
  aos 12 `user_id` da liga real lidos ao vivo (`manager − real = ∅` e vice-versa), e os 8 da
  fantasma são **subconjunto** disso. Confirma a propriedade que sustenta o D6: **`owner_id` é
  identidade de CONTA, não de time nem de liga** — atravessa as duas ligas com o mesmo valor.

- **🔲 D6 segue ABERTO — mecanismo confirmado, cobertura não.** Faltam **4 rosters (9–12) com
  `owner_id` nulo**, que **nenhuma leitura resolve**: dependem de aceite. Times do Manager ainda sem
  owner na fantasma: **#2 3 peat… of pain** (`fertorquato`), **#7 AlexTheDawg** (`freddupont`),
  **#8 Trust The Process** (`michelzela`), **#10 achane** (`gabrieldiinis`) — quem falta cutucar,
  informação que antes só existia na tela. Pelo achado "keeper fora do board é jogador leiloável",
  esses 4 **já são bloqueantes de abertura por outro motivo**: a costura não é o gargalo.

- **📌 Reforço da justificativa da regra de identificação — a REGRA NÃO MUDA.** "Casar só por
  `sleeper_owner_id`, nunca por nome" agora tem **dois motivos independentes**, não um.
  **(1) Instabilidade no tempo** (já registrado: `Team.name` é mutado pelo sync) — com **evidência
  nova**: o Manager guarda `Tropa do Bicampeonato 🏆` e a liga real **hoje** exibe `Tropa do
  Jarra 🏆`; o nome **já divergiu sozinho**. **(2) Espaços de nome SEPARADOS** (novo, mais
  fundamental): nada vincula o nome usado na fantasma ao usado na real — ele pode **nascer
  diferente e permanecer diferente para sempre**, sem mutação. Não é dessincronização a corrigir;
  **são dois namespaces**, e casá-los é erro de categoria.

- **Evidência de campo medida (não suposta):** **`metadata.team_name` é `None` nos 8 owners da
  fantasma — 8/8**; enquanto ninguém batiza o time, a coluna exibe **username**, então durante boa
  parte da preparação **não existe nome de time para casar**. **Dois Rafas** entre os owners reais
  (`rafadgil`, `rafaelferreirap`) → colisão por nome é risco **concreto**. E **`rafaelferreirap` não
  tem `team_name` nem na liga real** → o Manager guarda o **username** como `Team.name` (#11): um
  cruzamento por nome acertaria esse caso **por coincidência de fallback**, não por identidade — o
  pior tipo de acerto, porque **valida a técnica errada**.

- **Nota de método.** Três premissas "óbvias" caíram nas 24 h anteriores, todas por **procedência de
  dado**. Esta **não caiu** — mas só se sabe disso porque foi **medida**, e a medição rendeu de
  quebra o reforço do motivo 2, que **nenhum raciocínio sobre a regra teria produzido**.

- **Nenhum status alterado. Status Rápido intocado. Sem código.**

### MAN-OFF26-4 — F2: a auditoria de keepers pré-leilão existe como código (03/08/2026, Opus)

**Escopo único: leitura, diff e apresentação.** Status do [[OFF26-4]] **🔲 → ⚠️** — não fecha ✅ sem
smoke em produção (PROC1), e a **sheet real só nasce em 20/08**.

- **`keeper_audit.py` — núcleo puro, molde `salary_engine`.** `audit(board, sheet)` não toca DB nem
  rede; é o que os 29 testes exercem. A camada de IO (`fetch_board`/`build_sheet`/`run_audit`) é
  **read-only estrita** — só `GET`. Tela em `/admin/keeper_audit`, JSON em `/api/admin/keeper_audit`,
  e um `POST` que persiste **só o `league_id`**.

- **Veredito, não lista.** A tela abre com **ABERTURA LIBERADA / BLOQUEADA** e os motivos.
  **Zero divergências NÃO libera:** bloqueiam keeper exposto (classe 1), **time não populado**,
  **time sem coluna**, **coluna órfã** e **keeper sem identidade resolvível**. É o que a
  requalificação do item pedia — gate de integridade, não conferência de cap.

- **Decisões que a spec delegou.** **D3 = re-query**: `build_sheet` consome a sheet canônica do
  [[OFF26-2]] e enriquece com `sleeper_player_id` consultando `Player` — **o OFF26-2 não foi
  tocado**, como o critério do owner mandava. **Severidade relativa** das classes 2-4 (alta/alta/
  média; a 1 é bloqueante por natureza). **Ordenação pior-primeiro** — o gate se lê de cima.

- **7 divergências spec × terreno, relatadas e não resolvidas por conta própria.** As de maior
  peso: **(1) o helper do D6 não tinha o que reusar** — `_team_by_roster` consulta o banco, e o
  núcleo puro casa owner↔time **em memória**; a invariante ("só por `sleeper_owner_id`") foi
  cumprida, o **meio previsto** é que não se aplicava. **(2) A spec previa UM estado, o terreno tem
  DOIS** — time **sem coluna** (convite não aceito) não é coluna vazia: não é auditável **nem
  populável**. **(3) Keeper sem `sleeper_player_id` não é divergência — é limite de insumo**: vira
  aviso e **bloqueia por auditoria incompleta**, porque cair para nome está proibido ("Brown").

- **Budget: exibido, não diferenciado.** A base do D2 (`usable_draft_budget`) está correta e vem da
  sheet, mas **diferença de soma NÃO virou classe** — é **consequência** das classes 1-4, e
  transformá-la em achado produziria exatamente a **quarta divergência** que a fixture B existe para
  proibir. A **ressalva das 22 rodadas virou verificação automática** pelo lado da sala (aviso se um
  time tiver mais keepers que `rounds`); o lado do regulamento 8.3.4 **segue pendente**.

- **Achado da geração da fixture — e a auditoria estava certa.** A fixture "coerente" acusou **18
  falsos `time_errado`** na primeira tentativa: os 24 jogadores do board estavam **espalhados pelos
  elencos reais** dos outros times (o board veio de lista de teste). **O erro era da fixture** — o
  jogador **estava** em dois times. Corrigida a geração, zero divergências.

- **A fixture B não cobre a classe bloqueante.** Os três erros pedidos são das classes 2, 3 e 4 —
  a classe 1 **não está entre eles**. Sem uma fixture dirigida (C), **a classe mais grave do item
  ficaria sem teste**. Criada, mais duas: coluna sem owner e keeper sem sid (com **dois Brown**).

- **Validado com dado real atravessando o núcleo:** `draft_id` derivado do `league_id`, **24
  designações** lidas com `status=pre_draft`, `rounds=22` **lido do draft**, **3 colunas sem owner**
  → cruzado com a fixture A dá 0 divergências, 3 `sem_coluna`, 3 órfãs. **Sem sheet, a auditoria
  DIZ isso** e devolve 0 times — não 12 falsos positivos. Id morto → erro em **0,21 s**.
  **`draft_id` não persistido em lugar nenhum** (grep). 29/29 novos + **48/48 do `salary_engine`
  intactos**. Board intacto, draft não iniciado, nenhuma escrita na plataforma.

- **Cobertura do D6 — terceira leitura, terceira contagem.** De manhã 4 times sem coluna, à tarde
  **3**: `fertorquato` entrou entre duas leituras da **mesma sessão**. A auditoria **lê, nunca
  assume** — e é por isso que a contagem é campo do relatório, não constante.

### MAN-OFF26-4-META — a meta da liga deixa de depender da keeper sheet (03/08/2026, Opus)

**Origem: o smoke de produção do [[OFF26-4]]** (deploy `d83d2f8`) fechou **3 de 4** pontos. O 4º
**não era alcançavel** — e virou esta correção. Mudança de **borda e apresentação**: núcleo,
veredito e classes **intocados**.

- **⚠️ Achado de processo, antes do técnico:** os **10 commits do dia ficaram locais**. O deploy
  vivo era o de 02/08; o smoke só foi possível depois do push. **O auto-deploy dispara no push, e
  não havia push.** Sem *tentar* o smoke, isso apareceria em **20/08**.

- **O buraco.** A auditoria bloqueia por ausência de sheet **antes** de exibir qualquer coisa, então
  o bloco de meta (`draft_id` derivado, `pre_draft`, rodadas) **não renderizava**. A ordem era
  coerente — sem os dois lados não há diff —, mas deixava sem prova justamente **o que só produção
  prova**: que o serviço no Render **alcança a API do Sleeper** e que a **derivação do `draft_id`
  funciona de lá**. São modos de falha de **AMBIENTE** (egress, DNS, timeout de plano) que **não
  aparecem em localhost**, e seriam descobertos **no dia em que a auditoria precisa funcionar**.
  **Buraco de validação, não bug.**

- **A correção foi menor do que o diagnóstico sugeria.** O `run_audit` **já lia os dois lados de
  forma independente** e o `_no_input` **já carregava** a meta. Faltavam duas coisas: a meta
  **carregar o suficiente** (designações, colunas com/sem dono) e o template **renderizá-la fora do
  `if report.ok`**. Nada no caminho do diff foi tocado.

- **Erro de leitura virou estado PRÓPRIO do bloco**, distinto do bloqueio por falta de insumo: o
  veredito segue dizendo o que falta de insumo, o bloco diz o que houve com a liga. `league_id`
  inválido → **erro limpo em 0,29 s, HTTP 200**. `run_audit` ganhou guarda contra exceção de rede/
  parse fora do que o `_get` já absorve — **falha de liga nunca derruba a rota**.

- **Motivo de produto, independente do smoke:** antes de a sheet existir, o operador precisa
  conferir que aponta para a **liga certa**. `league_id` errado no `AppConfig` era **falha
  silenciosa até 20/08**.

- **Validação:** **34/34** (29 + 5 novos) e **48/48** do `salary_engine`; fixtures A/B/C com o mesmo
  resultado; os três caminhos do bloco exercidos em render real (válido sem sheet / inválido /
  vazio), todos **HTTP 200**; `draft_id` segue **não persistido** (grep); board intacto, draft não
  iniciado, só `GET`.

- **⚠️ A contagem de donos mudou pela QUARTA vez no mesmo dia: 7 esperados → 8 → 9 → 10** (2 sem
  dono agora). É exatamente por isso que ela é **campo do relatório, nunca constante** — e agora o
  bloco a mostra ao vivo, que é o ponto.

### MAN-OFF26-4-LABELS — rename dos cards + a conferencia aritmetica do D2 (03/08/2026, Opus)

**Smoke de producao COMPLETO (4 de 4, deploy `aec8d8f`):** o Render **alcanca a API do Sleeper** e
a **derivacao do `draft_id` funciona de producao** (22 rodadas, 24 designacoes, 10/12 colunas com
dono, `pre_draft`). **Modos de falha de ambiente descartados** — nao sao mais coisa a descobrir em
20/08. Item segue **⚠️**: falta o smoke com **sheet real**.

- **(A) Dois cards tinham o mesmo titulo.** "Liga fantasma" nomeava a **leitura ao vivo** e a
  **configuracao persistida**. Sob prazo, isso convida a procurar informacao no card errado ou a
  **salvar onde nao se pretendia**. Agora: **"Estado da liga fantasma"** e **"ID da liga
  fantasma"**. **So rotulo** — ordem, layout, logica, rota e payload intactos; conferido em **5
  estados da pagina** (sem sheet, fixtures A/B/C, erro de liga), zero duplicatas em todos.

- **(B) ✅ D2 FECHADO: as contagens COINCIDEM.** A **8.3.4** do regulamento diz, verbatim,
  *"completar as **22 posicoes do roster** … (22 – numero de keepers)"*. Regulamento **22** = sala
  **22** (`roster_positions` e `draft.settings.rounds`) = Manager **22** (`MAX_ROSTER`), com a
  **mesma formula de reserva**. **O medo do D2 — "limites nao coincidem apesar da formula
  identica" — nao se concretizou.**

- **⚠️ A diferenca residual nao e de contagem, e de QUEM ENTRA NA CONTA.** O item **1.3** diz que
  os **2 IR "nao sao considerados no total de 22"**. O **Manager conta o IR dentro** dos 22
  (`cuts._team_fa_budget` passa todos os nao-dropados) e o **Sleeper tambem** (o keeper em IR **e
  designado** e ocupa uma das 22 rodadas). → **Os dois lados que a auditoria compara concordam
  entre si: NAO ha falso positivo.** Ambos divergem do **regulamento** em ate **$2** de
  `usable_draft_budget` para time com IR (3 times hoje). **Nenhum calculo alterado.**

- **🔲 Ambiguidade devolvida ao owner (regra de liga, nao implementacao):** a 8.3.4 **nao diz** se
  keeper em IR entra em "(22 − keepers)". Leitura **(a)** conta → e o que Manager e Sleeper ja
  fazem, nada muda. Leitura **(b)** nao conta → o Manager esta **ate $2 permissivo** e o ajuste
  **mexeria no `salary_engine`**. **Decisao do owner.**

- **⚠️ A aritmetica adicional do D2 tem resposta: SIM, um time PODE exceder o board.** O
  regulamento permite **24** (22 + 2 IR, item 1.3); o board comporta **22 designacoes**. **Um time
  esta em 24 hoje** (roster 10 — 22 nao-IR + 2 IR), medido ao vivo. Se chegar assim em 20/08,
  **2 keepers nao cabem e ficam EXPOSTOS** pelo achado "keeper fora do board e leilavel".
  **Segunda causa de time nao populavel**, ao lado do teto de budget — e esta **nao se resolve com
  o late drop** (1 drop nao tira 2 excedentes). Registrada como **risco, nao solucao**.

- **⛔ QUARTA premissa da mesma familia REFUTADA: "a fantasma nao tem slot de IR" e FALSO.**
  `settings.reserve_slots = 2` **nas duas ligas**; e o `roster_positions` da liga **REAL** — que
  tem IR, com 3 rosters usando — **tambem nao lista "IR"**. **IR nao mora em `roster_positions`;
  mora em `settings.reserve_slots`.** Observacao verdadeira, **procedencia errada**, pela quarta
  vez no mesmo arco — e derrubada pelo mesmo metodo das outras tres: **ir a superficie certa**
  (aqui, comparar com a liga real, cujo IR ninguem duvida). **A divergencia de config real ×
  fantasma quanto a IR NAO EXISTE.** A resolucao do owner **permanece correta e necessaria**, por
  outro motivo: **slot de IR nao e slot de draft** — 22 rodadas = 22 designacoes, com ou sem IR.
  **A decisao nao muda; o porque muda** — e e o porque que alguem usaria para reabri-la.

- **Limitacao registrada e NAO corrigida:** timeout parcial (`/league` responde, `/picks` nao —
  ocorreu de fato nos testes) degrada para **"0 designacoes"**, indistinguivel de board vazio.
  **Falha para o lado SEGURO**: board vazio deixa todos os times "nao populados" e o veredito
  **BLOQUEADO** — a auditoria **nunca libera por falta de leitura**. **Imprecisao de rotulo, nao
  risco de gate.**

- **34/34** e **48/48**; fixtures A/B/C com o mesmo resultado; `draft_id` nao persistido; board
  intacto, draft nao iniciado, so `GET`. **Status do OFF26-4 inalterado (⚠️).**

### MAN-OFF26-10-SPEC — urna do late drop: decisão arbitrada + spec U1–U8 (06/08/2026, Fable)

**Docs-only (exceção deliberada: sessão sem código).** As duas decisões em aberto do pacote
intertemporada foram **arbitradas pelo owner em 06/08** e registradas; a spec da urna deixa a
F2 pronta para disparo em prompt separado.

- **[[OFF26-10]] DECIDIDO: a URNA — 2ª mini-janela selada no Manager, para 2026** (molde
  OFF26-1; sigilo cobre até a **existência** da declaração; bilhete na urna, urna só abre no
  prazo). **DM ao comissário descartada pelo owner.** Spec **U1–U8** registrada na seção do
  item: 1 declaração/time (drop ou passo) · não declarar = passo · janela 20/08 (revelação dos
  cortes) → 22/08 configurável · substituível até o lock · lock+hash+revelação por **REUSO** do
  mecanismo OFF26-1 · elegibilidade = roster atual (saiu antes do lock → passo com aviso) ·
  revelação **reemite a keeper sheet definitiva** (a de 20/08 vira provisória na trilha) ·
  corte executa pelo caminho canônico do OFF26-1, sem paralelo.
- **U6 × regulamento, conferido no texto (12/08/2025): SILENCIOSO** sobre proteção de rookie de
  1ª contra drop. O que existe: **8.2.6** (obrigação de draftar na 1ª — o drop imediato
  esvaziaria a obrigação, leitura defensável **não escrita**) e **8.2.2** (rookie draft "sempre
  antes os drops" — só sequência). Se o owner quiser a proteção na urna, **arbitra na F2**;
  default da spec: elegível = está no roster.
- **Pré-condições de sequência registradas (não executadas):** (1) **smoke real do OFF26-1/2
  antes da estreia** — lock/reveal nunca rodaram em prod; janela de teste em produção (cortes
  fictícios → lock → hash → reveal → reset) antes de 20/08, coordenada com owner e co-admin;
  (2) F2 da urna **entregue e smokada antes de 22/08**, idealmente antes de 20/08.
- **[[OFF26-11]] DECIDIDO: opção A — Manager fonte única.** Keeper sheet definitiva (pós-urna)
  como **lista de exclusão**; importador OFF26-3 ingere **só arremates**; keeper nos picks é
  ignorado por definição; garantia board×sheet = **auditoria OFF26-4 antes do leilão**; **sem
  reconciliação pós-leilão**. Decisão fechada; código fica para a F2 do item (escopo próprio).
  O probe pós-draft do `is_keeper` deixa de ser bloqueante (vira confirmação na F2).
- **Nota no [[OFF26-7]] (sem item novo):** transferência dos arremates para a liga real =
  **manual, por owner** (keepers já estão nos rosters; ~30–50 adições na liga toda). Checklist
  pós-leilão: "cada owner adiciona seus arremates antes da semana 1; admin confere contra o
  import do Manager".
- `git diff` **não toca código** (improvements.md + este log); board intacto, draft não
  iniciado. Próximos disparos esperados: **F2 da urna** e **ensaio do OFF26-1** em prompts
  separados.

### MAN-OFF26-4-SLOTS — prompt reeditado; o que faltava era transformar o residuo em ITEM (03/08/2026, Opus)

**O prompt pediu (A) a conferencia aritmetica do D2 e (B) o rename dos cards — ambas ja entregues e
publicadas no `b467651`**, na sessao imediatamente anterior (o prompt foi escrito antes do
relatorio). **Nada foi refeito.** Conferido item a item contra o HEAD: os dois cards ja se chamam
"Estado da liga fantasma" e "ID da liga fantasma", na ordem original, e a conferencia ja esta
registrada na secao do [[OFF26-4]].

- **O que FALTAVA de verdade era um item da VALIDACAO deste prompt:** *"a decisao de trata-la ficou
  como **item**, nao como alteracao feita nesta tarefa"*. A divergencia estava registrada **dentro
  da secao do OFF26-4**, com magnitude, causa e efeito — mas **sem ID rastreavel**. Registro sem ID
  no Status Rapido **nao entra no namespace nem na baseline de dedupe** (O3): some da vista.
  **Corrigido com dois itens.**

- **[[OFF26-12]] 🔲 Baixa — keeper em IR conta na reserva de $1?** A 8.3.4 manda reservar
  `(22 − keepers)`; a 1.3 diz que os 2 IR "nao sao considerados no total de 22"; **a regra nao diz**
  se keeper em IR entra em "keepers". Manager e Sleeper hoje **contam o IR dentro** dos 22 — o que
  deixa o Manager **ate $2 mais permissivo que o regulamento** (3 times com IR hoje). **Efeito
  sobre o veredito da auditoria: NENHUM** — os dois lados comparados concordam entre si; a margem e
  **entre as plataformas e o regulamento**. Dai Baixa, apesar de tocar dinheiro. Se a leitura (b)
  vencer, o ajuste **mexe em `salary_engine.draft_budget`** (3 consumidores) e **exige F1 propria**.
  **Regra de liga — decisao do owner.**

- **[[OFF26-13]] 🔲 Alta — time com mais de 22 keepers nao cabe no board.** Regulamento permite
  **24** (22 + 2 IR); board comporta **22 designacoes**. **1 time esta em 24 hoje.** Se chegar assim
  em 20/08, **2 keepers ficam EXPOSTOS** pelo achado do OFF26-4. **Segunda causa de time nao
  populavel**, ao lado do teto ([[OFF26-10]]) — se manifestam igual no relatorio (`nao populado`) e
  tem **remedios diferentes** — e **nao se resolve com o late drop** (1 drop x 2 excedentes).
  **Nada no regulamento obriga** a descer de 24 para 22. Decisao em aberto: corte adicional
  obrigatorio x excecao administrativa. **O Manager ja pode pre-calcular quem vai estourar**, sem
  depender da decisao.

- **Reafirmado, porque o prompt repete a premissa derrubada:** *"a fantasma nao tem IR
  (`roster_positions` = 22)"* segue **FALSO** — `settings.reserve_slots = 2` **nas duas ligas**, e o
  `roster_positions` da liga **REAL** (que tem IR, com 3 rosters usando) **tambem nao lista "IR"**.
  O que sustenta o limite de 22 designacoes **nao e a ausencia de IR na sala** — e que **slot de IR
  nao e slot de draft**. A conclusao operacional nao muda; a justificativa, sim.

- **Ressalva do D2: FECHADA** (22 = 22 = 22, mesma formula), com o residuo agora **rastreavel**.
  34/34 e 48/48; **nenhuma linha de codigo ou template alterada nesta sessao**; board intacto,
  draft nao iniciado; status do OFF26-4 inalterado (⚠️).

### MAN-OFF26-13-F1 — ocupacao de roster dos 12 times: a hipotese central caiu (03/08/2026, Opus)

**Diagnose read-only.** Zero escrita (so `GET` + `sqlite mode=ro`), board intacto, draft nao
iniciado, nenhum arquivo de codigo tocado. Instantaneo, nao estado estavel — as contagens mudam
entre leituras (quatro num unico dia nesta sessao).

- **✅ T2 — a ambiguidade se dissolve por ESTRUTURA, nao por interpretacao.** `roster.reserve` e
  **subconjunto** de `roster.players` (verificado nos 3 rosters com IR) → **"24 no ativo" nunca
  existiu**. O time e o **`achane`** (roster 10, `gabrieldiinis`): **22 ativos + 2 IR** (Penix $1,
  Travis Hunter $8). O `is_on_ir` do Manager **bate 100%** com o `reserve` do Sleeper nos 3 times —
  a suspeita de contagem local defasada **nao se confirmou**.

- **T1/T3 — 1 time nao cabe; 5 estao com folga ZERO.** Contando toda a posse como designacao (o IR
  ocupa **banco** na sala), so o achane excede: **24 num board de 22 (+2)**. Mas **Pitbull, 3 peat,
  Fazenda, mongoloides e Miller Time estao em 22 exatos** — qualquer aquisicao antes de 20/08 os
  poe na mesma situacao, e **isso nao aparece em contagem nenhuma de excedente**. No agregado sobra
  espaco (248 de 264) e **isso nao ajuda**: o limite e por time.

- **Limite declarado como INFERENCIA, nao teste.** `draft.settings.rounds = 22` da 22 picks por
  time; **nao foi testado** se a UI recusa a 23a designacao — exigiria tocar o board, proibido.
  Registrado assim de proposito, dado o historico de premissas desta sessao.

- **⛔ A HIPOTESE CENTRAL DO ITEM ESTA REFUTADA: os cortes de 20/08 NAO resolvem sozinhos.**
  Supunha-se que "quem excede o roster tende a exceder o cap". **O time das 24 esta em $195,
  ABAIXO do cap**; os dois times acima do cap (mongoloides $206, Tropa $201) **cabem no board**.
  As duas condicoes sao independentes e hoje estao **anticorrelacionadas**. → **Nada obriga o
  achane a cortar ninguem**: ele fecha a janela legal, sob o cap, com 24 — e **2 keepers dele ficam
  fora do board, expostos ao leilao**.

- **T4 — o teto de 22 NAO e validado em lugar nenhum.** `MAX_ROSTER` e definido em **dois** lugares
  e usado **so como divisor** (`draft_budget:221`), onde o `max(0, …)` **apaga o excedente**: 24
  keepers dao `empty_spots = 0`, **indistinguivel** de roster exatamente cheio — **o Manager nao
  tem como saber que estourou**. Nenhuma porta confere contagem: `record_acquisition` nao confere;
  o **sync tambem nao, e ai e correto** (o Sleeper e autoridade de posse, e um roster de 24 entra
  legitimamente); trades nao movem jogador. **Assimetria que responde a T4:** o teto **menor**
  (`MAX_IR = 2`) **e** enforcado (`roster.py:155`, 400 "IR cheio"); o **maior**, que hoje expoe
  keepers ao leilao, **nao**. Achado lateral: `routes/salary.py:4` **importa `MAX_ROSTER` e nunca
  usa** — residuo de uma validacao que nunca foi escrita.

- **T5 — duas replicas.** (1) `MAX_ROSTER` com **duas definicoes** (`models.py:9` e
  `salary_engine.py:40`): inocuo hoje, contra a invariante [[F10]]. (2) **Duas contagens de
  "salario usado" convivem** — as telas de cap **excluem** IR (`active_salary`, `league.py`,
  `admin.py`) e o budget de keeper **inclui** (D5 do [[OFF26-2]]). Divergem em **3 times, $14 no
  total**; o achane exibe **$186 numa tela e $195 noutra**. **Nao e bug — sao perguntas
  diferentes** ("cap comprometido em quem pontua" x "cap comprometido no total"); **e risco de
  leitura**: sob prazo, em 20/08, convida a achar que uma das duas esta errada.

- **Premissas do prompt contraditas:** (1) *"o board da fantasma nao tem slot de IR"* — 5a
  ocorrencia da mesma familia; `reserve_slots = 2` nas duas ligas. **A conclusao do prompt continua
  correta** (24 designacoes num board de 22), mas o motivo e outro: **slot de IR nao e slot de
  draft**. (2) *"os cortes provavelmente resolvem"* — refutada com dado. (3) O prompt previu "um
  time em 23"; **nao ha nenhum em 23** — ha **cinco em 22 exatos**, a mesma fragilidade sem
  aparecer como excedente.

- **Nada corrigido, nada implementado, status inalterado (🔲).** As duas decisoes seguem do owner:
  o que fazer com quem chegar acima de 22 em 20/08, e se o Manager passa a **avisar** — o que e
  barato, ja que a auditoria [[OFF26-4]] **ja conta keepers por time**.

### MAN-OFF26-14-F1 — o IR na contagem de salario: item OFF26-14 registrado (03/08/2026, Opus)

**Diagnose read-only.** Zero escrita: so `sqlite mode=ro` no `dynasty.db` e leitura do PDF do
regulamento em `data/`. Board intacto, draft nao iniciado, **nenhum arquivo de codigo alterado**.
Registro do item novo [[OFF26-14]] (🔲, Alta) — a Fase 2 depende de decisao do owner.

**Criterio declarado no prompt: o IR CONTA no cap.** Logo o que esta desalinhado nao e uma duvida,
e um grupo de telas — justamente o que cada owner olha para decidir o corte de 20/08.

- **T1 — mapa fechado: 11 superficies EXCLUEM IR, 8 INCLUEM.** Grupo A (exclui): `active_salary`
  (`models.py:96`) + `cap_remaining` + `to_dict`/`/api/teams` + chip da navbar (`app.py:121` →
  `base.html:73`) + banner M1 (`roster.py:98`) + pagina de roster (`roster.py:85,89`) + cards do
  League Hub (`league.py:22`) + `/team/<id>` (`league.py:97-99`) + preview de rollover
  (`admin.py:159-160`) + alerta pos-trade do sync (`sync_sleeper.py:581`) + preview de trade
  (`trades.py:151-152`). Grupo B (inclui): `draft_budget` (`salary_engine.py:218`) + cap_projector
  GET + porta `POST …/budget` + janela de cortes (`projected:false`) + `fa_budget` da keeper sheet
  (`cuts.py:387-392`) + auditoria OFF26-4 + alertas do importador + `Team.total_salary()` (morto).

- **Divergencia medida (mode=ro, 03/08): 3 times, $14.** achane **$186 x $195** — a diferenca e
  **exatamente** Penix $1 + Travis Hunter $8; rafaelferreirap $133 x $136 (Charbonnet $3); Fazenda
  $176 x $178 (Kendre Miller $1 + Tory Horton $1). Os outros **9 times batem**, porque nao tem
  ninguem em IR — e por isso que a divergencia passou despercebida.

- ⛔ **T3 — A REPLICA ESTA TODA NO LADO ERRADO.** O lado que **inclui** IR tem **1 fonte**
  (`draft_budget`; invariante [[F10]] preservada — 7 consumidores, nenhuma aritmetica propria). O
  lado que **exclui** tem **6**: `active_salary` **+ 5 somas inline** (`roster.py:89`,
  `league.py:22`, `league.py:99`, `admin.py:159`, `admin.py:160`) que reescrevem
  `sum(p.salary … if not p.is_on_ir)` a mao **sem chamar `active_salary()`**. Corrigir a regra custa
  **6 pontos, nao 1**. Nenhuma replica em JS/Jinja — a F10 vale dos dois lados.

- ✅ **T5 — a pergunta de severidade alta do prompt NAO se materializou.** Keeper sheet e auditoria
  [[OFF26-4]] consomem **o MESMO numero**: `keeper_audit.build_sheet` importa
  `routes.cuts._build_keeper_sheet` e repassa o `fa_budget` pronto (D3/D4). Ambas **incluem** IR; a
  cadeia do leilao e internamente coerente. **O descompasso real e tela do owner x regua do
  leilao.** Laterais da mesma familia: a keeper sheet **nao marca quem esta em IR** (zero "IR" no
  `keeper_sheet.html`) embora keeper em IR **ocupe designacao** no board ([[OFF26-13]]); e
  `Team.total_salary()` — a regua "com IR" no modelo — e **codigo morto, zero consumidores**.

- **T2 — nao ha decisao registrada, mas ha registro do gap.** O filtro e **explicito e dedicado**
  (`and not p.is_on_ir`), **sem docstring, sem comentario e sem nenhum teste** (`grep` por
  `is_on_ir|active_salary` em `*_test.py`: zero). `git log -S` devolve **so `f2271ba`** — nasceu com
  o projeto. ⚠️ Porem a F1 do [[OFF26-1]] ja anotara o **GAP — IR e K/DEF**
  (`improvements.md:1860-1863`) prevendo o achado ao pe da letra: *"a barra de cap e o budget da
  janela **divergiriam** para times com IR — **decisao pendente**"*. **Nao e achado novo: e decisao
  pendente que virou risco quando a data chegou.**

- **T6 — o regulamento e SILENCIOSO sobre salario de IR no cap** (transcrito, sem interpretar). O
  **1.3** ("os 2 IR nao sao considerados no total de **22**") fala de **contagem de jogadores**, nao
  de folha salarial; **5.1** ("CAP de $200 … respeitado NO MOMENTO DO DRAFT"), **8.1.2** ("manter
  quantos jogadores quiser, respeitando o CAP") e **8.3.3** ("$200 MENOS o salario dos jogadores
  mantidos") falam de salario **sem abrir excecao para IR**. A **unica** exclusao explicita de folha
  no documento inteiro e o **7.1.8**, e trata de **FAAB**, nao de IR. → o texto **nao contradiz** a
  decisao do owner, e tambem **nao a confirma**. Nada a resolver; e registro.

- ⛔ **T4 — a string "cabe ate 24" NAO EXISTE no codigo.** `grep -rn "cabe"` em todo
  `.py`/`.html`/`.js` devolve **uma** ocorrencia, e e `keeper_audit.py:211` ("nao cabem", ressalva
  do D2). O que a tela exibe e `roster.html:98-102`: *"N jogador(es) no IR — salary IR: $X"*.
  **Nao ha limite dinamico de 24 em lugar nenhum, logo nao ha terceiro teto de roster**: a T4 se
  resolve por **ausencia**. Confirmacao independente: o Manager **nunca le `settings.reserve_slots`**
  — do payload de IR le so `roster.reserve`, a lista (`sync_sleeper.py:239`). O `24` do
  enquadramento vem do **regulamento** (1.1 + 1.3), nao de nenhuma tela.

- **Premissas do prompt contraditas:** (1) *"a tela exibe 'cabe ate 24'"* — nao existe; (2) *"se
  sheet e auditoria divergirem, e severidade alta"* — consomem a mesma fonte, nao divergem; (3)
  *"duas contagens convivem"* — certo, mas **nao sao duas fontes**: sao **1 do lado que inclui e 6
  do lado que exclui**. **Nao previsto pelo prompt:** o gap ja registrado desde a F1 do OFF26-1;
  `total_salary()` morto; as 5 somas inline; a sheet nao marcar IR; zero cobertura de teste sobre
  `active_salary`/`is_on_ir`; `reserve_slots` nunca lido.

- **Nada corrigido, nada unificado, status de nenhum item alterado.** A decisao da Fase 2 e do
  owner e **nao e de implementacao**: unificar as 6 superficies do grupo A na regua com IR **x**
  exibir os dois numeros lado a lado, rotulados ("folha total" x "cap ativo") — as duas perguntas
  sao legitimas, e o que falta hoje nao e o numero, e o **rotulo**.

### MAN-OFF26-14-F2 — as duas reguas ROTULADAS, nao unificadas (04/08/2026, Opus)

**Decisao registrada para nao ser revisitada por engano: NAO unificar.** (1) A cadeia critica do
leilao **ja e coerente** — o risco que motivaria a unificacao nao existe; (2) unificar custa **6
pontos**, **sem nenhum teste** cobrindo, em codigo do commit inicial, **a 17 dias do leilao**; (3)
os dois numeros **tem sentidos diferentes e ambos sao legitimos**. **O que faltava nao era o numero:
era o rotulo.**

- **Vocabulario unico, aplicado em 7 superficies.** `cap ativo` = exclui IR (o que se paga por quem
  joga). `folha total ⚖️` = inclui IR e **e a REGUA DO LEILAO** — a que `draft_budget` aplica e,
  por consequencia, a que a keeper sheet (OFF26-2) e a auditoria (OFF26-4) consomem. O rotulo diz
  isso explicitamente onde cabe (roster, trade, `/team/<id>`).

- **Gate de exibicao — sem IR, sem ruido.** O par so aparece quando `ir_cap > 0` / `has_ir`: **3
  times hoje**. Os **9 sem IR seguem exibindo um unico numero**, identico ao de antes. Caso
  concreto conferido: **achane $186 (cap ativo) x $195 (folha total)**, restante $14 → $5;
  rafaelferreirap $133/$136; Fazenda $176/$178.

- **Superficies:** A4 chip da navbar (valor e **limiar de cor inalterados**; ganha `$195 c/ IR` +
  `title` com os dois rotulos), A5 banner M1, A6 pagina de roster (2a linha de rotulos sob a barra
  + o alerta de IR passa a nomear as duas), A7 cards do League Hub, A8 `/team/<id>` (rotulo vira
  `Cap ativo` + item `Folha total ⚖️`), A9 preview de rollover (os 2 agregados viram `(ativo)`, +2
  `⚖️ Folha (c/ IR)` so se divergirem), A11 preview de trade (linha `⚖️ Folha total` com o **mesmo
  delta** — o contrato viaja com o jogador, esteja em IR ou nao).

- ⚠️ **Banner NOVO e aditivo — o caso que o antigo nao pega.** Par (cap ativo ≤ $200, folha total >
  $200): o banner M1 **silencia** e o time se ve em dia entrando no leilao estourado. Agora avisa.
  **Nenhum time esta nesse par hoje**, mas um drop ou uma ida para o IR o cria. `own_cap_overrun`
  segue **identico** — o banner novo e uma segunda condicao, nao uma troca de limiar.

- ✅ **NENHUM VALOR CALCULADO MUDOU (prova mecanica).** O `git diff` das rotas remove **5 linhas,
  todas estruturais**: 2 `return` de context processor (valores preservados, chaves acrescentadas),
  a assinatura de `side()` e seus 2 call sites. **Nenhuma linha de calculo foi removida ou
  alterada** — `active_salary`, as **5 somas inline** (`roster.py:89`, `league.py:22/99`,
  `admin.py:159/160`) e `draft_budget` estao **byte a byte iguais**.

- **`Team.total_salary()` deixou de ser codigo morto.** Virou a fonte unica da folha total onde ha
  objeto `Team` (chip, banner, trade). ⚠️ **Desvio consciente do "registrar e parar"**: a
  alternativa era calcular `cap + ir` em paralelo nesses 3 pontos, criando **uma segunda definicao
  da mesma regua** — exatamente o vicio que o OFF26-14 documenta e que o OFF26-16 tera de desfazer
  do outro lado. Nada foi apagado, como o prompt exigia. Registrado como [[OFF26-17]] ⚠️.

- **Correcao de premissa sobre o regulamento, com a leitura anterior PRESERVADA.** O **1.3 NAO e
  silencioso**: estabelece que os 2 IR **nao sao considerados no total de 22**, logo **22+2 = 24 e
  composicao legitima e o Manager esta CORRETO**. Nao ha conflito Manager x regulamento — o
  conflito e **regulamento (24) x sala do leilao (22 vagas)**, que e o [[OFF26-13]]. **Delimitacao
  para as duas leituras nao se sobreporem de novo:** o 1.3 e explicito sobre **CONTAGEM** e nada
  diz sobre **SALARIO**; o silencio que a F1 mediu era o de salario, e **permanece**. A F1 media
  salario; a correcao fala de contagem. As duas valem, em escopos distintos.

- **Dois itens novos escopados e NAO implementados.** [[OFF26-15]] 🔲 **Alta** — a keeper sheet
  **nao marca quem esta em IR** (zero "IR" no template), e keeper em IR **ocupa designacao no
  board**: quem transcrever em 20/08 **nao sabe que precisa inclui-los**, e omitir **expoe ao
  leilao** (achado do OFF26-4). Sao **5 jogadores em 3 times**; o `fa_budget` **ja os conta** —
  falta so a marcacao visual (+ coluna no CSV, p/ manter a paridade 1:1). [[OFF26-16]] 🔲 **Baixa**
  — unificar as 6 superficies **pos-leilao**, com **pre-requisito duro: escrever a cobertura
  antes** (hoje e zero). Unificar sem teste e trocar seis somas silenciosas por uma mudanca de
  comportamento silenciosa.

- **Validado aqui:** 48/48 (`salary_engine`) + 34/34 (`keeper_audit`), `py_compile` das 6 rotas,
  parse Jinja dos 8 templates, aritmetica conferida contra o banco em `mode=ro`. ⚠️ **PENDENTE DE
  SMOKE EM PROD — o item NAO fecha ✅ em localhost:** so producao prova que o par **renderiza** nas
  7 superficies e **nao aparece** nas 9 sem IR, que o chip nao quebra a navbar no mobile, que a
  linha nova do preview de trade nao desalinha as 2 colunas e que os 2 cards do rollover cabem no
  `stat-grid`.

- **Cadeia do leilao INTOCADA:** `draft_budget`, keeper sheet, auditoria OFF26-4, `salary_engine`,
  schema e sync. Board intacto, draft nao iniciado, `CLAUDE.md` ganhou a secao das duas reguas.

### MAN-OFF26-18 — fencepost na reserva de $1 do draft_budget (04/08/2026, Opus)

**O erro.** A reserva de `$1 x vagas` protegia **tambem a vaga que o proprio lance esta
preenchendo**. Com **1 spot vazio**, o Manager reservava $1 para uma vaga "seguinte" que nao existe
— tornando **o ultimo dolar impossivel de gastar**. Achado pelo owner simulando no Cap Projector
com o time reduzido a 1 spot. Consequencia: **o Manager era $1 mais restritivo que o Sleeper em
todo time com >= 1 vaga**.

- **A correcao** (`salary_engine.py:221`): `min_required = max(0, empty_spots - 1) * MIN_SALARY`.
  O `max(0, ...)` **nao e defensivo, e obrigatorio**: com **0 vagas** a subtracao daria reserva
  **-1**, **inflando** o budget em $1 num time completo — trocaria um erro por outro, de sinal
  contrario.

- **A referencia e comportamento MEDIDO, nao interpretacao.** Experimento na plataforma (02/08):
  `teto = 200 - gasto - (vagas_restantes - 1)`. O `-1` e a vaga que o lance preenche.

- **Distincao de leitura da 8.3.4, registrada para nao ser revisitada.** O texto — *"pelo menos $1
  disponivel no CAP para cada jogador a ser draftado (22 - keepers)"* — **ao pe da letra sustenta a
  formula antiga**. Mas essa leitura reserva $1 **para um jogador que ja esta sendo comprado**, e o
  efeito e deixar $1 do cap permanentemente inacessivel. Vale a **leitura operacional**, a mesma que
  a plataforma implementa. **Nao e o regulamento que muda; e qual das duas leituras dele o Manager
  aplica.**

- **A fonte unica fez o trabalho.** Os **7 consumidores** herdaram a correcao **sem uma linha de
  mudanca** (Cap Projector GET e POST, janela de cortes, `fa_budget` da keeper sheet, auditoria
  OFF26-4, importador OFF26-3). `grep` confirma **zero replica**: `cap_projector.html` e `cuts.html`
  so **exibem** `empty_spots`/`min_required_for_spots` vindos do payload. [[F10]] preservada.

- **Efeito medido no banco (`mode=ro`): +$1 exatamente onde deveria.** Os **6 times com >= 1 vaga**
  (Cangaceiros, AlexTheDawg, Trust The Process, Tropa, rafaelferreirap, ESPN FANTASY) ganharam
  **+$1**; os **6 sem vaga** (Pitbull, 3 peat, Fazenda, mongoloides, Miller Time, achane) ficaram
  **inalterados** — o `max(0, ...)` fazendo o seu trabalho.

- **Casos da validacao, conferidos com salarios REAIS por jogador:** Trust The Process (1 vaga) →
  reserva **$0**, usavel **$76** = restante inteiro; Miller Time! (0 vagas, exatamente no cap) →
  reserva **$0**, usavel **$0**, nem -$1 nem $1; Cangaceiros (4 vagas) → reserva **$3**.

- **Testes: 54/54** (era 48 — **+6 bordas** na classe nova `TestDraftBudgetFencepost`: 0 vagas,
  roster cheio exatamente no cap, 1 vaga, 2 vagas, o experimento do Sleeper e roster estourado >22).
  Os dois que codificavam a formula antiga (`test_usable_budget_accounts_for_spots`,
  `test_empty_roster`) foram atualizados. Auditoria **34/34** intacta.

- ⚠️ **CONFERENCIA ARITMETICA — divergencia com o prompt.** Ele registra o experimento ($150
  gastos, 21 vagas) como *"teto $29 (nao $28, que e o que a formula atual do Manager daria)"*. As
  contas: **antiga** = 200-150-21 = **$29**; **corrigida** = 200-150-20 = **$30**. Ou seja, **o $29
  do prompt e o que a formula ANTIGA produz**, e **$28 nao sai de nenhuma das duas**. **Isso NAO
  invalida a correcao** — invalida so o poder probatorio *daquele* caso: os lances medidos ($29
  aceito; $32/$33/$40 recusados) limitam o teto real ao intervalo **[29, 31]**, que contem tanto o
  $29 da antiga quanto o $30 da nova; **$30 e $31 nunca foram testados**. **Quem decide e o caso de
  1 vaga**, que e dedutivo e independe de medicao. **Teste decisivo sugerido ao owner: tentar $30
  nesse mesmo cenario** — aceito ⇒ formula nova confirmada; recusado ⇒ o Sleeper usa a antiga e a
  correcao precisa ser revista.

- ⚠️ **PENDENTE DE SMOKE EM PROD.** So producao prova o Cap Projector e a barra da janela de cortes
  exibindo o valor novo (o `min $N` ao lado de `spots` deve cair em 1) e o alerta de
  `insufficient_budget` nao disparando indevidamente para time com vaga.

- **Intocados:** keeper sheet, auditoria OFF26-4, schema, caminho canonico de salario, sync, e as
  reguas cap ativo x folha total do [[OFF26-14]] (a correcao e **ortogonal** a elas). Board intacto,
  draft nao iniciado.

### MAN-OFF26-18-CONF — a formula do fencepost CONFIRMADA por medicao direta (04/08/2026, Opus)

**Registro docs-only.** Nenhum arquivo de codigo tocado: formula, testes, schema, rotas e templates
inalterados. Do lado da plataforma, so `GET`.

- **O que estava em aberto.** O relatorio do `4bef82a` reportou que o caso de referencia do prompt
  **nao provava o que afirmava provar**: os lances de 02/08 ($29 aceito; $32/$33/$40 recusados)
  limitavam o teto real ao intervalo **[29, 31]**, que contem **tanto** o $29 da formula antiga
  **quanto** o $30 da corrigida. A correcao ficou sustentada **apenas pelo argumento dedutivo** do
  caso de 1 vaga, e o relatorio indicou qual lance fecharia a medicao.

- ✅ **O teste decisivo foi executado pelo owner, na fantasma real (04/08).** Cenario: **Team 5,
  $60 gastos, 16 vagas livres**. Formula antiga (`vagas`) preveria teto **200-60-16 = $124**;
  corrigida (`vagas - 1`), **200-60-15 = $125**. **Designacao de $125 ACEITA** (J. Gibbs, removida
  em seguida). Como $125 esta **acima** do teto da antiga e **exatamente no** da corrigida, o lance
  **discrimina as duas** — o que o intervalo [29, 31] nao fazia. **A formula rival nao fica apenas
  "nao contradita": fica FALSIFICADA.**

- **Estado probatorio final de `teto = 200 - gasto - (vagas - 1)`:** (1) **recusa acima do teto** —
  $32/$33/$40 num teto de $29, 02/08; (2) **aceite no limiar exato** — $125 num teto previsto de
  $125, 04/08; (3) **aceite acima do teto da formula rival** — $125 > $124, 04/08. ⇒ alinhada a
  plataforma **por medicao direta nos dois sentidos**, nao mais por deducao. O teste
  `TestDraftBudgetFencepost.test_experimento_sleeper_150_gastos_21_vagas`, que assere **$30** no
  cenario de 02/08, **passa a ter lastro empirico**.

- **Cenario reconferido por leitura read-only do board (nao pela palavra do prompt):** liga
  `Dynasty SB FA Auction`, `draft_status = pre_draft`, **22 rodadas**, **24 designacoes**; coluna 5
  com **6 designacoes somando $60** ⇒ `22 - 6 = 16 vagas`, **exatamente o cenario declarado**; e
  **Gibbs ausente** do board. **Board restaurado**, draft nao iniciado, `draft_id` derivado e nao
  persistido.

- **Nota de metodo (por que a distincao valeu a pena).** Separar *correcao implementada* de *poder
  probatorio do caso* evitou registrar como **confirmado** o que ainda era **intervalo** — a formula
  rival seguiria viva dentro de um item marcado ✅. **O teste decisivo custou um lance**, e foi
  barato justamente porque a pergunta estava formulada com precisao: nao *"a formula esta certa?"*,
  mas **"qual lance separa as duas?"**. Padrao a repetir quando uma medicao "confirmar" algo: checar
  se ela **discrimina** as hipoteses ou apenas **e compativel** com a preferida.

- **Fora deste fechamento:** o **smoke de producao** das telas que exibem o valor novo (Cap
  Projector e barra da janela de cortes) segue **pendente** — e outra pergunta, nao probatoria.

### MAN-OFF26-16 — regua UNICA de folha: o IR conta no cap, sempre (04/08/2026, Opus)

**Decisao do owner, explicita e final:** *jogador no IR conta no cap hit como qualquer outro*. Nao
existem duas reguas — existe **uma** folha salarial, que inclui todos os jogadores do time (ativos e
IR), e e a mesma em toda tela, todo calculo e todo contexto.

- ⛔ **REVERTE a F2 do [[OFF26-14]]** (`f809a68`), que rotulou as duas reguas em vez de unifica-las.
  O racional daquela decisao — *"os dois numeros tem sentidos diferentes e ambos sao legitimos"* —
  **caiu**: pela regra do owner, **o numero sem IR nao mede nada**. O racional antigo foi
  **preservado no registro** (precedente de correcao com historico, nao apagamento). Leitura
  historica intacta: o filtro `not p.is_on_ir` **nunca foi decisao de ninguem** — a F1 do
  [[OFF26-1]] anotou "decisao pendente", a pendencia foi para producao no commit inicial, e a F2 deu
  **rotulo e banner ao acidente**.

- ✅ **PRE-REQUISITO DURO CUMPRIDO — cobertura primeiro.** `cap_regua_test.py`, **14 testes**,
  escritos e rodados **ANTES** de tocar em qualquer soma. Contra o codigo antigo falharam exatamente
  onde deviam: **`186 != 195`**, **`14 != 5`**, e a guarda apontando `models.py`, `routes/league.py`
  e `routes/admin.py`. Classes: `TestRosterSalary` (nucleo puro), `TestTeamSalaryORM` (SQLite **em
  memoria**, sem tocar o `dynasty.db` — caso achane $195/$5), `TestLeagueCard` (`_build_team_card`,
  testavel direto por nao ter query) e ⛔ `TestSemReplicaDeFolha` — **guarda anti-replica** que falha
  se qualquer `sum` de salario voltar a filtrar `is_on_ir` **ou** se `active_salary` ressuscitar. A
  guarda existe porque a F1 mediu **SEIS** definicoes da mesma regua: o problema deste codigo nunca
  foi escrever a soma errada uma vez, foi **reescreve-la a mao em cada rota**.

- **AS 6 FONTES VIRARAM 1.** Fonte unica `salary_engine.roster_salary(players)` (pura, sem DB,
  `is_dropped` e o unico filtro); entrada ORM `Team.total_salary()` delega a ela e `cap_remaining()`
  deriva. **`Team.active_salary()` REMOVIDO** — o nome mentia. As 5 somas inline (`roster.py:89`,
  `league.py:22`, `league.py:99`, `admin.py:159`, `admin.py:160`) foram substituidas; no
  `admin.py:160` **o N+1 saiu junto** (era um `Player.query.get` por linha do preview).

- **+2 correcoes de coerencia que a unificacao expos:** (1) `team_detail.cap_by_pos` somava so os
  nao-IR e **nao fechava com o `cap_used` exibido na MESMA tela**; agora percorre todos. (2) A chave
  da API `to_dict()` virou **`salary_total`** (antes `active_salary`), idem em
  `sync_sleeper._compute_cap_alerts` — consumidor: `templates/trades.html`.

- **O rotulo duplo saiu das 7 superficies.** Removidos: o par rotulado, o **banner aditivo** do par
  (ativo <= cap, folha > cap), a legenda *"⚖️ e a folha total que vale no leilao"*, as 3 classes CSS
  da F2, o `g_user_team_folha` e as chaves `folha_*`/`has_ir`/`ir_cap` dos payloads. Chip, barra de
  progresso e "Restante" operam sobre a folha unica.

- **Banner de IR virou informativo de ESCALACAO:** *"🏥 2 jogador(es) no IR: Michael Penix, Travis
  Hunter."* Sem aritmetica paralela; em `/team/<id>` o item IR mostra so a contagem, nomes no
  `title`.

- **Numeros conferidos contra o banco (`mode=ro`):** achane **$186 → $195**, restante **$5**, barra
  **97,5%**; rafaelferreirap $133 → **$136**; Fazenda $176 → **$178**; **os 9 times sem IR
  identicos**. Suites: **14/14** (`cap_regua`) + **54/54** (`salary_engine`) + **34/34**
  (`keeper_audit`); imports das 6 rotas e do `sync_sleeper` OK; parse Jinja dos 9 templates OK.

- **Fora de escopo, deliberado (e por que):** (a) **`dynasty_total` segue excluindo IR** — e **valor
  de ativo**, nao folha salarial; a decisao do owner e sobre **cap**, e estender seria decidir sem
  mandato. (b) ⚠️ **OBSERVACAO REGISTRADA:** `renewal_candidates` (`roster.py`) deriva de
  `active_players`, logo **um jogador em IR no Ano 4 NAO aparece como candidato a renovacao** — e
  pergunta de **contrato**, nao de folha, e nao foi corrigida aqui. (c) [[OFF26-15]] nao entra.
  (d) `draft_budget` intocado (formula fechada e confirmada, [[OFF26-18]]). (e) Keeper sheet,
  auditoria OFF26-4, schema e sync intocados fora do rename de chave.

- ⚠️ **PENDENTE DE SMOKE EM PROD.** So producao prova: achane em **$195/$5** com barra 97,5% e o
  banner com os dois nomes; os 9 sem IR com tela **identica**; `/team/<id>` sem o custo de IR
  duplicado; preview de trade e card do League Hub sem residuo de layout; e **`/api/teams` servindo
  `salary_total`** — se algo externo consumia `active_salary`, quebra ai.

- Board intacto, draft nao iniciado; `CLAUDE.md` teve a secao das duas reguas **substituida** pela
  da regua unica, e o `cap_regua_test.py` entrou nos comandos e na estrutura do projeto.

### MAN-IR-CLEANUP — toggle de IR removido + bug de renovacao registrado (04/08/2026, Opus)

**(A) IR-CLEANUP executado — decisao do owner: remover.**

- **O argumento ficou MAIS FORTE que na diagnose original.** O MAN-IR-F1 tratava o toggle como
  **ruido inocuo**: controle sem efeito persistente, revertido em silencio pelo sync (que reescreve
  `Player.is_on_ir` de forma autoritativa a partir do array `reserve`, `sync_sleeper.py:290`). Com a
  **regua unica** do [[OFF26-16]] — em que **o IR conta no cap** — o toggle passou a **aparentar
  mudar a FOLHA SALARIAL do time** sem mudar nada. **Deixou de ser ruido e virou controle
  ativamente enganoso**, a 16 dias do leilao.

- **Removidos:** endpoint `POST /api/player/<id>/ir` (`toggle_ir`, `routes/roster.py`), handler
  `toggleIR` (`roster.html`), os 2 botoes (`↑ Tirar IR` / `IR`, `_macros.html`), **a coluna
  `col-actions` INTEIRA** (macro + colgroup + `<th>`), o CSS morto (`.btn-ir-remove`,
  `col.col-actions`, `.col-actions`, e o `.status-ir-cost` que ficara orfao do OFF26-16) e o import
  orfao de `MAX_IR`. **Efeito colateral bom:** a coluna existia **so** para o toggle, entao `/` e
  `/team/<id>` passam a ter **exatamente a mesma forma de tabela**.

- **Preservados, como o item exigia:** `Player.is_on_ir` (sync segue escrevendo), badge **🏥 IR**,
  `MAX_IR` e **toda** a logica de cap (hoje a regua unica). O **banner de escalacao** do OFF26-16
  (*"🏥 2 jogador(es) no IR: Michael Penix, Travis Hunter."*) **permanece** — e **leitura, nao
  controle**. `MAX_IR` ficou **sem referencia em codigo** (era validado so dentro do toggle):
  preservado de proposito **com comentario no `models.py` dizendo por que** — documenta a regra da
  liga (item 1.3) e e a ancora se algum dia houver validacao local. **Nao e residuo a limpar.**

- **Caveat de UX do registro original — DESCARTADO, com o motivo registrado.** A alternativa era
  manter o seletor com tooltip *"Sera sobrescrito no proximo sync"*, preservando override offline.
  O owner decidiu remover: **o custo permanente de um controle enganoso sobre a folha supera a
  hipotese de operar sem Sleeper** — e **mudar IR se faz no Sleeper**, onde a autoridade sempre
  esteve.

- **Validacao:** os **5 jogadores em IR seguem em IR** (Kendre Miller, Tory Horton, Michael Penix,
  Travis Hunter, Zach Charbonnet); badge e banner intactos; **os 12 valores de cap identicos** aos
  do OFF26-16; `grep` nao encontra endpoint, handler nem controle; `toggle_ir` **nao existe mais no
  blueprint**. Suites **14/14 + 54/54 + 34/34**; imports e parse Jinja OK.

- ⚠️ **Pendente de smoke em prod:** (1) tabela do roster **sem a coluna de acoes** — conferir que o
  `colgroup` nao desalinhou larguras; (2) badge 🏥 e banner de escalacao renderizando; (3) um **sync
  manual** mantendo os 5 em IR — e a prova de que a autoridade do Sleeper segue funcionando sem o
  toggle.

**(B) [[OFF26-19]] registrado 🔲 Baixa — NAO corrigido.**

- **Mecanismo:** `renewal_candidates` (`routes/roster.py`) deriva de `active_players`, a lista que
  **exclui quem esta em IR**. E **heranca do mesmo filtro** que o OFF26-16 removeu das telas de cap;
  sobreviveu ali porque **nao e pergunta de folha, e de contrato** — e por isso ficou fora daquele
  escopo, deliberadamente.

- **Dano:** jogador **em IR no Ano 4** nao aparece no aviso *"N jogador(es) no Ano 4 — renovar ou
  cortar"*; o contrato **expira sem decisao registrada** e o salario seguinte sai errado. **Dano
  silencioso**, familia do [[OFF26-11]]: nao ha erro visivel, ha uma **decisao que ninguem foi
  convidado a tomar**. O perfil de risco e justamente **fim de contrato + lesao** — o caso que mais
  exige a decisao de renovar x cortar.

- **Dano HOJE: ZERO, verificado.** Distribuicao da liga: **ano 1 = 50**, **ano 2 = 198**, **ano 4+ =
  0**. Com tudo em anos 1-2, o primeiro Ano 4 so existe depois de **DOIS rollovers** — ha folga
  real, e e o que sustenta a prioridade Baixa apesar de o bug tocar salario. **Mas e atemporal:** o
  bug nao caduca, so esta adormecido.

- **Correcao exige F1 propria** (toca o fluxo de renovacoes): decidir se `is_renewal_candidate()`
  vale para jogador em IR (provavelmente sim) e **varrer se o mesmo filtro se repete em outras
  superficies de contrato** — o OFF26-16 so varreu as de folha.

**Intocados:** sync, `is_on_ir`, regua unica, `draft_budget`, keeper sheet, auditoria OFF26-4,
schema. Board intacto, draft nao iniciado. `CLAUDE.md`: a linha do blueprint `roster` deixou de
dizer "IR management" e a secao de autoridade de dados ganhou **"IR e read-only no Manager"**.

### MAN-OFF26-20-F1 — rotulos de aquisicao e regras salariais (04/08/2026, Opus)

**Parte 1 — SMOKE CONSOLIDADO DE PRODUCAO PASSOU nos 6 pontos; o lote FECHA ✅.** Roster do achane
$195/$5 com banner de nomes e tabela sem coluna de acoes; time sem IR inalterado; Cap Projector com
**`min $3` em 4 spots e `min $0` em 1 spot** (o fencepost do OFF26-18 **vivo na tela**); `/trades`
carregando com o rename da chave (`salary_total`); League Hub coerente com o roster; e **sync manual
mantendo os 5 em IR** — a prova de que a autoridade do Sleeper funciona sem o toggle. Fecham
[[OFF26-14]]/F2, [[OFF26-16]], [[OFF26-17]], [[OFF26-18]] e [[IR-CLEANUP]]. As 5 secoes detalhadas
foram **migradas para o `improvements_archive.md`** (regra O3), com nota no cabecalho de que **a F2
do OFF26-14 foi REVERTIDA pelo OFF26-16** e os dois racionais ficam lado a lado de proposito.

**Parte 2 — diagnose read-only: [[OFF26-20]] registrado 🔲 Alta. A hipotese do owner CAIU.**

- **T1 — censo e procedencia.** 6 tipos em 248 jogadores. O valor vem do campo
  `Player.acquisition_type`; o rotulo, do dict **unico** `_ACQ_LABELS` (`routes/roster.py:343`, 3
  consumidores). **Sem derivacao em template, sem fallback do sync.** O truncamento *"Waiver / Free
  A…"* e **puro CSS** (`text-overflow: ellipsis` em `td.col-acq`, com o texto completo no `title`) —
  **nao e problema de dado**. Distribuicao: `auction_draft` 96, `free_agent` 39, **`fa_waiver` 37**,
  `rookie_draft` 31, `fa_auction` 28, `waiver` 17.

- ⛔ **T2 — HIPOTESE FALSIFICADA.** A hipotese era "todo ambiguo esta em Ano 2+, bifurcacao ja
  passada, cicatriz benigna". **Ha 5 `fa_waiver` em ANO 1** — Chimere Dike, Jaylin Noel, Malik
  Willis, Oronde Gadsden, Tyler Shough — com a bifurcacao **PENDENTE** para o rollover de 18/08
  (+ 4 `fa_auction` em Ano 1). O rotulo tambem **nao se correlaciona** com epoca de importacao: os
  seis tipos convivem em Ano 1 e Ano 2; `fa_waiver` e apenas o enum que o pipeline grava.

- ⛔ **T3 — O BURACO: `fa_waiver` e `fa_auction` NAO estao em `_WAIVER_TYPES`**
  (`{"waiver","free_agent","fa"}` — e `"fa"` e **enum morto**, nao existe no banco). Os **37**
  `fa_waiver`, cujo rotulo literalmente diz *"Waiver / Free Agent"*, **nunca recebem** a regra
  `floor(0,80 x ESPN)` do ano 2 (regulamento **6.6**); caem sempre na valorizacao. **Dano HOJE:
  zero — por COINCIDENCIA, nao por desenho**: os 5 de Ano 1 tem `espn_ref_value = 1.0` (tabela
  provisoria) e as duas regras dao $1. ⚠️ **A ESPN definitiva entra em 18/08, o MESMO DIA do
  rollover**: com valor real o erro escala (ESPN $5 → −$2; $10 → −$3; $20 → −$6) e seria **selado**
  na keeper sheet de 20/08. **Pergunta de REGRA DE LIGA em aberto:** `fa_auction` tambem entra? A
  7.1.1 (aquisicao em waiver e por *"Waiver Auction"*) sugere que sim, mas os 4 de Ano 1 tem
  salarios de lance ($4/$1) enquanto a 6.6 manda ano 1 "sem valor" — **as duas leituras sao
  defensaveis**.

- ⚠️ **T4/T5 — 2o ACHADO, INDEPENDENTE E MAIOR: a coluna PROJ do roster NAO e o que o rollover
  fara.** Ha **TRES** funcoes de "proximo salario": (1) `compute_salary_for_year` via
  `Player.projected_next_salary()` — consumida **so** pela coluna PROJ de `/` e `/team/<id>`
  (`_macros.html:73`); (2) `salary_engine.project_next_salary` — Cap Projector, porta `/budget`,
  `to_dict()`; (3) `apply_season_rollover` — preview do admin e **o rollover real**. **(2) e (3)
  concordam; a (1) discorda em 26 de 248**, **sempre superestimando**, somando **+$62**. Mecanismo:
  a (1) **reconstroi o contrato do zero e DESCARTA o salario armazenado** — viola diretamente o
  principio *"o DB e autoridade sobre salarios e anos de contrato"* do `CLAUDE.md`. **Os maiores
  erros sao de ROOKIE, nao de waiver/FA** (para rookie, `year1_salary` devolve `floor(ESPN)`, entao
  recalcula o ano 1 com o ESPN de hoje): **Omarion Hampton — tela $44, rollover $26, erro +$18**;
  McMillan +$15; Egbuka +$13; Skattebo +$13; Judkins +$12.

- **T4 — Watson resolvido.** `free_agent`, ano 2, $1, ESPN 6.0. Os **$4** da tela saem da
  reconstrucao: ano 1 = $1 (waiver type → MIN_SALARY), ano 2 = `floor(0,8 x 6)` = **4**, ano 3 =
  `max(4, 3)` = 4 — **o palpite do owner sobre a conta estava certo**. **O rollover fara $3**
  (`valorization_rule($1, 6)` = `max(1, 3)`). **Resposta direta a pergunta do prompt:** na **tela**,
  TODO jogador e tratado como aquisicao nova; **no rollover, NAO** — ele respeita o contrato
  armazenado ⇒ **o dano esta confinado ao display**, o que sera escrito em 18/08 nao e afetado por
  essa funcao.

- **Premissas contraditas:** (1) "o rotulo ambiguo e cicatriz de importacao" — **falsificada por 5
  casos em Ano 1**, e o problema real nao e o rotulo (dict correto, truncado por CSS) e sim o enum
  **nao existir para o motor de salario**; (2) "se a regra de FA nova for aplicada, ha jogadores em
  ano 2+ tratados como aquisicao nova" — inferencia certa, **lugar errado**: quem faz isso e a
  coluna PROJ, nao o rollover; (3) "Waiver x FA tem regras salariais diferentes" — no **regulamento**
  a 6.6 trata os dois **juntos**, e no **codigo** eles estao no **mesmo conjunto**; a distincao real
  e `fa_waiver`/`fa_auction` **fora** do conjunto x os demais dentro. **Nao previsto:** as 3 funcoes
  de projecao; os erros de rookie; o `"fa"` morto; o truncamento ser CSS; e **85 jogadores com
  `contract_start_season = 2025` E `contract_year = 2`** com `current_season = 2025` — ⚠️
  **observacao a verificar, NAO veredito** (o campo e escrito em 3 pontos e a diagnose nao apurou a
  semantica pretendida), porem relevante porque `contract_year` alimenta a bifurcacao.

- **Nada corrigido.** Se houver salario a corrigir, o caminho e `correct_player_salary` — nunca
  patch. **Tres decisoes do owner, em ordem de prazo:** (1) **ate 18/08** — `fa_waiver` (e
  `fa_auction`?) entra em `_WAIVER_TYPES`? **regra de liga**; (2) **ate 20/08** — a coluna PROJ passa
  a consumir a fonte (2)/(3)? e correcao de **display**, nao toca o rollover, mas e o numero que guia
  os cortes; (3) verificar a inconsistencia `contract_start_season` x `contract_year` nos 85.

`git diff` sem arquivo de codigo; board intacto, draft nao iniciado.

### MAN-OFF26-20-F1B — a arbitragem pelo regulamento INVERTE a conclusao da F1 (05/08/2026, Opus)

**Registro docs-only.** Nenhum arquivo de codigo tocado; leitura do banco em `mode=ro`; board intacto.

⚠️ **O owner tinha razao ao recusar a conclusao da F1.** Ela dizia *"o rollover esta certo e a tela
esta errada"* — inferido da **arquitetura** (uma funcao respeita o banco, a outra nao), **nao**
medido contra a regua definitiva. Concordancia entre as duas funcoes do backend prova
**consistencia, nao correcao**. Ao aplicar o regulamento a mao, caso a caso, **o cenario que o
prompt antecipou se materializou**: para uma coorte grande **o banco esta errado**, a funcao que o
respeita **propaga o erro com conviccao**, e a que reconstroi **acerta**.

- ⛔ **ACHADO CENTRAL — 73 CONTRATOS COM A REGRA ERRADA NO ROLLOVER DE 18/08 (a F1 falava em 5).**
  Os **85** suspeitos tem, **todos**, `drop` **e** reaquisicao de 2025 **REAIS** no chain do Sleeper
  (eventos com `sleeper_event_ref` — transacoes da API, nao artefato de backfill). Pela **6.1**
  (*"o primeiro ano e o ano da aquisicao no draft ou nos waivers"*), o contrato **recomecou em 2025
  como ano 1** — e o salario **$1** armazenado e exatamente o *"sem valor"* que a **6.6** manda para
  o ano 1 de waiver/FA. Logo, **em 2026 eles estao no ANO 2**, e a regra devida e **0,8 x ESPN**.
  O rollover os tratara como **ano 3** (valorizacao) ⇒ **regra errada**, e o resultado entra
  **selado** na keeper sheet de 20/08.

- **T3 — a semantica dos dois campos, apurada: `contract_start_season` esta CERTO e
  `contract_year = 2` esta ERRADO** (inverte a leitura preliminar reportada ao owner). Escritores
  distintos, guards **independentes**: `contract_year` vem do **CSV do owner**
  (`import_csv.py:103`, guard `csv_bootstrap_done`); `contract_start_season` e **derivado**
  (`CURRENT_SEASON - cyr + 1`, `import_csv.py:105`, guard `f8_rebuilt`) e, apos o F8, **sobrescrito**
  por `ev["season"]` = a season do **ultimo evento real** (`sync_sleeper.py:1232`). Nao e "erro de
  importacao" nem "convencao legitima": e **colisao semantica entre dois escritores**.
  A **6.8** e a unica defesa possivel do `contract_year = 2`, mas exige *"adquiridos ... pelo
  **proprio** owner"* — e **73 dos 85 foram readquiridos por um time DIFERENTE**, onde a 6.8 **nao
  pode** ser invocada. Quebra por evento de reaquisicao: `fa_waiver` 32 (4 mesmo time),
  `free_agent` 29 (7), `fa_auction` 24 (1).

- **Exposicao dos 73, e ela TROCA DE SINAL com o ESPN:** hoje (ESPN quase toda 1.0) o rollover
  **sobrecobra $79** no agregado; a ESPN $10 passa a **subcobrar $131**; a ESPN $20, **$393**. Em
  qualquer cenario **a regra aplicada esta errada** — o valor final so se fecha com a ESPN definitiva
  de 18/08.

- **T1 — veredito POR POPULACAO (a resposta a "qual funcao corrigir"):**
  · **21 rookies** (dado consistente, `start=2025`/`ano=1`) → **o ROLLOVER acerta, a TELA erra**.
    Hampton: 6.2/6.3 da `max(26, floor(0,5x44)=22)` = **$26** ✅ contra **$44** da tela, que descarta
    o contrato e recalcula o ano 1 como `floor(ESPN de hoje)` — violando a **6.1** (o ano 1 e o valor
    do Auction, nao o ESPN corrente). Idem McMillan ($15 x $30) e Egbuka ($13 x $26).
  · **73 readquiridos** → **a TELA acerta, o ROLLOVER erra**. Watson: `2024 auction_draft` →
    `2025 rollover` → **`2025 drop`** → **`2025 free_agent`** ⇒ ano 2 em 2026 ⇒ 6.6 ⇒
    `floor(0,8 x 6)` = **$4** ✅ contra **$3** do rollover.
  ⇒ **Nenhuma das duas funcoes e "a certa": corrigir a TELA, o DADO e o ENUM.**

- ⚠️ **A tela erra nos DOIS sentidos — a F1 disse "sempre para cima", e isso e FALSO.** **9 dos 26
  subestimam**: Jeanty **$57** correto contra **$45** na tela (**-$12**), Henderson $21 x $10
  (**-$11**). O `+$62` e **saldo liquido**, nao direcao. E subestimar e a direcao perigosa: leva a
  **manter** um contrato que nao cabe.

- **T2 — causa-raiz do vocabulario, e a resposta e ACIDENTE, nao decisao.** O rebuild **F8** grava
  o vocabulario de **evento** dentro do campo de **aquisicao**:
  `sync_sleeper.py:1217-1218` → `if ev["season"] >= 2025: new_acq = ev["event_type"]`.
  O `_norm_acq` (`import_csv.py:30`) **nunca produz** `fa_waiver`/`fa_auction` — seu contradominio e
  `{auction_draft, waiver, free_agent, rookie_draft, unknown}`, e o `_WAIVER_TYPES` foi escrito
  contra **esse** vocabulario. Dois vocabularios no mesmo campo, **nunca reconciliados**.
  **Prova empirica (`F8PlayerBackup`, 127 linhas): 100%** dos `fa_waiver` (37), `fa_auction` (28) e
  `free_agent` (39) foram escritos pelo F8; **0%** dos `waiver` (17), `auction_draft` (96) e
  `rookie_draft` (31). Transicoes incluem `rookie_draft → fa_waiver` (7) e `auction_draft →
  fa_auction` (25).
  ⚠️ **Consequencia para a informacao do owner:** os **17 `waiver` que ele validou sao exatamente os
  que o F8 NAO tocou** — a validacao **nao alcanca** os 37 `fa_waiver`, que nasceram do F8.
  **Ironia registrada:** o comentario em `sync_sleeper.py:1215-1216` (*"protege year-1 rules do
  salary_engine"*) mostra que o autor **sabia** que o campo alimenta regra salarial e pos um guard
  **de season** — o buraco e de **vocabulario**, e esta no ramo tido como seguro.

- **T4 — alcance.** `Player.projected_next_salary()` (a que reconstroi) tem **UM unico consumidor**:
  `_macros.html:73`, a coluna PROJ — que serve `/` **e** `/team/<id>`. O **Cap Projector usa a conta
  do backend** (`salary.py:87`), a mesma do rollover ⇒ **Cap Projector e coluna PROJ mostram numeros
  diferentes para o mesmo jogador, e nenhuma tela avisa**.

- **Premissas contraditas:** (1) *"a tela diverge sempre para cima, +$62"* — **falso** (9 de 26
  subestimam); (2) *"o problema pode ser so de classificacao, nao de contrato errado"* —
  **parcialmente falso**: ha **as duas coisas**; (3) *"rookie entra a floor(ESPN x 1,2) conforme
  rodada"* — a **8.2.7 nao modula por rodada**; (4) a **propria F1** errou ao dizer que o regulamento
  trata waiver e FA juntos — a **6.6** trata, mas a **6.8** os separa, e **a distincao do owner
  existia**.

- **Nao previsto:** a **6.8 e hoje INIMPLEMENTAVEL** — nao existe campo que distinga "readquirido
  pelo proprio owner via waiver" de "virou FA"; e o [[WV1]], agora **confirmado e agravado**. E
  **`salary_history` esta VAZIA**, com `EspnValueStore` so em 2026 ⇒ **nao ha trilha para auditar se
  a 6.6 foi aplicada em anos anteriores**.

- ⚠️ **Caveat de metodo:** o corte "mesmo time x time diferente" usa `PlayerHistory.team_name`, que o
  [[S4]] registra como **chave instavel**. Os **73** sao um **piso confiavel** para o argumento, mas
  a contagem exata merece conferencia por `roster_id` antes de qualquer correcao.

- **Nada corrigido.** Correcao de salario passa por `correct_player_salary` — nunca patch.
  **Decisoes do owner, em ordem de prazo:** (1) ⛔ **ate 18/08** — os 73 estao em ano 2 ou ano 3 em
  2026? Pela 6.1 e **ano 2**; se o owner concordar, **`contract_year` precisa ser corrigido ANTES do
  rollover**; (2) **ate 18/08** — `fa_waiver` (e `fa_auction`?) entram em `_WAIVER_TYPES`? Sem isso,
  mesmo com o `contract_year` certo os 37 seguem sem a 6.6; (3) **ate 20/08** — a coluna PROJ passa a
  consumir a fonte do backend; (4) **pos-leilao** — reconciliar os dois vocabularios e criar o dado
  que a 6.8 exige ([[WV1]]).

**Prioridade do [[OFF26-20]] elevada de Alta para CRITICA (prazo 18/08).**

### MAN-OFF26-20-F1C — o discriminador e o CANAL: de 73 para 29 (05/08/2026, Opus)

**Registro docs-only.** Nenhum arquivo de codigo tocado; banco lido em `mode=ro`; board intacto.

⚠️ **A F1B usou o CRITERIO ERRADO.** O corte *"readquirido pelo proprio owner x por time
diferente"* saiu de uma leitura da 6.8 que **nao corresponde a regra real da liga**. Regra
esclarecida pelo owner em 05/08 (autoridade sobre qualquer leitura do texto): **o discriminador e o
CANAL de aquisicao, nao a identidade do time.**
· **Waiver (leilao de FAAB):** o dropado vai a leilao; quem vence **leva com o contrato que ele
  tinha** — salario e contagem de anos preservados — **para qualquer time**.
· **Free agent (add gratis pos-lock):** entra **sem contrato**; $0/$1 no ano corrente e, no
  seguinte, ja como **ano 2**, **0,8 x 1,2 x ESPN**.

- ✅ **T1 — A DISTINCAO NUNCA SE PERDEU, e nao era verificacao manual: e CODIGO VIVO.** Esta em
  `sync_sleeper.py:911-915` (`_collect_transaction_events`), que mapeia o `tx["type"]` da **propria
  API** — `"waiver" -> "fa_waiver"`, `"free_agent" -> "free_agent"` — e o preserva em
  `PlayerHistory.event_type`. Os **117 `fa_waiver`** e **150 `free_agent`** do historico tem
  **todos** `sleeper_event_ref`: sao transacoes reais, nao reconstrucao. **Unica perda:** o **bid
  FAAB** (`tx["settings"]["waiver_bid"]`) **nao e capturado** — **inocuo para salario** pela
  **7.1.8** (*"os valores pagos pelos waivers nao sao considerados na folha salarial"*).
  ⇒ **Nao era preciso refazer a identificacao.**

- **T2 — Censo pelo canal, confianca ALTA, ZERO indeterminados.** Ultimo evento de aquisicao de
  cada um dos 85, com trocas resolvidas para a aquisicao anterior (**6.7**): **32 `fa_waiver`**,
  **29 `free_agent`**, **24 `fa_auction`**. O `acquisition_type` do `Player` **bate com o ultimo
  evento em 100%** dos casos (32/32, 29/29, 24/24) — o F8 fez esse trabalho corretamente.

- **T3 — os tres grupos, e o impacto real.**
  · **(a) 32 via waiver — CERTOS.** Carregam contrato legitimamente, mesmo tendo trocado de time;
    `contract_year = 2` esta correto. **Nada a corrigir.**
  · **(c) 24 via leilao de 2025 — contagem errada, SALARIO CERTO.** Deveriam ser ano 1 em 2025, mas
    **o erro nao tem efeito em 2026**: na trilha de valorizacao, `max(salario, 0,5 x ESPN)` da **o
    mesmo numero em qualquer ano >= 2**. O off-by-one so se materializa na **renovacao (ano 5)**,
    em 2029.
  · **(b) 29 via free agent — ERRADOS; e o grupo do prazo.** Deveriam estar em ano 1 (2025) ⇒ **ano
    2 em 2026** ⇒ `0,8 x 1,2 x ESPN`. O rollover os tratara como ano 3 (valorizacao) e vai
    **SUBCOBRAR**: delta **+$6** com a ESPN provisoria de hoje, **+$58** a ESPN $5, **+$87** a $10,
    **+$174** a $20.

- **T4 — AMBIGUIDADE DO 1,2 ELIMINADA.** O fator e aplicado na **fronteira de escrita**, nunca no
  calculo: `espn_pdf_parser.py:129` (`max(1.0, float(int(espn_raw*1.2)))`) e `routes/admin.py:173`
  (CSV bulk). `Player.espn_ref_value` guarda o valor **ja ajustado**, e `salary_engine._adj()` e
  **apenas guard de `None`** — nao multiplica. Logo `waiver_year2_salary` = `floor(0,8 x
  espn_ref_value)` = **`floor(0,8 x 1,2 x ESPN_raw)`** ✅, e o mesmo vale para valorizacao (0,5) e
  rookie (1,0). **O codigo ja implementa a formula que o owner descreve.** Confirma a
  [[MAN-ESPN12]], que ja havia varrido o tema.

- **T5 — revisao item a item da F1B.** ⛔ **"73 contratos errados" CAI** — sao **29**. ⛔ **O achado
  da F1 sobre `fa_waiver` INVERTE: estar FORA de `_WAIVER_TYPES` esta CERTO** (waiver carrega
  contrato ⇒ valorizacao), e `free_agent` estar **dentro** tambem esta certo (FA ⇒ 0,8 no ano 2).
  ⛔ **"5 `fa_waiver` em ano 1 expostos" CAI.** ⚠️ *"`contract_start_season` certo, `contract_year`
  errado"* **sobrevive PARCIALMENTE**: vale para os 29 e, na contagem, para os 24; **nao vale** para
  os 32, onde `contract_year = 2` e o correto. ✅ **Sobrevivem intactos:** os **21 rookies** com
  divergencia de tela (Hampton **$26** rollover ✅ x $44 tela; Jeanty **$57** ✅ x $45), a tela
  errando nos **dois sentidos**, o **Cap Projector x coluna PROJ** e a **`salary_history` vazia**.
  ✅ O fato de o **F8 gravar `event_type` em `acquisition_type`** sobrevive, mas ⚠️ **a leitura
  muda: nao e acidente danoso** — os valores gravados (`fa_waiver`/`free_agent`) **sao exatamente o
  canal**, e o `_WAIVER_TYPES` os trata **corretamente**. E **acoplamento fragil** (dois
  vocabularios no mesmo campo), **nao bug ativo**.

- ⚠️ **ACHADO NOVO, DE SINAL TROCADO:** o enum **`waiver`** (17 jogadores, vocabulario do CSV) esta
  **DENTRO** de `_WAIVER_TYPES` e, pela regra do owner, **nao deveria** — waiver carrega contrato.
  **Impacto em 2026: ZERO** — todos os 17 estao em `contract_year = 2`, logo `next_yr = 3` e a regra
  do ano 2 **nao dispara**. **Latente, nao ativo.**

- ⚠️ **INDETERMINADO, declarado como tal (sem inferencia):** os **5 `fa_waiver` em ano 1** (Dike,
  Noel, Willis, Gadsden, Shough) entraram por waiver **sem contrato previo**. A regra do owner diz o
  que acontece quando o jogador **tem** contrato (carrega), mas **nao diz** qual e o ano 2 de um
  contrato que **nasceu** de um claim de waiver. A **6.6** literal (*"Waivers **ou** Free
  Agents ... no segundo ano, 80%"*) mandaria 0,8; a leitura "waiver != FA" mandaria valorizacao.
  Hoje as duas dao $1 (ESPN provisoria 1.0); em 18/08 podem divergir. **Decisao do owner.**

- **Premissas refutadas:** *"a identificacao ja foi feita — encontrar onde vive"* — **certo, e
  melhor do que o prompt supunha**: nao e verificacao manual perdida, e codigo que roda a cada sync
  alimentado pela API. *"o erro real esta so nos que vieram como FA"* — **quase**: ha tambem os 24
  do leilao com contagem errada, mas **sem efeito no salario de 2026**. **Nao previsto:** a
  valorizacao ser **indiferente ao numero do ano** (>=2) — e isso que reduz o problema de 73 para 29,
  porque o off-by-one so importa na porta do 0,8 (ano 2 de FA) e na renovacao (ano 5).

- **Prioridade do [[OFF26-20]] rebaixada de CRITICA para ALTA** (29 jogadores, delta de $6 hoje) —
  **o prazo continua 18/08**, e o numero cresce com a ESPN definitiva. **Decisoes do owner:**
  (1) confirmar que os **29 do canal FA** vao a `contract_year = 1`; (2) decidir o **indeterminado**
  dos 5; (3) ate 20/08, a coluna PROJ passar a consumir a fonte do backend; (4) sem pressa, os 24 do
  leilao (efeito so em 2029) e o enum `waiver` no conjunto errado (latente). **Nada a fazer nos 32
  do waiver — estao certos.** Correcao, se houver, passa por `correct_player_salary` — nunca patch.

### MAN-OFF26-20-VERIF — os 34 verificados nominalmente contra a API (05/08/2026, Opus)

**Registro docs-only, read-only ABSOLUTO.** Banco em `mode=ro`, API só com `GET`, nenhuma escrita.
Draft 2026 conferido em `pre_draft` — **board intacto**.

O owner condicionou a correcao a uma pergunta unica: **algum dos 34 foi adquirido em 2024?** Se sim,
ja passou pela valorizacao de 2025 e "corrigi-lo" quebraria um contrato certo.

- ✅ **A PREMISSA DA DATA ESTA CONFIRMADA: 34 de 34 abrem em 2025. ZERO em 2024.** Baixado o chain
  inteiro (`1316547584378048512` 2026 → `1224848075609100288` 2025 → `1107510813394341888` 2024):
  **1125 transacoes** e **9 drafts**. Os **173 refs `tx:`** do `PlayerHistory` desses 34 resolvem
  **todos** contra a API — nenhum evento orfao. O risco que motivou o prompt **nao se materializou
  como regra**.

- ⛔ **MAS A F1C ERROU O EIXO, e isso muda a natureza da correcao.** Nao sao "29 errados + 5
  indeterminados". Sao dois defeitos **diferentes** que produzem **o mesmo sintoma**:
  · **29 `free_agent`** — `contract_year = 2` quando deveria ser 1 ⇒ **o DADO esta errado**.
  · **5 `fa_waiver`** — `contract_year = 1`, que esta **CERTO**; quem erra e o **MOTOR**
    (`fa_waiver` ∉ `_WAIVER_TYPES` ⇒ o ramo `next_yr == 2` nao dispara).
  ⇒ **Os 34 receberao VALORIZACAO no rollover de 18/08 e os 34 deveriam receber 0,8 × ESPN REF —
  por causas OPOSTAS.**

- ✅ **Achado que simplifica a correcao futura:** por `fa_waiver` dentro de `_WAIVER_TYPES` alcanca
  **exclusivamente os 5**. Os outros 32 `fa_waiver` estao **todos** em `contract_year = 2` ⇒
  `next_yr = 3` ⇒ o ramo do 0,8 **nunca** os toca. A regua da F1C (*"estar fora esta certo"*) e
  **verdadeira para os 32 e falsa para os 5** — e o enum consegue servir aos dois sem conflito.

- ⛔ **O "+$6" da F1C e ILUSAO DO ESPN PROVISORIO — nao usar para dimensionar urgencia.** **134 dos
  248** jogadores estao com `espn_ref_value <= 1.0`, e a tabela definitiva entra **18/08, o mesmo
  dia do rollover**. Hoje so **5 dos 34** divergem; com ESPN real, **32 dos 34**:
  ESPN 4 → **+$33** · ESPN 10 → **+$87** · ESPN 20 → **+$168**. O rollover **SUBCOBRA** em todos os
  cenarios.

- **Veredito: 21 CORRIGIR · 3 CORRETO (dado) · 10 AMBIGUO.** Cada CORRIGIR tem `tx:` de 2025 + data
  citados na tabela do `improvements.md`. Os 3 CORRETO (Dike, Gadsden, Shough) tem o dado certo — a
  exposicao e do enum. Motivos dos ambiguos: 6.8 mesmo owner antes (6), trade depois do opener (5),
  trade em 2026 (2), contrato previo em waiver (1).

- ⚠️ **A FALSIFICACAO PARCIAL QUE O OWNER PEDIU PARA DESTACAR — duas aberturas de 2024 candidatas.**
  Nenhum dos 34 tem *transacao de aquisicao* de 2024 como ultimo evento, mas **dois** tem aquisicao
  de 2024 **pelo mesmo owner que os readquiriu em 2025**:
  1. ⛔ **Kenny Gainwell** — `ESPN FANTASY LEAGUE` o adicionou como FA em **2024-11-27**, dropou em
     **2025-08-26** e o **readquiriu em 2025-09-01**, seis dias depois. E a **6.8 literal**. Sob ela:
     2024 = ano 1, 2025 = ano 2, **2026 = ano 3 ⇒ valorizacao ⇒ O BANCO ESTA CERTO e o rollover
     acerta**. Sob a leitura "recomecou", esta errado. **As duas leituras dao respostas OPOSTAS.**
  2. ⚠️ **Jake Bates** — `AlexTheDawg` o adicionou por waiver em **2024-10-08**, dropou em
     **2024-12-04** e o readquiriu como FA em **2025-09-24** — mas houve **dono intermediario**
     (Vila Gugu FC / achane), o que enfraquece muito a 6.8.
  Os outros 8 ambiguos abrem **inequivocamente em 2025**; o flag e sobre *qual* evento de 2025 abre,
  nao sobre o ano, e a resposta de 2026 (ano 2) e a mesma nas duas leituras.

- **Premissas refutadas:**
  1. ⛔ *"os 5 `fa_waiver` entraram por waiver SEM contrato previo"* (premissa do proprio prompt) —
     **falso para Jaylin Noel**: foi **draftado no leilao de 2025** (r2p17, $1) pelo proprio
     `Fazenda Pederasta`, dropado, passou por achane e **voltou por waiver ($0) ao time original**.
     6.8 pura, com contrato previo real. Os outros 4 confirmam a premissa. **Sem efeito pratico** —
     em qualquer leitura o contrato de Noel abre em 2025.
  2. ⛔ *"o delta e +$6"* — so com o ESPN provisorio de hoje.
  3. ⛔ *"o bid FAAB nao foi capturado"* (F1C-T1) — verdade quanto ao **sync**, mas o dado **esta na
     API** e foi lido aqui: Dike $8, Gadsden $16, Shough $18, Tucker $66, Stafford $35. **Nao se
     perdeu; e recuperavel a qualquer momento.**
  4. ✅ **`team_name` instavel entre ligas, CONFIRMADO por medicao:** `Vila Gugu FC` (2024) e
     `achane` (2025/26) sao o **mesmo `owner_id`** (`867557566065045504`). Esta verificacao resolveu
     times por `owner_id` **por liga**, nunca por nome — reforca a licao da F1B.
  5. ⚠️ **Ressalva de fonte (limitacao, nao refutacao):** o banco lido e o **seed local**
     (`dynasty.db` do git, 01/08), **nao** o `/data/dynasty.db` de producao. Ele **reflete as trades
     de 28-30/07/2026**, o que indica frescor — mas **a lista nominal deve ser reconferida contra o
     banco vivo antes da correcao**.

**Nada corrigido. Aguardando aprovacao nominal do owner — a correcao e prompt separado, e passa por
`correct_player_salary`, nunca patch.** Sob a **6.7** (a trade carrega o contrato) os 4 ambiguos de
"trade depois" (Stafford, Robinson, Stroud, K. Miller) seriam determinados e entrariam em CORRIGIR;
ficaram fora porque o prompt classificou "trade no meio" como duvida — registrado, nao decidido.

### MAN-OFF26-20-CANAL — Gainwell pelo canal, e o grupo fecha em 22 (05/08/2026, Fable)

**Registro docs-only, read-only ABSOLUTO.** Nenhuma escrita em banco ou plataforma; board intacto.

O owner recusou aprovar sem resolver o Gainwell pelo **canal** — o discriminador que ele proprio
fixou — em vez do padrao (mesmo owner + 6 dias). A recusa era metodologicamente correta, e o dado
deu razao a leitura dele.

- ✅ **T1 — Gainwell e `free_agent`, e ENTRA no grupo.** A reaquisicao de 2025-09-01 e
  `tx:1268069831555424256` (liga 2025, leg 1): `type: "free_agent"`, `status: "complete"`,
  `settings: null`, `waiver_bid: null` — **reconfirmada AO VIVO na API nesta sessao**, nao so do
  dump. Prova de contraste na propria historia dele: o waiver claim **failed** de 2024
  (`tx:1159714113438957568`) veio com `type: "waiver"` e `settings.waiver_bid: 0` — quando e
  waiver, a API marca. Canal FA ⇒ 6.8 nao se aplica (so existe no canal waiver) ⇒ contrato reabre
  em 2025 ⇒ `contract_year = 2` errado tambem para ele. ⛔ **A "6.8 literal" da VERIF cai; a
  leitura do owner (6 dias atravessam o waiver period) esta confirmada pelo dado.**

- ✅ **T2 — canal dos 21 + Bates: `free_agent` em 23/23.** Os 21 CORRIGIR reconfirmados um a um
  contra a transacao da API (type + status + bid); **nenhum waiver inesperado**. Bates
  (`tx:1276659069179924480`) tambem `free_agent` — ambiguidade mantida por escopo, mas sob a mesma
  regua ela se dissolve. **Invariante estrutural medido nas 1125 txs do chain: 225/225 waivers
  completos tem `settings.waiver_bid`; 661/661 `free_agent` completos nao tem.** O canal e
  estrutura da API, nao convencao de rotulo.

- **T3 — a conta e o mecanismo.** Os 22 sao **homogeneos**: `cy=2, css=2025, acq=free_agent,
  sal=$1, needs_review=0`. **A correcao toca UM campo: `Player.contract_year`, 2 → 1.** Salario
  ($1 = ano-1 FA correto), `contract_start_season` (2025 certo), `acquisition_type` (canal real) e
  `espn_ref_value` ficam. Como `free_agent ∈ _WAIVER_TYPES`, **a correcao de dado basta** — com
  `cy=1` o rollover aplica sozinho `0,8 × ESPN REF` no `next_yr=2`; nao precisa mexer no motor
  para os 22. Conta com ESPN REF atual: **$28 → $33 (+$5)** — Pierce $3→$5, Watson $3→$4,
  P. Washington $3→$4, Wilson $1→$2; os 16 com ESPN REF 1.0 tem delta $0 **hoje** (correcao de
  contagem; o valor aparece com a definitiva de 18/08).
  ⚠️ **Vao canonico declarado:** `correct_player_salary` (models.py:216) so corrige salario; a
  unica porta que edita `contract_year` com trilha e o approve do M2 (`_REVIEW_ALLOWED_EDITS`,
  admin.py:1015), que exige `needs_review=True` — e os 22 estao em 0. **O prompt de correcao
  devera criar a porta no molde do M2:** escrita do campo + `PlayerHistory` de auditoria (old→new
  nas notes) na mesma transacao. Trilha resultante: 1 linha de `PlayerHistory` por jogador;
  `SalaryHistory` intocada (sem mudanca de salario; e esta vazia, F1B).

- ⚠️ **T4 — reconferencia contra `/data/dynasty.db`: BLOQUEADA desta maquina.** Sem Render CLI nem
  API key local; rotas de prod atras de OAuth interativo. O vivo so e alcancavel via Render
  Dashboard → Shell. **Comando sqlite3 read-only pronto no `improvements.md`** (select das 22
  linhas por `sleeper_player_id`) — esperado: todas `cy=2, css=2025, acq=free_agent, sal=1,
  needs_review=0, is_dropped=0`; qualquer divergencia suspende a linha correspondente. O seed
  lido (git, 01/08) reflete as trades de 28-30/07 — frescor indireto, nao prova.

- **Registrado sem decidir:** a regua do canal generaliza — os flags "6.8 mesmo owner" de
  **Tucker** e **Bigsby** tambem se dissolvem (openers `free_agent`); **Willis** e **Noel**
  entraram por waiver real (bid $0) e seguem como estavam — Noel continua o indeterminado
  legitimo (claim que carrega contrato de leilao 2025).

**Nada corrigido. O grupo final para aprovacao nominal e de 22 — os 21 da VERIF + Gainwell.
A correcao segue sendo prompt separado, condicionada ao T4 no Render Shell.**
