# improvements.md — Fantasy Manager

> Backlog vivo de melhorias, bugs e features pendentes.
> Atualizado em: 08/06/2026 (lottery M15/M15-FIX/M16; OFF26-3 importador; E1 import ESPN ✅ prod; E2 store de valores ESPN de rookie; DP1 board pré-draft; F9/F10/M17/M18 registrados)
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
| M1 | Alerta de cap estourado pós-S1 (preview escalonado + warnings de sync, banner gated por offseason) | Média | ✅ 27/04/2026 |
| M1-FOLLOWUP | Avaliar auto-desativação de offseason mode após FA auction concluído (banner M1 persiste como ruído se admin esquecer de desligar manualmente) | Baixa | 🔲 |
| MAN-S1-FIX | Backfill de previous_league_id reverte estado pós-trades da current league (idempotência cross-season + movimentação cega de Player.team_id em `_sync_trades`) | Alta | ✅ 28/04/2026 |
| M2 | Tela de aprovação em lote de jogadores `needs_review=True` | Média | ✅ 27/04/2026 |
| M3 | Exportar dynasty.db em formato legível para os outros owners | Baixa | 🔲 |
| M4 | Banner de sync desatualizada com timestamp e botão "Sincronizar agora" | Baixa | 🔲 |
| M8 | Auditoria do lottery (seed + página de verificação) + visualização de bolinhas + fluxo em 2 fases | Baixa | ✅ 23/04/2026 |
| M9 | Redesign tela de picks: grid navegável + atalho para trade | Média | ✅ 23/04/2026 |
| M10 | Busca de Jogador: Global + Calculadora (refinado 28/04/2026 — MAN-M10-REFINE) | Média | 🔲 |
| M11 | Teste de auto-containment documental | Média | ✅ 22/04/2026 |
| M12 | Vincular owners a times via tela de admin com lookup do Sleeper | Média | ✅ 22/04/2026 |
| M13 | Página de jogador + "Propor Trade" | Média | ✅ 23/04/2026 |
| M14 | /trades aceitar query params team_a/team_b (pré-requisito M9 + M13) | Média | ✅ 23/04/2026 |
| M15 | Lottery com 6 seeds (inclusão do 7º colocado com 1 bolinha; pool 96) — MAN-M15-REG | Média | ✅ 05/06/2026 |
| M15-FIX | Editor de pesos do lottery: pool/legenda não re-renderizam ao editar + legenda /picks pós-sorteio lê canônico, não o audit | Média | ✅ 05/06/2026 |
| M16 | Lottery aplica ordem sorteada a R2/R3 (deveria ser standings invertido) — corrompe ordem + valores dynasty de R2/R3 — MAN-M16-REG | Alta | ✅ 05/06/2026 |
| OFF26-1 | Janela de keepers/cuts selada no Manager (declaração privada + budget ao vivo + lock e revelação simultânea no deadline, audit padrão M8) — MAN-OFF26-REG | Alta | 🔲 |
| OFF26-2 | Keeper sheet exportável (relatório por time pós-revelação: keepers, salários, budget FA) — insumo do Cowork — MAN-OFF26-REG | Alta | 🔲 |
| OFF26-3 | Importador de drafts de liga fantasma (rookie linear + FA auction via API, match por sleeper_player_id, preview + helper atômico) — MAN-OFF26-REG | Alta | ✅ 05/06/2026 |
| OFF26-4 | Auditoria de keepers pré-leilão (diff keeper sheet × config real da liga fantasma via API read-only) — MAN-OFF26-REG | Média | 🔲 |
| OFF26-5 | Runbook do procedimento Cowork (documentação da transcrição supervisionada da keeper sheet → liga fantasma) — MAN-OFF26-REG | Média | 🔲 (doc) |
| F9 | `bulk_register` (/auction) cria jogadores sem SalaryHistory — risco de dano silencioso já existente (achado de MAN-OFF26-3-F1; exige F1 de avaliação de dano antes do fix) | Alta | 🔲 |
| F10 | `draft_budget` replicado em JS no cap_projector (viola "1 fonte por modo de render", T2-FIX-2; cliente deve consumir endpoint canônico) — achado de MAN-OFF26-3-F1 | Média | 🔲 |
| M17 | Personalização por usuário logado: home + cap widget + 8 surfaces derivam de `current_user.team_rel` (fonte única `inject_user_team`; réplica JS do chip removida) — prompt MAN-M15-REG (ID remapeado: M15 ocupado) | Alta | ⚠️ |
| M18 | Timestamps no fuso do usuário: fonte única (`timeutil.utc_iso` + macro `local_dt` + JS `formatLocalDT`); ~11 sites migrados; armazenamento UTC mantido — prompt MAN-M16-REG (ID remapeado: M16 ocupado) | Média | ✅ 09/06/2026 (validado em prod: sync 11:47 BRT → "11:47", não 14:47 UTC) |
| E1 | Import ESPN robusto end-to-end no Render: upload manual do PDF + degradação graciosa (sem 500) + estado de review em FS gravável + parser 299→300 — MAN-E1-REG/F1/F2/FIX | Alta | ✅ 08/06/2026 (validado em prod: upload → review 300, sem 500) |
| E2 | Camada de dados: store de valores ESPN de rookie keyed por `sleeper_id` (resolve not_found+approx via pool global do Sleeper, nome+team) — consumido pelo salário do rookie draft (OFF26-3) + board DP1; rejeita Sleeper-sync e stub-$1 — MAN-E2 REG/F1/REFINE/F2 | Alta | ⚠️ store implementado + validado em localhost (12/12); store validável em prod via import; aplicação no draft só e2e no rookie draft real (~ago) |
| E3 | Import ESPN upload-only: remover a opção de URL (download inviável em prod — ESPN bloqueia IP do Render); remoção completa UI + fetch server-side + degradação graciosa associada — MAN-E3-REG (vai REG → F2 direto, sem F1) | Baixa/Média | 🔲 |
| E2-RISK | Review do import ESPN oferece rookie como match fuzzy de veterano (falso-positivo "Carnell Tate"~"Darnell Mooney" 0.665) → confirm errado contamina `espn_ref_value` do veterano (classe "Brown"). **F2: default neutro no select + confirm gated (sem confirm-por-inércia); raiz do matcher → E4-a** — MAN-E2RISK-REG/F1/F1B/F2 | Média | ⚠️ (validado localhost; pendente smoke prod com import ESPN) |
| E4 | **Guarda-chuva** — redesenho da camada de valor ESPN (`espn_ref_value` por `sleeper_id`); F1 de design concluída → fatiado em E4-a/b/c — MAN-E4-F1 | — | 🔲 (fatiado) |
| E4-a | Matcher do import ESPN resolve entrada → `sleeper_id` (pool global, nome+team Brown-safe), não fuzzy contra roster; escreve via id; sem schema. Elimina o "Brown" na raiz + troca corrupção→miss. **Absorve o conserto do matcher ex-E2-RISK** — MAN-E4-F1/F2 | Alta | ⚠️ (validado localhost; pendente smoke prod com import real) |
| E4-b | Saneamento de `sleeper_id`: F1 refutou backfill — os 2 nulos (Hollywood Brown=dup de Marquise Brown; Cameron Ward=dup de Cam Ward) são **duplicatas órfãs → DELETE** (+ 1 PlayerHistory stray) via rota admin auditável em PROD; **guard** (dedup-por-sid + `needs_review` no import_csv) p/ a causa-raiz. Sem schema — MAN-E4-F1/E4-b-F1/F2 | Média | ✅ 09/06/2026 (limpeza executada em prod: 2 removidos, 278 players, 0 sid nulo, canônicos intactos) |
| E4-c | **Guarda-chuva** — store canônico de valor ESPN `(sleeper_id, season)`; F1 de migração concluída → sub-fatiado em E4-c-1/E4-c-2 — MAN-E4-c-F1 | — | 🔲 (sub-fatiado) |
| E4-c-1 | Fundação do store (aditivo/reversível): tabela `espn_value_store (sleeper_id,season)[raw,adjusted,is_final]` via `db.create_all()` + backfill da coluna (Migration 7, season 2026 prelim) + helper único `set_espn_value` nos 8 escritores + badge PROV repontada ao store. **Entrega o store ao DP1.** — MAN-E4-c-F1/F2 | Alta | ✅ 09/06/2026 (backfill em prod: 273 linhas, schema ok, store==coluna, coluna intocada) |
| E4-c-2 | Limpeza do store (destrutivo/isolado): DROP ESPNValue (vazio) + generalizar/migrar RookieEspnValue. Único passo irreversível-sem-backup; higiene após E4-c-1; **não bloqueia DP1** — MAN-E4-c-F1 | Baixa (higiene) | 🔲 |
| DP1 | Board de planejamento de cap pré-draft: rookies entrantes com `espn_ref_value` + salário projetado `floor(ESPN×1.2)` + simulação de impacto no cap (projeção, não contrato) — lê o **store canônico** — MAN-DP1-REG | A definir | 🔲 (desbloqueado: E4-c-1 ✅ em prod) |
| WV1 | Salário de aquisição via waiver sem drop tratado como FA (waiver de jogador nunca dropado → regra de salário de FA); toca `record_acquisition` + histórico — MAN-WV1-REG | Média | 🔲 |
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
| O2 | Enriquecer página do jogador: contexto NFL (time + depth chart) + stats históricas + ECR/ADP + schedule | Média | 🔲 |
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
| UX4-b | Redesign de densidade e layout da página de detalhe de time (4 camadas + ESPN/Projeção em ambas telas) | Triagem | ✅ 24/04/2026 |
| UX4-c | Aperto visual final de /team/<id> e / (status bar + progress bar nova + espaçamento entre grupos + colgroup denso) | Média | ✅ 24/04/2026 |
| UX4-d | Tabela única de roster com pos inline (elimina cabeçalhos repetidos por posição) | Média | ✅ 24/04/2026 |
| UX4-e | Remover fundo pintado das rows por posição (preservar strip + cor no nome) | Média | ✅ 24/04/2026 |
| UX7 | Tema visual global mais claro (recalibragem da paleta dark) | Média | ✅ 24/04/2026 |
| UX6 | Revisão da largura máxima do container global da aplicação (~700px de ar lateral em monitor 1920px) | Média | 🔲 |
| UX5 | Redesign da seção Picks em detalhe de time (3 tabelas anuais com baixa densidade, coluna Notas vazia) | Média | 🔲 |
| DATA-1 | Badges TRADE e REVISÃO removidos da macro de listagem (info pertence à timeline/admin, não à listagem) | Média | ✅ 24/04/2026 |
| T3 | Valores redraft do FantasyCalc no Trade Manager (modelo 3 — duas barras independentes dynasty + redraft) | Média | ✅ 27/04/2026 |
| T3-FIX-UX | Migrar barras dynasty + redraft de dual-fill (T2 pattern) para delta-pointing + corrigir overflow mobile + redraft no modal preview + descrição de trade em formato "de/para" 2-colunas + alinhamento vertical entre colunas (5 sub-iterações, owner-driven via screenshot mobile) | Média | ✅ 27-28/04/2026 |

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

