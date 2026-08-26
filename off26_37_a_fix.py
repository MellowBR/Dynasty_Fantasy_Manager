"""
off26_37_a_fix.py — runner ONE-SHOT do GRUPO A do OFF26-37 (reset de contrato, caso 3 da régua).

Aprovação do owner em 26/08/2026, sobre a régua canônica registrada no OFF26-37 e o parecer
MAN-CONTRATO-VIVO-F1 (commit `3669dce`). Estado dos 2 medido pelo owner em produção
(`/data/dynasty.db`) em 26/08/2026, **após** a execução do Grupo B (commit `32e4cc0`).

O QUE CORRIGE. Os dois tiveram o contrato **MORTO** (drop de intertemporada — não há waiver na
intertemporada — e não foram arrematados no leilão de 24/08) e foram **readquiridos como free
agent** em 25/08. Pelo **caso 3 da régua**, a reaquisição abre contrato **NOVO, ano 1**. O re-add
do sync é **uma linha** (`is_dropped = False`, [sync_sleeper.py:320](sync_sleeper.py#L320)) que
reativa **sem consultar contrato**: contagem, season, canal e salário voltaram **intactos** do
contrato morto.

⭐ **É o único ponto do arco com EFEITO DE CAIXA:** o Aiyuk carrega **$8** quando o devido é **$1**
(**−$7** na folha do AlexTheDawg). O Wicks já estava a $1 — o dano dele é só contagem/season/canal.

⛔ **POR QUE NÃO REUSA O RUNNER DO GRUPO B.** O Grupo B escreve **um** campo (`contract_year`) pela
porta de correção de contagem. Aqui são **QUATRO** campos numa transação — `contract_year=1`,
`contract_start_season=2026`, `acquisition_type='free_agent'` e `salary=$1` — e a porta que os
escreve junto é `models.record_acquisition`. Usar a porta do Grupo B aqui deixaria season, canal e
salário errados; usar esta lá reescreveria `css` de quem deve manter 2025.

⛔ **ARMADILHA OBRIGATÓRIA — o ESPN (medida na F1, e é requisito, não zelo).**
`record_acquisition` chama `set_espn_value(player, season, espn_adjusted)`, cuja **primeira linha**
é `player.espn_ref_value = adjusted` — **antes** da guarda `if not adjusted: return`
([models.py:764](models.py#L764)) — e o parâmetro tem **default `0.0`**. Chamar a porta sem
repassar o ESPN atual **ZERA** o valor do jogador, e todo projetado futuro passa a cair no piso.
Este runner **lê e repassa** o ESPN corrente de cada alvo, e a verificação pós-escrita **falha** se
o valor mudar. Há teste dedicado.

DUAS DECISÕES DO OWNER, executadas e não rediscutidas:

  1. **O runner grava evento próprio de timeline.** `record_acquisition` grava `SalaryHistory` +
     `AuctionLog`, mas **não** `PlayerHistory` (lacuna registrada em [[OFF26-34]]/[[OFF26-36]]) —
     sem evento próprio, o reset ficaria **invisível na timeline**, que é exatamente a
     invisibilidade que produziu o contrato-fantasma. O evento nasce com `ref` próprio
     (`fix:off26-37-a`), e o rebuild [[F8]] só apaga rows com `sleeper_event_ref IS NULL`
     ([sync_sleeper.py:1167](sync_sleeper.py#L1167)) — este sobrevive.
  2. **Rótulo off-label aceito:** a porta grava `AuctionLog.entry_type='fa_auction'` para um add de
     free agent ([[OFF26-34]]). Não bloqueia a F2.
  3. **Salário devido = $1**, o valor de entrada de free agent — e sai assim **por construção**:
     `year1_salary` manda `free_agent` para `_WAIVER_TYPES` ⇒ `MIN_SALARY`. ⛔ Contrato novo em ano
     1 **não valoriza**; nada aqui chama motor de valorização.

⛔ **A LISTA É CONGELADA — dois sids nomeados.** A F1 mediu que nenhum critério de estado no banco
separa alvo de não-alvo. Derivar por query é **defeito**. O que se deriva no dia é a
**elegibilidade**: a intertemporada está aberta e os cortes acontecem **direto no Sleeper**, de
modo que o `is_dropped` do banco pode estar atrasado de propósito. Sem API, não há escrita.

Uso (no Render Shell, com DYNASTY_DB=/data/dynasty.db no ambiente):

    # 0) BACKUP OBRIGATÓRIO (sem ele o --apply recusa escrever):
    sqlite3 /data/dynasty.db ".backup '/data/pre_off26_37_a_fix.db'"

    # 1) Conferência read-only (guarda + atual × devido + delta de cap + ESPN):
    python off26_37_a_fix.py --check

    # 2) Escrita (guarda → porta canônica + trilha → verificação → commit):
    python off26_37_a_fix.py --apply --backup /data/pre_off26_37_a_fix.db

    # Ensaio local: acrescentar --db <caminho de uma CÓPIA>
    # Inspeção sem rede (só no --check): --offline
"""

