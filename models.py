from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

SALARY_CAP = 200
MAX_ROSTER = 22
MAX_IR = 2
CURRENT_SEASON = 2025  # fallback — prefer get_current_season()
CONTRACT_LENGTH = 4
MY_TEAM_NAME = "Cangaceiros da Colina"
MY_OWNER_ID = "1130162144764506112"
LEAGUE_ID = "1316547584378048512"

POS_ORDER = {"QB": 0, "RB": 1, "WR": 2, "TE": 3, "K": 4, "DST": 5, "D/ST": 5, "DEF": 5}


def sort_players_by_pos(players):
    """Sort players by position (QB→DEF), then salary descending."""
    return sorted(players, key=lambda p: (POS_ORDER.get(p.position, 99), -p.salary))


# ── AppConfig helpers ────────────────────────────────────────────────────────

def get_config(key: str, default=None) -> str | None:
    row = db.session.get(AppConfig, key) if _table_exists("app_config") else None
    return row.value if row else default


def set_config(key: str, value):
    row = db.session.get(AppConfig, key)
    if row:
        row.value = str(value)
    else:
        db.session.add(AppConfig(key=key, value=str(value)))
    db.session.commit()


def get_current_season() -> int:
    return int(get_config("current_season", CURRENT_SEASON))


def is_offseason() -> bool:
    return get_config("offseason_mode", "false") == "true"


def _table_exists(name: str) -> bool:
    from sqlalchemy import inspect
    try:
        return name in inspect(db.engine).get_table_names()
    except Exception:
        return False


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=True)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    team_rel = db.relationship("Team", foreign_keys=[team_id])

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "team_id": self.team_id,
            "is_admin": self.is_admin,
        }


class Team(db.Model):
    __tablename__ = "teams"

    id = db.Column(db.Integer, primary_key=True)
    sleeper_roster_id = db.Column(db.String(50), unique=True, nullable=True)
    sleeper_owner_id = db.Column(db.String(50), nullable=True)
    name = db.Column(db.String(120), nullable=False)
    display_name = db.Column(db.String(120), nullable=True)
    owner_name = db.Column(db.String(120), nullable=True)
    owner_avatar = db.Column(db.String(120), nullable=True)
    is_my_team = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    players = db.relationship("Player", back_populates="team_rel", lazy="dynamic",
                              foreign_keys="Player.team_id")

    def active_salary(self):
        return sum(
            p.salary for p in self.players
            if not p.is_dropped and not p.is_on_ir
        )

    def total_salary(self):
        return sum(p.salary for p in self.players if not p.is_dropped)

    def cap_remaining(self):
        return SALARY_CAP - self.active_salary()

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name or self.name,
            "owner_name": self.owner_name or "",
            "owner_avatar": self.owner_avatar or "",
            "is_my_team": self.is_my_team,
            "active_salary": self.active_salary(),
            "cap_remaining": self.cap_remaining(),
        }


