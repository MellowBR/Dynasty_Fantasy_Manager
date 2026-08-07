# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Dynasty SB is a Flask web app for managing a 12-team dynasty fantasy football league (Sleeper platform). It handles salary cap, contracts, trades, draft picks, and offseason workflows. The primary artifact is `dynasty.db`, consumed by the companion `fantasy_optimizer` and `predictor` projects. All projects live under `C:\Users\Erico Mello\Fantasy\`.

**League:** Dynasty SB | **My team:** Cangaceiros da Colina (MellowBR) | **Sleeper League ID:** 1316547584378048512

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run app (port 5000) — 1º boot semeia salary/contract de data/dynasty_rosters_clean.csv
# (bootstrap one-shot, F12: boots seguintes preservam edições in-app; flag csv_bootstrap_done)
python app.py

# Run salary engine unit tests
python salary_engine_test.py

# Run keeper audit unit tests (OFF26-4 — núcleo puro, sem Flask/DB/rede)
python keeper_audit_test.py

# Run cap régua tests (OFF26-16 — folha única com IR; núcleo puro + ORM em memória)
python cap_regua_test.py

# Seed users (after first deploy)
python seed_users.py --csv data/users.csv
python seed_users.py --email user@gmail.com --name "Name" --team-id 1 --admin
python seed_users.py --list
```

**Note on `seed_users.py` dual-seed behavior:** running the CLI imports `app.py`, which runs the full boot sequence (including auto-seed from `data/users.csv`) before the CLI flags are processed. If the target user is already in `users.csv`, the subsequent `--email` call fails with "já existe" (exit code 1) — expected. For production, edit `data/users.csv` + commit; next deploy auto-seeds on startup. The CLI is dev convenience for the local DB only.

## Architecture

### Core Principle: Salary Logic is Pure

`salary_engine.py` contains all salary/contract calculation logic with **zero DB dependencies** — pure functions only. This is the testable core. All ESPN values passed to the engine are **already adjusted** (raw × 1.2), as stored in `Player.espn_ref_value`. UI forms send raw values and multiply by 1.2 before passing to the engine.

### Data Authority Split

- **Sleeper API** is authoritative for: roster membership, player names/positions/NFL team, IR slots, traded picks
  - **IR é read-only no Manager** (IR-CLEANUP): `Player.is_on_ir` só é escrito pelo sync, a partir do array `reserve` de cada roster. Não existe toggle na UI — mudar IR se faz **no Sleeper**, e reflete aqui no sync seguinte
- **Local DB (`dynasty.db`)** is authoritative for: salaries, contract years, acquisition types, ESPN ref values
- **Sleeper sync never overwrites salary/contract data**

### App Startup Sequence (app.py)

Ordem real do boot (verificada contra o código — cada passo cita a âncora em `app.py`):

1. `load_dotenv()` → load `.env` (module top, line 4 — antes de `create_app()` rodar)
2. `create_app()` (linha 13) → Flask init; URI do SQLite vem da env **`DYNASTY_DB`** (fallback `BASE_DIR/dynasty.db`); `SECRET_KEY`; **ProxyFix só em produção** (`APP_ENV=production`); `db.init_app`
3. Registra o filtro Jinja **`utc_iso`** (M18 — fonte única do "marcar UTC" nos templates; linhas 30-31)
4. Dentro de `with app.app_context()` (linha 33), em ordem:
   1. `db.create_all()` → cria tabelas faltantes (linha 34)
   2. `_run_migrations()` → ALTER/CREATE para schema existente (incl. tabela `users`; 8 migrações idempotentes — linha 35)
   3. `_seed_app_config()` → semeia AppConfig default (linha 36)
   4. **Auto-seed users** → lê `data/users.csv` se existir, insere emails novos (pula existentes — linhas 37-57)
   5. `fresh_import = run_import()` → upsert de salary/contract de `data/dynasty_rosters_clean.csv`; **retorna flag** (linha 60). Em prod o CSV não está no git → skip com WARNING (`fresh_import` falsy)
   6. **CONDICIONAL — só `if fresh_import`** (linhas 61-82, tipicamente só no 1º boot/seed):
      - `run_sync()` → Sleeper API sync, atribui times (envolto em try/except — app sobe mesmo se a Sleeper cair)
      - `_backfill_player_history()` → **legacy**, e **só `if not f8_rebuilt`** (AppConfig); o F8 (rebuild canônico via chain do Sleeper) substituiu esse fluxo, então em DBs já migrados é pulado
5. Define 4 **context processors** (estado global de offseason, times da navbar, time do usuário logado `inject_user_team`/M17, badge de review — linhas 84-134)
6. `init_auth(app)` + registra `auth_bp` → Flask-Login + Google OAuth (linhas 137-139) — **perto do fim, depois dos context processors, não antes do sync**
7. Registra os **9 blueprints** (roster, salary, trades, picks, auction, admin, offseason, league, draft_import — linhas 142-160)
8. Error handlers 404/500 (linhas 163-173)
9. No nível do módulo: `app = create_app()` (linha 424); `app.run(host='localhost')` só sob `__main__` (dev)

**Nota de propagação (DOC1):** `run_sync` e `_backfill_player_history` **não** rodam em todo boot — só quando `run_import` semeia dados frescos. Não assumir "o sync roda no startup" ao diagnosticar dados stale em prod (onde o CSV ausente já zera o `fresh_import`).

### Route Blueprints (11)

| Blueprint | URL | Purpose |
|-----------|-----|---------|
| auth | `/login`, `/logout`, `/auth/callback` | Google OAuth authentication |
| roster | `/`, `/player/<id>` | Team rosters, cap bar, página dedicada por jogador (M13), banner de cap estourado em offseason (M1), banner informativo de IR (OFF26-16 — leitura, não controle). **IR-CLEANUP: não há toggle de IR** — o Sleeper é autoridade sobre `is_on_ir` e o sync sobrescreve |
| salary | `/salary`, `/salary_history`, `/cap_projector` | Salary calculator, cap projector, salary history com timeline clicável. **DP1/DP2/DP3:** board de planejamento de rookie draft no cap_projector — lista a **classe entrante capturada** (`RookieEspnValue.in_class=True`, snapshot da captura admin DP3, menos já-rosterados; valorados ESPN no topo, massa a $1 atrás de busca/filtro) via `/api/cap_projector/rookies`; cenário keep/corte + rookies num único POST ao `/budget` canônico (DP2 — o antigo `/simulate` foi removido), projeção pura sem escrever contrato |
| trades | `/trades`, `/trades/proposta/<uuid>` | Trade simulador puro (T1), preview com dynasty + redraft delta-pointing bars (T2/T3), descrição "de/para" 2-colunas, query params pré-seleção (M14), propostas compartilháveis |
| picks | `/picks`, `/picks/lottery/<season>` | Grid navegável de picks (M9), auditoria pública do lottery (M8), legenda de odds audit-first — pesos do audit canônico, senão config (M15/M15-FIX), projeção do draft: R1 = lottery, R2/R3 = standings invertido (M16) |
| auction | `/auction` | FA auction & rookie draft registration |
| admin | `/admin`, `/admin/users`, `/admin/review`, `/admin/keeper_audit` | Sleeper sync, ESPN import, season rollover, user↔team management (M12), trade backfill (S1), PlayerHistory canonical rebuild (F8), dynasty values refresh (T2), revisão admin auditável Cat A/B (M2), **auditoria de keepers pré-leilão (OFF26-4 — read-only, ver `keeper_audit.py`)** |
| offseason | `/offseason` | 7-step offseason workflow com lottery auditável (M8), 6 seeds via fonte única (M15), editor de pesos reativo com render single-source JS (M15-FIX) |
| draft_import | `/draft_import` | OFF26-3: importa drafts via API read-only — **rookie linear (roda na liga REAL)** / **FA auction (roda na liga fantasma permanente)**; preview→confirm, match por sleeper_player_id, idempotente, escreve só via `record_acquisition`. ⚠️ OFF26-11 🔲: com keepers designados no board da fantasma os picks vêm misturados, e a porta é de **contrato ano 1** — ingerir keeper zera a idade do contrato |
| cuts | `/cuts`, `/cuts/keeper_sheet` | OFF26-1: mecanismo da janela selada — lock/revelação simultânea admin-manual com snapshot auditável molde M8 (`CutWindowAudit`), hash verificável, write-by-team do admin com **hierarquia owner > admin** (recusa seca 409), gate de abertura = `needs_review` zerado (D3). **⚠️ A PORTA DE DECLARAÇÃO DO OWNER FOI APOSENTADA (MAN-OFF26-1-ETAPA2, 07/08/2026):** os cortes de 20/08 acontecem **direto no Sleeper** e o Manager só fotografa por sync; a tela não renderiza mais roster/checkbox/botão de declarar — sobra a explicação do fluxo e, para admin, o **motor rotulado "legado"**. As **rotas** de declaração seguem vivas de propósito (são o mecanismo que a urna do OFF26-10 reusa e a rede de regressão da hierarquia). ⛔ **A urna não pode reusar a flag `cuts_window_open`** — reabriria a porta antiga. OFF26-2: keeper sheet consolidada (leitora, keepers = roster − cortes; tabela + CSV) — **hoje exige snapshot canônico; no desenho novo passa a nascer do sync** (U7 do OFF26-10, escopo da F2 da urna) |
| league | `/league`, `/team/<id>` | League Hub (L1): grid de 12 times com cap/picks/dynasty/record + detalhe por time (roster, picks, cap breakdown) |

### Models (models.py)

21 SQLAlchemy models. Key ones: **User** (email, team_id, is_admin), Team, Player, SalaryHistory, Pick, AuctionLog, Trade, ESPNValue, AppConfig (key-value global state), SeasonStandings, DraftLotteryResult, PlayerHistory, **TradeProposal** (T1 — UUID + assets JSON + TTL 7d), **LotteryAudit** (M8 — seed + weights_json + pool_json + result_hash + is_canonical + previous_audit_id), **F8PlayerBackup** (rollback do F8a), **RookieEspnValue** (E2/DP3 — valor ESPN de entrante não-Player + `in_class` = membership da classe entrante, ver seção própria), **EspnValueStore** (E4-c — store canônico de valor ESPN por `(sleeper_id, season)`), **CutDeclaration** (OFF26-1 — declaração privada/editável de cortes por `(season, team_id)`, `cut_ids_json`; keepers = complemento), **CutWindowAudit** (OFF26-1 — snapshot canônico molde M8: `declarations_json` + `is_canonical` + `previous_audit_id` + `reason` + `result_hash`).

### Salary Cap Rules

- **Cap:** $200 | **Roster max:** 22 | **Min salary:** $1 | **Contract:** 4 years
- **Year 1:** auction_draft = bid amount; rookie_draft = floor(ESPN×1.2); waiver/FA = $1 (F6: "keeper" foi removido do vocabulário canônico)
- **Year 2+ (VALORIZAÇÃO):** MAX(prev_salary, floor(0.5 × ESPN_adjusted)), min $1
- **Waiver/FA Year 2 exception:** floor(0.80 × ESPN_adjusted), min $1
- **Renewal (after Year 4):** new 4-year contract, Year 1 = floor(ESPN_adjusted), min $1
- **Draft budget:** $200 − Σ(keeper salaries), minimum $1 per empty slot

#### Régua única de folha — o IR conta no cap, sempre (OFF26-16)

**Decisão do owner (04/08/2026), explícita e final: jogador no IR conta no cap hit como qualquer
outro.** Existe **UMA** folha salarial — todos os jogadores do elenco, ativos e IR — e ela é a mesma
em toda tela, todo cálculo e todo contexto.

- **Fonte única:** `salary_engine.roster_salary(players)` — soma tudo, filtra só `is_dropped`.
  Pura, sem DB, testável (`cap_regua_test.py`).
- **Entrada ORM:** `Team.total_salary()` (delega ao helper) e `Team.cap_remaining()`.
  `to_dict()` expõe `salary_total`.
- É a mesma regra que `salary_engine.draft_budget` sempre aplicou — e que a keeper sheet (OFF26-2)
  e a auditoria (OFF26-4) já consumiam. **Agora as telas usam a mesma.**

⛔ **Não recriar uma soma que filtre `is_on_ir` para fins de folha.** Havia **seis** definições da
régua sem IR (`Team.active_salary()` + 5 somas inline em `roster.py`, `league.py` ×2, `admin.py` ×2)
e a F2 do OFF26-14 chegou a **rotulá-las na tela** ("cap ativo" × "folha total") antes da decisão do
owner tornar o número sem IR **sem significado**. `cap_regua_test.TestSemReplicaDeFolha` falha se a
réplica voltar ou se `active_salary` ressuscitar.

`is_on_ir` segue existindo para **composição de elenco** (contagem, lista de quem está no IR,
`MAX_IR = 2` no `toggle_ir`) — nunca para folha. O regulamento é explícito sobre **contagem** (item
1.3 — os 2 IR não entram no total de 22) e **silencioso sobre salário de IR no cap**; quem decidiu
foi o owner.

### Offseason Workflow (7 steps)

1. Close Season → import standings from Sleeper or manual entry
2. Lock Draft Order → weighted lottery for picks 1-6 (7th-12th place; M15: 7º com 1 bolinha, pool 96, fonte única `DEFAULT_LOTTERY_WEIGHTS`), fixed 7-12. O sorteio define só o R1; R2/R3 seguem standings invertido (M16)
3. Update ESPN Values → bulk PDF import + player matching. **Inclui a captura da classe entrante
   (DP3):** botão na tela do import ESPN → `POST /api/admin/capture_rookie_class` materializa a
   membership da classe (`RookieEspnValue.in_class`) que o board do cap_projector lê;
   re-executável/idempotente. A contagem varia com o calendário NFL (~288 com rosters de 90 em
   julho; ~150 pós-corte de agosto) — comportamento esperado; recapturar após o corte se o board
   seguir em uso
4. Season Rollover → apply salary rules, increment contract years
5-7. Informational: rookie draft, keepers/cuts, FA auction (manual via /auction)

### Authentication & Permissions

- **Google OAuth** via `authlib` + `flask-login` (blueprint `routes/auth.py`)
- **User model**: email → team_id + is_admin. Auto-seeded from `data/users.csv` on startup (skip existing). Also available via CLI: `seed_users.py`
- **`@login_required`**: all routes except `/login`, `/logout`, `/auth/callback`
- **`@admin_required`**: POST/PATCH/DELETE that alter calculated data or are irreversible
- **Exception**: `POST /api/admin/sync` uses `@login_required` only (reflexive, never overwrites salary/contract data)
- **Unauthorized handler**: `/api/*` routes return 401/403 JSON; page routes redirect to `/login`
- **WSGI**: `wsgi.py` as entry point for PythonAnywhere; `ProxyFix` for reverse proxy headers (production only)
- **Local dev**: `app.run(host='localhost')` — matches Google OAuth redirect URI `http://localhost:5000/auth/callback`
- **Environment**: `.env` with `SECRET_KEY`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `APP_ENV`

### External Integrations

- **Sleeper API** (`sync_sleeper.py`): rosters, team info, winners bracket, previous league, **trades via `/transactions/{leg}`** (S1 — `_sync_trades(league_id)`, idempotente via `sleeper_transaction_id`, trata N-way como placeholder row). Player DB cached ~semanal (~15MB `.sleeper_players_cache.json`). **F13:** o cache vive em `dirname(DYNASTY_DB)` (volume persistente `/data` no Render — padrão E1), **fora do git** (gitignore + untracked); validade por carimbo `fetched_at` **dentro** do arquivo (não mtime do FS — imune ao mtime renovado por deploy). Formato antigo/sem carimbo/vencido → re-baixa. Startup sync wrapped in try/except for graceful degradation.
- **ESPN PDF** (`espn_pdf_parser.py`): parse draft value sheets, match to DB players with 3-tier matching (exact → case-insensitive → normalized). Import (E1): **upload manual do PDF** (preferido) ou download por URL com **degradação graciosa** (guarda magic-bytes `%PDF` + try/except → flash, nunca 500; a ESPN bloqueia o download do IP do Render). Estado de review gravado em `dirname(DYNASTY_DB)` (FS gravável), não na raiz do app
- **Google OAuth**: OpenID Connect via Google's well-known endpoint

### Player Name Matching (player_lookup.py)

Strict full-name matching to prevent the "3 Browns" bug. Never falls back to partial/substring matching. Three tiers: exact → case-insensitive → normalized (strips accents, suffixes, punctuation).

### Rookie ESPN value store (E2)

`RookieEspnValue` (models.py) é a **camada de dados** dos valores ESPN de rookies/entrantes
que ainda **não existem como Player** (caem em not_found/approximate no import ESPN, pois
entram só no rookie draft). Keyed por `sleeper_player_id` (resolvido contra o **pool global do
Sleeper** por nome+team, Brown-safe). **DP3 (31/07/2026):** a tabela também carrega a
**membership da classe entrante** (`in_class`), escrita SÓ pela captura admin
(`capture_rookie_class`, critério único `is_entering_class_member`: `years_exp==0` + skill +
`active`+`status='Active'`); `upsert_rookie_espn` é porta única com dois donos por campo
(import ESPN = valores; captura = membership; `None` = não tocar). Populado no confirm do
import ESPN (valores) + captura (membership); consumido pelo importador de draft (OFF26-3) —
que aplica `floor(ESPN×1.2)` via `year1_salary` ao criar o rookie — e pelo **board DP1/DP3**
(cap_projector: lê `in_class=True` menos rosterados; sem valor ESPN → $1 via `year1_salary`).
Transitório: `clear_rookie_espn_store()` no fim do rookie draft (esvazia o board — gate
preservado). Helpers: `upsert_rookie_espn` / `rookie_espn_adjusted` / `clear_rookie_espn_store`
/ `is_entering_class_member`.

### Acquisition (criação de contrato ano-1)

`models.record_acquisition(...)` é a **única porta canônica** de criação de contrato
de aquisição (Player upsert + SalaryHistory + AuctionLog atômicos; salário sempre via
`salary_engine.year1_salary`). Usado pelas **4 portas** do `/auction` (FA/rookie/bulk/excel)
e pelo importador OFF26-3. Idempotência por token `[ref:<event_ref>]` em `AuctionLog.notes`
via `acquisition_already_recorded()`. **Nenhuma porta escreve contrato inline** (F9, 16/06/2026:
`bulk_register` roteado pelo helper — última réplica inline fechada; ⚠️ aguardando smoke prod).
Não criar contrato fora desse helper.

### Keeper audit — gate de integridade do leilão (OFF26-4)

`keeper_audit.py` compara a **keeper sheet** (OFF26-2) com o **board da liga fantasma** lido ao
vivo pela API read-only, e devolve o relatório dos **12 times de uma vez**. **Não é conferência
de cap:** um keeper que não esteja designado no board é, para o Sleeper, **jogador disponível** —
qualquer owner pode arrematá-lo ao vivo. Mesma separação do `salary_engine`: **`audit(board,
sheet)` é puro** (sem DB, sem rede — é o que os testes exercem); `fetch_board`/`build_sheet`/
`run_audit` são a camada de IO. UI em `/admin/keeper_audit` (+ `/api/admin/keeper_audit`).

- **4 classes de divergência:** keeper ausente do board (**bloqueante** — é a exposição), salário
  divergente, keeper no time errado, jogador no board fora da sheet. **A classe "slot errado" não
  existe** (`pick_no`/`round` não indicam vaga; a atribuição é automática por posição) — há teste
  que falha se alguém a criar.
- **3 estados de time (estado ≠ divergência):** `ok`, `nao_populado` (coluna vazia — pode ser
  bloqueio legítimo pelo teto, OFF26-10), `sem_coluna` (owner não aceitou o convite). Coluna sem
  dono vai para um balde próprio (`orphan_columns`) — **não é divergência de time nenhum**.
- **Bloqueiam a abertura:** classe 1, time não populado, time sem coluna, coluna órfã e keeper sem
  `sleeper_player_id` (auditoria incompleta). **Zero divergências não libera.**
- **Parametrização (D1):** `AppConfig["phantom_league_id"]` — **só o `league_id`, que é estável**.
  O `draft_id` **muda a cada RESET DRAFT** e é **derivado a cada uso** (vem no próprio objeto da
  liga, 1 requisição). ⛔ **Nunca persistir `draft_id`** (constante, config, coluna ou cache).
- **Armadilhas medidas:** `player_id` de DEF é **sigla** (`"LAR"`) — nunca coagir a inteiro;
  `metadata.amount` é **string**; rodadas vêm do **draft** (`draft.settings.rounds`), não da liga.
- **Identidade:** jogador só por `sleeper_id`, time só por `sleeper_owner_id` — **nunca por nome**
  (`metadata.team_name` veio nulo em 8/8 dos owners da fantasma, e há dois Rafas entre eles).
- **Meta da liga é independente da sheet (F2-META):** o bloco com `draft_id` derivado, status,
  rodadas, designações e colunas com/sem dono é exibido **mesmo sob bloqueio por falta de sheet** —
  é a única prova de que **o ambiente onde o app roda alcança a API do Sleeper** (falhas de egress/
  DNS não aparecem em localhost) e a única forma de conferir que o `league_id` aponta para a liga
  certa antes de a sheet existir. Erro de leitura é **estado próprio do bloco**, nunca 500.
- **Fixtures:** `keeper_audit_fixtures.py` é **material de teste congelado — NÃO é a keeper sheet
  real** (essa nasce da revelação da janela de cortes e vive no banco). Nenhum caminho de produção
  o importa.

### Audit Trails

Every action is logged: SalaryHistory (with `rule_applied` explanation), PlayerHistory (trades, corrections), SyncLog, Trade records, AuctionLog, ESPNImportLog.

## Conventions

- UI and comments in Portuguese (PT-BR), code identifiers in English
- Positions: QB, RB, WR, TE, K, DEF
- IR slots: max 2 per team
- AppConfig stores global state flags (current_season, offseason_mode, offseason_step, etc.)
- Players added via Sleeper sync are marked `needs_review=True`
- K/DEF excluded from salary cap calculations in some contexts

## Project Structure

```
fantasy_manager/
  app.py, wsgi.py, models.py       # Core app
  salary_engine.py                  # Pure salary logic (no DB)
  keeper_audit.py                   # OFF26-4: auditoria pré-leilão (núcleo puro + IO read-only)
  keeper_audit_fixtures.py          # material de TESTE congelado (NÃO é a keeper sheet real)
  cap_regua_test.py                 # OFF26-16: régua única de folha (IR conta) + guarda anti-réplica
  import_csv.py                     # CSV → DB upsert (reads data/)
  sync_sleeper.py                   # Sleeper API sync
  seed_users.py                     # User seeding (reads data/)
  init_data.py                      # Copy dynasty.db seed to /data/ on Render
  startup_check.py                  # Verify DB exists before startup
  routes/                           # Flask blueprints
  templates/, static/               # UI
  dynasty.db                        # Seed DB (in git for Render deploy)
  Procfile, render.yaml             # Render deployment config
  data/                             # Data files (mostly not in git)
    users.csv                       # User seed (in git — auto-seed on startup)
    dynasty_rosters_clean.csv       # Salary source (not in git)
    *.csv                           # Stats brutos (not in git)
  manager_devplan.md                # Plano vivo + log de decisões
  manager_vision.md                 # Motivação e casos de uso
  improvements.md                   # Backlog ATIVO (🔲/⚠️) + Status Rápido completo
  improvements_archive.md           # Histórico de itens ✅ (detalhe movido verbatim — O3)
  runbook_cowork_liga_fantasma.md   # OFF26-5: runbook operacional Cowork (montar/popular a liga fantasma na UI do Sleeper)
```

**Esquema de dois arquivos do backlog (item O3, 11/06/2026 — Manager-only):**
`improvements.md` é o backlog **ativo** — cabeçalho + **Status Rápido completo** (todos os IDs,
inclusive ✅; é o namespace e a baseline de dedupe) + seções detalhadas **só de itens 🔲/⚠️**.
`improvements_archive.md` guarda as seções detalhadas dos itens **✅**, movidas **verbatim** (registro
de evidência para diagnoses futuras: incidente Brown, post-mortem T2-FIX, decisões M15…). **Diagnose
que precise do histórico de um item fechado deve ler o archive.** **Regra de migração (entra no
checklist de fim de sessão):** ao marcar um item ✅ (validado em prod), mover sua seção detalhada para
o archive no fechamento da sessão; **⚠️ nunca migra** (fica no ativo até ✅).

## Version Control

Git initialized. Tag: `manager-v1.0` (hash `f2271ba`).
dynasty.db is the source of truth consumed by fantasy_optimizer and predictor.

## Deployment

### Render.com (primary)
- **URL:** https://dynasty-fantasy-manager.onrender.com
- **WSGI:** `wsgi.py` → calls `init_data()` (copies seed DB to `/data/`) then `create_app()`
- **Persistent disk:** mounted at `/data/`, holds `dynasty.db` in production
- **Env vars:** `APP_ENV=production`, `SECRET_KEY`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `DYNASTY_DB=/data/dynasty.db`
- **Seed DB:** `dynasty.db` is included in the repo. `init_data.py` copies it to `/data/` on first deploy only (never overwrites existing)
- **User seed:** `data/users.csv` is in git. Auto-seed on startup inserts new emails into `users` table
- `ProxyFix` enabled only when `APP_ENV=production`

#### Banco vivo de produção vs. seed — onde operar (confirmado 09/06/2026)

Há **dois** `dynasty.db` no servidor Render; operações em dados de prod (delete, backup,
auditoria) devem mirar o **vivo**, não o seed. A distinção é pela **env `DYNASTY_DB`**, não
pelo tamanho (as contagens podem coincidir por momento).

- **VIVO (produção):** `/data/dynasty.db` — disco persistente do Render. É o que o app usa
  em runtime: `render.yaml` define `DYNASTY_DB=/data/dynasty.db` e `app.py` lê
  `os.environ.get("DYNASTY_DB", ...)`. **Toda operação em dados de prod opera aqui.**
- **SEED (NÃO é produção):** `/opt/render/project/src/dynasty.db` — vem do git a cada deploy
  junto com o código. Não reflete o estado vivo; **editá-lo não tem efeito em produção**
  (`init_data.py` copia o seed p/ `/data/` só no 1º deploy, nunca sobrescreve).
- **Acesso:** Render Dashboard → serviço → **Shell**.
- **Backup seguro (com o app rodando):**
  `sqlite3 /data/dynasty.db ".backup '/data/<nome>.db'"` — usa a backup API do SQLite
  (consistente sob escrita concorrente). `/data` é persistente (sobrevive a restart),
  diferente do `/tmp`. Convenção de nome: `dynasty_prod_backup_<YYYY-MM-DD>_<motivo>.db`.

(Concretiza a regra "seed (git) ≠ produção (disco persistente)": o caminho vivo é
`/data/dynasty.db`.)

### PythonAnywhere (legacy)
- **URL:** https://mellowbr.pythonanywhere.com
- Same `wsgi.py` entry point
- DB and CSVs uploaded manually
