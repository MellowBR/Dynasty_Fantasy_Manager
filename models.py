from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import json
import os
from timeutil import utc_iso  # M18: transporte UTC não-ambíguo nos to_dict de display
from salary_engine import roster_salary  # OFF26-16: fonte única da folha (inclui IR)

db = SQLAlchemy()

SALARY_CAP = 200
MAX_ROSTER = 22
# MAX_IR: informativo. Quem enforça o limite de IR é o Sleeper — o Manager só espelha
# `reserve` no sync. Sem referência em código desde o IR-CLEANUP (04/08/2026), que removeu
# o toggle manual onde a constante era validada. Preservado de propósito: documenta a
# regra da liga (item 1.3 do regulamento) e é a âncora se algum dia houver validação local.
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

    # ── OFF26-16: RÉGUA ÚNICA DE FOLHA — o IR conta no cap, sempre ────────────────
    #
    # Decisão do owner (04/08/2026), explícita e final: **jogador no IR conta no cap hit
    # como qualquer outro**. Existe UMA folha salarial — todos os jogadores do elenco,
    # ativos e IR — e ela é a mesma em toda tela, todo cálculo e todo contexto.
    #
    # Aritmética em `salary_engine.roster_salary` (fonte ÚNICA, testável sem DB). É a
    # mesma regra que `draft_budget` sempre aplicou; agora também nas telas.
    #
    # ⛔ NÃO recriar uma soma que filtre `is_on_ir` para fins de folha. Havia SEIS
    # definições da régua sem IR (este helper + 5 somas inline nas rotas) e a F2 do
    # OFF26-14 chegou a rotulá-las na tela; a decisão do owner tornou o número sem IR
    # sem significado. `cap_regua_test.TestSemReplicaDeFolha` falha se a réplica voltar.
    def total_salary(self):
        """Folha salarial do time — a única régua. Inclui IR; exclui só dropados."""
        return roster_salary(self.players)

    def cap_remaining(self):
        return SALARY_CAP - self.total_salary()

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name or self.name,
            "owner_name": self.owner_name or "",
            "owner_avatar": self.owner_avatar or "",
            "is_my_team": self.is_my_team,
            # OFF26-16: a chave antiga tinha nome que mentia (excluía IR); virou
            # `salary_total`. Consumidor: templates/trades.html.
            "salary_total": self.total_salary(),
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
        # OFF26-20 T4: fonte ÚNICA de projeção — a mesma do Cap Projector, da porta /budget
        # e do rollover real (respeita o salário armazenado; a reconstrução do contrato do
        # zero superestimava a coluna PROJ em 26/248 jogadores, até +$18 num único rookie).
        from salary_engine import project_next_salary
        return project_next_salary(self)

    def to_search_dict(self):
        """
        M10 — payload ENXUTO da busca (`/api/player/search`), os dois consumidores.

        `to_dict()` invoca `is_renewal_candidate()` + `project_next_salary()` por
        jogador: 20 resultados × cada tecla digitada é projeção de contrato que a
        busca não exibe. Aqui só o que as duas telas renderizam/preenchem:
        - navegação e identidade: `id` (destino `/player/<id>`) e `sleeper_player_id`
          (foto — mesma chave do `renderPlayerPhoto`; ⛔ nunca o nome);
        - desambiguação de homônimos na lista: posição + time NFL + franquia;
        - autocomplete da calculadora: contrato, aquisição e ESPN (**ajustado**, como
          está no banco — quem exibe em cru divide por 1.2, ver `salary.html`);
        - status FA (M21-A): `is_dropped` alimenta o badge "FA" da linha — sem ele o
          dropado apareceria com a última franquia como se fosse dono atual.
        """
        return {
            "id": self.id,
            "is_dropped": self.is_dropped,
            "sleeper_player_id": self.sleeper_player_id,
            "name": self.name,
            "position": self.position,
            "nfl_team": self.nfl_team or "",
            "fantasy_team": self.fantasy_team_name,
            "team_id": self.team_id,
            "salary": self.salary,
            "contract_year": self.contract_year,
            "contract_display": self.contract_display(),
            "acquisition_type": self.acquisition_type,
            "espn_ref_value": self.espn_ref_value or 0.0,
        }

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
    player.team_id = team.id
    player.is_my_team = team.is_my_team
    player.is_dropped = False
    if sleeper_player_id and not player.sleeper_player_id:
        player.sleeper_player_id = str(sleeper_player_id)
    # E4-c-1: valor ESPN via fonte única (store canônico + materializa a coluna). Após o
    # sid estar finalizado, para o upsert do store usar a chave correta.
    set_espn_value(player, season, espn_adjusted)

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


