"""
salary_engine.py — All salary cap rule logic for Dynasty SB.

IMPORTANT: All functions that accept an ESPN value expect the ALREADY-ADJUSTED
value (raw × 1.2), as stored in Player.espn_ref_value in the DB.
Callers that receive raw ESPN from external input (e.g. UI forms) must multiply
by 1.2 before passing here.

Rules:
  - Cap = $200.  Min salary = $1.  Always round DOWN (int()).
  - Contract = 4 years.

Year 1 salary:
  auction_draft           → value paid at auction
  rookie_draft            → floor(espn_adj), min $1
  waiver / free_agent     → $1

Note: "keeper" deprecated as acquisition_type (F6, 22/04/2026) — players mantidos
são auction_draft. O termo "keeper" permanece no contexto do draft_budget()
como sinônimo de "active roster pre-FA auction".

Year 2+ — VALORIZAÇÃO RULE:
  salary = MAX(prev_salary, floor(0.5 × espn_adj)), min $1

Exception — Waiver/FA Year 2:
  salary = floor(0.80 × espn_adj), min $1

Years 3–4 waiver/FA: normal VALORIZAÇÃO.

Contract renewal (after Year 4):
  New 4-yr contract.
  Year 1 = floor(espn_adj), min $1.
  Years 2–4: VALORIZAÇÃO.

Draft budget = $200 − sum(keeper salaries)
Must have at least $1 per empty roster spot (22 − keepers).
"""

SALARY_CAP = 200
MAX_ROSTER = 22
MIN_SALARY = 1
CONTRACT_LENGTH = 4

_WAIVER_TYPES  = {"waiver", "free_agent", "fa"}
_AUCTION_TYPES = {"auction_draft"}
_ROOKIE_TYPES  = {"rookie_draft"}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _floor(value: float) -> int:
    """Floor to int, enforce minimum salary of $1."""
    return max(MIN_SALARY, int(value))


def _adj(espn_adj: float) -> float:
    """Return the already-adjusted ESPN value, guarding against None."""
    return espn_adj or 0.0


# ── Core rules ────────────────────────────────────────────────────────────────

def year1_salary(acquisition_type: str, value_paid: float, espn_adj: float) -> int:
    """
    Compute Year 1 salary.
    espn_adj: already-adjusted ESPN value (raw × 1.2).
    """
    acq = (acquisition_type or "unknown").lower().strip()
    if acq in _ROOKIE_TYPES:
        return _floor(_adj(espn_adj))
    elif acq in _WAIVER_TYPES:
        return MIN_SALARY
    else:
        return max(MIN_SALARY, int(float(value_paid or MIN_SALARY)))


def valorization_rule(prev_salary: float, espn_adj: float) -> int:
    """
    VALORIZAÇÃO (Year 2+):
    MAX(prev_salary, floor(0.5 × espn_adj)), min $1
    espn_adj: already-adjusted ESPN value (raw × 1.2).
    """
    floor_val = int(0.5 * _adj(espn_adj))
    return max(MIN_SALARY, max(int(prev_salary), floor_val))


def waiver_year2_salary(espn_adj: float) -> int:
    """
    Waiver/FA Year 2: floor(0.80 × espn_adj), min $1
    espn_adj: already-adjusted ESPN value (raw × 1.2).
    """
    return _floor(0.80 * _adj(espn_adj))


# ── Main calculator ───────────────────────────────────────────────────────────

def compute_salary_for_year(
    acq_type: str,
    year1_value: float,
    espn: float,
    target_yr: int,
) -> int:
    """
    Compute salary for any contract year (1–N).
    espn: already-adjusted ESPN value (raw × 1.2) as stored in DB.
    Years > 4 trigger contract renewal cycles automatically.
    """
    acq = (acq_type or "unknown").lower().strip()
    e = _adj(espn)

    # Renewal cycle: year 5 = new year 1, etc.
    if target_yr > CONTRACT_LENGTH:
        eff = (target_yr - 1) % CONTRACT_LENGTH + 1
        if eff == 1:
            return _floor(e)
        # Renewal years 2–4: VALORIZAÇÃO from renewal year 1
        prev = _floor(e)
        for y in range(2, eff + 1):
            prev = valorization_rule(prev, e)
        return prev

    if target_yr <= 1:
        return year1_salary(acq, year1_value, e)

    # Build iteratively from year 1
    prev = year1_salary(acq, year1_value, e)
    for yr in range(2, target_yr + 1):
        if acq in _WAIVER_TYPES and yr == 2:
            prev = waiver_year2_salary(e)
        else:
            prev = valorization_rule(prev, e)
    return prev


