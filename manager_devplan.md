# devplan.md — Fantasy Manager

> Plano vivo + Log de Decisões  
> Última atualização: 02/04/2026  
> Status atual: Produção (PythonAnywhere) | Tag: `manager-v1.0`

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