class Player(db.Model):
    __tablename__ = "players"

    id = db.Column(db.Integer, primary_key=True)
    sleeper_player_id = db.Column(db.String(50), nullable=True, index=True)
    name = db.Column(db.String(120), nullable=False)
    position = db.Column(db.String(10), nullable=False, default="")
    nfl_team = db.Column(db.String(60), default="")
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=True)
    fantasy_team = db.Column(db.String(120), default="", index=True)
    salary = db.Column(db.Float, nullable=False, default=1.0)
    contract_year = db.Column(db.Integer, nullable=False, default=1)
    contract_start_season = db.Column(db.Integer, nullable=True)
    acquisition_type = db.Column(db.String(40), default="unknown")
    espn_ref_value = db.Column(db.Float, default=0.0)
    is_on_ir = db.Column(db.Boolean, default=False)
    is_my_team = db.Column(db.Boolean, default=False)
    is_dropped = db.Column(db.Boolean, default=False)
    via_trade = db.Column(db.Boolean, default=False)
    needs_review = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text, default="")
    orig_draft_season = db.Column(db.Integer, nullable=True)
    orig_draft_type = db.Column(db.String(50), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    team_rel = db.relationship("Team", back_populates="players", foreign_keys=[team_id])
    salary_history = db.relationship("SalaryHistory", back_populates="player", lazy="dynamic",
                                     cascade="all, delete-orphan")

    @property
    def fantasy_team_name(self):
        return self.fantasy_team or (self.team_rel.name if self.team_rel else "—")

    def contract_display(self):
        return f"Ano {self.contract_year}/{CONTRACT_LENGTH}"

    def is_renewal_candidate(self):
        return self.contract_year >= CONTRACT_LENGTH

    def projected_next_salary(self):
        from salary_engine import compute_salary_for_year
        espn = self.espn_ref_value or 0.0
        if not espn:
            return int(self.salary)
        next_yr = self.contract_year + 1
        return compute_salary_for_year(
            acq_type=self.acquisition_type,
            year1_value=self.salary,
            espn=espn,
            target_yr=next_yr,
        )

    def to_dict(self):
        from salary_engine import project_next_salary
        return {
            "id": self.id,
            "sleeper_player_id": self.sleeper_player_id,
            "name": self.name,
            "position": self.position,
            "nfl_team": self.nfl_team or "—",
            "fantasy_team": self.fantasy_team_name,
            "team_id": self.team_id,
            "salary": self.salary,
            "contract_year": self.contract_year,
            "contract_display": self.contract_display(),
            "contract_start_season": self.contract_start_season,
            "acquisition_type": self.acquisition_type,
            "espn_ref_value": self.espn_ref_value or 0.0,
            "is_on_ir": self.is_on_ir,
            "is_my_team": self.is_my_team,
            "is_dropped": self.is_dropped,
            "via_trade": self.via_trade,
            "needs_review": self.needs_review,
            "notes": self.notes,
            "is_renewal_candidate": self.is_renewal_candidate(),
            "projected_next_salary": project_next_salary(self),
        }


def correct_player_salary(player_id: int, new_salary: float,
                          reason: str = "Correção manual") -> dict:
    """
    Correct a player's salary in BOTH Player and SalaryHistory tables.

    Updates Player.salary and the most recent SalaryHistory record.
    Also records a PlayerHistory entry with event_type='salary_correction'.

    Returns dict with old/new values for confirmation.
    """
    player = db.session.get(Player, player_id)
    if not player:
        return {"error": f"Player id={player_id} not found"}

    old_salary = player.salary
    if old_salary == new_salary:
        return {"player": player.name, "salary": new_salary, "changed": False}

    # 1. Update Player.salary
    player.salary = new_salary
    player.updated_at = datetime.utcnow()

    # 2. Update most recent SalaryHistory record (if exists)
    latest_sh = (SalaryHistory.query
                 .filter_by(player_id=player_id)
                 .order_by(SalaryHistory.season.desc(), SalaryHistory.id.desc())
                 .first())
    if latest_sh:
        latest_sh.salary = new_salary

    # 3. Record in PlayerHistory
    team_name = player.team_rel.name if player.team_rel else ""
    season = int(get_config("current_season", CURRENT_SEASON))
    ph = PlayerHistory(
        player_id=player_id,
        season=season,
        team_name=team_name,
        event_type="salary_correction",
        salary=new_salary,
        contract_year=player.contract_year,
        notes=f"{reason}: ${old_salary:.0f} -> ${new_salary:.0f}",
    )
    db.session.add(ph)

    return {
        "player": player.name,
        "old_salary": old_salary,
        "new_salary": new_salary,
        "changed": True,
        "salary_history_updated": latest_sh is not None,
    }


class SalaryHistory(db.Model):
    __tablename__ = "salary_history"

    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=False)
    season = db.Column(db.Integer, nullable=False)
    salary = db.Column(db.Float, nullable=False)
    contract_year = db.Column(db.Integer, nullable=False)
    rule_applied = db.Column(db.String(100), default="")
    espn_ref_value = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    player = db.relationship("Player", back_populates="salary_history")

    def to_dict(self):
        return {
            "id": self.id,
            "player_id": self.player_id,
            "player_name": self.player.name if self.player else "—",
            "season": self.season,
            "salary": self.salary,
            "contract_year": self.contract_year,
            "rule_applied": self.rule_applied,
            "espn_ref_value": self.espn_ref_value,
        }


class Pick(db.Model):
    __tablename__ = "picks"

    id = db.Column(db.Integer, primary_key=True)
    season = db.Column(db.Integer, nullable=False)
    round = db.Column(db.Integer, nullable=False)
    original_team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=True)
    current_team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=True)
    original_team_name = db.Column(db.String(120), default="")
    current_team_name = db.Column(db.String(120), default="")
    traded_away = db.Column(db.Boolean, default=False)
    notes = db.Column(db.String(200), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "season": self.season,
            "round": self.round,
            "original_team_name": self.original_team_name,
            "current_team_name": self.current_team_name,
            "traded_away": self.traded_away,
            "notes": self.notes,
        }