def full_contract_table(
    acquisition_type: str,
    year1_value_paid: float,
    espn_adj: float,
    current_contract_year: int = 1,
) -> list:
    """
    Return a 5-row table: years 1–4 + renewal Year 1.
    espn_adj: already-adjusted ESPN value (raw × 1.2).
    Each row: {year, label, salary, is_current, is_renewal}
    """
    e = _adj(espn_adj)
    rows = []
    for yr in range(1, CONTRACT_LENGTH + 1):
        sal = compute_salary_for_year(acquisition_type, year1_value_paid, e, yr)
        rows.append({
            "year": yr,
            "label": f"Ano {yr}/{CONTRACT_LENGTH}",
            "salary": sal,
            "is_current": yr == current_contract_year,
            "is_renewal": False,
        })

    renewal_sal = _floor(e)
    rows.append({
        "year": 5,
        "label": "Renovação (Ano 1/4)",
        "salary": renewal_sal,
        "is_current": False,
        "is_renewal": True,
    })
    return rows


def project_next_salary(player) -> int:
    """
    Project a player's salary for next season (contract_year + 1).
    Uses player.espn_ref_value (already adjusted) directly.
    """
    next_yr = player.contract_year + 1
    espn = _adj(player.espn_ref_value)
    acq   = (player.acquisition_type or "unknown").lower()

    if not espn:
        return int(player.salary)

    if next_yr > CONTRACT_LENGTH:
        return _floor(espn)

    if acq in _WAIVER_TYPES and next_yr == 2:
        return waiver_year2_salary(espn)

    return valorization_rule(player.salary, espn)


def apply_season_rollover(player, new_espn_adj: float = None) -> tuple:
    """
    Compute new salary + contract year for season rollover.
    new_espn_adj: already-adjusted ESPN value to use (overrides player's current value).
    Returns (new_salary, new_contract_year, rule_description).
    Does NOT mutate the player — caller applies the values.
    """
    espn = _adj(new_espn_adj if new_espn_adj is not None else player.espn_ref_value)
    acq = (player.acquisition_type or "unknown").lower()
    next_yr = player.contract_year + 1

    if next_yr > CONTRACT_LENGTH:
        new_sal = _floor(espn)
        rule = f"Renovação: floor(ESPN_adj={espn:.1f})=${new_sal}"
        return new_sal, 1, rule

    if acq in _WAIVER_TYPES and next_yr == 2:
        new_sal = waiver_year2_salary(espn)
        rule = f"Waiver Ano 2: floor(0.80×{espn:.1f})=${new_sal}"
        return new_sal, next_yr, rule

    new_sal = valorization_rule(player.salary, espn)
    rule = f"VALORIZAÇÃO: MAX(${int(player.salary)}, floor(0.5×{espn:.1f}))=${new_sal}"
    return new_sal, next_yr, rule


def draft_budget(team_players: list) -> dict:
    """Calculate draft budget given a list of player objects."""
    active = [p for p in team_players if not p.is_dropped]
    keeper_salaries = sum(p.salary for p in active)
    num_keepers = len(active)
    empty_spots = max(0, MAX_ROSTER - num_keepers)
    min_required = empty_spots * MIN_SALARY
    raw_budget = SALARY_CAP - keeper_salaries
    usable = raw_budget - min_required

    return {
        "salary_cap": SALARY_CAP,
        "keeper_salaries": keeper_salaries,
        "num_keepers": num_keepers,
        "empty_spots": empty_spots,
        "min_required_for_spots": min_required,
        "raw_budget": raw_budget,
        "usable_draft_budget": usable,
        "over_cap": keeper_salaries > SALARY_CAP,
        "insufficient_budget": usable < 0,
    }
