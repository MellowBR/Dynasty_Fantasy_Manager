"""
wv1_fix_coorte.py — runner ONE-SHOT da correção MAN-WV1-FIX-COORTE.

Aprovação do owner em 19/08/2026, sobre o parecer MAN-WV1-FIX-COORTE (padrão MAN-METH-2).

O QUE CORRIGE. A F1 do WV1 + a sonda VERIFY-PROD (19/08) mediram 18 jogadores adquiridos por
**claim de waiver FORA da janela aberta pelo drop** em 2025 — aquisição NOVA sob QUALQUER
leitura da regra (estrita ou lock-aware; a decisão pendente só move os 17 ambíguos, que estão
FORA deste escopo). Aquisição nova ⇒ ano 1 = 2025 (o ano do claim), sem valor ($1) ⇒ **2026 é
ano 2**. O banco conta a partir do contrato MORTO (pré-drop) e o rollover de 17/08 incrementou
o número errado: hoje marcam **ano 3**. Dois deles carregam ainda **salário $2** onde a regra de
ano 2 de waiver/FA — `floor(0,8 × ESPN)`, piso $1 (6.6 + 6.10) — dá **$1**.

⛔ **`contract_start_season` NÃO é escrito — já está correto (2025) e foi medido assim.** O
passo 6 do rebuild F8 reconcilia `contract_start_season` e `acquisition_type` pelo último evento
ativo (o claim de 2025); o que ele NÃO toca é `contract_year`, e é exatamente aí que mora o erro.
Isso elimina a única mutação que não teria porta canônica: o runner escreve só
`contract_year` (porta `contract_year_correction`) e `salary` (porta `correct_player_salary`).

PRAZO — e por que este runner roda ANTES do lock, ao contrário do `off26_32_fix.py`. A janela
de cortes fecha em 20/08 e os owners decidem keeper com o que a tela mostra: "Ano 2/4 a $1"
(3 anos restantes) é ativo diferente de "Ano 3/4 a $2". O OFF26-32 roda **pós-lock** porque a
lista dele é derivada AO VIVO e corrigir quem está prestes a ser cortado é escrever em contrato
morto. Aqui a lista é **CONGELADA** (18 sids explícitos) — o resultado não depende do estado dos
rosters, então rodar cedo é seguro e é a única forma de o dado chegar a tempo da decisão.
⛔ Lista congelada, **nunca** filtro por `acquisition_type`: esse campo é reescrito pelo F8 e foi
exatamente assim que o censo do OFF26-32 perdeu membros (ver OFF26-33).

DECISÕES DO OWNER (19/08) EMBUTIDAS AQUI:
  1. duas idas ao Shell — este runner hoje; o `off26_32_fix.py` amanhã, pós-fechamento;
  2. **dropados são PULADOS** (consistente com o `derive_targets` do OFF26-32: quem foi cortado
     tem contrato morto e o re-add abre contrato novo pela porta canônica);
  3. `contract_start_season` divergente de 2025 ⇒ **ABORTA tudo e reporta** — nada é escrito.

POLÍTICA DE TRIAGEM (explícita, para não haver dúvida do que é pular e do que é abortar):
  ABORTA a execução inteira ...... sid ausente do banco · sid ambíguo (2+ linhas) ·
                                   `contract_start_season` ≠ 2025 · `acquisition_type` ≠
                                   `fa_waiver` · `needs_review` = True · `contract_year`
                                   fora de {3 (alvo), 2 (já corrigido)}
  PULA e segue ................... `is_dropped` = True (decisão 2) ·
                                   `contract_year` já = 2 (idempotência)

Uso (no Render Shell, com DYNASTY_DB=/data/dynasty.db no ambiente):

    # 0) BACKUP OBRIGATÓRIO (sem ele o --apply recusa escrever):
    sqlite3 /data/dynasty.db ".backup '/data/pre_wv1_fix.db'"

    # 1) Conferência read-only (lê os 18 ao vivo do banco + triagem + invariante):
    python wv1_fix_coorte.py --check

    # 2) Escrita (triagem → guarda da porta → escrita+trilha → verificação → commit):
    python wv1_fix_coorte.py --apply --backup /data/pre_wv1_fix.db

    # Ensaio local: acrescentar --db <caminho de uma CÓPIA>
    # Sem rede (a checagem de roster ao vivo é ADVISÓRIA aqui): --offline
"""