class AuctionLog(db.Model):
    __tablename__ = "auction_log"

    id = db.Column(db.Integer, primary_key=True)
    season = db.Column(db.Integer, nullable=False, default=CURRENT_SEASON)
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=True)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=True)
    player_name = db.Column(db.String(120), default="")
    team_name = db.Column(db.String(120), default="")
    entry_type = db.Column(db.String(30), default="fa_auction")  # fa_auction / rookie_draft
    value_paid = db.Column(db.Float, default=1.0)
    round_num = db.Column(db.Integer, nullable=True)
    espn_ref_value_at_time = db.Column(db.Float, default=0.0)
    notes = db.Column(db.String(200), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "season": self.season,
            "player_name": self.player_name,
            "team_name": self.team_name,
            "entry_type": self.entry_type,
            "value_paid": self.value_paid,
            "round_num": self.round_num,
            "espn_ref_value_at_time": self.espn_ref_value_at_time,
            "notes": self.notes,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else "",
        }


# ── OFF26-3: helper atômico canônico de aquisição (ano 1) ─────────────────────

def record_acquisition(*, team, acquisition_type, season, player=None,
                       player_name=None, position="", value_paid=0.0,
                       espn_adjusted=0.0, round_num=None, sleeper_player_id=None,
                       event_ref=None, notes=""):
    """
    OFF26-3 — ÚNICA porta de criação de contrato de aquisição (ano 1).

    Cria/atualiza Player + grava SalaryHistory + AuctionLog atomicamente
    (adiciona à sessão; o CHAMADOR faz commit — permite lote transacional no
    importador). Salário SEMPRE via salary_engine.year1_salary (canônico):
    rookie_draft → floor(ESPN×1.2); demais (auction/fa) → value_paid.

    player: Player existente p/ atualizar, ou None p/ criar (usa player_name).
    event_ref: token de idempotência (ex 'draft:<id>:<pick>') gravado em
               AuctionLog.notes como '[ref:<event_ref>]'. A checagem de duplicata
               é do chamador, via acquisition_already_recorded().
    Retorna (player, salary).
    """
    from salary_engine import year1_salary
    salary = year1_salary(acquisition_type, value_paid, espn_adjusted)
    is_rookie = (acquisition_type or "").lower().strip() == "rookie_draft"
    entry_type = "rookie_draft" if is_rookie else "fa_auction"

    if player is None:
        player = Player(
            name=(player_name or "").strip(),
            position=position or "",
            team_id=team.id,
            is_my_team=team.is_my_team,
            needs_review=True,
            sleeper_player_id=str(sleeper_player_id) if sleeper_player_id else None,
        )
        db.session.add(player)
        db.session.flush()

    player.salary = salary
    player.contract_year = 1
    player.contract_start_season = season
    player.acquisition_type = acquisition_type
    player.espn_ref_value = espn_adjusted
    player.team_id = team.id
    player.is_my_team = team.is_my_team
    player.is_dropped = False
    if sleeper_player_id and not player.sleeper_player_id:
        player.sleeper_player_id = str(sleeper_player_id)

    if is_rookie:
        rd = f" Rd{round_num}" if round_num else ""
        rule = f"Rookie Draft{rd}: floor(ESPN×1.2)=${salary}"
        log_value = salary
    else:
        rule = f"FA Auction: ${salary} (bid)"
        log_value = value_paid or salary

    db.session.add(SalaryHistory(
        player_id=player.id, season=season, salary=salary, contract_year=1,
        rule_applied=rule, espn_ref_value=espn_adjusted,
    ))

    note_full = notes or ""
    if event_ref:
        tag = f"[ref:{event_ref}]"
        note_full = (note_full + " " + tag).strip()
    note_full = note_full[:200]
    db.session.add(AuctionLog(
        season=season, player_id=player.id, team_id=team.id,
        player_name=player.name, team_name=team.name, entry_type=entry_type,
        value_paid=log_value, round_num=round_num,
        espn_ref_value_at_time=espn_adjusted, notes=note_full,
    ))
    return player, salary


def acquisition_already_recorded(event_ref) -> bool:
    """OFF26-3 — idempotência SEM mudança de schema: detecta se já existe um
    AuctionLog com o token '[ref:<event_ref>]' em notes."""
    if not event_ref:
        return False
    tag = f"[ref:{event_ref}]"
    return db.session.query(AuctionLog.id).filter(
        AuctionLog.notes.like(f"%{tag}%")).first() is not None