### M17 — Personalização por usuário logado (default team + cap widget)
⚠️ **Implementado (F2) — pendente smoke em produção** — Prioridade **Alta** — prompt MAN-M15-REG (ID remapeado: M15 já era o Lottery)

**CONTEXTO**
Feedback de produção do Michel (owner do team_id=8, "Trust the Process") em
07/06/2026, via screenshots no WhatsApp. Com o multi-usuário (X1) ativo e os 12
owners acessando o Manager, surfaces que assumem um único usuário ficaram expostas.

**PROBLEMA / OPORTUNIDADE**
Duas surfaces ignoram o usuário logado e mostram dados do time do admin (Cangaceiros
da Colina): (1) ao abrir o site, o primeiro time exibido é o do Erico, não o do
usuário logado; (2) o widget de cap no topo mostra "$255/$200" — valores do
Cangaceiros — estático para todos os usuários, em vez de puxar o cap do time de quem
logou. Para um app multi-usuário, o estado padrão deve ser centrado no time do
próprio owner.

**DISCUSSÃO**
- O valor $255 do screenshot bate com o active_salary atual do Cangaceiros
  (confirmado pós MAN-S1-FIX), indicando que o widget renderiza o time errado, não
  um valor stale.
- Hipótese de causa raiz comum: resquício do conceito single-user "my team" (flag
  legada em vez de `current_user.team_rel`). M9/M13 já usam o padrão correto
  (`my_team_name = current_user.team_rel.name`), então existe precedente canônico.
- Possível que existam outras surfaces com o mesmo vício além das duas reportadas —
  F1 deve mapear o conjunto completo antes de fechar escopo.

**DECISÕES JÁ TOMADAS**
- Um único item para as duas surfaces (mesma família de causa raiz).
- Padrão alvo: derivar o time padrão de `current_user`, com fallback definido para
  admin/usuário sem time vinculado (comportamento exato a decidir na F1).

**ALTERNATIVAS DESCARTADAS**
- Dois itens separados (um por surface): rejeitado — fix fragmentado arriscaria
  corrigir uma surface e deixar a outra com a mesma raiz.

**QUESTÕES EM ABERTO** (F1)
- De onde vem hoje o "time padrão" da home e o time do cap widget? Mesma fonte?
- Quais outras surfaces assumem "my team" fixo?
- Qual o fallback para usuário sem time vinculado (team_id NULL) e para o admin?
- O cap widget tem réplica de lógica em JS/template além do backend?

**F1 — ACHADOS (diagnose read-only, concluída)**

Confirmada a hipótese de causa raiz: nenhuma surface reportada deriva de
`current_user.team_rel`; todas ancoram no conceito legado single-user
(`MY_TEAM_NAME` em `models.py:12` / flag `Team.is_my_team`), que resolve sempre
para o time do admin (Cangaceiros). O `$255` bate com `active_salary()` real do
Cangaceiros → time errado renderizado, não valor stale.

*Conjunto completo de surfaces com "my team" fixo:*

- **Funcionais** (renderizam dados/estado do time errado):
  1. Home — default do roster: `routes/roster.py:53` (`request.args.get("team", MY_TEAM_NAME)`).
  2. Home — fallback do roster: `routes/roster.py:63` (`Team.query.filter_by(is_my_team=True)`).
  3. Cap widget — chip JS: `templates/base.html:157-167` (`teams.find(t => t.is_my_team)` sobre `/api/teams`).
  4. Cap widget — título: `templates/base.html:71` (string `"Cangaceiros da Colina"` hardcoded).
  5. Cap Projector — pré-seleção: `routes/salary.py:22-25` (`Team.query.filter_by(is_my_team=True)`).
- **Cosméticas** (enfeite visual no time do admin para qualquer usuário):
  6. Tag "EU" no dropdown "Times ▾": `templates/base.html:51` e `:116` (mobile).
  7. League Hub — destaque do card `league-card-mine` + tag "EU": `templates/league.html:12,25`.
  8. Header do roster — prefixo 🏆: `templates/roster.html:15` (`summary.team.is_my_team`).

*Réplica, não fonte única:* a resolução do "meu time" existe em quatro lugares no
padrão legado — rota Python (home + cap projector), JS client-side (chip),
literal hardcoded (título do chip). O cap widget **re-resolve no cliente** (não
consome valor server-side); o server não envia "qual é o time do usuário" ao
template.

*Precedente canônico a replicar:* derivação por `current_user.team_rel` já
coexiste em `/team/<id>` (`routes/league.py:103-110`), banner M1
(`routes/roster.py:89-92`) e picks (`routes/picks.py:81`) — inclusive já tratam
`team_rel is None` como estado neutro.

*Fallback hoje:* as surfaces fixas não quebram com usuário sem time — mostram o
time do admin **por acidente**, não um estado neutro. As surfaces canônicas já
tratam `team_rel is None` (estado neutro / `my_team_name=None`).

*Observação:* `MY_TEAM_NAME` é importado em `routes/trades.py:9` mas **não** usado
para default (pré-seleção é só via query param M14) — import possivelmente morto.

**DECISÕES DE ESCOPO F2 (owner, pós-F1)**
1. **Fallback para usuário sem time vinculado (team_id NULL): estado neutro**
   (sem time, sem cap) — alinhado ao padrão canônico já existente
   (`team_rel is None` → neutro em `/team/<id>` e M1).
2. **Surfaces cosméticas entram na F2 junto com as funcionais** — mesma
   causa-raiz; corrigir num só passo (as 8 surfaces acima).
3. **Cap widget passa a resolução server-side, eliminando a réplica JS** —
   reaproveitar o padrão de context processor já usado na navbar
   (`inject_nav_teams` em `app.py:90-99`).

**F2 — IMPLEMENTAÇÃO (08/06/2026, ⚠️ validado em localhost)**

*Fonte única server-side:* novo context processor `inject_user_team` (`app.py`)
injeta `g_user_team` (= `current_user.team_rel` ou `None`) e `g_user_team_cap`
(= `active_salary()`) em todos os templates. É a única resolução do "time do
usuário" nas surfaces de exibição; replica o precedente canônico (`/team/<id>`,
M1, picks). Usuário sem time → `None` → estado neutro.

*8 surfaces unificadas:*
1. Home default — `roster.py:index` deriva de `current_user.team_rel.name`;
   `?team=` ainda permite ver outro time; fallback robusto cai no próprio time, não
   num time fixo; sem time → neutro (`summary=None`).
2. Home fallback — eliminado `filter_by(is_my_team=True) or teams[0]`.
3. Cap chip valor — renderizado server-side em `base.html` a partir de
   `g_user_team_cap` (réplica JS `loadCapChip` removida).