import argparse
import json
import os
import sqlite3
import sys
import urllib.request
from pathlib import Path
from types import SimpleNamespace

BASE_DIR = Path(__file__).resolve().parent
LEAGUE_ID = "1316547584378048512"

# Coorte CONGELADA — os 18 "certos" da MAN-WV1-F1 (claim fora da janela sob QUALQUER leitura),
# confirmados em prod pela MAN-WV1-VERIFY-PROD. IDs são STRINGS: as DEFs usam sigla ("BUF"),
# nunca coagir a inteiro.
COHORT = [
    ("BUF",   "Buffalo Bills"),
    ("9501",  "DeMario Douglas"),
    ("10226", "Andrei Iosivas"),
    ("11643", "Jaylen Wright"),
    ("11435", "Emanuel Wilson"),
    ("96",    "Aaron Rodgers"),
    ("7839",  "Evan McPherson"),
    ("5095",  "Daniel Carlson"),
    ("11647", "Kimani Vidal"),
    ("2374",  "Tyler Lockett"),
    ("7002",  "Juwan Johnson"),
    ("9228",  "Bryce Young"),
    ("11625", "Adonai Mitchell"),
    ("6130",  "Devin Singletary"),
    ("6650",  "Chase McLaughlin"),
    ("JAX",   "Jacksonville Jaguars"),
    ("ATL",   "Atlanta Falcons"),
    ("9754",  "Quentin Johnston"),
]

# Guarda pré-escrita da porta canônica (revalidada linha a linha por ela).
EXPECTED = {
    "contract_year": 3,
    "contract_start_season": 2025,
    "acquisition_type": "fa_waiver",
    "needs_review": False,
    "is_dropped": False,
}
NEW_YEAR = 2
CSS_EXPECTED = 2025

# Correção de salário: ano 2 de waiver/FA = floor(0,8 × ESPN), piso $1 (6.6 + 6.10).
# Medido em prod: ESPN 1.0 (Mitchell) e 2.0 (Johnston) ⇒ $1 nos dois. ⭐ O alvo $1 é ROBUSTO à
# pendência raw × ajustado do MAN-ESPN12: mesmo lendo os valores como raw (×1,2 ⇒ 1.2 e 2.4),
# floor(0,8 × ESPN) continua $1 nos quatro cenários.
SALARY_FIXES = {"11625": (2.0, 1.0), "9754": (2.0, 1.0)}

EVENT_REF = "fix:wv1-coorte"
REASON = ("Correção MAN-WV1-FIX-COORTE aprovada pelo owner em 19/08/2026 (claim de waiver fora "
          "da janela do drop = aquisição nova; regra 6.6/6.1: ano 1 = 2025, logo 2026 é ano 2)")
SALARY_REASON = ("Correção MAN-WV1-FIX-COORTE (ano 2 de waiver/FA = floor(0,8 x ESPN), piso $1 "
                 "- regras 6.6 e 6.10)")


# ── Núcleo puro ───────────────────────────────────────────────────────────────