import argparse
import json
import os
import sqlite3
import sys
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
LEAGUE_ID = "1316547584378048512"

# ── Lista CONGELADA dos 2 (estado medido em produção em 26/08/2026, pós-Grupo B) ──────────────
# `owner` é o `sleeper_owner_id` do time no dia da medição — REGISTRO de identidade estável
# (⛔ nunca nome de time). Não entra na guarda: trade legítima entre a medição e a execução não
# invalida o reset, e a porta grava o time ATUAL do jogador (no-op quando não houve trade).
# `expected` é a guarda pré-escrita; `devido` é o alvo dos quatro campos.
# ⛔ `espn_ref_value` NÃO está na guarda de propósito: um import ESPN legítimo entre a medição e a
# execução mudaria o número, e o runner **preserva o que estiver lá** em vez de exigir um valor.
COHORT = [
    {
        "sid": "6803", "name": "Brandon Aiyuk", "owner": "698015187109773312",
        "team_hint": "AlexTheDawg",
        "cadeia": "drop 12/08/2026 (intertemporada, sem waiver) -> nao arrematado em 24/08 -> "
                  "re-add free agent 25/08 04:21",
        "expected": {
            "contract_year": 2, "contract_start_season": 2025,
            "acquisition_type": "fa_auction", "salary": 8.0,
            "needs_review": False, "is_dropped": False,
        },
    },
    {
        "sid": "9486", "name": "Dontayvion Wicks", "owner": "1131747074137272320",
        "team_hint": "Haliburton Time!",
        "cadeia": "drop 20/08/2026 20:29 (janela de cortes) -> nao arrematado -> "
                  "re-add free agent 25/08 13:12",
        "expected": {
            "contract_year": 2, "contract_start_season": 2025,
            "acquisition_type": "free_agent", "salary": 1.0,
            "needs_review": False, "is_dropped": False,
        },
    },
]

# O devido é o MESMO para os dois — é o caso 3 da régua, não uma tabela por jogador.
NEW_SEASON = 2026
NEW_ACQ = "free_agent"
NEW_YEAR = 1
NEW_SALARY = 1

EVENT_REF = "fix:off26-37-a"
# ⭐ `free_agent` é event_type CANÔNICO da timeline (rotulado "Free Agent (add)" nos dois
# templates) e é semanticamente o que aconteceu: aquisição de free agent em 2026. ⛔ Nenhum
# event_type novo — evitar rótulo cru na tela sem tocar template nenhum.
EVENT_TYPE = "free_agent"
REASON = ("Correcao OFF26-37 Grupo A aprovada pelo owner em 26/08/2026 (caso 3 da regua canonica: "
          "contrato morto no drop de intertemporada; a reaquisicao de 25/08 abre contrato NOVO, "
          "ano 1)")