# ── OFF26-29: pick consumida — predicado ÚNICO por evidência de AuctionLog ─────

def consumed_pick_seasons() -> set:
    """OFF26-29 — seasons cujo rookie draft JÁ ACONTECEU: existe AuctionLog
    `entry_type='rookie_draft'` na season. A MESMA evidência do gate do passo 5
    (OFF26-23); materializada em 2026 pelos 36 registros do reparo OFF26-26.

    É o que decide "pick consumida" nas superfícies de exibição/seleção
    (board, /team/<id>, /api/picks → simulador/propostas). Data-driven de
    propósito: autossustentável entre seasons (2027 fica tradável até o draft
    2027 ter registro), sem ciclo de vida de flag (`rookie_draft_done` foi
    descartada — família L4). ⛔ A row da Pick fica VIVA (delete foi refutado
    na F1: o sync recriaria via /traded_picks) e `_sync_trades` segue
    espelhando trade real — consumida é estado de LEITURA, não de tabela."""
    rows = db.session.query(AuctionLog.season).filter_by(
        entry_type="rookie_draft").distinct().all()
    return {r[0] for r in rows}


def pick_is_consumed(pick, consumed: set = None) -> bool:
    """OFF26-29 — True se a pick pertence a uma season de draft já realizado.
    `consumed`: passe o set de consumed_pick_seasons() ao filtrar listas
    (1 query para N picks). ⛔ Predicado em 1 lugar só — consumidores importam
    daqui; nenhuma réplica em JS/template."""
    if consumed is None:
        consumed = consumed_pick_seasons()
    return pick.season in consumed


# ── UX23: season-alvo de PLANEJAMENTO do cap projector — fonte única de fase ──

# Calibração do predicado de "auction realizada" (decisão delegada ao Code no F2):
# ≥3 registros. Um leilão real entra em LOTE pelo importador (dezenas de arremates);
# 1-2 registros são a assinatura de teste manual/engano avulso no /auction — que NÃO
# deve virar a chave no meio da janela 20-24/08 (hoje o /auction ainda carimba 2025 —
# OFF26-28 — mas o fix dele removeria essa proteção acidental; o limiar cobre o vão).
AUCTION_EVIDENCE_MIN = 3


def planning_target_season() -> int:
    """UX23 — a season que o cap projector PLANEJA (fonte única; era `current+1`
    inline em 6 sítios, sem consciência de fase — a F1 mapeou todos):

    - pré-rollover → `current + 1` (comportamento histórico: projetar a próxima);
    - pós-rollover, FA auction da season corrente AINDA NÃO realizada → `current`
      (a janela operacional é a auction da season que acabou de virar; a base
      correta é a folha CORRENTE — modo D9, `compose_budget(projected=False)`);
    - auction realizada → `current + 1` de novo (planejamento da próxima recomeça).

    "Auction realizada" é EVIDÊNCIA, não flag (decisão do owner, opção b — família
    do predicado OFF26-29): ≥ AUCTION_EVIDENCE_MIN AuctionLog `fa_auction` na season
    corrente. Autossustentável entre seasons; vira sozinho quando o import do leilão
    entrar. ⛔ `auction_done` (passo 7) fica como está — não é insumo daqui."""
    season = get_current_season()
    if get_config("rollover_done", "false") != "true":
        return season + 1
    n = db.session.query(AuctionLog.id).filter_by(
        entry_type="fa_auction", season=season).count()
    return season + 1 if n >= AUCTION_EVIDENCE_MIN else season


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