def triage(states_by_sid: dict, cohort=None, expected=None, new_year=NEW_YEAR) -> tuple:
    """Classifica a coorte congelada em (eligible, skipped, aborts) — puro, sem DB.

    states_by_sid: sid → LISTA de estados (dicts) lidos do banco (lista, para detectar sid
    ambíguo). Devolve:
      eligible — sids a corrigir (contract_year → new_year);
      skipped  — [{"sleeper_player_id", "reason"}] — categorias ESPERADAS (dropado, já corrigido);
      aborts   — [{"sleeper_player_id", "reason"}] — qualquer um deles cancela a execução inteira.
    """
    cohort = cohort or COHORT
    expected = expected or EXPECTED
    eligible, skipped, aborts = [], [], []
    for sid, _name in cohort:
        rows = states_by_sid.get(sid) or []
        if not rows:
            aborts.append({"sleeper_player_id": sid, "reason": "ausente do banco"})
            continue
        if len(rows) > 1:
            aborts.append({"sleeper_player_id": sid,
                           "reason": f"{len(rows)} linhas para o mesmo sleeper_player_id - ambiguo"})
            continue
        st = rows[0]
        css = st.get("contract_start_season")
        if css is None or int(css) != CSS_EXPECTED:
            aborts.append({"sleeper_player_id": sid,
                           "reason": f"contract_start_season={css!r} (esperado {CSS_EXPECTED}) "
                                     "- decisao 3 do owner: abortar e reportar"})
            continue
        acq = str(st.get("acquisition_type") or "").strip()
        if acq != expected["acquisition_type"]:
            aborts.append({"sleeper_player_id": sid,
                           "reason": f"acquisition_type={acq!r} (esperado "
                                     f"{expected['acquisition_type']!r}) - canal mudou"})
            continue
        if bool(st.get("needs_review")):
            aborts.append({"sleeper_player_id": sid, "reason": "needs_review=True"})
            continue
        if bool(st.get("is_dropped")):
            skipped.append({"sleeper_player_id": sid,
                            "reason": "DROPADO - pulado por decisao do owner (contrato morto; "
                                      "re-add abre contrato novo pela porta canonica)"})
            continue
        cy = st.get("contract_year")
        if cy == new_year:
            skipped.append({"sleeper_player_id": sid,
                            "reason": f"contract_year ja e {new_year} - nada a fazer"})
            continue
        if cy != expected["contract_year"]:
            aborts.append({"sleeper_player_id": sid,
                           "reason": f"contract_year={cy!r} (esperado {expected['contract_year']} "
                                     f"ou {new_year}) - estado inesperado"})
            continue
        eligible.append(sid)
    return eligible, skipped, aborts


def select_salary_fixes(eligible: list, states_by_sid: dict, fixes=None) -> tuple:
    """Quais correções de salário aplicar entre os elegíveis — puro.

    Só entra quem (a) está elegível na contagem, (b) consta no mapa de correções e (c) tem
    o salário ATUAL exatamente igual ao esperado. Devolve (to_fix, mismatches).
    """
    fixes = SALARY_FIXES if fixes is None else fixes
    to_fix, mismatches = [], []
    for sid in eligible:
        if sid not in fixes:
            continue
        want_old, new = fixes[sid]
        got = (states_by_sid.get(sid) or [{}])[0].get("salary")
        if got is None or float(got) != float(want_old):
            mismatches.append({"sleeper_player_id": sid,
                               "reason": f"salary={got!r} (esperado {want_old}) - nao corrigido"})
        else:
            to_fix.append((sid, float(want_old), float(new)))
    return to_fix, mismatches


def expected_money_after(states_by_sid: dict, eligible: list, new_year=NEW_YEAR,
                         fixes=None) -> dict:
    """Estado financeiro ESPERADO pós-correção, por sid — puro (usa o salary_engine)."""
    from salary_engine import project_next_salary
    fixes = SALARY_FIXES if fixes is None else fixes
    out = {}
    for sid in eligible:
        st = (states_by_sid.get(sid) or [{}])[0]
        sal = float(fixes[sid][1]) if sid in fixes else float(st.get("salary") or 0)
        stub = SimpleNamespace(salary=sal, espn_ref_value=st.get("espn_ref_value"),
                               acquisition_type=st.get("acquisition_type"),
                               contract_year=new_year)
        out[sid] = {"salary": int(sal), "projected": int(project_next_salary(stub))}
    return out


