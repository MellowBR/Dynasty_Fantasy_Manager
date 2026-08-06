"""
contract_year_correction.py — porta canônica de correção de `contract_year` (OFF26-20-FIX).

Preenche o vão declarado no MAN-OFF26-20-CANAL: `correct_player_salary` (models.py) corrige
salário, e o approve do M2 só edita `contract_year` de quem tem `needs_review=True`. Não havia
porta com trilha para corrigir `contract_year` de jogador já aprovado. Esta é a porta, no molde
do M2: escrita do campo + `PlayerHistory` (old→new nas notes) **na mesma transação** — a porta
NÃO comita; o chamador decide (mesmo contrato do `correct_player_salary`).

Mesma separação do salary_engine/keeper_audit:
  * `guard_mismatches` / `plan_correction` — núcleo PURO (sem DB, sem Flask): recebe estados
    como dicts, devolve elegíveis e pulados com motivo. É o que os testes exercem.
  * `apply_contract_year_correction` — camada ORM: consulta por `sleeper_player_id`, revalida
    a guarda linha a linha e encena as escritas na sessão.

Guarda pré-escrita (inegociável): cada jogador só é corrigido se o estado lido no banco casar
EXATAMENTE com o estado esperado declarado pelo chamador. Linha que não case é pulada e
reportada — nunca corrigida por força. `sleeper_player_id` é SEMPRE string (as DEFs usam sigla,
'DET'/'HOU'/... — a armadilha conhecida da coerção a inteiro).
"""

EVENT_TYPE = "contract_year_correction"


# ── Núcleo puro ───────────────────────────────────────────────────────────────

def guard_mismatches(state: dict, expected: dict) -> list:
    """Compara o estado lido com o esperado, campo a campo; devolve as divergências.

    Lista vazia = elegível. Normalização por tipo do valor esperado: bool compara como
    bool (0/1 do SQL ≡ False/True do ORM), numérico como float, string após strip.
    """
    mismatches = []
    for field, want in expected.items():
        got = state.get(field)
        if isinstance(want, bool):
            equal = bool(got) == want
        elif isinstance(want, (int, float)):
            equal = got is not None and float(got) == float(want)
        else:
            equal = str(got or "").strip() == str(want).strip()
        if not equal:
            mismatches.append(f"{field}={got!r} (esperado {want!r})")
    return mismatches


def plan_correction(target_ids: list, rows_by_id: dict, expected: dict) -> tuple:
    """Decide, id a id, quem é elegível e quem é pulado (com motivo).

    target_ids: sleeper_player_ids (strings) na ordem pedida.
    rows_by_id: sleeper_player_id → lista de estados (dicts) encontrados no banco.
    Retorna (eligible_ids, skipped) — skipped = [{"sleeper_player_id", "reason"}, ...].
    Pula: id ausente do banco, id ambíguo (mais de uma linha viva) e guarda divergente.
    """
    eligible, skipped = [], []
    for sid in target_ids:
        matches = rows_by_id.get(sid, [])
        if not matches:
            skipped.append({"sleeper_player_id": sid,
                            "reason": "não encontrado no banco"})
        elif len(matches) > 1:
            skipped.append({"sleeper_player_id": sid,
                            "reason": f"{len(matches)} linhas para o mesmo sleeper_player_id — ambíguo"})
        else:
            mm = guard_mismatches(matches[0], expected)
            if mm:
                skipped.append({"sleeper_player_id": sid,
                                "reason": "guarda: " + "; ".join(mm)})
            else:
                eligible.append(sid)
    return eligible, skipped


def _player_state(p) -> dict:
    """Projeta um Player (ou duck-type) nos campos que a guarda conhece."""
    return {
        "contract_year": p.contract_year,
        "contract_start_season": p.contract_start_season,
        "acquisition_type": p.acquisition_type,
        "needs_review": p.needs_review,
        "is_dropped": p.is_dropped,
    }


# ── Camada ORM ────────────────────────────────────────────────────────────────

def apply_contract_year_correction(sleeper_ids: list, *, expected: dict, new_year: int,
                                   reason: str, event_ref: str, season: int = None) -> dict:
    """Encena a correção na sessão ativa — escrita + trilha atômicas, SEM commit.

    Para cada id elegível: `Player.contract_year = new_year` + `PlayerHistory` com
    old→new nas notes e `sleeper_event_ref=event_ref` (a UNIQUE de player_history
    barra dupla execução do mesmo event_ref). O chamador comita — ou dá rollback e
    nada acontece (escrita e trilha vivem ou morrem juntas).

    Retorna {"applied": [{sleeper_player_id, player_id, name, team, old, new}, ...],
             "skipped": [{sleeper_player_id, reason}, ...]}.
    """
    from datetime import datetime
    from models import db, Player, PlayerHistory, get_config, CURRENT_SEASON

    target_ids = [str(s) for s in sleeper_ids]
    players = (Player.query
               .filter(Player.sleeper_player_id.in_(target_ids))
               .all())
    rows_by_id = {}
    for p in players:
        rows_by_id.setdefault(p.sleeper_player_id, []).append(p)

    eligible, skipped = plan_correction(
        target_ids,
        {sid: [_player_state(p) for p in ps] for sid, ps in rows_by_id.items()},
        expected,
    )

    if season is None:
        season = int(get_config("current_season", CURRENT_SEASON))

    applied = []
    for sid in eligible:
        player = rows_by_id[sid][0]
        old = player.contract_year
        player.contract_year = new_year
        player.updated_at = datetime.utcnow()
        team_name = player.team_rel.name if player.team_rel else ""
        db.session.add(PlayerHistory(
            player_id=player.id,
            season=season,
            team_name=team_name,
            event_type=EVENT_TYPE,
            salary=player.salary,
            contract_year=new_year,
            notes=f"{reason}: contract_year {old} -> {new_year}",
            sleeper_event_ref=event_ref,
        ))
        applied.append({
            "sleeper_player_id": sid,
            "player_id": player.id,
            "name": player.name,
            "team": team_name,
            "old": old,
            "new": new_year,
        })

    return {"applied": applied, "skipped": skipped}