class ESPNValue(db.Model):
    __tablename__ = "espn_values"

    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=False)
    season = db.Column(db.Integer, nullable=False)
    espn_raw = db.Column(db.Float, default=0.0)
    espn_adjusted = db.Column(db.Float, default=0.0)  # raw × 1.2
    is_final = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("player_id", "season", name="uq_player_season"),)

    def to_dict(self):
        return {
            "player_id": self.player_id,
            "season": self.season,
            "espn_raw": self.espn_raw,
            "espn_adjusted": self.espn_adjusted,
            "is_final": self.is_final,
        }


class ESPNImportLog(db.Model):
    __tablename__ = "espn_import_log"

    id = db.Column(db.Integer, primary_key=True)
    imported_at = db.Column(db.DateTime, default=datetime.utcnow)
    season = db.Column(db.Integer, nullable=False)
    url_used = db.Column(db.String(500), default="")
    status = db.Column(db.String(20), default="provisional")  # provisional / final
    total_matched = db.Column(db.Integer, default=0)
    total_approximate = db.Column(db.Integer, default=0)
    total_notfound = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            "id": self.id,
            "imported_at": self.imported_at.strftime("%d/%m/%Y %H:%M") if self.imported_at else "",
            "season": self.season,
            "url_used": self.url_used,
            "status": self.status,
            "total_matched": self.total_matched,
            "total_approximate": self.total_approximate,
            "total_notfound": self.total_notfound,
        }


class Trade(db.Model):
    __tablename__ = "trades"

    id = db.Column(db.Integer, primary_key=True)
    trade_date = db.Column(db.DateTime, default=datetime.utcnow)
    team_a = db.Column(db.String(120), nullable=False)
    team_b = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, default="")
    source = db.Column(db.String(20), default="manual")  # 'manual' | 'sleeper_sync'
    sleeper_transaction_id = db.Column(db.String(50), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "trade_date": self.trade_date.strftime("%d/%m/%Y %H:%M") if self.trade_date else "",
            "team_a": self.team_a,
            "team_b": self.team_b,
            "description": self.description,
            "source": self.source,
            "sleeper_transaction_id": self.sleeper_transaction_id,
        }


class SyncLog(db.Model):
    __tablename__ = "sync_log"

    id = db.Column(db.Integer, primary_key=True)
    synced_at = db.Column(db.DateTime, default=datetime.utcnow)
    players_updated = db.Column(db.Integer, default=0)
    players_added = db.Column(db.Integer, default=0)
    teams_updated = db.Column(db.Integer, default=0)
    picks_updated = db.Column(db.Integer, default=0)
    summary = db.Column(db.Text, default="")
    had_errors = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "synced_at": self.synced_at.strftime("%d/%m/%Y %H:%M") if self.synced_at else "",
            "players_updated": self.players_updated,
            "players_added": self.players_added,
            "teams_updated": self.teams_updated,
            "picks_updated": self.picks_updated,
            "summary": self.summary,
            "had_errors": self.had_errors,
        }


# ── Offseason models ─────────────────────────────────────────────────────────

class AppConfig(db.Model):
    __tablename__ = "app_config"

    key = db.Column(db.String(80), primary_key=True)
    value = db.Column(db.Text, nullable=False, default="")

    def to_dict(self):
        return {"key": self.key, "value": self.value}


class SeasonStandings(db.Model):
    __tablename__ = "season_standings"

    id = db.Column(db.Integer, primary_key=True)
    season = db.Column(db.Integer, nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=True)
    team_name = db.Column(db.String(120), nullable=False)
    rank = db.Column(db.Integer, nullable=True)
    wins = db.Column(db.Integer, default=0)
    losses = db.Column(db.Integer, default=0)
    points_for = db.Column(db.Float, default=0.0)
    is_champion = db.Column(db.Boolean, default=False)
    is_runner_up = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "season": self.season,
            "team_id": self.team_id,
            "team_name": self.team_name,
            "rank": self.rank,
            "wins": self.wins,
            "losses": self.losses,
            "points_for": round(self.points_for, 2),
            "is_champion": self.is_champion,
            "is_runner_up": self.is_runner_up,
        }


class DraftLotteryResult(db.Model):
    __tablename__ = "draft_lottery_result"

    id = db.Column(db.Integer, primary_key=True)
    season = db.Column(db.Integer, nullable=False)
    pick_number = db.Column(db.Integer, nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=True)
    team_name = db.Column(db.String(120), nullable=False)
    source = db.Column(db.String(30), default="standings")  # lottery / standings
    locked = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "season": self.season,
            "pick_number": self.pick_number,
            "team_id": self.team_id,
            "team_name": self.team_name,
            "source": self.source,
            "locked": self.locked,
        }