def money_diff(before: dict, after: dict, allowed: set = None) -> list:
    """Violações do invariante financeiro — puro.

    `allowed` = sids em que o dinheiro PODE mudar (as correções de salário aprovadas). Para os
    demais, salário e projeção do ano seguinte têm de sair idênticos.
    """
    allowed = allowed or set()
    viol = []
    for sid, pre in before.items():
        post = after.get(sid)
        if post is None:
            viol.append(f"{sid}: ausente na releitura pos-escrita")
            continue
        if sid in allowed:
            continue
        if int(pre["salary"]) != int(post["salary"]):
            viol.append(f"{sid}: salario {pre['salary']} -> {post['salary']}")
        if int(pre["projected"]) != int(post["projected"]):
            viol.append(f"{sid}: projecao {pre['projected']} -> {post['projected']}")
    return viol


# ── IO ────────────────────────────────────────────────────────────────────────

def fetch_rostered_sids(league_id: str = LEAGUE_ID, timeout: int = 30) -> set:
    """GET read-only dos rosters — conjunto de sleeper_player_ids rosterados (inclui IR)."""
    url = f"https://api.sleeper.app/v1/league/{league_id}/rosters"
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        rosters = json.load(resp)
    sids = set()
    for ro in rosters:
        for key in ("players", "reserve", "taxi"):
            for pid in (ro.get(key) or []):
                sids.add(str(pid))
    return sids


def _db_path(cli_db: str = None) -> Path:
    return Path(cli_db or os.environ.get("DYNASTY_DB") or (BASE_DIR / "dynasty.db"))


def _make_app(db_path: Path):
    """App Flask mínimo — só o bind do banco. NÃO roda o boot do app.py."""
    from flask import Flask
    from models import db
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_path.as_posix()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    return app


def _states_from_db(sids: list) -> dict:
    """sid → [estado] lido do ORM, com os campos que a triagem e o invariante conhecem."""
    from models import Player
    out = {}
    for p in Player.query.filter(Player.sleeper_player_id.in_(sids)).all():
        out.setdefault(p.sleeper_player_id, []).append({
            "player_id": p.id,
            "name": p.name,
            "team": p.team_rel.name if p.team_rel else "",
            "contract_year": p.contract_year,
            "contract_start_season": p.contract_start_season,
            "acquisition_type": p.acquisition_type,
            "needs_review": p.needs_review,
            "is_dropped": p.is_dropped,
            "salary": p.salary,
            "espn_ref_value": p.espn_ref_value,
        })
    return out


def _snapshot_players(db_path: Path) -> dict:
    con = sqlite3.connect(str(db_path))
    cols = [r[1] for r in con.execute("PRAGMA table_info(players)")]
    rows = {r[0]: dict(zip(cols, r)) for r in
            con.execute(f"SELECT {', '.join(cols)} FROM players")}
    con.close()
    return rows


def _money_state(states_by_sid: dict, sids: list) -> dict:
    from salary_engine import project_next_salary
    out = {}
    for sid in sids:
        st = states_by_sid[sid][0]
        stub = SimpleNamespace(salary=st["salary"], espn_ref_value=st["espn_ref_value"],
                               acquisition_type=st["acquisition_type"],
                               contract_year=st["contract_year"])
        out[sid] = {"salary": int(st["salary"]), "projected": int(project_next_salary(stub))}
    return out


def _live_note(sids: list, offline: bool) -> tuple:
    """Cruzamento ADVISÓRIO com os rosters ao vivo. Devolve (nao_rosterados, nota)."""
    if offline:
        return set(), "SEM cruzamento ao vivo (--offline) - a triagem usa a foto do banco"
    try:
        rostered = fetch_rostered_sids()
    except Exception as exc:
        return set(), (f"cruzamento ao vivo INDISPONIVEL ({exc.__class__.__name__}) - "
                       "seguindo pela foto do banco (lista congelada; a guarda protege)")
    missing = {s for s in sids if s not in rostered}
    return missing, f"rosters ao vivo do Sleeper ({len(rostered)} rosterados)"