4. Cap chip título — `title="Cap: {{ g_user_team.name }}"` (literal "Cangaceiros
   da Colina" removido).
5. Cap projector — `salary.py` pré-seleciona `current_user.team_rel`.
6. Tag "EU" dropdown Times (desktop+mobile) — `t.id == g_user_team.id`.
7. League Hub `league-card-mine`+EU — `_build_team_card` recebe `my_team_id` do
   usuário logado; flag legada `team.is_my_team` não é mais lida.
8. Header roster 🏆 — `summary.team.id == g_user_team.id`.

*Limpezas:* import morto `MY_TEAM_NAME` removido de `routes/trades.py` e
`routes/roster.py`; projeção `Team.is_my_team` removida de `inject_nav_teams`
(`app.py`) — agora dado morto na navbar. A flag `is_my_team` permanece como
**dado** escrito pelo sync (schema/`sync_sleeper.py`/`record_acquisition`/
`/api/teams` to_dict) — apenas deixou de ser fonte de "time do usuário".

*Validação localhost (test_client, DB copiado, login via sessão):* 8/8 critérios.
Michel (team 8) → home + chip `$183/$200` "Trust The Process"; Erico (team 5) →
Cangaceiros; usuário sem time → neutro (200, "Sem dados", sem chip); cap projector
pré-seleciona o time certo; `league-card-mine`/🏆 no time do usuário; chip
server-side sem `teams.find`/`loadCapChip`. `salary_engine_test.py` 48/48.
**Pendente:** smoke em produção (login real dos owners).

**DEPENDÊNCIAS**
- Depende de: nenhum item aberto (X1 concluído). Bloqueia: nenhum.

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

### WV1 — Salário de aquisição via waiver sem drop tratado como FA
🔲 **Pendente** — Prioridade **Média** — prompt MAN-WV1-REG (novo: 1º item da série WV/waiver)

**CONTEXTO**
Regra de aquisição emergida em discussão de 08/06/2026 (durante o MAN-M18). A liga
distingue dois caminhos de aquisição fora de draft: **waiver** e **free agency (FA)**.
Um jogador é adquirido via waiver quando **nunca foi dropado por nenhum time**; caso
contrário, via FA. O salário atribuído ao contrato difere conforme o caminho.

Caso ilustrativo (Puka, rookie year): plausível que um rookie não seja draftado no
rookie draft e, após boa performance na semana 1, vire alvo de disputa via waiver.
Como nunca foi dropado por nenhum time, a aquisição se dá por **waiver** — mas o
salário deve ser tratado **como se viesse via FA**, justamente porque não houve drop
prévio.

**PROBLEMA / OPORTUNIDADE**
A lógica atual de criação de contrato (`record_acquisition` → `salary_engine`) resolve
salário por tipo de aquisição, mas a distinção **waiver-sem-drop → salário-como-FA**
ainda não está representada. Sem isso, uma aquisição via waiver de jogador nunca
dropado poderia receber tratamento de salário incorreto quando a regra for
implementada.

**DISCUSSÃO**
- O caminho (waiver vs. FA) depende do **histórico do jogador**: existência ou não de
  drop prévio por algum time.
- Quando não houve drop, o salário segue a regra de **FA** mesmo que o mecanismo de
  aquisição seja waiver.
- A regra toca o helper canônico (`record_acquisition`) e potencialmente o histórico
  (`PlayerHistory` / `AuctionLog`) — relevante para **não remover ainda** campos hoje
  "mortos" no payload (decisão do MAN-M18: preservar `created_at` de `AuctionLog` e do
  salary history, pois podem virar campos vivos aqui).
- Regulamento da liga a confrontar na F1 (cláusulas de waiver/FA e salário associado)
  antes de fechar escopo.

**DECISÕES JÁ TOMADAS**
- Waiver de jogador **nunca dropado** → salário tratado como **FA**.
- Registro agora, implementação adiada (depende do pacote offseason / lógica de
  aquisição).
- Campos de timestamp hoje não exibidos (`AuctionLog`, salary history) **preservados**
  — possíveis consumidores desta regra.

**ALTERNATIVAS DESCARTADAS**
- (a definir na F1)

**QUESTÕES EM ABERTO** (F1)
- Como a aplicação sabe hoje se um jogador foi dropado por algum time (fonte do sinal:
  Sleeper transactions, `PlayerHistory`, flag)?
- O regulamento define salários distintos para waiver vs. FA além do caso sem-drop?
  Quais valores/regras exatas?
- O `record_acquisition` já recebe o tipo de aquisição de uma fonte confiável, ou o
  tipo é inferido?
- Esta regra de salário tem ou terá réplica (JS do cap projector, preview de draft
  import)?

**DEPENDÊNCIAS**
- Depende de: lógica de aquisição / pacote offseason (criação de contrato fora de
  draft).
- Relaciona-se com: **OFF26-3** (importador de drafts), **E2** (salário de rookie),
  **F9** (consolidação em `record_acquisition`).
- Bloqueia: nenhum item aberto hoje.

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

### E2 — Store de valores ESPN de rookie (camada de dados)
⚠️ **Store implementado + validado em localhost (08/06/2026) — aplicação no draft aguarda o rookie draft real** — Prioridade **Alta** — MAN-E2 REG/F1/REFINE/F2

**CONTEXTO**
No smoke test do E1 em produção, o owner notou que rookies da tabela ESPN não foram
"identificados" (ex.: **Carnell Tate** WR/TEN/$12 — citado como "Cornell Tate").

**PROBLEMA / OPORTUNIDADE**
**Não é bug de parse nem de matching** — o parser lê "Carnell Tate, TEN, $12"
corretamente; ele simplesmente **não existe no DB** (rookie 2026; rookies entram só no
rookie draft, passo 5, *depois* do import ESPN, passo 3). O ESPN PPR Top 300 inclui
rookies + FA fora do elenco → caem em **not_found** → o valor ESPN é **descartado**
(E1-VERIFY confirmou: not_found = skip puro). Quando o rookie é criado no rookie draft
(via OFF26-3 ou `/auction`), `salary = floor(ESPN×1.2)` **não tem o valor** → default
**$1** no importador (ou exige digitação manual no `/auction`). Resultado: salários de
rookie errados se a fonte não for resgatada.

**DIMENSIONAMENTO (contra o DB de produção, 08/06/2026):** dos 300 parseados, 71 são
not_found (28 K/DST + **43 skill**). Os skill são majoritariamente **rookies 2026** de
valor relevante — ex.: **Jeremiyah Love RB $46** (rank 12), **Carnell Tate WR $12**,
Makai Lemon, KC Concepcion, Kenyon Sadiq TE, Omar Cooper Jr. Parte são veteranos/FA com
**$0** (Rashod Bateman, Pat Freiermuth, Samaje Perine…) — esses são **inofensivos** (já
virariam $1). O dano concentra-se nos **rookies de alto valor**.

**PROPOSTA (F1 read-only decide a forma):**
- Opções a avaliar: (a) permitir **criar player** a partir de entradas not_found no review
  (stub + espn_ref_value antes do draft); (b) **persistir** os not_found num store de
  valores ESPN pendentes, aplicados quando o player for criado; (c) o importador OFF26-3 /
  `register_rookie` **buscar o valor** num snapshot ESPN ao criar o rookie; (d) manter
  digitação manual como fallback (`register_rookie` já aceita `espn_ref_value`).
- Não auto-criar players sem revisão; preservar os caminhos canônicos de escrita.

**DEPENDÊNCIAS**
- Relaciona-se a **OFF26-3** (importador de rookie precisa do `espn_ref_value` p/ o salário).
- Workaround atual: admin digita o ESPN value no `/auction` ao registrar o rookie.
- Bloqueia: salário correto no **rookie draft 2026** (passo 5).

#### Fase 1 Diagnose ✅ (08/06/2026) — MAN-E2-F1 (read-only, zero writes)

- **(a) Sync cria Player para roster novo? SIM.** `run_sync` (sync_sleeper.py:260-282)
  cria com estado **stub**: `salary=$1, contract_year=1, contract_start_season=CURRENT_SEASON,
  acquisition_type="unknown", espn_ref_value=0, needs_review=True`, linkado por
  `sleeper_player_id`. Em players **existentes nunca toca** salary/contract/acquisition_type
  (linha 242). Match: sleeper_id → nome normalizado (sem fallback de sobrenome — fix 3 Browns).
- **(b) Rookies já rosterados na liga? NÃO — premissa do owner refutada.** Carnell Tate
  (id 13279), Jeremiyah Love (13287), Makai Lemon (13294), KC Concepcion (13298) existem
  no **pool global** do Sleeper (têm id) mas **0 de 4 estão rosterados** (273 rosterados na
  liga, nenhum deles). Rookies só entram em roster **quando draftados** (passo 5). Logo um
  sync agora **NÃO** criaria a row do Carnell Tate.
- **(c) Rookie draft cria ou atribui? Idempotente por sleeper_id.** O importador OFF26-3
  (`draft_import.py`) resolve por `find_player_by_sleeper_id` → **atualiza** se existir,
  **cria** (`record_acquisition(player=None, sleeper_player_id=…)`) se não; idempotente por
  `event_ref`. **Pré-popular um player (stub) com o sleeper_id é SEGURO** — o importador o
  casa por id, sem colisão/duplicata. `register_rookie` (`/auction`) casa por **nome+team**
  → risco pequeno de duplicata se o nome divergir (caminho manual).
- **(d) `floor(ESPN×1.2)`: fonte única, sem réplica.** O **salário** rookie é só
  `salary_engine.year1_salary("rookie_draft",0,espn_adj)` → `_floor(espn_adj)`, consumido por
  `record_acquisition` (importador + `/auction`). O `×1.2` (raw→ajustado) é conversão de
  **boundary** em cada entrada (auction/admin/salary/parser), por design (CLAUDE.md). **Sem
  réplica do cálculo de salário em JS/templates** — só texto de display ("floor(ESPN×1.2)").
- **(e) Ordem sync → ESPN Final → rookie draft fecha o gap? NÃO.** Dois motivos: (1) rookies
  não estão rosterados pré-draft (b) → sync não os traz; (2) **o Sleeper não tem ESPN value**
  (é roster-only) — o valor existe **só no PDF**. A via Sleeper-sync **não fornece** o
  `espn_ref_value`. (Se os rookies estivessem rosterados, não haveria hazard de escrita: sync
  casa por sleeper_id, ESPN import faz upsert por player+season, importador casa por id — tudo
  idempotente. Mas é moot: eles não estão.)

**RECOMENDAÇÃO → solução ESPN-side (via Sleeper-sync NÃO é viável).** Insight aproveitável:
os rookies **existem no pool global do Sleeper com `sleeper_player_id`** (só não rosterados).
Então dá para, no review do import, **mapear cada not_found (nome) → pool global do Sleeper →
`sleeper_player_id`** e, por essa chave: (opção stub) criar um Player stub com `espn_ref_value`,
ou (opção pending-store) persistir o valor ESPN keyed por `sleeper_id`. Em qualquer das duas,
o **importador OFF26-3 casa por `sleeper_id` e aplica idempotentemente** ao criar o rookie no
draft — sem inventar dados (PDF dá nome+valor, pool do Sleeper dá o id canônico). **Disparar
REFINE do E2** para escolher entre *stub no review* × *pending-store* antes de qualquer F2.
Status E2 permanece 🔲.

#### REFINE ✅ (08/06/2026) — MAN-E2-REFINE: re-escopo como camada de dados
A discussão de produto revelou um **segundo consumidor** do valor ESPN de rookie além do
salário no draft: um **board de planejamento de cap pré-draft** ([[DP1]]). Com dois
consumidores, o armazenamento fica decidido.

**Escopo final (contratos fixados; mecânica fica p/ o F2):**
- No import ESPN, cada `not_found` é resolvido para um **`sleeper_player_id`** via o **pool
  global do Sleeper**, usando o **matcher canônico com nome+team** como desambiguador (sem
  substring/sobrenome isolado — risco "Brown").
- O `espn_ref_value` resolvido é persistido num **store de valores keyed por `sleeper_id`**
  (camada de dados; formato exato no F2).
- **Consumidor (a):** o caminho de criação de rookie (**OFF26-3**) lê o store ao materializar
  o rookie no draft e aplica `floor(ESPN×1.2)` **idempotentemente** (casa por `sleeper_id`).
- **Consumidor (b):** o **board de planejamento de cap** ([[DP1]]).
- **Limpeza:** o store é transitório do ciclo de draft — limpar/expirar pós-draft (o contrato
  vivo passa a ser a fonte). Entradas **$0** e **K/DST** são inócuas/fora do foco.

**Rejeitadas:**
- **Via Sleeper-sync** (E2-F1): inviável — rookies não rosterados pré-draft e o Sleeper é
  roster-only (não tem ESPN value).
- **Player stub de $1:** rejeitada — viola "rookie entra só pelo draft", polui roster/cap com
  meio-contratos de $1, e serve mal o board de planejamento.

Próximo: **MAN-E2-F2** (implementar o store + aplicação no draft). E2 permanece 🔲.

#### Fase 2 Implementação ⚠️ (08/06/2026) — MAN-E2-F2
Regulamento **8.2.7**: salário de rookie = ESPN ref × 1,2 — encapsulado no `salary_engine`.

**Camada de dados (`models.py`):** modelo **`RookieEspnValue`** (`uq(sleeper_id, season)`),
criado por `db.create_all()` (sem migration). Helpers: `upsert_rookie_espn` (idempotente),
`rookie_espn_adjusted(sid, season)`, `clear_rookie_espn_store(season=None)`. Guarda
`espn_adjusted` (= raw×1.2, ref value — **não** salário); NÃO é Player (não polui roster/cap).

**População (`routes/admin.py`, no confirm do import):** `_resolve_not_found_to_store`
resolve cada candidato (`not_found` **+ approximate não resolvido a player do DB**) contra o
**pool global do Sleeper** via `_norm_name` + **desambiguação por team** (nome único → ok;
múltiplos → exige team único, senão `ambiguous` e não chuta — **Brown-safe**, sem
substring/sobrenome). Exclui **$0** e **K/DST**. Upsert idempotente (provisório reimportável).
Achado: rookies podem cair em **approximate** por falso-positivo de fuzzy (ex.: "Carnell Tate"
~ "Darnell Mooney" 0.665) — por isso o approximate-skipped também entra no store.

**Consumo no draft (`routes/draft_import.py` / OFF26-3):** ao materializar o rookie (criar
por `sleeper_id`, ou matched sem espn), busca `rookie_espn_adjusted` e passa a
`record_acquisition`, que deriva `floor(ESPN×1.2)` via `year1_salary` — **sem replicar o
cálculo**. Idempotente por `event_ref`. O preview também exibe o salário projetado dos
unmatched a partir do store.

**Limpeza (`routes/offseason.py`):** `toggle_rookie_draft` (marcar concluído) chama
`clear_rookie_espn_store()` — store é transitório do ciclo de draft.

**Validação (08/06/2026) — 12/12** (test_client, temp DB; PDF real + pool read-only):
store populado (Jeremiyah Love sid 13287 → adj **55**; **Carnell Tate 13279 → adj 14**);
re-import upsert sem duplicar; $0/K-DST fora; **Brown-safe** (nome do store == nome do pool
p/ o sid); matched (Bijan 68) intocado e fora do store; rookie criado → salário **floor(55)=55**
via `record_acquisition` (SalaryHistory+AuctionLog); cleanup zera o store; `salary_engine` 48/48.

**Status ⚠️ (não ✅):** o store + resolução + população são **validáveis em prod agora** (rodar
um import e conferir o store); a **aplicação no draft** só tem e2e no **rookie draft real (~ago,
regra 8.2.2)**. Regra "✅ só após prod". **DP1 desbloqueado** — o store existe; F1/F2 do DP1 podem
seguir.

**⚠️ Risco residual conhecido (candidato a item — classe "Brown"):** a mitigação cobre o
approximate-**skipped**, mas se o admin **CONFIRMAR** um match falso de fuzzy (ex.: "Carnell Tate" →
"Darnell Mooney" 0.665), o valor ESPN do rookie **contamina o `espn_ref_value` de um veterano real**.
Fix limpo (próxima sessão): não oferecer como fuzzy-match contra veterano do DB uma entrada que já
resolve para o `sleeper_id` de um rookie (rebaixar/sinalizar esses candidatos no review).

**Arquivos:** `models.py` (modelo + helpers), `routes/admin.py` (resolver + confirm),
`routes/draft_import.py` (consumo), `routes/offseason.py` (limpeza), `CLAUDE.md`.

---

### E3 — Import ESPN upload-only: remover a opção de URL
🔲 **Pendente** — Prioridade **Baixa/Média** — MAN-E3-REG (08/06/2026) — **vai REG → F2 direto (sem F1)**

**CONTEXTO**
O import ESPN (passo 3 do offseason workflow) oferece hoje dois caminhos de entrada:
**upload do PDF** (recomendado) e **download por URL** (alternativa, com degradação
graciosa). O **E1** estabeleceu que o download por URL é **estruturalmente inviável em
produção** — a ESPN bloqueia o IP de datacenter do Render (anti-bot). Como o import é
operação de **prod** (único contexto real de uso pelo admin), a URL nunca funciona lá
e só gera ruído/confusão na UI.

**PROBLEMA / OPORTUNIDADE**
A opção de URL é uma falsa escolha em produção: o owner pode tentá-la, ela falha (cai
na degradação graciosa → flash), e o caminho real continua sendo o upload. Remover a
URL simplifica a UI e elimina código (fetch server-side + a degradação graciosa que
existia **só** para cobrir esse fetch).

**DISCUSSÃO**
- **E1-F1 já isolou** download/parse/match num **único caminho server-side**
  (`routes/admin.py` + `espn_pdf_parser.py`), **sem réplica** em JS/templates. A
  isolação já está diagnosticada → o item pode ir **REG → F2 direto, sem F1**.
- **Nuance:** a URL **funciona em dev/localhost** (E1-F1), mas o import é operação de
  prod — o ganho de manter a URL para dev é **marginal** e não justifica o ruído em
  prod.
- UI atual: "UPLOAD DO PDF (RECOMENDADO)" + "...OU URL DO PDF ESPN PPR (ALTERNATIVA)".

**DECISÃO DE ESCOPO (a confirmar pelo owner na F2)**
- **(a) Remoção completa — RECOMENDADA:** input de URL na UI **+** caminho de download
  server-side **+** a degradação graciosa associada (que existia só para cobrir esse
  fetch). Resultado: import **upload-only**, menos código e superfície de erro.
- **(b) Esconder só a UI**, mantendo o backend de download: descarta menos código e
  preserva a URL para dev, mas deixa caminho morto em prod. Menos limpo.

**ALTERNATIVAS DESCARTADAS**
- Manter ambos como está: rejeitado — a URL é falsa escolha em prod (origem do item).

**DEPENDÊNCIAS**
- Depende de: **[[E1]]** (✅ — upload é o caminho funcional comprovado em prod).
- Relaciona-se com: nada aberto. Bloqueia: nenhum.

---

### E2-RISK — Fuzzy oferece rookie como match de veterano no review (classe "Brown")
⚠️ **Implementado (F2) — validado em localhost; pendente smoke em prod com import ESPN real** — Prioridade **Média** — MAN-E2RISK-REG/F1/F1B/F2 — **RE-ESCOPADO (híbrido): E2-RISK = só o mínimo de tela; conserto do matcher (raiz) → [[E4-a]]**

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

### E4 — Redesenho da camada de valor ESPN (`espn_ref_value` por `sleeper_id`)
🔲 **Pendente (guarda-chuva)** — origem **MAN-E2RISK-F1B**; F1 de design concluída (MAN-E4-F1, 09/06/2026) — **FATIADO em [[E4-a]] (agora) / [[E4-b]] (em seguida) / [[E4-c]] (atrelado a [[DP1]])**

**CONTEXTO**
Surgiu da diagnose **[[E2-RISK]]**-F1B. A proposta do owner: tratar `espn_ref_value`
como **atributo do jogador resolvido por `sleeper_id`** (chave canônica, à prova de
homônimo), com o **uso** variando por status de roster (veterano → referência de
contrato; rookie/FA fora da liga → projeção de salário de draft). Sob esse desenho, o
matcher do import ESPN teria **uma única tarefa — resolver entrada ESPN → `sleeper_id`**
— e os consumidores leriam por id, eliminando o falso-positivo "Brown" **na raiz** (o
valor pousa no jogador certo por id, não por similaridade de nome).

**PROBLEMA / OPORTUNIDADE**
Hoje há **três tabelas de valor ESPN** sob chaves distintas — `Player.espn_ref_value`
(por player), `ESPNValue` (player_id+season, exige Player), `RookieEspnValue`
(sleeper_id+season, transitório). O matcher resolve por **fuzzy contra o roster local**
(origem do hazard E2-RISK). Convergir matcher + armazenamento para a chave certa
(`sleeper_id`) de uma vez é mais limpo do que mexer no matcher sobre fundação ainda não
decidida.

**DISCUSSÃO / RESTRIÇÕES TÉCNICAS (da F1B)**
- **`salary_engine` é puro** (lê `.espn_ref_value` de um objeto, sem DB) → o valor
  precisa continuar **materializado no Player** de qualquer forma; "resolver por
  `sleeper_id`" não elimina a coluna, no máximo a torna um cache/derivado.
- **Unificar exige chave nova `sleeper_id+season`** e **inverter o store** de
  transitório → canônico (persistente), reconciliando com `ESPNValue` (que já é o
  registro por-season com `is_final`).
- **`sleeper_id` tem buracos** (ex.: `import_csv` cria Player sem ele) → a chave de
  junção precisa ser **saneada/garantida** antes de virar canônica.
- **Ganho de segurança:** resolução por id + nome+team Brown-safe troca "corrupção"
  por "miss" (ambíguo → não chuta); ressalva: pode sub-resolver se o team da entrada
  estiver stale.

**DECISÕES JÁ TOMADAS**
- É **item de design próprio** (não o fix de segurança — esse é o mínimo de tela do
  E2-RISK).
- **Recebe o conserto do matcher** (resolução por `sleeper_id`) que saiu do escopo do
  E2-RISK.
- O `salary_engine` **permanece puro** — qualquer desenho preserva o valor materializado
  no Player.

**QUESTÕES EM ABERTO** (F1 deste item)
- Qual a chave/tabela canônica final e como reconciliar as três existentes sem perder
  `is_final`/histórico por season?
- Como sanear `sleeper_id` em Players legados/CSV antes de virar chave de junção?
- O store deixa de ser transitório (persistente) ou continua transitório alimentando um
  Player materializado?

**F1 — ACHADOS (diagnose de design, read-only; snapshot prod 07/06, 280 players)**

Os três receios da F1B foram **desmontados pelos dados**:
- **Não há três fontes vivas disputando.** Só `Player.espn_ref_value` é viva (250/280
  `>0`). **`ESPNValue` está VAZIA em prod** (0 linhas; único leitor = badge PROV do
  cap_projector, que com 0 linhas nunca acende). `RookieEspnValue` é transitória e
  **complementar** (cobre o vão pré-roster que as outras não cobrem — ambas exigem
  `player_id`). Sobreposição ativa: só Player↔ESPNValue (mesmo `adjusted`, escritos
  juntos por `_save_espn_value`), latente porque ESPNValue está vazia.
- **`sleeper_id` já cobre 99,3%** (278/280; **0 duplicatas**). Só **2 nulos**
  ("Hollywood Brown" = apelido de Marquise Brown; "Cameron Ward"), ambos não-rosterados
  e com `nfl_team` vazio. Saneamento é mínimo, **incremental, não pré-requisito atômico**
  (nulos degradam graciosamente = sem valor, como hoje).
- **Pureza do `salary_engine` preservada SEM tocar a engine:** a materialização do valor
  no Player **já existe** (`_save_espn_value` seta `player.espn_ref_value`); muda só a
  **fonte** (store canônico) e o **join** (por `sleeper_id`, não por fuzzy). A engine
  continua lendo `.espn_ref_value` do objeto, nunca faz lookup.

*Modelo-alvo:* chave canônica **`(sleeper_id, season)`**; base = **`RookieEspnValue`
generalizado** (persistente, com `is_final`) que **subsume `ESPNValue`**;
`Player.espn_ref_value` vira **cache materializado**; **`ESPNValue` aposentada** (vazia
→ sem migração de linhas).

*Achado estrutural decisivo:* o **conserto do matcher** (resolver entrada ESPN →
`sleeper_id`) é **independente** da reconciliação e entrega **quase todo o ganho de
segurança sem tocar schema**. A fundação de dados (store canônico) só precisa vir quando
a **leitura pré-roster (DP1)** for priorizada.

*Regressão roster→pool:* a falha vira **miss** (seguro e visível em not_found/review),
**não corrupção**; concentra-se nos 2 nulos e em `team` stale raro.

**FATIAMENTO (priorização da F1)**
- **[[E4-a]] — matcher por id** *(agora; sem schema, reversível, maior retorno/risco)*:
  resolve entrada ESPN → `sleeper_id` contra o pool global, Brown-safe (reusa
  `_load_players_db`/`_norm_name`/desambiguação nome+team); escreve via
  `find_player_by_sleeper_id`; `approximate`/review só para ambiguidade genuína. Entrega
  a eliminação do "Brown" **na raiz** + troca corrupção→miss. **Absorve/substitui o
  conserto do matcher que saíra do [[E2-RISK]].**
- **[[E4-b]] — saneamento de `sleeper_id`** *(em seguida; incremental, sem schema)*:
  backfill dos 2 nulos (com tratamento de apelido) + guard para Players novos.
- **[[E4-c]] — store canônico** *(atrelado a [[DP1]]; único passo com migração,
  data-light)*: generalizar `RookieEspnValue` → store persistente
  `(sleeper_id, season)[raw, adjusted, is_final]`; confirm + rollover escrevem nele;
  materializar `Player.espn_ref_value` a partir dele; badge PROV passa a ler o store;
  **aposentar `ESPNValue`**. Habilita leitura pré-roster (DP1).

**DEPENDÊNCIAS**
- Origem: **[[E2-RISK]]**-F1B. Guarda-chuva dos sub-itens **[[E4-a]]/[[E4-b]]/[[E4-c]]**.
  Relaciona-se com **[[E2]]** (store), **[[E3]]** (UI de import), **[[DP1]]** (E4-c
  habilita a leitura pré-roster). Não bloqueia itens abertos hoje.

---

### E4-a — Matcher do import ESPN resolve por `sleeper_id` (Brown-safe)
⚠️ **Implementado (F2) — validado em localhost; pendente smoke em prod com import real** — Prioridade **Alta** — fatia de **[[E4]]** (MAN-E4-F1/F2) — **absorve o conserto do matcher ex-[[E2-RISK]]; fecha a raiz que o F2 do E2-RISK só paliou**

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

### E4-c — Store canônico de valor ESPN por `(sleeper_id, season)`
🔲 **Pendente (guarda-chuva)** — fatia de **[[E4]]**; F1 de migração concluída (MAN-E4-c-F1) — **SUB-FATIADO em [[E4-c-1]] (aditivo/reversível — agora) / [[E4-c-2]] (destrutivo/isolado — higiene)**

**ESCOPO**
Generalizar `RookieEspnValue` → **store persistente** keyed `(sleeper_id, season)` com
`raw + adjusted + is_final` (deixa de ser transitório). Confirm do import + rollover
escrevem nele; **materializar** `Player.espn_ref_value` a partir dele (engine intocada —
lê do objeto); badge PROV (cap_projector) passa a ler o store; **aposentar `ESPNValue`**
(vazia em prod → sem migração de linhas).

**POR QUÊ / QUANDO**
Realiza a visão "valor ESPN como atributo único por `sleeper_id`" e **habilita leitura
pré-roster** ([[DP1]]). É o **único passo com migração** (atômico), mas **data-light**
pelo estado vazio do `ESPNValue`. Só compensa atrelado a um consumidor (DP1) — priorizar
junto.

**INVARIANTES A PRESERVAR**
- `salary_engine` puro (valor materializado no Player, nunca lookup na engine);
  idempotência; `is_final`/semântica provisório-final preservada no store; sem perda de
  histórico por season.

**F1 — ACHADOS (diagnose de migração, read-only; prod pós-E4b)**
- **Estado-alvo confirmado:** **tabela canônica NOVA** `(sleeper_id, season)[raw, adjusted,
  is_final]` via `db.create_all()` (aditivo, **sem ALTER**) — **mais reversível** que
  generalizar o `RookieEspnValue` in-place (que exigiria ALTER p/ `is_final`).
  `Player.espn_ref_value` vira **cache materializado**; `ESPNValue` aposentado;
  `RookieEspnValue` migrado/generalizado **por último**.
- **Backfill seguro:** **248 value-bearing, 100% com sid** (os 2 sem-sid eram os órfãos
  279/280, já deletados no E4-b); **0 sids duplicados** → chave `(sid, season)` segura. A
  coluna é populada **a partir de si mesma** → pós-backfill **coluna == store** (sem
  backfill store→coluna separado).
- **Refactor central (o grosso do E4-c):** os **8 escritores** de `espn_ref_value` passam a
  um **helper único** `set_espn_value` (store upsert **+** materializa a coluna),
  substituindo os `player.espn_ref_value = X` espalhados.
- **Leitores:** **só a badge PROV do cap_projector** é repontada (`ESPNValue`→store, join
  `player_id`→`sleeper_id`); **todos os demais leem a coluna materializada, inalterados**;
  a **engine nunca vira lookup** (pureza de graça).
- **Ordem (1-5), irreversível isolado:** (1) criar tabela, (2) backfill, (3) rotear
  escritores ao helper, (4) repontar badge — **todos reversíveis, sem downtime**; (5) DROP
  `ESPNValue` + generalizar `RookieEspnValue` — **irreversível-sem-backup, isolado no fim**.

**SUB-FATIAMENTO (E4-c vira guarda-chuva)**
- **[[E4-c-1]] — fundação (aditivo/reversível, agora):** passos 1-4. **Já entrega o store ao
  [[DP1]].** Backup antes do backfill; nada destrutivo; a coluna serve os leitores o tempo
  todo.
- **[[E4-c-2]] — limpeza (destrutivo/isolado, higiene):** passo 5. Sem leitor após o
  repontamento → pode esperar.

**DECISÕES DE ESCOPO (owner, pós-F1)**
1. **Season do backfill = 2026**, marcado **preliminar** (a tabela ESPN atual é prévia;
   serve 2026; o import definitivo futuro re-materializa).
2. **Linhas backfilladas:** `adjusted` autoritativo, `raw` **vazio** (não recuperável sem
   perda pelo floor), `is_final=False` (preliminares; o import definitivo completa).
3. **DST incluídas** no store como qualquer jogador (**não filtrar**) — seguem a mesma regra
   de cap/valor da liga. **F2 deve validar** que a chave do store funciona com o **sid de
   texto** das DST (`"IND"`,`"BUF"`…).
4. **Sequência:** **E4-c-1 agora** (constrói a fundação com o contexto fresco); **DP1 logo
   depois**, perto do draft; **E4-c-2 quando convier** (higiene).

**DEPENDÊNCIAS**
- Guarda-chuva de **[[E4-c-1]]/[[E4-c-2]]**. Fatia de **[[E4]]**. **[[E4-c-1]] habilita
  [[DP1]]**. Beneficia-se de **[[E4-b]]** (chave saneada — ✅).

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

### E4-c-2 — Store canônico: limpeza (drop ESPNValue + generalizar RookieEspnValue)
🔲 **Pendente** — Prioridade **Baixa (higiene; quando convier)** — fatia de **[[E4-c]]** (MAN-E4-c-F1) — **único passo destrutivo (irreversível-sem-backup)**

**ESCOPO** (passo 5 da ordem da F1)
- **Dropar `ESPNValue`** (vazio em prod → sem migração de linhas; após confirmar 0 leitores
  pós-repontamento da badge no E4-c-1).
- **Generalizar/retirar `RookieEspnValue`** — migrar suas linhas transitórias p/ o store
  canônico e aposentar a tabela.

**POR QUÊ ISOLADO**
- É o **único ponto irreversível-sem-backup**; sem leitor após o E4-c-1 → **higiene pura**,
  pode esperar. **Backup `/data/dynasty_*.db` antes.**

**DEPENDÊNCIAS**
- Fatia de **[[E4-c]]**. Depende de **[[E4-c-1]]** (badge já repontada). **Não bloqueia
  [[DP1]].**

---

### DP1 — Board de planejamento de cap pré-draft (rookies)
🔲 **Pendente** — Prioridade **a definir** — MAN-DP1-REG (08/06/2026) — **DESBLOQUEADO** ([[E4-c-1]] ✅ em prod 09/06/2026 — store canônico `(sleeper_id, season)` existe e backfillado; F1/F2 podem seguir)

**CONTEXTO**
Owners precisam planejar o rookie draft contra o cap: avaliar drops, valorização de contratos
e picks sabendo o valor de referência ESPN dos rookies e o salário que cada um custaria se
draftado. Hoje isso não existe — exige planilha manual; é o gap que o Manager quer preencher.

**DESCRIÇÃO**
Um board que lista os **rookies entrantes** com `espn_ref_value` e o **salário projetado**
(`floor(ESPN×1.2)`), e permite ao owner **simular** o impacto no cap de draftar um rookie numa
pick. **Projeção, não pré-contrato** — o cap real só muda no draft (a simulação não cria
contrato vivo).

**DOMÍNIO / LOCALIZAÇÃO**
Cap (não fantasy points) → mora no **Manager** (cap_projector), acessível a todos os owners —
**não** no Optimizer (estatística, acesso restrito).

**REUSO (sem réplica)**
`floor(ESPN×1.2)` é fonte única no `salary_engine` (`year1_salary`) — reusar, **não** replicar
em JS/template (mesmo princípio do T2-FIX-2 / F10).

**Exemplo de uso:** owner da pick 1.1 avalia Jeremiyah Love (ESPN $46 → projeção ~$55) contra
o próprio cap.

**DEPENDÊNCIAS**
- **Desbloqueado** — [[E4-c-1]] ✅ em prod (09/06/2026): o **store canônico** de valor ESPN
  por `(sleeper_id, season)` (leitura pré-roster) existe e está backfillado (273 linhas). O
  DP1 lê o canônico (`espn_store_adjusted`). **[[E4-c-2]]** (higiene) **não** bloqueia o DP1.
  F1/F2 do DP1 podem seguir.

---

## Offseason 2026 — pacote OFF26 (cuts selados + ligas fantasmas)
🔲 **Registrado 05/06/2026** — MAN-OFF26-REG (registro apenas; nenhuma implementação)

**Contexto do pacote (sessão com o comissário, 05/06/2026):** o formato da liga
(keeper + dynasty + salary cap) não cabe nativamente no Sleeper e a API do Sleeper
é **read-only** — não há como escrever salários/configuração via API. Decisão: o
Sleeper mantém o que faz bem (salas de lance ao vivo, via **ligas fantasmas** —
rookie draft em draft linear e FA Auction em draft auction), e o **Manager** assume
todo o ciclo de decisão e registro (declaração selada de keepers/cuts, keeper sheet,
auditoria da config da liga fantasma, import dos resultados dos drafts). A
transcrição da keeper sheet para o Sleeper é feita via **Cowork + Claude in Chrome**
(procedimento operacional supervisionado, fora do código do Manager).

**Dependências do pacote:** OFF26-1 → OFF26-2 → OFF26-4; OFF26-3 independente e
paralelizável; OFF26-5 é documentação (depende conceitualmente de 2 e 4).
**Prioridades abaixo são triagem inicial — o comissário re-prioriza.**
**Próximos candidatos naturais de F1 (sessões separadas):** OFF26-1 e OFF26-3.

---

### OFF26-1 — Janela de keepers/cuts selada
🔲 **Pendente** — Prioridade **Alta**

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

**Dependências:** nenhuma. É a **fonte** dos itens OFF26-2 e OFF26-4.

---

### OFF26-2 — Keeper sheet exportável
🔲 **Pendente** — Prioridade **Alta**

**Descrição:** relatório por time gerado a partir da revelação do OFF26-1 — keepers,
salários e budget resultante para o FA Auction.

**Motivação:** é o **insumo** que o Cowork transcreve para a liga fantasma; sem ele,
a transcrição não tem fonte de verdade.

**Escopo resumido:** exportar, por time, a lista de keepers + salário + budget de FA,
derivada da revelação selada.

**Dependências:** depende do **OFF26-1**.

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

### OFF26-4 — Auditoria de keepers pré-leilão
🔲 **Pendente** — Prioridade **Média**

**Descrição:** após a transcrição via Cowork, compara a keeper sheet (OFF26-2) com a
configuração **real** da liga fantasma lida via API read-only, reportando diffs
(keeper ausente, salário divergente, time errado) **antes** do início do leilão.

**Motivação:** a transcrição manual é o ponto de falha; a auditoria pega divergências
antes que o leilão comece sobre uma configuração errada.

**Escopo resumido:** ler config da liga fantasma via API read-only; diff contra a
keeper sheet; relatório de divergências como gate pré-leilão.

**Dependências:** depende de **OFF26-1** e **OFF26-2**.

---

### OFF26-5 — Runbook do procedimento Cowork
🔲 **Pendente** — Prioridade **Média** — **item de documentação (não é código)**

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

---

### F9 — `bulk_register` cria jogadores sem SalaryHistory
🔲 **Pendente** — Prioridade **Alta** — achado lateral de [[MAN-OFF26-3-F1]] (registrado 05/06/2026)

**Descrição:** o endpoint `POST /api/auction/bulk` (`routes/auction.py:187`
`bulk_register`) cria/atualiza `Player` + `AuctionLog` mas **não grava
`SalaryHistory`** — diferente dos demais caminhos de aquisição (`register_fa_auction`,
`register_rookie`, `upload_excel`), que sempre gravam o histórico. O código ainda
contém um hack inerte (`_noop` + `test_request_context`) sem efeito.

**Motivação:** jogadores registrados em massa ficam sem o registro de histórico
salarial correspondente — inconsistência silenciosa entre `Player.salary` e a
timeline de `SalaryHistory` (que alimenta `/salary_history` e auditorias). É **dano
potencial já existente**, não hipotético, daí prioridade Alta.

**Exige F1 próprio antes do fix** (avaliação de dano), respondendo:
- A rota `bulk_register` foi efetivamente usada em produção?
- Existem hoje jogadores sem `SalaryHistory` decorrentes dela (e quantos)?
- Qual o dano acumulado, se houver, e ele precisa de backfill corretivo?

**Escopo do fix (após o F1):** fazer `bulk_register` passar pelo mesmo caminho
atômico de aquisição dos demais (idealmente o helper canônico criado no F2 do
OFF26-3) + remover o hack `_noop`; eventual backfill dos órfãos conforme o F1.

**Ref. cruzada:** [[MAN-OFF26-3-F1]] (diagnose do importador OFF26-3, achado §3).

#### Fase 1 Diagnose ✅ (05/06/2026) — MAN-F9-F1 (avaliação de dano)
Read-only. Auditoria SQL direta do `dynasty.db` local (representante de produção;
sem subir o app, p/ não acionar `import_csv` no boot). **Achado que reformula o F9.**

**Estado do banco auditado:** `players`=280 (todos ativos), `player_history`=1132,
mas **`salary_history`=0 linhas** e **`auction_log`=0 linhas** (ambas VAZIAS).

- **§1 — Usado em produção? → NÃO há evidência.** `auction_log` está vazio → nenhum
  caminho do fluxo de auction (bulk_register OU os demais) deixou rastro neste DB.
  **Ressalva:** este é o *seed commitado*; o disco persistente do Render (não
  acessível daqui) é a fonte autoritativa de uso ao vivo. Se houver dúvida, **puxar
  o `dynasty.db` de produção** e re-rodar esta auditoria.
- **§2 — Órfãos:** atribuíveis ao bulk_register (fingerprint = `AuctionLog` sem
  `SalaryHistory` irmã por player+season) = **0** (auction_log vazio → lista nominal
  vazia). **Baseline:** 280 players ativos sem nenhuma `SalaryHistory` — mas isso é
  **condição global do DB** (tabela `salary_history` vazia), **não dano do
  bulk_register**: os 280 vêm de `import_csv.py:98` (import do CSV) + sync de roster
  (`sync_sleeper.py:262`), que setam `Player.salary` direto e **não escrevem
  salary_history** (por design — salary_history é camada de aquisição/auditoria).
  Lista completa reproduzível pela query de auditoria; origem = startup 2024 / draft
  2025 / FA, todos via CSV+sync.
- **§3 — Impacto a jusante: o rollover NÃO depende de salary_history.**
  `apply_season_rollover` (salary_engine.py:190-213) lê **`player.salary`** (prev) +
  **`player.espn_ref_value`** — não consulta `salary_history`. Logo os órfãos
  **rolam corretamente** (VALORIZAÇÃO usa Player.salary). **A premissa do prompt
  ("rollover calcula VALORIZAÇÃO a partir do histórico salarial") está refutada
  empiricamente.** Impacto real dos órfãos = **display/auditoria**: `/salary_history`
  mostra timeline vazia e a narrativa de contrato fica incompleta; cálculo de cap usa
  Player.salary (ok).
- **§4 — Réplicas (SIM):** criação de Player **sem** salary_history existe em mais
  de um lugar — `import_csv.py:98` (bulk do CSV) e `sync_sleeper.py:262` (sync de
  roster). Ambos **por design** (membership/seed; salary é Player.salary). O
  `bulk_register` (`routes/auction.py:141`) é o único que cria via **fluxo de
  aquisição** sem salary_history — inconsistente com os irmãos do `/auction`
  (que via `record_acquisition` gravam Player+SalaryHistory+AuctionLog). `admin
  espn_bulk` (admin.py:144) não cria player (atualiza ESPN). Fonte canônica de
  aquisição = `models.record_acquisition` (OFF26-3-F2).
- **§5 — Escopo recomendado do F2: REFATORAÇÃO APENAS** (no estado auditado).
  Como o dano atribuível = 0, F2 do F9 = rotear `bulk_register` pelo
  `record_acquisition` + remover o hack `_noop`/`test_request_context`. **Sem
  backfill** necessário aqui. **Condicional:** confirmar o `dynasty.db` de produção
  ao vivo; SE lá houver `auction_log` de bulk_register sem `SalaryHistory`, esses
  casos são **100% reconstruíveis** a partir do próprio `AuctionLog` (player_id +
  season + value_paid + espn_ref_value_at_time + entry_type → `year1_salary`
  recompõe a SalaryHistory). Nada se perde irrecuperavelmente, pois o bulk_register
  *grava* AuctionLog (só omite SalaryHistory).

**Observação fora do escopo do F9 (candidata a item próprio):** o seed `dynasty.db`
não tem **nenhuma** `salary_history` (0 linhas) — `/salary_history` ficaria vazio p/
todos. Pode ser esperado (seed reconstruído via CSV+chain, sem a camada de aquisição)
ou indicar que o backfill histórico de salary_history nunca foi semeado. Confirmar
contra o disco de prod; se prod também estiver vazio, avaliar um item de **backfill
de salary_history do roster** (separado do F9).

**Não iniciar F2.** Status do F9 permanece 🔲.

#### Fase 1B ✅ (07/06/2026) — MAN-F9-F1B (re-auditoria contra produção)
Cópia do `dynasty.db` de produção fornecida pelo comissário (`integrity_check: ok`).
**As conclusões condicionais da F1 viram definitivas:**

| Contagem | seed (git) | **produção** |
|---|---|---|
| players (total) | 280 | 280 |
| players ativos | 280 | **277** (3 dropados: Emari Demercado, Kareem Hunt, Nick Chubb) |
| player_history | 1132 | **1132** |
| salary_history | 0 | **0** |
| auction_log | 0 | **0** |

- **§1 — bulk_register usado em produção? → NÃO (definitivo).** `auction_log` de produção
  está **vazio** e **0 players ativos** têm qualquer AuctionLog. O fluxo `/auction`
  (bulk_register ou qualquer outro) **nunca foi usado em produção**. As sessões reais de
  FA auction de 2025 **existem**, mas em `PlayerHistory` (fa_auction=54, auction_draft=181,
  rookie_draft=34, trade=118, drop=258, rollover=220, …; 1132 eventos), reconstruídas pelo
  F8a a partir da chain do Sleeper — **não** via a tela do Manager. (A premissa do prompt
  "auction_log de produção deve refletir as FA auctions de 2025" está **refutada**: refletem-se
  em PlayerHistory, não em auction_log.)
- **§3 — Órfãos atribuíveis ao bulk_register: 0** (lista nominal: vazia). auction_log vazio
  → nenhum AuctionLog-sem-SalaryHistory possível.
- **§4 — salary_history em produção: VAZIA (0), confirmado — não era artefato do seed.** Mas
  é **inofensivo**: nada lê `salary_history`. O `/api/salary_history` (`routes/salary.py:122`)
  consome **PlayerHistory**; cap usa `Player.salary`; rollover usa `Player.salary`. A
  `salary_history` é **tabela legada superseded pelo PlayerHistory (F8a)**. **Nenhum backfill
  necessário.** (Se um dia se quisesse popular, PlayerHistory é a fonte — já tem season +
  salary + contract_year por evento.)
- **§5 — Veredito final do F9-F2: REFATORAÇÃO APENAS (sem condicional).** Dano = 0 em produção.
  F2 do F9 = rotear `bulk_register` por `record_acquisition` + remover o hack `_noop`. Sem
  backfill.

**Observações para planejamento (fora do escopo do F9 — candidatas a item próprio):**
1. **`salary_history` é tabela legada/morta** — superseded pelo PlayerHistory, escrita por
   `record_acquisition`/`/auction` mas lida por ninguém. Avaliar deprecar a escrita ou
   alinhar o helper canônico ao PlayerHistory (a tela de histórico lê PlayerHistory).
2. **Acquisitions feitas pelo Manager não aparecem no PlayerHistory** — `record_acquisition`
   grava SalaryHistory+AuctionLog, não PlayerHistory; em produção a história só se forma via
   sync/F8a (chain do Sleeper). Como o fluxo OFF26 (importador) e o `/auction` escrevem no
   Manager, vale avaliar se precisam emitir PlayerHistory para aparecer no `/salary_history`.
3. **Risco seed ≠ produção / sem backup automatizado** — confirmado (seed de abril ≠ disco
   vivo). A cópia recebida hoje serve de backup pontual; avaliar item de rotina de backup +
   refresh do seed.

---

### F10 — `draft_budget` replicado em JavaScript no cap projector
🔲 **Pendente** — Prioridade **Média** — achado lateral de [[MAN-OFF26-3-F1]] (registrado 05/06/2026)

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

### M10 — Busca de Jogador: Global + Calculadora
🔲 **Pendente — refinado 28/04/2026 (MAN-M10-REFINE)** — Prioridade **Média**

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

### O2 — Enriquecer Página do Jogador: Contexto NFL + Valor de Campo
🔲 **Pendente** — Prioridade **Média**

**Problema:** A página atual (`player_detail.html`, M13) mostra contrato, salary history e botão "Propor Trade". Faltam duas camadas de contexto: (a) **valor de campo** — pontuações históricas por temporada, posição no ranking/ADP, próximos jogos; e (b) **contexto NFL básico** — time NFL atual visível no header, e posição relativa do jogador entre os jogadores da mesma posição no time NFL (depth chart).

**Origem da observação:**
Caso real DJ Moore (WR) em 27/04/2026 — owner abriu a player page e percebeu ausência completa de contexto NFL: nem o time NFL aparecia no header (apesar de `Player.nfl_team` estar no banco), nem havia indicação de o jogador ser WR1/2/3 do Carolina. Decisão tomada na sessão de planejamento (27/04/2026, decisão A): refinar O2 in-place absorvendo as duas dimensões novas, em vez de abrir item separado (O3). Critérios para refinar e não fragmentar: mesma página alvo (`player_detail.html`), mesma fonte de dados (Sleeper), escopo natural de "enriquecer page do jogador" já existia no item — abrir O3 seria fragmentação artificial.

**Objetivo (5 dimensões, agrupadas):**

*Contexto NFL — dimensões novas, dependem só de campos já presentes no banco/cache:*
- **Time NFL no header:** exibir `Player.nfl_team` no cabeçalho da player page. Hoje o header mostra posição, nome do jogador e dono na liga, sem o time NFL. Trivial — apenas exibir.
- **Depth chart NFL embedded:** listar os jogadores da mesma `Player.position` e do mesmo `Player.nfl_team` ranqueados por `depth_chart_order` do Sleeper players cache (campo já consumido pela aplicação). Permite ao owner avaliar em segundos se o jogador é WR1/2/3 do time NFL sem sair da página.

*Valor de campo — dimensões originais do escopo:*
- **Stats históricas:** buscar da Sleeper API (`/stats/nfl/player/<sleeper_player_id>?season_type=regular&season=<year>`) — pontos totais e média por semana por temporada disponível.
- **ECR/ADP:** usar `adp` e `search_rank` já presentes no Sleeper players cache (`.sleeper_players_cache.json`) — zero request extra. Para ranking ESPN, usar ESPN ref value (`espn_ref_value`) já no banco como proxy de tier.
- **Schedule próximo (consolidado de UX4):** próximas semanas via Sleeper schedule (avaliar fonte exata — `/v1/state/nfl` + matchups por week, ou cache externo).

Apresentar de forma compacta, sem sobrecarregar a página. Referência: FantasyPros (abas Overview, Statistics, Schedule).

**Notas para F1:**
- Item UX4 da rodada de 23/04/2026 foi consolidado aqui em vez de duplicado — escopo virtualmente idêntico (mesma API Sleeper, mesma página alvo).
- F1 deve avaliar se as 5 dimensões cabem numa única camada de implementação ou se vale propor batches (ex: contexto NFL como batch 1 — só template + leitura de cache local; valor de campo como batch 2 — exige fetch Sleeper stats + schedule), considerando densidade da página e prioridade percebida pelo owner.

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

**Observação metodológica (para futuros F1 de refatoração de UI):** a dinâmica que gerou UX4-b sugere regra nova potencial no DEV_METHODOLOGY — F1 de refatoração de UI deveria listar explicitamente "campos presentes hoje que não estão no design proposto", com parecer por item (remoção intencional / perda não-intencional / deslocamento). Especificação positiva por si só omite silenciosamente. Item para próximo baseline do DEV_METHODOLOGY se priorizar.

---

### UX5 — Redesign da Seção Picks em Detalhe de Time
🔲 **Pendente** — Prioridade **Média**

**Problema:** A seção Picks em `/team/<id>` (introduzida em L1, 23/04/2026; intocada por UX1/UX4) renderiza **3 tabelas anuais idênticas** (2026, 2027, 2028) com headers repetidos a cada ano (Round / Origem / Notas). A coluna Origem mostra apenas emojis decorativos + nome do time de origem, a coluna **Notas aparece vazia em todas as ocorrências observadas**, e o layout ocupa espaço vertical significativo com baixa densidade informacional. Tipicamente 3 linhas por ano (Rd1, Rd2, Rd3), 3 anos → 9 linhas úteis espalhadas em 3 tabelas com 3 headers repetidos.

**Referências:** observação visual pós-UX4 (commit `a10fcb6`, 24/04/2026).

**Escopo candidato (a fechar na F1 de UX5):**

Várias direções possíveis, não mutuamente exclusivas:

- **(a) Reestruturação de colunas** — avaliar se Origem e Notas devem continuar como colunas separadas, ou consolidar (ex: "Rd1 via 2024 trade com X"), ou remover campos sem uso (Notas) e adicionar campos com utilidade real (dynasty value da pick, projected_pick, pick number absoluto).
- **(b) Consolidação visual das 3 tabelas** — 1 tabela única com coluna Season + agrupamento, ou grid compacto de cards por round, ou timeline horizontal por ano. Elimina header repetido.
- **(c) Avaliação do modelo de dados por trás** — a coluna Notas está vazia porque o campo nunca é populado na prática? Se sim, vira débito estrutural (remover da UI + avaliar no model). Se populado em casos específicos, documentar e usar.
- **(d) Mudança de paradigma** — tabela → cards ou grid estilo "pick chip" (reusar `.pick-chip` existente do Trade Manager), com seleção visual densa e clickability pra propor trade.

F1 de UX5 mapeia estado atual (frequência de uso de Notas, payload do handler, infra reusável) e decide escopo concreto.

**Infra relacionada reusável:**
- `dynasty_value` por pick já canonizada em **T2-FIX-2** (`/api/picks` pré-resolve via backend). Se UX5 exibir valor dynasty inline, caminho já limpo.
- Classe `.pick-chip` existente (usada em Trade Manager e em M9 grid de picks).
- Helper `pick_sleeper_id` + `resolve_asset_value` canônicos em `dynasty_values.py`.

**Relação com outros items:**
- **Independente de UX2** (PT-BR em outras telas) e **UX4-b** (restauração ESPN+Projeção em roster).
- **Pode impactar contrato do endpoint/handler** (`/team/<id>` em `routes/league.py`) se a F1 decidir adicionar `dynasty_value` ou outros campos derivados ao payload de picks.
- **Sem conflito com UX4** — UX4 redesenhou a seção Roster em `/team/<id>`; UX5 toca seção diferente (Picks) da mesma página.

**Pré-requisito:** nenhum bloqueante.

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

### UX6 — Revisão da Largura Máxima do Container Global da Aplicação
🔲 **Pendente** — Prioridade **Média**

**Problema (sintoma observado):** Análise visual das páginas do Fantasy Manager (24/04/2026, pós-UX4-b) identificou que o conteúdo principal (roster, cap breakdown, picks, trades, etc.) fica espremido no centro da viewport com **margens laterais significativas** — em monitor de ~1920px de largura, ~700px ficam como ar lateral (~350px em cada lado). Referências externas modernas (FantasyPros, apps de produtividade) aproveitam largura maior da viewport em monitores wide.

**Referências:** commits UX4 (`a10fcb6`), UX4-b (`e495453`).

**Escopo (a fechar na F1 de UX6 como investigação aberta):**

- **F1 — diagnose da causa real** (sem presumir): mapear qual conjunto de propriedades CSS do wrapper/container global (incluindo, mas não limitado a, `max-width`, `padding`, estrutura de grid, flexbox, ou wrappers aninhados) produz o comportamento observado. Identificar o(s) seletor(es) envolvidos em `base.html`, `static/style.css`, ou outros. Medir valores atuais. Não assumir qual é a causa antes de inspecionar.

- **F1 — mapeamento cross-tela:** percorrer as 12+ telas (roster, detalhe de time, trades, cap_projector, admin, league hub, picks, auction, offseason, player detail, salary history, salary) e avaliar por tela:
  - Qual largura útil atual ocupa e qual faria sentido
  - Se há componentes com largura fixa (ex: modais, cards centralizados) que poderiam quebrar com mais espaço horizontal
  - Se tabelas densas (cap_projector com 10 colunas, admin review) ganhariam com mais largura

- **F1 — opções com trade-offs:** após identificar a(s) causa(s) real(is), propor caminhos de correção com prós e contras. Não pré-selecionar solução — owner decide entre opções mapeadas.

**Impacto cross-tela:** afeta **todas as páginas do app**. Risco de regressão em layouts específicos que implicitamente assumem a largura atual. F1 precisa mapear amplamente.

**Relação com outros items:**
- **Independente de UX4-c** (densidade localizada em `/team/<id>` e `/`), **UX5** (Picks), **UX2** (PT-BR).
- **Pode reduzir ou eliminar** necessidade de alguns aperfeiçoamentos localizados se liberar largura horizontal suficiente — ex: pressão no colgroup (UX4-c frente 3) pode diminuir se a tabela ganhar mais espaço horizontal.
- **Ordem decidida pelo owner:** UX4-c primeiro, UX6 depois.

**Riscos:**
- Componentes com largura fixa (cards, modais, filtros centrados) podem ficar visualmente desbalanceados com container mais largo — precisa mapear na F1.
- Tabelas longas (cap_projector) podem ganhar com mais espaço mas também podem virar "parede de dados" difícil de scanear — validação visual empírica pós-implementação.
- Telas com poucas colunas (admin users, offseason standings) podem parecer vazias/ilhadas em container muito largo. Padding interno ou constraint de tabela específica resolve.

**Pré-requisito:** nenhum bloqueante.

**Observação estratégica:** este é um dos poucos items do backlog com **escopo cross-app verdadeiro**. Enquanto UX1-UX5 tocaram telas específicas, UX6 muda o framing visual de tudo. Por isso F1 merece cuidado extra — investigação aberta da causa antes de propor soluções, mapeamento amplo antes de qualquer F2, e possivelmente prototipagem em 1 tela específica antes de roll-out.

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
