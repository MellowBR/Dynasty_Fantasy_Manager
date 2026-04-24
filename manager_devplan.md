# devplan.md — Fantasy Manager

> Plano vivo + Log de Decisões  
> Última atualização: 23/04/2026 (M14 + M9 + M13 concluídos — atalho universal para propor trade em 1 clique)  
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
