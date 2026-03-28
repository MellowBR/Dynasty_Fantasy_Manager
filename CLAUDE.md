# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Dynasty SB is a Flask web app for managing a 12-team dynasty fantasy football league (Sleeper platform). It handles salary cap, contracts, trades, draft picks, and offseason workflows. The primary artifact is `dynasty.db`, consumed by the companion `fantasy_optimizer` and `predictor` projects. All projects live under `C:\Users\Erico Mello\Fantasy\`.

**League:** Dynasty SB | **My team:** Cangaceiros da Colina (MellowBR) | **Sleeper League ID:** 1316547584378048512

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run app (port 5000) — first run auto-imports dynasty_rosters_clean.csv
python app.py

# Run salary engine unit tests
python salary_engine_test.py
```

## Architecture

### Core Principle: Salary Logic is Pure

`salary_engine.py` contains all salary/contract calculation logic with **zero DB dependencies** — pure functions only. This is the testable core. All ESPN values passed to the engine are **already adjusted** (raw × 1.2), as stored in `Player.espn_ref_value`. UI forms send raw values and multiply by 1.2 before passing to the engine.

### Data Authority Split

- **Sleeper API** is authoritative for: roster membership, player names/positions/NFL team, IR slots, traded picks
- **Local DB (`dynasty.db`)** is authoritative for: salaries, contract years, acquisition types, ESPN ref values
- **Sleeper sync never overwrites salary/contract data**

### App Startup Sequence (app.py)

1. `create_app()` → Flask + SQLAlchemy init
2. `db.create_all()` → create tables
3. `_run_migrations()` → add columns to existing tables
4. `_seed_app_config()` → seed default AppConfig key-value pairs
5. `run_import()` → one-time CSV import (players without team assignment)
6. `run_sync()` → Sleeper API sync (assigns players to teams)
7. `_backfill_player_history()` → create history records

### Route Blueprints (7)

| Blueprint | URL | Purpose |
|-----------|-----|---------|
| roster | `/` | Team rosters, IR management, cap bar |
| salary | `/salary` | Salary calculator, cap projector, salary history |
| trades | `/trades` | Trade preview/confirmation with cap impact |
| picks | `/picks` | Draft picks 2025-2028, lottery system |
| auction | `/auction` | FA auction & rookie draft registration |
| admin | `/admin` | Sleeper sync, ESPN import, season rollover |
| offseason | `/offseason` | 7-step offseason workflow |

### Models (models.py)

15+ SQLAlchemy models. Key ones: Team, Player, SalaryHistory, Pick, AuctionLog, Trade, ESPNValue, AppConfig (key-value global state), SeasonStandings, DraftLotteryResult, PlayerHistory.

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

### External Integrations

- **Sleeper API** (`sync_sleeper.py`): rosters, team info, winners bracket, previous league. Player DB cached weekly (~15MB `.sleeper_players_cache.json`)
- **ESPN PDF** (`espn_pdf_parser.py`): parse draft value sheets, match to DB players with 3-tier matching (exact → case-insensitive → normalized)

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
