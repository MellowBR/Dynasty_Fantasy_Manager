# improvements_archive.md — Fantasy Manager (histórico de itens concluídos)

> Seções detalhadas de itens ✅ (validados), movidas **verbatim** do improvements.md (item O3, 11/06/2026).
> Registro de evidência para diagnoses futuras (incidente Brown, post-mortem T2-FIX, decisões M15…).
> **Status Rápido e itens ativos (🔲/⚠️) vivem em `improvements.md`.**

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

### M1 — Alerta de Cap Estourado Pós-S1
✅ **Concluído (27/04/2026)** — Prioridade **Média**

**Reframing pós-F1:** o item original assumia paradigma pré-S1 ("validação antes de confirmar trade") com `confirm_trade()` bloqueante. Diagnose `MAN-M1-F1` (27/04/2026) confirmou que esse paradigma não existe mais: T1 transformou Trade Manager em simulador puro (preview + link compartilhável); S1 fez do sync Sleeper o único caminho que materializa trades reais. Owner também esclareceu que **cap é soft** (hard só na entrada do FA auction) — M1 vira alerta, nunca bloqueio. Item reescrito de "gate" para "alerta em duas surfaces complementares".

**Implementado (A+B integrados, não redundantes):**

- **Surface A — preview escalonado no Trade Manager** (`templates/trades.html` JS render + `templates/trade_proposal.html` Jinja): `_compute_cap_impact` (`routes/trades.py:86`) já retornava `over_cap: bool` por lado; M1 elevou o sinal de um `<p class="text-danger">⚠️ Acima do cap!</p>` discreto para banner `.cap-overrun-alert` proeminente no topo de cada preview-side com cópia explícita "⚠️ {Time} ficaria $X acima do cap". Aplicado tanto no simulador interativo (`/trades`) quanto na proposta read-only compartilhável (`/trades/proposta/<uuid>`). Zero novo backend — pré-decisão exploratória, owner pode mudar de ideia antes de fechar trade no Sleeper.

- **Surface B — alert de sync + banner pós-fato** (`sync_sleeper.py:_compute_cap_alerts` + `_sync_trades` integration + `routes/roster.py` summary + `templates/roster.html` banner): novo helper `_compute_cap_alerts(affected_team_ids)` computa `Team.active_salary()` para cada time tocado pela leva de transações; teams estritamente acima de `SALARY_CAP` viram entries `{"team": str, "active_salary": float, "over_by": float}` em `result["cap_alerts"]`. `_sync_trades` rastreia `affected_team_ids` durante o loop de movimento e chama o helper antes do `db.session.commit()`, **wrapped em try/except** — falha de cálculo loga em `result["warnings"]` mas **não aborta o sync** (Sleeper é source of truth, asset movement sempre completa). `run_sync` propaga para `summary["cap_alerts"]`. Surface visual: banner em `roster.html` (página `/`) com cópia fixa "⚠️ Time está $X acima do cap. Cap será aplicado na entrada do FA auction." Banner é gated por **`g_offseason_mode` AND `summary.own_cap_overrun`** — durante season ativa, suprimido mesmo se time estiver acima. Captura 100% das trades reais (incluindo as feitas direto no Sleeper sem passar pelo simulador).

- **Threshold estritamente acima:** `active_salary() > SALARY_CAP` dispara alerta. Sub-cap = silêncio. Sem margem de aviso preventivo (rejeitado por gerar ruído crônico). Time exato em $200 não dispara.

- **Sem persistência:** banners recalculam a cada page load via context processor + summary. Cap é estado, não evento — rejeitada coluna nova, tabela nova ou `PlayerHistory` de cap (mistura semântica). Sem `event_type` novo no PH.

- **Sem horizonte temporal:** mensagem do banner é fixa, sem contagem regressiva até FA auction. Owner sabe a janela; Manager só comunica o estado.

- **Canal de retorno do alert: novo campo `cap_alerts` separado de `warnings`.** `warnings` carrega data-integrity issues (roster não mapeado, n-way placeholder, player ausente); `cap_alerts` é estado operacional esperado em offseason. Consumidores existentes de `warnings` (`admin.html:236-237`) continuam ignorando o novo campo sem precisar filtrar.

- **Banner B não vai para navbar nesta camada.** Slot da navbar foi para review_count em M2; cap pode receber slot próprio em camada futura se virar dor — banner no roster do user logado é suficiente por ora.

- **Housekeeping aproveitado:** endpoint legado `POST /api/admin/review_players/<pid>/clear` (preservado em M2 por restrição de retro-compat) **removido nesta camada**. Único consumidor era o JS antigo em `admin.html` deletado em M2; F1 confirmou zero consumidores remanescentes via grep. Caminho atual de aprovação é `POST /approve` (auditável). Linha de housekeeping no commit message é o registro — sem entrada em improvements.md (decisão owner).

**Validação (27/04/2026, smoke transitório `scripts/m1_smoke.py` + page-level):**
- `salary_engine_test.py`: 48/48.
- 5 cenários de smoke OK: synthetic player com marker `_M1_TEST_*` injetado no team admin pushed `active_salary` para $449 (over_by=$249); banner aparece com cópia + valor correto quando offseason_mode=true; banner ausente quando offseason_mode=false (gating funciona); helper `_compute_cap_alerts` chamado direto retorna entry com over_by correto; helper com set vazio retorna `[]`. Cenário (iv) "sub-cap → banner ausente" foi skipado graciosamente porque baseline real do team admin já está acima do cap ($239) — exato use case do M1; threshold strict-above coberto via helper.
- Smoke pages: `/admin` 200, `/admin/review` 200, `/` 200, `/trades` 200, `/api/admin/review_players` 200; `/clear` legado retorna **404** (removido com sucesso).
- Smoke deletado pós-validação (`scripts/m1_smoke.py` + diretório `scripts/`).

**Não alterado:**
- `_compute_cap_impact` (já retornava `over_cap` — M1 só consome).
- `Team.active_salary()`, `Team.cap_remaining()`, helpers do salary engine.
- Schema do `Player` (sem coluna nova).
- Lógica de M2 (review approval), auction, lottery, dynasty values.
- Endpoints `/api/admin/review_players` (GET) e `/api/admin/review_players/<pid>/approve` (POST).

**Gap registrado (item M1-FOLLOWUP):** `is_offseason()` cobre "offseason mode ativo" mas não auto-desativa após FA auction concluído. Aproximação aceita: depende do admin desligar manualmente. Se flag persistir além da janela esperada, banner M1 vira ruído ("cap será aplicado na entrada do FA auction" mostrado mesmo após FA auction acontecer). Item registrado em Status Rápido como `M1-FOLLOWUP` (Baixa) para revisitar.

---

### M2 — Tela de Aprovação em Lote de Jogadores `needs_review=True`
✅ **Concluído (27/04/2026)** — Prioridade **Média**

**Diagnose F1 (MAN-M2-F1):** três descobertas moldaram o escopo da F2 — (1) `/admin` já tinha `review_count` + card consumindo `/api/admin/review_players` e `/clear`, então F2 estendeu em vez de construir do zero; (2) o flag `Player.needs_review` cobre duas categorias semanticamente distintas — Cat A (sync sem match: `salary=$1`, `acquisition_type='unknown'`, `espn_ref_value=0`) e Cat B (auction registrada manualmente ou outros: dados válidos pendentes de validação cruzada); (3) o caminho de aprovação anterior era lossy — `/clear` não criava `PlayerHistory`, e PATCH bruto via `setattr` ignora o helper canônico que mantém `SalaryHistory` + `PlayerHistory` consistentes.

**Implementado:**

- **Categorização runtime, sem coluna de schema** (`routes/admin.py: _categorize_review_player`): predicate inline `acquisition_type='unknown' AND salary=1.0 AND espn_ref_value=0.0` distingue Cat A; complemento é Cat B. Endpoint `GET /api/admin/review_players` ganha campo `category: "A"|"B"` no payload de cada player — frontend não duplica predicate.

- **Tela dedicada `/admin/review`** (`templates/admin_review.html`, `@admin_required`): duas seções com header e contagem por seção. Cat A — botão "Aprovar todos com defaults (N)" (modal) + aprovação individual. Cat B — aprovação individual com inputs inline editáveis para `salary`, `acquisition_type`, `contract_year`. Modal de bulk computa contagem em runtime na abertura e exige confirmação explícita.

- **Aprovação auditável atômica** (`POST /api/admin/review_players/<pid>/approve`): body opcional `{salary, acquisition_type, contract_year}`. Sem edits + Cat A → aplica defaults (`unknown→free_agent`). Sem edits + Cat B → confirma sem alteração. Com `salary` editado → usa `correct_player_salary` (helper canônico em `models.py:200`) que atualiza Player + SalaryHistory in-place + cria `PlayerHistory(event_type='salary_correction')`. Sempre cria `PlayerHistory(event_type='review_approved')` adicional com notes contextuais (`"Cat A; applied defaults..."` / `"Cat B; edited: salary $X→$Y, ..."` / `"Cat B; confirmed without changes"`). Tudo numa transação.

- **Aprovação em massa Cat A com guard de race condition** (`POST /api/admin/review_players/bulk_approve_cat_a`): body `{player_ids: [...]}`. Server re-valida cada ID contra estado atual; se algum não é mais Cat A (porque outro admin aprovou ou sync mudou estado), rejeita transação inteira com 409 e mensagem "Estado mudou desde abertura do modal — recarregue". Aplicação parcial proibida — modal mostrou "X serão aprovados" e admin clicou OK; aplicar a Y < X seria divergir do que admin aprovou.

- **Badge global no navbar (Slot A)** (`app.py: inject_review_count` + `templates/_macros.html: nav_dropdown` ganha param `badge`): novo `@app.context_processor` expõe `g_review_count` (admin-only — não-admins recebem 0 sem trigger de query). Dropdown "Admin ▾" no desktop renderiza `Admin ▾ (3)` quando count > 0, oculto quando 0. Mobile section title "Admin (3)" + item "Revisão de Jogadores (3)" replicam o contador. Item novo "Revisão de Jogadores" adicionado ao dropdown Admin.

- **Endpoint legado `/clear` preservado intacto** para retro-compatibilidade (decisão da F1: não quebrar consumidores existentes além do mapeado). UI nova usa `/approve`; legado continua acessível mas sem audit trail (sempre foi assim).

- **Card antigo `#review-card` em `/admin` removido** + JS de fetch/clearReview deletado. Stat-item "Revisão pendente" virou link clicável `<a href="/admin/review">` com mesmo número e estilo (a contagem agora vem de `g_review_count` via context processor — fonte única).

**Auditoria prospectiva, não retroativa:** aprovações futuras geram `PlayerHistory(event_type='review_approved')`. Aprovações passadas via `/clear` legado ficam sem rastro — princípio aprendido em F8 (não sintetizar histórico sem fonte canônica).

**Validação (27/04/2026, smoke transitório `scripts/m2_smoke.py` + páginas):**
- `salary_engine_test.py`: 48/48.
- 7 cenários de pipeline OK: GET com category, approve Cat A defaults, approve Cat B com edição (correct_player_salary atualiza SH in-place, dois `PlayerHistory` criados — `salary_correction` + `review_approved`), bulk com IDs válidos, race-guard com ID já aprovado (409), approve em player não-em-revisão (400), legacy `/clear` segue 200.
- Smoke de páginas: `/admin` 200 (sem crash de `review_count`, link `/admin/review` presente); `/admin/review` 200 com título correto; `/api/admin/review_players` retorna lista vazia em DB local (esperado, 0 players em revisão atualmente).
- DB local zerado obrigou seed sintético com marker `_M2_TEST_*`, `team_id=NULL`. Cleanup atômico no `finally` removeu 3 rows + history. Scripts deletados pós-validação (não merecem slot permanente — se padrão se repetir em camadas futuras, criar `scripts/smoke/` com convenção).

**Não alterado:**
- Schema de `Player` (Cat A/B é runtime, não coluna).
- Setters do flag (sync Sleeper, auction manual, PATCH manual).
- Helper `correct_player_salary` ou outros helpers do salary engine.
- Banner em `roster.html:81-84` e badge em `cap_projector.html:114` (consumidores leitores do flag em outras telas — coerentes via mesmo flag canônico).
- Endpoint legado `/clear` (compat).

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

### M15 — Lottery com 6 seeds (inclusão do 7º colocado com 1 bolinha) — MAN-M15-REG
✅ **Concluído (05/06/2026)** — Prioridade **Média**

**CONTEXTO**
Decisão da liga (owner + comissário, 05/06/2026): o draft lottery passa a incluir
o 7º colocado como sexto seed, com peso de 1 bolinha. A implementação atual (M8,
concluída 23/04/2026) assume 5 seeds (8º-12º) em múltiplos pontos e não permite
a inclusão. O regulamento 8.2.4 já menciona "os seis times não classificados",
mas lista apenas 5 pesos (50/25/12/5/3, soma 95) — a decisão da liga fecha essa
lacuna.

**PROBLEMA / OPORTUNIDADE**
A ferramenta é a fonte de verdade do lottery e hoje bloqueia uma regra já
acordada pela liga. Sem a mudança, o sorteio de 6 seeds teria que ser feito fora
do Manager, quebrando a auditabilidade conquistada no M8 (seed reprodutível,
hash, histórico de re-runs).

**DISCUSSAO**
- Novo pool: 96 bolinhas — 12º=50, 11º=25, 10º=12, 9º=5, 8º=3, 7º=1.
- Lottery passa a definir picks 1-6; picks 7-12 ficam fixos por standings
  (hoje a fronteira é 5/6-12).
- Percentuais da legenda deixam de ser redondos (50/96 ≈ 52,1%) — exibição
  deve derivar de bolinhas/total, nunca de % hardcoded.
- A premissa de 5 seeds está espalhada: pool, paleta fixa de 5 cores na UI,
  result_hash sobre picks 1-5, pool_json, fronteira lottery/standings.
- Auditorias antigas (pool de 5 seeds) precisam continuar verificáveis — o
  endpoint de verify deve operar sobre o pool_json salvo, não sobre a
  configuração vigente.

**DECISOES JA TOMADAS**
- 6º seed = 7º colocado, com exatamente 1 bolinha; pesos dos demais inalterados.
- Pool total = 96 bolinhas; soma de pesos não precisa fechar em 100.
- Auditabilidade do M8 preservada integralmente (seed, hash, verify, re-run
  com reason).

**ALTERNATIVAS DESCARTADAS**
- Rebalancear pesos para somar 100 (ex: 7º com 5 bolinhas): rejeitada — a liga
  quis impacto mínimo nas chances atuais; 1 bolinha é simbólica e suficiente.
- Sortear fora do Manager só nesta temporada: rejeitada — perde auditoria e
  cria precedente de fonte de verdade paralela.

#### Fase 1 Diagnose ✅ (05/06/2026) — MAN-M15-F1
Read-only. Verificado contra código (commit vigente) + leitura direta de
`dynasty.db`. Sweep de réplicas: `grep` por `lottery|bolinha|ball-color|95|seed|
weight|pick_number|[12,11,10,9,8]|range(1,6)` em toda a árvore `fantasy_manager`.
**Não existe arquivo `static/*.js`** — todo o JS do lottery é inline em
`offseason.html` / `lottery_audit.html`. Fora dos 6 arquivos abaixo, os únicos
matches são as definições de modelo em `models.py` (schema, não lógica) e usos
incidentais de "seed"/"weight"/"95" sem relação com o sorteio (seed_users, etc.).

**A premissa de 5 seeds vive em exatamente 6 arquivos:** `routes/offseason.py`,
`routes/picks.py`, `templates/offseason.html`, `templates/lottery_audit.html`,
`static/style.css`, `models.py` (só schema).

**V1 — Literais vs. parametrizados + réplicas (resposta explícita):**
- **Pesos/pool:** `DEFAULT_LOTTERY_WEIGHTS` (`offseason.py:32`) = 5 entradas,
  fonte única do backend. No `offseason.html` a render é **data-driven** (pool de
  bolinhas, legenda e editor de pesos iteram `lottery_weights`).
- **Percentuais da legenda:** já **derivados** de `weight*100/total_weight`
  (`offseason.html:165`) — não hardcoded. ✓
- **Réplica de % hardcoded (SIM, existe):** `routes/picks.py:13-21` `LOTTERY_ODDS`
  é dict Python literal (`50/25/12/5/3/3/2`) consumido na legenda de
  `picks.html:112-113`. Está **já divergente da realidade hoje** (7 entradas com
  pick6=3%/pick7=2% que não batem com o pool real de 5 seeds/95 bolinhas) →
  ver "Item descoberto" abaixo.
- **Contagem de bolinhas hardcoded (SIM):** string `"Total: 95 bolinhas
  (50 + 25 + 12 + 5 + 3)"` em `offseason.html:128`.
- **Listas de ranks literais (SIM, replicadas):** `[12, 11, 10, 9, 8]` em
  `offseason.py:144` (lottery_seeds), `:383` (simulate), `:478` (execute) e
  `picks.py:195` (standings order).
- **Paleta de cores literal (SIM):** CSS só define `ball-color-1`…`ball-color-5`
  (`static/style.css:1910-1914`), com comentários atados a 12º-8º. Falta
  `ball-color-6`. Template gera a classe via `'ball-color-' ~ seed`
  (`offseason.html:137`) — um 6º seed renderiza com classe inexistente (sem cor).
- **JS:** sem cálculo de peso/percentual em JS. `animateReveal`
  (`offseason.html:494`) filtra por `r.source === 'lottery'` (data-driven; a var
  `lottery5` é só nome).

**V2 — result_hash/verify hardcoded a "picks 1-5"? Audits antigas quebram?**
- `_compute_result_hash` (`offseason.py:73`) **deriva do tamanho da lista**
  recebida (não hardcoded; parâmetro só se chama `picks_1_to_5`). ✓
- **Hardcoded a 5 (SIM, 2 pontos):** o draw `_draw_weighted_lottery`
  (`offseason.py:58`, `for pick_num in range(1, 6)`) e o verify
  (`picks.py:313-318`, `DraftLotteryResult.pick_number <= 5`).
- **Audits antigas (5 seeds) quebram com a mudança? → NÃO**, *desde que* a F2
  derive a contagem de draws do tamanho do `pool_json` salvo (não de uma
  constante global "6"). Justificativa: o verify reproduz lendo
  `canonical.pool_json` + `canonical.random_seed` (snapshot imutável), e o hash
  já deriva do tamanho da lista. Uma audit de 5 times reproduz 5 picks e bate com
  seu hash gravado. **O risco de retrocompat só aparece se a F2 trocar `range(1,6)`
  por `range(1,7)` fixo** — aí audits de 5 seeds desenhariam 6 e divergiriam.
  Regra para a F2: parametrizar draw e threshold por `len(pool)` do snapshot,
  nunca por constante de módulo. O `pick_number <= 5` do verify também deve virar
  `<= len(pool)`.

**V3 — Audit canônica para 2026 no banco? → NÃO.**
- `lottery_audit`: **0 rows** (tabela vazia). `current_season=2025` →
  draft_season=2026; `season_locked=false`; `has_canonical_audit`=False.
- `draft_lottery_result` tem 12 rows para 2026 (5 `source='lottery'`), porém são
  fallback de standings / execução pré-canônica — **sem** `LotteryAudit`
  correspondente. **Conclusão: o sorteio oficial 2026 ainda não ocorreu.**
- **Fluxo da F2 = `POST /api/offseason/run_lottery` normal** (NÃO
  `/lottery/replace` com reason; replace é só para re-execução pós-canônica).

**V4 — Fronteira picks 5/6→12 (fixos por standings): fonte única? → NÃO,
replicada em 5 pontos:**
- `offseason.py:_execute_lottery_and_persist` (linhas 497-521).
- `offseason.py:lottery_simulate` (linhas 397-414).
- `offseason.py:save_lottery` (`if pick_num > 5: continue`, linha 573).
- `picks.py:_apply_standings_order` (linhas 194-215).
- `picks.py:_build_pick_projections` — branch de lottery é data-driven (lê
  `lr.pick_number`), mas o fallback de standings delega a `_apply_standings_order`.
- **Nota útil p/ F2:** com a nova fronteira o rank 7 sai dos fixos e entra no
  pool; os fixos atuais picks 7-10 = ranks 6,5,4,3 e picks 11/12 = vice/campeão
  **permanecem idênticos** — só o **pick 6 migra de fixo → lottery**.

**V5 — Recomendação de escopo p/ F2 (parametrizar > ajustar literais):**
Introduzir uma fonte única (ex.: `LOTTERY_SEEDS = [(seed, rank, weight), …]` ou
derivar de `DEFAULT_LOTTERY_WEIGHTS` + nº de seeds) e fazer todos os pontos
consumirem dela / do `len(pool)`. Custo estimado por área:
- **Backend offseason.py** (pesos, `range`, 3× `[12..8]`, fronteira `>5`,
  pool builder ×2): ~1.5-2h. Núcleo da mudança.
- **Backend picks.py** (`_apply_standings_order`, verify `<=5`, `LOTTERY_ODDS`):
  ~1h. Derivar verify de `len(pool)` é o ponto crítico de retrocompat.
- **Template offseason.html** (string "95", legenda já ok): ~15min.
- **CSS** (`ball-color-6`): ~10min.
- **lottery_audit.html** (textos "Pool (ranks 8-12)" `:40`, "Picks 1-5" `:119`):
  ~15min — derivar do pool/contagem real.
- **Validação** (run_lottery 6 seeds → 96 bolinhas, verify de audit nova de 6
  seeds + verify de audit sintética de 5 seeds ainda verde, hash, `salary_engine_test`):
  ~1h. **Custo total estimado: ~5-6h.**

**Item descoberto (pré-existente, independente do M15):** a legenda de odds em
`/picks` (`picks.py:13-21` `LOTTERY_ODDS` → `picks.html:112`) mostra valores
**errados hoje** (7 posições, pick6=3%/pick7=2%, somando ≠ pool real de 5
seeds/95 bolinhas). É um defeito de display latente que antecede o M15.
Recomendação: **absorver na F2 do M15** (a legenda tem de ser reconciliada quando
os seeds mudam — corrigir agora e re-tocar na F2 seria retrabalho). Registrado
aqui para o owner decidir se prefere promover a ID própria (ex.: `M16`) antes da
F2; default proposto = dobrar no M15.

#### Fase 2 Implementação ✅ (05/06/2026) — MAN-M15

**Fonte única criada (`routes/offseason.py`):**
- `DEFAULT_LOTTERY_WEIGHTS = {1:50, 2:25, 3:12, 4:5, 5:3, 6:1}` (soma 96) — única
  declaração de seeds/pesos. `_normalize_weights()` (aceita chaves int/str de
  JSON) e `_seed_rank(seed)` = `13 - seed` (seed 1 = 12º).
- Três builders compartilhados: `_build_lottery_pool(standings, weights)`,
  `_build_fixed_picks(standings, num_seeds)` (limiar deriva de `num_seeds`;
  vice/campeão sempre picks 11/12) e `_build_default_draft_order()` (fallback de
  projeção sem sorteio). Eliminaram as 3 cópias de pool e as 5 cópias da fronteira.

**Pontos que passaram a derivar da fonte única:**
- `_draw_weighted_lottery`: `range(1, len(pool)+1)` (era `range(1,6)`) — contagem
  vem do pool, nunca de constante.
- `run_lottery` / `lottery_simulate` / `_execute_lottery_and_persist`: usam
  `_build_lottery_pool` + `_build_fixed_picks`.
- `offseason_page.lottery_seeds` e `save_lottery` (`> num_seeds`): derivam de
  `DEFAULT_LOTTERY_WEIGHTS`.
- `routes/picks.py`: `LOTTERY_ODDS` hardcoded **removido** → `_build_lottery_odds()`
  (pct = peso/total, importa a config canônica); `_apply_standings_order` delega a
  `_build_default_draft_order`; verify usa `n_lottery = len(pool)` (era `<= 5`).
- `_compute_result_hash`: parâmetro renomeado p/ `lottery_picks` (algoritmo
  intacto; já derivava do tamanho da lista).
- Templates: `offseason.html` total/range derivam de `lottery_weights` (string
  "95 bolinhas" removida); `picks.html` legenda ganhou coluna Bolinhas + 6 linhas
  derivadas; `lottery_audit.html` "Pool (… times)" e texto de verify derivam do
  snapshot. `static/style.css`: `ball-color-6` (ciano #06b6d4, 7º).

**Retrocompat (decisão-chave):** draws e verify derivam de `len(pool_json)` do
snapshot salvo, **nunca** de constante global. Audit de 5 seeds reproduz 5 picks
e bate com seu `result_hash`; audit de 6 seeds reproduz 6. Schema/contrato de
`LotteryAudit` e fluxo de 2 fases do M8 (409 duplicata, replace com reason)
**inalterados**.

**Item descoberto absorvido:** o `LOTTERY_ODDS` divergente (legenda errada em
`/picks`) foi corrigido aqui — passou a derivar da mesma fonte; não virou ID próprio.

**Validação (05/06/2026) — 8 validações via Flask `test_client` sobre cópia
temporária de `dynasty.db` (DB real intocado), 19 asserts, 19/19 PASS:**

| # | Validação | Resultado |
|---|-----------|-----------|
| V1 | `run_lottery` 2026 | 200, 12 picks (1-6 lottery / 7-12 standings), audit pool 6 times, soma pesos = 96 |
| V2 | verify do audit novo | `match=true`, `result_hash_match=true` |
| V3 | retrocompat: audit sintético 5 seeds | reproduz exatamente 5 picks, `match=true` (cleanup ok) |
| V4 | UI `/offseason` | 96 bolinhas, `ball-color-6` presente, legenda 6 linhas, 7º=1.0%, "95 bolinhas" ausente |
| V5 | legenda odds `/picks` | 6 posições (12º…7º), 12º=52.1% / 7º=1.0%, valores antigos ausentes |
| V6 | run duplicado / replace sem reason | 409 / 400 (fluxo M8 intacto) |
| V7 | `lottery/simulate` | 6 lottery + 6 fixos, picks 1-6 sorteados (96 bolinhas) |
| V8 | `salary_engine_test.py` | 48/48 |

**Arquivos modificados:** `routes/offseason.py` (fonte única + 3 builders +
refactors), `routes/picks.py` (odds derivada, verify por `len(pool)`, standings
order delegado), `templates/offseason.html`, `templates/picks.html`,
`templates/lottery_audit.html`, `static/style.css` (`ball-color-6`), `CLAUDE.md`.
Script de validação descartado pós-run (não merece slot permanente).

**Nenhum item novo pendente descoberto na F2.** O sorteio oficial 2026 segue a
cargo do admin via `/offseason` (a fronteira/pool agora suportam 6 seeds).

**DEPENDENCIAS**
- Depende de: M8 (base auditável — concluído).
- Bloqueia: execução do lottery 2026 (sorteio oficial ainda não ocorreu; agora
  desbloqueado — a ferramenta suporta 6 seeds).

---

### M15-FIX — Editor de pesos do lottery desconectado do pool/legenda — MAN-M15-FIX-REG
✅ **Concluído (05/06/2026)** — Prioridade **Média**

**CONTEXTO**
Pós-deploy do M15 (6 seeds, 96 bolinhas), owner editou os pesos via seção
"Editar pesos (avançado)" do `/offseason` (valores 24/12/6/3/2/1) e o pool de
bolinhas + legenda continuaram renderizando o canônico (50/25/12/5/3/1).

**PROBLEMA / OPORTUNIDADE**
Editor e visualização divergem, e não estava estabelecido quais pesos o sorteio
oficial consome nem quais são gravados no audit. O owner quer pesos editáveis
como capacidade permanente — o fluxo precisa ficar consistente ponta a ponta:
o que a tela mostra = o que o sorteio usa = o que o audit grava.

**DISCUSSAO**
- Pesos canônicos do M15 (50/25/12/5/3/1) viram default; editor permite override
  por execução.
- Auditabilidade do M8 já snapshota `weights_json`/`pool_json` — se o sorteio usar
  os pesos editados e o audit gravar exatamente esses, a auditoria se mantém íntegra.
- Ponto de design derivado: a legenda de odds do `/picks` deriva hoje da config
  canônica (M15). Com pesos editáveis, após o sorteio oficial ela deve refletir os
  pesos efetivamente usados (`weights_json` do audit canônico), não o default.

**DECISOES JA TOMADAS**
- Editor permanece e deve ser funcional: edição re-renderiza pool e legenda em
  tempo real, sorteio oficial usa os pesos editados, audit grava os pesos usados.
- Canônicos 50/25/12/5/3/1 são o estado inicial dos inputs (default).

**ALTERNATIVAS DESCARTADAS**
- Remover o editor e fixar pesos só na fonte canônica: rejeitada — owner quer
  flexibilidade de ajustar pesos por decisão de liga sem deploy.
- Fix visual direto sem diagnose: rejeitado — pode mascarar divergência entre
  sorteio e audit.

#### Fase 1 Diagnose ✅ (05/06/2026) — MAN-M15-FIX-F1
Read-only. Verificado contra `templates/offseason.html`, `routes/offseason.py`,
`routes/picks.py` (pós-M15, commit 09f3b0a).

- **O sorteio (oficial + simulação) consome pesos editados ou canônicos? O audit
  grava o que foi usado? → Consome os EDITADOS; audit grava os USADOS (backend já
  correto).** `gatherLotteryWeights()` (offseason.html:411) lê os inputs
  `.lottery-weight` e `runLottery()`/`submitReplace()` enviam `{weights}` no body.
  No backend, `run_lottery` (offseason.py:421), `lottery_simulate` (:460) e
  `lottery_replace` (:511) fazem `weights = data.get("weights", DEFAULT_LOTTERY_WEIGHTS)`
  → usam os editados. `_execute_lottery_and_persist` chama
  `_build_lottery_pool(standings, weights)` (:537) e grava `weights_json` (:564-570)
  + `pool_json` com exatamente esses pesos. **Auditabilidade íntegra.**
- **O editor é resquício pré-M15 desconectado da fonte única? → NÃO do backend; SIM
  da visualização.** Os inputs estão ligados ao backend (acima) e partem dos
  canônicos (`value="{{ pct }}"`, :179). O que está desconectado é a render
  **pré-sorteio**: o grid `#lottery-pool` (Jinja, :143-152) e a legenda (:159-169)
  são gerados UMA vez no server a partir de `lottery_weights` (canônico, passado no
  page load), e os inputs **não têm `oninput`/`onchange`** → editar não re-renderiza
  pool/legenda/total. A divergência reportada é puramente client-side; o resultado
  do sorteio sai correto (usa os editados), mas a tela "mente" antes do clique.
- **A legenda do `/picks` pós-sorteio lê da config canônica ou do audit? → Sempre da
  config canônica (gap).** `_build_lottery_odds()` (picks.py:13-27) lê sempre
  `DEFAULT_LOTTERY_WEIGHTS`, nunca do audit. Após um sorteio oficial com pesos
  editados, a legenda do `/picks` mostraria os % canônicos, divergindo do
  `weights_json` do audit canônico.

**Escopo do fix (fase seguinte) — 2 frentes:**
- **A — re-render em tempo real (`/offseason`):** dar `oninput` aos `.lottery-weight`
  → função JS que reconstrói `#lottery-pool` (bolinhas por peso, classes
  `ball-color-{seed}`), a legenda (bolinhas + % = peso/total) e o "Total: N bolinhas"
  a partir dos pesos atuais. Custo ~1.5-2h (lógica de render que hoje só existe em
  Jinja precisa de equivalente JS — atenção à réplica: derivar do mesmo critério
  peso/total, ver [[feedback_grep_replicas_before_scope]]).
- **B — legenda `/picks` reflete os pesos usados:** `_build_lottery_odds()` passa a
  aceitar/buscar o `weights_json` do audit canônico da `draft_season` quando existir;
  senão usa o default canônico. `picks_page` injeta a season relevante. Custo ~45min.
- **Validação alvo:** editar pesos → pool/legenda/total atualizam na hora; sorteio
  oficial com pesos editados grava `weights_json` correto (já ok); `/picks` pós-sorteio
  mostra % = `weights_json` do audit; `salary_engine_test` 48/48.

**Item observado (não bloqueante):** confirmar com o owner se, com pesos editáveis,
faz sentido a legenda do `/picks` **antes** de qualquer sorteio mostrar o default
canônico (hoje mostra) — provável sim, pois é o estado inicial dos inputs.

#### Fase 2 Implementação ✅ (05/06/2026) — MAN-M15-FIX

**Frente A — editor reativo, fonte ÚNICA de render (`templates/offseason.html`):**
- A render peso→bolinhas/%/total saiu do Jinja e passou a viver só em
  `renderLotteryPool()` (JS). O template fornece **apenas dados**: os inputs
  `.lottery-weight` com `data-seed` + `data-team` + valor default canônico; o pool
  (`#lottery-pool`) e a legenda (`#lottery-legend-body`) vão vazios e o "Total" é
  um `<span id="lottery-total-balls">`.
- `getSeedRows()` é a única leitura dos pesos; `renderLotteryPool()` reconstrói
  bolinhas, legenda (bolinhas + % = peso/total) e total. Estado inicial sai da
  mesma fonte via `DOMContentLoaded`. `oninput` em cada input dispara o re-render.
- `gatherLotteryWeights()` reescrito sobre `getSeedRows()` → o que é sorteado = o
  que é exibido = o que o audit grava. Removida a leitura paralela antiga
  (`parseFloat(el.value)`).
- **Input inválido** (vazio/zero/negativo/não-numérico; mínimo 1 bolinha):
  `lotteryWeightsValid()` + banner `#lottery-invalid-banner`; `runLottery()` e
  `submitReplace()` bloqueiam antes de qualquer request. Inputs com `min="1" step="1"`.

**Frente B — legenda `/picks` audit-first (`routes/picks.py`):**
- `_build_lottery_odds(weights=None)` agora aceita pesos; `_canonical_lottery_weights(draft_season)`
  lê `LotteryAudit.weights_json` da audit canônica. `picks_page` passa esses pesos
  quando há audit; senão usa `DEFAULT_LOTTERY_WEIGHTS`. Pós-sorteio com pesos
  editados, a legenda reflete os pesos efetivamente usados.

**Backend/contrato inalterados:** endpoints seguem recebendo `{weights}` e gravando
os pesos usados (já era o comportamento — confirmado na F1); schema do `LotteryAudit`,
fluxo de 2 fases do M8 e retrocompat do verify (5 seeds) intocados.

**Validação (05/06/2026) — 8 validações / 15 asserts, 15/15 PASS.** Client-render
(V1/V2/V5) rodou o **JS real** extraído da página `/offseason` em Node com DOM shim;
backend/audit via Flask `test_client` sobre cópia temporária do `dynasty.db` (DB real
intocado):

| # | Validação | Resultado |
|---|-----------|-----------|
| V1 | `/offseason` limpo (50/25/12/5/3/1) | 96 bolinhas, total 96, legenda 52.1/26.0/12.5/5.2/3.1/1.0% |
| V2 | editar p/ 24/12/6/3/2/1 (sem reload) | 48 bolinhas, total 48, legenda 50.0/25.0/12.5/6.3/4.2/2.1%, gather envia editados |
| V3 | sorteio oficial c/ pesos editados | audit `weights_json` = editados; verify `match=true` + `hash=true` |
| V4 | legenda `/picks` audit-first | com audit → pesos do audit (24/50.0%); sem audit → canônico (52.1%) |
| V5 | input inválido (0 / vazio) | `lotteryWeightsValid()=false`, sorteio/simulação bloqueados |
| V6 | fonte única de render | sem render Jinja de bolinhas; 1 só impl JS (`createElement` único) |
| V7 | retrocompat audit 5 seeds | reproduz 5 picks, `match=true` |
| V8 | `salary_engine_test` | 48/48 |

**Arquivos modificados:** `templates/offseason.html` (render single-source JS +
validação + reatividade), `routes/picks.py` (odds audit-first), `CLAUDE.md`. Script
de validação descartado pós-run.

**Nenhum item novo pendente.** O sorteio oficial 2026 está desbloqueado: tela, sorteio
e audit consistentes ponta a ponta, com pesos editáveis por execução.

**DEPENDENCIAS**
- Depende de: M15 (concluído).
- Desbloqueia: sorteio oficial 2026 (tela = sorteio = audit, com pesos editáveis).

---

### M16 — Lottery aplica ordem sorteada a R2/R3 (deveria ser standings invertido) — MAN-M16-REG
✅ **Concluído (05/06/2026)** — Prioridade **Alta**

**CONTEXTO**
Lottery oficial da próxima temporada executado (fluxo M15/M15-FIX). Owner lembrou
regra do regulamento (8.2.1/8.2.5): o lottery define **apenas** a ordem do Round 1
do rookie draft; Rounds 2 e 3 seguem standings invertidos (último colocado abre,
campeão fecha — campeão tem as escolhas 12, 24 e 36).

**PROBLEMA / OPORTUNIDADE**
Com o sorteio canônico gravado e o rookie draft próximo, ordem errada em R2/R3
propaga para trades de picks e para o draft. Verificação read-only antes do draft.

**QUESTOES EM ABERTO (respondidas na F1)**
- A ordem de R2/R3 nas projeções segue standings ou lottery?
- A fronteira dessa regra é fonte única ou replicada?

#### Fase 1 Diagnose ✅ (05/06/2026) — MAN-M16-F1 — **divergência CONFIRMADA (é bug)**
Read-only. Código (`routes/picks.py`) + reprodução do estado pós-lottery em cópia
temporária do `dynasty.db` (DB real intocado — `lottery_audit` local = 0 rows; o
sorteio oficial pode já existir só na produção/Render).

- **R2/R3 seguem o LOTTERY, não standings (bug).** `_build_pick_projections`
  (picks.py:158-166) faz `for rnd in PICK_ROUNDS: proj[(draft, rnd, lr.team_name)]
  = {pick_number: lr.pick_number}` — aplica o **mesmo** `lr.pick_number` (a ordem
  sorteada, com o shuffle dos picks 1-6) a R1, R2 **e** R3. Reprodução com sorteio
  default:

  | | hoje (R2/R3) | regulamento (R2/R3) |
  |---|---|---|
  | abre o R2 (posição 1) | mongoloides (11º, ganhou pick 1) | Miller Time! (12º colocado) |
  | R2 == ordem do lottery? | **sim** | deveria ser não |
  | R2 == standings invertido? | **não** | sim |

  A divergência fica nos **6 times do lottery** (picks 1-6) cuja posição sorteada ≠
  posição por standings; os picks 7-12 (já standings) coincidem, e o campeão cai em
  12/12/12 por coincidência (é sempre o último). Confirmado: `R2/R3 == ordem do
  lottery = True`, `R2/R3 == standings invertido = False`.

- **Propaga para valores dynasty.** `pick_sleeper_id` (dynasty_values.py:192) monta a
  chave FantasyCalc `DP_<round-1>_<projected_pick-1>` a partir de `pick.projected_pick`
  — que vem dessa projeção. Logo R2/R3 com posição errada → **valor dynasty errado**
  nos picks de R2/R3 → avaliação de trade distorcida. Não é só cosmético.

- **Fonte única? NÃO — regra "R2/R3 = mesma do R1" replicada em 3 loops**, todos em
  `_build_pick_projections`: (1) branch lottery do draft_season (161-166); (2) branch
  future seasons com lottery (178-183); (3) `_apply_standings_order` (205-209). Não há
  ponto único dizendo "R1 = lottery; R2/R3 = standings invertido".
  **Nuance:** o caso (3) (sem lottery) está **correto** — sem sorteio, R1=R2=R3=standings;
  o bug é exclusivo de quando HÁ lottery: R2/R3 deveriam reverter para standings.

**Recomendação de escopo (F2):** quando existir lottery, R1 usa as rows do
`DraftLotteryResult`; R2/R3 derivam de `_build_default_draft_order(standings)` (já
existe — fonte única do M15, produz exatamente a ordem standings-invertida 12º→1 …
campeão→12). Aplicar nos dois branches de lottery (draft_season + future). Caso
standings-fallback fica inalterado. Custo ~1-1.5h + validação (R1=lottery,
R2/R3=standings, valores dynasty de R2/R3, regressão `salary_engine`). Sem mudança
de schema/contrato; não toca o sorteio nem o audit (a ordem do lottery em si está
certa — o bug é a fan-out para R2/R3).

**DECISOES JA TOMADAS**
- Verificação read-only antes do rookie draft, em código + estado real pós-lottery.

**ALTERNATIVAS DESCARTADAS**
- Conferir só visualmente no /picks: rejeitada — projeção exibida e picks
  materializados podem divergir; reproduzi o estado e inspecionei a projeção.

#### Fase 2 Implementação ✅ (05/06/2026) — MAN-M16

**Correção (`routes/picks.py`):** o fan-out que aplicava o mesmo `pick_number` aos 3
rounds foi substituído por um orquestrador `_apply_lottery_with_standings_tail()`,
usado pelos **dois** branches de lottery (draft_season + future):
- **R1** deriva das rows do `DraftLotteryResult` (ordem sorteada — data-driven).
- **R2/R3** derivam de `_build_default_draft_order(standings)` — a **fonte única já
  existente** (M15) que produz a ordem standings-invertida (12º abre, campeão fecha).
  Sem nova implementação da ordem por standings.
- Caso **sem lottery** (`_apply_standings_order`) **inalterado** — R1=R2=R3=standings
  já era o correto.

**Impacto colateral corrigido:** como `pick_sleeper_id` (dynasty_values.py) monta a
chave FantasyCalc a partir de `projected_pick`, os valores dynasty de picks de R2/R3
de times do lottery estavam distorcidos desde o sorteio — agora derivam da posição
standings correta (ex.: mongoloides R2 → índice 14/`DP_1_1`, não 13/`DP_1_0`).

**Validação (05/06/2026) — 8 validações / 8 PASS** sobre estado pós-lottery sintético
(discriminante do diagnose) em cópia temporária do `dynasty.db` (DB real intocado):

| # | Validação | Resultado |
|---|-----------|-----------|
| V1 | R1 | picks 1-6 = sorteados (mongoloides 1, Miller 4) + 7-12 standings |
| V2 | R2/R3 | standings invertido — Miller (12º) abre, campeão fecha (12) |
| V3 | caso discriminante | mongoloides 1/14/26, Miller 4/13/25, campeão 12/24/36 |
| V4 | valor dynasty | chave R2 mongoloides = `DP_1_1` (índice 14), não `DP_1_0` |
| V5 | regressão sem lottery | R1=R2=R3=standings (inalterado) |
| V6 | fonte única | R2/R3 vêm de `_build_default_draft_order`; sem rank-list nova |
| V7 | grid `/picks` | renderiza 200 |
| V8 | `salary_engine_test` | 48/48 |

**Arquivos modificados:** `routes/picks.py` (orquestrador R1-lottery/R2-R3-standings;
docstring). Script de validação descartado pós-run.

**Nenhum item novo pendente.** Pós-deploy, owner confere no `/picks` de produção
(audit canônica real): pick 13 deve ser o 12º colocado.

**DEPENDENCIAS**
- Depende de: lottery 2026 executado (feito). Desbloqueia: rookie draft.

---

### M18 — Timestamps exibidos em UTC em vez do fuso do usuário
✅ **Concluído (09/06/2026 — validado em produção)** — Prioridade **Média** — prompt MAN-M16-REG (ID remapeado: M16 já era o R2/R3 fix)

**VALIDAÇÃO EM PRODUÇÃO (09/06/2026 — smoke BRT)**
Sync disparado às **11:47 BRT** (= 14:47 UTC) exibido como **"09/06/2026 11:47"** no
rodapé global — bate com o relógio local, descartando o bug de UTC cru (que mostraria
14:47). Conversão para o fuso do dispositivo confirmada ao vivo. Os 8 critérios
estruturais já haviam passado em localhost no commit `462e3bc`.

**CONTEXTO**
Feedback de produção do Michel (07/06/2026, via screenshot): o card "Sleeper Sync"
mostra "Último sync: 08/06/2026 00:25" quando para ele eram ~21:25 de 07/06 (BRT).
Diferença exata de +3h = UTC renderizado cru.

**PROBLEMA / OPORTUNIDADE**
Timestamps são exibidos no fuso do servidor (UTC) em vez do fuso local do usuário.
Para owners no Brasil, datas "viram o dia" 3 horas antes, gerando confusão sobre
quando o sync realmente rodou. Pedido do Michel: usar o timezone do computador da
pessoa, não GMT como padrão.

**DISCUSSÃO**
- A causa quase certamente não é o armazenamento (UTC no banco é correto e deve
  permanecer), mas a renderização sem conversão.
- Conversão para o fuso do usuário sem pedir config manual aponta para renderização
  client-side (JS lê o timestamp em formato não-ambíguo e formata com o timezone do
  browser).
- Risco clássico de fix pela metade: o formato provavelmente é renderizado em vários
  pontos (card de sync, listagem de trades, salary history, expiração de proposta de
  trade, telas admin). Corrigir só o card reportado deixaria o resto inconsistente.

**DECISÕES JÁ TOMADAS**
- Armazenamento permanece UTC — o item é exclusivamente sobre exibição.
- Fuso deve vir do dispositivo do usuário automaticamente (sem campo de config).

**ALTERNATIVAS DESCARTADAS**
- Hardcode de America/Sao_Paulo no servidor: rejeitado — quebra o princípio (DST/
  owners em outros fusos) e não atende o pedido literal.
- Campo de timezone por usuário no perfil: rejeitado — fricção desnecessária quando
  o browser já expõe o fuso.

**QUESTÕES EM ABERTO** (F1)
- Como os timestamps são armazenados hoje (naive UTC? aware? string)?
- Quantos e quais pontos de renderização de timestamp existem (Jinja + JS)?
- Há helper/filtro central de formatação de data ou cada template formata inline?
- Qual o formato de transporte ideal para o JS converter sem ambiguidade (ISO 8601
  com sufixo de fuso)?

**F1 — ACHADOS (diagnose read-only, concluída)**

Escopo é mais estrutural do que o registro supunha.

*Armazenamento:* **naive UTC** via `datetime.utcnow` (`default`/`onupdate`) em todos os
modelos com data. Exceções (`Trade.trade_date` e snapshot F8 via `fromtimestamp`)
também são **naive**. Armazenamento permanece UTC — **nada a mudar nessa camada**.

*Sem ponto central de formatação:* não há filtro Jinja, util Python nem helper JS.
A string de formato `%d/%m/%Y %H:%M` está **duplicada ~9×** entre `to_dict()` de
modelos, rotas e templates. **~10 sites independentes** de formatação.

*Conjunto completo de pontos de renderização, por camada:*
- **Server-side Jinja (`strftime` no template):** card "Sleeper Sync"
  (`admin.html:45`); snapshot F8 (`admin.html:171,177`); ESPN import
  (`espn_import.html:80`); lottery audit (`lottery_audit.html:28,86`); lista de
  trades — **só data** (`trades.html:162`); proposta de trade — created/expired/
  days_left (`trade_proposal.html:16,39,41`).
- **Server-side via `to_dict`/rota, entregue pré-formatado ao JS:** rodapé global de
  último sync (`base.html:167` ← `/api/admin/last_sync` → `SyncLog.to_dict`) — **é o
  que o Michel viu**, além do card admin; modal de detalhe de trade
  (`_trade_detail_modal.html:58` ← `Trade.to_dict`).
- **Client-side com `Date` real:** criação de link de proposta
  (`trades.html:651`, `new Date(d.expires_at).toLocaleString`) — **único** que tenta
  conversão, e está **bugado**: recebe ISO de datetime **naive sem `Z`/offset**
  (`routes/trades.py:339`), `new Date` interpreta como **local** → conversão sai
  deslocada.

*Candidatos do registro reavaliados:* trades ✅; expiração de proposta ✅; telas
admin ✅ (ESPN import, lottery audit, snapshot F8). **Salary history NÃO exibe
timestamp** — `created_at` chega no payload (`routes/salary.py:156`) mas
`renderEventRow` mostra só `S<season>`+label+notes → **campo morto na UI**.
**Bônus:** `AuctionLog.created_at` (`models.py:693`) também no payload e **não
exibido** → campo morto.

*Transporte:* quase nenhum timestamp chega ao cliente em formato convertível — onde o
servidor já formatou para string, **o fuso foi destruído antes do browser**. O único
ponto entregue como ISO (`expires_at`) vem de datetime **naive (sem `Z`/offset)** →
ambíguo. **Conversão client-side é impossível sem antes mudar o transporte.**

**DECISÕES DE ESCOPO F2 (owner, pós-F1)**
1. **Fonte única:** criar um ponto único de formatação (transporte UTC não-ambíguo do
   servidor → conversão para o fuso do dispositivo no cliente) e **migrar os ~10
   sites** para ela. Não corrigir pontualmente site a site.
2. **Transporte:** armazenamento permanece UTC; servidor passa a entregar **UTC
   não-ambíguo** (ISO-8601 com `Z`/offset ou epoch) em vez de string pré-formatada;
   cliente converte para o fuso do browser **automaticamente, sem config** do usuário.
3. **Campos mortos preservados:** `salary history` e `AuctionLog.created_at` não
   exibidos **NÃO** são removidos nesta F2 — possíveis consumidores futuros (amarração
   com **WV1**, que pode torná-los vivos). Escopo da F2 restrito à correção de fuso.
4. **Ponto client-side bugado** (criação de link de proposta) é corrigido **pela mesma
   fonte única** — o transporte não-ambíguo resolve a causa.

**F2 — IMPLEMENTAÇÃO (08/06/2026, ⚠️ validado em localhost)**

*Fonte única (1 por modo de render, convenção do projeto):*
- **Marcação UTC (servidor):** `timeutil.utc_iso(dt)` — naive-UTC → ISO-8601 com `Z`.
  Usada por `to_dict()`/rotas **e** registrada como filtro Jinja `utc_iso` (`app.py`),
  consumido pela macro **`local_dt(value, fmt)`** (`_macros.html`) que emite
  `<time class="js-localtime" datetime="…Z" data-fmt="…">`.
- **Formatação humana (cliente):** **`formatLocalDT(iso, fmt)`** (`base.html`) — único
  ponto que escolhe `dd/mm/aaaa [HH:MM]` e aplica o fuso do device (via `new Date`
  sobre o ISO `Z`). `applyLocalTimes()` converte os `<time>` no `DOMContentLoaded`;
  conteúdo construído por JS chama `formatLocalDT` direto.

*~11 sites migrados:* card "Sleeper Sync" (`admin.html`) + rodapé global
(`base.html` ← `SyncLog.to_dict`); snapshot F8 (`admin.html`, agora `utcfromtimestamp`
em vez de hora local do servidor); ESPN import (`espn_import.html`); banner ESPN do
cap projector (`cap_projector.html` ← `salary.py`); lottery audit (`lottery_audit.html`
×2); lista de trades (`trades.html`, `fmt='date'`); modal de detalhe de trade
(`_trade_detail_modal.html` ← `/api/trades/by_tx`); proposta create/expired
(`trade_proposal.html`); **link de proposta** (`trades.html` — antes bugado: recebia
ISO naive sem fuso; agora ISO `Z` + `formatLocalDT`).

*Transporte corrigido:* `SyncLog.synced_at`, `Trade.trade_date`,
`ESPNImportLog.imported_at`, `LotteryAudit.executed_at` (to_dict) e
`/api/trades/by_tx`, `expires_at`, `espn_status.date` (rotas) passam a emitir ISO `Z`
em vez de string pré-formatada.

*Preservado (decisão 3 / amarração WV1):* `created_at` de salary history
(`PlayerHistory.to_dict`, `routes/salary.py`) e `AuctionLog.to_dict` **não** alterados
nem exibidos — seguem como campos mortos. Armazenamento intacto: `utcnow` naive, **sem
migração de schema**.

*Validação localhost:* `utc_iso(00:25 naive)` → `2026-06-08T00:25:00Z`; rodapé/admin
emitem `<time …Z>`; banco mantém `00:25:00Z`; páginas (`/admin`, `/trades`,
`/cap_projector`, `/salary_history`, `/picks`) → 200; nenhum timestamp cru no `/admin`;
`/api/trades/by_tx` → ISO `Z`. `salary_engine_test.py` 48/48. **Pendente:** smoke em
prod com cliente em BRT (confirmar 00:25 UTC → 21:25 do dia anterior) — não verificável
sem browser real.

**DEPENDÊNCIAS**
- Depende de: nenhum.
- Bloqueia: **M4** (banner de sync desatualizada usará o mesmo timestamp — se M4 for
  implementado antes do fix, herda o bug).
- Relaciona-se com: **WV1** (campos mortos preservados podem virar consumidores).

---

### E1 — Import ESPN robusto end-to-end (upload + degradação graciosa)
✅ **Concluído (08/06/2026 — validado em produção)** — Prioridade **Alta** — MAN-E1-REG / F1 / F2 / FIX

**CONTEXTO**
A ESPN publicou a tabela PPR Top 300 de 2026 (`NFL26_CS_PPR300.pdf`, atualizada em
02/06/2026), insumo do **passo 3 do offseason workflow** (Update ESPN Values). O
parser (`espn_pdf_parser.py`) foi construído e validado contra o PDF de **2025**;
mudança de layout ano a ano pode **quebrar o parsing silenciosamente** e contaminar os
ESPN ref values — que alimentam a **VALORIZAÇÃO do rollover** (`Player.espn_ref_value`
× 1.2 → salário ano 2+). Erro aqui propaga para os salários de toda a liga.

**PROBLEMA / OPORTUNIDADE**
Importar um PDF com layout divergente sem validação pode gravar valores errados/parciais
sem alarme. O passo 3 deve ser destravado só após confirmar que o parser lê o PDF 2026
corretamente.

**PROPOSTA**
- **F1 (read-only):** rodar o parser contra `NFL26_CS_PPR300.pdf` em localhost, **sem
  importar**; conferir contagem total (300) + distribuição posicional esperada
  (QB 32, RB 90, WR 104, TE 34, K 18, DST 22), amostragem de linhas e detecção de
  divergência de layout vs o padrão `{rank}. ({POS}{posrank}) {Nome}, {TIME} ${valor}
  {bye}`. Reportar se o parser precisa de ajuste antes de qualquer import.
- **F2:** import validado em **localhost** (cópia do banco) antes de prod; só então
  liberar o passo 3 em produção.

**DADOS**
- PDF: `NFL26_CS_PPR300.pdf` (owner fornece o arquivo localmente).
- 300 entradas, 4 colunas, padrão `{rank}. ({POS}{posrank}) {Nome}, {TIME} ${valor} {bye}`.
- Distribuição posicional esperada: QB 32, RB 90, WR 104, TE 34, K 18, DST 22.

**DEPENDÊNCIAS**
- Depende de: nenhum. Bloqueia: **passo 3 do offseason** (Update ESPN Values) e, por
  consequência, o **Season Rollover** (passo 4, que usa os ESPN values atualizados).

#### Fase 1 Diagnose ✅ (07/06/2026) — MAN-E1-F1 (diagnose do 500)
Read-only (zero writes — a sonda não abriu o DB; ESPNImportLog/SalaryHistory intactos).

- **(a) Estágio do 500 = parsing, exceção não tratada.** `espn_import_page` (admin.py)
  envolve **só o download** em try/except (linhas 509-515 → falha de download vira
  flash+redirect 302, **não** 500). Já `parse_pdf_bytes(pdf_bytes)` (linha 519) e
  `match_players` (525) **não** têm guarda. Reproduzido: `parse_pdf_bytes(<bytes
  não-PDF>)` lança **`PDFSyntaxError: No /Root object! - Is this really a PDF?`** →
  sem try/except na rota → **HTTP 500**.
- **(b) Resposta da ESPN ao fetch server-side (do meu IP, não-bloqueado):** HTTP **200**,
  content-type **application/pdf**, 230.457 bytes, magic `%PDF-1.7` válido. **Não
  bloqueado aqui.** Inferência: o IP de datacenter do **Render** recebe um corpo
  **não-PDF com status 200** (anti-bot) que passa pelo `raise_for_status()` e quebra o
  `extract_text`. Confirmação 100% exige o log do Render ou rodar do IP do Render —
  não acessível nesta fase.
- **(c) Parser × layout 2026: FUNCIONA** (não é o bloqueio). Do PDF real: **299**
  entradas, spot checks corretos — rank 1 = Bijan Robinson/ATL/$57; rank 92 = KC
  Concepcion/CLE/$3 (nome com 1ª palavra = código de time, tratado); rank 202 =
  Tyreek Hill/**FA**/$0 (free agent, tratado). **Achado secundário:** 299 ≠ 300
  esperado — 1 entrada some (dedup por rank / linha sem `$valor`); reconciliar no F2,
  **não** é a causa do 500 (299 é não-vazio → fluxo segue).
- **(d) Réplicas? NÃO.** Download/parse/match existe em **um único caminho
  server-side**: `routes/admin.py` (download) + `espn_pdf_parser.py` (parse+match).
  Sem parsing/download em JS/templates; `espn_review.html` só dá POST no endpoint de
  confirmação e lê `total_parsed` server-rendered. `espn_bulk` (CSV) é caminho manual
  separado (não usa PDF).

**Causa raiz consolidada:** a rota confia no **código HTTP** (`raise_for_status`) mas
não no **content-type/corpo** da resposta. Quando a ESPN devolve um 200 não-PDF
(anti-bot, típico p/ IPs de datacenter como o do Render), `pdf_bytes` é HTML, o
`parse_pdf_bytes`→`extract_text` lança `PDFSyntaxError`, e a ausência de try/except no
parse vira 500. **O PDF e o parser estão corretos** (provado de IP não-bloqueado).
Candidato secundário (só se o download passar no Render): a escrita de
`.espn_review_pending.json` na raiz do app (admin.py:541) pode falhar em FS read-only
do Render → OSError não tratado.

**Direção sugerida p/ F2 (decisão do owner):** (1) validar content-type/magic-bytes
após o download + envolver parse/match em try/except → flash gracioso no lugar de 500;
(2) suportar **upload manual** do PDF (o owner já tem o arquivo) para não depender do
fetch server-side de um IP bloqueado; (3) reconciliar 299 vs 300.

#### Fase 2 Implementação ✅ (07/06/2026) — MAN-E1-F2
Quatro frentes (causa raiz: a rota confiava no código HTTP, não no corpo; e gravava
estado na raiz do app, read-only em prod):

1. **Upload manual do PDF** (`templates/espn_import.html` + `routes/admin.py`): novo
   `<input type="file" name="pdf_file">` (form `multipart/form-data`); o handler usa os
   bytes do upload se presentes, senão cai para o download por URL. Caminho preferido —
   não depende do IP do servidor (a ESPN bloqueia o datacenter do Render).
2. **Degradação graciosa (anti-500):** guarda de magic-bytes (`pdf_bytes[:4] == b"%PDF"`)
   após obter o conteúdo + `parse_pdf_bytes`/`match_players` agora em `try/except` →
   **flash claro + redirect 302**, nunca HTTP 500. Cobre o 200-não-PDF (anti-bot), URL
   inválida e PDF corrompido.
3. **Estado de review em FS gravável:** `_espn_review_path()` grava
   `.espn_review_pending.json` no **diretório do `dynasty.db`** (`os.path.dirname(DYNASTY_DB)`
   = volume persistente `/data` no Render), nunca na raiz do app (read-only em prod).
4. **Parser 299→300:** `_NAME_RE` ganhou `/` na classe de caracteres — o rank 170
   (`Texans D/ST`, defesa cujo nome caiu em linha standalone) era descartado porque o `/`
   não casava. Agora 300/300.

**Preservado:** matching 3-tier, salary_engine, schema, sync, caminho CSV (`espn_bulk`)
e a semântica provisório/final — todos intocados. Escrita só pelos caminhos canônicos
(`_save_espn_value`, upsert por player+season). Default URL atualizado p/ o de 2026.

**Validação (07/06/2026) — 13 asserts / 13 PASS** (test_client, temp DB, produção
intocada; PDF real obtido read-only e usado como upload):

| Caso | Resultado |
|---|---|
| Upload NFL26 PDF | parse **300**, review total_parsed=300, spot checks Bijan/ATL/$57, KC Concepcion/CLE/$3, Tyreek/FA/$0 |
| URL não-PDF (example.com) / URL inválida | **302 gracioso, nunca 500**, zero escrita |
| Estado de review | gravado no dir do DB (gravável), **não** na raiz do app |
| Confirm provisório → reimport | ESPNValue **não duplica** (280→280); final persiste com `is_final=True` |
| Réplica JS/template | **ausente** (parse/download/match só server-side) |

**Arquivos:** `espn_pdf_parser.py` (`/` no `_NAME_RE`), `routes/admin.py` (upload +
guarda + try/except + `_espn_review_path` + default URL 2026), `templates/espn_import.html`
(upload field + textos). Script de validação descartado pós-run.

#### FIX (07/06/2026) — MAN-E1-FIX: `pdfminer.six` faltava no requirements (500 em prod)
**O ✅ do F2 foi prematuro:** validei tudo em localhost (onde `pdfminer.six` está
instalado), mas o `requirements.txt` **não declarava o pacote** → o build limpo do
Render não o instalava → `ModuleNotFoundError: No module named 'pdfminer'` em
`espn_pdf_parser.py:16` (`from pdfminer.high_level import extract_text`), na **importação
do módulo** — antes de qualquer lógica, afetando upload **e** URL. Ou seja: em prod o
import ESPN nunca funcionou.
- **Fix:** adicionado `pdfminer.six>=20231228` ao `requirements.txt` (pacote correto —
  o legado `pdfminer` é Python 2, abandonado, e **não** fornece `pdfminer.high_level`).
- **Validação em venv limpo** (simula o build do Render): `pip install -r requirements.txt`
  instala `pdfminer.six-20260107`, `from pdfminer.high_level import extract_text` resolve,
  e o legado `pdfminer` não entra. Demais imports do caminho ESPN já cobertos (requests,
  pandas; resto é stdlib).
- **Status revertido p/ ⚠️** até o smoke test em produção (upload do PDF → review 300,
  sem 500). Só então ✅ — regra "marcar ✅ apenas quando validado em produção".
- **Smoke test em produção (08/06/2026): PASSOU** — upload do `NFL26_CS_PPR300.pdf` no
  Render retornou a tela de review com 300, sem 500. **E1 → ✅.**

---

### E4-b — Saneamento de `sleeper_id` (chave de junção confiável)
✅ **Concluído (09/06/2026 — limpeza executada e verificada em produção)** — Prioridade **Média** — fatia de **[[E4]]** (MAN-E4-F1/E4-b-F1/F2) — **PREMISSA CORRIGIDA: os 2 nulos eram duplicatas órfãs → DELETE, não backfill (ver F1 abaixo)**

**VALIDAÇÃO EM PRODUÇÃO (09/06/2026)**
Limpeza executada via a rota admin ("🧹 Limpar Órfãos Duplicados") contra o banco vivo
(`/data/dynasty.db` no Render). **Backup pré-operação:**
`/data/dynasty_prod_backup_2026-06-09_pre-E4b.db`.
- Resultado da rota: **2 órfãos removidos** — "Hollywood Brown" (id 279, +1 PlayerHistory
  stray) e "Cameron Ward" (id 280, +0 hist).
- Estado pós-limpeza: `COUNT(players)=278` (era 280); **players com `sleeper_id` NULL = 0**;
  canônicos intactos (id 58 Marquise Brown sid 5848; id 255 Cam Ward sid 12522).
- **Idempotência confirmada:** segundo acionamento removeu 0.
- Causa-raiz fechada pelo guard (dedup-por-sid + `needs_review` no `import_csv`) na mesma F2.
- Nota: o **seed versionado** (não o banco de prod) ainda contém os 2 órfãos — intencional;
  a rota é re-rodável se um re-seed ocorrer. O **estado vivo está limpo**.

**F2 — IMPLEMENTAÇÃO (09/06/2026, ⚠️ código localhost; limpeza de PROD pendente)**
- **(a) Limpeza — rota admin auditável** `POST /api/admin/cleanup_orphan_players`
  (`routes/admin.py`) + botão **"🧹 Limpar Órfãos Duplicados"** no painel admin. Remove
  Players **sem `sleeper_id`, não-rosterados (`team_id` NULL), não-dropados e SEM
  `SalaryHistory`/`AuctionLog`** (assinatura do órfão sem valor); remove junto
  `PlayerHistory`/`ESPNValue` stray. **Idempotente** (re-rodar acha 0); **auditável**
  (retorna lista de removidos + os preservados-por-terem-histórico); **canônicos (com
  sid) nunca entram no filtro**. Não usa script one-shot.
- **(b) Guard — `import_csv`** (`run_import`): no create, resolve nome+team → `sid` via o
  resolver Brown-safe do [[E4-a]] (`_build_pool_index`/`_resolve_entry_sid`, lazy: só
  carrega o pool no 1º create). Se resolve p/ um Player existente → **atualiza o canônico
  (dedup), não insere**; se resolve p/ sid livre → nasce **com sid**; se não resolve →
  **`needs_review=True`** (fecha o gap: `import_csv` não marcava review → órfão invisível).
  **Sem hard-block** — criação legítima segue.
- **Não toca** schema, `salary_engine`, `sync`, nem o matcher do E4-a (só consome o
  resolver). `run_import` já pula quando não há CSV (prod não tem CSV → guard não
  regenera; os órfãos de prod vieram do seed via `init_data`).
- **Validação localhost (test_client, DB copiado):** a rota removeu os 2 órfãos reais do
  seed (id 279 "Hollywood Brown" +1 PlayerHistory stray; id 280 "Cameron Ward") + 2
  sintéticos; **canônico intacto** (salário/contrato/espn/team_id/sid + SalaryHistory);
  um órfão-com-SalaryHistory foi **preservado** (skipped); **idempotente** (2ª chamada
  removeu 0). Guard: nome→sid de canônico existente resolve p/ dedup; nome irresolúvel →
  `needs_review`. `salary_engine_test.py` 48/48.

**PASSO OPERACIONAL EM PRODUÇÃO (fecha o item)**
Após o deploy: logar como admin → **Admin → "🧹 Limpar Órfãos Duplicados"** → confirmar.
- **Antes:** conferir que existem os 2 órfãos (Hollywood Brown / Cameron Ward) sem time.
- **Depois:** o resultado deve listar **2 removidos** (Hollywood Brown +1 hist, Cameron
  Ward); re-clicar deve dar **0 removidos** (idempotência). Verificar que **Marquise
  Brown** e **Cam Ward** (canônicos) seguem nos seus times com salário/contrato/sid
  intactos. Só então E4-b → ✅.

**ESCOPO** *(premissa original — corrigida pela F1; ver subseção abaixo)*
Backfill dos Players sem `sleeper_player_id` (prod: **2** — "Hollywood Brown" via apelido,
"Cameron Ward") resolvendo contra o pool (com tratamento de apelido) + **guard** para que
Players novos nasçam com `sleeper_id` (ou sejam sinalizados). Sem schema.

**POR QUÊ**
Torna `sleeper_id` chave de junção confiável para [[E4-a]]/[[E4-c]]. **Incremental, não
pré-requisito atômico** — a 99,3% de cobertura, os nulos degradam graciosamente.

**F1 — ACHADOS (diagnose read-only; prod 07/06) — REFUTA O BACKFILL**

Os 2 nulos **não são jogadores a backfillar — são duplicatas órfãs de canônicos já
rosterados:**

| id | nome | sid | team_id | salary/ano | histórico |
|----|------|-----|---------|-----------|-----------|
| **279** | Hollywood Brown | **NULL** | None | 3.0 / 2 | 1 PlayerHistory stray (`rollover` 2025, `team_name=''`) |
| 58 | Marquise Brown **(canônico)** | 5848 | 4 | 3.0 / 2 | 5 eventos completos |
| **280** | Cameron Ward | **NULL** | None | 1.0 / 1 | **nenhum** |
| 255 | Cam Ward **(canônico)** | 12522 | 8 | 1.0 / 1 | 3 eventos |

- **279 "Hollywood Brown" = duplicata de 58 "Marquise Brown"** (apelido↔nome real; salary
  3.0/ano 2 idênticos; canônico rosterado com história completa; `sid 5848` já existe).
- **280 "Cameron Ward" = duplicata de 255 "Cam Ward"** (mesmo QB rookie; 1.0/ano 1 idêntico;
  canônico rosterado; `sid 12522` já existe). Órfão **puro** — 0 registros associados
  (`SalaryHistory`/`AuctionLog`/`PlayerHistory`/`espn_values`/`f8_player_backup` = 0).
- **Backfill duplicaria sids existentes** → viola a unicidade que o E4 assume. **Ação
  ERRADA.** Nenhum merge necessário (canônicos completos).

**Causa-raiz:** `import_csv` cria Player **sem sid e sem `needs_review`**; quando o nome do
CSV/ESPN diverge do Sleeper (Hollywood≠Marquise, Cameron≠Cam), o sync nunca casa por nome
→ **órfão permanente e invisível** (sem `needs_review`, não aparece no review M2).

**RE-PREMISSA + AÇÃO (F1)**
- **279 → DELETE** (+ remover a 1 row `PlayerHistory` stray com `team_name=''`).
- **280 → DELETE** (órfão puro, nada a preservar).
- **Nem backfill nem merge** para nenhum dos dois.

**GUARD recomendado (reusa o existente; sem mecanismo novo; sem hard-block):**
1. **Dedup-por-sid na criação:** resolver nome→sid via o resolver Brown-safe do [[E4-a]]
   (`_resolve_entry_sid`/`_build_pool_index`) e, se resolver, **`find_player_by_sleeper_id`
   → atualizar o canônico** em vez de inserir (teria evitado os 2 órfãos).
2. **`needs_review=True` quando não resolve:** fechar o gap do `import_csv` (que hoje **não**
   marca; `record_acquisition` já marca) → o órfão **surge no review M2** para reconciliação.
- **Rejeitado:** hard-block de criação sem sid — quebra `import_csv` (seed) e `/auction`
  manual, fluxos legítimos onde o sync reconcilia depois.

**DECISÕES DE ESCOPO F2 (owner, pós-F1)**
1. **Delete dos 2 órfãos + guard na MESMA F2.**
2. **Delete reusa infra existente se possível, senão rota admin auditável** — **não**
   script one-shot (preferência: reusar infra sobre criar one-shot).
3. **O delete atinge o banco de PRODUÇÃO** (disco do Render), não o seed versionado
   (seed ≠ prod) — daí a rota admin auditável rodando contra o estado vivo.

**DEPENDÊNCIAS**
- Fatia de **[[E4]]**. Complementa [[E4-a]] (remove o ponto cego dos 2 nulos; reusa o
  resolver do E4-a no guard). Pode rodar antes ou depois de E4-a.

---

### E4-c-1 — Store canônico: fundação (criar + backfill + helper + repontar badge)
✅ **Concluído (09/06/2026 — store backfillado e verificado em produção)** — Prioridade **Alta** — fatia de **[[E4-c]]** (MAN-E4-c-F1/F2) — **aditivo, reversível, sem downtime; entrega o store ao [[DP1]]**

**VALIDAÇÃO EM PRODUÇÃO (09/06/2026)**
Migration 7 rodou no boot pós-deploy contra o banco vivo (`/data/dynasty.db`). **Backup
pré-op:** `/data/dynasty_prod_backup_2026-06-09_pre-E4c1.db`.
- Log do boot: `[migrate] E4-c-1: backfilled 273 rows into espn_value_store (season 2026)`.
- **Store: 273 linhas** (bate com os Players value-bearing com sid, não-dropados).
- **Schema (PRAGMA):** `sleeper_player_id VARCHAR` (aceita chave de texto das DEF), `season`,
  `espn_raw` (nullable, vazio nas linhas backfilladas), `espn_adjusted`, `is_final`.
- **Consistência coluna↔store:** `espn_adjusted` no store == `espn_ref_value` na coluna —
  Marquise Brown (sid 5848) = **1.0** em ambos; **Indianapolis Colts (sid `'IND'`) = 1.0**
  em ambos (chave de texto das DEF funciona no banco vivo).
- **Valores reais preservados:** store MIN 1.0, MAX 68.0, média 8.7; distribuição coerente
  (160 stubs em 1.0 + cauda de valores reais) — backfill fiel, não uniformizado.
- **Coluna intocada:** 278 Players com `espn_ref_value>0` (inalterado — backfill puramente
  aditivo).
- Backfill **idempotente** (guard `COUNT==0` no boot).
- **Correção de registro (F1 do E4-c):** o exemplo de spot-check citava "Marquise Brown
  `espn_ref_value=60`" — **valor real é 1.0**; o `60` era de outro jogador (confusão da
  classe "Brown" no próprio exemplo da doc). O backfill está correto; a **expectativa
  documentada estava errada** — registrado aqui para não propagar o exemplo equivocado.

**F2 — IMPLEMENTAÇÃO (09/06/2026, ⚠️ localhost)**
- **(1) Tabela** `EspnValueStore`/`espn_value_store` `(sleeper_player_id, season)[raw,
  adjusted, is_final]` (`models.py`) — criada por `db.create_all()` (aditivo, **sem ALTER**);
  aceita **sid de texto** (DST `'IND'`…).
- **(2) Backfill** = **Migration 7** (`app.py _run_migrations`): `INSERT ... SELECT` de
  `Player.espn_ref_value>0 + sid + não-dropado` → store em `season=current_season+1` (2026
  prelim), `raw=NULL`, `is_final=0`. **Idempotente** (guard `COUNT==0`). Roda no boot.
- **(3) Helper único** `set_espn_value(player, season, adjusted, raw, is_final)`
  (`models.py`): upsert no store (só se `adjusted>0`) **+** materializa `player.espn_ref_value`.
  **8 escritores roteados:** `_save_espn_value` (confirm), admin bulk, salary bulk,
  `bulk_register` (auction), `record_acquisition`, `import_csv`, roster PATCH. (`sync` segue
  escrevendo `0`/stub — não é valor, não roteado.) Grep confirma: nenhuma escrita de
  `espn_ref_value` fora do helper nos caminhos roteados (resta só `set_espn_value` e o stub
  do sync).
- **(4) Badge PROV** (`cap_projector_data`, `salary.py`) repontada: lê `is_final` do
  **store** por `sleeper_id` (era `ESPNValue` por `player_id`). Demais leitores (engine,
  `to_dict`, templates, draft_import) **inalterados** — leem a coluna materializada; **engine
  nunca vira lookup**.
- **Aditivo:** `ESPNValue` e `RookieEspnValue` **intactos** (DROP/generalização = [[E4-c-2]]).
- **Validação localhost (DB copiado, 10/10):** tabela criada; backfill **248** == value-bearing
  com sid; `store==coluna` (amostra + Marquise Brown 60.0); **DST `'IND'`** no store; badge
  lê `is_final=True` do store; re-migrate **não duplica** (248→248); helper sincroniza
  store+coluna; páginas (`/ /salary /cap_projector /salary_history /picks /league
  /player/<id>`) 200. `salary_engine_test.py` 48/48.

**PASSO OPERACIONAL EM PRODUÇÃO (fecha o item)**
O backfill é a **Migration 7**, que roda **automaticamente no boot pós-deploy** (não há botão).
- **Antes do deploy:** Render Shell → backup `sqlite3 /data/dynasty.db ".backup
  '/data/dynasty_prod_backup_2026-06-09_pre-E4c1.db'"` (o backfill é aditivo/reversível, mas
  backup por disciplina — ver CLAUDE.md).
- **Deploy** (push) → boot loga `[migrate] E4-c-1: backfilled N rows into espn_value_store
  (season 2026)`.
- **Depois:** Shell → `SELECT COUNT(*) FROM espn_value_store` deve bater com os Players
  value-bearing com sid (prod ~248); spot-check de um jogador conhecido (store == coluna).
  Só então **E4-c-1 → ✅**.

**ESCOPO** (passos 1-4 da ordem da F1, todos reversíveis)
1. **Criar** a tabela canônica nova `(sleeper_id, season)[raw, adjusted, is_final]` via
   `db.create_all()` (sem ALTER).
2. **Backfill** store ← `Player.espn_ref_value>0` (248 linhas, **season=2026 preliminar**,
   `adjusted` autoritativo, `raw` vazio, `is_final=False`) — migração idempotente com guard
   por contagem, **backup `/data/dynasty_*.db` antes**.
3. **Rotear os 8 escritores** por um **helper único** `set_espn_value(sid, season, raw,
   adjusted, is_final)` (store upsert + materializa `player.espn_ref_value`).
4. **Repontar** a badge PROV do cap_projector p/ ler `is_final` do store (join por
   `sleeper_id`).

**INVARIANTES**
- `salary_engine` puro (coluna materializada; nunca lookup); idempotência; demais leitores
  inalterados; **DST com sid de texto** representáveis (validar).

**DEPENDÊNCIAS**
- Fatia de **[[E4-c]]**. **Habilita [[DP1]]**. Beneficia-se de [[E4-b]] (sid 100% — ✅).
  Não depende de [[E4-c-2]].

---

### MAN-AUD1-REG — Série AUD: auditoria estrutural read-only por lentes de incidentes
🔲 **Registrado 11/06/2026** — MAN-AUD1-REG (registro apenas; a execução é MAN-AUD1-F1, mesma
sessão). **Série nova `AUD` — auditorias**: varreduras sistemáticas do codebase guiadas por
classes de bug do histórico do projeto, sem fase de implementação própria.

**Objetivo:** diagnose read-only do codebase inteiro (rotas, módulos de domínio, templates com JS
inline, scripts) através de **6 lentes derivadas do histórico de incidentes**, cada uma com
veredito explícito (ocorrências OU varredura limpa, sempre com evidência de busca):
1. **Réplicas Python↔JS/templates** (classe T2-FIX / [[F10]]) — busca pelo padrão de saída, não só
   por nome de função.
2. **Escritas de salary fora do helper canônico** `record_acquisition` (classe [[F9]]).
3. **Resíduos do anti-pattern single-user** — `is_my_team` e equivalentes vs o padrão canônico
   `current_user.team_rel` (precedente M17).
4. **Matching por nome sem `sleeper_id`** (classe "Brown"), fora dos pontos já consertados
   (E4-a, E2-RISK) — inclui scripts utilitários e imports secundários.
5. **Violações do contrato de cap soft** — hard block só na entrada da FA auction (regulamento,
   regra 8.2.7 e contrato de cap; `data/Regulamento - Dynasty - SB FANTASY FOOTBALL LEAGUE -
   12-08-2025.pdf`).
6. **Divergência docs×código** (classe DP1-F1) — premissas afirmadas em CLAUDE.md / devplan /
   improvements.md que o código contradiz; parecer por divergência: premissa falsa / doc
   desatualizado / código errado. **Test drive da regra candidata [[MAN-METH-REG]]**.

**Natureza (sem F2):** AUD1 tem **apenas F1** (diagnose). Não existe AUD1-F2 — cada achado vira
item individual no backlog (série existente adequada: M/E/OFF26/UX/T/S/WV, ou docs-only fix) com
ciclo REG/F1/F2 próprio. Critério de "done" da auditoria: **absorção dos achados nos docs
canônicos** (não há código alterado, logo não há validação em prod).

**Formato de saída exigido:** todo achado entra como entrada candidata no improvements.md com
**evidência** (módulo/área + comportamento observado no código real), **severidade**
(alta/média/baixa) e **parecer** (novo / já catalogado com cross-ref / falso-positivo descartado
com justificativa) — nunca relatório solto fora dos docs canônicos. Conforme a regra do
DEV_METHODOLOGY de absorção imediata de achados de diagnose ("diagnose que aponta novo bug → novo
item 🔲 imediatamente"; precedente de refinamento documental: MAN-O2-REFINE 27/04/2026).

**Baseline de dedupe (já catalogados — cross-ref, não achado novo):** [[F10]] (réplica JS
`draft_budget` no cap_projector), [[F9]] (`bulk_register` sem SalaryHistory), E4-c-2 (higiene do
store), achados secundários do MAN-ESPN12 (×1.2 espalhado em 5 sítios Python; "adjusted"
floorado×não-floorado).

**Origem das lentes:** devplan 23/04/2026 (META: 4 regras pós-T2-FIX) e 10/06/2026 (MAN-METH-REG +
correção de premissa DP1). **Timing:** janela de acesso ao Fable 5 no Claude Code (até 22/06)
motivou rodar a varredura agora — caso cirúrgico da política de modelos (diagnose de causa-raiz
não-óbvia em codebase inteiro).

**F1 EXECUTADA 11/06/2026 — ✅ — VEREDITOS POR LENTE** (MAN-AUD1-F1; evidência de busca por lente;
sanity: `salary_engine_test.py` 48/48 OK, git diff docs-only):

- **Lente 1 (réplicas Python↔JS) — 1 cross-ref + 1 achado novo + 1 descarte.** Varrido: grep
  `Math.*/.toFixed/.reduce` + multiplicações (×1.2/×0.5/×0.8) em todos os 27 templates; hits só em
  cap_projector, offseason, salary, salary_history, trades. (a) `updateSummary` do cap_projector
  (linhas 181-214: total/remaining/spots/usable/pct) = **cross-ref [[F10]]** (escopo integral).
  (b) Editor de pesos do lottery (offseason.html:390-439): réplica da fórmula bolinhas/% entre
  modos de render é **decisão consciente M15-FIX** (comentário "fonte ÚNICA de render" in-code) —
  descartado; mas a assimetria de **validação** virou [[M19]]. (c) Barras de trade
  (trades.html:430-475): agregação client de valores pré-resolvidos pelo server (T2-FIX-2 /
  dynasty_values 100% sid), sem contraparte backend — **limpo**. Labels "×1.2" em templates são
  texto de ajuda com valores do server (já evidenciado no MAN-ESPN12).
- **Lente 2 (escritas de salary) — 2 achados novos + 1 cross-ref.** Varrido: grep
  `.salary =`/`.contract_years =` em todos os .py (8 sítios). Legítimos: `record_acquisition`
  (models.py:375, porta canônica), `correct_player_salary` (models.py:201 — atualiza Player +
  SalaryHistory + PlayerHistory), rollover com history (admin.py:103, offseason.py:674), fixture de
  teste. Achados: **[[F11]]** (rollover DUPLICADO admin×offseason, guards divergentes),
  **[[F12]]** (`import_csv.py:111` sobrescreve sem history a cada boot local). `bulk_register`
  (auction.py:149) = **cross-ref [[F9]]** (confirmado: sem SalaryHistory, sem `record_acquisition`,
  sem token `[ref:]`; + bloco vestigial no-op nas linhas 121-124, fold no F9).
- **Lente 3 (single-user) — consumidores limpos; write-side virou [[M20]].** As 8 surfaces do
  M17-F1 conferidas migradas (roster.html sem flag; league.py/team_detail derivam de
  `current_user`; fonte única `inject_user_team` app.py:115-121). Resíduo genuinamente fora do
  escopo M17 (que só mapeou consumidores): manutenção write-side da flag + constantes
  `MY_OWNER_ID`/`MY_TEAM_NAME` → **[[M20]]** (dep: M17 ✅).
- **Lente 4 (matching por nome) — 2 limpos + 2 cross-refs + 1 achado novo.** Varrido: grep
  `SequenceMatcher/difflib/fuzz/ratio/ilike/contains` em todos os .py. **Limpos:** sync
  (sid-first + fallback nome-completo-normalizado, last-name fallback removido com comentário
  3-Browns, sync_sleeper.py:222-239) e dynasty_values (100% sid + formato DP_). **Cross-refs:**
  espn_pdf_parser fuzzy → [[E4-a]]/E2-RISK; buscas substring user-facing (roster.py:333,
  salary.py:219) são display-only, legítimas. **Achado:** portas do /auction → **[[E4-d]]**.
- **Lente 5 (cap soft) — varredura LIMPA de violações.** Varrido: grep `SALARY_CAP/over_cap/
  cap_remaining/>200` em routes/. Todos os pontos são informativos: preview de trade
  (trades.py:203-204, flag `over_cap`), banner M1 (roster.py:99-100), draft_import
  (`_budget_alerts` — docstring explícita "soft — não bloqueia"). **Gap inverso anotado:** o hard
  block PERMITIDO na entrada da FA auction não existe (auction.py: zero menções a cap/budget) —
  promessa do banner M1 ("cap será aplicado na entrada do FA auction") sem lastro em código;
  enforcement pertence ao escopo planejado do [[OFF26-1]] (budget ao vivo na janela selada) —
  cross-ref, não item novo.
- **Lente 6 (docs×código) — 1 achado novo (CLAUDE.md) + claims confirmadas.** Refutadas contra o
  código as claims do CLAUDE.md (maior blast radius): `salary_engine` zero-DB ✅ (zero imports no
  módulo); "sync nunca sobrescreve salary/contract" ✅ (grep + comentário sync_sleeper.py:242);
  exceção `@login_required` no `/api/admin/sync` ✅ (admin.py:33-34); `clear_rookie_espn_store` no
  Step 5 ✅ (offseason.py:715); `record_acquisition` porta única com exceção F9 ✅. **Divergência:**
  App Startup Sequence → **[[DOC1]]**. Comentário stale em admin.py:122-123 ("CURRENT_SEASON is a
  constant" — contradito por `AppConfig.current_season` + `set_config`) fold no [[F11]].

---

### O3 — Split do improvements.md em ativo + arquivo histórico
🔲 **Registrado 11/06/2026** — MAN-O3-REG (registro apenas; execução = MAN-O3, mesma sessão) —
Prioridade **Média** — série O (organização/processo; precedente MAN-O2-REFINE) — escopo
**Manager-only**.

**PROBLEMA / OPORTUNIDADE**
O improvements.md passou de 2.300 linhas e cresce a cada sessão (o lote AUD1 somou 6 itens +
vereditos). Custo em três frentes: leitura integral pelo Code a cada sessão, ruído no
`project_knowledge_search`, navegação do owner. **Mas as entradas ✅ não são peso morto** — são o
registro de evidência que diagnoses futuras consultam (incidente Brown, post-mortem T2-FIX,
decisões M15). O design separa **volume** sem perder **pesquisabilidade**.

**DESIGN DECIDIDO**
- **improvements.md (ativo)** mantém: cabeçalho + **Status Rápido COMPLETO** (todos os IDs,
  inclusive ✅ — é o namespace de IDs e a baseline de dedupe; fica íntegro num lugar só) + seções
  detalhadas **apenas de itens 🔲 e ⚠️**.
- **improvements_archive.md (novo)** recebe as seções detalhadas dos itens ✅, movidas
  **VERBATIM** — zero reescrita, zero sumarização. **Ambos** os arquivos permanecem no Project
  Knowledge.
- **Regra de migração permanente:** a seção detalhada migra quando o item vira ✅ (validado em
  prod); **⚠️ nunca migra** (segue no ativo até ✅). A migração entra no **checklist de fim de
  sessão**.
- **CLAUDE.md** ganha nota documentando o esquema de dois arquivos, para que diagnoses futuras
  saibam que o histórico vive no archive.
- Promoção a **padrão transversal** (optimizer/predictor) fica para a sessão de revisão de
  metodologia — aqui é Manager-only.

**DESVIO DE SEQUENCIAMENTO (registrado p/ não contradizer o devplan de 11/06)**
O log "Encerramento da sessão AUD1" ordenou DOC1+F12+O3 numa sessão Opus única, com **O3 por
último**. Decisão do owner: **O3 antecipado e executado SOZINHO nesta sessão**. A ressalva "por
último" só valia no caso intra-sessão (DOC1/F12 escreveriam no arquivo antes da reorganização);
executado sozinho, ela cai — fixes futuros (DOC1, F12) nascem direto no arquivo enxuto. **DOC1+F12
seguem na fila** para sessão Opus própria; **F11+F10 (Fable)** permanecem antes de 22/06.

**AO EXECUTAR (MAN-O3):** criar `improvements_archive.md`, mover verbatim as seções ✅, deixar o
Status Rápido intacto no ativo, adicionar a nota no CLAUDE.md, e incorporar a regra de migração ao
checklist de fim de sessão.

---

### OFF26-3 — Importador de drafts de liga fantasma
✅ **Concluído (05/06/2026)** — Prioridade **Alta**

**Descrição:** lê picks de um draft do Sleeper via API (informado o identificador do
draft): **rookie draft** (linear → ordem + jogador; salário pela fórmula vigente do
`salary_engine`) e **FA Auction** (auction → jogador + valor do lance). Match por
`sleeper_player_id` (exato, **sem matching por nome**), **preview obrigatório** antes
da confirmação, criação de contratos **exclusivamente via helper atômico canônico**.

**Motivação:** substitui a entrada manual da tela `/auction` — identificada no
`manager_vision.md` como o passo de **maior risco operacional** do calendário.

**Escopo resumido:** leitura de draft por ID via API; dois modos (linear/auction);
match estrito por `sleeper_player_id`; preview→confirm; contratos via helper atômico.

**Dependências:** **independente** dos demais; paralelizável. Testável contra os
drafts de 2025 já presentes na chain de ligas.

#### Fase 2 Implementação ✅ (05/06/2026) — MAN-OFF26-3-F2

**Camada 1 — helper atômico canônico de aquisição (`models.py`):**
`record_acquisition(...)` é a **única porta** de criação de contrato ano-1:
cria/atualiza Player + grava SalaryHistory + AuctionLog atomicamente (adiciona à
sessão; chamador faz commit → lote transacional no importador). Salário **sempre**
via `salary_engine.year1_salary` (canônico). `acquisition_already_recorded(event_ref)`
dá idempotência **sem mudança de schema** (token `[ref:<event_ref>]` em
`AuctionLog.notes`). **`/auction` refatorado:** `register_fa_auction`,
`register_rookie` e `upload_excel` agora passam pelo helper — criação de contrato
existe em 1 ponto. **Exceção documentada:** `bulk_register` ficou intocado por ser
o item **F9** (restrição explícita do F2); é a única réplica inline remanescente, a
ser consolidada quando o F9 for implementado.

**Camada 2 — importador (`routes/draft_import.py`, blueprint novo):** fluxo único,
modo auto-detectado por `draft.type` (linear→rookie / auction→FA). Lê 1 draft por
`draft_id` via API read-only (reusa `sync_sleeper._get`), resolve Player por
`sleeper_player_id` (`find_player_by_sleeper_id`). **preview** (zero escrita):
matched com salário (canônico) + alertas de budget (`draft_budget`, **soft** — não
bloqueia) + unmatched classificados por causa (DST / rookie não cadastrado /
dropado / roster não mapeado). **confirm**: cada unmatched exige ação explícita
(resolver→player_id/`create` ou `skip`+justificativa); **nenhum pulo silencioso** →
confirm bloqueia (400) se houver pendência. Escreve só via `record_acquisition`.
Idempotente por `event_ref` `draft:<id>:<pick_no>`. Página `/draft_import` (admin).

**Validação (05/06/2026) — 12 asserts / 12 PASS** contra os drafts reais de 2025
em cópia temporária do `dynasty.db` (produção intocada) + API read-only:

| # | Validação | Resultado |
|---|-----------|-----------|
| V1 | dry-run rookie 2025 (36 picks) | 34 match c/ salário = fórmula canônica; 2 unmatched classificados; **0 escritas** |
| V2 | import auction 2025 | 45 contratos criados, salário gravado = `metadata.amount` em 100%; SalaryHistory + AuctionLog por contrato |
| V3 | reimport do mesmo draft | **0 criados** (45 já importados); AuctionLog inalterado — idempotência por contagem |
| V4 | preview/rejeição de junk | **0 escritas** |
| V5 | `/auction` manual | funcional via helper (Player+SalaryHistory+AuctionLog; salário correto) |
| V5b | ponto único de criação | helper usado 3× no `/auction`; 1 inline restante = `bulk_register` (F9) |
| V6 | confirm com unmatched não resolvido | **400 bloqueado** |
| V8 | `salary_engine_test` | 48/48 |

**Picks sem match (rookie 2025):** 2 de 36 — rookies ainda não cadastrados / DST,
apresentados no preview com causa, exigindo ação explícita (não há pulo silencioso).
(Os 21 sem match do F1 eram o agregado das 6 sessões de FA auction, não do rookie.)

**Helper canônico agora existe** — relevante p/ **F9** (consolidar `bulk_register`
nele) e **OFF26-1** (janela selada deve calcular budget/salário consumindo o
canônico, não criar réplica).

**Arquivos:** `models.py` (+`record_acquisition`/`acquisition_already_recorded`),
`routes/auction.py` (3 refactors), `routes/draft_import.py` (novo),
`templates/draft_import.html` (novo), `app.py` (registro do blueprint), `CLAUDE.md`.
Script de validação descartado pós-run. **Fora do escopo (itens próprios):** F9
(`bulk_register`), F10 (réplica JS do budget).

#### Fase 1 Diagnose ✅ (05/06/2026) — MAN-OFF26-3-F1
Read-only. Código + sonda da Sleeper API (leitura) contra a chain real. Nenhuma
escrita (probe rodou sobre cópia temporária do DB; `dynasty.db` real intocado).

**1. Infra de leitura de drafts (reaproveitável):** `sync_sleeper.py` já tem o
necessário, hoje acoplado ao rebuild histórico do PlayerHistory (F8a):
- `_get`, `_walk_league_chain`, `_classify_draft(draft, is_first)` (linear→rookie_draft;
  auction→ startup `auction_draft` se rounds≥20 & primeira liga, senão `fa_auction`).
- `_collect_draft_events()` lê `/league/{lid}/drafts` + `/draft/{did}/picks`, extrai
  `player_id` (=sleeper_player_id), `metadata.amount` (lance), `round`, `pick_no`,
  `roster_id`→team. **Reaproveitável o núcleo de leitura**; **adaptar** porque hoje
  produz event-dicts p/ histórico (salary=amount apenas, sem ESPN p/ rookie, sem
  resolver Player no DB, sem criar contrato) e varre a chain inteira em vez de 1
  draft por `draft_id`.

**2. Caminho de criação de contrato (hoje, via `/auction`):** `routes/auction.py`
faz tudo **inline**, sem helper único: upsert de `Player` + `SalaryHistory` +
`AuctionLog` + commit. Salário: FA = `max(1, int(value_paid))`; rookie =
`max(1, int(espn_raw×1.2))`. **NÃO usa o helper canônico `salary_engine.year1_salary`**
(importado mas não chamado). Matching por **nome** (`Player.name.ilike` + team_id),
não por sleeper_player_id.

**⚠️ Premissa do prompt corrigida:** o "helper atômico canônico de criação de
contrato" **não existe**. O que existe: `correct_player_salary()` (models.py:200) —
canônico só para **correção** de salário (Player+SalaryHistory+PlayerHistory). Criar
o helper atômico de **aquisição** é construção nova (e deveria absorver as 4 réplicas
do `/auction`).

**3. Réplicas (resposta: SIM, várias):**
- **Cálculo de salário ano-1:** canônico = `salary_engine.year1_salary`; replicado
  inline em `routes/auction.py` (`register_fa_auction:45`, `register_rookie:130`,
  `bulk_register:217`, `upload_excel:312`) como `max(1, int(...))`. Coincide hoje,
  mas é divergência latente.
- **Criação de contrato** (Player+SalaryHistory+AuctionLog): sem canônico; replicada
  4× em `routes/auction.py`.
- **Validação de budget:** canônico = `salary_engine.draft_budget`; replicado em **JS**
  em `templates/cap_projector.html` (~linhas 150-171: raw_budget, usable, aviso
  "Budget insuficiente").
- **Ajuste ESPN ×1.2:** inline em vários pontos (auction.py, admin ESPN import).
- **Achado lateral:** `bulk_register` (auction.py:187) está quebrado (hack `_noop`/
  `test_request_context`, não grava `SalaryHistory`) — bug pré-existente.

**4. Matching de jogadores:** picks trazem `player_id` (=sleeper_player_id)
**diretamente** em 100% dos picks (sonda: sid==picks em todos os drafts). Helper
canônico existe: `player_lookup.find_player_by_sleeper_id` (exato, filtra
`is_dropped=False`); `Player.sleeper_player_id` é indexado. **Jogador inexistente no
DB OCORRE:** na sonda de 2025, **21 picks** sem Player correspondente — rookies recém
draftados (DJ Giddens, Dont'e Thornton), **DST** (`SF`), e jogadores de sessões de FA
nunca rosterados/ dropados (Najee Harris, Tua, DeAndre Hopkins…). Hoje o `/auction`
**cria** Player novo por nome com `needs_review=True`; o importador (match por sid)
precisa de política explícita p/ pick sem match (skip+report vs criar com sid +
needs_review).

**5. Preview/dry-run/rollback (modelos existentes):** lottery `simulate` (M8 — roda
sem persistir) + `verify` + `replace`; `_compute_cap_impact` (trade preview sem
persistir); `F8PlayerBackup` (rollback do rebuild F8a); revisão admin Cat A/B (M2,
preview→approve). Idempotência por chave: `sleeper_event_ref` (`draft:{did}:{pick_no}`)
e `sleeper_transaction_id` (S1). Servem de molde p/ preview→confirm + idempotência.

**6. Verificação contra dados reais (sonda read-only):** chain = **3 ligas** (2024
startup, 2025, 2026). **8 drafts completos**: 1 auction startup 2024 (264 picks,
`auction_draft`) + **2025: 6 auctions (`fa_auction`) + 1 linear (`rookie_draft`, 36
picks)** → bate com o "7 drafts (6 auctions + 1 linear)" do F8a. A liga fantasma 2026
existe como auction `pre_draft` (classif None, ignorada — guard de status OK).
**Picks de auction carregam `metadata.amount` em 100%** (confirmado); rookie/linear
não tem amount (salário vem do ESPN). Todos os picks têm sleeper_player_id.

**Divergências DB(2025) × API:** 88 picks 2025 conferidos; **7 divergências de salário**
em auction — mas concentradas em Joe Mixon, Patrick Mahomes ($19/$100/$498/$3…),
Isiah Pacheco. **Causa: 2025 teve 6 sessões de FA auction distintas**; a sonda
comparou o único contrato atual do DB contra TODOS os picks das 6 sessões → o mesmo
jogador aparece com lances diferentes em sessões diferentes. **Não são bugs limpos** —
são (a) evidência de que um jogador aparece em múltiplos drafts (o importador DEVE ser
escopado a 1 `draft_id`, como já previsto) e (b) valores anômalos ($498 p/ Mahomes)
sugerem drafts de teste/junk em 2025 que o **preview precisa deixar o admin rejeitar**.

**Escopo recomendado p/ F2 — FLUXO ÚNICO com dois modos** (não dois fluxos): rookie e
auction compartilham ~tudo (ler draft por `draft_id` → resolver picks por sleeper_id →
preview → criar contrato atômico). Diferem só na fonte de salário, resolvida pelo
canônico `year1_salary(acquisition_type, value_paid, espn_adj)` — auction usa
`metadata.amount`, rookie usa `floor(ESPN×1.2)`. Modo auto-detectado por `draft.type`
via `_classify_draft`. **Gaps classificados:**
- *Reaproveitar:* `_get`/`_walk_league_chain`/`_classify_draft`; padrão `/draft/{id}/picks`;
  `year1_salary`; `draft_budget`; `find_player_by_sleeper_id`; modelos
  SalaryHistory/AuctionLog.
- *Adaptar:* extrair de `_collect_draft_events` um leitor de **1 draft por id** que
  resolve Player no DB e separa salário rookie (ESPN) de auction (amount).
- *Construir novo:* **helper atômico canônico de aquisição** (e refatorar as 4 réplicas
  do `/auction` p/ usá-lo); **preview→confirm** (molde M8/trade); **idempotência** por
  `sleeper_event_ref`; **política de pick sem match** (skip+report vs needs_review);
  matching por sleeper_id no lugar de nome.

**Itens novos descobertos (🔲 próprios sugeridos, decisão do owner):** (a) `bulk_register`
quebrado no `/auction`; (b) réplica do `draft_budget` em JS no `cap_projector.html`;
(c) `/auction` não usa `year1_salary` (replica inline). Candidatos a serem absorvidos
pelo F2 do OFF26-3 (que já vai criar o helper canônico) — registrar como sub-fixes se o
owner preferir rastrear à parte.

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

### UX4-b — Redesign de Densidade e Layout da Página de Detalhe de Time
✅ **Concluído (24/04/2026)** — Prioridade **Triagem**

**Escopo expandido:** originalmente registrado para "restaurar ESPN + Projeção no roster principal", UX4-b cresceu após análise visual completa em `MAN-UX4-b-F1` — 4 camadas coordenadas entregues em 1 commit, cobrindo densidade dos cards de Cap Breakdown, layout 2-col do Cap Breakdown + cap-by-pos, distribuição de colunas da tabela de roster (alinhamento vertical entre posições), e restauração de ESPN/Projeção com paridade em ambas as telas.

**Implementado:**

**Camada D — ESPN + Projeção (restauração + paridade):**
- Macro `player_roster_row` ganha 2 células: `col-espn` (consome `player.espn_ref_value` formatado como `$X.X`) e `col-proj` (consome `player.projected_next_salary()` como `$X`).
- Renderizadas em **ambos contextos** (`team_detail` e `roster`) — paridade total.
- Headers ESPN + Proj 2026 em ambos templates.

**Camada C — distribuição e alinhamento de colunas:**
- `table-layout: fixed` em `.player-roster-table`.
- Nova macro `player_roster_colgroup(context)` em `_macros.html` renderiza `<colgroup>` compartilhado com `<col class="col-*">` para cada coluna. Invocada antes do `<thead>` em cada instância de tabela (6 posições × 2 telas = 12 invocações).
- CSS `col.col-* { width: Xpx }` — larguras explícitas garantem alinhamento cross-table (entre as 6 tabelas por posição) e cross-page (entre `/team/<id>` e `/`).
- `tabular-nums` também nos `<th>` das colunas numéricas (alinha visualmente com valores).
- `col-acq` ganha `overflow: hidden; text-overflow: ellipsis; white-space: nowrap` + macro adiciona `title="{{ player.acquisition_label }}"` para preservar info completa no hover.
- `td { overflow: hidden; text-overflow: ellipsis; white-space: nowrap }` global na tabela, com override `td.col-name { white-space: normal }` para permitir wrap do nome stacked.

**Camada A — densidade dos cards de Cap Breakdown:**
- Override **scoped** em `.cap-breakdown-stat .stat-num { font-size: 1.2rem }` (era 1.6rem) e `.cap-breakdown-stat .stat-label { font-size: .68rem }`.
- `.cap-breakdown-stat` padding reduzido de `.65rem .8rem` para `.4rem .55rem`.
- Grid minmax reduzido de 140px para 120px.
- Zero alteração em `.stat-num`/`.stat-label` globais (preservados para outros 4 templates consumidores: admin, espn_import, league, lottery_audit).

**Camada B — layout 2-col Cap Breakdown + cap-by-pos:**
- Wrapper novo `.team-detail-cap-layout` envolve `.cap-breakdown-grid` + `.cap-by-pos-table`.
- `display: grid; grid-template-columns: 1fr 360px` em desktop.
- `@media (max-width: 768px)` empilha vertical (1 col).
- `.team-detail-cap-layout .cap-by-pos-table { max-width: none }` permite tabela preencher sua coluna de 360px.

**Responsividade progressiva (@media atualizado):**
- < 640px: esconde `col-contract`, `col-acq`, `col-espn`, `col-proj` (inclui os 2 novos).
- < 414px: esconde também `col-dynasty`.
- Sempre visíveis: strip + foto + nome+NFL + salário + actions.

**Valores calibrados (documentados no devplan):**
- Colgroup widths calibrados por conteúdo real (72px salary, 90px contract, 96px dynasty, 68px ESPN, 78px proj, 128px acq, 84px actions). Total fixo 576px (team_detail) / 660px (roster); col-name flexível com o resto.
- Densidade: 1.2rem stat-num (redução 25% vs 1.6rem), 0.4/0.55rem padding (redução ~35%).

**Validação:**
- `salary_engine_test.py` 48/48.
- Smoke `GET /team/<id>`, `/`, `/admin`, `/player/<id>`, `/league`, `/offseason`, `/salary`: todos HTTP 200.
- `/team/<id>` tem 6 `<colgroup>` (1 por posição), col-espn TH, col-proj TH, wrapper `team-detail-cap-layout` presentes.
- `/` tem 6 `<colgroup>` dinâmicos por posição, col-espn/proj TH, `toggleIR` handler intocado.
- Grep de hex pos-color em classes prefixed novas UX4-b: 0 matches (strip e col usam apenas CSS vars canonizadas em UX4).
- Outras telas consumidoras de `.stat-num`/`.stat-label` (league, offseason, lottery_audit, espn_import, salary) renderizam sem mudança visual — override scoped não afeta.

**Observação metodológica (para futuros F1 de refatoração de UI):** a dinâmica que gerou UX4-b sugere regra nova potencial no DEV_METHODOLOGY — F1 de refatoração de UI deveria listar explicitamente "campos presentes hoje que não estão no design proposto", com parecer por item (remoção intencional / perda não-intencional / deslocamento). Especificação positiva por si só omite silenciosamente. → **Absorvida e generalizada em [[MAN-METH-REG]]** (10/06/2026), que consolida esta ocorrência com a premissa-de-fonte-falsa do DP1-F1 sob uma regra única, candidata a baseline do `DEV_METHODOLOGY.md`.

---

### UX4-c — Aperto Visual Final de /team/<id> e /
✅ **Concluído (24/04/2026)** — Prioridade **Média**

**Entregue:** 3 frentes coordenadas em 1 commit, seguindo a ordem da F1 (3 → 2 → 1).

**Frente 3 — Colgroup denso:** widths reduzidas em 7 colunas com base em auditoria do DB (n=280 active players):
- col-photo: 44 → 40
- col-salary: 72 → 56 (pior caso `$63` = 3 chars)
- col-contract: 90 → 72 + ellipsis defensivo com `title` attr na macro
- col-dynasty: 96 → 88 (pior caso `🪙 11.179`)
- col-espn: 68 → 58 (pior caso `$68.4`, tight mas dentro do limite em tabular-nums)
- col-proj: 78 → 56 (pior caso `$63`)
- col-acq: 128 → 108 (`Origem não registrada` 21 chars trunca com ellipsis + title)
- col-actions: 84 → 76 (`↑ Tirar IR` compacto)

Redução total fixa: 576→478px (team_detail, -17%); 660→554px (roster, -16%). `col-name` (auto) absorve ~100px extras de largura, beneficiando nomes longos e tags.

**Frente 2 — Compactação de `.pos-block`:** gap vertical entre grupos de posição reduzido:
- `.pos-block { margin-bottom: 1rem → .5rem }` (16→8px)
- `.pos-block-title { font-size: .9rem → .85rem; margin: .5rem 0 .35rem → .25rem 0 .2rem }`
- Gap efetivo: ~52px → ~36px por par de grupos (-30%). Em 6 posições (5 gaps), economia vertical de ~80px.

**Frente 1 — Status bar compacta + progress bar em `/team/<id>`:**
- Substituiu `cap-breakdown-grid` + `cap-by-pos-table` (layout 2-col de UX4-b) por `.team-status-bar` horizontal única.
- 11 elementos: Cap usado/total, Resto, Dynasty, Ativos, IR (+custo), divider vertical, 6 pos-chips (QB/RB/WR/TE/K/DEF).
- Pos-chips com strip de cor via `border-left-color: var(--pos-color-*)` — reuso canônico UX4, zero hex novo.
- **Progress bar nova:** 5px altura abaixo da status bar. Cores via semantic tokens do theme: `--green` (< 80%), `--yellow` (80-100%), `--red` (> 100%). Feature que não existia em `/team/<id>` antes — roster principal tinha via `.cap-bar` separado, agora detalhe de time ganha paralelo visual.
- Responsividade progressiva: `@media < 768px` esconde pos-chips inteiras; `@media < 414px` esconde também o detalhe `(custo)` do IR. Cap overview e progress bar sempre visíveis.

**Ganho agregado no header:** redução estimada de ~240px → ~65px (economia de ~175px verticais em `/team/<id>`). Empiricamente, muito mais densidade informacional em linha única que em cards dispersos.

**Zero mudanças no backend** (handler já fornecia todos os agregados — confirmado F1). **Zero macro/helper novo** (pos-chips são 6 invocações inline).

**Decisões delegadas:**
1. **col-espn 58px (tight)** e **col-actions 76px (tight)** — calibrados no limite do pior caso observado. Fallbacks se quebrarem visualmente: 62px e 84px respectivamente. Sem ajuste reservado agora; owner valida no uso real.
2. **Progress bar cores via theme vars** (`--green`, `--yellow`, `--red` já em `:root`) — zero hex novo introduzido no CSS.

**Validação:**
- `salary_engine_test.py` 48/48.
- Smoke HTTP 200 em 7 telas: `/team/<id>`, `/`, `/admin`, `/player/<id>`, `/league`, `/offseason`, `/salary`.
- `/team/<id>`: status bar renderiza (1 match), progress bar renderiza (2 matches — wrapper + fill), 6 pos-chips presentes, HTML antigo ausente (`cap-breakdown-grid`, `cap-by-pos-table`, `team-detail-cap-layout` todos 0 matches).
- Classe `progress-over` aplicada corretamente em time over-cap.
- Outras telas consumidoras de `.stat-num`/`.stat-label` globais renderizam sem mudança (override scoped removido implicitamente com HTML, mas as classes globais estão intocadas).
- Grep de hex de cor em UX4-c novo: 0 matches (tudo via CSS vars do theme / `--pos-color-*` canonizadas).

---

### UX4-d — Tabela Única de Roster com Pos Inline
✅ **Concluído (24/04/2026)** — Prioridade **Média**

**Entregue:** colapso estrutural 6 `<table>` → 1 tabela única em ambas as telas, com 6 decisões consolidadas pela F1.

**Implementado:**

1. **Macro `player_roster_row`** ganha 1ª `<td class="col-pos">` com pos-badge inline. Novo param `group_first` adiciona atributo `data-group-first` no `<tr>` quando é a 1ª row de um grupo de posição (usado pelo CSS para separador dashed).

2. **Macro `player_roster_colgroup`** ganha 1ª `<col class="col-pos">` (width 40px).

3. **Templates** substituem o loop externo por posição + wrapper (`pos-block` / `roster-section`) por **1 única `<table class="player-roster-table">`** com loop aninhado `{% for pos %}{% for p %}...{{ player_roster_row(..., group_first=loop.first) }}`. Linha `.roster-counts` no topo agrega contagem por posição.

4. **roster.html**: `ir-count-badge` legado absorvido na linha de counts (badge agregado `IR N` no final da linha, em `var(--red)`).

5. **CSS novo:** col-pos width 40px (centrada); 5 regras de cor de nome por posição (`.player-roster-table tr.pos-{QB,RB,WR,TE,DST/DEF} .player-name { color: var(--pos-color-*) }`); separador `.player-roster-table tr[data-group-first]:not(:first-child) > td { border-top: 1px dashed var(--border) }`; estilo `.roster-counts` (flex wrap, tabular-nums nos números).

**Decisões delegadas, tomadas:**

- **Localização dos counts: linha dedicada em ambas as telas.** Justificativa: coerência cross-tela, redundância com status bar em team_detail é aceitável (status bar mostra `$` por pos; linha de counts mostra `quantidade` por pos — info complementar, não duplicada). Alternativa (integrar na status bar só em team_detail) criaria divergência entre as 2 telas.

- **Fallback K aplicado a priori:** `tr.pos-K .player-name` deliberadamente omitida das 5 regras de cor. Justificativa: `var(--pos-color-k) = #94a3b8` (cinza-azulado) renderizaria o nome visualmente "apagado" em contraste com as 5 posições saturadas (roxo, verde, azul, laranja, ciano). K preserva cor `--text` default; pos-badge colorido já carrega a identidade visual. Decisão conservadora ante impossibilidade de validação empírica via CLI — se owner quiser a cor aplicada no K, remoção do fallback é 1 linha CSS.

**Colgroup atualizado:**
- col-pos: 40px (nova)
- Demais colunas: widths UX4-c preservadas (photo 40, salary 56, contract 72, dynasty 88, espn 58, proj 56, acq 108, actions 76)
- Total fixo: 478 → **518px** (team_detail, +40px) / 554 → **594px** (roster, +40px)
- col-name (auto) absorve os +40px

**Ordem das rows:** QB → RB → WR → TE → K → DEF preservada via loop aninhado (sem JS, sem ordenação clicável — feature futura fora de escopo).

**Economia vertical agregada estimada (6 posições, pós colapso):**
- Antes (UX4-c): 6 wrappers `pos-block`/`roster-section` + 6 `<h3>`/`<h2>` título externo + 6 `<thead>` = ~270-300px estruturais
- Depois (UX4-d): 1 linha de counts (~22px) + 1 `<thead>` único (~22px) + 5 separadores dashed 1px = ~49px
- **Economia: ~220-250px verticais** por tela de roster típica com 6 posições

**Validação:**
- `salary_engine_test.py` 48/48.
- Smoke HTTP 200 em 7 telas: `/team/<id>`, `/`, `/admin`, `/player/<id>`, `/league`, `/offseason`, `/salary`.
- `/team/<id>`: 1 `<table class="player-roster-table">`, 1 `.roster-counts`, 6 `data-group-first` (uma por posição), col-pos TH presente. Wrapper `pos-block` ausente (0 matches).
- `/`: idem; wrapper `roster-section` ausente (0 matches); `ir-count-badge` legado ausente (absorvido na linha de counts).
- Grep de novos hex de cor em classes UX4-d: 0 matches (tudo via CSS vars canonizadas em UX4).
- Convenção salário preservada: `.salary-cell` ainda em `var(--green)`, `.salary-high` em `var(--yellow)`.

---

### UX4-e — Remover Fundo Pintado das Rows por Posição
✅ **Concluído (24/04/2026)** — Prioridade **Média**

**Entregue:** override CSS scoped que neutraliza fundo pintado em `tr.pos-*` dentro de `.player-roster-table tbody`, sem tocar as regras genéricas `.pos-*` (preservadas para pos-badge em col-pos, counts, status bar). 1 bloco novo de CSS (~10 LOC), zero HTML/macro afetado.

**Descoberta durante implementação:** as regras `.pos-QB { background: rgba(...) }` (style.css:476-482) são **genéricas** — aplicam em **qualquer elemento** com classe `pos-QB`, incluindo:
1. `span.pos-badge` em col-pos (tabela row) — **precisa** do fundo
2. `span.pos-badge` em counts no topo, status bar pos-chips, cabeçalhos legados — **precisam** do fundo
3. `<tr class="pos-QB">` na tabela (row inteira) — **não deveria** ter fundo

Remover o background das regras genéricas afetaria (1), (2) e (3) simultaneamente → regressão visual em pos-badge. Solução correta: override scoped especificamente em `.player-roster-table tbody tr.pos-*`, preservando regras genéricas intactas.

**Preservar `.player-ir-row` e `.renewal-flag`:** essas rows têm backgrounds semânticos próprios (vermelho alpha para IR, amarelo alpha para ANO 4). `:not(.player-ir-row):not(.renewal-flag)` em cada seletor do override exclui essas rows do match — o background de status prevalece.

**Implementação:**

```css
.player-roster-table tbody tr.pos-QB:not(.player-ir-row):not(.renewal-flag),
.player-roster-table tbody tr.pos-RB:not(.player-ir-row):not(.renewal-flag),
.player-roster-table tbody tr.pos-WR:not(.player-ir-row):not(.renewal-flag),
.player-roster-table tbody tr.pos-TE:not(.player-ir-row):not(.renewal-flag),
.player-roster-table tbody tr.pos-K:not(.player-ir-row):not(.renewal-flag),
.player-roster-table tbody tr.pos-DST:not(.player-ir-row):not(.renewal-flag),
.player-roster-table tbody tr.pos-DEF:not(.player-ir-row):not(.renewal-flag) {
  background-color: transparent;
}
```

7 seletores (QB, RB, WR, TE, K, DST, DEF) — DST e DEF listados separadamente por já existirem como classes distintas no codebase.

**Decisão adjacente (não tomada):** row-hover já existe (`.player-roster-table tbody tr:hover { background: var(--bg3) }` do UX4), funciona normalmente pós-UX4-e — serve como separação sutil entre rows sem cor de posição. Nenhum ajuste adicional necessário.

**Preservado intacto:**
- Strip vertical colorido (`border-left-color: var(--pos-color-*)`) — UX4-b
- Cor no nome (`tr.pos-XX .player-name`) com fallback K — UX4-d
- Separador dashed entre grupos (`tr[data-group-first]`) — UX4-d
- Linha de counts (`.roster-counts`) — UX4-d
- Colgroup + col-pos (40px) — UX4-d
- Convenção salário (`--green`/`--yellow`) — UX1+UX4
- Pos-badge inline em col-pos com fundo via `.pos-XX` genérica — UX4-d
- Pos-chips em status bar com fundo próprio — UX4-c
- Pos-badge em roster-counts com fundo próprio — UX4-d

**Validação:**
- `salary_engine_test.py` 48/48.
- Smoke HTTP 200 em 7 telas: `/team/<id>`, `/`, `/admin`, `/player/<id>`, `/league`, `/offseason`, `/salary`.
- Grep `tr.pos-.*background:` dentro do contexto `.player-roster-table`: **0 matches** (validação atendida — o override usa `background-color: transparent`, grep literal do padrão "background:" retorna zero no contexto esperado).
- `.player-ir-row` e `.renewal-flag` backgrounds preservados por construção (via `:not()` excluindo do match).

**Zero regressão esperada em outras telas:** override é totalmente scoped em `.player-roster-table tbody tr.pos-*`. Pos-badge em qualquer outro contexto (col-pos da row, counts, status bar, cabeçalhos legados) preserva fundo.

---

### UX7 — Tema Visual Global Mais Claro (Recalibragem da Paleta Dark)
✅ **Concluído (24/04/2026)** — Prioridade **Média**

**Entregue:** clareamento uniforme de +3pp em 6 tokens de fundo/borda em `:root` (Opção A aprovada pelo owner após comparar mocks das opções A e B). Matiz 218° preservado; saturação ~30% preservada; hierarquia entre superfícies mantida (mesmo delta entre tokens). `--text-dim` intocado (Opção A não requer). Zero outra mudança.

**Mudança em `static/style.css` (`:root`):**

| Token | Hex antigo | Hex novo | Camada |
|---|---|---|---|
| `--bg` | `#0d1117` (L7%) | `#161c28` (L10%) | fundo base |
| `--bg2` | `#161b27` (L12%) | `#1b2436` (L15%) | surface |
| `--bg3` | `#1e2736` (L16%) | `#243049` (L19%) | hover / tabs |
| `--bg4` | `#243044` (L20%) | `#2c3a51` (L23%) | hover++ |
| `--border` | `#2c3a52` (L25%) | `#364864` (L28%) | bordas |
| `--border2` | `#384d6b` (L32%) | `#485c7a` (L35%) | bordas acentuadas |

**Preservado intacto:**
- `--text` (L90%), `--text-dim` (L54%), `--text-muted` (L33%)
- Tokens semantic: `--green`, `--yellow`, `--red`, `--accent`, `--purple`, `--orange`, `--cyan`
- `--pos-color-*` canonizadas (UX4)
- Estados destacados: `.player-ir-row` (vermelho alpha), `.renewal-flag` (amarelo alpha)
- Strip vertical + cor no nome por posição (UX4-b, UX4-d)
- Override de fundo em rows (UX4-e)
- Todos os consumidores via `var(--*)` — mudança em `:root` propaga automaticamente

**Referências:** diagnose `MAN-UX7-F1`, commit UX7-REG `45998c7`.

**Cross-ecossistema:** nota **adicionada localmente** em `fantasy_optimizer/CLAUDE.md` registrando que o Manager clareou paleta (Opção A, +3pp, commit `4af9144`) e indicando que Optimizer mantém paleta original por ora. **Commit pendente com o owner** — o repo do Optimizer tem edits locais pré-existentes não-relacionados ao UX7 (path fix de `DEV_METHODOLOGY.md`, bloco "Pick Valuation" no `CLAUDE.md`, `optimizer_improvements.md` modificado, `DEV_METHODOLOGY.md` deletado localmente). Commit agregado unilateral misturaria contextos; owner decide quando e como commitar (agregado ou separado da nota UX7). Predictor **intocado**. Pendência delimitada, sem bloqueio para Manager.

**Validação:**
- `salary_engine_test.py` 48/48.
- Smoke HTTP 200 em **13 telas**: `/team/<id>`, `/`, `/trades`, `/admin`, `/offseason`, `/player/<id>`, `/salary_history`, `/cap_projector`, `/league`, `/picks`, `/auction`, `/admin/users`, `/salary`.
- Grep dos 6 hex antigos em `style.css`: **0 matches** (substituídos integralmente).
- Grep dos 6 hex novos em `style.css`: 1 ocorrência cada (só em `:root`; consumidores usam `var()`).

**Validação empírica visual:** não executada via CLI (fora das capacidades do ambiente). **Fica pendente pelo owner no uso real.** Checklist para auditar (per F1): texto principal legível em todas as surfaces; hierarquia fundo < surface < hover perceptível; `.player-ir-row` e `.renewal-flag` ainda transmitindo estado (aviso F1: `.renewal-flag` alpha 5% já era marginal, vai ficar mais sutil pós-UX7 — aceito como débito delimitado, item futuro se virar dor); cores semantic não destoando; `--text-dim` legível sobre bg/bg2/bg3 (falha AA em bg4 é regressão pré-existente, não introduzida aqui).

**Débito delimitado observado** (aceito, item futuro se virar dor):
- `.renewal-flag` (alpha 5%) fica marginalmente mais sutil sobre fundo clareado. F1 já sinalizou; owner aceita; ajuste possível = aumentar alpha para 8-10% em item separado se sinal visual ficar fraco no uso real.
- `--text-dim` sobre `--bg4`: continua falhando WCAG AA small (3.5:1 < 4.5). Regressão pré-existente de antes do UX7 — não introduzida aqui.

**Se futuramente escalar para Opção B (+5pp):** `--text-dim` precisaria subir para L58 (`#8098b5`) para preservar contraste. Não tocado agora.

---

### DATA-1 — Badges TRADE e REVISÃO Removidos de Listagens de Roster
✅ **Concluído (24/04/2026)** — Prioridade **Média**

**Reformulação UX:** a investigação read-only sobre `Player.via_trade` confirmou semântica vitalícia por omissão (campo setado por `_sync_trades` em `sync_sleeper.py:529`, nunca resetado automaticamente). A conversa sobre casos de uso de `/team/<id>` (olhando roster alheio) reformulou a pergunta primária: **"essa info deveria aparecer em tela de listagem?"** Resposta: listagem mostra estado atual; timeline de `/player/<id>` mostra história (fonte canônica); contexto admin mostra tarefas operacionais. Badge TRADE numa listagem duplica info que pertence à timeline; badge REVISÃO em roster alheio é info admin-interna irrelevante para owner não-admin. Remover ambos resolve o problema na raiz sem tocar nos campos do modelo.

**Entregue:**

- **Template `_macros.html`** (macro `player_roster_row`): removidas 2 linhas que renderizavam `{% if player.via_trade %}TRADE{% endif %}` e `{% if player.needs_review %}REVISÃO{% endif %}`. Afeta ambos contextos (`/team/<id>` e `/`) por construção. Outros badges da célula `name-main` (IR, ANO 4) preservados.

- **Modelo intocado:** `Player.via_trade` e `Player.needs_review` continuam sendo setados por `_sync_trades` (sync de trade do Sleeper) e sync de player novo (match CSV). Continuam editáveis via `PATCH /api/player/<id>`. Continuam consumidos em rebuild de history em `routes/admin.py`.

- **CSS preservado:** classes `.tag-trade` e `.tag-review` mantidas — ambas ainda consumidas em múltiplos contextos legítimos:
  - `.tag-trade` em `auction.html` (entry_type fa_auction), `offseason.html` (source lottery), `player_detail.html` + `salary_history.html` (EVENT_LABELS para trade/fa_waiver/fa_auction/free_agent).
  - `.tag-review` em `cap_projector.html` (needs_review JS), `roster.html` (banner alert), `player_detail.html` (IR/Dropado + drop/commissioner/salary_correction/cut EVENT_LABELS), `salary_history.html` (mesmos EVENT_LABELS).

- **Fora de escopo (preservado):** banner de alerta `roster.html:85` (lista agregada de `needs_review` como link linkificado), `cap_projector.html:114` (badge REVISÃO em projeção — listagem diferente, fora do escopo "macro de roster").

**Validação:**
- `salary_engine_test.py` 48/48.
- Smoke `GET /team/<id>`, `/`, `/admin`, `/player/<id>`: todos HTTP 200.
- Grep de `class="tag tag-trade">TRADE` e `class="tag tag-review">REVISÃO` nos HTMLs de `/team/<id>` e `/`: 0 matches em cada. Badge IR continua presente (contagem > 0).
- `/player/<id>`: `tag-trade` continua presente no HTML (EVENT_LABELS JS intocado). Timeline preservada.
- Grep `via_trade` em `templates/_macros.html`: 0 matches. Mesmo para `needs_review`.
- Grep `via_trade` no codebase total: ocorrências apenas em `models.py`, `sync_sleeper.py`, `routes/admin.py`, `routes/roster.py` (PATCH endpoint). Zero em templates de listagem.

**Ganho:** telas de listagem ficam mais limpas visualmente (sem badges históricos acumulados). Mental model claro: estado atual aqui, história lá. Campos persistem vitalícios no modelo, mas agora sem consumidor UI visual em listagem — deixa de ser dor.

**Débito reduzido (não criado):** o problema original "via_trade vitalício por omissão" deixa de ser urgente. Se algum futuro caso de uso pedir "players tradados recentemente", implementar via query filtrada em `PlayerHistory` por `event_type='trade' AND season=corrente`, sem depender do campo boolean.

---

### T3 — Valores redraft do FantasyCalc no Trade Manager
✅ **Concluído (27/04/2026)** — Prioridade **Média**

**Briefing originado em chat do Optimizer (27/04/2026)** durante análise da trade real D'Andre Swift × RJ Harvey, que demonstrou que a escolha entre dynasty e redraft pode inverter o veredicto da trade (Harvey +189 dynasty / Swift +265 redraft — flip de 454 pontos). Item registrado em formato REG primeiro, depois implementado no mesmo dia após F1 conclusiva.

**Diagnose F1 (MAN-T3-F1, 27/04/2026):** três descobertas reduziram o escopo de F2 em ~50%:
1. Endpoint `isDynasty=true` do FantasyCalc **já retorna `redraftValue`** ao lado de `value` em cada entry — sem fetch separado, sem cache paralelo, sem refator de TTL.
2. Picks têm `redraftValue=0` explícito (12/12 PICK entries verificadas) — degradação elegante natural sem marcador "n/a".
3. Barra dynasty existente em `style.css:1198-1221` é **centro-zero** com fills `max-width: 50%`, estrutura ideal pra clonar.

**Modelo escolhido em planejamento (27/04/2026):** duas barras independentes paralelas (dynasty + redraft), escala separada, totais nos labels da própria barra. Owner confirmou 5 decisões de design: paleta dynasty mais clara para redraft, naming `redraft_value` snake_case, helper `get_dynasty_values` mantido por retro-compat, totais nos labels (sem rodapé extra), implementação imediata.

**Implementado:**

- **Backend extensão (`dynasty_values.py`):** `_build_map_from_raw` agora captura `redraft_value` em cada entry do mesmo cache (single fetch, single file). Helper novo `resolve_asset_redraft_value(values_map, sid)` paralelo a `resolve_asset_value` — picks retornam 0 sempre. Helper público `get_dynasty_values()` preservado (zero refs externas mexidas, retro-compat com T2/T2-FIX/T2-FIX-2/M1); docstring atualizada explicitando que retorna ambas dimensões.

- **Routes (`routes/trades.py`):** `_player_asset_dict` propaga `redraft_value`; `_pick_asset_dict` força `redraft_value=0`. `_compute_cap_impact` calcula bloco paralelo `redraft_total_out`/`redraft_total_in`/`redraft_delta` por side. Endpoint `/api/dynasty_values` ganha mapa paralelo `redraft_values: {sid: int}` (consumidores legacy ignoram). `/api/picks` em `routes/picks.py` extension com `redraft_value=0` por pick.

- **Frontend (`templates/trades.html`):** novo `<div id="redraft-bar-section">` clonado do `dynasty-bar-section` (IDs `rdft-*`), stacked verticalmente logo abaixo da dynasty bar. Função JS `updateRedraftBar()` paralela a `updateDynastyBar()` — same gramática (centro-zero, max-width 50%, chip de delta com cor neutral/win-a/win-b), escala separada (max próprio dos dois totais redraft). `loadDynastyValues` carrega `redraftMap` paralelo a `dynastyMap`. `toggleAsset` chama ambos updaters.

- **Read-only proposal (`templates/trade_proposal.html`):** dynasty bar nunca foi portada pra proposal por T2 — em vez de inflar o escopo de T3, adicionadas linhas compactas Jinja-formatted "🪙 Dynasty: envia X · recebe Y · Δ Z" e "⚡ Redraft: envia X · recebe Y · Δ Z" por side, no mesmo estilo `cap-mini`. Visualizadores externos da proposta veem ambas dimensões sem custo de markup.

- **CSS (`static/style.css`):** classes `.redraft-bar-*` espelhando `.dynasty-bar-*` com paleta lighter — dynasty A `#6ea8fe`/`#4d8df0` → redraft A `#a3c4ff`/`#7eaaf5`; dynasty B `#ff8f6b`/`#e86a3a` → redraft B `#ffb8a0`/`#f29670`. "Irmã caçula" visualmente identificável como variante da dynasty bar.

**Validação (27/04/2026, smoke transitório `scripts/t3_smoke.py` deletado pós-execução):**
- 7 cenários: cache traz `redraft_value` por entry incluindo picks com 0; `resolve_asset_redraft_value` retorna inteiro pra player; `_player_asset_dict`/`_pick_asset_dict`/`_compute_cap_impact` propagam novos campos; endpoint `/api/dynasty_values` expõe `redraft_values` map; endpoint `/api/picks` retorna `redraft_value=0` por pick; `/trades` renderiza markup das 2 barras com IDs `redraft-bar-section`, `rdft-fill-a`, função `updateRedraftBar()`.
- `salary_engine_test.py` 48/48.
- Smoke validou lógica e payload — **validação visual (cores, alinhamento das 2 barras, comportamento mobile) fica pendente do owner em desktop**. Implementação foi feita em sessão mobile remote control (auto mode), risco visual residual aceito antecipadamente. Owner ajusta pixel se algo destoar pós-deploy.

**Não alterado:**
- Helper `get_dynasty_values()` (nome mantido, escopo expandido via docstring).
- Schema do `Player` ou `Pick` — `redraft_value` é puro runtime no payload.
- Idempotência do cache TTL 24h (single fetch retorna ambos os calculadores).
- Search/autocomplete/ranking interno do Manager (continuam usando dynasty).
- PlayerHistory e qualquer persistência histórica de redraft (fora de escopo, conforme T3-REG).

**Observação:** ordem de inserção do registro REG → F1 → F2 aconteceu na MESMA sessão (27/04/2026). Caso de uso onde a discussão do Claude.ai forneceu rationale completo + F1 confirmou que o trabalho era menor que esperado + decisões fechadas pela owner em 5 trocas curtas via mobile. F2 implementação executada autonomamente em auto mode.

---

### MAN-S1-FIX — Backfill de previous_league_id reverte estado pós-trades da current league
✅ **Resolvido 28/04/2026** — Prioridade **Alta**

**Bug confirmado em auditoria local 27/04/2026** durante diagnose de divergência local↔prod (active_salary local=$239 vs prod=$255 em Cangaceiros). Detectado via análise da ordem de inserção das Trade rows e comparação com PlayerHistory canônico.

**Mecanismo:**
- `POST /api/admin/sync_trades/backfill` (`routes/admin.py:305-329`) chama `_sync_trades(previous_league_id)` para importar trades da temporada anterior.
- `_sync_trades` em `sync_sleeper.py:495+` aplica `player.team_id = dst_team.id` + `player.fantasy_team = dst_team.name` cegamente para cada trade processada — não verifica se uma trade subsequente já moveu o player.
- Idempotência usa `Trade.query.filter_by(sleeper_transaction_id=tx_id)` em **toda a tabela `trades`** — Trade rows de 2024 e 2025 vivem na mesma tabela. `_sync_trades(LEAGUE_ID=current)` em runs futuros vê Trade rows já existentes e skipa, sem re-mover players.
- **Resultado:** rodar backfill de previous league **DEPOIS** que a current league já foi sincronizada **destrói o estado atual** dos players envolvidos em trades cross-season. Sem caminho automático de recuperação — sync subsequente reporta `updated=0` mesmo com players claramente fora de lugar.

**Sintomas observados (local DB, 27/04/2026):**
- 6 players em Cangaceiros local que deveriam estar em outros times: Tank Dell, Emanuel Wilson, Chase Brown, Rico Dowdle (drops/trades 2025 não aplicadas) + Jaydon Blue, RJ Harvey (vieram via trades 2025 mas state diverge).
- `Player.updated_at` desses 6 = `2026-04-22 19:41:57` — coincide com inserção das Trade rows id 30-47 (todas de 2024-09 a 2024-11).
- Trade rows ordering confirma: id 1-29 são 2025 (sync da current league), id 30-47 são 2024 (backfill rodou DEPOIS).
- 4 SyncLogs subsequentes (até 02/04/2026) reportaram `updated=0` — idempotência impediu correção.
- Owner não lembra de ter clicado o botão "Importar Trades Históricas" em `/admin` — disparo pode ter sido acidental, automação de teste, outro admin, ou ação esquecida. Reforça necessidade de fix arquitetural (não só "não clicar").

**Mecanismo de fix candidato (a ser refinado em F1):**
- (a) Comparar `current_season` vs `trade.season`: rejeitar movimentação `Player.team_id` quando a trade processada é de uma season anterior à atual — cria apenas Trade row + PlayerHistory event, não move asset.
- (b) Idempotência composta: `(sleeper_transaction_id, league_id)` em vez de só `tx_id` — permitiria re-processar trades em runs subsequentes para corrigir estado.
- (c) Modo "force re-apply" ao chamar `_sync_trades` para current league — ignora idempotência e re-aplica movimentações na ordem cronológica das trades.
- (d) Validação prévia: antes de mover `player.team_id`, checar se existe trade subsequente do mesmo player que já o moveu para outro time (lookup em PlayerHistory).

F1 deve avaliar trade-offs (idempotência preservada vs poder de recovery) e cobertura cross-season (regular + offseason rollover). Provavelmente combinação de (a) + (d) é mais segura.

**Recovery do estado local atual (a discutir em F1 ou ação imediata):**
- (i) **Snapshot prod → local:** se Render expõe download do `dynasty.db` da persistent disk, é o caminho mais limpo. Se não, custa criar endpoint admin tipo `GET /admin/db_snapshot` ou rota temporária.
- (ii) **Re-aplicar trades 2025 manualmente via SQL:** scripted patch baseado nas Trade rows id 1-29 já presentes — para cada trade 2025, re-aplicar movimento. Determinístico, ~50 linhas Python, mas não generalizável.
- (iii) **Hack temporário:** rodar `_sync_trades(LEAGUE_ID)` com modo "force" (ignorando idempotência) uma vez. Bate-pronto se F1 implementar opção (c) primeiro.

**Cobertura prod vs local:**
- Prod (Render) provavelmente NÃO tem o problema atualmente — se o botão de backfill foi clicado lá, foi antes da sync da current league processar trades 2025 (ordem segura), OU nunca foi clicado.
- M1 não é afetado em prod — só local mostra cap incorreto. Prod calcula `team_rel.active_salary()` sobre roster real e deveria mostrar `$55 acima` corretamente quando offseason_mode ativar.
- **Risco residual em prod:** se algum admin clicar o botão futuro mente, o bug se manifesta. Fix arquitetural protege.

**Não fazer no F1:**
- Não propor implementação imediata — F1 é diagnose das opções (a/b/c/d) e do recovery.
- Não tocar dynasty.db local antes de decisão sobre recovery.
- Não remover botão "Importar Trades Históricas" — funcionalidade legítima quando rodada na ordem certa; fix protege contra ordem errada.

**Disparo da auditoria:** sessão de validação de M1 em 27/04/2026 detectou `team_admin.active_salary()=$239` localmente, dissonante do `$255` reportado pelo owner em prod. Investigação cascateou de "stale player" → "PlayerHistory canônico vs Player row stale" → "padrão F8" → "Trade rows ordering" → bug arquitetural de `_sync_trades` cross-season.

**Fase 1 Diagnose ✅ 28/04/2026**

**Mecanismo confirmado contra dados reais.** Auditoria SQL local confirmou: 47 Trade rows (id 1-29 = 2025 created 14:49, id 30-47 = 2024 created 18:26 = backfill +3.5h). `Player.updated_at` dos 6 stale = `2026-04-22 19:41:57` coincide com Trade rows 2024. Idempotência por `sleeper_transaction_id` UNIQUE global é o gatilho da impossibilidade de auto-cura. 0 duplicatas de tx_id, 0 tx_ids compartilhados entre as 2 leagues — ambos esperados.

**Achado crítico que altera escopo:** apenas **4 dos 6 players** citados são genuinamente stale. Jaydon Blue e RJ Harvey ESTÃO corretos em Cangaceiros — vieram via trades 2025 (rookies); o `via_trade=True` + `updated_at=22/04 19:41:57` deles é da sync legítima da current league. Diff $239 vs $255 ($16) é compatível com 4 stale, não 6.

**Mecanismo por player:**

| Player | Estado real | Stale? | run_sync corrige? |
|---|---|---|---|
| Tank Dell | dropado (PH 984 `drop` Cang 2025) | sim | **NÃO** (sync_sleeper.py:286-291 só seta `is_dropped`) |
| Emanuel Wilson | em ESPN FL (PH 571 `trade` 2025) | sim | **SIM** (linhas 251-254 com guard `!=`) |
| Chase Brown | em Pitbull (PH 565 `trade` 2025) | sim | **SIM** |
| Rico Dowdle | em rafaelferreirap (PH 1104 `fa_auction` 2025) ou dropado | sim | **PROVAVELMENTE SIM** se ainda em roster |
| Jaydon Blue | em Cangaceiros | **NÃO** (correto) | N/A |
| RJ Harvey | em Cangaceiros | **NÃO** (correto) | N/A |

**Réplicas de mutação `Player.team_id` (mapeamento completo):**

| Local | Bug? | Justificativa |
|---|---|---|
| `sync_sleeper.py:251-254` (run_sync alignment) | NÃO | Guard `if p.team_id != team.id`. Sleeper authoritative. **É parte do recovery natural.** |
| `sync_sleeper.py:267` (run_sync new player) | NÃO | Só na criação; `sleeper_player_id` UNIQUE. |
| `sync_sleeper.py:286-291` (drop logic) | NÃO | Só seta `is_dropped`, não muta `team_id`. (Mas explica por que Tank/Rico não são auto-curáveis.) |
| `sync_sleeper.py:561-562` (`_sync_trades`) | **SIM** | O bug. |
| `sync_sleeper.py:909` (F8a `_rebuild_player_history`) | **HERDADO** | Itera `_walk_league_chain(LEAGUE_ID)` e chama `_sync_trades(lid)` por liga — herda o bug se chain inclui current+previous sem Trade rows pré-existentes. |
| `routes/auction.py:320-321` (auction manual) | NÃO | Mutação humana autoritativa, fora do escopo cross-season. |
| `import_csv.py:50` (CSV import) | NÃO | "Preserves team_id from Sleeper" — só cria novos sem time. |
| `routes/offseason.py:629-673` (rollover) | NÃO | Não toca `team_id`. |

**Trade-offs das 4 fixes (a/b/c/d):**

| | Esforço | Risco regressão | Recovery automático | Cobertura cross-season + F8a |
|---|---|---|---|---|
| **(a)** reject move se `trade.season < season-da-liga` | **baixo** (~10-15 LoC, sem migration) | **baixíssimo** | não (preventivo) | **forte** |
| (b) idempotência composta `(tx_id, league_id)` | médio (migration ALTER + drop/recreate UNIQUE) | médio | não cura mutação cega | parcial |
| (c) `force_re_apply` mode | médio (~25 LoC) | médio-alto (force ignora guard) | sim (= recovery iii) | parcial |
| (d) lookup PH subsequente | médio-alto (~40 LoC) | alto (heurístico ordering) | não | forte |

**Trade-offs das recoveries (i/ii/iii) + (iv) descoberta em F1:**

| | Esforço | Determinístico | Aplicabilidade aos 4 stale | Dependência |
|---|---|---|---|---|
| (i) snapshot prod→local | médio-alto (CLI Render ou endpoint admin novo) | sim (se prod limpo) | 4/4 | nenhuma |
| (ii) SQL re-aplicar trades 2025 | baixo (~30 linhas) | sim | 2/4 (Tank/Rico sem trade 2025) | nenhuma |
| (iii) `force_re_apply` | trivial após (c) | sim, ordem cronológica | 2/4 (idem) | requer fix (c) |
| **(iv) `run_sync()` puro** | **mínimo** (1 clique) | parcial (depende roster Sleeper vivo) | 2/4 (Chase/Emanuel via guard); 2 órfãos via path 286-291 | nenhuma |

**Idempotência (resposta direta):** `sleeper_transaction_id` é UNIQUE global na tabela `trades` (`models.py:385-395`, index `uq_trades_sleeper_tx`); filtro de existência (`sync_sleeper.py:532`) cobre **todas as leagues** indiscriminadamente. Tabela não tem `season` nem `league_id`. Tx_ids compartilhados entre as 2 leagues: 0 (esperado).

**Cobertura cross-season:** rollover (`routes/offseason.py:629-673`) não toca `team_id` — imune ao bug raiz. Interação patológica: após rollover, `current_season=2026`, e `_sync_trades:519` (`season = get_current_season()`) graveria `PlayerHistory.season=2026` mesmo para trades de 2024 — agrava o problema. Fix (a) deve usar `season-da-liga-processada` (derivada do `_get(/league/{lid}).season`), **não** `get_current_season()`. Linha 519 é parte do bug raiz, não acessório.

**Risco em prod (latente vs manifesto):** inconclusivo via endpoint público (todas rotas exigem `@login_required`). Hipótese: prod provavelmente latente, não manifesto. Owner valida manualmente em `/team/5` antes do F2 (decisão sobre criar `/api/admin/diag/stale_players` fica para o prompt do F2 — provavelmente desnecessário se 1 visita manual basta).

**Recomendação final:** fix **(a)** + recovery **(iv)** + UPDATE one-shot targeted (Tank Dell + Rico Dowdle). Fix (a) é a menor superfície de regressão; cobre F8a e rollover inerentemente; deve corrigir simultaneamente a linha 519 (gravar `PlayerHistory.season` como `season-da-liga-processada`). Recovery (iv) cura 2/4 (Chase Brown, Emanuel Wilson) sem código novo via guard das linhas 251-254. UPDATE one-shot cura os 2 dropados (`team_id=NULL` + `is_dropped=True`, ou aponta para roster atual no Sleeper se ainda existir). Não escolher (b)/(c)/(d) (cosmético, perigoso ou frágil), nem (i)/(ii)/(iii) (overkill, frágil para Tank/Rico, ou bloqueado por fix).

**Surpresas relevantes para F2:**
- Escopo de recovery menor: 4 stale (não 6).
- F8a (`sync_sleeper.py:909`) é caminho indireto do mesmo bug — F2 precisa cobrir e validar.
- Linha 519 (`season = get_current_season()`) é parte do bug raiz — fix (a) deve cobrir.
- PH rows 2024 (4 rows criadas em 22/04 19:42:31-32) são **factualmente corretas** (em 2024 esses players foram tradados para Cangaceiros) — preservar como histórico canônico, sem expurgo.
- Cosmético opcional: botão "Importar Trades Históricas" fica seguro pós-fix mas confuso semanticamente. Owner registra item separado pós-F2 se decidir tratar.

**Pendências de input do owner antes de F2:**
1. Validar manualmente cobertura prod (4 stale também?) — owner faz via `/team/5`. Sem necessidade de endpoint diagnóstico se 1 visita basta.
2. Confirmar estado Sleeper atual de Tank Dell e Rico Dowdle (ainda dropped?) — owner consulta no Sleeper. Determina target do UPDATE one-shot.
3. Preservar PH 2024 — confirmado.
4. Cosmético do botão de backfill — fora do escopo do F2; eventual item separado pós-F2.

**Fase 2 Implementação ✅ 28/04/2026**

**Validação manual de prod feita pelo owner antes do F2:** prod (Render) está limpo — nenhum dos 4 stale aparece em Cangaceiros lá. Sem migration de prod necessária. Owner também confirmou que os 4 stale têm rosters Sleeper ativos (Chase Brown→Pitbull, Emanuel Wilson→ESPN FL, Tank Dell→rafadgil, Rico Dowdle→rafaelferreirap), tornando recovery via `run_sync()` viável para todos os 4 — UPDATE one-shot tornou-se desnecessário.

**Mudanças aplicadas (apenas guard lógico, zero schema):**
- `sync_sleeper.py:495+` — assinatura de `_sync_trades` ganhou parâmetro opcional `league_season: int | None = None`. Se não passada, é derivada uma única vez via `_get(/league/{league_id}).season`. Variável local `is_previous_season = (league_season < current_season)` calculada antes do loop de trades.
- `sync_sleeper.py:587-600` — mutação de `Player.team_id`/`fantasy_team`/`is_my_team`/`via_trade` envolvida em `if not is_previous_season:`. Trade row + PlayerHistory event continuam sendo gravados incondicionalmente (preserva histórico canônico). `affected_team_ids` (cap recompute) também só atualiza dentro do guard — trade cross-season não muda cap atual.
- `sync_sleeper.py:604-612` — `season=season` (que era `get_current_season()`) trocado por `season=league_season` no INSERT de `PlayerHistory`. PH agora reflete a season da liga sendo processada, não a current global.
- `routes/admin.py:323-329` — `sync_trades_backfill()` passa `league_season=int(prev_data["season"])` evitando I/O redundante (payload já estava em escopo).
- `sync_sleeper.py:909-915` — F8a `_rebuild_player_history` passa `league_season=int(league.get("season"))` ao iterar pela chain. Cobre o caminho indireto.
- `sync_sleeper.py:307` — `run_sync()` chama `_sync_trades(LEAGUE_ID)` sem `league_season` (deriva internamente). Aceitável pelo overhead trivial.

**Resultado dos 6 cenários de validação:**

1. **Backfill cross-season com guard ativo** ✅ — em DB de cópia, deletadas as 29 Trade rows da liga `previous_league_id` e PH correspondentes; chamado `_sync_trades(prev_id, league_season=2024)` (forçando guard ativo, `2024 < 2025`). Resultado: `imported=29` Trade rows criadas + 78 PH novas, **zero mutações de team_id** dos 4 stale.

2. **F8a (caminho indireto)** ✅ — coberto pela mesma função; lógica idêntica. F8a passa `league_season` explicitamente após mudança em `sync_sleeper.py:909-915`.

3. **PlayerHistory.season correto** ✅ — todas as 78 PH novas do Cenário 1 gravadas com `season=2024` (= season da liga processada), zero com `season=current_season`.

4. **Recovery dos 4 stale via run_sync** ✅ — rodado no DB local real após fix:
   - Tank Dell: team_id=5 (Cangaceiros) → team_id=1 (Pitbull do Samba / owner rafadgil) ✓
   - Emanuel Wilson: team_id=5 → team_id=12 (ESPN FANTASY LEAGUE) ✓
   - Chase Brown: team_id=5 → team_id=1 (Pitbull do Samba) ✓
   - Rico Dowdle: team_id=5 → team_id=11 (rafaelferreirap) ✓
   - Jaydon Blue, RJ Harvey: permaneceram em Cangaceiros (corretos, conforme F1)
   - **Cangaceiros active_salary: $239 → $255** (bate com prod) ✓

5. **Idempotência** ✅ — segunda passada de `run_sync()`: `players_updated=0`. Backfill de teste rodado 2x: segunda passada `imported=0 skipped=29`, zero mutações.

6. **Regressão zero** ✅ — `salary_engine_test.py` 48/48. Smoke endpoints HTTP não rodado em sessão (recovery via REPL com app context é equivalente — exercitou bootstrap completo, models, sync, salary calc).

**Surpresas/decisões durante implementação:**
- Sleeper avançou a season da liga entre 22/04 e 28/04: `LEAGUE_ID` agora retorna `season=2026`, `previous_league_id` retorna `season=2025`. AppConfig local ainda em `current_season=2025`. Significa que o cenário do bug *natural* não é reproduzível sem forçar `league_season` explicitamente. Não afeta o fix — apenas a estratégia de teste (forçar via parâmetro).
- (Nota de leitura: "rafadgil" no prompt do F2 é o owner do time "Pitbull do Samba" — não há discrepância nos 4 destinos.)
- Cangaceiros roster: 25 → 23 jogadores pós-recovery (4 saíram, 2 corretos ficaram = 21; 23 finais sugere que outros 2 players além dos 4 stale foram reclassificados pelo run_sync via roster alignment ou drop logic — coerente com sync rotineiro, não falha).

**Commit:** mudanças em `sync_sleeper.py`, `routes/admin.py`, `improvements.md`, `manager_devplan.md`. Render auto-deploy via push origin/main.

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

---

### F11 — Rollover de season duplicado e divergente (admin × offseason)
✅ **12/06/2026** (prod verificado limpo + fix Opção A + smoke de prod OK) —
registrado 11/06/2026, achado AUD1 Lente 2 — Prioridade **Alta**

**Evidência:** dois endpoints aplicam o rollover, ambos vivos na UI: (1) `/api/admin/rollover/apply`
(routes/admin.py:89-130; botão "⚡ Aplicar Rollover" em admin.html:285) e (2) `/api/offseason/rollover`
(routes/offseason.py:653-697; Step 4 do workflow, offseason.html:724). Divergências do lado admin:
**sem gate de etapas** (offseason exige steps 2+3), **sem check `rollover_done`** (re-execução livre),
**não avança `current_season`** nem seta flags — grava SalaryHistory com `season=next_season` deixando
a config da season para trás (estado inconsistente). Comentário stale em admin.py:122-123 afirma
"CURRENT_SEASON in models is a constant — in production you'd persist this in a Settings table",
contradito pelo código atual (`AppConfig.current_season` + `set_config`, usados pelo fluxo offseason).
**Risco:** rodar o rollover do admin após o do offseason (ou 2× o do admin) **incrementa contratos e
salários duas vezes** — corrupção em massa de dados calculados, sem reversão fácil.
**Parecer:** item novo. Proposta: matar a réplica (admin delega ao endpoint canônico do offseason, ou
remove o botão), à la T2-FIX-2/"1 fonte por caminho de escrita". F1 dispensável — diagnose acima já
cobre causa e evidência; F2 direto.

**Etapa 1 — verificação retroativa em prod (12/06/2026): VEREDITO LIMPO.** Queries read-only
executadas pelo owner no Render Shell contra `/data/dynasty.db` (`sqlite3 -readonly`). Números:
**`salary_history` = 0 linhas** (nenhum rollover jamais aplicado em prod — contratos vivos vieram do
CSV bootstrap, que não gera history; classe F12); **0 lotes** de rollover por season (Q2 vazia);
**0 duplicatas** (player, season) com regra de rollover (Q3); **0 assinaturas** `"Season rollover"` no
`sync_log` (Q4 — o botão admin **nunca foi usado**; assinatura exclusiva do caminho admin, que gravava
SyncLog; o offseason não grava); **0 players** ativos com contract_year fora de 1..4 (Q5); config
consistente: `current_season=2025`, `rollover_done=false`, `season_locked=true` — offseason 2026 em
andamento, rollover legitimamente pendente no Step 4. **Sem corrupção; janela de risco estava aberta**
(1º rollover da história da liga é iminente) — fix urgente, repair desnecessário.

**Etapa 2 — fix Opção A (12/06/2026, ⚠️ localhost):** removidos o endpoint `POST /api/admin/rollover/apply`
(routes/admin.py — substituído por comentário-guard apontando a porta única), o botão "⚡ Aplicar
Rollover" + `confirmRollover()` + `#rollover-result` (admin.html), e o comentário stale (vivia dentro
do endpoint removido). **Preview mantido** (`GET /api/admin/rollover/preview` + card "Season Rollover
(preview)"): read-only, usa só a função pura `apply_season_rollover`, zero dependência do caminho
removido; card e step-list do admin agora apontam o apply para o workflow do Offseason (Step 4).
Offseason intocado (gates/flags/semântica idênticos — git diff não toca offseason.py/offseason.html).
**Validação:** grep pós-fix = exatamente 1 caminho de escrita (offseason.py:675-683; models.py:396 é
record_acquisition ano-1, admin.py:882 é edição per-player M2); 0 referências a `rollover/apply`/
`confirmRollover`; Jinja parse OK; `salary_engine_test.py` 48/48. **✅ após smoke em prod:** deploy +
admin sem botão (preview funcional) + offseason Step 4 intacto.

**Smoke de prod (12/06/2026): PASSOU — F11 ✅.** Deploy do commit `75e69e7`; `/admin` sem o botão de
apply, card "Season Rollover (preview)" funcional com dados reais (**273 jogadores, 0 renovações,
cap $2187 → $2310**); `/offseason` com Step 4 **bloqueado por gate** (step 3 pendente) — gates
intactos. Porta única de rollover confirmada em produção. Sub-item de carona: [[F11-FIX-UX]]
(microcopy dos dois cards do /admin, sessão F10).


---

### F10 — `draft_budget` replicado em JavaScript no cap projector
✅ **12/06/2026** (réplica eliminada + smoke prod OK)

_Status original quando aberto:_ 🔲 **Pendente** — Prioridade **Média** — achado lateral de [[MAN-OFF26-3-F1]] (registrado 05/06/2026)

**Descrição:** a lógica canônica de budget de draft existe no backend
(`salary_engine.draft_budget` — `$200 − keepers`, mínimo $1 por slot vazio,
`usable`/`over_cap`/`insufficient`) e está **reimplementada no cliente** em JS, em
`templates/cap_projector.html` (~linhas 150-171: cálculo de `raw_budget`, `usable`
e aviso "Budget insuficiente").

**Motivação:** viola o princípio "1 fonte por modo de render" estabelecido no
**T2-FIX-2** (eliminar réplica de cálculo entre backend e JS). Divergência latente:
qualquer mudança na regra de budget exigiria editar dois lugares.

**Escopo do fix:** o cliente passa a consumir a fonte canônica via endpoint (expor
`draft_budget` por time numa rota e o `cap_projector.html` consome em vez de
recalcular).

**Observação de dependência:** idealmente resolvido **antes do OFF26-1** (janela
selada de keepers/cuts), que calculará budget ao vivo e deve **nascer consumindo o
canônico** — evita criar uma terceira réplica.

**Ref. cruzada:** [[MAN-OFF26-3-F1]] (diagnose do importador OFF26-3, achado §3).

#### F2 ⚠️ (12/06/2026) — réplica eliminada; summary consome o backend (localhost)

**Premissa do prompt refutada (MAN-METH-REG):** "pode bastar consumir o payload atual" — **não
basta**. O `budget` do GET (`salary.py`, `draft_budget(players)`) é calculado sobre o **salário
ATUAL do roster inteiro**; o `updateSummary` calcula sobre o **subconjunto mantido (keep/corte)
com `next_salary` projetado** (cap_projector.html:183-184 pré-fix) — entradas diferentes, o
payload existente não cobre nenhum cenário com corte. Solução no padrão DP1 (simulação no
backend): **novo endpoint `POST /api/cap_projector/<team>/budget`** recebe `{kept_ids}` e devolve
`draft_budget` canônico sobre os mantidos com `project_next_salary` (mesma fonte da coluna "Sal
próximo ano"), + derivados de display `cap_pct`/`shortfall` (derivam do retorno do helper — o
cliente não faz nenhuma aritmética). Projeção pura, nada escrito; ids inválidos ignorados.

**JS (`updateSummary`):** vira POST dos `kept_ids` + exibição do payload — somas, `SALARY_CAP`/
`MAX_ROSTER` (consts deletadas), spots, pct e aviso de insuficiência **todos do backend**. Guard
de sequência contra resposta obsoleta em toggles rápidos. Mensagens "cap de $200" trocadas por
`$${b.salary_cap}` (tb. no painel DP1 — string renderizada idêntica, endpoint DP1 intocado).
Comentário stale do DP1 ("débito F10 fica restrito ao updateSummary") atualizado para "quitado".

**Gap existe×proposto (mapeamento campo a campo, completo):** total→`keeper_salaries`;
remaining/budget-bruto→`raw_budget` (ambos exibiam o mesmo valor; preservado); usable→
`usable_draft_budget`; spots/min→`empty_spots`/`min_required_for_spots`; pct→`cap_pct` (min 100
preservado); aviso over-cap→`over_cap`; aviso insuficiência→`insufficient_budget`+`shortfall`.
**Única mudança comportamental:** o summary atualiza por round-trip (async) a cada toggle, em vez
de sincronamente — padrão já estabelecido pelo DP1 na mesma página; mitigado pelo guard de
sequência. Classes de cor (<0 danger, <10 warn) seguem no JS (comparação de display, não agregação).

**Relatório do grep de réplicas (codebase inteiro):** única réplica JS de cálculo de budget era o
`updateSummary` (+ consts). Demais ocorrências, com parecer: literais de display "$200"
(base.html:73,153; trades.html:375 — valores calculados no backend, só o texto fixo; cap é
constante de regulamento documentada → decisão consciente, sem item novo; os do cap_projector
foram absorvidos de graça); agregações server-side de cap usado (roster/league/trades —
semântica "cap usado", não a regra de budget; server-side, fora do princípio backend↔JS);
draft_import.py:75 **consome** o canônico via SimpleNamespace (padrão correto). **Zero réplicas
novas → zero itens novos.**

**Validação (localhost, test client, usuário não-admin temporário):** página 200; payload ×
canônico **idêntico** em 4 cenários (todos mantidos $256/insuf, metade $159/usable $30, todos
cortados $0/$178, ids inválidos ignorados); paridade com o summary antigo (Σ next_salary == 
`keeper_salaries`); 404 p/ time inexistente; **regressão DP1**: cenário vazio == budget atual e
caso de referência **2 picks +$58** reproduzido ($46→$55, $3→$3; store local re-semeado
temporariamente e limpo); **nada escrito** (salaries + store intactos); grep no template = zero
aritmética de budget/`SALARY_CAP`/`MAX_ROSTER`/literais; Jinja parse OK; `salary_engine_test.py`
**48/48**. **✅ após smoke em prod** (summary com valores corretos + toggles + board DP1).


---

### DOC1 — CLAUDE.md "App Startup Sequence" desatualizada (docs-only)
✅ **12/06/2026** (seção reescrita contra o boot real)

_Registrado_ 11/06/2026 — achado AUD1 Lente 6 — Prioridade **Média** (blast radius: doc carregada em toda sessão do Code)

**Evidência:** CLAUDE.md lista 10 passos com `init_auth` (8) antes de `run_sync` (9) e
`_backfill_player_history` (10) incondicionais. Código real (app.py): `run_import` (60) →
**`run_sync` e backfill SÓ se `fresh_import`** (app.py:61-82; backfill ainda atrás do guard
`f8_rebuilt`) → context processors → `init_auth` **por último** (app.py:138). **Risco:** sessão
futura assume "sync roda em todo boot" e mis-diagnostica dados stale (premissa falsa classe DP1-F1
no doc de maior propagação). **Parecer:** doc desatualizado → docs-only fix no CLAUDE.md (reescrever
a sequência refletindo condicionalidade e ordem reais). Sem F1 — evidência acima é a diagnose.

**Fix ✅ (12/06/2026, docs-only).** Seção "App Startup Sequence" reescrita lendo `app.py` passo a
passo, cada passo com âncora de linha. Correções aplicadas:
- **Ordem do `init_auth`:** estava como passo 8 (antes do sync); real = perto do fim (linha 138),
  **depois** dos context processors. Corrigido.
- **Condicionalidade de `run_sync`/backfill:** estavam como passos incondicionais 9 e 10; real =
  ambos sob `if fresh_import` (linha 61), e o backfill ainda sob `if not f8_rebuilt` (legacy
  superseded pelo F8). Documentado como sub-bloco condicional + nota de propagação.
- **Divergências adicionais encontradas na mesma passada (todas corrigidas aqui, nenhuma vira item
  novo):** (1) URI do SQLite vem da env `DYNASTY_DB`, não fixa — antes omitido; (2) registro do
  filtro Jinja `utc_iso` (M18) não constava; (3) os 4 context processors, os 9 blueprints e os
  error handlers 404/500 não constavam (a sequência parava no backfill); (4) `app.run(host=...)` só
  sob `__main__`. Claims restantes da seção (passos 1-6) conferidas contra o código e corretas.

**Critério de done (sem smoke de prod — docs):** cada passo documentado tem âncora apontável em
`app.py` (verificado nesta sessão); divergências adicionais reportadas e corrigidas inline. ✅ direto.


---

### DP2 — Cadeia única de planejamento no cap projector (board sobre keep/corte + summary sticky)
✅ **15/06/2026 (smoke de prod confirmado)** — MAN-DP2-REG/DP2 — Prioridade
**Média** — revisão consciente da base do [[DP1]]-F2; estende o canônico do [[F10]]

**CONTEXTO (REG, decisão do owner 12/06/2026).** Pós-F10, a tela tinha **dois painéis de números com
bases distintas**: o summary do topo respondia aos toggles keep/corte via o `/budget` canônico
(salário projetado), enquanto o board DP1 simulava sobre o **roster integral com salário atual**
(`/simulate`, decisão DP1-F2 "cenário vazio = budget atual"). O owner decidiu que o planejamento é
**uma cadeia só** (cortes → budget → picks de rookies): o board passa a partir do cenário keep/corte
e a tela ganha **uma superfície única de números**. Alternativa de painel lateral descartada (depende
de viewport largo / acoplaria ao UX6 pendente; sticky funciona em mobile).

**FIX (preferiu estender, não criar 2ª fonte).** O `POST /api/cap_projector/<team>/budget` do F10 foi
**estendido** para aceptar `rookie_sids` além de `kept_ids`: os rookies do cenário entram na **mesma
base** (membros de roster adicionais com `year1_salary` modo rookie — ocupam spot e custam salário,
como um pick real) e o `draft_budget` canônico calcula o todo. O `POST /api/cap_projector/simulate`
do DP1-F2 foi **removido** (sua conta vive aqui agora) — **fonte única de cálculo, sem segunda rota**.
O endpoint passou a devolver também `scenario_count`/`scenario_salary_total` (campos próprios do
board). Base unificada = **salário projetado** do summary (não mais o "salário atual" do DP1-F2).

**UI.** O `#proj-cap-bar` virou **barra sticky** (`.cap-summary-sticky`: `position:sticky; top:54px`
= altura do navbar; `z-index:20` < navbar 100; `.cap-summary-grid` já é `flex-wrap` → sem overflow
horizontal em mobile) refletindo cortes + rookies. O painel do board (`#rookie-sim`) foi **reduzido
aos campos próprios** (nº de rookies + custo); cap/budget/spots/avisos saíram de lá e vivem só na
barra. As duas funções JS (`updateSummary` + `simulateScenario`) fundiram-se em **`refreshScenario`**
(um POST com `kept_ids`+`rookie_sids`); toggle de keep e de rookie disparam o mesmo refresh; guard de
sequência preservado (resposta obsoleta descartada).

**Grep de duplicação (pergunta obrigatória do prompt).** A formatação desses números (`usable`,
`empty_spots`, `min $`) aparecia em 2 lugares — ambos **dentro** do cap_projector (`#proj-*` ×
`#rk-*`), exatamente a duplicação que o DP2 colapsa. Único outro sítio: `draft_import.html:83`
(alerta soft do audit de keepers OFF26-3, por-time, backend-derivado) — **superfície distinta, fora
de escopo**, não dedupa aqui. **Zero duplicação cross-template remanescente.**

**Validação (localhost, test client, usuário não-admin temporário):** **retrocompat** — todos kept +
0 rookies == budget do F10 ($256, base projetada); **cadeia integrada** — payload × canônico idêntico
em 4 cenários (metade cortada + 2 rookies $138/usable $53; todos kept + 2 rookies $314/usable −$114;
todos cortados + 1 rookie; dedup + sid inválido ignorado); **caso de referência DP1 preservado** —
rookies $46→$55 e $3→$3, soma +$58, keeper $256→$314; **`/simulate` removido** (405, sem POST
handler); **nada escrito** (salaries + store intactos); grep no template = zero aritmética de budget,
zero identificador órfão (`simulateScenario`/`updateSummary`/`rk-total`…); Jinja parse OK;
`salary_engine_test.py` **48/48**. **✅ após smoke em prod:** barra sticky visível ao rolar
(desktop+mobile), toggles keep/corte + rookies refletindo no topo, board com nº/custo.

---

### F11-FIX-UX — Microcopy do preview de rollover no /admin (carona F10)
✅ **15/06/2026 — fecha junto com o [[UX9]]** (sintoma do passo 2 eliminado pela raiz; sem trabalho próprio remanescente) — sub-item de [[F11]]
(seção principal no archive) — padrão N1-FIX/T3-FIX-UX — Prioridade **Baixa**

**Motivação:** após o F11, o card "Season Rollover (preview)" e o passo 2 do "Ordem do Fluxo
Pré-Temporada" descreviam o preview em linguagem de dev ("Step 4", "workflow do Offseason",
nomes de campo). Microcopy reescrita em linguagem de owner: o que a prévia mostra, que nada é
alterado ali, e onde a aplicação real acontece (etapa Season Rollover da página de
**Intertemporada**, com link em /offseason), incluindo as condições de liberação (sorteio do
draft travado + valores ESPN atualizados). Sem nº de step e sem season hardcoded nos dois cards.

**Arquivos:** `templates/admin.html` (2 cards). ✅ quando o smoke do F10 passar em prod.

**Smoke parcial (12/06/2026):** card "Season Rollover (preview)" PASSOU. O passo 2 do card "Ordem
do Fluxo Pré-Temporada" **quebrou o layout** — o texto longo fragmentou em colunas ("...da página
de / Intertemporada ; aqui, apenas / a prévia", com espaço antes do `;`). **Fix:** encurtado só o
passo 2 para "— aplicado na etapa Season Rollover da página de Intertemporada; aqui, só a prévia"
(link em "Intertemporada" mantido); o card do preview fica como está. **Segue ⚠️ até o smoke do
layout em prod.**

**Smoke de prod (15/06/2026) — encurtar NÃO resolveu:** o passo 2 **continua fragmentando em
colunas** em produção (palavras fora da ordem de leitura). Conclusão: a causa **não é
comprimento de texto** e sim **layout do card**. O bug de layout vira item próprio — ver
**[[UX9]]** (MAN-UX9-REG + F1 de diagnose). **F11-FIX-UX permanece ⚠️**: seu critério de done
depende do passo 2 ficar correto em prod, agora rastreado pelo UX9.

**Causa real (UX9-F1, 15/06/2026):** não era "texto longo" — é o **`<a>Intertemporada</a>` inline
no meio da frase** dentro de uma `<li>` que é `display:flex`: o link parte o texto em flex items
separados, cada um colapsando numa coluna estreita. Encurtar nunca resolveria (o link continua
partindo a linha). Fix recomendado: envolver o body do passo num único `span` inline (Opção A do
UX9). O "espaço antes do `;`" observado aqui era o `gap: .6rem` entre flex items.

**Fix aplicado pela raiz no [[UX9]] (F2, 15/06/2026, ⚠️ localhost):** o body de cada passo virou
um `<span class="step-body">` único → passo 2 flui em linha contínua, link `/offseason` clicável.
**Dependência de done explícita:** o critério do F11-FIX-UX (passo 2 correto em prod) **não tem
mais trabalho próprio** — quando o smoke de prod do UX9 passar, **F11-FIX-UX fecha junto** (✅).
Até lá, ambos seguem ⚠️.

---

### UX9 — Passo 2 do fluxo pré-temporada fragmenta em colunas no /admin
✅ **F2 validada em smoke de prod (15/06/2026)** — Prioridade **Baixa** (cosmético; não afeta cálculo nem dados) — MAN-UX9-REG/F1/F2 (15/06/2026) — relacionado a [[F11-FIX-UX]]

**CONTEXTO**
O card "Ordem do Fluxo Pré-Temporada" no `/admin` tem um **passo 2** cujo texto, em
produção, **fragmenta verticalmente em colunas** — as palavras quebram fora da ordem de
leitura (ex.: "aplicado na / Intertemporada / ; aqui, / só a / prévia" intercalado com
"etapa Season / Rollover da / página de"). O **smoke de prod de 15/06/2026** confirmou a
fragmentação.

**PROBLEMA / OPORTUNIDADE**
É o mesmo sintoma que o **F11-FIX-UX** tentou corrigir **encurtando** o texto do passo 2
("— aplicado na etapa Season Rollover da página de Intertemporada; aqui, só a prévia").
O smoke de 15/06 mostra que **encurtar não resolveu** → a causa **não é comprimento de
texto** e sim **layout do card** (provável container com comportamento de coluna /
`column-count`/`columns` herdado, ou largura insuficiente forçando wrap anômalo). Bug de
UI próprio, que **desbloqueia o done do F11-FIX-UX** (cujo critério depende deste layout
ficar correto em prod).

**DECISÕES JÁ TOMADAS**
- Item **próprio** (separado do F11-FIX-UX, que era microcopy; aqui é layout).
- Registro agora; **diagnose (F1) e implementação são itens próprios**.

**QUESTÕES EM ABERTO** (F1 — MAN-UX9-F1, read-only)
- Qual marcação/CSS governa o card "Ordem do Fluxo Pré-Temporada" e o passo 2 em
  `templates/admin.html`? Há `column-count`/`columns`/`display` herdado de um wrapper
  que produza o efeito de coluna?
- A fragmentação vem de **largura do container** (texto quebra dentro de uma célula
  estreita) ou de uma propriedade de **multi-coluna** aplicada ao bloco?
- O sintoma é específico do passo 2 (texto mais longo) ou os outros passos também
  quebrariam com texto equivalente? (isola se é layout do card vs. conteúdo do item)
- Há réplica do bloco em outra tela (preview de rollover compartilha marcação)?

**RESTRIÇÕES**
- Cosmético: não tocar lógica de offseason, rollover, `salary_engine`, schema ou sync.
- Não antecipar causa-raiz nem correção — entregável da F1.

**DEPENDÊNCIAS**
- Desbloqueado: **MAN-UX9-F1** concluída (abaixo). Causa confirmada; escopo **local** ao card.
- Relaciona-se com: **[[F11-FIX-UX]]** (encurtar texto não resolveu — a F1 explica por quê; done
  do F11-FIX-UX depende deste layout em prod), **[[F11]]** (sessão de origem).

**F1 — ACHADOS (diagnose read-only, concluída 15/06/2026 — MAN-UX9-F1, zero writes)**

*Causa-raiz confirmada — é flex, NÃO multi-coluna.* A premissa do REG (`column-count`/`columns`)
está **refutada**: não existe propriedade de multi-coluna em jogo (grep em `static/style.css`:
todos os `column-*` são `grid-template-columns`/`column-gap`, nenhum em `.workflow-steps`). A
regra responsável é **`.workflow-steps li { display: flex; align-items: baseline; gap: .6rem }`**
(CSS do card workflow). Cada `<li>` é uma **linha flex** (default `flex-direction: row`,
`flex-wrap: nowrap`), e **cada filho direto vira um flex item** — inclusive **cada trecho de
texto separado por um elemento inline vira um flex item anônimo próprio**.

*Por que incide no passo 2 e não no 1/3.* No `templates/admin.html`, os bodies dos passos 1 e 3
são `<strong>…</strong>` + **um único trecho de texto contíguo** → no máximo 3 flex items, com a
descrição inteira sendo **um** item que quebra normalmente, na ordem de leitura. O **passo 2 tem
um `<a href="/offseason">Intertemporada</a>` no MEIO da frase**, que **parte o texto em dois**:
os filhos do `<li>` viram `[step-num] [strong] [texto-antes] [<a>] [texto-depois]` = **5 flex
items**. Com `nowrap` e a largura do card, cada item de texto encolhe até ~min-content e **quebra
o próprio texto numa coluna estreita** → "fragmenta em colunas, fora da ordem de leitura". O
`gap: .6rem` entre itens também explica o "espaço antes do `;`" observado no smoke do F11-FIX-UX.

*Por que encurtar (F11-FIX-UX) não resolveu.* A fragmentação é **estrutural** (flex na `li` +
link no meio da frase partindo o texto em vários flex items), **independente do comprimento**.
Reduzir o texto não remove o `<a>` interno → os fragmentos persistem. **Isto corrige o
entendimento do F11-FIX-UX**: o sintoma não era "texto longo", era **o link inline** dentro de
uma `li` flex.

*Compartilhamento / blast radius — local, zero propagação.* `.workflow-steps`, `.workflow-steps
li` e `.step-num` aparecem **só neste card** (grep: 1 template, `admin.html`; classes não usadas
em nenhuma outra tela). O card "Season Rollover (preview)" logo abaixo também tem um link
`/offseason`, mas dentro de um `<p>` normal (**não** flex) → flui bem; não compartilha o defeito.
Corrigir `.workflow-steps li` (ou o markup dos `<li>`) afeta **apenas** este card.

*Opções de implementação (F2 — não implementar nesta sessão):*
- **Opção A (RECOMENDADA):** **embrulhar o conteúdo pós-badge num único elemento** — cada `<li>`
  passa a ter exatamente 2 flex items: `.step-num` + `<span class="step-body">…</span>` (com
  `<strong>` + texto + link dentro). Dentro do `step-body` o conteúdo volta a ser **fluxo inline
  normal** → o link fica inline no meio da frase e o texto quebra na ordem de leitura. Mudança de
  markup em `admin.html` (aplicar aos 3 passos por consistência); provável `min-width:0` no
  `step-body` para permitir encolher. Preserva o alinhamento do badge (baseline). **Blast radius
  local** (só o card). Causa-raiz de fato resolvida (colapsa os 5 items de volta a 2).
- **Opção B:** **tirar o flex da `li`** — `.workflow-steps li { display: block }` + `.step-num`
  como `float:left` (com `margin-right`) ou `inline-flex` com `vertical-align`. Conteúdo vira
  fluxo inline → link inline, texto em ordem. Trade-off: perde o hanging-indent limpo (coluna do
  número × coluna do texto) que o flex dava; precisa de `padding-left`/`text-indent` para
  restaurar. CSS um pouco mais delicado; ainda local.
- **Rejeitada (C):** só adicionar `flex-wrap: wrap` à `li` — mantém o texto como flex items
  separados; eles quebrariam como grupo, mas cada segmento continua um item próprio e ainda pode
  colapsar em coluna quando estreito. Não ataca a raiz.
- **Rejeitada (D):** encurtar mais o texto — já provado que não resolve (smoke 15/06); a causa
  não é comprimento.

**Recomendação para a F2:** Opção A (envolver o body do passo num único `span` inline). Fecha a
causa-raiz, preserva o badge, local ao card. Quando aplicada e validada em prod, **fecha também
o critério de done do [[F11-FIX-UX]]** (layout do passo 2 correto em produção).

**F2 — IMPLEMENTAÇÃO (15/06/2026, ⚠️ validado em localhost) — MAN-UX9**

*Correção estrutural (Opção A), não de comprimento:* em `templates/admin.html`, o corpo de cada
passo (tudo após o badge `.step-num`) foi envolto num **`<span class="step-body">…</span>`**
único. Agora cada `<li>` tem **exatamente 2 flex items** (badge + body), e dentro do `step-body`
o conteúdo — incluindo o `<a href="/offseason">Intertemporada</a>` do passo 2 — volta a ser
**fluxo inline normal**, em ordem de leitura. Nova regra CSS `.step-body { flex: 1; min-width: 0 }`
(em `static/style.css`) faz o body ocupar a largura restante e permitir que o texto quebre dentro
do card. **Aplicado uniformemente aos 3 passos** → card consistente e resistente a links inline
futuros.

*Sem mudança de redação/conteúdo:* badge, textos, o link interno do passo 2 (href `/offseason`,
clicável) e o alinhamento badge↔texto preservados. Passos 1 e 3 visualmente equivalentes (corpo
contíguo, agora dentro do span).

*Escopo local confirmado:* `git diff` = 3 `<li>` envoltos + 1 regra `.step-body`. **Não** tocou
o card "Season Rollover (preview)" (link `/offseason` dele já vive num `<p>` normal, sem o
defeito) nem nenhum outro card do `/admin`. Classes `.workflow-steps`/`.step-num`/`.step-body`
exclusivas deste card → zero propagação.

*Validação localhost:* `salary_engine_test.py` **48/48** (sanity de cálculo). Diff revisado: só
markup do card + 1 regra CSS. **Pendente:** smoke visual em prod (passo 2 em linha contínua, link
clicável; passos 1/3 sem regressão) — owner dispara o deploy.

**Arquivos:** `templates/admin.html` (3 `<li>`), `static/style.css` (regra `.step-body`).
Sem mudança de lógica/JS/schema.

*Done do [[F11-FIX-UX]] amarrado a este fix:* o sintoma que o F11-FIX-UX perseguia (passo 2
quebrado em prod) é eliminado **pela raiz** aqui. Quando o smoke de prod do UX9 passar, o
F11-FIX-UX **fecha junto** (não há mais layout pendente a validar).

---

### F12 — `run_import` sobrescreve salary/contract a cada boot local, sem history
✅ **Concluído 15/06/2026 (critério dev-local; sem smoke de prod — comportamento puramente dev-local)** — achado AUD1 Lente 2 — Prioridade **Média** (dev local; prod safe)

**Evidência:** import_csv.py:110-112 — para player existente, `player.salary = salary` +
`player.contract_year = cyr` **incondicionalmente** a cada `run_import()` (todo boot com CSV
presente, app.py:60), **sem criar SalaryHistory**. O guard `f8_rebuilt` (import_csv.py:61-63)
protege só `acquisition_type`/`contract_start_season`. A coluna lida é `salary_2025` (hardcoded,
import_csv.py:90) — snapshot estático de 2025. Em prod o CSV não existe (não está no git) → skip
(WARNING, import_csv.py:54-56). **Risco:** em dev local, rollover/correções feitos in-app são
silenciosamente revertidos ao snapshot 2025 no próximo boot, sem trilha — explica/agrava o
"dynasty.db local diverge do repo" e cria falsos negativos em testes locais de rollover.
**Parecer:** item novo. Candidatos de fix (decidir em F2): guard tipo `csv_imported` one-shot,
ou skip de salary/cyr quando `f8_rebuilt`/flag equivalente — manter CSV como bootstrap, não como
autoridade contínua. Atualizar CLAUDE.md junto ("first run auto-imports" hoje não descreve o código).

#### F2 ⚠️ (12/06/2026) — bootstrap one-shot via flag própria (validado localhost)

**Decisão de design — Opção B (flag one-shot `csv_bootstrap_done`), NÃO o guard `f8_rebuilt`.**
Justificativa: `f8_rebuilt` é semanticamente o marcador do rebuild de PlayerHistory via chain do
Sleeper (estado tipicamente só atingido em prod). Num DB de **dev fresco** `f8_rebuilt=false`, então
reusá-lo **não fecharia o caso dev-local** (salary/cyr seguiriam sobrescritos todo boot). Uma flag
própria casa exatamente com o critério "CSV é bootstrap, não autoridade contínua" e segue o
**precedente do próprio `f8_rebuilt`** (flag de guard de import, lazy, lida com fallback `"false"` e
fora do `_seed_app_config`) — `csv_bootstrap_done` é **chave nova em AppConfig**, não mudança de
schema (restrição respeitada: AppConfig existente, sem coluna nova).

**Implementação (import_csv.py, contida em 1 arquivo):** lê `csv_bootstrap_done`; no branch de player
**existente**, `salary`/`contract_year` só são escritos `if not csv_bootstrap_done` (a 1ª semeadura);
após o commit, seta a flag. Branch de player **novo** intocado (o create segue semeando salary/cyr do
CSV — primeiro contrato legítimo). Em prod (CSV ausente) o `run_import` retorna cedo no WARNING e
**nunca seta a flag** — inofensiva (sem CSV não há o que reescrever). **Escopo estrito a salary/cyr:**
`set_espn_value`, `position`, `nfl_team` etc. seguem como estavam (fora do escopo do F12).

**Observação fora de escopo (candidata a item próprio):** o `set_espn_value` também re-aplica o
snapshot ESPN do CSV todo boot local — mesma classe de "snapshot estático reescreve estado in-app",
mas para ESPN values, não salary/contract. Não tocado aqui (escopo F12 = salary/cyr); registrar se
virar incômodo real em dev (após import ESPN local seria revertido no boot seguinte).

**CLAUDE.md atualizado:** a linha "first run auto-imports …" (Commands) agora descreve o bootstrap
one-shot de salary/contract + a flag `csv_bootstrap_done`.

**Validação localhost (DB de teste = cópia do seed + `db.create_all`):** (1) **boot duplo** — boot 1
semeia (Mahomes salary 9.0) e seta a flag; edição in-app (→26.0/cyr 3); boot 2 com guard ativo
**preserva** (26.0/cyr 3, não reverteu); (2) **player novo** com a flag já `true` entra normalmente
via CSV temporário (salary 7.0/cyr 1, `created=1`); (3) **caminho prod** (CSV ausente) → skip com
WARNING, `return False`, flag intacta. `salary_engine_test.py` **48/48**. **Critério de ✅
(dev-local, sem smoke de prod):** a validação dupla acima — registrada como done; F12 pode flipar ✅
direto. (Mantido ⚠️ no Status Rápido até o owner confirmar; comportamento é puramente dev-local.)

---

### UX8 — Densidade vertical do cap projector (foto ao lado do nome)
✅ **F2 validada em smoke de prod (15/06/2026)** — Prioridade **Baixa/Média** (UX, sem mudança de cálculo) — MAN-UX8-REG/F1/F2 (15/06/2026)

**CONTEXTO**
O `/cap_projector` renderiza as rows de jogador em **JS** (template literals — não SSR),
com a foto do jogador empilhada **acima** do nome. Em telas com 20+ jogadores, o
espaçamento vertical resultante dificulta a visão do conjunto. As demais telas densas
(`/team/<id>`, `/`, `/trades`, `/salary_history`, `/player/<id>`) usam a infra de foto
compartilhada de UX1/UX3 (macro Jinja `player_photo` + helper JS `renderPlayerPhoto` +
classe CSS `.player-photo-sm`) — fonte única por modo de render (convenção MAN-O2/O1).

**PROBLEMA / OPORTUNIDADE**
A foto acima do nome custa altura por row; com 20+ jogadores o owner perde a visão do
conjunto no cap projector. Mover a foto para **ao lado** do nome recupera densidade
vertical sem abrir mão da identidade visual da foto.

**DECISÕES JÁ TOMADAS**
- **Opção B (foto ao lado do nome)** — mock confirmado em chat pelo owner (15/06/2026).
- Registro agora; **diagnose (F1) e implementação (F2) são itens próprios**.

**QUESTÕES EM ABERTO** (F1 — MAN-UX8-F1, read-only)
- A classe `.player-photo-sm` (foto acima do nome) é **compartilhada** com as outras
  telas densas, ou o cap projector tem layout próprio? Disso depende se a mudança é
  uma classe nova/variante (não regredir as outras telas) ou um ajuste à classe comum.
- Onde exatamente o cap projector monta a row em JS (`renderPlayerPhoto` + template
  literal) e qual marcação/CSS governa o empilhamento foto-acima-do-nome?
- Há réplica do layout de foto entre o cap projector e as outras telas, ou a infra de
  UX1/UX3 já é fonte única (e a mudança só precisa de uma variante de classe)?

**RESTRIÇÕES**
- Sem mudança de cálculo: não tocar `salary_engine`, schema, sync, nem a lógica de
  budget/salário. Mudança puramente de apresentação.

**DEPENDÊNCIAS**
- Desbloqueado: **MAN-UX8-F1** concluída (abaixo). Escopo confirmado **local** ao cap projector.
- Relaciona-se com: **UX1/UX3** (infra de foto compartilhada), **F10/DP2** (render JS do cap projector).

**F1 — ACHADOS (diagnose read-only, concluída 15/06/2026 — MAN-UX8-F1, zero writes)**

*Como o cap projector monta foto+nome:* render **100% JS** (template literal em
`templates/cap_projector.html`). A row coloca, **dentro de um único
`<td class="player-name-cell">`**: `renderPlayerPhoto(p, 'player-photo-sm')` (img inline) +
`renderPlayerNameLink(p)` (gera elemento `.player-name`) + tags ANO 4/REVISÃO. **Não** usa a
macro Jinja `player_roster_row`.

*Causa-raiz do empilhamento (premissa do REG refinada):* o stacking **não vem** de
`.player-photo-sm` nem da infra compartilhada — vem do **container local**. `.player-name-cell`
(em `static/style.css`) é só `font-weight:600`, **sem `display:flex`**; e `.player-name` é
`display:flex` → **caixa block-level**, que cai para a linha **abaixo** da `<img>` inline.
Resultado: foto acima do nome. **`.player-photo-sm` só define tamanho (32px) e borda — não
posiciona nada.**

*A estrutura foto+nome existe em mais de um lugar? SIM a infra de imagem, NÃO o layout.* O que
é compartilhado (`renderPlayerPhoto` / `player_photo` / `.player-photo` / `.player-photo-sm`)
governa **só a imagem** (URL Sleeper CDN, tamanho, borda, fallback `onerror`). O
**posicionamento relativo ao nome é próprio de cada tela** — e **todas as outras já põem a foto
AO LADO**:
- `/` (roster) e `/team/<id>`: macro `player_roster_row` → foto e nome em **`<td>` separados**
  (`col-photo` + `col-name`) → lado a lado por coluna.
- `/trades`: `<label class="asset-item">` (`display:flex; align-items:center`) → lado a lado.
- `/salary_history`: `.player-card-header` (pos-badge + foto + `.player-name` num header) → lado a lado.
- `/player/<id>`: `player_photo(player)` **sem `-sm`** (96px) em `.player-detail-header` → cabeçalho, não row.
**O cap projector é o único que empilha**, porque é o único que mete foto+nome no **mesmo `td`**
sem flex. **`.player-name-cell` é exclusiva do cap projector** (grep: 1 só ocorrência no projeto).

*Blast radius — local, zero propagação:* mexer em `.player-name-cell` (torná-la flex) afeta
**somente** o cap projector. **Não** precisa tocar `.player-photo-sm` (isso sim propagaria os
32px a 5 telas). Logo a mudança "ao lado" é **local ao cap projector, sem variante nova de
classe e sem risco às outras 5 telas** — refuta a hipótese do REG de que poderia exigir classe
própria para não propagar.

*Premissas/efeitos colaterais:*
- **Confirmada:** a foto **está** empilhada acima do nome (sintoma real).
- **Refinada:** o REG temia compartilhamento via `.player-photo-sm`; o código mostra que o
  compartilhado é só a imagem, não o layout → escopo **local**, não cross-tela.
- **Sem perda de campo:** ao virar flex, img + nome + tags ANO 4/REVISÃO ficam na mesma linha;
  nenhum campo some (deslocamento intencional, não remoção).
- **Achado incidental (fora do escopo de layout, mas no mesmo bloco que a F2 vai editar):** as
  tags fecham com `<\span>` (não `<\/span>`) no template literal — em JS `\s`→`s`, então renderiza
  um `<span>` de abertura solto em vez de fechamento. Pré-existente, tolerado pelo browser;
  registrar para limpeza oportunista na F2 (não é UX8 em si).

*Opções de implementação (F2 — não implementar nesta sessão):*
- **Opção A (RECOMENDADA):** dar `display:flex; align-items:center; gap:.4rem` (+ `flex-wrap:wrap`)
  a `.player-name-cell` em `static/style.css`. ~1 regra, **zero blast radius** (classe exclusiva),
  recupera ~32px de altura por row. Trade-off: as tags ANO 4/REVISÃO viram itens flex inline após
  o nome — provável OK (com wrap); validar visualmente.
- **Opção B:** embrulhar foto+nome num `<div class="cap-name-wrap">` flex novo dentro do `td`
  (mudança no template literal JS + classe nova). Isola o flex a foto+nome e deixa as tags fora;
  mais código, mesmo zero blast radius. Usar só se as tags na Opção A destoarem.
- **Rejeitada:** tocar `.player-photo-sm` ou a macro compartilhada — desnecessário e propagaria às
  outras telas.

**Recomendação para a F2:** Opção A (uma regra CSS local). Escopo fechado, sem cross-tela.

**F2 — IMPLEMENTAÇÃO (15/06/2026, ⚠️ validado em localhost) — MAN-UX8**

*Mudança única (Opção A):* `.player-name-cell` (em `static/style.css`) passou de
`{ font-weight: 600 }` para `{ font-weight: 600; display: flex; align-items: center; gap: .4rem;
flex-wrap: wrap }`. A `<td>` da row vira container flex → foto (`player-photo-sm`, 32px
intactos), nome (link) e tags ANO 4/REVISÃO ficam **na mesma linha**; `flex-wrap` deixa as tags
caírem se faltar largura. **Zero mudança de markup** (a row já tinha foto→nome→tags em ordem no
`td`). Recupera ~32px de altura por row.

*Achado incidental da F1 era FALSO POSITIVO (registro corrigido):* a "tag de fechamento
malformada (`<\span>`)" reportada pela F1 **não existe no código** — era artefato de renderização
do Grep, que exibe `/` como `\` (o `</span>` real aparecia como `<\span>`; idem `</th>` na tabela
de rookies). O Read do fonte confirma `</span>`/`</th>` bem formados em `cap_projector.html`.
**Nenhuma correção de tag foi necessária nem feita** — não havia bug. (Lição: validar achados de
"tag malformada" vindos de Grep contra o Read do fonte antes de tratar como real.)

*Escopo local confirmado (telas intocadas):* `git diff` = só a 1 regra de `.player-name-cell`.
Não tocou `.player-photo-sm`, `.player-photo`, a macro `player_photo`, nem o helper
`renderPlayerPhoto`. As outras 5 telas densas não usam `.player-name-cell` (usam `<td>` separados
via macro, ou `.asset-item`/`.player-card-header`/`.player-detail-header`) → **sem propagação
visual**.

*Validação localhost:* `salary_engine_test.py` **48/48** (sanity de cálculo). Diff revisado: 1
regra CSS, classe exclusiva do cap projector. **Pendente:** smoke visual em prod (foto ao lado,
altura menor, tags/link preservados) — owner dispara o deploy.

**Arquivos:** `static/style.css` (1 regra). Sem mudança de template/JS/schema.

---

### OFF26-9 — Acoplamento das fases da intertemporada × dependência do ESPN definitivo
✅ **17/06/2026 — F1 confirmou a suspeita (abertura só exige `needs_review` zerado; E4-a por
arrasto) + correção de redação/microcopy aplicada (D8 esclarecida, pré-condições separadas,
microcopy do passo 6 ajustado); smoke do microcopy em prod conferido. Sem mudança de
lógica/gate.** — MAN-OFF26-PHASE-REG/F1/FIX — Prioridade **Alta**

> **Smoke do microcopy ✅ (17/06/2026, prod pós-deploy):** o owner abriu `/offseason` e conferiu
> o passo 6 ("Definir Keepers / Cortes") — o texto distingue corretamente a **pré-condição de
> abertura** ("Abrir a janela exige apenas a fila de revisão needs_review zerada") da
> **recomendação de qualidade de dado** ("rodar o Rollover antes para o budget refletir o salário
> valorizado — não é pré-condição de abertura"); **texto lê bem e layout intacto**. Critério
> pendente de ✅ satisfeito. **O3:** seção migrada para `improvements_archive.md` no fechamento.

**Descrição:** investigar se as **fases da intertemporada do Manager** (notadamente o
Season Rollover, passo 4, e a abertura da **janela de cortes** [[OFF26-1]]) estão
**indevidamente acopladas** ao import do **ESPN definitivo** ([[E4-a]]). A regra da liga é
que a intertemporada **começa logo após o fim da anterior**, mas o E4-a é **deliberadamente
tardio** — só ocorre **perto do rookie draft**, para não distorcer os valores. Se a abertura
da intertemporada depende do E4-a, o início está sendo **atrasado por arrasto**.

**Motivação:** o handoff de fechamento da maratona OFF26 listou **"E4-a (ESPN definitivo) +
Season Rollover aplicados"** como pré-condições do smoke da janela de cortes (OFF26-1), e a
spec **D8** da OFF26-1 fixou que a janela roda **pós-rollover** (para ler salário
**valorizado**). O owner levantou a suspeita de que o **E4-a entrou na lista por arrasto**: o
que realmente importa para **abrir a janela** seria o **rollover + `needs_review` zerado**
(gate D3), **não** o ESPN. Os dois relógios — o da **intertemporada** (rollover, logo após o
fim da temporada) e o do **ESPN** (E4-a, perto do rookie draft) — seriam **independentes**.
Se for o caso, a intertemporada pode começar **antes** do ESPN definitivo, sem esperar o E4-a.

**Escopo da investigação (3 perguntas — a F1 responde read-only):**
1. **Rollover × ESPN** — o Season Rollover (passo 4) **depende** do import ESPN definitivo
   (E4-a) ou opera sobre **outra base**? (i.e., a VALORIZAÇÃO/renovação do rollover lê
   `espn_ref_value` já gravado no DB — e esse valor precisa ser o **definitivo** ou o
   **preliminar** já basta para rollar?)
2. **O que a fase habilita/bloqueia** — o que o estado **"intertemporada"** e **cada passo**
   do workflow de fato **habilitam e bloqueiam no código** (`is_offseason`,
   `_get_step_statuses`, flags individuais de AppConfig, gates de abertura)?
3. **Pré-condição real de abertura** — a abertura da janela de cortes ([[OFF26-1]]) exige
   **E4-a** (ESPN definitivo) ou **apenas rollover + `needs_review` zerado** (gate **D3**)?
   Confirmar se o E4-a é dependência **real** da abertura ou **arrasto** do handoff.

**Hipótese a confrontar:** a dependência do E4-a na **abertura** da janela é **por arrasto**;
o gate real de abertura é **`needs_review` zerado (D3)** + rollover aplicado. O E4-a seria
dependência de **dados de salário** (para o salário valorizado que a janela exibe via budget
não-projetado, D9), mas **não** um gate temporal que precise ocorrer **antes** do início da
intertemporada.

**Conceitos a mapear na F1:** rollover (passo 4, `apply_season_rollover` /
`/api/offseason/rollover`); gate de abertura da janela (**D3** — `needs_review` zerado);
`_get_step_statuses` e o backing do passo 6; estado de fase da intertemporada
(`get_current_season` / `is_offseason` sobre AppConfig k-v).

**Natureza:** **investigação** — a execução é a **F1 (MAN-OFF26-PHASE-F1, diagnose
read-only)**, despachada em **prompt separado** (não agora). **Sem F2 próprio garantido**: os
achados que exijam mudança viram **itens individuais**.

**Restrições de escopo (deste registro e da investigação):** **não** reabre as decisões
**D1–D11** da [[OFF26-1]] (o item investiga **acoplamento de fase**, não a mecânica da
janela); **não** altera código, schema, `salary_engine`, sync, nem os specs já arbitrados de
OFF26-1/OFF26-2.

**Ref. cruzada:** [[OFF26-1]] (janela de cortes — spec **D8** pós-rollover, gate **D3**
`needs_review`, **D9** budget não-projetado), [[OFF26-2]] (keeper sheet), [[E4-a]] (matcher
ESPN, ⚠️), [[E4-c-1]] (store ESPN canônico, ✅). Série **OFF26** (intertemporada).

#### F1 — Diagnose read-only (MAN-OFF26-PHASE-F1, 17/06/2026) ✅ — zero mutação

Diagnose estritamente read-only contra o código atual. **Confirma a suspeita do owner:**
nenhum gate de código acopla a abertura da janela (nem o rollover) ao **E4-a**. O E4-a entrou
nas pré-condições do smoke **por arrasto de spec/handoff** (D8 + handoff de fechamento), não
por dependência funcional. Os quatro vereditos:

**(1) Rollover × ESPN — COMPUTACIONALMENTE acoplado ao DADO, NÃO gated no E4-a (evento).**
- O cálculo `apply_season_rollover(p)` ([salary_engine.py:190-213]) lê como insumo
  `p.espn_ref_value` (+ `p.salary` prev, `p.acquisition_type`, `p.contract_year`). ESPN **é**
  entrada da VALORIZAÇÃO/renovação. Com `espn_ref_value=0` a valorização degrada para
  `MAX(prev_salary, floor(0.5×0)) = prev_salary` — **roda mesmo sem ESPN**, só produz valor de
  baixa qualidade.
- A rota `do_rollover` ([offseason.py:657-701]) é **gated no nível do workflow** por
  `step4.locked = not (lottery_locked and espn_updated)` ([offseason.py:193]). Mas
  `espn_updated` = flag **`espn_values_updated`**, setada **manualmente** por `confirm_espn`
  ([offseason.py:645-650], passo 3 = "marcar como atualizado") — **NÃO** pelo import E4-a. O
  import ESPN (`routes/admin.py`) **não escreve** `espn_values_updated` (grep: zero ocorrências
  em admin.py). Logo o gate do rollover é satisfeito por um **checkbox do admin**, agnóstico a
  *qual* import (preliminar ou definitivo) rodou.
- **Veredito:** o rollover **pode rodar sobre ESPN preliminar**; a base de cálculo é
  `Player.salary` + `Player.espn_ref_value` (o que estiver no DB) + tipo/ano. "Rollover depende
  do E4-a" = **premissa parcialmente falsa (arrasto)**: depende do *dado* `espn_ref_value`
  presente e de uma *flag manual*, não do **evento** E4-a.

**(2) O que a fase habilita/bloqueia — quase tudo é RÓTULO; só 2 gates funcionais duros.**
- `offseason_mode`/`is_offseason()` ([models.py:45-46]) é **uma flag setada `true` SÓ no
  rollover** ([offseason.py:692]) e **nunca revertida por código** (só o seed default
  `false`, [app.py:410]; é o sintoma do [[M1-FOLLOWUP]]). Gateia **apenas cosmético**: banner
  de offseason ([base.html:142]) e banner de cap estourado M1 ([roster.html:72]). **Não** trava
  trades/auction/escrita. Nuance temporal: a flag de "fase" só liga **no passo 4**, não no
  fechamento da temporada (passo 1) — o "estado intertemporada" como flag **atrasa** o início
  real do workflow.
- Status dos 7 passos (`_get_step_statuses`, [offseason.py:168-209]) é majoritariamente
  **UI/label**. "locked" duro só em **passo 2** (`not standings_exist`) e **passo 4**
  (`not (lottery_locked and espn_updated)`). Passos 1/3/5/6/7 **nunca** travam.
- **Gates funcionais reais que bloqueiam ação:** só **(a)** rota do rollover (gate do passo 4)
  e **(b)** abertura da janela de cortes (gate `needs_review`, ver §3). Todo o resto é
  rótulo/cosmético.
- **Veredito:** a "fase intertemporada" é **mistura** — predominantemente label de UI (banner +
  display de passos), com **dois** gates funcionais isolados (rollover, abertura de cortes).

**(3) Pré-condição de ABERTURA da janela — SÓ `needs_review` zerado. NÃO E4-a, NÃO rollover.**
- `admin_open_window` ([cuts.py:183-197]) checa **exatamente dois** itens: (i) `_window_locked`
  falso (não há audit canônica ainda) e (ii) `_pending_review_count() == 0`
  ([cuts.py:53-55, 190-195], conta `Player.needs_review=True, is_dropped=False`).
- **Não** checa `espn_values_updated`, **não** checa E4-a, **não** checa `rollover_done`. Grep
  confirma: `cuts.py` não referencia nenhuma flag de ESPN nem de rollover.
- **Veredito (suspeita do owner CONFIRMADA):** abrir a janela exige **apenas `needs_review`
  zerado** (+ não estar já travada). **E4-a: NÃO** (arrasto puro). **Rollover: NÃO** sequer é
  gate de código — o "pós-rollover" da **D8** e o "E4-a + rollover aplicados" do handoff são
  **convenção de processo / correção de dado** (para o budget não-projetado **D9** exibir
  salário **já valorizado e definitivo**), não trava de abertura. O acoplamento real
  E4-a→janela é **transitivo via salário exibido**: a janela (D8) mostra `p.salary`
  pós-rollover; esse salário só é "definitivo" se o rollover tiver lido ESPN definitivo. Não há
  nada no código que force essa ordem.

**(4) Réplica — em geral fonte única por preocupação; 1 duplicação leve + gates NÃO compartilham camada.**
- `_get_step_statuses` ([offseason.py:168]) é a fonte única do status/locks dos passos;
  consumida por `offseason_page`, `/api/offseason/status` e pelo próprio `do_rollover` (relê o
  step 4). ✔ única.
- `is_offseason()` ([models.py:45]) — helper único; exposto via context processor
  `g_offseason_mode` ([app.py:89]) e lido nos templates ([base.html:142], [roster.html:72]). ✔
  única.
- `espn_values_updated` — escrita só em `confirm_espn` ([offseason.py:649]); lida só em
  `_get_step_statuses` ([offseason.py:176]). ✔ única.
- **Duplicação leve (mesma query, 2 lugares):** "janela travada/passo 6 done" é computado em
  `cuts.py` (`_window_locked`, [cuts.py:38-41]) **e** em `_get_step_statuses` (`cuts_done`,
  [offseason.py:181-183]) — ambos `CutWindowAudit.filter_by(season, is_canonical=True)`. Não é
  bug (read-only, mesma verdade), mas é o local a alinhar se a semântica mudar.
- **Achado estrutural (relevante p/ qualquer fix futuro):** o **gate de abertura da janela**
  (D3 `needs_review`) vive **só em `cuts.py:admin_open_window`**, **totalmente separado** do
  `_get_step_statuses`. As travas do workflow offseason e a trava da janela de cortes **não
  compartilham camada de pré-condição**. Logo, se um item futuro quiser "abertura exige
  `rollover_done`" (ou explicitamente *desacoplar* do ESPN), a mudança é em **`cuts.py`**, não
  no helper de passos — e não há réplica a fechar além disso.

**Classificação das premissas do contexto:**
- *"Abertura acoplada ao E4-a"* → **arrasto (premissa falsa no código)**: o único gate de
  abertura é `needs_review` zerado. Item de correção candidato: **desacoplar formalmente** —
  revisar a pré-condição de smoke da [[OFF26-1]] (handoff) e a redação da **D8** para separar
  "janela pós-rollover" (timing) de "ESPN definitivo" (qualidade de dado), **sem reabrir D1–D11**.
- *"Rollover depende do ESPN definitivo"* → **deslocamento**: depende do **dado**
  `espn_ref_value` (qualquer) + flag manual `espn_values_updated`, não do **evento** E4-a; pode
  rodar sobre preliminar.
- *"Relógios intertemporada (rollover) × ESPN (rookie draft) independentes"* → **confirmada no
  código**: nenhum gate liga abertura/rollover ao E4-a; o E4-a só é insumo de *qualidade* do
  salário valorizado (rollover) e do salário de rookie (`floor(ESPN×1.2)`, passo 5).
- *"D8 justifica timing só por salário valorizado, não menciona ESPN"* → **imprecisa**: a D8
  **bundla** "ESPN definitiva E4-a + regra de valorização" na dependência de dado
  ([improvements.md], D8 da OFF26-1). É exatamente nesse bundle que o E4-a entrou — mas é
  **decisão de spec, não trava de código**.

**Natureza do desfecho:** divergência confirmada (acoplamento por arrasto). **Sem F2 próprio
garantido** — o achado vira insumo de uma revisão de redação/processo da pré-condição de smoke
da OFF26-1 (handoff + D8), que é **decisão do owner**, não mudança de código. Nenhum gate de
código precisa mudar para a intertemporada começar antes do E4-a: o código **já** permite abrir
a janela com só `needs_review` zerado.

#### FIX — correção de redação/microcopy (MAN-OFF26-9, 17/06/2026) ✅ smoke do microcopy conferido em prod — sem mudança de lógica

Separados, nos pontos onde a redação os havia fundido, o **TIMING "pós-rollover"** (qualidade
de dado: budget valorizado) da **QUALIDADE DE DADO "ESPN definitivo (E4-a)"** (exatidão de
valor + salário de rookie no draft, posterior), deixando explícito que a **abertura** exige
**só `needs_review` zerado**. **Nenhum gate, rota, schema, salary_engine, sync ou decisão
D1–D11 tocados** — só texto de orientação.

- **`templates/offseason.html`** (microcopy do passo 6 "Definir Keepers / Cortes"): trocado
  "Pressupõe o Rollover já aplicado" por texto que distingue **abertura** (só `needs_review`
  zerado) de **recomendação** (rodar rollover antes → budget valorizado; "qualidade de dado,
  não pré-condição"). **Único artefato de runtime** — texto estático dentro do `<p>` existente,
  **sem Jinja/condição/CSS novos** (grep: nenhuma condição de gate no bloco do passo 6).
- **`improvements.md`** — OFF26-1: **D8** ganhou esclarecimento anexo (sem alterar a decisão);
  a linha **"Dependências"** foi reescrita separando pré-condição de abertura (`needs_review`)
  das recomendações de qualidade de dado (rollover/E4-a); a nota de dependência de dados do
  OFF26-7 (seção F2) idem.
- **`handoff_code_manager_16_06_2026_pt12.md`** — item 2 das pré-condições de smoke reescrito
  com a mesma distinção (abertura = `needs_review`; rollover/E4-a = qualidade de dado).

**Verificação:** `grep` confirma que o passo 6 do `offseason.html` não tem nenhuma condição de
gate (`{% if %}` de trava) ligada ao texto alterado — a mudança é puramente de redação. As
demais edições são documentais. **Comportamento de fluxo inalterado.**

---

### E4-a — Matcher do import ESPN resolve por `sleeper_id` (Brown-safe)
✅ **Concluído (23/06/2026) — smoke prod do import real OK** — Prioridade **Alta** — fatia de **[[E4]]** (MAN-E4-F1/F2/PRODF1/F2-EixoA/DONE) — **absorve o conserto do matcher ex-[[E2-RISK]]; fecha a raiz que o F2 do E2-RISK só paliou**

> **Fechamento (MAN-E4a-DONE, 23/06/2026):** filtro de posição (commit 97b90ed) deployado em prod e validado com import ESPN real (cheat sheet PPR Top 300, Temporada 2026). **Eixo A fechado:** D/ST só recebem candidato de posição compatível (Broncos D/ST → só Denver Broncos DEF); as demais D/ST sem entrada no índice caem limpas em "Não Encontrados", sem skill (sem Stefon Diggs / Tank Dell / Calvin Austin). **Sem regressão:** ramo skill intacto (Antonio Williams ainda recebe candidatos skill); rookies skill 2026 (Carnell Tate, Jeremiah Love, Jadarian Price…) seguem not_found → store. **Split de prod: 211 matched (por sleeper_id) / 5 aproximados (4 D/ST casando consigo) / 84 não encontrados (→ store) / 62 ausentes no PDF.** Gates de ✅ satisfeitos.

> **Caminho p/ ✅ (gate explícito, sem inércia de localhost):** deploy do commit do filtro → import ESPN real em prod → no review, conferir (a) **nenhuma D/ST ou K exibe candidato skill** (Texans D/ST sem Diggs; Rams D/ST sem Sanders) e (b) colher o **split** (matched-por-id / approximate / not_found→store). Com (a)+(b) confirmados, **E4-a e E2-RISK → ✅** (flip viaja junto da confirmação de prod).

**F2 — IMPLEMENTAÇÃO (09/06/2026, ⚠️ validado em localhost)**
- **`espn_pdf_parser.match_players(parsed, db_players, sid_resolver=None)`** ganhou o
  parâmetro injetável `sid_resolver`. Em modo resolver, a identidade é por **`sleeper_id`**:
  sid → Player rosterado = **matched por id** (sem review); sid → não-rosterado =
  **not_found** (vai p/ o store no confirm — **nunca oferecido como match de veterano**);
  sem sid limpo = fallback **igualdade exata** de nome (matched) ou **review**
  (approximate). **Sem auto-match silencioso por similaridade** no modo resolver. Modo
  legado (`sid_resolver=None`) **preservado byte-a-byte** (testes/retrocompat).
- **`routes/admin.py`:** extraídos `_build_pool_index()` + `_resolve_entry_sid(entry, idx)`
  (fonte única Brown-safe nome+team, reusada pelo store E2 — `_resolve_not_found_to_store`
  refatorado p/ usá-los). `espn_import_page` constrói o índice do pool e passa
  `sid_resolver` ao matcher; pool indisponível → `None` → fallback gracioso (sem 500).
- **Não toca** `salary_engine` (puro), camada de armazenamento (escrita segue em
  `Player.espn_ref_value` via id — store canônico é [[E4-c]]), nem `SalaryHistory`/
  `PlayerHistory`. **Sem schema.** Reversível (remover o resolver volta ao legado).
- **Validação localhost (test_client + pool real, 11.810 nomes):** caso Tate/Mooney —
  "Carnell Tate" resolve ao sid 13279, vai p/ **not_found**, **não** entra em matched nem
  como candidato de approximate; **Mooney não recebe o valor**. Veterano (Jayden Daniels)
  **matched por sleeper_id**. Typo ("Jayden Daneils") → **review**. Sobrenome isolado
  ("Brown") **não resolve**. 2 nulos (Hollywood Brown, Cameron Ward) degradam sem match
  espúrio. Reimport **idempotente**. Confirm de matched-by-id grava `espn_ref_value`
  (=60.0); review renderiza 200. `salary_engine_test.py` 48/48.
- **Relação com [[E2-RISK]]:** o E2-RISK (default neutro + gate) permanece como a **camada
  de tela**; **E4-a é a raiz** (resolução por id) — juntos, o "Brown" não acontece nem por
  inércia (tela) nem por similaridade contra lista pobre (matcher).
- **Pendente:** smoke em prod com import ESPN real (medir split resolvidos-limpos vs.
  review).

**ESCOPO**
Trocar a resolução de identidade do import ESPN de **fuzzy contra o roster local** (origem
do hazard "Brown", `match_players`) por **resolução da entrada ESPN → `sleeper_id` contra
o pool global do Sleeper**, reusando `_load_players_db` / `_norm_name` / desambiguação
nome+team **Brown-safe** (sem substring/sobrenome) já existente em
`_resolve_not_found_to_store`. Escrita continua em `Player.espn_ref_value` via
`find_player_by_sleeper_id` (sem mudança de schema). `approximate`/review fica só para
**ambiguidade genuína**.

**POR QUÊ AGORA**
Independente da reconciliação de tabelas; entrega a **eliminação do "Brown" na raiz** + a
troca **corrupção→miss** (falha segura/visível). Reversível, sem schema, maior
retorno/risco. Substitui o "conserto do matcher" que saíra do E2-RISK (cujo F2 entregou
só o mínimo de tela).

**INVARIANTES A PRESERVAR**
- `salary_engine` puro (não tocar); idempotência do import/confirm; Brown-safety
  (nome+team, nada de substring); `SalaryHistory`/`PlayerHistory` intactos.

**DEPENDÊNCIAS**
- Fatia de **[[E4]]**. Fecha a raiz do **[[E2-RISK]]** (cujo F2 foi paliativo de tela).
  Não depende de [[E4-b]]/[[E4-c]].

**Diagnose PRODF1 (MAN-E4a-PRODF1, 23/06/2026 — read-only, Opus) — por que o review ainda mostra fuzzy espúrio em prod**

Contexto: import ESPN real do owner (cheat sheet PPR Top 300) mostrou D/ST recebendo skill como candidato (Texans D/ST → Stefon Diggs; Rams D/ST → Raheim Sanders) e rookies 2026 em "Não Encontrados (76)", com similaridade colapsando em 52.2%/50.0%. Suspeita do owner: prod estaria em **modo legado** (fuzzy contra roster). **Refutada pela evidência.**

- **H1 (resolver inativo / fallback legado por pool vazio) → REFUTADA.** O wiring que liga o legado existe (`admin.py:630` `_sid_resolver = ... if _pool_idx else None` → pool vazio cai em `match_players` modo legado, auto-match 0.82/0.65). **Mas não foi acionado.** Prova: no modo legado o threshold de approximate é **`>= 0.65`** (`espn_pdf_parser.py:262`); no modo resolver é **`>= 0.5`** (`:239`). As sugestões observadas estão em **0.50/0.522 — abaixo de 0.65**, logo só podem vir do modo resolver. Reforço: rookies caem em not_found **com `resolved_sid`** (`:204`), comportamento exclusivo do resolver. **O resolver ESTÁ ativo; o pool carregou.**
- **H2 (código E4-a ausente/divergente em prod) → REFUTADA** (sujeito a confirmar o commit deployado no Render, que não é lível daqui). A assinatura comportamental (threshold 0.5 + rookie→not_found com sid limpo + select default neutro do E2-RISK em `espn_review.html:64`) é a do E4-a/E2-RISK, não a do legado.
- **H3 (lógica de sugestão replicada fora do matcher) → REFUTADA.** A similaridade/candidatos são computados **só** em `match_players` (`espn_pdf_parser.py:226,244`), persistidos em `.espn_review_pending.json` (`admin.py:644-652`) e **apenas renderizados** por `espn_review.html:56,67`. Nenhum recálculo em template/JS/rota. A lógica que produz o candidato espúrio **mora no próprio matcher** — no ramo resolver-mode de fallback (`:236-251`), fonte única, não replicada.

**Causa-raiz (CÓDIGO, não dado/ambiente):** no modo resolver, toda entrada que **não resolve a um sid** (D/ST sempre — são excluídas do índice em `admin.py:508`; rookie eventual que erre o pool) cai no ramo `:236-251`, que monta candidatos por **fuzzy `>= 0.5` SEM filtro de posição/identidade**. O bônus de posição (`:228-231`) só soma +0.05, **não filtra** cross-position. Logo uma D/ST recebe skill como sugestão. Gap de desenho do E4-a presente desde a F2 (não regressão, não degradação) — não pego no smoke localhost (sheet/roster local não cruzou D/ST > 0.5).

**Eixos:**
- **Eixo A (D/ST + K com sugestão skill espúria) = BUG DE UI/SUGESTÃO (residual do E4-a).** A exclusão de D/ST do índice e do store (`:508`, `:550`) é **intencional**; o resíduo é só a tela oferecer candidato skill (falta filtro de posição no ramo `:236-251`). **Severidade baixa/cosmética:** o confirm é gated por default neutro (E2-RISK) e o `_resolve_not_found_to_store` pula K/DST (`:550`) — sem risco de corrupção, só ruído.
- **Eixo B (rookies skill 2026 em not_found) = COMPORTAMENTO INTENCIONAL (E4-a funcionando).** Rookie resolve a sid → não-rosterado → not_found → store no confirm (reproduz o caso-âncora Carnell Tate de localhost). A premissa "rookie em not_found = bug" é **falsa**. A única anomalia adjacente seria a sugestão fuzzy aparecer junto (mesmo mecanismo do Eixo A) caso um rookie erre o pool.

**Refutação de premissas (DEV_METHODOLOGY):** (a) "parece modo legado/fuzzy contra roster" → **premissa falsa** (threshold 0.5 = resolver); "rookie em not_found = bug" → **premissa falsa** (E4-a correto); "ausência de âncora de posição" → **deslocamento** (o bônus existe em `:228-231`, mas é nudge, não filtro). (b) ausentes do report: o gate de confirm do E2-RISK e o skip K/DST do store **mitigam** a severidade (sem corrupção) — **comportamentos existentes não creditados**.

**Veredito final:** problema de **CÓDIGO** (gap de desenho no ramo resolver-mode), não de dado/ambiente. **Próxima fase = F2 do E4-a** (não item novo, não só re-smoke): guardar o fallback de candidatos por **filtro de posição/identidade** (entrada D/ST/K nunca recebe skill; idealmente nenhuma entrada recebe candidato de posição incompatível). O núcleo do E4-a/E2-RISK **passou** no smoke de prod (resolver ativo, rookie→store, zero corrupção por inércia) — candidato a destravar o ⚠️→✅ desses claims, com o Eixo A como resíduo rastreado na F2.

**F2 do Eixo A — IMPLEMENTAÇÃO (MAN-E4a-F2-EixoA, 23/06/2026, ⚠️ validado localhost; pendente smoke prod):**
- **`espn_pdf_parser.py`:** helper `_special_pos_compatible(entry_pos, cand_pos)` + ramo
  especial no modo resolver de `match_players`. Entrada **D/ST ou K** recompõe best/candidatos
  **só entre posições compatíveis** (D/ST → DEF/DST; K → K); sem candidato compatível ≥0.5 →
  **not_found limpo**. O ramo **skill segue inalterado** (sem filtro skill×skill — fora do
  escopo). **Modo legado (`sid_resolver=None`) intocado** (mudança 100% dentro de
  `if sid_resolver is not None`). Não toca `salary_engine`/store/sync/schema/`SalaryHistory`/
  `PlayerHistory`; gate de confirm + default neutro do [[E2-RISK]] **intactos** (só confirmados).
- **Validação localhost (harness sintético + `salary_engine_test.py` 48/48):** Texans D/ST →
  not_found (não oferece Diggs WR); Rams/Ravens D/ST → not_found (sem skill cruzado);
  **sem regressão** — Carnell Tate (rookie) → not_found via `resolved_sid` (Eixo B intacto),
  Jayden Daniels (vet rosterado) → matched por id. Modo legado reproduz o baseline.
- **Pendente p/ ✅:** smoke em prod (ver gate acima) — confirmar filtro ativo na tela + colher
  o split numérico (resolvidos / review / store) que o claim do E4-a deixou em aberto.

---


### E2-RISK — Fuzzy oferece rookie como match de veterano no review (classe "Brown")
✅ **Concluído (23/06/2026) — smoke prod OK (via [[E4-a]])** — Prioridade **Média** — MAN-E2RISK-REG/F1/F1B/F2/DONE — **RE-ESCOPADO (híbrido): E2-RISK = só o mínimo de tela; conserto do matcher (raiz) → [[E4-a]]**

> **Fechamento (MAN-E4a-DONE, 23/06/2026):** default neutro + gate de confirm confirmados em prod no mesmo import real — nenhum valor gravado por inércia; com a F2 do Eixo A do [[E4-a]] (commit 97b90ed) a sugestão espúria nem aparece mais na origem. Split de prod: 211 matched / 5 aproximados / 84 não encontrados / 62 ausentes no PDF. Gate satisfeito.

**F2 — IMPLEMENTAÇÃO (09/06/2026, ⚠️ validado em localhost)**
- **Mudança única (camada de tela):** `templates/espn_review.html` — o `<select>` de cada
  approximate passa a iniciar **NEUTRO** (`<option value="" selected>— selecionar —`);
  removido o `selected` que pré-escolhia o `best_player` (veterano). **Não toca** matcher,
  `salary_engine`, `ESPNValue`, `RookieEspnValue`, sync nem schema.
- **Gate de confirmação (já existente, agora ativado pelo default neutro):**
  `getApproxResolutions` conta select vazio como não-resolvido e `updateStatus()` (no load
  + a cada `change`) desabilita `#btn-confirm` enquanto houver pendência. Confirm só
  habilita quando **toda** approximate tem escolha explícita (match ou "Nenhum (aplicar
  $1)").
- **Caminho de escrita inalterado:** resolução explícita a um veterano ainda grava via
  `_save_espn_value` (a F2 só impede confirm-por-inércia, não muda o que a escrita faz).
- **Smoke prod 23/06 (via [[E4-a]] PRODF1):** o default neutro + gate **confirmados em
  produção** — mesmo com a sugestão fuzzy espúria de D/ST (Texans D/ST → Stefon Diggs),
  nenhum valor é gravado por inércia. O E2-RISK (camada de tela) **passou**; o resíduo da
  sugestão aparecer é do matcher (Eixo A → F2 do [[E4-a]]), não desta camada.
- **F2 do Eixo A aplicada (23/06, no [[E4-a]]):** o filtro de posição no matcher remove a
  sugestão espúria na origem; este item **→ ✅ junto do [[E4-a]]** assim que o smoke prod do
  filtro confirmar (mesmo gate). Status segue ⚠️ até lá (sem flip por inércia de localhost).
- **Validação localhost (test_client, DB copiado):** review renderiza sem pré-select
  (option neutra `selected`, nenhum candidato `selected`); confirm **sem ação** NÃO altera
  o `espn_ref_value` do veterano (32.4→32.4 — Mooney não recebe o valor de Tate); confirm
  com resolução explícita grava normal (32.4→48.0); auto-matched/not_found intactos.
  `salary_engine_test.py` 48/48. **Pendente:** smoke em prod com import ESPN real.

**CONTEXTO**
Achado durante o **[[E2]]**-F2 (08/06/2026), registrado como risco residual no E2 e no
handoff, agora item próprio. No **review do import ESPN**, o matching fuzzy pode
oferecer um **rookie** como candidato de match a um **veterano real do DB** por
falso-positivo de similaridade. Caso observado: **"Carnell Tate"** (rookie) ~
**"Darnell Mooney"** (veterano), similaridade **0.665**. A mitigação do E2 cobre apenas
o caso em que o approximate é **pulado** (skip — o valor do rookie é capturado no store
mesmo assim); **não** cobre o caso em que o admin **confirma** o match falso.

**PROBLEMA / OPORTUNIDADE**
Se o admin confirmar um match falso no review (aceitar "Carnell Tate" → "Darnell
Mooney"), o valor ESPN do rookie **contamina o `espn_ref_value` de um veterano real**
(Mooney receberia o valor de referência do Carnell Tate). É a **classe do incidente
"Brown"** (Marquise / A.J. / Amon-Ra St. Brown com salários trocados por match
parcial). Risco latente de corrupção de dado em prod, dependente de erro humano no
review.

**DISCUSSÃO**
- O hazard é específico do **fluxo de confirmação do review** do import ESPN.
- A entrada problemática é justamente uma que **já resolve para o `sleeper_id` de um
  rookie** (via pool global do Sleeper) — o sistema tem como saber que aquele candidato
  "é rookie" e mesmo assim o oferece como match contra um veterano.
- Fix delineado no E2 (a confirmar/refinar na F1): **não oferecer** como fuzzy-match
  contra veterano do DB uma entrada que já resolve para o `sleeper_id` de um rookie; ou
  **rebaixar/sinalizar** esses candidatos no review para o admin não confirmar por
  engano.

**DECISÕES JÁ TOMADAS**
- Item **próprio** (separado do E2), focado no caminho de **confirm errado** (o *skip*
  já está mitigado).
- O **matching canônico** (exato → case-insensitive → normalizado, sem substring/
  sobrenome isolado) **não muda** — o foco é o que o review *oferece* como candidato
  fuzzy.

**QUESTÕES EM ABERTO** (F1)
- Onde exatamente o review monta a lista de candidatos fuzzy de match contra o DB, e em
  que ponto uma entrada rookie (resolvível a `sleeper_id` no pool) poderia ser
  excluída/sinalizada?
- Essa lógica de "oferecer candidato fuzzy" existe em mais de um lugar (rota, template,
  JS do review)? (réplica)
- O sinal "esta entrada é rookie" (resolve a `sleeper_id` de não-rosterado) está
  disponível no momento em que os candidatos são montados, ou exigiria resolução
  adicional?
- Há outros consumidores do mesmo mecanismo de candidatos fuzzy além do confirm de
  `espn_ref_value`?

**F1 — ACHADOS (diagnose read-only)**
- **Hazard nasce em `match_players`** (`espn_pdf_parser.py`): fuzzy via
  `difflib.SequenceMatcher` **contra o roster local apenas**. Faixa `0.65 ≤ r < 0.82`
  → `approximate` com `candidates[:5]` (qualquer DB player com `r ≥ 0.5`). Tate~Mooney
  cruza 0.665 por **falta de candidato melhor local**.
- **Sem réplica:** a lógica fuzzy é **fonte única server-side** (`match_players`); o
  template `espn_review.html` só renderiza os candidatos no `<select>` e o JS
  (`getApproxResolutions`) lê `sel.value` — **não recomputa nada no cliente**.
- **Sem outros consumidores:** `match_players` tem um único caller
  (`admin.py:610`); `/admin/review` (M2) é código distinto (`needs_review` do sync),
  não candidatos fuzzy.
- **Agravante:** o `<select>` **pré-seleciona o `best_player`** (veterano —
  `espn_review.html:62` `selected if c.player_id == a.player_id`) e o JS trata
  **qualquer `sel.value` truthy como resolvido** → **confirm sem interação** grava o
  valor do rookie no `espn_ref_value` do veterano via `_save_espn_value`
  (`admin.py:746-760`) — **escrita direta no confirm, NÃO passa por
  `record_acquisition`**.

**F1B — ACHADOS (diagnose complementar: `espn_ref_value` por `sleeper_id`?)**
- `espn_ref_value` é lido como **atributo de Player** por `salary_engine`
  (rollover/projeção — **puro, sem DB**), `models`, e templates. Virar "resolvido por
  `sleeper_id`" **violaria a pureza da engine** ou exigiria **materializar no Player de
  qualquer forma** (a coluna não sumiria).
- **Três tabelas de valor ESPN** sob chaves distintas: `Player.espn_ref_value`
  (player), `ESPNValue` (player_id+season, exige Player), `RookieEspnValue`
  (**sleeper_id**+season, hoje transitório). Unificar exige **chave nova
  `sleeper_id+season`** e **inverter o store de transitório→canônico**.
- **`sleeper_id` não é confiável em todo Player** (`import_csv` cria Player sem ele;
  preenchido só quando o sync casa) → **chave de junção furada hoje**.
- **Ganho de segurança lateral:** resolver por id contra o pool (nome+team Brown-safe)
  troca a classe de falha de **"corrupção/escrita errada"** por **"miss/não escreve"**
  (ambíguo → não chuta) — estritamente mais seguro. Ressalva: pode **sub-resolver**
  (miss) onde o roster acertava se o team da entrada estiver stale.
- **Conclusão F1B:** a unificação é correta e elegante, mas é **redesenho de camada de
  dados**, não fix de segurança → F2 no escopo menor; unificação como item à parte.

**RE-ESCOPO + DECISÃO HÍBRIDA (owner, pós-F1B)**
- **E2-RISK passa a ser SOMENTE o mínimo de tela:** remover o **pré-select do veterano**
  no review do import ESPN, de modo que um **confirm sem interação não grave valor em
  veterano** (default seguro). **Não toca** matcher, `salary_engine`, `ESPNValue` nem
  schema. Risco quase nulo, para a corrupção **agora**.
- **O conserto do matcher (resolução por `sleeper_id`) sai do escopo do E2-RISK** e passa
  a fazer parte do item de design da estrutura ESPN — agora a fatia **[[E4-a]]** (o E4
  foi fatiado na F1 de design), onde matcher (resolução por id) e armazenamento
  **convergem para a chave certa**, em vez de mexer no matcher sobre fundação ainda não
  decidida.

**DEPENDÊNCIAS**
- Relaciona-se com: **[[E2]]** (mesma área de resolução de import ESPN), **[[E3]]**
  (limpeza da UI de import ESPN) e **[[E4-a]]** (recebe o conserto do matcher — fecha a
  raiz que o F2 do E2-RISK só paliou).
- Não bloqueia itens abertos.

---


### PROC1 — Gate de ✅ exige confirmação do hash deployado live em prod
✅ **Concluído (23/06/2026) — Forma 1 ancorada no `DEV_METHODOLOGY`** — MAN-PROC1-REG/F1/DONE — **registro de processo**; robustez extra (surfacear o hash no `/admin`) fica como **PROC2** (follow-up separado).

> **Fechamento (MAN-PROC1, 23/06/2026):** F1 recomendou a **Forma 1** (afinar o gate existente, não criar checklist/automação nova). A regra foi **afinada no bullet de gate de ✅ da seção "Checklist de fim de sessão" do `DEV_METHODOLOGY.md`** (transversal manager+optimizer — ambos deployam no Render): fechamentos com gate de smoke em prod exigem confirmar que o **hash deployado live = o commit validado** (não basta commitado/pushado); escopo limitado a gates de prod (localhost não afetado). Reforçou o bullet existente, **sem seção paralela**. Ressalva da F1 (gate de disciplina não é à prova de falha — E1) endereçada por **PROC2** (surfacear `RENDER_GIT_COMMIT` no `/admin`), fora deste escopo.

**Lição de processo** que emergiu **duas vezes**: **"o código foi commitado/validado" ≠ "o código
está rodando em prod".** Para itens cujo ✅ depende de **smoke em produção**, o gate atual não exige
confirmar que o **hash deployado live** é o commit que contém a mudança validada — deixando espaço
para marcar ✅ (ou rodar um smoke "de prod") contra binário antigo.

**REGRA CANDIDATA (forma a refinar):**
> Para qualquer item cujo ✅ tenha **gate de smoke em produção**, o fechamento passa a exigir
> **confirmação explícita de que o hash deployado live em prod é o commit que contém a mudança
> validada** — não basta "commitado" nem "pushado". Confirmar no painel do Render (deploy live = hash
> esperado) **antes** de confiar no resultado do smoke e antes de flipar ✅. **Escopo:** só
> fechamentos com gate de prod; itens validáveis só em localhost (sem gate de prod) não são afetados.

**CASOS-ÂNCORA (mesma família — validado ≠ deployado):**
- **[[E1]] — ✅ prematuro pós-localhost → falha em prod.** Marcar ✅ por validação local, sem o
  comportamento confirmado no binário de produção, levou a falha em prod.
- **[[E4-a]] (23/06/2026) — smoke falho por hash divergente.** O primeiro teste de prod **reproduziu
  o comportamento pré-fix** porque o deploy live no Render era um commit **docs-only anterior
  (`927831a`, 17/06)**, e não o commit do filtro (`97b90ed`), que **nunca tinha sido pushado**. O
  smoke só virou confiável depois de confirmar, no painel do Render, que o deploy live passou a ser
  o hash correto (`927831a..97b90ed`). Sintoma da classe: **smoke reproduz o comportamento pré-fix
  apesar de o código estar commitado/validado**, por divergência entre commit validado e hash live.

**DEPENDÊNCIAS:** transversal a todo item com gate de prod ([[OFF26-1]]/[[OFF26-2]], futuros smokes).
Não bloqueia itens abertos; absorvível como checklist de fim de sessão ou automação numa sessão futura.

---


---
### DP3 — Composição da lista de rookies do board de cap projector
✅ **Concluído 31/07/2026 — smoke em prod OK sobre hash `e12fdef` (PROC1 atendido)** — MAN-DP3-REG/F1/REFINE/F2/CLOSE — F1 + REFINE (diagnose/arquitetura), **F2 sob D1–D5** (snapshot materializado, postura P3), smoke prod validado. Migrado verbatim do `improvements.md` (O3) no fechamento.

**FECHAMENTO — SMOKE EM PRODUÇÃO (MAN-DP3-CLOSE, 31/07/2026)**

Smoke executado sobre o hash **`e12fdef`**, confirmado live no painel do Render (PROC1: hash
deployado = commit validado). Backup pré-deploy em **`/data/pre_dp3.db`**. Resultados:
- **Captura idempotente:** 1ª execução **148 entraram**; 2ª execução **0 entraram / 0 saíram**,
  total estável.
- **Board:** ordenado com os **valorados no topo**; **não-rookies ausentes**; **busca e filtro sem
  reload**; **cenário refletindo na barra fixa**.

**RESSALVA (não é defeito do DP3):** a captura em prod retornou **148**, contra **288** no smoke
local sobre o pool vivo. O 148 é exatamente o snapshot do pool de **12/06/2026** versionado no git.
O predicado e a captura operaram **corretamente sobre o pool que lhes foi entregue** — o board mostra
a classe de junho porque **é o que o pool em prod contém**. A causa é o **[[F13]]** (cache do pool
trackeado no git + mtime renovado a cada deploy ⇒ TTL de 168h nunca vence ⇒ pool congelado no
commit). **A completude da lista (classe corrente e inteira) depende da resolução do F13**, elevado
a Alta com janela antes do rookie draft (agosto). Fecha o DP3 como ✅ porque a mecânica entregue
(critério de classe, captura idempotente, board, gate) está correta e validada; o dado de entrada
(frescor do pool) é problema separado, próprio do F13.

**BAIXA DA RESSALVA (anexo — MAN-F13-CLOSE, 31/07/2026, hash `2cd8de3`):** o F13 foi **resolvido e
validado em prod**. Com o pool descongelado, a recaptura devolveu **287** (não mais 148) e o board
em prod passou a exibir a **classe entrante corrente e completa**. **A ressalva acima está baixada**:
o board não mostra mais a classe de junho. Fecha também a pendência que ficara fraca no DP3 — dos
**84** registros do import ESPN, apenas **12** pertencem à classe entrante (os 6 valorados + 6 a $1);
os demais 72 eram os não-rookies/veteranos não-rosterados que motivaram o item, corretamente **fora**
do board via `in_class`. (Registro anexado; o fechamento original do DP3 acima permanece intocado.)

**NOTA DE ARQUIVAMENTO:** seção abaixo preservada íntegra (histórico REG→F1→REFINE→F2). As
"Pendências de smoke em prod" listadas na F2 foram **satisfeitas** por este smoke, exceto a nº 4
(contagem de valorados × import real), que permanece um follow-up amarrado ao F13 — quando o pool
em prod for atualizado (F13) e o import ESPN da season rodar, confere-se a interseção `in_class` ×
valor>0 no topo do board.

---

⚠️ **[registro histórico — status no fechamento da F2, antes do smoke prod]** — MAN-DP3-REG/F1/REFINE/F2 — F1 + REFINE (diagnose/arquitetura) concluídas; **F2 entregue sob D1–D5** (snapshot materializado, postura P3). Smoke 27/27 em DB temporário + `salary_engine_test` 48/48. **✅ só após smoke prod** (captura real + board na tela + hash live = commit).

**CONTEXTO**
O board "🏈 Planejamento de Rookie Draft" do cap projector (entregue no [[DP1]]-F2, revisado pelo
[[DP2]]) lista hoje as entradas de `RookieEspnValue` da season alvo. Essa tabela **não é uma lista
de rookies**: ela é populada no confirm do import ESPN com as entradas do Top-300 que **não
casaram com nenhum Player rosterado**, excluindo K/DST e valor $0. A F1 do DP1 (09/06/2026) já
havia registrado a nuance — "entrante ESPN-valorado não-rosterado, não estritamente rookie" — como
ressalva semântica aceita na época.

**PROBLEMA / OPORTUNIDADE**
Em smoke de produção (31/07/2026) o owner constatou que a ressalva vira **ruído na tela**:
(a) aparecem jogadores que **não são rookies da classe entrante** — veteranos não-rosterados e
rookies de classes anteriores; (b) **faltam rookies da classe**, porque quem está fora do Top-300
da ESPN nunca entra na tabela e portanto não existe para o board. O critério de inclusão vigente
("não-rosterado com valor ESPN") **não é** o critério que o header da seção promete.

**DECISÕES DO OWNER (tomadas — NÃO reabrir na F1)**
- **D1 — critério de inclusão:** o board deve listar **apenas rookies da classe entrante** — a
  classe draftada pela NFL mais recentemente. Após a realização do nosso rookie draft, a classe
  alvo passa a ser a seguinte. O **ponto de corte** entre uma classe e outra é questão aberta
  (ver Q1).
- **D2 — cobertura:** a lista deixa de ser limitada ao Top-300 da ESPN. A classe passa a vir do
  **pool global do Sleeper**, com valor ESPN quando houver e **$1 quando não houver** — este $1 é
  a regra vigente da liga para jogadores ausentes do Top-300, **não é dado inventado**.
- **D3 — filtro de status (REFINE, 31/07/2026):** entram na lista **apenas jogadores com status
  ativo na NFL**, excluindo os cortados. No pool atual: `active==True` → **151** dos 289 skill
  entrantes; acrescentando `status=='Active'` → **148** (3 com status diverso). O predicado exato
  (`active` vs. `active`+`status`) é detalhe de F2; a decisão é: **cortado não aparece**.

**QUESTÕES EM ABERTO (destino F1 — não responder no REG)**
1. Qual sinal define o corte da classe alvo, e quando ele vira.
2. Como ordenar a massa de entradas a $1, sem inventar dado.
3. Qual passa a ser o efeito de `clear_rookie_espn_store` se a lista não depender mais dela.
4. Se e como excluir do board rookies já draftados/rosterados.
5. Se K/DST seguem excluídos sob o critério novo.
6. Volume e custo de leitura do pool global no endpoint atual.

**REFERÊNCIAS (só citar, não alterar)**
- [[DP1]] — fonte da lista (`RookieEspnValue` por season) + ressalva semântica da F1.
- [[DP2]] — cadeia única de planejamento keep/corte + rookies.
- [[E2]] — store de valor ESPN + resolução via pool global do Sleeper (nome+team).
- [[E4-a]] — matcher por `sleeper_id`.

**F1 — ACHADOS (diagnose read-only, MAN-DP3-F1, 31/07/2026; sem alteração de código/schema/DB/template)**

*Base empírica:* pool global cacheado `.sleeper_players_cache.json` (11.578 entradas, snapshot
12/06/2026) + FantasyCalc `data/.dynasty_values_cache.json` (keyed por `sleeperId`, fetch
09/06/2026). Os 7 nomes citados foram inspecionados nominalmente nesse pool.

**Q1 — Fonte atual + os 7 nomes.** Caminho completo: import ESPN PDF (`admin.espn_import_page`) →
`match_players` → entradas `not_found` (não bateram com Player rosterado) → no confirm,
`_resolve_not_found_to_store(not_found, season)` (`admin.py:554`) filtra via
`_classify_not_found_entry` (exclui K/DST, valor≤0, sid ambíguo) e resolve o sid por
`_resolve_entry_sid` (pool global, nome+team **Brown-safe**) → `upsert_rookie_espn(season, …)` →
`RookieEspnValue`. O board lê `/api/cap_projector/rookies` (`salary.py:194`) =
`RookieEspnValue.filter_by(season=get_current_season()+1)` ordenado por `espn_adjusted desc, name asc`.
**Critério de inclusão VIGENTE:** "entrada do Top-300 ESPN que (a) não casou com Player rosterado,
(b) é skill (≠K/DST), (c) valor ESPN>0, (d) resolve a um sid **único** no pool". É **cego a classe**.
Os 7 entram pelo **mesmo** critério; o campo que os separaria sob D1 é `years_exp` no pool:
- Calvin Ridley (sid 4981, `years_exp=8`) → **veterano, NÃO-entrante** (FA não-rosterado no Top-300).
- Braelon Allen (sid 11576, `years_exp=2`) → **classe 2024, NÃO-entrante**.
- Terrance Ferguson (sid 12487, `years_exp=1`) → **classe 2025, NÃO-entrante**.
- Germie Bernard (sid 13274, `years_exp=0`) → **classe entrante 2026 ✓**.
- Antonio Williams (`years_exp=0` sid 13301 **✓** / homônimo `years_exp=2` sid 7203) → entrante, mas
  homônimo (o entrante tem `team=None` → risco de desambiguação por team falhar).
- Jeremiyah Love (sid 13287, `years_exp=0`) → **entrante ✓**.
- Carnell Tate (sid 13279, `years_exp=0`) → **entrante ✓**.
→ 3 dos 7 (Ridley/Allen/Ferguson) **não são da classe entrante** = exatamente o defeito (a). Mesmo
critério p/ os dois grupos, confirmado.

**Q2 — Identificação de classe (campos do pool).** Disponíveis por jogador: `full_name`,
`first/last_name`, `team`, `position`, `fantasy_positions`, `age`, `college`, `birth_date`,
`years_exp`, `search_rank`, `status`, `active`, `number`, `depth_chart_*`, `metadata{rookie_year,
years_exp_shift,…}`, ids externos. Veredito de estabilidade p/ identificar classe entrante:
- **`years_exp` (int) — ÚNICO sinal viável.** `0` = classe entrante; estável dentro da season (a
  classe 2025 já está em `1` no snapshot de jun/2026, a 2026 em `0`). Vira `0→1` no rollover de
  league-year do Sleeper (~março, evidência: classe 2025 já em 1 em jun/2026) — **depois** do nosso
  draft (ago) e **antes** do próximo draft NFL (abr). É o único campo que captura a classe **mais
  nova**.
- **`metadata.rookie_year` — NÃO serve p/ a entrante.** Populado p/ classes passadas (2024=840,
  2025=714 entradas) mas **ausente na classe 2026**: os 4 rookies entrantes checados têm metadata só
  com `source_id`, sem `rookie_year`; **não existe bucket '2026'**. **Atrasa uma classe** — falha
  justamente na população-alvo.
- **`age`/`college`/`birth_date` — sparse/nulos** nos stubs da classe entrante (os 4 entrantes têm
  `age=None`, `college=None`). Não confiáveis p/ a entrante.
- **`search_rank` — NULO na classe entrante** (os 4 entrantes = `None`). Inútil p/ ela (ver Q7).
- **`status`/`active` — não são class-specific.**
Ressalva: os entrantes carregam **metadata pobre** no pool cacheado (sem team/age/college/rank).

**Q3 — Ponto de corte da classe alvo (sinais internos).** 
- `rookie_draft_done` (AppConfig; `offseason.py:714`) — toggle **MANUAL** do admin (passo 5);
  dispara `clear_rookie_espn_store()`. **Confiável como intenção** "nosso draft acabou", mas manual.
- `current_season` (AppConfig; `get_current_season`) — avança **automático** no rollover (passo 4,
  `offseason.py:691`), **antes** do rookie draft. É o relógio **da liga**, não o do draft NFL.
- `espn_values_updated` / `rollover_done` / `season_closed` / `season_locked` / `offseason_mode` —
  flags do workflow de intertemporada; rollover é auto, `offseason_mode` **desliga manual**.
- Importador OFF26-3 materializa o rookie draftado como Player rosterado — sinal **implícito** de
  saída da classe "por draftar" (ver Q5).
**Descompasso NFL × liga:** draft NFL ~fim de abril → 2026 vira `years_exp=0`; nosso rookie draft
~agosto; Sleeper vira `years_exp 0→1` ~março (próximo league-year), **depois** do nosso draft e
**antes** do próximo draft NFL. Logo `years_exp==0` = classe 2026 de ~abr/2026 a ~fev/2027. No
intervalo **ago/2026 → abr/2027** "classe entrante do NOSSO próximo draft" é ambígua: já draftamos a
2026 (que o Sleeper ainda marca `0`) e a 2027 NFL ainda não existe. **Implicação:** `years_exp==0`
sozinho **não avança** o alvo após o nosso draft — exige gate separado (`rookie_draft_done` + excluir
draftados, ou limitar o board à janela pré-draft).

**Q4 — Réplicas (grep reportado).** 
- **Critério da lista:** **1 sítio** — `cap_projector_rookies` (`salary.py:194-224`) lendo
  `RookieEspnValue`. O JS de `cap_projector.html:234-263` só **exibe** o payload (`$${r.projected_salary}`),
  **0 cálculo**.
- **Salário `floor(ESPN×1.2)`:** fonte única `salary_engine.year1_salary`; consumidores `salary.py:222`,
  `draft_import.py:135/143/259`, `record_acquisition`. **0 réplica** JS/template.
- **Critério "é rookie":** **não existe** como predicado de classe hoje. `draft_import.py:100`
  (`is_rookie = acquisition_type=="rookie_draft"`) é **tipo de draft**, não classe do jogador;
  `auction.html` "rookie" = aba de registro do rookie draft (nomes digitados à mão), **sem lista de
  classe**. **⚠️ p/ F2:** o predicado `years_exp==0` do D1 seria o **primeiro** critério de classe do
  codebase — nascer como **helper único** p/ não semear réplica.

**Q5 — Rookies já draftados.** Pós-draft o rookie vira Player rosterado (`record_acquisition`/
`draft_import`, `is_dropped=False`, `team_id` setado). Hoje o board lê `RookieEspnValue` (nunca
Player) e o store é **limpo em bloco** no `rookie_draft_done` → board esvazia inteiro; **não há
exclusão por jogador**. Sob D2 (lista do pool), o draftado **continuaria** listado (segue `years_exp=0`
no pool) sem exclusão. Sinal p/ excluir: **sid já existe como Player não-dropado**
(`find_player_by_sleeper_id`). **Interação DP2:** draftado é membro de roster **sujeito a corte** na
cadeia keep/corte unificada → tem de **sair da lista de draftáveis e entrar no cenário de roster**,
senão é **contado em dobro** (uma vez como rookie $1 no board, outra como jogador no roster).

**Q6 — Volume e custo (número concreto).** Classe entrante (`years_exp==0`): **718 no total, 289
skill (QB/RB/WR/TE), 151 ativos** — vs. hoje o board = só o subconjunto Top-300 não-rosterado (~dezenas).
D2 cresce a lista **~1 ordem de grandeza** (dezenas → **289** skill, ou **151** se filtrar ativos). O
endpoint atual **não carrega o pool** (só 1 query indexada em `RookieEspnValue`). Sob D2 precisaria
carregar/varrer o pool (`_load_players_db` = parse de **~15 MB**, `.sleeper_players_cache.json`, TTL
semanal) + scan das 11,5k entradas por request — o `_build_pool_index` já faz isso no import ESPN, mas
seria **novo custo por request** neste endpoint (parse cold ~centenas de ms; aceitável se o pool for
carregado 1× e filtrado, mas não é gratuito como hoje).

**Q7 — Ordenação (sem inventar dado).** 
- **Valor ESPN ajustado:** só p/ o subconjunto ~Top-300; o resto → $1 (empate). É o sort atual.
- **FantasyCalc dynasty `value` + `redraft_value` + `overall_rank`** (`data/.dynasty_values_cache.json`,
  keyed por `sleeperId`, TTL 24h, **já usado** por trades/league/picks): cobre **70 dos 289** skill
  entrantes → **219 sem valor dynasty**. Ordena bem o topo, deixa 219 empatados.
- **`search_rank`:** **NULO p/ a classe entrante** (os 4 entrantes = `None`) → inútil **exatamente**
  nessa população; nem como desempate serve aqui. (Registrado: é proxy **fraco** de ADP — rank de
  popularidade, não posição de draft — **e** ausente nos entrantes.)
Conclusão: **nenhuma chave única** ordena a classe inteira. Melhor combinação sem inventar dado =
ESPN (topo) → FantasyCalc dynasty (~70 seguintes) → nome/posição (os **219** residuais). O grosso do $1
fica **inordenável além de alfabético/posicional**.

**Q8 — Efeito da limpeza pós-draft.** Hoje `clear_rookie_espn_store()` (no `rookie_draft_done`)
**esvazia** `RookieEspnValue` → board vazio pós-draft (correto p/ a janela). Sob D2 (lista do pool),
limpar o store **não esvazia mais** o board — ele ficaria **permanentemente populado a $1** (classe
inteira do pool), inclusive pós-draft. **D2 exige gate próprio:** (a) limitar o board à janela
pré-draft via `rookie_draft_done` (esconder quando `true`), e/ou (b) excluir draftados (Q5) p/ encolher
naturalmente a zero conforme a classe é draftada. O join de **valor ESPN** seguiria lendo o store
season-keyed; limpá-lo derruba todos p/ $1 — aceitável sob D2 **só se** o board também estiver fechado.
`clear_rookie_espn_store` **deixa de ser o "interruptor"** do board.

**Q9 — Gap assumido×real / existe×proposto.** 
(a) *Premissas do prompt que o código contradiz:*
- "pool tem sinal de classe (rookie_year)" → **`premissa falsa`**: `rookie_year` atrasa uma classe,
  ausente na 2026; só `years_exp==0` serve.
- "$1 sem ESPN é fácil de ordenar" → **`premissa falsa`**: 219/289 sem dynasty value, `search_rank`
  nulo → ordenação não-resolvida.
- "entrante tem `nfl_team` p/ exibir" → **`premissa falsa`**: só **2/289** têm team no cache; team/age
  em geral nulos nos stubs entrantes.
(b) *Campos/comportamentos de hoje que somem sob D1/D2:*
- Veteranos/2ª-3ª-ano não-rosterados do Top-300 (Ridley/Allen/Ferguson) exibidos hoje →
  **`remoção intencional`** (D1 restringe à entrante; aceito pelo owner).
- Ordenação primária por valor ESPN (funciona hoje pois lista=Top-300) → insuficiente sob D2 →
  **`deslocamento`** (precisa de estratégia de sort nova).
- `clear_rookie_espn_store` como interruptor do board → **`deslocamento`** (precisa de gate novo).
- `RookieEspnValue` season-keyed como fonte única da lista → substituída por scan do pool →
  **`deslocamento`**.
- Exibir `nfl_team`/`position` vindos do `RookieEspnValue` (populados no import) → nos $1 do pool esses
  campos são esparsos/nulos → **`perda não-intencional`**.

**PARECER (opções viáveis + custo) — decisão de escopo é do owner; F2 não iniciada**
- **Opção A (D1+D2 pleno):** membership da classe = `years_exp==0` do pool (helper único) + excluir
  draftados (Q5) + gate `rookie_draft_done` (Q8); valor ESPN via store, senão $1 (D2); sort ESPN →
  FantasyCalc dynasty → nome. *Custo:* +load/scan do pool por request (Q6), +predicado de classe
  single-source (Q4), +join de exclusão a Player, +integração FantasyCalc no endpoint. Cobre (a) e (b).
- **Opção B (D1+D2, store como camada de valor):** igual A, mas o board faz **membership pelo pool** e
  **LEFT-JOIN a `RookieEspnValue`** só p/ o valor ESPN ($1 default). Minimiza mudança no store; a limpeza
  pós-draft zera valores (→ todos $1) e a visibilidade fica no gate. Mesmo custo de pool/sort de A.
- **Opção C (parcial — NÃO cumpre D2):** só **filtrar a lista atual por `years_exp==0`** (remove
  veteranos), sem trazer a massa $1. *Custo baixo* (1 lookup de pool por entrada existente, sem scan
  total). Corrige (a), **não** corrige (b) [rookies fora do Top-300 seguem ausentes] → **não satisfaz
  D2**; listada só p/ contraste de custo.

**REFINE — ARQUITETURA DE FONTE (MAN-DP3-REFINE, 31/07/2026; read-only — decide COMO a classe
chega ao board, antes da F2. Supera as opções A/B da F1, que assumiam pool ao vivo. Ordenação e
layout ficam FORA — decisão visual separada do owner.)**

*Evidência nova levantada:* (i) o pool `.sleeper_players_cache.json` (~15 MB, 11.578 entradas)
**está trackeado no git** — vai no deploy; o mtime vira o do deploy, então o TTL de 168h
(`PLAYER_CACHE_TTL_HOURS`, `sync_sleeper.py:32`) conta a partir dele; expirado, `_load_players_db`
re-baixa ~15 MB da API Sleeper (gravação do cache na raiz do app é try/except-pass — em prod a raiz
é tratada como read-only [doutrina E1], falha silenciosa ⇒ **re-download a cada load**). (ii) O app
**não tem hoje nenhum cache em processo** — `dynasty_values` é file-cache relido a cada chamada;
`_build_pool_index` re-parseia o pool a cada import. (iii) Medições: parse do pool ~**200 ms** na
máquina dev (Render Starter ~2-4×: **0,4–0,8 s**); scan das 11,5k entradas **~4 ms**; payload
filtrado da classe (D3) ~**10 KB**; deploy = gunicorn **1 worker** (Procfile sem `--workers`).

*Comparação — 3 posturas × 6 eixos:*

**P1 — pool por request** (opção B da F1):
- *Custo/request:* 1 query (`RookieEspnValue`, valores) + open+parse de **15 MB** (~200 ms dev /
  0,4–0,8 s Render) + scan 4 ms — **a cada carga do board**. Processo frio = igual (nada amortiza);
  **pior caso** (TTL 168h vencido + raiz read-only): **download de ~15 MB da API Sleeper dentro do
  request** (segundos, sujeito a timeout). Mobile: payload ~10 KB ok — o custo é latência do server.
- *Frescor:* melhor das 3 — defasagem ≤ TTL 168h (7 dias) + lag do próprio Sleeper; automático.
- *Gate:* limpeza existente **NÃO serve** (membership não vem mais do store) → exige check novo no
  endpoint sobre `rookie_draft_done` (flag **manual** já existente; sinal novo = novo consumo dela).
- *NFL×liga:* **herda** a ambiguidade (Q3) — `years_exp==0` segue apontando a classe já draftada até
  ~março; mitigação = o mesmo gate manual.
- *Draftados:* join por request sid→Player não-dropado (1 query `IN` sobre ~148 sids — barato).
- *Escrita:* **zero** (postura só-leitura; trivialmente idempotente).

**P2 — pool com cache em memória:**
- *Custo/request:* warm = 1 query + filtro em memória ~4 ms (~10 KB). **Frio (1º request do
  processo) = P1 inteiro** (parse 0,4–0,8 s ou download 15 MB). 1 worker gunicorn → 1 cache por
  processo, zerado a cada deploy/restart. RAM: pool parseado ≈ **10× o JSON** (dict Python de 11,5k
  entradas — ~centenas de MB) — relevante em instância pequena; mitigável guardando **só o índice
  filtrado** (~148 entradas, poucos KB), o que já é meio caminho para a P3.
- *Frescor:* = P1 **+ TTL do cache em memória** (pior caso soma os dois).
- *Gate:* = P1 — exige check novo (limpeza não serve).
- *NFL×liga:* = P1 — herda.
- *Draftados:* = P1 (join por request).
- *Escrita:* zero em DB, **mas** introduz o **primeiro estado global mutável de processo** do app
  (hoje não existe — novidade arquitetural com custo de raciocínio em restart/multi-worker futuro).

**P3 — snapshot materializado** (captura por ação de admin):
- *Custo/request:* **1-2 queries indexadas** (~148 linhas + subquery de exclusão de draftados) —
  ~1-5 ms, ~10 KB. **Idêntico ao board de hoje**; mobile e processo frio indiferentes (é DB local).
  O parse do pool é pago **1× por captura** (ação admin), não por request.
- *Frescor:* as-of última captura — defasagem máxima = intervalo entre capturas (controle do admin).
  Stubs que o Sleeper adiciona tarde e mudanças de status (D3: cortado pós-captura) só entram/saem
  na **recaptura** — mitigado por ela ser re-executável a qualquer momento (upsert idempotente).
- *Gate:* **PRESERVA a rotina existente** — snapshot vivendo em `RookieEspnValue` (linhas da classe
  com valor ESPN opcional; sem valor → $1 no read, D2), `clear_rookie_espn_store()` no
  `rookie_draft_done` volta a esvaziar o board integralmente, como hoje. **Nenhum sinal novo.**
- *NFL×liga:* **RESOLVE** — a captura é ato explícito no calendário DA LIGA (intertemporada);
  pós-draft a limpeza esvazia; a classe seguinte só existe quando o admin capturar de novo (e aí o
  Sleeper já virou o `years_exp`). A janela ambígua ago→abr não vaza para a tela.
- *Draftados:* exclusão no read via subquery local (sid ∉ Player não-dropado) — SQL barato; sem
  acoplamento de escrita com o draft import. (Sob DP2, o draftado sai da lista e entra no cenário
  de roster — sem dupla contagem.)
- *Escrita:* endpoint admin no fluxo de intertemporada, **upsert idempotente por `(sid, season)`** —
  molde já provado no próprio store (`upsert_rookie_espn`, confirm do import ESPN) e na família M8
  de ações admin re-executáveis. Re-executável N vezes; o import ESPN posterior segue preenchendo
  **as mesmas linhas** com valores (captura = membership + $1 default; import = camada de valor).
  Única postura que escreve — mas pelo caminho mais idempotente e auditável do codebase.

*Conflito com [[E4-c-2]] — parecer explícito:* **colidem.** O E4-c-2 prevê "generalizar/migrar
`RookieEspnValue` p/ o store canônico e aposentá-la" sob a premissa de que ela é **só valor ESPN
órfão**. A P3 **redefine a natureza da tabela**: passa a ser *membership da classe entrante com
valor opcional* (nome/pos/status/season + ESPN quando houver) — semântica que **não tem casa** no
`EspnValueStore` (que é `(sid, season, valor)` puro, sem membership). **Recomendação de
sequenciamento:** DP3-F2 **primeiro**; depois **reescopar** o E4-c-2 para a metade não-contestada
(DROP do `ESPNValue` legado, vazio) e **cancelar/reenquadrar** a metade "subsumir RookieEspnValue"
contra a natureza nova da tabela. Custo de esperar: zero — E4-c-2 é Baixa/higiene, 🔲, sem
dependentes. *(Registro apenas — o item E4-c-2 não foi alterado.)*

**D4 (owner, pós-REFINE):** fonte por snapshot materializado (P3). **D5 (owner):** tela na
alternativa A — valorados ordenados por ESPN desc no topo; massa a $1 atrás de busca por nome +
filtro de posição, com contagem visível.

**RECOMENDAÇÃO (única): P3 — snapshot materializado.** Trade-off que a sustenta: paga-se o parse
do pool 1× por captura (ação admin idempotente, molde já existente) para devolver ao board o custo
de request de hoje (1-2 queries, ~10 KB, ~ms — inclusive mobile e processo frio), **preservar
`clear_rookie_espn_store` como gate sem sinal novo** e **resolver** (não herdar) o descompasso
NFL×liga, ancorando a virada de classe no calendário da liga. P1/P2 têm frescor melhor, mas pagam
0,4 s–vários s por request (P1) ou introduzem o primeiro estado global de processo do app (P2), e
ambas ainda exigem gate novo e herdam a ambiguidade de calendário. **Risco principal da P3,
nomeado: frescor manual** — a classe exibida envelhece entre capturas (stub adicionado tarde pelo
Sleeper fica fora; jogador cortado pós-captura segue listado, violando D3 até a recaptura). Mitigação
natural: recaptura re-executável a qualquer momento + refresh do pool já semanal; residual aceito
como decisão de F2 (ex.: botão de recaptura ao lado do import ESPN no fluxo de intertemporada).

**F2 — IMPLEMENTADO (MAN-DP3-F2, 31/07/2026)** — ⚠️ validado em localhost; smoke em prod pendente.

*Camada de dados (models.py):* coluna **`in_class`** em `RookieEspnValue` (Migration 8 no
`app.py`, ALTER idempotente; default 0 → linhas pré-existentes do import ficam fora do board até a
captura). `upsert_rookie_espn` estendido como **porta única com dois donos por campo** (None = não
tocar): import ESPN é dono dos valores; captura é dona da membership — nenhum sobrescreve o outro.
Predicado **`is_entering_class_member`** = o 1º critério de classe do codebase, helper único
(grep: `years_exp` executável só em `models.py:509`; consumidor único = captura; **zero réplica**
em JS/rotas).

*Predicado D3 escolhido:* **`years_exp==0` AND posição skill AND `active is True` AND
`status=='Active'`** (conjunção deliberada). Justificativa com evidência do pool: cada flag isolada
tem um modo de falha — `status='Active'` com `active=False` são stubs fantasmas antigos cujo
`years_exp` nunca avançou (falsos entrantes, ex. Dontre Wilson classe 2018); `active=True` com
`status='Inactive'` são cortados/limbo. A conjunção exclui ambos. K/DST seguem fora (mesma
semântica E2 do store; posições `ENTERING_CLASS_POSITIONS = {QB,RB,WR,TE}`).

*Captura (admin.py):* `POST /api/admin/capture_rookie_class` (`@admin_required`) — varre o pool
(`_load_players_db`), aplica o predicado, upsert idempotente por `(sid, season)`; quem saiu do
critério é **desmarcado** (`in_class=False`), não deletado (preserva valor ESPN do import).
Relatório `{added, updated, removed, total_in_class}`. Pool indisponível → 503 gracioso, sem 500.
Botão na tela do **import ESPN** (`espn_import.html`, card próprio) — fluxo de intertemporada.

*Leitura (salary.py):* `/api/cap_projector/rookies` lê `in_class=True` da season-alvo **excluindo
sids já rosterados** (subquery Player não-dropado — sem double-count com a cadeia keep/corte DP2).
Contrato de resposta preservado; salário segue da fonte única `year1_salary` (sem ESPN →
`espn_adjusted=0` → **$1 sai do próprio engine**, zero código novo de salário). 2 queries
indexadas, leitura pura.

*Tela (cap_projector.html, D5 alt. A):* valorados (ESPN>0) no topo em tabela ordenada (ordem do
server, ESPN desc); massa a $1 atrás de **busca por nome + filtro de posição** com contagem
visível ("classe entrante: N — X com valor, Y a $1"); rookies já no cenário permanecem visíveis
mesmo sem busca ativa. Renderer de linha único; controles montados 1× (foco da busca preservado);
split valorado/massa é só display — **nenhuma** lógica de classe/salário/budget em JS; barra fixa
segue no `/budget` canônico DP2 (intocado).

*Validação (smoke 27/27, DB temporário — seed do git intocado; + 48/48):*
- Captura 2× idempotente: 2ª = added 0/removed 0/total igual; zero duplicata por (sid,season).
- 7 nomes da F1: Ridley/Allen/Ferguson **fora**; Love/Tate/Bernard/A.Williams **dentro**.
- Caso de referência DP1: Love $46→**$55**; Makai Lemon $3→**$3**; 286 sem ESPN → todos **$1**.
- Rosterado sai do board (Tate rosterizado → ausente); cenário 2 rookies → barra fixa +$58 exato
  e 2 spots ocupados; rookie $1 no cenário custa $1; `salary_history` inalterado (0→0).
- `clear_rookie_espn_store` → board vazio (gate preservado, rotina intocada).
- Gates: captura sem login → 401; `GET /cap_projector` e `/admin/espn_import` → 200.
- **Recalibragem de contagem (achado do smoke):** o TTL de 168h do cache do pool expirou e a
  captura baixou o pool **vivo de 31/07**: classe entrante ativa = **288 de 436** ye0-skill (D3
  exclui 148). O "~151" da REFINE era retrato do cache de 12/06 (pré-assinaturas de camp; rosters
  NFL hoje em 90). Paridade exata captura×pool verificada (288==288). Efeito colateral: o
  `.sleeper_players_cache.json` trackeado no git foi atualizado pelo download durante o smoke —
  **restaurado antes do commit** (não é artefato do DP3); o achado do versionamento virou o item
  **[[F13]]**.

**COMPORTAMENTO ESPERADO — a contagem da classe varia com o calendário da NFL (não é bug).**
O predicado D3 lê o status vivo do pool: em **julho/agosto** os rosters NFL estão em **90**
jogadores (training camp) e a classe ativa fica em ~**288**; após o **corte de fim de agosto**
(rosters a 53 + practice squads) o MESMO predicado devolve a ordem de ~**150**. Como o nosso
rookie draft ocorre **antes** do corte, o board em uso real exibe a **contagem alta** — correto:
naquele momento todos esses jogadores estão de fato em roster NFL. *Nota operacional:* se o board
seguir em uso após o corte da NFL (ex.: consulta tardia pré-FA), **recapturar** — a recaptura
desmarca os cortados (`removed` no relatório) e a lista encolhe para a ordem de ~150 sozinha.

*Pendências de smoke em prod (gate do ✅, PROC1 — hash live = commit):*
1. Captura real no Render (1ª execução baixa ~15 MB do pool na request — custo aceito na REFINE)
   → relatório coerente; re-execução idempotente.
2. Board na tela: valorados no topo pós-import ESPN; busca/filtro da massa $1 sem reload e com
   foco preservado (interação JS validada por revisão de código + página 200 — comportamento real
   só no navegador); contagem visível coerente com a captura.
3. Cenário com rookie da massa $1 refletindo na barra fixa em prod.
4. **Contagem de valorados × import real:** o smoke local exibiu só **2** valorados porque o DB
   temporário partiu do seed (store vazio; os 2 foram semeados pelo harness — Love/Lemon). O
   import real da season já gravou **84** entradas no store em prod (split E4-a). Confirmar em
   prod que o nº de valorados no topo do board corresponde às entradas do import ESPN que são
   membros da classe capturada (interseção in_class × valor>0 — não necessariamente os 84: os
   não-membros do import, ex. veteranos não-rosterados, ficam `in_class=False` e fora do board).

---
### F13 — Versionamento do cache do pool Sleeper
✅ **Concluído 31/07/2026 — smoke em prod OK sobre hash `2cd8de3` (PROC1 atendido)** —
MAN-DP3-COMMIT (registro) / MAN-DP3-CLOSE (evidência de prod) / **MAN-F13-F1/F2/CLOSE** — Prioridade
**Alta** — caminho **(b) padrão E1 + (d) carimbo por conteúdo**, validado em prod. Migrado verbatim
do `improvements.md` (O3) no fechamento.

**FECHAMENTO — SMOKE EM PRODUÇÃO (MAN-F13-CLOSE, 31/07/2026)**

Smoke sobre o hash **`2cd8de3`**, confirmado live no painel do Render (PROC1). Backup pré-deploy em
**`/data/pre_f13.db`**. Resultados:
- **Recaptura sobre pool fresco = 287** (o board saiu de 148 congelado → 287 corrente). Decomposição:
  **145 entraram** (exatamente os que não existiam no cache de junho — magnitude prevista pela F1),
  **142 atualizados**, **6 saíram do critério** (cortados entre junho e julho) → confirma a
  **desmarcação em condição real** (`in_class=False`, não delete).
- **2ª captura imediata: 0 entraram / 0 saíram, total estável, sem novo download** → o carimbo por
  conteúdo (`fetched_at` no envelope) operou: cache fresco não re-baixa. Valida o complemento (d) em
  prod (o mtime de deploy não mais reinicia o TTL).
- **Board em prod exibindo 287**, com **12 registros vindos do import ESPN**, dos quais **6 acima do
  mínimo** (valorados no topo); busca por nome e filtro de posição validados em navegador.

**PENDÊNCIA REMANESCENTE (não impede o ✅):** a 4ª pendência de smoke — o frescor **sobreviver a um
2º deploy** (o cache em `/data` não recongelar, por não vir mais do checkout) — só é verificável no
**próximo release**. Verificação vinculada ao próximo deploy: após ele, sem recaptura, a captura
deve seguir devolvendo ~287 (não voltar a 148). É a diferença estrutural que o F13 promete; a
mecânica já está provada (o arquivo saiu do git e o carimbo é por conteúdo), resta a observação no
tempo.

**NOTA DE ARQUIVAMENTO:** seção abaixo preservada íntegra (F1 diagnose + F2 implementação). As
pendências de smoke 1-3 listadas na F2 foram **satisfeitas** por este smoke; a nº 4 (2º deploy)
fica como verificação vinculada ao próximo release acima.

---

⚠️ **[registro histórico — status no fechamento da F2, antes do smoke prod]** —
MAN-DP3-COMMIT (registro) / MAN-DP3-CLOSE (evidência de prod) / **MAN-F13-F1/F2** — Prioridade
**Alta** — ⏳ **janela: antes do rookie draft (agosto)** — caminho **(b) padrão E1 + (d) carimbo por
conteúdo** entregue; smoke cache 21/21 + e2e captura 287 + `salary_engine_test` 48/48. **✅ só após
smoke prod** (recaptura da classe = 287, não 148; hash live = commit).

**PROBLEMA / OPORTUNIDADE**
`.sleeper_players_cache.json` (~15 MB, 11,5k jogadores) está **trackeado no git**. Três efeitos
colaterais, todos observados/derivados durante o DP3:
1. **Frescor enganoso:** a cada deploy o mtime do arquivo vira o do checkout → o TTL de 168h
   (`PLAYER_CACHE_TTL_HOURS`) reinicia contando de um dado que pode ter semanas/meses (o cache
   commitado era de 12/06; em 31/07 o pool real divergia muito — 288 vs 151 na classe entrante).
2. **Peso no repositório:** cada refresh commitado adiciona ~15 MB à história do git.
3. **Gravação silenciosamente perdida em prod:** o cache é escrito na **raiz do app**, tratada
   como read-only em produção (doutrina E1); `_load_players_db` engole a falha (try/except-pass)
   → com TTL vencido, **todo** load re-baixa ~15 MB da API Sleeper (sync, captura DP3, imports).

**EVIDÊNCIA DE PRODUÇÃO (smoke DP3, 31/07/2026 — confirma o efeito 1 acima, não mais só derivado):**
- A captura DP3 em **prod** retornou **148**; o smoke local contra o pool vivo retornou **288**.
  O 148 é exatamente o snapshot do pool de **12/06/2026** (o arquivo versionado no git). Prod está
  servindo o pool de junho **de forma indefinida**.
- **Mecanismo do TTL que nunca vence:** o deploy do Render recria o arquivo a partir do git a cada
  release → `os.path.getmtime` devolve a data do **deploy**, sempre recente → `age_hours < 168`
  quase sempre verdadeiro → o conteúdo (junho) nunca é considerado vencido. O caminho de re-download
  (efeito 3) só dispara se o arquivo faltar ou passar 168h sem deploy — com deploys frequentes,
  **nunca**. Ou seja: em prod o pool é **congelado no commit**, não semanal como o código sugere.
- **Alcance além do DP3:** o mesmo `_load_players_db` alimenta a resolução de `sleeper_id` do
  **import ESPN** (`_build_pool_index` / E4-a) e o **sync**. Um pool de junho significa que rookies
  assinados/movidos depois de 12/06 podem não resolver (ou resolver para time errado) no import — o
  problema não é cosmético do board.
- **Por que virou Alta + janela:** o **rookie draft ocorre em agosto** e o board precisa da classe
  **completa e corrente** antes disso (hoje mostra a classe de junho, incompleta). Resolver o F13 é
  pré-condição prática para o DP3 entregar valor real na janela de planejamento — daí a elevação.

**CAMINHOS A AVALIAR (decisão do owner, não tomada — segue sem escolher)**
- (a) **gitignore** + download no 1º uso (boot mais lento no 1º acesso; repo limpo).
- (b) Mover o cache para **`dirname(DYNASTY_DB)`** (FS gravável em prod — mesmo padrão do estado
  de review do import ESPN/E1), mantendo ou não o seed no git.
- (c) Manter como está (aceitar re-download por load pós-TTL em prod).

**DEPENDÊNCIAS**
- Relaciona-se com: [[DP3]] (captura lê o pool; completude da lista **depende** deste item), import
  ESPN / [[E4-a]] (resolução de `sleeper_id` pelo mesmo loader), sync Sleeper (mesmo loader), E1
  (doutrina do FS gravável). Bloqueia: completude prática do board [[DP3]] antes do rookie draft.

**F1 — ACHADOS (diagnose read-only, MAN-F13-F1, 31/07/2026; zero mutação — cache local intocado,
pool vivo baixado só para o scratchpad p/ comparação)**

**Q1 — Caminho de leitura/escrita + consumidores.** Loader único `_load_players_db`
(`sync_sleeper.py:45`): arquivo existe **e** `getmtime` com idade <168h (`PLAYER_CACHE_TTL_HOURS`,
linha 32) → lê; senão → download `_get(BASE_URL/players/nfl)` (**timeout 15s**) → tenta gravar na
**raiz do app** (try/except-**pass**, linha 61) → retorna o dado mesmo sem gravar; download falho →
`{}` (todos os consumidores degradam). **Consumidores (6 sítios — todos admin/boot, NENHUM caminho
de owner comum;** o board DP3 lê o snapshot materializado, não o pool**):**
1. `run_sync` (`sync_sleeper.py:98`) — boot condicional a `fresh_import` (prod: skip, sem CSV) +
   `POST /api/admin/sync`. Sid do roster ausente do pool → Player criado com **nome = número do
   sid** e posição vazia (`sync_sleeper.py:213-217`) — consequência observável direta.
2. Matcher do import ESPN (`admin.py:703`, E4-a). 3. Confirm→store (`admin.py:565`, E2).
4. Render do review E5 (`admin.py:755`). 5. Captura DP3 (`admin.py:609`).
6. Guard E4-b no `import_csv.py:86` (lazy, só no 1º create; prod sem CSV → não roda).

**Q2 — Comportamento em produção: veredito = NEM TENTA escrever.** Na cadência real de deploys
(23/06, 10/07, 31/07…) o mtime do checkout mantém a idade <168h → o branch de download/escrita é
**inalcançável**. Evidência: a captura de 31/07 devolveu 148 = conteúdo de 12/06, lido do arquivo
do git no dia do deploy. Na única janela >168h sem deploy (30/06→10/07), se algum consumidor
tivesse rodado, a escrita seria tentada e **silenciosa se falhasse** (try/except-pass — garantido
pelo código); a gravabilidade da raiz do Render **não é verificável por diagnose read-only**. E há
um **2º mecanismo, não registrado antes: checkout-revert** — mesmo um download+escrita
bem-sucedidos são **desfeitos no deploy seguinte** (o checkout repõe o arquivo de junho). O
congelamento é estrutural (mtime-renewal + checkout-revert), não acidental.

**Q3 — Custo do congelamento (evidência: diff junho×vivo, 31/07).** Pool vivo **12.204** entradas ×
junho **11.578** → **+626 sids novos**. Classe entrante D3 viva **287** × junho **148**; dos 287,
**145 (50,5%) NEM EXISTEM no pool de junho** (ex.: Colbie Young/CIN, Kaden Wetjen/PIT) — não é
status desatualizado, é **ausência**: a captura não os vê, `_resolve_entry_sid` devolve 0
candidatos, o sync criaria stub numérico. **108 dos 142** membros presentes em ambos **mudaram de
NFL team** desde junho (stubs de junho tinham team=None) → o desambiguador Brown-safe **nome+team**
do import ESPN opera com team errado/ausente para metade da classe → homônimos caem em
ambíguo→$1 (**miss, não corrupção** — a classe de erro E4-a é preservada, mas o miss cresce).
**Retroativo pequeno:** o import real (23/06) usou pool de 11 dias (rookies do Top-300, draftados
em abril, já estavam no pool). **Prospectivo grande:** captura/import/sync futuros seguem vendo
junho até o F13 — o board DP3 hoje mostra 148 de 287, e um waiver de jogador pós-junho viraria
Player "13XXX" needs_review.

**Q4 — Padrão E1 aplica-se? SIM, quase direto — e resolve os dois mecanismos de uma vez.**
Correção de registro sobre o precedente: no archive do E1, a escrita na raiz era **candidato
secundário não confirmado** ("pode falhar em FS read-only → OSError **não tratado**" — falharia
**barulhento**, 500, não silencioso); o fix foi **preventivo**. O que o E1 **comprova** é que
`dirname(DYNASTY_DB)` (= `/data`) é **gravável em prod** — o estado de review vive lá desde 07/06,
com imports reais em 08/06 e 23/06. Diferenças relevantes do cache vs review state: (i) **15 MB vs
KB** — irrelevante para o disco (1 GB montado, `render.yaml`; dynasty.db 540 KB + backups → sobra
~900 MB); (ii) "lido em caminho de request" — na prática **só requests de admin** (Q1: nenhum
caminho de owner comum lê o pool) → tolera segundos; (iii) **bônus que o E1 não tinha:** em `/data`
o arquivo **sobrevive ao deploy com mtime verdadeiro** → o TTL de 168h volta a valer o que o código
promete, e o checkout-revert desaparece.

**Q5 — Consequência de desversionar (números).** Boot pós-deploy sem o arquivo: **o boot não paga
nada** em prod (`run_sync` só roda sob `fresh_import`, falso sem CSV; guard E4-b é lazy). Quem
paga: **a 1ª ação de admin** que precisar do pool (sync manual / import ESPN / captura) —
download de **14,6 MB medido em 1,5 s** (folga ~10× no timeout de 15 s; datacenter→datacenter
tende a ≥). O admin vê a request ~2-5 s mais lenta, 1×. Download falho → **degradação graciosa já
existente em todos os consumidores** (idx `{}` → fallback/needs_review; captura → 503; sync → erro
no summary) — nenhum 500, nenhum caminho de owner exposto. **Porém**, desversionar SEM mover o
caminho deixa a escrita pós-download na raiz **incerta**: se a raiz não gravar, paga-se 14,6 MB
**por ação**; se gravar, perde-se no deploy seguinte — por isso (a) sozinho é inferior a (a)+(b).

**Q6 — Réplicas: 1 sítio único, 0 réplicas.** Caminho+TTL definidos só em `sync_sleeper.py:31-32`
(lógica 45-66); grep não encontra segundo sítio em código (menções restantes = docs/handoffs).
*Contraste relevante:* `dynasty_values.py` é um **2º mecanismo de cache** independente no codebase
com TTL **por conteúdo** (`fetched_at` dentro do JSON — imune a mtime-renewal) — o padrão mais
robusto já existe em casa, candidato a **complemento** na F2.

**Q7 — Comparação dos caminhos (5 eixos):**
| Caminho | 1º boot | Por request | Frescor máx | Falha em prod | Operação manual |
|---|---|---|---|---|---|
| (a) só gitignore | 0 no boot; 1ª ação admin paga 14,6 MB/~1,5 s | 0 **se** a raiz gravar (até o próximo deploy); senão 14,6 MB/ação | 168h | escrita na raiz **incerta**; Sleeper down na 1ª ação (degrada gracioso) | nenhuma |
| **(b) padrão E1: cache em `dirname(DYNASTY_DB)` + gitignore** | idem (a) na 1ª ação (seed-copy opcional) | **0** (arquivo persistente, mtime real) | **168h REAL** (renova ≤1×/semana na 1ª ação pós-vencimento) | **mínima** (/data gravável comprovado pelo E1; timeout coberto por degradação) | nenhuma |
| (c) manter como está | 0 | 0 | = data do último commit do cache (**indefinido**) | zero técnica, 100% dado stale | recommit de ~15 MB a cada refresh desejado |
| (d) TTL por conteúdo (`fetched_at`) sem mover | 0 | 0 até o 1º vencimento; depois = (a) | 168h | = (a) (raiz incerta; o arquivo de junho vence imediato → download na 1ª ação) | nenhuma |

(d) foi revelado pela diagnose; sozinho equivale a (a) com o arquivo ainda pesando no git — serve
como **complemento de robustez** do (b) (protege contra cópia de arquivo com mtime novo), não como
caminho próprio.

**Q8 — Gap assumido × real.**
- *"Prod re-baixa 15 MB a cada load pós-TTL"* (efeito 3 do registro original) → **falsa na
  prática**: o branch nunca é alcançado na cadência de deploys; prod **não re-baixa nada** — isso É
  o congelamento.
- *"A escrita falha em silêncio em produção"* → **não-observado/indeterminado**: a escrita nunca
  foi tentada em prod; o código garante silêncio SE falhar, mas a gravabilidade da raiz não é
  verificável read-only.
- *"O E1 também falhava silenciosamente"* (premissa do prompt) → **imprecisa**: no registro do E1 a
  escrita na raiz era hipótese secundária não confirmada e falharia **barulhenta** (OSError não
  tratado → 500); o fix foi preventivo. O que o E1 comprova é a **gravabilidade de `/data`**.
- **Mecanismo novo registrado:** checkout-revert (deploy desfaz qualquer refresh que prod consiga).
- *O que some por caminho:* (a)/(b) eliminam o "refresh por recommit" — hoje o **único** mecanismo
  (acidental) de atualizar o pool de prod; (c) mantém tudo, inclusive o freeze.

**RECOMENDAÇÃO (única): caminho (b) — padrão E1: mover o cache para `dirname(DYNASTY_DB)` +
gitignore do arquivo (absorve o (a)); complemento opcional (d) `fetched_at` no payload, a decidir
na F2.** Trade-off que a sustenta: paga-se **1 download de 14,6 MB (~1,5-5 s) na 1ª ação de admin**
pós-migração e depois ≤1×/semana, em troca de TTL real de 7 dias, eliminação dos **dois** mecanismos
do congelamento, superfície de falha mínima (gravabilidade de `/data` comprovada pelo E1 +
degradação graciosa já existente em todos os 6 consumidores) e repo sem ~15 MB por refresh. F2
estimada pequena (1 constante de caminho + gitignore; consumidores intocados). **Risco principal,
nomeado:** a 1ª ação de admin que precisar do pool (e cada renovação semanal) depende da API do
Sleeper naquele momento — timeout de 15 s → pool `{}` → aquela ação degrada (captura 503, import em
fallback) e o admin re-executa; sem 500, mas a ação não completa na hora. Residual aceitável dentro
da janela de agosto.

**F2 — IMPLEMENTADO (MAN-F13-F2, 31/07/2026)** — ⚠️ validado em localhost; smoke em prod pendente.
Caminho **(b)** com complemento **(d)**, sem tocar a semântica dos 6 consumidores nem o formato do
payload lido por eles (envelope só na camada de disco).

- **Localização (b), sítio único:** novo `sync_sleeper._player_cache_path()` deriva de `DYNASTY_DB`
  → `dirname` (volume persistente `/data` no Render; fallback dev = BASE_DIR, gravável) — mesmo
  padrão do `_espn_review_path` (E1). Constante morta `PLAYER_CACHE_FILE` (raiz do app) **removida**;
  grep confirma **0 outro sítio** de caminho.
- **Desversionamento:** `git rm --cached .sleeper_players_cache.json` (já estava em `.gitignore:34`,
  mas fora committado antes disso → seguia trackeado); cópia de junho **removida da árvore de
  trabalho**. `git ls-files` não lista mais o arquivo; checkout limpo não o repõe. Em prod o deploy
  deixa de trazer o arquivo → app root sem cópia; `/data` sem cópia (nunca escrito lá) → cache frio.
- **Validade por conteúdo (d), sítio único:** `_load_players_db` passa a ler um **envelope**
  `{"fetched_at": ISO, "players": {…}}` e valida pelo carimbo via `_cache_envelope_age_hours`
  (espelha `dynasty_values._cache_age_hours`), **não** por `os.path.getmtime` — imune ao mtime
  renovado por deploy. Devolve sempre o dict cru `{sid:…}` aos leitores (desembrulha na leitura;
  embrulha na escrita). **Formato antigo** (dict cru sem `fetched_at`), **sem carimbo**, **carimbo
  ilegível** (→ idade `inf`) ou **JSON corrompido** → tratado como vencido, dispara refresh, **nunca
  lança**. Escrita = `{fetched_at: utcnow, players: data}` no novo caminho (try/except-pass mantém a
  degradação; `makedirs` garante o dir).
- **Migração:** primeiro boot pós-deploy encontra o novo local vazio → caminho normal de cache frio
  (download + envelope), sem intervenção manual; consumidores intactos (todos já degradam a `{}`).
  Removido `import time` (órfão após trocar mtime→carimbo).

*Validação localhost:*
- **Smoke de cache (21/21, dir isolado via `DYNASTY_DB` temp, `_get` stubado com o pool vivo da F1):**
  caminho resolve p/ o volume (não a raiz); cache frio → 1 download + envelope carimbado no novo
  local; carimbo fresco → 0 download; carimbo antigo (200h) → refresh; **formato antigo → vencido,
  não lança**; sem carimbo → vencido; carimbo ilegível → idade `inf` → refresh; JSON corrompido →
  não lança + refresh; **API down + vencido → `{}`, sem 500**; classe entrante sobre pool fresco =
  **287** (não 148).
- **E2E real (boot do app + DB temp + download real):** cache **inexistente antes** da captura →
  `POST /api/admin/capture_rookie_class` → cache criado em `dirname(DYNASTY_DB)` como envelope com
  `fetched_at`; captura retorna **287** (não 148). Confirma o caminho completo em contexto de app.
- **Sítio único (grep):** caminho só em `_player_cache_path`; critério de validade só em
  `_cache_envelope_age_hours` + o guard de `_load_players_db`; 0 réplica. `salary_engine_test` 48/48.

*Pendências de smoke em prod (gate do ✅, PROC1 — hash live = commit):*
1. Deploy: confirmar que o arquivo **não** vem no checkout (`/opt/render/.../src` sem a cópia de
   junho) e que `/data` recebe o cache novo na 1ª ação de admin.
2. **Recaptura da classe entrante (verificação ponta-a-ponta):** `/admin/espn_import` → capturar →
   relatório em **ordem de 287** (não mais 148) — fecha o ciclo DP3+F13 (o board passa a exibir a
   classe corrente e completa). Re-executar → idempotente.
3. Frescor persistente: após um 2º deploy (sem recaptura), o cache em `/data` **sobrevive** com o
   carimbo real (não recongela em junho) — a diferença central vs. o estado atual.
4. Import ESPN sobre pool fresco: resolução de `sleeper_id` passa a ver os ~626 sids novos e os
   times corrigidos (108/142 da classe) — conferir quando o import da season rodar.

---
<!-- O3: movido verbatim de improvements.md em 02/08/2026 (MAN-S3-DONE), apos smoke em producao aprovado sobre o hash 89dc08d. -->
### S3 — Rename de time quebra o match de picks (identidade por string, classe "Brown")
✅ **Concluído (02/08/2026)** — MAN-S2-F1a/F1b (achado colateral) → MAN-S3-F1/F2/DONE — Prioridade
**Alta** — família [[S1]] / [[S2]] — smoke em prod aprovado sobre o hash `89dc08d` (gate [[PROC1]]);
**sync religado, suspensão encerrada**

**PROBLEMA**
O sync **renomeia `Team.name`** quando o owner troca o nome do time no Sleeper
(`sync_sleeper.py:181-189`) e cascateia para `Player.fantasy_team` (`:186-187`) — **mas não cascateia
para as picks**. As tabelas de pick guardam o nome como **string**:

- `_ensure_default_picks` indexa o que já existe por `(season, round, original_team_name)`
  (`sync_sleeper.py:383`) e compara com `team.name` **novo** → chave não bate → cai no ramo de criação
  (`:391`) e **insere 9 picks duplicadas** (3 seasons × 3 rounds) para o time renomeado.
- `_sync_traded_picks` busca a `Pick` por `original_team_name=orig_team.name` **novo**
  (`:421-425`) → não acha → ramo `else` (`:432`) **insere outra duplicata**.
- `_build_pick_projections` chaveia por `original_team_name` (`routes/picks.py:137`): as linhas com o
  nome antigo perdem a projeção e caem no fallback `999` (`:64`).
- `DraftLotteryResult.team_name` e `SeasonStandings.team_name` também guardam string e **não são
  atualizados** → a ordem canônica passa a apontar para um nome que não existe mais.

**ESTADO: ARMADO, AINDA NÃO DISPARADO**
O time `id=9` é **"Tropa do Bicampeonato 🏆"** no banco e **"Tropa do Jarra 🏆"** no Sleeper hoje. O
rename aconteceu **depois** do último sync (30/07 12:05), então ainda não foi ingerido — as 108 picks
seguem íntegras (12 × 3 × 3, sem duplicata). **O próximo sync dispara.**

**POR QUE É ALTA E BLOQUEANTE**
O [[S2]] só se resolve com o sync voltando a rodar. Se voltar antes deste fix, a primeira execução
cria picks duplicadas **e** corrompe a correção do S2 recém-aplicada. Ordem obrigatória: **S3 → sync
→ S2-F2**.

**CLASSE DO DEFEITO**
Mesma família do incidente "Brown" e do guard do [[E4-b]]: **identidade por string em vez de id**.
`Pick` já tem `original_team_id`/`current_team_id` — o caminho natural é casar por **id** e tratar
`*_team_name` como rótulo derivado (ou removê-lo do critério de unicidade).

#### F1 — Diagnose (read-only, 02/08/2026 — MAN-S3-F1)

Código lido e **reproduzido sobre cópia** (`scratchpad/s3_sim.db`, cópia do snapshot de prod de
31/07). Nenhuma escrita em prod, nenhuma chamada de rede, nenhuma alteração de código.
**Nota de segurança da simulação:** `data/dynasty_rosters_clean.csv` **existe** na máquina local, o
que tornaria `fresh_import` truthy e faria `import app` disparar `run_sync()` **de verdade** (rede) —
violando a suspensão. A simulação portanto **não importa `app.py`**: monta um Flask mínimo apontando
para a cópia e chama só `_ensure_default_picks` / `_sync_traded_picks`, com os `traded_picks` vindos
do JSON já capturado na F1a.

**1 — INVENTÁRIO: onde pick é casada, criada ou lida por nome**

Só existem **3 sítios que escrevem `Pick`**, todos em `sync_sleeper.py` — e **um deles já está
certo**:

| sítio | como casa | cria linha se não achar? | veredito |
|---|---|---|---|
| `_ensure_default_picks` (`:361`) | `(season, round, **original_team_name**)` (`:383`) | **sim** (`:391`) | **quebrado** — é o que duplica |
| `_sync_traded_picks` (`:407`) | `filter_by(..., **original_team_name**=…)` (`:421-425`) | **sim** (`:432`) | **quebrado** |
| `_sync_trades` (`:649-671`) | `filter_by(..., **original_team_id**=orig_team.id)` (`:670`) | **não** — só emite warning (`:677`) | **JÁ CANÔNICO** |

**Resposta explícita sobre réplicas:** a lógica de match por nome **não** existe fora desses dois
sítios — não há réplica em outro módulo, em JS ou em template. O que existe, e é o ponto cego do
registro original, é uma **segunda camada**: os leitores que usam o nome como **chave de join**,
sem nunca escrever:

- `_build_pick_projections` (`routes/picks.py:135-232`) monta `proj` chaveado por
  `**team_name**` vindo de `DraftLotteryResult.team_name` (`:219`) e de `_build_default_draft_order`
  (→ `SeasonStandings.team_name`, `routes/offseason.py:152-162`), e o casa contra
  `p.original_team_name` (`picks.py:118`, `:76`). **Três tabelas diferentes, join por string.**
- `api_picks?team=` → `filter_by(current_team_name=…)` (`picks.py:106`).
- `trades.py:87` → `pick.current_team_name == team_name` para pré-seleção (M14).
- `picks.py:61` monta as linhas do grid a partir do conjunto de `original_team_name` distintos.
- `picks.html:39-40,63-64,80-82` — `data-orig`/`data-cur` são **display**, usados só pelo filtro
  client-side; ambos os lados saem do mesmo render → **não precisam de fix**.

Leitores **imunes** (já usam id): `routes/league.py:53-54` e `:89-90`, `routes/trades.py:449`,
`routes/picks.py:247,257`.

**2 — REPRODUÇÃO DA DUPLICAÇÃO (código real, sobre cópia)**

Aplicado o rename do time 9 (`Tropa do Bicampeonato 🏆` → `Tropa do Jarra 🏆`) exatamente como o
sync faz (`sync_sleeper.py:181-189`) e rodados os passos 10 e 11:

| etapa | picks | Δ |
|---|---|---|
| antes | 108 | (0 duplicatas) |
| após `_ensure_default_picks` | **117** | **+9** — `[sync] Created 9 default picks for seasons [2026, 2027, 2028]` |
| após `_sync_traded_picks` (32 entradas) | 117 | **+0** |

**Confirmado: 9 picks duplicadas** — 3 seasons (2026/2027/2028) × 3 rounds, todas com
`original_team_id=9`, metade com o nome velho e metade com o novo.

**Achado que corrige a F1b:** na prática **só `_ensure_default_picks` duplica**. Ele roda **primeiro**
(`:331`) e já cria as linhas com o nome **novo**; quando `_sync_traded_picks` roda (`:334`), acha
essas linhas e apenas as atualiza. O segundo ramo de inserção existe, mas é **inalcançável nesta
ordem**. O dano é 9, não 18.

**Estado resultante — o pior dos dois mundos:** as linhas **velhas** guardam a projeção (o nome bate
com o lottery) mas **congelam a titularidade antiga**; as linhas **novas** recebem a titularidade
correta do `/traded_picks` mas **perdem a projeção**.

**3 — EFEITOS DERIVADOS OBSERVADOS**

- **Projeção:** `'Tropa do Jarra 🏆' → SEM PROJEÇÃO` (fallback `999`, `picks.py:64`) — porque
  `DraftLotteryResult.team_name` e `SeasonStandings.team_name` seguem com o nome velho. No grid do
  `/picks` a linha do time renomeado **desce para o fim** e aparece **duas vezes**.
- **League Hub** (`league.py:53-54`): contagem inflada em **7 dos 12 times** — Cangaceiros passa de
  9 para **17** picks, e o próprio time 9 cai para **4**. Total 117 em vez de 108.
- **Valores dynasty:** `pick_sleeper_id` (`dynasty_values.py:192`) deriva a chave FantasyCalc de
  `projected_pick`; sem projeção, as picks novas caem no fallback agregado (`FP_`) — valor errado em
  preview de trade, exatamente o modo de falha do [[T2-FIX]].
- **`api_picks?team=`** passa a devolver as duas cópias com donos divergentes.

**4 — CHAVE ESTÁVEL DISPONÍVEL POR SÍTIO — sim, em todos**

O ponto decisivo: **`Pick.original_team_id` / `current_team_id` já existem** (`models.py:287-288`),
já são FK para `teams.id`, e a simulação mostra que **as duplicatas nascem com o id CERTO** — as 18
linhas têm `original_team_id=9`. **Só o nome é usado como chave; o id já está lá e correto.**
Portanto: **nenhuma mudança de schema é necessária.**

| ponto | chave estável disponível |
|---|---|
| `_ensure_default_picks` | itera objetos `Team` → `team.id` |
| `_sync_traded_picks` | `teams_by_roster` (roster_id → `Team`) → `orig_team.id` — **é exatamente o que `_sync_trades` já faz** |
| `_build_pick_projections` | `DraftLotteryResult.team_id` e `SeasonStandings.team_id` **existem** (schema confirmado) |
| `api_picks?team=` / `trades.py:87` | resolver `Team` pelo nome **uma vez** e comparar id |

**O que o payload do Sleeper oferece em cada porta de entrada:**

| endpoint | identificadores | nome? |
|---|---|---|
| `/traded_picks` | `roster_id`, `owner_id`, `previous_owner_id` | **nenhum** |
| `/rosters` | `roster_id`, `owner_id` | **nenhum** |
| `/users` | `user_id` | `metadata.team_name`, `display_name` — **a única fonte de nome, e é a mutável** |

Ou seja: **na fronteira de picks o Sleeper nunca manda nome.** A string é introduzida pelo próprio
Manager ao traduzir `roster_id → Team → Team.name`. O bug é 100% auto-infligido.

**5 — RESTRIÇÃO DESCOBERTA: não dá para "só atualizar os nomes"**

A saída ingênua — cascatear o rename para `Pick.*_team_name`, espelhando o cascade que já existe para
`Player.fantasy_team` (`sync_sleeper.py:186-187`) — **não fecha**: a projeção casa `Pick` contra
`DraftLotteryResult`/`SeasonStandings`, que continuariam com o nome velho. Converte "linha duplicada"
em "linha sem projeção" (o mesmo efeito observado em "3"). Seria preciso atualizar as três tabelas.

**E atualizar `DraftLotteryResult.team_name` é proibido:** o verify do [[M8]]
(`routes/picks.py:334-336`) compara `team_name` **reproduzido do `pool_json` congelado** contra o
`team_name` **atual** das linhas de `DraftLotteryResult`. Renomear a tabela viva **quebraria a
verificação da auditoria do lottery** — que é justamente a prova pública de que o sorteio não foi
adulterado. Hoje as duas pontas estão congeladas juntas e por isso a auditoria segue válida.

> **Conclusão forçada:** o join da projeção **tem** de migrar para `team_id`. Não é preferência de
> estilo — é a única saída que não sacrifica a auditoria do M8.

**6 — A CLASSE É MAIOR QUE PICKS**

| domínio | chave estável? | exposição ao rename |
|---|---|---|
| `Pick` | **sim** (`original_team_id`/`current_team_id`) | alta — é o S3 |
| `SeasonStandings` / `DraftLotteryResult` | **sim** (`team_id`) | média — nomes congelados; **devem continuar congelados** (M8) |
| `AuctionLog` | **sim** (`team_id`) | baixa — `team_name` é snapshot de display |
| `PlayerHistory` | **NÃO** — só `team_name` (`models.py:780`) | **alta e silenciosa**: `team_name` entra no **índice UNIQUE** de dedupe do [[F8]]a (`app.py:361`: `player_id, season, event_type, team_name, sleeper_event_ref`). Pós-rename, o mesmo evento com nome novo **não colide** com a linha antiga → a idempotência do histórico deixa de valer |
| `Trade` (`team_a`/`team_b`) | **NÃO** — só strings | **alta**: `routes/roster.py:245-250` resolve a contraparte da trade comparando `trade.team_a == h.team_name`. Trades antigas guardam o nome velho e `PlayerHistory` novo guarda o novo → o timeline do jogador cai no ramo `else` e perde a contraparte |

`PlayerHistory` e `Trade` **não têm chave estável nenhuma** — são name-only por construção. É a
mesma classe, mas **não cabe no S3**: mexer ali toca schema, o índice de dedupe do F8a e o histórico
já gravado. **Recomendo escopo separado**, registrado abaixo como questão aberta, não como parte da
F2 do S3.

**7 — DESENHOS AVALIADOS**

| | (A) match por id, nome só display | (B) cascatear o rename para `Pick` | (C) congelar `Team.name` (parar de renomear) |
|---|---|---|---|
| **muda schema?** | **não** — ids já existem e já estão certos | não | não |
| **resolve a duplicação?** | sim, na raiz | sim | sim (elimina o gatilho) |
| **resolve a projeção?** | sim (join por id) | **não** — vira "sem projeção" (ver "5") | sim (nada muda de nome) |
| **picks já persistidas** | **nada a migrar** para correção; refresh de nome é cosmético e pode rodar a cada sync | exige UPDATE nas 3 tabelas → **quebra o M8** | nada |
| **renames futuros** | absorvidos automaticamente | absorvidos, mas com o furo da projeção | **owners nunca veem o rename** — nome do Manager congela |
| **fecha a classe?** | fecha para picks; deixa `PlayerHistory`/`Trade` | não | não — só desarma o gatilho |
| **custo** | ~4 pontos de código, todos com precedente no próprio arquivo | ~1 ponto + 2 quebras | ~1 linha |

**(C)** é o desarme tático: uma linha, e o sync volta a rodar hoje. Mas troca um bug por uma
mentira permanente na UI (o time renomeado aparece com o nome antigo para todos os 12 owners) e não
fecha nada. **(B)** é sedutor por espelhar um cascade que já existe, mas colide com o M8.

**8 — RECOMENDAÇÃO DE ESCOPO PARA A F2 (única)**

**Adotar (A), sem schema, em uma fatia só** — quatro pontos, todos espelhando precedente que já
existe no próprio `sync_sleeper.py`:

1. `_ensure_default_picks`: indexar o existente por `(season, round, original_team_id)`.
2. `_sync_traded_picks`: casar por `original_team_id=orig_team.id` — **copiar literalmente a linha
   `:670` do `_sync_trades`**.
3. `_build_pick_projections` + `_build_default_draft_order`: chavear por `team_id`
   (`DraftLotteryResult.team_id` / `SeasonStandings.team_id` já existem). **Sem tocar em
   `team_name` de nenhuma das duas tabelas** — a auditoria do M8 fica intacta.
4. `Pick.*_team_name` passa a ser **coluna de display derivada**, reescrita a partir de `Team.name` a
   cada sync (mesmo espírito do cascade de `Player.fantasy_team`, `:186-187`). Os dois leitores por
   nome restantes (`api_picks?team=`, `trades.py:87`) resolvem `Team` uma vez e comparam id.

**Picks já persistidas: não há migração de correção a fazer.** Os ids já estão corretos em 100% das
linhas; o refresh de nome do ponto 4 normaliza os rótulos na primeira execução. Não é preciso
backfill separado nem rota admin.

**Ordem interna vs. [[S2]]-F2 — S3 primeiro, e isso simplifica o S2:**
os dois tocam `_sync_traded_picks`, mas em **camadas diferentes e componíveis**: o S3 muda *como se
acha a `Pick`* (nome → id); o S2-F2 muda *qual pick é essa* (desconto `x → L(S⁻¹(x))`). Com o S3
primeiro, o desconto opera sobre **`Team`/id** e o lookup subsequente já é por id — e π é
naturalmente expresso sobre ids, já que `DraftLotteryResult.team_id` e `SeasonStandings.team_id`
existem. Na ordem inversa, o desconto produziria um **nome** que cairia justamente no match quebrado.
**Recomendo que a F2 do S3 deixe explícito o ponto de costura** — uma resolução única
"entrada de `/traded_picks` → `Team` original" — para o S2-F2 se plugar ali sem reabrir o sítio.

**Sequência final: S3-F2 → sync liberado → S2-F2-1 (corretiva) → S2-F2-2/3.**

**9 — PREMISSAS DESTE PROMPT CONTRADITAS PELO CÓDIGO**
| # | premissa | classificação | veredito |
|---|---|---|---|
| 1 | "dois sítios de match por nome … `_ensure_default_picks` **e** `_sync_traded_picks`" | **deslocamento** | Ambos são por nome, mas **só o primeiro duplica**: roda antes e já cria as linhas com o nome novo, que o segundo então encontra. Dano = **9**, não 18. |
| 2 | "criaria 9 picks duplicadas" | **confirmada** | Exatamente 9 (3 seasons × 3 rounds), reproduzido com o código real. |
| 3 | "verificar **se há** chave estável disponível" | **premissa falsa (a favor)** | Não só há — **já está gravada e correta**, inclusive nas duplicatas (`original_team_id=9` nas 18 linhas). **Zero mudança de schema.** |
| 4 | "necessidade e forma de **migração/backfill** das picks já persistidas" | **premissa falsa** | Não há o que migrar: os ids já estão certos. O refresh de nome é cosmético e cabe no próprio sync. |
| 5 | "mesma classe do incidente Brown" | **confirmada, e melhor** | O **precedente canônico está no mesmo arquivo**: `_sync_trades:670` já casa por `original_team_id`. A F2 é alinhar dois retardatários ao terceiro. |
| 6 | (implícita) "o fix é local às picks" | **perda não-intencional** | Corrigir só o match **não basta**: o join da projeção casa `Pick` × `DraftLotteryResult` × `SeasonStandings` por string, e refrescar os nomes **quebraria o verify do M8**. O join tem de ir para id — restrição forçada, não opcional. |
| 7 | (implícita) "picks são o alcance da classe" | **premissa falsa** | `PlayerHistory` (nome no índice UNIQUE de dedupe do F8a) e `Trade` (`team_a`/`team_b`) **não têm chave estável nenhuma**. Fora do escopo do S3 — item próprio. |

#### F2 — Implementação (02/08/2026 — MAN-S3-F2) ⚠️ validado em cópia, **✅ só após smoke prod**

Desenho **(A)** da F1, **sem mudança de schema**, em 4 pontos + 1 ponto de costura.

**Ponto 1 — `_ensure_default_picks` (`sync_sleeper.py:381-406`)**
`existing` passa a ser indexado por `(season, round, **original_team_id**)` e a chave de criação
vira `(season, rnd, team.id)`. Era daqui que nasciam as 9 duplicatas.

**Ponto 2 — `_sync_traded_picks` (`sync_sleeper.py:445-449`)**
`filter_by(..., original_team_id=orig_team.id)` — **cópia literal do padrão de `_sync_trades:670`**.

**Ponto 3 — join da projeção por id**
`_build_pick_projections` e as duas appliers passam a chavear
`(season, round, **team_id**)`. `_build_default_draft_order` (`routes/offseason.py:148`) passou a
devolver `(pick_number, **team_id**, team_name)`. Novo helper `_resolve_tid` usa o id e **só cai no
nome em linha legada** com `team_id` NULL (ambas as colunas são nullable).
**O contrato do M8 ficou intacto por construção:** `_build_lottery_pool` e `_build_fixed_picks` —
que alimentam o `pool_json` congelado — **não foram tocados**, e nenhum `team_name` de
`DraftLotteryResult`/`SeasonStandings` é reescrito em lugar nenhum.
Consumidores alinhados: `picks_page` (matrix chaveada por id, `teams_ordered` vira
`[{id, name}]`), `api_picks` (join por id; `?team=` resolve o `Team` uma vez e filtra por
`current_team_id`), `templates/picks.html` (linha usa `row.id`/`row.name`) e
`trades.py:78-92` (posse comparada por id).

**Ponto 4 — nome como display derivado**
Novo `_refresh_pick_team_names` (`sync_sleeper.py:471`), chamado como **passo 11b** do `run_sync`
(`:334-339`): reescreve `original_team_name`/`current_team_name` a partir de `Team.name` a cada
sync. Idempotente — sem rename, 0 linhas mudam. **Não houve migração de dados**: os ids já estavam
corretos em 100% das linhas, então não havia backfill de correção a fazer.

**Ponto de costura para o [[S2]]-F2 — `_resolve_traded_pick_identity` (`sync_sleeper.py:407`)**
Porta única "entrada de `/traded_picks` → `(season, round, Team original, Team dono)`", devolvendo
**objetos `Team`**. O docstring documenta explicitamente: o S3 responde **como** se acha a `Pick`;
o desconto do S2-F2 (`x → L(S⁻¹(x))`) responde **qual** pick é essa e entra **ali**, sobre
`orig_team` — em id, nunca em string. Nenhum outro sítio precisa ser reaberto.

**VALIDAÇÃO — 25/25 sobre cópia, sem rede**
Isolamento herdado da F1 (**não importa `app.py`**: o CSV local torna `fresh_import` truthy e
dispararia `run_sync()` real). Harness: Flask mínimo + blueprint de picks + `LOGIN_DISABLED` +
filtro `utc_iso`, `traded_picks` do JSON capturado na F1a.

| bloco | resultado |
|---|---|
| **regressão** (sync sem rename) | estado das 108 picks **byte-equivalente**; 0 nomes refrescados; 32 entradas processadas |
| **rename ingerido** | **108 picks, 0 duplicatas**; time 9 com exatamente 9; 0 rótulos com o nome antigo; refresh atuou (10 campos) |
| **projeção** | time 9 mantém **pick #11** (sem fallback 999); 12/12 times projetados no R1 2026 |
| **League Hub** | contagens **idênticas à baseline** (o rename não move posse); soma 108 |
| **rótulos** | coerentes com `Team.name` em **100%** das 108 linhas |
| **dynasty** | picks 2026 do time 9 resolvem por `DP_`, **0** em fallback `FP_` |
| **grid `/picks`** | HTTP 200; rowlabel novo **3×** (1 por season); nome antigo ausente |
| **`/api/picks`** | 36 picks em 2026, **100%** com `projected_pick` e `dynasty_value`; `?team=` pelo nome novo OK |
| **[[M8]] verify** | `match=true` + `hash=true` **antes e depois** do fix |
| `salary_engine_test` | **48/48** |

**Duas asserções da validação caíram — e o errado era o teste, não o código:**
(1) "nenhum time com >12 picks" **não é invariante** — um time acumula picks alheias via trade
(Cangaceiros tem 16, e tinha 16 na baseline). Substituída por "contagens idênticas à baseline".
(2) O **17** que a F1 reportou para o Cangaceiros era o valor **inflado pela duplicação**, não a
baseline real.

#### SMOKE EM PRODUÇÃO — ✅ APROVADO (02/08/2026)

**Gate [[PROC1]] cumprido:** hash live no Render confirmado pelo owner = **`89dc08d`** (o commit
validado, não um docs-only posterior). Backup pré-smoke: **`/data/dynasty_pre_s3_smoke_2026-08-02.db`**.

| verificação | resultado |
|---|---|
| `/picks` | **12 linhas por temporada**, **108 picks** — nenhuma linha órfã, nenhum time duplicado |
| `/league` | contagens de picks **corretas por time** |
| verify do lottery 2026 ([[M8]]) | **reprodução conferindo** — auditoria intacta após a migração do join para `team_id` |
| valores dynasty de picks no `/trades` | **resolvendo** (sem queda para o fallback agregado) |

**O caso concreto que originou o item passou limpo.** O owner **religou o sync**, e a **primeira
execução real** ingeriu o rename do time 9 (**"Tropa do Jarra"**): **sem duplicação**, com a
**projeção #11 preservada** e as referências de display atualizadas. É a validação em condição real
do que a cópia previu — o rename que teria criado 9 picks duplicadas foi absorvido sem incidente.

**Suspensão do sync ENCERRADA.** O bloqueio que o S3 impunha caiu; o [[S2]] segue 🔲 aguardando o
S2-F2, com as **posições 2–5 do R1 2026 ainda no estado permutado** — esperado e documentado.

**QUESTÕES EM ABERTO** (pós-F1 — as 4 originais foram respondidas em "1", "4", "5" e "6")
- ~~**Escopo separado a registrar:** `PlayerHistory` e `Trade` sem chave estável de time (ver "6").~~
  → **registrado como [[S4]]** (02/08/2026, MAN-S4-REG).
- O refresh de `Pick.*_team_name` no sync deve ser incondicional (toda execução) ou só quando o sync
  detectar `names_changed`? (incondicional é mais simples e idempotente)

**DEPENDÊNCIAS**
- **Bloqueia [[S2]]-F2** (o sync não pode voltar antes). Relaciona-se com [[E4-b]] (guard de
  identidade), [[M8]] (o verify do lottery **proíbe** refrescar `DraftLotteryResult.team_name`),
  [[M16]], [[T2-FIX]] (valor dynasty depende da projeção que o rename derruba), [[F8]] (índice de
  dedupe de `PlayerHistory` inclui `team_name`).

---
<!-- O3: movido verbatim de improvements.md em 02/08/2026 (MAN-S2-DONE), apos smoke em producao aprovado sobre o hash 9b4bcf1. A fatia F2-3 (tela prescritiva) foi desmembrada e segue ativa como item S5. -->
### S2 — Sync ingere trocas administrativas de picks como trades reais
✅ **Concluído (02/08/2026)** — MAN-S2-REG/F1a/F1b/F2/DONE — Prioridade **Alta** — família [[S1]] —
smoke em produção aprovado sobre o hash `9b4bcf1` (gate [[PROC1]]); desconto **armado para 2026**

**CONTEXTO**
Para montar a ordem do rookie draft 2026 no Sleeper, o co-admin criou **trocas de picks na UI do
Sleeper**. Elas **não são trades reais da liga** — são **artefato operacional**: o Sleeper só suporta
**uma ordem única de draft** para todos os rounds, enquanto o Manager já modela nativamente
**R1 = lottery** e **R2/R3 = standings invertido** ([[M16]]). Trocar picks no Sleeper é a única forma
de fazer a ordem exibida lá bater com a ordem canônica do Manager para o round que está sendo
draftado.

**SINTOMA (produção, 28/07/2026 — durante o rookie draft 2026)**
A **pick 2 do R1 2026** constava no Manager como do **time do Icaro**, quando pertence ao **time do
Fehl**. O Sleeper é a referência correta neste caso: o dono lá está certo, o Manager é que registrou
a troca administrativa como transferência de titularidade.

**CAUSA SUSPEITA (registro original — ⚠️ REFUTADA pela F1a, mantida para rastro)**
~~O sync de trades do [[S1]] (`_sync_trades`, `sync_sleeper.py:528` — movimentação de picks em
`sync_sleeper.py:648-649, "draft_picks"`) trata **toda** transação de tipo trade do
`/transactions/{leg}` como trade real da liga e a aplica ao Manager.~~
**Causa real (F1a):** as trocas administrativas **não geram transação alguma** (ferramenta de
comissário) — `_sync_trades` nunca as viu. Entram por **`_sync_traded_picks`**
(`sync_sleeper.py:407`), que reescreve o dono de toda pick de `/traded_picks` **em todo sync**, sem
auditoria. Ver F1a, seções "1" e "10".

**RISCO DE RECORRÊNCIA (anual, não pontual)**
Não é incidente de uma vez: **toda intertemporada** que envolva montar a ordem do rookie draft no
Sleeper vai gerar trocas administrativas de picks — enquanto o Sleeper mantiver ordem única por draft
e o Manager mantiver R1 = lottery + R2/R3 = standings invertido ([[M16]]), o conflito se repete a cada
ano. Sem um fix, a mitigação continua sendo operacional (suspender o sync na janela de draft), o que é
frágil e depende de lembrança.

**ESTADO DOS DADOS (a confirmar na F1 — não auditado nesta sessão)**
- Correções manuais de dono de pick **podem** ter sido aplicadas pelo co-admin via edição admin no
  `/picks` após o sintoma. O estado atual das picks 2026 em prod **não foi verificado** aqui.
- Além do dono das picks, o sync pode ter criado **registros de `Trade`** (e histórico associado)
  para essas transações — resíduo de auditoria a inventariar.

**DIRETRIZ OPERACIONAL — ATUALIZADA EM 02/08/2026**
~~Sync suspenso até o fix.~~ **Suspensão ENCERRADA:** com o [[S3]] ✅ em produção (hash `89dc08d`),
o owner **religou o sync** em 02/08/2026 e a primeira execução real correu limpa (ingeriu o rename
do time 9 sem duplicar picks). O bloqueio era do S3, não do S2.

**O que continua valendo:** o sync **reingere a permutação administrativa a cada execução** — as
posições **2–5 do R1 2026 seguem no estado permutado** e qualquer correção manual de dono de pick
listada em `/traded_picks` **não sobrevive** ao próximo sync (ver F1a "7" e F1b). Só o **S2-F2**
(desconto determinístico) fecha isso. Até lá, o estado permutado é **conhecido e documentado**, não
um defeito novo.

#### F1a — Retrato do estado (levantamento read-only, 02/08/2026 — MAN-S2-F1a)

**Nada foi escrito.** Toda leitura de banco correu sobre **cópia**; a referência externa veio da API
pública do Sleeper (só GET). Nenhum código, schema ou comportamento do sync tocado.

**RESSALVA DE ACESSO — a base auditada NÃO é `/data/dynasty.db`**
O banco vivo de produção só é alcançável pelo **Render Shell**, indisponível nesta sessão. O
levantamento correu sobre o **snapshot de prod commitado em 31/07** (`dynasty.db` da raiz, commit
`326324a` "Update dynasty.db seed com estado de prod (31/07, trades via Sleeper sync)"), copiado para
`scratchpad/s2_f1a_work.db` (598.016 bytes, original intocado). O snapshot é **posterior ao último
sync registrado** (30/07 12:05, `sync_log` id 23) e à diretriz de suspensão, então cobre o estado
relevante — mas **qualquer escrita em prod após 31/07 não está aqui**. Backup de prod que o owner
deve rodar antes de qualquer F2 que escreva:
`sqlite3 /data/dynasty.db ".backup '/data/dynasty_prod_backup_2026-08-02_pre-s2.db'"`.

**1 — AS "TRANSAÇÕES ADMINISTRATIVAS" NÃO SÃO TRANSAÇÕES**
Varredura da chain inteira de ligas (2026 `1316547584378048512` → 2025 `1224848075609100288` →
2024 `1107510813394341888`): **1.123 transações**, das quais **53 do tipo trade**. Na liga 2026 há
**6 trades**, e **todas as 6 carregam jogadores** (`adds`/`drops` não vazios). **Não existe uma única
trade só-picks em lugar nenhum da chain.**

As trocas administrativas foram feitas por **ferramenta de comissário**, que altera
`/traded_picks` **sem gerar transação**. Elas não têm `transaction_id`, não aparecem em
`/transactions/{leg}` e portanto **`_sync_trades` nunca as viu**. A porta de entrada no Manager é
**`_sync_traded_picks`** (`sync_sleeper.py:407`), que varre `/traded_picks` e sobrescreve
`Pick.current_team_id/current_team_name/traded_away` **in place, a cada sync, sem
`Trade`, sem `PlayerHistory`, sem `notes`, sem trilha de auditoria nenhuma**.

**2 — ORDEM DO BOARD DO SLEEPER (confirmada na API, não inferida)**
`GET /draft/1316547584390627328` (2026, snake, 3 rounds, `pre_draft`) — `slot_to_roster_id` e
`draft_order` são idênticos e batem **exatamente com o standings 2025 invertido**:

| slot | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| board Sleeper | Miller | mongoloides | 3 peat | Trust | Fazenda | Alex | ESPN | rafael | Cangaceiros | achane | Tropa | Pitbull |
| lottery (canônico R1) | Miller | **Fazenda** | **Trust** | **mongoloides** | **3 peat** | Alex | ESPN | rafael | Cangaceiros | achane | Tropa | Pitbull |

Os slots 2–5 divergem — é exatamente o buraco que a montagem tentou tapar.

**3 — A MONTAGEM: 4 MOVIMENTOS, TODOS EM R1 2026, INTENÇÃO CONFIRMADA 12/12**
Reconstruindo o dono canônico de cada pick **só por transações** e comparando com `/traded_picks`:

| # | pick original de | dono canônico | virou (Sleeper) | tem transação? |
|---|---|---|---|---|
| 1 | mongoloides | mongoloides | Fazenda Pederasta | **nenhuma** |
| 2 | Trust The Process | Trust The Process | mongoloides | **nenhuma** |
| 3 | 3 peat… of pain | mongoloides | Trust The Process | **nenhuma** |
| 4 | Fazenda Pederasta | Fazenda Pederasta | mongoloides | **nenhuma** (ver 4-bis) |

O nº 4 ficou **mascarado**: a trade real de 29/07 02:10 UTC (`tx 1388014829050040320`,
mongoloides→Cangaceiros) o sobrescreveu, e o `previous_owner_id` que o Sleeper reporta para essa pick
é *mongoloides* — mas **nenhuma transação da chain jamais entregou a pick da Fazenda a mongoloides**.
A chegada é administrativa; só a saída é real.

**Teste da intenção** (estado pré-29/07, montagem recém-aplicada): para cada slot do board, o dono da
pick daquele slot no Sleeper × o dono exigido pela ordem do lottery → **OK nos 12 slots**. A montagem
é **coerente e completa**: faz o board do Sleeper exibir a mesma sequência de donos que a ordem
canônica do Manager. Não foi erro do co-admin — foi tradução correta entre dois modelos incompatíveis.

**4 — DATAÇÃO: a montagem é de 08/06, não da véspera do draft**
A série `sync_log.picks_updated` é o tamanho de `/traded_picks` a cada sync:

| sync | data | picks | Δ |
|---|---|---|---|
| 1–10 | 25/03 → 08/06 00:25 | 18 | — |
| **11** | **08/06/2026 21:38** | **21** | **+3 ← montagem entra aqui** |
| 12–17 | 09/06 → 28/07 23:03 | 21 | 0 |
| 18–23 | 29/07 02:07 → 30/07 12:05 | 23 → 32 | +11 (as 6 trades reais) |

Fecha na aritmética: **18** keys movidas por transação antes de 28/07 + **3 linhas novas** da montagem
(picks próprias de mongoloides, Trust e **Fazenda** — a da 3 peat já tinha linha, virou update) = **21**,
o número exato do sync de 08/06; + **11** linhas novas das 6 trades de julho = **32**, o total de hoje
(`/traded_picks` = 32, confirmado). O `+3` do dia 08/06 é, por si só, a **prova independente do 4º
movimento** — sem a pick da Fazenda a conta daria 20, não 21.

A montagem entrou no Sleeper **entre 08/06/2026 00:25 e 08/06/2026 21:38** e foi ingerida **no mesmo
dia**, ~7 semanas antes do rookie draft.

**5 — R1 2026: DONO ATUAL × DONO CANÔNICO** (posição = ordem do lottery, modelo M16)

| pos | pick original de | dono no Manager (=Sleeper) | dono canônico (só trades) | |
|---|---|---|---|---|
| 1 | Miller Time! | Miller Time! | Miller Time! | OK |
| 2 | Fazenda Pederasta | Cangaceiros da Colina | Cangaceiros da Colina | OK *(coincidência — ver 8)* |
| 3 | Trust The Process | **mongoloides** | Trust The Process | **DIVERGE** |
| 4 | mongoloides | **Fazenda Pederasta** | mongoloides | **DIVERGE** |
| 5 | 3 peat… of pain | **Trust The Process** | mongoloides | **DIVERGE** |
| 6 | AlexTheDawg | Miller Time! | Miller Time! | OK |
| 7 | ESPN FANTASY LEAGUE | ESPN FANTASY LEAGUE | ESPN FANTASY LEAGUE | OK |
| 8 | rafaelferreirap | rafaelferreirap | rafaelferreirap | OK |
| 9 | Cangaceiros da Colina | mongoloides | mongoloides | OK |
| 10 | 🕯️ achane 🕯️ | 🕯️ achane 🕯️ | 🕯️ achane 🕯️ | OK |
| 11 | Tropa | 3 peat… of pain | 3 peat… of pain | OK |
| 12 | Pitbull do Samba | Tropa | Tropa | OK |

**3 de 12 posições divergentes hoje** (3, 4 e 5). R2/R3 2026 e todas as picks de 2027/2028: **zero**
divergência — a montagem tocou **só R1 2026**.

**6 — CONTABILIDADE DE EFEITOS PERSISTIDOS**

| efeito | atribuível às trocas administrativas |
|---|---|
| linhas de `Pick` com dono alterado | **4** (3 ainda divergentes; 1 sobrescrita por trade real) |
| linhas de `Trade` criadas | **0** — as 53 do Manager casam 1:1 com as 53 trades reais da chain; 0 órfãs |
| linhas de `PlayerHistory` criadas | **0** — as 138 de tipo `trade` têm `sleeper_event_ref` válido; 0 sem ref, 0 com ref inexistente |
| `SalaryHistory` / `AuctionLog` | **0** (tabelas vazias no snapshot) |

O dano é **estreito e cirúrgico**: 4 linhas de `Pick`, nenhum resíduo de auditoria. Contrapartida
ruim: como não há resíduo, **não há rastro nenhum** de que a alteração aconteceu.

**7 — SYNC × EDIÇÃO MANUAL: nenhuma correção manual sobreviveu**
Divergência Manager × Sleeper em **todas as 108 picks: ZERO**. O Manager é espelho fiel do
`/traded_picks` — inclusive da ficção. Como uma correção manual produziria necessariamente
divergência (o Sleeper segue com a montagem), **não há correção manual viva neste snapshot**: ou não
foi feita, ou um sync posterior a reverteu (houve 6 syncs entre 28/07 e 30/07).

Não é possível separar sync × edição manual pelos registros: `PATCH /api/picks/<id>`
(`routes/picks.py:235`) altera `current_team_name`/`notes` **in place**, a tabela `picks` **não tem
`updated_at`**, e a rota **não grava auditoria**. As únicas evidências indiretas possíveis são
`notes` preenchida (**0 de 108**) e divergência vs. Sleeper (**0**). Os 108 `created_at` são todos do
mesmo instante (25/03/2026 18:49:02, criação inicial).

**8 — O CASO DA PICK 2, RESOLVIDO**
Posição 2 do R1 2026 = pick **originalmente da Fazenda Pederasta** (`fernandoxmf`), sorteada para o
2º overall. O movimento administrativo nº 4 (Fazenda→mongoloides) fez o Manager exibi-la como do
**mongoloides = `icarocosta1` = Icaro** ✓, quando o dono canônico era a **própria Fazenda Pederasta**.
Bate com o sintoma relatado — assumindo **"Fehl" = `fernandoxmf` (Fazenda Pederasta)**, mapeamento
que **não é confirmável pelos dados** (nenhum campo do banco ou do Sleeper carrega esse apelido) e
que o owner precisa confirmar.

Cronologia: o rookie draft foi em **28/07**; a trade real mongoloides→Cangaceiros é de **29/07 02:10
UTC** (23:10 BRT de 28/07). Ou seja, **no momento do sintoma a posição 2 era do Icaro**; depois dela,
passou a ser do Cangaceiros **nos dois sistemas**. **O sintoma originalmente relatado já não é
visível** — o dano residual migrou para as posições 3, 4 e 5.

**9 — COMPLICAÇÃO REAL PARA O FIX (não resolver aqui)**
A trade real `tx 1388014829050040320` foi **registrada contra uma pick que mongoloides só possuía por
causa da ficção administrativa** (a da Fazenda). Em termos de *board*, o negócio é legítimo:
mongoloides cedeu o direito de escolher **no 5º overall**, que ele de fato tinha (pick da 3 peat,
adquirida em trade real de 30/09/2025). Só o **rótulo** de "qual pick original" está errado.
Qualquer reconstrução do estado canônico terá de **re-rotular essa trade** (o certo seria "pick da
3 peat → Cangaceiros"), não apenas desfazer os 4 movimentos. Desfazer cegamente devolveria a pick da
Fazenda à Fazenda **e apagaria o que o Cangaceiros comprou**.

**10 — PREMISSAS DESTE PROMPT / DO REGISTRO CONTRADITAS PELOS DADOS**
| # | premissa | veredito |
|---|---|---|
| 1 | "o **sync de trades** ([[S1]] `_sync_trades`) ingeriu as trocas" | **FALSA.** As trocas não são transações; entram por `_sync_traded_picks` (`/traded_picks`). `_sync_trades` nunca as viu. Muda a superfície inteira do fix. |
| 2 | "transações de trade **envolvendo apenas picks**" | **FALSA.** Não existe trade só-picks na chain; as 6 trades de 2026 têm jogadores. Filtrar "trade só-picks" **não pega nada** e **quebraria trades reais** de picks. |
| 3 | "trocas criadas **pouco antes** do rookie draft de 28/07" | **FALSA.** Entraram em **08/06/2026**, ingeridas no mesmo dia, ~7 semanas antes. |
| 4 | "correções manuais **podem ter sido aplicadas** pelo co-admin" | **SEM SUSTENTAÇÃO.** 0 divergências vs. Sleeper, 0 `notes`. Se houve, foi revertida por sync posterior. |
| 5 | "o sync pode ter criado **linhas de `Trade`/histórico**" | **FALSA.** 0 linhas atribuíveis; auditoria 100% conciliada com transações reais. |
| 6 | "**suspender o sync** protege o estado" | **PARCIAL.** Protege contra novas reversões, mas o estado **já está corrompido** (3 posições) e **fica** corrompido enquanto suspenso. Suspensão não é mitigação — é congelamento. |
| 7 | "o **Sleeper é a referência correta**" (registro) | **PARCIAL/PERIGOSA.** O Sleeper está certo na *sequência do board*, mas **errado na titularidade** — é a fonte da ficção. Copiar o Sleeper é justamente o que produz o bug. |

**OBSERVAÇÃO COLATERAL (não é S2 — candidata a item próprio na F1b)**
O time `id=9` chama-se **"Tropa do Bicampeonato 🏆"** no banco e **"Tropa do Jarra 🏆"** no Sleeper
hoje — foi renomeado. `_sync_traded_picks` casa pick por **`original_team_name` (string)**
(`sync_sleeper.py:421-425`): se o nome do `Team` for atualizado pelo sync enquanto as linhas de
`Pick` guardam a string antiga, o lookup falha e o ramo `else` **insere linha duplicada** em vez de
atualizar. Hoje ainda são 108 picks (12 × 9, sem duplicata), então **não disparou** — mas é a mesma
classe do incidente "Brown" (identidade por string em vez de id).

#### F1b — Diagnose analítica (read-only, 02/08/2026 — MAN-S2-F1b)

Código lido, nada alterado. Nenhuma escrita em banco.

**1 — SEMÂNTICA DE `_sync_traded_picks` (`sync_sleeper.py:407`)**

O passo 11 do `run_sync` (`sync_sleeper.py:334`) roda **depois** do passo 10
(`_ensure_default_picks`, `:361`) e **antes** do `_sync_trades` (`:340`). A cadeia é:

1. `_ensure_default_picks` **apaga** `Pick.season < datetime.now().year` (`:376`) e **cria** as
   faltantes com `current = original`, indexando o que já existe por
   **`(season, round, original_team_name)`** (`:383`) — chave de **string**.
2. `_sync_traded_picks` varre `/traded_picks` e, para cada entrada, busca a `Pick` por
   `original_team_name` (`:421-425`) e **sobrescreve** `current_team_id`, `current_team_name` e
   `traded_away` (`:427-430`). Não lê `sleeper_transaction_id`, não consulta estado anterior, não
   grava nada além disso.

**Pick ausente do payload: NÃO é tocada.** Não existe passo de reconciliação que devolva ao dono
original uma pick que saiu de `/traded_picks`. Consequência prática — **refina a F1a**: "correção
manual não sobrevive ao sync" vale **só para picks listadas em `/traded_picks`**. Uma correção numa
pick não-trocada sobreviveria indefinidamente. As 4 em questão **estão todas no payload**, então
para elas a conclusão da F1a se mantém integralmente.

**2 — DONO-NA-POSIÇÃO: fonte única para a POSIÇÃO, réplica difusa para o DONO**

A pergunta tem **duas respostas diferentes**, e é aí que mora a armadilha:

- **Posição — fonte única, sem réplica.** `_build_pick_projections` (`routes/picks.py:135`) é o
  único lugar que deriva `(season, round, original_team_name) → pick_number`. Aplica M16 via
  `_apply_lottery_with_standings_tail` (`:208`, R1 = `DraftLotteryResult`) e
  `_apply_standings_order` (`:187`), ambos delegando a `_build_default_draft_order`
  (`routes/offseason.py`) — a fonte única do M15. Consumidores: `picks_page` (`:51`) e `api_picks`
  (`:112`). **Não há réplica em JS**: o `<script>` de `picks.html` só filtra linhas por
  `data-orig`/`data-cur` já renderizados; nenhuma aritmética de ordem no cliente.
- **Dono — lido cru de `Pick.current_team_*` em ≥ 4 sítios que NÃO passam pela projeção:**
  `routes/league.py:53-54` (contagem de picks por time no League Hub), `routes/league.py:89-90`
  (lista de picks no detalhe do time), `routes/trades.py:86` e `:449` (ativos de trade),
  `routes/picks.py:106` (filtro `?team=`). Nenhum deles sabe de posição.
- **"Dono-na-posição" não existe como objeto em lugar nenhum** — é um *join implícito* feito no
  template (`picks.html:39-40`, célula = `cells[(team,rnd)]` + `projections[(team,rnd)]`). Não há
  fonte única a corrigir: **corrigir a projeção não corrige o dono, e vice-versa.**
- **Nota colateral:** `routes/trades.py:124-125` decide `dynasty_value_is_estimate` por
  `getattr(pick, "projected_pick", None)`, que **só é populado em `api_picks`** (`:123`). No caminho
  de `_compute_cap_impact` o atributo nunca existe → **toda** pick vira estimativa middle-of-round.
  É o dead path já documentado no T2-FIX-2; não é dano do S2, mas significa que o cap impact de
  trade **não consome a projeção**.

**3 — MECANISMO FORMAL DA DUPLA APLICAÇÃO (provado nas 12 posições)**

Sejam `L(p)` = time sorteado para a posição `p` (lottery), `S(p)` = time do slot `p` no board do
Sleeper (standings 2025 invertido) e `O(t)` = dono canônico da pick própria de `t` por trades reais.

A montagem do co-admin estabelece, para todo `p`: `dono_sleeper(pick de S(p)) = O(L(p))`.
O Manager, por sua vez, exibe na posição `p` o dono da pick de `L(p)`. Substituindo:

> **Manager(p) = O( L( π(p) ) )**, com **π = S⁻¹ ∘ L** — em vez de `O(L(p))`.

Verificado computacionalmente: a fórmula **reproduz o Manager nas 12 posições**. Logo o Manager está
correto exatamente onde **π é a identidade**, isto é, onde `S(p) = L(p)`:

| p | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| π(p) | 1 | **5** | **4** | **2** | **3** | 6 | 7 | 8 | 9 | 10 | 11 | 12 |

**Por que 8 das 12 coincidem:** o lottery só sorteia as 6 primeiras posições (M15) e **não moveu**
Miller (1º) nem AlexTheDawg (6º); as posições 7–12 são fixas por standings nos **dois** modelos. Sobra
π como um **4-ciclo puro em {2,3,4,5}** (2→5→3→4→2). As 8 posições fixas são **imunes por
construção**, não por sorte. Corolário para o risco anual: o dano é limitado ao número de seeds do
lottery que o sorteio de fato deslocou — **no máximo 6 posições**, nunca 12.

**4 — CORREÇÃO DA F1a: são 4 posições divergentes, não 3**

A F1a comparou o Manager contra um "canônico" que ainda carregava o **rótulo errado** da trade de
29/07 (`tx 1388014829050040320`), e por isso a **posição 2 apareceu como OK**. Aplicando o re-rótulo,
ela é divergente. O dano correto é **4 de 12** — posições **2, 3, 4 e 5**, exatamente o suporte de π.

**Derivação do re-rótulo (única possível).** No board, mongoloides detinha os slots 4, 5 e 9. A trade
cedeu ao Cangaceiros o **slot 5**, que a Sleeper rotula como "pick da Fazenda". Pelo lottery, a
posição 5 é a pick da **3 peat**, que mongoloides possuía legitimamente desde 30/09/2025. Restam-lhe
o slot 4 (= sua própria pick) e o slot 9 (= pick do Cangaceiros, trade real de 02/10/2025) — tudo
consistente. Portanto o ativo negociado é a **pick da 3 peat**, não a da Fazenda.

**5 — ESTADO-ALVO DO R1 2026**

| pos | pick original de | dono no Manager hoje | **dono-ALVO** | bate com o board? | |
|---|---|---|---|---|---|
| 1 | Miller Time! | Miller Time! | Miller Time! | OK | |
| 2 | Fazenda Pederasta | Cangaceiros da Colina | **Fazenda Pederasta** | OK | **DIVERGE** |
| 3 | Trust The Process | mongoloides | **Trust The Process** | OK | **DIVERGE** |
| 4 | mongoloides | Fazenda Pederasta | **mongoloides** | OK | **DIVERGE** |
| 5 | 3 peat… of pain | Trust The Process | **Cangaceiros da Colina** ← re-rótulo | OK | **DIVERGE** |
| 6 | AlexTheDawg | Miller Time! | Miller Time! | OK | |
| 7 | ESPN FANTASY LEAGUE | ESPN FANTASY LEAGUE | ESPN FANTASY LEAGUE | OK | |
| 8 | rafaelferreirap | rafaelferreirap | rafaelferreirap | OK | |
| 9 | Cangaceiros da Colina | mongoloides | mongoloides | OK | |
| 10 | 🕯️ achane 🕯️ | 🕯️ achane 🕯️ | 🕯️ achane 🕯️ | OK | |
| 11 | Tropa | 3 peat… of pain | 3 peat… of pain | OK | |
| 12 | Pitbull do Samba | Tropa | Tropa | OK | |

**Verificação independente:** o alvo coincide com a **leitura direta do board do Sleeper**
(`dono do pick do time que ocupa o slot p`) nas **12 posições**. Ou seja — o board do Sleeper **já
exibe a ordem correta**; o Manager é que a re-permuta ao projetar.

**6 — POR QUE "MANDAR O CO-ADMIN NÃO FAZER A MONTAGEM" NÃO É OPÇÃO**
A alternativa óbvia — editar o `draft_order` do Sleeper para a ordem do lottery em vez de permutar
picks — **quebraria o M16**: o `slot_to_roster_id` vale para **todos os rounds**, então o lottery
vazaria para R2/R3, que devem seguir standings invertido. A permutação de picks é justamente a
técnica **correta**: move só os ativos do R1 e deixa R2/R3 no slot order nativo (= standings
invertido = M16). **A montagem é necessária e vai se repetir todo ano** — o fix tem de conviver com
ela, não eliminá-la.

**7 — TRÊS DESENHOS DE FIX (avaliação, sem implementar)**

*Observação estrutural que reordena a discussão:* **(a) e (b) produzem a mesma ordem** — ambos
equivalem a `O(L(p))`. A diferença não está no resultado exibido, mas em **onde a correção mora**:
(a) conserta a *leitura*, (b) conserta o *dado gravado*. E (b) tem uma propriedade forte: re-chavear
a entrada de `/traded_picks` de `x` para `L(S⁻¹(x))` transforma os **3 movimentos puramente
administrativos em no-ops** (`pick de X → X`) e **re-rotula sozinha** a trade real. A montagem *é* a
permutação; descontá-la a aniquila.

| critério | (a) virada de autoridade | (b) desconto determinístico | (c) marcação manual pós-sync |
|---|---|---|---|
| **trades reais na janela** | corretas de graça — lê por slot, o re-rótulo é implícito | corretas — re-chaveamento re-rotula automaticamente | corretas se ninguém errar a marcação; risco de marcar trade real como administrativa |
| **correção manual sobrevive?** | pergunta não se aplica (nada a corrigir), mas o **dado gravado segue errado** → os ≥4 leitores diretos de `current_team_*` (League Hub, detalhe de time, trades) continuam exibindo dono errado | **sim** — grava o estado certo; auto-cura a cada sync; todos os consumidores ficam certos | **não**, salvo com coluna nova de *pin* que `_sync_traded_picks` respeite (schema + UI + disciplina) |
| **recorrência anual** | precisa de flag de janela (quando o board está espelhado); erra feio se aplicada fora da janela | mesma flag, mesmo risco — mas **verificável**: fora da janela o desconto vira identidade se π = id | trabalho manual todo ano, ≤ 6 movimentos; é exatamente o modo de falha que gerou o S2 |
| **[[OFF26-3]] (importador)** | **indiferente** | **indiferente** | **indiferente** |

Sobre o importador: `draft_import` lê `roster_id` **de cada pick real do draft** na API
(`routes/draft_import.py:109-125`) e mapeia direto a time. **Não consulta `Pick` nem a projeção** —
é imune aos três desenhos e ao dano do S2. Não é critério de desempate.

**Risco compartilhado por (a) e (b):** ambos dependem de a montagem estar **completa** quando o sync
roda. Meia-montagem ingerida com desconto ligado produz rótulos errados *com aparência de corretos* —
pior que o bug atual, que ao menos é detectável. Isso empurra para uma quarta peça, abaixo.

**8 — RECOMENDAÇÃO DE ESCOPO PARA A F2 (única)**

**Adotar (b), em duas fatias, mais o fechamento do laço operacional.**

- **F2-1 — corretiva, isolada, agora.** Levar as 4 linhas do R1 2026 ao estado-alvo da tabela em "5",
  por rota admin auditável (molde M8: snapshot + `reason` + hash), com o sync ainda suspenso. É
  reversível e não depende de nenhuma decisão estrutural. **Pré-requisito bloqueante:** o
  [[S3]] (rename) precisa ser fechado **antes** de o sync voltar a rodar — hoje o time 9 já está
  renomeado no Sleeper e o próximo sync criaria linhas duplicadas de `Pick`, corrompendo a correção
  recém-aplicada.
- **F2-2 — estrutural.** Desconto determinístico em `_sync_traded_picks`, escopado a
  **R1 da draft season**, armado por flag explícita de AppConfig, com π derivado do
  `DraftLotteryResult` canônico + `_build_default_draft_order` (as duas fontes únicas que já
  existem). Fora da janela, π = identidade e o desconto é inócuo.
- **F2-3 — fecha o laço (é o que torna (b) seguro).** Tela na intertemporada que **calcula π e emite
  a lista exata de permutações** que o co-admin deve executar no Sleeper, e só então liga a flag.
  Hoje a montagem é conhecimento tácito do co-admin; com isso o Manager **prescreve** a permutação e
  portanto **sabe** exatamente o que vai ler de volta — que é a única forma de o desconto não ser
  heurística. Sem F2-3, (b) é aposta na disciplina alheia; com ela, é aritmética fechada.

Rejeitados: **(a)** porque conserta só a tela e deixa `Pick.current_team_*` errado para os ≥ 4
leitores diretos — o League Hub continuaria contando picks no time errado; **(c)** porque exige
schema novo *e* disciplina anual, entregando menos que (b) por mais trabalho.

**9 — PREMISSAS DESTE PROMPT CONTRADITAS PELO CÓDIGO / PELOS DADOS**
| # | premissa | classificação | veredito |
|---|---|---|---|
| 1 | "Dano: **3** de 12 posições (3, 4 e 5)" | **premissa falsa** (erro meu na F1a) | São **4** — 2, 3, 4 e 5. A F1a comparou contra um canônico que ainda tinha o rótulo errado da trade de 29/07, e a posição 2 passou como OK. |
| 2 | "correções manuais não sobrevivem: o sync seguinte as reverte" | **verdadeira, mas por motivo mais estreito** | Só vale para picks **listadas em `/traded_picks`**; não há passo de reconciliação para picks ausentes do payload. Vale para as 4 em questão. |
| 3 | "(a) e (b) são desenhos alternativos" | **deslocamento** | Produzem a **mesma ordem** (ambos = `O(L(p))`). O eixo real de escolha é *consertar leitura × consertar dado gravado*, não a ordem resultante. |
| 4 | "a derivação dono-na-posição existe em fonte única ou replicada?" (pressupõe que exista) | **premissa falsa** | "Dono-na-posição" **não existe como objeto**. A *posição* tem fonte única (`_build_pick_projections`); o *dono* é lido cru em ≥ 4 sítios. O join só acontece no template. |
| 5 | "o fix vive no sync" (implícita) | **perda não-intencional** | O sync não pode voltar a rodar antes do [[S3]]: o rename já feito no Sleeper dispara criação de `Pick` duplicada em `_ensure_default_picks` **e** em `_sync_traded_picks`. |

#### F2 — Implementação (02/08/2026 — MAN-S2-F2) ⚠️ validado em cópia, **✅ só após smoke prod**

Desenho **(b)** da F1b — desconto determinístico. Fatias **F2-2** (desconto) e **F2-1** (correção do
estado). **Sem schema.** A F2-3 (tela prescritiva) segue como item futuro.

**Novo módulo `board_mirror.py`** — π derivado, nunca hardcoded:
- `L` = `{pick_number: team_id}` do `DraftLotteryResult` da draft season;
- `S` = `{slot: team_id}` do board = **standings invertido**, derivado da **fonte única já
  existente** `_build_default_draft_order` (M15/M16) — não reimplementa a ordem;
- `π = {S[p]: L[p]}`. Se não for **bijeção**, retorna `{}` e o desconto **não opera** — colisão
  significa board meio-montado, e descontar aí produziria rótulos errados com cara de certos.

**Armamento — `AppConfig["board_mirrored_season"]` guarda a SEASON, não um booleano.**
Decisão do Code, com justificativa: o **rollover desarma sozinho** (avança `current_season`, logo
`draft_season = current_season + 1` muda e o valor guardado deixa de casar). Um booleano
sobreviveria ao rollover e dispararia o desconto no ano seguinte sobre um board **ainda não
montado** — corrupção silenciosa, pior que o bug atual. Dois gates ANDados: season armada ==
draft season corrente **e** existe **audit canônica de lottery** para ela (sem sorteio canônico não
existe `L`, logo não existe π).

**Por que toggle explícito e não detecção automática:** a montagem **não deixa rastro** (não é
transação, F1a "1"). Inferi-la seria adivinhar intenção a partir de ausência de evidência, e uma
montagem **parcial** ingerida com o desconto ligado corromperia em silêncio. O ato explícito de quem
executou a montagem é o único sinal honesto — e a F2-3 fecha o laço fazendo o Manager **prescrever**
a permutação.

**Sítios ligados (o desconto compõe sobre o casamento por id do [[S3]], não o substitui):**
1. `_resolve_traded_pick_identity` (`sync_sleeper.py:427`) — a costura que o S3 deixou pronta.
   Aplica π sobre `orig_team`, em `Team`/id.
2. **`_sync_trades`, loop de picks (`sync_sleeper.py:~665`) — extensão deliberada além da letra do
   prompt.** Uma trade **real** fechada dentro da janela é registrada pelo Sleeper contra o rótulo
   do slot; sem o mesmo desconto ali, o passo 12 sobrescreveria com o rótulo errado o que o passo 11
   acabou de gravar certo (o estado só se recuperaria no sync seguinte). Os outros dois chamadores
   de `_sync_trades` (backfill de ligas anteriores) não passam desconto → identidade.
3. `/admin` — card mínimo de armar/desarmar + `POST /api/admin/board_mirror` (`@admin_required`).
   Não é a tela prescritiva da F2-3; é só o interruptor.

**F2-1 — RESPOSTA: a rota corretiva é REDUNDANTE. O próprio sync reescreve as 4 posições.**
As 4 entradas administrativas de `/traded_picks` re-chaveadas formam uma **bijeção** sobre o mesmo
conjunto de times `{mongoloides, 3 peat, Trust, Fazenda}` → **exatamente as 4 linhas divergentes
recebem escrita explícita**. Três viram no-op (`pick de X → X`) e a quarta re-rotula a trade real.
Nenhuma linha-alvo fica de fora, então **não há o que corrigir à mão**: a correção é armar o
desconto e rodar o sync. Verificado na validação (bloco 2). **A rota admin auditável prevista na
F1b não foi implementada** — seria código morto.

**VALIDAÇÃO — 24/24 sobre cópia, sem rede** (isolamento das fases anteriores: sem `import app`)

| bloco | resultado |
|---|---|
| **desarmado** | desconto inativo; estado das picks **byte-equivalente** ao atual |
| **armado → alvo** | π com 12 entradas, **4 re-chaveadas**; as **12 posições do R1 2026 batem com a tabela-alvo da F1b** |
| **re-rótulo** | pos. 2 → **Fazenda Pederasta**, pos. 5 → **Cangaceiros** (o ativo da trade de 29/07 é a pick da 3 peat) |
| **idempotência** | 2ª execução não altera **nenhuma** pick; R1 segue no alvo |
| **escopo** | 96 linhas fora do R1 2026 (R2/R3 + 2027/2028) **idênticas** ao estado inicial |
| **trade real na janela** | move **só** a posição negociada, com o desconto armado |
| **gates** | season ≠ draft season → inativo; sem audit canônica → inativo; armado correto → ativo |
| **[[M8]] verify** | `match` + `hash` **antes e depois** |
| **`/admin`** | render 200, card presente, armar/desarmar via endpoint, estado refletido |
| `salary_engine_test` | **48/48** |

**PREMISSA DO PROMPT CONTRADITA — critério de validação incorreto.** O prompt pediu "posição 2 →
Cangaceiros via pick da 3 peat". Isso **contradiz a própria tabela-alvo da F1b** que o prompt cita
como autoridade: o alvo é **pos. 2 → Fazenda Pederasta** e **pos. 5 → Cangaceiros**. A confusão vem
de "Cangaceiros na posição 2" ser o **estado permutado atual** (o defeito), não o alvo — a pick da
3 peat ocupa a **posição 5** pelo lottery. A implementação segue a tabela da F1b.

#### SMOKE EM PRODUÇÃO — ✅ APROVADO (02/08/2026)

**Gate [[PROC1]] cumprido:** hash live no Render confirmado pelo owner = **`9b4bcf1`**.
Backup prévio: **`/data/dynasty_pre_s2_smoke_2026-08-02.db`**.

Executado: desconto **armado para 2026** via `/admin` → **sync rodado** → conferência.

| verificação | resultado |
|---|---|
| pos. **2** | **Fazenda Pederasta**, sem troca — a ficção administrativa desapareceu |
| pos. **5** | **3 peat → Cangaceiros** — **re-rótulo da trade de 29/07 confirmado em produção** |
| pos. **3 e 4** | donas originais corretas |
| cruzamento com o board do Sleeper | **confere** — `1.05` via `fernandoxmf` visível no roster MellowBR |
| 2ª execução do sync | **nenhuma alteração** — idempotência confirmada **em produção** |
| verify do lottery 2026 ([[M8]]) | reprodução conferindo |
| pos. 1 e 6–12, R2/R3 e seasons futuras | **intactos** |

As **4 posições convergiram para o alvo derivado na F1b**, e a checagem contra o board do Sleeper
fechou o ciclo: o alvo era, desde a derivação, "o que o board já exibia" — e é o que o Manager
agora exibe.

**Estado operacional:** sync **liberado e com o desconto armado para 2026**. O **desarme no rollover
é por construção** (o armamento guarda a season, não um booleano) — nada a lembrar na virada.

**Fica em aberto (item próprio, não iniciado):** a fatia **F2-3** — tela que **prescreve** a
permutação ao co-admin — registrada como **[[S5]]**. Enquanto ela não existir, o desconto depende de
o co-admin montar o board exatamente como a álgebra prevê, e do owner armar o toggle depois disso.

**QUESTÕES EM ABERTO** (F1b — a F1a acima **fechou as de nº 2, 3 e 6** e **refutou a premissa da
nº 1**; ver vereditos em "10". As reformuladas ficam abaixo como **1', 2', 3', 6'**)

*Fechadas pela F1a:*
- ~~2. Escopo do dano~~ → **4 linhas de `Pick`** (3 divergentes hoje), **0** `Trade`, **0**
  `PlayerHistory`, **0** correção manual sobrevivente. Só R1 2026.
- ~~3. Idempotência × correção manual~~ → **não há idempotência a invocar**: `_sync_traded_picks`
  não consulta `sleeper_transaction_id` (não existe transação); ele **reescreve o dono de toda pick
  de `/traded_picks` em todo sync**. Correção manual **não sobrevive ao próximo sync**, sempre.
- ~~6. Detecção~~ → **nenhuma superfície** mostra mudança de dono de pick; `picks` não tem
  `updated_at`, a rota PATCH não audita e `notes` está vazia nas 108. O sintoma só aparece na tela.

*Abertas / reformuladas:*
1'. **Distinguibilidade sem transação:** já que a troca administrativa chega por `/traded_picks`
   **sem payload de transação**, o único sinal disponível é **estrutural** — uma mudança de dono que
   **nenhuma transação da chain explica** (foi exatamente assim que a F1a achou as 4). Isso é
   computável a cada sync. Vale como gate automático (`needs_review`), ou o custo de varrer a chain
   inteira em todo sync é proibitivo? Há alternativa (cachear o conjunto explicado)?
2'. **Estratégia de reconstrução:** desfazer os 4 movimentos **não basta** — a trade real de 29/07
   precisa ser **re-rotulada** (ver "9"). O alvo é um estado canônico derivado **só de transações**,
   e ele é integralmente computável (a F1a já o computou). Reconstruir tudo por derivação × corrigir
   as 3 linhas divergentes à mão?
3'. **Reincidência dentro do mesmo ciclo:** a montagem de 08/06 continua **viva no Sleeper**. Qualquer
   sync futuro a reingere. O fix precisa ser **idempotente contra um Sleeper permanentemente
   "errado"**, não uma limpeza de uma vez.
6'. **Superfície de detecção:** vale expor "picks cujo dono mudou no último sync" / divergência
   Manager × canônico no `/admin`, no espírito do [[PROC2]]?
4. **Autoridade sobre picks:** o split de autoridade documentado ("Sleeper é autoritativo para traded
   picks") ainda vale, dado que o Manager tem ordem canônica própria (M16) e o Sleeper é forçado a
   distorcer a dele? Candidato a **inverter a autoridade de picks** para o Manager — decisão de
   design, não de implementação.
5. **Forma do fix (não decidir antes da F1b):** as opções mudaram com a F1a — o alvo é
   `_sync_traded_picks`, não `_sync_trades`, e "filtrar trade só-picks" está **descartado** (não
   existe nenhuma). Restam: derivar picks **só de transações** e parar de ler `/traded_picks` ×
   aplicar `/traded_picks` só quando explicado por transação, senão `needs_review` × inverter a
   autoridade de picks para o Manager (ver nº 4) × janela de bloqueio na intertemporada. Todas
   precisam preservar as trades **reais** de picks, que existem e continuam entrando.

**DEPENDÊNCIAS**
- Relaciona-se com: [[S1]] (família do sync — mas a porta é `_sync_traded_picks`, não `_sync_trades`;
  ver F1a "10"), [[M16]] (modelo R1 lottery / R2-R3 standings invertido — a razão de o Sleeper e o
  Manager divergirem), [[MAN-S1-FIX]] (precedente de dano por movimentação cega no sync), [[PROC2]]
  (superfície de detecção no `/admin`). ~~Bloqueia: uso normal do sync até o fix.~~ **Não bloqueia
  mais o sync** — com o [[S3]] ✅ (02/08/2026) a suspensão foi encerrada e o sync está religado; o
  que resta é o estado permutado das posições 2–5 do R1 2026, que só o S2-F2 corrige.

## Sessão 04/08/2026 — arco do IR no cap (OFF26-14/16/17/18 + IR-CLEANUP)

> Migrados do backlog ativo ao serem marcados ✅ (regra O3), após o **smoke consolidado de
> produção de 04/08/2026** passar nos 6 pontos. Seções **verbatim**. ⚠️ Leitura importante:
> a **F2 do OFF26-14 (rotular duas réguas) foi REVERTIDA pelo OFF26-16** (régua única, o IR
> conta no cap) — o racional das duas decisões está preservado lado a lado de propósito,
> como precedente de correção com histórico.

### OFF26-14 — Duas contagens de cap convivem: as telas de roster EXCLUEM o salário de IR
✅ **Fechado em 04/08/2026 — smoke consolidado de produção PASSOU** — Prioridade **Alta** — `MAN-OFF26-14-F1`/`-F2`. ⚠️ **A F2 (rotular duas réguas) foi REVERTIDA pelo [[OFF26-16]]** — racional preservado abaixo de propósito

**A decisão do owner é o critério:** o **IR CONTA no cap**. Logo, toda superfície que exclui o
salário de IR da contagem está **desalinhada da regra** — e é justamente a superfície que cada owner
olha para decidir o que cortar em **20/08**.

**Por que é Alta e não cosmético:** o número errado governa uma decisão com prazo. Um owner que veja
`$186 usados / $14 restantes` na tela de roster pode concluir que está enquadrado quando a régua que
o leilão realmente usa diz outra coisa.

#### T1 — Mapa completo das contagens de salário

**Grupo A — EXCLUI IR (11 superfícies).** Todas descendem de uma decisão só, mas **não de uma fonte
só** (ver T3).

| # | onde | linha | procedência |
|---|---|---|---|
| A1 | `Team.active_salary()` | [models.py:96-100](models.py#L96-L100) | **a origem** — `if not p.is_dropped and not p.is_on_ir` |
| A2 | `Team.cap_remaining()` | [models.py:105](models.py#L105) | deriva de A1 |
| A3 | `Team.to_dict()` → `/api/teams` | [models.py:116-117](models.py#L116-L117) | expõe A1 e A2 |
| A4 | chip de cap da navbar (`$X/$200`) | [app.py:121](app.py#L121) → [base.html:73](templates/base.html#L73) | `g_user_team_cap` = A1 |
| A5 | banner M1 "time está $N acima do cap" | [roster.py:98-100](routes/roster.py#L98-L100) | A1 |
| A6 | **página de roster** (`$186 / $14`) | [roster.py:85,89,108](routes/roster.py#L85-L108) | **soma inline**, não usa A1 |
| A7 | cards do League Hub (`cap_used`/`cap_space`) | [league.py:22,33-34](routes/league.py#L22-L34) | **soma inline** |
| A8 | `/team/<id>` (`cap_used`/`cap_remaining`) | [league.py:97-99,120-121](routes/league.py#L97-L121) | **soma inline** |
| A9 | preview de rollover (`total_current`/`total_next`) | [admin.py:159-160](routes/admin.py#L159-L160) | **soma inline** |
| A10 | alerta de cap pós-trade no sync | [sync_sleeper.py:581](sync_sleeper.py#L581) | A1 |
| A11 | preview/proposta de trade (`cap_before/after`, `over_cap`) | [trades.py:151-152,204-207](routes/trades.py#L151-L207) | A1 |

**Grupo B — INCLUI IR (a régua do leilão).** Todas descendem de **uma fonte única**.

| # | onde | linha | procedência |
|---|---|---|---|
| B1 | `salary_engine.draft_budget()` | [salary_engine.py:218-219](salary_engine.py#L218-L219) | **a fonte** — filtra só `is_dropped`; **sem menção a IR** |
| B2 | Cap Projector (GET) | [salary.py:92](routes/salary.py#L92) | B1 |
| B3 | porta canônica `POST …/budget` | [salary.py:180](routes/salary.py#L180) | B1 (`kept_ids` do cliente) |
| B4 | **janela de cortes — budget ao vivo** | [cuts.html:115-119](templates/cuts.html#L115-L119) | B3 com `projected:false`; `rosterIds()` vem da tabela renderizada, que **inclui os de IR** ([cuts.py:102-107](routes/cuts.py#L102-L107), badge IR na linha 38) |
| B5 | **keeper sheet — `fa_budget`** | [cuts.py:387-392](routes/cuts.py#L387-L392) | B1 sobre `keepers` = roster − cortes (**IR incluído**) |
| B6 | **auditoria [[OFF26-4]] — `fa_budget` e `sheet_total`** | [keeper_audit.py:429-458](keeper_audit.py#L429-L458), [:215](keeper_audit.py#L215) | consome `_build_keeper_sheet` (= B5) |
| B7 | alertas de budget do importador OFF26-3 | [draft_import.py:74-77](routes/draft_import.py#L74-L77) | B1 |
| B8 | `Team.total_salary()` | [models.py:102-103](models.py#L102-L103) | ⚠️ **código morto** — definido, **zero consumidores** |

**Quantificação (leitura `mode=ro` de 03/08, dev):** os dois grupos divergem em **3 times, $14 no
total**. O resto dos 12 tem os dois números iguais porque **não tem ninguém em IR** — é o motivo de
a divergência ter passado despercebida.

| time | sem IR (grupo A) | com IR (grupo B) | dif | quem está em IR |
|---|---|---|---|---|
| **🕯️🕯️ achane 🕯️🕯️** | **$186** | **$195** | **$9** | Michael Penix $1, Travis Hunter $8 |
| rafaelferreirap | $133 | $136 | $3 | Zach Charbonnet $3 |
| Fazenda Pederasta | $176 | $178 | $2 | Kendre Miller $1, Tory Horton $1 |
| *(os outros 9)* | — | — | **$0** | ninguém |

Confere com o lido em produção pelo owner: **$186 na tela de roster, $195 na contagem de keeper**, e
a diferença é **exatamente** a soma dos dois jogadores em IR.

#### T2 — Origem da divergência: não há decisão registrada

- **Não é efeito colateral de filtro de roster.** O filtro é **explícito e dedicado**:
  `if not p.is_dropped and not p.is_on_ir` ([models.py:99](models.py#L99)). Alguém escreveu `and not
  p.is_on_ir` de propósito.
- **Não há comentário, docstring ou teste** justificando. `active_salary` não tem docstring; **nenhum
  teste cobre `is_on_ir` ou `active_salary`** (`grep` em `*_test.py`: zero ocorrências).
- **É do commit inicial.** `git log -S "not p.is_on_ir" -- models.py` devolve **só `f2271ba`**
  (*Fantasy Manager v1.0*) — nasceu com o projeto, nunca foi objeto de decisão posterior.
- ⚠️ **Mas já estava registrada — e a decisão ficou pendente.** A F1 do [[OFF26-1]] anotou o
  **GAP — IR e K/DEF** ([improvements.md:1860-1863](improvements.md#L1860-L1863)), que previu este
  achado com precisão: *"`Team.active_salary()` exclui `is_on_ir`, mas `draft_budget` conta o salário
  de IR. A barra de cap e o budget da janela **divergiriam** para times com IR. **Decisão
  pendente**."* A divergência **foi vista, anotada e enviada a produção**; o que faltou foi a
  decisão que agora existe.

#### T3 — Onde a réplica vive (a pergunta obrigatória)

**Sim, e a assimetria é o achado:**

| lado | fontes | avaliação |
|---|---|---|
| **INCLUI IR** (grupo B) | **1** — `draft_budget` | invariante [[F10]] **preservada**: 7 consumidores, nenhuma aritmética própria |
| **EXCLUI IR** (grupo A) | **6** — `active_salary` **+ 5 somas inline** | ⛔ **replicado**: `roster.py:89`, `league.py:22`, `league.py:99`, `admin.py:159`, `admin.py:160` reescrevem `sum(p.salary … if not p.is_on_ir)` à mão, **sem chamar `active_salary()`** |

**O lado que está errado é justamente o replicado** — corrigir a regra exige tocar **6 pontos**, não
1. Mesma família da réplica de `MAX_ROSTER` do [[OFF26-13]], porém pior: lá são duas definições da
mesma constante (inócuo), aqui são **cinco cópias de uma fórmula** que precisa mudar.

**Não há réplica em JS/Jinja** — nenhuma agregação de cap no cliente (`grep` por `reduce`/`sum` sobre
salário nos templates: só formatação de linha). A F10 segue valendo para os dois lados.

#### T4 — O "cabe até 24": **essa string não existe no código**

⛔ **`grep -rn "cabe"` em todo o `.py`/`.html`/`.js` devolve UMA ocorrência** — e é
[keeper_audit.py:211](keeper_audit.py#L211) (*"não cabem"*, ressalva do D2), **não a tela de roster**.

O que a tela de roster exibe é ([roster.html:98-102](templates/roster.html#L98-L102)):

> 🏥 **{{ ir_count }} jogador(es) no IR** — salary IR: ${{ ir_cap }}

**Não há limite dinâmico de 24 em lugar nenhum**, e portanto **não existe uma terceira definição de
teto de roster** — a resposta a T4 é que o `24` **não é calculado pelo Manager**. Confirmação
independente: o Manager **nunca lê `settings.reserve_slots`**; do payload de IR ele lê só
`roster.reserve`, a lista, em [sync_sleeper.py:239](sync_sleeper.py#L239). As definições de teto
existentes seguem sendo as duas do [[OFF26-13]] (`MAX_ROSTER = 22` em dois lugares, não enforçada;
`MAX_IR = 2`, enforçada).

#### T5 — Alcance, e a pergunta de severidade alta

**A keeper sheet e a auditoria do [[OFF26-4]] consomem o MESMO número, e ambas INCLUEM IR — elas NÃO
divergem entre si.** A auditoria não recalcula: `keeper_audit.build_sheet` importa
`routes.cuts._build_keeper_sheet` e repassa o `fa_budget` já pronto (D3/D4). **O achado de severidade
alta que o prompt antecipava não se materializou** — a cadeia do leilão é internamente coerente.

O que **de fato** consome a contagem sem IR é a cadeia de **leitura do owner** (A4/A5/A6/A7/A8) mais
o preview de **trade** (A11) e o preview de **rollover** (A9). Ou seja: **quem decide vê um número, e
o que vale no leilão é outro.**

**Dois achados laterais da mesma família:**
1. A keeper sheet **lista os jogadores de IR como keepers sem marcá-los** — `keeper_sheet.html` não
   tem badge de IR (`grep`: zero ocorrências de "IR" no template). Isso liga direto no [[OFF26-13]]:
   **os keepers em IR contam para as designações do board**, mas não estão sinalizados na folha que
   se usa para transcrever.
2. `Team.total_salary()` ([models.py:102](models.py#L102)) — o método "com IR" existe no modelo e
   **nunca é chamado**. Sinal de que a régua correta foi escrita e depois abandonada, gêmeo do
   `MAX_ROSTER` importado e não usado do [[OFF26-13]].

#### T6 — O que o regulamento diz (texto, sem interpretação)

Do `data/Regulamento - Dynasty - SB FANTASY FOOTBALL LEAGUE - 12-08-2025.pdf`, verbatim:

| item | texto |
|---|---|
| **1.1** | "12 Owners - Rosters de 22 jogadores;" |
| **1.3** | "2 IR (injuried reserves) – **não são considerados no total de 22**." |
| **5.1** | "Temos um CAP de $200 em salários (definidos nos itens a seguir) que deve ser respeitado a cada ano, **NO MOMENTO DO DRAFT**." |
| **5.2** | "Após o draft, os salários podem ultrapassar $200, mas a cada nova temporada, cada owner deverá voltar a adequar seu time dentro do cap de $200, considerando os keepers e os novos jogadores draftados." |
| **8.1.2** | "Cada owner pode manter **quantos jogadores quiser, respeitando o CAP de $200**." |
| **8.3.3** | "Budget para o draft de início de ano (auction): $200 MENOS o salário dos jogadores mantidos (calculados conforme regras dos contratos – item 6)." |
| **8.3.4** | "Cada owner deverá draftar o número de jogadores necessários para completar as 22 posições do roster. Para isso deverá ter PELO MENOS $1 disponível no CAP para cada jogador a ser draftado (22 – número de keepers)" |

**Leitura do texto, sem interpretar:**
- Sobre **contagem de roster**, o regulamento é **explícito**: o IR fica **fora** dos 22 (1.3).
- Sobre **salário de IR entrar no cap**, o regulamento é **SILENCIOSO**. Não há nenhuma frase
  excluindo IR da folha salarial. O item 1.3 fala de "**total de 22**" — uma contagem de jogadores —
  e não menciona salário; os itens de cap (5.1, 8.1.2, 8.3.3) falam de "salários" e "jogadores
  mantidos" **sem abrir exceção para IR**.
- A **única** exclusão explícita da folha salarial no regulamento inteiro é o **7.1.8** — "Os valores
  pagos pelos waivers não são considerados na folha salarial" — que trata de **FAAB**, não de IR.

⇒ **O texto não contradiz a decisão do owner** (IR conta no cap): ele é silencioso, e o silêncio não
é objeção. Mas também **não a confirma textualmente** — quem quiser oposição documental não a
encontra, e quem quiser respaldo documental também não. **Nada a resolver aqui; é registro.**

*(O 1.3 e o 8.3.4 continuam sendo a fonte do [[OFF26-12]], que é pergunta distinta: se keeper em IR
entra na **contagem** de `(22 − keepers)`. Este item é sobre **salário**, aquele é sobre **vaga**.)*

##### Refutação de premissas (MAN-METH-REG)

**(a) Premissas deste prompt contraditas pelo observado:**
1. ⛔ **"A tela de roster exibe *'2 jogador(es) no IR — cabe até 24'*."** A string **"cabe até 24"
   não existe no código**. O template diz *"2 jogador(es) no IR — salary IR: $9"*. **Consequência
   real:** não há terceiro teto de roster a reconciliar, e a T4 se resolve por **ausência**, não por
   origem. O `24` do enquadramento é do **regulamento** (1.1 + 1.3), não de nenhuma tela.
2. ⛔ **"Se a keeper sheet e a auditoria consumirem números diferentes, é achado de severidade
   alta."** Consomem **o mesmo** (`_build_keeper_sheet` é fonte única das duas). O achado alto está
   **noutro lugar**: não é sheet × auditoria, é **tela do owner × régua do leilão**.
3. ⚠️ **"Duas contagens convivem."** Correto — mas o prompt (e a F1 do [[OFF26-13]]) sugere **duas
   fontes**. São **1 fonte do lado que inclui IR e 6 do lado que exclui**: a réplica está toda no
   lado errado.

**(b) Comportamentos presentes que o prompt não previu:**
1. **A divergência já estava registrada desde a F1 do [[OFF26-1]]** ([improvements.md:1860](improvements.md#L1860)),
   com o texto *"divergiriam para times com IR — decisão pendente"*. Não é achado novo: é **decisão
   pendente que virou risco** quando a data chegou.
2. **`Team.total_salary()` é código morto** — a régua "com IR" existe no modelo e ninguém chama.
3. **Cinco somas inline** replicam o filtro de IR sem passar por `active_salary()` — o custo de
   corrigir é 6 pontos, não 1.
4. **A keeper sheet não marca quem está em IR**, e é a folha usada para transcrever o board.
5. **Zero cobertura de teste** sobre `active_salary`/`is_on_ir` — qualquer unificação vai ser feita
   sem rede.
6. **`reserve_slots` nunca é lido pelo Manager** (só `roster.reserve`) — o Manager não tem, hoje,
   nenhuma noção de "quantos slots de IR existem".

##### O que esta diagnose NÃO faz

Não altera contagem nenhuma, não unifica réplica, não toca `salary_engine`, tela, schema ou keeper
sheet, e **não muda o status de item nenhum**. A Fase 2 depende de uma decisão que **não é de
implementação**: se o alinhamento é **unificar as 6 superfícies do grupo A na régua com IR**, ou
**exibir os dois números lado a lado** (rotulados "folha total" × "cap ativo"), já que as duas
perguntas são legítimas — o que hoje falta não é o número, é o **rótulo**.

**Cross-refs:** [[OFF26-13]] (a réplica de `MAX_ROSTER` é a irmã desta; e os keepers em IR ocupam
designação no board), [[OFF26-12]] (a mesma ambiguidade do 1.3, mas sobre **vaga**, não salário),
[[OFF26-1]] (onde o GAP foi registrado e a decisão ficou pendente), [[OFF26-2]] (D5 — a sheet é o
lado que **inclui** IR), [[OFF26-4]] (consome a sheet, herda a régua com IR), [[F10]] (a invariante
que o grupo B respeita e o grupo A não).

#### Correção de premissa sobre o regulamento (04/08/2026)

**Leitura anterior (F1), preservada:** *"o regulamento é **SILENCIOSO** sobre se o salário de IR
entra no cap"* — e, sobre o `24`, *"a string 'cabe até 24' não existe no código; o 24 vem do
regulamento (1.1 + 1.3)"*.

**Correção do owner:** o **1.3 não é silencioso** — ele **estabelece** que os 2 IR **não são
considerados no total de 22**, logo **22 + 2 IR = 24 é composição legítima**, e o comportamento do
Manager **está correto**. ⇒ **Não há conflito entre Manager e regulamento.** O conflito real é entre
o **regulamento** (permite 24) e a **sala do leilão** (22 vagas, sem IR) — que é precisamente o
[[OFF26-13]], e não este item.

**Delimitação, para as duas leituras não se sobreporem de novo:** o 1.3 é **explícito sobre
CONTAGEM** (quantos jogadores) e **não fala de salário**; a ausência de regra sobre **salário de IR
na folha** permanece — é sobre ela que a decisão do owner (*o IR conta no cap*) se apoia, e é o que
a F1 chamou de silêncio. **A F1 media salário; a correção fala de contagem.** As duas valem, em
escopos distintos.

#### F2 (MAN-OFF26-14-F2, 04/08/2026) — rotular, não unificar

**Decisão registrada para não ser revisitada por engano.** Não se unificou porque: (1) a cadeia
crítica do leilão **já é coerente** — o risco que motivaria a unificação não existe; (2) unificar
custa **6 pontos**, **sem nenhum teste** cobrindo, em código do commit inicial, **a 17 dias do
leilão**; (3) os dois números **têm sentidos diferentes e ambos são legítimos**. **O que faltava não
era o número: era o rótulo.**

**Vocabulário único, aplicado em todas as superfícies:**

| rótulo | o que é | onde vale |
|---|---|---|
| **cap ativo** | exclui IR (`active_salary` e as 5 somas inline — **intocados**) | o que o time paga por quem joga |
| **folha total ⚖️** | inclui IR (`Team.total_salary()` / `cap_ativo + ir_cap`) | **é a régua do leilão** — `draft_budget`, keeper sheet, auditoria [[OFF26-4]] |

**Gate de exibição — sem IR, sem ruído:** toda superfície mostra o par **só quando o time tem
alguém em IR** (`ir_cap > 0` / `has_ir`). Hoje isso é **3 times**; os outros **9 seguem exibindo um
único número**, byte a byte como antes.

| # | superfície | o que mudou |
|---|---|---|
| A4 | chip da navbar ([base.html:73](templates/base.html#L73), [app.py:121](app.py#L121)) | valor e **limiar de cor inalterados**; com IR, ganha `$195 c/ IR` ao lado + `title` com os dois rótulos |
| A5 | banner M1 de cap estourado ([roster.py](routes/roster.py), [roster.html](templates/roster.html)) | `own_cap_overrun` **inalterado**; ganha o valor pela folha quando maior. **+ banner NOVO** para o par (ativo ≤ cap, folha > cap) — o caso em que o banner antigo silencia e o time entra no leilão estourado |
| A6 | página de roster ([roster.html](templates/roster.html)) | 2ª linha de rótulos sob a barra: `Cap ativo (sem IR)` × `Folha total (com IR)` + restante + *"⚖️ é a folha total que vale no leilão"*; o alerta de IR passa a nomear as duas |
| A7 | cards do League Hub ([league.html](templates/league.html)) | `Cap restante (ativo · c/ IR)` com os dois valores |
| A8 | `/team/<id>` ([team_detail.html](templates/team_detail.html)) | rótulo vira `Cap ativo` + item novo `Folha total ⚖️`; `Resto` ganha `($5 c/ IR)` |
| A9 | preview de rollover ([admin.py](routes/admin.py), [admin.html](templates/admin.html)) | os 2 agregados existentes viram `(ativo)`; **+2** `⚖️ Folha … (c/ IR)`, só se divergirem |
| A11 | preview de trade ([trades.py](routes/trades.py), [trades.html](templates/trades.html)) | `Cap` → `Cap ativo` quando há IR; **+ linha** `⚖️ Folha total (com IR — é a que vale no leilão): antes → depois (restante)`. Mesma aritmética de delta: **o contrato viaja com o jogador, esteja em IR ou não** |

**Prova de que nenhum valor calculado mudou:** `git diff` das rotas remove **5 linhas, todas
estruturais** — dois `return` de context processor (valores preservados, chaves acrescentadas), a
assinatura de `side()` e seus dois call sites. **Nenhuma linha de cálculo foi removida ou
alterada** — `active_salary`, as 5 somas inline e `draft_budget` estão byte a byte iguais.

**Números conferidos** (réplica read-only da aritmética das rotas, 04/08):

| time | cap ativo | folha total | restante (ativo → folha) | exibe par? |
|---|---|---|---|---|
| **🕯️🕯️ achane 🕯️🕯️** | **$186** | **$195** | $14 → $5 | ✅ **sim** |
| rafaelferreirap | $133 | $136 | $67 → $64 | ✅ sim |
| Fazenda Pederasta | $176 | $178 | $24 → $22 | ✅ sim |
| *(os outros 9)* | — | *idem* | — | ❌ **um número só** |

**`Team.total_salary()` deixou de ser código morto** — virou a fonte única da folha total onde há
objeto `Team` (chip, banner, trade). A alternativa (calcular `cap + ir` em paralelo nesses três
pontos) criaria **mais uma definição da mesma régua**, que é exatamente o vício que este item
documenta. Registrado como [[OFF26-17]].

⚠️ **PENDENTE DE SMOKE EM PRODUÇÃO — o item NÃO fecha ✅ com validação em localhost.** O que foi
validado aqui: **48/48** (`salary_engine`) + **34/34** (`keeper_audit`), `py_compile` das 6 rotas,
parse Jinja dos 8 templates, e a aritmética conferida contra o banco em `mode=ro`. **O que só prod
prova:** (1) o **par renderiza** nas 7 superfícies para um time com IR e (2) **não aparece** para os
9 sem IR; (3) o chip não quebra a navbar no mobile; (4) a linha nova do preview de trade não
desalinha as 2 colunas; (5) os 2 cards novos do rollover cabem no `stat-grid`. **Sugestão de caso
de smoke: abrir `/?team=🕯️🕯️ achane 🕯️🕯️` e conferir $186 e $195 lado a lado**, depois qualquer
time sem IR para conferir que nada mudou.

**Fora do escopo por decisão explícita (itens próprios):** marcação de IR na keeper sheet
([[OFF26-15]], **Alta**), unificação das 6 superfícies ([[OFF26-16]], **Baixa**, pós-leilão e com
testes), `total_salary()` ([[OFF26-17]], **Baixa**). **Nada da cadeia do leilão foi tocado**:
`draft_budget`, keeper sheet, auditoria [[OFF26-4]], `salary_engine`, schema e sync intactos.

---

---

### OFF26-16 — Régua única de folha: o IR conta no cap, sempre
✅ **Fechado em 04/08/2026 — smoke consolidado de produção PASSOU** — Prioridade **Alta** — `MAN-OFF26-16`

**Decisão do owner, explícita e final (04/08/2026):** *jogador no IR conta no cap hit como qualquer
outro.* Não existem duas réguas — existe **uma** folha salarial, que inclui todos os jogadores do
time (ativos e IR), e é a mesma em toda tela, todo cálculo e todo contexto.

#### Reversão da F2 do [[OFF26-14]] — com o racional preservado

Esta implementação **reverte** a F2 (`f809a68`), que rotulou as duas réguas em vez de unificá-las.
O registro do racional antigo fica **de propósito**: é precedente de correção com histórico.

| | F2 (03-04/08) | OFF26-16 (04/08) |
|---|---|---|
| **decisão** | rotular: "cap ativo" × "folha total ⚖️" | **unificar**: uma folha só |
| **racional** | *"os dois números têm sentidos diferentes e ambos são legítimos"* | ⛔ **caiu** — pela regra do owner, **o número sem IR não mede nada** |
| **custo alegado** | 6 pontos, sem teste, a 17 dias do leilão | **pré-requisito cumprido**: cobertura escrita primeiro |

**O que não muda na leitura histórica:** o filtro `not p.is_on_ir` **nunca foi decisão de ninguém** —
a F1 do [[OFF26-1]] registrou *"decisão pendente"*, a pendência foi para produção no commit inicial,
e a F2 deu **rótulo e banner ao acidente**. A decisão foi tomada agora, e é no sentido oposto.

**O que a F2 deixou de útil:** ter concentrado os consumidores em `Team.total_salary()` ([[OFF26-17]])
**barateou** esta unificação — parte do caminho já estava feita.

#### 1. Cobertura primeiro (pré-requisito duro, cumprido)

`cap_regua_test.py` — **14 testes**, escritos e rodados **antes** de tocar em qualquer soma.
Rodados contra o código antigo, falharam exatamente onde deviam: `186 != 195`, `14 != 5`, e a guarda
apontando `models.py`, `routes/league.py`, `routes/admin.py`.

| classe | o que fixa |
|---|---|
| `TestRosterSalary` | o núcleo puro: IR conta, dropado não, IR sozinho, roster vazio, time sem IR inalterado |
| `TestTeamSalaryORM` | `Team.total_salary()`/`cap_remaining()`/`to_dict()` contra **SQLite em memória** (não toca o `dynasty.db`) — caso achane: $195 e **$5** |
| `TestLeagueCard` | `_build_team_card` devolve `cap_used` **195** e `cap_space` **5**, sem as chaves da régua dupla |
| `TestSemReplicaDeFolha` | ⛔ **guarda anti-réplica**: falha se qualquer `sum` de salário voltar a filtrar `is_on_ir`, ou se `active_salary` ressuscitar em qualquer arquivo |

A guarda existe porque a F1 mediu **seis** definições da mesma régua: o problema deste código nunca
foi escrever a soma errada uma vez, foi **reescrevê-la à mão em cada rota**.

#### 2. As 6 fontes viraram 1

**Fonte única:** `salary_engine.roster_salary(players)` — pura, sem DB, `is_dropped` é o único
filtro. **Entrada ORM:** `Team.total_salary()` delega a ela; `cap_remaining()` deriva.

| antes (6 definições) | depois |
|---|---|
| `Team.active_salary()` | ⛔ **removido** — o nome mentia |
| `roster.py:89` soma inline | `roster_salary(all_players)` |
| `league.py:22` soma inline | `roster_salary(players)` |
| `league.py:99` soma inline | `roster_salary(players)` |
| `admin.py:159` soma inline | `roster_salary(players)` |
| `admin.py:160` soma inline (com **N+1**: um `Player.query.get` por linha) | `sum(new_salary)` — o filtro sai **e o N+1 junto** |

**+2 correções de coerência que a unificação expôs:**
- `team_detail.cap_by_pos` somava só os não-IR — **não fechava com o `cap_used` exibido na mesma
  tela**. Agora percorre todos.
- Chave da API `to_dict()`: `active_salary` → **`salary_total`** (consumidor: `trades.html`).
  `sync_sleeper._compute_cap_alerts` idem.

#### 3-5. O rótulo duplo saiu; um número só

As **7 superfícies** voltaram a exibir **um valor** — a folha com IR. Saíram: o par rotulado, o
banner aditivo do par (ativo ≤ cap, folha > cap), a legenda *"⚖️ é a folha total que vale no
leilão"*, as 3 classes CSS da F2, `g_user_team_folha`, e as chaves `folha_*`/`has_ir`/`ir_cap` dos
payloads. Chip, barra de progresso e "Restante" operam sobre a folha única.

**O banner de IR virou informativo de escalação** — *"🏥 2 jogador(es) no IR: Michael Penix, Travis
Hunter."* Sem aritmética paralela; em `/team/<id>` o item IR mostra só a contagem, com os nomes no
`title`.

#### Números conferidos contra o banco (`mode=ro`)

| time | antes | **agora** | restante | barra |
|---|---|---|---|---|
| **🕯️🕯️ achane 🕯️🕯️** | $186 | **$195** | **$5** | 97,5% |
| rafaelferreirap | $133 | **$136** | $64 | 68,0% |
| Fazenda Pederasta | $176 | **$178** | $22 | 89,0% |
| *(os 9 sem IR)* | — | **idênticos** | — | — |

**Suítes:** `cap_regua_test` **14/14** · `salary_engine_test` **54/54** · `keeper_audit_test`
**34/34**. Imports das 6 rotas + `sync_sleeper` OK; parse Jinja dos 9 templates OK.

#### Fora de escopo — deliberado, e por que

- **`dynasty_total` segue excluindo IR** (`league.py`) — é **valor de ativo**, não folha salarial.
  A decisão do owner é sobre **cap**; mexer aqui seria estender a decisão sem mandato.
- **`renewal_candidates`** (`roster.py`) segue derivando de `active_players` ⇒ **um jogador em IR no
  Ano 4 não aparece como candidato a renovação**. É pergunta de contrato, não de folha — **registrar
  como observação**, não corrigido aqui.
- **[[OFF26-15]]** (keeper sheet não marca IR) **não** entra aqui, como o prompt determinou.
- **`draft_budget`** intocado — fórmula fechada e confirmada por medição ([[OFF26-18]]).
- Keeper sheet, auditoria [[OFF26-4]], schema e sync (fora do rename de chave) intocados.

⚠️ **PENDENTE DE SMOKE EM PRODUÇÃO.** Só prod prova: (1) achane exibindo **$195 / $5** com a barra
em 97,5% e o banner listando os dois nomes; (2) os 9 times sem IR com tela **idêntica**; (3) o
`/team/<id>` sem o custo de IR duplicado; (4) o preview de trade e o card do League Hub sem resíduo
de layout das linhas removidas; (5) `/api/teams` servindo `salary_total` para o seletor de times do
`/trades` (chave renomeada — se algo externo consumia `active_salary`, quebra aqui).

**Cross-refs:** [[OFF26-14]] (a F1 que mediu as 6 fontes; a F2 revertida), [[OFF26-17]]
(`total_salary` — de código morto a régua oficial), [[OFF26-1]] (onde o gap foi registrado como
"decisão pendente"), [[OFF26-18]] (`draft_budget` — ortogonal), [[F10]] (a invariante de fonte
única, agora valendo dos dois lados).

---

---

### OFF26-17 — `Team.total_salary()` era código morto
✅ **Fechado em 04/08/2026 — smoke consolidado de produção PASSOU** (resolvido por consumo; hoje é a única entrada ORM de salário) — Prioridade **Baixa**

**O achado (F1):** `Team.total_salary()` ([models.py:102](models.py#L102)) — a régua **folha total**,
semanticamente correta — estava definida no modelo com **zero consumidores**. Sinal de que a régua
certa foi escrita e depois abandonada; gêmeo do `MAX_ROSTER` importado e nunca usado do [[OFF26-13]].

**⚠️ O que a F2 fez, e por que difere do "registrar e parar":** o item foi registrado como manda o
prompt, **mas a F2 o consumiu** em vez de deixá-lo morto — ele é a fonte única da folha total nos
três pontos onde há objeto `Team` (chip da navbar, banner do roster, preview de trade). **A
alternativa seria calcular `cap_ativo + ir_cap` em paralelo nesses pontos, criando uma segunda
definição da mesma régua** — exatamente o vício que o [[OFF26-14]] documenta e que o [[OFF26-16]]
vai ter de desfazer do outro lado. **Resíduo resolvido por consumo, não por remoção**; nada foi
apagado, como o prompt exigia.

**Decisão do owner, se discordar:** reverter é trocar as 3 chamadas por `cap + ir` local — mas isso
recria a réplica. Registrado assim para que a escolha fique visível.

---

---

### OFF26-18 — Fencepost na reserva de $1 do `draft_budget`
✅ **Fechado em 04/08/2026 — smoke consolidado de produção PASSOU** (`min $3` em 4 spots / `min $0` em 1 spot — fencepost vivo na tela) — Prioridade **Alta** — `MAN-OFF26-18`

**O erro.** A reserva de `$1 × vagas` protegia **também a vaga que o próprio lance está
preenchendo**. Com **1 spot vazio**, o Manager reservava $1 para uma vaga "seguinte" que não existe
— tornando **o último dólar impossível de gastar**. Achado pelo owner simulando no Cap Projector com
o time reduzido a 1 spot.

**A correção** ([salary_engine.py:221](salary_engine.py#L221)):

```python
min_required = max(0, empty_spots - 1) * MIN_SALARY   # antes: empty_spots * MIN_SALARY
```

O `max(0, …)` **não é defensivo, é obrigatório**: com **0 vagas** a subtração daria reserva **−1**,
**inflando** o budget em $1 num time completo — trocaria um erro por outro, de sinal contrário.

**A referência não é interpretação — é comportamento medido.** Experimento na plataforma
(02/08/2026): `teto = 200 − gasto − (vagas_restantes − 1)`. O `−1` é a vaga que o lance preenche.

**Distinção de leitura da 8.3.4 (registrada para não ser revisitada).** O texto — *"pelo menos $1
disponível no CAP para cada jogador a ser draftado (22 − keepers)"* — **ao pé da letra sustenta a
fórmula antiga**. Mas essa leitura reserva $1 **para um jogador que já está sendo comprado**, e o
efeito é deixar $1 do cap permanentemente inacessível. Vale a **leitura operacional** — a mesma que
a plataforma implementa. **Não é o regulamento que muda; é qual das duas leituras dele o Manager
aplica.**

**Fonte única fez o trabalho:** os **7 consumidores** herdaram a correção sem uma linha de mudança
(Cap Projector GET e POST, janela de cortes, keeper sheet `fa_budget`, auditoria [[OFF26-4]],
importador OFF26-3). `grep` confirma que **nenhuma aritmética foi replicada** — `cap_projector.html`
e `cuts.html` só **exibem** `empty_spots`/`min_required_for_spots` vindos do payload. [[F10]]
preservada.

**Efeito medido no banco (04/08, `mode=ro`) — +$1 exatamente onde deveria:**

| vagas | times | usável antes → depois |
|---|---|---|
| **0 vagas** | Pitbull, 3 peat, Fazenda, mongoloides, Miller Time, achane | **sem alteração** ($0 de mudança — o `max(0,…)` fazendo o seu trabalho) |
| **≥1 vaga** | Cangaceiros, AlexTheDawg, Trust The Process, Tropa, rafaelferreirap, ESPN FANTASY | **+$1 cada** |

**Casos da validação, conferidos com salários reais por jogador:**

| caso | time | resultado |
|---|---|---|
| 1 vaga → restante inteiro | Trust The Process | vagas 1, reserva **$0**, usável **$76** (= 200 − 124) ✅ |
| 0 vagas, exatamente no cap | Miller Time! | vagas 0, reserva **$0**, usável **$0** — nem −$1 nem $1 ✅ |
| n vagas → reserva n−1 | Cangaceiros da Colina | vagas 4, reserva **$3** ✅ |

**Testes:** suíte do `salary_engine` **54/54** (era 48 — **+6 casos de borda** na classe nova
`TestDraftBudgetFencepost`: 0 vagas, roster cheio exatamente no cap, 1 vaga, 2 vagas, o experimento
do Sleeper e roster estourado >22). Os dois testes que codificavam a fórmula antiga
(`test_usable_budget_accounts_for_spots`, `test_empty_roster`) foram atualizados para o valor novo.
Auditoria **34/34** intacta.

##### ⚠️ Conferência aritmética do caso de referência (divergência com o prompt)

O prompt do OFF26-18 registra o experimento como *"$150 gastos, 21 vagas → teto **$29** (não $28,
que é o que a fórmula atual do Manager daria)"*. **As duas contas não fecham:**

| fórmula | conta | resultado |
|---|---|---|
| antiga (Manager, antes) | 200 − 150 − 21 | **$29** |
| corrigida (= a do Sleeper, `vagas − 1`) | 200 − 150 − 20 | **$30** |

⇒ **o $29 do prompt é o que a fórmula ANTIGA produz**, não o alvo da correção; e o "$28" não é
produzido por nenhuma das duas. O teste registra **$30**, que é o que a fórmula pedida na TAREFA dá.

**Isso NÃO invalida a correção** — apenas o poder probatório *daquele* caso: os lances medidos
($29 aceito; $32/$33/$40 recusados) limitam o teto real ao intervalo **[29, 31]**, que contém tanto
o $29 da fórmula antiga quanto o $30 da nova — **$30 e $31 nunca foram testados**. Quem decide é o
**caso de 1 vaga**, que é dedutivo e não depende de medição: com uma única vaga não há vaga seguinte
a proteger, e reservar $1 ali é reservar contra o próprio lance.

✅ **PENDÊNCIA PROBATÓRIA FECHADA em 04/08/2026** — o teste decisivo foi executado. Ver a seção
seguinte; **a sustentação deixou de ser dedutiva e passou a ser medição direta nos dois sentidos**.

##### ✅ Confirmação empírica da fórmula (MAN-OFF26-18-CONF, 04/08/2026)

**O teste decisivo foi executado pelo owner na liga fantasma real**, e distingue as duas fórmulas —
que é exatamente o que o experimento de 02/08 **não** fazia.

**Cenário:** Team 5 do board da fantasma — **$60 gastos, 16 vagas livres**.

| fórmula | conta | teto previsto |
|---|---|---|
| antiga (`vagas`) | 200 − 60 − 16 | $124 |
| **corrigida (`vagas − 1`)** | 200 − 60 − 15 | **$125** |

**Resultado: designação de $125 ACEITA** (J. Gibbs, removida em seguida — o board voltou às 24
designações). Os $125 estão **acima do teto da fórmula antiga** e **exatamente no teto da
corrigida** ⇒ **a fórmula rival fica eliminada**, não apenas "não contradita".

**Conferência independente do cenário (leitura read-only do board, 04/08):** liga
`Dynasty SB FA Auction`, `draft_status = pre_draft`, **rodadas 22**, **24 designações** — coluna 5
com **6 designações somando $60**. Logo `22 − 6 = 16 vagas`: **o cenário declarado no teste confere
com o board ao vivo**, e Gibbs **não está mais** entre as designações (board restaurado).

**Estado probatório final de `teto = 200 − gasto − (vagas − 1)`:**

| evidência | data | o que estabelece |
|---|---|---|
| recusa em limiar+3 / +4 / +11 ($32/$33/$40 num teto de $29) | 02/08 | **existe** um teto, e ele é baixo — mas [29, 31] não discrimina as fórmulas |
| **aceite no limiar exato** ($125 num teto previsto de $125) | **04/08** | a fórmula corrigida **acerta o limiar** |
| **aceite acima do teto da fórmula rival** ($125 > $124) | **04/08** | a fórmula antiga é **falsificada** |

⇒ A fórmula do Manager (`max(0, empty_spots − 1) * MIN_SALARY`, commit `4bef82a`) está **alinhada à
plataforma por medição direta nos dois sentidos** — recusa acima do teto e aceite no teto —, não
mais por dedução. O teste `TestDraftBudgetFencepost.test_experimento_sleeper_150_gastos_21_vagas`,
que assere **$30** no cenário de 02/08, **passa a ter lastro empírico**.

**Nota de método (por que a distinção valeu a pena).** O relatório da implementação identificou que
o caso de referência do prompt **não provava o que afirmava provar** — e separou *correção
implementada* de *poder probatório do caso*. Sem essa separação, o item teria sido registrado como
**confirmado** quando ainda era **intervalo**, e a fórmula rival seguiria viva num item marcado
✅. **O teste decisivo custou um lance** — e foi barato justamente porque a pergunta estava
formulada com precisão: não "a fórmula está certa?", mas "**qual lance separa as duas?**".

**Fica fora deste fechamento** (é outra pergunta, não probatória): o **smoke de produção** das telas
que exibem o valor novo, que segue pendente.

⚠️ **PENDENTE DE SMOKE EM PRODUÇÃO.** Validado aqui: 54/54, 34/34, e os três casos conferidos contra
o banco. **O que só prod prova:** o Cap Projector e a barra da janela de cortes exibindo o valor
novo (o `min $N` ao lado de `spots` deve cair em 1), e o alerta de `insufficient_budget` não
disparando indevidamente para time com vaga.

**Cross-refs:** [[OFF26-4]] (o D2 ressalvava divergência de **contagem de slots**; esta é de
**fórmula**, categoria diferente), [[OFF26-12]] (a outra pergunta aberta sobre a 8.3.4 — se keeper
em IR entra em "keepers"; **ortogonal a esta**, que é sobre o `−1`), [[OFF26-14]] (as réguas cap
ativo × folha total — **intocadas**, a correção é ortogonal), [[F10]] (a fonte única que fez os 7
consumidores herdarem sem réplica).

---

---

### IR-CLEANUP — Remover Seletor Manual de IR no Roster
✅ **Fechado em 04/08/2026 — smoke consolidado de produção PASSOU** (inclusive o **sync manual mantendo os 5 em IR**) — Prioridade **Baixa** — `MAN-IR-CLEANUP`

#### Execução (04/08/2026) — decisão do owner: remover

**O argumento ficou mais forte do que na diagnose.** O registro original (MAN-IR-F1) tratava o
toggle como **ruído inócuo**: controle sem efeito persistente, revertido em silêncio pelo sync. Com
a **régua única** do [[OFF26-16]] — em que **o IR conta no cap** — um toggle que aparenta mudar o
status de IR passou a aparentar mudar **a folha salarial do time**, sem mudar nada. **Deixou de ser
ruído e virou controle ativamente enganoso.**

**Removido:**

| o quê | onde |
|---|---|
| endpoint `POST /api/player/<id>/ir` (`toggle_ir`) | [routes/roster.py](routes/roster.py) — substituído por comentário explicando a autoridade do Sleeper |
| handler `toggleIR(playerId, toIR)` | [templates/roster.html](templates/roster.html) |
| os 2 botões (`↑ Tirar IR` / `IR`) | [templates/_macros.html](templates/_macros.html) |
| **a coluna `col-actions` inteira** | macro `player_roster_row` + `player_roster_colgroup` + `<th>` do roster — existia **só** para o toggle |
| CSS morto: `.btn-ir-remove`, `col.col-actions`, `.col-actions` | [static/style.css](static/style.css) |
| import agora órfão de `MAX_IR` | [routes/roster.py](routes/roster.py) |

**Efeito colateral bom:** `/` e `/team/<id>` passaram a ter **exatamente a mesma forma de tabela** —
era o `context='roster'` que injetava a coluna a mais.

**Preservado, como o item exigia:** o campo `Player.is_on_ir` (o sync segue escrevendo), o badge
**🏥 IR** na linha do jogador, a constante `MAX_IR` e **toda** a lógica de cap — que hoje é a régua
única do [[OFF26-16]]. O **banner informativo de escalação** (*"🏥 2 jogador(es) no IR: Michael
Penix, Travis Hunter."*) **permanece**: é leitura, não controle.

`MAX_IR` ficou **sem referência em código** (era validado só dentro do toggle). Preservado de
propósito e com comentário no [models.py](models.py) dizendo por quê — documenta a regra da liga
(item 1.3) e é a âncora se algum dia houver validação local. **Não é resíduo a limpar.**

**Caveat de UX do registro original — DESCARTADO, com o motivo.** A alternativa conservadora era
manter o seletor com tooltip *"Será sobrescrito no próximo sync"*, preservando override para
ambiente sem Sleeper. **O owner decidiu remover:** o custo permanente de um controle enganoso —
agora sobre a folha salarial, a 16 dias do leilão — é maior que a hipótese de operar offline. E
**mudar IR se faz no Sleeper**, que é onde a autoridade sempre esteve.

**Validação:** os **5 jogadores em IR seguem em IR** (Kendre Miller, Tory Horton, Michael Penix,
Travis Hunter, Zach Charbonnet), badge e banner intactos, e os **12 valores de cap idênticos** aos
do [[OFF26-16]]. `grep` não encontra o endpoint, o handler nem o controle. `toggle_ir` não existe
mais no blueprint. Suítes: **14/14** + **54/54** + **34/34**.

⚠️ **Pendente de smoke em prod:** (1) a tabela do roster sem a coluna de ações — conferir que o
`colgroup` não desalinhou as larguras; (2) o badge 🏥 e o banner de escalação renderizando; (3) um
**sync manual** mantendo os 5 em IR (é a prova de que a autoridade do Sleeper segue funcionando sem
o toggle).

---

#### Registro original (MAN-IR-F1) — a diagnose que motivou o item

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

**Caveat de UX:** se quiser preservar capacidade de override em ambiente sem Sleeper (offline ou API fora), avaliar alternativa conservadora — manter o seletor mas adicionar tooltip "Será sobrescrito no próximo sync". Recomendação default é remover (regra do projeto: ações na UI devem ser efetivas ou marcadas claramente como simulação). — **⛔ DESCARTADO na execução; ver acima.**

*(Nota de leitura: a seção "O que preservar" acima cita `Team.total_active_salary` e "lógica de cap
que exclui IR". Essa descrição é **anterior ao [[OFF26-16]]** e não vale mais — o IR passou a contar
no cap, e a régua é única. O que o IR-CLEANUP preservou foi a **lógica de cap vigente**, seja ela
qual for; a remoção do toggle é ortogonal a qual régua o cap usa.)*

---
### OFF26-1 — Janela de cortes selada
✅ **CONCLUÍDO (07/08/2026)** — mecanismo selado provado em produção **três vezes** e porta legada
aposentada e verificada — Prioridade **Alta**

> #### Status final declarado (MAN-OFF26-10-SMOKE, 07/08/2026)
>
> **O que fechou o ⚠️ que restava.** Em 06/08 o item era ⚠️ por **uma** razão declarada: o código
> da aposentadoria da porta (MAN-OFF26-1-ETAPA2) não tinha rodado em produção. Ele rodou — está
> no ar desde aquele deploy, e o **smoke da urna (07/08) atravessou a mesma instalação**,
> incluindo a conferência de que `/cuts` não oferece mais roster, checkbox nem botão de declarar.
> **Não sobra nada em aberto neste item.**
>
> **A prova do mecanismo é tripla, e a terceira é a mais forte:** Etapa 1 (localhost, 10/10) ·
> Etapa 2 (produção, 12 declarações, hash `52274d01…`, reset limpo) · **o smoke da urna**, que
> exercita **o mesmo motor** (lock · hash · revelação · snapshot · reset · hierarquia) num
> segundo consumidor, com outra tela e outra tabela. Um mecanismo que serve a dois donos e
> sobrevive aos dois é mecanismo, não coincidência.
>
> **O que sobra vivo deste item, e é de propósito:** as rotas de declaração legadas (`/api/cuts/*`)
> seguem no código como **motor reusado** e **rede de regressão** (7 testes de hierarquia + 22 da
> suíte da janela). O **bloco admin de `/cuts`**, por outro lado, perdeu a última função que o
> justificava — ele era o **produtor de fallback da keeper sheet**, e o U7 tirou isso dele. Virou
> item próprio: [[OFF26-21]] (🔲 Baixa) — **não é dívida deste item nem motivo de ⚠️**.

> #### ETAPA 2 (MAN-OFF26-1-ETAPA2, 06–07/08/2026) — ensaio APROVADO em produção; a porta de declaração foi APOSENTADA
>
> **Etapa 2 executada em produção em 06/08 pelo owner e pelo co-admin — que foi o RAFA, não o
> Michel** (o runbook nomeava o Michel; corrigido lá). **Ciclo completo passou:** banner de
> ensaio ON, janela aberta, **declarações reais de contas distintas** (o Rafa usou o caminho
> novo do **manter-todos** — team 1 com `num_cuts=0` na trilha), **sigilo cruzado conferido**,
> **hierarquia owner > admin exercitada com sucesso** (o suprimento admin sobre time que
> declarou pessoalmente foi **recusado**, com a mensagem expondo só existência + autoria —
> desenho **confirmado em campo** pelo owner), **lock + revelação**, **hash canônico
> `52274d01…`**, keeper sheet gerada, e **reset verificado**: **12 declarações e 1 snapshot
> apagados → 0/0/fechada/banner off → janela reabrindo em seguida**. Backup
> `/data/pre_ensaio_off26_1.db` (**618.496 bytes**) conferido antes de tudo.
>
> ⇒ **A pré-condição 1 da spec da urna está CUMPRIDA:** lock, hash e reveal **rodaram em
> produção**, com 12 declarações e trilha íntegra. O que era ⚠️ por "nunca rodaram em prod"
> **está resolvido**.
>
> **Achado de UI 1 — o `confirm()` nativo falha no celular (BLOQUEANTE de fluxo, não cosmético).**
> No desktop funciona; **no mobile o pop-up impediu a declaração do Rafa** (ele precisou ir ao
> computador). Como **em 22/08 a maioria declara pelo celular**, o padrão de confirmação passa a
> ser **inline** (o botão vira "confirmar?" e só executa no 2º clique): **obrigatório na urna**
> ([[OFF26-10]], U-CONF), e já aplicado ao único `confirm()` que sobreviveu nesta tela (o
> `adminLock`) como padrão a copiar — `confirmarInline()` em `templates/cuts.html`.
>
> **Achado de UI 2 — a recusa da hierarquia apareceu como desenhada** (existência + autoria, sem
> conteúdo) e **o owner validou o comportamento em campo**. Nada a corrigir; o desenho da recusa
> seca deixa de ser hipótese testada em localhost e passa a ser **comportamento confirmado**.
>
> **APOSENTADORIA DA PORTA (consequência do redesenho de arquitetura — ver [[OFF26-10]]):** os
> cortes de 20/08 passam a acontecer **direto no Sleeper**, e o Manager entra **só em 22/08**
> como a urna. A tela de declaração múltipla **sai do caminho**: `/cuts` não renderiza mais
> roster, checkbox de corte nem botão de declarar; sobra a explicação do fluxo de 2026 e, para
> admin, o **motor rotulado como legado** (abrir/fechar/lock/revelação/suprir), com aviso
> explícito de que abri-lo em 20–22/08 criaria uma **segunda porta**.
> **As ROTAS de declaração seguem vivas de propósito** — são o mecanismo que a urna reusa
> (U5/U8) e a **rede de regressão** da hierarquia owner > admin (7 testes). Sem janela aberta,
> `POST /api/cuts/declaration` já recusa com **409**: a porta única é **estrutural**, desde que
> a urna **não reuse a flag `cuts_window_open`** (restrição registrada na spec da F2).
> **Reversível por git** se uma temporada futura voltar a querer a janela grande.
>
> **Validação:** `janela_ensaio_test.py` **22/22 verde** (nenhuma rota tocada — só a camada de
> tela); `cap_regua_test` 34, `keeper_audit_test` 34, `salary_engine_test` 54 verdes; `/cuts`
> renderiza **200** como admin sem resquício de `saveDeclaration`/`declareKeepAll`/`recalc`.

> #### POSENSAIO (MAN-OFF26-1-POSENSAIO, 06/08/2026) — Etapa 1 executada 10/10; dois achados, implementados
>
> **Etapa 1 (localhost) executada pelo owner em 06/08 — checklist 10/10:** gate D3 exercitado
> de verdade (3 needs_review bloquearam; fila zerada em /admin/review liberou), declaração,
> substituição, lock, hash conferido (`5024b17a…`, match), revelação, keeper sheet com CSV,
> trilha com 1 snapshot CANÔNICO, e o reset devolvendo 0/0/fechada com a janela reabrindo.
> **Etapa 2 (produção, com o co-admin) segue autorizada e pendente.**
>
> **(A) Bug corrigido — `--db` relativo abria o banco errado e falhava em silêncio:** o
> `exists()` checava contra o cwd, mas a URI do SQLAlchemy resolvia contra OUTRO diretório —
> e o SQLite criava lá um banco VAZIO ("no such table" mascarava a causa). Agora `--db` e
> `--backup` resolvem para **absoluto (contra o cwd de quem invocou) antes de qualquer
> conexão**, e arquivo inexistente é **recusado** com mensagem clara (criar banco novo nunca
> é intenção de quem passa `--db`). Runbook atualizado.
>
> **(B) Manter-todos explícito + hierarquia owner > admin (decisão de desenho do owner):**
> - Tela da janela ganhou **"✋ Não vou cortar ninguém (manter todos)"** — declaração ativa
>   (autor + timestamp), distinta do silêncio; conta no "N/12". O default silencioso (D2)
>   **continua existindo** para quem sumir.
> - Keeper sheet ganhou o **3º status**: `owner_kept_all` → **"Declarou (manteve todos)"**,
>   distinto de "Declarou" e de "Default (manteve todos)". ("Admin supriu" inalterado.)
> - **Hierarquia no suprimento (desenho escolhido: RECUSA SECA):** `/api/cuts/admin/declare`
>   sobre time que **já declarou pessoalmente** (cortes ou manter-todos) devolve **409**
>   "este time já declarou pessoalmente" — expõe só existência+autoria, **nunca conteúdo**
>   (D6). Time silencioso ou suprido por admin: funciona como antes; e o owner **sempre**
>   pode sobrescrever o suprimento do admin (o outro sentido da hierarquia).
> - **Propagado à spec da urna** ([[OFF26-10]]): a urna herda a mesma hierarquia.
>
> **Validação:** suíte da janela **22 testes** (10 do ensaio + 5 do fix A + 7 da hierarquia B,
> incl. não-vazamento na recusa); dry-run re-executado **51/51 PASS** (41 originais + --db
> relativo/inexistente + manter-todos + hierarquia + 3º status na sheet). Mecanismo selado
> (lock/hash/reveal/snapshot) **intocado**. Nota de teste: request de test_client reusa app
> context externo se houver um empurrado, e o flask_login cacheia o usuário em `g` — os
> testes de rota NÃO mantêm contexto persistente (armadilha registrada no próprio teste).

> #### ENSAIO (MAN-OFF26-1-ENSAIO, 06/08/2026) — preparado; execução é do owner
>
> Pré-condição 1 da spec da urna ([[OFF26-10]]): lock/hash/reveal nunca rodaram em prod.
> Roteiro completo em **`runbook_ensaio_janela_selada.md`** (Etapa 1 localhost → Etapa 2
> produção com Michel, backup + aviso no grupo + reset verificado).
>
> - **ACHADO BLOQUEANTE da Etapa 0, resolvido:** não existia caminho de desfazer — e o estado
>   "travada" É a existência do snapshot canônico, então um ensaio sem reset **bloquearia a
>   abertura da janela real de 20/08** (o `/open` recusa com 409). Construído
>   **`ensaio_janela_selada.py`** (molde do runner do OFF26-20-FIX): `--status` (conferência
>   read-only, sem expor conteúdo de declaração — D6 vale até para o operador), `--banner
>   on|off`, `--reset --backup <path>` (gate duro: sem backup conferido, nenhuma escrita;
>   escopo por season; verificação pós-reset 0/0/fechada). **Comportamento declarado: o reset
>   apaga a trilha do ensaio de propósito** — a evidência fica no backup, não no banco vivo.
> - **Rótulo de ensaio incluído (custo baixo):** AppConfig `cuts_ensaio_banner` → banner
>   "🧪 ENSAIO — NÃO DECLARAR" em `/cuts` e `/cuts/keeper_sheet`. Mitiga o risco operacional
>   real (owner declarar achando que vale) junto com o aviso no grupo.
> - **Dry-run do Code (06/08, cópia do seed, app real + test_client): 41/41 checks PASS** —
>   ciclo completo com 3 contas (admin, co-admin, owner comum): gate D3 exercido de verdade
>   (409 com needs_review pendente), sigilo pré-reveal (inclusive `?team_id=` ignorado),
>   substituição, lock trava tudo, hash verify, reveal simultâneo dos 12, keeper sheet
>   (cortado fora + CSV), trilha, **reset devolve estado pré-ensaio e a janela REABRE**.
> - Testes permanentes: `janela_ensaio_test.py` (10 — núcleo do reset, propriedade crítica
>   pós-reset, escopo por season, atomicidade, banner nas duas telas).
> - Mudança de código declarada (escopo Etapa 0): `ensaio_janela_selada.py` (novo),
>   flag `ensaio_banner` nas 2 rotas de página de `routes/cuts.py`, banner nos 2 templates.
>   **Mecanismo da janela intocado** (nenhuma rota de lock/reveal/declaração alterada).

**Descrição:** cada owner autenticado vê **apenas o próprio roster** e declara
keepers/cuts no Manager, com budget resultante (`$200 − keepers`) calculado ao vivo
e validação do regulamento (mínimo $1 por slot vazio, item 8.3.4). Declarações
editáveis até o deadline; **sigilo total pré-deadline, inclusive para admins** (que
também são owners); **lock + revelação simultânea** no deadline.

**Motivação:** hoje os cortes acontecem sequencialmente e em público no Sleeper,
vazando informação entre owners (quem corta por último vê o que já foi liberado). A
janela selada elimina o vazamento.

**Escopo resumido:** declaração privada por owner + cálculo de budget ao vivo +
validação 8.3.4 + deadline com lock e revelação simultânea + trilha auditável no
padrão do M8 (lottery audit). Sigilo aplicado mesmo a admins.

**Dependências:** é a **fonte** dos itens OFF26-2 e OFF26-4. **Pré-condição de ABERTURA
(trava de código — confirmada pela F1 do [[OFF26-9]]):** apenas **`needs_review` zerado**
(`admin_open_window` não checa E4-a nem rollover). **Recomendações de QUALIDADE DE DADO (não
travam abertura):** rodar o **Season Rollover (passo 4)** antes — para o budget não-projetado
(D9) exibir salário **já valorizado** —; e ter o **E4-a (ESPN definitiva)** para a **exatidão
dos valores** (e o salário de rookie no draft, evento posterior). Ver D8 + esclarecimento
MAN-OFF26-9.

#### Spec final — decisões de produto arbitradas (MAN-OFF26-1-REFINE, 16/06/2026)

Decisões do owner pós-F1. **Esta spec é a verdade do item e SUPERA o enquadramento
preliminar** de "keepers" da Descrição/Escopo acima (que falavam em declarar *keepers*;
a unidade real é a **lista de cortes** — ver D1). A F2 lê esta camada. O que a F1
mapeou (terreno/portas/gaps) continua válido abaixo; aqui ficam as **decisões**.

- **D1 — Unidade = lista de CORTES (`cut_ids`), não keepers.** Keepers são o **complemento**
  (roster atual − cortes). UI, snapshot, keeper sheet e todos os consumidores falam a língua
  do **corte**. (Resolve o "keepers vs cuts" que a F1 deixou em aberto.)

- **D2 — Default de quem não declara: zero cortes = mantém todos.** Coerente com o
  regulamento 5.2. O cap pode estourar pós-rollover; a **adequação é resolvida depois pelo
  admin** (e a trava de cap mora na fronteira do FA auction, não aqui — ver D9).

- **D3 — Pré-condição de ABERTURA: fila `needs_review` ZERADA é BLOQUEIO DURO.** O admin
  **não pode abrir** o prazo de cortes enquanto houver qualquer jogador em `needs_review`
  em qualquer roster. Previne propagar salário não-confiável para o snapshot selado e toda
  a cadeia a jusante. É **gate na abertura**, não validação por-jogador na declaração.

- **D4 — Lock + revelação: disparo admin-manual (botão), padrão M8.** O deadline é **data
  exibida**, não trava sozinho.

- **D5 — Owner que não declara ou cujo time viola adequação: o admin supre/ajusta
  manualmente** (corta pelo owner) **antes do lock**. (Precedente de escrita admin scoped a
  `team_id` arbitrário existe — F1; precisa de exceção explícita à regra cega-pré-lock.)

- **D6 — Sigilo: apenas a DECLARAÇÃO DE CORTES é secreta pré-lock, inclusive para admins**
  (que são owners). Exposto **só contagem agregada** ("8/12 declararam"), nunca conteúdo
  alheio. O **ROSTER permanece público** (já é hoje) — o sigilo recai sobre a **decisão de
  corte**, não sobre o roster. (Confirma o *deslocamento* que a F1 apontou.)

- **D7 — Revelação congela um SNAPSHOT auditável** (molde M8: canônico + `previous_id` +
  `reason` + `hash`; ver F1). **NÃO escreve no Sleeper** (isso é **OFF26-8**) **nem
  materializa cortes** no estado oficial do Manager. A aplicação de salário/adequação segue
  no rollover (passo 4) e na fronteira do FA auction.

- **D8 — Ordem no fluxo: a janela roda DEPOIS do Season Rollover (passo 4).** ⚙️ **DECISÃO
  DE INFRA DELIBERADA (a).** Lê salário **já valorizado** para a temporada nova (ESPN
  definitiva E4-a + regra de valorização aplicadas), porque a decisão de corte depende do
  salário **novo**. Cria a dependência de dados registrada acima (E4-a + rollover antes da
  janela). **Resolve o "gap timing" da F1** (passo 6 pós-rollover) escolhendo o lado
  pós-rollover.
  - **⚠️ Esclarecimento (MAN-OFF26-9, 17/06/2026 — NÃO altera a D8, só separa dois conceitos
    que a redação acima fundiu):** o "pós-rollover" da D8 é **timing de QUALIDADE DE DADO** —
    existe para o budget **não-projetado** (D9) exibir salário **já valorizado**, não como
    **trava de abertura**. A F1 do [[OFF26-9]] confirmou contra o código que a **abertura** da
    janela (`admin_open_window`, `routes/cuts.py`) exige **apenas `needs_review` zerado** — não
    checa E4-a nem `rollover_done`. A menção a "ESPN definitiva E4-a" nesta D8 é **qualidade do
    dado de salário** (afeta a exatidão dos valores valorizados e, depois, o salário de rookie
    no draft via `floor(ESPN×1.2)`), **eventos posteriores que não bloqueiam o início da
    intertemporada**. Em suma: **abrir** só pede `needs_review` zerado; **rodar pós-rollover** é
    recomendação para o budget aparecer valorizado; **E4-a** é exatidão de valor, não pré-condição
    de abertura. A decisão D8 (janela após o passo 4) permanece como está.

- **D9 — Budget ao vivo: consome a porta canônica `POST /api/cap_projector/<team>/budget`
  em MODO NÃO-PROJETADO.** ⚙️ **DECISÃO DE INFRA DELIBERADA (b).** Como o salário **já está
  rollado**, re-projetar (`project_next_salary`) **duplicaria** a valorização (o "gap duplo"
  da F1). Logo a janela precisa do salário **corrente** (já novo), não projetado. Isto é uma
  **ampliação consciente da porta canônica** (um modo não-projetado), **NÃO uma réplica e
  NÃO um débito** — a fonte de cálculo segue única (`draft_budget`); só muda a *base de
  salário* que alimenta o helper. **Registrar como decisão deliberada, não como violação do
  princípio de fonte única do F10.**

- **D10 — Validação 8.3.4 na janela: ALERTA, não trava.** O **enforcement** de adequação ao
  cap pertence à **fronteira do FA auction**, fora deste item. (Confirma a F1: hoje
  `insufficient_budget` já é soft.)

- **D11 — IR e K/DEF CONTAM no budget de keeper**, igual ao `draft_budget` atual. (Resolve o
  gap IR/K-DEF da F1 a favor de manter o comportamento do helper — sem exclusão especial.)

**Resumo das duas decisões que tocam infra (marcadas ⚙️, deliberadas):** (a) **D8** —
dependência de ordem pós-rollover (janela após o passo 4); (b) **D9** — ampliação da porta
canônica de budget com **modo não-projetado** (base = salário corrente já rollado), fonte de
cálculo ainda única.

#### F2 — Implementação (MAN-OFF26-1, 16/06/2026) — ⚠️ aguarda smoke prod

Construído sobre a Spec final. **e2e localhost: 23/23 checks** (script descartável, removido).
`salary_engine_test` 48/48. **Não marcar ✅ até smoke de produção** (lição E1).

**Arquivos tocados:**
- `models.py` — 2 models novos + helper de hash: **`CutDeclaration`** (estado editável/privado
  por `(season, team_id)`, `cut_ids_json`, `declared`; keepers por complemento) e
  **`CutWindowAudit`** (snapshot canônico no molde M8: `declarations_json` de todos os times +
  `is_canonical` + `previous_audit_id` + `reason` + `result_hash` + `executed_at/by`);
  `compute_cut_snapshot_hash` (SHA256 determinístico, ordenado por team_id/cut_id). Tabelas
  novas → criadas por `db.create_all()` (sem ALTER/migração).
- `routes/cuts.py` (**novo blueprint** `cuts_bp`) — página `/cuts` + API: `state` (contagem
  agregada, **sem conteúdo**), `declaration` GET/POST (**escopo `current_user.team_id`** — sem
  param de team_id, sigilo D6), `admin/open` (gate duro `needs_review` D3), `admin/close`,
  `admin/declare` (write-by-team D5, **não lê o alheio**), `admin/lock` (revelação D4/D7),
  `admin/replace` (M8, exige reason), `audit` (revela pós-lock) e `audit/verify` (re-deriva hash).
- `routes/salary.py` — **D9: ampliação da porta canônica** `POST .../budget` com
  `projected` (default `True` — **default intocado**; `False` = salário corrente já rollado).
  Fonte de cálculo segue `draft_budget` (sem 2ª rota, sem aritmética nova — invariante F10).
- `app.py` — registra `cuts_bp`; seed da flag `cuts_window_open`.
- `routes/offseason.py` — **backing do passo 6**: `done` = existe `CutWindowAudit` canônico.
- `templates/cuts.html` (**novo**) + link do passo 6 em `offseason.html`. O cliente só **exibe**
  o budget da porta; `kept_ids = roster − cortes` é **diferença de seleção, não aritmética de
  cap** (grep confirma: única referência a budget no template é display de `usable_draft_budget`).

**Validação de sigilo (requisito de segurança):** owner A tentando ler a declaração de B via
`GET /api/cuts/declaration?team_id=<B>` → o param é **ignorado**, retorna sempre o time de A.
Nenhuma rota expõe `cut_ids` alheios pré-lock; `state` só devolve contagem. Admin opera o time
alheio **só por escrita** (`admin/declare` retorna `num_cuts`, nunca o conteúdo). ✅ e2e.

**Default preservado (D9):** budget sem `projected` == `projected:true` (mesmo JSON); o
cap_projector (consumidor existente) não passa a flag → continua projetado. ✅ e2e.

**Não-mutação:** roster/Player intocados após lock+reveal (snapshot só lê). Nada escrito no
Sleeper. ✅ e2e.

**Fronteiras respeitadas:** 8.3.4 é só alerta (D10); IR/K-DEF contam (D11, herdado do
`draft_budget`); nenhum enforcement de cap; cortes reais no Sleeper = **OFF26-8**;
materialização de salário = Rollover/FA auction.

**Dependência de dados para o OFF26-7 (dry run E2E) — distinção MAN-OFF26-9:** a **abertura**
da janela exige só **`needs_review` zerado** (trava de código). O **Season Rollover (passo 4)**
e o **E4-a (ESPN definitiva)** são **qualidade de dado**, não travas: rodar o rollover antes
faz o budget não-projetado ler salário **já valorizado** (D8); o E4-a dá **exatidão de valor**
(e o salário de rookie no draft, evento posterior). Encadear nessa ordem no ensaio é
**recomendação para os valores aparecerem corretos**, não pré-condição que impeça abrir.

**Pendente (smoke prod):** abrir a janela em prod com `needs_review` real zerado; um owner
declarar; admin lock + verify hash; conferir contagem agregada e a revelação. Só então ✅.

#### Smoke PARCIAL em prod (MAN-OFF26-SMOKE-REG, 17/06/2026) — ⚠️ permanece (não vira ✅)

Smoke parcial executado pelo owner em produção **antes da intertemporada real** e **antes dos
passos 3 (ESPN) e 4 (Rollover)** do fluxo de offseason. Objetivo: validar **infraestrutura +
mecânica de abertura** sem criar snapshot canônico de teste no banco real. **Backup feito
antes:** `dynasty_prod_backup_17_06_2026_pre-off26.db` (540K). O owner optou por **NÃO travar
(lock)** a janela — a validação completa (lock/hash + cortes reais + budget definitivo) fica
para o **[[OFF26-7]]** (dry run E2E).

**Validado em prod (17/06):**
- Deploy do código OFF26-1/2 **live** — `/cuts` e o fluxo `/offseason` carregam sem erro.
- Tabelas novas (`CutDeclaration`, `CutWindowAudit`) **criadas no schema de prod** via
  `create_all` sem erro (toque de schema aditivo confirmado).
- Tela da janela renderiza: estado **"Fechada — 0/12"**, roster, budget **bruto/usável**,
  **alerta de cap soft** (não trava — D10), checkboxes de corte.
- **Gate `needs_review` zerado confirmado** (tela de Revisão de Jogadores) — pré-condição
  única de abertura (D3) satisfeita.
- Fluxo de 7 passos **coerente com o mapa da F1**.

**NÃO validado — fica para o [[OFF26-7]]:**
- Abertura efetiva da janela + declaração de **cortes reais**.
- **Lock/reveal** escrevendo o snapshot canônico + **verificação de hash** em prod.
- Conferência de budget da keeper sheet com **valores definitivos pós-ESPN/rollover**.

**Status:** **⚠️ mantido** — o smoke completo (com lock) ficou pendente; só vira ✅ após a
validação E2E na intertemporada real (OFF26-7).

#### F1 — Diagnose read-only do terreno (MAN-OFF26-1-F1, 16/06/2026)

Diagnose estritamente read-only (zero mutação). Mapeou os 5 terrenos que a janela
consome/colide. Base verificada para a F2.

**Budget canônico (fonte única confirmada pós-F10):** `salary_engine.draft_budget(team_players)`
([salary_engine.py:216-236]) é a função pura; a porta HTTP é `POST
/api/cap_projector/<team_name>/budget` ([routes/salary.py:114-179], `@login_required`),
body `{kept_ids:[Player.id], rookie_sids:[sleeper_id]}`, retorna
`{budget:{salary_cap, keeper_salaries, num_keepers, empty_spots, min_required_for_spots,
raw_budget, usable_draft_budget, over_cap, insufficient_budget}, cap_pct, shortfall, ...}`.
**Cobre o cenário keep-subconjunto** (passa-se os mantidos; cortados ficam fora) e **já
calcula a 8.3.4** (`usable = raw − empty_spots×$1`; `insufficient_budget`). **RÉPLICA:**
o F10/DP2 removeu o `POST /api/cap_projector/simulate` e a aritmética JS; o cliente só
exibe (`cap_projector.html` lê `b.*`, sem conta). **Fonte única confirmada** — OFF26-1
NÃO pode criar 3ª réplica; deve consumir esta porta.

**M8/LotteryAudit como molde:** [models.py:785-819]. **Transferível** (genérico):
`is_canonical`, `previous_audit_id` (cadeia), `reason` (obrigatório no replace),
`executed_at/by`, `result_hash` (SHA256 de conteúdo determinístico), blob JSON de
snapshot; **fluxo replace** = marca canônica antiga `is_canonical=False` + cria nova com
`previous_audit_id`+`reason` ([routes/offseason.py] `_execute_lottery_and_persist` /
`/lottery/replace`); endpoint `verify` re-deriva e compara hash. **Lottery-específico
(NÃO transfere):** `random_seed`, `weights_json`, `pool_json`. Para a janela, o snapshot
do lock guarda `declarations_json` (12 times). **Distinção arquitetural chave:** as
declarações **editáveis/privadas pré-lock** são um estado de trabalho SEPARADO (novo
storage por time) que **congela** no snapshot canônico no momento do lock — o audit M8
é molde só da peça "snapshot+canônica+replace", não do estado editável.

**Identidade de jogador/roster:** chave de declaração = **`Player.id`** (PK local — é o
que `kept_ids` já usa; `sleeper_player_id` só p/ rookies). Roster atual =
`Player.query.filter_by(team_id, is_dropped=False)`. `is_dropped` permanece na DB.

**Autorização — GAP NOVO sem precedente:** `@login_required`/`@admin_required` em
[routes/auth.py:101-112]; vínculo `User.team_id`+`team_rel`; context processor
`inject_user_team` ([app.py:115-121]). **Hoje NÃO existe escopo por-owner**: qualquer
logado lê o roster de qualquer time (`/api/roster/<id>`, `/team/<id>`, `/league` sem
filtro). **Sigilo-mesmo-de-admin é 100% novo e CONTRADIZ o modelo aberto atual.** Nuance:
o sigilo recai sobre a **declaração** (quem manteve quem), não sobre o roster (já público).
Admin escrevendo por time ausente **tem precedente** (admin.py escreve scoped a `team_id`
arbitrário), mas precisa de **exceção explícita** à regra cega-pré-lock.

**Estado de offseason:** `get_current_season()`/`is_offseason()` ([models.py:41-46]) sobre
AppConfig k-v. **O passo 6 "Definir Keepers / Cortes" do workflow é um placeholder**
(`_get_step_statuses`, [routes/offseason.py], `"done": False` hardcoded, sem flag, sem
backing) — é exatamente o slot da janela. `offseason_step` nunca é escrito (só lido); a UI
deriva estado de flags individuais.

**GAP CRÍTICO — base do budget × timing do rollover:** a porta canônica projeta cada
mantido via **`project_next_salary`** ([salary.py:149] → [salary_engine.py:169], usa
`contract_year+1`). O passo 6 fica **depois** do rollover (passo 4), que **já** incrementa
`contract_year` e valoriza `Player.salary`. Consumir a porta como está **pós-rollover
projeta um 2º incremento** (duplo). F2 deve arbitrar **quando** a janela roda e **qual
base** usa (salário corrente vs. projetado) para casar com o momento do fluxo.

**GAP — IR e K/DEF:** `Team.active_salary()` exclui `is_on_ir` ([models.py:96-100]), mas
`draft_budget` **conta** o salário de IR (só filtra `is_dropped`, [salary_engine.py:218]).
A barra de cap e o budget da janela divergiriam para times com IR. K/DEF idem (incluídos no
`draft_budget`, "excluídos em alguns contextos" no CLAUDE.md). Decisão pendente.

**GAP — 8.3.4 é soft hoje:** `insufficient_budget` é só **alerta**, nunca bloqueia
([draft_import.py], `cap_projector.html`). Se a janela deve **travar** declaração inválida,
é enforcement novo sobre a porta.

**REFUTAÇÃO DE PREMISSAS (MAN-METH-REG):**
- *(premissa que o código contradiz)* "sigilo total inclusive p/ admins" — **premissa nova
  válida, mas sem suporte e contra o modelo atual** (tudo público pós-login); exige
  construção do zero (deslocamento do modelo aberto → fechado por-declaração).
- *(premissa parcialmente falsa)* "budget ao vivo consome o endpoint canônico" — **certo
  consumir**, mas a projeção embutida (`project_next_salary`) **só casa se a janela roda
  pré-rollover**; pós-rollover é duplo. Seam, não bug.
- *(perda intencional?)* "validação 8.3.4" — hoje é **alerta soft**; tratar como trava é
  **decisão de produto**, não regressão silenciosa.
- *(perda não-intencional)* **IR/K-DEF**: a proposta é silente; o budget canônico conta IR
  e K/DEF, a barra de cap não conta IR. Precisa decisão.
- *(deslocamento)* o sigilo recai sobre a **declaração**, não o roster (já público) — a
  proposta diz "owner só vê o próprio roster", mas o roster já é visível a todos hoje.

**Decisões de produto ainda NÃO arbitradas (reveladas pela F1):** (1) janela pré ou
pós-rollover (define base do budget); (2) 8.3.4 trava ou só alerta; (3) IR conta no budget
de keeper?; (4) K/DEF conta?; (5) `needs_review` é elegível como keeper?; (6) a porta de
budget precisa de escopo por-owner (senão owner B sondável via `kept_ids`) ou aceita-se por
o roster já ser público?

**Gaps que a F2 fecha (curto):** storage editável/privado por-owner (≠ snapshot do lock);
autorização por-owner + cego-pré-lock (novo, sem precedente); endpoint só-contagem ("8/12")
sem vazar conteúdo; transição lock+reveal congelando snapshot canônico (molde M8:
`declarations_json`+`is_canonical`+`previous_audit_id`+`reason`+`result_hash`); reconciliar
base do budget com o timing do rollover; decidir 8.3.4 hard/soft e IR/K-DEF; backing do
passo 6 (flag + status em `_get_step_statuses`); caminho admin "supre time ausente" com
exceção à regra cega.

---
### OFF26-2 — Keeper sheet exportável
✅ **CONCLUÍDO (07/08/2026) — origem reescrita (U7: a sheet nasce do SYNC) e SMOKADA EM
PRODUÇÃO** no smoke da urna — MAN-OFF26-REG/F1/REFINE/F2/SMOKE/ETAPA2/**MAN-OFF26-10(-SMOKE)** —
Prioridade **Alta**

> **Fechamento (MAN-OFF26-10-SMOKE, 07/08/2026):** o ⚠️ que restava era **de fonte** — a sheet
> exigia um snapshot de janela que o redesenho extinguiu. Resolvido pelo U7 (`keepers = roster
> vivo`, carimbo do sync) e **conferido em produção**: a **PROVISÓRIA com o aviso de drops
> revelados não executados/sincronizados** foi vista na tela durante o smoke — é o estado
> intermediário perigoso, e ele grita. A virada para **DEFINITIVA** (sync posterior à revelação)
> ficou provada no E2E da entrega.

> #### U7 implementado (MAN-OFF26-10, 07/08/2026)
>
> - **`keepers = roster vivo`** (o que o último sync fotografou). Sem inversão de cortes, sem
>   `CutWindowAudit` — a janela extinta não produz mais nenhum snapshot, e sem esta reescrita
>   **não sairia sheet em 20/08**.
> - **Provisória × definitiva pelo carimbo do sync**, e a regra é explícita: sem revelação da
>   urna → provisória; **revelada mas sem sync depois dela → PROVISÓRIA** (é o estado perigoso —
>   drops revelados e não executados — e a tela **grita** em vez de silenciar); revelada + sync
>   posterior → **DEFINITIVA**.
> - **Coluna de status de declaração morreu** (não há mais declaração de cortes): virou
>   **Late drop** — "Late drop: \<nome\>" / "Sem late drop" / "—" antes da revelação.
> - **[[OFF26-15]] fecha junto:** `is_on_ir` por keeper, coluna **IR** na tabela e no CSV, e
>   "N no IR" no cabeçalho do time.
> - **Sheet virou @admin_required** (decisão do owner, 07/08): é artefato de transcrição e
>   auditoria; o budget do owner vive no League Hub e no Cap Projector.
> - **Contrato preservado, e por quê:** a chave `revealed` continua no payload — é o que o
>   **núcleo puro da auditoria** ([[OFF26-4]], 34 testes + fixtures congeladas) lê para saber se
>   há sheet utilizável. Mudou a **origem**, não o contrato; `lock_timestamp` passou a carregar
>   o carimbo do sync (é o instante que congela ESTA sheet). Chaves novas: `stage`,
>   `stage_label`, `sync_timestamp`, `late_drop`, `available`, `source`.

> **Consequência do redesenho de 06/08 (MAN-OFF26-1-ETAPA2) — fato verificado no código:**
> `routes/cuts.py::_build_keeper_sheet` exige um `CutWindowAudit` canônico para produzir
> qualquer sheet. Com os cortes de 20/08 acontecendo **no Sleeper** (sem declaração, sem lock,
> sem snapshot), **não haverá snapshot da janela grande** — e a sheet, do jeito que está, não
> sai. O caminho novo é mais simples e é **escopo da F2 da urna** (U7): pós-sync, **keepers =
> roster vivo**, sem inversão de cortes e sem gate de revelação; a sheet **provisória** (20/08)
> e a **definitiva** (pós-execução do late drop) são a mesma função em dois momentos, separadas
> pelo carimbo do sync. **Até a F2:** o único produtor de sheet é o motor legado em `/cuts`
> (abrir → lock com zero declarações → revelação), razão pela qual o bloco admin **não** foi
> removido junto com a porta de declaração do owner.

**Descrição:** relatório por time gerado a partir da revelação do OFF26-1 — keepers,
salários e budget resultante para o FA Auction.

**Motivação:** é o **insumo** que o Cowork transcreve para a liga fantasma; sem ele,
a transcrição não tem fonte de verdade.

**Escopo resumido:** exportar, por time, a lista de keepers + salário + budget de FA,
derivada da revelação selada.

**Dependências:** depende do **OFF26-1** (revelação/snapshot canônico).

#### Spec final — decisões de produto arbitradas (MAN-OFF26-2-REFINE, 16/06/2026)

Decisões do owner pós-F1. **Esta spec é a verdade do item.** A F2 lê esta camada; o
terreno/portas/gaps da F1 continuam válidos abaixo.

- **D1 — Língua do KEEPER por inversão do snapshot.** A sheet mostra **quem fica + salário
  + budget de FA**, derivada de `keepers = roster_live − cut_ids` do snapshot canônico do
  OFF26-1 (`CutWindowAudit`, season = `get_current_season()`), chave **`Player.id`**.

- **D2 — Fonte mista assumida e mitigada (⚙️ DELIBERADA).** Os **cortes** vêm congelados do
  snapshot; **salário e budget** são derivados **AO VIVO** na geração. A página exibe o
  **timestamp do lock** + aviso ("salários conferidos agora; regenere se algo mudou desde o
  lock"). **Justificativa:** não congelar salário no snapshot evita **duplicar a fonte
  canônica `p.salary` dentro do audit** e **não mexe no OFF26-1 já validado** (⚠️ localhost).
  O risco (rollover/correção/drop entre lock e sheet) é coberto pelo aviso de timestamp.

- **D3 — Salário = `p.salary`** (valorizado pós-rollover, D8 do OFF26-1). A sheet **NÃO**
  re-deriva via `project_next_salary`.

- **D4 — Budget de FA = `usable_draft_budget`** (reserva $1/slot, regra 8.3.4), obtido pela
  porta canônica `POST /api/cap_projector/<team>/budget` em **`projected:false`** — **mesma
  chamada e mesmo modo da janela**, para a sheet **bater com o que o owner viu no lock**. A
  sheet **NÃO recalcula** budget.

- **D5 — IR conta normalmente** (D11 do OFF26-1 mantida — jogador no IR é tratado como
  qualquer outro no budget). A sheet **NÃO** tem coluna/flag de IR.

- **D6 — Colunas:** `keeper`, `salário`, `budget de FA do time`, e **`declared`** (declarou de
  verdade / default-zero mantém-todos / admin-supriu) como **coluna de conferência**. **SEM**
  slots vazios, **SEM** contagem 8.3.4 — pertencem à fronteira do FA auction, não à transcrição.

- **D7 — Granularidade: CONSOLIDADA** — os **12 times** de uma vez (o Cowork monta a liga
  inteira; a OFF26-4 também quer todos).

- **D8 — Saída:** **CSV** como artefato principal (consumo do Cowork + registro anual) **+
  tabela renderizada na mesma página** (conferência humana). A F2 verifica se há precedente
  de export reutilizável (F1: **não há** — `csv` stdlib + `Content-Disposition` é padrão novo).

- **D9 — Pré-condição:** só gera **após a revelação** do OFF26-1 (snapshot canônico da season
  existe — `_window_locked`/`revealed:true`); a página comunica claramente se a janela ainda
  **não foi locked/revelada**.

**Decisão que toca a arquitetura, marcada deliberada:** **D2** — derivar salário/budget ao
vivo + aviso de timestamp (em vez de congelar no snapshot), preservando a fonte única
`p.salary`/`draft_budget` e o OFF26-1 intocado.

#### F2 — Implementação (MAN-OFF26-2, 16/06/2026) — ⚠️ aguarda smoke prod

Construído sobre a Spec final. **LEITORA — não muta nada.** e2e localhost **20/20**;
`salary_engine_test` 48/48. **Não marcar ✅ até smoke de prod** (depende, como o OFF26-1, de
janela revelada numa season real pós-rollover).

**Arquivos tocados:**
- `routes/cuts.py` — `_build_keeper_sheet(season)` (deriva `keepers = roster_live − cut_ids`
  do snapshot canônico; salário = `p.salary`; budget = `usable_draft_budget` via o **único**
  `draft_budget` com base corrente — mesmo precedente de `draft_import.py`, **sem aritmética
  nova**), `_declared_status` (default-zero/owner/admin-supplied: declared do snapshot +
  `CutDeclaration.updated_by` live, congelada pós-lock), `_team_fa_budget`. Rotas:
  `GET /cuts/keeper_sheet` (página), `GET /api/cuts/keeper_sheet` (JSON),
  `GET /api/cuts/keeper_sheet.csv` (download, `Content-Disposition`, `csv` stdlib).
- `templates/keeper_sheet.html` (**novo**) — tabela consolidada 12 times + aviso de fonte
  mista com **timestamp do lock** (D2) + botão CSV + comunicação da pré-condição (D9).
- `templates/cuts.html` + `templates/offseason.html` — links para a sheet (reveal / passo 6).

**Validações (e2e):**
- **keepers = roster − cortes:** Alpha corta A-Three → keepers {A-One, A-Two}; **Bravo
  default-zero** → mantém todos (status `default_zero`); **Charlie admin-supriu** → status
  `admin_supplied`. ✅
- **Budget == porta:** `fa_budget` (sheet) == `usable_draft_budget` da porta em
  `projected:false` para os mesmos keepers (130 == 130; usa `p.salary`, não `raw_budget`). ✅
- **Paridade tabela × CSV:** nº de linhas do CSV == total de keepers; CSV carrega
  `fa_budget`+status por time. ✅
- **Sem snapshot:** página 200 comunicando a pré-condição (não quebra); JSON `revealed:false`. ✅
- **Sem mutação:** Player intocado após gerar sheet/CSV. ✅
- **Réplica:** grep confirma **zero** aritmética de cap em `cuts.py`/`keeper_sheet.html` (única
  referência a budget é `draft_budget(...)["usable_draft_budget"]`). Invariante F10 mantida. ✅

**Cadeia (para OFF26-4 e OFF26-7):** a **OFF26-4** (auditoria pré-leilão) compara a config real
da liga fantasma **contra esta sheet** — consumir `/api/cuts/keeper_sheet` (JSON) como base de
diff. O **OFF26-7** (dry run E2E) encadeia: revelação OFF26-1 → **keeper sheet (CSV)** → Cowork
transcreve → OFF26-4 audita. A sheet pressupõe **snapshot revelado** (logo E4-a + rollover +
janela locked antes).

**Pendente (smoke prod):** com janela revelada numa season real, abrir `/cuts/keeper_sheet`,
conferir keepers/salário/budget por time, baixar CSV e validar paridade. Só então ✅.

#### Smoke PARCIAL em prod (MAN-OFF26-SMOKE-REG, 17/06/2026) — ⚠️ permanece (não vira ✅)

Coberto pelo mesmo smoke parcial do [[OFF26-1]] em produção (17/06, **antes dos passos 3 ESPN
e 4 Rollover**; backup `dynasty_prod_backup_17_06_2026_pre-off26.db` 540K; owner optou por
**não travar** a janela).

**Validado em prod (17/06):** deploy OFF26-1/2 **live**; tabela **`CutWindowAudit`** (fonte da
keeper sheet) **criada no schema de prod** via `create_all` sem erro; fluxo `/offseason`
coerente.

**NÃO validado — depende da revelação, fica para o [[OFF26-7]]:** a keeper sheet só é exercível
**com janela revelada** (snapshot canônico), e o lock **não foi disparado** neste smoke. Logo
ficam pendentes: `/cuts/keeper_sheet` com dados reais, conferência de **keepers = roster −
cortes**, **budget de FA** com valores **definitivos pós-ESPN/rollover**, e **paridade
tabela×CSV** em prod.

**Status:** **⚠️ mantido** — a sheet depende da revelação do OFF26-1, que não ocorreu neste
smoke parcial; validação completa no OFF26-7.

#### Melhoria com validação empírica: ORDENAR a sheet na sequência do board (MAN-OFF26-RUNBOOK-REG-PT2, 02/08/2026)

> **Registro apenas — nada implementado.** A sheet hoje sai agrupada por time, em ordem de roster
> do Manager. A melhoria abaixo tem **evidência de campo**, não é preferência estética.

Na 2ª execução do Cowork (02/08), a lista de keepers foi entregue **pré-ordenada na sequência exata
do board** — e o efeito foi qualitativo, não marginal: **eliminou busca, deliberação e navegação**,
transformando a transcrição numa **descida linha a linha**. **6 dos 24 keepers dispensaram edição
de preço** por serem de **$1** (o campo já nasce em `$1` — ver [[OFF26-5]]).

**Forma da melhoria:** emitir a sheet **time a time, na ordem das linhas do board**, com **marcação
explícita dos keepers de $1** (os que não exigem edição de preço). O consumidor é o procedimento
Cowork ([[OFF26-5]]), não uma tela do Manager.

**Por que isto merece registro e não é detalhe de formatação:** a sheet é o **artefato de handoff**
entre o Manager e o único passo do calendário que roda **fora** dele. Ordená-la na sequência do
consumidor é a diferença entre "dados corretos" e "dados operáveis" — e o custo é de ordenação,
não de lógica nova.

**Dependência de terreno:** a ordem das linhas do board segue a **config de roster** (QB, RB, RB,
WR, WR, WR, TE, FLEX, DEF, K, banco…), que o runbook exige espelhar a liga real. Ou seja, a ordem
é **derivável** do que o Manager já sabe — mas **confirmar contra o board real** antes de fixar,
porque a ordem exata das vagas de banco/FLEX não foi verificada.

#### F1 — Diagnose read-only do terreno (MAN-OFF26-2-F1, 16/06/2026)

Read-only (zero mutação) sobre o OFF26-1 F2 recém-commitado (`2c243d4`), roster e a
porta de budget. Base verificada para a F2.

**Estrutura do snapshot revelado (o que a sheet deriva):** `CutWindowAudit`
([models.py:854]); `to_dict()` expõe `declarations` = lista por time
`[{team_id, team_name, cut_ids, cut_names, num_cuts, declared}]`. **ACHADO CHAVE: o
snapshot congela SÓ a decisão de corte — NÃO grava salário nem budget.** Acesso ao
canônico: `CutWindowAudit.query.filter_by(season=season, is_canonical=True).first()`,
já exposto por `GET /api/cuts/audit` (`{revealed:true, audit:{...}}`). **Chave de season:**
a janela usa `get_current_season()` **direto** (pós-rollover) — NÃO `season+1` (isso é só
o lottery). A sheet deve casar essa chave.

**Derivar keepers:** `keepers = roster_atual − cut_ids`, com `roster_atual =
Player.query.filter_by(team_id, is_dropped=False)` e chave **`Player.id`** (mesma de
`cut_ids`). ⚠️ **Fonte mista:** roster é LIVE, `cut_ids` vêm do SNAPSHOT — coerente só
enquanto o roster ficar estável pós-lock (sem drop/trade entre o lock e a geração da sheet).

**Salário a exibir (fonte canônica):** **`p.salary`** (já valorizado pós-rollover — D8).
A janela calculou budget em **modo não-projetado** (D9), logo a sheet usa o **mesmo**
`p.salary`, **não** `project_next_salary`. O snapshot não guarda salário → a sheet lê live;
bate com o lock só na janela estável pós-lock (ver acima).

**Budget de FA (consumir, nunca recalcular):** `POST /api/cap_projector/<team>/budget`
com **`projected:false`** + `kept_ids = roster − cuts` — **exatamente a chamada que a
janela fez** (salary.py:114-189, D9). Retorna `raw_budget`, `usable_draft_budget`,
`empty_spots`, `min_required_for_spots`, `insufficient_budget`. **Decisão pendente: qual
número é "o budget de FA"** que o Cowork digita (provável `usable_draft_budget`, que já
reserva $1/slot vazio — 8.3.4).

**Pré-condição de existência:** a sheet só faz sentido com snapshot canônico presente —
`_window_locked(season)` (cuts.py:34) / `revealed:true` no `/api/cuts/audit`. Gate.

**Formato de export (precedente no app):** **NÃO há** export de CSV, página imprimível
(`@media print`/`window.print`), nem clipboard-de-dados. O que existe: import CSV/Excel
(admin/auction), **JSON por time** (`/api/roster`, `/api/cap_projector`, `/api/cuts/audit`),
tabelas **server-side Jinja** (casa de `league.py` team_detail, `roster.py`) e **1
precedente de clipboard** (link de trade, `trades.html:659-670`). `pandas`+`openpyxl`
disponíveis (requirements). Opções viáveis p/ o Cowork: (a) página Jinja imprimível
(mais aderente à casa, Cowork lê na tela), (b) download CSV (`csv` stdlib + header
`Content-Disposition` — padrão novo), (c) clipboard TSV (reusa o mecanismo do trade).

**PERGUNTA DE RÉPLICA — fonte única confirmada:** o cálculo de budget é só `draft_budget`
(via porta; F10/F1 confirmaram, `cuts.html` só exibe). O salário do keeper é só `p.salary`
/ `project_next_salary` — nenhuma 2ª derivação. **A sheet DEVE consumir** (porta + `p.salary`),
**nunca recalcular.** Nenhuma réplica encontrada.

**REFUTAÇÃO DE PREMISSAS (MAN-METH-REG):**
- *(premissa falsa)* "o snapshot congela salários/budget no lock" — **falso**: congela só
  `cut_ids`/`cut_names`/`num_cuts`/`declared`. A sheet deriva salário/budget **live**; só
  bate com o lock enquanto não houver rollover/correção/drop entre lock e sheet.
- *(deslocamento)* "keeper = roster − cortes revelados" — verdadeiro, mas é **fonte mista**
  (roster live − cuts do snapshot). Decisão da F2: aceitar derivação live (documentar a
  premissa de janela estável) — o snapshot **não** guarda a composição do roster no lock.
- *(premissa correta)* "modo de budget = não-projetado p/ bater com o lock" — confirmada (D9).
- *(perda)* o snapshot tem `declared` (declaração real vs. default-zero vs. suprido por admin);
  a proposta da sheet é silente. O Cowork deveria ver a **proveniência** (sheet de time que
  não declarou = roster inteiro por default, não escolha ativa).
- *(deslocamento/decisão)* keepers incluem **IR** (roster só exclui `is_dropped`; IR conta no
  budget — D11). A sheet listará IR; decidir se sinaliza.

**Decisões de produto NÃO arbitradas (p/ o owner, antes da F2):** (1) **formato de export**
(página imprimível vs. CSV vs. clipboard TSV); (2) **por-time individual vs. consolidada**
(12 times — o Cowork monta a liga inteira; a OFF26-4 também quer todos); (3) **qual número
é o "budget de FA"** (`usable_draft_budget` vs. `raw_budget`); (4) a sheet **inclui** slots
vazios / contagem 8.3.4 / flag IR / status `declared`?

**Gaps que a F2 fecha (curto):** derivar keepers = roster live − `cut_ids` do snapshot
(documentar premissa de estabilidade pós-lock); coluna de salário = `p.salary` canônico;
budget consumido da porta em `projected:false` (nunca recalcular); gate por snapshot canônico
existir; escolher formato de export; surfacing de `declared`/IR/qual budget; decidir
por-time vs. consolidada.

---
### OFF26-10 — Late drop pós-lock na janela selada (a URNA)
✅ **CONCLUÍDO (07/08/2026) — SMOKE EM PRODUÇÃO APROVADO** (owner + co-admin Rafa) —
MAN-OFF26-10-11-REG → -SPEC → -ETAPA2 → -F2 → -AJUSTES → **-SMOKE** — Prioridade **Alta**

> #### SMOKE EM PRODUÇÃO (MAN-OFF26-10-SMOKE, 07/08/2026) — passou por inteiro
>
> Executado pelo **owner e pelo co-admin Rafa** contra o checklist do
> `runbook_urna_late_drop.md`. Backup `/data/pre_smoke_urna.db` (**630.784 bytes**) conferido
> antes de tudo; banner de ensaio ON; reset verificado no fim.
>
> **O que ficou provado em produção — e não só em teste:**
> - **O escape do banner foi exercitado de fato:** com o rollover pendente, o agendamento só
>   passou **porque o banner estava ligado**. O gate do MAN-OFF26-10-AJUSTES não é teoria — e a
>   decisão de deixar o escape (em vez de exigir o rollover antes do smoke) **se pagou na
>   primeira vez que rodou**. A tela do admin documenta a ordem travada e o escape.
> - **Depósito pelo celular com confirmação inline, sem pop-up nativo.** O achado que travou o
>   Rafa no ensaio da janela (06/08) está **provado resolvido na urna** — no mesmo aparelho, com
>   a mesma pessoa. Era a razão de existir do U-CONF.
> - **Escolha única** (marcar o segundo desmarca o primeiro) e **"não vou dropar ninguém"**
>   contando no N/12 — as duas decisões de interface do owner, na mão dele.
> - **Fechamento automático pelo horário, provado por acidente produtivo:** a primeira agenda
>   (6 min) **expirou e a urna encerrou sozinha**, sem intervenção. O U3 ganhou a prova que
>   nenhum teste dá — o relógio virando em produção. Reagendada para o restante do smoke.
> - **Sigilo cruzado com o Rafa:** nem conteúdo nem autoria visíveis; **só o agregado**. É a
>   confirmação em campo da arbitragem do U1-CONT (o selado é *quem* e *o quê*; o N não é
>   nenhum dos dois).
> - **Hierarquia owner > admin:** suprimento sobre o time do Rafa (declarante pessoal)
>   **recusado sem vazamento**; sobre time mudo, gravando normalmente.
> - **Lock + Revelação** publicando a lista completa — drops e "sem late drop".
> - **Sheet PROVISÓRIA com o aviso** de drops revelados ainda não executados/sincronizados: o
>   estado que **grita em vez de silenciar** foi conferido com olho humano. (A virada para
>   DEFINITIVA já estava provada no E2E da entrega.)
> - **Reset** zerando bilhetes, snapshot **e a agenda**, banner off, estado pré-smoke.
>
> **Fica registrado como decisão de liga pendente (não é dívida de código):** a flag "bloquear
> rookie de 1ª rodada no late drop" segue **OFF** por default — o regulamento é silencioso e o
> código não arbitra. Ligá-la é decisão do comissário, de um clique, a qualquer momento.

> #### AJUSTES (MAN-OFF26-10-AJUSTES, 07/08/2026) — contagem agregada volta; ordem vira código
>
> **(A) U1-CONT — a contagem agregada volta ("N/12 depositaram").** A F2 a tinha removido por
> leitura estrita do sigilo; **o owner arbitrou a distinção**: o que é selado é **quem** e **o
> quê** — e a contagem não expõe nenhum dos dois. **Drop e passo contam indistintamente**, então
> **nem inclinação vaza** (quem entra no N pode estar passando). Função operacional: andamento
> para os owners e, para o admin, **quantos faltam cutucar** perto do lock. Superfície única:
> `/api/late_drop/state` devolve `declared_count` + `total_teams` — **números, não times**. Há
> teste que falha se aparecer qualquer chave capaz de individualizar o N ou de separar drop de
> passo (lista branca de chaves do endpoint).
>
> **(B) O bloqueio urna × rollover virou CÓDIGO — nos dois sentidos.** Era aviso de runbook
> (achado da F2); *runbook é promessa, código é garantia* (decisão do owner). O perigo é mudo:
> bilhetes e snapshot são escopados por `current_season`, então virar a season no meio **deixa
> os bilhetes órfãos e a revelação sai VAZIA, sem erro nenhum**.
> - **Rollover recusado (409, `blocked_by: urna_late_drop`)** enquanto a urna estiver
>   **agendada/aberta e não revelada** — mensagem diz o que bloqueia e o que fazer (revelar, ou
>   limpar a agenda). Gate em `POST /api/offseason/rollover`, via `urn_blocks_rollover()`.
>   **Depois da revelação libera** (snapshot congelado).
> - **Agendamento da urna recusado (409, `blocked_by: rollover_pendente`)** enquanto
>   `rollover_done != true`. **O gap que o prompt admitia não existe:** "rollover pendente" **é**
>   estado detectável (flag de AppConfig do ciclo). **Limpar a agenda é sempre permitido** — é o
>   caminho de destravar; se o gate barrasse a limpeza, urna e rollover ficariam em impasse.
> - ⚠️ **ESCAPE DECLARADO:** com o **banner de ensaio ligado** (`cuts_ensaio_banner`), o segundo
>   bloqueio libera. **Sem ele, o gate impediria o próprio smoke da urna**, que roda antes de
>   20/08 e pode cair antes do rollover de 18/08 (medido: `rollover_done=false` no seed local em
>   07/08). O escape é ato explícito do operador, **visível na tela para todos** e apagado pelo
>   `--reset`. Se o owner preferir bloqueio sem escape, é uma linha — mas aí o smoke exige rodar
>   o rollover antes.
>
> **Validação:** suíte da urna **47 → 64 testes** (6 da contagem, 11 do bloqueio nos dois
> sentidos, incl. rota real do rollover com o passo 4 destravado); dry-run E2E **42/42**;
> demais suítes verdes.

> #### F2 (MAN-OFF26-10, 07/08/2026) — a urna existe como código
>
> **Onde:** `routes/late_drop.py` (blueprint `late_drop`, página `/late_drop`),
> `templates/late_drop.html`, modelos `LateDropDeclaration` + `LateDropAudit` +
> `is_first_round_rookie` em `models.py`, suíte `late_drop_test.py` (47).
>
> **Decisão de schema declarada — tabelas PRÓPRIAS, não reuso das do OFF26-1.** Três motivos:
> (1) a cardinalidade é outra (UM drop ou passo, não lista de cortes); (2) a janela precisa de
> **flag de estado própria** de qualquer jeito; (3) as tabelas da janela grande são a rede de
> regressão do mecanismo provado em produção e ficam **congeladas**. **O que É reusado,
> literalmente:** `compute_cut_snapshot_hash` — cada entrada do snapshot carrega `cut_ids` com
> 0 ou 1 id, então o hash cobre exatamente **a lista de drops a executar**. Há teste que
> re-deriva o hash pela função da janela e compara.
>
> ⛔ **`cuts_window_open` NÃO é o gate da urna** (`late_drop_opens_at`/`late_drop_closes_at`
> são). `TestPortaUnicaESigilo.test_a_urna_nao_usa_a_flag_da_janela_legada` falha se alguém
> "simplificar" reusando a flag — porque reusá-la reabriria `POST /api/cuts/declaration` e a
> porta única viraria promessa de UI. Com a urna aberta, a rota legada segue recusando 409.
>
> **Sigilo mais estrito que o da janela (U1):** não existe contagem agregada — `/api/late_drop/state`
> devolve só `i_declared` do próprio time. Nem a **existência** do bilhete alheio vaza.
>
> **U6 na prática:** elegível = roster ativo do declarante. A flag de admin **"bloquear rookie
> de 1ª rodada" nasce OFF** (o regulamento é silencioso; o código não arbitra regra em disputa)
> — ligada, o jogador aparece **PROTEGIDO** na lista e o servidor recusa com o nome dele na
> mensagem. Fonte do "rookie de 1ª": `AuctionLog(entry_type='rookie_draft', round_num=1)`.
> Bilhete de jogador que **saiu do roster** entre o depósito e o lock vira **passo com aviso**
> na revelação — nunca drop fantasma.
>
> **U-CONF:** `confirmarInline()` em todo o caminho de declaração (owner, suprimento de admin e
> lock). ⛔ Zero `window.confirm()`, com guarda de grep na suíte.
>
> **Revelação = lista de drops a executar.** A tela publica os 12 times + o aviso de que **a
> execução é manual no Sleeper**, e o `--reset` do `ensaio_janela_selada.py` passou a limpar
> bilhetes, snapshots **e a agenda** da urna (horário de teste esquecido a reabriria sozinha).
>
> **Dry-run E2E no app real (07/08, cópia do seed): 38/38 PASS** — agenda → depósito de drop e
> de passo → escolha única → sigilo conferido por terceiro → substituição → hierarquia recusando
> sem vazar → flag do rookie → porta única → lock → hash `327ceace…` → revelação dos 12 →
> sheet provisória → execução + sync → **sheet definitiva** → CSV com IR → auditoria → reset.

**Calendário da intertemporada 2026, confirmado pelo comissário (02/08/2026):** **17/08**
rookie draft · **18/08** congelamento ESPN · **20/08** prazo de cortes · **22/08 late drop**
(cada time pode dropar **no máximo um** jogador) · **24/08** FA auction.

**Descrição:** a janela de cortes do [[OFF26-1]] foi desenhada com **deadline único, lock e
revelação simultânea**. O **late drop de 22/08** altera o conjunto de keepers **dois dias
depois do lock**, e keeper sheet ([[OFF26-2]]), budget de FA e board da liga fantasma derivam
**todos** do snapshot selado (`CutWindowAudit`). O item registra esse descompasso entre o
desenho vigente e o calendário real.

> **⚠️ Emenda de premissa (06–07/08/2026, MAN-OFF26-1-ETAPA2):** a Descrição acima e a Motivação
> abaixo descrevem o **descompasso original** — e ele **deixou de existir por dissolução, não
> por remendo**: com os cortes de 20/08 acontecendo **no Sleeper**, **não há lock de 20/08 nem
> snapshot da janela grande** para o late drop desencontrar. A "sheet provisória" continua
> existindo, mas por outro motivo (é a foto do sync **antes** do late drop). Ler o bloco
> **REDESENHO DE ARQUITETURA** abaixo como a premissa vigente; o texto original fica como
> registro do terreno que gerou o item.

**Motivação:** consequência operacional **já identificada** — a keeper sheet emitida em 20/08 é
**provisória** para os times que fecharam os cortes **acima do cap**, tornando-se definitiva só
**após 22/08**. Sem tratamento explícito, um artefato provisório circula com cara de definitivo
no exato ponto em que o Cowork o transcreve para o board.

**Fundamentos registrados (descrição do terreno, não decisão):**
- O late drop existe como **válvula** para o time que fecha os cortes ainda acima do cap e se
  ajusta antes do leilão.

##### Achados empíricos (experimento manual na liga fantasma real, 02/08/2026)

A suspeita registrada mais cedo nesta mesma sessão — "o Sleeper pode recusar designação acima do
budget" — **deixou de ser probe: foi CONFIRMADA por experimento.**

- **Fórmula do teto de lance, confirmada:** `teto = 200 − gasto − (vagas_restantes − 1)`. O Sleeper
  reserva **$1 por vaga ainda não preenchida**. Time com **$150 gastos** e **21 vagas livres** →
  teto **$29**: **$40, $33 e $32 rejeitados** (*"The specified slot does not have enough budget."*),
  **$29 aceito**. Sem falso positivo no sentido oposto — outro time recebeu **10 keepers somando
  $140** (folga de $49) **sem nenhum aviso**.
- **Time acima do limite NÃO ENTRA no board** — a designação é **recusada**. Logo **a população
  escalonada é OBRIGATÓRIA, não alternativa**: os times já enquadrados entram na primeira leva
  (20/08) e os estourados **só depois do late drop** (22/08). Não existe "popular tudo em 20/08 e
  remendar".
- **Funcionalidade concreta que isso abre:** o Manager **pode calcular antecipadamente quais times
  ficarão bloqueados** — antes de o Cowork tentar e apanhar da UI.

> ##### ⛔ PROPAGAÇÃO (MAN-OFF26-4-REFINE-PT2, 03/08/2026) — o bloqueio EXPÕE os keepers do time
>
> O [[OFF26-4]] registrou que **um keeper fora do board é, para o Sleeper, JOGADOR DISPONÍVEL**:
> qualquer owner pode nomeá-lo e o leilão **processa o lance normalmente**. Combinado com o achado
> deste item — times acima do teto **não conseguem ser populados até o late drop** —, a consequência
> é direta e **não é hipotética**:
>
> **Enquanto um time permanece bloqueado, TODOS os keepers dele estão expostos ao leilão.**
>
> → **A população completa do board é PRÉ-CONDIÇÃO DE ABERTURA do leilão, não preparativo.**
> **Abrir o leilão com qualquer time não populado expõe os keepers desse time** — e o dano não é
> contábil: é **transação inválida ao vivo, sem forma limpa de desfazer sem interromper o leilão**.
>
> **O que isso NÃO decide:** a **decisão em aberto** deste item (2ª mini-janela selada × correção
> administrativa pós-lock) **permanece em aberto** — isto é **registro de consequência**, não
> arbitragem. Mas qualquer desenho que saia dela **tem de terminar com o board 100% populado antes
> de 24/08**, porque a janela 22/08 → 24/08 é curta e o custo de errar é o leilão.
- **Assimetria de limite — a premissa mudou de lado.** O que se supunha ser regra só do Manager
  (reserva de $1/slot) é **a mesma dos dois lados**; ver a **refutação do §5 da F1 do [[OFF26-4]]**,
  registrada nesta sessão. **Ressalva pendente:** o Sleeper reserva sobre as **22 rodadas** da sala;
  a regra **8.3.4** conta slots pelo **regulamento**. Se as contagens divergirem, os limites não
  coincidem apesar da fórmula idêntica — **conferência aritmética pendente, não experimento**.

**Escopo resumido:** registro apenas. Definir como a janela selada acomoda uma alteração de
keepers posterior ao lock, e o que isso implica para a emissão da keeper sheet, para o budget
de FA e para a ordem de população do board.

**✅ DECISÃO ARBITRADA PELO OWNER (06/08/2026, MAN-OFF26-10-SPEC): a URNA — segunda mini-janela
selada, no Manager, para 2026.** O late drop de 22/08 é uma segunda janela selada no molde do
[[OFF26-1]]: cada owner deposita sua declaração em sigilo; ninguém vê **nada** — nem a existência
de declarações — até o prazo; revelação simultânea depois. Metáfora do owner: **bilhete na urna,
e a urna só abre depois do prazo.** A alternativa de baixa tecnologia (**DM ao comissário**) foi
**DESCARTADA pelo owner** — não funciona; desenvolve-se a ferramenta, há tempo. O ramo "correção
administrativa pós-lock" morre junto: haverá **novo lock/hash e revelação simultânea de novo**.

#### ⛔ REDESENHO DE ARQUITETURA (MAN-OFF26-1-ETAPA2, 06/08/2026) — o modelo selado vale APENAS para o late drop

**Decisão do owner, durante o ensaio de produção:** os **cortes principais de 20/08 acontecem
direto no Sleeper** — **públicos e graduais, sem sigilo e sem declaração no Manager**. Confirmado
explicitamente: **o sigilo que a regra da liga exige é só o do late drop**. **O Manager entra
apenas em 22/08, como a urna.**

**Princípio que a arquitetura preserva:** o **Sleeper é a única fonte de roster o tempo todo** —
o Manager **nunca escreve roster, só fotografa**. A urna é **protocolo de sigilo e revelação**;
a **execução fica onde sempre esteve**.

**Linha do tempo operacional decidida:**

| Quando | Onde | O quê |
|---|---|---|
| **20/08** | **Sleeper** | cada owner corta no próprio roster, em público e no seu tempo |
| **20/08 (após o prazo)** | Manager | **sync** → o Manager fotografa os rosters → **keeper sheet provisória** (nasce do sync, **não** de declarações) |
| **20→22/08** | Manager | **urna aberta**: um late drop **ou** passo, por time, em sigilo total |
| **22/08** | Manager | **lock + revelação** da urna → produz a **lista de drops a executar** |
| **22/08 (após a revelação)** | **Sleeper** | **execução manual** dos drops revelados (owner/admin) |
| **22/08 (após a execução)** | Manager | **sync final** → **keeper sheet definitiva** → é ela que o Cowork transcreve e que a auditoria [[OFF26-4]] usa como gate |
| **24/08** | Sleeper (fantasma) | FA auction |

**Janela de execução manual (entra no runbook do dia):** revelou → **owners executam no
Sleeper** → **admin confere que os drops revelados sumiram dos rosters** → **sync final** →
sheet definitiva. **Se um revelado não executar, a auditoria [[OFF26-4]] acusa** (o jogador
aparece na sheet e/ou no board fora do esperado) — **comportamento correto, registrado como
tal**: a detecção existe e é a rede.

**PORTA ÚNICA durante a urna (exigência, não preferência):** enquanto a urna estiver aberta,
**nenhuma outra tela pode aceitar declaração**. Duas consequências já executadas/registradas:
1. **A tela de declaração múltipla de cortes foi APOSENTADA** (feito nesta sessão — ver o
   destino declarado logo abaixo).
2. ⛔ **A urna NÃO pode reusar a flag `cuts_window_open`.** Ela precisa do **próprio estado**
   (chave AppConfig própria). Motivo verificado no código: `POST /api/cuts/declaration` só
   aceita quando `cuts_window_open == "true"`; se a urna ligasse essa mesma flag, **reabriria a
   porta antiga** e a porta única deixaria de ser estrutural — viraria promessa de UI.

**DESTINO DA TELA DE DECLARAÇÃO MÚLTIPLA — decidido e executado (07/08/2026): APOSENTADA
(porta do owner removida), motor mantido como ferramenta administrativa rotulada.**
- **Removido da tela `/cuts`:** roster com checkbox de corte, "💾 Salvar minha declaração",
  "✋ Não vou cortar ninguém", barra de budget ao vivo e todo o JS associado. No lugar: a
  **explicação do fluxo de 2026** (Sleeper 20/08 → sync → urna 22/08 → execução manual → sync
  final) e o link para a keeper sheet.
- **Mantido (admin, rotulado "legado — fora do fluxo"):** abrir/fechar janela, **lock +
  revelação**, suprir/ajustar pelo time, revelação + verificação de hash. **Por que não removi
  tudo:** hoje **o motor legado é o único produtor de keeper sheet** (`_build_keeper_sheet`
  exige snapshot canônico — ver [[OFF26-2]]); removê-lo antes da F2 deixaria a liga **sem
  sheet nenhuma** se a F2 escorregar. Aviso explícito na tela: **abrir esta janela em 20–22/08
  criaria uma segunda porta**.
- **Rotas de declaração preservadas** (não é porta na tela): são o mecanismo que a urna reusa e
  a rede de regressão da hierarquia owner > admin (7 testes de `janela_ensaio_test.py`).
  Reversível por git.

#### SPEC DA URNA — decisões do owner (06/08/2026), insumo direto da F2

> **Os itens U1, U3 e U7 foram REESCRITOS em 06–07/08/2026 pelo redesenho acima.** O texto
> vigente é este; a versão anterior (urna encadeada à revelação da janela grande) **não vale
> mais**.

- **U1 (REESCRITO) — Uma declaração por time, conteúdo selado por completo, em lista de escolha
  única.** A declaração é: **um jogador do próprio roster** (o late drop) **ou "passo"** (sem
  drop). **Decisão de interface do owner:** lista de **escolha única com aparência de checkbox**
  — **marcar um desmarca o anterior** —, com a opção destacada **"Não vou dropar ninguém"** como
  **item da própria lista** (N jogadores **+ 1** passo; **uma marcação sempre**). Declarar dois
  é **tecnicamente impossível pela interface**, não apenas validado no servidor (a validação
  continua existindo, como rede). Durante a janela, **nada é visível a ninguém** — nem o
  conteúdo, nem se o time declarou. **O sigilo cobre a existência da declaração** (mais estrito
  que o OFF26-1, que mostra o agregado "Fechada — N/12").
- **U2 — Efeito de não declarar = passo.** Quem não depositar nada até o prazo fica sem late
  drop. Declarar "passo" e não declarar têm o **mesmo efeito revelado** ("sem late drop"); a
  distinção **pode** existir internamente (trilha), nunca no resultado.
- **U3 (REESCRITO) — Janela: abre por HORÁRIO DEFINIDO PELO ADMIN**, depois do prazo dos cortes
  no Sleeper **e do sync** que fotografa os rosters; fecha em **22/08**, também em horário
  configurável. **Não há encadeamento com revelação de janela grande — ela não existirá.**
  Fora da janela, a urna **não aceita depósito**. (O gate útil aqui é o **sync recente**: sem
  ele, a lista de elegíveis do U6 mostra roster velho — jogador já cortado no Sleeper apareceria
  como dropável.)
- **U4 — Declaração substituível até o lock.** Dentro da janela, o owner troca a própria
  declaração à vontade (outro jogador, ou passo). **Vale a última antes do lock** — coerente com
  a janela de cortes.
- **U5 — Lock + hash + revelação simultânea, no molde do OFF26-1.** **Reuso, não
  reimplementação** do mecanismo existente (lock, hash de integridade, trilha de auditoria molde
  M8, revelação). Onde for parametrizável, parametrizar; onde exigir adaptação, adaptar **sem
  duplicar lógica**.
- **U6 — Elegibilidade do drop:** apenas jogador **atualmente no roster do time declarante**.
  Drop declarado de jogador que **saiu do roster entre a declaração e o lock** (trade, p.ex.) é
  **inválido e tratado como passo, com aviso na revelação**.
  **O que o regulamento diz (conferido no texto de 12/08/2025):** sobre proteção de rookie de 1ª
  rodada contra drop, o regulamento é **SILENCIOSO** — não existe regra escrita que proíba dropar
  o rookie recém-draftado. O que existe: **8.2.6** ("todos os owners são obrigados a draftar na
  primeira rodada; podem renunciar às picks de 2ª e 3ª") — o drop imediato do rookie de 1ª
  **esvaziaria de fato a obrigação**, leitura defensável mas **não escrita**; e **8.2.2** (rookie
  draft "**sempre antes os drops**") — fixa só a sequência do calendário. ⇒ A exclusão "keepers
  já protegidos por regra" citada na spec **não tem hoje regra escrita que a alimente**; se o
  owner quiser a proteção do rookie de 1ª na urna, é **decisão de liga a arbitrar na F2**
  (default da spec, na ausência dela: elegível = está no roster).
- **U7 (REESCRITO) — A sheet definitiva nasce do SYNC PÓS-EXECUÇÃO, não da revelação.** A
  revelação da urna produz a **lista de drops a executar** (não a sheet). Sequência: revelação →
  **execução manual no Sleeper** → **admin confere** que os drops sumiram dos rosters → **sync
  final** → **keeper sheet definitiva**. É essa sheet que a auditoria [[OFF26-4]] usa como lado
  do diff e que o Cowork transcreve no board.
  **Consequência de implementação (escopo da F2, fato verificado no código):**
  `routes/cuts.py::_build_keeper_sheet` hoje **exige um `CutWindowAudit` canônico** e inverte
  cortes (`keepers = roster_live − cut_ids`). No desenho novo **não há snapshot da janela
  grande**, então a sheet passa a ser **`keepers = roster vivo`**, sem gate de revelação e sem
  inversão — a **provisória** (20/08) e a **definitiva** (pós-execução) são a **mesma função em
  dois momentos**, distinguidas pelo **carimbo do sync** exibido na página. A distinção
  provisória × definitiva **continua sendo o coração deste item** (o artefato provisório não
  pode circular com cara de definitivo) — só muda **de onde ela vem**: do timestamp do sync, não
  do lock.
- **U8 — O efeito do drop no contrato segue o caminho canônico** de corte já existente
  (devolução integral do salário, **sem dead money** — regra da liga; o regulamento é
  consistente: o cap deriva dos mantidos, 8.3.3, e o cortado fica disponível para o draft,
  8.1.3). **A urna declara; a execução do corte na revelação usa o mecanismo de corte do
  OFF26-1, não um paralelo.**

> **Herança registrada (06/08/2026, MAN-OFF26-1-POSENSAIO): a urna herda a hierarquia
> owner > admin da janela de cortes.** A declaração pessoal do owner (drop OU passo)
> **prevalece** sobre a escrita do admin: suprimento admin sobre time que já declarou
> pessoalmente é **recusado** (recusa seca, molde da janela), com aviso que expõe só
> **existência e autoria** — nunca o conteúdo. O "passo" do U1 é o análogo do
> "manter todos" explícito da janela (POSENSAIO), e como lá, **distingue-se do silêncio**
> (U2) na trilha e no resultado revelado. A F2 da urna nasce com isso.
>
> **Confirmado em campo na Etapa 2 (06/08):** a recusa apareceu exatamente como desenhada
> (existência + autoria, **sem conteúdo**) e **o owner validou o comportamento**. Deixa de ser
> desenho testado em localhost e passa a ser **comportamento observado em produção**.

- **U-CONF (NOVO, 06/08/2026 — achado da Etapa 2) — confirmação INLINE, nunca `confirm()`
  nativo.** No ensaio, o **pop-up nativo falhou no celular** e **impediu a declaração** do
  co-admin (funcionou no desktop; ele precisou ir ao computador). Como **em 22/08 a maioria
  declara pelo celular**, na urna a confirmação é **obrigatoriamente inline**: o botão **vira
  "confirmar?"** e só executa no **2º clique** (com reversão automática por timeout). ⛔
  **Nenhum `window.confirm()` no caminho de declaração da urna.** Padrão já implementado e
  disponível para copiar: `confirmarInline()` em `templates/cuts.html`
  (MAN-OFF26-1-ETAPA2).

#### Pré-condições de sequência da F2 (registradas)

1. ✅ **CUMPRIDA (06/08/2026) — o smoke real do OFF26-1/2 rodou em produção.** A Etapa 2 do
   ensaio executou o **ciclo completo em prod** (12 declarações, sigilo cruzado, hierarquia,
   lock, hash `52274d01…`, revelação, sheet, reset verificado). O mecanismo que a urna reusa
   está **provado**, não suposto — ver o bloco ETAPA 2 no [[OFF26-1]].
2. A F2 da urna precisa estar **entregue e smokada antes de 22/08** — e agora **antes de 20/08**
   por um motivo novo: com a janela grande fora do fluxo, **a keeper sheet provisória de 20/08
   também depende da F2** (U7 — sheet a partir do sync). Sem F2, o único produtor de sheet é o
   motor legado de `/cuts` (abrir → lock com zero declarações → revelação), que é fallback, não
   plano.

#### O que o redesenho SIMPLIFICA (registro, 06/08/2026)

O fluxo de **declaração/lock/reveal da janela grande deixa de ser usado no caminho principal** —
mas o **mecanismo** (lock, hash, snapshot, reset, banner de ensaio, hierarquia owner > admin) é
**exatamente o motor da urna**, e este ensaio o **provou em produção**. **Nada do que foi
construído se perde**; o que muda é **qual tela o aciona**. Some do caminho crítico: a coleta de
12 declarações múltiplas sob prazo, a adequação de cap dentro da janela, e o risco de a sheet de
20/08 circular como definitiva (agora a distinção é o carimbo do sync). Fica: **um bilhete por
time, uma abertura, uma revelação.**

**Dependências:** depende do **[[OFF26-1]]** (é o snapshot que o late drop altera; e é o
mecanismo reusado — U5/U8); **afeta [[OFF26-2]]** (sheet provisória 20/08 × definitiva
pós-urna — U7) e **[[OFF26-4]]** (a auditoria compara contra a definitiva — U7). Entra como
**etapa do [[OFF26-7]]**, entre o lock e a sheet definitiva.

---
### OFF26-15 — Keeper sheet não marca quem está em IR
✅ **CONCLUÍDO (07/08/2026)** — entregue na F2 da sheet (MAN-OFF26-10) e coberto pelo **smoke da
sheet em produção** (MAN-OFF26-10-SMOKE) — Prioridade **Alta** — achado da [[OFF26-14]] F1,
escopado como item na F2 (04/08/2026)

> **Como fechou:** a sheet passou a carregar `is_on_ir` por keeper (a reescrita da origem, U7 do
> [[OFF26-10]], tocava exatamente esse ponto — fazer junto custou uma coluna). Superfícies:
> **coluna IR** na tabela, **coluna `IR`** no CSV (o que o Cowork transcreve) e **"N no IR"** no
> cabeçalho de cada time. O `fa_budget` já contava o salário deles (régua com IR, [[OFF26-16]]);
> o que faltava era a **marcação**, e é ela que evita omitir um keeper de IR no board — omissão
> que, pelo achado do [[OFF26-4]], **o expõe ao leilão**. Medido no dry-run: **5 linhas
> marcadas** (eram 5 jogadores em 3 times no censo de 04/08).

**O problema.** `keeper_sheet.html` **não tem badge de IR** (zero ocorrências de "IR" no template).
A sheet lista os jogadores em IR como keepers quaisquer, **sem distinguir**.

**Por que é Alta, e não cosmético.** Keeper em IR **ocupa designação no board** da liga fantasma —
o board **não tem slot de IR** ([[OFF26-13]]). Quem transcrever a sheet em 20/08 **não tem como
saber que precisa incluí-los**, e pelo achado do [[OFF26-4]] — *"keeper fora do board é jogador
leiloável"* — **omitir um deles o expõe a ser arrematado ao vivo**. É a mesma classe de dano do
OFF26-13, por outra porta: lá o keeper não cabe, aqui **cabe mas ninguém sabe que precisa entrar**.

**Estado hoje:** **5 jogadores em 3 times** — achane (Michael Penix $1, Travis Hunter $8), Fazenda
Pederasta (Kendre Miller $1, Tory Horton $1), rafaelferreirap (Zach Charbonnet $3).

**O que já está certo e NÃO deve ser mexido:** a sheet **já conta** o salário deles no `fa_budget`
(régua com IR, D4 do [[OFF26-2]]). **Não é erro de cálculo — é ausência de marcação visual.** O
`is_on_ir` já existe no `Player`; falta levá-lo ao payload da sheet e renderizar o badge (+ coluna
no CSV, para manter a paridade 1:1 que o `keeper_sheet_csv` promete).

**Cross-refs:** [[OFF26-13]] (keeper em IR ocupa designação), [[OFF26-4]] (o achado que dá a
gravidade), [[OFF26-2]] (a sheet e a paridade CSV), [[OFF26-14]] (de onde saiu).

---

### OFF26-5 — Runbook do procedimento Cowork
✅ **17/06/2026 — runbook criado (`runbook_cowork_liga_fantasma.md`), reconciliado com as
decisões do OFF26-6** — MAN-OFF26-6-7-REG/MAN-OFF26-5 — Prioridade **Média** — **item de
documentação (não é código)**

> **Critério de ✅:** documento de runbook criado no local/convenção do projeto, com os detalhes
> operacionais do PoC preservados — **sem código, sem smoke prod aplicável**.

**Descrição:** passo a passo operacional da transcrição supervisionada da keeper
sheet para a liga fantasma via **Cowork + Claude in Chrome**, incluindo pré-requisitos
de acesso (sessão do comissário detentor dos direitos no Sleeper, ou co-comissário),
gravação do workflow na primeira execução para reuso anual, e o gatilho da auditoria
(OFF26-4) ao término.

**Motivação:** o procedimento é supervisionado e anual; um runbook torna-o
reproduzível e reduz dependência de memória entre temporadas.

**Escopo resumido:** documento de runbook (pré-requisitos de acesso → gravação do
workflow → execução → gatilho da auditoria OFF26-4).

**Dependências:** documentação; depende conceitualmente de **OFF26-2** e **OFF26-4**
para fazer sentido completo.

#### Entrega (MAN-OFF26-5, 17/06/2026) — ✅ runbook criado

Arquivo **`runbook_cowork_liga_fantasma.md`** (raiz, convenção `manager_*.md`/`*_*.md` do
projeto). Conteúdo-base escrito pelo **Cowork** logo após o PoC ([[OFF26-6]]), com detalhes
operacionais fiéis **preservados** (edição do preço com **Ctrl+A**, anti-homônimo por **sigla
NFL** — dois Josh Allen, conexão da **extensão** Claude in Chrome, anatomia do **board**,
**SET PLAYERS** → board, **não clicar START DRAFT**, checklist **TL;DR**).

**3 reconciliações aplicadas (decisões do [[OFF26-6]]), sem perder detalhe operacional:**
1. **Config de roster espelha a liga real** — ajuste **WR 2→3 marcado como OBRIGATÓRIO** (não
   opcional); alvo 1QB/2RB/3WR/1TE/1FLEX/1DEF/1K (+ banco/IR reais); preservado o "como" (+/–).
2. **Liga PERMANENTE + mapa por owner** — liga criada **uma vez** com os 12 owners reais;
   identidade por **`sleeper_owner_id`/handle**, nunca por nome nem "Team N = roster N"; o
   bloqueio "times sem dono não renomeáveis" rebaixado a **nota histórica do PoC** (não-aplicável
   na liga permanente).
3. **SETUP ÚNICO × TRABALHO ANUAL separados** — Fase A (criar liga, roster, Auction+Budget,
   convidar owners) vs. Fase B (só popular keepers da [[OFF26-2]] no board); **reset de rosters é
   automático** (redraft); **gatilho da auditoria [[OFF26-4]] ao término**, antes do auction.

**Cross-refs:** [[OFF26-2]] (keeper sheet — fonte dos keepers/salários), [[OFF26-4]] (auditoria —
gatilho ao término), [[OFF26-6]] (PoC que originou o runbook). **Sem código.**

#### Correção do runbook contra a UI real (02/08/2026 — MAN-OFF26-10-11-REG) — **status ✅ mantido**

> Correção de **texto factual** de um item fechado: o runbook descrevia um caminho que **não existe**
> na interface atual. **O status não é reaberto** — o documento existe e cumpre sua função; o que
> mudou é o conteúdo, agora conferido contra uma transcrição real cronometrada.

**Origem:** a liga fantasma permanente foi **criada de fato** em 02/08/2026 — **Dynasty SB FA
Auction**, Redraft, 12 times, draft **Auction**, budget **$200**, **22 rodadas**, roster espelhando
a real (**3 WR**). O Cowork então transcreveu **1 time completo (10 keepers)** e, no caminho,
descobriu que a Fase B do runbook estava errada.

**8 correções aplicadas em `runbook_cowork_liga_fantasma.md`:**
1. **O caminho documentado NÃO EXISTE.** Não há engrenagem → Draft Settings → *SET
   KEEPERS/DYNASTY PLAYERS* → *SET PLAYERS*. O board **já está em modo de designação** no
   pré-draft; o fluxo real é clicar **direto na célula vazia** da coluna do time → menu → **Set
   Player**.
2. Dentro do Set Player, clicar no **"+" da linha, NUNCA no nome** — clicar no nome abre o perfil
   do jogador, e fechar o perfil **cancela o fluxo inteiro** sem setar nada.
3. **K e DEF ficam abaixo da dobra** do board; revelar pela **seta ▼** do canto direito — o
   **scroll do mouse não move o board**.
4. Para K e DEF, usar o **filtro de posição** em vez de digitar o nome.
5. O campo de preço **já vem com $1** → para keepers de $1 **não é preciso editar**.
6. **Ctrl+A antes de digitar funcionou em 100% dos casos** → rebaixado de **alerta** a **nota**.
7. **Homônimo:** o pool de designação traz **apenas ofensivos elegíveis**, então o Josh Allen
   **LB/JAX não aparece**. Alerta **suavizado, não removido** — dois ofensivos homônimos
   continuariam ambíguos.
8. Nome correto da liga: **Dynasty SB FA Auction**.

**Estado da liga (atualizado — MAN-OFF26-RUNBOOK-REG-PT2, 02/08/2026):** após o reset, a **2ª
execução do Cowork repopulou o board** com **Team 3 ($148)**, **Team 4 ($95)** e **Team 5 ($60)**
— dados de **teste**. **Novo RESET DRAFT pendente antes do uso real**, e ele **trocará o
`draft_id` outra vez**. Identificadores: **`league_id` = `1389725099556372481`** (estável) ·
**`draft_id` atual = `1389755381567213568`** — o anterior (`1389725100684611584`) **está morto**,
com a URL travando em LOADING. Tabela completa e a **restrição de desenho** decorrente no bloco do
pacote OFF26 e na seção do [[OFF26-4]]; **nada persistido em código** — a parametrização é decisão
em aberto do OFF26-4.
*(A URL do draft morto "travando em LOADING" é comportamento do **app web**; **pela API ela dá 404
limpo** — ver a correção de premissa do **D1** na spec do [[OFF26-4]].)*

#### ⛔ PROPAGAÇÃO (MAN-OFF26-4-REFINE-PT2, 03/08/2026) — board incompleto NÃO é estado aceitável

> Correção de conteúdo do runbook (**status ✅ mantido**), de peso operacional alto.

O [[OFF26-4]] registrou que **um keeper fora do board é JOGADOR LEILOÁVEL**: o Sleeper o trata como
**disponível**, qualquer owner pode **nomeá-lo** e o **lance é processado normalmente**. Isso muda o
peso de uma instrução que o runbook **já tinha** (*"NÃO clicar em START DRAFT até tudo estar
populado"*): deixa de ser **higiene de processo** e vira **integridade do leilão**.

**Aplicado em `runbook_cowork_liga_fantasma.md`: board incompleto NÃO é estado aceitável para
iniciar o leilão.** Cada keeper não designado é **um jogador com contrato vigente exposto a ser
arrematado por outro time, ao vivo, sem desfazer limpo**. Vale inclusive — e sobretudo — para o
caso do **[[OFF26-10]]**: times **bloqueados pelo teto** ficam com **todos os seus keepers
expostos** até serem populados após o late drop.

**Também registrado no runbook (resolução do owner, 03/08):** **keeper em IR se designa
normalmente**; os excedentes caem no **banco** e a vaga é atribuída **automaticamente por posição**
— a fantasma **não tem slot de IR** e isso **não é problema**. Detalhe e a alternativa descartada na
seção do [[OFF26-4]].

#### Medição de esforço e decisão de método (02/08/2026 — MAN-OFF26-10-11-REG)

**Medido, não estimado:** transcrição de **1 time (10 keepers)** pelo Cowork = **20 min 32 s**
totais, dos quais **~9 min de overhead único** de descoberta do caminho. **Ritmo de regime:
~75 s/jogador ≈ 12,5 min/time → ~2,5 h para os 12 times.** Comparação: a transcrição **manual** do
ano anterior consumiu **uma tarde inteira**.

**Decisão do owner (registrada):**
- **2026 → via Cowork**, com o runbook corrigido.
- **Script determinístico de transcrição → item de melhoria para 2027.** O argumento que o
  justificaria — *"não cabe na janela de 48 h entre o late drop (22/08) e o leilão (24/08)"* —
  **cai** diante dos **2,5 h medidos**. Registrado aqui, e **não** como linha do Status Rápido, por
  restrição do prompt de registro (só OFF26-10/11 entram); **candidato natural a ID próprio** na
  próxima sessão de registro.
- **Caminho via API interna não documentada: DELIBERADAMENTE DESCARTADO.** Sem contrato → quebra
  sem aviso; provável **violação de termos de uso**; e **expõe a conta de comissário da liga real**.
  Registrado para que não seja re-proposto como "otimização óbvia" em 2027.

#### 2ª execução do Cowork — runbook corrigido VALIDADO (MAN-OFF26-RUNBOOK-REG-PT2, 02/08/2026)

Segunda rodada no mesmo dia, agora **com o runbook já corrigido** e **com a lista de keepers
pré-ordenada na sequência do board**. Populados **Team 3 (10 keepers, $148)**, **Team 4 (8, $95)** e
**Team 5 (6, $60)** — **todos os totais conferindo**.

**Objetivo duplo — um resultado e uma perda:** o runbook corrigido **foi validado** (o fluxo real
descrito no `MAN-OFF26-10-11-REG` levou o agente ao fim três vezes, sem redescoberta de caminho);
a **medição de tempo foi perdida** por instabilidade de ambiente (ver bloco próprio abaixo).

##### ⛔ FALSO ACHADO — NÃO APLICAR: "rebaixar o check anti-homônimo"

> **Este é o registro mais importante desta entrada.** O relatório do Cowork **recomenda enfraquecer
> uma proteção**, e a recomendação **está errada**.

**O que o relatório diz:** que a sigla do time NFL exibida pelo Sleeper **diverge** da keeper sheet
(observado: **Waddle exibido como DEN**, **Hill sem sigla**), e que portanto o check anti-homônimo
da §B.3 deveria ser rebaixado.

**Por que está errado:** a causa foi a **lista de teste**, montada manualmente pelo owner-side com
**times de temporadas anteriores**. É **dado velho na lista**, não divergência da plataforma. Na
execução **real**, a keeper sheet sai do **Manager**, que **sincroniza do Sleeper** — os dois lados
**bebem da mesma fonte** e a sigla **bate**.

**A orientação correta é a INVERSA da recomendada:** se a sigla divergir na execução real, isso é
**sinal de problema no sync ou na sheet** → **parar e reportar**, não seguir em frente. Uma
divergência de sigla é **sintoma**, não ruído.

**Decisão registrada: o check anti-homônimo da §B.3 permanece INALTERADO**, sem nenhum
enfraquecimento. Nada foi aplicado no runbook a partir desta recomendação.

**Nota de método (família [[MAN-METH-REG]]):** *recomendação de melhoria vinda de execução com
**dados sintéticos** precisa ser conferida contra a **origem do dado** antes de virar correção de
documento.* Sem essa conferência, **uma proteção teria sido enfraquecida na véspera do uso real por
artefato de teste** — e o enfraquecimento pareceria justificado, porque a observação era verdadeira
(a sigla **de fato** divergiu). O erro não estava no que se viu; estava em **de onde o dado vinha**.

##### 5 correções aplicadas ao runbook

1. **Identificação de coluna com times placeholder — os DOIS estados.** Enquanto os times não
   tiverem donos reais, os cabeçalhos das colunas são **avatares vazios, sem rótulo de texto** — não
   há "Team N" escrito em lugar nenhum. A verificação canônica nesse estado é o **menu de contexto
   da célula**, que exibe *"Manually set a player for Team N"*. A orientação anterior ("identifique
   pelo owner") **pressupõe rótulos que só existirão quando os owners reais entrarem**.
2. **Reescala do board após a primeira interação.** O board **desloca/reescala**, o que **quebra
   referência posicional**. Mitigação observada: revelar **FLEX/K/DEF pela seta ▼ antes** de mirar
   as linhas de baixo, e **confirmar o time pelo menu de contexto antes de cada designação**.
3. **Atribuição de vaga é POR POSIÇÃO.** Escolher o jogador o coloca na vaga correta
   automaticamente (um **RB entra no FLEX** quando as vagas de RB estão cheias). **Clicar a célula
   exata é conveniência, não obrigação** — reduz a criticidade do item 2.
4. **O campo de preço nasce em `$1` SEMPRE**, inclusive quando o `$PROJ` é maior. **Regra
   generalizada:** vale para **qualquer keeper de $1**, não só K/DEF (o registro anterior sugeria
   escopo menor).
5. **Filtro de posição para K/DEF confirmado como mais rápido**, com propriedade útil descoberta:
   kickers e defesas **já designados somem do filtro** → "pegar o primeiro disponível" é **limpo e
   sem colisão**.

##### Ganho da lista ordenada — validado qualitativamente

A lista pré-ordenada na sequência do board **eliminou busca, deliberação e navegação**; a execução
virou **descida linha a linha**. **6 dos 24 keepers dispensaram edição de preço** (keepers de $1).
→ **Vira melhoria concreta do [[OFF26-2]]** (ordenar a sheet na sequência do board, marcando os de
$1), registrada lá **sem implementação**.

##### ⚠️ Medição PERDIDA + risco de variância de ambiente

**Tempos de relógio:** Team 3 = **26min52s** (10 keepers) · Team 4 = **14min13s** (8) · Team 5 =
**13min58s** (6) · **total 58min26s**. **Estes números NÃO medem o procedimento:** o ambiente do
Cowork acumulou **dezenas de timeouts de captura de tela, de 30 s cada**, que **dominam o relógio**.

**Evidência de que o gargalo é o ambiente, não o método:**
- o **Team 4 foi mais rápido por jogador que o Team 3**, e o **Team 5 voltou a subir** — por
  **concentração de timeouts**, não por regressão de fluxo (a curva de aprendizado não sobe);
- a execução **anterior**, no **mesmo dia**, **sem** runbook corrigido e **sem** lista ordenada,
  rendeu **~75 s/jogador**. **Nenhuma explicação plausível sustenta que corrigir o documento e
  pré-ordenar a lista tenha tornado o trabalho mais lento.**

**Risco operacional registrado:** as duas execuções rodaram **no mesmo ambiente**, com resultados
**muito diferentes** e **sem causa identificada**. A instabilidade é **imprevisível**. Projeção por
ritmo de regime: **~2 h para 12 times**; numa execução degradada como a segunda, **~5 h** — e **não
há como saber qual será antes de começar**.

**Mitigação registrada: fatiar a transcrição POR TIME**, cada um uma **unidade verificável** — se a
sessão degradar, a seguinte **retoma do time seguinte sem refazer nada**. É a mitigação certa
justamente porque o modo de falha é *lentidão*, não *erro*: o trabalho já feito permanece válido.

##### Efeito sobre a decisão Cowork-2026 / script-2027 — reconsideração PARCIAL, em aberto

- **A decisão vigente NÃO muda:** 2026 roda **via Cowork**.
- **O argumento original do script segue caído:** "não cabe na janela de 48 h" — o **tempo médio
  cabe**.
- **Mas surge um argumento NOVO, de natureza diferente: VARIÂNCIA.** O script determinístico **não
  tem esse modo de falha**. O risco deixou de ser "demora demais" e passou a ser "**não dá para
  prever quanto demora**" — e é a imprevisibilidade, não a duração, que ameaça uma janela de 48 h.
- **Contra-argumentos preservados (seguem válidos):** **fragilidade de seletores** (script que
  dirige UI quebra com mudança de front-end — e a UI **já mudou uma vez** entre junho e agosto);
  **competição por prazo** com [[OFF26-4]] e [[OFF26-11]], que estão no caminho crítico; e
  **estreia no dia do uso** como pior cenário possível.
- **Status: reconsideração parcial ABERTA.** Não arbitrada aqui.


---

### OFF26-6 — PoC de viabilidade do Cowork montando a liga fantasma
✅ **17/06/2026 — PoC executado em liga de teste descartável; mecânica central validada +
decisões de design arbitradas** — MAN-OFF26-6-7-REG/PoC — Prioridade **Alta** — **validação
operacional (NÃO é código do Manager)** — **GATE PASSOU**

> **Critério de ✅:** validação operacional com resultado documentado — **sem código, sem smoke
> prod aplicável** (a prova é o experimento na UI do Sleeper, registrado abaixo).

**Descrição:** prova de conceito, em liga de **teste descartável** e com antecedência,
de que **Cowork + Claude in Chrome** conseguem, dirigindo a UI do Sleeper, montar a liga
fantasma de ponta a ponta: **criar sala → popular 12 times → configurar draft auction →
setar keepers como rosters + budgets**. Produz um **roteiro de experimento** + **registro
estruturado do resultado** (onde o procedimento trava, que intervenção manual exige).

**Motivação:** a API do Sleeper é **read-only** — a montagem só é possível dirigindo a UI
pelo navegador, frágil por natureza e **nunca validada**. O runbook OFF26-5 já documenta
esse procedimento **assumindo que ele funciona**; falta o passo anterior, que prova **SE e
COMO** funciona. É premissa não testada no **caminho crítico** (a FA auction real depende
dela).

**Escopo resumido:** roteiro do experimento (passos da montagem na UI) + execução numa liga
de teste com **dados fake** (não precisa da keeper sheet real) + registro estruturado do
resultado (sucesso/trava por etapa, intervenções manuais necessárias). Testa a **mecânica
pura** da montagem, isolada das demais peças.

**Função de GATE:** deve **passar antes** de confiar a FA auction real ao procedimento Cowork.

**Dependências:** nenhuma para rodar (testa a mecânica isolada, dados fake). **Relação com
OFF26-5:** o resultado do PoC é o **insumo** do runbook (o runbook documenta o caminho
**comprovado** pelo PoC). **Relação com OFF26-7:** é um **subconjunto** dele (a etapa "Cowork
monta a liga" dentro do ensaio E2E maior).

#### Resultado do PoC (MAN-OFF26-6-PoC, 17/06/2026) — ✅ GATE passou

PoC executado pelo owner em **liga de teste descartável**. A **mecânica central foi validada**
e emergiram **decisões de design** que reformulam a estratégia da liga fantasma. Sem código.

**(a) Validado (Cowork + Claude in Chrome dirige a UI sozinho):**
- **Cria a liga no Sleeper** via wizard: Fantasy Football → nome → 12 times → Redraft →
  **Auction no Step 4**.
- **Seta keeper com salário**, descobrindo o mecanismo sozinho: Settings → Draft Settings →
  **"SET KEEPERS/DYNASTY PLAYERS"** → SET PLAYERS → draft board → slot do time → Set Player →
  busca jogador → define salário → **SET PLAYER**.
  > **⚠️ Anexo (02/08/2026 — MAN-OFF26-10-11-REG):** este **caminho não existe mais** na UI atual.
  > A transcrição real de 02/08 mostrou que o board **já está em modo de designação** no pré-draft —
  > clica-se **direto na célula vazia** → menu → **Set Player**. O registro acima é **preservado como
  > estado da UI em 17/06/2026**; o caminho vigente está no `runbook_cowork_liga_fantasma.md`
  > (corrigido) e na seção do [[OFF26-5]]. **A conclusão do PoC — o Cowork consegue designar keeper
  > com salário sozinho — permanece válida e agora está confirmada em escala** (10 keepers
  > cronometrados).
- **Confere nome completo + time NFL antes de adicionar** (comportamento anti-homônimo;
  ex.: Mahomes QB-KC, Bijan RB-ATL confirmados) — mesma higiene da classe "Brown" na camada de
  operação manual.

**(b) Decisões de design (arbitradas pelo owner a partir do PoC):**
- **Liga fantasma passa a ser PERMANENTE** (redraft fixa, com os 12 owners reais dentro), **não
  recriada a cada ano**. Motivo empírico: times **sem dono** (placeholders) **não são
  renomeáveis/gerenciáveis** pela UI — bloqueio observado no PoC. Liga permanente com owners
  reais elimina o bloqueio.
- **Reset de roster NÃO é trabalho do Cowork:** o formato **redraft reseta rosters
  automaticamente** na virada de season. O trabalho **anual** do Cowork = **apenas popular o
  pré-draft com os keepers**.
- **Config de roster da liga fantasma DEVE espelhar a liga real:** **1QB, 2RB, 3WR, 1TE, 1 FLEX
  (RB/WR/TE), 1DEF, 1K** (+ banco/IR conforme a liga real). Achado: a liga de teste nasceu com
  **2 WR** (padrão Sleeper) ≠ **3 WR** da liga real — **config exata é requisito**.
- **Mapeamento owner↔time ancorado em `sleeper_owner_id`** (chave canônica), **NUNCA no nome do
  time** (mutável). Mesma família de risco do "Brown" (id canônico vs. nome), aplicada à camada
  de **owner**.

**(c) Achados técnicos (impacto a jusante — ver [[OFF26-4]] / [[OFF26-5]] / [[OFF26-8]]):**
- **"Salary cap" no Sleeper não é toggle separado:** é o **budget do auction** (Draft Settings →
  Budget, **$200 global**). O cap individual **emerge** dos salários dos keepers consumindo o
  budget global.
- **Cap restante por time só é visível AO VIVO durante o auction;** no estado pré-draft **não há
  número de budget restante na tela**. → **Impacto [[OFF26-4]]:** a auditoria deve **CALCULAR**
  (`$200 − Σ salários dos keepers`), **não ler** um número pronto da liga fantasma.
- **Keepers ficam como designação de board no pré-draft;** só **populam o roster quando o draft
  roda**. → **Impacto [[OFF26-4]]:** a auditoria lê **designações de keeper**, não o roster.
- **Ponte de identidade de OWNER já existe no Manager:** `Team.sleeper_owner_id` (populado pelo
  Sleeper sync; vínculo **M12** ✅). → **Impacto [[OFF26-4]]:** a ponte de **owner está
  resolvida**; resta investigar na F1 **apenas a ponte de JOGADOR** (se
  `/api/cuts/keeper_sheet` expõe `sleeper_player_id`).

**Cross-refs de desfecho:**
- **[[OFF26-4]]** (auditoria de keepers pré-leilão): a auditoria **calcula** o budget (não lê),
  **lê designações de keeper** (não roster); **ponte de owner resolvida** via `sleeper_owner_id`;
  **resta a ponte de jogador** (escopo da F1 do OFF26-4).
- **[[OFF26-5]]** (runbook): documentar o caminho **comprovado** acima — incl. a config de roster
  espelhando a real (3 WR etc.), o modelo de **liga permanente** e o trabalho anual reduzido a
  **popular keepers no pré-draft**.
- **[[OFF26-8]]** (Cowork aplica cortes no Sleeper): mesma natureza operacional (dirigir a UI);
  o anti-homônimo (nome+time NFL) validado aqui vale para a aplicação de cortes.

**Status:** ✅ — GATE de viabilidade **passou** (a FA auction real pode ser confiada ao
procedimento Cowork, observadas as decisões de design acima). Sem smoke prod aplicável (a prova
é o experimento operacional registrado).

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

---

### UX12 — Busca de jogador + página de perfil enriquecida
✅ **ROTEADO 08/08/2026 (MAN-UX12-REFINE)** — **despachado em [[M10]] (busca) e [[O2]] (perfil)
— roteamento (b), decisão do owner.** O item não tem escopo próprio remanescente: os campos 2 e
5 foram absorvidos pelo O2 (refinado in-place na mesma sessão), os campos 1/6 já eram do O2, os
campos 3/4/7 **já existem** na página atual (achado da F1), e a busca já era o M10. Esta seção
(registro + diagnose F1, a evidência do roteamento) migra ao archive conforme [[O3]].
Histórico: **Registrado 08/08/2026 (MAN-UX12-REG)**, Prioridade Média; **F1 concluída
08/08/2026 (MAN-UX12-F1**, read-only — diagnose absorvida no fim desta seção)

**Origem:** pedido do **co-admin Michel**, trazido pelo owner. Michel é quem faz o smoke das
features user-facing, e o pedido nasce de uso, não de leitura de código.

**Sintoma (dois, e o segundo só aparece depois de resolver o primeiro):**

1. **Não existe caminho de busca.** A única forma de chegar a um jogador é **clicá-lo dentro da
   página de um time** — ou seja, é preciso **já saber em que franquia ele está** para conseguir
   abri-lo. Quem não sabe, abre os 12 rosters procurando visualmente.
2. **A página que abre não tem o que a liga precisa** para avaliar o jogador. Ela existe (é a
   `/player/<id>` do [[M13]] ✅) e mostra contrato + histórico de salário + "Propor Trade", mas o
   conjunto de informações que se usa numa avaliação está espalhado por outras telas ou fora do
   Manager.

**Por que Média e sem prazo:** não é bug de dado, não corrompe nada e **não está no caminho crítico
de 24/08** (FA auction). É custo de navegação e de leitura, pago por toda a liga a cada avaliação
de jogador.

#### Escopo funcional pedido

**Busca:** encontrar qualquer jogador da liga **pelo nome**, sem precisar navegar por times.

**Perfil do jogador**, exibindo:

| # | Campo | Observação de registro (não é decisão de implementação) |
|---|-------|---------------------------------------------------------|
| 1 | **Time na NFL** e **time na liga** (franquia do Dynasty SB) | o dono na liga já aparece hoje; o time NFL é justamente o dado do [[UX11]] e do [[O2]] |
| 2 | **Link p/ a página do time dele na liga** | destino existe (`/team/<id>`, [[L1]]) |
| 3 | **Link p/ trade com o time dele já pré-selecionado** | o [[M14]] ✅ fez `/trades` aceitar `team_a`/`team_b` por query param; a F1 confere se o botão atual do [[M13]] já faz isso ou se pré-seleciona só um lado |
| 4 | **Cap hit atual** (contrato/salário) | ⚠️ a régua de folha é única e **o IR conta** ([[OFF26-16]]) — o que se exibe é o salário do jogador, sem inventar variante |
| 5 | **Idade** | ⚠️ **não se sabe se o Manager persiste isso hoje** — ver questão 2 |
| 6 | **Roster depth no time da NFL** (posição no depth chart) | ⚠️ mesma dúvida de disponibilidade — ver questão 2 |
| 7 | **Histórico dele na liga** (eventos de `PlayerHistory`: trades, cortes, aquisições) | o dado existe e é auditável por desenho; o [[S4]] 🔲 registra que `PlayerHistory` identifica time **só por nome** — a F1 lê isso antes de desenhar a exibição |

#### ⚠️ Questão 0 (resolver ANTES das outras): isto já está registrado em dois itens

**Esta é a primeira coisa que a F1 tem de resolver, e não está arbitrada aqui.** O escopo pedido
pelo Michel atravessa dois itens 🔲 que já existem no backlog:

- **[[M10]] 🔲 Média — "Busca de Jogador: Global + Calculadora"** é **a busca**, já refinada em
  28/04/2026 com o levantamento feito: o endpoint **já existe** (`GET /api/player/search`), os 5
  entry points atuais estão mapeados, o caso de uso registrado lá ("owner queria ver o contrato do
  Mahomes e teria que abrir os 12 rosters") é **o mesmo sintoma** que o Michel relata agora.
- **[[O2]] 🔲 Média — "Enriquecer página do jogador"** é **o perfil**, e já inclui nominalmente
  **time NFL no header** e **depth chart NFL** (campos 1 e 6 acima), além de stats/ADP/schedule.

Ou seja: **os campos 1 e 6 e a busca inteira já têm dono**; o que o UX12 traz de novo é a
**demanda de um segundo usuário** (validação independente da prioridade), o **agrupamento como uma
experiência só** e os campos **2, 3, 5 e 7** (links de time/trade, idade, histórico da liga).

**Três roteamentos possíveis, nenhum escolhido:** (a) UX12 vira o **guarda-chuva** e M10/O2 são
absorvidos; (b) UX12 é **despachado** — busca → M10, perfil → O2 — e o item fecha como registro de
demanda; (c) UX12 fica só com **o que sobra** (2, 3, 5, 7) e depende dos outros dois. ⛔ **Não
implementar em paralelo a M10/O2** — seria a enésima réplica, exatamente o que as últimas sessões
vêm fechando. O precedente do próprio M10 (refinado in-place, ID preservado, [[UX4]] consolidado
no O2 em vez de duplicado) é a referência de método.

#### Questões abertas para a F1

1. **Réplica de fonte (obrigatória).** A exibição de **time do jogador** — NFL e liga — tem **fonte
   comum**, ou **cada tela deriva a sua**? É a mesma pergunta central do [[UX11]], e a F1 do UX12
   pode **absorver o UX11** ou **despachá-lo** (registrar a relação explicitamente, dos dois lados).
   Se cada tela deriva, acrescentar o perfil como mais um consumidor **piora** o problema.
2. **Disponibilidade do dado.** O sync com o Sleeper **persiste hoje algum campo de depth chart**?
   (O [[O2]] afirma que `depth_chart_order` está no players cache e já é consumido — a F1 **confere**
   em vez de herdar a afirmação.) Mesma pergunta para **idade**/data de nascimento. Se não persiste:
   **qual o custo de passar a persistir × derivar em tempo de leitura** (o cache tem ~15 MB e vive
   fora do git, `.sleeper_players_cache.json` — ver [[F13]]).
3. **Página nova × enriquecer a existente.** A `/player/<id>` atual ([[M13]] ✅) **vira** o perfil
   enriquecido, ou nasce página nova e a atual é aposentada? Há **links internos apontando para a
   atual** que precisariam seguir funcionando (o helper `renderPlayerNameLink` em `base.html` é
   reusado por várias telas — o M10 lista os sítios).
4. **Busca: superfície e resolução de identidade.** Barra global na navbar × página dedicada de
   busca (o M10 já desenhou o caminho da navbar, incluindo o comportamento mobile). E como resolver
   **homônimos e nomes parciais**: ⛔ **exibição pode usar nome, resolução de identidade é por
   `sleeper_player_id`** — precedente do incidente **Brown** (`player_lookup.py` é estrito de
   propósito e **não serve** para autocomplete, como o próprio M10 já registrou).
5. **Foto do jogador.** Se o perfil exibir foto, **herda o problema do [[UX10]]** (fotos de
   temporada anterior, causa não diagnosticada). Cross-ref registrado **sem acoplar os itens**: o
   UX12 não deve esperar o UX10, e o UX10 não vira pré-requisito.

**Cross-refs:** [[M10]] (a busca — sobreposição direta), [[O2]] (o perfil — sobreposição direta),
[[M13]] ✅ (a página que existe hoje) e [[M14]] ✅ (query params de `/trades`, que o campo 3 usa),
[[L1]] ✅ (a página de time, destino do campo 2), [[UX11]] (a mesma pergunta de réplica de fonte),
[[UX10]] (foto, se entrar), [[S4]] 🔲 (`PlayerHistory` identifica time por nome — relevante ao
campo 7), [[OFF26-16]] (régua única de folha — o cap hit exibido não pode virar uma sétima
definição).

#### F1 — diagnose read-only (MAN-UX12-F1, 08/08/2026)

Toda evidência é do código no HEAD (`571be2f` + working tree) e de arquivos locais; **zero
chamada externa nova** (a régua do prompt) — o campo do cache foi conferido lendo o próprio
`.sleeper_players_cache.json` local (carimbo `fetched_at` 31/07/2026, 12.204 entradas).

##### Q0 — Roteamento. Recomendação: **(b) despachar** — busca → M10, perfil → O2 (absorvendo campos 2 e 5); UX12 fecha como registro de demanda

**O levantamento de 28/04 do M10 vale INTEIRO hoje:** o endpoint sobreviveu
(`GET /api/player/search` em `routes/roster.py:323-337` — mesma assinatura: `ilike` substring,
`is_dropped=False`, limit 20, `to_dict()`), e os entry points citados existem todos
(`roster.html:83,92` · `admin_review.html:43,77` · `salary_history.html:282` · `trades.html:313`
— só line drift de 1 linha no último). Nada da spec do M10 apodreceu.

**O O2 também tem F1 pronta — e mais completa do que a seção dele registra:** a diagnose
MAN-O2-F1 (28/04/2026) está consolidada no `handoff_code_manager_28_04_2026_pt2.md` (tabela de
disponibilidade por dimensão, endpoints Sleeper corrigidos **sem `/v1/`**, plano de 2 batches,
reuso mapeado). ⚠️ O handoff se declara "descartável após leitura" — **se o roteamento (b) for
aceito, absorver esse conteúdo na seção do O2 é parte do refinamento** (não feito agora: esta F1
não altera o texto do O2).

**O que muda o quadro — 3 dos 7 campos JÁ EXISTEM na página atual** (ver lista (a) abaixo):
campo 3 (o botão "⇄ Propor Trade" já navega com **os dois times pré-selecionados** via M14),
campo 4 (grid "Contrato e Valores" exibe salário/contrato/aquisição/ESPN/dynasty) e campo 7
(a Timeline já renderiza `PlayerHistory` completo, com trades clicáveis abrindo modal). O gap
real do perfil é: **metade do campo 1** (time NFL ausente do header — exatamente a dimensão 1 do
O2), **campo 2** (o nome do time da liga é `<strong>`, não link — `player_detail.html:26`),
**campo 5** (idade — em lugar nenhum) e **campo 6** (depth chart — dimensão 2 do O2).

**Custo comparado dos três roteamentos:**

| Roteamento | Duplicação | Rastreabilidade |
|---|---|---|
| (a) guarda-chuva UX12 | Zero, mas **funde dois entregáveis independentes** (a busca é shippável sem o perfil e vice-versa) e supersede duas F1s prontas | Perde a continuidade auditável do M10 (refinado in-place em 28/04 justamente para preservá-la) e do O2 (F1 consolidada + refutação da Opção D — "não absorver busca em O2" — **já registrada e ainda válida**) |
| **(b) despachar** ✅ | **Zero.** Busca → M10 **intacto** (já cobre tudo, inclusive o consumidor 2 — calculadora — que o UX12 nem menciona). Perfil → O2 **refinado in-place** absorvendo os campos 2 e 5 (duas adições triviais ao Batch 1) + Michel como 2ª origem de demanda | Melhor: cada ID mantém sua história; UX12 fecha como registro de demanda com ponteiros (precedente [[UX4]] → O2). A "experiência única" vira nota de sequência: M10 primeiro (gap de navegação), O2 depois — ordem que o próprio M10 já sugeria |
| (c) UX12 fica com o resto | Sobra **micro-item** (só campos 2 e 5, pois 3/4/7 já existem) | Pior: 3 itens interdependentes, sequenciamento forçado, o micro-item não se sustenta sozinho |

A refutação da Opção D registrada no M10 (critérios a/b/c de 27/04) **continua válida** e é
argumento contra o guarda-chuva: "navegar até a página" e "enriquecer a página" seguem sendo
verbos com fontes de dados distintas (DB local × Sleeper API/cache).

##### Q1 — Réplica de fonte: **o DADO tem fonte única; a EXIBIÇÃO é inline por tela mas lê sempre o mesmo campo** — e a resposta **resolve a F1 do [[UX11]]**

**Time do jogador (NFL): 1 fonte de dado, 8 sítios de exibição.** Fonte única:
`Player.nfl_team` (coluna, `models.py:143`), escrita **só** pelo sync
(`sync_sleeper.py:280-281`, a partir do pool do Sleeper) e exposta em `to_dict()`
(`models.py:190`). Sítios que exibem: `_macros.html:59` (macro `player_roster_row` → roster +
team_detail, **1 sítio serve 2 telas**), `admin_review.html:45,79`, `cap_projector.html:141,260`
(JS), `espn_review.html:55,104,120`. **Nenhum deriva time por conta própria** — todos leem a
mesma coluna. Veredito: **fonte-comum**; o medo "cada tela deriva a sua" está **refutado** para
este dado.

**Consequência direta para o [[UX11]]:** o quadro de trades busca
`/api/roster/by_name/<team>` → `to_dict()`, cujo payload **já contém `nfl_team`**
(`models.py:190`) — a tela simplesmente **não renderiza o campo** (`trades.html:303-318` mostra
posição/foto/nome/salário/contrato/dynasty). O fix do UX11 é **1 edição de template literal, sem
backend**. A pergunta central do UX11 ("fonte comum ou derivação por tela?") está respondida
aqui: **a F1 do UX11 pode ser dada por cumprida por referência a esta seção** (status/texto dele
não alterados — decisão do owner). Ressalva de staleness que passa a ser a única pendência real
do UX11: (i) o sync atualiza `nfl_team` só com valor truthy (`if nfl_team and ...`,
`sync_sleeper.py:280`) — **jogador que vira FA mantém o time antigo** (17 casos medidos em
28/04); (ii) o sync **não roda em todo boot** (DOC1) — frescor = último sync manual; (iii) o
pool tem TTL 168h (`PLAYER_CACHE_TTL_HOURS`, `sync_sleeper.py:30`).

**Foto de jogador: 2 construtores, deliberadamente espelhados, zero réplica inline.** Macro
server `player_photo` (`_macros.html:28-35`) + helper JS `renderPlayerPhoto`
(`base.html:275-281`), cada um documentando o outro como contraparte; **mesma URL**
`sleepercdn.com/content/nfl/players/thumb/<sleeper_player_id>.jpg`. Todos os usos passam por um
dos dois (conferido por grep; os `sleepercdn.com/avatars/…` restantes são **avatar de owner**,
família distinta, ~8 sítios inline — fora do escopo de foto de jogador). **Achado lateral para o
[[UX10]], registrado sem mexer no item:** a URL **não tem componente de temporada nem de time**
— é keyed **só** por `sleeper_player_id`. As hipóteses (b) e (c) do UX10 ficam **sem mecanismo
no lado do Manager**; sobra a (a) — o próprio CDN do Sleeper servindo thumb velho — que não é
corrigível por construção de URL. A F1 do UX10, quando rodar, parte daqui.

**Nome+identidade: 2 helpers + 6 réplicas inline de link.** Helpers: macro `player_name_link`
(`_macros.html:16-22`) e JS `renderPlayerNameLink` (`base.html:261-269`). Réplicas inline que
constroem o link manualmente: `admin_review.html:43,77`, `roster.html:83,92`,
`salary_history.html:282`, `trades.html:313`. Todas apontam para a mesma rota com o **id local**
do Player (estável; `sleeper_player_id` segue sendo a identidade de sync — precedente Brown
respeitado). Nome exibido = `Player.name`, coluna única atualizada pelo sync.

##### Q2 — Depth chart: **o sync NÃO persiste; o pool que ele já baixa TEM o dado; e persistir coluna não bastaria**

**Grep no repo: zero consumo de `depth_chart*` em código de produção** — a afirmação do O2 de
que o campo é "já consumido pela aplicação" é **falsa** (ver lista (a)). Mas o dado **existe no
payload que o sync já consome**: conferido no cache local (31/07) — `depth_chart_order` +
`depth_chart_position` presentes em **75%** dos skill players com time NFL (bate com a medição
de 28/04: QB 73% · RB 71% · WR 62% · TE 64% · K 74% · **DEF 0%**), `age` e `birth_date` em
**94%**.

**O ponto que decide o desenho:** o campo 6 pede o depth chart **do time NFL** — os rivais de
posição do jogador, que em geral **não são Players do DB local** (~280 rosterados vs. 12.204 no
pool). **Persistir `depth_chart_order` como coluna do Player não montaria o depth chart** — os
companheiros de posição não estão no banco. O único caminho completo é **derivar em leitura do
pool** (`_load_players_db()`, `sync_sleeper.py:68` — leitor já existente; o MAN-O2-F1 já
desenhou o helper `_get_depth_chart(team, position, players_db, exclude_sid)`). Staleness desse
caminho: TTL 168h do cache — stale conhecido em janela de trades NFL (out–nov), observação 1 do
handoff. **Idade é o caso oposto:** `birth_date` é **imutável** — persistir no sync teria custo
de migração mas **zero staleness**; derivar em leitura do pool custa zero schema com a mesma
TTL. Escolha é da fase de design, os dois caminhos são viáveis.

##### Q3 — Histórico × [[S4]]: **pode nascer exibindo como está; acoplamento novo = zero**

O perfil **já exibe** o histórico: a Timeline consome `GET /api/player/<id>/history`
(`roster.py:264-320`), que ordena `PlayerHistory` por cronologia Sleeper e formata PT-BR via
`_format_event_display` — o qual resolve contraparte de trade comparando **strings de nome**
(`trade.team_a == h.team_name`, `roster.py:243-246`: exatamente o sítio que o S4 cita). Exibir
isso no perfil **não cria dependência nova** — é o mesmo endpoint e o mesmo formatador já em
produção; nome funciona como **snapshot de exibição** (compatível com o precedente Brown). O
risco do S4 é de **escrita** (dedupe/idempotência pós-rename no índice UNIQUE que contém
`team_name`, `models.py:803`), não de leitura — um rename quebraria a contraparte exibida
igualmente na página atual e no salary_history; o perfil não piora nem melhora isso.

##### Q4 — Cap hit: **fonte canônica é `Player.salary` (hit individual) e `Team.total_salary()` (folha)** — e a página atual já lê a certa

O hit individual do jogador é a coluna `Player.salary`, que a página **já exibe**
(`player_detail.html:52`). Se o perfil vier a exibir contexto de folha do time, a fonte é
`Team.total_salary()` → `salary_engine.roster_salary` (OFF26-16 — inclui IR; é o que
`roster.py:93` usa). ⛔ Nenhuma soma nova, nenhum filtro de IR. Não há o que desenhar aqui: a
guarda do registro está satisfeita por leitura das fontes existentes.

##### Q5 — Página nova × existente: **enriquecer a existente; 2 helpers + 6 inline apontam para ela**

Mapa completo dos links internos para `/player/<id>` (rota `roster.player_detail`,
`roster.py:357`): via macro `player_name_link` — rows de roster/team_detail
(`player_roster_row`) e `trade_proposal.html:92,115`; via JS `renderPlayerNameLink` —
`admin.html:330`, `cap_projector.html:137`, `_trade_detail_modal.html:69`; inline — os 6 sítios
listados na Q1. **Enriquecer a página atual custa zero nos links** (nenhum sítio muda); página
nova exigiria redirect na rota velha e re-apontar 2 helpers + 6 inlines sem ganho identificado —
o O2 já parte da premissa "mesma página alvo". Não há evidência que sustente página nova.

##### Listas da regra [[MAN-METH-REG]] (F1 de consumo de infra existente)

**(a) Premissas do registro que o código contradiz:**

1. **"a página que abre não tem as informações que a liga precisa" — parcialmente falsa.**
   Campos 3, 4 e 7 **já existem** na página atual: o botão de trade pré-seleciona **os dois
   times** (`player_detail.html:36-43`, gated por `can_propose_trade` — só aparece se o user tem
   time e o jogador é de outro; para jogador do próprio time não há botão, coerente), o grid de
   contrato exibe o cap hit, e a Timeline exibe o `PlayerHistory` completo com trades clicáveis.
   O gap verdadeiro: metade do campo 1 (NFL no header), 2, 5 e 6. **Parecer: premissa
   parcialmente falsa** — reduz o escopo novo do perfil a 4 adições, 2 delas já no O2.
2. **Afirmação herdada do O2 ("depth_chart_order já é consumido pela aplicação") — falsa.**
   Zero consumo em produção (grep). O campo está no **cache**, não no código. O registro do
   UX12 mandava conferir em vez de herdar — conferido, e a seção do O2 fica com a correção
   pendente para o refinamento do roteamento (b). **Parecer: premissa falsa (do O2), sem dano**
   — a viabilidade se mantém, o verbo muda de "reusar consumo" para "criar o primeiro consumo".
3. **"réplica de fonte" como risco central — refutada para time e para foto.** Time: fonte
   única + exibições inline do mesmo campo (Q1). Foto: 2 construtores espelhados por desenho.
   A réplica real que existe é a de **links de nome** (6 inlines ao lado de 2 helpers) —
   cosmética, não de dado. **Parecer: premissa falsa no grau** — o risco temido não se
   materializa neste domínio.

**(b) Campos/comportamentos existentes hoje que o escopo proposto omite:**

1. **Dynasty value (FC)** — exibido no grid atual (`player_detail.html:70-79`, resolvido no
   backend/E3). Ausente dos 7 campos. **Parecer: perda não-intencional se houvesse página nova;
   com o roteamento (b) e enriquecimento in-place, não-issue** (permanece).
2. **ESPN ref value, início de contrato, tipo de aquisição, badges IR/Dropado** — idem: já na
   página, fora dos 7 campos. **Parecer: deslocamento** — o pedido do Michel lista o que falta,
   não re-especifica o que existe; nada a remover.
3. **Trades clicáveis na Timeline** (modal `_trade_detail_modal`) — o campo 7 pede "histórico";
   a página já entrega histórico **com drill-down**. **Parecer: deslocamento** — comportamento
   preservado por construção no enriquecimento in-place.
4. **Consumidor 2 do M10 (autocomplete da calculadora)** — a busca do UX12 não o menciona.
   **Parecer: omissão que vira argumento do roteamento (b)** — um guarda-chuva UX12 que
   absorvesse o M10 tenderia a perder esse consumidor; despachando, ele fica onde sempre esteve.

---

---

### M10 — Busca de Jogador: Global + Calculadora
✅ **CONCLUÍDO 10/08/2026 (MAN-M10-F2 → MAN-ARC-BUSCA-DONE; gate [[PROC1]] cumprido — hash
`20b346b` live confirmado pelo owner)** — Prioridade **Média** — spec refinada em 28/04/2026
(MAN-M10-REFINE), conferida viva pela MAN-UX12-F1 e executada sem redesenho

**Smoke de produção aprovado (owner, 10/08/2026):** o caso âncora de 28/04 **morreu em prod** —
"Mahomes" resolve da navbar direto ao perfil, zero rosters abertos; homônimos distinguíveis na
lista (posição + time NFL + franquia); autocomplete da calculadora funcional preenchendo os 3
campos. **Validação do solicitante: Michel** (o pedido do [[UX12]] que virou a demanda dupla)
conferiu e aprovou a busca. A extensão de universo (FAs marcados) validada junto vive no [[M21]],
fatia A.

#### F2 — entregue (MAN-M10-F2, 10/08/2026)

Os **dois consumidores** da spec estão no ar sobre **uma engrenagem só** — `createPlayerSearch`
em `templates/base.html`, com dois modos:

- **Consumidor 1 — busca global.** Barra na navbar **desktop** (o slot vazio entre `.nav-links` e
  `.nav-right`, como a spec desenhou) e **section no topo do overlay mobile**, acima de
  "Navegação" (padrão N1 preservado). Modo **navegação**: cada resultado é um `<a href="/player/
  <id>">` de verdade — ctrl+clique e clique do meio funcionam, e o destino é o `id`.
- **Consumidor 2 — autocomplete da calculadora.** Modo **seleção** (`onSelect`): preenche
  **ESPN ref value, ano de contrato e tipo de aquisição**, exatamente os 3 campos da spec, e
  mostra um hint com o jogador escolhido (linkado para o perfil).

**Identidade — a régua que governa a tela** (mesma do `player_lookup`, mesmo precedente Brown):
o `ilike` do backend produz **sugestão exibida**, nunca resolução. Cada linha traz **posição +
time NFL + franquia**, que é o que separa um homônimo do outro; a resolução é **sempre ato
explícito** — clique, ou seta + Enter. ⛔ **Enter sem item destacado não seleciona nada** (não
existe "vai no primeiro resultado"), e nada resolve por nome em lugar nenhum do caminho.
`player_lookup.find_player_by_name` **não** foi tocado nem chamado — segue sendo a reconciliação
estrita dos imports.

**Backend: reusado, com 3 ajustes** (a spec previa "ajustes opcionais"; assinatura, filtro
`is_dropped=False` e teto de 20 **preservados**):
1. **`Player.to_search_dict()`** (12 campos) — `to_dict()` invocava `is_renewal_candidate()` +
   `project_next_salary()` por jogador: **20 projeções de contrato por tecla digitada** para
   exibir 4 campos. Era a otimização que as "Notas para F1" deixaram condicional; o custo de
   criar o método é uma dúzia de linhas.
2. **Ordenação prefixo-primeiro**, depois alfabética. Sem `order_by` o teto de 20 cortava em
   ordem arbitrária de tabela — em liga cheia, "moore" podia devolver 20 linhas **sem o Moore**.
3. **Escape dos curingas do LIKE** — `%` e `_` digitados são texto. Sem isso, `%` sozinho
   devolvia o elenco inteiro como se fosse "resultado da busca".

**Decisões das questões que a spec delegou à F2:**
- **Breakpoint:** reusa o **768px** que a navbar já usa (⛔ nenhum breakpoint novo). Acima, barra
  inline; abaixo, `.nav-search { display: none }` e a busca vive no overlay.
- **Dropdown no mobile:** **fluxo normal** (`.ps-dropdown-inline`, `position: static`) — empurra o
  painel em vez de flutuar sobre ele; num `aside` que já rola, dropdown absoluto vaza.
- **Renderização do resultado:** link montado no componente, **não** `renderPlayerNameLink` — a
  linha inteira é o `<a>` e âncora aninhada é HTML inválido. O mesmo destino (`/player/<id>`) e a
  foto vêm do **`renderPlayerPhoto` já existente** (keyed por `sleeper_player_id`), as fontes
  comuns mapeadas na Q1 da UX12-F1; **nenhuma derivação nova por tela**.
- **Batching:** os 2 consumidores numa camada só — o custo do segundo, com o componente pronto,
  foi o `onSelect`.

⚠️ **A conversão que era fácil de errar:** o campo "ESPN Ref Value (PPR)" da calculadora é
**RAW** (o `×1.2` acontece em `routes/salary.py`), e `Player.espn_ref_value` guarda o
**ajustado** — o autofill **divide por 1.2**. Sem isso o valor entraria ajustado, seria
multiplicado de novo e **inflaria a tabela de contrato inteira**. ⛔ **"Valor Pago no Ano 1" não
é preenchido**: o banco tem o salário **corrente**, não o do ano 1; preenchê-lo produziria uma
tabela plausível e falsa.

**Testes — `player_search_test.py` (27):** escape do LIKE (núcleo puro) · endpoint contra ORM em
memória (âncora Mahomes; **dois DJ Moore com ids e sids distintos**, distinguíveis por
posição+time; prefixo antes de substring; dropado fora; filtro por time; vazio gracioso; curinga;
teto de 20; payload enxuto sem projeção) · **guardas estáticas de identidade** (engrenagem única,
Enter sem destaque não escolhe, navegação por `id`, a busca não chama `player_lookup`, a
calculadora não inventa o ano 1 e converte o ESPN, escape de HTML sem réplica).

**Smoke local (GET-only, test client logado, cópia do DB):**
- **"Mahomes" → 1 resultado**, com link direto ao perfil: **o caso âncora de 28/04 morre** (zero
  rosters abertos).
- **"brown" → 5 resultados** (A.J. Brown, Amon-Ra St. Brown, Chase Brown, Cleveland Browns DEF,
  Hollywood Brown), cada um com posição/time/franquia e **id próprio** — o incidente Brown vira
  uma **lista para o usuário escolher**, que é exatamente o comportamento pedido. De carona, dois
  casos-limite reais renderizam sem erro: DEF com `sleeper_player_id` **sigla** ("CLE") e jogador
  **sem sid** (Hollywood Brown → sem foto, silenciosamente).
- Inexistente, `%` e `_` → **lista vazia**, sem erro. As 3 páginas conferidas (`/`, `/salary`,
  `/salary_history`) trazem os 3 entry points.
- **Componente exercido em DOM headless** (harness descartável em node): debounce de 1 request,
  `<2` caracteres não busca, os 2 homônimos com hrefs diferentes, Enter sem destaque **não**
  navega, seta+Enter navega para o id certo, Escape fecha, modo seleção não vira link, e a
  conversão 68.4 → 57.

⚠️ **O que NÃO foi exercido, e é o smoke do owner:** a **interação em navegador** (aparência do
dropdown, foco/teclado reais, overlay mobile em tela pequena). E o caso literal **"dois DJ Moore"
com dado real é inexercível**: só o WR do BUF está rosterado, e a busca é do **DB local** — por
desenho da spec, que o separou da fonte do [[O2]] (pool). O cenário existe nos testes e no
harness; em produção, o análogo real é o "brown".

**Suítes:** 27 novos + 54 (salary_engine) + 34 + 25 + 36 + 64 + 22 + 14 + 19 — todas verdes.
Zero schema, zero toque em folha/cap/sync e **zero mudança na página de perfil** (a busca leva
até ela; quem a enriquece é o [[O2]]).

---

#### Spec autoritativa (MAN-M10-REFINE, 28/04/2026) — origem, preservada

> ⚠️ Texto de 28/04 mantido **verbatim** como origem do escopo; a F2 acima é o que está no
> código. Onde os dois divergem, vale a F2 — em especial o payload do endpoint, que **deixou de
> ser `to_dict()`** (hoje `to_search_dict()`), e as "Questões em aberto delegadas a F1", **todas
> decididas** na seção acima.

**Histórico:** item aberto originalmente como "Autocomplete de Jogador na Calculadora de Salário" (Baixa). Refinado in-place em 28/04/2026 após diagnose MAN-SEARCH-F1 — escopo ampliado para absorver busca global de jogador, prioridade promovida para Média, ID preservado. Calculadora segue como um dos consumidores; não é mais o único.

**Problema (escopo ampliado):**
- (1) **Busca global ausente.** Manager não tem ponto de entrada para chegar à player page (`/player/<id>`, M13) sem antes saber em que time fantasy o jogador está. Os 5 entry points existentes (`templates/roster.html:83,92`, `templates/admin_review.html:43,77`, `templates/salary_history.html:282`, `templates/trades.html:312`) todos pressupõem contexto. Caso de uso real de 28/04/2026: owner queria ver o contrato do Patrick Mahomes e teria que abrir os 12 rosters procurando visualmente.
- (2) **Calculadora de salário sem autocomplete.** `POST /api/salary/calculate` (`routes/salary.py:37-58`) recebe `player_name`, `espn_ref_value`, `contract_year`, `acquisition_type` como input manual. Se o jogador já existe no banco, esses dados estão disponíveis e poderiam ser pré-preenchidos.

**Objetivo (2 consumidores sob mesmo backend):**

- **Consumidor 1 — busca global na navbar.** Input acessível de qualquer tela. Dropdown de matches durante o typing. Ao selecionar um match, navegar para `/player/<id>`. Desktop: input inline na navbar, no slot vazio entre `.nav-links` e `.nav-right` (`templates/base.html:23-93`, `static/style.css:69-156`). Mobile: section nova no topo de `aside.nav-mobile-overlay` (`templates/base.html:97-133`), acima da section "Navegação" — padrão N1 preservado.
- **Consumidor 2 — autocomplete na calculadora de salário.** Substitui o input manual de `player_name` na tela `/salary` por input com dropdown de sugestões. Ao selecionar, preencher automaticamente ESPN ref value, contract year e acquisition type. Escopo original do M10, preservado.

**Backend — endpoint já existe (correção factual do diagnose):**
- `GET /api/player/search?q=<nome>&team_id=<opt>` em `routes/roster.py:312-326`. Singular (não `/api/players/search` plural como sugeria a versão pré-refinamento). Substring match (`Player.name.ilike("%q%")`), filtro opcional por `team_id`, `Player.is_dropped == False`, limit 20. Retorna `[p.to_dict() for p in players]`.
- F2 não precisa criar endpoint do zero. Possíveis ajustes (opcionais): payload reduzido (ver nota sobre `to_dict()` abaixo) e/ou inclusão/exclusão de campos derivados específicos para autocomplete da calculadora.

**Código a reusar (validado pelo diagnose):**
- Padrão de dropdown UI: `team-filter` em `templates/roster.html:51-65, 159-170` + classes em `static/style.css:311-340` (vanilla JS, abs-positioned, sem libs externas). Clonável diretamente para `player-dropdown` / `player-option`.
- Helper JS `renderPlayerNameLink` em `templates/base.html:245` — gera `<a href="/player/${id}" class="player-name">`. Já reusado por `salary_history.html:282` e `trades.html:312`. Disponível para renderização dos resultados, mas avaliar em F1 se vale usar direto ou montar link manual no JS local.
- Padrão debounce: `oninput="loadHistoryDebounced()"` em `templates/salary_history.html:27-31`. Aplicar para reduzir spam de requests durante typing.

**Código que NÃO serve (correção factual do diagnose):**
- `player_lookup.find_player_by_name()` é matching **estrito 4-tier** (exact → case-insensitive → normalized → None) usado em reconciliação de imports Sleeper/CSV (`player_lookup.py:53-122`). **Não serve para autocomplete** — incompatível com prefix typing ("mah" → Mahomes). O endpoint `/api/player/search` já usa `ilike` substring, que é o caminho certo. A versão pré-refinamento do M10 sugeria reusar `find_player_by_name`, premissa incorreta agora corrigida.

**Por que não absorver em O2 (refutação explícita da Opção D do diagnose, baseada nos 3 critérios de MAN-O2-REFINE de 27/04/2026):**
- (a) **Target page diferente:** O2 enriquece o conteúdo de `/player/<id>` (cards de NFL/stats/ADP no template). Busca global atravessa o app via navbar — não é "da página".
- (b) **Fonte de dados diferente:** O2 puxa Sleeper API (`/stats/nfl/...`, `/v1/state/nfl`) + Sleeper players cache. Busca usa apenas DB local (`Player.query.filter`). Zero overlap de fonte.
- (c) **Escopo natural distinto:** "enriquecer página" e "navegar até a página" são verbos diferentes. Absorver em O2 forçaria escopo heterogêneo e travaria O2 atrás da busca, ou inverso.

**Por que não criar item novo (refutação da Opção A — "S1 — Search"):** ID novo seria mais descritivo, mas perderia o histórico do M10 (a calculadora segue sendo um consumidor legítimo) sem ganho técnico. Opção C (refinar in-place) preserva continuidade auditável.

**Notas para F1:**
- `Player.to_dict()` em `models.py:173-197` retorna 21 campos por jogador, incluindo invocação de `is_renewal_candidate()` (método) e `projected_next_salary` (função). Para 20 resultados de busca = ~5KB JSON + 20 invocações por request. F1 avalia se vale criar `Player.to_search_dict()` minimal (~6 campos: `id, name, position, nfl_team, fantasy_team, salary`) ou se 5KB é aceitável. Otimização condicional, não pré-requisito.
- Diagnose qualificou ausência de rate limiting global em endpoints Flask como decisão de plataforma — não absorvida neste item.

**Questões em aberto delegadas a F1:**
- **Breakpoint exato desktop ↔ mobile.** Diagnose sugeriu <768px só overlay; >1024px inline na navbar; faixa intermediária a definir.
- **Layout do dropdown dentro do overlay mobile.** Flow normal (dentro do `aside`, sem `position: absolute`) vs absolute. Define se o dropdown empurra conteúdo do overlay ou flutua sobre ele.
- **`Player.to_search_dict()` minimal vs `to_dict()` completo.** F1 decide com base em medição (5KB × frequência typing) ou simplesmente custo de criar o método.
- **Renderização do link no result item.** Reusar `renderPlayerNameLink` direto vs link manual no JS local — escolha de consistência.
- **Decisão de batching.** 2 consumidores numa única camada vs quebrar (ex: navbar primeiro, calculadora depois). F1 avalia priorizando o gap UX maior (navegação global) primeiro.

**Validação de demanda (08/08/2026, MAN-UX12-REFINE — sem mudança de escopo):** segundo usuário
relatando o mesmo sintoma do caso de uso original — o co-admin **Michel** pediu busca de jogador
via [[UX12]], que foi **despachado** para cá (roteamento (b), decisão do owner; a UX12-F1
conferiu esta spec **inteira e viva**: endpoint na mesma assinatura, entry points todos
presentes). A spec de 28/04 segue autoritativa. **Requisitos originais e diagnose no
`improvements_archive.md`, seção UX12.**

---

### UX11 — Quadro de trades não mostra o time atual do jogador
✅ **CONCLUÍDO 10/08/2026 (MAN-UX11-F2 → MAN-ARC-BUSCA-DONE; gate [[PROC1]] cumprido — hash
`20b346b` live)** — Prioridade **Média** — registrado em 08/08/2026 (MAN-UX10-UX11-REG); **F1
respondida por transbordo** da MAN-UX12-F1, sem diagnose própria

**Smoke de produção aprovado (owner, 10/08/2026) — PRIMEIRA observação do fix em prod.** ⚠️
**Ressalva de proveniência registrada (família "observação verdadeira, procedência errada"):** os
smokes de produção anteriores a este ocorreram **antes do push do `a63d6ab`** — qualquer impressão
de "quadro conferido" naquelas passagens não valia para este item; a franquia NFL no quadro só
passou a existir em prod no deploy do lote `5e3c403..456b49d`, e a primeira observação real é a
desta sessão (10/08, junto com o smoke do M21-A sobre `20b346b`).

#### F2 — entregue (MAN-UX11-F2, 10/08/2026)

O fix foi **o que o transbordo previu**: uma linha de renderização em `templates/trades.html`. A
franquia NFL entra na **linha dim que já existia** sob o nome do jogador — `BUF · $21 · Ano 2/4`
—, no padrão que as demais telas usam para o mesmo dado (`text-dim`, separador `·`).

- ⛔ **Zero backend.** Payload, rota, sync e lógica **intocados**: `/api/roster/by_name/<team>`
  segue devolvendo `to_dict()` com as mesmas 21 chaves, e `nfl_team` **já era uma delas**.
- ⛔ **Nada derivado na tela** — o campo é consumido como vem. É a réplica que a Q1 da UX12-F1
  temia e que este item, por ser justamente o "mais um consumidor", poderia ter criado.
- **`—` para nulo sai de graça:** `to_dict()` já devolve `self.nfl_team or "—"`, o mesmo fallback
  de `_macros.html` e do `cap_projector`. Nenhum tratamento novo de ausência.
- **Ressalva de staleness registrada no código, não só aqui:** comentário no ponto do render diz
  que o frescor é o do **último sync** e que quem vira FA **mantém o time antigo** (o sync só
  sobrescreve `nfl_team` com valor truthy — 17 casos medidos em 28/04) e que o sync **não roda em
  todo boot** (DOC1). Quem ler a linha entende o que ela promete.

**Smoke local (GET-only, cópia do DB):** caso concreto conferido nas duas pontas — **DJ Moore** no
quadro (`BUF · $21 · Ano 2/4`) × no perfil (`🏈 BUF`): **mesma coluna, mesmo valor**. Amostra do
quadro mostra franquias distintas por jogador (NYG, HOU, SEA, PHI, KC, TEN — não é constante nem
herdada do time da liga). Nenhuma outra tela alterada — `/`, `/salary`, `/cap_projector` e
`/league` respondem 200. Suítes verdes, **`salary_engine_test` 54/54**.

⚠️ **Não exercido:** a aparência em navegador (é o smoke do owner) e o **caso do FA com time
antigo** — nenhum jogador do roster de teste está nessa condição hoje; é a ressalva conhecida,
não um caminho novo.

**Escopo do que NÃO entrou:** a página de proposta compartilhável (`trade_proposal.html`) renderiza
assets por `player_name_link` (Jinja, outra superfície) e **não foi tocada** — o sintoma registrado
é o quadro do simulador, e ampliar por conta própria seria outro item.

---

#### Registro original (MAN-UX10-UX11-REG, 08/08/2026) — preservado

**Sintoma reportado pelo owner (08/08/2026):** no **quadro de trade**, o jogador aparece **sem
indicação da franquia NFL** em que está.

**Por que Média e por que sem prazo:** o time do jogador é informação **usada para avaliar a
troca** (bye week, situação do backfield, contexto ofensivo) e hoje o owner precisa buscá-la fora
da tela. Não é bug de dado nem bloqueia nada — **não está no caminho crítico de 24/08**.

#### O que a F1 tem de responder

1. **De onde vem o dado de time hoje?** É campo do `Player` (escrito pelo sync do Sleeper) ou é
   derivado na hora, em cada tela? O Sleeper é autoridade sobre nome/posição/time NFL — mas isso é
   o contrato declarado, e a F1 confere se ele vale aqui.
2. **O dado está atualizado?** Um jogador que trocou de franquia na offseason precisa aparecer com
   o time novo. Se estiver stale, o item deixa de ser só de exibição — e aí encosta no [[UX10]]
   (hipótese (b): componente de time desatualizado também explicaria foto velha).
3. **Pergunta de réplica (obrigatória):** **a exibição de time do jogador existe em outras
   superfícies com fonte comum, ou cada tela deriva a sua?** Se cada tela deriva, acrescentar mais
   uma no quadro de trades **piora** o problema; o fix nasce na fonte única.

**Cross-refs:** [[UX10]] (mesmo registro; a hipótese (b) de lá e a pergunta 2 daqui podem ter a
mesma raiz), [[T1]]/[[T2]]/[[T3]] (o simulador e o preview de trades, onde o quadro vive).

**Transbordo da UX12-F1 (08/08/2026, MAN-UX12-REFINE): a F1 deste item está respondida.** A Q1
da diagnose do [[UX12]] (evidência no `improvements_archive.md`, seção UX12) respondeu as três
perguntas acima: (1) o dado vem de **fonte única** — `Player.nfl_team`, coluna escrita só pelo
sync a partir do pool do Sleeper, exposta em `to_dict()`; (3) **não há derivação por tela** —
os 8 sítios que exibem time do jogador leem a mesma coluna, e o quadro de trades busca
`/api/roster/by_name/<team>`, cujo payload **já contém `nfl_team`** — a tela simplesmente não
renderiza o campo (`trades.html:303-318`). **O item vira candidato a F2 direta de causa
conhecida** (1 edição de template literal, sem backend — carona em sessão futura). (2) A única
pendência real é a ressalva de **staleness**, que a F2 deve exibir ciente: o sync só atualiza
`nfl_team` com valor truthy (jogador que vira FA **mantém o time antigo** — 17 casos medidos em
28/04) e o sync não roda em todo boot (DOC1) — frescor = último sync.

---

### O5 — Quitação da dívida O3 + auditor poka-yoke do backlog
✅ **Concluído 13/08/2026 (mesma sessão — MAN-O5-REG/MAN-O5; critério de done: reorg íntegra +
auditor funcionando, sem smoke de prod, precedente O3 de self-aplicação)** — Prioridade **Média**
— **escopo Manager-only** (docs + script standalone; nenhum código da aplicação)

**Problema (dívida recorrente).** A regra de migração do [[O3]] (seção ✅ → archive no fechamento
da sessão) foi descumprida pela SEGUNDA vez: auditoria do owner (13/08/2026, via Claude.ai) mediu
o ativo em 481 KB / 5.927 linhas, estimando ~14 seções ✅ (~107 KB) não migradas e ~17 seções
`###` sem emoji de status próprio (~22 KB) — sub-blocos de achados de sessão promovidos
indevidamente a heading de item, que quebram a convenção estrutural "1 seção `###` = 1 item com
emoji" usada pela classificação por máquina do O3. A primeira recorrência (08/08/2026) já havia
encontrado 3 seções não migradas. A migração depende hoje de disciplina no checklist de fim de
sessão; a lição da casa é poka-yoke sobre disciplina.

**Desenho (quitação + auditor).**
1. **Reancorar** as sub-seções `###` órfãs ao item pai (rebaixamento de heading, texto verbatim).
2. **Quitar** a dívida: classificar todas as seções `###` cruzando emoji-da-seção × Status Rápido
   (regra "primeiro emoji da célula vence", precedente O3) e migrar as ✅ verbatim ao archive.
   ⚠️ nunca migra.
3. **Auditor poka-yoke** (`tools/backlog_audit.py`): script standalone, stdlib-only, read-only,
   que valida o invariante estrutural do ativo e falha com exit code ≠ 0 apontando as violações.
   Invariantes: (1) nenhuma seção `###` com status ✅ no ativo; (2) toda seção `###` tem emoji de
   status reconhecível; (3) todo ID de seção detalhada existe no Status Rápido e vice-versa para
   🔲/⚠️; (+) IDs únicos e toda row do Status Rápido com emoji.
4. **Ancorar no processo**: o auditor entra no checklist de fim de sessão do `CLAUDE.md` como
   gate. (Promoção transversal ao DEV_METHODOLOGY fica para sessão de revisão de metodologia —
   fora deste escopo.)

**Regra permanente.** Ao fechar QUALQUER sessão que toque `improvements.md`:
`python tools/backlog_audit.py` deve retornar sucesso ANTES do commit. Violações não se
contornam — se um item fechou ✅, a seção migra na mesma sessão; se nasceu seção nova, nasce com
emoji e com row no Status Rápido.

**Critério de done:** reorg íntegra (verificação por máquina, precedente O3 de self-aplicação) +
auditor funcionando (falha no estado pré-limpeza, sucesso no pós). Sem smoke de prod — docs +
script standalone.

**Resultado (MAN-O5, 13/08/2026).** Quitação executada com divergência material contra a baseline
do owner — e a classificação por máquina é a autoritativa:
- **Zero seções ✅ de item para migrar.** As ~14 seções ✅ (~107 KB) da baseline eram itens
  ABERTOS (🔲/⚠️ como primeiro emoji da seção E da row) com marcos ✅ **dentro** da linha de
  status — OFF26-24 ("critério de 19/08 ✅ cumprido; fecha ✅ e migra após a população real de
  22/08", confirmado no log do devplan), M21 ("fatia A ✅; o item segue 🔲 pela fatia B"),
  DP1/OFF26-20/O2 (⚠️ com smoke pendente). A heurística externa (emoji nas primeiras linhas) leu
  o ✅ interno como status do item.
- **42 headings reancorados** (baseline estimava ~17 seções): a narrativa
  F1B/F1C/VERIF/CANAL/FIX/CLOSE do [[OFF26-20]] — 6 blocos de sessão promovidos indevidamente a
  `##` e 36 sub-blocos a `###` — rebaixada a `####`/`#####` sob o item pai, texto verbatim (só o
  prefixo de heading mudou; +2 bytes por heading). Divisor `## Itens UX` criado para os itens UX
  não herdarem o aninhamento.
- **Namespace fechado nos dois sentidos:** rows criadas para MAN-METH-REG e MAN-ESPN12 (seções
  detalhadas que nunca tiveram entrada no Status Rápido); stubs estruturais criados para
  M1-FOLLOWUP, F8, OFF26-14 e IR-CLEANUP (rows 🔲/⚠️ sem seção no ativo — os 3 últimos com
  detalhe no archive, anomalia histórica à regra "⚠️ nunca migra" registrada nos próprios stubs).
- **Auditor demonstrado nos dois sentidos:** ativo pós-limpeza OK (exit 0; 4 avisos legítimos de
  divergência emoji seção × row — DP1, OFF26-4, F9, OFF26-20 — deixados para arbitragem humana);
  backup pré-limpeza (`improvements_backup_pre_O5_2026-08-13.md`) FALHOU com exit 1 e 83
  violações listadas (V1 ✅ no ativo ×3, V2 sem emoji ×30, V3 fora do namespace ×27, V4 row sem
  seção ×4, V6 IDs duplicados ×19).
- **Self-aplicação:** esta seção migrou ao archive na mesma sessão em que o item fechou ✅.

---

### L3 — Projeção de cap por time na `/league`
✅ **CONCLUÍDO 13/08/2026** — smoke visual do owner **aprovado** na `/league` e no `/team/<id>`;
produção no hash `7883cd9`, [[PROC1]] confirmado **por artefato servido** (CSS byte-idêntico ao do
commit), não por dashboard — Prioridade **A definir** — **6 sessões no mesmo dia:** MAN-L3-F1 ·
MAN-L3 · MAN-L3-FIX-F1 · MAN-L3-FIX · MAN-L3-FIX-UX · MAN-L3-FIX-UX2

**O arco, numa passada:**
1. **F1** (read-only) — achou a fonte canônica (composição `project_next_salary` → `draft_budget`,
   inline num sítio só) e **refutou a premissa** de que havia débito de agregação em JS (era o
   [[F10]], já fechado). Registrou o item, que **não existia** no backlog.
2. **F2** — extraiu a composição para `compose_budget` (3 consumidores) **antes** de usar; refactor
   puro **provado por medição** (payload do `/budget` idêntico em 12 times + cenário de corte +
   `projected:false`). Cap projetado nas duas telas, gate `rollover_done`, 8 rótulos com ano
   derivado, 22 testes novos.
3. **FIX-F1** — o sintoma "projeção não aparece em prod" **não era bug**: o commit **nunca fora
   empurrado** (`main` ahead 2). Gate, helper e divergência liga × detalhe **refutados com
   evidência**.
4. **FIX** — card reorientado a **planejamento** (3 zonas), PROV nas duas grandezas projetadas,
   slots, docstring do gate corrigida (⇒ [[L4]]) e o push que faltava.
5. **FIX-UX** — sobreposição de rótulos: linha flex de 2 colunas `nowrap` não cabia nos ~258px
   úteis do card de produção.
6. **FIX-UX2** — a quebra do fix anterior era **condicional**; anatomia passou a ser **idêntica
   nos 12**.

**As 3 gerações do instrumento de validação — e o que cada uma deixou passar:**
| Geração | O que mediu | O que **não** viu |
|---|---|---|
| **1. Regex sobre HTML** (F2) | valores, payloads, contagem de queries — provou o refactor puro | **layout**: aprovou 12 cards com o texto **sobreposto** |
| **2. Geometria** (FIX-UX) | `getBoundingClientRect`, colisão/transbordo/overflow, com **controle** contra o CSS de prod (24 colisões → 0) | **uniformidade**: passou verde com anatomias diferentes entre cards |
| **3. Anatomia** (FIX-UX2) | assinatura `classe@topo` comparada entre os 12 cards | — (pegou as 2 anatomias no card de 300px) |

**Lições de método (a parte reaproveitável — origem do [[O7]]):**
- **Validar na largura REAL de produção.** A divergência de anatomia **só existia no card mais
  estreito** (300px); em 1024px+ o mesmo CSS parecia uniforme.
- **Layout não se valida por texto/regex** — e nenhuma suíte de unidade cobre pixel.
- **Ausência de colisão ≠ uniformidade.** Cada geração do instrumento nasceu de um defeito que a
  anterior aprovou.
- **Assinatura tem de medir ESTRUTURA, não dado:** incluir o `left` fazia 1px de largura de texto
  (`$5/$200` × `$180/$200`) parecer "anatomia diferente".
- **Todo detector precisa de controle positivo** — provado contra o defeito conhecido antes de
  valer como aprovação. O poller sem controle deu um **falso TIMEOUT de 10 min** sobre um deploy
  que já estava no ar (`python -c` lendo `/tmp/`, que o Python nativo do Windows não enxerga).
- **Commitar ≠ estar em produção** (a FIX-F1 inteira).

**Decisões de produto do owner (todas implementadas):** exibir cap atual **E** projetado ·
destacar over-cap projetado · levar também ao `/team/<id>` · projeção visível **só pré-rollover**
(gate `rollover_done`) · rótulo pelo **ano derivado**.

**O que foi feito (F2):**
- **Helper único `routes.salary.compose_budget(players, projected=True, extra_salaries=())`** —
  a composição *salário-base → roster sintético → `draft_budget`* que vivia **inline** no POST
  `/budget`. Três consumidores: o endpoint do projector, a `/league` e o `/team/<id>`.
  ⛔ Nenhuma aritmética de cap no helper (soma, vagas e reserva de $1 seguem no `draft_budget`);
  `projected=False` preserva o modo D9 do [[OFF26-1]]; filtro `is_dropped` alinhado ao
  `roster_salary` ([[OFF26-16]]).
- **`/league`:** 6º stat no card — *"Cap proj. `<ano>`"* ao lado de *"Cap restante"*, nos 12 times.
  Over-cap projetado: ⚠️ + valor em vermelho + faixa no card (`.league-card-proj-over`, faixa
  interna para não disputar com o destaque do próprio time). Selo **PROV** herda o gate do Bid
  Máximo (mesma tabela ESPN, nenhuma 2ª definição de "provisório").
- **`/team/<id>`:** *"Cap proj."* + *"Resto proj."* na status bar, mesma fonte e mesmo gate.
- **Gate de fase `_projection_open()`** (`rollover_done`): pós-rollover a projeção significaria
  **season+2** sobre salário já valorizado e contradiria o número ao lado — a mesma arbitragem do
  D9. ⚠️ **Corrigido em 13/08 (MAN-L3-FIX):** a redação original dizia que a flag "volta
  sozinha na intertemporada seguinte" — **não volta**; ver [[L4]].
- **Ano derivado em 8 rótulos** (`g_current_season`, custo zero — o context processor já o
  injeta): título + h1 + barra do Cap Projector, 2 cabeçalhos da tabela JS, banner ESPN, e a
  coluna PROJ de `/` e `/team/<id>`. ⛔ Zero ano literal nas 4 superfícies (guarda estática).

**Validação (localhost, cópia do banco — nada de prod tocado):**
- **Refactor puro provado:** payload do `/budget` **idêntico** antes × depois nos 12 times + no
  cenário com corte + no modo `projected:false`.
- **12/12 coerentes** entre `/team/<id>` e o projector (folha projetada e resto).
- ⛔ **Bid Máximo, Cap restante, Record, Picks e Dynasty idênticos byte a byte** nos 12 cards.
- Gate exercido nos dois sentidos; rótulos conferidos virando `current_season` para 2026 (tudo
  acompanhou: "Cap Projector 2027", "Proj 2027").
- **22 testes novos** (`cap_projetado_test.py`, incl. guardas anti-réplica e a do Bid Máximo);
  **494 verdes** no total (salary_engine 54/54 intacto).
- **Dado real:** só **2 dos 12** times têm projeção diferente do cap atual hoje — Cangaceiros
  (−$1) e Trust The Process (**$76 → $59**) — porque a ESPN ainda é **provisória** (≈1.0 em 134
  dos 248, [[OFF26-20]]) e a projeção colapsa para perto do corrente. É exatamente o que o selo
  PROV comunica; os números separam de verdade quando a definitiva entrar (18/08). Único over-cap
  projetado: **3 peat… of pain** ($201, −$1) — o destaque foi exercido em dado real, não montado.
- ⚠️ **Desvio consciente de um critério:** a contagem de queries do render **subiu** —
  `/league` 17 → **19**, `/team/<id>` 18 → **21**. A **projeção custa ZERO query** (o ponto da F1:
  ela opera sobre os players já carregados; as 12 composições não aparecem no trace). O acréscimo
  é **constante, não por time**: +2 do gate (`get_config` custa **2 queries** nesta base — 1
  `sqlite_master` do `_table_exists` + 1 select; as 4 chamadas já existentes respondiam por **8
  das 17** do baseline) e +1 no detalhe do time pelo `ESPNImportLog` do selo PROV. Zerar o gate
  exigiria mexer no `get_config`/`_table_exists` em `models.py` — **fora do escopo** desta F2
  (candidato a item próprio: 4 varreduras de `sqlite_master` por render é desperdício que nada
  tem a ver com o L3).

**Fora do gate de propósito:** a **coluna PROJ por jogador** de `/` e `/team/<id>` continua
aparecendo pós-rollover — ela é pré-existente (T4 do [[OFF26-20]]), útil o ano todo, e o item só
pediu o **ano derivado** nela. O gate cobre o **agregado** novo.

---

**FIX-F1 (13/08/2026, read-only) — por que a projeção não aparece em produção:**

⛔ **CAUSA RAIZ: o commit do L3 NUNCA FOI EMPURRADO.** `main` está **`ahead 2`** de
`origin/main`, que segue em `ac1a2cf` (MAN-O6-REFINE). O Render faz deploy do GitHub ⇒
**produção roda o código pré-L3**. Não é hipótese — é estado verificável:
- `git show origin/main:templates/league.html` renderiza **exatamente 5 rótulos** — Record ·
  Cap restante · Bid Máximo · Picks · Dynasty — **idêntico ao screenshot**;
- `compose_budget` e `_projection_open`: **0 ocorrências** em `origin/main`;
- os 2 commits retidos são `8ecce54` (F1, docs) e `e4aa5e4` (F2, código).

**Veredicto por hipótese:**
1. **Helper não invocado no render da liga** — ✅ *é a causa, por ausência de código*: no
   `_build_team_card` novo ele É invocado (12 cards mediram projeção na validação local); em
   produção o helper **não existe**. Mapa rótulo→valor do que prod renderiza hoje: `Record` =
   `standing.wins-losses` · `Cap restante` = `SALARY_CAP − roster_salary` (folha única com IR,
   [[OFF26-16]]) · `Bid Máximo` = `draft_budget(...)["usable_draft_budget"]` base **corrente**
   (L1-BID) + tag PROV de `ESPNImportLog(season+1, final)` · `Picks` = contagem · `Dynasty` =
   soma FantasyCalc. **Nenhum campo de projeção existe no payload do card deployado.**
2. **Gate errado / invertido / default errado / divergência local × prod** — ⛔ **REFUTADO.**
   `_projection_open()` lê `rollover_done` com default `"false"` e abre quando `!= "true"`;
   exercido nos dois sentidos em teste. Prod está **pré-rollover**, e há evidência direta: o
   smoke da urna em prod (07/08) **exercitou o escape do banner de ensaio** — escape que só é
   necessário quando `rollover_done != "true"` ([[OFF26-10]] / `rollover_blocks_urn`). Logo o
   gate em prod está **aberto**; ele não tem participação no sintoma.
3. **Projeção renderiza colapsada pela ESPN provisória** — ⛔ **não é a causa** (a linha está
   *ausente*, não igual), ⚠️ **mas é achado real para o pós-deploy**: na medição local **10 dos
   12** times têm projetado **idêntico** ao atual; só Cangaceiros (−$1) e Trust The Process
   ($76 → $59) separam. Dois números iguais lado a lado em 10 cards **lê como bug** — é o que
   sustenta o ajuste de rótulo que o owner já sinalizou. Separa de verdade quando a ESPN
   definitiva entrar (18/08).
4. **Divergência liga × detalhe** — ⛔ **inexistente**: as duas telas chamam o **mesmo**
   `_projection_open()` e o **mesmo** `compose_budget`, e as duas estão igualmente ausentes de
   produção. Não há caminho divergente para explicar.
5. **Réplicas de exibição/gate** — **uma só definição**: o gate vive em `_projection_open()`
   (`routes/league.py`), os dois templates apenas **leem** `show_projection`, e **não há JS**
   envolvido. Os outros leitores de `rollover_done` (passo 4 do `/offseason`,
   `rollover_blocks_urn` do late_drop) são consumidores da mesma flag para **outra finalidade**
   — não réplicas do gate de exibição.

**Smoke de produção do L3: NUNCA foi realizado** — o próprio registro da F2 diz "smoke de
produção PENDENTE (gate [[PROC1]])" e toda a validação foi em **localhost sobre cópia do banco**.
O cenário validado (pré-rollover, 12 cards com projeção) **corresponde** ao estado de prod; o que
não correspondia era o **código deployado**. Lição: "commitar" ≠ "estar em produção", e a
validação local não tem como perceber a diferença.

⚠️ **Achado colateral do próprio L3** (não causa o sintoma): a docstring de `_projection_open`
afirma que `rollover_done` "volta sozinha na intertemporada seguinte, quando o reset da season a
zera". **É FALSO pelo código:** `_seed_app_config` só insere chave **ausente**
([app.py:441](app.py#L441)), o `ensaio_janela_selada --reset` não toca a flag, e **nenhum sítio
grava `"false"`** — só o rollover grava `"true"`
([routes/offseason.py:707](routes/offseason.py#L707)). Consequência: depois de 18/08 a projeção
some e **não volta sozinha** no ciclo seguinte. O comportamento de hoje é o desejado (pós-rollover
a projeção deve mesmo sumir); o que está errado é a **frase**, escrita por raciocínio e não por
verificação.

**Menor caminho de fix:** `git push origin main` + deploy + conferência do hash (PROC1).
**Nenhuma linha de código é necessária para o sintoma.** Ajuste de rótulo (owner) e correção da
docstring são escopo à parte — decisão do próximo prompt.

---

**FIX (13/08/2026, MAN-L3-FIX) — card reorientado a PLANEJAMENTO + push:**

Feedback da liga colhido pelo owner antes do push: o card tinha de responder primeiro *"quanto
posso gastar na auction"*. As grandezas **projetadas** viram a informação principal; as atuais
descem a linha de conferência, sem sair da tela.

- **Card da `/league` em 3 zonas:** (1) **bloco de planejamento** — *Bid máximo `<ano>`* como o
  maior número da peça, com *Cap `<ano>`* e **Slots livres** ao lado; (2) linha discreta
  **"Atual: cap $X · bid $Y"**; (3) **rodapé** com picks · record · dynasty. Pós-rollover o gate
  fecha e **as grandezas correntes assumem o mesmo bloco de destaque** — mesma macro Jinja
  (`bloco_destaque`), dois usos, **nenhuma condicional além do gate**.
- **Selo PROV nas duas grandezas projetadas** (era só no bid). É o que explica os pares
  coincidentes enquanto a ESPN for provisória — o achado (a) da FIX-F1 vira microcopy, não bug.
- **`slots`** = `empty_spots` do **mesmo** `draft_budget` já chamado para o bid (⛔ zero conta
  nova; o número é igual nas duas bases porque projetar não muda o **tamanho** do elenco).
- **`/team/<id>`:** rótulos passam a **"Cap atual"/"Resto atual"** × **"Cap proj. `<ano>`"/"Resto
  proj."**, ambos os projetados com PROV. Sem reestruturação de layout.
- **Docstring do gate corrigida** (task 4) + guarda de teste
  (`TestGateSemPromessaFalsa`) que barra tanto a volta da promessa quanto uma implementação
  silenciosa da reabertura. ⚠️ **A 1ª versão da guarda proibia a palavra "automátic" e derrubava a
  própria NEGAÇÃO** ("não é automática hoje") — refeita para mirar a afirmação. Registro do
  tropeço porque é a classe de teste que empurra o autor seguinte a apagar a explicação.
- ⛔ **Bid Máximo atual intocado** — base, cálculo e valor idênticos; `proj_bid_max` é **campo
  separado**, com teste que falha se um contaminar o outro.

**Validação (localhost, cópia do banco):** 12 cards com as 3 zonas · **slots conferidos contra a
contagem de elenco do banco nos 12** · **linha "Atual" idêntica** ao que o card exibia antes desta
mudança (comparação automática contra a captura do L3) · **Trust The Process separa de verdade**
(bid $76 → **$59**, cap $124 → **$141**) e **Miller Time!** coincide com PROV visível · gate
fechado ⇒ bloco de destaque passa a mostrar *"Bid máximo"* corrente, linha "Atual" some, rodapé
permanece · **499 testes verdes** (salary_engine 54/54).

⚠️ **Achado colhido na validação (não é regressão, é o [[OFF26-13]] aparecendo na tela):** o
**achane tem 24 jogadores** (22 + 2 IR) ⇒ `empty_spots` sai **clampado em 0** pelo `max(0, …)` do
`draft_budget`, então o card exibe *"Slots livres 0"* — verdadeiro, mas **silencia que o time está
2 acima do teto**. Não inventei UI para isso: a decisão (corte obrigatório × exceção) é do
[[OFF26-13]], que segue 🔲.

**PUSH + DEPLOY (13/08/2026) — [[PROC1]] cumprido por evidência do que está NO AR:**
`ac1a2cf..19d9398 main -> main`; os **4 commits retidos** (`8ecce54` · `e4aa5e4` · `ac35f6a` ·
`19d9398`) estão em `origin/main`, que é de onde o Render deploya. Confirmação do deploy **sem
depender de dashboard**: o `static/style.css` **servido em produção** é **byte-idêntico** ao do
commit (83.467 B, `diff` limpo) e contém as classes que só existem nele
(`league-plan`, `league-now`, `league-card-foot`, `league-card-proj-over`); o app — não só o
static — responde `GET /league → 302 /login` (roteamento + guarda de auth vivos). O build foi
observado subindo (502 → 502 → 200).
⚠️ **Isto é confirmação de DEPLOY, não o smoke.** O item segue ⚠️: falta a conferência **visual**
do owner na `/league` logada (as 3 zonas nos 12 cards, o bid projetado em destaque e o bid atual
coerente com a keeper sheet).

---

**FIX-UX (13/08/2026) — sobreposição de rótulos no bloco de planejamento (CSS-only):**

O smoke visual do owner pegou o que a minha validação não tinha como pegar: **"BID MÁXIMO 2026"
sobreposto a "Cap 2026 [PROV] $X/$200"**, com as duas tags PROV empilhadas, em **todos** os cards
na largura real. Dados, over-cap, linha "Atual" e rodapé estavam corretos — defeito puramente de
layout.

**Causa raiz (medida):** `.league-plan` era **uma linha flex com duas colunas, ambas
`white-space: nowrap`**. Na grade `repeat(auto-fill, minmax(280px, 1fr))` o card de produção dá
**~258px úteis** dentro do bloco, contra **~310px de largura MÍNIMA** do conteúdo. O
`min-width: 0` do herói permitia encolher, mas **texto `nowrap` sem `overflow` não encolhe:
transborda** — e pintava por cima da coluna vizinha; as duas tags PROV caíam uma sobre a outra
porque uma fica no fim do rótulo que vazava e a outra no início do item vizinho.

**Fix:** o bloco passa a **empilhar** (`flex-direction: column`) e a fila secundária ganha
`flex-wrap: wrap` — nenhuma largura depende mais de caber numa linha. Cada item segue `nowrap`
**internamente** (um valor nunca se separa do seu rótulo) e a quebra acontece **entre** itens.
O rótulo do herói virou flex com `gap`, então a tag PROV senta ao lado do texto em vez de flutuar.
⛔ Nada além de CSS: **34 linhas em `static/style.css`**, zero backend, zero template, zero JS.

**Validação — geométrica, não textual (a lição do defeito):** script Playwright mede o
`getBoundingClientRect()` de cada caixa de texto do bloco e acusa cruzamento entre caixas
não-aninhadas, em 4 larguras. **Rodou primeiro contra o CSS DE PRODUÇÃO como controle, para provar
que o instrumento enxerga o defeito: 24 colisões a 1280px (12 cards × 2 pares), 13 a 1024px, 1 a
390px.** Com o fix: **0 colisões, 0 transbordos, 0 overflow horizontal** nas 4 larguras (cards de
300 / 320 / 406 / 358px), com e sem over-cap projetado. Hierarquia intacta (bid projetado é o
maior número; ⚠️ + vermelho + faixa no card do over-cap). `/team/<id>` conferido: **0 colisões** —
a `.team-status-bar` sempre teve `flex-wrap: wrap`, então **nunca** sofreu do defeito.
**499 testes verdes.**

⚠️ **Correção de premissa do prompt:** a macro `bloco_destaque` **não é compartilhada com o
`/team/<id>`** — seus dois usos são os **dois ramos do gate**, ambos em `league.html`; o detalhe do
time tem markup próprio (`.team-status-bar`). A raiz era exclusiva do card da liga.

**Achado de carona (pré-existente, fora do escopo):** a **navbar** transborda a viewport a ~860px
(`nav-right` / `btn-sync` / `nav-user-menu`) — **idêntico no controle e no fix**, portanto não é
regressão do L3. Fica anotado como candidato a item próprio.

**PUSH + DEPLOY do FIX-UX ([[PROC1]]):** commit `f012d28` em `origin/main`; o `style.css` **servido
em produção** é **byte-idêntico** ao do commit (84.262 B, `diff` limpo), o bloco `.league-plan` no
ar traz `flex-direction: column` e o app responde `GET /league → 302 /login`.
⚠️ Segue faltando **só** o smoke visual do owner na largura real.

---

**FIX-UX2 (13/08/2026) — anatomia idêntica nos 12 cards (CSS-only, 9 linhas):**

O FIX-UX matou a sobreposição, mas com **quebra CONDICIONAL** (`flex-wrap`) na fila secundária: o
card com over-cap projetado tem o rótulo mais largo (⚠️ + valor) e empurrava *"Slots livres"* para
a 2ª linha, enquanto o vizinho cabia em uma — **cards lado a lado com anatomias diferentes**.
Decisão do owner: **padrão único**. `.league-plan-side` deixa de ser fila com wrap e passa a
**empilhar sempre** (`flex-direction: column` + `align-items: flex-start`): bid (herói) · cap ·
slots, uma grandeza por linha, **em qualquer largura e com qualquer dado**.

**A sonda geométrica ganhou uma medida nova — ANATOMIA**, porque ausência de colisão não prova
uniformidade: para cada bloco ela extrai a assinatura `classe@topo` de cada linha e compara os 12.
⚠️ 1ª versão da assinatura incluía o `left`, e acusava "3 anatomias" por diferenças de **1px**
vindas da largura do texto (`$5/$200` × `$180/$200`) — dado, não anatomia; o `left` virou
verificação separada (alinhamento de coluna).

**Controle × fix (mesmo instrumento, mesmas 4 larguras):**
- **CSS de produção:** no card de **300px**, **2 anatomias** — 11 cards com `item@69 | item@69`
  (mesma linha) e o over-cap com `item@69 | item@93`; `linhas/bloco = [3, 4]`, alturas **100 e
  123**; 11 dos 12 com as linhas fora da mesma coluna. ⚠️ Nas larguras maiores a divergência
  **não aparecia** — era exclusiva do card mais estreito, que é o de produção.
- **Com o fix:** **1 anatomia**, `linhas/bloco = [4]`, altura **123** e `fora da coluna: []` nas
  **quatro** larguras; 0 colisões, 0 transbordos, 0 overflow. **499 testes verdes.**

**PUSH + DEPLOY ([[PROC1]]):** commit `b228efa`; o `style.css` **servido em produção** é
**byte-idêntico** ao do commit (84.765 B, `diff` limpo), o `.league-plan-side` no ar traz
`flex-direction: column` + `align-items: flex-start`, e o app responde `GET /league → 302`.
✅ **A lição do poller anterior foi aplicada e funcionou:** detector 100% em ferramenta do bash
(`diff` contra o arquivo do commit), que registrou a transição real **84.262 B → 502 (restart) →
84.765 B** e parou sozinho na 4ª tentativa — sem falso negativo.

⚠️ **Lição de ferramenta (custou um falso TIMEOUT):** o poller do deploy dizia "não pousou" por
**10 minutos depois de ter pousado** (o tamanho servido mudou de 83.467 → 84.262 B na 5ª
tentativa). O detector inline era `python -c` lendo `/tmp/prod2.css` — e **Python nativo do Windows
não enxerga `/tmp/`**, que é mount do Git Bash: resolve como `C:\tmp\` e estoura
`FileNotFoundError`, caindo no `|| echo 0` a cada iteração. As ferramentas do bash (`wc`, `diff`,
`grep`, `awk`) leem esse caminho **sem problema** — foi por isso que o poller do deploy anterior,
feito com `grep`, funcionou. **Regra:** num pipeline Git Bash, a checagem tem de ser feita com
ferramenta do bash, ou o caminho tem de ser nativo do Windows. E **um detector que só sabe dizer
"não" precisa de um controle positivo** — o mesmo cuidado que a validação geométrica teve, e o
poller não.

---

**F1 (parecer read-only, 13/08/2026) — preservado:**

**Problema:** a `/league` exibe o cap da season corrente (`cap_used`/`cap_space`, computados no
render); a projeção da season seguinte (valorização × tabela ESPN) só existe agregada no Cap
Projector, **time a time**. Não há tela com o agregado projetado dos 12 — a divergência entre as
duas grandezas motivou o item.

**F1 — as 5 respostas (evidência por âncora):**

**1. Fonte canônica.** Por jogador: `salary_engine.project_next_salary`
([salary_engine.py:176](salary_engine.py#L176)) — pura (projeta `contract_year+1`; sem ESPN →
salário atual; renovação → floor(ESPN); waiver ano 2 → 0,8; senão VALORIZAÇÃO). Agregação:
`salary_engine.draft_budget` (pura). O agregado PROJETADO que o projector exibe nasce da
**composição** dos dois — inline, num único sítio: o POST `/api/cap_projector/<team>/budget`
([routes/salary.py:150-180](routes/salary.py#L150-L180)) monta roster sintético de
`SimpleNamespace(salary=project_next_salary(p))` p/ os mantidos (+ rookies do cenário a
`year1_salary`) e passa ao `draft_budget`. ⚠️ O GET `/api/cap_projector/<team>` devolve
`next_salary` por jogador, mas o `budget` dele é sobre salário **CORRENTE**
([routes/salary.py:92](routes/salary.py#L92)) — o número projetado da barra sticky vem do POST.
**Não existe helper nomeado "budget projetado"**; a composição não tem nome nem segundo consumidor.

**2. Inventário de réplicas — veredicto: ZERO réplicas de cálculo hoje.**
(a) `project_next_salary` = canônica; (b) `Player.projected_next_salary()`
([models.py:178](models.py#L178)) **DELEGA** (T4 do [[OFF26-20]]) — wrapper, não réplica;
consumidor: coluna PROJ de `/` e `/team/<id>` (`_macros.html:73`); (c) `Player.to_dict()` idem
([models.py:239](models.py#L239)); (d) `apply_season_rollover` implementa as mesmas regras
**dentro** do engine, com teste de concordância (`trilha_fa_proj_test.py:89`); (e) **JS: nenhuma
agregação** — o débito era o [[F10]], **eliminado em 12/06/2026**; o JS atual do projector só
posta estado e exibe payload (`cap_projector.html:167-170`, "Nenhuma agregação de cap em JS").
**Como a F2 não cria réplica:** o risco real é a composição inline do `/budget` ganhar uma 2ª
cópia em `league.py`. Caminho: extrair a composição p/ **helper único fora do `salary_engine`**
(p.ex. em `routes/salary.py`, importado pela `/league` — precedente de import cross-blueprint já
existe: [routes/league.py:14](routes/league.py#L14) importa de `routes.roster`), ficando o POST
`/budget` e o render da `/league` como os 2 consumidores. Nenhuma aritmética nova em lugar nenhum.

**3. Custo: 0 queries novas, sem N+1.** O `league_hub` faz 5 queries (Team, SeasonStandings,
contagem de Pick, **todos** os Players numa query, ESPNImportLog —
[routes/league.py:59-86](routes/league.py#L59-L86)) e já computa `cap_used`/`bid_max` no render
sobre `players_by_team`. `project_next_salary` lê só colunas já carregadas (salary,
contract_year, acquisition_type, espn_ref_value) — **nenhuma query por chamada**. Projetar os 12
= ~250 chamadas puras + 12 `draft_budget` sobre listas de ~22, O(n) em memória. Caminhos
rejeitados: 12 fetches JS ao GET por time (12 requests + 1 query `EspnValueStore` **cada** — o
único N+1 real do mapa; a `/league` não precisa dela — o PROV por jogador é do projector, e o
flag de liga `bid_provisional` já sai do ESPNImportLog em
[routes/league.py:85](routes/league.py#L85)); endpoint batch novo (complexidade de cliente sem
ganho — o render server-side preserva o perfil da tela).

**4. Fase.** `project_next_salary` projeta sobre o estado **armazenado** ⇒ o significado muda no
rollover: **pré**-rollover projeta a season seguinte (janela útil máxima entre a ESPN definitiva
de 18/08 e o rollover); **pós**-rollover o salário armazenado JÁ É o da season nova e re-projetar
mostraria season+2 — exibi-lo ao lado do cap corrente contradiria as grandezas. O código já
arbitrou isso: **D9 do [[OFF26-1]]** usa `projected:false` pós-rollover porque "re-projetar
duplicaria" ([routes/salary.py:133-138](routes/salary.py#L133-L138)). Flags disponíveis:
`rollover_done` (AppConfig por ciclo, setada em
[routes/offseason.py:707](routes/offseason.py#L707)) decide exibição/rótulo; `bid_provisional`
marca PROV (mesma flag do Bid Máximo). Qualidade pré-definitiva: com ESPN provisória (~1.0 em
134/248, cf. [[OFF26-20]]) a projeção colapsa p/ ≈ salário atual (subestimada) — mesmo caveat do
banner do projector. O que o código permite exibir sem contradição: rotular pelo **ano**
(`season`/`season+1` — ⛔ não hardcodar "2026" como fazem hoje o título do projector e a coluna
PROJ) e ocultar/rebaixar o projetado quando `rollover_done`.

**5. Premissas × código / comportamentos em risco.**
(a) "L3 registrado no improvements.md" — **FALSA**: não existia (Status Rápido ia de L1 a L2);
registrado nesta sessão. (b) "cap ATUAL pré-computado" — **imprecisa**: nada é persistido; é
computado a cada render (`roster_salary`, [routes/league.py:26](routes/league.py#L26)) —
inofensiva, e reforça o caminho (projeção no MESMO render). (c) "disponível apenas no
cap_projector" — **imprecisa**: por JOGADOR a projeção já está em `/` e `/team/<id>` (coluna
"Proj 2026"); o que só existe no projector é o **agregado**. (d) "débito conhecido de agregação
em JS" — **FALSA/desatualizada** ([[F10]] ✅ 12/06/2026). Comportamentos: ⛔ **não trocar a base
do Bid Máximo** — o `bid_max` do card é base CORRENTE (L1-BID,
[routes/league.py:31-34](routes/league.py#L31-L34)), o **mesmo número** da keeper sheet
(`fa_budget`, D4); um "bid projetado" no lugar quebraria a coerência tela × sheet (perda
não-intencional). "Cap restante" corrente: se a F2 **substituir** em vez de somar, some a única
leitura corrente da liga em tela (remoção só se intencional do owner).

**Questões de produto (owner decide; a F1 só informa o que o código permite):** atual+projetado ×
só projetado (ambos custam o mesmo: $0 de query); levar o agregado projetado também ao
`/team/<id>` (mesma composição, mesmo custo); destaque de over-cap projetado (`draft_budget` já
devolve `over_cap`/`insufficient_budget` — flags prontas); comportamento pós-rollover (ocultar ×
rebaixar com rótulo de ano).

---

### O7 — Sonda de validação visual como ferramenta permanente
✅ **CONCLUÍDO 13/08/2026 (MAN-O7)** — ferramenta em `tools/visual_probe/`, gate ancorado no
`CLAUDE.md`, **demonstração bidirecional passou** — Prioridade **Média** — self-aplicação no
molde do [[O5]]/[[O3]] (fecha e migra na mesma sessão)

**O que entrou:**
- `tools/visual_probe/core.py` — **núcleo puro** (config, JS injetado, decisão). Sem Playwright,
  Flask, banco ou rede: é o que os testes exercem.
- `tools/visual_probe/cli.py` — driver. **Sem app de pé** (test client) · **sem login real**
  (cookie de sessão injetado) · **sem rede** (`run_sync` neutralizado) · **sem estado** (o banco é
  **copiado** para diretório temporário e é a cópia que o app abre — o `dynasty.db` real nunca é
  aberto para escrita). `--page` / `--width` / `--list` / `--keep`.
- `visual_probe_test.py` — **28 testes** do núcleo puro, sem browser.
- `tools/visual_probe/README.md` — cobertura, larguras, limites declarados e o controle positivo.

**Cobertura inicial (o critério decidiu a lista, não o gosto):** `/league` (geometria +
**anatomia** — 12 irmãos do mesmo loop em grade livre) · `/team/<id>`, `/` e `/picks` (geometria).
⛔ `/cap_projector` e `/trades` **ficaram fora, com razão medida**: montam o conteúdo principal
por `fetch` (3 e 9 chamadas) e são invisíveis ao serviço `file://` — cobri-las exige servidor
efêmero, registrado como próximo passo em vez de silenciado. ⛔ A matriz do `/picks` ficou **só na
geometria**: as células divergem **legitimamente** (vazia × preenchida × trocada), e anatomia ali
seria falso positivo.

**Demonstração bidirecional (o critério do [[O5]]):**
| Sentido | Comando | Resultado |
|---|---|---|
| **Verde** | `cli.py` (suíte completa) | **exit 0** · 16 medições · UX16 reportado como **conhecido** em 4 páginas @860px · **~20s** |
| **Controle** | `cli.py --css <478b915> --page league` | **exit 1** · **37 colisões @1280px**, **26 @1024px**, incl. o sintoma literal do screenshot: `"PROV" x "PROV"` |

⚠️ **Contagens maiores que as do L3 (24/13) — e o motivo importa:** a sonda ad-hoc olhava dentro
de `.league-plan`; a ferramenta olha o `.league-card` inteiro, então compara mais pares (pega
também o wrapper `div.league-plan-side`). **Mais sensível, mesmo defeito, mesmas larguras.**

**Mecanismo defeito conhecido × regressão nova** (a peça que impede o gate de nascer vermelho e
ser desligado na primeira semana): achado que **casa** uma entrada de `KNOWN_DEFECTS` reporta e
**não bloqueia**; o que **não casa** bloqueia; entrada que **não reproduz** é anunciada (defeito
corrigido → remover). O casamento exige tipo + página + largura **e culpados ⊆ registrados** — se
um elemento novo entra na conta, volta a bloquear. ⛔ Entrada ali **exige item no backlog**.

⭐ **Achado da própria estreia — o mecanismo se provou sozinho:** a F1 registrara **4** culpados do
[[UX16]]; a medição real trouxe **5** (faltava `nav-user-avatar`), e o achado **não casou** e
bloqueou — exatamente o desenho. O registro foi corrigido **pela medição**, não pela memória.

⚠️ **Defeito do próprio instrumento, achado e corrigido no 1º run:** a sonda acusava 2 "colisões"
no `/picks` @390px envolvendo o `.pick-edit-btn`, que tem **`opacity: 0`** até o hover — elemento
**invisível não colide visualmente**. Filtro de `opacity: 0` / `visibility: hidden` adicionado,
com o **limite declarado** no README: a medição é do **estado padrão** da página; estados
revelados por `:hover` ficam fora.

**Gate ancorado no `CLAUDE.md`** com disparo mecânico: `git diff --name-only` casando
`static/*.css` ou `templates/*.html` ⇒ suíte completa antes do push. ⛔ **Sem mapa template→rota
de propósito** — o app tem **um único CSS**, logo qualquer diff nele afeta todas as páginas, e
20s de suíte custam menos que manter (e errar) o mapa.

**[[UX16]] segue 🔲 e é o primeiro cliente** — aparecer no relatório é **validação da cobertura**,
não pendência desta sessão.

---

**Registro original (13/08/2026, MAN-L3-CLOSE-REG):**
🔲 Prioridade **Média**

**De onde veio:** a saga do [[L3]] queimou **três gerações** de instrumento de validação em um dia,
cada uma nascida de um defeito que a anterior **aprovou** (detalhe na seção L3 do
`improvements_archive.md`):

| Geração | Mediu | Deixou passar |
|---|---|---|
| Regex sobre HTML | valores, payloads, queries | **layout** — aprovou 12 cards com texto sobreposto |
| Geometria (`getBoundingClientRect`) | colisão, transbordo, overflow | **uniformidade** — anatomias diferentes entre cards vizinhos |
| Assinatura de anatomia (`classe@topo`) | estrutura repetida entre N elementos | — |

**Proposta:** promover a sonda a `tools/`, no **molde do [[O5]]** (ferramenta read-only em
`tools/` + gate ancorado no `CLAUDE.md`). Hoje ela vive no scratchpad e morre com a sessão —
enquanto o defeito que ela pega é recorrente por natureza (todo CSS de grade/flex).

**A F1 decide:**
- **cobertura inicial** de páginas (candidatas: `/league`, `/team/<id>`, `/` e `/cap_projector` —
  as de maior densidade);
- **larguras canônicas**, obrigatoriamente incluindo a **largura real de produção** e **mobile**
  — no [[L3]] a divergência de anatomia **só existia no card mais estreito** e sumia em telas
  largas;
- **como servir as páginas**: hoje é `file://` sobre HTML salvo do test client (avatares remotos
  não carregam — aceitável, mas é desenho a confirmar) × subir um servidor efêmero;
- **ancoragem do gate**: sessão que toca CSS/template roda a sonda nas páginas afetadas **antes do
  push**, como o `backlog_audit.py` é gate do fechamento.

**Lições de método a preservar na ferramenta** (todas pagas com defeito real):
- **validar na largura REAL de produção** — aprovação em tela larga não vale;
- **layout não se valida por texto/regex**;
- **ausência de colisão ≠ uniformidade** — são duas medidas;
- **assinatura mede ESTRUTURA, não dado** — incluir o `left` fazia 1px de largura de texto parecer
  anatomia diferente;
- ⛔ **todo detector precisa de controle positivo**: rodar contra o defeito conhecido **antes** de
  aceitar o verde. Sem isso, um poller deu **falso TIMEOUT de 10 min** sobre deploy que já estava
  no ar.

**Primeiro cliente:** [[UX16]] (transbordo da navbar) — defeito já medido pela sonda, com culpado
nomeado, esperando correção com validação pelo mesmo instrumento.

---

**F1 (13/08/2026, MAN-O7-F1 — read-only; a sonda NÃO foi tocada):**

**1. Inventário do que existe hoje.** Script único no scratchpad (~180 linhas, Playwright):
- **6 verificações:** colisão par-a-par entre caixas de texto **não-aninhadas** · transbordo para
  fora do bloco · overflow horizontal do card (`scrollWidth > clientWidth`) · **assinatura de
  anatomia** (`classe@topo`) comparada entre irmãos · alinhamento de coluna (conjunto de `left`) ·
  no `/team/<id>`, colisão entre `status-item` + overflow do documento **com o elemento culpado
  nomeado**.
- **Como serve as páginas:** copia `dynasty.db` → scratchpad e aponta `DYNASTY_DB` (⇒ **nunca toca
  o banco real**) · monkeypatch em `run_sync` (⇒ **zero rede**) · test client com cookie de sessão
  injetado (⇒ **sem login real, sem OAuth**) · salva o HTML, reescreve o `href` do CSS e abre por
  `file://` no Chromium headless.
- ⭐ **`--css <caminho>`: o controle positivo.** Troca **só** a folha de estilo e roda o **mesmo**
  HTML — é o que provou que o instrumento enxerga o defeito antes de o verde valer alguma coisa
  (24 colisões no CSS de produção → 0; 2 anatomias → 1). **Esta é a feature mais importante a
  preservar na promoção.**
- Já tem: `exit code` 1 em falha e screenshot por largura.
- **Custo medido: 21 s** a execução inteira (boot + 4 larguras × 2 páginas).
- **Falta para virar ferramenta:** páginas/larguras estão **hardcoded**; caminhos absolutos do
  scratchpad; relatório é `print` solto; sem degradação quando o browser não existe (o
  `tools/phantom_board` já tem o molde: import **lazy** + abort nomeado); e decidir `file://`
  (atual) × servidor efêmero.

**2. Cobertura — critério, não lista.**
- **Assinatura de anatomia** quando houver **N irmãos gerados pelo MESMO loop de template em
  layout LIVRE (flex/grid) que devem parecer idênticos**. ⛔ **Tabela não entra** — `<table>` já
  garante alinhamento por construção. Casam o critério: `.league-grid` (12 cards, o cliente que
  originou), `.picks-matrix`, `.admin-grid`, `.preview-grid` (trades), cards de passo do
  `/offseason`.
- **Só geometria** quando for **superfície densa de instância única**: a **navbar** (vive em
  `base.html` ⇒ **está em toda página**, e é o [[UX16]]), a status bar do `/team/<id>`, a barra
  sticky do `/cap_projector`, as colunas do `/trades`.
- **Cobertura inicial sugerida (4 telas):** `/league` · `/team/<id>` · `/` · `/cap_projector` —
  as mais densas; a navbar entra de brinde em todas.

**3. Larguras canônicas.**
| Largura | Por quê |
|---|---|
| **1280px** | ⚠️ **o achado contra-intuitivo:** `repeat(auto-fill, minmax(280px, 1fr))` faz o viewport **mais largo** produzir o card **mais estreito** (4 colunas × **300px**). **Os dois defeitos do L3 apareceram aqui** — "testar largo" não é testar fácil |
| **1024px** | 3 colunas × 320px — a largura do **screenshot de produção** do owner |
| **860px** | 2 colunas; é onde a **navbar transborda** ([[UX16]]) |
| **390px** | mobile |

**4. Ancoragem do gate — e "páginas afetadas" sem depender de disciplina.**
Molde do [[O5]]: ferramenta em `tools/`, `exit ≠ 0`, gate citado no `CLAUDE.md`. ⭐ **O app tem UM
único arquivo de CSS** (`static/style.css` — conferido: é o único em `static/`) ⇒ **qualquer diff
que o toque afeta TODAS as páginas**; não há inferência a fazer. Para `templates/*.html` caberia um
mapa template→rota, mas **a suíte inteira custa 21 s**: sai mais barato **rodar tudo** quando o
`git diff --name-only` casar `static/*.css` ou `templates/*.html` do que manter o mapa.

**5. Custo e primeiro cliente.** 21 s, **sem app rodando**, **sem login real**, **sem rede** e
sobre **cópia** do banco. Dependência real: **Playwright + Chromium** (já instalados; precedente de
uso e de import lazy no `tools/phantom_board`). ✅ **[[UX16]] serve como primeiro cliente** — o
defeito já está medido por este instrumento, com culpados nomeados
(`nav-right`/`btn-sync`/`nav-user-menu`/`nav-user-button`) e faixa isolada (**390 ok · 860
transborda · 1024+ ok**); falta só a sonda saber olhar a navbar em qualquer página, o que ela já
faz no `/team/<id>`.

**Achado de carona (não é escopo):** `.team-detail-cap-layout` tem **4 regras no CSS e 0 usos** nos
templates — resíduo da substituição feita pelo UX4-c. Higiene, não defeito.

**Cross-refs:** [[O5]] (precedente de ferramenta em `tools/` + gate), [[UX16]] (1º cliente),
[[L3]] (origem, archive).

---

### UX16 — Navbar transborda a viewport a ~860px
✅ **CONCLUÍDO 14/08/2026** — smoke visual do owner **aprovado nas três faixas**: desktop,
intermediária (~680–860, com hamburger + `cap-chip` + Sync + avatar **contidos** na barra) e
mobile — Prioridade **Baixa** — achado de carona da [[L3]]-FIX-UX, registrado 13/08/2026
(MAN-L3-CLOSE-REG); **primeiro cliente do gate visual do [[O7]]** — MAN-UX16 →
**MAN-CLOSE-LOTE-14-08**

**O arco, numa passada:**
1. **Achado pela F1 do [[O7]], não por olho** — a sonda geométrica mediu `scrollWidth >
   innerWidth` na faixa intermediária e **nomeou os culpados**; o **controle** (CSS pré-[[L3]])
   reproduziu idêntico ⇒ defeito **pré-existente**, não regressão.
2. **FIX (CSS puro, 2 media queries, zero template/JS)** — a causa medida não era falta de
   espaço, era **colapso tardio**: a barra desktop precisa de **916px** e o hamburger só entrava
   em **≤768px** ⇒ 769–944 transbordava em **toda** página. Colapso passa a **1023px**;
   **1024+ intocado**; menu do usuário só sai abaixo de 768.
3. ⭐ **O gate do [[O7]] provado no sentido INVERSO** — com o fix aplicado, a sonda imprimiu
   `conhecido(s) que NÃO reproduziram: ['UX16'] — remover de KNOWN_DEFECTS` e a entrada saiu do
   registro **por indicação da ferramenta**. `KNOWN_DEFECTS` **vazio**; suíte **exit 0 sem
   máscara**. 527 testes verdes.
4. **Smoke do owner (14/08)** — navbar íntegra nas três faixas, nenhuma função perdida no
   colapso. ✅

**Problema (medido, com controle):** a ~860px de viewport o documento fica com
`scrollWidth > innerWidth` e a página ganha rolagem horizontal. Os elementos que ultrapassam a
borda são os do lado direito da navbar: `nav-right`, `btn-sync`, `nav-user-menu`,
`nav-user-button`.

⚠️ **NÃO é regressão do [[L3]]:** o transbordo apareceu idêntico no **controle** (o CSS anterior
ao fix de layout) e no fix — a sonda geométrica mediu os dois e nomeou os mesmos culpados. É
defeito **pré-existente**, que só ficou visível porque a sonda passou a olhar geometria.

**Faixa exata:** medido em **390px → sem transbordo**, **860px → transborda**, **1024px e
1280px → sem transbordo**. A faixa intermediária é onde a navbar ainda tenta manter tudo em
linha e já não cabe.

**Como corrigir (a decidir na F1/F2):** a mesma família de causa do bloco de planejamento — fila
horizontal que não cabe. Opções óbvias: `flex-wrap` na navbar, esconder rótulos (deixando ícones)
na faixa, ou colapsar em menu. **Não decidir sem medir** — e **validar pela sonda** ([[O7]]),
que já sabe apontar o elemento culpado.

---

**FIX (13/08/2026, MAN-UX16) — primeiro cliente do gate visual:**

✅ **Implementado e validado** — smoke visual do owner aprovado em 14/08/2026 nas 3 faixas.

**Causa raiz medida** (com a sonda do [[O7]], largura a largura): a barra **desktop precisa de
916px** — `nav-brand` 123 + `nav-links` **507** + `nav-right` 214 + cromo ~72 — e o hamburger só
entrava em **≤768px**. Logo, a faixa **769–944px transbordava a viewport em TODA página** (a
navbar vive no `base.html`). Nada ali podia ceder: `.nav-links` **não encolhe** (filhos `nowrap`
⇒ `min-width: auto`) e `.nav-right` é `flex-shrink: 0`; só a busca cedia — de 178px a 0 — e os
916px restantes continuavam sem caber. ⇒ **o defeito não era "faltar espaço", era o colapso
entrar tarde**.

**Fix (CSS puro, 2 media queries, zero template e zero JS):** o colapso passa a **`max-width:
1023px`** — a barra desktop passa a existir **só onde foi medida cabendo**. E o menu do usuário,
que sumia junto com os links, agora **só sai abaixo de 768px**: na faixa nova a barra colapsada
precisa de ~380px e sobra espaço, então avatar e logout ficam visíveis.

**Nada de função se perdeu:** o painel do hamburger já tinha **busca, navegação completa, times,
admin e logout** — conferido antes de escolher o breakpoint.

**Medição antes × depois** (mesma sonda, mesmas larguras):
| viewport | antes | depois |
|---|---|---|
| 1280 / 1100 / 1024 | desktop, sem transbordo | **idêntico** (⇒ "1024+ sem mudança perceptível" ✓) |
| 960 · 900 · 860 · 820 · 800 · 780 | **TRANSBORDA** (precisa 916px) | hamburger, precisa **434px**, folga de 346–526px |
| 768 · 700 · 390 | hamburger | **idêntico** |

**Verificação funcional nas 4 larguras** (Playwright): dropdown do [[N1]] **abre no clique, fecha
no clique-fora e no Esc** em 1280/1024 (`.nav-group-label`) e em 860 (`.nav-user-button`);
hamburger abre com busca + logout em 860 e 390; `cap-chip`, `btn-sync` e altura de 54px intactos
em todas. **527 testes verdes.**

⭐ **O gate do [[O7]] foi exercido e o mecanismo fechou o ciclo no sentido INVERSO ao da estreia:**
com o fix aplicado e a entrada `UX16` **ainda registrada**, a sonda passou a imprimir
`ℹ️ conhecido(s) que NÃO reproduziram: ['UX16'] — remover de KNOWN_DEFECTS`. A entrada saiu por
**indicação da ferramenta**, não por memória. `KNOWN_DEFECTS` está **vazio** — e a suíte completa
dá **exit 0 sem defeito conhecido mascarando nada** (16 medições, 0 achados, ~16s).

⚠️ **Tropeço da minha verificação (não do app):** o script funcional tentou clicar o menu do
usuário a 390px, onde ele está escondido **de propósito** — 30s de timeout até eu ver que o
comportamento certo era o do app. Corrigi o script para só clicar alvo visível.

**PUSH + DEPLOY ([[PROC1]]):** commit `b750ce6`; o `style.css` **servido em produção** é
**byte-idêntico** ao do commit (**85.800 B**, `diff` limpo), a regra `@media (max-width: 1023px)`
está **no ar** (linha 2480 do arquivo servido) e o app responde `GET /league → 302`. Transição
observada: 84.765 B → 502 (restart) → 85.800 B, com o detector 100% em ferramenta do bash (a
lição do falso TIMEOUT segue aplicada).
✅ **Smoke visual do owner aprovado em 14/08/2026** nas três faixas (~1280 · intermediária
~680–860, com hamburger + chip + Sync + avatar contidos · celular). Item fechado.

**Cross-refs:** [[N1]] (redesign da navbar que criou a estrutura atual), [[UX6]] (largura máxima
do container), [[O7]] (o instrumento), [[L3]] (de onde o achado caiu).

---

### UX18 — Bid Máximo inviável ($0 com vagas abertas) não acende alerta
✅ **CONCLUÍDO 14/08/2026** — smoke do owner **aprovado nas DUAS direções**: o alerta **acende**
no cenário simulado do `/cap_projector` (com o banner explicativo) e o card do **Miller Time!**
na `/league` **deixou de pintar vermelho** — Prioridade **Média** — a diagnose (abaixo,
preservada) refutou a premissa do fix original; o owner decidiu a **opção (a)** e liberou o
`salary_engine` só para isso — MAN-UX-BID0 (REG + diagnose) · MAN-UX-BID0-F2 (fix) →
**MAN-CLOSE-LOTE-14-08**

**O arco, numa passada:**
1. **REG + diagnose (docs-only, fix NÃO implementado de propósito)** — ⛔ a **premissa central do
   prompt foi REFUTADA por medição**: `insufficient_budget` é `usable < 0` e dava **`False`** no
   caso do owner (folha 198 · 3 vagas · bid $0) ⇒ implementá-lo à risca **pioraria** o item. O
   predicado correto saiu das **duas fronteiras** medidas: folha **197** (fecha exatamente,
   viável) e **roster cheio a $200 / 0 vagas** (bid $0 **saudável** ⇒ `empty_spots > 0` é
   obrigatório). Veredicto de réplica: **3 limiares divergentes**, nenhum correto.
2. **Decisão do owner: opção (a)** — a flag nasce **no `salary_engine.draft_budget`**, ao lado de
   `over_cap`/`insufficient_budget`, **aditiva** (9 chaves antigas intactas):
   `cannot_fill_roster := empty_spots > 0 and usable < MIN_SALARY`. Baseline do engine **54 → 62**.
3. **Os DOIS defeitos de sinal corrigidos de uma vez** — o falso **negativo** (bid $0 inviável
   mudo) e o falso **positivo** já em produção (Miller Time! vermelho). Os 4 limiares inline
   saíram das telas; amarelos informativos ficam. Gate do [[O7]] **exit 0**; **535 testes verdes**.
4. **Smoke do owner (14/08)** — as duas direções confirmadas em produção. ✅

**Problema (screenshot do owner, cap_projector em simulação):** barra sticky com
**Cap projetado $198 · Restante $2 · Spots vazios 3 (min $2) · Bid Máximo $0** — plano de corte
em que o time **não consegue preencher o roster** ($2 para 3 vagas a $1 cada) — e a barra não
comunica nada. A simulação é o habitat natural do estado: é onde se exploram planos.

⛔ **A PREMISSA CENTRAL DO PROMPT ESTÁ REFUTADA — e implementá-lo à risca pioraria o caso.**
O prompt supõe que o estado é "capturado pela flag canônica". Não é:

```
insufficient_budget := usable_draft_budget < 0        (salary_engine.py:270)
```

Reprodução numérica do cenário exato (via `draft_budget`, não pelo screenshot):

| cenário | folha | resto | vagas | min | **BID** | `over_cap` | `insufficient_budget` | inviável **de fato** |
|---|---|---|---|---|---|---|---|---|
| **caso do owner** (19 jog.) | 198 | 2 | 3 | 2 | **$0** | False | **False** | **SIM** |
| limite de viabilidade (folha 197) | 197 | 3 | 3 | 2 | $1 | False | False | não |
| roster **cheio** a $200 (0 vagas) | 200 | 0 | 0 | 0 | **$0** | False | False | **não** |
| negativo (folha 210) | 210 | −10 | 1 | 0 | −$10 | True | **True** | sim |

⇒ **as duas flags dizem "tudo bem"** no caso que motivou o item. Trocar as comparações locais
pela flag canônica — o que o prompt pede — **apagaria** o pouco de sinal que hoje existe.

**Predicado correto (medido, não deduzido):** `empty_spots > 0 and usable < MIN_SALARY`.
Equivale a `raw_budget < empty_spots × $1` — não dá para completar o elenco. A linha do roster
cheio prova que **o `empty_spots > 0` é obrigatório**: bid $0 com 0 vagas é estado **saudável**.

**Inventário — superfície → fonte da decisão → limiar → erro** (veredicto de réplica:
**REPLICADO E DIVERGENTE — 3 limiares para a mesma grandeza, nenhum correto**):

| superfície | fonte da decisão | limiar | erro |
|---|---|---|---|
| `/cap_projector` — cor do bid (`cap_projector.html:196`) | **comparação inline em JS** | `< 0` → danger; `< 10` → warn | **falso negativo**: o $0 inviável fica *warn*, igual a um $9 saudável |
| `/cap_projector` — banner de aviso (`:207`) | **flag canônica** `insufficient_budget` | `usable < 0` | **falso negativo**: não dispara no $0 |
| `/league` — bid do bloco de destaque (`league.html`, macro) | **comparação inline em template** | `<= 0` | **falso POSITIVO**: roster cheio a $200/0 vagas pinta vermelho — é o caso **Miller Time!** hoje em produção |
| `/league` — linha "Atual: … bid" | **comparação inline em template** | `<= 0` | idem |
| `/team/<id>` | — | — | **não exibe bid** (só cap atual/projetado) |
| `/cuts/keeper_sheet` e `/admin/keeper_audit` | — | — | exibem `fa_budget` **sem tratamento nenhum** |
| `/draft_import` — alertas por time | **flags canônicas** | canônico | herda o falso negativo |

**Achado colateral (defeito de sinal oposto, já em produção):** o `<= 0` da `/league` **acusa
falso positivo** em time completo e dentro do cap — visível no card do **Miller Time!** ($200,
0 vagas, bid $0, pintado de vermelho). Corrigir só o falso negativo sem tratar este deixaria a
tela com os dois erros trocando de lugar.

**Por que parei aqui (e não implementei):** a restrição do próprio prompt diz — *"se a flag
existente não capturar exatamente o estado (verificar na diagnose), **reportar antes de
implementar variação, não decidir sozinho**"*. É exatamente o caso. Criar a flag envolve decisões
que são do owner: **onde** ela mora, **qual** o limiar e **qual** o tratamento visual.

**Opções (com recomendação, sem decidir):**
- ⭐ **(a) `salary_engine.draft_budget`** — é onde `over_cap` e `insufficient_budget` já moram;
  uma linha (`"cannot_fill_roster": empty_spots > 0 and usable < MIN_SALARY`) + teste no
  `salary_engine_test`, e **os 7 consumidores herdam** (incluindo keeper sheet, auditoria e
  `/draft_import`, hoje sem sinal). ⚠️ Exige liberar o `salary_engine`, que **esta sessão
  proibia**. **Recomendada:** é estado do budget, não de tela.
- **(b) derivação de display na rota** (`/budget` já devolve `cap_pct` e `shortfall`) +
  `_build_team_card`. Não toca o engine, mas **nasce em dois lugares** — a réplica que o [[L3]]
  gastou uma sessão para eliminar.
- **(c) corrigir o limiar inline em cada tela** — ⛔ mantém 3 réplicas e o limiar em JS/template.

**Escopo excluído por decisão registrada:** o excesso de teto de roster do achane é
[[OFF26-13]] 🔲, não este item.

**Nenhuma linha de código foi alterada nesta sessão** — logo o gate visual do [[O7]] não
disparou (o diff não toca `static/*.css` nem `templates/*.html`), o que é o comportamento
correto do disparo mecânico.

---

**F2 (13/08/2026, MAN-UX-BID0-F2) — a flag canônica e os DOIS defeitos corrigidos:**

**A flag nasceu no engine, ao lado das irmãs** (`salary_engine.draft_budget`), **aditiva** — as 9
chaves anteriores intactas:

```python
"cannot_fill_roster": empty_spots > 0 and usable < MIN_SALARY
```

**8 testes de fronteira novos** (`salary_engine_test.TestCannotFillRoster`), entre eles os três
casos que a diagnose mediu **antes de a flag existir**: 198/3 vagas (**inviável**, e as duas flags
antigas dizendo `False`), 197 (**fecha exatamente** — teto $1 para 3 vagas, viável) e **roster
cheio a $200 com 0 vagas** (**saudável**, o falso positivo do Miller Time!). Mais um teste que
falha se alguma chave antiga mudar. **Baseline do engine: 54 → 62.**

**Consumidores — nenhum recalcula limiar:**
- **`/cap_projector`** (barra sticky, a cada atualização da simulação): o **perigo** de folha,
  restante e bid passa a vir de `over_cap` / `insufficient_budget || cannot_fill_roster`; banner
  novo *"Cenário inviável: com $X não dá para preencher N spot(s) a $1 cada"*; a barra de
  progresso troca `cap_pct >= 100` por `over_cap` (o `>= 100` pintava de perigo a folha
  **exatamente** no cap). **Amarelos (`< 10`, `> 80%`) ficam** — aconselhamento, não estado
  (item 3 do prompt).
- **`/league`**: `bid_alerta` e `over_cap` vêm **prontos** do card; os **dois** pontos de template
  com `<= 0` e os **dois** com `cap_space < 0` saíram.
- **Auditoria pré-leilão**: a flag vira **aviso** no canal `warnings` que já existia. ⛔ **Não é
  uma 5ª classe de divergência** (o D2 fixa quatro e há teste que falha se alguém criar outra);
  sheet sem a chave → `.get()` → nada acontece, e as **34 fixtures congeladas seguem válidas sem
  edição**.
- **Keeper sheet**: a flag entra **só no payload**. **CSV e tabela byte-idênticos** — cabeçalho
  conferido (`Time,Keeper,Posicao,Salario,IR,Bid Maximo (time),Late drop`), zero coluna nova.

**Validação em cópia do banco, com os dois cenários CONSTRUÍDOS** (19 jogadores somando 198; e um
roster cheio somando exatamente 200):

| | bid | alerta | veredicto |
|---|---|---|---|
| time inviável (3 vagas, teto $0) | **$0** | **⚠️ + vermelho** | acende ✓ |
| roster cheio saudável (0 vagas, teto $0) | **$0** | nenhum | apaga ✓ |

⭐ **O mesmo número, $0, com tratamentos opostos** — é exatamente a discriminação que o item pedia,
e que nenhum limiar numérico local conseguiria fazer. Conferido nas **duas bases**: linha "Atual"
(corrente, pré-rollover) e herói do card (corrente, pós-rollover, com o gate fechado). No
`/budget`, o alerta **acende com o cenário inviável e apaga ao cortar 1 jogador** (teto $0 → $17).

**Gate do [[O7]] exercido** (o diff toca templates): suíte **exit 0**, 16 medições, 0 achados.
**535 testes verdes** no total.

⚠️ **Tropeço meu na validação:** a 1ª versão da sonda mirou o **herói** do card, que pré-rollover
é o bid **PROJETADO** — outra base, com os salários que eu construí já valorizados. O app estava
certo; a leitura é que estava errada. Corrigido para conferir as duas bases explicitamente.

**Cross-refs:** [[OFF26-18]] (o fencepost que define `usable`), [[L3]] (flags canônicas e a
regra de não recalcular limiar na tela), [[OFF26-13]] (o excesso de roster, fora daqui),
[[O7]] (o gate que não precisou disparar).

---
### UX20 — Board global de picks ilegível quando a ordem do round difere da ordem das linhas
✅ **FECHADO 17/08/2026 (MAN-UX20-DONE) — smoke de produção aprovado pelo owner** sobre o hash
live **`70a73bf`** conferido antes do smoke (gate [[PROC1]] cumprido) — implementado no mesmo dia
(MAN-UX20-F2 + FIX1 + FIX2), registrado e diagnosticado no mesmo dia — Prioridade **Média**

> ⚠️ **Nota de namespace:** o prompt de registro pedia o ID **UX15**, que já estava ocupado desde
> 10/08/2026 (*jogador pré-selecionado na página de trade*, seção acima). Reusar o ID colidiria com
> a baseline de dedupe do [[O3]] — o item nasceu como **UX20**, o próximo livre do namespace UX.

**Problema (observação visual do owner, 17/08/2026, board de 2026):** o board global de picks
ancora as **linhas por owner** (coluna fixa à esquerda) e as **colunas por round**, deixando a
posição da pick apenas na badge `#N` dentro da célula. Isso responde bem *"quais picks o time X
tem"* e falha para *"qual é a ordem do round N"*: quando a ordem de um round não coincide com a
ordem em que as linhas estão dispostas, a **leitura vertical da coluna induz uma sequência falsa**.

- **Caso concreto medido a olho:** no **Round 2**, a segunda célula de baixo para cima é a pick
  **#5**, não a #2 — a posição vertical não corresponde à ordem do round. O Round 1 estava alinhado
  (#1–#12 na ordem das linhas), o Round 3 repetia o desalinho do 2.
- **Custo para o usuário:** para reconstruir a ordem de um round é preciso **varrer as 12 badges** e
  reordenar mentalmente — trabalho que a disposição da tabela deveria estar fazendo.

**Direções candidatas — registradas, NÃO arbitradas** (a escolha é entregável da F1):

- **(a) Inverter o eixo** — colunas de round ordenadas pela ordem da pick (1→12), com a célula
  mostrando o **dono atual**. Perde a âncora por owner, ganha escaneabilidade da ordem.
- **(b) Toggle entre duas visões** — "por time" (a atual) × "por ordem de draft".
- **(c) Visão linear complementar por round** (`1.01…N.12`), **sem remover** o board atual.
- **(d) Outra forma** que a F1 identifique como superior às três.

**Comportamentos existentes a preservar em qualquer redesenho** (lista para a F1 conferir **contra
o código**, no espírito do [[MAN-METH-REG]] — nenhum deles foi verificado neste registro):

1. **Filtro por equipe** do board.
2. **Edição de admin por célula.**
3. **Indicação de pick trocada** (seta → time atual).
4. **Destaque "minha"** (pick do time do usuário logado).
5. **Suporte a múltiplas seasons.**

**Perguntas para a F1 (registrar, não responder aqui):**

- **De onde vem a ordem de cada round?** O R1 é projeção do lottery e os rounds seguintes seguem
  standings invertido ([[M16]]) — mas *onde essa ordem já está disponível para o template*, e ela
  chega pronta ou é reconstruída na tela? (É a pergunta que decide se (a)/(c) custam dado novo.)
- **Réplica:** a marcação/lógica do board **existe em mais de um lugar**? Candidatos a conferir:
  outras telas que rendem picks, **chips de pick no trade manager** e a **seção Picks do detalhe de
  time**. Um redesenho que toque só uma cópia deixaria as leituras divergentes.

**Relações:**

- **Distinto do [[UX5]]** (redesign da seção Picks em `/team/<id>`) — outra tela, e o problema lá é
  **densidade**, não ordem. Se a F1 encontrar marcação compartilhada, a fronteira precisa ser
  reafirmada em vez de fundir os itens.
- **[[S2]] / `board_mirror`** é a **fonte canônica de dono de pick**: ⛔ o redesenho **não pode criar
  leitura própria de ownership**.
- **[[M9]]** (o grid navegável que este board é), **[[M8]]/[[M15]]/[[M16]]** (a origem da ordem que a
  tela exibe).

#### F1 (17/08/2026, MAN-UX20-F1 — read-only; nenhuma escrita em código)

⛔ **A premissa central do registro está REFUTADA por leitura do código, e ela muda o parecer.**
O board **não** ancora as linhas por owner: elas são ordenadas pelo **`pick_number` projetado do
Round 1** ([picks.py:68-71](routes/picks.py#L68-L71)), com queda para `999` + nome (alfabético)
quando não há projeção. ⇒ o board **já é** a "visão por ordem de draft" — **do R1**. O eixo real é
**ordem do R1 × round**, não *owner × round*.

**A causa medida é outra:** o desalinho é **R1 × R2/R3**, e nasce do próprio [[M16]] — R1 = lottery,
R2/R3 = standings invertido (`_build_default_draft_order`). As linhas seguem o R1; logo R2/R3
divergem **exatamente nas posições que o sorteio embaralhou** (as 6 do lottery), e coincidem de 7 a
12. Reprodução mecânica do board de 2026 a partir do banco (`current_season=2025`, lottery 2026
travado 12/12):

| linha | time | R1 | R2 | R3 | rank 2025 |
|---|---|---|---|---|---|
| 1 | Miller Time! | #1 | #1 | #1 | 12º |
| 2 | Fazenda Pederasta | **#2** | **#5** | **#5** | 8º |
| 3 | Trust The Process | #3 | **#4** | **#4** | 9º |
| 4 | mongoloides | #4 | **#2** | **#2** | 11º |
| 5 | 3 peat… of pain | #5 | **#3** | **#3** | 10º |
| 6 | AlexTheDawg | #6 | #6 | #6 | 7º |
| 7–12 | (times de playoff) | #7–#12 | #7–#12 | #7–#12 | 6º–1º |

- ✅ **O valor observado pelo owner confere**: a **segunda linha** tem R2 = **#5**. ⚠️ A direção do
  registro (*"de baixo para cima"*) está **errada** — é a segunda **de cima para baixo**; de baixo
  para cima a segunda linha é `#11`.
- ⚠️ **R2 e R3 não são "dois desalinhos parecidos": são o MESMO vetor**, por construção
  (`tail_rounds = [2, 3]`, mesma chamada — [picks.py:266-277](routes/picks.py#L266-L277)). A visão
  linear precisa de **2 ordens, não 3**.
- ⚠️ **`board_mirror`/[[S2]] não é consumido pelo board.** É módulo de **sync** (desconta a permutação
  administrativa ao ingerir `/traded_picks`); em tempo de render a autoridade do dono é a **linha
  `Pick`** (`current_team_id`/`current_team_name`). A restrição do registro segue válida na prática
  (consumir `Pick`, nunca recalcular dono) — mas o texto que a justificava estava impreciso. ⭐ O
  docstring do `board_mirror.py` **já descreve a divergência R1×R2/R3** que produz este item: a
  álgebra do problema estava escrita no repo antes do sintoma ser registrado.

**Q1 — origem da ordem (respondida).** Camada: **backend, na rota** — `_build_pick_projections()`
([picks.py:159](routes/picks.py#L159)), chamada por `picks_page` **e** por `/api/picks`. O template
só lê `projection.pick_number`; **não há cálculo de ordem no template nem no JS**. A ordem **já
chega estruturada**: `matrix[season]["projections"][(team_id, round)] = {pick_number, locked}` —
completa por (time, round). ⇒ **rechavear para `{round: [(posição, time)]}` é transformação pura na
rota, zero query nova.** Critério por round: R1 = `DraftLotteryResult` (data-driven, [[M8]]/[[M15]]);
R2/R3 = `_build_default_draft_order(standings)` = seeds 1..6 por `rank 13-seed` + fixas 7..12.

- **Sem lottery para a draft season:** os **3 rounds** recebem a mesma ordem de standings ⇒ o board
  fica **perfeitamente alinhado** e o sintoma **não existe**. ⇒ ⚠️ **o defeito só se manifesta na
  janela em que há lottery travado para a draft season.**
- **Sem standings tampouco:** `proj` fica **vazio** — **nenhuma badge**, linhas em ordem
  **alfabética**. É o estado de 2027/2028 hoje (medido: standings só de 2025).
- ⛔ **Consequência de calendário, medida:** depois do rollover de 18/08 (`current_season` 2025→2026),
  `draft_season` vira **2027**, que não tem lottery **nem** standings de 2026 ⇒ `proj = {}` e a
  **2026 deixa de ser draft_season**. **O board inteiro perde TODAS as badges** — o sintoma do UX20
  desaparece e é substituído por *ausência total de ordem*. Quem for fazer a F2 precisa saber:
  **a janela para observar (e validar contra) o desalinho real fecha em 18/08** — depois disso só
  em cópia do banco.

**Q2 — os 5 comportamentos declarados, conferidos um a um:**

| # | Comportamento | Veredito | Evidência |
|---|---|---|---|
| 1 | Filtro por equipe | ✅ **confirmado, com ressalva** | `filterTeam` ([picks.html:145](templates/picks.html#L145)): mostra a linha do time **ou** linha alheia com célula cujo **dono atual** casa. ⚠️ Anda em passo fixo de 4 (`HEADER_COUNT = 4`, `i += 4`) — **assume 3 rounds** |
| 2 | Edição admin por célula | ⚠️ **DIVERGENTE** | O `✎` é renderizado para **todo usuário** — não há gate de admin no template; o CSS só o esconde até o `:hover` ([style.css:1514](static/style.css#L1514)). A proteção é **só server-side** (`@admin_required`), e `savePick` faz `.then(r => r.json())` + `location.reload()` **sem tratar 403** ⇒ para o não-admin a edição falha **em silêncio** |
| 3 | Indicação de pick trocada | ✅ confirmado | `is-traded` + `→ {{ pick.current_team_name }}` ([picks.html:70](templates/picks.html#L70)) + legenda no subtítulo |
| 4 | Destaque "minha" | ✅ **confirmado, com ressalva** | `is_mine = pick.current_team_name == my_team_name` — comparação **por NOME**, contra o espírito do [[S3]] (que moveu as linhas para `id` justamente porque `Team.name` é mutável) |
| 5 | Multi-season | ✅ **confirmado, com ressalva** | `PICK_SEASONS = [2025, 2026, 2027, 2028]` **hardcoded** ([picks.py:10](routes/picks.py#L10)); season sem pick é pulada em silêncio (2025 hoje) |

**Comportamentos existentes que o registro NÃO capturou** (⚠️ o primeiro é o mais funcional da tela):

1. ⭐ **Toda célula é um link para `/trades` com pré-seleção** ([[M9]]-FIX): pick minha →
   `?team_a=meu&pick_a=<id>`; pick alheia → `?team_a=meu&team_b=<dono>&pick_b=<id>`. É o que torna o
   board **ferramenta de trade**, e nenhuma direção pode perdê-lo.
2. **O board não distingue projeção travada de estimada** — mas o `/trades` distingue (`#` × `~#`,
   por `projection_locked` — [trades.html:337](templates/trades.html#L337)). O dado **existe** no
   board (`projections[...]["locked"]`) e o template **não o usa**. A mesma pick aparece mais
   qualificada no trade manager do que no board.
3. **Tooltip por célula** com season · round · original · atual + a dica de ação.
4. **Célula vazia `—`** para (time, round) sem pick; **banner** para usuário sem time vinculado;
   **card de odds do lottery** ([[M15]]/M15-FIX) no rodapé.
5. ⛔ **Nenhuma legenda explica o `#N`** nem que R2/R3 usam ordem diferente do R1 — o subtítulo só
   fala de cor ("azul = trocados"). **É a omissão que produz a leitura falsa.**
6. **`resetPick()` é código morto** ([picks.html:195](templates/picks.html#L195)): definido, nunca
   chamado ⇒ `/api/picks/<id>/reset` é **inalcançável pela UI**.
7. **"3 rounds" está TRIPLICADO**: `PICK_ROUNDS` (Python), `HEADER_COUNT`/`i += 4` (JS), `repeat(3,
   …)` (CSS, [style.css:1407](static/style.css#L1407) e :1539).
8. **`.picks-matrix` está sob o gate visual do [[O7]]** (`core.py:97`, geometria) — a F2 já nasce com
   rede.

**Q3 — réplica (respondida): 3 sítios renderizam pick, e só UM compartilha a fonte da ordem.**

| Sítio | Renderiza | Fonte | Veredito |
|---|---|---|---|
| `/picks` board | badge `#N` | `_build_pick_projections()` na rota | **origem** |
| `/trades` chips (JS) | `2026 Rd1 ~#5` + 🪙 | `/api/picks` → **a mesma** `_build_pick_projections` | ✅ **fonte comum** — e **mais rica** (`#` × `~#`) |
| `/team/<id>` seção Picks | `Rd{N}` + origem + notas | query própria ([league.py:166](routes/league.py#L166)) | **derivação própria, SEM projeção** (é a tela do [[UX5]]) |
| `/trades/proposta/<uuid>` | `{season} Rd{N}` | assets da proposta | **derivação própria, sem projeção** |
| `/picks/lottery/<season>` | tabela linear `pick · time · fonte` | `DraftLotteryResult` direto | **fonte irmã** (o R1 cru) |
| `/offseason` passo 2 | resultado do sorteio | `DraftLotteryResult` | irmã |
| `/league` | só `pick_count` | contagem | não renderiza pick |

- **Arrasta:** um redesenho **que só mexa no board** não arrasta ninguém. ⚠️ Mas **mexer em
  `_build_pick_projections` arrasta duas coisas**: os chips do `/trades` **e a valoração dynasty**
  (`pick_sleeper_id` monta `DP_<round-1>_<projected_pick-1>` — [dynasty_values.py:161](dynasty_values.py#L161)).
- **Órfão:** ninguém fica órfão. ⭐ Mas há um órfão **já existente**: `/picks/lottery/<season>` — que
  é a visão linear da candidata (c), **já implementada para o R1** — **não tem link a partir do
  board**; os únicos acessos são pelo `/offseason` (admin). A tela de auditoria tem *"← Voltar ao
  Picks"*; o caminho de ida não existe.

**Q4 — parecer sobre as candidatas:**

- **(a) inverter o eixo — ⛔ rejeitada como enunciada.** O eixo **já está invertido para o R1**, e o
  ganho declarado ("escaneabilidade da ordem") **já é o estado atual** daquele round. Pior: como R1
  e R2/R3 são vetores **diferentes por construção**, **uma única ordem de linhas não pode servir aos
  três** — inverter "de vez" só troca qual round mente. E o custo é real: some a leitura *"quais
  picks o time X tem"*, o filtro por equipe perde sentido e a célula-link muda de semântica.
- **(b) toggle — custo alto, ganho condicionado.** Preserva tudo, mas **duplica a marcação** da
  matriz, duplica o filtro JS (que já é frágil no passo de 4) e dobra a superfície do gate [[O7]] —
  em troca de um ganho que depende de o usuário lembrar de trocar de visão.
- **(c) visão linear complementar — barata e aditiva.** A ordem **já está estruturada na rota**;
  o bloco é **re-key puro, zero query nova**, o board fica **intocado** (os 5 comportamentos + os 8
  não listados preservados **por construção**) e a superfície do O7 se limita à marcação nova. E
  **R2 ≡ R3** ⇒ o bloco tem **2 ordens, não 3**.
- **(d) ⭐ RECOMENDADA — (c) enxuta + a legenda que falta, nesta ordem de valor:**
  1. **Rotular a origem da ordem no cabeçalho de cada coluna** (`Round 1 · sorteio` ×
     `Round 2/3 · classificação invertida`). ⛔ **É a única peça que ataca a CAUSA**: o usuário não
     lê uma sequência falsa por falta de tabela, lê porque **nada na tela diz que o R2 usa outra
     ordem**. Custo: uma linha de template.
  2. **Bloco linear por season** — "Ordem do draft": `#1 … #12 → dono atual`, **duas** colunas
     (R1 · R2=R3), alimentado pelo `projections` que a rota já monta.
  3. **Ligar o board ao `/picks/lottery/<season>`**, fechando o órfão de navegação.
  4. **De carona, se o owner quiser:** o `~#` × `#` do `/trades` no board (o dado já está lá) e o
     gate de admin no `✎` (hoje o não-admin vê um botão que falha calado).

  **Justificativa:** é a única direção que responde **às duas** perguntas do usuário (*"o que o time
  X tem"* e *"qual é a ordem do round N"*) em vez de trocar uma pela outra; não toca
  `_build_pick_projections`, logo **não propaga** para os chips do `/trades` nem para a valoração
  dynasty; e sobrevive ao estado pós-rollover (com `proj` vazio, o bloco simplesmente não é
  renderizado — como as badges).

⚠️ **Decisão da direção é do owner** — a F1 recomenda, não arbitra. ⚠️ **Produção não foi lida**
(sem credencial nesta máquina); todas as medições vêm do `dynasty.db` **local** em modo read-only.

#### F1b (17/08/2026, MAN-UX20-F1b — read-only; análise crítica pré-execução da direção (e))

O owner, ao ver o achado da F1 (R1×R2/R3 causador do desalinho), definiou a **direção (e)**: colunas
por round independentes, lista linear com nome do time na célula, rótulo de origem no cabeçalho,
clique realça picks do time, sem ✎. Análise crítica confronta as premissas da direção contra o
código e mapeia a anatomia da mudança.

**Premissas críticas verificadas:**

| Premissa | Evidência | Veredito |
|---|---|---|
| Ordem nasce no backend na rota | `picks_page()` → `_build_pick_projections()` (picks.py:51) | ✅ |
| Chega estruturada por `(team_id, round)` | `proj: {(season, round, team_id) → {pick_number, locked}}` (linhas 261, 274) | ✅ |
| R2 e R3 são o mesmo vetor | `tail_rounds = [r for r in PICK_ROUNDS if r != 1]` reutiliza `_build_default_draft_order(standings)` (linhas 268-277) | ✅ |
| Rechaveamento é transformação pura, zero query | Ordem já está em `proj`; reordenar por round é reordenação do dict existente | ✅ |
| Sem tocar `_build_pick_projections` | Transformação nova recebe `matrix` pronto, rota fica em cima | ✅ viável |

**Omissões do prompt (não refutam, apenas alertam):**

- R2 e R3 podem divergir no futuro se standings for refrescado entre draft real e redraft; hoje não.
- Célula vazia `—` em (time, round) sem pick original existe e precisa destino.
- Filtro JS acoplado a "exatamente 3 rounds" (passo de 4); novo JS sem acoplamento.
- Projeção travada vs estimada existe no template mas não é usada; direção (e) preserva.

**Anatomia da mudança por camada:**

| Camada | Hoje | Depois | Tamanho | Risco |
|---|---|---|---|---|
| **Rota (Python)** | `matrix[season]["projections"] = {(team_id, round): {...}}` | Transformação nova: `round_centered = {(season, round): [(position, team_id, ...)]}`; reordenação pura após `_build_pick_projections` | +20 linhas | 🟢 Nenhum — reordenação de estrutura existente |
| **Template** | Grid 4 colunas (times + 3 rounds), linha por time | 3 seções lineares por round, lista ordenada de picks com nome do time | 30 add / 60 rem = -30 linhas | 🟢 Simpler — sem grid minmax |
| **CSS** | `.picks-matrix` grid `minmax(150px, 1.4fr) repeat(3, minmax(110px, 1fr))` | `.draft-order-row` flexbox linear | 25 add / 15 rem = +10 linhas | 🟢 Mais seguro (sem reflow espremido) |
| **JavaScript** | `filterTeam(name)` com passo de 4 (`HEADER_COUNT=4, i+=4`) | `highlightTeam(name)` com toggle por elemento vivo + novo `filterTeam` simples | 20 add / 15 rem = +5 linhas | 🟡 Mecânica muda, sem testes automáticos |

**Diff total:** ~30 linhas neto. **Nenhum impacto em `/api/picks` ou `/trades`** (restrição respeitada).

**Destino dos 5 comportamentos preservados:**

| # | Comportamento | Status | Forma |
|---|---|---|---|
| 1 | Filtro por equipe | ✅ Continua | `filterTeam` refatorado — itera `.draft-order-row` por `data-team-name`, sem passo de 4 |
| 2 | Edição admin por célula | ❌ Removido (F15) | UI: ✎ desaparece; backend: check consumidores antes de remover rota (escopo de F15) |
| 3 | Indicação de pick trocada | ✅ Preservado | `is-traded` + `→ {{ pick.current_team_name }}` vira texto `(via <original>)` na linha |
| 4 | Destaque "minha" | ⚠️ Convive com realce | 3 opções: (a) cor de fundo + borda sutil de realce, (b) borda/box-shadow sutil, (c) abandona cor em favor de realce único — visual pending F2 |
| 5 | Multi-season | ✅ Preservado | Mesmo `PICK_SEASONS`; seções por season independentes; sem projeção = seção não renderiza |

**Comportamentos existentes não capturados no registro (F1, linhas 6757-6776) — destino:**

| Comportamento | Direção (e) | Risco |
|---|---|---|
| ⭐ **Link trade pré-seleção (M9-FIX)** — toda célula navega para `/trades?team_a=...` | ⚠️ **Migra para alvo discreto dentro da linha** — gesto (a) decidido: clique realça, trade fica em alvo explícito (ícone? link discreto?) | 🔴 **Alta** — perda de funcionalidade sem forma concreta; F2 deve resolver |
| **`projection.locked` (travada vs estimada)** — dado existe, não é renderizado | ✅ Preservado — não é escopo desta direção; carregar de F1: `/trades` usa `#` × `~#`, board não | 🟢 Baixa |
| **Tooltip** com season · round · original · atual | ✅ Preservado — atributo `title` na linha | 🟢 Nenhum |
| **Célula vazia `—`** para sem pick | ✅ Renderizada — lista simples deixa o hiato óbvio | 🟢 Nenhum |
| **Banner e card de odds** | ✅ Intactos — fora do redesenho | 🟢 Nenhum |
| **`resetPick()` código morto** | ✅ Removido de carona — função JS morta | 🟢 Nenhum |

**Casos degenerados:**

| Caso | Comportamento | Risco |
|---|---|---|
| Sem projeção (2027/2028 hoje; 2026 após rollover) | Seção não é renderizada (como badges hoje) OU renderiza vazia com nota | 🟢 Nenhum — viável em ambos sentidos |
| Viewport estreito (mobile) | Flexbox reflui naturalmente; muito estreito (<300px): `flex-direction: column` em media query | 🟢 Melhor que hoje (sem "apertão" de colunas) |
| "3 rounds" triplicado (Python/JS/CSS) | Python: intacto (outros consumidores); JS: sem passo de 4 (novo `filterTeam` itera elemento); CSS: nenhum `repeat(3)`; acoplamento reduz de 3 → 1 sítio | 🟢 Positivo — dívida reduz |

**Gate visual (O7):**

Hoje `.picks-matrix` é exercida por testes de geometria. Depois:
- ✅ `.draft-order-section`, `.draft-order-row` são estruturas lineares simples
- ✅ Geometria previsível — sem minmax rebotes
- ⚠️ Novo bloco é novo sítio para exercer, mas simpler que grid
- **Parecer:** O7 fica mais seguro.

**Veredito de execução:**

- **F2 é seguro?** ✅ SIM — nenhuma premissa refutada, transformação viável, riscos mapeados, 1 decision point (forma do trade link)
- **Tamanho?** ~30 linhas neto (moderado) — sem toque em lógica pura
- **Bloqueadores?** ⚠️ 1 decision point: **forma concreta do alvo de trade discreto** — precisa estar resolvida na F2
- **Janela?** ✅ Executável a qualquer momento — ideal pré-18/08 para validar em vivo; pós-rollover, seções vazias (não observável mas funcional). **Nenhum bloqueador operacional.**

#### F2 (17/08/2026, MAN-UX20-F2 — o redesenho construído)

**Arbitragens do owner incorporadas:** alvo de trade = ícone **⇄ discreto na linha** (`opacity .6`,
opaco no hover); convivência realce × "minha" = **duas cores** (verde de "minha" fixo, azul de
destaque por cima; a célula que é as duas coisas recebe um `linear-gradient` dos dois).

**O que nasceu — 3 colunas lineares, uma por round:**

- **Rota** (`picks_page`): transformação `round_centered[season][rnd] = [{position, team_id,
  team_name, pick, locked}, …]`, **ordenada por `pick_number`**. ⛔ **Re-key puro sobre o
  `matrix` que já existia — zero query nova, `_build_pick_projections` intocada** (a restrição que
  protege os chips do `/trades` e a valoração dynasty). A `matrix` **permanece** no contexto: é o
  que alimenta a transformação.
- **Template**: macro `coluna_round(entries, rnd, titulo, origem)` — **um só corpo de célula para
  os 3 rounds**, contra a triplicação que a F1 mediu. Célula = **posição `R.PP`** (`1.05`, `2.02` —
  formato pedido) · **nome do time atual** · **`via <original>`** quando trocada (substitui a seta)
  · **⇄**. Cabeçalho carrega o rótulo da origem: *Round 1 · Sorteio (lottery)* × *Round 2/3 ·
  Classificação invertida* — ⭐ **a peça que ataca a causa** apontada pela F1.
- **JS**: `highlightTeam` (toggle por `data-team-name`, listener delegado no `DOMContentLoaded`,
  ignorando clique no `⇄`) + `filterTeam` reescrito. ⛔ **O passo fixo de 4 (`HEADER_COUNT`,
  `i += 4`) morreu** — o novo itera `.draft-order-row` viva, **sem saber quantos rounds existem**.
- **CSS**: `.picks-order-container` (flex, colunas empilham em ≤720px) + `.draft-order-*`.
  ⛔ **Todo o bloco `.picks-matrix*` foi REMOVIDO** (~3,1 KB), incluindo o `repeat(3, …)` das duas
  media queries: a dívida do "3 rounds" **caiu de 3 sítios para 1** (`PICK_ROUNDS`, no Python).

**⚠️ Um valor da lista de validação do prompt não confere — e quem está errado é o prompt.**
O enunciado esperava *"1.05 = Cangaceiros via 3 peat"*; o render diz **`1.05 · Trust The Process ·
via 3 peat… of pain`**, e o banco confirma: a pick R1 de original `3 peat` tem
`current_team_name = "Trust The Process"`. Os outros três batem — `1.06 Miller Time! via
AlexTheDawg`, `2.02 Trust The Process via mongoloides`, `2.05 Tropa do Jarra via …` (⚠️ o prompt
diz *"via Julia Mendes"*; o nome vivo do time hoje é **Fazenda Pederasta** — posição e dono
conferem, o rótulo é o `Team.name` atual, exatamente o comportamento do [[S3]]).

**Remoções (lado cliente apenas — a rota PATCH continua viva, é escopo do [[F15]]):** o `✎`, o
modal `#pick-modal`, `openPickEdit`, `closePick`, `savePick` e o `resetPick()` que a F1 achou
**morto**. Render medido: **0 ocorrências** de `pick-edit-btn`/`openPickEdit`/`pick-modal`.

**Degenerados, com comportamento definido:** season **com picks e sem projeção** (2027/2028 hoje;
2026 depois do rollover) rende **frase explicativa** no lugar das colunas — não coluna quebrada,
não silêncio; season **sem pick nenhuma** segue pulada como sempre. Entrada com projeção mas **sem
linha `Pick`** rende `—`. Viewport ≤720px: `min-width: 100%` ⇒ colunas **empilham**.

**Sonda do [[O7]] reapontada:** a página `picks` media `.picks-matrix`, que **deixou de existir** —
o seletor foi trocado para `.picks-order-container` (`core.py`), com a nota atualizada. ⚠️ Sem isso
o gate mediria um seletor ausente e o verde não significaria nada.

**Verificação local (sem push — deploy e smoke de prod são do owner):**
- **Ordem conferida contra o banco**, coluna a coluna, e contra a reprodução mecânica da F1: R1 =
  lottery (`1.01` Miller Time! … `1.06` Miller Time! via AlexTheDawg), R2 e R3 = standings
  invertido, **idênticos entre si na ordem** — o desalinho que originou o item agora está
  **rotulado**, não escondido.
- ⭐ **Smoke em navegador real** (Playwright, mesmo perfil da sonda: cópia do banco, sessão por
  cookie): 36 linhas, 36 ⇄; clique em `mongoloides` acende **6/6** das dele; **as 5 linhas
  `is-mine` continuam verdes durante o realce de outro time**; 2º clique limpa; clique em outro
  time troca (4/4); filtro deixa 6 visíveis e limpa de volta a 36; clique no ⇄ **não** dispara
  realce. **Zero erro de JS** (o único console error é o `fetch` de `/api/admin/last_sync` do
  `base.html`, que não resolve sob `file://` — pré-existente e alheio a este diff).
- **Gate do [[O7]]: exit 0** nas 4 larguras (o diff toca CSS **e** template — disparo mecânico).
- **Suítes:** `salary_engine` 62 · `cap_regua` · `cap_projetado` 27 · `player_search` ·
  `poka_yoke` · `template_js` 3 · `espn_gate` 33 · `visual_probe` 28 · `late_drop` 64 ·
  `keeper_exclusion` 36 — **todas OK**. Auditor do [[O5]]: exit 0.

⚠️ **Falta o smoke de produção** (é do owner) — por isso o item está ⚠️ e não ✅.
⚠️ **Não coberto por teste automatizado:** o board não tem suíte própria; a rede desta mudança é o
smoke de navegador acima + o gate visual. Um `picks_test.py` cobrindo a transformação
`round_centered` seria item próprio, se o owner quiser.

#### FIX1 (17/08/2026, MAN-UX20-F2-FIX1) — densidade e alinhamento, **medidos** antes de corrigir

Dois achados cosméticos do smoke local do owner. ⭐ **Nenhum dos dois foi corrigido por palpite —
a geometria foi medida no navegador em 13 larguras antes de tocar o CSS**, e a medição mudou o
diagnóstico do segundo.

**1. Densidade — a linha quebrava em 2 e desigualava a altura.** Medido: alturas de **65, 71, 93,
116 e até 135px** na mesma coluna, porque `.draft-order-team` era item flex **sem `min-width: 0`**
— sem isso o ellipsis não age e o texto quebra dentro do item. Corrigido com `white-space: nowrap`
na linha + `min-width: 0` + `text-overflow: ellipsis` nos itens de texto, padding e gaps enxutos.
**Resultado medido: altura ÚNICA de 32px em todas as larguras**, e a seção de 2026 caiu de
**953px → 492px** (os 12 × 3 cabem numa viewport desktop sem rolagem interna).

⭐ **O "via" cede espaço ANTES do nome do time** (`flex: 0 8 auto`): quando falta largura, o que
some é o contexto, não a informação. A 1600 e 1280px **nada trunca**; abaixo disso o `title` da
linha (season · round · original · atual) segue carregando o texto inteiro.

**2. Alinhamento — a causa medida NÃO era o cabeçalho.** A hipótese natural (rótulo de origem mais
longo empurrando a lista para baixo) foi **refutada pela medição**: os 3 cabeçalhos têm **36px em
toda largura** e os `listTop` **coincidiam** de 960px para cima. O desnível real vinha do
`flex-wrap`: a partir de **900px** uma coluna inteira **caía para a linha seguinte** e passava a
começar numa altura própria — o que o owner viu como "o Round 2 começa mais baixo".

**Correção estrutural:** o container virou **grade** — `grid-template-columns: repeat(auto-fit,
minmax(260px, 1fr))`. Colunas da mesma faixa alinham o topo **por construção**, e a que sobra desce
como faixa inteira, não como coluna solta. ⛔ **`auto-fit`, não `repeat(3, …)`**: o CSS continua
**sem saber quantos rounds existem** — a triplicação que o F2 quitou não volta. O cabeçalho ganhou
**altura fixa (2rem) + `nowrap`** como cinto de segurança; medido que **não corta** em 1280, 1024,
860 nem 390px.

**Verificação:** alturas uniformes e topos coincidentes nas 13 larguras varridas; **regressão zero**
no smoke de navegador (realce 6/6, as 5 linhas `is-mine` verdes durante o realce, 2º clique limpa,
troca de time 4/4, filtro 6 → 36, ⇄ sem disparar realce, zero erro de JS novo); gate do [[O7]]
**exit 0** nas 4 larguras; suítes e auditor verdes. ⛔ **Diff é CSS puro** — rota, transformação
`round_centered`, template e JS **intocados**.

#### FIX2 (17/08/2026, MAN-UX20-F2-FIX2) — altura TRAVADA + densidade no meio-termo

⚠️ **O drift do owner NÃO reproduz em headless — e a correção foi feita mesmo assim, por
construção.** Medido em ponto flutuante (o FIX1 media arredondado, que é onde um desvio
acumulativo se esconde): **31,750px idêntico** nas 36 linhas, drift **0,00** entre colunas, em
dpr 1 / 1,25 / 1,5. Também medida a altura **natural** (com o `min-height` neutralizado): 31,75
uniforme, **inclusive nas linhas com emoji**.

⇒ o que sobrou é o **mecanismo**, não a instância: `min-height` é **piso, não trava** — quem
decidia a altura era o **conteúdo**, e o conteúdo **difere por coluna** (a distribuição do `via`
não é a mesma nos 3 rounds; o R2 é o que mais tem). Basta uma fonte com métrica diferente da desta
máquina para uma linha crescer, e o erro **acumula até a 12ª** — exatamente o padrão relatado.
**Não dava para reproduzir o ambiente do owner, mas dava para tornar a altura imune a ele.**

**A trava:** `height: 38px` + `box-sizing: border-box` + `overflow: hidden` + `line-height` fixa.
Nem conteúdo nem estado mexem na altura. ⛔ **Estado só muda COR** — a borda é sempre `1px` (as
regras `is-mine`/`highlighted` tocam apenas `border-color`/`background`) e o realce usa
`box-shadow`, que **não ocupa layout**. Verificado por medição: `normal`, `is-mine` e `highlighted`
**todas em 38,000px**.

**Densidade — meio-termo:** 32px → **38px**, com tipografia um passo acima (time `.88rem`,
posição `.82rem`, `via` `.76rem`, ⇄ `.9rem`) e `gap` de 4px. A seção de 2026 termina em **813px**:
os **12 × 3 + cabeçalhos cabem numa viewport de 900px sem rolagem interna**, com respiro visível
contra o FIX1. As 3 colunas ficam lado a lado até **860px**; abaixo disso empilham, como no FIX1.

⭐ **O gate do [[O7]] pegou uma regressão que a medição de geometria não pegaria — e bloqueou o
push:** 81 achados de **transbordo a 390px**. Causa medida: item de grade tem `min-width: auto` =
**min-content**, e como cabeçalho e linha são `nowrap`, o min-content deles virou **piso da
trilha** — a coluna calculou **370,7px dentro de um container de 358px** e o conteúdo vazou. Fix:
**`min-width: 0` no `.draft-order-column`**, que é o que devolve a decisão de largura ao container
e deixa o `overflow: hidden` de cada peça truncar. ⚠️ **Registro honesto:** o `min-width: 0` do
FIX1 foi posto nos itens de texto **e faltou no item de grade** — o gate cobriu o vão.

**Verificação:** altura **38,000px única** e drift **0,00** nas **14 larguras** varridas (1600 →
390); regressão zero no smoke (realce 6/6, 5 linhas verdes preservadas, 2º clique limpa, troca 4/4,
filtro 6 → 36, ⇄ sem disparar realce, **console limpo** fora do `last_sync` pré-existente); gate do
[[O7]] **exit 0** nas 4 larguras; 6 suítes e auditor verdes. ⛔ **Diff segue CSS puro.**

#### FECHAMENTO (17/08/2026, MAN-UX20-DONE) — smoke de produção aprovado

**Cadeia validada em produção:** F2 (`24f92a9`) + FIX1 (`08d5e25`) + FIX2 (`70a73bf`), com o
**deploy live conferido no hash `70a73bf` ANTES do smoke** — o [[PROC1]] pôde ser cumprido aqui
porque o diff toca `static/style.css`, que é **artefato público servido**; nas sessões em que o
diff é só Python/template autenticado essa prova não existe e a confirmação fica circunstancial.

**Aprovado pelo owner, item a item:** layout de colunas por round independentes · densidade de
38px do FIX2 · ⭐ **a linha `.12` das três colunas alinhada no navegador onde o drift era
observado** (a prova que faltava — o FIX2 travou a altura por construção **sem conseguir
reproduzir** o drift localmente) · realce por clique com o verde de "minha" preservado · ⇄ com
pré-seleção · filtro por equipe · dados do R1 conferindo com a referência da liga.

⚠️ **A divergência local × prod observada durante o smoke local NÃO é item aberto.** As trocas do
R1 no banco local divergiam do board de produção: o `dynasty.db` do repo é **seed defasado**, não
espelho do vivo (`/data/dynasty.db` no Render — a distinção está no `CLAUDE.md`). **Prod é a
superfície canônica e confere**; nenhuma pendência de dado nasce daqui.

**O que este item deixa para trás:** a parte de **UI** do [[F15]] (o `✎`, o modal e os handlers)
saiu de carona no F2 e **está fechada** — o que resta lá é só a **rota PATCH de backend**, viva de
propósito até a conferência de consumidores. O órfão de navegação apontado pela F1
(`/picks/lottery/<season>` sem link a partir do board) **não foi fechado** — a direção (e) do owner
substituiu a candidata (c) que o previa.

---

### OFF26-26 — Rookie draft 2026 realizado FORA do board do Sleeper: incidente, diagnose e reparo one-shot
✅ **Concluído 18/08/2026 (auditoria limpa em produção)** — Prioridade **Alta** — trilha
MAN-OFF26-24-REG / MAN-OFF26-24-F1 / MAN-OFF26-24-FIX (`bcf8a5d`) / MAN-OFF26-24-FIX-b (`d77314b`)

> ⚠️ **Nota de namespace:** as sessões desta trilha foram nomeadas `MAN-OFF26-24-*` em regime de
> urgência, mas o ID **OFF26-24 do backlog já pertencia** ao script do board da fantasma (e
> OFF26-25 ao gate ESPN do rollover). O item vive como **OFF26-26** — próximo livre — pelo
> precedente UX15→UX20 (a baseline de dedupe do [[O3]] não se fura). Os desdobramentos seguiram a
> mesma regra: fix do sync = [[OFF26-27]], `/auction` = [[OFF26-28]], picks 2026 = [[OFF26-29]].

**Registro retroativo — exceção consciente à ordem REG→F1→F2:** a operação rodou em urgência
(17-18/08, madrugada) com os caps precisando estar corretos ANTES do planejamento da FA auction de
24/08; os prompts existiram e estão na trilha da conversa. Este registro consolida o ciclo.

**Linha do tempo (17→18/08):**

1. 17/08: tabela ESPN definitiva travada → **rollover executado** (season 2025→2026, gate
   [[OFF26-25]] exercido no ciclo real) → **rookie draft realizado via WhatsApp**, fora do board
   do Sleeper; os owners inseriram as picks manualmente nos rosters.
2. Sync intermediário criou a classe como **31 stubs** — `$1, unknown, needs_review=1,
   contract_start_season=2025`; 5 jogadores adicionados ao Sleeper após o sync nem existiam no
   Manager. O draft linear da liga real ficou `pre_draft` — **o importador OFF26-3 nunca teve
   insumo** e não foi usado.
3. **F1 (read-only):** raiz do carimbo 2025 = `sync_sleeper.py:304` usa a **constante de módulo**
   `CURRENT_SEASON` (fixa em 2025, comentada *"fallback — prefer get_current_season()"*) enquanto o
   rollover avança o AppConfig — fonte estagnada. **Achado irmão** no `/auction` (2025 hardcoded no
   cliente, 4 campos + `now_year` nunca passado pela rota → [[OFF26-28]]). `record_acquisition` no
   caminho de update **cura** salary/contract_year/contract_start_season/acquisition_type/
   espn_ref_value + grava SalaryHistory/AuctionLog, mas **NÃO limpa needs_review**; a fila de
   review não esvazia (muda de Cat A → Cat B); `RookieEspnValue` 2026 íntegro (âncora Love
   sid 13287). Preview do importador provado read-only por AST.
4. **FIX (`bcf8a5d`):** `wa_draft_2026_fix.py` — one-shot molde M2/off26_20_fix, **toda escrita
   pela porta canônica** `record_acquisition`. Preflight obrigatório: resolução Brown-safe contra
   o pool global (nome+posição+time NFL; posição por PERTENCIMENTO — lição FIX11/Hunter), franquia
   por exato → normalizado → hint de owner (só os 2 documentados), estados classificados
   (stub/ausente/já-aplicado; INESPERADO aborta), guarda de fase (`current_season=2026` +
   `rollover_done`) e **âncoras de salário** (Love $54 · Tate $12 · Price $9 · Tyson $6 · Sadiq $2
   · demais $1) — divergência impede a escrita (`--allow-anchor-mismatch` só para ensaio). Apply:
   backup conferível obrigatório, valor pela MESMA precedência do importador (coluna → store → $1
   nativo do `year1_salary`), **clear explícito de needs_review** com trilha `review_approved`
   molde M2, verificação in-transação, **idempotência por `wa_draft:2026:<round>.<pick>`**.
   Auditoria molde OFF26-4 (exit 0 = limpo) + smoke de escopo (hash dos players fora dos 36; toda
   linha nova de SH/AL pertencente ao conjunto). Ensaio local completo sobre seed adaptado: 36/36,
   os 3 caminhos de franquia exercitados, gate de âncora recusando sem flag, idempotência provada.
5. **FIX-b (`d77314b`):** o preflight de produção reprovou com **1 achado real** — Nicholas
   Singleton (1.11, sid 13288) em `free_agent/$1/needs_review=False`, a assinatura exata da
   **aprovação Cat A com defaults** (cenário 5 da F1: alguém aprovou o stub na fila antes do
   reparo). Classificador ganhou o terceiro estado elegível **"aprovado em review (update)"** com
   critério ESTREITO (free_agent + $1 + espn 0 + css ∈ {2025,2026}); qualquer outra assinatura
   segue INESPERADA. Ensaio: cenário A (Singleton fabricado → 36/36) e B (salary $2 → aborta).
6. **Execução em PRODUÇÃO (18/08, madrugada):** backup
   `/data/dynasty_prod_backup_2026-08-18_wa_draft.db` → preflight **36/36** (âncoras OK, 30 stubs
   + 1 aprovado em review + 5 criações) → apply → **AUDITORIA LIMPA 36/36** (salário, ano 1,
   season 2026, rookie_draft, review zerado, time, trilha SH+AL) → smoke de escopo OK →
   idempotência disponível. Snapshots de segurança do Sleeper em `/data` (traded_picks + draft
   2026 pre_draft).

**Folhas pós-reparo (informativo):** Haliburton Time! $209, SAFIEL $208, mongoloides $208 — acima
do teto; **enquadramento via cortes de 20/08** (comportamento esperado da régua [[OFF26-16]]).

**Decisões de produto registradas:**

- **FA auction de 24/08 VOLTA ao fluxo da liga fantasma** ([[OFF26-24]] segue plano A) — a ideia
  de usar o draft da liga real foi **descartada**: picks 2026 vivas + risco às picks 2027 trocadas.
- Draft da liga real permanece **pre_draft**; picks 2026 mortas **por governança** (aviso no
  grupo). Pendências funcionais no Manager → [[OFF26-29]].

**Nota metodológica (candidata à família [[MAN-METH-REG]] — registrada, NÃO consolidada):**
a operação de emergência inverteu REG→execução; o custo foi trilha retroativa — o benefício foi
cap correto no prazo. ⭐ **O preflight abortando no Singleton validou o desenho: a máquina recusou
um estado imprevisto que a pressa não teria visto.**

**Desdobramentos:** [[OFF26-27]] (raiz no sync — corrigida na mesma janela deste registro),
[[OFF26-28]] (`/auction` hardcoded, prazo 24/08), [[OFF26-29]] (picks 2026 tradáveis no Manager,
F1 feita). Relações: [[OFF26-3]] (o importador que ficou sem insumo), [[OFF26-23]]/[[OFF26-25]]
(os poka-yokes da semana, exercidos no ciclo real), [[M2]] (a fila de review cujo Cat A produziu o
caso Singleton), [[E2]]/[[DP3]] (o store que deu os salários).

---

### UX22 — Board de picks: visão de inventário quando a ordem da season não existe
> ✅ **FECHADO 19/08/2026 (MAN-SESSION-CLOSE-1908): smoke de produção confirmado pelo owner** — inventário de 2027/2028 no ar com as contagens da liga real. Commit `aac4e97`. Seção movida verbatim (regra O3).
⚠️ **F2 implementada 18/08/2026 (MAN-UX21-REG-F2, registro + execução na mesma janela) —
smoke de produção PENDENTE** (gate [[PROC1]]) — Prioridade **Alta** (semana de trades em curso)

> ⚠️ **Nota de ID:** o prompt pedia **UX21**, ocupado desde 17/08 (*página do lottery sem porta
> de entrada*). Nasceu **UX22**, próximo livre — precedente UX15→UX20, baseline de dedupe do [[O3]].

**Problema (feedback do owner, 18/08, com print):** após a ocultação das picks consumidas
([[OFF26-29]]), as seções 2027/2028 do board mostravam apenas *"ordem ainda não definida"* —
nenhuma pick listada. A informação de **POSSE** existe integralmente na tabela `Pick` (dono
original, dono atual, rodada, season); o que não existe antes do sorteio/classificação é a
**ORDEM** dentro da rodada. Na semana mais movimentada de trades, a página não respondia
*"quantas picks tenho, de quem, em que rodada"*.

**F2 — visão de inventário (leitura pura):**

- **Rota** ([routes/picks.py](routes/picks.py)): season presente na matriz cujo `round_centered`
  ficou sem rodadas ganha `inventory[season]` — picks por rodada ordenadas pelo **nome do dono
  atual** (alfabética é visivelmente não-draft: nada aqui inventa ordem) + contagem por time.
  Consumidas já saíram rio acima (predicado [[OFF26-29]] intocado).
- **Template** ([templates/picks.html](templates/picks.html)): a célula do inventário reusa a
  anatomia do board [[UX20]] (`draft-order-row`, 38px, `via <original>` na trocada, verde de
  "minha", ⇄ com pré-seleção) **sem o número de posição**; cabeçalho da coluna diz
  *"Round N · X picks · ordem pendente"*; chips de contagem por time no topo da seção; o aviso
  antigo **encolheu** para uma linha dentro da visão (*"a ordem virá do sorteio × classificação
  invertida e nada aqui a inventa"*). ⭐ Como as células carregam `data-team-name`, **o filtro por
  equipe e o clique-realça existentes funcionam no inventário sem uma linha de JS nova**.
- **Season com ordem → comportamento atual intacto:** quando o lottery/classificação nascer,
  `round_centered` ganha as rodadas e a visão de inventário **sai de cena sozinha** — nenhuma
  flag, nenhum estado novo.
- ⛔ Intocados: lógica de ordem (lottery/classificação), card Lottery Odds, predicado de
  consumida, schema, sync.

**Verificação:** `picks_inventory_test.py` (5 testes — posse+proveniência sem posição, gancho do
filtro nas células, contagem batendo com a tabela, consumida fora de qualquer visão, **render
ordenado intacto** via fixture de standings 2026→draft 2027); smoke com o app real sobre a cópia
do ensaio: **72 células = 72 picks** da tabela (2027+2028), chips somando 72, 2 seções de
inventário, nomes reais com emoji íntegros; **gate [[O7]] exercido e exit 0** (o diff toca
template — 4 larguras × 4 páginas limpas); suítes verdes (inventário 5, pick_consumed 13,
cap_projetado, engine 62, template_js, player_search, poka_yoke).

**Fecha ✅ quando:** smoke de prod do owner — board mostrando o inventário de 2027/2028 com as
contagens da liga real (gate [[PROC1]]: conferir o hash deployado antes).

**Relações:** [[OFF26-29]] (a ocultação que expôs o vazio — e o predicado que o inventário
herda), [[UX20]] (a anatomia de célula reusada), [[UX21]] (colisão de ID — item distinto),
[[M9]]/[[M9]]-FIX (o ⇄ preservado), [[M16]] (de onde a ordem virá quando existir).

---

### UX23 — Cap Projector mira a season de planejamento real (helper de fase + modo corrente D9)
> ✅ **FECHADO 19/08/2026: smoke de produção confirmado pelo owner** — título 2026 + tag FOLHA CORRENTE, banner verde, board DP1 populado, cenário DP2 somando. Commit `296f166`. Seção movida verbatim (regra O3).
⚠️ **F2 implementada 18/08/2026 (MAN-UX23-F2) — smoke de produção PENDENTE** ([[PROC1]]) —
Prioridade **Alta** (janela 20-24/08) — F1 18/08 (MAN-UX23-REG-F1, relatório na trilha da conversa)

**Sintoma (print do owner, 18/08):** pós-rollover o projector virou "2027" no meio da janela da
auction de 2026 — banner de ESPN respondendo a pergunta errada, Δ +$0 em toda linha, board DP1
**vazio** e cadeia DP2 **ignorando rookie em silêncio** (`rookie_espn_adjusted(sid, 2027)` → None
→ `continue`).

**O que a F1 provou:** alvo `get_current_season() + 1` **inline em 6 sítios** (rota:
data/budget/rookies; template: título ×2, rótulo, `SEASON_PROJ` do JS), **zero** helper e **zero**
gate de fase — a `/league` fecha a projeção com `_projection_open()`; o projector não tinha
equivalente. ⭐ A base correta **já existia**: modo D9 (`compose_budget(projected=False)` — *"o
salário armazenado já está valorizado; re-projetar duplicaria"*). O Δ +$0 **não era bug de
cálculo**: era `MAX(sal, floor(0.5×espn)) = sal` — a resposta certa para a pergunta errada.

**F2 (decisões do owner no REFINE: sinal = opção b/evidência AuctionLog; colunas saem; título
explicita o modo):**

- **`models.planning_target_season()`** — fonte única de fase: `current+1` pré-rollover ·
  `current` pós-rollover com auction pendente · `current+1` quando existir **evidência** de
  leilão (`AuctionLog fa_auction` da season corrente ≥ **`AUCTION_EVIDENCE_MIN = 3`**).
  ⭐ **Calibração do limiar (delegada ao Code, documentada no código):** leilão real entra em
  LOTE pelo importador (dezenas); 1-2 registros são assinatura de teste manual avulso no
  `/auction` — que não pode virar a chave no meio da janela 20-24/08. Hoje o [[OFF26-28]]
  (carimbo 2025) ainda "protege" por acidente; o limiar cobre o vão quando o 28 for corrigido.
  ⛔ `auction_done` (passo 7) **não é insumo** — flag manual fica como está.
- Os **6 sítios consomem o helper**: as 3 rotas via `_planning_ctx()`; títulos, rótulo do cap e
  `SEASON_PROJ`/`MODE` do JS **vêm do servidor**. Guardas **AST** falham se `current+1` inline
  voltar (rota E template).
- **Modo corrente**: colunas Sal-próximo/Δ **saem** (mostrar Δ zerado seria responder a pergunta
  errada), ordenação desempata pelo salário corrente, POST `/budget` envia `projected:false`
  (parâmetro D9 **que já existia** — consumido, não criado), título ganha a tag
  **"FOLHA CORRENTE · AUCTION 2026"**. Modo projetado (pós-virada): comportamento histórico
  **intacto**.
- **Banner, badge PROV, board DP1 e cadeia DP2 voltaram SOZINHOS** pela mudança do target nas
  queries — zero lógica nova, como a F1 previu.

**Verificação:** `planning_target_test.py` (12 — 3 fases; limiar 2 não vira × 3 vira; 36
`rookie_draft` **não** contam (o estado real de prod); `fa_auction` de outra season não conta;
payload `target_season`/`mode`; board de fase; guardas AST). **Smoke estado-de-prod** (cópia:
current 2026, rollover done, ESPN final, 0 fa_auction): título "Cap Projector 2026" + tag,
`espn_status=final`, **board DP1 com 251** (287 in_class − 36 draftados, auto-limpeza pelo filtro
de rosterados), DP2 **somando** o rookie do cenário, budget corrente == GET (a régua do Hub);
**fixture pós-24/08** (3 `fa_auction`): **volta a 2027/projetado sozinho**, tag some. Gate [[O7]]
exit 0; `template_js_test` + 9 suítes verdes. ⚠️ Nota do smoke: as 14 badges PROV vistas na cópia
são **artefato do boot local** (o `import_csv` do seed regrava `is_final=0` via `set_espn_value` —
em prod o CSV não existe e o boot não toca o store).

**Fecha ✅ quando:** smoke de prod do owner — título 2026 com a tag de modo, banner verde, board
populado, cenário somando (PROC1: conferir o hash deployado antes).

**Relações:** [[OFF26-29]] (a família do predicado por evidência), [[OFF26-28]] (o carimbo 2025 do
`/auction` — interage com o limiar, ver acima), [[DP1]]/[[DP2]] (as cadeias que voltaram),
[[OFF26-1]]-D9 (o modo de base reusado), [[UX19]]/[[L4]] (a família "gate que só fecha" — aqui o
sinal é por evidência justamente para não herdar esse problema), [[UX24]] (carona registrada).

---

### UX25 — Hub: excesso de roster vira obrigação explícita ("cortar ≥N até 20/08")
> ✅ **FECHADO 19/08/2026: smoke de produção confirmado pelo owner** — Hub com as faixas de obrigação E o indicador vivo no projector (arco -b). Commits `d3cfceb` + `752a4a6`. Seção movida verbatim (regra O3).
⚠️ **F2 implementada 19/08/2026 (MAN-UX-NEXT-REG-F2, F1-rápida + F2 na mesma sessão) — smoke de
produção PENDENTE** ([[PROC1]]; o diff toca `style.css`, artefato público conferível por URL) —
Prioridade **Crítica** (prazo 20/08)

**Problema (feedback do owner, 19/08, com print):** na janela pré-cortes, o card do Hub mostra
**"Slots livres 0"** tanto para o time exatamente no limite quanto para o time **acima** dele —
com os rosters inflados pelos 36 rookies, times com jogadores demais não viam **nenhuma**
obrigação. O cap negativo tem alerta próprio e **não** é o assunto deste item.

**F1-rápida (read-only, embutida):**

- **Truncamento confirmado:** `empty_spots = max(0, MAX_ROSTER − num_keepers)` no
  [salary_engine](salary_engine.py) — 27 jogadores → `max(0, −5)` → **0**, o excesso é engolido.
- **Limite canônico adotado: `MAX_ROSTER = 22` ATIVOS**, com os até 2 IR **fora da conta** — é a
  contagem de **composição** do regulamento (item 1.3), a mesma distinção que o [[OFF26-16]]
  cristalizou (IR conta na FOLHA, não na contagem). Fonte no código: a constante do engine —
  **zero literal novo**; os settings do Sleeper corroboram, mas a régua da liga é a do
  regulamento.

**F2 (leitura pura — zero schema, zero mudança de régua):**

- [league.py](routes/league.py): `cut_needed = max(0, ativos − MAX_ROSTER)` + `active_count` /
  `ir_count` / `roster_limit` como campos **novos** do card. ⛔ `atual` (a chamada do
  `draft_budget`) segue intocada — bid, slots e flags idênticos.
- [league.html](templates/league.html): faixa **"⚠️ Cortar ≥N jogador(es) até 20/08"** com a
  contagem **"X/22 ativos (+K IR)"** (o owner confere de onde vem o N; tooltip explica a régua).
  Renderiza **só** quando `cut_needed > 0` — time regular, zero ruído. CSS mínimo na cor de
  alerta que o card já usa.
- ⚠️ **Limite declarado:** o literal *"até 20/08"* morre com a janela — generalizar/remover fica
  para o pós-cortes (o mecanismo em si é permanente: excesso reaparece em qualquer inflação
  futura).

**Verificação:** `roster_excess_test.py` (5 — excesso vira obrigação; **IR fora da conta** (22+2
= legal); excesso com IR conta só ativos; limite exato/abaixo = zero; **réguas intocadas** — o
`slots` truncado continua o mesmo). Smoke na cópia inflada (estado 18/08): **3 cards com
obrigação** (24/22→≥2, 26/22→≥4, 27/22→≥5), 3/3 batendo com a query direta; ⭐ **âncora Trust The
Process conferida dos dois lados: 26 ativos → "cortar ≥4", e o Sleeper AO VIVO devolve os mesmos
26** (MellowBR: 22, regular — sem faixa). Gate [[O7]] exit 0; suítes verdes.

**-b (19/08/2026, MAN-UX25-b) — a mesma obrigação, VIVA no cap projector:** item **"Roster"** na
barra sticky, recalculado pelo **POST `/budget` que já roda a cada toggle** — o servidor conta
(ele conhece `is_on_ir` do banco; o payload do GET também o carrega — gap inexistente, conferido)
e o JS **só exibe** (F10); o limite chega no payload (`roster.limit` = `MAX_ROSTER` do engine —
zero hardcode no cliente). Exibição: `X/22 ativos (+K IR) ✓` discreto quando regular; **"· cortar
≥N"** em alerta quando o cenário excede, **contando para baixo** conforme os toggles até
regularizar. **Rookies do cenário ocupam vaga de ativo** (entram na contagem). **"Spots vazios"
mantido como está** — significado de vagas da AUCTION, onde 0 com excesso é verdadeiro; o
indicador novo ao lado desambigua (decisão de menor mudança). Campo `roster` **aditivo**;
D9/`budget` intocados — teste prova a folha $125 **com** o IR (régua [[OFF26-16]]) e o
`empty_spots` seguindo truncado. Smoke (cópia de prod): Trust **26/22 cortar ≥4 → toggla 4 → ✓ →
volta → reaparece**; rafaelferreirap com `+1 IR` fora da conta; Pitbull 22/22 neutro. +4 testes
(suíte em 9); `template_js_test` + gate [[O7]] exit 0.

**Fecha ✅ quando:** smoke de prod do owner — os cards estourados do Hub exibindo a faixa com N
correto **e** o projector com o indicador vivo (PROC1 pelo hash do `style.css` servido).

**Relações:** [[OFF26-16]] (a distinção folha × contagem que define a régua), [[UX18]] (o
precedente de "estado inviável sem alerta" e das flags canônicas), [[L3]] (o card em 3 zonas onde
a faixa se encaixa), [[OFF26-26]] (a entrada dos 36 que inflou os rosters), [[M1]] (o alerta de
cap que NÃO foi tocado).

---

### UX26 — Badge PROV em rookies já contratados (salário real rotulado de provisório)
> ✅ **FECHADO 19/08/2026: smoke de produção confirmado pelo owner** — Cooper/Douglas/Love sem PROV. Commit `2a2d94f`. Seção movida verbatim (regra O3).
⚠️ **F1-rápida + F2 implementadas 19/08/2026 (MAN-UX26-REG-F1F2) — smoke de produção PENDENTE**
([[PROC1]]) — Prioridade **Média**

**Sintoma (print do owner, 19/08):** no projector (modo corrente pós-[[UX23]]), Omar Cooper e
Caleb Douglas — **contratados** pelo reparo [[OFF26-26]], Ano 1/4, rookie_draft, ESPN definitiva
travada — exibiam **PROV** ao lado do salário. Semanticamente errado: PROV marca projeção de
fonte não-final; $1/$54 ali é **contrato gravado**.

**F1-rápida:**

- **Derivação única, sem réplica por-jogador:** [salary.py](routes/salary.py) lê `is_final` do
  `EspnValueStore` → payload `espn_is_final` → JS `=== false` mostra o badge. Os demais
  `tag-prov` do app são semânticas **distintas** (o `bid_provisional` table-level da liga, o
  estágio da keeper sheet, o "PROTEGIDO" da urna, cores de timeline) — nada a consolidar.
- ⭐ **Causa-raiz medida — e é outra que a suspeita do prompt:** o clear do passo 5 é
  **irrelevante** (o badge lê `EspnValueStore`; o clear esvazia `RookieEspnValue`). A raiz é
  **`record_acquisition` → `set_espn_value(...)` com default `is_final=False`**
  ([models.py:428](models.py#L428)): toda aquisição grava a row do store carimbada **provisória**
  — o reparo OFF26-26 fez isso com os 36, mesmo com os valores vindos da tabela definitiva (via
  `RookieEspnValue`).

**F2 (exibição apenas — zero mudança em salário/contrato/store/réguas):**

- **`models.contracted_player_ids(season)`** — fonte única (evidência AuctionLog, mesma família
  [[OFF26-29]]/[[UX23]]): jogador com contrato de aquisição gravado na season corrente **nunca**
  exibe PROV, independentemente do carimbo do store.
- Decisão calculada **no servidor** (`espn_prov` novo no payload); o JS troca `espn_is_final ===
  false` por `p.espn_prov` — **guarda de teste falha se o JS voltar a decidir pelo dado cru**.
  `espn_is_final` permanece no payload como dado CRU do store, intocado.
- **Caso legítimo preservado:** provisório sem contrato na season corrente segue exibindo PROV.

**Verificação:** `espn_prov_badge_test.py` (6 — contratado não exibe; legítimo exibe; final não
exibe; sem store não exibe; critério só em models; JS consome a decisão). Smoke na cópia (estado
do reparo: rows do store `is_final=0` + 36 AuctionLog): **12 times varridos, 0 contratados-2026
com PROV, 241 legítimos preservados** (⚠️ o 241 é artefato do boot local que o [[UX23]] já
documentou — em prod a definitiva carimbou os veteranos e sobra ~zero); âncoras
Love/Cooper/Douglas/Price limpas. Gate [[O7]] exit 0; `template_js_test` + suítes verdes.

**Nota de dado (não corrigida aqui, de propósito):** o default `is_final=False` do
`set_espn_value` continua carimbando rows de aquisição como provisórias — o F2 corrigiu a
**exibição** pela semântica verdadeira, que blinda qualquer estado do store. Mudar o default (ou
propagar a finality da fonte) mexeria na porta canônica de contrato — fora do escopo por
restrição, e desnecessário com o critério novo.

**Fecha ✅ quando:** smoke de prod — Cooper/Douglas/Love sem PROV no projector.

**Relações:** [[OFF26-26]] (os contratos), [[UX23]] (o modo corrente onde o badge vive),
[[OFF26-29]] (a família de predicados por evidência), [[E4-c]]/[[E2]] (o store e sua semântica de
`is_final`), [[M2]] (o `record_acquisition` — a porta que carimba o default).

---

### OFF26-27 — Criação de stub no sync usava season estagnada (a raiz do carimbo 2025)
> ✅ **FECHADO 19/08/2026** — pela COMBINAÇÃO: fix deployado (`bdd3044`) + guarda AST + smoke com `run_sync` REAL recriando os 36 stubs em 2026 + ausência de recorrência em prod desde o deploy. O caso natural (próximo jogador novo entrando por sync) segue como observação de rotina, não gate. Seção movida verbatim (regra O3).
⚠️ **Fix no ar (`bdd3044`, 18/08/2026) — smoke de produção PENDENTE** — Prioridade **Crítica**,
prazo **antes do sync pós-cortes de 20/08** (o fix precisa estar deployado antes do próximo stub
nascer) — prompt MAN-OFF26-25 (⚠️ o ID de backlog é **27**: OFF26-25 já era o gate ESPN do rollover)

**Raiz (provada na F1 do [[OFF26-26]]):** [sync_sleeper.py:304](sync_sleeper.py#L304) criava o
Player stub com `contract_start_season=CURRENT_SEASON` — constante de módulo fixa em 2025, cujo
próprio comentário diz *"fallback — prefer get_current_season()"* — enquanto o rollover avança o
**AppConfig**. Todo entrante pós-rollover nascia na season errada; a classe 2026 inteira nasceu
assim (curada pelo one-shot do [[OFF26-26]]); o defeito seguia **ativo** para qualquer add/waiver
com os syncs frequentes da semana (cortes de 20/08, trades).

**Fix mínimo (`bdd3044`):** `stub_season = get_current_season()` lido **uma vez por sync**
(hoisted antes do loop de rosters) e usado no construtor; a constante segue como fallback de
última instância **dentro** do helper. Zero uso cru remanescente no módulo (só o import);
players existentes intocados (a linha 242 do sync — nunca tocar salary/contract de existente —
não foi alterada).

**Verificação:** `sync_stub_season_test.py` (6 testes) — guarda **AST** no construtor `Player(`
(reintroduzir a constante na criação de dados FALHA), `run_sync` contém a leitura canônica,
AppConfig 2026 → 2026, ausente → fallback sem quebrar, pós-rollover o carimbo acompanha.
⭐ **Smoke com `run_sync` REAL** contra cópia adaptada (2026) reproduziu o incidente como
validação: os 36 rookies ausentes do seed foram recriados como stubs **todos em
`contract_start_season=2026`**, e **zero** player existente teve salary/contract/acq/css alterado.
Suítes verdes: engine 62, poka_yoke 15, late_drop 64, espn_gate 33.

**Fora do escopo (mapeado na F1, sem mudança):** `import_csv` (dormente em prod — CSV fora do
git), `AuctionLog.season` default (latente — `record_acquisition` sempre passa explícito),
`/auction` (item próprio: [[OFF26-28]]). Nenhuma migração de dados: não há outros registros 2025
pós-rollover fora dos 36 já curados.

**Fecha ✅ quando:** hash `bdd3044`+ conferido em prod ([[PROC1]]) e o próximo jogador novo criado
por sync nascer `contract_start_season=2026` (a movimentação de 20/08 produz o caso natural).

---

### OFF26-29 — Picks 2026 consumidas seguem vivas como ativo no Manager
> ✅ **FECHADO 19/08/2026: F2 executada (`bfcbd61`, 18/08) + smoke de produção pelo print do board (só 2027/2028 visíveis).** A F2 implementou a recomendação da F1: predicado único `consumed_pick_seasons`/`pick_is_consumed` em models (evidência AuctionLog), filtro no `/api/picks` (fecha simulador, propostas novas e preset), funil `_fetch_picks` (preview + proposta antiga com TTL vivo + delta dynasty), ocultação no board e `/team/<id>`, contagem do card do Hub corrigida (consumidor que a F1 não listara); row VIVA na tabela e `_sync_trades` intocado (espelho preservado); 13 testes + guardas anti-réplica. Seção movida verbatim (regra O3).
🔲 **Registrado 18/08/2026 (MAN-OFF26-24-REG); F1 read-only FEITA na mesma janela
(MAN-OFF26-27-F1 — ⚠️ ID de backlog = 29)** — Prioridade **Baixa (REG) — a F1 sugere reavaliar
para Média** (a exposição é na janela de trades até 24/08) — F2 aguarda decisão do owner

**Contexto:** o rookie draft 2026 foi materializado pelo [[OFF26-26]], mas as picks 2026 seguem
vivas como ativo: no Sleeper (draft `pre_draft` — governança por aviso) e no Manager (tabela
`Pick`).

**O que a F1 mediu (evidência na trilha da conversa de 18/08):**

- **7 consumidores** da Pick 2026; o funcional é **`/api/picks` sem filtro de consumida**
  ([picks.py:127-148](routes/picks.py#L127-L148)), que alimenta a lista de picks **selecionáveis**
  do simulador ([trades.html:329](templates/trades.html#L329)), o preview e as propostas
  (`_fetch_picks` resolve ao vivo, [trades.py:453](routes/trades.py#L453)). Board `/picks`,
  `/team/<id>` e a valoração dynasty ([dynasty_values.py:183](dynasty_values.py#L183) corta só
  `< current`) exibem/valoram normalmente.
- ⛔ **Premissa "permite registrar trade" DESLOCADA:** o Manager **não executa** trade (POSTs de
  `/trades` = preview puro, proposta, delete de registro); ativo só se move via sync ([[S1]]).
  Exposição real = **planejamento enganoso**, não execução.
- ⛔ **Delete REFUTADO como mecanismo:** o critério do sync é **ano-calendário**
  (`datetime.now().year` — [sync_sleeper.py:398-401](sync_sleeper.py#L398-L401); as 2026 morreriam
  só em 01/01/2027, rollover é irrelevante) e a recriação viria do próprio sync:
  `active_seasons` sai do `/traded_picks` do Sleeper, que ainda lista **21 picks 2026** (medido ao
  vivo, 18/08) — com o draft real `pre_draft` para sempre, o Sleeper nunca as solta.
- **Trade real do Sleeper com pick 2026 pós-expiração:** com a row viva, `_sync_trades` espelha e
  move ([sync_sleeper.py:746-757](sync_sleeper.py#L746-L757)) — correto para um espelho; com
  delete, warning `"não encontrada (drafada?)"` e Trade sem a pick rastreada.

**Recomendação da F1 (F2 ~1 sessão, zero schema, zero delete, sync intocado):** predicado
data-driven **`pick consumida = existe AuctionLog(entry_type='rookie_draft', season da pick)`** —
a mesma evidência que o gate do passo 5 ([[OFF26-23]]) já usa, materializada pelo reparo (36
registros) — em **helper único** + filtro no `/api/picks` (fecha simulador, propostas novas e
preset de uma vez) + selo/ocultação no board e `/team/<id>` (**selo × sumiço = decisão do
owner**). Autossustentável entre seasons (2027 fica tradável até o draft 2027 ter registro), sem
risco de ciclo de vida de flag (`rookie_draft_done` foi descartada como predicado — família
[[L4]]). Riscos nomeados: proposta antiga (TTL 7d) com pick 2026 ainda renderiza; valoração
dynasty da pick morta segue no delta até o filtro alcançar `_pick_asset_dict`; trade real no
Sleeper continua espelhando (correto — constar no aviso de governança).

**Pendências do registro original:** expirar/ocultar as picks 2026 no Manager (a F2 acima) +
**ensaio opcional do draft room na liga fantasma** (operacional, sem código).

---

### OFF26-30 — Draft replay no Sleeper: consumir as picks 2026 no board
✅ **Concluído 18/08/2026 (execução manual do co-admin; registrado no fechamento
MAN-SESSION-CLOSE-1908)** — Prioridade **Alta**

**O que era:** as picks 2026 seguiam vivas no board do Sleeper (draft `pre_draft` eterno) depois
de o rookie draft ter acontecido fora do board ([[OFF26-26]]). O replay consome as picks NO
SLEEPER — a contraparte da ocultação que o [[OFF26-29]] fez no Manager.

**Execução (18/08, manual, sob o freeze [[OPS2]]):**

- 36 picks registradas pick a pick no board do draft da liga real; draft levado a **`complete`**.
- **Conferência pela API**: pick a pick nas 4 primeiras + contagem total (36/36).
- Picks 2026 **consumidas no Sleeper**; picks futuras (2027+) **intactas** no `/traded_picks`.
- O `start_time` agendado do draft foi **eliminado pelo próprio complete** — o risco de o
  Sleeper abrir um draft room espúrio morreu junto.
- **Sync pós-operação: contratos intocados** (âncora Love $54 conferida) — o freeze foi
  destravado só após o `complete`.

⭐ **O ensaio previsto na F1 nunca foi necessário** — a execução real respondeu as perguntas
(inclusive as do draft room). Lição registrada no devplan: rookie draft 2027 = WhatsApp como
palco + **registro pick a pick no board do Sleeper** logo em seguida, para o board nunca mais
divergir da realidade.

**Relações:** [[OFF26-26]] (o incidente que criou a dívida), [[OFF26-29]] (a ocultação no
Manager — as duas pontas fecham juntas), [[OPS2]] (o freeze que protegeu a janela),
[[OFF26-24]] (o script da fantasma — infra irmã, não usada aqui: a liga real pediu operação
manual).

---

### OFF26-31 — Forense: Cam Little $3→$1 — regra correta sobre estado herdado anômalo
✅ **Concluída 19/08/2026 (MAN-OFF26-31-REG-F1) — ZERO reparo** — Prioridade **Alta**

**O reporte (Leo, ao vivo):** Cam Little (K/JAX, id 115) "estava $3 e mudou para $1", entre as
fotos de 07/08 (`pre_smoke_urna.db`) e 18/08 03:30 (`dynasty_prod_backup_2026-08-18_wa_draft.db`),
aparentemente sem trilha.

**Veredito — ⛔ a premissa central caiu, com evidência dupla:**

1. **A mudança TEM trilha:** a linha de SalaryHistory de **17/08 21:34:17** — *"Waiver Ano 2:
   floor(0.80×1.0)=$1"* — é gerada por um único sítio do código (`apply_season_rollover`, ramo
   `waiver + next_yr==2`) e crava a mutação ao segundo. O **"1.0" é o ESPN ajustado** (K,
   placeholder), não uma base salarial lida errada: **o ramo não lê `Player.salary` por
   decisão do owner** (06/08, [[OFF26-20]]: canal waiver/FA não carrega contrato; ano 2 =
   0,8×ESPN REF).
2. **Sem trilha estava o $3:** o jogador tinha **zero** linhas de SalaryHistory pré-rollover —
   o $3 veio da era do import e nunca foi trilhado. O que parecia "mudança sem trilha" era o
   inverso: **valor sem passado que finalmente ganhou uma linha**.

**A cadeia completa** (PlayerHistory + transações do Sleeper 2025, liga `1224848075609100288`):
FA Auction pelo Cangaceiros (~$2-3) → **drop 12/10** → **re-add `free_agent` pelo Leo 29/10**.
O re-add não abre contrato novo (o sync nunca toca salário — raiz = [[WV1]], família Gainwell),
então o $3 do contrato morto sobreviveu como híbrido `$3/free_agent/cy=1` até o rollover aplicar
a régua do canal.

**Alcance:** a coorte achatável deste rollover (`cy=1 + canal waiver/FA + salary>1`) era
**exatamente {Cam Little}** — prevista pelo seed e confirmada pelos backups; os 22 do
[[OFF26-20]] estavam a $1 e **subiram** pela mesma régua. Diff completo foto A × foto B sem
inexplicados. **População híbrida restante: ~5, todos cy≥2** — caem na VALORIZAÇÃO
(`MAX(prev, …)`), **nunca descem**. ⚠️ O gerador de híbridos segue vivo até o [[WV1]]: todo
dropado-readicionado mantém o salário morto, e o rollover de 2027 achatará híbridos novos —
**por regra**.

**Candidatos eliminados por código:** sync (*NEVER salary/contract*), urna/ensaio, migrações de
boot, [[OFF26-26]] (fora dos 36 + foto pré-reparo já $1); `correct_player_salary` muda salário
sem linha NOVA (edita a última in-place) mas emite PlayerHistory — nenhum no período.

**Decisão: ZERO reparo** — $1 é o valor correto do canal; devolver $3 contradiria a decisão de
06/08 (seria mudança de regra, e regra é pauta — [[REG1]]). **Desdobramentos:** [[WV1]]
promovido a Alta (fechar o gerador pela porta canônica + caronas: baseline de SalaryHistory,
revisão do default `is_final` — nota do [[UX26]] —, conferência do lance real de 2025),
[[REG1]] (FA add × waiver claim na renovação).

**Relações:** [[OFF26-20]] (a decisão de canal que a régua aplica), [[WV1]] (a raiz),
[[OFF26-26]] (inocentado), [[M2]] (a fila de review — inocentada no período), [[F7]]/[[S1]]
(a Timeline que preservou a cadeia).
### OFF26-37 — Régua canônica de contrato vivo × morto + a porta do sync que a viola

✅ **CONCLUÍDO em 26/08/2026 (MAN-CONTRATO-VIVO-CLOSE)** — Prioridade **Alta**.
**Critério de fechamento cumprido:** **duas execuções em produção** (Grupo B `32e4cc0` + Grupo A
`2374f4e`, cada uma com backup conferido por `ls -la` antes da escrita), **verificação independente
por consulta read-only** após ambas, e **smoke de produção na interface web confirmado pelo owner**.
⭐ Os **13 alvos** corrigidos e o **Goff intocado** — ver a lição de método no fim da seção.
Registro original abaixo, verbatim: MAN-CONTRATO-VIVO-REG-F1 (25/08, registro + diagnose F1
read-only) → **-ARB** (arbitragem Jones × Goff) → **-F1** (parecer do runner) → **-F2B** → **-F2A**.

🔲 **Registrado em 25/08/2026 (MAN-CONTRATO-VIVO-REG-F1) — registro + diagnose F1 read-only,
medida no banco VIVO e na API.** Prioridade **Alta** (efeito de cap corrente; porta aberta).
⛔ Reparo e gravações são **F2, com backup e desenho aprovado pelo owner** — nada implementado.

#### A RÉGUA CANÔNICA (decisão de liga, 25/08/2026 — fechada, não rediscutível)

Consolida a regra do co-admin Michel sobre waiver, o caso Aiyuk e a lacuna do rollover
([[OFF26-36]]) numa régua única. ⭐ **O discriminante é o estado do contrato no momento da
aquisição — vivo ou morto — e não a forma de aquisição nem a data.**

| situação | consequência |
|---|---|
| **1.** Arrematado no FA auction | contrato **novo** do leilão: ano 1, salário do lance. Vale para todos — o leilão zera tudo para quem passa por ele |
| **2.** Adquirido na temporada com contrato **VIVO** (drop recente, dentro da janela de waiver) | **waiver mantém o contrato** — mesmo ano, mesma contagem, mesmo salário |
| **3.** Adquirido **SEM** contrato vivo | contrato **novo**: ano 1. Duas rotas: drop de **intertemporada** não arrematado no leilão (não há waiver na intertemporada — o drop mata por si só); ou janela de waiver **vencida** sem claim vencedor (regra 6.8) |

Ancoragem em regulamento: 6.1 (leilão abre contrato novo) e 6.8 (FA status mata contrato).

#### O caso âncora — Brandon Aiyuk (sid 6803), com efeito de cap HOJE

| evento | data | consequência devida |
|---|---|---|
| dropado | 12/08/2026 (intertemporada) | contrato morre |
| não arrematado no leilão de 24/08 | — | segue sem contrato |
| re-add por free agent | 25/08 04:21 | **caso 3: contrato novo, ano 1, 2026, $1** |

**Em produção:** `cy=2 · css=2025 · fa_auction · $8`, AlexTheDawg — **o contrato morto sobreviveu
inteiro**. ⚠️ **$8 na folha quando o devido é $1**: diferente dos demais casos da semana, este
erra o **cap da temporada corrente** (−$7 para o AlexTheDawg no reparo), não só o display.

#### A porta que viola a régua — e é UMA linha

O re-add do sync ([sync_sleeper.py:320](sync_sleeper.py#L320)):

```python
p.is_dropped = False  # back on a roster = not dropped
```

Reativa **sem consultar estado de contrato** — o código nem distingue "já estava em roster" de
"voltou" (a transição dropado→rosterado é invisível no ramo `if p:`). Mantém o contrato para
**todos** os casos: acerta o caso 2 **por acidente** e erra o caso 3. ⭐ **Réplica medida: todas
as demais portas de entrada já respeitam a régua** — o import do draft e as 4 portas do `/auction`
passam por `record_acquisition` ([models.py:423](models.py#L423)), que abre contrato novo (casos
1/3); trade carrega contrato (não é aquisição — comportamento correto). **Há UMA porta a ensinar,
e a decisão vivo × morto pertence a ela.** O mecanismo completo do fantasma: o rollover **pula
dropados** (`filter_by(is_dropped=False)` — o contrato congela na contagem velha) + o re-add
reativa como está.

#### A classe, medida no banco vivo (25/08) — EXATAMENTE 2

Método: 178 rosterados com `css<=2025` × keeper sheet congelada de 22/08 × arremates do leilão;
controle inverso limpo (**0** arrematados carregando css antigo).

| sid | jogador | time | drop | re-add | em prod | devido (caso 3) | efeito de cap |
|---|---|---|---|---|---|---|---|
| 6803 | **Brandon Aiyuk** | AlexTheDawg | 12/08 (intertemporada) | 25/08 04:21 FA | `cy=2 · css=2025 · fa_auction · $8` | ano 1 · 2026 · free_agent · **$1** | **−$7** |
| 9486 | **Dontayvion Wicks** | Haliburton Time! | 20/08 22:29 (cortes) | 25/08 13:12 FA | `cy=2 · css=2025 · free_agent · $1` | ano 1 · 2026 · free_agent · $1 | **zero** (salário já = devido; dano só cy/css) |

**Os demais adds de FA de 25/08 nasceram limpos** — e são **7, não 6**: o arco listava 8
companheiros; a API mediu **9 adds** (o nono é **Malik Davis, 8800**). Nenhum dos 7 existia no
banco → o sync criou stubs (`cy=1 · css=2026 · unknown · $1 · needs_review=1`, criados 25/08
13:34): Davis, Freiermuth, Jordan James, Flournoy, Helm, Raiders DEF, McGowan, Wicks*
(*Wicks existia — é o 2º da classe). A fila de revisão (7) são exatamente os stubs. ⚠️ O stub
**aproxima o caso 3 por acidente** (ano 1 · $1 · 2026) — o defeito só atinge quem **existia** com
contrato anterior.

**Adds desde o rollover, decompostos (52):** 7 trades (contrato carregado — fora da régua), 37
`commissioner` de 18/08 (vaivém da equalização, rookies 2026) e os 9 FA de 25/08.

#### ⚖️ ARBITRAGEM da disputa Jones × Goff (26/08/2026, MAN-CONTRATO-VIVO-ARB) — a lista FECHA em 13

**Medição independente do owner, fora do circuito do Code**, varrendo a API de transações da liga
de 2025 (`league_id 1224848075609100288`) nas **21 semanas disponíveis**. Resolve a disputa que o
`handoff_contrato_vivo_26_08_2026.md` (seção 2) registrava como **bloqueante da lista completa** —
as duas alegações eram **mutuamente exclusivas** (discordavam sobre qual dos dois tinha
re-aquisição de 2025 dentro da janela de 48h), e a arbitragem resolve **uma a favor da lista e uma
contra**. ⛔ **Este registro SUPERA a seção 2 daquele handoff**, que permanece **intocado** como
documento histórico.

| sid | jogador | time | veredito | Δ desde o **próprio** drop | caso da régua | consequência |
|---|---|---|---|---|---|---|
| `5870` | **Daniel Jones** | Cangaceiros da Colina | **É ALVO** | **69,2h** — **FORA** da janela de 48h, margem de **21,2h** | **caso 3** — contrato **novo** nascido em 2025 | `contract_year` devido = **2** (em prod, **3**). ⭐ `contract_start_season` **já está correto em 2025** — a correção é **só de contagem**, mesma forma do Grupo B |
| `3163` | **Jared Goff** | Pitbull do Samba | **NÃO É ALVO** | **12,3h** — **DENTRO** da janela de 48h | **caso 2** — contrato de **2024 preservado** | `contract_year = 3` está **CORRETO**. ⛔ **Não tocar.** Nenhuma outra transação **completa** dele em 2025 |

**Cadeia medida — Jones:** drop **03/11/2025 04:45 UTC** (roster 2, waiver, `complete`) → última
aquisição de 2025 em **06/11/2025 01:54 UTC** (roster 6, waiver, `complete`). ⚠️ **Fio solto
benigno, registrado:** existe um add anterior em **08/09/2025 01:11 UTC** (roster 2) **sem drop
precedente dentro de 2025** — a cadeia dele atravessa a liga de 2024. **Não afeta o veredito**,
porque quem governa é o **último** add.

**Cadeia medida — Goff:** drop **10/09/2025 01:11 UTC** (roster 8, waiver, `complete`) → claim
**completo** em **10/09/2025 13:31 UTC** (roster 1, waiver, `complete`).

**Consequência para o D4** (os `css` reescritos pelo rebuild — 🔲 **gated** no fix do passo 6 do
rebuild, estado **inalterado por esta sessão**): se o contrato de **2024** foi preservado, o
`contract_start_season` devido do Goff é **2024** e produção mostra **2025**. ⛔ Registrado como
**evidência entregue ao D4**, **não** como correção a executar — o D4 segue gated.

#### Contagem do arco, corrigida — **13 alvos** (supera o 12 do handoff)

**2 (Grupo A: Aiyuk, Wicks) + 11 (Grupo B, agora com Jones) = 13.** O handoff de 26/08 registrava
**12 incontroversos com 2 em disputa**; a arbitragem resolve **um a favor** (Jones entra no Grupo
B, 10 → 11) e **um contra** (Goff nunca foi alvo). ⛔ **12 está superado — a lista da F2 é de 13.**

#### Evidência literal da medição (saída do `medir_disputa.py`, 26/08/2026)

Cobertura: **21 arquivos**; semanas **0, 18, 19 e 20 vazias** (2 bytes cada).

```
arquivos lidos (21): tw0.json ... tw20.json
5870 Daniel Jones
  sem1   08/09/2025 01:11 UTC  ADD  waiver complete roster=2 ts=1757293879911
  sem9   03/11/2025 04:45 UTC  DROP waiver complete roster=2 ts=1762145105158
  sem10  06/11/2025 01:54 UTC  ADD  waiver complete roster=6 ts=1762394083840
         delta 69.2h => FORA da janela -> contrato NOVO
3163 Jared Goff
  sem1   10/09/2025 01:11 UTC  DROP waiver complete roster=8 ts=1757466673903
  sem2   10/09/2025 11:13 UTC  ADD  waiver failed   roster=6  [IGNORADO]
  sem2   10/09/2025 13:31 UTC  ADD  waiver complete roster=1 ts=1757511117748
         delta 12.3h => DENTRO da janela -> contrato PRESERVADO
  sem2   10/09/2025 22:46 UTC  ADD  waiver failed   roster=6  [IGNORADO]
  sem2   11/09/2025 12:01 UTC  ADD  waiver failed   roster=1  [IGNORADO]
```

#### ⭐ Lição de método (candidata a baseline do `DEV_METHODOLOGY`, família MAN-METH-REG)

**No feed de transações do Sleeper, TENTATIVA e AQUISIÇÃO ocupam a mesma estrutura** — o que as
separa é **só o campo `status`**. A medição encontrou **três** claims `failed` do Goff na mesma
janela (10/09 11:13 roster 6 · 10/09 22:46 roster 6 · 11/09 12:01 roster 1) **além** do claim
`complete`. **Sem filtrar por `status == "complete"`, a cadeia reconstruída é outra** — são
exatamente essas três linhas que explicam por que as medições anteriores divergiam.
Consequência registrada: **"a API de transações não é discriminante sem o filtro de status"**.
⛔ Registrada aqui como **candidata**; a consolidação transversal no `DEV_METHODOLOGY` é sessão
própria — **não é regra vigente ainda**.

#### ⚠️ Premissas do arco refutadas por esta arbitragem

1. **"Os arquivos `tw*.json` das 18 semanas já estão baixados na raiz do projeto"** — **falsa**:
   estavam **ausentes** (contagem **zero**). Aceita sem conferência, teria produzido varredura
   sobre **cobertura parcial com aparência de completa**. A medição os baixou (21 arquivos, 4
   vazios).
2. **A alegação B da disputa atribuía ao Jones a cadeia de datas que pertence ao Goff** — ⭐ **não
   era medição divergente, era troca de sujeito.** É o segundo caso do arco em que uma "divergência
   de medição" se dissolve em erro de atribuição, não em erro de leitura.

#### Decisões do owner (25/08) — a F2 executa, não rediscute

1. Preencher **retroativamente** a lacuna de 2026 **e** passar a **gravar ao vivo**.
2. Consertar as **três** portas omissas do [[OFF26-36]] (rollover · aquisição · drop do sync).
3. O evento de drop registra **fato + fase** (intertemporada × temporada), **sem interpretar
   consequência** — quem decide se o contrato morreu é a régua, aplicada no evento seguinte.

#### Computabilidade da régua (veredito da F1)

**Computável daqui para frente** com as três gravações; **NÃO computável retrospectivamente só
com o banco** — o dado que falta é a **data do drop** (`is_dropped` é booleano sem carimbo e o
evento de drop nunca foi gravado ao vivo). O insumo histórico vem da **API de transações** (foi
assim que Aiyuk e Wicks foram medidos). Fase: `offseason_mode` existe em AppConfig e é consultável
**agora**, mas as transições da flag não são carimbadas — gravar a fase **no momento do evento**
(decisão 3 do owner) é o que a torna confiável; sync congelado atravessando fronteira de fase é o
caso residual. **Janela de waiver: nada no código nem em config** — `waiver_clear_days=2` veio das
settings da liga na API (diagnose [[WV1]]); fixar em AppConfig × ler ao vivo é decisão em aberto.

#### Desenho das três gravações (proposto na F1 — aprovação do owner antes da F2)

| porta | tipo de evento | campos | referência (imune ao rebuild [[F8]]) |
|---|---|---|---|
| **rollover** (`do_rollover`, junto ao SalaryHistory) | `rollover` (valorização) / `renewal` (pós-ano 4) | season alvo, time, salário novo, ano novo, notes = regra aplicada | `rollover:<season>` — o F8 já preserva `LIKE 'rollover:%'`, o display ("Valorização (Ano N)") e a ordenação rollover-last já existem |
| **aquisição** (`record_acquisition`, junto ao AuctionLog) | = o `acquisition_type` gravado | season, time, salário, ano 1, notes = regra | `event_ref` quando houver (`draft:<id>:<pick>`); portas manuais sem ref → proposta `acq:<id do AuctionLog>` (⚠️ questão de desenho: exigir `event_ref` sempre?) |
| **drop do sync** (passo 8) | `drop` | season, time que dropou, salário/ano no momento, notes = **"drop (intertemporada)"** ou **"drop (temporada)"** — fato + fase | ⚠️ o passo 8 **não tem tx id** (drop inferido por ausência); proposta `syncdrop:<season>:<player_id>:<sync_log_id>` — questão de desenho: dedupe contra um futuro drop `tx:<id>` do rebuild |

Idempotência das três: UNIQUE `uq_player_history_event` já existente. A gravação na aquisição
fecha de tabela o buraco lateral do [[OFF26-34]]/[[OFF26-36]] (os 52 sem evento não se repetem).

#### Backfill retroativo de 2026 (proposto)

- **Rollover (222):** as 222 rows de `SalaryHistory` season 2026 (regras `VALORIZ%`/`Waiver Ano
  2%`) carregam jogador, salário, ano e regra — **bastam** (confirmado na diagnose do
  [[OFF26-36]]). Eventos `rollover`, ref `rollover:2026`, idempotentes pela UNIQUE. ⚠️ Ressalva de
  fidelidade: **7 jogadores trocaram de time por trade DEPOIS do rollover** (17/08 22:31 em
  diante: Dobbins, Shough, Jones, Murray, Diggs, Tucker, Nix) — `team_name` atual seria
  anacrônico; reconstruir o time da época pelas trades é possível. Decisão do owner.
- **Leilão (52):** `AuctionLog` com `[ref:draft:1396615822058721280:<pick>]` → eventos de
  aquisição com ref `draft:…` — **mesmo formato do F8**; fiel e idempotente. ⚠️ Se um rebuild
  futuro enxergar o **draft paralelo da liga real** ([[OFF26-35]]), geraria eventos duplicados com
  id de draft diferente — mais um peso na decisão de lá.
- **Drops de agosto (cortes 20/08, urna 22/08, equalização 24/08):** todos têm **tx id** na API →
  eventos `drop` ref `tx:<id>`, fase = intertemporada (derivável do timestamp). Reconstruíveis.

#### Reparo da classe (F2, com backup — NÃO executado)

**Alvo:** caso 3 → `cy=1 · css=2026 · free_agent · $1` (add de free agent não tem lance; canal
`free_agent` ∈ `_WAIVER_TYPES` → ano 1 = $1, ano 2 = floor(0.8×ESPN)). Aiyuk: −$7 na folha do
AlexTheDawg. Wicks: só cy/css mudam. **Porta:** `record_acquisition` — caso 3 é aquisição nova, e
a porta canônica é a única que abre contrato ano 1 (F9: "não criar contrato fora desse helper");
as portas de correção existentes não cobrem css/canal (`contract_year_correction` só cy;
`correct_player_salary` só salário). **Molde estrutural:** `wv1_fix_coorte_b` (censo congelado de
2 + cruzamento ao vivo + backup + check/apply), com o passo de escrita trocado pela porta de
aquisição. ⚠️ Questão de desenho: `record_acquisition` grava `AuctionLog` com
`entry_type="fa_auction"` — rótulo off-label para um add de FA (vizinho do [[OFF26-34]]).

#### ⚠️ Caso que a régua não cobre — reportado como PERGUNTA, não objeção

O **vaivém de comissário**: a equalização de 18-24/08 dropou e devolveu jogadores por ação de
comissário (37 adds de 18/08; JAX, Fairbairn e Tyler Loop dropados em 24/08 e devolvidos pela
replicação). Pela letra da régua, drop de intertemporada mata o contrato — um rookie de
floor(ESPN×1.2) movido para montar o board voltaria a **$1**. O sistema manteve os contratos
(intenção certa). **Movimento de comissário conta como drop/add para a régua, ou é vaivém
operacional invisível?**

#### Arrumação recomendada dos vizinhos (recomendação, não execução)

- **[[OFF26-36]]** fica como está: é o registro da lacuna e das três portas; as decisões do owner
  acima **respondem às decisões em aberto de lá** — a F2 deste item e a de lá são **o mesmo
  diff** (gravações + backfill) e devem sair juntas, fechando os dois.
- **[[WV1]]** (coorte B nunca executada — 3 remanescentes: Fairbairn, Dicker, NE) e
  **[[OFF26-33]]** (zero remanescentes, com ressalva de recall) ficam como estão — a régua agora
  registrada é o critério que qualquer fechamento deles usará.
- **[[OFF26-32]]**: executado em prod em 25/08 (19 contratos 3→2, trilha `fix:off26-32`, backup
  `/data/pre_off26_32_fix.db`) — o fechamento ✅ é do owner, com a migração de seção do O3.

**Cross-refs:** [[OFF26-36]] (as três portas e a lacuna — mesma F2), [[OFF26-34]] (o rótulo do
AuctionLog e a porta de aquisição), [[OFF26-35]] (o draft paralelo × backfill do leilão),
[[WV1]]/[[OFF26-20]] (a família waiver e a decisão estrita que antecipou o caso 3),
[[OFF26-32]] (o reparo-irmão executado), [[OFF26-33]] (a subcoorte invisível, dimensionada zero).


#### 🔎 PARECER F1 do runner dos 13 (26/08/2026, MAN-CONTRATO-VIVO-F1) — read-only, zero escrita

⛔ **Eixo 1 NÃO foi medido nesta sessão — e a razão é estrutural, não omissão.** O banco alcançável
do Code é `./dynasty.db` = **o SEED do git** (mtime **07/08**, `current_season=2025`,
`rollover_done=false`), **não** `/data/dynasty.db`. Ele é **pré-rollover**: mostra os 13 em `cy=2`
porque o incremento de 17/08 ainda não aconteceu ali. ⛔ **Isso NÃO contradiz o registrado** — é
outro banco em outro momento. A medição de produção é do owner, no Render Shell; o bloco read-only
está no fim deste parecer. Os eixos 2, 3 e 4 **não dependem do banco vivo** (são código e listas
congeladas) e estão **fechados** abaixo.

##### Eixo 2 — invariante salarial sobre os 11 do Grupo B: **0 violações**, e é ANALÍTICO

Rodado com o motor real (`salary_engine.project_next_salary`): `cy=3` e `cy=2` caem **ambos** no
ramo da valorização (`next_yr` nem é 2, nem passa de 4) ⇒ a projeção do **ano seguinte** é idêntica
**para qualquer ESPN** — não é resultado de dado, é da forma da regra. **Violações = 0** (11/11,
testado também contra ESPN raw × ajustado).

⚠️ **Mas o dinheiro SE MOVE — em dois lugares que a frase "mexe na contagem, nunca no dinheiro"
esconde:**

| onde | quem move | de → para |
|---|---|---|
| **Horizonte 2** (a temporada DEPOIS da seguinte) | **Stafford (421)**, 1/11 | `cy=3` → ano 5 = **renovação** `floor(ESPN)=$4`; `cy=2` → ano 4 = valorização **$2**. Robusto a raw × ajustado |
| **Passivo do rollover de 17/08** (ano 2 de waiver/FA devido = `floor(0,8×ESPN)`) | **Stafford (421)**, 1/11 medido | **$2 → $3**. Os outros 9 medidos: `floor(0,8×ESPN)` = $1 = atual, **não movem** |

⚠️ **Jones (5870) é INDETERMINADO — e é o buraco de dado do eixo 2.** Nem os DADOS do prompt nem o
handoff trazem o ESPN dele. Limiar medido: **move se e somente se `espn_adj >= 2,5`**
(`floor(0,8 × 2,4)=$1` · `floor(0,8 × 2,5)=$2`). O seed diz `espn_ref_value=1.2` (⇒ não moveria),
**mas o seed é de 07/08 e a tabela definitiva de 2026 entrou depois** — o número que decide é o de
produção.

##### Eixo 3 — a porta **NÃO é uma só**: são duas, com forças de guarda diferentes

| grupo | porta | escreve | guarda pré-escrita | idempotência |
|---|---|---|---|---|
| **A** (2) — reset ano 1 | `models.record_acquisition` ([models.py:382](models.py#L382)) | `salary` (via `year1_salary`) · `contract_year=1` · `contract_start_season` · `acquisition_type` · `is_dropped=False` + `SalaryHistory` + `AuctionLog` | ⛔ **NENHUMA** — não confere estado esperado | só o token `[ref:…]` em `AuctionLog.notes`, **e a checagem é do CHAMADOR** (`acquisition_already_recorded`) |
| **B** (11) — contagem 3→2 | `contract_year_correction.apply_contract_year_correction` | **só** `contract_year` + `PlayerHistory` | ✅ **exata, campo a campo** (`guard_mismatches`) — linha que não casa é pulada, nunca forçada | guarda (cy já = 2 ⇒ pulado) + UNIQUE `uq_player_history_event` |

⭐ **`record_acquisition` é errada para o Grupo B** (forçaria `cy=1` e `css=season`, quando o devido
é `cy=2` com `css=2025` preservado), e `contract_year_correction` é **insuficiente** para o Grupo A
(não toca `css`, canal nem salário). **O fix nasce em dois caminhos, ou nasce errado.**

⚠️ **Três armadilhas medidas no caminho do Grupo A:**

1. ⛔ **`set_espn_value` ZERA o ESPN se o runner não passar o valor.** `record_acquisition` chama
   `set_espn_value(player, season, espn_adjusted)` e a **primeira linha** dele é
   `player.espn_ref_value = adjusted`, **antes** da guarda `if not adjusted: return`
   ([models.py:764](models.py#L764)) — com o default `espn_adjusted=0.0` o valor é apagado, e todo
   projetado futuro passa a cair no piso. **O runner tem de reler e repassar o ESPN corrente.**
2. **A porta não grava `PlayerHistory`** — é a lacuna já registrada do [[OFF26-34]]/[[OFF26-36]].
   O Grupo A sai **sem evento de timeline**, ao contrário do Grupo B.
3. Rótulos off-label conhecidos: `AuctionLog.entry_type="fa_auction"` e
   `SalaryHistory.rule_applied = "FA Auction: $1 (bid)"` para um add de free agent (vizinho do
   [[OFF26-34]]).

**Réplica da lógica de escrita de contrato — varredura `.py` + `.html` + JS inline:** ⭐ **nenhuma
réplica da REGRA.** Escrevem campo de contrato, fora das duas portas: `import_csv.py:125-128`
(bootstrap one-shot do CSV), `routes/offseason.py:764-766` (`do_rollover`), `routes/admin.py`
(approve do M2 — **gated em `needs_review=True`**, e os 13 têm `needs_review=0`),
`routes/admin.py:598` (rollback do F8) e ⚠️ **`sync_sleeper.py:1268-1269` — o passo 6 do rebuild
[[F8]]**, que reescreve `contract_start_season` e `acquisition_type` a partir da cadeia da API.
**Medido:** o passo 6 **não toca `contract_year`** (a correção do Grupo B é imune a ele) e
`"contract_year_correction"` **não pertence** a `_ACTIVE_ACQUISITION_TYPES`
([sync_sleeper.py:836](sync_sleeper.py#L836)) — a trilha da correção **não** vira insumo do
rebuild. Em JS/template a única coisa parecida é `cap_projector.html:160`
(`const isRenewal = p.contract_year >= 4`) — **exibição**, coerente com a fronteira do motor, não
escreve. ⛔ Nenhum fator `0.5` / `0.8` / `1.2` em template nenhum.

##### Eixo 4 — interseção com o executado e com o pendente

| runner | estado | ∩ com os 13 | consequência |
|---|---|---|---|
| `off26_32_fix.py` (19 contratos, 25/08) | ✅ executado | **censo** ∩ 13 = `{6803}`; **executado** ∩ 13 = **∅** | Aiyuk está em `DROPPED_2026` — excluído **de propósito**, com o motivo já escrito lá: *"um re-add em 2026 abre contrato NOVO … quem os readquirir entra por `record_acquisition`, não por aqui"*. ⭐ A doutrina do Grupo A **já estava escrita** no runner anterior |
| `off26_20_fix.py` (22 contratos, 06/08) | ✅ executado | `{9486}` | ⚠️ **Interseção que o prompt não previu.** Wicks teve `cy 2→1` em 06/08 (`fix:off26-20`) e o rollover de 17/08 o levou a `cy=2` — o `cy=2` dele é **contrato mantido corretamente que depois morreu no drop de 20/08**, não congelamento. Muda a narrativa, **não** o devido |
| `wv1_fix_coorte.py` coorte A (19/08) | ✅ executado | **∅** | sem interação |
| `wv1_fix_coorte_b.py` | 🔲 **nunca executado** | `{3451, 8259, NE}` | confirmado — exatamente os 3 do handoff |

⭐ **Dupla aplicação: IMPOSSÍVEL nas duas ordens, e por mecanismos diferentes.**
`wv1_fix_coorte.triage` trata `cy == new_year` como **`skipped`** ("já é 2 — nada a fazer"),
**não** como abort: se este runner corrigir os 3 primeiro, a coorte B ainda escreve os outros 6.
Na ordem inversa, a guarda de `contract_year_correction` pula os 3 por divergência. ⚠️ **O custo da
ordem é operacional, não de dado:** `--check` sai **exit 1** quando `elegíveis ≠ alvos`
([off26_32_fix.py:295-297](off26_32_fix.py#L295)), então quem rodar depois **precisa da exclusão
documentada** — molde `DROPPED_2026`, exatamente o que o commit `7eaa2aa` fez com o Goedert.

##### ⚠️ Dois achados de desenho que a F2 herda

1. **O Grupo B é de canal MISTO — uma `EXPECTED` única não serve.** Medido: **6 `fa_waiver`**
   (Dicker, CHI, CLE, Fairbairn, NE, Jones) + **5 `free_agent`** (Robinson, Bates, Stafford,
   Bigsby, Tucker). ⛔ O molde `wv1_fix_coorte.triage` **ABORTA a execução inteira** com
   `acquisition_type` divergente; o molde `off26_32_fix`/`plan_correction` apenas **pula**. ⇒ ou
   **dois lotes por canal**, ou `acquisition_type` **fora** da guarda (que a enfraquece).
   ⚠️ Divergência registrada: o handoff dá o add do **CHI** como `free_agent` (05/11) e o banco
   grava `fa_waiver` — provável herança do claim de 12/11 que **só preservou**. Não muda salário
   (ambos em `_WAIVER_TYPES`); muda a guarda.
2. ⭐ **A lista TEM de ser congelada — varredura por query pegaria o Goff.** Medido no seed: **60**
   jogadores no mesmo estado (`cy` do grupo · `css=2025` · canal waiver/FA · vivo), dos quais **12**
   são dos 13 e **48 seriam falso positivo** — **Goff entre eles**. ⛔ Nenhum critério de estado
   distingue alvo de não-alvo: o discriminante é a **cadeia da API**, que o banco não carrega. A
   lista dos 13 é congelada, como o censo do [[OFF26-32]].

##### Bloco read-only para o owner fechar o eixo 1 (Render Shell, `/data/dynasty.db`)

```sql
-- os 13, por sid; identidade de time por sleeper_owner_id (nunca por nome)
SELECT p.sleeper_player_id, p.name, p.contract_year, p.contract_start_season,
       p.acquisition_type, p.salary, p.espn_ref_value, p.is_dropped, p.needs_review,
       t.sleeper_owner_id, t.name
  FROM players p LEFT JOIN teams t ON t.id = p.team_id
 WHERE p.sleeper_player_id IN ('6803','9486','8154','8259','CHI','CLE','11539',
                               '3451','421','NE','9225','10213','5870')
 ORDER BY p.sleeper_player_id;

-- controle negativo: 3163 (Goff) NAO e alvo; se entrar em qualquer lista, e falso positivo
SELECT sleeper_player_id, contract_year, contract_start_season, acquisition_type, salary
  FROM players WHERE sleeper_player_id = '3163';
```

**O que essa saída fecha:** (a) o estado dos quatro campos alvo a alvo; (b) o **ESPN do Jones**, que
decide o único indeterminado do eixo 2; (c) se algum dos 13 está `is_dropped=1` ou `needs_review=1`
em prod (qualquer um dos dois **pula ou aborta** a guarda).

#### ✅ EXECUTADO EM PRODUÇÃO (owner, Render Shell, 26/08/2026) — em DUAS etapas

Alvo `/data/dynasty.db` (`current_season=2026` · `rollover_done=true` · `offseason_mode=true`).
⭐ **Toda a cadeia foi conferida por HASH pelo owner antes de cada etapa**, e cada execução teve
**backup com `ls -la` confirmado ANTES da escrita**. ⛔ **Nenhuma etapa foi aceita por relato** — o
precedente dos **relatórios fabricados deste próprio arco** (commits `4c19a2e` e `a3f81c9`, que
**não existem no repositório**) é a origem dessa disciplina.

| etapa | commit | runner | backup | `--check` | `--apply` |
|---|---|---|---|---|---|
| **Grupo B** — contagem `cy 3→2`, 11 alvos | `32e4cc0` (deploy conferido) | `off26_37_b_fix.py` · suíte **40 verde** | `/data/pre_off26_37_b_fix.db` (**737.280 B**) | **11/11 elegíveis**, invariante intacto | **11 corrigidos · 11 linhas alteradas · 11 de trilha**, `event_ref='fix:off26-37-b'` |
| **Grupo A** — reset de 4 campos, 2 alvos | `2374f4e` (deploy conferido) | `off26_37_a_fix.py` · suíte **40 verde** | `/data/pre_off26_37_a_fix.db` (**741.376 B**) | **2/2 elegíveis**, **sem** aviso de divergência de membership | **2 resetados · 2 linhas alteradas · 2 de trilha · 2 no `auction_log` · ESPN PRESERVADO**, `event_ref='fix:off26-37-a'` |

**Grupo B (11):** `contract_year` 3 → 2, com **`contract_start_season`, canal e salário
preservados** — a correção mexeu na contagem, nunca no dinheiro (o invariante da F1, medido).

**Grupo A (2) — o caso 3 da régua aplicado:**

| sid | jogador | de | para | efeito de folha |
|---|---|---|---|---|
| `6803` | **Brandon Aiyuk** | `cy=2 · css=2025 · fa_auction · $8` | `cy=1 · css=2026 · free_agent · $1` | **−$7** no AlexTheDawg |
| `9486` | **Dontayvion Wicks** | `cy=2 · css=2025 · free_agent · $1` | `cy=1 · css=2026 · free_agent · $1` | **zero** (o salário do morto já era o devido) |

**Verificação independente, por consulta read-only DEPOIS das duas execuções** (colada pelo owner):
os **11** do Grupo B em `cy=2 · css=2025`; **Aiyuk e Wicks** em `cy=1 · css=2026 · free_agent · $1 ·
espn 1.0`; ⭐ **Goff (3163) INTACTO em `cy=3`**. **Smoke de produção na interface web confirmado
pelo owner.** ⇒ Critério de fechamento cumprido: **duas execuções + verificação independente por
consulta + smoke web**.

#### ⭐ LIÇÃO DE MÉTODO DO ARCO — o resultado certo dependeu de NÃO corrigir o Goff

**O sucesso deste arco não está nos 13 corrigidos; está no 1 que não foi tocado.** O Goff
compartilhava estado **idêntico** ao dos 11 do Grupo B no banco — a F1 mediu **48 jogadores no
mesmo perfil** que seriam falso positivo — e ⛔ **nenhuma consulta de estado o distinguiria**. O que
o separou foi a **cadeia de transações da API**: claim **12,3h** após o próprio drop, **dentro** da
janela de 48h (caso 2 — contrato de 2024 preservado), contra os **69,2h** do Jones (caso 3 —
contrato novo).

Três traços do método, para além do resultado:

1. **A medição decisiva foi feita FORA do circuito automático**, pelo owner, e **refutou** a
   alegação que vinha de um prompt anterior — a qual **atribuía ao Jones a cadeia de datas que
   pertencia ao Goff**. ⭐ Não era medição divergente: era **troca de sujeito**.
2. **Lista congelada, elegibilidade derivada.** Os dois runners nasceram com a lista de alvos
   **congelada** e cruzam **rosters ao vivo** só para decidir quem ainda está elegível — nunca para
   descobrir quem é alvo.
3. **Filtro de status na API** (registrado na arbitragem): tentativa e aquisição ocupam a mesma
   estrutura no feed do Sleeper; sem `status == "complete"` a cadeia reconstruída é outra.
   ⭐ **Candidata registrada** a baseline do `DEV_METHODOLOGY` — ⛔ a consolidação transversal é
   sessão própria, e **não** foi feita aqui.

#### O que o arco deixou registrado como backlog (nasceram desta execução)

- **[[OFF26-38]]** — passivo de salário do **Stafford** (`$2 → $3`), raiz distinta: o rollover de
  17/08 aplicou valorização onde devia ano 2 de waiver/FA.
- **[[OFF26-39]]** — **família de armadilhas de `record_acquisition`**: o token `[ref:]` decepado
  pelo truncamento e o `espn_ref_value` zerado pelo default. ⛔ A porta canônica **não** foi
  alterada; os dois runners a **contornam**.
- **[[OFF26-40]]** — caminho de banco **relativo** no molde de runner cria banco vazio em
  `instance/`. Corrigido **só no runner novo**; o artefato já executado **não foi tocado**, por
  decisão.
- **[[OFF26-41]]** — deriva de documentação: a suíte do motor salarial roda **62** testes, não as
  **54** registradas no `CLAUDE.md`.
- **[[WV1]] coorte B** (item já existente): três dos seus 9 candidatos foram corrigidos aqui e
  agora saem como `skipped` — ver a emenda registrada lá.

**Consequência MEDIDA, não pendência — o horizonte 2 do Stafford:** em `cy=3` ele chegaria a **ano
5** e **renovaria** por `floor(ESPN)` = **$4**; em `cy=2`, chega a **ano 4** com valorização = **$2**.
⭐ A correção já aplicada **muda o desfecho de 2027** — é o único ponto do Grupo B onde a contagem
tinha consequência financeira, e ela foi resolvida a favor do correto.

---