# ── Relatórios ────────────────────────────────────────────────────────────────

def _report(states, eligible, skipped, aborts, names, live_missing, live_note):
    print(f"\nCoorte congelada: {len(COHORT)} sids (MAN-WV1-F1 + VERIFY-PROD, 19/08/2026)")
    print(f"Cruzamento ao vivo: {live_note}")
    print(f"Guarda da porta: {EXPECTED}")

    print(f"\nELEGIVEIS ({len(eligible)}):")
    for sid in eligible:
        st = states[sid][0]
        sal_note = ""
        if sid in SALARY_FIXES:
            sal_note = f"  + salario ${int(SALARY_FIXES[sid][0])} -> ${int(SALARY_FIXES[sid][1])}"
        live = "  [!] NAO rosterado ao vivo" if sid in live_missing else ""
        print(f"  ok     {sid:>6}  {st['name']:<22} {st['team'][:22]:<22} "
              f"cy {st['contract_year']} -> {NEW_YEAR}  sal ${int(st['salary'])} "
              f"espn {st['espn_ref_value']} css {st['contract_start_season']}{sal_note}{live}")

    print(f"\nPULADOS ({len(skipped)}):")
    for s in skipped:
        sid = s["sleeper_player_id"]
        st = (states.get(sid) or [{}])[0]
        flag = "DROPADO" if "DROPADO" in s["reason"] else "       "
        print(f"  {flag} {sid:>6}  {names.get(sid, '?'):<22} {s['reason']}")
    if not skipped:
        print("  (nenhum)")

    if aborts:
        print(f"\n[ABORT] MOTIVOS DE ABORTO ({len(aborts)}) - NADA sera escrito:")
        for a in aborts:
            print(f"  ABORT  {a['sleeper_player_id']:>6}  {names.get(a['sleeper_player_id'], '?'):<22} "
                  f"{a['reason']}")


# ── Comandos ──────────────────────────────────────────────────────────────────

def cmd_check(db_path: Path, offline: bool = False) -> int:
    """Read-only: lê os 18 ao vivo do banco, tria, simula o invariante. Nada é escrito."""
    names = dict(COHORT)
    sids = [sid for sid, _ in COHORT]
    live_missing, live_note = _live_note(sids, offline)

    app = _make_app(db_path)
    with app.app_context():
        states = _states_from_db(sids)
        eligible, skipped, aborts = triage(states)
        print(f"\nBanco: {db_path}")
        _report(states, eligible, skipped, aborts, names, live_missing, live_note)

        to_fix, sal_mm = select_salary_fixes(eligible, states)
        print(f"\nCorrecoes de salario previstas: {len(to_fix)}")
        for sid, old, new in to_fix:
            print(f"  ok     {sid:>6}  {states[sid][0]['name']:<22} ${int(old)} -> ${int(new)}")
        for m in sal_mm:
            print(f"  PULADO {m['sleeper_player_id']:>6}  {m['reason']}")

        before = _money_state(states, eligible)
        after = expected_money_after(states, eligible)
        viol = money_diff(before, after, allowed={sid for sid, _, _ in to_fix})
        print(f"\nInvariante financeiro (simulado): "
              f"{'OK - so os salarios aprovados mudam' if not viol else 'VIOLADO'}")
        for v in viol:
            print(f"  x {v}")
        for sid, _, _ in to_fix:
            print(f"  esperado {sid}: salario {before[sid]['salary']} -> {after[sid]['salary']}, "
                  f"projecao {before[sid]['projected']} -> {after[sid]['projected']}")

    ok = not aborts and not viol and not sal_mm
    print(f"\n--check: {'OK - ' + str(len(eligible)) + ' elegiveis, ' + str(len(skipped)) + ' pulados, invariante intacto' if ok else 'ATENCAO - ver acima; --apply RECUSA executar'}")
    return 0 if ok else 1