class RookieEspnValue(db.Model):
    """E2 + DP3 — store de valores ESPN de rookies/entrantes que ainda NÃO existem como
    Player no DB (caem em not_found no import ESPN, pois entram só no rookie draft).
    Keyed por sleeper_player_id (resolvido contra o pool global do Sleeper).
    Camada de dados transitória do ciclo de draft — limpa pós-rookie-draft.
    Consumido por: OFF26-3 (salário no draft) + DP1/DP3 (board de planejamento de cap).
    NÃO é Player (não polui roster/cap); `espn_adjusted` = raw×1.2 (mesma semântica de
    Player.espn_ref_value). O salário (floor) é derivado por salary_engine no draft.
    DP3 (snapshot materializado, postura P3): `in_class` marca a MEMBERSHIP da classe
    entrante, escrita SÓ pela captura admin (varre o pool via is_entering_class_member).
    O board lê in_class=True; linhas do import ESPN sem captura (ex.: veterano
    não-rosterado do Top-300) ficam in_class=False — servem só de camada de valor."""
    __tablename__ = "rookie_espn_value"

    id = db.Column(db.Integer, primary_key=True)
    season = db.Column(db.Integer, nullable=False)
    sleeper_player_id = db.Column(db.String(50), nullable=False, index=True)
    name = db.Column(db.String(120), default="")
    position = db.Column(db.String(10), default="")
    nfl_team = db.Column(db.String(10), default="")
    espn_raw = db.Column(db.Float, default=0.0)
    espn_adjusted = db.Column(db.Float, default=0.0)  # raw × 1.2 (ref value, não salário)
    in_class = db.Column(db.Boolean, default=False)   # DP3: membership da classe entrante
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("sleeper_player_id", "season",
                                          name="uq_rookie_espn_sid_season"),)

    def to_dict(self):
        return {
            "season": self.season,
            "sleeper_player_id": self.sleeper_player_id,
            "name": self.name,
            "position": self.position,
            "nfl_team": self.nfl_team,
            "espn_raw": self.espn_raw,
            "espn_adjusted": self.espn_adjusted,
            "in_class": self.in_class,
        }


# DP3 — posições elegíveis da classe entrante (K/DST seguem fora do board, mesma
# semântica do store E2: _classify_not_found_entry já exclui K/DST → $1 no confirm).
ENTERING_CLASS_POSITIONS = {"QB", "RB", "WR", "TE"}


def is_entering_class_member(info) -> bool:
    """DP3 — CRITÉRIO ÚNICO de "rookie da classe entrante" (D1+D3), aplicado a uma
    entrada do pool global do Sleeper. Primeiro predicado de classe do codebase —
    NÃO replicar (nem em JS/template): o único consumidor é a captura admin que
    materializa a membership em RookieEspnValue (postura P3 da REFINE).
    - `years_exp == 0`: único sinal do pool que captura a classe mais nova (F1:
      metadata.rookie_year atrasa uma classe; age/college/nfl_team nulos nos stubs).
    - posição skill (QB/RB/WR/TE): K/DST seguem excluídos (semântica E2 do store).
    - `active is True` E `status == 'Active'` (D3, conjunção deliberada): cada flag
      isolada tem um modo de falha — status='Active' com active=False são stubs
      fantasmas antigos cujo years_exp nunca avançou (falsos entrantes, ex. classe
      2017-18); active=True com status='Inactive' são cortados/limbo. A conjunção
      exclui ambos (148 skill entrantes no pool de referência, vs. 289 sem D3)."""
    if not isinstance(info, dict):
        return False
    return (info.get("years_exp") == 0
            and (info.get("position") or "").upper() in ENTERING_CLASS_POSITIONS
            and info.get("active") is True
            and info.get("status") == "Active")