# ⛔ ARMADILHA MEDIDA NESTA SESSÃO — a nota do AuctionLog NÃO pode ser longa.
# `record_acquisition` monta `notes + " [ref:<event_ref>]"` e só então **trunca em 200**
# ([models.py:445](models.py#L445)); `AuctionLog.notes` é `String(200)`. Com a `REASON` inteira
# (178 chars) o total dá 204 e **o token de idempotência é decepado** — a segunda execução não
# reconheceria o alvo como já registrado. Por isso a nota do log é CURTA, e a explicação completa
# vive no evento de `PlayerHistory` (coluna `Text`). `note_fits` prova isso antes de escrever.
AUCTION_NOTE = "OFF26-37-A: reset caso 3 da regua (contrato morto no drop)"
AUCTION_NOTE_MAX = 200

# ⛔ Casos negativos que a suíte fiscaliza: nenhum pode ser alcançado por plano, log ou trilha.
#    3163 = Goff (cy=3 CORRETO); os 11 do Grupo B já foram corrigidos pelo `off26_37_b_fix.py`.
GRUPO_B_SIDS = ["3451", "5870", "8259", "CHI", "CLE", "NE",
                "421", "8154", "9225", "10213", "11539"]
FORBIDDEN = {
    "3163": "Jared Goff - NAO e alvo: contrato de 2024 preservado (claim 12,3h, dentro da janela)",
    **{sid: "GRUPO B - ja corrigido por off26_37_b_fix.py (cy 3->2); contrato VIVO, nao resetar"
       for sid in GRUPO_B_SIDS},
}


# ── Núcleo puro ───────────────────────────────────────────────────────────────

def cohort_sids() -> list:
    return [t["sid"] for t in COHORT]


def target_event_ref(sid: str) -> str:
    """Token de idempotência POR ALVO — a porta de aquisição o grava em `AuctionLog.notes`
    como `[ref:...]`, e `acquisition_already_recorded` o lê. Por alvo, e não por execução,
    para que uma segunda rodada saiba exatamente quem já entrou."""
    return f"{EVENT_REF}:{sid}"


def note_fits(note: str, sid: str, limit: int = AUCTION_NOTE_MAX) -> bool:
    """O token `[ref:...]` sobrevive ao truncamento de `record_acquisition`? — puro.

    Reproduz exatamente o que a porta faz: concatena e corta em `limit`. Falso = a nota é longa
    demais e a idempotência morreria silenciosamente.
    """
    tag = f"[ref:{target_event_ref(sid)}]"
    return tag in ((note or "") + " " + tag).strip()[:limit]


def derive_eligible_by_roster(cohort: list, rostered_sids) -> tuple:
    """Cruza a lista congelada com os rosters vivos — puro, sem rede e sem DB.

    Quem não está rosterado ao vivo foi cortado no Sleeper depois da medição: o contrato que este
    runner abriria já teria morrido de novo. Fica de fora COM MOTIVO.
    """
    rostered = {str(s) for s in rostered_sids}
    targets, out = [], []
    for t in cohort:
        if t["sid"] in rostered:
            targets.append(t)
        else:
            out.append({"sleeper_player_id": t["sid"], "name": t["name"],
                        "reason": "nao esta em nenhum roster ao vivo (cortado no Sleeper) - "
                                  "o contrato a abrir ja teria morrido"})
    return targets, out


def plan_reset(cohort: list, states_by_sid: dict) -> tuple:
    """Decide, alvo a alvo, quem é elegível — puro, sem DB.

    ⭐ Reusa `contract_year_correction.guard_mismatches` (núcleo puro já testado) em vez de
    replicar a comparação campo a campo. `states_by_sid`: sid → LISTA de estados (dicts), lista
    para detectar sid ambíguo. Devolve (eligible_sids, skipped).
    """
    from contract_year_correction import guard_mismatches

    eligible, skipped = [], []
    for t in cohort:
        sid = t["sid"]
        rows = states_by_sid.get(sid) or []
        if not rows:
            skipped.append({"sleeper_player_id": sid, "reason": "nao encontrado no banco"})
            continue
        if len(rows) > 1:
            skipped.append({"sleeper_player_id": sid,
                            "reason": f"{len(rows)} linhas para o mesmo sleeper_player_id - ambiguo"})
            continue
        st = rows[0]
        if st.get("already_recorded"):
            skipped.append({"sleeper_player_id": sid,
                            "reason": f"ja registrado ({target_event_ref(sid)}) - nada a fazer"})
            continue
        mm = guard_mismatches(st, t["expected"])
        if mm:
            skipped.append({"sleeper_player_id": sid, "reason": "guarda: " + "; ".join(mm)})
            continue
        eligible.append(sid)
    return eligible, skipped


