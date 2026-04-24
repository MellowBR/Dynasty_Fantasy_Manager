# improvements.md — Fantasy Manager

> Backlog vivo de melhorias, bugs e features pendentes.
> Atualizado em: 24/04/2026 (UX1 + UX3 + UX4 concluídos)
> Convenções: 🔲 pendente | ⚠️ parcial | ✅ concluído

---

## Status Rápido

| ID | Item | Prioridade | Status |
|----|------|------------|--------|
| X1 | Acesso multi-usuário (PythonAnywhere + OAuth + permissões) | Alta | ✅ 31/03/2026 |
| X1a | Preparar app para produção (wsgi.py, .env, ProxyFix, python-dotenv) | Alta | ✅ 31/03/2026 |
| X1b | Google OAuth + Flask-Login | Alta | ✅ 31/03/2026 |
| X1c | Tabela `users` no dynasty.db + seed_users.py | Alta | ✅ 31/03/2026 |
| X1d | Decorators `@login_required` / `@admin_required` nas rotas | Alta | ✅ 31/03/2026 |
| S1 | Sync detecta trades do Sleeper e move contratos automaticamente | Alta | ✅ 22/04/2026 |
| T1 | Redesign Trade Manager: simulador multi-owner + link compartilhável | Alta | ✅ 22/04/2026 |
| T2 | Integrar valores dynasty FantasyCalc no preview de trade | Média | ✅ 22/04/2026 |
| Q1 | Script de simulação de temporada (validar salary rollover) | Média | 🔲 |
| M1 | Validação de cap antes de confirmar trade | Média | 🔲 |
| M2 | Tela de aprovação em lote de jogadores `needs_review=True` | Média | 🔲 |
| M3 | Exportar dynasty.db em formato legível para os outros owners | Baixa | 🔲 |
| M4 | Banner de sync desatualizada com timestamp e botão "Sincronizar agora" | Baixa | 🔲 |
| M8 | Auditoria do lottery (seed + página de verificação) + visualização de bolinhas + fluxo em 2 fases | Baixa | ✅ 23/04/2026 |
| M9 | Redesign tela de picks: grid navegável + atalho para trade | Média | ✅ 23/04/2026 |
| M10 | Autocomplete de jogador na calculadora de salário | Baixa | 🔲 |
| M11 | Teste de auto-containment documental | Média | ✅ 22/04/2026 |
| M12 | Vincular owners a times via tela de admin com lookup do Sleeper | Média | ✅ 22/04/2026 |
| M13 | Página de jogador + "Propor Trade" | Média | ✅ 23/04/2026 |
| M14 | /trades aceitar query params team_a/team_b (pré-requisito M9 + M13) | Média | ✅ 23/04/2026 |
| F6 | Remover "keeper" como acquisition_type (migrar → auction_draft) | Média | ✅ 22/04/2026 |
| F8-RESTORE-GAP | /restore deveria chamar backfill_trades automaticamente | Baixa | ✅ 22/04/2026 |
| M5 | Ordenação por posição em todas as telas de roster | Baixa | ✅ 02/04/2026 |
| M6 | Importar resultados de temporada para atualizar ESPN ref values automaticamente | Baixa | 🔲 |
| M7 | Trade Manager: layout mais compacto e janela maior | Baixa | ✅ 02/04/2026 |
| F4 | Fix OAuth callback local (ProxyFix, host, APP_ENV, secret) | Alta | ✅ 02/04/2026 |
| F5 | Auto-seed users no startup a partir de `data/users.csv` | Média | ✅ 02/04/2026 |
| F7 | Fix SalaryHistory duplicado + rewrite 3 Browns + redesign /salary_history narrativo | Alta | ✅ 22/04/2026 |
| F7b | Data migration automática para limpar DB de produção (Render) no próximo boot | Alta | ✅ 22/04/2026 |
| F8 | Reconstruir PlayerHistory a partir da Sleeper API (drafts + transactions chain) | Alta | ⚠️ F8a concluído 22/04/2026 |
| F8a | Core rebuild via Sleeper chain + migration (sleeper_event_ref + UNIQUE) | Alta | ✅ 22/04/2026 |
| F8b | Guard AppConfig.f8_rebuilt em import_csv.py | Alta | ✅ 22/04/2026 |
| F8c | Endpoint admin + UI + ajuste do boot | Alta | ✅ 22/04/2026 |
| F1 | Correção de salários por partial name match (3 Browns bug) | Alta | ✅ 28/03/2026 |
| F2 | Ordenação do Round 1 via `draft_lottery_result` + `season_standings` | Alta | ✅ 28/03/2026 |
| F3 | Histórico inline (accordion) na aba de histórico | Média | ✅ 28/03/2026 |
| O1 | Linkificar nomes de jogadores em todas as telas | Média | ✅ 23/04/2026 |
| O2 | Enriquecer página do jogador: stats históricas + ADP | Média | 🔲 |
| L1 | League Hub: visão geral da liga + detalhe por time | Alta | ✅ 23/04/2026 |
| L2 | League Hub season mode: matchups, schedule, standings | Baixa | 🔲 |
| N1 | Redesign navbar: estrutura com dropdowns + acesso rápido aos times | Média | ✅ 23/04/2026 |
| C1 | Cap projector: modo "drop programado" para simular liberações de cap | Média | 🔲 |
| M8-PERM | Lottery: simulação aberta a owners + bloqueio server-side pós-oficial | Média | ✅ 23/04/2026 |
| T2-FIX | Picks Rd2+ sem dynasty value no preview/proposta de trade | Média | ✅ 24/04/2026 |
| T2-FIX-2 | Réplica JS pickFcSid em trades.html (fix estrutural — `/api/picks` pré-resolve dynasty_value) | Alta | ✅ 24/04/2026 |
| IR-CLEANUP | Remover seletor manual de IR no roster (sync Sleeper já é autoritativo) | Baixa | 🔲 |
| UX1 | Redesign tabela de roster em /team/<id>: foto, badge acquisition PT-BR, dynasty inline | Média | ✅ 24/04/2026 |
| UX2 | Acquisition types PT-BR em telas restantes (admin, cap_projector, salary, salary_history) | Baixa | 🔲 (team_detail + roster ✅ via UX1+UX4) |
| UX3 | Fotos de jogadores em telas densas (team_detail, cap_projector) | Baixa | ✅ 24/04/2026 |
| UX4 | Macro compartilhada de linha de roster (HYBRID) — converge layout de /team/<id> e / com densidade estilo FantasyPros | Média | ✅ 24/04/2026 |

---

## Itens Pendentes

---

### S1 — Sync Detecta Trades do Sleeper e Move Contratos Automaticamente
✅ **Concluído (22/04/2026)** — Prioridade **Alta**

**Problema:** Trades eram registradas manualmente via `POST /api/trades/confirm`. Sync não distinguia trade de waiver/drop — reatribuía `team_id` sem Trade/PlayerHistory. `Trade` table tinha 0 rows.

**Resolvido (22/04/2026):**

**Arquitetura:**
- Nova função `_sync_trades(league_id)` em `sync_sleeper.py`: itera legs 1-18 de `GET /league/{id}/transactions/{leg}`, filtra `type=trade AND status=complete`, idempotente via `sleeper_transaction_id`. Move `Player.team_id` via `adds/drops`, `Pick.current_team_id` via `draft_picks[]`, cria `PlayerHistory` por ativo, cria `Trade` row com `source='sleeper_sync'`.
- Integrado em `run_sync()`: toda sincronização com Sleeper agora detecta trades automaticamente.
- Novo endpoint `POST /api/admin/sync_trades/backfill` (`@admin_required`): importa trades da `previous_league_id` (liga da temporada anterior). Idempotente.
- Migração schema: `Trade.source` (default 'manual') + `Trade.sleeper_transaction_id` (unique nullable) via `_run_migrations()`.

**Tratamento de N-way trades (abordagem C+):**
- 2-way: Trade row normal (`team_a`, `team_b`).
- N>2: Trade row placeholder com `team_b = "N-way: <outros times>"` e `description = "[N-WAY] ..."`. Players/picks movem corretamente via adds/drops. PlayerHistory por ativo. Warning em SyncLog. Admin sempre vê a trade na UI, nunca precisa de intervenção de código.
- Dados reais: 29/29 trades históricas da liga 2025 são 2-way. N>2 é caminho futuro não bloqueante.

**Backfill inicial (incluído no seed `dynasty.db`):**
- 29 trades da liga 2025 importadas (legs 1-11).
- 78 entries `PlayerHistory event_type='trade'` geradas.
- 19 warnings esperados: picks de 2025 já drafadas (não existem mais em `picks` — `sync_sleeper` deleta picks de seasons passadas) + 1 player dropado antes do snapshot atual. Nenhum bloqueante.

**UI:**
- Card "Trades Históricas (Backfill)" adicionado ao `/admin` com botão "Importar Trades Históricas". Idempotente — re-chamadas retornam `imported=0, skipped=29`.

**Validação:**
- `SELECT COUNT(*) FROM trades` → 29
- `SELECT COUNT(DISTINCT sleeper_transaction_id) FROM trades` → 29
- `SELECT COUNT(*) FROM trades WHERE source='sleeper_sync'` → 29
- `SELECT COUNT(*) FROM player_history WHERE event_type='trade'` → 78
- Re-run backfill → imported=0, skipped=29 ✅ (idempotência confirmada)

**Impacto:** Confirmação manual de trades fica opcional — sync normal agora captura trades automaticamente. Desbloqueia T1 (trade manager como simulador puro).

---

### T1 — Redesign Trade Manager: Simulador Multi-Owner + Link Compartilhável
✅ **Concluído (22/04/2026)** — Prioridade **Alta**

**Implementado:**

1. **Removido `POST /api/trades/confirm`** de `routes/trades.py` (era `@admin_required`, movia players + criava Trade row). Com S1 ativo, esse endpoint criava shadow trades — o Manager confirmava antes do Sleeper e o sync criava duplicata. Import de `PlayerHistory` também removido (só era usado pelo confirm). JS `executeTrade()` removido do template.

2. **Novo modelo `TradeProposal`** em `models.py`: `id TEXT PK (UUID v4)`, `team_a_id`, `team_b_id`, `players_a/b` e `picks_a/b` como JSON text arrays, `created_by`, `created_at`, `expires_at` (created_at + 7 dias), relationships com Team e User. Método `is_expired()`. Criada automaticamente via `db.create_all()` (tabela nova, sem Migration explícita necessária).

3. **Extraído `_compute_cap_impact()`** como helper puro em `routes/trades.py` — compartilhado entre `preview_trade()` (POST JSON) e `view_trade_proposal()` (renderização read-only). Zero duplicação de lógica de cálculo. Enriquecido com `owner_name` e `owner_avatar` no payload por lado.

4. **`POST /api/trades/proposals`** (`@login_required`): recebe mesmo payload do preview. Valida que cada lado tem ≥ 1 asset (player ou pick). Persiste via UUID. Retorna `{proposal_id, url, expires_at, ttl_days}`.

5. **`GET /trades/proposta/<uuid>`** (`@login_required`): resolve proposal, renderiza `trade_proposal.html`. Cap impact **recalculado no momento** do acesso (reflete salários atuais, não snapshot do momento da criação — opção deliberada). Se expirada: 410 com mensagem amigável. Se não encontrada: 404 com template de erro.

6. **Template novo `trade_proposal.html`**: page header, badge "📸 Simulação", card com times + owner avatar + info de criação/expiração, layout `.trade-side` reutilizado, cada lado mostra "📤 Envia" e "📥 Recebe" com pos-badge + nome + salary + contract_display, cap before/after com text-ok/text-danger. Link de "← Simular nova trade" de volta. Zero controles de ação. Apresenta "Expira em X dia(s)" ou "expira hoje".

7. **UI em `trades.html`**: botão "✅ Confirmar Trade" virou "🔗 Gerar Link Compartilhável" (btn-primary). Modal reusado com novo estado: `modal-link-area` com input read-only do URL, botão "📋 Copiar" (via `navigator.clipboard.writeText` com fallback para `document.execCommand`) e botão "↗ Abrir" target=_blank. Título do modal muda para "🔗 Proposta Gerada". `closeModal()` resetta estado para próximo uso limpo.

**Validação (22/04/2026) — 8 casos via Flask test_client:**

| # | Cenário | Resultado |
|---|---------|-----------|
| 1 | Botão "Confirmar Trade" removido do HTML | ✓ |
| 2 | `POST /api/trades/confirm` → 404 | ✓ |
| 3 | `POST /api/trades/proposals` happy path | 200, UUID, URL, TTL=7 |
| 4 | `GET proposal URL` logado | 200, HTML com times/players/"Simulação" |
| 5 | Proposta expirada | 410 com "expirou" no body |
| 6 | Sem login | 302 → /login |
| 7 | Gerar sem assets / apenas um lado vazio | 400 com erro amigável |
| 8 | Preview endpoint continua funcional | 200, cap_after correto |

**Não implementado (escopo futuro):** X2 (propor/aceitar/recusar dentro do Manager — mencionado no devplan como evolução de T1).

**Problema:** A tela de trade atual (`/trades`) mistura duas responsabilidades: (1) simular cap impact e (2) confirmar/registrar o trade no banco. Com S1, a confirmação passa a ser automática via Sleeper sync. A tela de trade precisa virar um **simulador puro** acessível a qualquer owner autenticado.

**Decisão sobre escopo:** T1 é um item único (não dois separados), porque o link compartilhável só faz sentido como parte do redesign do simulador. Separar criaria uma tela de trade intermediária que seria substituída logo em seguida. Estrutura recomendada:

**Proposta — Simulador + Link em um único item:**
1. **Simulador acessível a todos:** Qualquer owner autenticado (`@login_required`, não `@admin_required`) seleciona dois times, monta a trade, e vê o cap impact de ambos os lados. Sem botão "Confirmar" — trades são confirmadas via Sleeper (S1)
2. **Gerar proposta:** Botão "Gerar Link" salva o estado da simulação com UUID na tabela `trade_proposals` e retorna URL `/trades/proposta/<uuid>`
3. **Visualização pública:** O link mostra o preview completo (rosters antes/depois, cap impact) sem exigir login (ou com login, a definir)
4. **Expiração:** Propostas expiram após 7 dias

**Código atual a reutilizar:**
- `routes/trades.py:26-73` — `preview_trade()` já calcula cap impact corretamente, reutilizar lógica
- `templates/trades.html:117-176` — JS de seleção de players/picks, reutilizar
- Remover: `confirm_trade()` (passa a ser responsabilidade do S1) e botão "Confirmar" do template

**Nova tabela:**
```sql
CREATE TABLE trade_proposals (
    id TEXT PRIMARY KEY,
    team_a_id INTEGER, team_b_id INTEGER,
    players_a TEXT, players_b TEXT,    -- JSON arrays de player_ids
    picks_a TEXT, picks_b TEXT,        -- JSON arrays de pick_ids
    created_by INTEGER,               -- user_id
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);
```

**Pré-requisito:** S1 (sem sync automático de trades, alguém ainda precisa confirmar manualmente)