class PlayerHistory(db.Model):
    __tablename__ = "player_history"

    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=False)
    season = db.Column(db.Integer, nullable=True)
    team_name = db.Column(db.String(120), default="")
    event_type = db.Column(db.String(30), nullable=False)
    salary = db.Column(db.Float, default=0.0)
    contract_year = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text, default="")
    # F8a — sleeper_event_ref is the 5th field of the UNIQUE index.
    # Formats: 'tx:<transaction_id>' | 'draft:<draft_id>:<pick_no>' | 'rollover:<season>' | NULL (legacy)
    sleeper_event_ref = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    player = db.relationship("Player", backref=db.backref("history", lazy="dynamic"))

    __table_args__ = (
        db.UniqueConstraint(
            "player_id", "season", "event_type", "team_name", "sleeper_event_ref",
            name="uq_player_history_event",
        ),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "player_id": self.player_id,
            "player_name": self.player.name if self.player else "",
            "season": self.season,
            "team_name": self.team_name,
            "event_type": self.event_type,
            "salary": self.salary,
            "contract_year": self.contract_year,
            "notes": self.notes,
            "sleeper_event_ref": self.sleeper_event_ref,
            "created_at": self.created_at.strftime("%d/%m/%Y %H:%M") if self.created_at else "",
        }


class F8PlayerBackup(db.Model):
    """F8a rollback — snapshot of Player.contract_start_season + acquisition_type
    before reconciliation. Restored by F8c endpoint on /api/admin/player_history/restore."""
    __tablename__ = "f8_player_backup"

    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=False)
    old_contract_start_season = db.Column(db.Integer, nullable=True)
    old_acquisition_type = db.Column(db.String(40), nullable=True)
    snapshot_at = db.Column(db.DateTime, default=datetime.utcnow)


class LotteryAudit(db.Model):
    """M8 — auditoria do draft lottery. 1 row por execução (canônica + superseded).
    Reprodução via seed + pool_json snapshot: resistente a edições posteriores de standings."""
    __tablename__ = "lottery_audit"

    id = db.Column(db.Integer, primary_key=True)
    season = db.Column(db.Integer, nullable=False)
    random_seed = db.Column(db.String(64), nullable=False)  # secrets.token_hex(16) = 32 chars
    weights_json = db.Column(db.Text, nullable=False)  # {"1": 50, "2": 25, ...}
    pool_json = db.Column(db.Text, nullable=False)  # [{team_id, team_name, seed, weight}, ...]
    executed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    executed_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    result_hash = db.Column(db.String(64), nullable=False)  # SHA256 hex
    previous_audit_id = db.Column(db.Integer, db.ForeignKey("lottery_audit.id"), nullable=True)
    reason = db.Column(db.Text, nullable=True)  # obrigatório quando previous_audit_id preenchido
    is_canonical = db.Column(db.Boolean, default=True, nullable=False)

    executor = db.relationship("User", foreign_keys=[executed_by])
    previous = db.relationship("LotteryAudit", remote_side=[id], foreign_keys=[previous_audit_id])

    def to_dict(self):
        import json as _json
        return {
            "id": self.id,
            "season": self.season,
            "random_seed": self.random_seed,
            "weights": _json.loads(self.weights_json),
            "pool": _json.loads(self.pool_json),
            "executed_at": self.executed_at.strftime("%d/%m/%Y %H:%M") if self.executed_at else None,
            "executed_by_name": self.executor.name if self.executor else None,
            "result_hash": self.result_hash,
            "previous_audit_id": self.previous_audit_id,
            "reason": self.reason,
            "is_canonical": self.is_canonical,
        }


class TradeProposal(db.Model):
    """T1 — simulação de trade salva com UUID para compartilhar via link.
    Expira 7 dias após created_at. Assets armazenados como JSON arrays
    de IDs (players_a, players_b, picks_a, picks_b). NÃO move nada no DB —
    é simulação pura. A confirmação real vem do Sleeper via S1."""
    __tablename__ = "trade_proposals"

    id = db.Column(db.String(36), primary_key=True)  # UUID v4
    team_a_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=False)
    team_b_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=False)
    players_a = db.Column(db.Text, nullable=False, default="[]")
    players_b = db.Column(db.Text, nullable=False, default="[]")
    picks_a = db.Column(db.Text, nullable=False, default="[]")
    picks_b = db.Column(db.Text, nullable=False, default="[]")
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)

    team_a = db.relationship("Team", foreign_keys=[team_a_id])
    team_b = db.relationship("Team", foreign_keys=[team_b_id])
    creator = db.relationship("User", foreign_keys=[created_by])

    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at