def due_state() -> dict:
    """Os quatro campos devidos — iguais para os dois (é o caso 3, não tabela por jogador)."""
    return {"contract_year": NEW_YEAR, "contract_start_season": NEW_SEASON,
            "acquisition_type": NEW_ACQ, "salary": float(NEW_SALARY)}


def cap_delta(states_by_sid: dict, sids: list) -> dict:
    """Delta de folha por time — puro. time → (soma do devido − soma do atual)."""
    out = {}
    for sid in sids:
        st = (states_by_sid.get(sid) or [{}])[0]
        team = st.get("team") or "?"
        out[team] = out.get(team, 0.0) + (float(NEW_SALARY) - float(st.get("salary") or 0.0))
    return out


def espn_violations(before: dict, after: dict) -> list:
    """⛔ O teste da armadilha: `espn_ref_value` NÃO pode mudar. Puro."""
    viol = []
    for sid, pre in before.items():
        post = after.get(sid)
        if post is None:
            viol.append(f"{sid}: ausente na releitura pos-escrita")
        elif float(pre or 0) != float(post or 0):
            viol.append(f"{sid}: espn_ref_value {pre} -> {post} (NAO pode mudar)")
    return viol


# ── Camada de IO ──────────────────────────────────────────────────────────────

def fetch_roster_owner_by_sid(league_id: str = LEAGUE_ID, timeout: int = 30) -> dict:
    """GET read-only dos rosters — sid → `owner_id` do roster que o carrega ao vivo.

    Inclui `reserve` (IR): jogador no IR segue sob contrato. Só leitura; nada é enviado.
    """
    url = f"https://api.sleeper.app/v1/league/{league_id}/rosters"
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        rosters = json.load(resp)
    by_sid = {}
    for ro in rosters:
        owner = str(ro.get("owner_id") or "")
        for key in ("players", "reserve", "taxi"):
            for pid in (ro.get(key) or []):
                by_sid[str(pid)] = owner
    return by_sid


def _db_path(cli_db: str = None) -> Path:
    """Caminho do banco, SEMPRE absoluto.

    ⛔ O `.resolve()` não é cosmético: com caminho RELATIVO o Flask-SQLAlchemy reescreve
    `sqlite:///dynasty.db` para dentro do `instance/` da app e **cria um banco vazio lá**
    (medido na F2B). Em produção o caminho vem absoluto por `DYNASTY_DB`."""
    return Path(cli_db or os.environ.get("DYNASTY_DB") or (BASE_DIR / "dynasty.db")).resolve()


def _make_app(db_path: Path):
    """App Flask mínimo — só o bind do banco. NÃO roda o boot do app.py (sem import CSV,
    sem sync, sem seed): correção cirúrgica não dispara efeito colateral."""
    from flask import Flask
    from models import db
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_path.as_posix()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    return app


def _snapshot_players(db_path: Path) -> dict:
    """Fotografa a tabela players inteira (todas as colunas) para o diff pós-escrita."""
    con = sqlite3.connect(str(db_path))
    cols = [r[1] for r in con.execute("PRAGMA table_info(players)")]
    rows = {r[0]: dict(zip(cols, r)) for r in
            con.execute(f"SELECT {', '.join(cols)} FROM players")}
    con.close()
    return rows


