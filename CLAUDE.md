# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Dynasty SB is a Flask web app for managing a 12-team dynasty fantasy football league (Sleeper platform). It handles salary cap, contracts, trades, draft picks, and offseason workflows. The primary artifact is `dynasty.db`, consumed by the companion `fantasy_optimizer` and `predictor` projects. All projects live under `C:\Users\Erico Mello\Fantasy\`.

**League:** Dynasty SB | **My team:** Cangaceiros da Colina (MellowBR) | **Sleeper League ID:** 1316547584378048512

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run app (port 5000) — first run auto-imports data/dynasty_rosters_clean.csv
python app.py

# Run salary engine unit tests
python salary_engine_test.py

# Seed users (after first deploy)
python seed_users.py --csv data/users.csv
python seed_users.py --email user@gmail.com --name "Name" --team-id 1 --admin
python seed_users.py --list
```

## Architecture

### Core Principle: Salary Logic is Pure

`salary_engine.py` contains all salary/contract calculation logic with **zero DB dependencies** — pure functions only. This is the testable core. All ESPN values passed to the engine are **already adjusted** (raw × 1.2), as stored in `Player.espn_ref_value`. UI forms send raw values and multiply by 1.2 before passing to the engine.

### Data Authority Split

- **Sleeper API** is authoritative for: roster membership, player names/positions/NFL team, IR slots, traded picks
- **Local DB (`dynasty.db`)** is authoritative for: salaries, contract years, acquisition types, ESPN ref values
- **Sleeper sync never overwrites salary/contract data**

### App Startup Sequence (app.py)

1. `load_dotenv()` → load `.env` variables (before `create_app()`)
2. `create_app()` → Flask + SQLAlchemy init + ProxyFix
3. `db.create_all()` → create tables
4. `_run_migrations()` → add columns/tables to existing schema (incl. `users` table)
5. `_seed_app_config()` → seed default AppConfig key-value pairs
6. `init_auth(app)` → Flask-Login + Google OAuth setup
7. `run_import()` → one-time CSV import (players without team assignment)
8. `run_sync()` → Sleeper API sync (with try/except — app loads even if Sleeper is down)
9. `_backfill_player_history()` → create history records

### Route Blueprints (8)

| Blueprint | URL | Purpose |
|-----------|-----|---------|
| auth | `/login`, `/logout`, `/auth/callback` | Google OAuth authentication |
| roster | `/` | Team rosters, IR management, cap bar |
| salary | `/salary` | Salary calculator, cap projector, salary history |
| trades | `/trades` | Trade preview/confirmation with cap impact |
| picks | `/picks` | Draft picks 2025-2028, lottery system |
| auction | `/auction` | FA auction & rookie draft registration |
| admin | `/admin` | Sleeper sync, ESPN import, season rollover |
| offseason | `/offseason` | 7-step offseason workflow |

### Models (models.py)

14 SQLAlchemy models. Key ones: **User** (email, team_id, is_admin), Team, Player, SalaryHistory, Pick, AuctionLog, Trade, ESPNValue, AppConfig (key-value global state), SeasonStandings, DraftLotteryResult, PlayerHistory.

### Salary Cap Rules

- **Cap:** $200 | **Roster max:** 22 | **Min salary:** $1 | **Contract:** 4 years
- **Year 1:** auction_draft/keeper = bid amount; rookie_draft = floor(ESPN×1.2); waiver/FA = $1
- **Year 2+ (VALORIZAÇÃO):** MAX(prev_salary, floor(0.5 × ESPN_adjusted)), min $1
- **Waiver/FA Year 2 exception:** floor(0.80 × ESPN_adjusted), min $1
- **Renewal (after Year 4):** new 4-year contract, Year 1 = floor(ESPN_adjusted), min $1
- **Draft budget:** $200 − Σ(keeper salaries), minimum $1 per empty slot

### Offseason Workflow (7 steps)

1. Close Season → import standings from Sleeper or manual entry
2. Lock Draft Order → weighted lottery for picks 1-5 (8th-12th place), fixed 6-12
3. Update ESPN Values → bulk PDF import + player matching
4. Season Rollover → apply salary rules, increment contract years
5-7. Informational: rookie draft, keepers/cuts, FA auction (manual via /auction)

### Authentication & Permissions

- **Google OAuth** via `authlib` + `flask-login` (blueprint `routes/auth.py`)
- **User model**: email → team_id + is_admin. Seeded via `seed_users.py` (CSV or CLI)
- **`@login_required`**: all routes except `/login`, `/logout`, `/auth/callback`
- **`@admin_required`**: POST/PATCH/DELETE that alter calculated data or are irreversible
- **Exception**: `POST /api/admin/sync` uses `@login_required` only (reflexive, never overwrites salary/contract data)
- **Unauthorized handler**: `/api/*` routes return 401/403 JSON; page routes redirect to `/login`
- **WSGI**: `wsgi.py` as entry point for PythonAnywhere; `ProxyFix` for reverse proxy headers
- **Environment**: `.env` with `SECRET_KEY`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `APP_ENV`

### External Integrations

- **Sleeper API** (`sync_sleeper.py`): rosters, team info, winners bracket, previous league. Player DB cached weekly (~15MB `.sleeper_players_cache.json`). Startup sync wrapped in try/except for graceful degradation.
- **ESPN PDF** (`espn_pdf_parser.py`): parse draft value sheets, match to DB players with 3-tier matching (exact → case-insensitive → normalized)
- **Google OAuth**: OpenID Connect via Google's well-known endpoint

### Player Name Matching (player_lookup.py)

Strict full-name matching to prevent the "3 Browns" bug. Never falls back to partial/substring matching. Three tiers: exact → case-insensitive → normalized (strips accents, suffixes, punctuation).

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
  import_csv.py                     # CSV → DB upsert (reads data/)
  sync_sleeper.py                   # Sleeper API sync
  seed_users.py                     # User seeding (reads data/)
  routes/                           # Flask blueprints
  templates/, static/               # UI
  data/                             # Data files (not in git)
    dynasty_rosters_clean.csv       # Salary source (ACTIVE)
    users.csv                       # User seed (ACTIVE)
    *.csv                           # Stats brutos (futuro)
  manager_devplan.md                # Plano vivo + log de decisões
  manager_vision.md                 # Motivação e casos de uso
  improvements.md                   # Backlog vivo
```

## Version Control

Git initialized. Tag: `manager-v1.0` (hash `f2271ba`).
dynasty.db is the source of truth consumed by fantasy_optimizer and predictor.

## Deployment

- **PythonAnywhere** (~$5/mês) — WSGI via `wsgi.py`
- `APP_ENV=production` disables debug mode
- `SECRET_KEY` must be fixed (changing it logs out all users)
- `.env` excluded from git via `.gitignore`
- `ProxyFix` ensures correct `https://` URLs behind reverse proxy
