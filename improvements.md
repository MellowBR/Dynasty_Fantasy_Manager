# improvements.md — Fantasy Manager

> Backlog vivo de melhorias, bugs e features pendentes.
> Atualizado em: 22/04/2026
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
| T1 | Redesign Trade Manager: simulador multi-owner + link compartilhável | Alta | 🔲 |
| T2 | Integrar valores KTC no preview de trade | Média | 🔲 |
| Q1 | Script de simulação de temporada (validar salary rollover) | Média | 🔲 |
| M1 | Validação de cap antes de confirmar trade | Média | 🔲 |
| M2 | Tela de aprovação em lote de jogadores `needs_review=True` | Média | 🔲 |
| M3 | Exportar dynasty.db em formato legível para os outros owners | Baixa | 🔲 |
| M4 | Banner de sync desatualizada com timestamp e botão "Sincronizar agora" | Baixa | 🔲 |
| M8 | Auditoria pública do sorteio de lottery (seed + página pública) | Baixa | 🔲 |
| M9 | Redesign da tela de picks: grid compacto + dono atual visível | Média | 🔲 |
| M10 | Autocomplete de jogador na calculadora de salário | Baixa | 🔲 |
| M11 | Teste de auto-containment documental | Média | ✅ 22/04/2026 |
| M12 | Vincular owners a times via tela de admin com lookup do Sleeper | Média | ✅ 22/04/2026 |
| F6 | Remover "keeper" como acquisition_type (migrar → auction_draft) | Média | 🔲 |
| M5 | Ordenação por posição em todas as telas de roster | Baixa | ✅ 02/04/2026 |
| M6 | Importar resultados de temporada para atualizar ESPN ref values automaticamente | Baixa | 🔲 |
| M7 | Trade Manager: layout mais compacto e janela maior | Baixa | ✅ 02/04/2026 |
| F4 | Fix OAuth callback local (ProxyFix, host, APP_ENV, secret) | Alta | ✅ 02/04/2026 |
| F5 | Auto-seed users no startup a partir de `data/users.csv` | Média | ✅ 02/04/2026 |
| F1 | Correção de salários por partial name match (3 Browns bug) | Alta | ✅ 28/03/2026 |
| F2 | Ordenação do Round 1 via `draft_lottery_result` + `season_standings` | Alta | ✅ 28/03/2026 |
| F3 | Histórico inline (accordion) na aba de histórico | Média | ✅ 28/03/2026 |

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
🔲 **Pendente** — Prioridade **Alta**

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

### T2 — Integrar Valores KTC no Preview de Trade
🔲 **Pendente** — Prioridade **Média**

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

### M8 — Auditoria Pública do Sorteio de Lottery
🔲 **Pendente** — Prioridade **Baixa**

**Problema:** O sorteio de lottery (`routes/offseason.py:258-357`) usa `random.uniform()` sem seed fixo. O resultado é salvo na tabela `draft_lottery_result` (season, pick_number, team_name, source, locked) mas sem registro do seed usado, dos pesos aplicados, nem do histórico de sorteios anteriores que foram descartados. Qualquer owner pode questionar se o sorteio foi justo — não há prova auditável.

**Proposta:**
1. **Salvar seed e pesos:** Ao rodar o lottery, gerar um `random_seed` (ex: hash de timestamp), setar `random.seed(seed)`, e salvar na tabela `draft_lottery_result` ou nova tabela `lottery_audit` (seed, pesos usados, timestamp, resultado completo)
2. **Página pública:** Rota `/picks/lottery/<season>` acessível sem login (ou com `@login_required`) mostrando: seed usado, pesos por posição, resultado detalhado pick a pick, possibilidade de verificar reproduzindo o sorteio com o mesmo seed
3. **Modelo `DraftLotteryResult`:** Hoje não tem campo para seed — adicionar coluna `random_seed` ou criar tabela auxiliar

---

### M9 — Redesign da Tela de Picks: Grid Compacto
🔲 **Pendente** — Prioridade **Média**

**Problema:** A tela de picks (`/picks`, `routes/picks.py`) exibe picks em listas por season/round, mas não deixa claro visualmente quem é o **dono atual** de cada pick quando ela foi trocada. O modelo `Pick` tem `original_team_name` e `current_team_name` (`sync_sleeper.py:358-395`), mas o template pode não distinguir bem picks próprias de picks recebidas via trade.

**Proposta:**
1. **Layout em grid:** Matrix `12 times × 3 rounds` por season, cada célula mostra o pick com: dono original + dono atual (se diferente, destacar visualmente)
2. **Picks trocadas sem duplicação:** Hoje a mesma pick pode aparecer sob o time original e sob o time atual. No grid, cada pick aparece uma vez na posição do dono original, com indicação visual de quem detém atualmente
3. **Compacto:** Badges coloridos por time, tooltip com detalhes, sem cards grandes
4. **Código existente:** `_build_pick_projections()` (linha 82-137) já resolve posição projetada de cada pick. `Pick.traded_away` e `Pick.current_team_name` já existem no modelo

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

### F6 — Remover "keeper" como acquisition_type
🔲 **Pendente** — Prioridade **Média**

**Problema:** "keeper" é uma **decisão de manutenção** (o owner decide manter o jogador), não uma **origem de aquisição**. Um jogador adquirido via auction_draft que é mantido como keeper continua sendo auction_draft — o fato de ter sido kept não muda como o salário é calculado.

**Verificação no código:**
- `salary_engine.py:41` — `_AUCTION_TYPES = {"auction_draft", "keeper"}` → keeper é tratado **identicamente** a auction_draft em todas as regras de salário (year1, valorization, renewal). Não há lógica condicional que distinga os dois.
- `import_csv.py:33` — `_norm_acq()` mapeia `"keeper" → "keeper"`, mantendo o tipo no import
- Banco atual: **101 jogadores** com `acquisition_type="keeper"` (verificado)

**Proposta:**
1. **Migração:** `UPDATE players SET acquisition_type='auction_draft' WHERE acquisition_type='keeper'`
2. **Atualizar SalaryHistory:** mesma migração para registros históricos
3. **Remover de `_AUCTION_TYPES`:** `{"auction_draft"}` apenas
4. **Remover de `_norm_acq()`:** tirar `"keeper": "keeper"` do mapeamento
5. **Remover de formulários de edição:** se houver dropdown/select com "keeper" como opção
6. **Atualizar CSV:** `dynasty_rosters_clean.csv` — substituir "keeper" por "auction_draft"

**Risco baixo:** Como `salary_engine.py` já trata keeper = auction_draft, a migração não altera nenhum cálculo de salário.

---

## Itens Concluídos

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

### F3 — Histórico Inline (Accordion) na Aba de Histórico ✅ 28/03/2026

**Problema:** Histórico de transações de um jogador só estava disponível via modal na aba de roster, não na aba de histórico (`/salary_history`).

**Solução:** Adicionado accordion expansível por jogador na aba de histórico, consistente com o comportamento do modal no roster.

---

### M5 — Ordenação por Posição em Todas as Telas de Roster ✅ 02/04/2026

**Problema:** Jogadores apareciam em ordem aleatória nos endpoints de API (roster by id, roster by name, cap projector). A página HTML de roster já ordenava via `_build_players_by_pos()`, mas as APIs JSON não.

**Solução:** `POS_ORDER` movido de `routes/roster.py` para `models.py` como constante central. Criada função `sort_players_by_pos(players)` em `models.py` que ordena por posição (QB→DEF) e salary DESC. Aplicada em `routes/roster.py` (2 endpoints API) e `routes/salary.py` (cap projector).