def _verify_backup(backup: Path, db_path: Path) -> bool:
    if not backup.exists():
        print(f"[X] Backup nao encontrado: {backup}")
        return False
    b, d = backup.stat().st_size, db_path.stat().st_size
    if b < 0.5 * d:
        print(f"[X] Backup implausivel: {b} bytes contra {d} do banco alvo")
        return False
    print(f"Backup conferido: {backup} ({b} bytes; banco alvo {d} bytes)")
    return True


def cmd_apply(db_path: Path, backup: Path, offline: bool = False) -> int:
    """Triagem → guarda da porta → escrita+trilha → verificação → commit."""
    from models import db, Player
    from contract_year_correction import apply_contract_year_correction, EVENT_TYPE
    from models import correct_player_salary

    if not _verify_backup(backup, db_path):
        return 1

    names = dict(COHORT)
    sids = [sid for sid, _ in COHORT]
    live_missing, live_note = _live_note(sids, offline)
    pre = _snapshot_players(db_path)

    app = _make_app(db_path)
    with app.app_context():
        states = _states_from_db(sids)
        eligible, skipped, aborts = triage(states)
        _report(states, eligible, skipped, aborts, names, live_missing, live_note)

        if aborts:
            print("\n[X] ABORTADO por estado inesperado (decisao 3 do owner). Nada escrito.")
            return 1
        if not eligible:
            print("\nNada elegivel - nenhuma escrita. (Ja corrigido, ou tudo dropado.)")
            return 1

        to_fix, sal_mm = select_salary_fixes(eligible, states)
        if sal_mm:
            print("\n[X] ABORTADO: salario divergente do esperado nos alvos de correcao "
                  "(estado inesperado). Nada escrito.")
            for m in sal_mm:
                print(f"  - {m['sleeper_player_id']}: {m['reason']}")
            return 1

        money_before = _money_state(states, eligible)

        # 1) contagem — porta canônica (revalida a guarda linha a linha)
        result = apply_contract_year_correction(
            eligible, expected=EXPECTED, new_year=NEW_YEAR,
            reason=REASON, event_ref=EVENT_REF)
        if len(result["applied"]) != len(eligible):
            db.session.rollback()
            print(f"\n[X] A guarda da porta canonica recusou {len(result['skipped'])} linha(s) "
                  "que a triagem julgou elegiveis - rollback, nada escrito:")
            for s in result["skipped"]:
                print(f"  - {s['sleeper_player_id']}: {s['reason']}")
            return 1
        for a in result["applied"]:
            print(f"  escrito {a['sleeper_player_id']:>6}  {a['name']:<22} "
                  f"contract_year {a['old']} -> {a['new']}")

        # 2) salário — porta canônica (Player + SalaryHistory + PlayerHistory)
        sal_applied = []
        for sid, old, new in to_fix:
            pid = states[sid][0]["player_id"]
            r = correct_player_salary(pid, new, reason=SALARY_REASON)
            if r.get("error") or not r.get("changed"):
                db.session.rollback()
                print(f"\n[X] correct_player_salary recusou {sid} ({r}) - rollback, nada escrito.")
                return 1
            sal_applied.append((sid, old, new))
            print(f"  escrito {sid:>6}  {states[sid][0]['name']:<22} "
                  f"salary ${int(old)} -> ${int(new)}")

        # verificação in-transação antes do commit
        bad = [a for a in result["applied"]
               if db.session.get(Player, a["player_id"]).contract_year != NEW_YEAR]
        bad += [sid for sid, _, new in sal_applied
                if float(db.session.get(Player, states[sid][0]["player_id"]).salary) != new]
        if bad:
            db.session.rollback()
            print(f"\n[X] Releitura in-transacao divergente ({len(bad)}) - rollback, nada escrito.")
            return 1

        db.session.commit()
        applied = result["applied"]

        post_states = _states_from_db(eligible)
        money_after = _money_state(post_states, eligible)
        viol = money_diff(money_before, money_after,
                          allowed={sid for sid, _, _ in sal_applied})

    # ── Verificação pós-commit por conexão independente (raw sqlite) ──────────
    post = _snapshot_players(db_path)
    applied_ids = {a["player_id"] for a in applied}
    sal_ids = {states[sid][0]["player_id"] for sid, _, _ in sal_applied}
    errors = []

    if set(pre) != set(post):
        errors.append(f"linhas criadas/apagadas em players: {sorted(set(pre) ^ set(post))}")
    changed = {pid for pid in pre if pid in post
               and any(pre[pid][c] != post[pid][c] for c in pre[pid])}
    if changed != applied_ids:
        errors.append(f"linhas alteradas != elegiveis: {sorted(changed ^ applied_ids)}")
    for pid in applied_ids:
        diff_cols = {c for c in pre[pid] if pre[pid][c] != post[pid][c]}
        allowed_cols = {"contract_year", "updated_at"} | ({"salary"} if pid in sal_ids else set())
        if not diff_cols <= allowed_cols:
            errors.append(f"player {pid}: colunas alteradas alem do previsto: {sorted(diff_cols)}")
        if post[pid]["contract_year"] != NEW_YEAR:
            errors.append(f"player {pid}: contract_year={post[pid]['contract_year']} "
                          f"(esperado {NEW_YEAR})")

    con = sqlite3.connect(str(db_path))
    trail = con.execute(
        "SELECT COUNT(*) FROM player_history WHERE event_type=? AND sleeper_event_ref=?",
        (EVENT_TYPE, EVENT_REF)).fetchone()[0]
    sal_trail = con.execute(
        "SELECT COUNT(*) FROM player_history WHERE event_type='salary_correction' "
        "AND notes LIKE ?", ("%MAN-WV1-FIX-COORTE%",)).fetchone()[0]
    con.close()
    if trail != len(applied):
        errors.append(f"trilha de contagem: {trail} linhas (esperado {len(applied)})")
    if sal_trail < len(sal_applied):
        errors.append(f"trilha de salario: {sal_trail} linhas (esperado >= {len(sal_applied)})")
    errors.extend(f"invariante financeiro: {v}" for v in viol)

    print(f"\nVerificacao pos-escrita: {len(applied)} contagens corrigidas; "
          f"{len(sal_applied)} salarios corrigidos; {len(changed)} linhas alteradas; "
          f"{trail}+{sal_trail} linhas de trilha; invariante {'OK' if not viol else 'VIOLADO'}.")
    if errors:
        print("[X] FALHAS DE VERIFICACAO (o commit JA ocorreu - avaliar restore do backup):")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("[OK] So contract_year (+salary dos 2 aprovados, +updated_at) mudou; trilha completa; "
          "nenhum outro salario ou projecao alterado.")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="MAN-WV1-FIX-COORTE: contract_year 3->2 nos 18 da coorte WV1 + 2 salarios $2->$1")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="read-only: triagem + invariante")
    mode.add_argument("--apply", action="store_true", help="escreve (exige --backup conferivel)")
    ap.add_argument("--backup", help="caminho do backup feito ANTES (obrigatorio no --apply)")
    ap.add_argument("--db", help="override do banco (ensaio); padrao: env DYNASTY_DB")
    ap.add_argument("--offline", action="store_true",
                    help="pula o cruzamento ADVISORIO com os rosters ao vivo")
    args = ap.parse_args(argv)

    db_path = _db_path(args.db)
    if not db_path.exists():
        print(f"[X] Banco nao encontrado: {db_path}")
        return 1
    if args.apply and not args.backup:
        print("[X] --apply exige --backup <caminho do backup feito antes>. Nenhuma escrita.")
        return 1
    if args.check:
        return cmd_check(db_path, args.offline)
    return cmd_apply(db_path, Path(args.backup), args.offline)


if __name__ == "__main__":
    sys.exit(main())