def _read_states(cohort: list) -> dict:
    """sid → LISTA de estados lidos do banco (lista para detectar sid ambíguo)."""
    from models import Player, acquisition_already_recorded

    ids = [t["sid"] for t in cohort]
    players = Player.query.filter(Player.sleeper_player_id.in_(ids)).all()
    out = {}
    for p in players:
        out.setdefault(p.sleeper_player_id, []).append({
            "player_id": p.id,
            "name": p.name,
            "team": p.team_rel.name if p.team_rel else "",
            "team_owner": p.team_rel.sleeper_owner_id if p.team_rel else "",
            "contract_year": p.contract_year,
            "contract_start_season": p.contract_start_season,
            "acquisition_type": p.acquisition_type,
            "salary": p.salary,
            "espn_ref_value": p.espn_ref_value,
            "needs_review": p.needs_review,
            "is_dropped": p.is_dropped,
            "already_recorded": acquisition_already_recorded(target_event_ref(p.sleeper_player_id)),
        })
    return out


# ── Relatórios ────────────────────────────────────────────────────────────────

def _report_header(source: str) -> None:
    print(f"\nLista CONGELADA: {len(COHORT)} alvos (Grupo A - reset de 4 campos, caso 3 da regua)")
    print(f"Cruzamento ao vivo: {source}")
    print(f"Fora por decisao: {len(FORBIDDEN)} sids "
          f"(3163 Goff + os {len(GRUPO_B_SIDS)} do Grupo B ja corrigidos)")


def _report_out(out: list) -> None:
    for o in out:
        print(f"  fora   {o['sleeper_player_id']:>6}  {o['name']:<22} {o['reason']}")


def _report_target(t: dict, st: dict, live_owner: str) -> None:
    due = due_state()
    print(f"\n  {t['sid']:>6}  {st['name']}  ({st['team']})")
    print(f"         cadeia: {t['cadeia']}")
    print(f"         {'campo':<24} {'atual':>12}  ->  {'devido':>12}")
    for campo in ("contract_year", "contract_start_season", "acquisition_type", "salary"):
        atual, devido = st.get(campo), due[campo]
        marca = "  " if str(atual) == str(devido) else " *"
        print(f"        {marca}{campo:<24} {str(atual):>12}  ->  {str(devido):>12}")
    print(f"         {'espn_ref_value':<24} {str(st['espn_ref_value']):>12}  ->  "
          f"{str(st['espn_ref_value']):>12}   (PRESERVADO - nunca zerar)")
    if live_owner and st.get("team_owner") and live_owner != st["team_owner"]:
        print(f"        ⚠️  time ao vivo (owner {live_owner}) != time no banco "
              f"(owner {st['team_owner']}) - o banco esta atrasado sobre membership; "
              f"a trilha sairia com o time do banco")
    elif t["owner"] and st.get("team_owner") and t["owner"] != st["team_owner"]:
        print(f"        ⚠️  time no banco (owner {st['team_owner']}) != owner da medicao "
              f"({t['owner']} = {t['team_hint']}) - trade posterior; o reset segue valido")


# ── Comandos ──────────────────────────────────────────────────────────────────

def _resolve_live(offline: bool) -> tuple:
    if offline:
        return {sid: "" for sid in cohort_sids()}, "SEM cruzamento ao vivo - so a guarda filtra"
    by_sid = fetch_roster_owner_by_sid()
    return by_sid, f"rosters ao vivo do Sleeper ({len(by_sid)} jogadores rosterados)"