def upsert_rookie_espn(season, sleeper_player_id, name, position, nfl_team,
                       espn_raw=None, espn_adjusted=None, in_class=None):
    """E2 + DP3 — upsert idempotente no store por (sleeper_id, season). Adiciona à
    sessão; o CHAMADOR faz commit. NÃO calcula salário (só guarda o ref value).
    Porta ÚNICA de escrita da tabela, com dois donos por campo (None = não tocar):
    - valores ESPN (import ESPN passa ambos; captura passa None → preserva o import);
    - `in_class` (captura passa True; import passa None → preserva a membership)."""
    sid = str(sleeper_player_id)
    row = RookieEspnValue.query.filter_by(
        sleeper_player_id=sid, season=season).first()
    if row:
        row.name, row.position, row.nfl_team = name or row.name, position or row.position, nfl_team or row.nfl_team
        if espn_raw is not None:
            row.espn_raw = espn_raw
        if espn_adjusted is not None:
            row.espn_adjusted = espn_adjusted
        if in_class is not None:
            row.in_class = in_class
    else:
        row = RookieEspnValue(
            season=season, sleeper_player_id=sid, name=name or "",
            position=position or "", nfl_team=nfl_team or "",
            espn_raw=espn_raw or 0.0, espn_adjusted=espn_adjusted or 0.0,
            in_class=bool(in_class))
        db.session.add(row)
    return row


def rookie_espn_adjusted(sleeper_player_id, season):
    """E2 — ref value (raw×1.2) do store para um sleeper_id+season, ou None."""
    if not sleeper_player_id:
        return None
    row = RookieEspnValue.query.filter_by(
        sleeper_player_id=str(sleeper_player_id), season=season).first()
    return row.espn_adjusted if row else None


