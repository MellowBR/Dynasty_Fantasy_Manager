# devplan.md — Fantasy Manager

> Plano vivo + Log de Decisões  
> Última atualização: 12/06/2026-pt2 (F11 ✅ smoke prod + F10: réplica JS de draft_budget eliminada — summary do cap projector consome o backend canônico)  
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