def cmd_check(db_path: Path, offline: bool = False) -> int:
    """Read-only: guarda + os quatro campos atual × devido + delta de cap + ESPN."""
    try:
        owner_by_sid, source = _resolve_live(offline)
    except Exception as exc:
        print(f"⛔ Falha ao ler os rosters ao vivo ({exc.__class__.__name__}: {exc}).")
        print("   Use --offline para inspecionar sem rede (nao vale para --apply).")
        return 1

    if offline:
        print("⚠️  MODO OFFLINE - lista NAO cruzada com os rosters ao vivo. So para inspecao.")
    _report_header(source)

    targets, out = derive_eligible_by_roster(COHORT, owner_by_sid.keys())
    _report_out(out)

    app = _make_app(db_path)
    with app.app_context():
        print(f"\nBanco: {db_path}")
        states = _read_states(targets)
        eligible, skipped = plan_reset(targets, states)

        # Os quatro campos atual × devido saem para TODO alvo — inclusive o pulado: é a
        # conferência que o owner lê antes de decidir, não um efeito colateral da elegibilidade.
        motivo_by_sid = {s["sleeper_player_id"]: s["reason"] for s in skipped}
        for t in targets:
            sid = t["sid"]
            if states.get(sid):
                _report_target(t, states[sid][0], owner_by_sid.get(sid, ""))
                veredito = "ELEGIVEL" if sid in eligible else f"PULADO - {motivo_by_sid.get(sid, '')}"
                print(f"         veredito: {veredito}")
            else:
                print(f"\n  PULADO {sid:>6}  {t['name']:<22} "
                      f"{motivo_by_sid.get(sid, 'nao encontrado no banco')}")

        print("\nDelta de folha (por time):")
        deltas = cap_delta(states, eligible)
        if not deltas:
            print("  (nenhum elegivel)")
        for team, d in sorted(deltas.items()):
            print(f"  {team:<28} {d:+.0f}")

        # Prova de que o salário devido sai da porta canônica, e não de conta feita aqui.
        from salary_engine import year1_salary
        motor = {sid: year1_salary(NEW_ACQ, 0.0, states[sid][0]["espn_ref_value"])
                 for sid in eligible}
        ruim = {sid: v for sid, v in motor.items() if v != NEW_SALARY}
        print(f"\nSalario ano 1 pelo motor ({NEW_ACQ}): "
              f"{'OK - $' + str(NEW_SALARY) + ' em todos' if not ruim else 'DIVERGENTE: ' + str(ruim)}")

    all_ok = len(eligible) == len(COHORT) and not ruim
    print(f"\n--check: {'OK - ' + str(len(eligible)) + '/' + str(len(COHORT)) + ' elegiveis' if all_ok else 'ATENCAO - ver acima'}")
    return 0 if all_ok else 1


def _verify_backup(backup: Path, db_path: Path) -> bool:
    if not backup.exists():
        print(f"⛔ Backup nao encontrado: {backup}")
        return False
    b, d = backup.stat().st_size, db_path.stat().st_size
    if b < 0.5 * d:
        print(f"⛔ Backup implausivel: {b} bytes contra {d} do banco alvo")
        return False
    print(f"Backup conferido: {backup} ({b} bytes; banco alvo {d} bytes)")
    return True