def _rookie_backup_dir():
    """OFF26-23 — diretório dos backups do clear: dirname(DYNASTY_DB), o mesmo FS
    gravável/persistente do padrão F13 (volume /data no Render), nunca a raiz do app."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.environ.get("DYNASTY_DB", os.path.join(base_dir, "dynasty.db"))
    return os.path.dirname(os.path.abspath(db_path))


def clear_rookie_espn_store(season=None):
    """E2 — limpeza do store transitório pós-rookie-draft. season=None limpa tudo.
    Adiciona o delete à sessão; o CHAMADOR faz commit.

    OFF26-23 (poka-yoke nº 3): antes de apagar, grava BACKUP automático do que vai
    sumir — JSON com carimbo dentro do arquivo (padrão F13), no volume persistente.
    O "clear sem undo" deixou de ser verdade: `restore_rookie_espn_backup(path)`
    reidrata via a porta única. Camada ADICIONAL — não substitui o backup manual
    pré-operação dos runbooks.

    Retorna (n_removidos, backup_path) — path None quando não havia nada a apagar
    (nenhum arquivo é criado à toa)."""
    q = RookieEspnValue.query
    if season is not None:
        q = q.filter_by(season=season)
    rows = q.all()
    n = len(rows)
    backup_path = None
    if n:
        stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        backup_path = os.path.join(_rookie_backup_dir(),
                                   f"rookie_espn_backup_{stamp}.json")
        payload = {
            "cleared_at": datetime.utcnow().isoformat() + "Z",
            "season_filter": season,
            "count": n,
            "rows": [r.to_dict() for r in rows],
        }
        with open(backup_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=1)
        q.delete()
    return n, backup_path


def restore_rookie_espn_backup(path):
    """OFF26-23 — reidrata o store a partir de um backup do clear. Escreve SÓ via
    `upsert_rookie_espn` (a porta única — dois donos por campo preservados; o backup
    carrega valores E membership, então passa os dois). Chamador faz commit.
    Retorna nº de linhas reidratadas."""
    with open(path, encoding="utf-8") as f:
        payload = json.load(f)
    n = 0
    for r in payload.get("rows", []):
        upsert_rookie_espn(r["season"], r["sleeper_player_id"], r.get("name", ""),
                           r.get("position", ""), r.get("nfl_team", ""),
                           espn_raw=r.get("espn_raw"),
                           espn_adjusted=r.get("espn_adjusted"),
                           in_class=r.get("in_class"))
        n += 1
    return n


class EspnValueStore(db.Model):
    """E4-c — store CANÔNICO de valor ESPN, keyed por (sleeper_player_id, season).
    Fonte de verdade do valor ESPN; `Player.espn_ref_value` é cache materializado a partir
    daqui (a engine lê a COLUNA no objeto, nunca faz lookup — pureza preservada).
    Aceita sid de TEXTO (DST: 'IND','BUF'…). Criada aditivamente via db.create_all().
    E4-c-2 (depois) generaliza o RookieEspnValue p/ cá e aposenta o ESPNValue."""
    __tablename__ = "espn_value_store"

    id = db.Column(db.Integer, primary_key=True)
    sleeper_player_id = db.Column(db.String(50), nullable=False, index=True)
    season = db.Column(db.Integer, nullable=False)
    espn_raw = db.Column(db.Float, nullable=True)        # vazio em linhas backfilladas
    espn_adjusted = db.Column(db.Float, default=0.0)     # autoritativo (raw×1.2)
    is_final = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("sleeper_player_id", "season",
                                          name="uq_espn_value_store_sid_season"),)

    def to_dict(self):
        return {
            "sleeper_player_id": self.sleeper_player_id,
            "season": self.season,
            "espn_raw": self.espn_raw,
            "espn_adjusted": self.espn_adjusted,
            "is_final": self.is_final,
        }


def set_espn_value(player, season, adjusted, raw=None, is_final=False):
    """E4-c-1 — FONTE ÚNICA de escrita de valor ESPN: upsert no store canônico
    (sleeper_id, season) + materializa `player.espn_ref_value` (cache que a engine lê do
    objeto). Adiciona à sessão; o CHAMADOR faz commit. Idempotente (upsert por chave).
    Player sem sleeper_id → materializa só a coluna (store não gravado — degrada como hoje,
    ver E4-b). Nenhum caminho roteado deve escrever `espn_ref_value` por fora deste helper."""
    player.espn_ref_value = adjusted
    sid = getattr(player, "sleeper_player_id", None)
    # Store guarda só linhas com valor (>0), igual ao backfill; 0 = "sem valor ESPN"
    # materializa só a coluna. (Player sem sid também só materializa a coluna.)
    if not sid or not adjusted or adjusted <= 0:
        return player
    row = EspnValueStore.query.filter_by(sleeper_player_id=str(sid), season=season).first()
    if row:
        row.espn_adjusted = adjusted
        if raw is not None:
            row.espn_raw = raw
        row.is_final = is_final
    else:
        db.session.add(EspnValueStore(
            sleeper_player_id=str(sid), season=season,
            espn_raw=raw, espn_adjusted=adjusted, is_final=is_final))
    return player


def espn_store_adjusted(sleeper_player_id, season):
    """E4-c — leitura por id do store canônico (pré-roster/DP1). adjusted ou None."""
    if not sleeper_player_id:
        return None
    row = EspnValueStore.query.filter_by(
        sleeper_player_id=str(sleeper_player_id), season=season).first()
    return row.espn_adjusted if row else None


def espn_store_is_final(sleeper_player_id, season):
    """E4-c — marca provisório/definitivo do store (badge PROV do cap_projector)."""
    if not sleeper_player_id:
        return None
    row = EspnValueStore.query.filter_by(
        sleeper_player_id=str(sleeper_player_id), season=season).first()
    return row.is_final if row else None


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
            "imported_at": utc_iso(self.imported_at),  # M18: ISO 'Z'; cliente formata via formatLocalDT
            "season": self.season,
            "url_used": self.url_used,
            "status": self.status,
            "total_matched": self.total_matched,
            "total_approximate": self.total_approximate,
            "total_notfound": self.total_notfound,
        }


def latest_espn_import(season: int):
    """Import ESPN mais RECENTE registrado para `season` — qualquer status, ou None.

    É a LEITURA; quem julga é o `espn_final_import` abaixo. Existe separada porque o
    preview do rollover precisa exibir o candidato mesmo quando ele NÃO satisfaz o gate
    (o operador tem que ver com o que a mutação rodaria)."""
    return (ESPNImportLog.query.filter_by(season=season)
            .order_by(ESPNImportLog.imported_at.desc()).first())


def espn_final_import(season: int):
    """OFF26-25 — FONTE ÚNICA de *"a tabela ESPN DEFINITIVA desta season entrou"*.

    Devolve o log do import se ele qualificar, senão None (verdade booleana direta).

    ⛔ **O critério é o import MAIS RECENTE da season, não "existe algum final"** — a
    diferença é de correção, não de estilo: reimportar uma PROVISÓRIA depois da definitiva
    (para corrigir um match, cenário real da tela de review) **sobrescreve
    `player.espn_ref_value`** via `set_espn_value` e devolve o banco ao estado provisório,
    enquanto a linha `final` antiga continua no log. Com "existe algum final" o gate daria
    falso OK — uma trava que mente é pior que trava nenhuma.

    ⚠️ **Limite residual, declarado e NÃO resolvido aqui:** isto prova um EVENTO (o import
    desta season), não o ESTADO da coluna que o rollover lê. `set_espn_value` materializa
    `espn_ref_value` em QUALQUER import, inclusive de outra season — um import posterior
    para 2027 sobrescreveria a coluna sem tocar este predicado. Prova de estado exigiria
    varrer `EspnValueStore`/`ESPNValue` da season alvo; decisão do owner (14/08/2026) foi
    ficar no evento por ora. O caso comum — reimport da mesma season — está coberto.

    ⛔ Não recriar esta consulta inline. Consumidores: gate do passo 4 + recusa do
    `do_rollover` (routes/offseason.py), preview do rollover (routes/admin.py), selo PROV
    da `/league` e do `/team/<id>` (routes/league.py)."""
    log = latest_espn_import(season)
    return log if (log is not None and log.status == "final") else None


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
            "trade_date": utc_iso(self.trade_date),  # M18: ISO 'Z'; cliente formata via formatLocalDT
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
            "synced_at": utc_iso(self.synced_at),  # M18: ISO 'Z'; cliente formata via formatLocalDT
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
            "executed_at": utc_iso(self.executed_at) or None,  # M18: ISO 'Z'; cliente formata via formatLocalDT
            "executed_by_name": self.executor.name if self.executor else None,
            "result_hash": self.result_hash,
            "previous_audit_id": self.previous_audit_id,
            "reason": self.reason,
            "is_canonical": self.is_canonical,
        }


class CutDeclaration(db.Model):
    """OFF26-1 — declaração de CORTES editável por owner (lista de Player.id).

    Estado de trabalho PRÉ-lock: PRIVADO (D6 — só o próprio owner lê o conteúdo;
    nem admin lê a alheia; o admin só ESCREVE pelo time via /admin/declare, nunca
    lê). Keepers derivam por complemento (roster atual − cortes). Default de quem
    não declara = zero cortes (D2 — mantém todos). 1 row por (season, team).

    NÃO muta roster nem Sleeper — só registra a decisão. Congela no snapshot
    canônico (CutWindowAudit) no momento do lock/revelação (D7)."""
    __tablename__ = "cut_declarations"
    __table_args__ = (db.UniqueConstraint("season", "team_id", name="uq_cut_decl_season_team"),)

    id = db.Column(db.Integer, primary_key=True)
    season = db.Column(db.Integer, nullable=False)  # season da janela (= current_season pós-rollover)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=False)
    cut_ids_json = db.Column(db.Text, nullable=False, default="[]")  # [Player.id, ...]
    declared = db.Column(db.Boolean, default=False, nullable=False)  # owner confirmou (conta no "X/12")
    updated_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    team = db.relationship("Team", foreign_keys=[team_id])
    editor = db.relationship("User", foreign_keys=[updated_by])

    def cut_ids(self) -> list:
        import json as _json
        try:
            return [int(x) for x in _json.loads(self.cut_ids_json or "[]")]
        except (ValueError, TypeError):
            return []


class CutWindowAudit(db.Model):
    """OFF26-1 — snapshot auditável da janela de cortes no lock (molde M8 / LotteryAudit).

    Congela a declaração de cortes de TODOS os times no momento da revelação
    simultânea (D7). Times sem declaração entram como zero cortes (D2). Canônico +
    previous_audit_id (cadeia no replace) + reason (obrigatório no replace) + hash
    determinístico + executed_at/by. Verify re-deriva o hash do snapshot.

    NÃO escreve no Sleeper (isso é OFF26-8) nem materializa cortes no estado oficial
    do Manager (adequação/salário moram no Rollover e na fronteira do FA auction)."""
    __tablename__ = "cut_window_audit"

    id = db.Column(db.Integer, primary_key=True)
    season = db.Column(db.Integer, nullable=False)
    # [{team_id, team_name, cut_ids:[...], cut_names:[...], num_cuts, declared}, ...] — todos os times
    declarations_json = db.Column(db.Text, nullable=False)
    executed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    executed_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    result_hash = db.Column(db.String(64), nullable=False)  # SHA256 hex determinístico
    previous_audit_id = db.Column(db.Integer, db.ForeignKey("cut_window_audit.id"), nullable=True)
    reason = db.Column(db.Text, nullable=True)  # obrigatório quando previous_audit_id preenchido
    is_canonical = db.Column(db.Boolean, default=True, nullable=False)

    executor = db.relationship("User", foreign_keys=[executed_by])
    previous = db.relationship("CutWindowAudit", remote_side=[id], foreign_keys=[previous_audit_id])

    def to_dict(self):
        import json as _json
        return {
            "id": self.id,
            "season": self.season,
            "declarations": _json.loads(self.declarations_json),
            "executed_at": utc_iso(self.executed_at) or None,  # M18
            "executed_by_name": self.executor.name if self.executor else None,
            "result_hash": self.result_hash,
            "previous_audit_id": self.previous_audit_id,
            "reason": self.reason,
            "is_canonical": self.is_canonical,
        }


def compute_cut_snapshot_hash(declarations: list) -> str:
    """OFF26-1 — SHA256 determinístico do snapshot de cortes (molde M8 _compute_result_hash).

    Ordena por team_id e por cut_id para ser estável independente da ordem de
    inserção. Chave: 'team_id:cut_id,cut_id;team_id:...'."""
    import hashlib
    ordered = sorted(declarations, key=lambda d: d["team_id"])
    parts = []
    for d in ordered:
        cuts = ",".join(str(c) for c in sorted(d.get("cut_ids", [])))
        parts.append(f"{d['team_id']}:{cuts}")
    key = ";".join(parts)
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


# ── OFF26-10: a URNA do late drop (22/08) ────────────────────────────────────
#
# Tabelas PRÓPRIAS, não reuso das do OFF26-1, por três motivos concretos:
# (1) a cardinalidade é outra — UM drop ou passo, não uma lista de cortes;
# (2) a janela precisa de FLAG DE ESTADO PRÓPRIA (⛔ `cuts_window_open` não pode ser o
#     gate: ligá-la reabriria `POST /api/cuts/declaration`, e a porta única — exigência
#     da spec — viraria promessa de UI);
# (3) as tabelas da janela grande são a rede de regressão do mecanismo provado em
#     produção (ensaio de 06/08) e ficam congeladas.
# O que É reusado, literalmente, é o núcleo de integridade: `compute_cut_snapshot_hash`
# (mesma função, sem cópia) e o molde M8 do audit (canônico + cadeia + reason + verify).

class LateDropDeclaration(db.Model):
    """OFF26-10 (U1/U2/U4) — o bilhete: UM jogador do próprio roster, OU passo.

    `player_id = None` com `declared=True` é o **passo explícito** ("não vou dropar
    ninguém"); a AUSÊNCIA de row é o silêncio. Os dois têm o mesmo efeito revelado
    (U2 — "sem late drop"); a distinção existe só na trilha. 1 row por (season, team).

    Sigilo (U1, mais estrito que o da janela grande): nem o conteúdo nem a EXISTÊNCIA
    da declaração são visíveis a terceiros antes do lock — não há contagem agregada.
    NÃO muta roster nem Sleeper: a execução do drop revelado é manual, no Sleeper."""
    __tablename__ = "late_drop_declarations"
    __table_args__ = (db.UniqueConstraint("season", "team_id",
                                          name="uq_late_drop_season_team"),)

    id = db.Column(db.Integer, primary_key=True)
    season = db.Column(db.Integer, nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=True)
    declared = db.Column(db.Boolean, default=True, nullable=False)
    updated_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    team = db.relationship("Team", foreign_keys=[team_id])
    player = db.relationship("Player", foreign_keys=[player_id])
    editor = db.relationship("User", foreign_keys=[updated_by])

    def is_pass(self) -> bool:
        return self.player_id is None


class LateDropAudit(db.Model):
    """OFF26-10 (U5) — snapshot auditável da urna no lock (molde M8, igual ao da janela).

    Congela a declaração dos 12 times na revelação simultânea. Times sem declaração
    entram como passo (U2). Hash determinístico pela MESMA função da janela de cortes
    (`compute_cut_snapshot_hash`) — cada entrada carrega `cut_ids` com 0 ou 1 elemento,
    então o hash cobre exatamente **a lista de drops a executar**.

    A revelação NÃO executa nada: produz a lista que os owners aplicam manualmente no
    Sleeper (U7). Se um revelado não executar, a auditoria do OFF26-4 acusa."""
    __tablename__ = "late_drop_audit"

    id = db.Column(db.Integer, primary_key=True)
    season = db.Column(db.Integer, nullable=False)
    # [{team_id, team_name, cut_ids:[pid] | [], drop_id, drop_name, declared,
    #   passed, invalidated, invalid_reason}, ...] — todos os times
    declarations_json = db.Column(db.Text, nullable=False)
    executed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    executed_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    result_hash = db.Column(db.String(64), nullable=False)
    previous_audit_id = db.Column(db.Integer, db.ForeignKey("late_drop_audit.id"), nullable=True)
    reason = db.Column(db.Text, nullable=True)
    is_canonical = db.Column(db.Boolean, default=True, nullable=False)

    executor = db.relationship("User", foreign_keys=[executed_by])
    previous = db.relationship("LateDropAudit", remote_side=[id],
                               foreign_keys=[previous_audit_id])

    def to_dict(self):
        import json as _json
        return {
            "id": self.id,
            "season": self.season,
            "declarations": _json.loads(self.declarations_json),
            "executed_at": utc_iso(self.executed_at) or None,
            "executed_by_name": self.executor.name if self.executor else None,
            "result_hash": self.result_hash,
            "previous_audit_id": self.previous_audit_id,
            "reason": self.reason,
            "is_canonical": self.is_canonical,
        }


def is_first_round_rookie(player_id: int, season: int) -> bool:
    """OFF26-10 (U6) — o jogador foi draftado na 1ª RODADA do rookie draft desta season?

    Insumo da flag de admin "bloquear rookie de 1ª rodada no late drop", que nasce
    **OFF** — o regulamento é SILENCIOSO sobre proteger o rookie de 1ª contra drop
    (conferido no texto de 12/08/2025), e o código **não arbitra regra em disputa**.
    Fonte: `AuctionLog` (entry_type='rookie_draft', round_num=1) — a trilha que a porta
    canônica de aquisição escreve."""
    if not player_id:
        return False
    return AuctionLog.query.filter_by(
        player_id=player_id, season=season,
        entry_type="rookie_draft", round_num=1).first() is not None


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
