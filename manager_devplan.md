# devplan.md — Fantasy Manager

> Plano vivo + Log de Decisões  
> Última atualização: 22/04/2026  
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