def cmd_apply(db_path: Path, backup: Path) -> int:
    """Guarda → porta canônica + trilha própria → verificação pós-escrita → commit."""
    from models import db, Player, PlayerHistory, record_acquisition

    if not _verify_backup(backup, db_path):
        return 1

    # ⛔ Sem cruzamento ao vivo não há escrita: o banco pode estar congelado ou atrasado, e o
    # Sleeper é a autoridade sobre quem ainda está rosterado.
    try:
        owner_by_sid, source = _resolve_live(offline=False)
    except Exception as exc:
        print(f"⛔ Falha ao ler os rosters ao vivo do Sleeper ({exc.__class__.__name__}: {exc}).")
        print("   Nenhuma escrita. A elegibilidade so e valida cruzada ao vivo - reagende.")
        return 1
    _report_header(source)

    targets, out = derive_eligible_by_roster(COHORT, owner_by_sid.keys())
    _report_out(out)

    pre = _snapshot_players(db_path)
    applied, espn_before = [], {}

    app = _make_app(db_path)
    with app.app_context():
        states = _read_states(targets)
        eligible, skipped = plan_reset(targets, states)
        for s in skipped:
            nome = next((t["name"] for t in COHORT if t["sid"] == s["sleeper_player_id"]), "?")
            print(f"  PULADO {s['sleeper_player_id']:>6}  {nome:<22} {s['reason']}")

        if not eligible:
            db.session.rollback()
            print("\nNada elegivel - nenhuma escrita. (Ja resetado, ou estado divergente.)")
            return 1

        for sid in eligible:
            st = states[sid][0]
            player = db.session.get(Player, st["player_id"])
            team = player.team_rel
            if team is None:
                db.session.rollback()
                print(f"⛔ {sid} sem time no banco - a porta exige time. Nada escrito.")
                return 1

            if not note_fits(AUCTION_NOTE, sid):
                db.session.rollback()
                print(f"⛔ {sid}: a nota do AuctionLog e longa demais e o token [ref:] seria "
                      f"truncado - a idempotencia morreria. Nada escrito.")
                return 1

            espn_atual = player.espn_ref_value      # ⛔ o valor que TEM de sobreviver
            espn_before[sid] = espn_atual
            antes = {"contract_year": player.contract_year,
                     "contract_start_season": player.contract_start_season,
                     "acquisition_type": player.acquisition_type,
                     "salary": player.salary}

            _p, salary = record_acquisition(
                team=team,
                acquisition_type=NEW_ACQ,
                season=NEW_SEASON,
                player=player,
                value_paid=0.0,
                espn_adjusted=espn_atual,          # ⛔ preserva o ESPN (armadilha da F1)
                sleeper_player_id=player.sleeper_player_id,
                event_ref=target_event_ref(sid),
                notes=AUCTION_NOTE,                # ⛔ curta: o token não pode ser truncado
            )
            if int(salary) != NEW_SALARY:
                db.session.rollback()
                print(f"⛔ {sid}: porta devolveu salario ${salary} (esperado ${NEW_SALARY}) - "
                      f"rollback, nada escrito.")
                return 1

            # Decisão 1 do owner: evento PRÓPRIO de timeline, com ref imune ao rebuild F8.
            db.session.add(PlayerHistory(
                player_id=player.id,
                season=NEW_SEASON,
                team_name=team.name,
                event_type=EVENT_TYPE,
                salary=salary,
                contract_year=NEW_YEAR,
                notes=(f"{REASON}: contrato resetado - ano {antes['contract_year']}->{NEW_YEAR}, "
                       f"inicio {antes['contract_start_season']}->{NEW_SEASON}, "
                       f"canal {antes['acquisition_type']}->{NEW_ACQ}, "
                       f"salario ${int(antes['salary'])}->${int(salary)}")[:500],
                sleeper_event_ref=EVENT_REF,
            ))
            applied.append({"sid": sid, "player_id": player.id, "name": player.name,
                            "team": team.name, "antes": antes, "salary": salary})
            print(f"  ok     {sid:>6}  {player.name:<22} {team.name[:26]:<26} "
                  f"ano {antes['contract_year']}->{NEW_YEAR}  "
                  f"css {antes['contract_start_season']}->{NEW_SEASON}  "
                  f"{antes['acquisition_type']}->{NEW_ACQ}  "
                  f"${int(antes['salary'])}->${int(salary)}")

        # Verificação in-transação antes do commit.
        bad = []
        for a in applied:
            p = db.session.get(Player, a["player_id"])
            if (p.contract_year, p.contract_start_season, p.acquisition_type, int(p.salary)) != \
               (NEW_YEAR, NEW_SEASON, NEW_ACQ, NEW_SALARY):
                bad.append(a["sid"])
            if float(p.espn_ref_value or 0) != float(espn_before[a["sid"]] or 0):
                bad.append(f"{a['sid']} (espn zerado/alterado)")
        if bad:
            db.session.rollback()
            print(f"⛔ Releitura in-transacao divergente ({bad}) - rollback, nada escrito.")
            return 1
        db.session.commit()

    # ── Verificação pós-commit por conexão independente (raw sqlite) ──────────
    post = _snapshot_players(db_path)
    applied_ids = {a["player_id"] for a in applied}
    errors = []

    if set(pre) != set(post):
        errors.append(f"linhas criadas/apagadas em players: {sorted(set(pre) ^ set(post))}")
    changed = {pid for pid in pre if pid in post
               and any(pre[pid][c] != post[pid][c] for c in pre[pid])}
    if changed != applied_ids:
        errors.append(f"linhas alteradas != elegiveis: {sorted(changed ^ applied_ids)}")

    permitidas = {"contract_year", "contract_start_season", "acquisition_type",
                  "salary", "updated_at"}
    espn_after = {}
    for a in applied:
        pid = a["player_id"]
        diff_cols = {c for c in pre[pid] if pre[pid][c] != post[pid][c]}
        if not diff_cols <= permitidas:
            errors.append(f"player {pid}: colunas alteradas alem das devidas: {sorted(diff_cols)}")
        alvo = (post[pid]["contract_year"], post[pid]["contract_start_season"],
                post[pid]["acquisition_type"], int(post[pid]["salary"]))
        if alvo != (NEW_YEAR, NEW_SEASON, NEW_ACQ, NEW_SALARY):
            errors.append(f"player {pid}: estado final {alvo} != devido "
                          f"{(NEW_YEAR, NEW_SEASON, NEW_ACQ, NEW_SALARY)}")
        espn_after[a["sid"]] = post[pid]["espn_ref_value"]
    errors.extend(f"ESPN: {v}" for v in espn_violations(espn_before, espn_after))

    con = sqlite3.connect(str(db_path))
    trail = con.execute(
        "SELECT COUNT(*) FROM player_history WHERE event_type=? AND sleeper_event_ref=?",
        (EVENT_TYPE, EVENT_REF)).fetchone()[0]
    logs = con.execute(
        "SELECT COUNT(*) FROM auction_log WHERE notes LIKE ?", (f"%{EVENT_REF}:%",)).fetchone()[0]
    con.close()
    if trail != len(applied):
        errors.append(f"trilha: {trail} linhas em player_history (esperado {len(applied)})")
    if logs != len(applied):
        errors.append(f"auction_log: {logs} linhas com o ref (esperado {len(applied)})")

    print(f"\nVerificacao pos-escrita: {len(applied)} resetados; {len(changed)} linhas alteradas; "
          f"{trail} linhas de trilha; {logs} no auction_log; "
          f"ESPN {'PRESERVADO' if not espn_violations(espn_before, espn_after) else 'ALTERADO'}.")
    for a in applied:
        print(f"  {a['sid']:>6} {a['name']:<22} espn {espn_before[a['sid']]} -> "
              f"{espn_after.get(a['sid'])}")
    if errors:
        print("⛔ FALHAS DE VERIFICACAO (o commit JA ocorreu - avaliar restore do backup):")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("✅ OK - os 4 campos nos devidos; ESPN preservado; trilha e log completos; "
          "nenhuma outra linha tocada.")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="OFF26-37 Grupo A: reset de contrato (caso 3 da regua) nos 2 readquiridos")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true",
                      help="read-only: guarda + atual x devido + delta de cap + ESPN")
    mode.add_argument("--apply", action="store_true", help="escreve (exige --backup conferivel)")
    ap.add_argument("--backup", help="caminho do backup feito ANTES (obrigatorio no --apply)")
    ap.add_argument("--db", help="override do banco (ensaio); padrao: env DYNASTY_DB")
    ap.add_argument("--offline", action="store_true",
                    help="--check apenas: inspeciona sem cruzar com os rosters ao vivo")
    args = ap.parse_args(argv)

    db_path = _db_path(args.db)
    if not db_path.exists():
        print(f"⛔ Banco nao encontrado: {db_path}")
        return 1
    if args.apply and args.offline:
        print("⛔ --offline nao vale no --apply: a elegibilidade so e valida cruzada com os "
              "rosters ao vivo (o banco pode estar congelado ou atrasado). Nenhuma escrita.")
        return 1
    if args.apply and not args.backup:
        print("⛔ --apply exige --backup <caminho do backup feito antes>. Nenhuma escrita.")
        return 1
    return cmd_check(db_path, args.offline) if args.check else cmd_apply(db_path, Path(args.backup))


if __name__ == "__main__":
    sys.exit(main())