**Nota:** X2 (propor/aceitar/recusar dentro do Manager) fica como evolução futura de T1, só faz sentido depois de T1 + S1 estáveis em produção.

---

### T2 — Valores dynasty FantasyCalc no preview de trade
✅ **Concluído (22/04/2026)** — Prioridade **Média**

**Fonte:** [FantasyCalc](https://fantasycalc.com/) via `GET https://api.fantasycalc.com/values/current?isDynasty=true&numQbs=1&numTeams=12&ppr=1`. API pública, matching direto com DB via `sleeperId` (100% exato em spot-check de 20 players; cobertura agregada 84,9% — 236/278 players ativos, os 42 restantes são DSTs/kickers/fringe).

**Implementado:**
1. **Módulo novo `dynasty_values.py`**: fetcher + cache JSON (`data/.dynasty_values_cache.json`, TTL 24h, padrão `.sleeper_players_cache.json`) + `get_dynasty_values(force_refresh)` + helper `pick_sleeper_id(pick, current_season)` que converte `Pick` em formato FC `DP_<year_offset>_<pick_index>`. Degradação elegante: se API cai e cache também, retorna `{values: {}, fetched_at: None, count: 0}`.

2. **Enriquecimento em `_compute_cap_impact()`** (`routes/trades.py`): cada player/pick no dict retornado ganha `dynasty_value` (int ou None). Picks sem `projected_pick` recebem valor estimado do middle-of-round (pick_index = (round-1)*12 + 5) e flag `dynasty_value_is_estimate=True`. Por side: `dynasty_total_out`, `dynasty_total_in`, `dynasty_delta`. Top-level: `dynasty_available` (bool).

3. **Endpoints novos em `routes/trades.py`**:
   - `GET /api/dynasty_values` (`@login_required`) — retorna `{values: {sid: value}, fetched_at, age_hours, count, ttl_hours}`. Usado pelo frontend pra carregar o mapa uma vez ao abrir `/trades`.
   - `POST /api/admin/dynasty_values/refresh` (`@login_required`, não admin — operação read-only externa) — força refetch ignorando TTL.

4. **Frontend `templates/trades.html`**:
   - Banner no topo do card com freshness: *"🪙 Valores dynasty (FantasyCalc) — 457 ativos, atualizados há Xh"* + botão "🔄 Atualizar Valores" (desabilita se age < 1h).
   - Badge inline em cada checkbox de player/pick (`🪙6.801` ou `🪙4.118 est.` para picks estimadas).
   - **Barra espelhada dinâmica** abaixo dos seletores — duas metades (A azul à esquerda, B laranja à direita) com largura proporcional ao `max(totalA, totalB)`, transição suave `.35s`. Chip central mostra "✅ TEAM leva +Δ" ou "⚖️ Equilibrada" se delta < 5%. Recálculo 100% local via `toggleAsset()` — zero round-trip.
   - Modal de preview ganhou badge de vantagem no topo (`✅ {TEAM} leva vantagem (+X)` ou `⚖️ Trade equilibrada`) + linha `🪙 Dynasty: envia X · recebe Y · Δ ±Z` em cada side.

5. **CSS novo em `static/style.css`**: `.dynasty-banner`, `.dynasty-value-badge`, `.dynasty-bar-section`, `.dynasty-bar-labels`, `.dynasty-bar-track`, `.dynasty-bar-fill-a/b`, `.dynasty-bar-delta-chip` (com variantes `neutral/win-a/win-b`), `.dynasty-advantage` (variantes `neutral/win`). Reutiliza paleta existente + transição `.cap-bar-fill` padrão.

**Validação (22/04/2026) — 6 cenários via Flask test_client:**

| # | Cenário | Resultado |
|---|---------|-----------|
| 1 | `GET /api/dynasty_values` | 200, count=457, Bijan value=11128 |
| 2 | `POST /api/admin/dynasty_values/refresh` | 200, count=457, fetched_at atualizado |
| 3 | Template `/trades` renderiza todos os hooks | ✓ banner, barra, JS (load/update/refresh/pickFcSid), CSS |
| 4 | Preview enriquecido McBride ↔ Bowers | dynasty_available=True, A envia 6801 recebe 6960 (+159), B espelhado |
| 5 | FC indisponível + cache vazio | count=0, dynasty_available=False, preview de cap funciona normal, dynasty_value=None por asset |
| 6 | `python salary_engine_test.py` | 48/48 passam |

**Decisões registradas no Log do devplan:**
- FantasyCalc > KTC: API pública estável, matching por `sleeperId` (100% exato vs KTC por nome com risco "3 Browns"), inclui picks com valor.
- Cache em JSON (não tabela): padrão Sleeper já existente + operação é puramente ephemeral (TTL 24h).
- Recálculo 100% client-side: endpoint só chamado 1x no load + 1x no refresh manual. `toggleAsset` opera em memória.
- Refresh `@login_required` (não admin): operação read-only, sem efeito em dados do DB, qualquer owner pode atualizar.
- Picks sem `projected_pick`: middle-of-round como fallback + flag `estimate` visível (sufixo "est." e tooltip).

**Problema:** O preview de trade (`routes/trades.py:26-73`) mostra apenas cap impact (salary antes/depois). Não há indicação de valor de mercado dos jogadores envolvidos. Os owners precisam consultar o KeepTradeCut externamente.

**Proposta:**
1. Consumir API não-oficial do KTC para obter valores de trade por jogador
2. Cachear valores localmente (tabela `ktc_values` ou arquivo JSON com TTL de 24h)
3. Exibir no preview de trade: valor KTC de cada jogador/pick trocado + diferença total (quem "ganha" o trade em valor de mercado)
4. Matching por nome (reusar `player_lookup.py:find_player_by_name()` com hierarquia estrita)

**Riscos:** API não-oficial pode mudar ou ficar indisponível. Implementar com degradação elegante (trade funciona sem KTC, só não mostra os valores).

---

### Q1 — Script de Simulação de Temporada Completa
🔲 **Pendente** — Prioridade **Média**

**Problema:** O season rollover (passo 4 do offseason, `routes/offseason.py`) aplica VALORIZAÇÃO, incrementa `contract_year`, e renova contratos expirados. Esse processo é irreversível e afeta todos os 278+ jogadores. Hoje não há como validar o resultado antes de rodar em produção.

**Proposta:**
1. Script CLI (`simulate_season.py`) que roda o rollover completo em memória (sem gravar no banco)
2. Input: estado atual do `dynasty.db` + ESPN ref values
3. Output: tabela comparativa por jogador: salary atual → salary projetado, contract_year atual → próximo, renovações, jogadores que seriam cortados por cap
4. Reusar `salary_engine.py` que já é puro (zero DB dependencies): `full_contract_table()`, `project_next_salary()`, `valorization_rule()`
5. Flags opcionais: `--team <nome>` (filtrar por time), `--over-cap-only` (só mostrar times que estouram)

**Uso:** Dev/comissário only. Rodar antes do passo 4 do offseason para validar que nenhum salário ficou absurdo.

---

### M1 — Validação de Cap Antes de Confirmar Trade
🔲 **Pendente** — Prioridade **Média**

**Problema:** O preview de trade (`routes/trades.py:57-68`) calcula `over_cap` (linha 63) e exibe warning visual, mas `confirm_trade()` (linha 76-145) não bloqueia a confirmação. Um trade que estoura o cap é registrado normalmente.

**Proposta:** Adicionar validação server-side no início de `confirm_trade()`: calcular `cap_a_after` e `cap_b_after` (mesma lógica do preview) e retornar 400 se `> SALARY_CAP`.

**Nota:** Com S1, trades passam a ser confirmadas via Sleeper sync. A validação de cap pode migrar para um alerta pós-sync ("trade detectada, time X acima do cap") em vez de bloqueio.

---

### M2 — Tela de Aprovação em Lote de Jogadores `needs_review=True`
🔲 **Pendente** — Prioridade **Média**

**Problema:** Jogadores criados pelo Sleeper sync sem match no CSV ficam com `needs_review=True`, `salary=1.0`, `acquisition_type="unknown"` (`sync_sleeper.py:262-282`). Não há alerta visual nem tela dedicada para revisar esses jogadores em lote.

**Proposta:**
1. **Badge na navbar:** Contador de jogadores pendentes visível em todas as páginas (context processor)
2. **Tela de aprovação (`/admin/review`):** Lista todos os jogadores com `needs_review=True`, agrupados por time
3. **Edição em lote:** Para cada jogador, formulário inline para definir: salary, acquisition_type, contract_year. Botão "Aprovar" marca `needs_review=False`
4. **Ação em massa:** "Aprovar todos com defaults" para jogadores menores (salary=$1, tipo=unknown → free_agent)

**Código existente:** `Player.needs_review` já existe no modelo. Sleeper sync já seta `needs_review=True` para novos jogadores (linha 276).

---

### M3 — Exportar Estado da Liga para Visualização Externa
🔲 **Pendente** — Prioridade **Baixa**

**Problema:** Com X1 os owners passam a ter acesso ao Manager. Mas pode ser útil ter um endpoint `/api/estado` que retorne JSON com rosters, salários e picks — para uso futuro no Optimizer ou para owners que queiram consumir os dados.

**Proposta:** Endpoint GET `/api/estado` retornando JSON read-only. Sem autenticação especial além do `@login_required`. Não expor dados sensíveis (sem `is_admin`, sem emails).

---

### M4 — Banner de Sync Desatualizada
🔲 **Pendente** — Prioridade **Baixa**

**Problema:** Quando o Sleeper sync falha no startup (timeout ou API fora), o usuário não tem indicação visual de que os dados podem estar desatualizados.

**Proposta:** Banner visível em todas as páginas com timestamp da última sync e botão "Sincronizar agora". Só exibir quando a sync está desatualizada. Fonte de dados: `SyncLog.query.order_by(SyncLog.synced_at.desc()).first()`.

---

### M6 — Importar Resultados de Temporada para Atualizar ESPN Ref Values
🔲 **Pendente** — Prioridade **Baixa**

**Problema:** Hoje a atualização de ESPN ref values é feita manualmente via PDF (passo 3 do offseason workflow, `espn_pdf_parser.py`). O processo exige download manual do PDF, upload no Manager, e matching de nomes.

**Proposta:** Criar pipeline que leia CSVs de stats por temporada (já disponíveis em `data/`: receiving, rushing, passing) e atualize os ESPN ref values automaticamente. Dados brutos já existem — falta o pipeline de processamento.

**Nota:** Os CSVs em `data/` são sementes desse trabalho. Formato e fonte dos dados futuros a definir.

---

### M8 — Lottery auditável + visualização de bolinhas + fluxo duas fases
✅ **Concluído (23/04/2026)** — Prioridade **Baixa**

**Implementado em três frentes (backend + UX + transparência):**

**Backend — auditoria com seed reprodutível:**
1. Modelo novo `LotteryAudit` em `models.py`: `random_seed`, `weights_json`, `pool_json` (snapshot dos 5 times + seeds + pesos), `executed_at`, `executed_by`, `result_hash` (SHA256 dos picks 1-5), `previous_audit_id`, `reason`, `is_canonical`. Criado via `db.create_all()` (tabela nova).
2. Helper `_draw_weighted_lottery(pool, seed)` em `routes/offseason.py`: bolinhas literais (cada time repetido `weight` vezes) + `random.seed(seed)` único + `random.shuffle` por pick (Opção B — seed derivado contínuo). Função pura, determinística, unit-testable.
3. `run_lottery` reescrito: gera `secrets.token_hex(16)`, delega picks 1-5 ao helper, persiste `LotteryAudit` com `is_canonical=True`. Retorna **409** se já existe audit canônica da season.
4. `POST /api/offseason/lottery/replace`: exige `reason` no body; marca audit canônica como superseded; grava nova row com `previous_audit_id` + `reason` + `is_canonical=True`. Cada re-run preserva histórico completo.
5. `GET /api/picks/lottery/<season>/verify`: re-roda `_draw_weighted_lottery` com o pool+seed salvos no audit canônico, compara com `DraftLotteryResult` + compara hash. Retorna `{match, result_hash_match, reproduced, actual}`.
6. Page `GET /picks/lottery/<season>`: template `lottery_audit.html` com seed, pool snapshot, picks 1-12, botão verificar, + histórico de tentativas superseded com timestamp + reason.

**UX — fluxo em duas fases no `/offseason`:**
7. **Fase 1 (pré-execução):** pool de 95 bolinhas coloridas (paleta fixa: vermelho 12º, azul 11º, verde 10º, roxo 9º, laranja 8º) em grid + legenda com % chance por time. **Nenhum botão "testar sorteio"** — fase é puramente estatística, remove cherry-picking.
8. **Fase 2 (execução única):** botão "🎲 Executar Sorteio Oficial" com confirm duplo. Ao executar: reveal animado pick a pick com `setTimeout 1500ms`, bolinhas do time sorteado são destacadas (`scale 1.6 + glow dourado`) e depois `eliminated` (opacity .15). Picks 6-12 aparecem de uma vez após os 5. Pós-reveal: "Travar" + "Executar novamente" + "Ver auditoria".
9. **Re-run com atrito:** modal secundário pede textarea `reason` obrigatória. POST a `/lottery/replace`. Nova row LotteryAudit linkada à anterior. Histórico público na page de auditoria.

**Decisões de design registradas no Log do devplan (23/04/2026):**
- Tabela `LotteryAudit` separada (não coluna em `DraftLotteryResult`) — granularidade por execução.
- `pool_json` snapshot — reprodução resistente a edições posteriores de `SeasonStandings`.
- Algoritmo bolinhas literais + `random.shuffle` — alinha com UI, auditoria didática. Matematicamente equivalente ao `random.uniform + cumulative sum` anterior, mas mais transparente.
- Fluxo duas fases — simulação estatística (só probabilidades) + sorteio oficial único. Fecha cherry-picking (admin não pode rodar 10x e travar o que prefere).
- Re-run caro, não proibido — `reason` obrigatório + histórico visível em `/picks/lottery/<season>`.
- Paleta fixa 5 cores (vermelho/azul/verde/roxo/laranja) em vez de HSL gerado — contraste garantido.

**Validação (23/04/2026) — 9 cenários via Flask test_client:**

| # | Cenário | Resultado |
|---|---------|-----------|
| 1 | `POST /run_lottery` inicial | 200, seed, hash, is_canonical=True, 12 picks |
| 2 | `POST /run_lottery` duplicado | 409 com mensagem apontando `/replace` |
| 3 | `GET /verify` match | `match=true, result_hash_match=true` |
| 4 | `UPDATE team_name` manual + verify | `match=false` (tampering detectado); `result_hash_match=true` correto pq audit é íntegra |
| 5 | `POST /lottery/replace` com reason | 200, `previous_audit_id` preenchido, nova row canônica |
| 6 | `POST /lottery/replace` sem reason | 400 "reason obrigatório" |
| 7 | `/picks/lottery/2026` template | 200, Seed + Pool + Histórico visíveis |
| 8 | `/offseason` UI | 95 bolinhas renderizadas, botão "Executar Sorteio Oficial" visível em estado limpo, "Travar" + "Ver auditoria" visíveis pós-execução |
| 9 | `salary_engine_test.py` | 48/48 passam |

**Arquivos modificados:** `models.py` (+modelo), `routes/offseason.py` (+helper, rewrite, replace endpoint, compute_result_hash), `routes/picks.py` (page + verify endpoint), `templates/offseason.html` (pool + reveal + modal), `templates/lottery_audit.html` (novo), `static/style.css` (classes lottery + keyframes).

**Problema:** O sorteio de lottery (`routes/offseason.py:258-357`) usa `random.uniform()` sem seed fixo. O resultado é salvo na tabela `draft_lottery_result` (season, pick_number, team_name, source, locked) mas sem registro do seed usado, dos pesos aplicados, nem do histórico de sorteios anteriores que foram descartados. Qualquer owner pode questionar se o sorteio foi justo — não há prova auditável.

**Proposta:**
1. **Salvar seed e pesos:** Ao rodar o lottery, gerar um `random_seed` (ex: hash de timestamp), setar `random.seed(seed)`, e salvar na tabela `draft_lottery_result` ou nova tabela `lottery_audit` (seed, pesos usados, timestamp, resultado completo)
2. **Página pública:** Rota `/picks/lottery/<season>` acessível sem login (ou com `@login_required`) mostrando: seed usado, pesos por posição, resultado detalhado pick a pick, possibilidade de verificar reproduzindo o sorteio com o mesmo seed
3. **Modelo `DraftLotteryResult`:** Hoje não tem campo para seed — adicionar coluna `random_seed` ou criar tabela auxiliar

---

### M9 — Redesign tela de picks: grid navegável + atalho para trade
✅ **Concluído (23/04/2026)** — Prioridade **Média**

**Implementado:**

1. **Backend (`routes/picks.py` `picks_page`):** substitui `grid = {season: {round: [picks]}}` por `matrix = {season: {teams_ordered, cells: {(team, round): pick}, projections: {(team, round): proj}}}`. Times ordenados por `projected_pick` do R1 (fallback alfabético). Passa `my_team_name = current_user.team_rel.name` ou `None` se admin sem time vinculado.

2. **Template (`templates/picks.html`):** grid matrix 4 colunas (label + R1 + R2 + R3) × N linhas (times). Célula é `<a>` clicável quando `traded_away=True` + `current_team != my_team_name`; senão é `<div>` estático. Link gerado via `url_for('trades.trades_page', team_a=my_team_name, team_b=pick.current_team_name)` — Flask aplica urlencode automático. Banner de warning quando `my_team_name is None` apontando pra `/admin/users`.

3. **CSS (`static/style.css`):** `.picks-matrix` grid, `.picks-matrix-cell` + variantes (`is-mine` borda verde sutil, `is-traded` fundo azul, `clickable` hover highlight), `.picks-badge` para `#N` do pick. Botão ✎ de edição admin aparece no hover (opacity transition).

4. **Filtro de equipe adaptado:** `filterTeam(name)` agora itera em grupos de 4 children (rowlabel + 3 cells) após os 4 headers iniciais. Linha visível se `origTeam === name` OU alguma célula tem `current_team === name`.

5. **Admin preservado:** botão ✎ discreto por célula (opacity 0 default, 1 no hover) chama `openPickEdit` existente. Modal de edição intocado.

**Validação (23/04/2026) — 9 cenários via Flask test_client:**

| # | Cenário | Resultado |
|---|---------|-----------|
| 1 | `/picks` renderiza grid 2026 | ✓ status 200, título "2026" visível |
| 2 | Ordem linhas por projected_pick R1 | ✓ Miller Time! (pick 1) no topo |
| 3 | Picks trocadas mostram → dono atual | ✓ 18 células com `.pick-current-owner` (18 picks trocadas no DB) |
| 4 | Células clicáveis quando `current_team != my_team` | ✓ 16 `<a>` (18 trocadas − 2 onde Cangaceiros é o destino; não faria sentido linkar pra proposta comigo mesmo) |
| 5 | URL gerada tem team_a + team_b + urlencode | ✓ `team_a=Cangaceiros+da+Colina&team_b=3+peat%E2%80%A6+of+pain+%F0%9F%AB%A0` |
| 6 | Picks próprias com `is-mine` + label "minha" | ✓ 9 células `is-mine` (picks da Cangaceiros do DraftLotteryResult + trades recebidas) |
| 7 | `filterTeam` presente no JS | ✓ adaptado para iterar em grupos de 4 children |
| 8 | Modal edit admin funcional | ✓ `openPickEdit` + `#pick-modal` intactos |
| 9 | Season 2027/2028 sem projeção | ✓ grid ordenado alfabeticamente, sem `.picks-badge` |
| bonus | `current_user.team_rel is None` (admin sem time) | ✓ banner warning visível, 0 células clicáveis |

**Desbloqueia:** M13 (página de jogador pode reusar o mesmo padrão de link para trade).

**M9-FIX (23/04/2026) — escopo expandido:** A condição original `clickable = traded_away AND current != my_team` era restritiva demais (só picks trocadas). Feedback do owner: todas as picks de outros times (trocadas ou não) devem permitir "pedir em trade", e minhas próprias picks devem permitir "oferecer". Mudanças:

- **`templates/picks.html`:** condição virou `clickable = my_team_name is not None`. Href condicional conforme dono:
  - Minha pick: `/trades?team_a=<meu>&pick_a=<id>`
  - Outra pick: `/trades?team_a=<meu>&team_b=<dono>&pick_b=<id>`
- **`routes/trades.py`:** `trades_page` aceita `?pick_a` e `?pick_b` (extensão do M14). Valida que pick existe E pertence ao team preset correspondente — senão ignora silenciosamente. Passa `preset_pick_a`/`preset_pick_b` ao contexto.
- **`templates/trades.html`:** `data-preset-pick-a`/`data-preset-pick-b` no `.trade-layout`. `data-pick-id` nos checkboxes de pick. No `loadSide`, após renderizar picks: se há preset para esse side, marca checkbox + adiciona ao `selected.picks[side]` + chama `updateDynastyBar()`. Consome o data-attr após uso para não remarcar em reloads.

Validado (7 cenários): 108 células clicáveis (12×3×3), 9 minhas (pick_a) + 99 outras (pick_b); preset-pick correto em todos os caminhos; pick inexistente/mismatch ignorada silenciosamente; `/trades` sem params preservado.

**Problema:** A tela `/picks` exibe picks em listas sem deixar claro quem é o **dono atual** quando a pick foi trocada. Para encontrar a pick 1.03 (ou qualquer pick futura) e propor trade, o owner faz 4 passos: (1) navegar pela lista, (2) identificar dono atual, (3) ir pra `/trades`, (4) selecionar manualmente os dois times. Fluxo longo e suscetível a erro.

**Proposta:**

1. **Grid visual por season:** matrix compacta com todas as picks organizadas por round e posição projetada. Cada célula mostra: **dono original** + **dono atual** (se diferente, destacar visualmente — badge colorido, tooltip com histórico da pick). Picks sem posição projetada (seasons futuras sem sorteio) agrupadas por round com dono atual visível.

2. **Estado do sorteio:** se `LotteryAudit.is_canonical=True` existe para a season (M8), usar posições reais do lottery. Se não existe, mostrar dono atual sem posição projetada.

3. **Clique numa pick → atalho para trade:** abre `/trades?team_a=<current_user.team_rel.name>&team_b=<current_team_name_da_pick>` com os dois times pré-selecionados via M14. Reduz o fluxo de 4 cliques para 1.

4. **Picks trocadas sem duplicação:** cada pick aparece uma vez (na posição do dono original), com indicação visual de quem detém atualmente. Elimina a duplicação atual onde a mesma pick aparece sob original e atual.

**Código existente a reusar:**
- `_build_pick_projections()` (`routes/picks.py:83-137`) — já resolve posição projetada considerando lottery + standings.
- `Pick.traded_away`, `Pick.current_team_name`, `Pick.original_team_name` — já no modelo.
- `LotteryAudit.is_canonical` (M8) — fonte de verdade pra posições reais.

**Pré-requisito:** M14 (`/trades` aceitar query params).

---

### M13 — Página de jogador + "Propor Trade"
✅ **Concluído (23/04/2026)** — Prioridade **Média**

**Implementado com 4 refinamentos da análise crítica pré-implementação (E1/E2/E3/O1):**

1. **Rota `GET /player/<int:player_id>`** (`@login_required`) em `routes/roster.py`:
   - E1: parâmetro nomeado `player_id` (não `id` — evita shadow do builtin Python).
   - E3: `dynasty_value` resolvido no backend via `get_dynasty_values()` do T2. Passa como contexto Jinja. Zero fetch JS na página, sem flash visual.
   - `can_propose_trade` boolean pré-calculado no backend — `my_team_name is not None AND player.team_id != current_user.team_id`. Simplifica condicional Jinja.
   - Mapa `_ACQ_LABELS` PT-BR inline (10 entries) para traduzir acquisition_type.

2. **Template novo `templates/player_detail.html`** (~180 linhas):
   - Header flex: foto via `sleepercdn.com/content/nfl/players/thumb/<sid>.jpg` com `onerror="this.style.display='none'"` + nome + posição + time + owner avatar.
   - Botão "⇄ Propor Trade" só renderizado quando `can_propose_trade=True`. Link via `url_for('trades.trades_page', team_a=my_team_name, team_b=team.name)` — M14 pré-seleciona ambos.
   - Bloco contrato: grid com 6 campos (salary, contract_display, contract_start_season, acquisition_label, espn_ref_value, dynasty_value formatado "🪙 X.XXX").
   - Timeline via fetch `/api/player/<id>/history` reusando `renderEventRow` (copiado inline + mesmo `EVENT_LABELS`/`EVENT_BADGES` do salary_history).
   - Include `_trade_detail_modal.html` para eventos de trade clicáveis.

3. **Partial novo `templates/_trade_detail_modal.html`** (O1 aplicado — ~80 linhas):
   - Extrai o modal de trade clicável do `salary_history.html` para partial reutilizável.
   - Inclui HTML + CSS (`.trade-detail-*`) + JS (`openTradeDetail`, `closeTradeDetail`).
   - Assume `escapeHtml(s)` disponível no escopo host (função simples, duplicada nos templates consumidores — trade-off aceito).

4. **`templates/salary_history.html`** refatorado para usar o include — modal inline removido, `<style>` e `<script>` enxutos. Nome do jogador no `renderPlayerCard` agora é `<a href="/player/${p.player_id}" onclick="event.stopPropagation()">` — `stopPropagation` evita colidir com o toggle do accordion.

5. **`templates/roster.html`** ganhou:
   - Lista resumo de `renewal_candidates` e `needs_review` com links `<a href="{{ url_for('roster.player_detail', player_id=p.id) }}">`.
   - Cada linha de player-row ganhou ícone discreto `🔗` ao lado do nome (título "Abrir página do jogador") — preserva comportamento atual de `showPlayerHistory` modal inline que owner pode já estar usando.

6. **`templates/trades.html`** — E2 aplicado:
   - Nome do jogador nos checkboxes virou `<a class="asset-name" href="/player/${p.id}" target="_blank" onclick="event.stopPropagation()">`.
   - **`event.stopPropagation()` é crítico**: sem ele, clique no `<a>` dentro do `<label>` toggleia o checkbox por default HTML. `target="_blank"` preserva estado da trade atual.

7. **CSS (`static/style.css`)**: `.player-detail-header`, `.player-photo` (96px circle), `.player-contract-grid`/`.player-contract-field` com `field-label` + `field-value`, `.player-link` azul, `.player-external-link` discreto (opacity 0.5 → 1 hover).

**Validação (23/04/2026) — 10 cenários via Flask test_client:**

| # | Cenário | Resultado |
|---|---------|-----------|
| 1 | GET `/player/91` (McBride) | 200, nome + foto + timeline + modal tudo presente |
| 2 | McBride (mesmo time do admin) — botão "Propor Trade" | **NÃO aparece** ✓ |
| 3 | Bowers (Trust The Process) — botão aparece | ✓ href=`/trades?team_a=Cangaceiros+da+Colina&team_b=Trust+The+Process` |
| 4 | `/` (roster) tem links `/player/<id>` | 25 links encontrados + ícone `🔗` |
| 5 | `/salary_history` JS `renderPlayerCard` | link + `stopPropagation` presentes |
| 6 | `/trades` JS `loadSide` | `target="_blank"` + `stopPropagation` + link `/player/${p.id}` |
| 7 | Hollywood Brown (sem sleeper_player_id) | img suprimido via Jinja `{% if %}`, nome e resto OK |
| 8 | GET `/player/99999` | **404** via `abort(404)` |
| 9 | E3: dynasty_value server-rendered | `🪙 X.XXX` no HTML static, zero `/api/dynasty_values` fetch |
| 10 | O1: modal partial em ambas páginas | `openTradeDetail` + `#trade-detail-modal` em `/salary_history` E `/player/<id>` |

**Arquivos modificados:** `routes/roster.py` (rota + ACQ_LABELS, ~60 linhas), `templates/player_detail.html` (novo, ~180), `templates/_trade_detail_modal.html` (novo, ~80), `templates/salary_history.html` (include + link + clean), `templates/roster.html` (2 refs + link external), `templates/trades.html` (asset-name → `<a>`), `static/style.css` (+80 linhas M13 classes).

**Problema:** Não existe página dedicada por jogador no Manager. Para propor trade por um jogador específico (de outro time), o owner vai até `/trades` e seleciona manualmente os times e o jogador na lista de checkboxes. Navegação indireta.

**Proposta:**

1. **Rota `GET /player/<id>` (`@login_required`):** página dedicada por jogador com:
   - **Header:** nome, posição (pos-badge), time atual, foto do jogador via template Sleeper — `https://sleepercdn.com/content/nfl/players/thumb/<sleeper_player_id>.jpg` com `onerror="this.style.display='none'"` (mesmo padrão dos avatars de team). Fallback silencioso para retirees, rookies recém-chegados, DSTs.
   - **Bloco contrato:** `salary`, `contract_year`, `contract_start_season`, `acquisition_type`, `espn_ref_value`, **`dynasty_value`** (FantasyCalc via `dynastyMap` do T2 — lookup por `sleeper_player_id`).
   - **Timeline:** histórico de eventos reusando `/api/player/<id>/history` (endpoint já existe com `display_notes` formatados e ordenação cronológica do F8).
   - **Botão "⇄ Propor Trade":** abre `/trades?team_a=<current_user.team_rel.name>&team_b=<time_do_jogador>` com os dois times pré-selecionados via M14.

2. **Links para `/player/<id>` a partir de:**
   - Tela de roster (`/`) — clicar no nome do jogador
   - Tela `/salary_history` — clicar no nome do jogador no card
   - Tela `/trades` — nomes de jogadores nos checkboxes (ou ícone 🔗 discreto ao lado)

3. **Reuso:** `Player.to_dict()` cobre a maioria dos campos. `dynastyMap` do T2 resolve valor dynasty. `/api/player/<id>/history` de F7 resolve timeline.

**Pré-requisito:** M14 (`/trades` aceitar query params).

---

### M14 — `/trades` aceitar query params `team_a`/`team_b` para pré-selecionar
✅ **Concluído (23/04/2026)** — Prioridade **Média**

**Implementado:**
- `routes/trades.py` `trades_page()`: lê `request.args.get("team_a")` e `team_b`, valida contra `{t.name for t in teams}` (ignora silenciosamente se não existir), passa como contexto `preset_team_a` / `preset_team_b`.
- `templates/trades.html`: `data-preset="{{ preset_team_a or '' }}"` nos selects `sel-a` e `sel-b`.
- JS `DOMContentLoaded`: itera pelos dois lados, se `dataset.preset` preenchido, seta `sel.value` e chama `loadSide(side, preset)` automaticamente. Guard `if (sel.value === preset)` evita disparo se o option não foi renderizado (defesa contra time removido entre render e load).

**Validação (23/04/2026) — 4 cenários via Flask test_client:**

| # | Query string | Resultado |
|---|--------------|-----------|
| 1 | `?team_a=Cangaceiros+da+Colina&team_b=Trust+The+Process` | Ambos presets populados, selects pré-selecionados no load |
| 2 | (sem params) | Ambos `data-preset=""`, comportamento original |
| 3 | `?team_a=TimeInexistente&team_b=Trust+The+Process` | Sel-a vazio (ignora), sel-b pré-selecionado |
| 4 | `?team_a=Cangaceiros+da+Colina` (só um lado) | Sel-a pré-selecionado, sel-b vazio |

**Desbloqueado para implementação:** M9 (clique em pick → trade pré-selecionado), M13 (botão "Propor Trade" na página de jogador).

**Problema:** Hoje `trades_page` (`routes/trades.py:17-27`) carrega a tela com dois `<select>` vazios. Para a tela ser endpoint de atalho (vinda de M9 clique em pick, M13 botão "Propor Trade"), precisa aceitar `?team_a=<nome>&team_b=<nome>` e pré-carregar os seletores automaticamente.

**Proposta:**

1. **Backend (`routes/trades.py`):** `trades_page` lê `request.args.get("team_a")` e `team_b`, valida contra `Team.query.filter_by(name=...)` (ignora silenciosamente se não existir), passa como contexto Jinja (`preselect_a`, `preselect_b`).

2. **Template (`trades.html`):** dois `data-*` attributes no container principal:
   ```
   <div class="trade-layout" data-preselect-a="{{ preselect_a or '' }}" data-preselect-b="{{ preselect_b or '' }}">
   ```

3. **JS:** no `DOMContentLoaded`, ler os data-attributes. Se presentes e não-vazios, setar o `<select>` correspondente + chamar `loadSide('a', name)` e/ou `loadSide('b', name)` automaticamente. Fluxo normal de uso manual permanece inalterado.

4. **Escopo:** ~20 linhas no total. Backend puro de leitura de args, JS aditivo no onload.

**Justificativa de ID separado:** é pré-requisito trackeável e reusável — além de M9 e M13, pode servir futuras features (ex: link "Propor trade" em cima do McBride na timeline do `/salary_history`).

---

### M10 — Autocomplete de Jogador na Calculadora de Salário
🔲 **Pendente** — Prioridade **Baixa**

**Problema:** A calculadora de salário (`POST /api/salary/calculate`, `routes/salary.py:37-58`) recebe `player_name`, `espn_ref_value`, `contract_year` e `acquisition_type` como input manual. O usuário precisa digitar/copiar esses valores. Se o jogador já existe no banco, esses dados já estão disponíveis.

**Proposta:**
1. **Endpoint de busca:** `GET /api/players/search?q=<nome>` retornando lista de matches (nome, posição, salary, espn_ref_value, contract_year, acquisition_type)
2. **Autocomplete no frontend:** Input de texto com debounce → dropdown de sugestões → ao selecionar, preencher automaticamente ESPN ref value, contract year e acquisition type
3. **Código a reusar:** `player_lookup.py:find_player_by_name()` para matching estrito. `Player.to_dict()` para serialização

---

### M11 — Teste de auto-containment documental
✅ **Concluído (22/04/2026)** — Prioridade **Média**

**Problema:** Parte do estado técnico do projeto pode estar implícito (em memória do Claude, conversas do Claude.ai, cabeça do owner) em vez de estar nos 4 docs + código. Isso viola o princípio de auto-containment definido no `DEV_METHODOLOGY.md`: um colaborador novo, outro Claude sem memória, ou o próprio owner daqui a 2 anos não conseguiria replicar/auditar o projeto usando só a documentação.

**Proposta:** Executar o teste prático definido no `DEV_METHODOLOGY.md` — responder *"o que eu perderia se apagasse a memória agora?"*. Migrar o que faltar para os 4 docs (CLAUDE.md, manager_devplan.md, manager_vision.md, improvements.md).

**Resolvido (22/04/2026):** Auditoria executada. Memória estava limpa de estado técnico do manager (nada a migrar daqui). Identificados 6 gaps nos docs, todos migrados:
- `manager_devplan.md` header atualizado (data 22/04/2026 + status Render como primário, PythonAnywhere como legacy)
- Nova Camada C (Deploy Render C1-C3) promovida do Log para a lista de "Camadas de Desenvolvimento" com sumário
- Log de Decisões recebeu entrada **22/04/2026** (users.csv canônico para produção, comportamento duplo do seed_users.py, M11/M12 adicionados, commit 82e1c29)
- `manager_vision.md` linha 33 atualizada (PythonAnywhere → Render)
- `CLAUDE.md` recebeu nota sobre comportamento duplo do seed_users.py (boot importa app.py → auto-seed CSV primeiro → CLI pode dar "já existe")
- Este item (M11) marcado como ✅ no status rápido e aqui na seção detalhada

---

### M12 — Vincular Owners a Times via Tela de Admin com Lookup do Sleeper
✅ **Concluído (22/04/2026)** — Prioridade **Média**

**Problema:** Hoje vincular um usuário a um time exige que o admin saiba de cor o team_id numérico do dynasty.db e rode o seed_users.py via CLI (local) ou edite `data/users.csv` + push (produção). É frágil: o admin pode errar o ID, novos owners precisam de intervenção manual toda vez, e não há interface visual.

**Resolvido (22/04/2026):** Tela `/admin/users` implementada. Decisões de escopo que divergiram da proposta original (registradas no Log de Decisões do devplan):

1. **Não criada coluna `User.sleeper_user_id`** — `Team.sleeper_owner_id/owner_name/owner_avatar` já existe e é populado pelo Sleeper sync. O lookup Manager↔Sleeper é feito via `User.team_rel.sleeper_owner_id`. Economiza uma migração.
2. **Não chamamos `/league/{id}/users` da Sleeper API na tela** — dados já vêm do sync existente. Botão "Sincronizar com Sleeper" no `/admin` já cobre atualização. Evita chamada duplicada.
3. **Não sincronizamos com `data/users.csv`** — CSV permanece como seed inicial, não source-of-truth. Users criados via UI persistem só no DB (aceitável: Render tem persistent disk, `init_data.py` não sobrescreve DB existente).

**Implementado:**
- Backend: 5 endpoints em `routes/admin.py` — `GET /admin/users` (page, `@login_required`); `GET /api/admin/users` (list teams+users); `POST/PATCH/DELETE /api/admin/users[/<id>]` (todos `@admin_required`)
- Frontend: `templates/admin_users.html` — tabela com 12 linhas (uma por time), avatar Sleeper, inputs de email/nome/admin, ações Vincular/Salvar/Desvincular. Seção "Users sem time vinculado" para órfãos
- Navegação: card "Gerenciar Users" adicionado ao `/admin`

**Validado (22/04/2026):** 7 casos de teste passaram via Flask test_client:
1. GET list → 12 times, 3 vinculados (Erico/5, Rafael/1, Michel/8)
2. POST create → 201 com user id=4
3. PATCH toggle admin + name → 200
4. POST duplicate email → 409 com mensagem clara
5. DELETE → 200
6. GET list após cleanup → volta a 3 vinculados
7. GET /admin/users (page) → 200, template renderiza

**Escopo NÃO incluído:** sincronização bidirecional com `users.csv`, integração com convite OAuth/validação Google, bulk import via UI.

---

### F8 — Reconstruir PlayerHistory a partir da Sleeper API
✅ **Concluído (22/04/2026)** — F8a + F8b + F8c. Prioridade **Alta**

**Problema:** `PlayerHistory` tem informação fictícia para qualquer jogador que trocou de mão entre temporadas. O backfill atual (`_backfill_player_history()` em `routes/admin.py:428-503`) e o `import_csv.py` usam snapshot do CSV + estado atual do `Player` para inventar histórico, sem consultar `/drafts/<id>/picks` nem `/transactions/<week>` do Sleeper, que têm a verdade factual.

**Descoberto em:** 22/04/2026, verificando histórico do A.J. Brown (reconciliação do F7) + 3 outros casos apontados pelo owner.

**4 casos verificados via Sleeper API (evidência concreta):**

**1. Brandon Aiyuk (pid=106, sid=6803)**
- DB atual: `auction_draft` 2024 team=ESPN $8, `rollover` 2025 $8
- Verdade Sleeper:
  - 2024 startup auction r5p53 roster=5 (**Cangaceiros**) **$29**
  - 2025 W1 drop free_agent de roster 5
  - 2025 FA auction r6p62 roster=12 (**ESPN FANTASY LEAGUE**) **$8**
- Gap: salary 2024 errado ($8 em vez de $29), team 2024 errado, falta drop + re-auction. `contract_start_season=2024` devia ser 2025.

**2. Brock Bowers (pid=276, sid=11604)**
- DB atual: `keeper` 2024 team=Trust $21 ❌ (não foi keeper)
- Verdade Sleeper:
  - 2024 startup auction r5p57 roster=5 (**Cangaceiros**) $21
  - 2025 W5 trade roster 5→8 (Cangaceiros→Trust The Process) ✅ (capturado pelo S1 hoje)
- Gap: `acquisition_type=keeper` errado (foi `auction_draft`). Team 2024 errado.
- Nota: user lembra que trade foi pelo McBride + outra peça — verificar no payload da trade.

**3. Buffalo Bills DST (pid=47, sid=BUF)**
- DB atual: `rookie_draft` 2024 team=3 peat $1 ❌ (DST não participa de rookie draft)
- Verdade Sleeper:
  - 2024 startup auction r7p78 roster=7 (AlexTheDawg) $1
  - 2024 W5-W6: múltiplos waivers/free_agent entre rosters 7, 5 (e reinserção em 7)
  - 2025 W1 drop de roster 7
  - 2025 FA auction r3p27 roster=3 (Fazenda) $1
  - 2025 W5-W6: mais rotações (3 peat, mongoloides, Fazenda)
- Gap: `acquisition_type` totalmente errado. History tem só 2 rows lineares quando na verdade houve **7 transações**.

**4. C.J. Stroud (pid=162, sid=9758)**
- DB atual: `rookie_draft` 2024 team=mongoloides $1 ❌
- Verdade Sleeper:
  - 2024 startup auction r2p14 roster=5 (**Cangaceiros**) **$19** (user: "preço alto")
  - 2025 W1 drop Cangaceiros; W2 drop Tropa; W3 free_agent para achane
  - 2025 FA auction r4p47 roster=9 (Tropa) $1
  - 2025 W11 trade achane→mongoloides
- Gap: `acquisition_type=rookie_draft` errado, salary 2024 errado ($1 vs $19 real), team 2024 errado, `contract_start_season=2024` devia ser 2025, falta registrar drop/re-auction/trade.

**Causa raiz:**
- `_backfill_player_history()` usa `p.contract_start_season` + `p.fantasy_team` (estado atual) + `p.acquisition_type` do CSV para inventar events. Quando o player trocou de time entre temporadas, tudo isso diverge da história real.
- `acquisition_type='rookie_draft'` foi atribuído indevidamente a vários jogadores que foram FA-auction ou startup-auction (qualquer player com year-1 salary=$1, aparentemente).
- CSV `dynasty_rosters_clean.csv` tem dados stale: campo `team` é snapshot mid-2025 inconsistente; `contract_year_2025=2` + `orig_draft_season=2024` não distingue "contrato mantido desde 2024" vs "re-auctionado em 2025".

**Consequências:**
- Trade Manager pode calcular cap errado via `contract_start_season`
- Auditoria pública (ex: F1 3 Browns bug, F8 aqui) fica comprometida
- Projeção de VALORIZAÇÃO OK (usa `Player.salary` e `Player.contract_year` atuais que batem com realidade)
- UX do `/salary_history` narra eventos falsos (A.J. Brown foi corrigido no F7 mas os 4+ casos acima ainda mostram história fictícia)

**Proposta:**

**F8a — Rebuild via Sleeper chain:**
1. Walk chain: `current_league → previous_league_id → ... → startup_league`
2. Por liga: coletar `drafts` + `drafts/<id>/picks` + `transactions/<week 0..18>`
3. Reconstruir `PlayerHistory` canonicamente por `sleeper_player_id`:
   - Evento `auction_draft`/`rookie_draft`/`fa_auction` derivado de `draft.type` + rodadas + timing (startup auction = draft com N rodadas igual roster size; rookie draft = linear; FA auction = auction pós-rookie com ~8 rodadas)
   - Eventos `fa_waiver`/`trade`/`drop` de transactions (S1 já resolve trades novas; F8 faz backfill retroativo)
   - `team_name` do evento = time no momento do evento (map via roster_id + `Team.sleeper_owner_id`)
   - `salary` do evento: `metadata.amount` do pick (auction) ou regra do salary_engine (waiver/FA = $1, etc.)
4. Corrigir `Player.contract_start_season` + `Player.acquisition_type` quando divergir

**F8b — Revisar uso do CSV:**
- Manter CSV como fonte inicial só para valores que Sleeper não sabe (salary/contract atuais)
- Parar de derivar histórico do CSV — histórico vem exclusivamente da Sleeper chain
- Avaliar deprecar `dynasty_rosters_clean.csv` após F8a estabilizar

**F8c — Backfill one-time em produção:**
- Endpoint admin `POST /api/admin/player_history/rebuild` (`@admin_required`)
- Idempotente via UNIQUE constraint `(sleeper_player_id, season, event_type, team_name)` ou equivalente
- Padrão similar ao `sync_trades/backfill` do S1

**Escopo estimado:** 2-3 sessões. Similar em complexidade a S1+F7 combinados. Requer leitura pesada das convenções Sleeper (draft types, transaction types, metadata fields).

#### F8a — Core rebuild via Sleeper chain ✅ 22/04/2026

**Implementado:**
- Migration 5 em `_run_migrations()` (app.py): adicionou coluna `sleeper_event_ref` TEXT + backfill das 78 trade rows (S1) e 220 rollover rows + pré-limpeza de duplicatas + `CREATE UNIQUE INDEX uq_player_history_event ON player_history(player_id, season, event_type, team_name, sleeper_event_ref)`.
- Funções novas em `sync_sleeper.py`: `_walk_league_chain`, `_classify_draft`, `_collect_draft_events`, `_collect_transaction_events`, `_snapshot_player_history`, `_rebuild_player_history(dry_run=False)`.
- Modelo `F8PlayerBackup` em `models.py` (tabela auxiliar de rollback com `old_contract_start_season` e `old_acquisition_type` por player).

**Decisões de escopo:**
1. **Quintupleto UNIQUE via `sleeper_event_ref`** em vez de quadrupleto simples. Justificativa: quadrupleto `(player_id, season, event_type, team_name)` colapsa casos reais como BUF DST com múltiplos drops/waivers do mesmo time. `sleeper_event_ref` com formato `'tx:<id>' | 'draft:<id>:<pick>' | 'rollover:<season>'` é auditor-friendly.
2. **Heurística de draft validada contra dados reais:** `type=linear → rookie_draft` (não snake — achado da Fase 2); `type=auction + rounds≥20 + primeira liga da chain → auction_draft (startup)`; demais auction → `fa_auction`. 2025 tem 7 drafts complete (6 fa_auctions + 1 rookie linear), não 1 como assumido inicialmente.
3. **Delete-and-rebuild preservando S1 + rollover:** DELETE apenas rows com `sleeper_event_ref IS NULL` (fictícias do `_backfill_player_history`). Preserva 78 trades do S1 e 220 rollover events do F7.
4. **Trades delegadas 100% ao S1:** `_rebuild_player_history` chama `_sync_trades(league_id)` por liga na chain (idempotente via S1 UNIQUE), garantindo cobertura retroativa. `_collect_transaction_events` explicitamente pula `type=trade`.
5. **Reconciliação de Player.acquisition_type só para eventos >= 2025:** protege year-1 salary rules do `salary_engine.py` para contratos vigentes.
6. **Reconciliação usa Trade.trade_date como timestamp real** para trades preservadas do S1 — sem isso, acquisition_type de players tradados em legs tardias (ex: Stroud leg 11) seria overridden por eventos de leg anterior (ex: free_agent leg 3).

**Resultado do rebuild local:**
- `ligas_visitadas: [2024, 2025, 2026]` (2026 é pre_draft, sem events)
- `events_written: 794` | `deleted_legacy: 320` | `players_corrected: 180`
- Total PlayerHistory pós: 1092 rows (vs 578 antes) — 269 draft + 603 tx (trades + waivers + FA + drops) + 220 rollover preservado.
- Snapshot salvo em `data/.player_history_snapshot_20260422_182651.json`.

**4 casos de validação (todos batem com proposta F8 em improvements.md):**

| Pid | Player | ANTES | DEPOIS |
|-----|--------|-------|--------|
| 106 | Aiyuk | 2 rows, acq=auction_draft, start=2024 | 4 rows (auction $29 Cangaceiros 2024 + drop 2025 + fa_auction $8 ESPN 2025 + rollover preservado), acq=fa_auction, start=2025 |
| 276 | Bowers | 2 rows, acq=keeper, start=2024 | 3 rows (auction $21 Cangaceiros 2024 + rollover preservado + trade 2025 preservada), acq=trade, start=2025 |
| 47  | BUF DST | 2 rows, acq=rookie_draft, start=2024 | 8 rows (auction $1 AlexTheDawg 2024 + drop/add 2024 + drop 2025 + fa_auction $1 Fazenda 2025 + drop + fa_waiver 3peat 2025 + rollover preservado), acq=fa_waiver, start=2025 |
| 162 | Stroud | 3 rows, acq=rookie_draft, start=2024 | 7 rows (auction $19 Cangaceiros 2024 + drop 2025 + fa_auction $1 Tropa 2025 + drop 2025 + free_agent achane 2025 + rollover preservado + trade 2025 preservada), acq=trade, start=2025 |

**Validação regression:**
- `python salary_engine_test.py` → 49 testes passam (zero regressões)
- Player.salary e contract_year atuais dos 4 casos inalterados
- Re-run do rebuild → `events_written=0, events_skipped=794` (idempotência confirmada via UNIQUE)

**Warnings aceitos (30 total):**
- 2 players sem sleeper_player_id (Hollywood Brown pid=279, Cameron Ward pid=280) — skip esperado
- 217 sleeper_player_ids sem match no DB local (sample: 10216, 10218, 10223, etc.) — players dropados antes da criação do Manager, não bloqueantes
- Warnings do S1 (pick de season passada drafada) — esperados

**Arquivos modificados:** `models.py` (PlayerHistory.sleeper_event_ref + UniqueConstraint + F8PlayerBackup), `app.py` (Migration 5 em 5 sub-blocos idempotentes), `sync_sleeper.py` (6 funções novas + helper `_count_players_to_correct`).

#### F8c — Endpoint admin + UI + ajuste do boot ✅ 22/04/2026

**Implementado:**
1. **3 endpoints em `routes/admin.py`**:
   - `POST /api/admin/player_history/rebuild` (`@admin_required`) — chama `_rebuild_player_history(dry_run=False)`. Retorna summary JSON.
   - `POST /api/admin/player_history/rebuild?dry_run=1` — simula sem gravar. Retorna `{events_written, events_skipped, warnings, players_corrected, ligas_visitadas, deleted_legacy, dry_run}`.
   - `POST /api/admin/player_history/restore` (`@admin_required`) — restaura último snapshot JSON em `data/`, reverte `Player.contract_start_season` e `acquisition_type` via `f8_player_backup`, limpa backup e flag. Retorna `{success, restored_rows, players_reverted, snapshot}`.
   - Helpers `_latest_snapshot_path()` e `_snapshot_info()` consultam `data/.player_history_snapshot_*.json` via glob — admin_page passa info para o template.

2. **UI card `Histórico Canônico (F8)` em `templates/admin.html`**:
   - Posicionado antes do card "Trades Históricas (Backfill)" pra agrupar ferramentas de backfill canônico.
   - 3 botões: "Simular (dry-run)" (cinza), "Executar Rebuild" (azul), "Restaurar Snapshot" (vermelho, `disabled` se não há snapshot).
   - Banner verde "Rebuild já foi executado neste DB" quando `AppConfig.f8_rebuilt='true'`.
   - Timestamp do último snapshot exposto em small-text abaixo dos botões quando existe.
   - Confirms em JS: rebuild tem confirm mencionando snapshot automático; restore tem confirm explicando reversão.
   - Resultado inline com contagens e warnings truncados (primeiros 3), seguindo padrão do card S1.

3. **EVENT_LABELS + EVENT_BADGES em `templates/salary_history.html`**: adicionados `drop → Dropado` (badge review), `free_agent → Free Agent (add)` (badge trade), `commissioner → Ajuste do comissário` (badge review). `fa_auction` já existia. Os 3 novos tipos são emitidos por `_collect_transaction_events` do F8a e não tinham label — apareciam crus na tela `/salary_history`.

4. **Skip condicional no boot em `app.py`**: dentro do block `if fresh_import:`, antes de chamar `_backfill_player_history()`, verifica `get_config('f8_rebuilt', 'false')`. Se `'true'`, loga `[boot] F8 rebuild já executado — _backfill_player_history ignorado` e skipa. Função em si não removida — continua disponível como legacy para DBs novos.

**Validação (22/04/2026) via Flask test_client com admin mockado:**
- `POST /rebuild?dry_run=1` → 200, summary correto, DB inalterado (PlayerHistory permanece 1092).
- `POST /rebuild` → 200, snapshot criado em `data/`, flag `f8_rebuilt='true'`, `f8_player_backup` com 182 rows.
- `POST /restore` → 200, 1092 rows restauradas do snapshot, 182 players revertidos (Aiyuk/Bowers/BUF/Stroud voltam aos valores do CSV), flag removida, backup zerado.
- Re-rebuild após restore → 200, 182 players novamente corrigidos, idempotência preservada (events_written=0 se nenhum mudou).
- `GET /admin` → 200, card F8 renderizado, banner de flag ativo, botão restore habilitado.
- `python salary_engine_test.py` → 49/49 passam.

**Observação sobre boot skip:** em DB maduro (sem `fresh_import`), o block inteiro de post-sync não executa, então o guard é no-op. O guard só age em DB novo (primeiro deploy Render, dev do zero) que já rodou F8 manualmente antes — cenário raro mas coberto. DBs novos sem F8 (default Render first boot) executam legacy normalmente.

**Arquivos modificados:** `routes/admin.py` (+~90 linhas: imports, helpers, 2 endpoints, snapshot_info passado para template), `templates/admin.html` (+~35 linhas card + ~95 linhas JS), `templates/salary_history.html` (+3 entradas em cada mapa), `app.py` (+5 linhas skip condicional), `manager_vision.md` (+~40 linhas seção Calendário Operacional da Liga).

#### F8-NOTES — Notas legíveis + trade context na timeline ✅ 22/04/2026

**Problema:** Timeline do `/salary_history` exibia strings cruas como `"auction_draft r6p65 (draft 1107510815168729088)"` e `"Trade sleeper_sync tx=1260798906057375745 (...)"` ilegíveis para owners. Trades sem contexto (contraparte + assets).

**Implementado em `routes/roster.py`:**
- Função `_format_event_display(h, trade_by_tx)`: rótulo PT-BR por event_type.
  - `auction_draft`: `Startup Auction · Rd {R}, Pick {P} · ${salary}`
  - `fa_auction`: `FA Auction · Rd {R}, Pick {P} · ${salary}`
  - `rookie_draft`: `Rookie Draft · Rd {R}, Pick {P}`
  - `fa_waiver`: `Waiver Add`  |  `free_agent`: `Free Agent Add`
  - `drop`: `Dropado por {team_name}`
  - `rollover`: `Valorização (Ano {contract_year})`
  - `trade`: `Trade com {counterparty} · {assets_resumidos}` via join com Trade table pelo `sleeper_transaction_id` extraído do `sleeper_event_ref`.
- Round/pick extraídos via regex `r(\d+)p(\d+)` do campo `notes` atual.
- Counterparty de trade: o lado de `Trade.team_a/team_b` que não bate com `h.team_name`.
- Resumo de assets: parseia `Trade.description` em boundaries `;` e trunca com `…` em ~100 chars.
- Prefetch de Trade rows em 1 query `IN(tx_ids)` por request.
- Payload inclui campo novo `display_notes` sem alterar `notes` cru (debugging preservado).

**Template (`templates/salary_history.html`):**
- `renderEventRow` usa `e.display_notes || e.notes` com fallback.
- Coluna `event-amount` removida — display_notes já carrega a info relevante por event_type (evita ruído `$0 · Ano 0` em drops).

#### F8-GAP — Backfill de trades órfãs (restore side-effect) ✅ 22/04/2026

**Problema:** 18 trades de 2024 existiam em `Trade` table mas sem rows em `PlayerHistory`. Investigação mostrou causa raiz: durante testes do F8c, chamadas a `/api/admin/player_history/restore` apagaram `player_history` restaurando o snapshot, mas mantiveram as `Trade` rows criadas pelo run anterior. Re-runs do `_sync_trades` skipam via idempotência de `Trade.sleeper_transaction_id`, então os events nunca foram recriados.

**Implementado em `sync_sleeper.py`:**
- Função `_backfill_missing_trade_history()`: query para Trade rows sem PlayerHistory correspondente, walking da Sleeper chain para resolver qual liga/leg cada tx pertence, criação de rows com `season` real (da liga), idempotente via UNIQUE. NÃO atualiza `Player.team_id/fantasy_team/via_trade` (backfill retroativo só cria rastro histórico).

**Endpoint + UI:**
- `POST /api/admin/player_history/backfill_trades` em `routes/admin.py` (`@admin_required`).
- Botão "🔗 Backfill de Trades Órfãs" no card F8 do `/admin`, entre Rebuild e Restore.

**Validado em dev (22/04/2026):** 18 trades processadas, 40 PlayerHistory events criados. Distinct `tx:` refs em player_history: 29 → 45 (2 tx sobraram órfãs por terem só assets de jogadores já dropados do DB — trades tx=1154533231048630272 e tx=1152430188438040576, esperadas). Casos testados: Tank Dell (agora mostra trade 2024 Pitbull→Cangaceiros), Chase Brown, Ladd McConkey, Chuba Hubbard, D'Andre Swift — todos com timeline completa pós-backfill.

#### F8b — Guard em import_csv.py (AppConfig.f8_rebuilt) ✅ 22/04/2026

**Problema resolvido:** `run_import()` rodava a cada boot e fazia upsert de `acquisition_type` + `contract_start_season` a partir do CSV, revertendo as 180 correções do F8a no próximo boot.

**Implementado:**
1. `_rebuild_player_history(dry_run=False)` em `sync_sleeper.py` agora chama `set_config('f8_rebuilt', 'true')` no fim do path bem-sucedido.
2. `run_import()` em `import_csv.py` lê `get_config('f8_rebuilt', 'false')` no início. Se `true`, log "F8b guard active — skipping acquisition_type and contract_start_season on existing players" e pula essas duas atribuições no update path. Todos os outros campos (salary, contract_year, espn, position, etc.) continuam normais.

**Decisões de escopo:**
- **AppConfig em vez de coluna nova em Player:** flag é estado global do DB ("rebuild já rodou neste banco"), não metadata per-player. `AppConfig` já existe (key/value pattern) e `get_config`/`set_config` são a API canônica — zero schema change.
- **Guard só no update path, não no create path:** player novo adicionado ao CSV pós-F8 (ex: rookie adicionado mid-season) precisa dos valores iniciais do CSV. F8 re-run depois reconcilia se necessário via Sleeper chain.
- **Guard inativo em DB sem a flag:** comportamento original preservado para DBs novos (flag ausente → `false` default → nenhuma proteção). Importante para primeiro deploy em Render quando DB novo é criado.

**Validado (22/04/2026) em 3 cenários:**
1. **Flag setada pelo rebuild:** `_rebuild_player_history(dry_run=False)` → `AppConfig.f8_rebuilt == 'true'` ✓
2. **Reboot preserva correções F8a:** re-importa Flask app com flag ativa → `run_import()` skipa os 2 campos → 4 casos permanecem corrigidos (Aiyuk/Bowers/BUF/Stroud com `acq` e `css` do F8a) ✓
3. **DB sem flag reverte:** deletar AppConfig row + chamar `run_import()` → CSV sobrescreve os 2 campos (Aiyuk volta a `auction_draft 2024`, Bowers a `keeper 2024`, etc.) — comportamento original preservado ✓

**Arquivos modificados:** `sync_sleeper.py` (+2 linhas: `from models import set_config; set_config("f8_rebuilt", "true")` no fim de `_rebuild_player_history`), `import_csv.py` (+4 linhas: import `get_config`, leitura da flag, log condicional, `if not f8_rebuilt` wrap nas duas atribuições).

---

### F6 — Remover "keeper" como acquisition_type
✅ **Concluído (22/04/2026)** — Prioridade **Média**

**Problema:** "keeper" era uma decisão de manutenção (owner retém antes do FA auction), não origem de aquisição. `salary_engine.py` já tratava `keeper` como sinônimo de `auction_draft` via `_AUCTION_TYPES = {"auction_draft", "keeper"}` — distinção era puro ruído semântico.

**Estado pré-F6** (após F8a):
- 60 players com `acquisition_type='keeper'` (era 101 pré-F8; F8a reconciliou 41 cuja última aquisição ativa era ≥ 2025).
- 0 rows em `PlayerHistory` com `event_type='keeper'` (F8 já havia substituído).
- 100 rows no CSV com `keeper`.

**Implementado (22/04/2026):**
1. **Migration 6 em `app.py`** (`_run_migrations`): `UPDATE players SET acquisition_type='auction_draft' WHERE acquisition_type='keeper'`. Guard por `SELECT COUNT`, idempotente. Aplicou 60 rows.
2. **`salary_engine.py`:** `_AUCTION_TYPES = {"auction_draft"}` (removido `"keeper"`). Docstring Year 1 atualizada.
3. **`import_csv.py:33`:** mapping `"keeper" → "auction_draft"` (defesa para CSVs legacy em DBs novos).
4. **`routes/admin.py:707`** (legacy `_backfill_player_history`): removido `"keeper"` da tupla `origin_event`.
5. **`salary_engine_test.py`:** `test_keeper_uses_value_paid` removido (redundante com `test_auction_draft_uses_value_paid`); `test_saquon_projection` passou a usar `"auction_draft"` em vez de `"keeper"`.
6. **`templates/salary.html`:** `<option value="keeper">Keeper</option>` substituído por `<option value="fa_auction">FA Auction</option>` (mais semanticamente correto).
7. **`data/dynasty_rosters_clean.csv`:** 100 rows `keeper` → `auction_draft`. Total auction_draft no CSV: 33 → 133.

**Não alterado:** `keeper_salaries` e `num_keepers` em `draft_budget()` (salary_engine.py:215-216) — são nomes descritivos do resultado (players ativos no roster pré-FA auction), não se referem a `acquisition_type`. Semanticamente corretos.

**Validação (22/04/2026):**
- `python salary_engine_test.py` → 48/48 (era 49, 1 redundante removido).
- Contagens: keeper=0, auction_draft=61 (era 1 + 60 migrados).
- Cap per team idêntico pré/pós Migration 6 — salary_engine já tratava ambos igualmente.
- Re-boot: Migration 6 skipa (idempotência confirmada).

---

### F8-RESTORE-GAP — Restore chama backfill_trades automaticamente
✅ **Concluído (22/04/2026)** — Prioridade **Baixa**

**Problema:** O endpoint `POST /api/admin/player_history/restore` (F8c) apaga `PlayerHistory` restaurando do snapshot JSON, mas **mantém** Trade rows criadas após o snapshot. Re-runs de `_sync_trades` skipam via idempotência de `Trade.sleeper_transaction_id`, deixando gap: trades existem em `Trade` table mas sem rows em `PlayerHistory`.

**Implementado:**
1. `player_history_restore()` em `routes/admin.py` chama `_backfill_missing_trade_history()` automaticamente após os passos 1-3 (restore rows + revert Player + clear backup/flag). Nova seção `4.` com try/except isolado — falha no backfill NÃO reverte o restore (que já foi aplicado), apenas reporta `backfill_error` no payload.
2. JSON de retorno ganha campos `backfill_result` (com `processed`, `events_created`, `warnings`) e `backfill_error` (quando falha).
3. UI (`templates/admin.html`, função `f8Restore`) exibe o resultado do backfill integrado na mensagem de sucesso. Confirm do botão atualizado mencionando que o backfill é automático. Classe `result-warn` aplicada quando backfill falha (restore bem-sucedido mas sem recuperação total).

**Validação (22/04/2026):**
- Test cenário "snapshot stale": deletei 40 events de trade 2024 manualmente, chamei `_backfill_missing_trade_history()` → processou 18 trades, criou 40 events, state completo (78 → 118 trade events).
- Test fluxo real: `POST /rebuild` → `POST /restore` → payload inclui `backfill_result` com contagens. Tank Dell (1 trade) e D'Andre Swift (3 trades) preservam events na timeline sem intervenção manual.

**Observação:** botão "🔗 Backfill de Trades Órfãs" continua existindo como fallback manual (caso algum cenário externo crie Trade rows sem events — ex: import de dados, manipulação direta do DB). Operação inofensiva via idempotência UNIQUE.

---

### O1 — Linkificar Nomes de Jogadores em Todas as Telas
✅ **Concluído (23/04/2026)** — Prioridade **Média**

**Problema:** A página de jogador (`GET /player/<player_id>`, M13) existia mas só era acessível via ícone `🔗` no roster e salary_history. Cap projector, admin tools e demais listers tinham nomes como texto puro.

**Implementado em 3 lotes:**

1. **Macros centralizados:**
   - `templates/_macros.html` (NOVO) — macro Jinja `player_name_link(player, klass, target, stop_propagation)`.
   - `templates/base.html` — helper JS `renderPlayerNameLink(p, opts)` para JS template strings, com escape HTML interno.

2. **Lote 1 — telas com payload pronto:**
   - `cap_projector.html`, `admin.html` (rollover preview + review_players), `trade_proposal.html` (assets in/out) — usando o helper/macro novo.

3. **Lote 2 — roster (decisão A):**
   - `roster.html` — nome do jogador agora vai direto para `/player/<id>` (era modal inline `showPlayerHistory`). Ícone 🔗 separado removido.
   - `base.html` — modal `#player-modal` + funções `showPlayerHistory` e `closePlayerModal` removidos (órfãos após Lote 2). CSS `.timeline*` preservado (usado por `player_detail.html`).

4. **Lote 3 — modal de trade (`_trade_detail_modal.html`):**
   - `routes/trades.py:trade_by_tx` — best-effort `find_player_by_name(asset)` adiciona `player_id` (nullable) por asset. Picks e nomes ambíguos ficam null (degradação elegante).
   - `_trade_detail_modal.html` — usa `renderPlayerNameLink` quando `player_id` existe; fallback para `escapeHtml(asset)` caso contrário.

**Validação (23/04/2026, via Flask test_client):**
- `salary_engine_test.py`: 48/48.
- `/cap_projector` renderiza, helper presente.
- `/?team=...` (roster): sem `showPlayerHistory`, sem `player-external-link` (🔗), com `href="/player/"`.
- `/api/trades/by_tx/<tx>`: matches reais — Kaleb Johnson→55, David Montgomery→235, Justin Jefferson→38. Picks corretamente null.
- Cobertura observada em 3 trades reais: 60%, 25%, 100% (gap = picks, esperado).

**Não retrofitados** (regra do prompt): `trades.html` e `salary_history.html` — já tinham links corretos via M13/M14, mexer abriria risco sem ganho.

---

### O2 — Enriquecer Página do Jogador: Stats Históricas + ADP
🔲 **Pendente** — Prioridade **Média**

**Problema:** A página atual (`player_detail.html`, M13) mostra contrato, salary history e botão "Propor Trade". Falta contexto de valor de campo: pontuações históricas por temporada e posição no ranking/ADP.

**Objetivo:**
- **Stats históricas:** buscar da Sleeper API (`/stats/nfl/player/<sleeper_player_id>?season_type=regular&season=<year>`) — pontos totais e média por semana por temporada disponível.
- **ECR/ADP:** usar `adp` e `search_rank` já presentes no Sleeper players cache (`.sleeper_players_cache.json`) — zero request extra. Para ranking ESPN, usar ESPN ref value (`espn_ref_value`) já no banco como proxy de tier.
- **Schedule próximo (consolidado de UX4):** próximas semanas via Sleeper schedule (avaliar fonte exata — `/v1/state/nfl` + matchups por week, ou cache externo).
- Apresentar de forma compacta, sem sobrecarregar a página. Referência: FantasyPros (abas Overview, Statistics, Schedule).

**Nota:** item UX4 da rodada de 23/04/2026 foi consolidado aqui em vez de duplicado — escopo virtualmente idêntico (mesma API Sleeper, mesma página alvo).

---

### L1 — League Hub: Visão Geral da Liga + Detalhe por Time
✅ **Concluído (23/04/2026)** — Prioridade **Alta**

**Implementado em novo blueprint `routes/league.py`:**

1. **`GET /league`** (`@login_required`) — grid de 12 cards, ordenado por rank da temporada (campeão primeiro). Cada card: avatar (Sleeper CDN thumb), nome, owner, badge 🏆/🥈, record W-L, cap restante (vermelho se negativo), nº de picks, dynasty total. Card do time do usuário logado destacado com border accent (`league-card-mine`). 5 queries totais, sem N+1: teams, standings, pick_counts (group_by), players (filtrados in-memory por team_id), `get_dynasty_values()` (cache JSON). Helper puro `_build_team_card(team, standing, pick_count, players, dv_map)`.

2. **`GET /team/<int:team_id>`** (`@login_required`, 404 via `db.get_or_404`) — detalhe com 3 seções server-rendered (sem tabs):
   - **Cap Breakdown:** cap usado/restante/total, IR (count + cap), dynasty total, salário comprometido por posição.
   - **Roster:** agrupado por posição via `_build_players_by_pos` (importado de `routes/roster.py`), nomes via macro O1 `player_name_link`.
   - **Picks:** agrupados por season+round (3 anos × 3 rounds = 9 cells por time). Indica quando origem != time atual (via trade).
   - Header: avatar full-size, nome, owner, record da temporada, rank, badges 🏆/🥈. Botão "⇄ Propor Trade" → `/trades?team_a=<my>&team_b=<other>` (M14 por nome). Não exibido para o próprio time do usuário logado.

3. **CSS novo** em `static/style.css`: `.league-grid` (auto-fill 280px), `.league-card`, `.league-card-mine`, `.league-card-avatar/titles/stats`, `.league-stat`, `.cap-negative`, `.team-detail-header/avatar/titles/section`, `.section-title`, `.cap-breakdown-grid/stat`, `.cap-by-pos-table`, `.pos-block`, `.picks-season-block`. Reusa variáveis `--bg2/3`, `--border/border2`, `--accent`, `--text-dim`.

4. **Decisões:**
   - `dynasty_total` só de **players** (T2-FIX aberto para picks Rd2+).
   - `_build_players_by_pos` importado com underscore de `routes/roster` (35 linhas; alternativa de duplicar foi rejeitada).
   - `team.cap_remaining()` evitado no loop dos cards (relationship `lazy="dynamic"` causaria N+1) — cap pré-computado no Python.
   - Sem tabs JS — página densa server-rendered, alinha com `player_detail.html`.
   - `resolve_asset_value(values_map, sid)` reusado de `dynasty_values.py` (não fazer lookup inline; entries são dicts `{value, name, position, ...}`, não ints).

**Validação (23/04/2026, Flask test_client):**
- `GET /league` → 200, 12 cards, badge 🏆 (Pitbull do Samba campeão), `cap-negative` (Pitbull -$2), `league-card-mine` no Cangaceiros.
- `GET /team/5` (meu time Cangaceiros) → 200, sem botão "Propor Trade".
- `GET /team/1` (adversário) → 200, com "Propor Trade", links `/player/<id>` via macro O1.
- `GET /team/999` → 404.
- `salary_engine_test.py`: 48/48.

---

### L2 — League Hub Season Mode: Matchups, Schedule, Standings
🔲 **Pendente** — Prioridade **Baixa**

**Problema:** Durante a temporada, a visão de liga precisa incluir resultados semanais, schedule e standings — dados que o Manager ainda não consome.

**Objetivo:**
- Sync de matchups via Sleeper API (`/league/<id>/matchups/<week>`).
- Na vista `/league`: adicionar coluna de record e pontos totais.
- Na vista `/team/<id>`: adicionar aba "Temporada" com schedule semanal e pontuações.
- **Pré-requisito:** L1 concluído. Implementar quando a temporada 2026 começar.

---

### N1 — Redesign Navbar
✅ **Concluído (23/04/2026)** — Prioridade **Média**

**Implementado em 2 lotes:**

1. **Context processor + macros (Lote 1):**
   - `app.py` — `inject_nav_teams` com query leve (`with_entities` em id, name, owner_name, owner_avatar, is_my_team) ordenada por nome. Só executa se autenticado; retorna `[]` em `/login`. Coexiste com `inject_global_state` existente.
   - `templates/_macros.html` — macros `nav_link(url, label, prefixes=None, exact=False)` e `nav_dropdown(label, items, active_prefixes)`. Helper interno `_nav_match` com algoritmo path-aware: `path == prefix` OR `path.startswith(prefix.rstrip('/') + '/')`. Robusto contra falsos matches (`/salary` não bate `/salary_history`).

2. **Navbar redesenhada (Lote 2):**
   - **Esquerda:** logo `🏈 Dynasty SB`.
   - **Centro:** Meu Roster | Liga ▾ | Ferramentas ▾ | Trades | Times ▾ | Admin ▾
     - **Liga ▾**: Visão Geral (`/league`), Picks (`/picks`), Histórico (`/salary_history`).
     - **Ferramentas ▾**: Calculadora (`/salary` exact), Cap Projector (`/cap_projector`).
     - **Times ▾**: dropdown com 12 times (g_nav_teams), cada item com avatar Sleeper thumb + nome + owner + tag EU se my_team. Linka para `/team/<id>`.
     - **Admin ▾** (só `current_user.is_admin`): Painel (`/admin` exact), Usuários (`/admin/users`), Offseason (`/offseason`), Auction (`/auction`).
   - **Direita:** hamburger ☰ (mobile only), cap-chip (preservado), botão Sync (preservado), avatar+dropdown do owner com Logout. Avatar com cascata 4-step: hash Sleeper → fallback inicial owner_name → inicial user.name → 👤.
   - Liga + Times **ambos ativos** em `/team/<id>` por design (comunica navegação contextual).

3. **Mobile (< 768px):** links centrais escondidos. Hamburger ☰ aparece. Toggle CSS-only via checkbox hack (`<input type="checkbox" id="nav-mobile-state">` + `<label>` no botão). Overlay vertical com painel lateral direito (320px max), agrupado por seção (Navegação, Times, Admin, Conta). Click no fundo escuro fecha (label aponta pro mesmo checkbox).

4. **CSS** em `static/style.css`: `.nav-item`, `.nav-group`, `.nav-group-label`, `.nav-dropdown`, `.nav-dropdown-item`, `.nav-dropdown-header`, `.nav-dropdown-teams`, `.nav-team-item/avatar/text/name/owner`, `.nav-user-menu/button/avatar`, `.nav-avatar-fallback`, `.nav-mobile-toggle/state/overlay/overlay-bg/panel/section-title/item`. Reusa variáveis existentes (`--bg2/3`, `--border`, `--accent`, `--text-dim`).

**Validação (23/04/2026, Flask test_client):**
- Navbar completa em `/`: 12 itens nav-team-item, hamburger, mobile overlay, user menu, cap-chip, Sync.
- Match path-aware: `/league` → Liga ON; `/team/1` → Liga + Times ON; `/salary` → Ferramentas ON; `/salary_history` → Liga ON, Ferramentas OFF; `/cap_projector` → Ferramentas ON, Liga OFF.
- `/login` (anon): `g_nav_teams=[]`, sem dropdown de Times.
- `salary_engine_test.py`: 48/48.

**Bug pego no smoke test:** algoritmo inicial `path.startswith(prefix + '/')` falhava quando prefix já terminava em `/` (ex: `/team/`) — gerava `'/team//'`. Corrigido com `prefix.rstrip('/')` antes de concatenar.

---

### C1 — Cap Projector: Modo "Drop Programado"
🔲 **Pendente** — Prioridade **Média**

**Problema:** O cap projector simula o roster atual. Não há como avaliar o impacto de cortar jogadores ou liberar cap para uma trade sem alterar dados reais.

**Objetivo:** Adicionar no cap projector a possibilidade de marcar jogadores como "drop temporário" — apenas na sessão de simulação, sem alterar o banco. O cap projetado recalcula em tempo real excluindo os jogadores marcados. Útil para:
- Planejar cortes de offseason
- Avaliar se há cap suficiente para receber um jogador numa trade
- Simular cenários antes de propor uma troca

Não persiste nenhuma alteração no banco — é simulação pura, análoga ao que o simulador de trades já faz.

---

### M8-PERM — Lottery: Simulação aberta a owners + bloqueio pós-oficial
✅ **Concluído (23/04/2026)** — Prioridade **Média**

**Problema:** Pós-M8, `/lottery/simulate` ficou com `@admin_required` (owners não podiam testar cenários de bolinhas). Adicionalmente não havia guarda server-side bloqueando simulação após o sorteio oficial — só a guarda visual no template via `has_canonical_audit`.

**Implementado:**
1. `routes/offseason.py:354` — decorator de `lottery_simulate` trocado de `@admin_required` para `@login_required`.
2. `routes/offseason.py` — guarda no topo de `lottery_simulate`: se existir `LotteryAudit` com `is_canonical=True` para `current_season+1`, retorna 409 com mensagem "Sorteio oficial da temporada {N} já realizado. Simulação indisponível até a próxima temporada." Espelha padrão de `run_lottery` (linha 326-332).
3. Template **não alterado** — `has_canonical_audit` já controla a substituição do botão `#btn-sortear` (linhas 201-212) por Travar / Re-executar / Ver auditoria. Reativação automática no rollover (current_season avança → query não acha audit → simulação reabre).

**Validação:**
- Owner (não-admin) sem audit → simulação roda.
- Audit canônico forçado → 409 no curl + botão desaparece no template (replaced).
- `/lottery/replace` segue exigindo admin.
- Após rollover, simulação reabre automaticamente.

---

### T2-FIX — Picks Rd2+ sem dynasty value no preview/proposta de trade
✅ **Concluído (24/04/2026)** — Prioridade **Média**

**Helper Python** corrigido em 23/04 (commit `55bfb16`). **Réplica JS** eliminada em 24/04 via T2-FIX-2 (fix estrutural — `/api/picks` passou a pré-resolver `dynasty_value` no backend, JS virou lookup direto por `pick.dynasty_value`). Não existe mais lógica de construção de chave `DP_*`/`FP_*` no frontend.

---



**Causa raiz (diagnose MAN-T2-FIX-F1):** Bug duplo em `pick_sleeper_id` (`dynasty_values.py`). O helper gerava `DP_<year_offset>_<pick_index_global>` mas o FantasyCalc usa **dois formatos**:
- `DP_<round-1>_<pick_in_round-1>` — picks específicas do draft próximo (2026)
- `FP_<year>_<round>` — agregados por ano+round (2026, 2027, 2028)

Eixo X estava errado (year_offset em vez de round-1) e eixo Y também (índice global cross-round em vez de within-round 0-11). Resultado: Rd1 retornava `DP_1_5` (=valor de uma Rd2, 1319) — bug latente exibindo dado errado. Rd2+ retornava índice fora de range (Y > 11) → None → 🪙 vazio (sintoma reportado).

**Implementado:** `pick_sleeper_id` reescrito com lookup em 3 camadas:
1. **Tier 1 (DP):** se `pick.season == ano_DP` E `projected_pick > 0`: tenta `DP_<round-1>_<projected_pick-1>`. Hoje **dead code path** (Pick model não tem coluna `projected_pick`, 0/108 picks têm o atributo) — implementado para uso futuro caso algum caller popule dinamicamente.
2. **Tier 2 (FP):** tenta `FP_<season>_<round>`. **Caminho vivo** para 100% das picks atuais.
3. **Tier 3:** None se nenhuma key existe no cache.

Helper auxiliar `_detect_dp_year(values_map)` escaneia entries `DP_0_*` e parseia o ano do `name` ("2026 Pick 1.04" → 2026) — detecção dinâmica, sem hardcode. Quando o cache atualizar para 2027 no off-season, o ano avança automaticamente.

Signature ganhou parâmetro opcional `values_map=None` para evitar I/O extra quando o caller já carregou o map (caso de `routes/trades.py`). Backwards-compatible.

**Mudança visível:** picks Rd1 sem projection saltam de 1319 (DP_1_5 errado, valor Rd2) para 2695 (FP_2026_1 correto, valor Rd1 agregado). Não é regressão — é a correção do bug latente.

**Validação (23/04/2026, 11 cenários):**
- 2026 Rd1/2/3/4 sem projection → FP_2026_1/2/3/4 (2695, 1291, 849, 632).
- 2027 Rd1/2 → FP_2027_1/2 (2939, 1488). 2028 Rd2 → FP_2028_2 (1283).
- Tier 1 com mock projected_pick=4 → DP_0_3 (3272). projected_pick=6 Rd2 → DP_1_5 (1319).
- season=2099 (não no cache) → None. season=2024 (passado) → None.
- `_detect_dp_year(cache atual)` → 2026.
- `salary_engine_test.py`: 48/48.

**Não alterado:** estrutura do cache JSON, URL fetch, signature de `get_dynasty_values()`, `resolve_asset_value()`, `routes/trades.py`, templates.

---

### T2-FIX-2 — Réplica JS pickFcSid Espelhar Lógica 3-Tier do Python
✅ **Concluído (24/04/2026)** — Prioridade **Alta**

**Problema original:** helper Python `pick_sleeper_id` (corrigido no T2-FIX, commit `55bfb16`) tinha uma réplica em JS (`pickFcSid` em `templates/trades.html:170-179`) com **bug ainda pior** — não só 3-tier errado, mas fórmula de índice linear `(round-1)*ROSTER_SIZE + (pp-1)` que gerava `DP_0_14` em vez do formato `DP_<round-1>_<pp-1>`. Sintoma em prod: picks Rd2+ mostravam 🪙— vazias, Rd1 mostrava valor de Rd2.

**Decisão: fix estrutural (opção D), não as 3 opções tácticas da diagnose F2.** As tácticas (a/b/c) mantinham a lógica replicada entre Python e JS — anti-padrão que as 4 regras novas do `DEV_METHODOLOGY.md` (sessão 23/04) existem exatamente para prevenir. Resolver certo nesta primeira oportunidade pós-regras.

**Implementado:**

**Backend (`routes/picks.py`):** endpoint `GET /api/picks` passa a carregar `dynasty_values` uma vez por request e chamar `pick_sleeper_id` + `resolve_asset_value` para cada pick. Payload ganha campo novo `dynasty_value: int | None`. Zero cópia de lógica — reusa o helper Python fixado no T2-FIX.

**Frontend (`templates/trades.html`):** função `pickFcSid` removida inteira (10 linhas). Variáveis órfãs `currentSeasonInt` e `DYNASTY_ROSTER_SIZE` também removidas. Os 2 call sites (`loadSide` e `computeSideDynastyTotal`) passam a ler `pick.dynasty_value` direto do payload. `dynastyMap` e o fetch `/api/dynasty_values` ficam só para jogadores (mapeados por `sleeper_player_id`).

**Não alterado:** `dynasty_values.py` (já correto), `/trades/proposta/<uuid>` (já era server-side via `_pick_asset_dict`), `/api/dynasty_values` (continua servindo players para o dynastyMap).

**Validação (24/04/2026):**
- `salary_engine_test.py`: 48/48.
- Teste manual de `pick_sleeper_id` em 4 casos — sids 100% corretos (`FP_2026_1`, `FP_2026_2`, `DP_0_3`, `None`). Valores absolutos têm drift pequeno vs. handoff do dia anterior (FantasyCalc atualiza continuamente) — 2571/1282/3264 hoje vs. 2695/1291/3272 em 23/04.
- Smoke `GET /api/picks?team=<name>` via test_client: HTTP 200, 9 picks, 100% com campo `dynasty_value` populado. Tier 1 (DP com `projected_pick`) e Tier 2 (FP agregado) ambos resolvendo.
- Grep de auditoria: `pickFcSid`, `DP_[0-9]`, `FP_[0-9]` em `templates/` e `static/` → **0 matches**. Réplica eliminada, regra das 4 regras do DEV_METHODOLOGY auditada.

**Impacto:** picks de qualquer round em `/trades` renderizam valor dynasty correto. Barra dynasty em tempo real calcula totais corretos. Primeiro fix estrutural pós-adoção das 4 regras — precedente de "resolver réplica, não ensinar JS a fazer a mesma conta".

---

### IR-CLEANUP — Remover Seletor Manual de IR no Roster
🔲 **Pendente** — Prioridade **Baixa**

**Problema:** O roster tem um toggle de IR manual (`@admin_required`) que não tem efeito persistente. O sync do Sleeper (`sync_sleeper.py:257`) sobrescreve `Player.is_on_ir` a cada execução de forma autoritativa, lendo o array `reserve` de cada roster da API. Toggle local cria falsa sensação de controle: admin clica, estado muda na UI, próximo sync (boot ou manual) reverte silenciosamente. Confirmado em diagnose MAN-IR-F1: 16 players IR localmente, todos com `sleeper_player_id`, todos provavelmente vindos do `reserve` Sleeper.

**O que remover:**
- Endpoint `POST /api/player/<player_id>/ir` em `routes/roster.py:119-135` (função `toggle_ir`).
- Handler JS `toggleIR(playerId, toIR)` em `templates/roster.html` (busca em `/api/player/<id>/ir`).
- Toggle visual na UI (botão/checkbox que dispara `toggleIR`).

**O que preservar:**
- Campo `Player.is_on_ir` (sync continua escrevendo, modelo intacto).
- Lógica de cap que exclui IR: `models.py:97-99` (`Team.total_active_salary`), `routes/roster.py:70-75` (cap projetado), `routes/admin.py:77-78` (rollover preview).
- Constante `MAX_IR` (informativa — sync respeita o limite via Sleeper).
- Badge `🏥 IR` no roster (visual, lê `p.is_on_ir`, sem alterar nada).

**Pré-condição:** nenhuma — sync já cobre 100% dos casos para players ativos da liga (todos têm `sleeper_player_id` e estão em algum roster Sleeper).

**Validação esperada:** após remoção, 16 players IR continuam IR; sync mantém o número alinhado com Sleeper; cap projector continua ignorando IR no total.

**Caveat de UX:** se quiser preservar capacidade de override em ambiente sem Sleeper (offline ou API fora), avaliar alternativa conservadora — manter o seletor mas adicionar tooltip "Será sobrescrito no próximo sync". Recomendação default é remover (regra do projeto: ações na UI devem ser efetivas ou marcadas claramente como simulação).

---

### UX1 — Redesign Tabela de Roster em /team/<id>
✅ **Concluído (24/04/2026)** — Prioridade **Média**

**Escolha de escopo:** Cenário C da diagnose F1 — UX1 + UX3 (3 telas com foto). UX2 (propagação PT-BR pra outras telas) permanece isolado no backlog por ter decisão arquitetural própria (como expor `_ACQ_LABELS` pra JS).

**Implementado:**

**Backend (`routes/league.py`):** handler `team_detail` passou a enriquecer cada `Player` com `p.dynasty_value` (via `resolve_asset_value` canônico) e `p.acquisition_label` (via `_ACQ_LABELS` importado de `routes.roster`). `dynasty_total` agregado agora consome `p.dynasty_value` em vez de chamar `resolve_asset_value` de novo (evita double call). Padrão arquitetural: mesmo de T2-FIX-2 para picks — backend resolve, template consome pronto.

**Template (`team_detail.html`):** tabela de roster ganhou 2 colunas (foto + dynasty inline), total 7 colunas. `acquisition_label` substitui `acquisition_type` cru (PT-BR via `_ACQ_LABELS` sem tocar o mapa). Macro `player_photo` importado de `_macros.html` usa variante `.player-photo-sm`.

**Macro nova (`_macros.html`):** `player_photo(player, klass='')` extrai o padrão inline do `player_detail.html` (M13). Fallback `onerror` preservado. Import atualizado no cabeçalho do arquivo.

**Helper JS (`base.html`):** `renderPlayerPhoto(p, klass)` como contraparte client-side, mesmo padrão do O1 (`player_name_link` + `renderPlayerNameLink`). Usado em `cap_projector.html` que renderiza em JS template literals. Mesma URL intencionalmente — single source por modo de render.

**Propagação (UX3):**
- `player_detail.html` — inline substituído por `{{ player_photo(player) }}`.
- `roster.html` — foto pequena adicionada antes da `pos-badge`. Acquisition continua cru (escopo UX2 preservado).
- `cap_projector.html` — foto pequena prepended ao `player-name-cell` JS. Acquisition continua cru.

**CSS (`static/style.css`):** `.player-photo-sm` (32px, border 1px) + `.team-roster-table .col-photo` (44px width) + `.dynasty-value-inline` (tabular-nums). Base `.player-photo` (96px do M13) intocado.

**Validação:**
- `salary_engine_test.py`: 48/48.
- Smoke `GET /team/<id>` via test_client: HTTP 200, `col-photo` + `dynasty-value-inline` + acquisition PT-BR + img Sleeper CDN presentes.
- Backend test: `sum(p.dynasty_value or 0 for p in active)` == `summary.dynasty_total` (bateu em 57514 no time testado).
- Amostra: "Javonte Williams dv=3089 acq=auction_draft→Startup Auction", "Jared Goff acq=unknown→Origem não registrada". Caminho `_ACQ_LABELS` funcional.
- Smoke `GET /`, `/cap_projector`, `/player/<id>`: todos HTTP 200, macro/helper resolvendo corretamente.
- Grep `sleepercdn.com/content/nfl/players/thumb` em `templates/` + `static/`: 2 matches (macro + helper JS), 0 inlines remanescentes. Convenção O1 (1 source por modo de render) seguida.

**Escopo UX2 preservado:** `roster.html:120` e `cap_projector.html:121` continuam renderizando `acquisition_type` cru — mapeamento PT-BR fica para camada UX2 dedicada.

---

### UX2 — Acquisition Types PT-BR em Todas as Telas
🔲 **Pendente** — Prioridade **Baixa**

**Problema:** Valores enum como `auction_draft`, `free_agent`, `fa_waiver`, `fa_auction`, `rookie_draft`, `unknown` aparecem em inglês cru em `team_detail.html`, `roster.html` (badge inline), `salary_history.html` (timeline). Termos técnicos do schema vazando para a UI.

**Objetivo:** mapa de tradução PT-BR centralizado, aplicado consistentemente:

| acquisition_type | Label PT-BR |
|------------------|-------------|
| auction_draft | Auction |
| rookie_draft | Rookie Draft |
| fa_waiver | Waiver |
| fa_auction | FA Auction |
| free_agent | Free Agent |
| unknown | — |

**Implementação proposta:**
- Macro Jinja `acquisition_label(acq_type)` em `templates/_macros.html` para contextos server-side.
- Helper JS `acquisitionLabel(t)` em `base.html` (junto com `renderPlayerNameLink`) para JS template strings.
- Aplicar em: `team_detail.html`, `roster.html` (badge inline), `salary_history.html`, `cap_projector.html`, `admin.html` (review_players).

**Pré-requisito:** nenhum.

---

### UX3 — Fotos de Jogadores em Telas Densas
✅ **Concluído (24/04/2026)** — Prioridade **Baixa**

**Entregue em 2 camadas:**
- **UX1 (cenário C, commit `dbfb76e`):** 3 telas — `team_detail.html`, `roster.html` (`/`), `cap_projector.html`. Macro Jinja `player_photo` + helper JS `renderPlayerPhoto` criados como infra reusável.
- **UX3-b (camada dedicada):** 3 telas remanescentes — `trade_proposal.html` (SSR), `trades.html` (CSR Trade Manager), `salary_history.html` (CSR card por player).

**UX3-b — detalhes:**
- Backend: `routes/salary.py` (`/api/salary_history`) passou a incluir `sleeper_player_id` no dict de cada record — era o único bloqueio identificado na diagnose F1.
- Zero helper/macro novo. Reuso total da infra UX1.
- Zero CSS novo. Tamanho único `player-photo-sm` (32px) em todas as 6 telas — decisão explícita por padronização > granularidade por contexto (se algum mobile ficar apertado no Trade Manager, ajuste vira `@media` pontual).
- Grep da URL Sleeper CDN em `templates/` + `static/`: 2 matches (macro + JS helper), 0 inlines. Convenção "1 source por modo de render" (O1) preservada.

**Validação:**
- `salary_engine_test.py` 48/48.
- `GET /trades` + `GET /salary_history`: HTTP 200 com `renderPlayerPhoto` no JS.
- `GET /api/salary_history?team=<name>`: 85 records, 100% com campo `sleeper_player_id`.
- Smoke SSR de `/trades/proposta/<uuid>`: não executado localmente (sem TradeProposal ativa em DB local); validado via leitura do template + padrão SSR já provado em `team_detail`.

---

### UX4 — Macro Compartilhada de Linha de Roster (HYBRID)
✅ **Concluído (24/04/2026)** — Prioridade **Média**

**Entregue:** macro Jinja `player_roster_row(player, context)` + classe CSS `.player-roster-table` + canonização de cores por posição via CSS vars `--pos-color-*`. Aplicada em `team_detail.html` e `roster.html`. `.player-row` legada preservada para uso residual em `admin.html:351` (review_players modal).

**Referência:** `MAN-UX1-REORG-CONSULT` (análise de 3 caminhos; HYBRID recomendado), `MAN-UX4-F1` (design consolidado).

**Implementado:**

**Macro nova (`_macros.html`):** `player_roster_row(player, context='team_detail'|'roster')` renderiza `<tr>` com strip de cor (classe `pos-*`), foto, nome+NFL stacked com tags inline (IR/TRADE/ANO 4/REVISÃO), salário right-aligned, contrato, dynasty, aquisição PT-BR, e — só se `context='roster'` — célula de actions com botão IR. Consome `player_photo` e `player_name_link` existentes (zero réplica).

**CSS (`style.css`):** classe `.player-roster-table` nova (~65 LOC incluindo `@media`). CSS vars `--pos-color-*` canonicalizadas no `:root` — 4 apontam para theme vars existentes (`--purple`, `--green`, `--orange`, `--cyan`), 2 são hex próprios (`--pos-color-wr`, `--pos-color-k`) por não haver correspondente no theme. `.pos-*` existentes refatoradas para consumir as vars. Strip vertical do `.player-roster-table tbody tr` consome as mesmas vars (zero duplicação de hex em seletor de posição novo).

**Responsividade progressiva:**
- `< 640px`: esconde colunas "Contrato" e "Aquisição"
- `< 414px`: esconde também "Dynasty" (sempre visíveis: strip + foto + nome+NFL + salário + actions)

**Backend (`routes/roster.py:index`):** enriquece `all_players` com `p.dynasty_value` (via `resolve_asset_value`) e `p.acquisition_label` (via `_ACQ_LABELS`). Mesmo padrão de UX1 em `routes/league.py:team_detail`.

**Templates:** `team_detail.html` substitui `<tbody>` inline por loop chamando `player_roster_row(p, context='team_detail')`. `roster.html` substitui `<div class="player-list">` + `<div class="player-row">` por `<table class="player-roster-table">` chamando `player_roster_row(p, context='roster')`.

**`.player-row` legacy:** permanece viva no CSS com comentário documentando uso residual em `admin.html:351` (review_players card). Não migrada para macro — semântica diferente (modal admin com campos ad-hoc).

**Decisões delegadas ao Code, documentadas no devplan:**

1. **Badge REVISÃO unificada** em ambos contextos (macro sempre renderiza se `needs_review=True`). Justificativa: status do dado é legítimo em qualquer tela de roster, não depende de ação disponível na tela.

2. **Perda de info em `/` pós-refactor:** roster antigo exibia `ESPN: $X · Projeção 2026: $Y` numa 2ª linha de meta; F1 especificou "name+meta = name + NFL only" — manter escopo estrito do F2 implicou descartar essas 2 métricas. Registrado como débito UX4-b potencial se for necessário restaurar.

**Validação:**
- `salary_engine_test.py` 48/48.
- Smoke `GET /team/<id>`, `/`, `/admin`: todos HTTP 200.
- Tabela com strip: 23 rows em `/team/<id>`, 25 em `/`, distribuídas nas 6 classes `.pos-*`.
- Sum HTML dynasty_value == backend total (60608 em team testado, 57514 em active-only bate com `dynasty_total` no Cap Breakdown).
- PT-BR ("Startup Auction") presente em ambas as telas.
- `toggleIR` handler intocado e funcional em `/`.
- Admin review_players modal (`.player-row` legacy) renderiza inalterado.
- Grep Sleeper CDN: 2 matches (macro + JS helper), 0 inlines novos. Grep de hex de pos-color em pos-color direta: só `#60a5fa` e `#94a3b8` (1 ocorrência cada). Os outros 4 apontam para theme vars — canonização estrutural.

---

### X1 — Acesso Multi-usuário ✅ 31/03/2026

**Problema:** O Manager rodava apenas localmente. Os outros 11 owners não tinham acesso ao estado real da liga.

**Solução:** Preparação completa para hospedagem no PythonAnywhere com autenticação Google OAuth. Subdividido em X1a-X1d abaixo.

---

### X1a — Preparar App para Produção ✅ 31/03/2026

**Solução:** `wsgi.py` como entry point WSGI. `.env` com `APP_ENV`, `SECRET_KEY`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`. `load_dotenv()` no topo do `app.py`. `ProxyFix` para reverse proxy. Debug condicional via `APP_ENV`. `requirements.txt` corrigido com todas as dependências (flask-login, authlib, python-dotenv, pandas, openpyxl). Startup sync com try/except para degradação elegante.

---

### X1b — Google OAuth + Flask-Login ✅ 31/03/2026

**Solução:** Blueprint `routes/auth.py` com `/login`, `/login/google`, `/auth/callback`, `/logout`. `LoginManager` com `unauthorized_handler` que retorna 401 JSON para `/api/*` e redirect para `/login` em rotas de página. OAuth via `authlib` com Google OpenID Connect. Template `login.html`. Email não cadastrado renderiza erro 403.

---

### X1c — Tabela `users` + seed_users.py ✅ 31/03/2026

**Solução:** Model `User(UserMixin)` em `models.py` (email, name, team_id FK, is_admin). Migration em `_run_migrations()`. Script `seed_users.py` aceita CSV ou parâmetros CLI (`--email`, `--name`, `--team-id`, `--admin`, `--list`).

---

### X1d — Decorators de Permissão ✅ 31/03/2026

**Solução:** `@login_required` em todas as rotas (exceto login/callback). `@admin_required` em 27 rotas POST/PATCH/DELETE que alteram dados calculados ou são irreversíveis. Exceções: `POST /api/admin/sync` (reflexivo, `@login_required`), `POST /api/trades/preview` e `POST /api/salary/calculate` (simulações, `@login_required`). `POST /api/player/<id>/ir` classificado como `@admin_required` (correção administrativa).

---

### F1 — Correção de Salários por Partial Name Match ✅ 28/03/2026

**Problema:** Partial/substring name matching durante o import original do CSV corrompeu salários de Marquise Brown, A.J. Brown e Amon-Ra St. Brown (todos resolvidos para o mesmo "Brown").

**Solução:** Correção atômica nos três jogadores em `Player`, `SalaryHistory` e `PlayerHistory`. `player_lookup.py` reformulado com hierarquia estrita: exato → case-insensitive → normalizado. Substring e surname isolado bloqueados explicitamente.

---

### F2 — Ordenação do Round 1 via Lottery + Standings ✅ 28/03/2026

**Problema:** Ordem do Round 1 do rookie draft estava incorreta — não respeitava `draft_lottery_result` para picks 1-5 e `season_standings` para picks 6-12.

**Solução:** Lógica corrigida na rota `/picks` para consultar as duas tabelas e montar a ordem correta.

---

### F7b — Data migration automática para limpar DB de produção ✅ 22/04/2026

**Problema:** F7 corrigiu o código e limpou o DB local, mas o DB de produção (Render persistent disk) continuou stale porque `init_data.py` não sobrescreve `/data/dynasty.db` quando já existe. Owner preferiu não usar Render shell (experiência ruim, trava).

**Solução:** Migração 4 em `_run_migrations()` (app.py) com 3 blocos independentes guardados por `SELECT COUNT`:
- 4a: `DELETE FROM salary_history WHERE rule_applied='import'` (quando count > 0)
- 4b: Rewrite 3 Browns via subquery de nome (robusto a pid diferente entre local/prod) + DELETE das rows `salary_correction` (quando count > 0)
- 4c: UPDATE das rows com `notes='import'` em rollover → `'Renovado (VALORIZAÇÃO)'` (quando count > 0)

**Idempotência verificada em 3 cenários locais:**
- DB limpo → todos os guards skipam (zero linhas F7b no stdout)
- Estado stale injetado → 3 linhas F7b aparecem, DB fica limpo
- Re-run pós-migração → guards skipam novamente

**Custo por boot:** 3 `SELECT COUNT(*)` extras (~ms). No-op após primeira execução em cada ambiente.

**Deploy:** Render auto-deploya com o push; na próxima partida do app em prod, os 3 blocos detectam o estado stale e aplicam o fix automaticamente. Logs de deploy devem mostrar `[migrate] F7b: deleted 9174 stale salary_history rows`, `[migrate] F7b: rewrote 3 Browns + deleted 3 salary_correction rows`, `[migrate] F7b: cleaned 220 'import' notes → 'Renovado (VALORIZAÇÃO)'`.

---

### F7 — Fix SalaryHistory duplicado + rewrite 3 Browns + redesign /salary_history narrativo ✅ 22/04/2026

**Problema 1 — SalaryHistory inflado:** `import_csv.py:104-111` inseria `SalaryHistory(rule_applied='import')` a cada boot sem guard de idempotência. DB tinha 9174 rows (esperado ~278) — inflação ~33× causada por ~33 boots do app.

**Problema 2 — 3 Browns com rastro de bug:** PlayerHistory rows 498/499/500 (event_type=salary_correction) eram reconciliação do "3 Browns bug" (F1) — swap de salários no import original. Não eventos da liga.

**Problema 3 — /salary_history técnica:** tela lia SalaryHistory (campos opacos tipo `rule_applied`), não narrava como o jogador chegou ao salário atual.

**Solução (Opção A — rewrite limpo):**
1. **Fix:** removido INSERT em `SalaryHistory` dentro de `run_import()` (rollover e auction já criam rows legítimos). Cleanup one-time: `DELETE FROM salary_history WHERE rule_applied='import'` (9174 rows removidas).
2. **3 Browns:** UPDATE em PlayerHistory para refletir salários reais desde o draft (A.J.Brown→$47, Marquise→$3, Amon-Ra→$61, em auction_draft/keeper + rollover). DELETE das 3 rows salary_correction. Audit do bug preservado em improvements.md (F1) + Log de Decisões — sem necessidade de rastro no banco.
3. **Redesign /salary_history:** API trocou fonte de `SalaryHistory` para `PlayerHistory`. Payload agora inclui `event_type`, `notes`, `team_name`, `current_salary`. Template redesenhado para cards agrupados por jogador, com rótulos PT-BR por event_type (Draft Auction, Mantido como keeper, Renovado pela VALORIZAÇÃO, Trade, etc.). Expansão inline continua existindo via `/api/player/<id>/history` já existente. Coluna "Regra" (rule_applied cru) removida.
4. **Cleanup cosmético extra:** 220 rows de PlayerHistory com `notes='import'` (fóssil de `_backfill_player_history` que usava `hist.rule_applied` como fallback) foram atualizadas para `'Renovado (VALORIZAÇÃO)'` — evento rollover agora tem nota legível.

**Validação:**
- `SELECT COUNT(*) FROM salary_history` → 0 (era 9174)
- `SELECT COUNT(*) FROM player_history WHERE event_type='salary_correction'` → 0 (era 3)
- A.J. Brown: auction_draft $47 S2024, rollover $47 S2025 (sem correção visível)
- Re-boot app 3× consecutivos → salary_history continua 0 (guard funcionando)
- Filtros por team/player/season na UI continuam funcionando
- Test_client: 500 records retornados, 242 jogadores únicos, zero salary_correction no payload

---

### F3 — Histórico Inline (Accordion) na Aba de Histórico ✅ 28/03/2026

**Problema:** Histórico de transações de um jogador só estava disponível via modal na aba de roster, não na aba de histórico (`/salary_history`).

**Solução:** Adicionado accordion expansível por jogador na aba de histórico, consistente com o comportamento do modal no roster.

---

### M5 — Ordenação por Posição em Todas as Telas de Roster ✅ 02/04/2026

**Problema:** Jogadores apareciam em ordem aleatória nos endpoints de API (roster by id, roster by name, cap projector). A página HTML de roster já ordenava via `_build_players_by_pos()`, mas as APIs JSON não.

**Solução:** `POS_ORDER` movido de `routes/roster.py` para `models.py` como constante central. Criada função `sort_players_by_pos(players)` em `models.py` que ordena por posição (QB→DEF) e salary DESC. Aplicada em `routes/roster.py` (2 endpoints API) e `routes/salary.py` (cap projector).
