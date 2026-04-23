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
